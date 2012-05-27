
import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.fbsettings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

import xlrd
from catalog.models import SellerRateChart, ProductTags, Product, Tag, ProductVariant
from lists.models import List, BattleTab, ListItem
from django.template.defaultfilters import slugify
from utils.solrutils import *
from django.template.defaultfilters import striptags
log = logging.getLogger('request')

def upload_sabse_sasta_sale(list_id, xls_path, client_id):
    book = xlrd.open_workbook(xls_path)
    sh = book.sheet_by_index(0)
    header = sh.row(0)
    map = {}
    idx = 0
    for idx in range(sh.ncols):
        map[header[idx].value.strip().lower()] = idx
    errors = []
    to_update = []
    
    lob_tabs = {}
    # Excel File requires below fields
    # lob - article no
    products = []
    for row_count in range(1, sh.nrows):
        row = sh.row(row_count)
        article_no = row[map['article no']].value
        article_no = int(article_no)
        lob = str(row[map['lob']].value)
        sku = None    
        try:
            sku = SellerRateChart.objects.select_related('product').get(article_id=article_no, seller__client = client_id)
            products.append(sku.product)
        except Exception,e:
            errors.append('Error for Article No: %s at row: %s -- %s' % (article_no, row_count + 1, repr(e)))
            continue
        update_item = {
            'article_no': article_no,
            'row_no' : row_count,
            'lob' : lob,
            'sku' : sku,
            'original_prod':sku.product,
        }

        to_update.append(update_item)
        # Get all LOBs, to create Tab
        if lob in lob_tabs:
            lob_tabs[lob].append(update_item)
        else:
            lob_tabs[lob] = [update_item]
    if errors:
        # Return if some article ids are not found 
        for error in errors:
            print error
        return False
    variant_products = products
    productvariants = ProductVariant.objects.select_related('blueprint', 'variant').filter(variant__in=variant_products)
    variant_product_map = {}

    for pv in productvariants:
        variant_product_map[pv.variant] = pv.blueprint
    products_map = {}
    for product in variant_products:
        prod = product
        if product.type == 'variant':
            try:
                prod = variant_product_map[product]
            except KeyError:
                continue
        if product not in products_map:
            products_map[product] = prod

    updated_items = []
    list = List.objects.get(id = list_id, type="sabse_sasta_sale")
    sort_order = 1
    to_be_deleted_product_tags = ProductTags.objects.filter(type='sabse_sasta_sale')
    for lob_name, lob_values in lob_tabs.iteritems():
        lob_tab = get_or_create_tab(lob_name ,list, sort_order)
        print "VALUES:: ",lob_values
        sort_order += 1
        for item in lob_values:
            item['product'] = products_map[item['original_prod']]
            product_tag = get_or_create_product_tag(item, list, lob_tab)
            update_solr_index(products_map[item['original_prod']], lob_tab.id)
            if product_tag in to_be_deleted_product_tags:
                to_be_deleted_product_tags.exclude(id=product_tag.id)
    print "Deleting Previously added: %s Product Tags" % len(to_be_deleted_product_tags)
    for pt in to_be_deleted_product_tags:
        print "Deleted -- ProductTag -- ",pt.product
        pt.delete()

def get_or_create_tab(name, list, sort_order):
    tab = BattleTab.objects.filter(list=list, name=name)
    if not tab:
        tab = BattleTab()
        tab.name = name
        tab.list = list
        tab.sort_order = sort_order
        tab.tag_name = slugify(name)
        print "CREATED BATTLE TAB:: ",name
    else:
        tab = tab[0]
        tab.sort_order = sort_order
        tab.tag_name = slugify(name)
    tab.save()
    return tab

def get_or_create_product_tag(item, list, tab):
    product = item['product']
    try:
        product_tag = ProductTags.objects.get(product=product, type='sabse_sasta_sale')
        product_tag.tab = tab
        product_tag.sort_order = item['row_no']
    except ProductTags.DoesNotExist:
        product_tag = ProductTags()
        product_tag.product = product
        product_tag.type = 'sabse_sasta_sale'
        product_tag.tab = tab
        product_tag.sort_order = item['row_no']
    product_tag.save()
    return product_tag


