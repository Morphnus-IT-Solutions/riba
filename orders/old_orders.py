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

import urllib2
import urllib
from lxml import etree
from categories.models import Category
from catalog.models import Brand, Product, SellerRateChart, Availability
from utils import htmlutils
from feeds.models import *
from feeds import feedutils
from feeds.feed import Feed
from django.template.defaultfilters import slugify, striptags
import logging
from django.conf import settings
from decimal import Decimal
from django.utils.html import strip_tags
from orders.models import *
from django.contrib.auth.models import User
from django.utils import simplejson
from users.models import *
from locations.models import *
import datetime
import pyExcelerator
import xlrd

log = logging.getLogger('feeds')

class migrateOrders(Feed):

    def get_related_payment_mode(self,paymentMode):
        print '@@@@paymentmode',paymentMode
        mode = {'card-ivr':'card-ivr',
            'card-moto':'card-moto',
            'card-phone':'card-moto',
            'card-web':'card-web',
            'cheque':'mail',
            'COD':'cod',
            'collection-agent':'mail',
            'deposit-axis':'deposit-axis',
            'deposit-hdfc':'deposit-hdfc',
            'deposit-icici':'deposit-icici',
            'mail':'mail',
            'netbanking':'card-web',
            'transfer-axis':'transfer-axis',
            'transfer-hdfc':'transfer-hdfc',
            'transfer-icici':'transfer-icici',
            'VPP':'cod'}
        if paymentMode and paymentMode in mode:
            pmode = mode[paymentMode]
        else:
            pmode = ''

        return pmode

    def get_or_create_new_user(self,old_user):
        try:
            '''get existing user profile'''
            usr = User.objects.get(username=old_user['mobile'])
            profile = Profile.objects.get(user = usr)
        except User.DoesNotExist:
            print '@@@@adding new user'''
            '''add new user and profile'''
            if 'email' in old_user:
                email = old_user['email']
            else:
                email = ''
            new_user = User.objects.create_user(old_user['mobile'],email,None)
            profile = Profile()
            profile.user = new_user
            profile.full_name = new_user.username
            profile.primary_phone = new_user.username
            profile.created_on = datetime.datetime.now()
            profile.save()
        except Profile.DoesNotExist:
            print '@@@profile doesnot exist'
            profile = Profile()
            profile.user = usr
            profile.primary_phone = usr.username
            profile.full_name = usr.username
            profile.created_on = datetime.datetime.now()
            profile.save()

        return profile

    def migrate_old_orders(self):
        '''get old-new product id mapping'''
        product_map = self.get_product_map()
        '''get all old orders'''
        for old_order in Orders.objects.iterator():
            url = 'http://192.168.91.101:8080/user/select?indent=on&version=2.2&q=id%3A' + str(old_order.userid) + '&start=0&rows=10&fl=*%2Cscore&qt=standard&wt=json&explainOther=&hl.fl='
            try:
                '''get all old orderitems'''
                old_orderItems = OrderItems.objects.filter(orderid=old_order.id)
                print '@@@items', old_orderItems
                if not old_orderItems:
                    continue
                found = True
                for old_item in old_orderItems:
                    if not old_item.itemid in product_map:
                        found = False
                if not found:
                    continue

                print '@@@@@',url
                json = urllib2.urlopen(url).read()
                dict = simplejson.loads(json)
                '''get old user'''
                if not dict['response']['docs']:
                    continue
                old_user = dict['response']['docs'][0]
                print '@@@@OLD USER', old_user
                '''create of get user from new system'''
                new_user_profile = self.get_or_create_new_user(old_user)

                '''create new order using old order'''
                print '@@@@@creating order'

                try:
                    order = Order.objects.get(id=old_order.id)
                    continue
                except Order.DoesNotExist:
                    order = self.create_order(new_user_profile,old_order)
                    '''add delivery info into the order'''
                    print '@@@@adding delivery info'
                    delivery_info,address = self.add_delivery_info(self.add_delivery_address(old_order,new_user_profile),old_order,order)
                    if not delivery_info:
                        print '@@@failed for delivery info'
                        continue

                    print '@@@adding orderitems'
                    items_to_save = []
                    for old_item in old_orderItems:
                        if old_item.itemid:
                            '''get product id from the new system'''
                            new_prod_id = product_map[old_item.itemid]
                            print '@@@getting product'
                            new_prod = Product.objects.get(id=new_prod_id)

                            seller_rate_chart = SellerRateChart.objects.get(product=new_prod,is_prefered=True)
                            '''add order item into new system using old order item'''
                            print '@@@adding order item'
                            order_item = self.add_orderitem(order,seller_rate_chart, old_item)
                            items_to_save.append(order_item)


                    order_items = OrderItem.objects.filter(order=order)
                    '''finaly update order billing'''
                    print '@@@@updateing billing'
                    order,coupon = self.updateOrderBilling(old_order,order,items_to_save)
                    for item in items_to_save:
                        item.save()
                    order.save()
                    if coupon:
                        coupon.save()
                    if address:
                        address.save()
                        delivery_info.save()
            except Exception,e:
                print '@@@@@Exception',e
                continue

    def create_order(self,profile, old_order):
        print '@@order not found'
        order = Order()
        try:
            if old_order.paymentmode:
                paymentMode = self.get_related_payment_mode(old_order.paymentmode)
            else:
                paymentMode = None
            if old_order.callid:
                callId = old_order.callid
            else:
                callId = ''
            order.reference_order_id = old_order.id
            order.id = old_order.id
            print '@@@profile',profile
            order.user = profile
            order.state = old_order.state or 'cart'
            if paymentMode:
                order.payment_mode = paymentMode
            if callId:
                order.call_id = callId
            print '@@here1'
            order.timestamp = old_order.timestamp or datetime.datetime.now()
            print '@@here2'
            order.payment_realized_on = old_order.paymentrealizedon or datetime.datetime.now()
            print '@@here3'
            order.payment_realized_mode = self.get_related_payment_mode(old_order.paymentrealizedmode)
            print '@@here4'
            order.modified_on = old_order.modifiedon or datetime.datetime.now()
            print '@@here5'
            #order.save(commit=False)
            print '@@here6'
        except Exception,e:
            print '####exception in order',e
        return order

    def updateOrderBilling(self,old_order,order, orderItems):

        list_price_total = Decimal(0)
        total = Decimal(0)
        shipping_charges = Decimal(0)
        taxes = Decimal(0)
        transaction_charges = Decimal(0)
        payable_amount = Decimal(0)

        for item in orderItems:
            list_price_total += item.list_price
            total += item.sale_price
            shipping_charges += item.shipping_charges
            payable_amount += (item.sale_price + item.shipping_charges)

        order.total = total
        order.list_price_total = list_price_total
        order.shipping_charges = shipping_charges
        order.payable_amount = payable_amount
        coupon = None
        if old_order.discountcode:
            coupon = Coupon()
            coupon.code = old_order.discountcode
            coupon.applies_to = 'order_total'
            if old_order.discountcode.find("PC") > 0 or old_order.discountcode.find("pc") > 0:
                coupon.discount_type = 'percentage'
            else:
                coupon.discount_type = 'fixed'
            coupon.discount_value = old_order.coupondiscount
            #coupon.save(commit=False)
            order.coupon = coupon
            order.coupon_discount = coupon.discount_value

        return order,coupon

    def add_orderitem(self,order,seller_rate_chart, old_item):
        '''add new item'''
        orderitem = OrderItem()
        orderitem.order = order
        orderitem.seller_rate_chart = seller_rate_chart
        orderitem.item_title = seller_rate_chart.product.title
        orderitem.gift_title = seller_rate_chart.gift_title
        if not old_item.quantity:
            qty = 1
        else:
            qty = old_item.quantity

        orderitem.qty = qty

        print '@@@', old_item.itemprice
        if not old_item.itemprice:
            itemprice = Decimal(0)
        else:
            itemprice = Decimal(str(old_item.itemprice))
        orderitem.list_price = itemprice * qty
        print '@@', old_item.billedamount
        if not old_item.billedamount:
            billedamount = Decimal(0)
        else:
            billedamount = Decimal(str(old_item.billedamount))
        orderitem.sale_price = billedamount
        if old_item.shippingcharges:
            orderitem.shipping_charges = old_item.shippingcharges * old_item.quantity
        else:
            orderitem.shipping_charges = 0
        #orderitem.save(commit=False)

        return orderitem

    def add_delivery_info(self,address,old_order,order):
        print '@@@adding delivery info'
        delivery_info = DeliveryInfo()
        if address:
            delivery_info.address = address
            delivery_info.name = old_order.deliveryname or ''
            delivery_info.phone = old_order.deliveryphone or ''
            delivery_info.notes = old_order.deliverynotes or ''
            delivery_info.order = order
            #delivery_info.save(commit=False)
        return delivery_info,address


    def add_delivery_address(self,old_order,profile):
        print '@@Adding delivery address'
        print '@@deliverycity',old_order.deliverycity
        print '@@deliverystate', old_order.deliverystate
        print '@@deliverycountry', old_order.deliverycountry
        address = Address()
        address.address = old_order.deliveryaddress or ''
        address.pincode = old_order.deliverypincode or ''
        try:
            address.city = City.objects.get(name=old_order.deliverycity)
            address.state = State.objects.get(name=old_order.deliverystate)
            address.country = Country.objects.get(name=old_order.deliverycountry)
        except City.DoesNotExist:
            print '@@@failed city',old_order.deliverycity, ' not found'
            if old_order.deliverycity:
                try:
                    state = State.objects.get(name=old_order.deliverystate)
                except State.DoesNotExist:
                    state = State()
                    state.name = old_order.deliverystate
                    state.country = Country.objects.get(name='India')
                    state.user_created = True
                    state.save()
                city = City()
                city.name = old_order.deliverycity
                city.state = state
                city.user_created = True
                city.save()
                address.city = city
                address.state = state
                address.country = state.country
            else:
                city = City.objects.get(name='Mumbai')
                address.city = city
                address.state = city.state
                address.country = city.state.country
        except State.DoesNotExist:
            print '@@@failed state',old_order.deliverystate, ' not found'
            print '@@@',address.city.state
            address.state = address.city.state
            address.country = address.state.country
        except Country.DoesNotExist:
            print '@@@failed country',old_order.deliverycountry, ' not found'
            print '@@',address.state.country
            address.country = address.state.country
        except Exception,e:
            print '@@@@',e

        address.type = 'delivery'
        address.profile = profile
        address.save()
        return address

    def get_product_map(self):
        print '@@@@getting map'
        book = xlrd.open_workbook("/tmp/id_map.xls")
        sh = book.sheet_by_index(0)
        header = sh.row(0)
        map = {}
        dict = {}
        idx = 0
        id_map = {}
        for x in header:
            val = x.value.strip().lower()
            map[val] = idx
            idx += 1
        for i in range(1, sh.nrows):
            row = sh.row(i)
            try:
                oldId = row[map['old_id']].value
                oldTitle = row[map['old_title']].value
                newTitle = row[map['new_title']].value
                try:
                    prod = Product.objects.filter(title = newTitle)
                    if len(prod) == 1:
                        id_map[oldId] = prod[0].id
                except Product.DoesNotExist:
                    print '@@@not found',newTitle
            except Exception, e:
                print '@@@@',e
        print '@@@map', id_map
        return id_map

    def create_product_map(self):
        file = open("/home/nilesh/dev/websvn/trunk/unique.txt","r")
        ids = []
        id_map = {}
        for line in file:
            id = line.strip()
            ids.append(id)
        file.close()
        wb = pyExcelerator.Workbook()
        ws = wb.add_sheet('data')
        ws.write(0,0,)
        row = 0
        col = 0
        item_info = ['old_id','old_title','options','ids']
        for x in item_info:
            ws.write(row,col,x)
            col += 1
        for id in ids:
            row += 1
            url = 'http://192.168.91.101:8080/listing/select?indent=on&version=2.2&q=id%3A' + id +'&start=0&rows=10&fl=*%2Cscore&qt=standard&wt=json&explainOther=&hl.fl='
            try:
                json = urllib2.urlopen(url).read()
                dict = simplejson.loads(json)
                prod = dict['response']['docs'][0]
                if prod['isActive']:
                    print '@@active'
                    if 'sku' in prod:
                        print '@@',prod['sku']
                        try:
                            src = SellerRateChart.objects.select_related('product').get(sku=prod['sku'])
                            product = src.product
                            id_map[id] = product.id
                            ws.write(row,0,id)
                            ws.write(row,1,prod['title'])
                            ws.write(row,2,product.title)
                            ws.write(row,3,product.id)
                        except:
                            product = None
                            ws.write(row,0,id)
                            ws.write(row,1,prod['title'])
                            print '@@@active product not found',prod['sku']
                    else:
                        try:
                            product = Product.objects.filter(title__contains=prod['title'])
                            ws.write(row,0,id)
                            ws.write(row,1,prod['title'])
                            ws.write(row,2,", ".join(x.title for x in product))
                            ws.write(row,3,", ".join(x.id for x in product))
                            if len(product) == 1:
                                id_map[id] = product[0].id
                        except:
                            product = None
                            ws.write(row,0,id)
                            ws.write(row,1,prod['title'])
                            print '@@active product without sku not found with title',prod['title']
                else:
                    print '@@inactive'
                    if 'sku' in prod:
                        if prod['sku']:
                            try:
                                src = SellerRateChart.objects.select_related('product').get(sku=prod['sku'])
                                product = src.product
                                id_map[id] = product.id
                                ws.write(row,0,id)
                                ws.write(row,1,prod['title'])
                                ws.write(row,2,product.title)
                                ws.write(row,3,product.id)
                            except:
                                try:
                                    product = Product.objects.filter(title__contains=prod['title'])
                                    if len(product) == 1:
                                        id_map[id] = product[0].id
                                    ws.write(row,0,id)
                                    ws.write(row,1,prod['title'])
                                    ws.write(row,2,", ".join(x.title for x in product))
                                    ws.write(row,3,", ".join(x.id for x in product))
                                except:
                                    product = None
                                    ws.write(row,0,id)
                                    ws.write(row,1,prod['title'])
                                    print '@@@inactive product not found with title',prod['title']
                    else:
                        try:
                            product = Product.objects.filter(title__contains=prod['title'])
                            if len(product) == 1:
                                id_map[id]= product[0].id
                            ws.write(row,0,id)
                            ws.write(row,1,prod['title'])
                            ws.write(row,2,", ".join(x.title for x in product))
                            ws.write(row,3,", ".join(x.id for x in product))
                        except:
                            product = None
                            ws.write(row,0,id)
                            ws.write(row,1,prod['title'])
                            print '@@inactive product without sku not found', prod['title']
            except Exception,e:
                print '@@',e
        file_name = '/home/nilesh/id_map.xls'
        wb.save(file_name)
        return id_map

if __name__ == '__main__':
    orders = migrateOrders()
    orders.migrate_old_orders()
    #map = orders.get_product_map()
    print '@@@@doneeeeeeeeeee'
