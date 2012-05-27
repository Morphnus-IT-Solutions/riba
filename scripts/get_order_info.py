import os
import sys, pdb
import tempfile

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.fbsettings'

ROOT_FOLDER = os.path.dirname(os.path.realpath(os.path.dirname(__file__)))

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER)

# also add the parent folder
PARENT_FOLDER = os.path.dirname(ROOT_FOLDER)
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from django.db import connections
from orders.models import *
import pyExcelerator

def get_price_lists(order_id, sku, cursor):
    query = """select
            fbprd_commerce.getpricelistname(b.catalog_id, 'ListPrice PriceList'),
            fbprd_commerce.getpricelistname(b.catalog_id, 'SalePrice PriceList')
        from fbprd_commerce.dcspp_order a, fbprd_commerce.dcspp_item b 
        where a.order_id = b.order_ref and a.order_Id = '%s' and b.catalog_ref_id = '%s';""" % (order_id, sku)
    cursor.execute(query)
    return cursor.fetchone()

def add_to_worksheet(ws, row, order):
    cursor = connections['atg'].cursor()
    for oi in order.orderitem_set.all():
        ws.write(row,0, order.reference_order_id)
        ws.write(row,1, order.timestamp.strftime('%d-%m-%y'))
        ws.write(row,2, order.payment_mode)
        ws.write(row,3, order.user.user.username)
        ws.write(row,4, oi.seller_rate_chart.sku)
        ws.write(row,5, oi.item_title)
        ws.write(row,6, oi.qty)
        ws.write(row,7, str(oi.list_price))
        ws.write(row,8, str(oi.sale_price))
        ws.write(row,9, str(order.coupon_discount))
        ws.write(row,10, str(order.auto_promotions_discount))
        ws.write(row,11, str(order.payable_amount))
        list_price_list, sale_price_list = 0,0 # get_price_lists(order.reference_order_id, oi.seller_rate_chart.sku, cursor)
        ws.write(row,12, str(list_price_list))
        ws.write(row,13, str(sale_price_list))

        shipping_info = order.get_delivery_info()
        if shipping_info:
            shipping_address = shipping_info.address
            ws.write(row,14, shipping_address.address)
            ws.write(row,15, shipping_address.city.name)
            ws.write(row,16, shipping_address.state.name)
            ws.write(row,17, shipping_address.country.name)
            ws.write(row,18, shipping_address.pincode)
            ws.write(row,19, shipping_address.email)
            ws.write(row,20, shipping_address.phone)
        billing_info = BillingInfo.objects.filter(user=order.user)
        if billing_info:
            billing_info = billing_info[len(billing_info) - 1]
            billing_address = billing_info.address
            ws.write(row,21, billing_address.address)
            ws.write(row,22, billing_address.city.name)
            ws.write(row,23, billing_address.state.name)
            ws.write(row,24, billing_address.country.name)
            ws.write(row,25, billing_address.pincode)
            ws.write(row,26, billing_address.email)
            ws.write(row,27, billing_address.phone)
        first_name = ''
        last_name = ''
        if order.user.user.first_name:
            first_name = order.user.user.first_name
        elif billing_info:
            first_name = billing_info.first_name
        if order.user.user.last_name:
            last_name = order.user.user.last_name
        elif billing_info:
            last_name = billing_info.last_name
        ws.write(row,26,first_name)
        ws.write(row,27,last_name) 
        row += 1
    return row

