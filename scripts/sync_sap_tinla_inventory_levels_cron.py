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

import urllib, urllib2
import logging
from catalog.models import SellerRateChart
from inventory.models import Inventory, InventoryLog, InventoryDcLspResolution, InventoryStoLog, SapEvents
from fulfillment.models import Dc
from orders.models import Order
from django.db.models import Q
from decimal import Decimal
from django.db import transaction
from datetime import datetime, timedelta

log = logging.getLogger('inventory')

def get_latest_sto_entry_for_oi(sto):
    oi = sto.orderitem
    latest_sto_entry_for_oi = oi.inventorystolog_set.all().filter(
        is_valid = True, 
        created_on__gt = sto.created_on)
    return latest_sto_entry_for_oi

def get_latest_dclsp_entry_for_oi(dclsp):
    oi = dclsp.orderitem
    created_on = dclsp.created_on
    latest_dclsp_entry_for_oi = oi.inventorydclspresolution_set.all().filter(
        is_valid = True,
        created_on__gt = dclsp.created_on)

def get_order_queue(rate_chart, dc):
    '''
    Get the orderitems waiting for this (rate_chart, dc)'s inward stock.
    '''
    order_queue = []
    
    dclsp_queue = InventoryDcLspResolution.objects.select_related(
        'orderitem','orderitem__sap_order_item').filter(
        orderitem__seller_rate_chart = rate_chart,
        dc = dc,
        stock_allocated = False,
        stock_to_be_allocated__gt = 0,
        is_valid = True).exclude(
        Q(orderitem__state = 'cancelled') | 
        Q(orderitem__order__state = 'booked')).order_by('created_on')

    sto_queue = InventoryStoLog.objects.select_related(
        'orderitem','orderitem__sap_order_item').filter(
        orderitem__seller_rate_chart = rate_chart,
        from_dc = dc,
        stock_allocated = False,
        stock_to_be_allocated__gt = 0,
        is_valid = True).exclude(
        Q(orderitem__state = 'cancelled') | 
        Q(orderitem__order__state = 'booked')).order_by('created_on')

    if not dclsp_queue and not sto_queue:
        return []
    elif not dclsp_queue:
        for item in sto_queue:
            if not get_latest_sto_entry_for_oi(item):
                order_queue.append(item)
        return order_queue
    elif not sto_queue:
        for item in dclsp_queue:
            if not get_latest_dclsp_entry_for_oi(item):
                order_queue.append(item)
        return order_queue
    else:
        sto_queue_len = len(sto_queue)
        dclsp_queue_len = len(dclsp_queue)
        sto_iter = 0
        dclsp_iter = 0

        while (sto_iter < sto_queue_len) and (dclsp_iter < dclsp_queue_len):
            if sto_queue[sto_iter].created_on < dclsp_queue[dclsp_iter].created_on:
                latest_sto_entry_for_oi = get_latest_sto_entry_for_oi(sto_queue[sto_iter])
                if not latest_sto_entry_for_oi:
                    order_queue.append(sto_queue[sto_iter])
                sto_iter += 1
            else:
                latest_dclsp_entry_for_oi = get_latest_dclsp_entry_for_oi(dclsp_queue[dclsp_iter])
                if not latest_dclsp_entry_for_oi:
                    order_queue.append(dclsp_queue[dclsp_iter])
                dclsp_iter += 1

            if sto_iter == sto_queue_len:
                for item in dclsp_queue[dclsp_iter:]:
                    if not get_latest_dclsp_entry_for_oi(item):
                        order_queue.append(item)
                dclsp_iter = dclsp_queue_len

            if dclsp_iter == dclsp_queue_len:
                for item in sto_queue[sto_iter:]:
                    if not get_latest_sto_entry_for_oi(item):
                        order_queue.append(item)
                sto_iter = sto_queue_len

        return order_queue
    return []

def set_inventorylog(inventory, dc, was_stock, new_stock, was_outward, new_outward):
    inventory_log = InventoryLog.objects.create(
        rate_chart = inventory.rate_chart,
        dc = dc,
        inventory = inventory,
        was_stock = was_stock,
        new_stock = new_stock,
        was_outward = was_outward,
        new_outward = new_outward,
        modified_by = 'sap_tinla_sync_cron')
        
