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
import os

log = logging.getLogger('feeds')

class LeadstartFeed(Feed):
    config = {
            'ACCOUNT': 'leadstart-publishing',
            'URL': 'http://www.leadstartcorp.com/feeds/create-xml-rssnew.php',
            'TYPE': 'XML'
            }

    def clean(self,string):
        keys = [u'\xef',u'\xa0',u'\xa1',u'\xa2',u'\xa3',u'\xa4',u'\xa5',u'\xa6',u'\xa7',u'\xa8',u'\xa9',u'\xaa',u'\xab',u'\xac',u'\xad',u'\xae',u'\xaf',u'\xb0',u'\xb1',u'\xb2',u'\xb3',u'\xb4',u'\xb5',u'\xb6',u'\xb7',u'\xb8',u'\xb9',u'\xba',u'\xbb',u'\xbc',u'\xbd',u'\xbe',u'\xbf',u'\xef',u'\xeb',u'\xf6',u'\xd7',u'\x96',u'\x92']
        for key in keys:
            string = string.replace(key,u'')

        if not string:
            return ''
        string = str(string)
        string = string.strip()
        return string.replace('\\t','')
 

    def parse(self, sync, *args, **kwargs):
        # create the directory to store data
        file = self.config['URL']
        if '_local_' in kwargs:
            file = 'feeds/data/%s.%s' % (self.config['ACCOUNT'],
                    self.config['TYPE'].lower())
        else:
            path = '%s/%s-%d.%s' % (settings.FEEDS_ROOT,
                    self.config['ACCOUNT'],
                    sync.id,
                    self.config['TYPE'].lower())
            class MyURLopener(urllib.FancyURLopener):
                def http_error_default(self, url, fp, errorcode, errmsg, headers):
                    raise Exception("Unable to fetch file")
            urllib.urlretrieve(file, path)
            file = path
        products = []
        xmldoc = etree.parse(file)
        count = 1
        for product in xmldoc.xpath("/channel/rss/item"):
            data = dict(cleaned_data=self.get_default_cleaned_data())
            fields = {'product_name':'itemtitle',
                    'sku':'isbn',
                    'list_price':'itemprice',
                    'offer_price':'itemprice',
                    'image_url':'image'}

            extracted_data = {}
            for field in fields:
                key = fields[field]
                node = product.xpath(key)
                if node and len(node)>0 and node[0].text:
                    extracted_data[field] = self.clean(node[0].text)
                else:
                    extracted_data[field] = None
            node = product.xpath('aboutbook/div')
            description = ''
            if node:
                description = etree.tostring(node[0]).replace("<strong>","<br /><br /><strong>")

            # ignore blaclists
            if self.is_blacklisted_sku(extracted_data['sku']): continue
            # create cleaned data 
            data['cleaned_data']['brand'] = Brand.objects.get(name='Leadstart Publishing')
            data['cleaned_data']['category'] = Category.objects.get(name='Books')
            if not extracted_data['sku']:
                data['cleaned_data']['sku'] = 'leadstart%s' % count
                count += 1
            else:
                data['cleaned_data']['sku'] = extracted_data['sku']
            data['cleaned_data']['model'] = ''
            data['cleaned_data']['title'] = extracted_data['product_name']
            data['cleaned_data']['shipping_duration'] = '4-5 Working Days'
            data['cleaned_data']['list_price'] = Decimal(extracted_data['list_price'])
            
            data['cleaned_data']['offer_price'] = Decimal(extracted_data['offer_price'])
            if not extracted_data['list_price'] or extracted_data['list_price'] < extracted_data['offer_price']:
                data['cleaned_data']['list_price'] = extracted_data['offer_price']
            data['cleaned_data']['description'] = description
            data['cleaned_data']['image_url'] = [extracted_data['image_url']]
            data['cleaned_data']['availability'] = AvailabilityMap.objects.get(
                    applies_to = 'account',
                    account = self.config['ACCOUNT']).availability
            products.append(data)
            self.update_description = True
        return products


if __name__ == '__main__':
    feed = LeadstartFeed()
    feed.sync()
