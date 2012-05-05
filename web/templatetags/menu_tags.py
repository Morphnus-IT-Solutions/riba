from django.template import Library, Node
from web.models import *
from catalog.models import Product, Brand, ProductTags, Tag
from django.core.cache import cache
from utils import utils
from categories.models import *
from decimal import Decimal
from datetime import datetime
from web.sbf_forms import get_facets_by_filter
import logging
import math
log = logging.getLogger('request')
register = Library()

def split_and_add(lst, cols, group):
    max_rows = len(lst)/cols
    remainder = len(lst)%cols
    if remainder:
        max_rows += 1

    sublists = {}
    for col_no in range(cols):
        start = col_no*max_rows
        end = start + max_rows
        sublists[col_no] = lst[start:end]
    for row_no in range(max_rows):
        row_col = []
        for col_no in range(cols):
            if len(sublists[col_no]) > row_no:
                row_col.append(sublists[col_no][row_no])
            else:
                row_col.append({})
        group['rows'].append({'columns':row_col})

def store_category_brand_list(seller,store, limit=None):
    cols = 3
    groups = []

    #cat_list = [c for c in store.category_set.all().order_by('name')]
    store_cat_key = 'store_cat_%s' % seller.id if seller else 'chaupaati'
    store_cat_map = cache.get(store_cat_key)
    if store_cat_map and store in store_cat_map:
        if store in store_cat_map:
            cat_list = store_cat_map[store]
    else:
        cat_list = []
        cc = seller.storeowner_set.all()
        cc.query.group_by = ["category_id"]
        for c in cc:
            if seller.id in utils.get_future_group():
                if c.category.product_set.filter(status='active',sellerratechart__seller=seller):
                    cat_list.append(c.category)
            else:
                if c.category.product_set.filter(status='active',sellerratechart__seller__is_exclusive=False):
                    cat_list.append(c.category)
        if not store_cat_map:
            store_cat_map = {}
            store_cat_map[store] = cat_list[:limit]
            cache.set(store_cat_key,store_cat_map,36000)
        else:
            if type(store_cat_map) is list:
                store_cat_map = store_cat_map[0]
            store_cat_map.update({store:cat_list[:limit]})
            cache.set(store_cat_key,store_cat_map,36000)
    cat_group = dict(heading='Categories', rows=[], cols=cols)
    split_and_add(cat_list[:limit], cols, cat_group)
    groups.append(cat_group)

    brands_group = dict(heading='Brands', rows=[], cols=cols)
    brands_list = Brand.objects.filter(id__in =
            Product.objects.filter(
                category__in = cat_list,status='active').distinct(
                    'brand').values('brand'))[:limit]
    split_and_add(brands_list, cols, brands_group)
    groups.append(brands_group)
    return groups

def render_mobile_menu_clearance(request):
    menu_context = {}
    menu_context['clearance_sale']=get_clearance_tags(request)
    menu_context['request'] = request
    return menu_context
register.inclusion_tag('web/clearance_list.html')(render_mobile_menu_clearance)

def render_mobile_menu_category(request):
    menu_key = 'menu#%s' % (request.client.client.id)
    menu_context = cache.get(menu_key)
    if not menu_context:
        menu_context = get_menu(request)
        cache.set(menu_key, menu_context, 3600)
    menu_context['request'] = request
    return menu_context
register.inclusion_tag('web/category_list.html')(render_mobile_menu_category)

def render_daily_deal(request):
    daily_deal_context = {}
    _client = request.client.client
    steal_of_the_day = DailyDeal.objects.filter(type='hero_deal', starts_on__lte = datetime.now(), ends_on__gte = datetime.now(), client=_client)
    daily_deal = None
    if steal_of_the_day:
        steal_of_the_day = steal_of_the_day[0]
        products = steal_of_the_day.dailydealproduct_set.all().select_related('product')
        if not products:
            steal_of_the_day = None
        else:
            product = products[0].product
            sku = product.primary_rate_chart()
            daily_deal = {'type':'daily_deal', 'sku':sku, 'deal_product':product, 'deal':steal_of_the_day}
    daily_deal_context['daily_deal'] = daily_deal
    daily_deal_context['request'] = request
    return daily_deal_context
register.inclusion_tag('web/daily_deal.html')(render_daily_deal)

