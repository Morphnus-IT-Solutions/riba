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
import simplejson
import xlrd

log = logging.getLogger('feeds')

class ToysFeed(Feed):
    config = {
            'ACCOUNT': 'kidzee',
            'PATH' : '/tmp/kidzee.xls'
            }

    def get_image_url(self,sku):
        image_url = 'http://www.chaupaati.in/media/images/kidzee/' + str(int(sku)) + '.jpg'
        return image_url


    def parse(self, sync, *args, **kwargs):
        file = self.config['PATH']
        book = xlrd.open_workbook(file)
        sh = book.sheet_by_index(0)
        header = sh.row(0)
        map = {}
        idx = 0
        for x in header:
            val = x.value.strip().lower()
            map[val] = idx
            idx += 1

        products = []
        for i in range(1,sh.nrows):
            row = sh.row(i)
            data = {'cleaned_data':self.get_default_cleaned_data()}
            data['title'] = row[map['title']].value
            data['description'] = row[map['description']].value
            data['mrp'] = int(row[map['mrp']].value)
            data['offer_price'] = int(row[map['offer_price']].value)
            data['sku'] = row[map['sku']].value

            

            data['cleaned_data']['sku'] = data['sku']
            data['cleaned_data']['brand'] = Brand.objects.get(name='kidzee')
            data['cleaned_data']['category'] = Category.objects.get(name='Toys & Games')
            data['cleaned_data']['model'] = data['sku']
            data['cleaned_data']['title'] = data['title']
            data['cleaned_data']['image_url'] = [self.get_image_url(data['sku'])]
            data['cleaned_data']['shipping_duration'] = '7-10 days'
            data['cleaned_data']['offer_price'] = Decimal(str(data['offer_price']))
            data['cleaned_data']['list_price'] = Decimal(str(data['mrp']))
            data['cleaned_data']['description'] = striptags(data['description'])
            data['cleaned_data']['availability'] = AvailabilityMap.objects.get(
                    applies_to = 'account',
                    account = self.config['ACCOUNT']).availability
            products.append(data)

        return products


if __name__ == '__main__':
    feed = ToysFeed(only_add=True)
    feed.sync(**{'_local_':True})