# Can't use the function available in catalog/models coz it would slow the normal feed sync
# Hence copting the same function and adding code for indexing battle tab
# ----------------------------------------------------------------------------------------------
def update_solr_index(product, tab_id, commit=True):
    self = product
    self.reset_default_variant()
    if not self.primary_rate_chart():
        solr_delete(self.id)
        return
    data = dict(title=self.title, model=self.model, brand=self.brand.name,
        brand_id = self.brand.id, type = self.type, status=self.status,
        currency = self.currency, id = self.id,sku=self.primary_rate_chart().sku, tab_id=tab_id)

    cat_parents = self.category.get_all_parents()
    if cat_parents:
        category = [x.name for x in self.category.get_all_parents()]
        category.append(self.category.name)
        category_id = [str(x.id) for x in self.category.get_all_parents()]
        category_id.append(str(self.category.id))
    else:
        category = [self.category.name]
        category_id = [str(self.category.id)]

    data.update({'category_id':category_id,'category':category})

    features = []
    p_features = self.productfeatures_set.select_related('feature').all()
    for pf in p_features:
        is_present = False
        key = pf.feature.solr_key()
        value = pf.to_python_value()
        if pf.feature.index_for_presence:
            is_present = True
            if str(value).lower().startswith('no'):
                is_present = False
            if str(value).lower().startswith('false'):
                is_present = False
            fg = pf.feature.group
            if is_present:
                if data.get('%s_pr_l' % fg.id):
                    data.get('%s_pr_l' % fg.id).append(pf.feature.id)
                else:
                    data['%s_pr_l' % fg.id] = [pf.feature.id]
        data.update({key:value})
        if pf.feature.type == 'boolean' and pf.bool:
            features.append(pf.feature.name)
            continue
        pfsc = pf.productfeatureselectedchoice_set.select_related('choice').all()
        if pfsc:
            for sc in pfsc:
                features.append(sc.choice.name)
            continue
    data.update({'features':features})

    try:
        psrcs = self.sellerratechart_set.all()
        seller_ids = []
        for src in psrcs:
            seller_ids.append(src.seller.id)
        data.update({'seller_id':seller_ids})
    except SellerRateChart.DoesNotExist:
        pass
    try:
        tags = self.producttags_set.all()
        if tags:
            data['tags'] = [tag.tag.tag for tag in tags]
            data['tag_id'] = [tag.tag.id for tag in tags]
        else:
            data['tags'] = []
            data['tag_id'] = []
    except:
        pass

    try:
        src = self.primary_rate_chart()
        price = src.offer_price
        inStock = True
        if src.stock_status != 'instock':
            inStock = False
        if src:
            sku = src.sku
        else:
            sku = None

        client_id = src.seller.client.id
        applicable_price_lists = []
        client_domains = src.seller.client.clientdomain_set.all()

        for domain in client_domains:
            price_info = src.get_price_for_domain(domain,**{'dont_cache':True})
            data.update({'offerprice_%s' % domain.id:price_info['offer_price'], 
                        'listprice_%s' % domain.id:price_info['list_price'], 
                        'discount_%s' % domain.id:price_info['discount']})

        data.update({'price':price,'inStock':inStock,'sku':sku,'client_id':client_id})
        if src.key_feature:
            data.update({'key_features': striptags(src.key_feature)})
    except SellerRateChart.DoesNotExist:
        pass
    except SellerRateChart.MultipleObjectsReturned:
        log.info('Found multiple rate charts for product %s' % self.id)

    #Add number of products sold in last 7 days
    from orders.models import OrderCount
    data['order_count'] = 0
    try:
        order_count_obj = OrderCount.objects.get(product=self)
        data['order_count'] = "%.0f" % order_count_obj.order_count
    except OrderCount.DoesNotExist:
        log.info('Order count not found for product %s' % self.id)

    add_data(data)
   
if __name__ == '__main__':
    list_id = 60
    # Upload excel path
    xls_path = '/home/saumil/Desktop/26th-Jan-Offers.xls'
    client_id = 5
    upload_sabse_sasta_sale(list_id, xls_path, client_id)



