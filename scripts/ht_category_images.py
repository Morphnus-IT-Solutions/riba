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
        category = Category.objects.get(name = par_cat, client = ht_client)
    except Category.DoesNotExist:
        category = Category(name = par_cat, client = ht_client, slug = slugify(par_cat))
        category.save()
    return category


def get_image_urls(image_path, cat):
    image_urls = []
    try:
        listing = os.listdir(image_path)
        listing = sorted(listing)
        for infile in listing:
            if infile != 'Thumbs.db':
                image_urls.append('http://dev.hometown.in:8000/media/images/category-images/%s/%s' % (cat, infile))
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
    category.save()


def add_category_images():
    ht_client = Client.objects.get(name = 'HomeTown')

    wb = xlrd.open_workbook('/home/saumil/tinla/feeds/data/hometown/ht_category_images.xls')
    count,heading_map = 0,{}
    s = wb.sheet_by_index(0)
    for col in range(s.ncols):
        heading_map[s.cell(0,col).value.lower()] = col
        
    for row_num in range(1,s.nrows):
        row = s.row(row_num)
        cat = row[heading_map['category']].value.strip()
        
        # create category
        category = create_category(ht_client, cat)
        
        # get image urls
        image_path = '/home/saumil/tinla/media/hometown/images/category-images/%s' % (cat)
        print cat
        image_urls = get_image_urls(image_path, cat)

        # delete all historic category images
        category.categoryimage_set.all().delete()
        
        # attach image to categories
        if image_urls:
            for url in image_urls:
                attach_image_to_category(category, url)

        print "added images for %s" % (cat)

if __name__=='__main__':
    add_category_images()
