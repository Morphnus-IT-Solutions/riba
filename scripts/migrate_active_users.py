import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.fbsettings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from atg.models import *
from datetime import datetime

if __name__ == '__main__':
    migrate_from = datetime(day=30, month=11, year=2008)
    qs = DcsppOrder.objects.filter(last_modified_date__gte = migrate_from).values('profile_id').distinct()
    print qs.query
    print qs.count()
