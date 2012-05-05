import os, sys
import socket
socket.setdefaulttimeout(10000)

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

ROOT_FOLDER = os.path.dirname(os.path.realpath(os.path.dirname(__file__)))

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER)

# also add the parent folder
PARENT_FOLDER = os.path.dirname(ROOT_FOLDER)
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

import urllib2
import urllib
from accounts.models import Client
from categories.models import Category,CategoryGraph
from catalog.models import Brand, Product, SellerRateChart, Availability
from utils import htmlutils
from feeds.models import *
from feeds import feedutils
from feeds.feed import Feed
from django.template.defaultfilters import slugify, striptags
import logging
from django.conf import settings
from decimal import Decimal
from django.utils.html import strip_tags
from BeautifulSoup import BeautifulSoup
from pricing.models import *
import simplejson
socket.setdefaulttimeout(10000)

log = logging.getLogger('feeds')

class FutureBazaarFeed(Feed):
    config = {
            'ACCOUNT': 'futurebazaarp',
            'URL': 'http://feeds.futurebazaar.com:%s/catalog/1000038/categories' % settings.FEED_SYNC_PORT_NUMBER,
            'TYPE': 'JSON'
            }

    def save_cat_heirarchy(self,category,parent):
        #print category['display_name'],parent['display_name'] if parent else None
        client = Client.objects.get(id=5)
        try:
            cat = Category.objects.get(ext_id=category['category_id'],client=client)
        except Category.DoesNotExist:
            cat = Category()
            cat.name = category['display_name']
            cat.ext_id = category['category_id']
            cat.slug = slugify(cat.name)
            cat.client = client
            cat.save()
        if parent:
            parent = Category.objects.get(ext_id=parent['category_id'],client=client)
        try:
            cat_graph = CategoryGraph.objects.get(category=cat,parent=parent)
        except CategoryGraph.DoesNotExist:
            cat_graph = CategoryGraph()
            cat_graph.category = cat
            cat_graph.parent = parent
            cat_graph.save()
    
    def get_cat_child(self,category,level,parent):
        s = ''
        for l in range(0,level):
            s += '#'
        self.save_cat_heirarchy(category,parent)
        level += 1
        for child in category['children']:
            self.get_cat_child(child,level,category)

    def get_child(self,category,products,level):
        s = ''
        for l in range(0,level):
            s += '#'

        variants = []
        for product in category['products']:
            has_variants = len(product['skus']) > 1
            blue_print_added = False
            if has_variants:
                log.debug('Found variants for %s' % product['product_id'])
            is_first = True

            # clear variants
            variants = []
            shipping = {}
            if 'percent' in category and category['percent'] != "None":
                # Get shipping rules from category level
                shipping['percent'] = category['percent']
                shipping['min_shipping'] = category['min_shipping']
                shipping['max_shipping'] = category['max_shipping']
            
            if ('percent' in product and product['percent'] != "None")and not shipping:
                # Get product based shipping ruls if not defined at category level
                shipping['percent'] = product['percent']
                shipping['min_shipping'] = product['min_shipping']
                shipping['max_shipping'] = product['max_shipping']
            
            for sku in product['skus']:
                applicable_price_lists = []
                price_lists = []
                if ('percent' in sku and sku['percent'] != "None") and not shipping:
                    # Get sku based shipping rules if not defined at product level
                    shipping['percent'] = sku['percent']
                    shipping['min_shipping'] = sku['min_shipping']
                    shipping['max_shipping'] = sku['max_shipping']

                data = dict(cleaned_data=self.get_default_cleaned_data())

                fields = {'title':'display_name','product_id':'product_id',
                        'description':'long_description'}
                extracted_data = {}
                for key in fields:
                    extracted_data[key] = product[fields[key]]
                extracted_data['category'] = Category.objects.get(client__id=5,ext_id=category['category_id'])
                data['cleaned_data']['title'] = extracted_data['title']
                data['cleaned_data']['category'] = Category.objects.get(client__id=5,ext_id=category['category_id'])
                data['cleaned_data']['external_product_id'] = extracted_data['product_id']
                data['cleaned_data']['model'] = sku.get('model_no','') or data['cleaned_data']['sku']
                data['cleaned_data']['article_id'] = sku.get('article_id','')
                data['cleaned_data']['tags'] = []

                if sku.get('misc3', None) in settings.FB_RETAILERS:
                    tag = {}
                    tag['value'] = sku.get('misc3')
                    tag['type'] = 'retailers'
                    data['cleaned_data']['tags'].append(tag)

                kw = product.get('keywords', [])
                for keyword in kw:
                    tag = {}
                    tag['value'] = keyword
                    tag['type'] = 'keywords'
                    data['cleaned_data']['tags'].append(tag)

                price_dict = {}
                offer_price = Decimal("0.00")
                list_price = Decimal("0.00")

                timed_fb_price_list = []
                fb_timed_price_lists = []
