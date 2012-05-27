from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponsePermanentRedirect
from django.template import RequestContext
from django.contrib import auth
from django.contrib.auth.models import User
from django.core.mail import EmailMessage, send_mail
from django.contrib.auth.decorators import login_required
from django.template.loader import get_template
from django.template import Context, Template
import re
import pyExcelerator
import logging
from django.utils import simplejson
import operator
import gviz_api
import random
from django.views.decorators.cache import never_cache
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_control
from django.conf import settings
import random
from django.http import HttpResponseRedirect
from decimal import Decimal, ROUND_FLOOR
import urllib, urllib2, httplib
from datetime import datetime, timedelta
from fulfillment.models import Dc, Lsp
from catalog.models import SellerRateChart
from inventory.models import *
from orders.models import Order, OrderItem
from utils import utils
from decimal import Decimal
from django.db import transaction
from django.db.models import Q

log = logging.getLogger('fborder')

def sap_updates(request):
    log.info('######### request.POST = %s' % request.POST)
#    log.info('HERE inside sap views')
#    log.info('')
#    log.info('###########')
#    log.info('transactioncode = %s' % request.POST['transactioncode'])
#    log.info('articleid = %s' % request.POST['articleid'])
#    log.info('issuingsite = %s' % request.POST['issuingsite'])
#    log.info('receivingsite = %s' % request.POST['receivingsite'])
#    log.info('issuingsitestorageloc = %s' % request.POST['issuingstorageloc'])
#    log.info('receivingsitestorageloc = %s' % request.POST['receivingstorageloc'])
#    log.info('movementtype = %s' % request.POST['movementtype'])
#    log.info('quantity = %s' % request.POST['quantity'])
#    log.info('#############')

    try:
        with transaction.commit_on_success():
            transaction_code = str(request.POST['transactioncode']).strip()
            article_id = int(str(request.POST['articleid']).strip())
            issuing_site = str(request.POST['issuingsite']).strip()
            if issuing_site:
                issuing_site = int(issuing_site)
            receiving_site = str(request.POST['receivingsite']).strip()
            if receiving_site:
                receiving_site = int(receiving_site)
            issuing_storage_location = str(request.POST['issuingstorageloc']).strip()
            if issuing_storage_location:
                issuing_storage_location = int(issuing_storage_location)
            receiving_storage_location = str(request.POST['receivingstorageloc']).strip()
            if receiving_storage_location:
                receiving_storage_location = int(receiving_storage_location)
            movement_type = str(request.POST['movementtype']).strip()
            quantity = str(request.POST['quantity']).strip()
            if quantity:
                actual_quantity = Decimal(quantity)
                quantity = int(round(Decimal(quantity)))

            #Get rate_chart
            try:
                rate_chart = SellerRateChart.objects.get(article_id=int(article_id), seller=87)
                fb_client = utils.get_future_ecom_prod()

                if receiving_site and receiving_storage_location and quantity:
                    dc = utils.get_dc(receiving_site, fb_client)
                    if dc:
                        sap_event = SapEvents.objects.create(rate_chart = rate_chart, 
                            dc = dc, 
                            actual_quantity = actual_quantity,
                            quantity = quantity, 
                            storage_location = int(receiving_storage_location),
                            type = 'inward')
                        if receiving_storage_location == int('10'):
                            inward_event(request, rate_chart, dc, quantity, sap_event)
                        sap_event.mark_sap_event_as_processed(request)

                if issuing_site and issuing_storage_location and quantity:
                    dc = utils.get_dc(issuing_site, fb_client)
                    if dc:
                        sap_event = SapEvents.objects.create(rate_chart = rate_chart,
                            dc = dc,
                            actual_quantity = actual_quantity,
                            quantity = quantity,
                            storage_location = int(issuing_storage_location),
                            type = 'outward')
                        if issuing_storage_location == int('10'):
                            outward_event(request, rate_chart, dc, quantity, sap_event)
                        sap_event.mark_sap_event_as_processed(request)
            except SellerRateChart.DoesNotExist:
                fb_client = utils.get_future_ecom_prod()
                fb_seller = utils.get_seller(87)
                unprocessed_sap_event = UnprocessedSAPEvents.objects.create(
                    article_id = int(article_id),
                    receiving_storage_location = receiving_storage_location,
                    receiving_site = receiving_site, 
                    issuing_storage_location = issuing_storage_location,
                    issuing_site = issuing_site,
                    quantity = quantity,
                    actual_quantity = actual_quantity,
                    seller = fb_seller,
                    client = fb_client)
                
    except Exception, e:
        log.exception('Cannot process SAP event')
        raise

    return HttpResponse()

