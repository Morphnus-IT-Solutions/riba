import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.nuezonesettings'

ROOT_FOLDER = os.path.dirname(os.path.realpath(os.path.dirname(__file__)))
ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

import urllib2
import urllib
from django.conf import settings
from categories.models import *
from accounts.models import *
from catalog.models import Brand, Product, SellerRateChart, Availability, ProductFeatures, Inventory
from pricing.models import PriceList
from utils import htmlutils
from feeds.models import *
from feeds import feedutils
from feeds.feed import Feed
from django.template.defaultfilters import slugify, striptags
import logging
from django.conf import settings
from decimal import Decimal
from django.utils.html import strip_tags
from pricing.models import Price
from datetime import datetime
import xlrd

log = logging.getLogger('feeds')


class EzoneonlineFeed(Feed):
    config = {
            'ACCOUNT': 'nuezone',
            }

    def __init__(self):
        self.only_add = True

    # -------------
    # get category
    # -------------
    def get_category(self, category_name, client):
        try:
            category = Category.objects.get(name = category_name, client = client)
        except Category.DoesNotExist:
            category = Category(name = category_name, client = client, slug = slugify(category_name))
            category.save()
        return category


    # ---------
    # get brand
    # ----------
    def get_brand(self, name):
        try:
            br = Brand.objects.get(name = name)
        except Brand.DoesNotExist:
            br = Brand(name = name, slug = slugify(name))
            br.save()
        return br


    # -----------------
    # get product type
    # -----------------
    def get_product_type(self, client, name):
        try:
            p = ProductType.objects.get(client = client, type = name)
        except ProductType.DoesNotExist:
            p = ProductType(type = name, client = client)
            p.save()
        return p

    # ------------------
    # get features dict
    # ------------------
    def get_features_dict(self, row, heading_map, product_type):
        feature_dict = {}
        features = Feature.objects.filter(product_type = product_type)
        for f in features:
            if heading_map.get(f.name.strip().lower()):
                feature_dict[f.name] = {'feature_type':'fixed', 'type':f.type or 'text', 'data':row[heading_map[f.name.lower()]].value}
        return feature_dict


    def parse(self, sync, *args, **kwargs):
        wb = xlrd.open_workbook(settings.HOME_PATH+'tinla/feeds/data/ezone/ezoneonline_data.xls')
        #heading_map = {}
        #s = wb.sheet_by_index(0)
        client = Client.objects.get(id=12)
        products=[]
        count = 0

        for w in wb.sheet_names():
            heading_map = {}
            s = wb.sheet_by_name(w)
            for col in range(s.ncols):
                heading_map[s.cell(0,col).value.lower().encode('ascii','ignore')] = col

            #product_type = self.get_product_type(client, w)



            product_variants = []
            prev_parent_variant_sku = ''
            print "************************* %s ********************************" % w
            for row_num in range(1,s.nrows):
                row = s.row(row_num)

                product_type = None
                category = self.get_category(row[heading_map['leaf category']].value.strip(), client = client)
                try:
                    product_type = CategoryProducttypeMapping.objects.get(category=category).product_type
                except CategoryProducttypeMapping.DoesNotExist:
                    product_type = self.get_product_type(client, w)

                data = dict(cleaned_data=self.get_default_cleaned_data())
                if row[heading_map['articleid']].ctype in (2,3):
                    article_id = str(int(row[heading_map['articleid']].value))
                else:
                    article_id =  str(row[heading_map['articleid']].value)
                
                # Check 
                # 1. Variant exists
                # 2. If yes then whether it is new or same as old one
                is_variant, new_variant, parent_variant_sku = False, True, ''
                if row[heading_map.get('variant sku', '')] and row[heading_map['variant sku']].value:
                    if row[heading_map['variant sku']].ctype in (2,3):
                        parent_variant_sku = str(int(row[heading_map['variant sku']].value))
                    else:
                        parent_variant_sku =  str(row[heading_map['variant sku']].value)

                    if parent_variant_sku and prev_parent_variant_sku == parent_variant_sku:
                        new_variant = False
                    is_variant = True

                #print "is variant ::::", is_variant
                #print "new_variant ::::", new_variant
                #print "current sku ::::", article_id
                #print "parent_variant_sku ::::", parent_variant_sku
                #print "prev_parent_variant_sku ::::", prev_parent_variant_sku
                data['cleaned_data']['sku'] = article_id
                data['cleaned_data']['article_id'] = article_id
                data['cleaned_data']['title'] = row[heading_map['product name']].value
                data['cleaned_data']['detailed_desc'] = row[heading_map['product description']].value or '--'
                data['cleaned_data']['brand'] = self.get_brand(row[heading_map['brand']].value.strip())
                data['cleaned_data']['model'] = ''
                data['cleaned_data']['category'] = category#self.get_category(row[heading_map['leaf category']].value.strip(), client = client)
                data['cleaned_data']['sku_type'] = product_type.type
                try:
                    data['cleaned_data']['key_feature'] = row[heading_map['key features']].value
                except:
                    pass
                data['cleaned_data']['is_preferred'] = True
                image_urls = []
                image_path = settings.HOME_PATH+'/tinla/media/nuezone/images/pd/%s' % (article_id)
                stock_status = 'notavailable'
                status = 'deactive'
                try:
                    listing = os.listdir(image_path)
                    listing = sorted(listing)
                    for infile in listing:
                        if infile != 'Thumbs.db':
                            image_urls.append(settings.CLIENT_DOMAIN+'media/images/pd/%s/%s' % (article_id, infile))
                    rate_chart = '' 
                    try:
                        rate_chart = SellerRateChart.objects.get(seller__client=client, article_id=article_id)
                    except Exception, e:
                        log.info(repr(e))
                    
                    if rate_chart:
                        try:
                            inventory = Inventory.objects.get(rate_chart=rate_chart)
                        except Exception, e:
                            log.info(repr(e))

                        prices = Price.objects.filter(
                            rate_chart=rate_chart).exclude(
                            Q(price_type='timed', start_time__gte=datetime.now())| 
                            Q(price_type='timed', end_time__lte=datetime.now())
                            )
                        if prices and inventory.stock > Decimal('0'):
                            stock_status = 'instock'
                            
                    status = 'active'
                except Exception, e:
                    print "No images found for %s" % (article_id)
                    print e
                    count += 1
                    print count
                data['cleaned_data']['image_url']= image_urls
                data['cleaned_data']['stock_status'] = stock_status
                data['cleaned_data']['status'] = status
                data['cleaned_data']['availability'] = Availability.objects.get(id=1)
                list_price = Decimal('0')#Decimal(str(row[heading_map['mrp']].value))
                offer_price = Decimal('0')#Decimal(str(row[heading_map['sale price']].value))

                if list_price < offer_price:
                    list_price = offer_price

                if offer_price == Decimal("0.00"):
                    offer_price = list_price
                
                data['cleaned_data']['list_price'] = list_price
                data['cleaned_data']['offer_price'] = offer_price
                data['cleaned_data']['features'] = self.get_features_dict(row, heading_map, product_type)

                if is_variant:
                    if parent_variant_sku == article_id:
                        data['cleaned_data']['is_default_product'] = True
                    else:
                        data['cleaned_data']['is_default_product'] = False
                    data['cleaned_data']['product_type'] = 'variant'

                    if new_variant:
                        #print len(product_variants)
                        if product_variants:
                            products.append(product_variants)
                            product_variants = []
                    product_variants.append(data)
                    prev_parent_variant_sku = parent_variant_sku
                else:
                    products.append(data)
        return products


if __name__ == '__main__':
    feed = EzoneonlineFeed()
    feed.sync()