#                if sku.get('future_slots',None):
#                    try:
#                        timed_fb_price_list = PriceList.objects.get(name='Timed FB Price')
#                    except PriceList.DoesNotExist:
#                        timed_fb_price_list = PriceList(name='Timed FB Price')
#                        timed_fb_price_list.save()
#
#                    for future_slot in sku['future_slots']:
#                        fb_timed_price_lists.append({
#                            'price_list' : timed_fb_price_list,
#                            'slot_price' : future_slot['slot_price'],
#                            'start_time' : future_slot['starts_on'],
#                            'end_time' : future_slot['ends_on'],
#                            })
#
#                futurebazaar_price_list = None
#                try:
#                    futurebazaar_price_list = PriceList.objects.get(name='Future Bazaar')
#                except PriceList.DoesNotExist:
#                    futurebazaar_price_list = PriceList(name='Future Bazaar')
#                    futurebazaar_price_list.save()
#
#                applicable_price_lists.append(futurebazaar_price_list)
#
#                futurebazaar_list_price = Decimal("0.00")
#                futurebazaar_offer_price = Decimal("0.00")
#               
#                anonymous_price_list = None
#                try:
#                    anonymous_price_list = PriceList.objects.get(name='Anonymous Futurebazaar Pricelist')
#                except PriceList.DoesNotExist:
#                    anonymous_price_list = PriceList(name='Anonymous Futurebazaar Pricelist')
#                    anonymous_price_list.save()
#                
#                applicable_price_lists.append(anonymous_price_list)
#
#
#                anonymous_futurebazaar_list_price = Decimal("0.00")
#                anonymous_futurebazaar_offer_price = Decimal("0.00")
#                                
#                visa_price_list = None
#                try:
#                    visa_price_list = PriceList.objects.get(name='VISA')
#                except PriceList.DoesNotExist:
#                    visa_price_list = PriceList(name='VISA')
#                    visa_price_list.save()
#
#                applicable_price_lists.append(visa_price_list)
#
#                khojguru_price_list = None
#                try:
#                    khojguru_price_list = PriceList.objects.get(name='Khojguru')
#                except PriceList.DoesNotExist:
#                    khojguru_price_list = PriceList(name='Khojguru')
#                    khojguru_price_list.save()
#
#                applicable_price_lists.append(khojguru_price_list)
#
#                upto75_price_list = None
#                try:
#                    upto75_price_list = PriceList.objects.get(name='Upto75')
#                except PriceList.DoesNotExist:
#                    upto75_price_list = PriceList(name='Upto75')
#                    upto75_price_list.save()
#
#                applicable_price_lists.append(upto75_price_list)
#
#                desidime_price_list = None
#                try:
#                    desidime_price_list = PriceList.objects.get(name='Desidime')
#                except PriceList.DoesNotExist:
#                    desidime_price_list = PriceList(name='Desidime')
#                    desidime_price_list.save()
#
#                applicable_price_lists.append(desidime_price_list)
#
#                visa_list_price = Decimal("0.00")
#                visa_offer_price = Decimal("0.00")
#                 
#                khojguru_list_price = Decimal("0.00")
#                khojguru_offer_price = Decimal("0.00")
#                 
#                upto75_list_price = Decimal("0.00")
#                upto75_offer_price = Decimal("0.00")
#
#                desidime_list_price = Decimal("0.00")
#                desidime_offer_price = Decimal("0.00")

                shipping_charges = Decimal("0.00")
            
                for price in sku['prices']:
                    price_dict[price['price_list']] = price['price']

                # price list priorities. first future bazaar, then anonymous 
                list_price_priority = ['plist3350002', 'plist130002']
                sale_price_priority = ['plist3350003', 'plist130003']

                for price_list in list_price_priority:
                    if price_list in price_dict:
                        list_price = Decimal(price_dict[price_list])
                        break

                for price_list in sale_price_priority:
                    if price_list in price_dict:
                        offer_price = Decimal(price_dict[price_list])
                        break

                if Decimal(list_price) < Decimal(offer_price):
                    list_price = offer_price

                if offer_price == Decimal("0.00"):
                    offer_price = list_price
                