def render_menu(request):
    menu_key = 'menu#%s' % (request.client.client.id)
    menu_context = cache.get(menu_key)
    if not menu_context:
        menu_context = get_menu(request)
        if utils.get_future_ecom_prod() == request.client.client:
            from lists.models import List
            menu_context['clearance_sale'] = get_clearance_tags(request)
        '''
        Caching Menu for 4 Hours
        '''
        cache.set(menu_key, menu_context, 14400)
    menu_context['request'] = request
    return menu_context
register.inclusion_tag('web/menu.html')(render_menu)

def render_mega_menu(request):
    menu_context = get_menu(request)
    menu_context['request'] = request
    return menu_context
register.inclusion_tag('web/menu.html')(render_mega_menu)


def get_menu(request):
    if utils.get_future_ecom_prod() == request.client.client:
        return get_future_bazaar_menu(request)
    items = []
    banner_urls = {'dod':'', 'battle':'', 'top10':''}

    if not items:
        items = []
        steal_of_the_day = DailyDeal.objects.filter(starts_on__lte = datetime.now(), ends_on__gte = datetime.now(), client=request.client.client)
        if steal_of_the_day:
            steal_of_the_day = steal_of_the_day[0]
            products = steal_of_the_day.dailydealproduct_set.all()
            product = products[0].product
            view_more = False
            if len(products) > 1:
                view_more = True
            sku = product.primary_rate_chart()
            items.append({'type':'daily_deal', 'sku':sku, 'deal_product':product, 'deal':steal_of_the_day, 'view_more':view_more})
        category_items = []
        for item in MegaDropDown.objects.filter(client=request.client.client).order_by('sort_order'):            
            if item.type == 'category':
                sub_cats = CategoryGraph.objects.select_related(
                    'category').filter(parent=item.category)
                active_cats = []
                if item.category and item.category.id not in [1097, 974, 976, 962]:
                    for cat in sub_cats:
                        if cat.category.product_set.filter(status='active').count() > 0:
                            active_cats.append(cat)
                        else:
                            total = 0
                            for c in cat.category.get_all_children():
                                total += c.product_set.filter(status='active').count()
                            if total > 0:
                                active_cats.append(cat)
                    if utils.get_future_ecom_prod() == request.client.client:
                        active_cats = active_cats[:4]
                        if len(active_cats) == 1 or item.category.id == 1097:
                            active_cats = []
                mitems = {}
                mitems={'item':item, 'active_cats':active_cats, 'type':'category'}
                if active_cats:
                    items.append(mitems)
                category_items.append(mitems)
        #cache.set('mega_items',items,36000)
    return {'mega_items':items}

def get_menu_items(request):
    parents = CategoryGraph.objects.filter(parent=None,category__client=request.client.client)
    menuitems = []
    for parent in parents:
        categories = CategoryGraph.objects.filter(parent=parent.category)
        subitems = []
        for cat in categories:
            subcategories = CategoryGraph.objects.filter(parent=cat.category)
            subitems.append({'item':cat,'subitems':subcategories})
        menuitem = {'item':parent,'subitems':subitems}
        menuitems.append(menuitem)
    return {'menuitems':menuitems,'request':request}

def render_store_brand_category_grid(request, store):
    seller,source = utils.get_exclusive_seller_from_request(request)
    groups = store_category_brand_list(seller,store)
    return {'groups': groups, 'request': request}
register.inclusion_tag('stores/brand_category_grid.html')(render_store_brand_category_grid)

