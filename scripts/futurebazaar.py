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

class FutureBazaarFeed(Feed):
    config = {
            'ACCOUNT': 'futurebazaar',
            'URL': {
                'mobiles':'http://ezone.futurebazaar.com/atom?name=Ezone&cat=Mobile+Phones',
                'computers':'http://ezone.futurebazaar.com/atom?name=Ezone&cat=Computers',
                'cameras':'http://ezone.futurebazaar.com/atom?name=Ezone&cat=Cameras',
                'audio-video':'http://ezone.futurebazaar.com/atom?name=Ezone&cat=Audio+%26+Video',
                'ipods-mp3-players':'http://ezone.futurebazaar.com/atom?name=Ezone&cat=iPods+%26+MP3+Players',
                'kitchen-appliances':'http://ezone.futurebazaar.com/atom?name=Ezone&cat=Kitchen+Appliances',
                'home-appliances':'http://ezone.futurebazaar.com/atom?name=Ezone&cat=Home+Appliances',
                'memory-storage':'http://ezone.futurebazaar.com/atom?name=Ezone&cat=Memory+%26+Storage',
                'gaming':'http://ezone.futurebazaar.com/atom?name=Ezone&cat=Gaming',
                },
            'TYPE': 'XML'
            }

    def get_brand_for_futurebazaar(self, sku, url):
        try:
            sku_info = SKUInfo.objects.get(account=self.config['ACCOUNT'],
                    sku=sku)
            if not sku_info.brand:
                brand = feedutils.get_brand_for_futurebazaar(url)
                brand_mapping  = self.get_brand_mapping(brand).mapped_to
                sku_info.brand = brand_mapping
                sku_info.save()
                return brand_mapping
            else:
                return sku_info.brand
        except SKUInfo.DoesNotExist:
            brand = feedutils.get_brand_for_futurebazaar(url)
            brand_mapping  = self.get_brand_mapping(brand).mapped_to
            sku_info = SKUInfo(account=self.config['ACCOUNT'], sku=sku, brand = brand_mapping)
            sku_info.save()
            return brand_mapping

    def parse(self, sync, *args, **kwargs):
        # create the directory to store data
        os.mkdir('%s/%s-%s' % (settings.FEEDS_ROOT, self.config['ACCOUNT'], sync.id))
        files = []
        for url_name in self.config['URL'].keys():
            url = self.config['URL'][url_name]
            # get the file and save it
            path = '%s/%s-%d/%s.%s' % (settings.FEEDS_ROOT,
                    self.config['ACCOUNT'],
                    sync.id,
                    url_name,
                    self.config['TYPE'].lower())
            class MyURLopener(urllib.FancyURLopener):
                def http_error_default(self, url, fp, errorcode, errmsg, headers):
                    raise Exception("Unable to fetch file")
            #MyURLopener().retrieve(url, path)
            #files.append(path)
            files.append('%s/%s-139/%s.%s' % (settings.FEEDS_ROOT,
                self.config['ACCOUNT'],
                url_name,
                self.config['TYPE'].lower()))

        products = []
        for file in files:
            xmldoc = etree.parse(file)
            entries = xmldoc.xpath('/n:feed/n:entry', namespaces =
                    {
                        'n':'http://purl.org/atom/ns#',
                        'fb':'http://localhost:8080/atom', 
                        'dc':'http://purl.org/dc/elements/1.1/'
                    }) 
            for product in entries:
                data = dict(cleaned_data=self.get_default_cleaned_data())
                fields = {'sku': 'fb:skuid', 'product_name':'fb:productname',
                        'list_price':'fb:mrp', 'offer_price':'fb:saleprice',
                        'desc':'fb:productdesc', 'image':'fb:imagelink',
                        'category': 'fb:subcategory', 'url':'fb:productlink',
                        'subcategory': 'fb:subsubcategory', 'subsubcategory': 'fb:subsubsubcategory'}

                extracted_data = {}
                for key in fields:
                    node = product.xpath(fields[key], namespaces =
                            {
                                'n':'http://purl.org/atom/ns#',
                                'fb':'http://localhost:8080/atom', 
                                'dc':'http://purl.org/dc/elements/1.1/'
                            }) 
                    if node and len(node) > 0 and node[0].text:
                        extracted_data[key] = node[0].text
                    else:
                        extracted_data[key] = None


                cat = extracted_data['category']
                if extracted_data.get('subcategory', None):
                    cat = extracted_data['subcategory']
                if extracted_data.get('subsubsubcategory',None):
                    cat = extracted_data['subsubsubcategory']

                print extracted_data['url']

                extracted_data['brand'] = self.get_brand_for_futurebazaar(
                        extracted_data['sku'],
                        extracted_data['url'])

                print cat, extracted_data['brand']

                continue

                # ignore blaclists
                if self.is_blacklisted_sku(extracted_data['sku']): continue
                # create cleaned data 
                data['cleaned_data']['brand'] = self.get_brand_mapping(extracted_data['brand']).mapped_to
                data['cleaned_data']['category'] = self.get_category_mapping(cat).mapped_to

                data['cleaned_data']['sku'] = extracted_data['sku']
                data['cleaned_data']['model'] = ''
                data['cleaned_data']['title'] = extracted_data['product_name']
                data['cleaned_data']['image_url'] = [self.get_image_url(extracted_data['image'])]
                data['cleaned_data']['shipping_duration'] = '7-10 Working Days'
                data['cleaned_data']['list_price'] = Decimal(self.get_text(extracted_data['list_price']))
                
                data['cleaned_data']['offer_price'] = Decimal(self.get_text(data['offer_price']))
                if not data['cleaned_data']['list_price'] or data['cleaned_data']['list_price'] < data['cleaned_data']['offer_price']:
                    data['cleaned_data']['list_price'] = data['cleaned_data']['offer_price']
                data['cleaned_data']['description'] = extracted_data['desc']
                data['cleaned_data']['availability'] = AvailabilityMap.objects.get(
                        applies_to = 'account',
                        account = self.config['ACCOUNT']).availability
                products.append(data)

        return []
        return products


if __name__ == '__main__':
    feed = FutureBazaarFeed()
    feed.sync()
