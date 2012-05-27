# Create your views here.
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Avg, Max, Min, Count
from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader
from django.http import Http404, HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import *
from django.contrib.auth import login as auth_login
from django.contrib  import auth
from django.core.mail import send_mail
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings
from django.db.models import Q, Sum
from django import forms
from django.forms.models import modelformset_factory
from decimal import Decimal, ROUND_UP
from django.views.decorators.cache import never_cache
import operator
import gviz_api
import calendar
import re
import ast
import operator
import math
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from sellers.decorators import check_role
import xlrd
from xlrd import XLRDError
from restapi import APIManager
from django.utils import simplejson
import logging
from datetime import datetime, timedelta

from inventory.models import Inventory, InventoryLog, InventoryBackorder
from accounts.models import Client, Account
from catalog.models import SellerRateChart, ProductImage
from fulfillment.models import Dc
from utils import utils
from utils.utils import check_dates
from django.core.cache import cache

log = logging.getLogger('fborder')

def log_book_backorder(request, backorder, orderitem, lsp):
    log_fields = {}
    log_fields['dc'] = backorder.dc
    log_fields['rate_chart'] = backorder.rate_chart
    log_fields['modified_by'] = request.client.type
    log_fields['backorder'] = backorder
    log_fields['order'] = orderitem.order
    log_fields['orderitem'] = orderitem
    log_fields['lsp'] = lsp
    
    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)

def log_edit_physical_inventory(request, inventory,
    was_is_active, new_is_active):
    log_fields = {}
    
    log_fields['was_is_active'] = was_is_active
    log_fields['new_is_active'] = new_is_active

    log_fields['dc'] = inventory.dc
    log_fields['rate_chart'] = inventory.rate_chart
    log_fields['modified_by'] = 'sellershub'
    log_fields['user'] = request.user
    log_fields['inventory'] = inventory
    log_fields['was_stock'] = inventory.stock
    log_fields['was_starts_on'] = inventory.starts_on
    log_fields['was_ends_on'] = inventory.ends_on
    log_fields['was_expected_on'] = inventory.expected_on
    log_fields['was_bookings'] = inventory.bookings
    log_fields['was_outward'] = inventory.outward
    log_fields['was_stock_adjustment'] = inventory.stock_adjustment
    log_fields['was_bookings_adjustment'] = inventory.bookings_adjustment
    log_fields['was_threshold'] = inventory.threshold
    log_fields['new_threshold'] = inventory.threshold
    log_fields['new_starts_on'] = inventory.starts_on
    log_fields['new_ends_on'] = inventory.ends_on
    log_fields['new_expected_on'] = inventory.expected_on
    log_fields['new_stock'] = inventory.stock
    log_fields['new_bookings'] = inventory.bookings
    log_fields['new_outward'] = inventory.outward
    log_fields['new_stock_adjustment'] = inventory.stock_adjustment
    log_fields['new_bookings_adjustment'] = inventory.bookings_adjustment
    
    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)

def log_edit_virtual_inventory(request, inventory, was_is_active, new_is_active,
    was_starts_on, new_starts_on, was_ends_on, new_ends_on, 
    was_expected_on, new_expected_on, was_expected_in, new_expected_in):
    log_fields = {}
    
    log_fields['was_is_active'] = was_is_active
    log_fields['new_is_active'] = new_is_active
    log_fields['was_starts_on'] = was_starts_on
    log_fields['new_starts_on'] = new_starts_on
    log_fields['was_ends_on'] = was_ends_on
    log_fields['new_ends_on'] = new_ends_on
    log_fields['was_expected_on'] = was_expected_on
    log_fields['new_expected_on'] = new_expected_on
    log_fields['was_expected_in'] = was_expected_in
    log_fields['new_expected_in'] = new_expected_in

    log_fields['dc'] = inventory.dc
    log_fields['rate_chart'] = inventory.rate_chart
    log_fields['modified_by'] = 'sellershub'
    log_fields['user'] = request.user
    log_fields['inventory'] = inventory
    log_fields['was_stock'] = inventory.stock
    log_fields['was_bookings'] = inventory.bookings
    log_fields['was_outward'] = inventory.outward
    log_fields['was_threshold'] = inventory.threshold
    log_fields['was_stock_adjustment'] = inventory.stock_adjustment
    log_fields['was_bookings_adjustment'] = inventory.bookings_adjustment
    log_fields['new_stock'] = inventory.stock
    log_fields['new_bookings'] = inventory.bookings
    log_fields['new_outward'] = inventory.outward
    log_fields['new_threshold'] = inventory.threshold
    log_fields['new_stock_adjustment'] = inventory.stock_adjustment
    log_fields['new_bookings_adjustment'] = inventory.bookings_adjustment
    
    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)

def log_add_virtual_inventory(request, inventory):
    log_fields = {}

    log_fields['dc'] = inventory.dc
    log_fields['rate_chart'] = inventory.rate_chart
    log_fields['modified_by'] = 'sellershub'
    log_fields['user'] = request.user
    log_fields['inventory'] = inventory

    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)

def log_increment_physical_inventory(request, inventory, orderitem, lsp, was_stock, new_stock):
    log_fields = {}

    log_fields['was_stock'] = was_stock
    log_fields['new_stock'] = new_stock

    log_fields['dc'] = inventory.dc
    log_fields['rate_chart'] = inventory.rate_chart
    log_fields['modified_by'] = request.client.type
    log_fields['inventory'] = inventory
    log_fields['order'] = orderitem.order
    log_fields['orderitem'] = orderitem
    log_fields['lsp'] = lsp
    log_fields['was_starts_on'] = inventory.starts_on
    log_fields['was_ends_on'] = inventory.ends_on
    log_fields['was_expected_on'] = inventory.expected_on
    log_fields['was_bookings'] = inventory.bookings
    log_fields['was_outward'] = inventory.outward
    log_fields['was_threshold'] = inventory.threshold
    log_fields['was_stock_adjustment'] = inventory.stock_adjustment
    log_fields['was_bookings_adjustment'] = inventory.bookings_adjustment
    log_fields['new_starts_on'] = inventory.starts_on
    log_fields['new_ends_on'] = inventory.ends_on
    log_fields['new_expected_on'] = inventory.expected_on
    log_fields['new_bookings'] = inventory.bookings
    log_fields['new_outward'] = inventory.outward
    log_fields['new_threshold'] = inventory.threshold
    log_fields['new_stock_adjustment'] = inventory.stock_adjustment
    log_fields['new_bookings_adjustment'] = inventory.bookings_adjustment
    
    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)

def log_block_inventory(request, inventory, orderitem, lsp, sap_event, 
    was_bookings, new_bookings):
    log.info('@@@@@ Inside log_block_inventory for inventory.id = %s' % inventory.id)
    log_fields = {}

    log_fields['was_bookings'] = was_bookings
    log_fields['new_bookings'] = new_bookings
    
    log_fields['dc'] = inventory.dc
    log_fields['rate_chart'] = inventory.rate_chart
    log_fields['modified_by'] = request.client.type
    log_fields['inventory'] = inventory

    if orderitem:
        log_fields['order'] = orderitem.order
        log_fields['orderitem'] = orderitem

    if sap_event:
        log_fields['sap_event'] = sap_event

    log_fields['lsp'] = lsp
    log_fields['was_stock'] = inventory.stock
    log_fields['new_stock'] = inventory.stock
    log_fields['was_starts_on'] = inventory.starts_on
    log_fields['was_ends_on'] = inventory.ends_on
    log_fields['was_expected_on'] = inventory.expected_on
    log_fields['was_outward'] = inventory.outward
    log_fields['was_threshold'] = inventory.threshold
    log_fields['was_stock_adjustment'] = inventory.stock_adjustment
    log_fields['was_bookings_adjustment'] = inventory.bookings_adjustment
    log_fields['new_starts_on'] = inventory.starts_on
    log_fields['new_ends_on'] = inventory.ends_on
    log_fields['new_expected_on'] = inventory.expected_on
    log_fields['new_outward'] = inventory.outward
    log_fields['new_threshold'] = inventory.threshold
    log_fields['new_stock_adjustment'] = inventory.stock_adjustment
    log_fields['new_bookings_adjustment'] = inventory.bookings_adjustment
    
    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)

def log_increment_virtual_inventory(request, inventory, orderitem, lsp, 
    was_stock_adjustment, new_stock_adjustment, 
    was_bookings_adjustment, new_bookings_adjustment):
    log_fields = {}
    
    log_fields['was_stock_adjustment'] = was_stock_adjustment
    log_fields['new_stock_adjustment'] = new_stock_adjustment
    log_fields['was_bookings_adjustment'] = was_bookings_adjustment
    log_fields['new_bookings_adjustment'] = new_bookings_adjustment

    log_fields['was_bookings'] = inventory.bookings
    log_fields['new_bookings'] = inventory.bookings
    log_fields['dc'] = inventory.dc
    log_fields['rate_chart'] = inventory.rate_chart
    log_fields['modified_by'] = request.client.type
    log_fields['inventory'] = inventory
    log_fields['order'] = orderitem.order
    log_fields['orderitem'] = orderitem
    log_fields['lsp'] = lsp
    log_fields['was_stock'] = inventory.stock
    log_fields['new_stock'] = inventory.stock
    log_fields['was_starts_on'] = inventory.starts_on
    log_fields['was_ends_on'] = inventory.ends_on
    log_fields['was_expected_on'] = inventory.expected_on
    log_fields['was_outward'] = inventory.outward
    log_fields['was_threshold'] = inventory.threshold
    log_fields['new_starts_on'] = inventory.starts_on
    log_fields['new_ends_on'] = inventory.ends_on
    log_fields['new_expected_on'] = inventory.expected_on
    log_fields['new_outward'] = inventory.outward
    log_fields['new_threshold'] = inventory.threshold
    
    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)
  
def log_backorder(request, inventory_backorder, orderitem, lsp):
    log_fields = {}
    log_fields['dc'] = inventory_backorder.dc
    log_fields['rate_chart'] = inventory_backorder.rate_chart
    log_fields['modified_by'] = request.client.type
    log_fields['backorder'] = inventory_backorder
    log_fields['order'] = orderitem.order
    log_fields['orderitem'] = orderitem
    log_fields['lsp'] = lsp
    
    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)

def log_sto_ack(request, sto, sap_event,
    was_sto_ack_received, new_sto_ack_received):
    log_fields = {}
    modified_by = 'sap'
    try:
        if request.client.type:
            modified_by = request.client.type
    except:
        pass
    log_fields['dc'] = sto.from_dc
    log_fields['rate_chart'] = sto.orderitem.seller_rate_chart
    log_fields['modified_by'] = 'sap'
    log_fields['orderitem'] = sto.orderitem
    log_fields['order'] = sto.orderitem.order
    log_fields['sto'] = sto
    log_fields['sap_event'] = sap_event
    log_fields['was_sto_ack_received'] = was_sto_ack_received
    log_fields['new_sto_ack_received'] = new_sto_ack_received

    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)