def main(reference_order_ids):
    orders_not_found = []
    orders_held_back = []
    orders_given_go_ahead = []
    multiple_approved_orders_found = []

    wb = pyExcelerator.Workbook()
    ws = wb.add_sheet('approved in tinla')
    ws_o = wb.add_sheet('not approved in tinla')
    ws_m = wb.add_sheet('multiple approved in tinla')
    ws.write(0,0,)
    field_headers = ['orderId',  'Submitted on', 'payment mode', 'user login', 'sku', 'title',
        'qty', 'list price', 'sale price', 'coupon discount', 'auto promotion discount', 'order price',
        'list price list', 'sale price list',
        'shipping address line 1',
        'shipping city', 'shipping state', 'shipping country', 'shipping pincode',
        'shipping email', 'shipping phone', 'billing addressline1', 'billing city',
        'billing state', 'billing country', 'billing pincode', 'billing email',
        'billing phone', 'first name', 'last name']

    col = 0
    for header in field_headers:
        ws.write(0,col,header)
        ws_o.write(0,col,header)
        ws_m.write(0,col,header)
        col += 1

    row_a = 1 # row counter for approved sheet
    row_o = 1 # row counter for pending sheet
    row_m = 1 # row counter for multiple approved sheet
    for reference_order_id in reference_order_ids:
        orders = Order.objects.filter(reference_order_id=reference_order_id)
        if orders.exists():
            # case where order exists
            order_list_approved = []
            for order in orders:
                if order.paymentattempt_set.filter(status='approved').exists():
                    order_list_approved.append(order)
            len_order_list_approved = len(order_list_approved)
            if len_order_list_approved == 0:
                # case where there is no approved order
                print "== %s ==" % reference_order_id
                for order in orders:
                    if order.state == 'pending_order':
                        # insert all orders in 'pending_order' state to excel worksheet
                        row_o = add_to_worksheet(ws_o, row_o, order)
                        orders_given_go_ahead.append(reference_order_id)
                    print "Order:", order.id, order.payable_amount, order.state
                    for pa in order.paymentattempt_set.all():
                        print "\tPA:", pa.id, pa.amount, pa.status
                if reference_order_id not in orders_given_go_ahead:
                    orders_held_back.append(reference_order_id)
            elif len_order_list_approved == 1:
                # positive case: where single approved order exists
                # insert in approved excel worksheet
                try:
                    row_a = add_to_worksheet(ws, row_a, order_list_approved[0])
                except Exception, e:
                    pdb.set_trace()
            else:
                # negative case: where there more than one approved order
                for order_m in order_list_approved:
                    row_m = add_to_worksheet(ws_m, row_m, order_m)
                multiple_approved_orders_found.append((reference_order_id, len_order_list_approved))
        else:
            # case: where orders don't exist in tinla
            orders_not_found.append(reference_order_id)

    # Safely create a tempfile and close the file descriptor to save it as
    # empty file. This makes a persistent file on disk. We need to close the
    # descriptor, to be on the safer side because pyExcelerator works with
    # file's name and not file descriptor.
    fd, path = tempfile.mkstemp('.xls', 'FB_ORDERS_', '/tmp/')
    os.close(fd)
    # Save Workbook to file
    wb.save(path)
    if orders_not_found:
        print "No order information found for the following order ids in tinla:"
        for rid in orders_not_found:
            print rid
        print ""
    if orders_held_back:
        print "Order found on tinla and held back for more analysis:"
        for rid in orders_held_back:
            print rid
        print ""
    if orders_given_go_ahead:
        print "Order which are given go ahead based on state of 'pending_order' subject to payment match:"
        for rid in orders_given_go_ahead:
            print rid
        print ""
    if multiple_approved_orders_found:
        print "Multiple approved orders found for following order ids in tinla:"
        for rid in multiple_approved_orders_found:
            print rid[0], '\t', rid[1], 'approved orders'
        print ""
    print "order infomation is saved at: %s" % path

import sys
if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] == ('-h' or '--help'):
        sys.stderr.write('Usage: %s <file-with-reference-order-id>\n' % sys.argv[0])
        sys.stderr.write('Reference ids in file must be one reference_order_id per line\n')
    else:
        fsock = open(sys.argv[1], 'r')
        reference_order_ids = [line.strip() for line in fsock.readlines()]
        reference_order_ids = [rid for rid in reference_order_ids if rid]
        fsock.close()
        main(reference_order_ids)
# vim: tabstop=8 expandtab shiftwidth=4 softtabstop=4 autoindent smartindent
