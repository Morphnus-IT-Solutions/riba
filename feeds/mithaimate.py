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

class MithaiMateFeed(Feed):
    config = {
            'ACCOUNT': 'mithaimate',
            'URL': 'http://www.mithaimate.com/productxml.php',
            'TYPE': 'XML'
            }
    


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
        print xmldoc.xpath("/products/product")
        for product in xmldoc.xpath("/products/product"):
            print '###here'
            data = dict(cleaned_data=self.get_default_cleaned_data())
            # single value fields
            single_value_fields = ['id','name','description','price',
                    'weight','categoryid','image']
            for field in single_value_fields:
                data[field] = ''
                node = product.xpath(field)
                if node and len(node) > 0:
                    data[field] = node[0].text

            print '@@@data',data
            # create cleaned data 

            data['cleaned_data']['sku'] = data['id']
            data['cleaned_data']['brand'] = Brand.objects.get(name='mithaimate')
            data['cleaned_data']['category'] = Category.objects.get(name='Sweets')
            data['cleaned_data']['model'] = data['id']
            data['cleaned_data']['title'] = data['name']
            data['cleaned_data']['image_url'] = [data['image']]
            data['cleaned_data']['shipping_duration'] = '4-5 Working Days'
            data['cleaned_data']['offer_price'] = Decimal(data['price'])
            data['cleaned_data']['list_price'] = Decimal(data['price'])
            data['cleaned_data']['description'] = 'Weight:%s gms\n\n%s' % (data['weight'],striptags(data['description']))
            data['cleaned_data']['availability'] = AvailabilityMap.objects.get(
                    applies_to = 'account',
                    account = self.config['ACCOUNT']).availability
            products.append(data)
        print '@@@',products
        return products


if __name__ == '__main__':
    feed = MithaiMateFeed()
    feed.sync()
    #feed.get_category_name()
    #feed.sync(**{'_local_':True})
