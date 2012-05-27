import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.holiisettings'
os.environ['PYTHON_EGG_CACHE'] = '/tmp/holii-python-eggs'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