def get_latest_dclsp_entry_for_oi(orderitem):
    latest_dclsp_entry_for_oi = InventoryDcLspResolution.objects.filter(
        orderitem = orderitem,
        is_valid = True).order_by('-created_on')

    if latest_dclsp_entry_for_oi:
        return latest_dclsp_entry_for_oi[0]

    return None

def get_order_queue(request, **kwargs):
    rate_chart = kwargs.get('rate_chart', None)
    dc = kwargs.get('dc', None)
    '''
    Get the orderitems waiting for this (rate_chart, dc)'s inward stock.
    '''
    order_queue = []
    
    dclsp_queue = InventoryDcLspResolution.objects.select_related(
        'orderitem','orderitem__sap_order_item').filter(
        stock_allocated = False,
        stock_to_be_allocated__gt = 0,
        is_valid = True).exclude(
        Q(orderitem__state = 'cancelled') | 
        Q(orderitem__order__state = 'booked')).order_by('created_on')

    if rate_chart:
        dclsp_queue = dclsp_queue.filter(
            orderitem__seller_rate_chart = rate_chart)

    if dc:
        dclsp_queue = dclsp_queue.filter(dc = dc)

    if dclsp_queue:
        for item in dclsp_queue:
            latest_dclsp_entry_for_oi = get_latest_dclsp_entry_for_oi(item.orderitem)
            if item == latest_dclsp_entry_for_oi:
                order_queue.append(item)
        return order_queue
    return []

def get_overall_adjustment_in_vi(unprocessed_vi_entries):
    stock = Decimal('0')
    stock_adjustment = Decimal('0')
    bookings = Decimal('0')
    bookings_adjustment = Decimal('0')
    for entry in unprocessed_vi_entries:
        if entry.stock:
            stock += entry.stock
        if entry.stock_adjustment:
            stock_adjustment += entry.stock_adjustment
        if entry.bookings:
            bookings += entry.bookings
        if entry.bookings_adjustment:
            bookings_adjustment += entry.bookings_adjustment

    adjustment = (stock - stock_adjustment - bookings - bookings_adjustment)
    if adjustment > Decimal('0'):
        return adjustment

    return Decimal('0')

def create_order_xml(request, orderitem):
    type = 'modify'
    if not orderitem.order.sap_date:
        type = 'new'
    orderitem.order.create_xml(request, type=type, items=[orderitem,])

def vi_adjustment(request, orderitem, vi_adjustment_list, sap_event):
    for item in vi_adjustment_list:
        inventory = item['inventory']
        quantity = item['quantity']
        processed = item['processed']
        inventory.perform_booking_adjustments(request, 
            quantity = quantity, 
            sap_event = sap_event,
            orderitem = orderitem)
        #if processed:
        #    inventory.mark_entry_as_procesed()

def get_active_inventory_entries(rate_chart, dc):
    current_time = datetime.now()
    inventory = Inventory.objects.filter(
        dc = dc,
        rate_chart = rate_chart,
        starts_on__lte = current_time, 
        ends_on__gte = current_time)
    
    physical_inventory = inventory.filter(type='physical')
    physical_inventory_obj = None
    if physical_inventory:
        physical_inventory_obj = physical_inventory.for_update()[0]
    else:
        '''
        No physical stock entry found for this (rate_chart,dc) combination.
        So let's create one, as we are getting stock for the first
        time for this (rate_chart, dc).
        '''
        physical_inventory_obj = Inventory.objects.create(
            rate_chart = rate_chart,
            dc = dc,
            is_active = True,
            starts_on = datetime(1111,1,1),
            ends_on = datetime(9999,12,31),
            type = 'physical',
            stock = 0,
            )
        physical_inventory_obj = Inventory.objects.filter(
            rate_chart = rate_chart,
            dc = dc,
            type = 'physical').for_update()[0]

    virtual_inventory = inventory.filter(
        type__in = ['backorder','madetoorder','preorder']).order_by('starts_on')

    virtual_inventory_obj = None
    if virtual_inventory:
        virtual_inventory_obj = virtual_inventory.for_update()[0]

    return {'physical':physical_inventory_obj, 'virtual':virtual_inventory_obj} 

