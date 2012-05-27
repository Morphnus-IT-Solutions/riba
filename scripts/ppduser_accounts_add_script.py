
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
from users.models import *

#group = Group(name="PpdAdminUser")
#group.save()
ppdadminusers = PpdAdminUser.objects.all()
for ppduser in ppdadminusers:
    profile = ppduser.profile
    accounts = ppduser.accounts.all()
    for account in accounts:
        profile.managed_accounts.add(account)

#ct = ContentType.objects.get(name="profile")
#permission = Permission(name="Can access ppd pages", content_type=ct, codename="access_ppd")
#permission.save()
#group.permissions.add(permission)
#
#groups2 = Group.objects.get(name="Manager")
#permission = Permission.objects.get(name = "Can change seller configurations")
#group2.permissions.add(permission)


