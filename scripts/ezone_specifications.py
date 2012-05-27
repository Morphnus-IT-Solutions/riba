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
from accounts.models import Client
from django.template.defaultfilters import slugify
from feeds.models import SkuTypeProductTypeMapping
import xlrd


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


# ---------------------
# create feature group
# ---------------------
def create_feature_group(name, product_type, sort):
    try:
        fgrp = FeatureGroup.objects.get(name = name, product_type = product_type)
    except FeatureGroup.DoesNotExist:
        fgrp = FeatureGroup(name = name, product_type = product_type)
    fgrp.sort_order = sort
    fgrp.save()
    return fgrp


# ------------
# create unit
# ------------
def create_unit(name):
    try:
        u = Unit.objects.get(code = slugify(name))
    except Unit.DoesNotExist:
        u = Unit(name = name, code = slugify(name))
        u.save()
    return u


# ---------------
# create feature
# ---------------
def create_feature(name, feature_group, product_type, type , unit, sort):
    try:
        feat = Feature.objects.get(name = name, product_type = product_type)
    except Feature.DoesNotExist:
        feat = Feature(name = name, product_type = product_type, group = feature_group, unit = unit)
    feat.type = type
    feat.sort_order = sort
    feat.save()
    return feat


def create_sku_product_type_mapping(product_type):
    try:
        sp = SkuTypeProductTypeMapping.objects.get(account='nuezone', sku_type = product_type.type, product_type = product_type)
    except SkuTypeProductTypeMapping.DoesNotExist:
        sp = SkuTypeProductTypeMapping(account='nuezone', sku_type = product_type.type, product_type = product_type)
        sp.save()

def add_specifications():
    _client = Client.objects.get(pk=12)
    
    wb = xlrd.open_workbook('/home/apps/tinla/feeds/data/ezone/specification_details.xls')
    count,heading_map = 0,{}
    for w in wb.sheet_names():
        s = wb.sheet_by_name(w)
        sort = 1

        for col in range(s.ncols):
            heading_map[s.cell(0,col).value.lower()] = col
            
        for row_num in range(1,s.nrows):
            row = s.row(row_num)

            # create product type
            product_type = create_product_type(row[heading_map['product type']].value.strip(), _client)
            create_sku_product_type_mapping(product_type)
            print "------------------------------------------"
            print "created product type ::::", product_type
            
            # create feature group
            feature_group = create_feature_group(row[heading_map['features group']].value.strip(), product_type, sort)
            print "created feature group ::::", feature_group

            # create unit
            unit = create_unit(row[heading_map['unit']].value.strip())

            type = row[heading_map['type']].value.strip()
            if type == 'Text': type = 'text'
            elif type == 'Num': type = 'number'
            elif type == 'Boolean': type = 'boolean'
            # create feature
            feature = create_feature(row[heading_map['features']].value.strip(), feature_group, product_type, type, unit, sort)
            print "added feature ::::" , feature, row[heading_map['type']].value.strip(), sort
            sort += 1

if __name__=='__main__':
    add_specifications()