def inward_event(request, rate_chart, dc, inward, sap_event=None, **kwargs):
    '''
    Expected Parameters:
        1) Rate chart for which inward event is received
        2) DC
        3) Inward quaantity
        4) request

    Steps:
    1) Get all the V.I. entries for this (rate_chart, dc) where (starts_on < current time) and 
       (stock - stock_adjustment - bookings - booking_adjustment) > 0. Order them by starts_on.
    2) For each such entry in (2),
            a) If (inward > 0), flush the order XML queue waiting for physical stock 
               from (rate_chart, dc) combination in the queue priority. 
            b) Let's say, orderitem is trying to book quantity=n. 
               If (inward - n) >= 0, then - 
               i) booking_adjustment = (booking_adjustment + n) and inward = (inward - n). 
               ii) Create the order XML.
               iii) Also check, if we need to create STO or not.
                    (Sto needs to be created if DC from inventory log and DC from 
                    DcLspResolution do not match. Create STO entry with 
                    from_dc={dc from inventory log} and 
                    to_dc={dc from DcLspResolution} )
    3) After performing (2), if still (inward > 0), then-
        a) Get physical stock entry for (rate_chart, dc) combination. Let's call it 'physical_stock_entry'.
        b) Get the V.I. entry where starts_on <= current time <= ends_on. Let's call it 'virtual_stock_entry'
        c) Perform the following operation: 
            i) physical_stock_entry.stock = physical_stock_entry.stock + inward
            ii)  if (virtual_stock_entry.stock - virtual_stock_entry.bookings) > 0:
                    possible_stock_adjustment = (virtual_stock_entry.stock - virtual_stock_entry.stock_adjustment - virtual_stock_entry.bookings)
                    if inward <= possible_stock_adjustment:
                        virtual_stock_entry.stock_adjustment = virtual_stock_entry.stock_adjustment + inward
                    else:
                        virtual_stock_entry.stock_adjustment = virtual_stock_entry.stock_adjustment + possible_stock_adjustment
    '''
    current_time = datetime.now()
    orderitem = kwargs.get('orderitem', None)
    
    #Step (1)
    #Do not add select_related. It causes problems in
    #SELECT FOR UPDATE implementation.
    unprocessed_vi_entries = Inventory.objects.filter(
        starts_on__lt = current_time,
        rate_chart = rate_chart,
        dc = dc, 
        type__in = ('backorder','madetoorder','preorder'),
        processed = False).order_by('starts_on')

    count_unprocessed_vi = len(unprocessed_vi_entries)
    unprocessed_vi_entries = unprocessed_vi_entries.for_update()
    current_unprocessed_vi_entry_iter = 0
    overall_adjustment_in_vi = get_overall_adjustment_in_vi(unprocessed_vi_entries)

    #Step (2)
    inward_adjustment = inward
    #Step 2(a)
    order_queue = get_order_queue(request, 
        rate_chart = rate_chart, 
        dc = dc)
    
    #Step 2(b)
    if order_queue:
        for item in order_queue:
            if inward_adjustment:
                quantity = item.stock_to_be_allocated
                active_inventory = get_active_inventory_entries(rate_chart, dc)
                physical_stock = Decimal('0')
                if not ((inward_adjustment-quantity) >= Decimal('0')):
                    physical_inventory = active_inventory['physical']
                    physical_stock = physical_inventory.get_available_stock()
                '''
                Check if order in current iteration of order queue can be flown to SAP
                or not. If yes, then do following actions, else check next one.
                '''
                if ((inward_adjustment + physical_stock) - quantity) >= Decimal('0'):
                    '''
                    Now, there are two cases. 
                    1) orderitem quantity <= adjustment:
                        Only processing will be done on current_unprocessed_entry.
                    2) orderitem quantity > adjustment:
                        Now, processing has to be done on current_unprocessed_entry 
                        for adjustment. For (orderitem quantity - adjustment), process 
                        next entry from unprocessed V.I. entry list.
                    '''
                    oi_quantity = quantity
                    vi_adjustment_list = []
                    while current_unprocessed_vi_entry_iter < count_unprocessed_vi:
                        current_unprocessed_entry = unprocessed_vi_entries[current_unprocessed_vi_entry_iter]
                        adjustment = current_unprocessed_entry.get_remaining_booking_adjustment()
                        if adjustment:
                            if quantity <= adjustment:
                                adjustment_dict = {'inventory':current_unprocessed_entry, 
                                    'quantity':quantity,
                                    'processed':False}
                                vi_adjustment_list.append(adjustment_dict)
                                quantity = Decimal('0')
                                break
                            else:
                                adjustment_dict = {'inventory':current_unprocessed_entry, 
                                    'quantity':adjustment,
                                    'processed':True}
                                vi_adjustment_list.append(adjustment_dict)
                                quantity -= adjustment
                                current_unprocessed_vi_entry_iter += 1
                        else:
                            current_unprocessed_vi_entry_iter += 1

                    vi_adjustment(request, item.orderitem, vi_adjustment_list, sap_event)
                    
                    #Compute inward_adjustment
                    if oi_quantity <= inward_adjustment:
                        #Order fulfilled using inward stock in SAP.
                        inward_adjustment -= oi_quantity
                    else:
                        #Order fulfilled using inward stock in SAP plus 
                        #remaining physical stock in SAP.
                        
                        #For (oi_quantity-inward_adjustment), deduct physical stock.
                        physical_inventory.block_inventory(request, 
                            quantity = (oi_quantity - inward_adjustment),
                            sap_event = sap_event)
                        
                        #Set inward_adjustment = 0
                        inward_adjustment = Decimal('0')
                        
                    #Set stock_allocated=True for this orderitem in InventoryDcLspResolution.
                    item.set_dclsp_stock_allocated_flag(request,
                        sap_event = sap_event)

                    if item.orderitem.sap_order_item and \
                        item.orderitem.sap_order_item.status != 'awaiting delivery creation':
                        item.orderitem.sap_order_item.move_state(request,
                            new_state='awaiting delivery creation')

                    #Create order XML, if stock has been allocated for 
                    #all the orderitems.
                    create_order_xml(request, item.orderitem)
            else:
                '''
                As all the inward quantity is utilised, no need to check for
                remaining entries in order queue, so break.
                '''
                break

    #Step (3)
    if inward_adjustment:
        active_inventory = get_active_inventory_entries(rate_chart, dc)
        #Step 3(a)
        physical_inventory = active_inventory['physical']
        #Step 3(b)
        virtual_inventory = active_inventory['virtual']
        #Step 3(c)(i)
        physical_inventory.update_physical_stock(request, 
            stock = inward_adjustment,
            sap_event = sap_event)
        #Step 3(c)(ii)
        if virtual_inventory:
            possible_stock_adjustment = (virtual_inventory.stock - virtual_inventory.stock_adjustment - virtual_inventory.bookings)
            if possible_stock_adjustment > Decimal('0'):
                if inward_adjustment <= possible_stock_adjustment:
                    virtual_inventory.perform_stock_adjustment(request, 
                        stock_adjustment = inward_adjustment,
                        sap_event = sap_event)
                else:
                    virtual_inventory.perform_stock_adjustment(request, 
                        stock_adjustment = possible_stock_adjustment,
                        sap_event = sap_event)

    '''
    Now check if the product was outofstock before doing the adjusment
    and now it is instock. If yes, then set 
    seller_rate_chart.stock_status = instock and run update solr index.
    '''
    if rate_chart.stock_status == 'outofstock':
        is_available_for_sale = rate_chart.is_available_for_sale(request)
        if is_available_for_sale:
            rate_chart.stock_status = 'instock'
            rate_chart.save(using='default')
            product = rate_chart.product
            product.update_solr_index()
        
