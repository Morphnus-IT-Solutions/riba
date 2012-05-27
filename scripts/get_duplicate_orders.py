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

from orders.models import *

orders = Order.objects.filter(client=5,state='confirmed')

for o in orders:
    if o.reference_order_id:
        oos = Order.objects.filter(reference_order_id=o.reference_order_id)
        for oo in oos:
            if oo.user != o.user:
                print 'duplicate orders', o.reference_order_id,o.payment_realized_on,o.payment_realized_mode, o.user,o.user.get_primary_emails(),o.user.get_primary_phones()
    else:
        print 'no reference found for %s' % o.id
