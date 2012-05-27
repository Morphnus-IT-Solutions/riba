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

from users.models import Profile
from integrations.fbapi import users, orders, fbapiutils
from orders.models import *
from payments.models import PaymentAttempt
from datetime import datetime, timedelta
from atg.models import *


def analyze_order_set(order_set):
    # Lets check if any of the following data is not matching for each order
    missing_in_atg = []
    no_ref_order_id = []
    amount_mismatch = []
    incomplete_orders = []
    failed_orders = []
    item_amount_mismatch = []
    product_mismatch = []

    for order in order_set:
        try:
            payment_status = 'Not Approved'
            for pa in order.paymentattempt_set.all():
                if pa.status == 'approved':
                    payment_status = 'Approved'

            print ''
            print 'RefID: %s : %s : %s: : %s' % (order.reference_order_id,
                order.payment_mode, order.payment_realized_mode,
                payment_status),
            atg_order =  FtbOrder.objects.get(order = order.reference_order_id)
            # Compare prices
            if order.payable_amount != atg_order.get_payable_amount():
                print ' Amount mismatch: %s - %s:%s' % (
                    order.reference_order_id,
                    str(order.payable_amount),
                    str(atg_order.get_payable_amount())),
                amount_mismatch.append(order)
            if atg_order.order.order_state == 'INCOMPLETE':
                print ' Incomplete: ',
                incomplete_orders.append(order)
            if atg_order.order.order_state == 'FAILED':
                print ' Failed: ', 
                failed_orders.append(order)

            tinla_item_map = {}
            for oi in order.orderitem_set.all():
                title = oi.seller_rate_chart.product.title
                ftbsku = FtbSku.objects.get(pk=oi.seller_rate_chart.sku)
                if ftbsku.get_bundle_skus():
                    bundle_skus = ftbsku.get_bundle_skus()
                    for sku in bundle_skus:
                        tinla_item_map[sku.bundle_item] = {
                            'qty': str(oi.qty * sku.quantity),
                            'title': 'Bundle split -- %s' % title
                            }
                else:
                    tinla_item_map[oi.seller_rate_chart.sku] = {
                        'title': title,
                        'qty': str(oi.qty)
                        }

            atg_item_map = {}
            for item in atg_order.dcsppitem_set.select_related('sku').all():
                atg_item_map[item.sku.sku.sku_id] = {
                    'qty': str(item.quantity),
                    'title': item.sku.sku.display_name
                    }

            delta = {}
            for key, value in tinla_item_map.items():
                if atg_item_map.get(key,{}).get('qty',0) == value['qty']:
                    del atg_item_map[key]
                else:
                    delta[key] = value
                    
            if atg_item_map or delta:
                print ' Product mismatch', 
                print ' Tinla Delta: %s, ATG Delta: %s' % (delta, atg_item_map), 
                product_mismatch.append(order)

        except FtbOrder.DoesNotExist:
            if order.reference_order_id:
                print 'Order missing in atg',
                missing_in_atg.append(order)
            else:
                no_ref_order_id.append(order)
                print 'Missing atg order id in tinla. Tinla ID: %s' % order.id,

    print ''
    print 'Order missing in ATG: %s' % len(missing_in_atg)
    print 'ATG order id not attached: %s' % len(no_ref_order_id) 
    print 'Product mismatch: %s' % len(product_mismatch)
    print 'Amount mismatch: %s' % len(amount_mismatch)
    print 'Incomplete orders: %s' % len(incomplete_orders)
    print 'Failed orders: %s' % len(failed_orders)
    errors = len(missing_in_atg) + len(no_ref_order_id) + len(amount_mismatch)
    errors += len(incomplete_orders) + len(failed_orders) + len(product_mismatch)
    print 'Total errors: %s' % errors
    print ''
    

def audit_orders(from_date, to_date):
    
    print 'Order audit from %s to %s ' % (from_date, to_date)

    confirmed_orders = Order.objects.filter(state='confirmed', client=5, 
        payment_realized_on__gte = from_date,
        payment_realized_on__lte = to_date)


    payment_attempts = PaymentAttempt.objects.filter(status='approved',
        order__client=5, order__payment_realized_on__gte=from_date,
        order__payment_realized_on__lte=to_date)

    pending_orders = Order.objects.filter(state='pending_order', client=5,
        timestamp__day = from_date.day,
        timestamp__month = from_date.month,
        timestamp__year = from_date.year).exclude(
        payment_mode = 'credit-card').exclude(
        payment_mode = 'debit-card').exclude(
        payment_mode = 'netbanking').exclude(
        payment_mode = 'credit-card-emi-web')

    print ''
    print 'Confirmed orders: %s' % confirmed_orders.count()
    print 'Confirmed payments: %s' % payment_attempts.count()
    print 'Pending orders: %s' % pending_orders.count()

    print 'Analyzing confirmed orders: %s' % confirmed_orders.count()
    analyze_order_set(confirmed_orders)

    print 'Confirmed payments, but not confirmed orders'
    m = {}
    for attempt in payment_attempts:
        if attempt.order.reference_order_id not in m:
            m[attempt.order.reference_order_id] = True
        else:
            print 'Ref ID: %s. Dup payment' % attempt.order.reference_order_id
        if attempt.order.state != 'confirmed':
            print 'Ref ID: %s. Not confirmed' % attempt.order.reference_order_id


    print 'Analyzing pending orders: %s' % pending_orders.count()
    analyze_order_set(pending_orders)

if __name__ == '__main__':
    for n in range(1, 2):
        y = datetime.now() + timedelta(days=-n)
        n = y + timedelta(days=1)
        from_date = datetime(year=y.year, month=y.month, day=y.day)
        to_date = datetime(year=n.year, month=n.month, day=n.day)
        audit_orders(from_date, to_date)
