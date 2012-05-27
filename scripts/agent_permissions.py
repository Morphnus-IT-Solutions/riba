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
from ccm.models import Agent

def add_perm(content_type, codename, perm_name):
    try:
        perm = Permission.objects.get(content_type=content_type,codename=codename)
    except Permission.DoesNotExist:
        perm = Permission(name=perm_name,content_type=content_type,codename=codename)
        perm.save()
    return perm


def add_permissions():
    content_type=ContentType.objects.get(app_label='auth', model='user')
    order_content_type = ContentType.objects.get(app_label='orders', model='order')
    perms = []

    perms.append(add_perm(content_type, 'access_callcenter', 'Can access callcenter interface'))
    perms.append(add_perm(content_type, 'access store', 'Can access store interface'))
    perms.append(add_perm(order_content_type, 'can_confirm_order', 'Can confirm order'))
    perms.append(add_perm(order_content_type, 'can_cancel_order', 'Can cancel order'))

    agents = Agent.objects.filter(role='agent')
    for ag in agents:
        for p in perms:
            ag.user.user_permissions.add(p)
        ag.save()
        print "added permissions to ",ag.name

if __name__=='__main__':
    add_permissions()

