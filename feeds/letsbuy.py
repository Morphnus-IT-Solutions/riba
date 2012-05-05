import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

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
from lxml import etree
from categories.models import Category
from catalog.models import Brand, Product, SellerRateChart, Availability
from utils import htmlutils
from feeds.models import *
from feeds import feedutils
from feeds.feed import Feed
from django.template.defaultfilters import slugify, striptags
import logging
from django.conf import settings
from decimal import Decimal

log = logging.getLogger('feeds')

class LetsBuyFeed(Feed):
    config = {
            'ACCOUNT': 'letsbuy',
            'URL': 'http://www.letsbuy.com/xmlchaupaati.php',
            'TYPE': 'XML'
            }

    def get_model_name(self, sku):
        try:
            sku_info = SKUInfo.objects.get(account=self.config['ACCOUNT'],
                    sku=sku)
            if not sku_info.model:
                model = feedutils.get_letsbuy_model_number(sku)
                sku_info.model = model
                sku_info.save()
                return model
            else:
                return sku_info.model
        except SKUInfo.DoesNotExist:
            model = feedutils.get_letsbuy_model_number(sku)
            sku_info = SKUInfo(account=self.config['ACCOUNT'],
                    model=model,sku=sku)
            sku_info.save()
            return model


    def parse(self, sync, *args, **kwargs):
        file = self.config['URL']
        if '_local_' in kwargs:
            file = 'feeds/data/%s.%s' % (self.config['ACCOUNT'],
                    self.config['TYPE'].lower())
        else:
            # get the file and save it
            path = '%s/%s-%d.%s' % (settings.FEEDS_ROOT,
                    self.config['ACCOUNT'],
                    sync.id,
                    self.config['TYPE'].lower())

            urllib.urlretrieve(self.config['URL'], path)
            file = path

        xmldoc = etree.parse(file)
        products = []
        for product in xmldoc.xpath("/root/products"):
            data = dict(cleaned_data=self.get_default_cleaned_data())
            no_html_fields = ['Brand_Name','categories_name']
            # single value fields
            single_value_fields = ['SKU','Title','Features','Specification',
                    'Overview','Brand_Name','Image_URL','categories_name',
                    'Warranty_Period','Offer_Price','MRP','Shipping_Duration']
            for field in single_value_fields:
                data[field] = ''
                node = product.xpath(field)
                if node and len(node) > 0:
                    data[field] = node[0].text
                    if field in no_html_fields:
                        data[field] = htmlutils.to_text(node[0].text)

            # ignore blaclists
            if self.is_blacklisted_brand(data['Brand_Name']): continue
            if self.is_blacklisted_sku(data['SKU']): continue
            if self.is_blacklisted_category(data['categories_name']): continue

            # create cleaned data 
            data['cleaned_data']['brand_mapping'] = self.get_brand_mapping(data['Brand_Name'])
            data['cleaned_data']['category_mapping'] = self.get_category_mapping(data['categories_name'])

            data['cleaned_data']['sku'] = data['SKU']
            data['cleaned_data']['brand'] = self.get_brand_mapping(data['Brand_Name']).mapped_to
            data['cleaned_data']['category'] = self.get_category_mapping(data['categories_name']).mapped_to
            data['cleaned_data']['model'] = self.get_model_name(data['SKU'])
            data['cleaned_data']['title'] = data['Title']
            data['cleaned_data']['image_url'] = [data['Image_URL']]
            data['cleaned_data']['shipping_duration'] = data['Shipping_Duration'] or '8-10 Working Days'
            data['cleaned_data']['offer_price'] = Decimal(data['Offer_Price'])
            if data['MRP'].replace('.','').replace('0',''):
                data['cleaned_data']['list_price'] = Decimal(data['MRP'])
            else:
                data['cleaned_data']['list_price']= Decimal(data['Offer_Price'])
            data['cleaned_data']['description'] = 'Overview\n\n%sFeatures\n\n%sSpecs\n\n%s' % (
                    striptags(data['Overview']), striptags(data['Features']), striptags(data['Specification']))
            data['cleaned_data']['availability'] = AvailabilityMap.objects.get(
                    applies_to = 'account',
                    account = self.config['ACCOUNT']).availability
            products.append(data)

        return products


if __name__ == '__main__':
    feed = LetsBuyFeed()
    feed.sync()
    #feed.sync(**{'_local_':True})