def log_set_dclsp_stock_allocated_flag(request, dclsp, sap_event,
        was_dclsp_stock_allocated, new_dclsp_stock_allocated):
    log_fields = {}
    modified_by = 'sap'
    try:
        if request.client.type:
            modified_by = request.client.type
    except:
        pass
    log_fields['dc'] = dclsp.dc
    log_fields['lsp'] = dclsp.lsp
    log_fields['rate_chart'] = dclsp.orderitem.seller_rate_chart
    log_fields['modified_by'] = modified_by
    log_fields['orderitem'] = dclsp.orderitem
    log_fields['order'] = dclsp.orderitem.order
    log_fields['dclsp'] = dclsp
    log_fields['sap_event'] = sap_event
    log_fields['was_dclsp_stock_allocated'] = was_dclsp_stock_allocated
    log_fields['new_dclsp_stock_allocated'] = new_dclsp_stock_allocated

    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)

def log_set_sto_stock_allocated_flag(request, sto, sap_event,
        was_sto_stock_allocated, new_sto_stock_allocated):
    log_fields = {}
    modified_by = 'sap'
    try:
        if request.client.type:
            modified_by = request.client.type
    except:
        pass
    log_fields['dc'] = sto.from_dc
    log_fields['rate_chart'] = sto.orderitem.seller_rate_chart
    log_fields['modified_by'] = modified_by
    log_fields['orderitem'] = sto.orderitem
    log_fields['order'] = sto.orderitem.order
    log_fields['sto'] = sto
    log_fields['sap_event'] = sap_event
    log_fields['was_sto_stock_allocated'] = was_sto_stock_allocated
    log_fields['new_sto_stock_allocated'] = new_sto_stock_allocated

    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)

def log_booking_adjustments(request, inventory, sap_event,
    orderitem,  was_bookings_adjustment, new_bookings_adjustment):
    log_fields = {}
    modified_by = 'sap'
    try:
        if request.client.type:
            modified_by = request.client.type
    except:
        pass

    log_fields['was_bookings_adjustment'] = was_bookings_adjustment
    log_fields['new_bookings_adjustment'] = new_bookings_adjustment
    
    log_fields['dc'] = inventory.dc
    log_fields['rate_chart'] = inventory.rate_chart
    log_fields['modified_by'] = modified_by
    log_fields['inventory'] = inventory
    log_fields['order'] = orderitem.order
    log_fields['orderitem'] = orderitem
    log_fields['sap_event'] = sap_event
    log_fields['was_stock'] = inventory.stock
    log_fields['new_stock'] = inventory.stock
    log_fields['was_bookings'] = inventory.bookings
    log_fields['new_bookings'] = inventory.bookings
    log_fields['was_starts_on'] = inventory.starts_on
    log_fields['was_ends_on'] = inventory.ends_on
    log_fields['was_expected_on'] = inventory.expected_on
    log_fields['was_outward'] = inventory.outward
    log_fields['was_threshold'] = inventory.threshold
    log_fields['new_starts_on'] = inventory.starts_on
    log_fields['new_ends_on'] = inventory.ends_on
    log_fields['new_expected_on'] = inventory.expected_on
    log_fields['new_outward'] = inventory.outward
    log_fields['new_threshold'] = inventory.threshold
    log_fields['was_stock_adjustment'] = inventory.stock_adjustment
    log_fields['new_stock_adjustment'] = inventory.stock_adjustment
    
    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)

def log_stock_adjustment(request, inventory, sap_event,
    was_stock_adjustment, new_stock_adjustment):
    log_fields = {}

    log_fields['was_stock_adjustment'] = was_stock_adjustment
    log_fields['new_stock_adjustment'] = new_stock_adjustment
    
    log_fields['dc'] = inventory.dc
    log_fields['rate_chart'] = inventory.rate_chart
    log_fields['modified_by'] = 'sap'
    log_fields['inventory'] = inventory
    log_fields['sap_event'] = sap_event
    log_fields['was_stock'] = inventory.stock
    log_fields['new_stock'] = inventory.stock
    log_fields['was_bookings'] = inventory.bookings
    log_fields['new_bookings'] = inventory.bookings
    log_fields['was_starts_on'] = inventory.starts_on
    log_fields['was_ends_on'] = inventory.ends_on
    log_fields['was_expected_on'] = inventory.expected_on
    log_fields['was_outward'] = inventory.outward
    log_fields['was_threshold'] = inventory.threshold
    log_fields['new_starts_on'] = inventory.starts_on
    log_fields['new_ends_on'] = inventory.ends_on
    log_fields['new_expected_on'] = inventory.expected_on
    log_fields['new_outward'] = inventory.outward
    log_fields['new_threshold'] = inventory.threshold
    log_fields['was_bookings_adjustment'] = inventory.bookings_adjustment
    log_fields['new_bookings_adjustment'] = inventory.bookings_adjustment
    
    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)

def log_update_physical_stock(request, inventory, sap_event,
    was_stock, new_stock):
    log_fields = {}
    modified_by = 'sap'
    try:
        if request.client.type:
            modified_by = request.client.type
    except:
        pass

    log_fields['was_stock'] = was_stock
    log_fields['new_stock'] = new_stock
    
    log_fields['dc'] = inventory.dc
    log_fields['rate_chart'] = inventory.rate_chart
    log_fields['modified_by'] = modified_by
    log_fields['inventory'] = inventory
    log_fields['sap_event'] = sap_event
    log_fields['was_bookings'] = inventory.bookings
    log_fields['new_bookings'] = inventory.bookings
    log_fields['was_starts_on'] = inventory.starts_on
    log_fields['was_ends_on'] = inventory.ends_on
    log_fields['was_expected_on'] = inventory.expected_on
    log_fields['was_outward'] = inventory.outward
    log_fields['was_threshold'] = inventory.threshold
    log_fields['new_starts_on'] = inventory.starts_on
    log_fields['new_ends_on'] = inventory.ends_on
    log_fields['new_expected_on'] = inventory.expected_on
    log_fields['new_outward'] = inventory.outward
    log_fields['new_threshold'] = inventory.threshold
    log_fields['was_bookings_adjustment'] = inventory.bookings_adjustment
    log_fields['new_bookings_adjustment'] = inventory.bookings_adjustment
    log_fields['was_stock_adjustment'] = inventory.stock_adjustment
    log_fields['new_stock_adjustment'] = inventory.stock_adjustment

    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)

def log_update_outward(request, inventory, sap_event,
    was_outward, new_outward):
    log_fields = {}

    log_fields['was_outward'] = was_outward
    log_fields['new_outward'] = new_outward
    
    log_fields['dc'] = inventory.dc
    log_fields['rate_chart'] = inventory.rate_chart
    log_fields['modified_by'] = 'sap'
    log_fields['inventory'] = inventory
    log_fields['sap_event'] = sap_event
    log_fields['was_stock'] = inventory.stock
    log_fields['new_stock'] = inventory.stock
    log_fields['was_bookings'] = inventory.bookings
    log_fields['new_bookings'] = inventory.bookings
    log_fields['was_starts_on'] = inventory.starts_on
    log_fields['was_ends_on'] = inventory.ends_on
    log_fields['was_expected_on'] = inventory.expected_on
    log_fields['was_threshold'] = inventory.threshold
    log_fields['new_starts_on'] = inventory.starts_on
    log_fields['new_ends_on'] = inventory.ends_on
    log_fields['new_expected_on'] = inventory.expected_on
    log_fields['new_threshold'] = inventory.threshold
    log_fields['was_bookings_adjustment'] = inventory.bookings_adjustment
    log_fields['new_bookings_adjustment'] = inventory.bookings_adjustment
    log_fields['was_stock_adjustment'] = inventory.stock_adjustment
    log_fields['new_stock_adjustment'] = inventory.stock_adjustment
    
    inventory_log = InventoryLog()
    inventory_log.set_inventorylog(log_fields)

def validate_articleid(article_id):
    errors = []
    try:
        article_id = int(article_id)
    except:
        errors.append('Please enter valid value for Articleid/SKU!')
    return errors

def get_seller_rate_chart(seller, article_id):
    rate_chart, errors = None, []
    if article_id:
        try:
            rate_chart = SellerRateChart.objects.select_related(
                'product__title','category__name').get(
                (Q(article_id = article_id)|Q(sku = article_id)),
                seller = seller)
        except SellerRateChart.MultipleObjectsReturned:
            errors.append('Multiple active articles maintained for Articleid/SKU = %s' % article_id)
        except SellerRateChart.DoesNotExist:
            errors.append('No active article maintained for Articleid/SKU = %s' % article_id)
    else:
        errors.append('Please enter Article Id/SKU!')

    return rate_chart, errors

def show_all_inventory_levels(request, **kwargs):
    #Variables
    errors, inventory_levels, backorder_levels = [], [], []
    product, product_image, rate_chart = None, None, None
    seller = request.session.get('seller')
    if seller:
        seller = seller[0]
    if request.method == 'POST' and seller:
        article_id = request.POST.get('article_id', '')
        errors = validate_articleid(article_id)
        if not errors:
            rate_chart, errors = get_seller_rate_chart(seller, article_id)
            if rate_chart and (not errors):
                product = rate_chart.product
                product_image = ProductImage.objects.filter(product=product)
                if product_image:
                    product_image = product_image[0]
                inventory_levels = rate_chart.get_all_inventory_levels()
                #backorder_levels = rate_chart.get_all_backorderable_entries()
                if not inventory_levels and not backorder_levels:
                    errors.append('No active inventory levels maintained for %s.' % rate_chart.product.title)
    
    inventory_dict = {
        'errors' : errors,
        'inventory_levels' : inventory_levels,
        'backorder_levels' : backorder_levels,
        'current_time' : datetime.now(),
        'product' : product,
        'product_image' : product_image,
        'rate_chart' : rate_chart,
        'url' : request.get_full_path(),
        'client_display_name':request.client.client.name
    }
    return render_to_response('inventory/all_inventory3.html', inventory_dict, context_instance=RequestContext(request))  

def get_inventory_object(id):
    inventory = Inventory.objects.select_related('rate_chart','dc').get(pk=id)
    return inventory

