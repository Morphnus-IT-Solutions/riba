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

import xlrd
from pricing.models import *
from accounts.models import *
from catalog.models import *
from datetime import datetime, timedelta
from decimal import Decimal

book = xlrd.open_workbook('/home/apps/tinla/scripts/Freeking_Friday_Slot_Price_Maintained_21stSept11.xls')
sh = book.sheet_by_index(0)
header = sh.row(0)
map = {}
idx = 0
for idx in range(sh.ncols):
    map[header[idx].value.strip().lower()] = idx
errors = []
to_update = []

for row_count in range(1, sh.nrows):
    row = sh.row(row_count)
    try:
        article_id = row[map['articleid']].value
        offer_price = row[map['offerprice']].value
        catalog = row[map['catalog']].value
        sku = row[map['skuid']].value
        start_time = row[map['starttime']].value
        end_time = row[map['endtime']].value
        slot_no = row[map['slot no']].value
        to_update.append({
            'article_id': str(article_id).split('.')[0],
            'offer_price' : offer_price,
            'catalog' : catalog,
            'sku':str(sku).split('.')[0],
            'start_time':start_time,
            'end_time':end_time,
            'slot_no':slot_no,
        })
    except KeyError:
        errors.append('Unsupported excel file.')

#print to_update

account = Account.objects.get(id=87)
price_list = None
try:
    price_list = PriceList.objects.get(name="Freaking Friday Price")
except PriceList.DoesNotExist:
    price_list = PriceList(name="Freaking Friday Price")
    price_list.save()

file = open('freaking_friday_articles.txt','w')
special_products = []
for item in to_update:
    try:
        rate_chart = SellerRateChart.objects.get(article_id=item['article_id'], seller__client=5)
        start_time = datetime.strptime(item['start_time'],'%d-%m-%Y %I:%M:%S %p') + timedelta(days=-1)
        end_time= datetime.strptime(item['end_time'],'%d-%m-%Y %I:%M:%S %p') + timedelta(days=-1)

        try:
            price = Price.objects.get(rate_chart=rate_chart, price_list=price_list, price_type='timed',
            start_time=start_time, end_time=end_time)
        except Price.DoesNotExist:
            price = Price(rate_chart=rate_chart, price_list=price_list, price_type='timed', start_time=start_time,
            end_time=end_time)
        
        price.offer_price = Decimal(str(item['offer_price']))
        #price.save()
        print '%s inserted successfully' % price
        file.write("%s inserted successfully -- sku = %s\n\n" % (price, item['sku']))
        if item['slot_no'] == 'Slot2':
            special_products.append("Special:: sku: %s -- time %s to %s, NAME::%s \n" % (item['sku'], start_time, end_time,
            rate_chart.product.id))

    except SellerRateChart.DoesNotExist:
        print 'Error in finding SellerRateChart for sku = %s' % item['sku']
        file.write('Error in finding SellerRateChart for sku = %s\n\n' % item['sku'])
for p in special_products:
    print "SPECIAL:",p
