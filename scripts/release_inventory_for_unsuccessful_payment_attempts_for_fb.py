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
from datetime import datetime, timedelta
from inventory.models import InventoryLog, InventoryStoLog, InventoryDcLspResolution, Inventory
import logging
from utils import utils


log = logging.getLogger('inventory')

class Client():
    type = 'cronjob'

class Request():
    client = Client()

request = Request()

def release_inventory(orderitem):
    from sap.views import inward_event
    log.info('orderitem.is_inventory_blocked = %s' % orderitem.is_inventory_blocked)
    if orderitem.is_inventory_blocked:
        vi_adjustment = Decimal('0')
        dc = None
        dclsp = InventoryDcLspResolution.objects.select_related(
            'orderitem__seller_rate_chart','dc').filter(
            orderitem = orderitem,
            is_valid = True).order_by('-created_on')

        if dclsp and \
            dclsp[0].stock_to_be_allocated > 0 and \
            dclsp[0].stock_allocated == False and \
            dclsp[0].is_valid == True:
            vi_adjustment = dclsp[0].stock_to_be_allocated
            
        #Invalidate DC-LSP enries.
        if dclsp:
            dc = dclsp[0].dc
            for item in dclsp:
                item.is_valid = False
                item.save()

        if dc:
            #Virtual stock adjustment
            virtual_inventory_log = InventoryLog.objects.select_related(
                'rate_chart','dc').filter(
                orderitem = orderitem,
                dc = dc,
                inventory__type__in=['backorder','madetoorder','preorder']).order_by('-created_on')

            if virtual_inventory_log:
                inventory_log = virtual_inventory_log[0]
                inventory_update_errors = inventory_log.inventory.increment_virtual_inventory(request, 
                    (inventory_log.new_bookings - inventory_log.was_bookings), inventory_log)

            #Physical stock adjustment
            physical_adjustment = (orderitem.qty - vi_adjustment)
            if physical_adjustment:
                inward_event(request, orderitem.seller_rate_chart,
                    dc, physical_adjustment)


        orderitem.is_inventory_blocked = False
        orderitem.save(force_update=True)
        log.info('Successfully released inventory %s' % orderitem.id)

if __name__ == '__main__':
    from datetime import *
    current_time = datetime.now()
    log.info('@@@@@@@@@@@@@@ Inside release inventory cron job at %s' % current_time)
    last_10_minute_pa = PaymentAttempt.objects.filter(
        created_on__gt = datetime.now()+timedelta(minutes=-10),
        created_on__lte = datetime.now(),
        status = 'pending realization',
        order__client = 5).exclude(
        payment_mode__in = utils.DEFERRED_PAYMENT_MODES)

    last_10_minute_pa_orders = []
    for payment_attempt in last_10_minute_pa:
        last_10_minute_pa_orders.append(payment_attempt.order)
    
    pa = PaymentAttempt.objects.filter(
        created_on__gte = datetime.now()+timedelta(minutes=-20),
        created_on__lte = datetime.now()+timedelta(minutes=-10),
        status = 'pending realization',
        order__client = 5, 
        order__support_state__in = [None, 'booked', '']).exclude(
        payment_mode__in = utils.DEFERRED_PAYMENT_MODES, 
        order__in = last_10_minute_pa_orders)

    for item in pa:
        order = item.order
        log.info('order.id = %s' % order.id)
        all_order_items = order.get_order_items(request, exclude=dict(state__in=['cancelled','bundle']),
            select_related=('seller_rate_chart'))

        for oi in all_order_items:
            log.info('calling release inventory for orderitem.id = %s' % oi.id)
            release_inventory(oi)
            log.info('success for orderitem.id = %s' % oi.id)