def edit_physical_inventory(request, **kwargs):
    #Variables
    inventory, errors, entry_edited_successfully = None, [], False

    id = request.GET.get('id')
    if id:
        inventory = get_inventory_object(id)

    if request.method == 'POST':
        id = request.POST['id']
        is_active = request.POST['is_active']
        
        inventory = get_inventory_object(id)
        #Now set the values for is_active
        if is_active == 'yes':
            is_active = True
        else:#is_active == 'no'
            is_active = False

        #Check if current value for is_active are same 
        #as newly updated values. If yes, then skip, else update.
        if inventory.is_active == is_active:
            pass
        else:
            was_is_active = inventory.is_active
            inventory.is_active = is_active
            inventory.save()
            new_is_active = inventory.is_active
            log_edit_physical_inventory(request, inventory, 
                was_is_active, new_is_active)
            
            rate_chart = inventory.rate_chart
            is_available_for_sale = rate_chart.is_available_for_sale(None)
            if rate_chart.stock_status in ['outofstock','notavailable'] and \
                is_available_for_sale:
                rate_chart.stock_status = 'instock'
                rate_chart.save()
                product = rate_chart.product
                product.update_solr_index()
            elif rate_chart.stock_status == 'instock' and \
                not is_available_for_sale:
                rate_chart.stock_status = 'outofstock'
                rate_chart.save()
                product = rate_chart.product
                product.update_solr_index()

        entry_edited_successfully = True
    
    inventory_dict = {
        'inventory' : inventory,
        'errors' : errors,
        'entry_edited_successfully':entry_edited_successfully,
        'url' : request.get_full_path(),
        'client_display_name':request.client.client.name
    }
   
    return render_to_response('inventory/edit_physical_inventory.html', 
        inventory_dict, 
        context_instance=RequestContext(request))  

def delete_virtual_inventory(request, **kwargs):
    #Variables
    inventory, errors, entry_deleted_successfully = None, [], False
    seller = kwargs.get('seller', None)
    id = request.GET.get('id')
    if id:
        inventory = get_inventory_object(id)

    if request.method == 'POST':
        id = request.POST['id']
        inventory = get_inventory_object(id)
        if inventory:
            inventory.delete()
            entry_deleted_successfully = True
        else:
            errors.append('Virtual Stock Entry cannot be deleted.')
    
    inventory_dict = {
        'inventory' : inventory,
        'errors' : errors,
        'entry_deleted_successfully':entry_deleted_successfully,
        'url' : request.get_full_path(),
        'client_display_name':request.client.client.name
    }
   
    return render_to_response('inventory/delete_virtual_inventory.html', 
        inventory_dict, 
        context_instance=RequestContext(request))  

def edit_virtual_inventory(request, **kwargs):
    seller = kwargs.get('seller', None)
    #Variables
    inventory, errors, entry_edited_successfully = None, [], False
    current_time = datetime.now()

    id = request.GET.get('id')
    if id:
        inventory = get_inventory_object(id)

    if request.method == 'POST':
        id = request.POST['id']
        stock = request.POST['stock']
        starts_on = request.POST["starts_on"]
        ends_on = request.POST["ends_on"]
        expected_on = request.POST["expected_on"]
        expected_in = request.POST["expected_in"]
        is_active = request.POST['is_active']

        #Perform data validation
        try:
            starts_on = date_formatting(starts_on)
        except:
            errors.append('Wrong value set for Starts On = %s' % starts_on)

        try:
            ends_on = date_formatting(ends_on)
        except:
            errors.append('Wrong value set for Ends On = %s' % ends_on)

        formatted_expected_on = None
        try:
            expected_on = date_formatting(expected_on)
            formatted_expected_on = expected_on
            if expected_on < starts_on:
                errors.append('Expected on must be greater than Starts on.')
        except:
            #errors.append('Wrong value set for Expected On = %s' % expected_on)
            pass
        
        formatted_expected_in = None
        try:
            expected_in = number_formatting(expected_in)
            formatted_expected_in = expected_in 
        except:
            #errors.append('Wrong value set for Expected in = %s' % expected_in)
            pass

        if not (formatted_expected_in or formatted_expected_on):
            errors.append('Wrong value set for Expected on/Expected in')
        elif (formatted_expected_on and formatted_expected_in):
            errors.append('Either set Expected on or Expected in')

        try:
            stock = number_formatting(stock)
        except:
            errors.append('Wrong value set for Stock = %s' % stock)

        if starts_on > ends_on:
            errors.append('Starts on must be less than Ends on.')
       
        if not errors:
            #As there are no data validation errors,
            #now check for overlapping timeslot error.
            inventory = get_inventory_object(id)
            conflicting_inventory = get_overlapping_vi_entries(inventory.rate_chart,
                inventory.dc, starts_on, ends_on)
            #This resultset will contains current inventory entry as weell.
            #So exclude that.
            conflicting_inventory = conflicting_inventory.exclude(id=inventory.id)
            if conflicting_inventory:
                errors.append('Cannot have overlapping V.I. entries.')

        if not errors:
            stock_changes = False
            if (inventory.starts_on <= current_time) and (current_time <= inventory.ends_on):
                #Currently active VI entry
                ats = inventory.get_available_stock()
                if stock > ats:
                    inventory.stock += (stock - ats)
                    stock_changes = True
                elif stock < ats:
                    inventory.stock_adjustment += (ats - stock)
                    stock_changes = True
            else:
                inventory.stock = stock
                stock_changes = True
            
            if is_active == 'yes':
                is_active = True
            else:#is_active == 'no'
                is_active = False

            #Check if current values for threshold and is_active are same 
            #as newly updated values. If yes, then skip, else update.
            if stock_changes or not(inventory.is_active == is_active) \
                or not(inventory.starts_on == starts_on)\
                or not(inventory.ends_on == ends_on)\
                or not(inventory.expected_on == expected_on):
                #Set the params
                was_is_active = inventory.is_active
                was_starts_on = inventory.starts_on
                was_ends_on = inventory.ends_on
                was_expected_on = inventory.expected_on
                was_expected_in = inventory.expected_in

                inventory.is_active = is_active
                inventory.starts_on = starts_on
                inventory.ends_on = ends_on
                if formatted_expected_on:
                    inventory.expected_on = formatted_expected_on
                else:
                    inventory.expected_on = None
                if formatted_expected_in:
                    inventory.expected_in = expected_in
                else:
                    inventory.expected_in = None
                inventory.save()

                new_is_active = inventory.is_active
                new_starts_on = inventory.starts_on
                new_ends_on = inventory.ends_on
                new_expected_on = inventory.expected_on
                new_expected_in = inventory.expected_in

                log_edit_virtual_inventory(request, inventory,
                    was_is_active, new_is_active, was_starts_on, new_starts_on,
                    was_ends_on, new_ends_on, was_expected_on, new_expected_on,
                    was_expected_in, new_expected_in)

                entry_edited_successfully = True
                
                rate_chart = inventory.rate_chart
                is_available_for_sale = rate_chart.is_available_for_sale(None)
                if rate_chart.stock_status in ['outofstock','notavailable'] and \
                    is_available_for_sale:
                    rate_chart.stock_status = 'instock'
                    rate_chart.save()
                    product = rate_chart.product
                    product.update_solr_index()
                elif rate_chart.stock_status == 'instock' and \
                    not is_available_for_sale:
                    rate_chart.stock_status = 'outofstock'
                    rate_chart.save()
                    product = rate_chart.product
                    product.update_solr_index()
    
    inventory_dict = {
        'inventory' : inventory,
        'errors' : errors,
        'entry_edited_successfully':entry_edited_successfully,
        'current_time' : current_time,
        'url' : request.get_full_path(),
        'client_display_name':request.client.client.name
        }
   
    return render_to_response('inventory/edit_virtual_inventory.html', 
        inventory_dict, 
        context_instance=RequestContext(request))  

def get_dc_codes(client):
    dc = Dc.objects.filter(client = client)
    if dc:
        dc_codes = [int(str(item.code)) for item in dc]
        return dc_codes
    else:
        return []

def date_formatting(date):
    return datetime.strptime(date,'%d-%m-%Y %H:%M')

def number_formatting(number):
    return int(number)

def get_overlapping_vi_entries(rate_chart, dc, starts_on, ends_on):
    conflicting_inventory = Inventory.objects.filter(
        type = 'virtual',
        rate_chart = rate_chart,
        dc = dc).exclude(
        Q(ends_on__lte = starts_on) |
        Q(starts_on__gte = ends_on))
    return conflicting_inventory

def create_virtual_stock_entry(request, rate_chart, dc, stock, starts_on, ends_on):
    errors, virtual_inventory = [], None
    #First, check whether there is any coflicting entry for VI.
    conflicting_inventory = get_overlapping_vi_entries(rate_chart, 
        dc, starts_on, ends_on)

    if conflicting_inventory:
        errors.append('Cannot have overlapping V.I. entries.')
    else:
        virtual_inventory = Inventory.objects.create(
            rate_chart = rate_chart,
            dc = dc,
            stock = stock,
            type = 'backorder',
            starts_on = starts_on,
            ends_on = ends_on)
        log_add_virtual_inventory(request, virtual_inventory)

    return errors, virtual_inventory

def add_virtual_inventory(request, **kwargs):
    #Variables
    errors, inventory = [], None
    virtual_entry_created = False
    seller = kwargs.get('seller', None)
    if seller:
        seller = seller[0]
    article_id = request.GET.get('article_id','')
    dc = get_dc_codes(request.client.client)
    
    if request.method == 'POST':
        starts_on = request.POST.get("starts_on",None)
        starts_on_hr = request.POST.get("starts_on_hr",None)
        starts_on_min = request.POST.get("starts_on_min",None)

        if starts_on and starts_on.strip():
            starts_on = starts_on + ' ' + starts_on_hr + ':' + starts_on_min
            try:
                starts_on = date_formatting(starts_on)
                if starts_on < datetime.now():
                    errors.append('Starts on must be future time!')
            except:
                errors.append('Wrong value set for Starts On = %s' % starts_on)
        else:
            starts_on = datetime.now()

        ends_on = request.POST.get("ends_on", None)
        ends_on_hr = request.POST.get("ends_on_hr", None)
        ends_on_min = request.POST.get("ends_on_min", None)

        if ends_on and ends_on.strip():
            ends_on = ends_on + ' ' + ends_on_hr + ':' + ends_on_min
            try:
                ends_on = date_formatting(ends_on)
                if starts_on and type(starts_on) == datetime and \
                    ends_on <= starts_on:
                    errors.append('Ends on has to be greater than Starts on.')
            except:
                errors.append('Wrong value set for Ends On = %s' % ends_on)
        else:
            ends_on = datetime(9999,12,31)

        stock = request.POST['stock']
        try:
            stock = number_formatting(stock)
        except:
            errors.append('Wrong value set for Stock = %s' % stock)

        dc_code = request.POST['dc']
        dc = utils.get_dc(dc_code, request.client.client)

        article_id = request.POST['article_id']
        rate_chart, error = get_seller_rate_chart(seller, article_id)
        if error:
            errors += error
        
        if not errors:
            errors, inventory = create_virtual_stock_entry(request, rate_chart, 
                dc, stock, starts_on, ends_on)
            if not errors:
                virtual_entry_created = True
                is_available_for_sale = rate_chart.is_available_for_sale(None)
                if rate_chart.stock_status in ['outofstock','notavailable'] and \
                    is_available_for_sale:
                    rate_chart.stock_status = 'instock'
                    rate_chart.save()
                    product = rate_chart.product
                    product.update_solr_index()
                elif rate_chart.stock_status == 'instock' and \
                    not is_available_for_sale:
                    rate_chart.stock_status = 'outofstock'
                    rate_chart.save()
                    product = rate_chart.product
                    product.update_solr_index()

    inventory_dict = {
        'article_id' : article_id,
        'dc' : dc,
        'errors' : errors,
        'virtual_entry_created' : virtual_entry_created,
        'inventory' : inventory,
        'url' : request.get_full_path(),
        'client_display_name':request.client.client.name
    }
    return render_to_response('inventory/add_vi.html', 
        inventory_dict, context_instance=RequestContext(request))  

