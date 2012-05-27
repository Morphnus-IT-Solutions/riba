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
from accounts.models import *
from catalog.models import *
from datetime import datetime
from dealprops.models import *

deal = FridayDeal.objects.get(id=1)
flag = True
sequence = 1
errors = []
skus = """
    """.split("\n")

book = xlrd.open_workbook('/home/kishan/apps/tinla/scripts/freaking_friday_model.xls')
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
        sku = row[map['skuid']].value
        start_time = row[map['starttime']].value
        end_time = row[map['endtime']].value
        to_update.append({
            'article_id': str(article_id).split('.')[0],
            'sku':str(sku).split('.')[0],
            'start_time':start_time,
            'end_time':end_time,
        })
    except KeyError:
        flag = False
        errors.append('Unsupported excel file.')

for item in to_update:
    try:
        id = item['article_id']
        src = SellerRateChart.objects.get(article_id=id,seller__client=5)
    except:
        flag = False
        errors.append("SKU not found: %s" % id)

if flag:
    for item in to_update:
        id = item['article_id']
        src = SellerRateChart.objects.get(article_id=id,seller__client=5)
        prod = FridayDealProducts()
        prod.deal = deal
        prod.product = src.product
        prod.sequence = sequence*10
        prod.starts_on = datetime.strptime(item['start_time'],'%d-%m-%Y %I:%M:%S %p')
        prod.ends_on = datetime.strptime(item['end_time'],'%d-%m-%Y %I:%M:%S %p')
        prod.save()
        sequence += 1
        print "ADDED::",id
else:
    for err in errors:
        print err
