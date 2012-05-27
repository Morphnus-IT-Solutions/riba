#!/usr/bin/python

import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.nuezonesettings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from categories.models import *
from lists.models import *
from accounts.models import *
from django.template.defaultfilters import slugify

from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import urllib2
import xlrd
from django.conf import settings


def create_category(_client, par_cat):
    try:
        category = Category.objects.get(name = par_cat, client = _client)
    except Category.DoesNotExist:
        category = Category(name = par_cat, client = _client, slug = slugify(par_cat))
        category.save()
    return category


def create_mega_drop_down(_client, parent_category):
    try:
        mega_drop_down = MegaDropDown.objects.get(category = parent_category, client = _client, type = "category")
    except MegaDropDown.DoesNotExist:
        mega_drop_down = MegaDropDown(category = parent_category, client = _client, type = "category")
        mega_drop_down.save()


def create_category_graph(cat, par_cat=None):
    try:
        cat_graph = CategoryGraph.objects.get(category = cat, parent = par_cat)
    except CategoryGraph.DoesNotExist:
        cat_graph = CategoryGraph(category = cat, parent = par_cat)
        cat_graph.save()

# --------------------
# create product type
# --------------------
def create_product_type(name, client):
    try:
        pr_type = ProductType.objects.get(type = name, client = client)
    except ProductType.DoesNotExist:
        pr_type = ProductType(type = name, client = client)
        pr_type.save()
    return pr_type

#------------------
#create category-product type mapping
#------------------
def create_category_producttype_mapping(category, product_type):
    try:
        cat_prtype_mapping = CategoryProducttypeMapping.objects.get(category=category, product_type=product_type)
    except CategoryProducttypeMapping.DoesNotExist:
        cat_prtype_mapping = CategoryProducttypeMapping(category=category, product_type=product_type)
        cat_prtype_mapping.save()

def add_categories():
    _client = Client.objects.get(id=12)

    wb = xlrd.open_workbook('/home/apps/tinla/feeds/data/ezone/ezone_categories.xls')
    count,heading_map = 0,{}
    s = wb.sheet_by_index(0)
    for col in range(s.ncols):
        heading_map[s.cell(0,col).value.lower()] = col
        
    for row_num in range(1,s.nrows):
        row = s.row(row_num)
        cat = row[heading_map['category']].value
        sub_cat = row[heading_map['level 1']].value
        sub_sub_cat = row[heading_map['level 2']].value
        product_type = row[heading_map['product type']].value

        #Create product type
        product_type = create_product_type(product_type, _client)
        
        # create category
        parent_category = create_category(_client, cat)
        sub_category = create_category(_client, sub_cat)
        if sub_sub_cat: 
            sub_sub_category = create_category(_client, sub_sub_cat)
            create_category_producttype_mapping(sub_sub_category, product_type)
        else:
            create_category_producttype_mapping(sub_category, product_type)


        # create mega drop down
        create_mega_drop_down(_client, parent_category)

        # create category graph
        create_category_graph(parent_category)
        create_category_graph(sub_category, parent_category)
        if sub_sub_cat: create_category_graph(sub_sub_category, sub_category)

        print "added %s, %s, %s" % (cat, sub_cat, sub_sub_cat)


if __name__=='__main__':
    add_categories()
