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

log = logging.getLogger('feeds')

class IkenFeed(Feed):
    config = {
            'ACCOUNT': 'iken',
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
    
    def get_category_name(self,old_id):
        map = { 154:'Vacuum Cleaners',
                153:'Cooking Range',
                136:'Inverters',
                91:'Refrigerators',
                100:'Air Conditioners',
                117:'Geysers',
                81:'Irons',
                88:'Toaster, Grill',
                84:'Food Processor',
                68:'LCD Televisions',
                160:'School',
		        0:'Uncategorized'}

        return map[old_id]
    
    def get_image_url(self,id):
        image_url = 'http://www.chaupaati.in/assets/images/adSnaps/' + id + '_thumb1.jpeg'
        return image_url


    def parse(self, sync, *args, **kwargs):
        
        url = 'http://192.168.91.101:8080/listing/select?indent=on&version=2.2&q=userId%3A182830+AND+isActive%3Atrue&start=0&rows=500&fl=*&qt=standard&wt=json&explainOther=&hl.fl='
        json = urllib2.urlopen(url).read()
        dict = simplejson.loads(json)
        prods = dict['response']['docs']
        products = []
        count = 0
        for product in prods:
            data = {'cleaned_data':self.get_default_cleaned_data()}
            # single value fields
            single_value_fields = ['id','sku','brand','description','mrp','askingPrice','title','shippingDuration','make','categoryId']
            for field in single_value_fields:
                data[field] = ''
                if field in product:
                    data[field] = product[field]
            
            print '@@@',data

            data['cleaned_data']['sku'] = 'iken%s' % count
            count += 1
            make = 'iken'
            data['cleaned_data']['brand'] = Brand.objects.get(name=make)
            data['cleaned_data']['category'] = Category.objects.get(name=self.get_category_name(data['categoryId']))
            data['cleaned_data']['model'] = data['sku']
            data['cleaned_data']['title'] = data['title']
            data['cleaned_data']['image_url'] = [self.get_image_url(data['id'])]
            data['cleaned_data']['shipping_duration'] = data['shippingDuration']
            if 'askingPriceStr' in data:
                askingPriceStr = data['askingPriceStr']
            else:
                askingPriceStr = data['askingPrice']
            data['cleaned_data']['offer_price'] = Decimal(str(askingPriceStr))
            if 'mrpStr' in data:
                mrpStr = data['mrpStr']
            else:
                mrpStr = data['mrp']
            data['cleaned_data']['list_price'] = Decimal(str(mrpStr))
            data['cleaned_data']['description'] = striptags(data['description'])
            data['cleaned_data']['availability'] = AvailabilityMap.objects.get(
                    applies_to = 'account',
                    account = self.config['ACCOUNT']).availability
            products.append(data)

        return products


if __name__ == '__main__':
    feed = IkenFeed()
    feed.sync(**{'_local_':True})
