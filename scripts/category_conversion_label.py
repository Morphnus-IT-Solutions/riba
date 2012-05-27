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

from categories.models import *
from catalog.models import *

types = [{'label':'djEKCMvOkwMQlf7m1wM','cat_id':'1074'}, # TV
         {'label':'p2tlCMPPkwMQlf7m1wM','cat_id':'1174'}, # Mobile
         {'label':'Qw7uCLPRkwMQlf7m1wM','cat_id':'1054'}, # Laptop 
         {'label':'w4k_CKPTkwMQlf7m1wM','cat_id':'1171'}, # Hard Drives
         {'label':'PXgdCJvLlgMQlf7m1wM','cat_id':'1038'}, # Camera
         {'label':'3eZrCJPMlgMQlf7m1wM','cat_id':'920'},  # Apparel
         {'label':'oiblCIvNlgMQlf7m1wM','cat_id':'1090'}, # Footwear
         {'label':'IJ_1CIPOlgMQlf7m1wM','cat_id':'1104'}, # Home Appliances
        ]

for type in types:
    cat_id = type['cat_id']
    label = type['label']
    categories = []
    category = Category.objects.get(id=cat_id)
    if category not in categories:
        categories.append(category)
    children_cats = category.get_all_children()
    for c in children_cats:
        if c not in categories:
            categories.append(c)
    for category in categories:
        category.google_conversion_label = label
        category.save()
    print "LABEL::",label
    print "CATEGORIES::",categories
