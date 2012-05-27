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

from django.contrib.auth.models import *
from django.contrib.contenttypes.models import *
#from users.models import *

#group = Group(name="Sellers Admin")
ct = ContentType.objects.get(name="profile")
try:
    permission = Permission.objects.get(name="Can access IFS pages", codename="access_ifs")
    print "Permission already exists, hence not created"
except:
    permission = Permission(name="Can access IFS pages", content_type=ct, codename="access_ifs")
    permission.save()
 #   group.permissions.add(permission)


