
from categories.models import Category, Store
from catalog.models import Brand, Product, ProductImage
from feeds.models import CategoryMapping, BrandMapping
from django.template.defaultfilters import slugify

from django.core.files import File
from django.core.files.temp import NamedTemporaryFile

import urllib2
import socket
from BeautifulSoup import BeautifulSoup


def get_or_create_category_mapping(account, theirs, ours, store=None):
    if not ours:
        ours = "Uncategorized"
    try:
        c = Category.objects.using('default').get(name=ours)
    except Category.DoesNotExist:
        # create category if it does not exist
        c = Category(name=ours, slug=slugify(ours))
        if store:
            c.store = Store.objects.using('default').get(name=store)
        c.moderate = True
        c.save(using='default')
    try:
        category_mapping = CategoryMapping.objects.using('default').get(
                category=theirs, account=account, mapped_to=c)
        return category_mapping
    except CategoryMapping.DoesNotExist:
        category_mapping = CategoryMapping(category=theirs,
                account=account,
                mapped_to = c)
        category_mapping.save(using='default')
        return category_mapping

def get_or_create_brand_mapping(account, theirs, ours):
    try:
        b = Brand.objects.using('default').get(name=ours)
    except Brand.DoesNotExist:
        try:
            b = Brand(name=ours,slug=slugify(ours),moderate=True)
            b.save(using='default')
        except:
            b = Brand.objects.using('default').get(name='Unknown')
    try:
        brand_mapping = BrandMapping.objects.using('default').get(
                brand=theirs, account=account,
                mapped_to=b)
        return brand_mapping
    except BrandMapping.DoesNotExist:
        brand_mapping = BrandMapping(mapped_to=b, brand=theirs, account=account)
        brand_mapping.save(using='default')
        return brand_mapping

def attach_image_to_product(product, url):
    if not url:
        return
    url = url.replace(' ', '%20')
    img_temp = NamedTemporaryFile()
    img_temp.write(urllib2.urlopen(url).read())
    img_temp.flush()

    pi = ProductImage()
    pi.name = product.title[:25]
    pi.product = product
    pi.image.save(product.title[:25], File(img_temp))
    pi.save(using='default')

    product.has_images = True
    product.save(using='default')

def get_letsbuy_model_number(sku):
    try:
        url = 'http://www.letsbuy.com/product_info.php?products_id=%s' % sku
        page = urllib2.urlopen(url)
        doc = BeautifulSoup(page)
        bread_crumb_links = doc.findAll('a', {"class":"headerNavigation"})[-1]
        model = bread_crumb_links.nextSibling.nextSibling
    except Exception, e:
        print repr(e)
        model = ""
    return model

def get_brand_for_futurebazaar(url):
    try:
        url = url.replace(' ','%20')
        page = urllib2.urlopen(url)
        doc = BeautifulSoup(page)
        brand = doc.findAll('small')[0].findAll('a')[0].text.strip('.')
    except Exception, e:
        brand = "Unknown"
    return brand

def isbn_to_isbn13(isbn):
    return ''

def isbn13_to_isbn(isbn13):
    return ''

def get_book_info(**kwargs):
    isbn = kwargs.get('isbn', None)
    isbn13 = kwargs.get('isbn13', None)

    if not isbn and not isbn13: return None
    if isbn and not isbn13: isbn13 = isbn_to_isbn13(isbn)
    if isbn13 and not isbn: isbn = isbn13_to_isbn(isbn13)

    # Feilds to get: Author, Publisher, Hardbound/Paperback, Description
    # Images, No. of pages, Genre
