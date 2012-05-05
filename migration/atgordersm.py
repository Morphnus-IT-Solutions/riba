#!/usr/bin/python

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

from atg.models import *
from orders.models import Order, OrderItem, DeliveryInfo
from users.models import Profile
from django.contrib.auth.models import User
from migration.models import AtgOrderMigrationMap
from accounts.models import Client
from catalog.models import SellerRateChart
from locations.models import Address, Country, State, City
from decimal import Decimal
import logging
log = logging.getLogger('migration')

def safe_convert(text, size, default_to=None):
    ''' Converts given text to ascii, truncates to size '''
    if text == None:
        return default_to
    return text.encode('ascii','ignore')[:size]


def get_order_state(atg_state):
    if atg_state in ['AWAITING_PAYMENT', 'CoD_AWAITING_VERIFICATION', 'AWAITING_CUSTOMER_VERIFICATION', 'AWAITING_VERIFICATION']:
        return 'pending_order'
    elif atg_state in ['PARTIALLY_PROCESSED', 'SUBMITTED', 'PROCESSING', 'AWAITING_DEPOSIT', 'NO_PENDING_ACTION', 'PROCESSED']:
        return 'confirmed'
    elif atg_state in ['REMOVED', 'PENDING_REMOVE', 'CANCELLED']:
        return 'cancelled'
    else:
        return ''

def get_country(name):
    try:
        c = Country.objects.get(name = name)
    except Country.DoesNotExist:
        c = Country(name = name)
        c.save()
    return c
    
def get_state(name, country):
    try:
        s = State.objects.get(name = name, country = country)
    except State.DoesNotExist:
        s = State(name = name, country = country)
        s.save()
    return s

def get_city(name, state):
    try:
        c = City.objects.get(name = name, state = state)
    except City.DoesNotExist:
        c = City(name = name, state = state)
        c.save()
    return c

def new_order(atg_order, tinla_profile, client):
    # Ensure that there is no profile with this atg login
    map_entry = None
    try:
        map_entry = AtgOrderMigrationMap.objects.select_related('order').get(
                        atg_order = atg_order.order.order)
        log.info("Already migrated %s, skipping new_order" % atg_order.order.order)
        return map_entry.order
    except AtgOrderMigrationMap.DoesNotExist:
        pass

    # create new order
    order = Order()
    order.user = tinla_profile
    order.state = get_order_state(atg_order.order.order_state)
    order.timestamp = atg_order.order.atg_creation_date
    order.payment_realized_on = atg_order.order.atg_submitted_date
    order.modified_on = atg_order.order.last_modified_date
    order.reference_order_id = atg_order.order.order
    order.client = client

    order.save()

    # delivery info
    shipping = DcsppShipGroup.objects.filter(order_ref = atg_order.order.order)
    if shipping: 
        shipping = shipping[0]
        dcspp_addr = DcsppShipAddr.objects.filter(shipping_group=shipping.shipping_group)
        if dcspp_addr:
            shipping = dcspp_addr[0]
            if shipping:
                addr = Address()
                addr.profile = tinla_profile
                addr.account = client.account_set.all()[0]
                addr.first_name = shipping.first_name
                addr.last_name = shipping.last_name
                addr.phone = shipping.phone_number
                addr.email = shipping.email
                addr.pincode = shipping.postal_code
                country, state, city = '', '', ''
                try:
                    if shipping.county: country = get_country(shipping.county)
                    if shipping.state and country: state = get_state(shipping.state.state_name, country)
                    if shipping.city and state: city = get_city(shipping.city, state)
                    if country: addr.country = country
                    if state: addr.state = state
                    if city: addr.city = city
                except:
                    pass

                addr.save()

                del_info = DeliveryInfo()
                del_info.address = addr
                del_info.order = order
                del_info.save()


    order_items = atg_order.order.dcspporderitem_set.all()
    list_price_total, shipping_charges = Decimal(0), Decimal(0)
    for atg_oi in order_items:
        oi = OrderItem()
        ci = atg_oi.commerce_items
        oi.order = order
        oi.state = get_order_state(ci.state)
        try:
            src = SellerRateChart.objects.get(sku=ci.sku.sku.sku_id, seller__client = client)
            oi.seller_rate_chart = src
        except SellerRateChart.DoesNotExist:
            pass

        oi.list_price = ci.amount_info.list_price
        list_price_total += ci.amount_info.list_price
        
        oi.sale_price = ci.amount_info.sale_price

        del_item = FtbShipitemRel.objects.filter(relationship__commerce_item = atg_oi)
        if del_item:
            del_item = del_item[0]
            oi.shipping_charges = del_item.shipping_cost
            shipping_charges += del_item.shipping_cost
            "shipping found for ", atg_order.order

        oi.qty = ci.quantity
        oi.save()

    # amount info
    order_discount_total = Decimal(str(atg_order.ord_misc_field1))
    sale_price_total = atg_order.order.price_info.raw_subtotal

    total_order_shipping = atg_order.order.price_info.shipping + shipping_charges
    order.shipping_charges = total_order_shipping
    order.list_price_total = list_price_total
    order.total = sale_price_total
    order.payable_amount = sale_price_total + total_order_shipping - order_discount_total
    order.save()

    print order.id
    print order.reference_order_id

    # map entry
    map_entry = AtgOrderMigrationMap(order = order, atg_order = atg_order.order.order)
    map_entry.save()


