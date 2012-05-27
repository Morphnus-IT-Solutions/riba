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

import xlrd


# --------------------
# create product type
# --------------------
def create_product_type(name, client):
    try:
        pr_type = ProductType.objects.get(type = name, client = client)
    except:
        pr_type = ''
    return pr_type

# ----------------
# create category
# ----------------
def create_category(name, client):
    try:
        c = Category.objects.get(name = name, client = client)
        return c
    except:
        return ''

# ---------------------
# create feature group
# ---------------------
def create_feature_group(name, product_type):
    fgrp = FeatureGroup.objects.get(name = name, product_type = product_type)
    return fgrp


# ---------------
# create feature
# ---------------
def create_feature(name, feature_group, product_type):
    print "feature ::::", name, feature_group, product_type
    feat = Feature.objects.get(name = name, product_type = product_type)
    return feat


def create_filter(category, feature_group, feature, type, name, sort_order):
    fil = ''
    if feature:
        try:
            fil = Filter.objects.get(category = category, feature = feature)
        except Filter.DoesNotExist:
            fil = Filter(category = category, feature = feature)
        fil.type = type
        fil.name = name
        fil.sort_order = sort_order
        fil.save()
        print "created ", fil

    if feature_group and not feature:
        try:
            fil = Filter.objects.get(category = category, feature_group = feature_group)    
        except Filter.DoesNotExist:
            fil = Filter(category = category, feature_group = feature_group)
        fil.type = type
        fil.name = name
        fil.sort_order = sort_order
        fil.save()
        print "created ", fil
    return fil


def create_filter_bucket(row, heading_map, facet):
    facet.filterbucket_set.all().delete()
    for d in range(5):
        choice = str(row[heading_map['choice'+str(d+1)]].value.strip())
        choice_range = str(row[heading_map['range'+str(d+1)]].value.strip())
        if choice and choice_range:
            start = choice_range.split('-')[0].strip()
            end = choice_range.split('-')[1].strip()
            fb = FilterBucket(fil = facet, display_name = choice, start = start, end = end, sort_order = d+1)
            fb.save()
            print "created FilterBucket for ::::", facet


def add_facets():
    _client = Client.objects.get(id=12)

    wb = xlrd.open_workbook('/home/apps/tinla/feeds/data/ezone/facets_details1.xls')
    count,heading_map = 0,{}
    s=wb.sheet_by_index(0)

    for col in range(s.ncols):
        heading_map[s.cell(0,col).value.lower()] = col
        
    for row_num in range(1,s.nrows):
        row = s.row(row_num)
        feat_grp = str(row[heading_map['features group']].value.strip())
        feat = str(row[heading_map['features']].value.strip())
        cat = str(row[heading_map['category']].value.strip())
        #pr_type = str(row[heading_map['product type']].value.strip())
        type = str(row[heading_map['type']].value.strip())
        if type == 'Check Box': type = 'checkbox'
        elif type == 'Positive Presence': type = 'positive_presence'
        elif type == 'Slider': type = 'slider'
        elif type == 'Bucketed': type = 'buckets'
        print cat, feat, type
        category = create_category(cat, _client)

        #Get product type 
        product_type = None
        try:
            product_type = CategoryProducttypeMapping.objects.get(category=category).product_type
        except CategoryProducttypeMapping.DoesNotExist:
            product_type = create_product_type(cat, _client)

        feature_group, feature = '', ''

        if product_type:
            if feat_grp: feature_group = create_feature_group(feat_grp, product_type)

            if feat: feature = create_feature(feat, feature_group, product_type)

            if category:
                facet = create_filter(category, feature_group, feature, type, row[heading_map['name']].value, sort_order = row_num)
                print cat, feat_grp
                if facet and type == 'buckets':
                    create_filter_bucket(row, heading_map, facet)

if __name__=='__main__':
    add_facets()
