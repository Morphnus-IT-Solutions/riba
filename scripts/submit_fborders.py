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

from users.models import Profile
from integrations.fbapi import users, orders, fbapiutils


if __name__ == '__main__':
    cookie_file = fbapiutils.init()
    print cookie_file
    # cookie_file = '/tmp/tmpD3VfgE'
    print users.get_user_by_mobile('ajayjindal@inbox.com', 'hemant.fb', cookie_file)
    #order = orders.get_cart('hemant.fb', cookie_file, '9326164025')
    #print order