def outward_event(request, rate_chart, dc, outward, sap_event):
    '''
    Expected Parameters:
        1) DC from which outward event has been received
        2) Outward quantity
        3) Rate chart

    Update outward = current_outward + outward
    '''
    if outward:
        #Get the type = 'physical' entry for (rate_chart,dc) combination.
        inventory = Inventory.objects.filter(
            rate_chart = rate_chart,
            dc = dc,
            type = 'physical')
        if inventory:
            inventory = inventory.for_update()[0]
        else:
            inventory = Inventory.objects.create(
                rate_chart = rate_chart,
                dc = dc,
                type = 'physical',
                starts_on = datetime(1111,1,1),
                ends_on = datetime(9999,12,31),
                stock = 0)
        
        #Add outward adjustment to inventory.outward
        inventory.update_outward(request,
            outward = outward,
            sap_event = sap_event)

    '''
    Now check if the product was instock before doing the adjusment
    and now it is outstock. If yes, then set 
    seller_rate_chart.stock_status = outofstock and run update solr index.
    '''
    if rate_chart.stock_status == 'instock':
        is_available_for_sale = rate_chart.is_available_for_sale(request)
        if not is_available_for_sale:
            rate_chart.stock_status = 'outofstock'
            rate_chart.save(using='default')
            product = rate_chart.product
            product.update_solr_index()