#                futurebazaar_list_price = price_dict.get('plist3350002',None)
#                futurebazaar_offer_price = price_dict.get('plist3350003',None)
#                anonymous_futurebazaar_list_price = price_dict.get('plist130002',None)
#                anonymous_futurebazaar_offer_price = price_dict.get('plist130003',None)
#
#                if anonymous_futurebazaar_offer_price:
#                    if not futurebazaar_offer_price:
#                        # There is no price in FB price list
#                        if sku.get('slot_price', None):
#                            # But there is a slot price. Which should get
#                            # precendence. Resetting anon price to slot price
#                            anonymous_futurebazaar_offer_price = Decimal(sku['slot_price'])
#                    
#                    if anonymous_futurebazaar_list_price:
#                        if Decimal(anonymous_futurebazaar_list_price) < Decimal(anonymous_futurebazaar_offer_price):
#                            anonymous_futurebazaar_list_price = anonymous_futurebazaar_offer_price
#                    else:
#                        anonymous_futurebazaar_list_price = anonymous_futurebazaar_offer_price
#
#                    price_lists.append({
#                        'price_list':anonymous_price_list,
#                        'list_price':anonymous_futurebazaar_list_price,
#                        'offer_price':anonymous_futurebazaar_offer_price})
#
#                if futurebazaar_offer_price:
#                    if sku.get('slot_price', None):
#                        futurebazaar_offer_price = Decimal(sku['slot_price'])
#                    
#                    if futurebazaar_list_price:
#                        if Decimal(futurebazaar_list_price) < Decimal(futurebazaar_offer_price):
#                            if anonymous_futurebazaar_list_price and (Decimal(anonymous_futurebazaar_list_price) >= Decimal(futurebazaar_offer_price)):
#                                futurebazaar_list_price = anonymous_futurebazaar_list_price
#                            else:
#                                futurebazaar_list_price = futurebazaar_offer_price
#                    else:
#                        if anonymous_futurebazaar_list_price and (Decimal(anonymous_futurebazaar_list_price) >= Decimal(futurebazaar_offer_price)):
#                            futurebazaar_list_price = anonymous_futurebazaar_list_price
#                        else:
#                            futurebazaar_list_price = futurebazaar_offer_price
#                       
#                    price_lists.append({
#                        'price_list':futurebazaar_price_list,
#                        'list_price':futurebazaar_list_price,
#                        'offer_price':futurebazaar_offer_price})
#                else:
#                    if anonymous_futurebazaar_list_price and anonymous_futurebazaar_offer_price:
#                        price_lists.append({
#                            'price_list':futurebazaar_price_list,
#                            'list_price':anonymous_futurebazaar_list_price,
#                            'offer_price':anonymous_futurebazaar_offer_price})
#
#                visa_list_price = price_dict.get('plist5400002',None)
#                visa_offer_price = price_dict.get('plist5400003',None)
#                
#                if visa_offer_price:
#                    if anonymous_futurebazaar_list_price:
#                        if (not visa_list_price) or (visa_list_price and (Decimal(visa_list_price) < Decimal(visa_offer_price))):
#                            visa_list_price = anonymous_futurebazaar_list_price
#                    else:
#                        visa_list_price = visa_offer_price
#
#                    price_lists.append({'price_list':visa_price_list,
#                        'list_price':visa_list_price,
#                        'offer_price':visa_offer_price}) 
#                
#                khojguru_list_price = price_dict.get('plist5560002',None)
#                khojguru_offer_price = price_dict.get('plist5560003',None)
#                
#                if khojguru_offer_price:
#                    if anonymous_futurebazaar_list_price:
#                        if (not khojguru_list_price) or (khojguru_list_price and (Decimal(khojguru_list_price) < Decimal(khojguru_offer_price))):
#                            khojguru_list_price = anonymous_futurebazaar_list_price
#                    else:
#                        khojguru_list_price = khojguru_offer_price
#
#                    price_lists.append({'price_list':khojguru_price_list,
#                        'list_price':khojguru_list_price,
#                        'offer_price':khojguru_offer_price}) 
#
#                upto75_list_price = price_dict.get('plist5730002',None)
#                upto75_offer_price = price_dict.get('plist5730003',None)
#                
#                if upto75_offer_price:
#                    if anonymous_futurebazaar_list_price:
#                        if (not upto75_list_price) or (upto75_list_price and (Decimal(upto75_list_price) < Decimal(upto75_offer_price))):
#                            upto75_list_price = anonymous_futurebazaar_list_price
#                    else:
#                        upto75_list_price = upto75_offer_price
#
#                    price_lists.append({'price_list':upto75_price_list,
#                        'list_price':upto75_list_price,
#                        'offer_price':upto75_offer_price})
#
#                desidime_list_price = price_dict.get('plist5750002',None)
#                desidime_offer_price = price_dict.get('plist5750003',None)
#                
#                if desidime_offer_price:
#                    if anonymous_futurebazaar_list_price:
#                        if (not desidime_list_price) or (desidime_list_price and (Decimal(desidime_list_price) < Decimal(desidime_offer_price))):
#                            desidime_list_price = anonymous_futurebazaar_list_price
#                    else:
#                        desidime_list_price = desidime_offer_price
#
#                    price_lists.append({'price_list':desidime_price_list,
#                        'list_price':desidime_list_price,
#                        'offer_price':desidime_offer_price})
               
                # override offer price with slot price if present
                if sku.get('slot_price', None):
                    offer_price = Decimal(sku['slot_price'])

                #Get the min qty to be sold.
                data['cleaned_data']['min_qty'] = sku.get('min_qty',1)
                    
                data['cleaned_data']['sku'] = sku['sku_id']
                data['cleaned_data']['features'] = sku['features']
                #For gift-vouchers, set sku_type = 'gift-voucher'
                if category['category_id'] == '1005608':
                    data['cleaned_data']['sku_type'] = 'gift-voucher'
                else:
                    data['cleaned_data']['sku_type'] = sku['sku_type']
                data['cleaned_data']['is_cod_available'] = product.get('cod_available',False)
                data['cleaned_data']['is_fmemi_available'] = product.get('fmemi_available',False)
                
                is_free_shipping = sku.get('free_shipping',False)
                #Maintaining shipping related info in SellerRateChart
                data['cleaned_data']['is_free_shipping'] = is_free_shipping

                data['cleaned_data']['percent'] = None
                data['cleaned_data']['min_shipping'] = None
                data['cleaned_data']['max_shipping'] = None

                if shipping and not is_free_shipping:
                    # Shipping charge is computed as percentage of offer price
                    # subject to a minumum and maximum
                    shipping_charges = (offer_price * Decimal(shipping['percent']))/Decimal("100.00")
                    if shipping_charges > Decimal(shipping['max_shipping']):
                        # cannot exceeed max_shipping
                        shipping_charges = Decimal(shipping['max_shipping'])
                    if shipping_charges < Decimal(shipping['min_shipping']):
                        # cannot be less than min_shipping either
                        shipping_charges = Decimal(shipping['min_shipping'])

                    data['cleaned_data']['percent'] = shipping['percent']
                    data['cleaned_data']['min_shipping'] = shipping['min_shipping']
                    data['cleaned_data']['max_shipping'] = shipping['max_shipping']

                if sku['sku_id'] == '2588470' or sku['sku_id'] == '2588471':
                    shipping_charges = Decimal('99.00')
                data['cleaned_data']['shipping_charges'] = shipping_charges
                
                if sku['sku_type'] != 2:
                    if not is_first:
                        # Variants are supported only for apparel.
                        # If we found variants for other sku types, then its a manual mistake.
                        # lets skip and continue
                        log.info('Skipping SKU: %s' % sku['sku_id'])
                        continue
                    else:
                        # this is the first product of non apparel sku.
                        # we should not treat it like one of the variants
                        has_variants = False

                if has_variants:
                    for f in sku['features']:
                        if sku['sku_type'] == 2 and f == 'apparel_size':
                            sku['features'][f]['feature_type'] = 'variable'

                if 'brand_name' in sku:
                    data['cleaned_data']['brand'] = self.get_brand_mapping(
                            sku['brand_name']).mapped_to
                else:
                    data['cleaned_data']['brand'] = Brand.objects.get(name='Unknown')

		extra_features = {}
                if 'width' in sku:
                    extra_features['width'] = {'data': sku['width'], 'type': 'char'}
                if 'height' in sku:
                    extra_features['width'] = {'data': sku['height'], 'type': 'char'}
                if 'depth' in sku:
                    extra_features['width'] = {'data': sku['depth'], 'type': 'char'}
                if 'weight' in sku:
                    extra_features['width'] = {'data': sku['weight'], 'type': 'char'}
                if 'color' in sku:
                    extra_features['color'] = {'data': sku['color'], 'type': 'char'}

                data['cleaned_data']['in_the_box'] = sku.get('accessory','')
                if not data['cleaned_data']['in_the_box']:
                    data['cleaned_data']['in_the_box'] = ''

                if 'features' in sku and sku['features']:
                    sku['features'].update(extra_features)
                else:
                    sku['features'] = extra_features

                data['cleaned_data']['video'] = sku.get('misc5','')
                if data['cleaned_data']['video'] == 'null':
                    data['cleaned_data']['video'] = ''
                image_urls = []
                scene7_categories = ['1006166', '1006168', '1006170', '1006172', '1006176', '1006178', '1006180', '1006182', '1006280', '1006282', '1006284', '1006324', '1006326', '1005986', '1005988', '1005990', '1005992', '1005994', '1005996', '1005998', '1006000', '1006002', '1006368', '1006370', '1006004', '1006006', '1006008', '1006010', '1006012', '1006014', '1006016', '1006018', '1006372', '1006374', '1006376', '1006022', '1006024', '1006026', '1006028', '1006030', '1006032', '1006034', '1006036', '1006038', '1006040', '1006042', '1006044', '1006046', '1006048', '1006050', '1006052', '1006054', '1006056', '1006058', '1006060', '1006062', '1006064', '1006378', '1006066', '1006068', '1006070', '1006072', '1006380', '1006382', '1006384', '1006386', '1006388', '1006074', '1006076', '1006078', '1006080', '1006390', '1006392', '1006394', '1005846', '1005848', '1005850', '1005852', '1005854', '1005856', '1006406', '1006408', '1005840', '1005842', '1005844', '1006132', '1006134', '1006136', '1006138', '1006140', '1006142', '1006160', '1006162', '1006164', '1005654', '1005656', '1006418', '1006022', '1006024', '1006026', '1006028', '1006030', '1006032', '1006034', '1006036', '1006038', '1006040', '1006042', '1006044', '1006046', '1006048', '1006050', '1006052', '1006054']
                cid = category['category_id']
                cid = str(cid)

                if category['scene7_flag'] != 0 and cid in scene7_categories:
                    scene7_url = 'http://futurebazaar.scene7.com/is/image/Futurebazaar/%s?wid=%s&hei=%s&fmt=jpeg&qlt=85,0&op_sharpen=0&resMode=sharp2&op_usm=1.0,'
                    image_urls.append(scene7_url % (sku['article_id'],'270', '340'))
                    if product.get('360_degree',False):
                        for i in ['05','09','13']:
                            image_urls.append(scene7_url % (sku['article_id'] + '-' + i,'270', '340'))  
                else:
                    url_keys = ['small_images']
                    for key in url_keys:
                        if key in sku:
                            image_urls.append(sku[key][0])

                data['cleaned_data']['description'] = extracted_data['description'] or '--'
                data['cleaned_data']['list_price'] = list_price
                data['cleaned_data']['offer_price'] = offer_price
                data['cleaned_data']['image_url'] = image_urls

                data['cleaned_data']['short_desc'] = sku.get('description','')
                data['cleaned_data']['detailed_desc'] = sku.get('detailed_desc', '')
                data['cleaned_data']['description'] = sku.get('detailed_desc', '')
                data['cleaned_data']['key_feature'] = sku.get('key_features', '')
                data['cleaned_data']['bundle_skus'] = sku.get('bundle_skus',[])
                
