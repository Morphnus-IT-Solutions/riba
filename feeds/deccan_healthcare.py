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
from django.utils.html import strip_tags
from BeautifulSoup import BeautifulSoup

log = logging.getLogger('feeds')

class DeccanFeed(Feed):
    config = {
            'ACCOUNT': 'deccan-healthcare',
            'URL': 'http://www.deccanhealth.com/product/xml',
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

        # clean the file


        xmldoc = etree.parse(file)
        products = []
        for product in xmldoc.xpath("/xml/node"):
            data = dict(cleaned_data=self.get_default_cleaned_data())

            # single value fields
            single_value_fields = ['Title','Id','Category','ProductOneLiner','Price','ImageURL',
                    'Composition','Packaging','ShippingInfo','ShippingTime']
            for field in single_value_fields:
                data[field] = ''
                node = product.xpath(field)
                if node and len(node) > 0 and node[0].text:
                    data[field] = node[0].text


            # create cleaned data 
            data['cleaned_data']['brand'] = Brand.objects.get(name='Deccan Healthcare')
            data['cleaned_data']['category'] = Category.objects.get(name='Healthcare')
            data['cleaned_data']['model'] = ''

            data['cleaned_data']['sku'] = data['Id']
            data['cleaned_data']['title'] = data['Title']
            data['cleaned_data']['image_url'] = [data['ImageURL']]
            data['cleaned_data']['shipping_duration'] = data['ShippingTime']
            data['cleaned_data']['list_price'] = Decimal(data['Price'].replace('Rs.','').replace(',',''))
            
            data['cleaned_data']['offer_price'] = Decimal(data['Price'].replace('Rs.','').replace(',',''))
            data['cleaned_data']['description'] = "<b>%s</b>%s<br /><br /><b>%s</b><br />%s<br /><br /><b>%s</b><br />%s<br /><br /><b>%s</b><br />%s<br /><br /><b>%s</b><br />%s" % ("Category: ",data['Category'],"Product One Liner", data['ProductOneLiner'],"Composition",data['Composition'],"Packaging",data['Packaging'],"ShippingInfo",data['ShippingInfo'])
            data['cleaned_data']['availability'] = AvailabilityMap.objects.get(
                    applies_to = 'account',
                    account = self.config['ACCOUNT']).availability
            products.append(data)
        print len(products)
        self.update_description = True

        return products


if __name__ == '__main__':
    feed = DeccanFeed()
    feed.sync()
