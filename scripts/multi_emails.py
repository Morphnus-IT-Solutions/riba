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

from users.models import *
from integrations.fbapi import users as apiuser, orders, fbapiutils


p = Phone.objects.get(phone = '0000000000')

emails = p.user.get_primary_emails()

print len(emails)
print emails


cookie_file = fbapiutils.init()
count = 0
notfound = []
for e in emails:
    u = apiuser.get_user_by_mobile(e.email,'nilesh',cookie_file)
    if u['responseCode'] == fbapiutils.USER_FOUND:
        count += 1
        print 'user found for %s' % e.email
        orders_info = orders.get_order_by_user(e.email,'nilesh',cookie_file,1)
        if orders_info['items'][0]['totalNoOfOrdersInProfile'] == 1:
            if not orders_info['items'][1]['items']:
                notfound.append(e.email)
        
        print 'order history for %s: %s' % (e.email,orders_info)
    else:
        notfound.append(e.email)

print notfound 

print 'total user found %s' % count