#                data['cleaned_data']['price_lists'] = price_lists
#                data['cleaned_data']['fb_timed_price_lists'] = fb_timed_price_lists
#                data['cleaned_data']['applicable_price_lists'] = applicable_price_lists
                strip_unicode = ['description', 'short_desc', 'detailed_desc']

                for key in strip_unicode:
                    if data['cleaned_data'][key]:
                        data['cleaned_data'][key] = data['cleaned_data'][key].encode('ascii','ignore')

                for key in strip_unicode:
                    if not data['cleaned_data'][key]:
                        data['cleaned_data'][key] = '--'
                

                data['cleaned_data']['availability'] = AvailabilityMap.objects.get(
                        applies_to = 'account',
                        account = self.config['ACCOUNT']).availability

                if not sku.get('inventory',{}).get('is_available', True):
                    data['cleaned_data']['status'] = 'deactive'
                else:
                    data['cleaned_data']['status'] = 'active'

                try:
                    src = SellerRateChart.objects.get(seller=87, sku=sku['sku_id'])
                    if src.is_available_for_sale(None):
                        data['cleaned_data']['stock_status'] = 'instock'
                    else:
                        data['cleaned_data']['stock_status'] = 'outofstock'
                except:
                    data['cleaned_data']['stock_status'] = 'notavailable'

                if has_variants:
                    data['cleaned_data']['product_type'] = 'variant'
                    if is_first:
                        data['cleaned_data']['is_default_product'] = True
                    else:
                        data['cleaned_data']['is_default_product'] = False
                    # add to variants cache
                    variants.append(data)
                    is_last_variant = (len(variants) == len(product['skus']))
                    if variants and is_last_variant:
                        # flush variants
                        log.info('Adding variants %s. skus are' % ", ".join(
                            [d['cleaned_data']['sku'] for d in variants]))
                        products.append(variants)
                else:
                    if sku['sku_id'] in ['2585225','2585226','2585227']:
                        log.info('Adding sku %s to products' % sku['sku_id']) 
                    products.append(data)
                is_first = False

        level += 1
        for child in category['children']:
            self.get_child(child,products,level)

        self.download_images = False        
        return products

    def parse(self, sync, *args, **kwargs):
        # get the file and save it
        path = '%s/%s-%d-categories.%s' % (settings.FEEDS_ROOT,
                self.config['ACCOUNT'],
                sync.id,
                self.config['TYPE'].lower())

        urllib.urlretrieve(self.config['URL'], path)
        file = open(path)
        json_obj = simplejson.loads(file.read())
        file.close()
        product_array = []
        for category in json_obj['categories']:
            #if category['category_id'] in settings.BLACKLIST_CATEGORIES:
            #    continue
            log.info('Syncing %s' % category['display_name'])
            self.get_cat_child(category,1,None)
            cpath = path.replace('categories', category['category_id'])
            from datetime import datetime
            urllib.urlretrieve(self.config['URL'].replace('categories', 
                'category/%s/' % category['category_id']), cpath)
            f = open(cpath)
            json = simplejson.loads(f.read())
            f.close()
            start = len(product_array)
            products = self.get_child(json, product_array,1)
            end = len(product_array)
            log.info('Found %s in %s' % ((end-start) , category['display_name']))
        return product_array


if __name__ == '__main__':
    feed = FutureBazaarFeed(False, False, False)
    feed.sync()
