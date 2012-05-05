import os, sys

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
<<<<<<< HEAD
import os
=======
>>>>>>> staging

log = logging.getLogger('feeds')

class BigbazaarOnlineFeed(Feed):
    config = {
            'ACCOUNT': 'bigbazaar',
            'URL': 'http://feeds.futurebazaar.com:8080/catalog/1000026/categories',
            'TYPE': 'JSON'
            }

    def save_cat_heirarchy(self,category,parent):
        client = Client.objects.get(name='bigbazaar')
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
            if variants:
                # flush variants
                products.append(variants)

            # clear variants
            variants = []
            shipping = {}
            if 'percent' in category and category['percent'] != "None":
                # Get shipping rules from category level
                shipping['percent'] = category['percent']
                shipping['min_shipping'] = category['min_shipping']
                shipping['max_shipping'] = category['max_shipping']
            if ('percent' in product and product['percent'] != "None"):
                # Get product based shipping ruls if not defined at category level
                shipping['percent'] = product['percent']
                shipping['min_shipping'] = product['min_shipping']
                shipping['max_shipping'] = product['max_shipping']
            for sku in product['skus']:
                applicable_price_lists = []
                price_lists = []
                if ('percent' in sku and sku['percent'] != "None"):
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
                extracted_data['category'] = Category.objects.get(client__name='bigbazaar',ext_id=category['category_id'])
                data['cleaned_data']['title'] = extracted_data['title']
                data['cleaned_data']['category'] = Category.objects.get(client__name='bigbazaar',ext_id=category['category_id'])
                data['cleaned_data']['external_product_id'] = extracted_data['product_id']
                data['cleaned_data']['model'] = sku.get('model_no','') or data['cleaned_data']['sku']
                data['cleaned_data']['article_id'] = sku.get('article_id','')

                price_dict = {}
                offer_price = Decimal("0.00")
                list_price = Decimal("0.00")
                shipping_charges = Decimal("0.00")

                for price in sku['prices']:
                    price_dict[price['price_list']] = price['price']

                # price list priorities. first bigbazaar, then anonymous 
                list_price_priority = ['plist130002', 'plist130002']
                sale_price_priority = ['plist130003', 'plist130003']

                for price_list in list_price_priority:
                    if price_list in price_dict:
                        list_price = Decimal(price_dict[price_list])

                for price_list in sale_price_priority:
                    if price_list in price_dict:
                        offer_price = Decimal(price_dict[price_list])

                if Decimal(list_price) < Decimal(offer_price):
                    list_price = offer_price

                if offer_price == Decimal("0.00"):
                    offer_price = list_price

                # override offer price with slot price if present
                if sku.get('slot_price', None):
                    offer_price = Decimal(sku['slot_price'])

                #Populating Pricing.price table for bigbazaar pricelists
                #First, Bigbazaar prices
                bigbazaar_price_list = None

                bigbazaar_list_price = price_dict.get('plist130002',None)
                bigbazaar_offer_price = price_dict.get('plist130003',None)
                bigbazaar_anonymous_list_price = price_dict.get('plist130002',None)
                bigbazaar_anonymous_offer_price = price_dict.get('plist130003',None)

                try:
                    bigbazaar_price_list = PriceList.objects.get(name='Bigbazaar')
                except PriceList.DoesNotExist:
                    bigbazaar_price_list = PriceList(name='Bigbazaar')
                    bigbazaar_price_list.save()

                applicable_price_lists.append(bigbazaar_price_list)

                if bigbazaar_offer_price:
                    if sku.get('slot_price', None):
                        bigbazaar_offer_price = Decimal(sku['slot_price'])

                    if bigbazaar_list_price:
                        if Decimal(bigbazaar_list_price) < Decimal(bigbazaar_offer_price):
                            if bigbazaar_anonymous_list_price and (Decimal(bigbazaar_anonymous_list_price) >= Decimal(bigbazaar_offer_price)):
                                bigbazaar_list_price = bigbazaar_anonymous_list_price
                            else:
                                bigbazaar_list_price = bigbazaar_offer_price
                    else:
                        if bigbazaar_anonymous_list_price and (Decimal(bigbazaar_anonymous_list_price) >= Decimal(bigbazaar_offer_price)):
                            bigbazaar_list_price = bigbazaar_anonymous_list_price
                        else:
                            bigbazaar_list_price = bigbazaar_offer_price
                    
                    price_lists.append({
                        'price_list':bigbazaar_price_list,
                        'list_price':bigbazaar_list_price,
                        'offer_price':bigbazaar_offer_price})
                
                #Second, Anonymous Bigbazaar prices
                bigbazaar_anonymous_price_list = None

                try:
                    bigbazaar_anonymous_price_list = PriceList.objects.get(name='Anonymous Bigbazaar Pricelist')
                except PriceList.DoesNotExist:
                    bigbazaar_anonymous_price_list = PriceList(name='Anonymous Bigbazaar Pricelist')
                    bigbazaar_anonymous_price_list.save()

                applicable_price_lists.append(bigbazaar_anonymous_price_list)

                if bigbazaar_anonymous_offer_price:
                    if not bigbazaar_offer_price:
                        if sku.get('slot_price', None):
                            bigbazaar_anonymous_offer_price = Decimal(sku['slot_price'])

                    if bigbazaar_anonymous_list_price:
                        if Decimal(bigbazaar_anonymous_list_price) < Decimal(bigbazaar_anonymous_offer_price):
                            bigbazaar_anonymous_list_price = bigbazaar_anonymous_offer_price
                    else:
                        bigbazaar_anonymous_list_price = bigbazaar_anonymous_offer_price
                    
                    price_lists.append({
                        'price_list':bigbazaar_anonymous_price_list,
                        'list_price':bigbazaar_anonymous_list_price,
                        'offer_price':bigbazaar_anonymous_offer_price})
                
                data['cleaned_data']['price_lists'] = price_lists
                data['cleaned_data']['applicable_price_lists'] = applicable_price_lists

                data['cleaned_data']['sku'] = sku['sku_id']
                data['cleaned_data']['features'] = sku['features']
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
                    if (shipping['max_shipping'] and shipping['max_shipping'] != 'None') and shipping_charges > Decimal(shipping['max_shipping']):
                        # cannot exceeed max_shipping
                        shipping_charges = Decimal(shipping['max_shipping'])
                    if (shipping['min_shipping'] and shipping['min_shipping'] != 'None') and shipping_charges < Decimal(shipping['min_shipping']):
                        # cannot be less than min_shipping either
                        shipping_charges = Decimal(shipping['min_shipping'])

                    data['cleaned_data']['percent'] = shipping['percent']
                    data['cleaned_data']['min_shipping'] = shipping['min_shipping']
                    data['cleaned_data']['max_shipping'] = shipping['max_shipping']

                data['cleaned_data']['shipping_charges'] = shipping_charges
                
                    
                if sku['sku_type'] != 2:
                    if not is_first:
                        # Variants are supported only for apparel.
                        # If we found variants for other sku types, then its a manual mistake.
                        # lets skip and continue
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
                    dat['cleaned_data']['video'] = ''
                image_urls = []
                cid = category['category_id']
                cid = str(cid)

                #if category['scene7_flag'] != 0:
                #    scene7_url = 'http://futurebazaar.scene7.com/is/image/Futurebazaar/%s?wid=%s&hei=%s&fmt=jpeg&qlt=85,0&op_sharpen=0&resMode=sharp2&op_usm=1.0,'
                #    image_urls.append(scene7_url % (sku['article_id'],'270', '340'))
                #    if product.get('360_degree',False):
                #        for i in ['05','09','13']:
                #            image_urls.append(scene7_url % (sku['article_id'] + '-' + i,'270', '340'))  
                #else:
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
                    data['cleaned_data']['stock_status'] = 'outofstock'
                else:
                    data['cleaned_data']['status'] = 'active'

                if has_variants:
                    data['cleaned_data']['product_type'] = 'variant'
                    if is_first:
                        data['cleaned_data']['is_default_product'] = True
                    else:
                        data['cleaned_data']['is_default_product'] = False
                    # add to variants cache
                    variants.append(data)
                else:
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
            if category['category_id'] in settings.BLACKLIST_CATEGORIES:
                continue
            log.info('Syncing %s' % category['display_name'])
            self.get_cat_child(category,1,None)
            cpath = path.replace('categories', category['category_id'])
            urllib.urlretrieve(self.config['URL'].replace('categories', 
                'category/%s/' % category['category_id']), cpath)
            f = open(cpath)
            json = simplejson.loads(f.read())
            f.close()
            start = len(product_array)
            products = self.get_child(json, product_array,1)
            end = len(product_array)
            log.info('Found %s in %s' % ((end-start) , category['display_name']))
        log.info('Ready for indexing...')
        return product_array


if __name__ == '__main__':
    feed = BigbazaarOnlineFeed(False, False, False)
    feed.sync()
