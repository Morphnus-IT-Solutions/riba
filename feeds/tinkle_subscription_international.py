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

class TinkleFeed(Feed):
    config = {
            'ACCOUNT': 'tinkle-international',
            'URL': 'http://www.amarchitrakatha.com/chaupaati.xml',
            'TYPE': 'XML'
            }

    def get_image_url(self, path):
        if not path: return ''
        soup = BeautifulSoup(path)
        link = soup.find('a')
        if not link: return ''
        if not soup.find('a'): return ''
        if not soup.find('a').getText(): return ''
        return 'http://amarchitrakatha.com/%s' % soup.find('a').getText()

    def get_text(self, html):
        s = BeautifulSoup(html)
        return s.getText()


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
        import fileinput
        for line in fileinput.input(file, inplace=1):
            keys_with_spaces = ['Product Name', 'List price', 'Sell price',
                    'All terms', 'Stock Level', 'Publisher Reference',
                    'Post date', 'Updated date']
            for key in keys_with_spaces:
                line = line.replace(key, key.replace(' ','_'))
            print line,

        ack_brand = Brand.objects.get(id=19)
        tinkle_brand = Brand.objects.get(id=28)
        karadi_brand = Brand.objects.get(id=29)

        books_and_comics = Category.objects.get(name='Books & Comics')

        xmldoc = etree.parse(file)
        products = []
        for product in xmldoc.xpath("/xml/node"):
            data = dict(cleaned_data=self.get_default_cleaned_data())
            no_html_fields = ['List_price','Sell_price', 'Product_Name','Description','Path']
            # single value fields
            single_value_fields = ['ISBN','Product_Name','Description','List_price','Sell_price',
                    'international','Path','Nid','Published']
            for field in single_value_fields:
                data[field] = ''
                node = product.xpath(field.split(' ')[0])
                if node and len(node) > 0 and node[0].text:
                    data[field] = node[0].text
                    if field in no_html_fields:
                        data[field] = htmlutils.to_text(node[0].text)

            if data.get('Published','').lower() == 'no':
                continue

            if 'subscription' in data.get('Product_Name','').lower() and 'tinkle' in data.get('Product_Name','').lower():
                print 'adding tinkle subscription'
            else:
                print 'skipping other ack products'
                continue
            if data.get('international') != 'Yes':
                continue
            # ignore blaclists
            if self.is_blacklisted_sku(data['Nid']): continue

            # create cleaned data 
            data['cleaned_data']['brand'] = tinkle_brand
            data['cleaned_data']['category'] = books_and_comics 

            data['cleaned_data']['sku'] = data['Nid']
            data['cleaned_data']['model'] = data['ISBN'] or ''
            data['cleaned_data']['title'] = data['Product_Name']
            data['cleaned_data']['currency'] = 'usd'
            data['cleaned_data']['image_url'] = [self.get_image_url(data['Path'])]
            data['cleaned_data']['shipping_duration'] = '4-6 Weeks'
            data['cleaned_data']['offer_price'] = Decimal(self.get_text(data['Sell_price']).replace(',','').replace('Rs',''))
            
            data['cleaned_data']['list_price'] = Decimal(self.get_text(data['List_price']).replace('Rs','').replace(',',''))
            # compute international price
            data['cleaned_data']['offer_price'] = data['cleaned_data']['offer_price'] * Decimal('2.5') * Decimal('0.025')
            data['cleaned_data']['list_price'] = data['cleaned_data']['list_price'] * Decimal('2.5') * Decimal('0.025')
            data['cleaned_data']['description'] = data['Description']
            data['cleaned_data']['availability'] = AvailabilityMap.objects.get(
                    applies_to = 'account',
                    account = self.config['ACCOUNT']).availability
            products.append(data)
        print len(products)

        return products


if __name__ == '__main__':
    feed = TinkleFeed()
    feed.sync()