import gc

def queryset_iterator(queryset, chunksize=1000):
    '''
    Iterate over a Django Queryset ordered by the primary key

    This method loads a maximum of chunksize (default: 1000) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not preload all the
    classes.

    Note that the implementation of the iterator does not support ordered query sets.
    '''
    pk = 0
    last_pk = queryset.order_by('-pk')[0].pk
    queryset = queryset.order_by('pk')
    while pk < last_pk:
        for row in queryset.filter(pk__gt=pk)[:chunksize]:
            pk = row.pk
            yield row
        gc.collect()


def migrate():
    # Migration plan
    # Read orders from atg
    # Create an order if atg.orderid doesn't exists in tinla.order.reference_order_id

    #migrated_logins = Profile.objects.exclude(atg_login=None).exclude(atg_login='').values('atg_login')[6100:6200]
    #print migrated_logins
    atg_orders = FtbOrder.objects.select_related('order','order__profile').filter(
        location__in = ['EZONE', 'EZONEPHONE','EZONESTORE']).exclude(order__order_state__in = ['INCOMPLETE',
    'FAILED'])
#    print atg_orders.query
    count = atg_orders.count()
    log.info('Found %s orders in atg' % count)
    no_user_exists = 0
    exists = 0
    index = 0
    non_existing = 0
    migrated = 0
    client = Client.objects.get(name="Ezone")
    atg_orders = queryset_iterator(atg_orders)
    for atg_order in atg_orders:
        index += 1
        found = False
        tinla_profile = ''
        atg_user_exists = True
       # check if atg_user exists in tinla and atg.order matches tinla.reference_order_id
        try: 
            tinla_profile = Profile.objects.get(atg_login = atg_order.order.profile.user.login)
            print "===================================================="
            print "atg_login : ", atg_order.order.profile.user.login
            print "tinla_profile : ", tinla_profile
        except:
            no_user_exists += 1
            atg_user_exists = False
            print " ************************ Did not find profile :",atg_order.order.profile

        if tinla_profile:
            if Order.objects.select_related('id').filter(reference_order_id = atg_order.order.order):
                found = True
        if found:
            exists += 1
        elif not found and atg_user_exists:
            non_existing += 1
            new_order(atg_order, tinla_profile, client)
            migrated += 1
            
        if index % 100 == 0:
            log.info('Processed %s/%s' % (index, count))

    log.info('ATG user does not exists: %s' % no_user_exists)
    log.info('Existing Order: %s' % exists)
    log.info('Non Existing: %s' % non_existing)
    log.info('Migrated: %s' % migrated)

if __name__ == '__main__':
    migrate()