def get_backorder_inventory_object(id):
    backorder_entry = InventoryBackorder.objects.get(id=id)
    return backorder_entry
    
def edit_backorderable_entry(request, client_name, seller_name, seller, client_id, profile):
    accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = client_id)
        cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)

    backorder, errors, entry_edited_successfully = None, [], False
    id = request.GET.get('id')
    if id:
        backorder = get_backorder_inventory_object(id)
    if request.method == 'POST':
        id = request.POST['id']
        expected_in = request.POST['expected_in']
        is_active = request.POST['is_active']
        backorderable = request.POST['backorderable']
        backorder = get_backorder_inventory_object(id)

        try:
            expected_in = int(str(expected_in).strip())
        except:
            errors.append('Wrong value set for Expected in = %s' % expected_in)

        if is_active == 'yes':
            is_active = True
        else:#is_active == 'no'
            is_active = False

        if backorderable == 'yes':
            backorderable = True
        else:#backorderable == 'no'
            backorderable = False

        if backorder.expected_in == expected_in and \
            backorder.is_active == is_active and \
            backorder.backorderable == backorderable:
            pass
        else:
            backorder.expected_in = expected_in
            backorder.is_active = is_active
            backorder.backorderable = backorderable
            backorder.save()
        entry_edited_successfully = True
    
    inventory_dict = {
        'backorder' : backorder,
        'errors' : errors,
        'entry_edited_successfully' : entry_edited_successfully,
        'accounts' : accounts,
        'url' : request.get_full_path(),
        'client_name':client_name,
        'seller_name':seller_name,
        'loggedin':True,
        'clients':clients,
        'client_display_name':Client.objects.filter(slug=client_name)[0].name,
    }
    
    return render_to_response('inventory/edit_backorder.html', 
        inventory_dict, context_instance=RequestContext(request))  
    
def add_backorderable_entry(request, client_name, seller_name, seller, client_id, profile):
    accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = client_id)
        cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    id = request.GET['id']
    inventory = get_inventory_object(id)
    if request.method == 'POST':
        id = request.POST['id']
        log.info(id)
        if id == '1244':
            return HttpResponse('/inventory/%s/%s/all_inventory' % (client_name, seller_name))
    
    inventory_dict = {
        'inventory':inventory,
        'accounts' : accounts,
        'url' : request.get_full_path(),
        'client_name':client_name,
        'seller_name':seller_name,
        'loggedin':True,
        'clients':clients,
        'client_display_name':Client.objects.filter(slug=client_name)[0].name,
    }
    
    return render_to_response('inventory/edit_inventory.html', inventory_dict, context_instance=RequestContext(request))  
    
def sto_report(request, client_name, seller_name, seller, client_id, profile):
    dates = check_dates(request)
    search_trend, from_date, to_date = dates['search_trend'], dates['start_date'], dates['end_date']
    if not from_date:
        from_date = datetime(year=2012, month=2, day=23)
    if not to_date:
        to_date = datetime.now()
    from django.db import connection
    accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = client_id)
        cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)

    cursor = connection.cursor()
    query = '''select from_dc.code as from_dc_code, 
            to_dc.code as to_dc_code, src.article_id, sum(oi.qty) as qty from 
            inventory_inventorystolog as sto 
            inner join fulfillment_dc as from_dc on (sto.from_dc_id = from_dc.id) 
            inner join fulfillment_dc as to_dc on (sto.to_dc_id = to_dc.id)
            inner join orders_orderitem oi on (sto.orderitem_id = oi.id) 
            inner join catalog_sellerratechart src on (oi.seller_rate_chart_id = src.id) 
            where sto.ack_received = false and sto.stock_allocated = true and  
            sto.modified_on > '%s' and sto.modified_on < '%s'
            group by from_dc_code, to_dc_code, article_id order by to_dc_code'''
    from_date = from_date.strftime('%Y-%m-%d') + ' 00:00:00'
    to_date = to_date.strftime('%Y-%m-%d') + ' 23:59:59'
    query = query % (from_date, to_date)

    cursor.execute(query)
    sto = cursor.fetchall()

    sto_dict = {
        'sto' : sto,
        'search_trend':search_trend,
        'from_date':from_date,
        'to_date':to_date,
        'accounts' : accounts,
        'url' : request.get_full_path(),
        'client_name':client_name,
        'seller_name':seller_name,
        'loggedin':True,
        'clients':clients,
        'client_display_name':Client.objects.filter(slug=client_name)[0].name,
    }
    
    return render_to_response('inventory/sto_report.html', 
        sto_dict, context_instance=RequestContext(request))  
   
def get_temporary_file_path():
    import tempfile
    tf = tempfile.NamedTemporaryFile()
    path = tf.name
    tf.close()
    return path

def save_uploaded_file(f):
    path_to_save = get_temporary_file_path()
    fp = open(path_to_save, 'w')
    for chunk in f.chunks():
        fp.write(chunk)
    fp.close()
    return path_to_save

def validate_backorder_excel_entry(article_id, dc, stock, starts_on, ends_on, 
        row_num=1):
    from datetime import timedelta
    validated_entry, errors = {}, []
    try:
        validated_entry['article_id'] = number_formatting(str(article_id).strip().split('.')[0])
    except:
        errors.append('Wrong value set for Articleid = %s in row number %s' 
            % (article_id, row_num))

    try:
        validated_entry['dc'] = number_formatting(str(dc).strip().split('.')[0])
    except:
        errors.append('Wrong value set for DC = %s in row number %s' 
            % (dc, row_num))

    try:
        validated_entry['stock'] = number_formatting(str(stock).strip().split('.')[0])
        if validated_entry['stock'] <= 0:
            errors.append('Stock has to be > 0 in row number %s' % row_num)
    except:
        errors.append('Wrong value set for Stock = %s in row number %s' 
            % (stock, row_num))

    if starts_on and starts_on.strip():
        try:
            validated_entry['starts_on'] = date_formatting(str(starts_on).strip())
            if not validated_entry['starts_on'] > datetime.now():
                errors.appned('Starts on must be future timestamp')
        except:
            errors.append('Wrong value set for Starts on = %s in row number %s' 
                % (starts_on, row_num))
    else:
        validated_entry['starts_on'] = datetime.now() + timedelta(minutes=-2)

    if ends_on and ends_on.strip():
        try:
            validated_entry['ends_on'] = date_formatting(str(ends_on).strip())
        except:
            errors.append('Wrong value set for Ends on = %s in row number %s' 
                % (ends_on, row_num))
    else:
        validated_entry['ends_on'] = datetime(9999,12,31)

    if validated_entry.get('starts_on',None) and \
        validated_entry.get('ends_on',None):
        #Starts on must be < Ends on.
        if validated_entry['starts_on'] >= validated_entry['ends_on']:
            errors.append('Starts on must be less than Ends on in row number %s' 
                % row_num)

    return validated_entry, errors


def validate_madetoorder_excel_entry(article_id, dc, stock, starts_on, ends_on, 
        expected_in, row_num=1):
    from datetime import timedelta
    validated_entry, errors = {}, []
    try:
        validated_entry['article_id'] = number_formatting(str(article_id).strip().split('.')[0])
    except:
        errors.append('Wrong value set for Articleid = %s in row number %s' 
            % (article_id, row_num))

    try:
        validated_entry['dc'] = number_formatting(str(dc).strip().split('.')[0])
    except:
        errors.append('Wrong value set for DC = %s in row number %s' 
            % (dc, row_num))

    try:
        validated_entry['stock'] = number_formatting(str(stock).strip().split('.')[0])
        if validated_entry['stock'] <= 0:
            errors.append('Stock has to be > 0 in row number %s' % row_num)
    except:
        errors.append('Wrong value set for Stock = %s in row number %s' 
            % (stock, row_num))

    if starts_on and starts_on.strip():
        try:
            validated_entry['starts_on'] = date_formatting(str(starts_on).strip())
            if not validated_entry['starts_on'] > datetime.now():
                errors.appned('Starts on must be future timestamp')
        except:
            errors.append('Wrong value set for Starts on = %s in row number %s' 
                % (starts_on, row_num))
    else:
        validated_entry['starts_on'] = datetime.now()

    if ends_on and ends_on.strip():
        try:
            validated_entry['ends_on'] = date_formatting(str(ends_on).strip())
        except:
            errors.append('Wrong value set for Ends on = %s in row number %s' 
                % (ends_on, row_num))
    else:
        validated_entry['ends_on'] = datetime(9999,12,31)

    try:
        validated_entry['expected_in'] = number_formatting(str(expected_in).strip().split('.')[0])
        if validated_entry['expected_in'] <= 0:
            errors.append('Expected in has to be > 0 in row number %s' % row_num)
    except:
        errors.append('Wrong value set for Expected in = %s in row number %s' 
            % (expected_in, row_num))

    if validated_entry.get('starts_on',None) and \
        validated_entry.get('ends_on',None):
        #Starts on must be < Ends on.
        if validated_entry['starts_on'] >= validated_entry['ends_on']:
            errors.append('Starts on must be less than Ends on in row number %s' 
                % row_num)

    if validated_entry.get('expected_in', None):
        if validated_entry['expected_in'] >= 30:
            errors.append('Expected in must be less than 30 days in row number %s'
                % row_num)
    
    return validated_entry, errors

