#!/usr/bin/python

import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.htsettings'

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

from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
from django.conf import settings


# --------------------
# create product type
# --------------------
def create_product_type(name, client):
    try:
        pr_type = ProductType.objects.using('default').get(type = name, client = client)
    except ProductType.DoesNotExist:
        pr_type = ProductType(type = name, client = client)
        pr_type.save(using='default')
        create_sku_product_type_mapping(pr_type)
    return pr_type


# ---------------------
# create feature group
# ---------------------
def create_feature_group(name, product_type):
    try:
        fgrp = FeatureGroup.objects.using('default').get(name = name, product_type = product_type)
    except FeatureGroup.DoesNotExist:
        fgrp = FeatureGroup(name = name, product_type = product_type)
        fgrp.save(using='default')
    return fgrp


# ------------
# create unit
# ------------
def create_unit(name):
    try:
        u = Unit.objects.using('default').get(code = slugify(name))
    except Unit.DoesNotExist:
        u = Unit(name = name, code = slugify(name))
        u.save(using='default')
    return u


# ---------------
# create feature
# ---------------
def create_feature(name, feature_group, product_type, type , unit):
    try:
        feat = Feature.objects.using('default').get(name = name, product_type = product_type, group = feature_group)
    except Feature.DoesNotExist:
        feat = Feature(name = name, product_type = product_type, group = feature_group, unit = unit)
    if type == 'Num': type = 'number'
    feat.type = type.lower()
    feat.save(using='default')
    return feat


def create_sku_product_type_mapping(product_type):
    try:
        sp = SkuTypeProductTypeMapping.objects.using('default').get(account='HomeTown', sku_type = product_type.type, product_type = product_type)
    except SkuTypeProductTypeMapping.DoesNotExist:
        sp = SkuTypeProductTypeMapping(account='HomeTown', sku_type = product_type.type, product_type = product_type)
        sp.save(using='default')

def add_specifications():
    _client = Client.objects.using('default').get(name='HomeTown')

    wb = xlrd.open_workbook(settings.HOME_PATH+'tinla/feeds/data/hometown/hometown_specification.xls')
    count,heading_map = 0,{}
    for w in wb.sheet_names():
        s = wb.sheet_by_name(w)
        
        for col in range(s.ncols):
            heading_map[s.cell(0,col).value.lower()] = col
            print s.cell(0,col).value.lower()
            
        for row_num in range(1,s.nrows):
            row = s.row(row_num)


            # create product type
            product_type = create_product_type(row[heading_map['product type']].value.strip(), _client)
            print "------------------------------------------"
            print "created product type ::::", product_type

            
            # create feature group
            feature_group = create_feature_group(row[heading_map['features group']].value.strip(), product_type)
            print "created feature group ::::", feature_group

            # create unit
            unit = create_unit(row[heading_map['unit 1']].value.strip())

            # create feature
            feature = create_feature(row[heading_map['features 1']].value.strip(), feature_group, product_type, row[heading_map['type 1']].value.strip(), unit)

            print "added feature ::::" , feature, row[heading_map['type 1']].value.strip()

            # create unit
            unit = create_unit(row[heading_map['unit 2']].value.strip())

            # create feature
            feature = create_feature(row[heading_map['features 2']].value.strip(), feature_group, product_type, row[heading_map['type 2']].value.strip(), unit)

            print "added feature ::::" , feature, row[heading_map['type 2']].value.strip()

            # create unit
            unit = create_unit(row[heading_map['unit 3']].value.strip())

            # create feature
            feature = create_feature(row[heading_map['features 3']].value.strip(), feature_group, product_type, row[heading_map['type 3']].value.strip(), unit)

            print "added feature ::::" , feature, row[heading_map['type 3']].value.strip()

            # create unit
            unit = create_unit(row[heading_map['unit 4']].value.strip())

            # create feature
            feature = create_feature(row[heading_map['features 4']].value.strip(), feature_group, product_type, row[heading_map['type 4']].value.strip(), unit)

            print "added feature ::::" , feature, row[heading_map['type 4']].value.strip()

            # create feature
            feature = create_feature(row[heading_map['features 5']].value.strip(), feature_group, product_type, row[heading_map['type 5']].value.strip(), None)

            print "added feature ::::" , feature, row[heading_map['type 5']].value.strip()

            # create feature
            feature = create_feature(row[heading_map['features 6']].value.strip(), feature_group, product_type, row[heading_map['type 6']].value.strip(), None)

            print "added feature ::::" , feature, row[heading_map['type 6']].value.strip()

            # create feature
            feature = create_feature(row[heading_map['features 7']].value.strip(), feature_group, product_type, row[heading_map['type 7']].value.strip(), None)

            print "added feature ::::" , feature, row[heading_map['type 7']].value.strip()


if __name__=='__main__':
    add_specifications()