def get_future_bazaar_menu(request):
    from lists.models import List
    banner_urls = {'dod':'', 'battle':'', 'top10':''}
    _client = request.client.client
    try:
        steal_of_the_day = DailyDeal.objects.get(type='hero_deal', starts_on__lte = datetime.now(), ends_on__gte = datetime.now(), client=_client)
    except DailyDeal.DoesNotExist:
        steal_of_the_day = None
    except DailyDeal.MultipleObjectsReturned:
        steal_of_the_day = DailyDeal.objects.filter(type='hero_deal',\
        starts_on__lte = datetime.now(), ends_on__gte = datetime.now(), client=_client).order_by('-id')[0]
    daily_deal = None
    hero_deal_product_id = None
    if steal_of_the_day:
        products = steal_of_the_day.dailydealproduct_set.all().select_related('product')
        if not products:
            steal_of_the_day = None
        else:
            product = products[0].product
            hero_deal_product_id = product.id
            sku = product.primary_rate_chart()
            deal = steal_of_the_day
            key_features = []
            if deal.features:
                key_features = deal.features.split("\r\n")
            elif product.primary_rate_chart().key_feature:
                key_features = product.primary_rate_chart().key_feature.split("<br>")
            key_features = key_features[:4]
            daily_deal = {'type':'daily_deal', 'rate_chart':sku, 'deal_product':product, 'deal':deal, 'key_features':key_features}
            if steal_of_the_day.home_thumb_banner:
                banner_urls['dod'] = steal_of_the_day.home_thumb_banner.url
    category_items_level1 = []
    category_level1 = []
    category_items_level2 = []
    get_categorygraph_mapping(request)
    tags_retailer = [prod_tag['tag__id'] for prod_tag in ProductTags.objects.select_related("tag__id").filter(type='retailers').values("tag__id").distinct()]
    mega_menu_categories = MegaDropDown.objects.select_related("category").\
                           filter(type__in=["menu_level2_category", "category"], client=_client).order_by('sort_order')
    parent_children_map = get_categorygraph_mapping(request)
    menu_brand_ids = []
    for item in mega_menu_categories:            
        if item.category:
            mitems = {'menu_category' : item.category}
            c2_level_context = []
            c2_categories = CategoryGraph.objects.select_related('category', 'parent').filter(parent = item.category)
            if item.level_2_type == 'only_retailers':
                category_query = "category_id:%s" % (item.category.id)
                brand_retailer_ctxt = get_brands_retailers_by_query(request, category_query, tags_retailer)
                c2_retailer_tags = brand_retailer_ctxt['retailer_tags']
                if c2_retailer_tags:
                    c2_level_context = [{'retailer_tags':c2_retailer_tags, 'brand_ids':[], 'menu_category':item.category}]
            else:
                for category_graph in c2_categories:                        
                    c2_mitems = {}
                    c2_mitems['menu_category'] = category_graph.category
                    c2_mitems['children_cats'] = []
                    if category_graph.category in parent_children_map:
                        c2_mitems['children_cats'] = parent_children_map[category_graph.category]
                        if item.level_2_type == 'grouped_category':
                            group_children_list = []
                            for category in c2_mitems['children_cats']:
                                c3_c4_map = {}
                                c3_c4_map['child'] = category
                                c3_c4_map['grand_children'] = []
                                if category in parent_children_map:
                                    c3_c4_map['grand_children'] = parent_children_map[category]
                                group_children_list.append(c3_c4_map)
                            c2_mitems['children_cats'] = group_children_list
                    if not c2_mitems['children_cats']:
                        continue
                    category_query = "category_id:%s" % (category_graph.category.id)
                    brand_retailer_ctxt = get_brands_retailers_by_query(request, category_query, tags_retailer)
                    for brand_id in brand_retailer_ctxt['brand_ids']:
                        menu_brand_ids.append(brand_id)
                    c2_mitems['brand_ids'] = brand_retailer_ctxt['brand_ids']
                    c2_mitems['retailer_tags'] = brand_retailer_ctxt['retailer_tags']
                    c2_level_context.append(c2_mitems)
            if c2_level_context:
                mitems['c2_level_context'] = c2_level_context
                mitems['level_2_type'] = item.level_2_type
                if item.type == 'category':
                    category_level1.append(mitems)
                else:
                    category_items_level2.append(mitems)

    top_sellers_ids = utils.get_top_sellers(request)
    if hero_deal_product_id:
        try:
            top_sellers_ids.remove(hero_deal_product_id)
        except ValueError:
            pass
    top_sellers_ctxt = get_menu_items_by_product_ids(request, top_sellers_ids, tags_retailer)
    for brand_id in top_sellers_ctxt['brand_ids']:
        menu_brand_ids.append(brand_id)
    category_items_level1 = top_sellers_ctxt['menu_items']

    new_arrivals_ids = utils.get_new_arrivals(request, products_count = 45)
    new_arrivals_ctxt = get_menu_items_by_product_ids(request, new_arrivals_ids, tags_retailer)
    for brand_id in new_arrivals_ctxt['brand_ids']:
        menu_brand_ids.append(brand_id)
    new_arrivals = new_arrivals_ctxt['menu_items']

    menu_brands = Brand.objects.filter(id__in=set(menu_brand_ids))
    menu_brands_map = {}
    for brand in menu_brands:
        menu_brands_map[brand.id] = brand
    for level1_ctxt in category_items_level1:
        level1_ctxt['brands'] = []
        for brand_id in level1_ctxt['brand_ids']:
            try:
                level1_ctxt['brands'].append(menu_brands_map[long(brand_id)])
            except KeyError:
                pass
    for level2_ctxt in category_items_level2:
        for c2_level2_ctxt in level2_ctxt['c2_level_context']:
            c2_level2_ctxt['brands'] = []
            for brand_id in c2_level2_ctxt['brand_ids']:
                try:
                    c2_level2_ctxt['brands'].append(menu_brands_map[long(brand_id)])
                except KeyError:
                    pass
    for level1_ctxt in category_level1:
        for c1_level1_ctxt in level1_ctxt['c2_level_context']:
            c1_level1_ctxt['brands'] = []
            for brand_id in c1_level1_ctxt['brand_ids']:
                try:
                    c1_level1_ctxt['brands'].append(menu_brands_map[long(brand_id)])
                except KeyError:
                    pass
    for new_arrivals_ctxt in new_arrivals:
            new_arrivals_ctxt['brands'] = []
            for brand_id in new_arrivals_ctxt['brand_ids']:
                try:
                    new_arrivals_ctxt['brands'].append(menu_brands_map[long(brand_id)])
                except KeyError:
                    pass
    menu_items = {
            'menu_items_level1' : category_items_level1,
            'menu_items_level2' : category_items_level2,
            'menu_level1'       : category_level1
        }
    menu_context = {
            'mega_items' : menu_items, 
            'daily_deal' : daily_deal, 
            'banner_urls' : banner_urls,
            'new_arrivals' : new_arrivals,
            }
    return menu_context