def validate_preorder_excel_entry(article_id, dc, stock, starts_on, ends_on, 
        expected_on, row_num=1):
    from datetime import timedelta
    validated_entry, errors = {}, []
    current_time = datetime.now()
    try:
        validated_entry['article_id'] = number_formatting(str(article_id).strip().split('.')[0])
    except:
        errors.append('Wrong value set for Articleid = %s in row number %s' 
            % (article_id, row_num))

    try:
        validated_entry['dc'] = number_formatting(str(dc).strip().split('.')[0])
    except:
        errors.append('Wrong value set for DC = %s in row number %s' 
            % (dc, row_num))

    try:
        validated_entry['stock'] = number_formatting(str(stock).strip().split('.')[0])
        if validated_entry['stock'] <= 0:
            errors.append('Stock has to be > 0 in row number %s' % row_num)
    except:
        errors.append('Wrong value set for Stock = %s in row number %s' 
            % (stock, row_num))

    if starts_on and starts_on.strip():
        try:
            validated_entry['starts_on'] = date_formatting(str(starts_on).strip())
            if validated_entry['starts_on'] < current_time:
                errors.appned('Starts on must be future timestamp')
        except:
            errors.append('Wrong value set for Starts on = %s in row number %s' 
                % (starts_on, row_num))
    else:
        validated_entry['starts_on'] = datetime.now()

    try:
        validated_entry['expected_on'] = date_formatting(str(expected_on).strip())
        validated_entry['ends_on'] = validated_entry['expected_on']
        if validated_entry['expected_on'] < current_time:
            errors.appned('Expected on must be future timestamp')
    except:
        errors.append('Wrong value set for Expected on = %s in row number %s' 
            % (expected_on, row_num))

    if ends_on and ends_on.strip():
        try:
            validated_entry['ends_on'] = date_formatting(str(ends_on).strip())
        except:
            errors.append('Wrong value set for Ends on = %s in row number %s' 
                % (ends_on, row_num))

    if validated_entry.get('starts_on',None) and \
        validated_entry.get('ends_on',None):
        #Starts on must be < Ends on.
        if validated_entry['starts_on'] >= validated_entry['ends_on']:
            errors.append('Starts on must be less than Ends on in row number %s' 
                % row_num)

    if validated_entry.get('ends_on', None) and \
        validated_entry.get('expected_on', None):
        if validated_entry['expected_on'] < validated_entry['ends_on']:
            errors.append('Ends on MUST BE <= Expected on in row number %s'
                % row_num)

    if validated_entry.get('starts_on', None) and \
        validated_entry.get('expected_on', None):
        if validated_entry['expected_on'] >= validated_entry['starts_on'] + timedelta(days=30):
            errors.append('Dfference between Expected on and Starts on should not be more \
                than 30 days in row number %s' % row_num)
    
    return validated_entry, errors

def validate_excel_entry(article_id, dc, stock, starts_on, ends_on, 
        expected_on, expected_in, row_num=1):
    from datetime import timedelta
    validated_entry, errors = {}, []
    if article_id:
        try:
            validated_entry['article_id'] = number_formatting(str(article_id).strip().split('.')[0])
        except:
            errors.append('Wrong value set for Articleid = %s in row number %s' 
                % (article_id, row_num))

    if dc:
        try:
            validated_entry['dc'] = number_formatting(str(dc).strip().split('.')[0])
        except:
            errors.append('Wrong value set for DC = %s in row number %s' 
                % (dc, row_num))

    if stock:
        try:
            validated_entry['stock'] = number_formatting(str(stock).strip().split('.')[0])
        except:
            errors.append('Wrong value set for Stock = %s in row number %s' 
                % (stock, row_num))

    if starts_on and starts_on.strip():
        try:
            validated_entry['starts_on'] = date_formatting(str(starts_on).strip())
            if not validated_entry['starts_on'] > datetime.now():
                errors.appned('Starts on must be future timestamp')
        except:
            errors.append('Wrong value set for Starts on = %s in row number %s' 
                % (starts_on, row_num))
    else:
        validated_entry['starts_on'] = datetime.now()

    if ends_on and ends_on.strip():
        try:
            validated_entry['ends_on'] = date_formatting(str(ends_on).strip())
        except:
            errors.append('Wrong value set for Ends on = %s in row number %s' 
                % (ends_on, row_num))
    else:
        validated_entry['ends_on'] = datetime(9999,12,31)

    if expected_on:
        try:
            validated_entry['expected_on'] = date_formatting(str(expected_on).strip())
        except:
            errors.append('Wrong value set for Expeted on = %s in row number %s' 
                % (expected_on, row_num))

    if expected_in:
        try:
            validated_entry['expected_in'] = number_formatting(str(expected_in).strip().split('.')[0])
        except:
            errors.append('Wrong value set for Expected in = %s in row number %s' 
                % (expected_in, row_num))

    if validated_entry.get('starts_on',None) and \
        validated_entry.get('ends_on',None):
        #Starts on must be < Ends on.
        if validated_entry['starts_on'] > validated_entry['ends_on']:
            errors.append('Starts on must be less than Ends on in row number %s' 
                % row_num)

    if validated_entry.get('ends_on', None) and \
        validated_entry.get('expected_on', None):
        if validated_entry['expected_on'] < validated_entry['ends_on']:
            errors.append('Expected on must be greater than Ends on in row number %s'
                % row_num)

    if validated_entry.get('expected_in', None):
        if validated_entry['expected_in'] > 30:
            errors.append('Expected in must be less than 30 days in row number %s'
                % row_num)
    
    if validated_entry.get('starts_on', None) and \
        validated_entry.get('expected_on', None):
        if validated_entry['expected_on'] > validated_entry['starts_on'] + timedelta(days=30):
            errors.append('Dfference between Expected on and Starts on should not be more \
                than 30 days in row number %s' % row_num)
    
#    if not validated_entry.get('expected_on', None) and \
#        not validated_entry.get('expected_in', None):
#        errors.append('Either Expected in or Expected On must be mentioned in row number %s'
#            % row_num)

    return validated_entry, errors

def is_conflicting_excel_entry(to_update_entry, new_entry):
    if (to_update_entry['article_id'] == new_entry['article_id']) and \
        (to_update_entry['dc'] == new_entry['dc']):
        if to_update_entry['starts_on'] >= new_entry['ends_on'] or \
            to_update_entry['ends_on'] <= new_entry['starts_on']:
            return False
        else:
            return True

def get_parsed_preorder_inventory_excel(path_to_save):
    import xlrd
    errors, to_update = [], []
    parsed_excel, parsed_excel_json = [], None
    article_id_list, dc_list = [], []
    
    try:
        book = xlrd.open_workbook(path_to_save)
    except:
        return

    try:
        sh = book.sheet_by_name('PREORDER')
        header = sh.row(0)
        map = {}
        idx = 0
        for idx in range(sh.ncols):
            map[header[idx].value.strip().lower()] = idx

        for row_count in range(1, sh.nrows):
            row = sh.row(row_count)
            try:
                article_id = row[map['articleid']].value
                dc = row[map['dc']].value
                stock = row[map['stock']].value
                starts_on = row[map['startson']].value
                ends_on = row[map['endson']].value
                expected_on = row[map['expectedon']].value

                add_dict, inv_errors = validate_preorder_excel_entry(article_id,
                    dc, stock, starts_on, ends_on, expected_on, row_count)

                if not inv_errors:
                    repeated = False
                    for item in to_update:
                        if is_conflicting_excel_entry(item, add_dict):
                            repeated = True
                            break

                    if not repeated:
                        to_update.append(add_dict)
                        excel_entry = {'article_id':str(article_id),
                            'dc':str(dc),
                            'stock':str(stock),
                            'starts_on':str(starts_on),
                            'ends_on':str(ends_on),
                            'expected_on':str(expected_on),
                            }
                        parsed_excel.append(excel_entry)
                        if not add_dict['article_id'] in article_id_list:
                            article_id_list.append(add_dict['article_id'])
                        if not add_dict['dc'] in dc_list:
                            dc_list.append(add_dict['dc'])
                    else:
                        errors.append('Conflicting entries for Articleid: %s and DC: %s combination.' 
                            % (add_dict['article_id'],add_dict['dc']))
                else:
                    errors += inv_errors
            except KeyError:
                errors.append('Unsupported excel file.')
                break

        parsed_excel_json = simplejson.dumps(parsed_excel)
    except:
        pass

    return {'errors' : errors, 
        'to_update' : to_update, 
        'article_id_list' : article_id_list, 
        'dc_list' : dc_list,
        'parsed_excel_json' : parsed_excel_json}

def get_parsed_madetoorder_inventory_excel(path_to_save):
    import xlrd
    errors, to_update = [], []
    parsed_excel, parsed_excel_json = [], None
    article_id_list, dc_list = [], []
    
    try:
        book = xlrd.open_workbook(path_to_save)
    except:
        return
    
    try:
        sh = book.sheet_by_name('MADETOORDER')
        header = sh.row(0)
        map = {}
        idx = 0
        for idx in range(sh.ncols):
            map[header[idx].value.strip().lower()] = idx

        for row_count in range(1, sh.nrows):
            row = sh.row(row_count)
            try:
                article_id = row[map['articleid']].value
                dc = row[map['dc']].value
                stock = row[map['stock']].value
                starts_on = row[map['startson']].value
                ends_on = row[map['endson']].value
                expected_in = row[map['expectedin']].value

                add_dict, inv_errors = validate_madetoorder_excel_entry(article_id,
                    dc, stock, starts_on, ends_on, expected_in, row_count)

                if not inv_errors:
                    repeated = False
                    for item in to_update:
                        if is_conflicting_excel_entry(item, add_dict):
                            repeated = True
                            break

                    if not repeated:
                        to_update.append(add_dict)
                        excel_entry = {'article_id':str(article_id),
                            'dc':str(dc),
                            'stock':str(stock),
                            'starts_on':str(starts_on),
                            'ends_on':str(ends_on),
                            'expected_in':str(expected_in),
                            }
                        parsed_excel.append(excel_entry)
                        if not add_dict['article_id'] in article_id_list:
                            article_id_list.append(add_dict['article_id'])
                        if not add_dict['dc'] in dc_list:
                            dc_list.append(add_dict['dc'])
                    else:
                        errors.append('Conflicting entries for Articleid: %s and DC: %s combination.' 
                            % (add_dict['article_id'],add_dict['dc']))
                else:
                    errors += inv_errors
            except KeyError:
                errors.append('Unsupported excel file.')
                break

        parsed_excel_json = simplejson.dumps(parsed_excel)
    except:
        pass

    return {'errors' : errors, 
        'to_update' : to_update, 
        'article_id_list' : article_id_list, 
        'dc_list' : dc_list,
        'parsed_excel_json' : parsed_excel_json}

