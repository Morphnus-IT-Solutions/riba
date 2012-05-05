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

class FnpFeed(Feed):
    config = {
            'ACCOUNT': 'fnp',
            'URL': 'http://220.226.189.115/fnp/faces/xmlfeed/response.jsp',
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
        for product in xmldoc.xpath("/products/product"):
            data = dict(cleaned_data=self.get_default_cleaned_data())
            # single value fields
            single_value_fields = ['sku','name','description','price',
                    'features','available','imageurl','shippingcost','shippingtime','keywords','modelnumber','category']
            for field in single_value_fields:
                data[field] = ''
                node = product.xpath(field)
                if node and len(node) > 0:
                    data[field] = node[0].text

            parts = data['imageurl'].partition('http://images.fnp.in/images/product/')
            if parts[2].startswith('http://images.fnp.in/images/product/'):
                imageurl = parts[2]
            else:
                imageurl = data['imageurl']
            data['imageurl'] = imageurl
            category = data['category']
            if category not in [1001,1006,1014,1017,1020,1022,1023,1086,1087,1089,1154,1156]:
                continue
            # create cleaned data 
            if not 'yes' in data.get('available','').lower():
                continue
            data['cleaned_data']['sku'] = data['sku']
            data['cleaned_data']['brand'] = Brand.objects.get(name='fnp')
            data['cleaned_data']['category'] = Category.objects.get(name='Gifts')
            data['cleaned_data']['model'] = data['modelnumber']
            data['cleaned_data']['title'] = data['name']
            data['cleaned_data']['image_url'] = [data['imageurl']]
            data['cleaned_data']['shipping_duration'] = data['shippingtime']
            data['cleaned_data']['shipping_charges'] = data['shippingcost']
            data['cleaned_data']['offer_price'] = Decimal(data['price'])
            data['cleaned_data']['list_price'] = Decimal(data['price'])
            data['cleaned_data']['description'] = 'Features: %s<br /><br />Keywords: %s<br /><br />%s' % (data['features'],data['keywords'],striptags(data['description']))
            data['cleaned_data']['availability'] = AvailabilityMap.objects.get(
                    applies_to = 'account',
                    account = self.config['ACCOUNT']).availability
            products.append(data)
        return products


if __name__ == '__main__':
    feed = FnpFeed()
    feed.sync()
    #feed.get_category_name()
    #feed.sync(**{'_local_':True})
