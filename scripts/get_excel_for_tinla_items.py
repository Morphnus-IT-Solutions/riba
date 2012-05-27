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

from django.contrib.auth.models import *
from django.contrib.contenttypes.models import *
from users.models import *
from analytics.models import *
import pyExcelerator
import random
from orders.models import *
from django.core.mail import EmailMessage

def purchases_report(queryset):
    if len(queryset) > 0:

        order_item = queryset[0]
        import csv, codecs
        from django.core.exceptions import PermissionDenied
        from django.template import Context, Template

        field_headers = ['Name','Phone','OrderId', 'Transaction No', 'Payment Notes','Pending Order Date', 'Order Date','Seller','Item','Gift', 'Qty', 'MRP', 'Offer Price','Shipping','Discount','Amount Paid','Agent','Delivery Notes','Gift Notes', 'Payment Mode','Delivery Address','Reference Order Id']
        field_names = ['f:user_name','f:user_phone','order', 'f:transaction_no', 'f:payment_notes', 'order.timestamp','order.payment_realized_on', 'f:seller','item_title', 'gift_title', 'qty','list_price','sale_price','shipping_charges','f:spl_discount','f:payable_amount_with_discount','f:booking_agent', 'f:delivery_notes', 'f:gift_notes', 'order.payment_mode','f:delivery_address','f:reference_order_id']
        ax = []
        qs = queryset 
        wb = pyExcelerator.Workbook()
        ws = wb.add_sheet('data')
        ws.write(0,0,)
        col = 0
        for header  in field_headers:
            ws.write(0,col,header)
            col +=1
        for obj in qs:
            acc = {}
            for field in field_names:
                if '.' in field:
                    o = getattr(obj,field.split('.')[0])
                    uf = unicode(getattr(o, field.split('.')[1]))
                elif 'f:' in field:
                    uf = unicode(getattr(obj,field.split('f:')[1])())
                else:
                    uf = unicode(getattr(obj, field))

                if '.' in field:
                    acc[field.replace('.','_')] =uf
                elif 'f:' in field:
                    acc[field.replace('f:','')] = uf
                else:
                    acc[field] = uf
            ax.append(acc)
        r = 1
        for row in ax:
            col = 0
            for field in field_names:
                if '.' in field:
                    field = field.replace('.','_')
                elif 'f:' in field:
                    field = field.replace('f:','')
                else:
                    field = field
                ws.write(r,col,row[field])
                col += 1
            r += 1
        #response = HttpResponse(mimetype='text/xls')
        random_number = random.randrange(99999999,999999999)
        file_name = '/tmp/orderreport%s.xls' % random_number
        wb.save(file_name)
        return file_name


def pending_order_report(queryset):
    if len(queryset) > 0:

        order_item = queryset[0]
        from django.core.exceptions import PermissionDenied
        from django.template import Context, Template

        ax = []
        field_headers = ['Name','Phone','OrderId','Pending Order Date','Seller','Item','Gift', 'Qty', 'MRP', 'Offer Price','Shipping','Discount','Amount Payable','Agent','Delivery Notes','Gift Notes', 'Payment Mode','Delivery Address']
        field_names = ['f:user_name','f:user_phone','order', 'order.timestamp', 'f:seller','item_title', 'gift_title', 'qty','list_price','sale_price','shipping_charges','f:spl_discount','f:payable_amount_with_discount','f:booking_agent', 'f:delivery_notes', 'f:gift_notes', 'order.payment_mode','f:delivery_address']

        qs = queryset
        wb = pyExcelerator.Workbook()
        ws = wb.add_sheet('data')
        ws.write(0,0,)
        col = 0
        for header  in field_headers:
            ws.write(0,col,header)
            col +=1
        for obj in qs:
            acc = {}
            for field in field_names:
                if '.' in field:
                    o = getattr(obj,field.split('.')[0])
                    uf = unicode(getattr(o, field.split('.')[1]))
                elif 'f:' in field:
                    try:
                        uf = unicode(getattr(obj,field.split('f:')[1])())
                    except:
                        uf = unicode('')
                else:
                    uf = unicode(getattr(obj, field))

                if '.' in field:
                    acc[field.replace('.','_')] =uf
                elif 'f:' in field:
                    acc[field.replace('f:','')] = uf
                else:
                    acc[field] = uf
            ax.append(acc)
        r = 1
        for row in ax:
            col = 0
            for field in field_names:
                if '.' in field:
                    field = field.replace('.','_')
                elif 'f:' in field:
                    field = field.replace('f:','')
                else:
                    field = field
                ws.write(r,col,row[field])
                col += 1
            r += 1
        #response = HttpResponse(mimetype='text/xls')
        random_number = random.randrange(99999999,999999999)
        file_name = '/tmp/pendingorderreport%s.xls' % random_number
        wb.save(file_name)
        return file_name


