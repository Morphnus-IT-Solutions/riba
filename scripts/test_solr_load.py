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

from datetime import datetime, timedelta, date
start_date = date(2012, 02, 26)
end_date = date(2012, 02, 27)
from orders.models import *
from fulfillment.models import *

order_item = OrderItem.objects.get(id= 2221439)
print order_item
order_item.index()
print "here"

order_items = OrderItem.objects.select_related('order').filter(order__booking_timestamp__gte = start_date, order__booking_timestamp__lt = end_date)
order_items = order_items.exclude(order__support_state = None).exclude(order__payment_mode = '').exclude(order__payment_mode = None)
print order_items.count()
count = 0
for order_item in order_items:
    count += 1
    print count
    order_item.index()

#orders = Order.objects.filter(booking_timestamp__gte = start_date, booking_timestamp__lt = end_date)
#orders = orders.exclude(support_state = None).exclude(payment_mode = '').exclude(payment_mode = None)
#print orders.count()
#count = 0
#for order in orders:
#    order.index()
#    count += 1
#    print count

#shipments = Shipment.objects.select_related('order').filter(order__booking_timestamp__gte = start_date, order__booking_timestamp__lt = end_date)
#shipments = shipments.exclude(order__support_state = None).exclude(order__payment_mode = '').exclude(order__payment_mode = None)
#print shipments.count()
#count = 0
#for shipment in shipments:
#    shipment.index()
#    count += 1
#    print count
