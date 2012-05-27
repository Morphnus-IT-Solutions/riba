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

def add_feature_groups(file):
    f = open(file)
    lines = [l.strip() for l in f.readlines()]
    for l in lines:
        if l.startswith('#') or not l.strip():
            continue
        typ, grp, f_tobe, f_now = l.split(',')
        typ = typ.strip()
        grp = grp.strip()
        f_tobe = f_tobe.strip()
        f_now = f_now.strip()
        print l
        ptyp = ProductType.objects.get(type=typ)
        f = Feature.objects.get(product_type = ptyp, name = f_now)
        try:
            fg = FeatureGroup.objects.get(name=grp, product_type = ptyp)
        except FeatureGroup.DoesNotExist:
            fg = FeatureGroup(name = grp, product_type = ptyp)
            fg.save()
        f.group = fg
        f.name = f_tobe
        f.save() 

if __name__ == '__main__':
    add_feature_groups(sys.argv[1])
