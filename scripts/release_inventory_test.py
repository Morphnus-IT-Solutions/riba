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

from payments.models import *
from utils import utils
from datetime import datetime, timedelta
from orders.models import Order
from inventory.models import Inventory, InventoryLog

class Client():
    type = 'cronjob'

class Request():
    client = Client()

request = Request()

def release_inventory(orderitem):
    from sap.views import inward_event
    if orderitem.is_inventory_blocked:
        #Get inventory log entries for this order item
        physical_inventory_log = InventoryLog.objects.select_related(
            'rate_chart','dc').filter(
            orderitem=orderitem,
            inventory__type = 'physical')

        virtual_inventory_log = InventoryLog.objects.select_related(
            'rate_chart','dc').filter(
            orderitem=orderitem,
            inventory__type = 'virtual')

        if physical_inventory_log:
            inventory_log = physical_inventory_log[0]
            inward_event(request, inventory_log.rate_chart, 
                inventory_log.dc, 
                (inventory_log.new_bookings - inventory_log.was_bookings))

        if virtual_inventory_log:
            inventory_log = virtual_inventory_log[0]
            inventory_update_errors = inventory_log.inventory.increment_virtual_inventory(request, 
                (inventory_log.new_bookings - inventory_log.was_bookings), inventory_log)

        orderitem.is_inventory_blocked = False
        orderitem.save(force_update=True)

if __name__ == '__main__':
    order = Order.objects.get(id=5352703)
    all_order_items = order.get_order_items(request, exclude=dict(state__in=['cancelled','bundle']),
        select_related=('seller_rate_chart','seller_rate_chart__product'))
    delta = []
    for oi in all_order_items:
        release_inventory(oi)

