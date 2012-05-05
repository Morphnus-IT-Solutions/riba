import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.htsettings'

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
from decimal import Decimal
from django.utils.html import strip_tags
import xlrd

log = logging.getLogger('feeds')


class HomeTownFeed(Feed):
    config = {
            'ACCOUNT': 'HomeTown',
            }

#    def create_master_product(self, data, sync, product=None, is_update=False):
#        if not product:
#            product = Product()
#        product.title = data['cleaned_data']['title']
#        product.description = data['cleaned_data']['detailed_desc'] or data['cleaned_data']['description']
#        product.brand = data['cleaned_data']['brand']
#        product.category = data['cleaned_data']['category']
#        product.slug = slugify(product.title)[:150]
#        product.model = data['cleaned_data']['model']
#        product.moderate = True
#        product.currency = data['cleaned_data'].get('currency','inr')
#        product.type = data['cleaned_data'].get('product_type','normal')
#        product.product_type = self.get_mapped_sku_type(data['cleaned_data'].get('sku_type',''))
#        if data['cleaned_data'].get('video',''):
#            product.video_embed = data['cleaned_data']['video']
#        if data['cleaned_data']['status'] in ['active','deactive','deleted']:
#            product.status = data['cleaned_data']['status']
#        product.save()
#        product.productimage_set.all().delete()
#
#        if self.download_images:
#            # download the image
#            for url in data['cleaned_data']['image_url']:
#                try:
#                    feedutils.attach_image_to_product(product,url)
#                except Exception, e:
#                    product.status = 'deactive'
#                    log.exception(
#                            'Error adding image to product %s from %s' % ( 
#                                product.id, data['cleaned_data']['image_url'],
#                                ))
#        else:
#            #product.productimage_set.all().delete()
#            # Dont download images, we will serve them using their original urls
#            for url in data['cleaned_data']['image_url']:
#                pi = ProductImage(product=product, type='external')
#                if 'scene7' in url:
#                    pi.type = 'scene7'
#                pi.name = product.title[:25]
#                pi.url = url
#                pi.save()
#        if sync and not is_update:
#            sync.new_masters += 1
#            sync.save()
#            sync_product = SyncEventProductMapping(sync_event=sync,
#                    product=product, action='added')
#            sync_product.sku = data['cleaned_data']['sku']
#            sync_product.save()
#
#        if sync and is_update:
#            sync.edits += 1
#            sync.save()
#            sync_product = SyncEventProductMapping(sync_event=sync,
#                    product=product, action='edited')
#            sync_product.sku = data['cleaned_data']['sku']
#            sync_product.save()
#
#        return product
#
#
#    def save_product_features(self, master, features, sku_type):
#        if not features:
#            return
#
#        product_type = self.get_mapped_sku_type(sku_type)
#        if not product_type:
#            return
#
#        for f in features:
#            if type(features[f]).__name__ != 'list':
#                if not features[f]:
#                    continue
#                if features[f] and not 'data' in features[f]:
#                    continue
#                if features[f]['data'] and features[f]['data'] != 'null':
#                    try:
#                        fm = FeatureMapping.objects.get(account = self.config['ACCOUNT'], sku_type = product_type, feature_name = f)
#                        feature = fm.feature
#                    except FeatureMapping.DoesNotExist:
#                        try:
#                            # See if a feature is already added to the system with given name for the same product type
#                            feature = Feature.objects.get(product_type = product_type, name=f, group = self.get_feature_group())
#                            # If yes, then save this as mapping
#                            fm = self.get_or_create_feature_mapping(feature, product_type, f)
#                        except Feature.DoesNotExist:
#                            feature = Feature(product_type = product_type, name=f, group = self.get_feature_group())
#                            if features[f]['type'] == 'char':
#                                t = 'text'
#                            if features[f]['type'] == 'int':
#                                t = 'number'
#                            else:
#                                t = 'text'
#                            feature.type = t
#                            feature.save()
#                            self.get_or_create_feature_mapping(feature, product_type, f)
#
#                    try:
#                        product_feature = ProductFeatures.objects.get(product=master,feature=feature)
#                    except ProductFeatures.DoesNotExist:
#                        product_feature = ProductFeatures(feature=feature,product=master)
#                    try:
#                        product_feature.data = self.clean_data((features[f]['data']))
#                        product_feature.type = features[f].get('feature_type','fixed')
#                        if master.type == 'variable':
#                            if product_feature.type == 'variable':
#                                product_feature.save()
#                        else:
#                            product_feature.save()
#                    except Exception, e:
#                        log.exception('Error saving feature %s for %s' % (feature.name, master.id))
#
#
#    _sku_type_map = {}
#    def get_mapped_sku_type(self, sku_type):
#        try:
#            if str(sku_type) in self._sku_type_map:
#                return self._sku_type_map.get(str(sku_type))
#            mapping = SkuTypeProductTypeMapping.objects.get(
#                    account = self.config['ACCOUNT'],
#                    sku_type = sku_type)
#        except SkuTypeProductTypeMapping.DoesNotExist:
#            get_product_type = self.create_product_type(ptype = sku_type)
#            mapping = SkuTypeProductTypeMapping(account = self.config['ACCOUNT'], sku_type = sku_type, product_type = get_product_type)
#            mapping.save()
#        self._sku_type_map[str(sku_type)] = mapping.product_type
#        return mapping.product_type
#
#
#    # ------------------
#    # get feature group
#    # ------------------
#    def get_feature_group(self):
#        try:
#            feature_group = FeatureGroup.objects.get(name = 'HomeTown Specification')
#        except FeatureGroup.DoesNotExist:
#            feature_group = FeatureGroup(name = 'HomeTown Specification')
#            feature_group.save()
#        return feature_group
#
#    # ----------------------
#    # create category graph
#    # ----------------------
#    def create_category_graph(self, category, parent_category):
#        try:
#            category_graph = CategoryGraph.objects.get(category = category, parent = parent_category)
#        except CategoryGraph.DoesNotExist:
#            category_graph = CategoryGraph(category = category, parent = parent_category)
#            category_graph.save()


    # ----------------
    # create category
    # ----------------
    def create_category(self, client, category_name, parent_category):
        try:
            category = Category.objects.using('default').get(name = category_name, client = client)
        except Category.DoesNotExist:
            category = Category(name = category_name, client = client, slug = slugify(category_name))
            category.save(using='default')
        #self.create_category_graph(category, parent_category)
        return category


    # -------------
    # create brand
    # -------------
    def create_brand(self, brand_name):
        try:
            brand = Brand.objects.using('default').get(name = brand_name)
        except Brand.DoesNotExist:
            brand = Brand(name = brand_name, slug = slugify(brand_name))
            brand.save(using='default')
        return brand


    # --------------------
    # create product type
    # --------------------
    def create_product_type(self, client, ptype):
        try:
            product_type = ProductType.objects.using('default').get(type = ptype, client = client)
        except ProductType.DoesNotExist:
            product_type = ProductType(type = ptype, client = client)
            product_type.save(using='default')
        return product_type


    # ---------------
    # create masters
    # ---------------
    def create_masters(self, row, heading_map, client):
        # create parent category
        parent_category = self.create_category(client, category_name = row[heading_map['category']].value.strip(), parent_category = None)
        # create sub category
        sub_category = self.create_category(client, category_name = row[heading_map['sub category']].value.strip(), parent_category = parent_category)
        # create sub sub category
        sub_sub_category = self.create_category(client, category_name = row[heading_map['sub sub category']].value.strip(), parent_category = sub_category)
        # create product type
        product_type = self.create_product_type(client, ptype = row[heading_map['category']].value.strip())
        # create brand
        if row[heading_map['brand']]:
            brand = self.create_brand(brand_name = row[heading_map['brand']].value.strip())

    # ------------------
    # get features dict
    # ------------------
    def get_features_dict(self, row, heading_map, product_type):
        feature_dict = {}
        features = Feature.objects.filter(product_type = product_type)
        for f in features:
            if heading_map.get(f.name.lower()):
                feature_dict[f.name] = {'feature_type':'fixed', 'type':f.type or 'text', 'data':row[heading_map[f.name.lower()]].value}
        return feature_dict



    def parse(self, sync, *args, **kwargs):
        wb = xlrd.open_workbook(settings.HOME_PATH+'tinla/feeds/data/hometown/hometowndata.xls')
        #s = wb.sheet_by_index(0)
        products = []
        client = Client.objects.using('default').get(name = 'HomeTown')
	for w in wb.sheet_names():
            s = wb.sheet_by_name(w)
            count,heading_map = 0,{}
            for col in range(s.ncols):
                heading_map[s.cell(0,col).value.lower().encode('ascii','ignore')] = col
            print "************************ %s ***********************" % w 
            for row_num in range(1,s.nrows):
                row = s.row(row_num)
                self.create_masters(row, heading_map, client)
                data = dict(cleaned_data=self.get_default_cleaned_data())
                if row[heading_map['article code']].ctype in (2,3):
                    article_id = str(int(row[heading_map['article code']].value))
                else:
                    article_id = str(row[heading_map['article code']].value)

                data['cleaned_data']['sku'] = article_id
                data['cleaned_data']['title'] = row[heading_map['product display name']].value
                data['cleaned_data']['detailed_desc'] = row[heading_map['product details long']].value
                data['cleaned_data']['description'] = None
                data['cleaned_data']['short_desc'] = row[heading_map['product details short']].value
                if row[heading_map['brand']]:
                    data['cleaned_data']['brand'] = Brand.objects.get(name = row[heading_map['brand']].value.strip())
                data['cleaned_data']['model'] = ''
                if row[heading_map['sub sub category']].value.strip():
                    data['cleaned_data']['category'] = Category.objects.using('default').get(name = row[heading_map['sub sub category']].value.strip(), client = client)
                else:
                    data['cleaned_data']['category'] = Category.objects.using('default').get(name = row[heading_map['sub category']].value.strip(), client = client)
                if row[heading_map['sub sub category']].value.strip():
                    data['cleaned_data']['sku_type'] = row[heading_map['sub sub category']].value.strip()
                else:
                    data['cleaned_data']['sku_type'] = row[heading_map['sub category']].value.strip()
                list_price = Decimal(str(row[heading_map['mrp']].value))
                data['cleaned_data']['list_price'] =  list_price
                offer_price = row[heading_map['offer price']].value
                if offer_price:
                    offer_price = Decimal(str(offer_price))
                else:
                    offer_price = list_price
                data['cleaned_data']['offer_price'] = offer_price
                data['cleaned_data']['is_preferred'] = True
                image_urls = []
                stock_status = 'instock'
                status = 'active'
                image_path = settings.HOME_PATH+'tinla/media/hometown_v2/images/pd/%s' % (article_id)
                try:
                    listing = os.listdir(image_path)
                    listing = sorted(listing)
                    for infile in listing:
                        if infile != 'Thumbs.db':
                            image_urls.append('http://www.hometown.in/media/images/pd/%s/%s' % (article_id, infile))
                except Exception, e:
                    stock_status = 'notavailable'
                    status = 'deactive'
                    print "error adding images for ",  article_id
                data['cleaned_data']['image_url']= image_urls
                data['cleaned_data']['stock_status'] = stock_status
                data['cleaned_data']['status'] = status
                data['cleaned_data']['availability'] = Availability.objects.get(id=1)
                product_type = None
                try:
                    if row[heading_map['sub sub category']].value.strip():
                        product_type = ProductType.objects.using('default').get(type = row[heading_map['sub sub category']].value.strip(), client = client)
                        data['cleaned_data']['features'] = self.get_features_dict(row, heading_map, product_type)
                    else:
                        product_type = ProductType.objects.using('default').get(type = row[heading_map['sub category']].value.strip(), client = client)
                        data['cleaned_data']['features'] = self.get_features_dict(row, heading_map, product_type)
                except ProductType.DoesNotExist:
                    print "No Product type for object"
                #data['cleaned_data']['warranty'] = row[heading_map['warranty']].value
                products.append(data)
        return products


if __name__ == '__main__':
    feed = HomeTownFeed()
    feed.sync()
