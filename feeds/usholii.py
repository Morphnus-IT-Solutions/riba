import os, sys


os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.holiisettings'

ROOT_FOLDER = os.path.dirname(os.path.realpath(os.path.dirname(__file__)))

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER)

# also add the parent folder
PARENT_FOLDER = os.path.dirname(ROOT_FOLDER)
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

import urllib2
import urllib
from categories.models import *
from accounts.models import *
from catalog.models import Brand, Product, SellerRateChart, Availability, ProductFeatures
from utils import htmlutils
from feeds.models import *
from feeds import feedutils
from feeds.feed import Feed
from django.template.defaultfilters import slugify, striptags
import logging
from django.conf import settings
from decimal import Decimal, ROUND_UP
from django.utils.html import strip_tags
import xlrd
from BeautifulSoup import BeautifulSoup
from datetime import datetime
from pricing.models import PriceList
import math

log = logging.getLogger('feeds')

class USHoliiFeed(Feed):
    config = {
            'ACCOUNT': 'usholii',
            }

    def get_text(self, html):
        s = BeautifulSoup(html)
        return s.getText()


    def get_feature_group(self):
        try:
            get_feature_group = FeatureGroup.objects.using('default').get(name = 'US Holii Specifications', product_type = ProductType.objects.using('default').get(type = 'HandBags'))
        except FeatureGroup.DoesNotExist:
            get_feature_group = FeatureGroup(name = 'US Holii Specifications', product_type = ProductType.objects.using('default').get(type = 'HandBags'))
            get_feature_group.save()


    def save_product_features(self, master, features, sku_type):
        if not features:
            return

        product_type = self.get_mapped_sku_type(sku_type)
        if not product_type:
            return

        for f in features:
            if type(features[f]).__name__ != 'list':
                if not features[f]:
                    continue
                if features[f] and not 'data' in features[f]:
                    continue
                if features[f]['data'] and features[f]['data'] != 'null':
                    try:
                        fm = FeatureMapping.objects.using('default').get(account = self.config['ACCOUNT'], sku_type = product_type, feature_name = f)
                        feature = fm.feature
                    except FeatureMapping.DoesNotExist:
                        try:
                            # See if a feature is already added to the system with given name for the same product type
                            feature = Feature.objects.using('default').get(product_type = product_type, name=f)
                            # If yes, then save this as mapping
                            fm = self.get_or_create_feature_mapping(feature, product_type, f)
                        except Feature.DoesNotExist:
                            feature = Feature(product_type = product_type, name=f, group = self.get_feature_group())
                            if features[f]['type'] == 'char':
                                t = 'text'
                            if features[f]['type'] == 'int':
                                t = 'number'
                            else:
                                t = 'text'
                            feature.type = t
                            feature.save(using='default')
                            self.get_or_create_feature_mapping(feature, product_type, f)

                    try:
                        product_feature = ProductFeatures.objects.using('default').get(product=master,feature=feature)
                    except ProductFeatures.DoesNotExist:
                        product_feature = ProductFeatures(feature=feature,product=master)
                    try:
                        product_feature.data = self.clean_data((features[f]['data']))
                        product_feature.type = features[f].get('feature_type','fixed')
                        if master.type == 'variable':
                            if product_feature.type == 'variable':
                                product_feature.save(using='default')
                        else:
                            product_feature.save(using='default')
                    except Exception, e:
                        log.exception('Error saving feature %s for %s' % (feature.name, master.id))



    _sku_type_map = {}
    def get_mapped_sku_type(self, sku_type):
        try:
            if str(sku_type) in self._sku_type_map:
                return self._sku_type_map.get(str(sku_type))
            mapping = SkuTypeProductTypeMapping.objects.using('default').get(
                    account = self.config['ACCOUNT'],
                    sku_type = sku_type)
        except SkuTypeProductTypeMapping.DoesNotExist:
            mapping = SkuTypeProductTypeMapping(account = self.config['ACCOUNT'], sku_type = sku_type, product_type = ProductType.objects.using('default').get(type = sku_type))
            mapping.save()
        self._sku_type_map[str(sku_type)] = mapping.product_type
        return mapping.product_type


    def parse(self, sync, *args, **kwargs):
        wb = xlrd.open_workbook('/home/apps/tinla/feeds/data/holii/Holii_Data.xls')
        count,heading_map = 0,{}
        s=wb.sheet_by_index(0)

        try:
            get_product_type = ProductType.objects.using('default').get(type = 'HandBags - US')
        except ProductType.DoesNotExist:
            get_product_type = ProductType(type = 'HandBags US')
            get_product_type.save(using='default')

        for col in range(s.ncols):
            heading_map[s.cell(0,col).value.lower()] = col
        products=[]
        
        for row_num in range(1,s.nrows):
            row = s.row(row_num)
            brand = row[heading_map['category 1']].value.strip()
            parent_category = row[heading_map['category 3']].value.strip()
            usholii_client = Client.objects.using('default').get(name = 'US Holii')
            try:
                get_parent_category = Category.objects.using('default').get(name=parent_category,client=usholii_client)
            except Category.DoesNotExist:
                get_parent_category=Category(name = parent_category,client=usholii_client,slug=slugify(parent_category))
                get_parent_category.save(using='default')

            try:
                get_feature_group = FeatureGroup.objects.using('default').get(category = get_parent_category, product_type = get_product_type)
            except FeatureGroup.DoesNotExist:
                get_feature_group = FeatureGroup(category = get_parent_category, product_type = get_product_type, name = parent_category)
                print "get_parent_category ", get_parent_category.id, "get_product_type ", get_product_type.id, "parent_category ", parent_category
                get_feature_group.save(using='default')
                        
            try:
                #this is to create a category with parent = none i.e parent itself is added
                parent_child_map = CategoryGraph.objects.using('default').get(category = get_parent_category,parent=None)
            except CategoryGraph.DoesNotExist:
                parent_child_map = CategoryGraph(category = get_parent_category,parent=None)
                parent_child_map.save(using='default')

            try:
                get_brand = Brand.objects.using('default').get(name = brand)
            except Brand.DoesNotExist:
                get_brand = Brand(name = brand, slug = slugify(brand))
                get_brand.save(using='default')

        rows_visited = []

        for row_num in range(1,s.nrows):
            if row_num in rows_visited:
                continue
            data = dict(cleaned_data=self.get_default_cleaned_data())
            product_variants=[]
            first_row = row_num
            temp_row = s.row(row_num)
            for variants in range(row_num,(row_num+int(temp_row[heading_map['variant']].value))):
                data = dict(cleaned_data=self.get_default_cleaned_data())
                row = s.row(variants)
                if row[heading_map['sku']].ctype in (2,3):
                    article_id = str(int(row[heading_map['sku']].value))
                else:
                    article_id = str(row[heading_map['sku']].value)
                data['cleaned_data']['sku'] = article_id
                data['cleaned_data']['article_id'] = article_id
                data['cleaned_data']['title'] = row[heading_map['product title']].value
                data['cleaned_data']['detailed_desc'] = row[heading_map['product description']].value or '--'
                data['cleaned_data']['brand'] = Brand.objects.using('default').get(name = row[heading_map['category 1']].value)
                data['cleaned_data']['category'] = Category.objects.using('default').get(name = row[heading_map['category 3']].value,client=usholii_client)
                data['cleaned_data']['model'] = ''
                usd_list_price = Decimal(str(row[heading_map['usd']].value)).quantize(Decimal('1.'),rounding=ROUND_UP)
                
                today = datetime.now().day
                #considered same offer and list price for US Holii
                usd_offer_price = usd_list_price
                data['cleaned_data']['shipping_duration']=row[heading_map['shipping duration']].value
                image_urls = []
                stock_status = 'instock'
                status = 'active'
                image_path = '/home/apps/tinla/media/holii/images/pd/%s' % (str(int(row[heading_map['image url']].value)))
                try:
                    listing = os.listdir(image_path)
                    listing = sorted(listing)
                    for infile in listing:
                        if infile != 'Thumbs.db':
                            image_urls.append('http://www.holii.in/media/images/pd/%s/%s' % (str(int(row[heading_map['image url']].value)), infile))
                except Exception, e:
                    print e
                #if not image_urls:
                    stock_status = 'notavailable'
                    status = 'deactive'
                data['cleaned_data']['stock_status'] = stock_status
                data['cleaned_data']['status'] = status
                data['cleaned_data']['image_url']= image_urls
                data['cleaned_data']['availability'] = Availability.objects.using('default').get(id=1)
                data['cleaned_data']['product_type'] = 'variant'
                data['cleaned_data']['sku_type'] = 'HandBags US'
                data['cleaned_data']['usd'] = usd_list_price
                if variants == first_row:
                    data['cleaned_data']['is_default_product'] = True
                else:
                    data['cleaned_data']['is_default_product'] = False
                data['cleaned_data']['features'] = {'Style' : {'feature_type':'fixed','type':'text','data':row[heading_map['category 2']].value}, 'Dimensions (L x H x W)': {'feature_type':'fixed', 'type':'text', 'data':str(row[heading_map['dimensions']].value)+ ' cms'}}
               # price_lists = [] 
               # holii_price_list = None
               # applicable_price_lists = []
               # try:
               #     usholii_price_list = PriceList.objects.using('default').get(name='us holii')
               # except PriceList.DoesNotExist:
               #     holii_price_list = PriceList(name='us holii')
               #     holii_price_list.save(using='default')
               # applicable_price_lists.append(holii_price_list)
               # if usd_list_price != 0: 
               #     price_lists.append({
               #         'price_list':holii_price_list,
               #         'list_price':usd_list_price,
               #         'offer_price':usd_offer_price})

                data['cleaned_data']['list_price'] =  usd_list_price
                data['cleaned_data']['offer_price'] =  usd_offer_price
               # data['cleaned_data']['usd_list_price'] = usd_list_price
               # data['cleaned_data']['price_lists'] = price_lists
               # data['cleaned_data']['applicable_price_lists'] = applicable_price_lists

                product_variants.append(data)
                rows_visited.append(variants)
            products.append(product_variants)
        return products

if __name__ == '__main__':
    feed = USHoliiFeed()
    feed.sync()