def cancelled_order_report(queryset):
    if len(queryset) > 0:

        order_item = queryset[0]
        from django.core.exceptions import PermissionDenied
        from django.template import Context, Template

        ax = []
        field_headers = ['Name','Phone','OrderId','Pending Order Date','Seller','Item','Gift', 'Qty', 'MRP', 'Offer Price','Shipping','Discount','Amount Payable','Agent','Delivery Notes','Gift Notes', 'Payment Mode','Delivery Address']
        field_names = ['f:user_name','f:user_phone','order', 'order.timestamp', 'f:seller','item_title', 'gift_title', 'qty','list_price','sale_price','shipping_charges','f:spl_discount','f:payable_amount_with_discount','f:booking_agent', 'f:delivery_notes', 'f:gift_notes', 'order.payment_mode','f:delivery_address']

        qs = queryset
        wb = pyExcelerator.Workbook()
        ws = wb.add_sheet('data')
        ws.write(0,0,)
        col = 0
        for header  in field_headers:
            ws.write(0,col,header)
            col +=1
        for obj in qs:
            acc = {}
            for field in field_names:
                if '.' in field:
                    o = getattr(obj,field.split('.')[0])
                    uf = unicode(getattr(o, field.split('.')[1]))
                elif 'f:' in field:
                    try:
                        uf = unicode(getattr(obj,field.split('f:')[1])())
                    except:
                        uf = unicode('')
                else:
                    uf = unicode(getattr(obj, field))

                if '.' in field:
                    acc[field.replace('.','_')] =uf
                elif 'f:' in field:
                    acc[field.replace('f:','')] = uf
                else:
                    acc[field] = uf
            ax.append(acc)
        r = 1
        for row in ax:
            col = 0
            for field in field_names:
                if '.' in field:
                    field = field.replace('.','_')
                elif 'f:' in field:
                    field = field.replace('f:','')
                else:
                    field = field
                ws.write(r,col,row[field])
                col += 1
            r += 1
        #response = HttpResponse(mimetype='text/xls')
        random_number = random.randrange(99999999,999999999)
        file_name = '/tmp/cancelledorderreport%s.xls' % random_number
        wb.save(file_name)
        return file_name


if __name__ == '__main__':
    from datetime import datetime, timedelta
    today = datetime.now()
    yesterday = today + timedelta(days=-1)
    today = today.strftime("%Y-%m-%d")
    yesterday = yesterday.strftime("%Y-%m-%d")
    order_items = OrderItem.objects.using('tinla_slave').filter(order__support_state='booked', 
        order__timestamp__gte=yesterday,order__timestamp__lt=today, order__client=1)
    p_file_name = pending_order_report(order_items)
    order_items = OrderItem.objects.using('tinla_slave').filter(order__support_state='confirmed', 
        order__payment_realized_on__gte=yesterday, order__payment_realized_on__lt=today, order__client=1)
    c_file_name = purchases_report(order_items)
    order_items = OrderItem.objects.using('tinla_slave').filter(order__support_state='cancelled', 
        order__payment_realized_on__gte=yesterday, order__payment_realized_on__lt=today, order__client=1)
    can_file_name = cancelled_order_report(order_items)
    subject = 'PO, CO and CanO report of %s' % yesterday
    body = 'PFA PO, CO and CanO Report of %s' % yesterday

    msg = EmailMessage(subject, body, 'report@chaupaati.com',
        ['hemanth@chaupaati.com','nikhil@chaupaati.com','amit@chaupaati.com','prashant@chaupaati.com','suhas.kajbaje@futuregroup.in',
        'sameer.virani@futuregroup.in','kais@chaupaati.com','muin@chaupaati.com','sandeep.rathi@futuregroup.in','saumil.dalal@futuregroup.in'],
        '',None)

    data1 = open(p_file_name, 'rb').read()
    data2 = open(c_file_name, 'rb').read()
    
    msg.attach('po%s.xls' % yesterday, data1)
    msg.attach('co%s.xls' % yesterday, data2)
    try:
        data3 = open(can_file_name, 'rb').read()
        msg.attach('cano%s.xls' % yesterday, data3)
    except:
        pass
    msg.send()
