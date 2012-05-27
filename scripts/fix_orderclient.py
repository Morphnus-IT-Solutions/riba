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

from catalog.models import *
from orders.models import *

orders = Order.objects.filter(state='confirmed')

mismatches = []
for o in orders:
    for oi in o.orderitem_set.iterator():
        if oi.seller_rate_chart.seller.client != o.client:
            mismatches.append(o)
            break

print len(mismatches)
print mismatches
        
