#!/usr/bin/python

import os, sys
os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.htsettings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from orders.models import *
from utils.utils import *
from django.core.mail import EmailMessage

item_info = []
end_date = datetime.now().date()
start_date = end_date + timedelta(days=-45)
orders = Order.objects.filter(client=6, support_state='confirmed',  payment_realized_on__gte=start_date, payment_realized_on__lte=end_date+timedelta(days=1))
for order in orders:
    orderitems = order.get_order_items()
    excel_data = []
    for item in orderitems:
        excel_data.append(item.item_info())
    print excel_data, "excel_data"
msg = EmailMessage('test', 'test',
    "Future Bazaar Reports<lead@futurebazaar.com>",
    ['ankush.thapa@futuregroup.in'])
msg.send()


