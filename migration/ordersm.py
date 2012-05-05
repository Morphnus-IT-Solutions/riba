
import urllib2, urllib
from catalog.models import Brand, Product, SellerRateChart, Availability, AvailabilityConstraint
from categories.models import Category
from migration.models import ListingRateChartMap
from feeds.feed import Feed
import logging
from decimal import Decimal
from orders.models import *
from django.contrib.auth.models import User
from users.models import Profile
from django.utils import simplejson
from users.models import *
from locations.models import *
import datetime
import pyExcelerator
import xlrd
from accounts.models import Account
from django.template.defaultfilters import slugify, striptags

from utils import utils
import solr
from promotions.models import Coupon

log = logging.getLogger('request')

users_solr = solr.SolrConnection('http://192.168.91.101:8080/user/')
listing_solr = solr.SolrConnection('http://192.168.91.101:8080/listing/')

def user_solr_search(q, fields=None, highlight=None,
                  score=True, sort=None, sort_order="asc", **params):
    s = users_solr
    response = s.query(q, fields, highlight, score, sort, sort_order, **params)
    return response

def listing_solr_search(q, fields=None, highlight=None,
                  score=True, sort=None, sort_order="asc", **params):
    s = listing_solr
    response = s.query(q, fields, highlight, score, sort, sort_order, **params)
    return response


