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
import xlrd
from categories.models import *
from feeds.models import *

def parse():
    book = xlrd.open_workbook('/home/hemanth/Desktop/fb-categories.xls')
    sh = book.sheet_by_index(0)
    header = sh.row(0)
    map = {}
    idx = 0
    for x in header:
        val = x.value.strip().lower()
        map[val] = idx
        idx += 1

    for i in range(1,sh.nrows):
        row = sh.row(i)
        fb_category = row[map['fb_category']].value.strip()
        ch_category = row[map['ch_category']].value.strip()
        print '####',fb_category, ch_category
        category = Category.objects.get(name=ch_category)
        category_mapping = CategoryMapping()
        category_mapping.mapped_to = category
        category_mapping.category = fb_category
        category_mapping.account = 'futurebazaar'
        category_mapping.save()
        print '@@',category



if __name__ == '__main__':
    parse()
