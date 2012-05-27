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

from catalog.models import *
from categories.models import *

category = Category.objects.get(name='Technology')

products = Product.objects.filter(category=category,type='variable')

for product in products:
    variants = ProductVariant.objects.filter(blueprint=product)
    print product
    for variant in variants:
        v = variant.variant
        v.category = product.category
        v.save()

