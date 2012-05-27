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

        field_headers = ['OrderId', 'Article Id', 'Customer Name', 'Customer Address','Customer Email', 'Customer Phone','Total Order Amount','Payment Mode','Product Name', 'Quantity', 'Product MRP', 'Product Sale Price','Delivery Address','Delivery Notes', 'List Price','Discount']

        field_names = ['order','f:article_id','f:user_name','f:customer_address', 'f:user_email', 'f:user_phone', 'f:payable_amount','f:payment_mode', 'item_title', 'qty','list_price','sale_price','f:delivery_address','f:delivery_notes','list_price','f:spl_discount']
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
        field_headers = ['OrderId', 'Article Id', 'Customer Name', 'Customer Address','Customer Email', 'Customer Phone','Total Order Amount','Payment Mode','Product Name', 'Quantity', 'Product MRP', 'Product Sale Price','Delivery Address','Delivery Notes', 'List Price','Discount']
        field_names = ['order','f:article_id','f:user_name','f:customer_address', 'f:user_email', 'f:user_phone', 'f:payable_amount','f:payment_mode', 'item_title', 'qty','list_price','sale_price','f:delivery_address','f:delivery_notes','list_price','f:spl_discount']

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
        import csv, codecs
        from django.core.exceptions import PermissionDenied
        from django.template import Context, Template

        field_headers = ['OrderId', 'Article Id', 'Customer Name', 'Customer Address','Customer Email', 'Customer Phone','Total Order Amount','Payment Mode','Product Name', 'Quantity', 'Product MRP', 'Product Sale Price','Delivery Address','Delivery Notes', 'List Price','Discount']

        field_names = ['order','f:article_id','f:user_name','f:customer_address', 'f:user_email', 'f:user_phone', 'f:payable_amount','f:payment_mode', 'item_title', 'qty','list_price','sale_price','f:delivery_address','f:delivery_notes','list_price','f:spl_discount']
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
                    if 'f:payable_amount' == field:
                        uf = '-%s' % uf
                else:
                    uf = unicode(getattr(obj, field))
                    if 'qty' == field:
                        uf = '-%s' % uf

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

if __name__ == '__main__':
    p_file_name, c_file_name, cancelled_file_name = None, None, None
    from datetime import datetime, timedelta
    today = datetime.now()
    yesterday = today + timedelta(hours=-12, minutes=-3)
    #today = today.strftime("%Y-%m-%d")
    #yesterday = yesterday.strftime("%Y-%m-%d")
    order_items = OrderItem.objects.filter(order__state='pending_order', 
        order__timestamp__gte=yesterday,order__timestamp__lt=today, order__client=7)
    if order_items:
        p_file_name = pending_order_report(order_items)
    order_items = OrderItem.objects.filter(order__state='confirmed', 
        order__payment_realized_on__gte=yesterday, order__payment_realized_on__lt=today, order__client=7)
    c_file_name = purchases_report(order_items)
    order_items = OrderItem.objects.filter(order__state='cancelled', 
        order__modified_on__gte=yesterday,order__modified_on__lt=today, order__client=7)
    cancelled_file_name = cancelled_order_report(order_items)
    subject = 'PO,CO and cancelled order report of %s' % yesterday
    body = 'PFA PO,CO and Cancelled order Report of %s' % yesterday
    msg = EmailMessage(subject, body, 'report@ezoneonline.in',
        ['Nirmal.Mekala@futuregroup.in','Alok.kumar@futuregroup.in','Gaurav.shitak@futuregroup.in','Joe.Kochitty@futuregroup.in','Zishaan.Hayath@futuregroup.in','Nikhat.Patel@futuregroup.in'],
        '',None)
    data1 = open(p_file_name, 'rb').read()
    data2 = open(c_file_name, 'rb').read()
    data3 = open(cancelled_file_name, 'rb').read()
    msg.attach('po%s.xls' % yesterday, data1)
    msg.attach('co%s.xls' % yesterday, data2)
    msg.attach('cancelled%s.xls' % yesterday, data3)
    msg.send()
