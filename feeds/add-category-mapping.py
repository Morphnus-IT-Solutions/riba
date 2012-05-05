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

from categories.models import Category, Store
from feeds.models import CategoryMapping
from django.template.defaultfilters import slugify
from feeds import feedutils

def add_category_mapping(file, account):
    f = open(file)
    for line in f.readlines():
        line = line.strip()
        if line and not line.startswith('#'):
            theirs, ours, store = line.split('","')
            theirs = theirs.replace('"','')
            ours = ours.replace('"','')
            store = store.replace('"','')
            if ours == 'Blacklisted':
                continue
            feedutils.get_or_create_category_mapping(account, theirs, ours, store)
    f.close()

if __name__ == '__main__':
    if len(sys.argv) < 3:
        'Incorrect usage: Need atleast two arguments - file and account'
    else:
        add_category_mapping(sys.argv[1], sys.argv[2])