def get_parsed_backorder_inventory_excel(path_to_save):
    import xlrd
    errors, to_update = [], []
    parsed_excel, parsed_excel_json = [], None
    article_id_list, dc_list = [], []
    
    try:
        book = xlrd.open_workbook(path_to_save)
    except:
        return

    try:
        sh = book.sheet_by_name('BACKORDER')
        header = sh.row(0)
        map = {}
        idx = 0
        for idx in range(sh.ncols):
            map[header[idx].value.strip().lower()] = idx

        for row_count in range(1, sh.nrows):
            row = sh.row(row_count)
            try:
                article_id = row[map['articleid']].value
                dc = row[map['dc']].value
                stock = row[map['stock']].value
                starts_on = row[map['startson']].value
                ends_on = row[map['endson']].value

                add_dict, inv_errors = validate_backorder_excel_entry(article_id,
                    dc, stock, starts_on, ends_on, row_count)

                if not inv_errors:
                    repeated = False
                    for item in to_update:
                        if is_conflicting_excel_entry(item, add_dict):
                            repeated = True
                            break

                    if not repeated:
                        to_update.append(add_dict)
                        excel_entry = {'article_id':str(article_id),
                            'dc':str(dc),
                            'stock':str(stock),
                            'starts_on':str(starts_on),
                            'ends_on':str(ends_on),
                            }
                        parsed_excel.append(excel_entry)
                        if not add_dict['article_id'] in article_id_list:
                            article_id_list.append(add_dict['article_id'])
                        if not add_dict['dc'] in dc_list:
                            dc_list.append(add_dict['dc'])
                    else:
                        errors.append('Conflicting entries for Articleid: %s and DC: %s combination.' 
                            % (add_dict['article_id'],add_dict['dc']))
                else:
                    errors += inv_errors
            except KeyError:
                errors.append('Unsupported excel file.')
                break

        parsed_excel_json = simplejson.dumps(parsed_excel)
    except:
        pass

    return {'errors' : errors, 
        'to_update' : to_update, 
        'article_id_list' : article_id_list, 
        'dc_list' : dc_list,
        'parsed_excel_json' : parsed_excel_json}

def get_parsed_inventory_excel(path_to_save):
    import xlrd
    try:
        book = xlrd.open_workbook(path_to_save)
    except XLRDError:
        return ['invalid file format'],['invalid file format']
    sh = book.sheet_by_index(0)
    header = sh.row(0)
    map = {}
    idx = 0
    for idx in range(sh.ncols):
        map[header[idx].value.strip().lower()] = idx
    errors, to_update = [], []
    parsed_excel, parsed_excel_json = [], None
    article_id_list, dc_list = [], []

    for row_count in range(1, sh.nrows):
        row = sh.row(row_count)
        try:
            article_id = row[map['articleid']].value
            dc = row[map['dc']].value
            stock = row[map['stock']].value
            starts_on = row[map['starts on']].value
            ends_on = row[map['ends on']].value
            expected_on = row[map['expected on']].value
            expected_in = row[map['expected in']].value

            add_dict, errors = validate_excel_entry(article_id,
                dc, stock, starts_on, ends_on, expected_on, expected_in, row_count)

            if not errors:
                repeated = False
                for item in to_update:
                    if is_conflicting_excel_entry(item, add_dict):
                        repeated = True
                        break

                if not repeated:
                    to_update.append(add_dict)
                    excel_entry = {'article_id':str(article_id),
                        'dc':str(dc),
                        'stock':str(stock),
                        'starts_on':str(starts_on),
                        'ends_on':str(ends_on),
                        'expected_on':str(expected_on),
                        'expected_in':str(expected_in),
                        }
                    parsed_excel.append(excel_entry)
                    if not add_dict['article_id'] in article_id_list:
                        article_id_list.append(add_dict['article_id'])
                    if not add_dict['dc'] in dc_list:
                        dc_list.append(add_dict['dc'])
                else:
                    errors.append('Timeslot Overlapping entries for Articleid: %s and DC: %s combination.' 
                        % (add_dict['article_id'],add_dict['dc']))
        except KeyError:
            errors.append('Unsupported excel file.')
            break

    parsed_excel_json = simplejson.dumps(parsed_excel)

    return {'errors' : errors, 
        'to_update' : to_update, 
        'article_id_list' : article_id_list, 
        'dc_list' : dc_list,
        'parsed_excel_json' : parsed_excel_json}

def check_dc_validity(request, dc_in_excel):
    from fulfillment.models import Dc
    dc_not_present = []

    if dc_in_excel:
        available_dc = Dc.objects.filter(
            code__in=dc_in_excel, client=request.client.client).values('code')

    if available_dc:
        if len(available_dc) == len(dc_in_excel):
            pass
        else:
            available_dc_codes = []
            for item in available_dc:
                available_dc_codes.append(int(item['code']))
            for dc_in_excel_item in dc_in_excel:
                if not dc_in_excel_item in available_dc_codes:
                    dc_not_present.append(dc_in_excel_item)
    else:
        dc_not_present = dc_in_excel

    return dc_not_present

def get_inventory_levels(article_id_list, dc_list, seller):
    current_time = datetime.now()
    inventory_levels = Inventory.objects.select_related(
        'rate_chart', 'dc').filter(
        (Q(rate_chart__article_id__in = article_id_list) | 
        Q(rate_chart__sku__in = article_id_list)),
        rate_chart__seller = seller,
        dc__code__in = dc_list,
        type__in = ['backorder','madetoorder','preorder'],
        is_active = True,
        ends_on__gte = current_time)
    return inventory_levels

def get_conflicting_inventory_entry(inventory_levels, new_entry):
    conflicting_inventory = inventory_levels.filter(
        (Q(rate_chart__article_id = new_entry['article_id']) |
        Q(rate_chart__sku = new_entry['article_id'])),
        dc__code = new_entry['dc']).exclude(
        Q(ends_on__lte = new_entry['starts_on']) |
        Q(starts_on__gte = new_entry['ends_on']))
    return conflicting_inventory

def get_preorder_inventory_updates(request, to_update, seller, save_changes, **kwargs):
    from django.db.models import Q
    user = kwargs.get('user', None)
    article_id_list = kwargs.get('article_id_list',[])
    dc_list = kwargs.get('dc_list',[])

    errors = []
    consolidated_updates, conflicts = [], []

    if article_id_list:
        rate_charts = SellerRateChart.objects.filter(
            (Q(article_id__in = article_id_list) |
            Q(sku__in = article_id_list)),
            seller = seller)
        
        if len(article_id_list) == len(rate_charts):
            for item in rate_charts:
                if item.is_bundle:
                    errors.append('Cannot update inventory levels for parent bundled product with Article Id = %s' % item.article_id)
        else:
            for item in article_id_list:
                rc = rate_charts.filter(Q(article_id=item) | 
                    Q(sku = item))
                if not rc:
                    errors.append('No active article found with Article Id/SKU = %s' % item)

    if to_update and not errors:
        #First, check if there are any conflicts with entries already in DB.
        '''
        Get all active/future virtual inventory entries for all possible 
        combinations of (article_id, dc) from article_id_list and dc_list.
        '''
        inventory_levels = get_inventory_levels(article_id_list, dc_list, seller)
        for item in to_update:
            conflicting_inventory = get_conflicting_inventory_entry(
                inventory_levels, item)
            #In case one of the conflicting entries
            conflict_dict = {'excel_entry':item,
                'conflicting_inventory':conflicting_inventory}
            conflicts.append(conflict_dict)

        if save_changes:
            for item in conflicts:
                rate_chart, errors = get_seller_rate_chart(seller, item['excel_entry']['article_id'])
                dc = utils.get_dc(item['excel_entry']['dc'], request.client.client)
                
                #Expire current backorder/made-to-order/pre-order entries if any.
                if item['conflicting_inventory']:
                    for entry in item['conflicting_inventory']:
                        if entry.starts_on > item['excel_entry']['starts_on'] and \
                            entry.ends_on < item['excel_entry']['ends_on']:
                            entry.is_active = False
                            entry.save()
                        elif entry.ends_on > item['excel_entry']['starts_on'] and \
                            entry.ends_on <= item['excel_entry']['ends_on']:
                            entry.ends_on = item['excel_entry']['starts_on']
                            entry.save()
                        elif entry.starts_on < item['excel_entry']['ends_on'] and \
                            entry.starts_on > item['excel_entry']['starts_on']:
                            entry.starts_on = item['excel_entry']['ends_on']
                            entry.save()
                        elif entry.starts_on < item['excel_entry']['starts_on'] and \
                            entry.ends_on > item['excel_entry']['ends_on']:
                            entry.ends_on = item['excel_entry']['starts_on']
                            entry.save()
                        elif entry.starts_on == item['excel_entry']['starts_on'] and \
                            entry.ends_on == item['excel_entry']['ends_on']:
                            entry.is_active = False
                            entry.save()
                
                #Create new entries.
                inventory = Inventory.objects.create(
                    rate_chart = rate_chart,
                    dc = dc,
                    type = 'preorder',
                    stock = item['excel_entry']['stock'],
                    starts_on = item['excel_entry']['starts_on'],
                    ends_on = item['excel_entry']['ends_on'],
                    expected_on = item['excel_entry']['expected_on'],
                    expected_in = None)

                #Update solr index.
                if rate_chart.stock_status in ['outofstock','notavailable'] and \
                    rate_chart.is_available_for_sale(None):
                    rate_chart.stock_status = 'instock'
                    rate_chart.save()
                    product = rate_chart.product
                    product.update_solr_index()
                elif rate_chart.stock_status == 'instock' and \
                    not rate_chart.is_available_for_sale(None):
                    rate_chart.stock_status = 'outofstock'
                    rate_chart.save()
                    product = rate_chart.product
                    product.update_solr_index()

    return errors, conflicts


