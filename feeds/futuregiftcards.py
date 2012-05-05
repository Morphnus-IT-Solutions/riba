import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.fgcsettings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from categories.models import *
from accounts.models import *
from catalog.models import Brand, Product, Availability
from feeds.models import *
from feeds import feedutils
from feeds.feed import Feed
from django.template.defaultfilters import slugify, striptags
import logging
from django.conf import settings
from decimal import Decimal
import xlrd

log = logging.getLogger('feeds')

class FGCFeed(Feed):
    config = {
            'ACCOUNT': 'fgc',
            }    

    def parse(self, sync, *args, **kwargs):
	wb = xlrd.open_workbook('/home/saumil/tinla/feeds/data/fgc/FGC_Data.xls')
        count,heading_map = 0,{}
        s = wb.sheet_by_index(0)
        for col in range(s.ncols):
            heading_map[s.cell(0,col).value.lower()] = col

        fgc_client = Client.objects.get(name='Future Gift Cards')
        # Category
        try:
            category = Category.objects.get(name = 'Gift Vouchers', client = fgc_client)
        except Category.DoesNotExist:
            category = Category(name = 'Gift Vouchers', client = fgc_client, slug=slugify('Gift Vouchers'))
            category.save()

        products, product_variants, rows_visited, flag, first_row = [], [], [], 0, 0
        
        for row_num in range(1,s.nrows):
            row = s.row(row_num)
            brand = row[heading_map['brand']].value

            # Brand
            try:
                brand = Brand.objects.get(name = brand)
                brand.description = row[heading_map['brand description']].value
                brand.save()
            except Brand.DoesNotExist:
                brand = Brand(name = brand, description = row[heading_map['brand description']].value, slug = slugify(brand))
                brand.save()

            if row_num in rows_visited:
                continue

            product_variants=[]
            first_row = row_num
            temp_row = s.row(row_num)
            for variants in range(row_num,(row_num+int(temp_row[heading_map['variant']].value))):
                data = dict(cleaned_data=self.get_default_cleaned_data())
                row = s.row(variants)
                if row[heading_map['skuid']].ctype in (2,3):
                    data['cleaned_data']['sku'] = str(int(row[heading_map['skuid']].value))
                else:
                    data['cleaned_data']['sku'] = str(row[heading_map['skuid']].value)
                data['cleaned_data']['title'] = row[heading_map['title']].value
                data['cleaned_data']['detailed_desc'] = row[heading_map['description']].value
                data['cleaned_data']['brand'] = brand
                data['cleaned_data']['category'] = category
                data['cleaned_data']['model'] = ''
                image_path = 'http://dev.futuregiftcards.com:8000/media/images/pd/%s.jpg'
                data['cleaned_data']['image_url']= [image_path % str(row[heading_map['image name']].value)]
                data['cleaned_data']['stock_status'] = 'instock'
                data['cleaned_data']['status'] = 'active'
                data['cleaned_data']['list_price'] =   Decimal(str(row[heading_map['mrp']].value))
                data['cleaned_data']['offer_price'] = Decimal(str(row[heading_map['offer price']].value))
                data['cleaned_data']['gift_desc'] = row[heading_map['terms & conditions']].value
                data['cleaned_data']['shipping_duration'] = row[heading_map['delivery time']]
                data['cleaned_data']['product_type'] = 'variant'
                data['cleaned_data']['availability'] = Availability.objects.get(id=1)
                data['cleaned_data']['is_default_product'] = (variants == first_row) and True or False
                product_variants.append(data)
                rows_visited.append(variants)
            products.append(product_variants)
        return products

if __name__ == '__main__':
    feed = FGCFeed()
    feed.sync()