if __name__ == '__main__':
    article_id, dc = '',''
    dc_code_list = ['2786','9010','2315','2330','2640','2641','2644']
    dc_list = Dc.objects.filter(code__in = dc_code_list)

    rate_charts = []
    current_time = datetime.now()
    orders = Order.objects.filter(client = 5,
        timestamp__gte = current_time + timedelta(hours = -1),
        timestamp__lt = current_time)

    for order in orders:
        order_items = order.get_order_items(None, exclude=dict(state__in=['bundle']),
            select_related=('seller_rate_chart'))
        for oi in order_items:
            rc = oi.seller_rate_chart
            if not rc in rate_charts:
                rate_charts.append(rc)

    total_count = len(rate_charts)
    counter = 1

    for rc in rate_charts:
        for dc in dc_list:
            with transaction.commit_on_success():
                try:
                    values = {'material':rc.article_id,
                        'plant':dc.code,
                        'storageLoc':'10'}
                    #url = 'http://10.0.102.22:18001/dpCallBAPI_stg_servlet_QueryInvetory/QueryInvetory'
                    url = 'http://10.0.101.53:28001/dpSAPBapiCall_servlet_QueryInventory/QueryInventory'
                    data = urllib.urlencode(values)
                    req = urllib2.Request(url, data)
                    res = urllib2.urlopen(req)
                    if res.getcode() == 200:
                        quantity = int(round(Decimal(res.read())))
                        log.info('DC:%s, article_id = %s, quantity = %s' % (dc.code, rc.article_id, quantity))
                        order_queue = get_order_queue(rc, dc)
                        stock_to_be_allocated = Decimal('0')
                        if order_queue:
                            for item in order_queue:
                                stock_to_be_allocated += item.stock_to_be_allocated
                            
                        log.info('stock_to_be_allocated = %s' % stock_to_be_allocated)
                        if (quantity - stock_to_be_allocated) > Decimal('0'):
                            log.info('(quantity - stock_to_be_allocated) > 0')
                            inventory = Inventory.objects.filter(rate_chart = rc,
                                dc = dc,
                                type = 'physical')
                            if inventory:
                                inventory = inventory.for_update()[0]
                            else:
                                inventory = Inventory.objects.create(rate_chart = rc,
                                    dc = dc,
                                    type = 'physical',
                                    threshold = 0,
                                    starts_on = datetime(1111,1,1),
                                    ends_on = datetime(9999,12,31))
                                inventory = Inventory.objects.filter(rate_chart = rc,
                                    dc = dc,
                                    type = 'physical').for_update()[0]

                            current_ats = (inventory.stock - inventory.stock_adjustment - inventory.bookings - inventory.outward - inventory.threshold)
                            log.info('current_ats = %s' % current_ats)
                            
                            was_stock = inventory.stock
                            was_outward = inventory.outward
                            changes = False
                            if current_ats < (quantity - stock_to_be_allocated):
                                inventory.stock += (quantity - stock_to_be_allocated - current_ats) 
                                inventory.save()
                                changes = True
                            elif current_ats > (quantity - stock_to_be_allocated):
                                inventory.outward += current_ats - (quantity - stock_to_be_allocated)
                                inventory.save()
                                changes = True
                                
                            new_stock = inventory.stock
                            new_outward = inventory.outward

                            if changes:
                                set_inventorylog(inventory, dc, was_stock, new_stock, was_outward, new_outward)
                            log.info('ats > 0 for dc=%s, articleid = %s' % (dc.code, rc.article_id))
                        else:
                            log.info('quantity - stock_to_be_allocated <= 0')
                            current_ats = Decimal('0')
                            inventory = Inventory.objects.filter(rate_chart = rc,
                                dc = dc,
                                type = 'physical')
                            if inventory:
                                inventory = inventory.for_update()[0]
                                current_ats = (inventory.stock - inventory.stock_adjustment - inventory.bookings - inventory.outward - inventory.threshold)

                            if current_ats and inventory:
                                was_stock = inventory.stock
                                was_outward = inventory.outward

                                inventory.outward += current_ats
                                inventory.save()

                                new_stock = inventory.stock
                                new_outward = inventory.outward

                                set_inventorylog(inventory, dc, was_stock, new_stock, was_outward, new_outward)
                                log.info('set ats=0 for dc=%s, articleid=%s' % (dc.code, rc.article_id))
                    else:
                        log.info('Some error in response for DC:%s, article_id=%s' % (dc.code, rc.article_id))
                        log.info('')
                except Exception as e:
                    log.info('Exception in response for DC:%s, article_id=%s' % (dc.code, rc.article_id))
                    log.info(e)
                    log.info('')
                    pass

        try:
            is_available_for_sale = rc.is_available_for_sale(None)
            if rc.stock_status == 'instock' and not is_available_for_sale:
                rc.stock_status = 'outofstock'
                rc.save()
                product = rc.product
                product.update_solr_index()
                log.info('updated solr index for article_id = %s' % rc.article_id)
            elif rc.stock_status in ['outstock','notavailable'] and is_available_for_sale:
                rc.stock_status = 'instock'
                rc.save()
                product = rc.product
                product.update_solr_index()
                log.info('updated solr index for article_id = %s' % rc.article_id)
        except:
            pass

        log.info('done with %s out of %s' % (counter, total_count))
        counter += 1
        log.info('')
        log.info('')