def get_madetoorder_inventory_updates(request, to_update, seller, save_changes, **kwargs):
    from django.db.models import Q
    user = kwargs.get('user', None)
    article_id_list = kwargs.get('article_id_list',[])
    dc_list = kwargs.get('dc_list',[])

    errors = []
    consolidated_updates, conflicts = [], []

    if article_id_list:
        rate_charts = SellerRateChart.objects.filter(
            (Q(article_id__in = article_id_list) |
            Q(sku__in = article_id_list)),
            seller = seller)
        
        if len(article_id_list) == len(rate_charts):
            for item in rate_charts:
                if item.is_bundle:
                    errors.append('Cannot update inventory levels for parent bundled product with Article Id = %s' % item.article_id)
        else:
            for item in article_id_list:
                rc = rate_charts.filter(Q(article_id=item) | 
                    Q(sku = item))
                if not rc:
                    errors.append('No active article found with Article Id/SKU = %s' % item)

    if to_update and not errors:
        #First, check if there are any conflicts with entries already in DB.
        '''
        Get all active/future virtual inventory entries for all possible 
        combinations of (article_id, dc) from article_id_list and dc_list.
        '''
        inventory_levels = get_inventory_levels(article_id_list, dc_list, seller)
        for item in to_update:
            conflicting_inventory = get_conflicting_inventory_entry(
                inventory_levels, item)
            conflict_dict = {'excel_entry':item,
                'conflicting_inventory':conflicting_inventory}
            conflicts.append(conflict_dict)

        if save_changes:
            for item in conflicts:
                rate_chart, errors = get_seller_rate_chart(seller, item['excel_entry']['article_id'])
                dc = utils.get_dc(item['excel_entry']['dc'], request.client.client)
                
                #Expire current backorder/made-to-order/pre-order entries if any.
                if item['conflicting_inventory']:
                    for entry in item['conflicting_inventory']:
                        if entry.starts_on > item['excel_entry']['starts_on'] and \
                            entry.ends_on < item['excel_entry']['ends_on']:
                            entry.is_active = False
                            entry.save()
                        elif entry.ends_on > item['excel_entry']['starts_on'] and \
                            entry.ends_on <= item['excel_entry']['ends_on']:
                            entry.ends_on = item['excel_entry']['starts_on']
                            entry.save()
                        elif entry.starts_on < item['excel_entry']['ends_on'] and \
                            entry.starts_on > item['excel_entry']['starts_on']:
                            entry.starts_on = item['excel_entry']['ends_on']
                            entry.save()
                        elif entry.starts_on < item['excel_entry']['starts_on'] and \
                            entry.ends_on > item['excel_entry']['ends_on']:
                            entry.ends_on = item['excel_entry']['starts_on']
                            entry.save()
                        elif entry.starts_on == item['excel_entry']['starts_on'] and \
                            entry.ends_on == item['excel_entry']['ends_on']:
                            entry.is_active = False
                            entry.save()
                
                #Create new entries.
                inventory = Inventory.objects.create(
                    rate_chart = rate_chart,
                    dc = dc,
                    type = 'madetoorder',
                    stock = item['excel_entry']['stock'],
                    starts_on = item['excel_entry']['starts_on'],
                    ends_on = item['excel_entry']['ends_on'],
                    expected_on = None,
                    expected_in = item['excel_entry']['expected_in'])

                #Update solr index.
                if rate_chart.stock_status in ['outofstock','notavailable'] and \
                    rate_chart.is_available_for_sale(None):
                    rate_chart.stock_status = 'instock'
                    rate_chart.save()
                    product = rate_chart.product
                    product.update_solr_index()
                elif rate_chart.stock_status == 'instock' and \
                    not rate_chart.is_available_for_sale(None):
                    rate_chart.stock_status = 'outofstock'
                    rate_chart.save()
                    product = rate_chart.product
                    product.update_solr_index()

    return errors, conflicts

def get_backorder_inventory_updates(request, to_update, seller, save_changes, **kwargs):
    from django.db.models import Q
    user = kwargs.get('user', None)
    article_id_list = kwargs.get('article_id_list',[])
    dc_list = kwargs.get('dc_list',[])

    errors = []
    consolidated_updates, conflicts = [], []

    if article_id_list:
        rate_charts = SellerRateChart.objects.filter(
            (Q(article_id__in = article_id_list) |
            Q(sku__in = article_id_list)),
            seller = seller)
        
        if len(article_id_list) == len(rate_charts):
            for item in rate_charts:
                if item.is_bundle:
                    errors.append('Cannot update inventory levels for parent bundled product with Article Id = %s' % item.article_id)
        else:
            for item in article_id_list:
                rc = rate_charts.filter(Q(article_id=item) | 
                    Q(sku = item))
                if not rc:
                    errors.append('No active article found with Article Id/SKU = %s' % item)

    if to_update and not errors:
        #First, check if there are any conflicts with entries already in DB.
        '''
        Get all active/future virtual inventory entries for all possible 
        combinations of (article_id, dc) from article_id_list and dc_list.
        '''
        inventory_levels = get_inventory_levels(article_id_list, dc_list, seller)
        for item in to_update:
            conflicting_inventory = get_conflicting_inventory_entry(
                inventory_levels, item)
            conflict_dict = {'excel_entry':item,
                'conflicting_inventory':conflicting_inventory}
            conflicts.append(conflict_dict)

        if save_changes:
            for item in conflicts:
                rate_chart, errors = get_seller_rate_chart(seller, item['excel_entry']['article_id'])
                dc = utils.get_dc(item['excel_entry']['dc'], request.client.client)
                
                #Expire current backorder/made-to-order entries if any.
                if item['conflicting_inventory']:
                    for entry in item['conflicting_inventory']:
                        if entry.starts_on > item['excel_entry']['starts_on'] and \
                            entry.ends_on < item['excel_entry']['ends_on']:
                            entry.is_active = False
                            entry.save()
                        elif entry.ends_on > item['excel_entry']['starts_on'] and \
                            entry.ends_on <= item['excel_entry']['ends_on']:
                            entry.ends_on = item['excel_entry']['starts_on']
                            entry.save()
                        elif entry.starts_on < item['excel_entry']['ends_on'] and \
                            entry.starts_on > item['excel_entry']['starts_on']:
                            entry.starts_on = item['excel_entry']['ends_on']
                            entry.save()
                        elif entry.starts_on < item['excel_entry']['starts_on'] and \
                            entry.ends_on > item['excel_entry']['ends_on']:
                            entry.ends_on = item['excel_entry']['starts_on']
                            entry.save()
                        elif entry.starts_on == item['excel_entry']['starts_on'] and \
                            entry.ends_on == item['excel_entry']['ends_on']:
                            entry.is_active = False
                            entry.save()

                #Create new entries.
                inventory = Inventory.objects.create(
                    rate_chart = rate_chart,
                    dc = dc,
                    type = 'backorder',
                    stock = item['excel_entry']['stock'],
                    starts_on = item['excel_entry']['starts_on'],
                    ends_on = item['excel_entry']['ends_on'],
                    expected_on = None,
                    expected_in = None)

                #Update solr index.
                if rate_chart.stock_status in ['outofstock','notavailable'] and \
                    rate_chart.is_available_for_sale(None):
                    rate_chart.stock_status = 'instock'
                    rate_chart.save()
                    product = rate_chart.product
                    product.update_solr_index()
                elif rate_chart.stock_status == 'instock' and \
                    not rate_chart.is_available_for_sale(None):
                    rate_chart.stock_status = 'outofstock'
                    rate_chart.save()
                    product = rate_chart.product
                    product.update_solr_index()

    return errors, conflicts

def get_inventory_updates(to_update, seller, save_changes, **kwargs):
    from django.db.models import Q
    user = kwargs.get('user', None)
    article_id_list = kwargs.get('article_id_list',[])
    dc_list = kwargs.get('dc_list',[])

    errors = []
    consolidated_updates, conflicts = [], []
    #is_global_dc_supported = utils.is_global_dc_maintained(request.client.client)

    if article_id_list:
        rate_charts = SellerRateChart.objects.filter(
            (Q(article_id__in = article_id_list) |
            Q(sku__in = article_id_list)),
            seller = seller)
        if len(article_id_list) == len(rate_charts):
            for item in rate_charts:
                if item.is_bundle:
                    errors.append('Cannot update inventory levels for parent bundled product with Article Id = %s' % item.article_id)
        else:
            for item in article_id_list:
                rc = rate_charts.filter(Q(article_id=item) | 
                    Q(sku = item))
                if not rc:
                    errors.append('No active article found with Article Id/SKU = %s' % item)

    if to_update and not errors:
        #First, check if there are any conflicts with entries already in DB.
        '''
        Get all active/future virtual inventory entries for all possible 
        combinations of (article_id, dc) from article_id_list and dc_list.
        '''
        inventory_levels = get_inventory_levels(article_id_list, dc_list, seller)
        if inventory_levels:
            for item in to_update:
                conflicting_inventory = get_conflicting_inventory_entry(
                    inventory_levels, item)
                if conflicting_inventory:
                    conflict_dict = {'excel_entry':item,
                        'conflicting_inventory':conflicting_inventory}
                    conflicts.append(conflict_dict)
                else:
                    consolidated_updates.append(item)
        else:
            consolidated_updates = to_update

        if save_changes:
            for item in consolidated_updates:
                rate_chart, errors = get_seller_rate_chart(seller, item['article_id'])
                dc = utils.get_dc(item['dc'], request.client.client)
                inventory = Inventory.objects.create(
                    rate_chart = rate_chart,
                    dc = dc,
                    type = 'virtual',
                    stock = item['stock'],
                    starts_on = item['starts_on'],
                    ends_on = item['ends_on'],
                    expected_on = item.get('expected_on',None),
                    expected_in = item.get('expected_in',None))

                if rate_chart.stock_status in ['outofstock','notavailable'] and \
                    rate_chart.is_available_for_sale(None):
                    rate_chart.stock_status = 'instock'
                    rate_chart.save()
                    product = rate_chart.product
                    product.update_solr_index()

    return errors, consolidated_updates, conflicts

