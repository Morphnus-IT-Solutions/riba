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
from lists.models import *
from accounts.models import *
from django.template.defaultfilters import slugify

from django.core.files import File
from django.core.files.temp import NamedTemporaryFile
import urllib2
import xlrd


def create_category(ht_client, par_cat):
    try:
        category = Category.objects.using('default').get(name = par_cat, client = ht_client)
    except Category.DoesNotExist:
        category = Category(name = par_cat, client = ht_client, slug = slugify(par_cat))
        category.save(using='default')
    return category


def create_mega_drop_down(ht_client, parent_category, par_cat_order):
    try:
        mega_drop_down = MegaDropDown.objects.using('default').get(category = parent_category, client = ht_client, type = "category")
    except MegaDropDown.DoesNotExist:
        mega_drop_down = MegaDropDown(category = parent_category, client = ht_client, type = "category")
    mega_drop_down.sort_order = par_cat_order
    mega_drop_down.save(using='default')


def create_category_graph(cat, sort_order, par_cat=None):
    try:
        cat_graph = CategoryGraph.objects.using('default').get(category = cat, parent = par_cat)
    except CategoryGraph.DoesNotExist:
        cat_graph = CategoryGraph(category = cat, parent = par_cat)
    cat_graph.sort_order = sort_order
    cat_graph.save(using='default')


def get_image_urls(image_path, cat):
    image_urls = []
    try:
        listing = os.listdir(image_path)
        listing = sorted(listing)
        for infile in listing:
            if infile != 'Thumbs.db':
                image_urls.append('http://www.hometown.in/media/images/category-images/%s/%s' % (cat, infile))
    except:
        print "Error adding images for category ",cat
    return image_urls

def attach_image_to_category(category, url):
    if not url:
        return
    url = url.replace(' ', '%20')
    img_temp = NamedTemporaryFile()
    img_temp.write(urllib2.urlopen(url).read())
    img_temp.flush()

    ci = CategoryImage()
    ci.name = category.name[:25]
    ci.category = category
    ci.image.save(category.name[:25], File(img_temp))
    ci.save()
    category.save(using='default')


def add_categories():
    ht_client = Client.objects.using('default').get(name = 'HomeTown')

    wb = xlrd.open_workbook(settings.HOME_PATH+'tinla/feeds/data/hometown/hometown_categories.xls')
    count,heading_map = 0,{}
    s = wb.sheet_by_index(0)
    for col in range(s.ncols):
        heading_map[s.cell(0,col).value.lower().encode('ascii','ignore')] = col
        
    for row_num in range(1,s.nrows):
        row = s.row(row_num)
        par_cat = row[heading_map['level 1']].value.strip()
        sub_cat = row[heading_map['level 2']].value.strip()
        sub_sub_cat = row[heading_map['level 3']].value.strip()
        par_cat_order = int(row[heading_map['level 1 order']].value or 1)
        sub_cat_order = int(row[heading_map['level 2 order']].value or 1)
        if sub_sub_cat: sub_sub_cat_order = int(row[heading_map['level 3 order']].value or 1)

        # create category
        parent_category = create_category(ht_client, par_cat)
        sub_category = create_category(ht_client, sub_cat)
        if sub_sub_cat: sub_sub_category = create_category(ht_client, sub_sub_cat)

        # create mega drop down
        create_mega_drop_down(ht_client, parent_category, par_cat_order)

        # create category graph
        create_category_graph(parent_category, par_cat_order)
        create_category_graph(sub_category, sub_cat_order, parent_category)
        if sub_sub_cat: create_category_graph(sub_sub_category, sub_sub_cat_order, sub_category)

        # get image urls
        parent_image_path = settings.HOME_PATH+'tinla/media/hometown_v2/images/category-images/%s' % (par_cat)
        sub_image_path = settings.HOME_PATH+'tinla/media/hometown_v2/images/category-images/%s' % (sub_cat)
        if sub_sub_cat: sub_sub_image_path = settings.HOME_PATH+'tinla/media/hometown_v2/images/category-images/%s' % (sub_sub_cat)

        parent_image_urls = get_image_urls(parent_image_path, par_cat)
        sub_image_urls = get_image_urls(sub_image_path, sub_cat)
        if sub_sub_cat: sub_sub_image_urls = get_image_urls(sub_sub_image_path, sub_sub_cat)

        # delete all historic category images
        parent_category.categoryimage_set.all().delete()
        sub_category.categoryimage_set.all().delete()
        if sub_sub_cat: sub_sub_category.categoryimage_set.all().delete()

        # attach image to categories
        if parent_image_urls:
            for url in parent_image_urls:
                attach_image_to_category(parent_category, url)

        if sub_image_urls:
            for url in sub_image_urls:
                attach_image_to_category(sub_category, url)

        if sub_sub_cat and sub_sub_image_urls:
            for url in sub_sub_image_urls:
                attach_image_to_category(sub_sub_category, url)

        print "added %s, %s, %s" % (par_cat, sub_cat, sub_sub_cat)


if __name__=='__main__':
    add_categories()