class MigrateOrders():

    _default_seller = Account.objects.get(code="chaupaati-bazaar")
    seller_account_map = {
        "129913" : Account.objects.get(code="9dot9"),
        "159907" : Account.objects.get(code="ack-international"),
        "79501" : Account.objects.get(code="ack"),
        "136688" : Account.objects.get(code="adya-international"),
        "13744" : Account.objects.get(code="alfa-marketing"),
        "172717" : Account.objects.get(code="storeji-anythinginit"),
        "118882" : Account.objects.get(code="bikanervala"),
        "189046" : Account.objects.get(code="casio"),
        "207678" : Account.objects.get(code="chandamama"),
        "34321" : Account.objects.get(code="chaupaati"),
        "34321" : Account.objects.get(code="combo"),
        "217127" : Account.objects.get(code="ezone"),
        "140518" : Account.objects.get(code="ferns-n-petals"),
        "34321" : Account.objects.get(code="flipkart"),
        "209685" : Account.objects.get(code="funskool"),
        "189805" : Account.objects.get(code="ibd"),
        "125301" : Account.objects.get(code="icici-lombard"),
        "213283" : Account.objects.get(code="ifb"),
        "182830" : Account.objects.get(code="iken"),
        "167702" : Account.objects.get(code="ibh"),
        "212639" : Account.objects.get(code="india today"),
        "144831" : Account.objects.get(code="infomedia18"),
        "189241" : Account.objects.get(code="jaipan"),
        "186840" : Account.objects.get(code="karbonn"),
        "215944" : Account.objects.get(code="kidzee"),
        "132534" : Account.objects.get(code="lava-mobiles"),
        "183732" : Account.objects.get(code="letsbuy"),
        "188822" : Account.objects.get(code="macmillan"),
        "208606" : Account.objects.get(code="mattel"),
        "186841" : Account.objects.get(code="micromax"),
        "218984" : Account.objects.get(code="mithaimate"),
        "209481" : Account.objects.get(code="my baby excel"),
        "161603" : Account.objects.get(code="myntra"),
        "167702" : Account.objects.get(code="ibh"),
        "204339" : Account.objects.get(code="newday"),
        "199719" : Account.objects.get(code="next gen publishing"),
        "211058" : Account.objects.get(code="ngbp"),
        "214164" : Account.objects.get(code="outlook group"),
        "189133" : Account.objects.get(code="penguin"),
        "154788" : Account.objects.get(code="robinage"),
        "218956" : Account.objects.get(code="skillofun"),
        "172717" : Account.objects.get(code="storeji-anythinginit"),
        "153201" : Account.objects.get(code="testminister"),
        "210988" : Account.objects.get(code="potluck"),
        "182826" : Account.objects.get(code="timtara"),
        "147143" : Account.objects.get(code="tinkle"),
        "23177" : Account.objects.get(code="toube-bas"),
        "160897" : Account.objects.get(code="videocon"),
        "187224" : Account.objects.get(code="videocon-kail"),
        "207697" : Account.objects.get(code="videocon-udcl"),
        "190526" : Account.objects.get(code="vu"),
        "215896" : Account.objects.get(code="wespro"),
        "211439" : Account.objects.get(code="whirlpool"),
        "146810" : Account.objects.get(code="zee-school"),
        "187223" : Account.objects.get(code="zenith"),
        "239367" : Account.objects.get(code="samsung-cdma"),
        "232894" : Account.objects.get(code="popleys-gold"),
    }
    def get_seller(self, seller_id):
        return self.seller_account_map.get(
                str(seller_id),
                self._default_seller)

    def get_related_payment_mode(self,paymentMode): 
        mode = {
            'card-ivr':'card-ivr',
            'card-moto':'card-moto',
            'card-phone':'card-moto',
            'card-web':'card-web',  
            'cheque':'mail',
            'COD':'cod',
            'collection-agent':'cod',
            'deposit-axis':'deposit-axis',
            'deposit-hdfc':'deposit-hdfc',
            'deposit-icici':'deposit-icici',
            'mail':'mail',
            'netbanking':'card-web',
            'transfer-axis':'transfer-axis',
            'transfer-hdfc':'transfer-hdfc',
            'transfer-icici':'transfer-icici',
            'VPP':'cod'
            }
        if paymentMode and paymentMode in mode:
            return mode[paymentMode]
        else:
            return ''

    def get_or_create_new_user(self,old_user):
        try:
            # get existing user profile
            usr = User.objects.get(username=old_user['mobile'])
            profile = Profile.objects.get(user = usr)
            return profile
        except User.DoesNotExist:
            log.error('Unable to find user for migrating order %s' % old_user['mobile'])
            return none

    def get_user(self, old_user_id):
        batch = user_solr_search('id:%s' % old_user_id)
        if batch and batch.results and len(batch.results) > 0:
            return batch.results[0]
        return None

    _other_brand_cache = None
    def get_other_brand(self, brand):
        if self._other_brand_cache:
            return self._other_brand_cache
        try:
            self._other_brand_cache = Brand.objects.get(name=brand)
            return self._other_brand_cache
        except Brand.DoesNotExist:
            brand = Brand(name=brand, slug=slugify(brand))
            brand.save()
            self._other_brand_cache = brand
            return self._other_brand_cache

    _other_category_cache = None
    def get_other_category(self, category):
        if self._other_category_cache:
            return self._other_category_cache
        try:
            self._other_category_cache = Category.objects.get(name=category)
            return self._other_category_cache
        except Category.DoesNotExist:
            category = Category(name=category, slug=slugify(category))
            category.save()
            self._other_category_cache = category
            return self._other_category_cache

    _availability_cache = None
    def get_available_every_where(self):
        if self._availability_cache:
            return self._availability_cache
        all_india = Availability()
        all_india.save()
        all_india_constraint = AvailabilityConstraint()
        all_india_constraint.status = 'available'
        all_india_constraint.zone = Country.objects.get(name='India')
        all_india_constraint.availability = all_india
        all_india_constraint.save()
        self._availability_cache = all_india
        return self._availability_cache

    def get_or_create_rate_chart(self, listing_id):
        try:
            rate_chart_map = ListingRateChartMap.objects.get(
                    listing_id = listing_id)
            if rate_chart_map.rate_chart:
                return rate_chart_map.rate_chart
        except ListingRateChartMap.DoesNotExist:
            pass

        results = listing_solr_search('id:%s' % listing_id)
        if results and results.results and len(results.results) > 0:
            listing = results.results[0]
            product = Product()
            product.title = listing.get('title','')
            product.description = listing.get('description','')
            product.currency = listing.get('currency','inr')
            product.brand = self.get_other_brand('Other')
            product.model = ''
            product.category = self.get_other_category('Other')
            product.type = 'normal'
            product.status = 'unavailable'
            product.save()

            rate_chart = SellerRateChart()
            rate_chart.listing_id = listing_id
            rate_chart.product = product
            rate_chart.seller = self.get_seller(listing.get('userId',0))
            rate_chart.status = 'unavailable'
            rate_chart.sku = listing.get('sku', '')
            rate_chart.condition = 'new'
            rate_chart.is_prefered = True
            rate_chart.list_price = Decimal(str(listing.get('mrp',0)))
            rate_chart.offer_price = Decimal(str(listing.get('askingPrice',0)))
            if rate_chart.offer_price > rate_chart.list_price:
                rate_chart.list_price = rate_chart.offer_price
            rate_chart.warranty = listing.get('warranty','')
            rate_chart.gift_title = listing.get('gifts','')
            rate_chart.shipping_charges = Decimal(str(listing.get('shippingCharges','0.0')))
            rate_chart.shipping_duration = listing.get('shippingDuration','7-10 working days')
            rate_chart.availability = self.get_available_every_where()
            rate_chart.stock_status = 'notavailable'
            rate_chart.status = 'deleted'
            rate_chart.save()

            listing_rate_chart_map = ListingRateChartMap(listing_id=listing_id, rate_chart=rate_chart)
            listing_rate_chart_map.save()

            return rate_chart

        return None


    def migrate_old_orders(self):
        product_map = {}
        old_orders = Orders.objects.filter(process='store')

        # some counts
        total_orders = len(old_orders)
        skipped = {
                "no-user-attached": 0,
                "no-order-items": 0,
                "no-user-found-from-solr": 0,
                "no-migrated-profile-found": 0,
                "duplicate-order-found": 0
                }

        for old_order in old_orders:
            try:

                if not old_order.userid:
                    skipped["no-user-attached"] += 1
                    log.info("Skipping order with no user id: %s" % old_order.id)
                    continue

                old_orderItems = OrderItems.objects.filter(orderid=old_order.id)
                if not old_orderItems:
                    skipped["no-order-items"] += 1
                    log.info("Skipping empty order: %s" % old_order.id)
                    continue
                
                old_user = self.get_user(old_order.userid)
                if not old_user:
                    skipped["no-user-found-from-solr"] += 1
                    log.info('Skipping order as user not found from solr: %s' % old_order.id)
                    continue

                new_user_profile = self.get_or_create_new_user(old_user)
                if not new_user_profile:
                    skipped["no-migrated-profile-found"] += 1 
                    log.info('Skipping order as new user profile not found: %s' % old_order.id)
                    continue

                try:
                    order = Order.objects.get(id=old_order.id)

                    order.billinginfo_set.all().delete()
                    order.deliveryinfo_set.all().delete()
                    order.giftinfo_set.all().delete()
                    order.shippingdetails_set.all().delete()
                    order.subscriptiondetails_set.all().delete()
                    order.orderitem_set.all().delete()

                except Order.DoesNotExist:
                    order = self.create_order(new_user_profile, old_order)

                delivery_info, address = self.add_delivery_info(self.add_delivery_address(old_order,new_user_profile),old_order,order)
                if not delivery_info:
                    skipped["unable-to-save-delivery-info"] += 1
                    log.info("Skipped as we are unable to save delivery info: %s" % old_order.id)
                    continue
                
                items_to_save = []
                for old_item in old_orderItems:
                    # get product id from the new system
                    seller_rate_chart = self.get_or_create_rate_chart(old_item.itemid)

                    # add order item into new system using old order item
                    order_item = self.add_orderitem(order,seller_rate_chart, old_item)
                    self.add_shipping_details(order_item, old_item)
                    items_to_save.append(order_item)

                # finaly update order billing
                order,coupon = self.updateOrderBilling(old_order,order,items_to_save)
            except Exception,e:
                log.exception('Error migrating orders %s' % repr(e))
                raise

        print 'Total orders %s' % total_orders
        for key, value in skipped.iteritems():
            print key, value

    def add_shipping_details(self, order_item, old_item):
        shipping_details = ShippingDetails()
        shipping_details.tracking_no = old_item.couriertrackingnumber or ''
        shipping_details.tracking_url = old_item.courierurl or ''
        shipping_details.courier = old_item.courierservicename or ''
        shipping_details.notes = ''
        shipping_details.order_item = order_item
        shipping_details.save()

    def get_agent(self, agent_name):
        try:
            usr = User.objects.get(username=agent_name)
            p = usr.get_profile()
            return p
        except User.DoesNotExist:
            try:
                usr = User.objects.create_user(agent_name, '%s@chaupaati.in' % agent_name)
                usr.save()
                p = Profile(user=usr, primary_phone=agent_name)
                p.created_on = datetime.datetime.now()
                p.save()
                return p
            except Exception, e:
                log.error('Error creating agent %s' % repr(e))
                return None
        except Profile.DoesNotExist:
            p = Profile(user=usr, primary_phone=agent_name, )
            p.created_on = datetime.datetime.now()
            p.save()
            return p


    def create_order(self, profile, old_order):
        order = Order()
        try:
            order.id = old_order.id
            order.state = old_order.state
            order.user = profile
            order.reference_order_id = old_order.friendlyorderid

            if old_order.paymentmode:
                order.payment_mode = self.get_related_payment_mode(old_order.paymentmode)
            if old_order.paymentrealizedmode:
                order.payment_realized_mode = self.get_related_payment_mode(old_order.paymentrealizedmode)
            if old_order.callid:
                order.call_id = old_order.callid

            order.modified_on = old_order.modifiedon
            order.timestamp = old_order.timestamp
            order.payment_realized_on = old_order.paymentrealizedon

            if old_order.createdby:
                agent = self.get_agent(old_order.createdby)
                if agent:
                    order.agent = agent
            order.save()
        except Exception, e:
            log.exception('Error creating order %s' % repr(e))
            raise
        return order

    def get_coupon(self, coupon_code):
        try:
            return Coupon.objects.get(code = coupon_code)
        except Coupon.DoesNotExist:
            return Coupon()
    
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
            coupon = self.get_coupon(old_order.discountcode)
            coupon.code = old_order.discountcode
            coupon.applies_to = 'order_total'
            if old_order.discountcode.find("PC") > 0 or old_order.discountcode.find("pc") > 0:
                coupon.discount_type = 'percentage'
                value = Decimal(old_order.discountcode.lower().replace('chpc','').replace('ch','').replace('pc',''))
                coupon.discount_value = value
            else:
                coupon.discount_type = 'fixed'
                coupon.discount_value = old_order.coupondiscount or Decimal('0.0')
            coupon.save()
            order.coupon = coupon
            order.coupon_discount = coupon.discount_value
            order.payable_amount = order.payable_amount - order.coupon_discount

        order.save()
        return order,coupon

    def add_orderitem(self,order,seller_rate_chart, old_item):
        '''add new item'''
        orderitem = OrderItem()
        orderitem.order = order
        orderitem.seller_rate_chart = seller_rate_chart
        orderitem.item_title = seller_rate_chart.product.title
        orderitem.gift_title = seller_rate_chart.gift_title
        if not old_item.quantity:
            orderitem.qty = 1
        else:
            orderitem.qty = old_item.quantity

        if not old_item.itemprice:
            itemprice = Decimal(0)
        else:
            itemprice = Decimal(str(old_item.itemprice))
        orderitem.list_price = itemprice * orderitem.qty

        if not old_item.billedamount:
            billedamount = Decimal(0)
        else:
            billedamount = Decimal(str(old_item.billedamount))
        orderitem.sale_price = billedamount
        if old_item.shippingcharges:
            orderitem.shipping_charges = old_item.shippingcharges * old_item.quantity
        else:
            orderitem.shipping_charges = 0
        orderitem.save()
        return orderitem

    def add_delivery_info(self,address,old_order,order):
        delivery_info = DeliveryInfo()
        if address:
            delivery_info.address = address
            delivery_info.notes = old_order.deliverynotes or ''
            delivery_info.order = order
            delivery_info.save()
        return delivery_info,address
        

    def add_delivery_address(self,old_order,profile):
        address = Address()
        address.phone = old_order.deliveryphone or ''
        address.name = old_order.deliveryname or ''
        address.address = old_order.deliveryaddress or ''
        address.pincode = old_order.deliverypincode or ''

        address.country = utils.get_or_create_country(old_order.deliverycountry or '', True)
        address.state = utils.get_or_create_state(old_order.deliverystate or '', address.country, True)
        address.city = utils.get_or_create_city(old_order.deliverycity or '', address.state, True)
        
        address.type = 'delivery'
        address.profile = profile
        address.save()
        return address

    def save_product_map(self):
        book = xlrd.open_workbook("/tmp/updated_map.xls")
        sh = book.sheet_by_index(0)
        header = sh.row(0)
        for i in range(1, sh.nrows):
            row = sh.row(i)
    
    def get_product_map(self):
        book = xlrd.open_workbook("~/apps/tinla/migrations/id_map.xls")
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
                    log.info('New title')
            except Exception, e:
                log.exception(repr(e))
        return id_map

    def create_product_map(self):
        file = open("/tmp/uniq-product-ids.txt","r")
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
        item_info = ['old_id','old_title','options','ids','status']
        for x in item_info:
            ws.write(row,col,x)
            col += 1
        for id in ids:
            try:
                ListingRateChartMap.objects.get(listing_id = id)
                continue
            except ListingRateChartMap.DoesNotExist:
                pass
            row += 1
            try:
                results = listing_solr_search('id:%s' % id)
                if results and results.results and len(results.results) > 0:
                    prod = results.results[0]
                else:
                    log.error('Have not found a matching product from solr %s' % id)
                    continue

                if prod['isActive']:
                    if 'sku' in prod:
                        try:
                            src = SellerRateChart.objects.get(sku=prod['sku'],
                                    seller=self.get_seller(prod['userId']))
                            listing_rate_chart_map = ListingRateChartMap(listing_id=id, rate_chart=src)
                            listing_rate_chart_map.save()
                            continue
                        except SellerRateChart.DoesNotExist:
                            product = Product.objects.filter(title__contains=prod['title'])
                            ws.write(row,0,id)
                            ws.write(row,1,prod['title'])
                            ws.write(row,2,"\r\n ".join(x.title for x in product))
                            ws.write(row,3,", ".join(str(x.id) for x in product))
                            ws.write(row,4,"active")
                    else:
                        product = Product.objects.filter(title__contains=prod['title'])
                        ws.write(row,0,id)
                        ws.write(row,1,prod['title'])
                        ws.write(row,2,"\r\n ".join(x.title for x in product))
                        ws.write(row,3,", ".join(str(x.id) for x in product))
                        ws.write(row,4,"active")
                else:
                    if 'sku' in prod:
                        if prod['sku']:
                            try:
                                src = SellerRateChart.objects.get(sku=prod['sku'],
                                        seller=self.get_seller(prod['userId']))
                                listing_rate_chart_map = ListingRateChartMap(listing_id=id, rate_chart=src)
                                listing_rate_chart_map.save()
                                continue
                            except SellerRateChart.DoesNotExist:
                                product = Product.objects.filter(title__contains=prod['title'])
                                ws.write(row,0,id)
                                ws.write(row,1,prod['title'])
                                ws.write(row,2,"\r\n ".join(x.title for x in product))
                                ws.write(row,3,", ".join(str(x.id) for x in product))
                                ws.write(row,4,"inactive")
                    else:
                        product = Product.objects.filter(title__contains=prod['title'])
                        ws.write(row,0,id)
                        ws.write(row,1,prod['title'])
                        ws.write(row,2,"\r\n ".join(x.title for x in product))
                        ws.write(row,3,", ".join(str(x.id) for x in product))
                        ws.write(row,4,"inactive")
            except Exception,e:
                log.exception('Error creating product mapping %s' % repr(e))
        file_name = '/tmp/id_map.xls'
        wb.save(file_name)
