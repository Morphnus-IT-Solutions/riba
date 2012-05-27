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
from django.utils import simplejson
import os
from categories.models import *
from accounts.models import *

class FutureBazaarCat():
    config = {
            'ACCOUNT': 'nfuturebazaar',
            'URL': 'http://omsn.futurebazaar.com/catalog/1000028/feed/raw',
            'TYPE': 'JSON'
            }
    def save_cat_heirarchy(self,category,parent):
        #print category['display_name'],parent['display_name'] if parent else None
        cat = Category()
        cat.name = category['display_name']
        cat.ext_id = category['category_id']
        cat.slug = slugify(cat.name)
        client = Client.objects.get(id=3)
        cat.client = client
        cat.save()
        cat_graph = CategoryGraph()
        cat_graph.category = cat
        if parent:
            parent = Category.objects.get(name=parent['display_name'],client=client)
        cat_graph.parent = parent
        cat_graph.save()

    def get_child(self,category,level,parent):
        str = ''
        for l in range(0,level):
            str += '#'
        print '%s:%s,%s' % (str,category['display_name'],parent['display_name'] if parent else None)
        self.save_cat_heirarchy(category,parent)
        level += 1
        for child in category['children']:
            self.get_child(child,level,category)
    def parse(self,*args, **kwargs):
        #req = urllib2.R
        file = open('/home/chaupaati/tinla/feeds/1000028.json')
        json_str = file.read()
        json_obj = simplejson.loads(json_str)
        for category in json_obj['categories']:
            self.get_child(category,1,None)


if __name__ == '__main__':
    feed = FutureBazaarCat()
    feed.parse()