def inventory_bulk_upload(request, **kwargs):
    from django.utils import simplejson
    from web.sbf_forms import FileUploadForm
    import os
    client = request.client.client
    seller = kwargs.get('seller', None)
    backorder_errors, madetoorder_errors, preorder_errors, errors_across_sheets, message = [], [], [], [], None
    backorder_conflicts, madetoorder_conflicts, preorder_conflicts = None, None, None
    parsed_backorder_excel_json, parsed_madetoorder_excel_json, parsed_preorder_excel_json = None, None, None
    form = None
    flag = None
    to_update = []
    path_to_save = None
    dc_not_present = []
    if request.method == 'POST':
        if request.POST.get("upload") == 'Upload':
            import xlrd
            form = FileUploadForm(request.POST, request.FILES)
            if form.is_valid():
                path_to_save = save_uploaded_file(request.FILES['status_file'])

                #backorder
                parsed_backorder_excel = get_parsed_backorder_inventory_excel(path_to_save)
                if parsed_backorder_excel and (parsed_backorder_excel['to_update'] or \
                    parsed_backorder_excel['errors']):
                    backorder_errors = parsed_backorder_excel['errors']
                    if not backorder_errors:
                        dc_not_present = check_dc_validity(
                            request, parsed_backorder_excel['dc_list'])
                        if dc_not_present:
                            dc_not_present_string = ''
                            for item in dc_not_present:
                                dc_not_present_string += str(item) + ','
                            if dc_not_present_string:
                                dc_not_present_string = dc_not_present_string[:(len(dc_not_present_string)-1)]
                            backorder_errors.append('Entries not found for DC Codes in Backorder sheet - %s. Please correct the DC Entries.' % dc_not_present_string)
                        else:
                            backorder_errors, backorder_conflicts = get_backorder_inventory_updates(
                                request,
                                parsed_backorder_excel['to_update'], 
                                seller, 
                                False, 
                                article_id_list = parsed_backorder_excel['article_id_list'], 
                                dc_list = parsed_backorder_excel['dc_list'])
                            parsed_backorder_excel_json = parsed_backorder_excel['parsed_excel_json']

                #made-to-order
                parsed_madetoorder_excel = get_parsed_madetoorder_inventory_excel(path_to_save)
                if parsed_madetoorder_excel and (parsed_madetoorder_excel['to_update'] or \
                    parsed_madetoorder_excel['errors']):
                    madetoorder_errors = parsed_madetoorder_excel['errors']
                    if not madetoorder_errors:
                        dc_not_present = check_dc_validity(
                            request, parsed_madetoorder_excel['dc_list'])
                        if dc_not_present:
                            dc_not_present_string = ''
                            for item in dc_not_present:
                                dc_not_present_string += str(item) + ','
                            if dc_not_present_string:
                                dc_not_present_string = dc_not_present_string[:(len(dc_not_present_string)-1)]
                            madetoorder_errors.append('Entries not found for DC Codes in Made-to-order sheet - %s. Please correct the DC Entries.' % dc_not_present_string)
                        else:
                            madetoorder_errors, madetoorder_conflicts = get_madetoorder_inventory_updates(
                                request,
                                parsed_madetoorder_excel['to_update'], 
                                seller, 
                                False, 
                                article_id_list = parsed_madetoorder_excel['article_id_list'], 
                                dc_list = parsed_madetoorder_excel['dc_list'])
                            parsed_madetoorder_excel_json = parsed_madetoorder_excel['parsed_excel_json']

                #pre-order
                parsed_preorder_excel = get_parsed_preorder_inventory_excel(path_to_save)
                if parsed_preorder_excel and (parsed_preorder_excel['to_update'] or \
                    parsed_preorder_excel['errors']):
                    preorder_errors = parsed_preorder_excel['errors']
                    if not preorder_errors:
                        dc_not_present = check_dc_validity(
                            request, parsed_preorder_excel['dc_list'])
                        if dc_not_present:
                            dc_not_present_string = ''
                            for item in dc_not_present:
                                dc_not_present_string += str(item) + ','
                            if dc_not_present_string:
                                dc_not_present_string = dc_not_present_string[:(len(dc_not_present_string)-1)]
                            preorder_errors.append('Entries not found for DC Codes in Pre-order sheet - %s. Please correct the DC Entries.' % dc_not_present_string)
                        else:
                            preorder_errors, preorder_conflicts = get_preorder_inventory_updates(
                                request,
                                parsed_preorder_excel['to_update'], 
                                seller, 
                                False, 
                                article_id_list = parsed_preorder_excel['article_id_list'], 
                                dc_list = parsed_preorder_excel['dc_list'])
                            parsed_preorder_excel_json = parsed_preorder_excel['parsed_excel_json']

                #Check for conflicting entries across 3 sheets.
                if parsed_backorder_excel and parsed_backorder_excel['to_update'] \
                    and parsed_madetoorder_excel and parsed_madetoorder_excel['to_update']:
                    for item1 in parsed_backorder_excel['to_update']:
                        for item2 in parsed_madetoorder_excel['to_update']:
                            if is_conflicting_excel_entry(item1, item2):
                                errors_across_sheets.append('Conflicting entries \
                                    between BACKORDER and MADETOORDER sheet for \
                                    Articleid=%s and DC=%s' % (item1['article_id'], \
                                    item1['dc']))

                if parsed_backorder_excel and parsed_backorder_excel['to_update'] \
                    and parsed_preorder_excel and parsed_preorder_excel['to_update']:
                    for item1 in parsed_backorder_excel['to_update']:
                        for item2 in parsed_preorder_excel['to_update']:
                            if is_conflicting_excel_entry(item1, item2):
                                errors_across_sheets.append('Conflicting entries \
                                    between BACKORDER and PREORDER sheet for \
                                    Articleid=%s and DC=%s' % (item1['article_id'], \
                                    item1['dc']))
                
                if parsed_madetoorder_excel and parsed_madetoorder_excel['to_update'] \
                    and parsed_preorder_excel and parsed_preorder_excel['to_update']:
                    for item1 in parsed_madetoorder_excel['to_update']:
                        for item2 in parsed_preorder_excel['to_update']:
                            if is_conflicting_excel_entry(item1, item2):
                                errors_across_sheets.append('Conflicting entries \
                                    between MADETOORDER and PREORDER sheet for \
                                    Articleid=%s and DC=%s' % (item1['article_id'], \
                                    item1['dc']))

                if backorder_errors or madetoorder_errors or preorder_errors or errors_across_sheets:
                    form = FileUploadForm()
                    flag = 'new'
                elif backorder_conflicts or madetoorder_conflicts or preorder_conflicts:
                    flag = 'show_details'
                elif not (parsed_backorder_excel or parsed_madetoorder_excel or parsed_preorder_excel):
                    form = FileUploadForm()
                    flag = 'new'
                    errors_across_sheets.append('Please upload file only in .xls format!')
                elif not(parsed_backorder_excel and parsed_backorder_excel['parsed_excel_json']) or \
                    not (parsed_madetoorder_excel and parsed_madetoorder_excel['parsed_excel_json']) or \
                    not (parsed_preorder_excel and parsed_preorder_excel['parsed_excel_json']):
                    form = FileUploadForm()
                    flag = 'new'
                    errors_across_sheets.append('Please upload excel file only in below mentioned format!')
                else:
                    form = FileUploadForm()
                    flag = 'new'
                    errors_across_sheets.append('No data to upload!')

                #Delete the uploaded excel file
                if path_to_save:
                    os.remove(path_to_save)
            else:
                errors_across_sheets.append('Please select the excel file and then click upload!!!')
                form = FileUploadForm()
                flag = 'new'
        elif request.POST.get("update") == 'Update':
            #backorder
            parsed_backorder_excel_json = request.POST.get("parsed_backorder_excel_json", None)
            if parsed_backorder_excel_json:
                parsed_backorder_excel_json = simplejson.loads(parsed_backorder_excel_json)
                backorder_article_id_list = []
                backorder_dc_list = []
                to_update = []

                for item in parsed_backorder_excel_json:
                    add_dict, errors = validate_backorder_excel_entry(
                        item['article_id'] , item['dc'], item['stock'],
                        item['starts_on'] , item['ends_on'])
                    to_update.append(add_dict)
                
                for entry in to_update:
                    article_id = number_formatting(str(entry['article_id']).strip().split('.')[0])
                    if not article_id in backorder_article_id_list:
                        backorder_article_id_list.append(article_id)

                    dc_id = number_formatting(str(entry['dc']).strip().split('.')[0])
                    if not dc_id in backorder_dc_list:
                        backorder_dc_list.append(dc_id)

                errors, conflicts = get_backorder_inventory_updates(
                    request, to_update, seller, True, user=request.user,
                    article_id_list = backorder_article_id_list,
                    dc_list = backorder_dc_list)
            
            #made-to-order
            parsed_madetoorder_excel_json = request.POST.get("parsed_madetoorder_excel_json", None)
            if parsed_madetoorder_excel_json:
                parsed_madetoorder_excel_json = simplejson.loads(parsed_madetoorder_excel_json)
                madetoorder_article_id_list = []
                madetoorder_dc_list = []
                to_update = []

                for item in parsed_madetoorder_excel_json:
                    add_dict, errors = validate_madetoorder_excel_entry(
                        item['article_id'] , item['dc'], item['stock'],
                        item['starts_on'] , item['ends_on'], item['expected_in'])
                    to_update.append(add_dict)
                
                for entry in to_update:
                    article_id = number_formatting(str(entry['article_id']).strip().split('.')[0])
                    if not article_id in madetoorder_article_id_list:
                        madetoorder_article_id_list.append(article_id)

                    dc_id = number_formatting(str(entry['dc']).strip().split('.')[0])
                    if not dc_id in madetoorder_dc_list:
                        madetoorder_dc_list.append(dc_id)

                errors, conflicts = get_madetoorder_inventory_updates(
                    request, to_update, seller, True, user=request.user,
                    article_id_list = madetoorder_article_id_list,
                    dc_list = madetoorder_dc_list)

            #pre-order
            parsed_preorder_excel_json = request.POST.get("parsed_preorder_excel_json", None)
            if parsed_preorder_excel_json:
                parsed_preorder_excel_json = simplejson.loads(parsed_preorder_excel_json)
                preorder_article_id_list = []
                preorder_dc_list = []
                to_update = []

                for item in parsed_preorder_excel_json:
                    add_dict, errors = validate_preorder_excel_entry(
                        item['article_id'] , item['dc'], item['stock'],
                        item['starts_on'] , item['ends_on'], item['expected_on'])
                    to_update.append(add_dict)
                
                for entry in to_update:
                    article_id = number_formatting(str(entry['article_id']).strip().split('.')[0])
                    if not article_id in preorder_article_id_list:
                        preorder_article_id_list.append(article_id)

                    dc_id = number_formatting(str(entry['dc']).strip().split('.')[0])
                    if not dc_id in preorder_dc_list:
                        preorder_dc_list.append(dc_id)

                errors, conflicts = get_preorder_inventory_updates(
                    request, to_update, seller, True, user=request.user,
                    article_id_list = preorder_article_id_list,
                    dc_list = preorder_dc_list)

            return HttpResponseRedirect('/category/category_management/inventory/inventory_upload_success/')
    else:
        form = FileUploadForm()
        flag = 'new'

    inventory_dict = {
        'forms' : form,
        'errors_across_sheets' : errors_across_sheets,
        'backorder_errors' : backorder_errors,
        'backorder_conflicts' : backorder_conflicts,
        'parsed_backorder_excel_json' : parsed_backorder_excel_json,
        'madetoorder_errors' : madetoorder_errors,
        'madetoorder_conflicts' : madetoorder_conflicts,
        'parsed_madetoorder_excel_json' : parsed_madetoorder_excel_json,
        'preorder_errors' : preorder_errors,
        'preorder_conflicts' : preorder_conflicts,
        'parsed_preorder_excel_json' : parsed_preorder_excel_json,
        'flag' : flag,
        'url' : request.get_full_path(),
        'client_display_name':client.name
        }
    return render_to_response('inventory/inventory_upload.html', 
        inventory_dict, context_instance=RequestContext(request))

def inventory_upload_success(request, **kwargs):
    client = request.client.client
    seller = kwargs.get('seller',None)

    if request.method == 'POST':
        next_action = request.POST.get('action','')
        if next_action == 'Update more stock levels':
            return HttpResponseRedirect('/category/category_management/inventory/inventory_bulk_upload/')
        return HttpResponseRedirect('/category/category_management/inventory/all_inventory/')
    
    inventory_dict = {
        'url' : request.get_full_path(),
        'client_display_name':client.name
        }
    return render_to_response('inventory/inventory_upload_successful.html', 
        inventory_dict, context_instance=RequestContext(request))