def get_menu_items_by_product_ids(request, product_ids, tags_retailer):
    data = utils.get_categories_by_id(request, product_ids)
    c1_categories = data['c1_categories']
    category_ids = data['category_ids']
    menu_items = []
    prod_ids = "(" + (" OR ").join(product_ids) + ")"
    brand_ids = []
    parent_children_map = get_categorygraph_mapping(request)

    for c1_category in c1_categories:
        children_cats = []
        if c1_category in parent_children_map:
            categories = parent_children_map[c1_category]
            for category in categories:
                if category.id in category_ids:
                    children_cats.append(category)
        if not children_cats:
            continue
        query = "category_id:%s AND id:%s" % (c1_category.id, prod_ids)
        brand_retailer_ctxt = get_brands_retailers_by_query(request, query, tags_retailer)
        for brand_id in brand_retailer_ctxt['brand_ids']:
            brand_ids.append(brand_id)
        mitems = {
            'menu_category': c1_category, 
            'children_cats': children_cats, 
            'brand_ids': brand_retailer_ctxt['brand_ids'], 
            'retailer_tags': brand_retailer_ctxt['retailer_tags']
        }
        menu_items.append(mitems)
    return {'menu_items':menu_items, 'brand_ids':brand_ids}

def get_brands_retailers_by_query(request, query, tags_retailer, **kwargs):
    retailer_tags = []
    filter_facets = get_facets_by_filter(request, query, ['brand_id', 'tag_id'])
    brand_count = 8
    brand_facets = filter_facets['brand_id']
    brand_facets = brand_facets[:brand_count]
    brand_ids = [ brand_id for brand_id, count in brand_facets]
    tag_facets = filter_facets['tag_id']
    retailer_tag_ids = []
    for tag_id, count in tag_facets:
        if long(tag_id) in tags_retailer:
            retailer_tag_ids.append(tag_id)
    retailer_tags = Tag.objects.filter(id__in=retailer_tag_ids)
    ctxt = {'brand_ids':brand_ids, 'retailer_tags':retailer_tags}
    return ctxt

def get_categorygraph_mapping(request):
    parent_children_map = utils.get_categorygraph_mapping(request.client.client)
    return parent_children_map
