from django.db import models
from decimal import Decimal, getcontext, ROUND_HALF_UP, ROUND_UP
import math
from datetime import datetime, timedelta
import xml.etree.ElementTree as xml
from django.db.models import Q, Sum
from utils import utils
from catalog.models import SellerRateChart, BundleProducts
from accounts.models import Account
from locations.models import Address, AddressBook
from web.views.as_views import write_to_as
from lists.models import *
from orders.signals import pending_order_signal, confirmed_order_signal
from pricing.models import DomainLevelPriceList
import logging
from django.utils import simplejson
from payments.models import PaymentAttempt, PointsHeader, PaymentLog, RefundLog
from django.db import transaction
from django.db.models import Max
from indexer import indexer
from django.conf import settings

log = logging.getLogger('fborder')


def encoder(s, encoding):
    try:
        return s.encode(encoding, 'ignore')
    except AttributeError:
        return s
xml._encode = encoder


class Order(models.Model):
    class Meta:
        permissions = (
            ('can_confirm_order','Can confirm order'),
        )

    PAYMENT_MODES = (
        ('card-web','Credit/Debit Card (web)'),
        ('card-moto','Credit Card (Moto)'),
        ('card-ivr','Credit Card (IVR)'),
        ('deposit-hdfc','Deposit (HDFC)'),
        ('deposit-icici','Deposit (ICICI)'),
        ('deposit-axis','Deposit (AXIS)'),
        ('transfer-hdfc','Transfer (HDFC)'),
        ('transfer-icici','Transfer (ICICI)'),
        ('transfer-axis','Transfer (AXIS)'),
        ('mail','Cheque/DD/Cash'),
        ('payback','Payback'),
        ('cod','COD'))
   
    GATEWAY = {'card-moto':'moto',
            'card-ivr':'atom-ivr',
            'deposit-hdfc':'deposit',
            'deposit-icici':'deposit',
            'deposit-axis':'deposit',
            'transfer-hdfc':'transfer',
            'transfer-icici':'transfer',
            'transfer-axis':'transfer',
            'mail':'mail',
            'ICICICash' : 'mail',
            'easybill' : 'mail',
            'Itz' : 'mail',
            'suvidha' : 'mail',
            'cheque':'mail',
            'dd':'mail',
            'cash':'mail',
            'cod':'cod',
            'card-at-store':'CCST',
            'cash-at-store':'CAST',
            'pay-at-store-by-card':'CCST',
            'pay-at-store-by-cash':'CAST'}

    ADMIN_PAYMENT_MODES = (
        ('card-moto','Credit Card (Moto)'),
        ('card-ivr','Credit Card (IVR)'),
        ('deposit-hdfc','Deposit (HDFC)'),
        ('deposit-icici','Deposit (ICICI)'),
        ('deposit-axis','Deposit (AXIS)'),
        ('transfer-hdfc','Transfer (HDFC)'),
        ('transfer-icici','Transfer (ICICI)'),
        ('transfer-axis','Transfer (AXIS)'),
        ('cash','Cash'),
        ('dd','Demand Draft'),
        ('cheque','Cheque'),
        ('card-at-store','Card At Store'),
        ('cash-at-store','Cash At Store'),
        ('pay-at-store-by-card','Pay at Store by Card'),
        ('pay-at-store-by-cash','Pay at Store by Cash'),
        ('easybill', 'EasyBill'),
        ('Itz', 'Itz Cash'),
        ('suvidha','Suvidha'),
        ('ICICICash','ICICICash'),
        ('cod','COD'))
    
    STATES = (
        ('unassigned_cart','Unassinged Cart'),
        ('cart','Cart'),
        ('guest_cart','Guest Cart'),
        ('temporary_cart','Temporary Cart'),
        ('buy_later','Buy Later'),
        ('awaiting xml creation','Awaiting XML Creation'),
        ('processing xml','Processing XML'),
        ('modified','Modified'))
    SUPPORT_STATES = (
        ('booked','Booked'),    #Pending order
        ('paid','Paid'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('invoiced', 'Invoiced'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'))
    user = models.ForeignKey('users.Profile',blank=True,null=True)
    state = models.CharField(max_length=25,default='unassigned_cart',verbose_name='State',choices=STATES, db_index=True)
    support_state = models.CharField(max_length=15, null=True, blank=True, verbose_name='Support State', choices=SUPPORT_STATES, db_index=True)
    #sum of orderitem mrps
    list_price_total = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0),verbose_name='List price')
    #sum of orderitem offer prices
    total = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0),verbose_name='Offer price')
    #sum of orderitem cashback amounts
    cashback_amount_total = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0),verbose_name='Cashback',blank=True,null=True)
    #sum of orderitem shipping charges
    shipping_charges = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0),verbose_name='Shipping')
    #sum of taxes on orderitem. not used currently
    taxes = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    #payment gateway charges. not used 
    transaction_charges = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    #any discount which is applied by user (order level)
    coupon_discount = models.DecimalField(max_digits=22,decimal_places=2,blank=True,null=True,default=Decimal(0),verbose_name='Spl discount')
    #any discount which is applied by system (order level)
    auto_promotions_discount = models.DecimalField(max_digits=22,decimal_places=2,blank=True,null=True,default=Decimal(0),verbose_name='Promotion discount')
    #applied coupon
    coupon = models.ForeignKey('promotions.Coupon',blank=True,null=True)
    #not used
    top10_discount = models.DecimalField(max_digits=22,decimal_places=2,blank=True,null=True,default=Decimal(0))
    #final amount to ask payment gateway
    payable_amount = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    timestamp = models.DateTimeField(blank=True,null=True, auto_now_add=True, verbose_name='Booking Date', db_index=True)
    #payment realization date
    payment_realized_on = models.DateTimeField(blank=True,null=True,verbose_name='Order date', db_index=True)
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True, db_index=True)
    #will not be used from 15-12-2011
    payment_realized_mode = models.CharField(max_length=25,blank=True,default='',choices=PAYMENT_MODES,verbose_name='Payment mode')
    #will not be used from 15-12-2011. use timestamp field
    booking_timestamp = models.DateTimeField(blank=True,null=True, auto_now_add=True, verbose_name='Booking Date')
    #date when order is confirmed
    confirming_timestamp = models.DateTimeField(blank=True,null=True, verbose_name='Confirming Date')
    #date when order is sent to SAP
    medium = models.CharField(max_length=20,blank=True,default='cc',verbose_name='Medium',choices=(
        ('guest','Guest Cart'),
        ('temporary','Temporary Cart'),
        ('normal','Normal Cart')))
        #('cc','Call Center'),
        #('store','Store'),
        #('web','Website'),
        #('support', 'Support'),
        #('mob','Mobile')))
    client = models.ForeignKey('accounts.Client')
    client_domain = models.ForeignKey('accounts.ClientDomain', null=True, blank=True, default=None)
    verify_code = models.IntegerField(blank=True, null=True)
    #Added new field 'notes' to save any additional notes related to order like FreeOrder on Aug.12, etc. 
    notes = models.CharField(max_length=100,blank=True,default='')
    
    def __unicode__(self):
        return str(self.id)

    #required - prady
    def get_order_items(self, request, **kwargs):
        ''' Returns the order line items which are not cancelled
        '''
        qs = self.orderitem_set.all()
        return self.get_objects(request, qs, **kwargs)

    '''def get_order_info(self):
        info = 'Tinla id: %s, Reference Order Id %s' % (self.id, self.reference_order_id)
        info += '===========Payable Amount: %s' % (self.payable_amount)
        info += '===========Coupon %s, Discount : %s' % (self.coupon.code if self.coupon else None,self.coupon_discount)
        info += '===========Top10 Discount: %s' % (self.top10_discount)
        info += '===========Order placed on %s , selected payment mode %s' % (self.payment_realized_on, self.payment_mode)
        info += '===========Items======================'
        for i in self.get_items_for_billing(None).iterator():
            info = '%s %s' % (info,i.item_info())
        info += 'Shipping info: ======================='
        di = self.get_address(None, type='delivery')
        #if self.get_delivery_info():
        #    info = '%s %s' % (info,self.get_delivery_info().address)
        info += '======================================='
        info += 'Billing info: ========================='
        billing_info = self.user.billinginfo_set.all()
        if billing_info:
            info = '%s %s' % (info,billing_info[0].address)
        return info'''
    

    def get_discount(self):
        return self.list_price_total - self.total
    
    def get_coupon_discount(self):
        discount = Decimal(0)
        if self.coupon_discount:
            discount = self.coupon_discount
        if self.auto_promotions_discount:
            discount += self.auto_promotions_discount
        return discount

    def get_item_count(self):
        total = 0
        for item in self.get_order_items(None, exclude=dict(state__in=['cancelled',
            'bundle_item'])):
            total += 1;
        return total

    def get_offerprice_total(self):
        return self.total
        #if self._offerprice_total_cache:
        #    return self._offerprice_total_cache
        #total = Decimal(0)
        #for item in self.get_items_for_billing(None):
        #    total += item.sale_price
        #self._offerprice_total_cache = total
        #return total
    
    #do not add request argument to this function. called from template

    def formatted_currency(self):
        return 'Rs.'

    def get_address(self, request, **kwargs):
        type = kwargs.get('type', 'delivery') # delivery or billing

        # XXX This might throw multiple objects returned exception.
        # XXX We should catch it and pick the latest one. Modifying code
        # XXX please check and review
        if type == 'delivery':
            info = DeliveryInfo.objects.select_related(
                'address','address__state','address__country','address__city'
                ).filter(order=self).order_by('-id')[:1]
        elif type == 'billing':
            info = BillingInfo.objects.select_related(
                'address','address__state','address__country','address__city'
                ).filter(order=self).order_by('-id')[:1]
        if info:
            return info[0]
        else:
            if type == 'billing': raise BillingInfo.DoesNotExist
            if type == 'delivery': raise DeliveryInfo.DoesNotExist

    def get_objects(self, request, qs, **kwargs):
        sr = kwargs.get('select_related', ())     #tuple containing select_related arguments
        fl_args = kwargs.get('filter_args', ())   #tuple for filter arguments (Q objects)
        fl = kwargs.get('filter', {})             #dictionary containing filter arguments
        ex_args = kwargs.get('exclude_args', ())  #tuple for exclude arguments (Q objects)
        ex = kwargs.get('exclude', {})            #dictionary containing exclude arguments
        if sr:
            qs = qs.select_related(*sr)
        if fl or fl_args:
            qs = qs.filter(*fl_args, **fl)
        if ex or ex_args:
            qs = qs.exclude(*ex_args, **ex)
        return qs
    
    def get_payments(self, request, **kwargs):
        qs = self.paymentattempt_set.all()
        return self.get_objects(request, qs, **kwargs)

    def get_shipments(self, request, **kwargs):
        qs = self.shipments.all()
        return self.get_objects(request, qs, **kwargs)

    def get_refunds(self, request, **kwargs):
        qs = self.refunds.all()
        return self.get_objects(request, qs, **kwargs)

    def get_delivery_city(self):
        di = self.get_address(None, type='delivery')
        if di:
            if di.address:
                if di.address.city:
                    return di.address.city.name
        return ''
    def get_delivery_state(self):
        di = self.get_address(None, type='delivery')
        if di:
            if di.address:
                if di.address.state:
                    return di.address.state.name
        return ''
    
    def get_delivery_address(self):
        di = self.get_address(None, type='delivery')
        if di:
            if di.address:
                address = ''
                if di.address.first_name:
                    address = di.address.first_name + ' '
                if di.address.last_name:
                    address += di.address.last_name + ', '
                if di.address.address:
                    address += di.address.address +', '
                if di.address.city:
                    address += di.address.city.name +', '
                if di.address.state:
                    address += di.address.state.name +', '
                if di.address.country:
                    address += di.address.country.name +' - '
                if di.address.pincode:
                    address += di.address.pincode
                return address
        return ''

    def get_delivery_country(self):
        di = self.get_address(None, type='delivery')
        if di:
            if di.address:
                if di.address.country:
                    return di.address.country.name
        return ''

    def create_payment_attempt(self, request, **kwargs):
        domain = kwargs.get('domain')
        payment_mode = kwargs.get('payment_mode_code')
        emi_plan = kwargs.get('emi_plan')
        amount = kwargs.get('amount', Decimal(0))
        pa = None
        if (payment_mode in utils.DEFERRED_PAYMENT_MODES) or \
            (payment_mode == 'cod'):
            pas = self.get_payments(request, filter=dict(payment_mode=payment_mode),
                exclude=dict(status__in=['rejected','paid'])).order_by('-id')[:1]
            if pas:
                pa = pas[0]
        if not pa:
            pa = PaymentAttempt()
        pa.status = 'unpaid'
        if (payment_mode in ['atom','paymate']) or \
            (payment_mode not in utils.DEFERRED_PAYMENT_MODES):
            pa.amount = self.payable_amount
        else:
            #Amount will be verified through support in this case
            pa.amount = Decimal('0')
        pa.order = self
        pa.action = 'fulfil'
        pa.payment_mode = payment_mode
        pa.create_transaction_id(request, order_id=self.get_id())
        pa.emi_plan = emi_plan

        if utils.is_wholii_client(request.client.client) or \
            utils.is_usholii_client:
            try:
                pl = DomainLevelPriceList.objects.get(domain=domain)
                exchange_rate = pl.price_list.exchange_rate
                if exchange_rate:
                    pa.amount =  Decimal(pa.amount * exchange_rate).quantize(Decimal('1.'),
                        rounding=ROUND_UP)
            except:
                pass
        pa.save()
        return pa

    def change_payment_mode(self, request, **kwargs):
        payment_mode = kwargs.get('payment_mode')
        gateway = kwargs.get('gateway')
        amount = kwargs.get('amount')
        profile = kwargs.get('profile')
        reject = kwargs.get('reject', False)    #to reject other un-paid payment attempts
        bank = kwargs.get('bank')
        
        if self.support_state != 'booked':
            raise self.InvalidOperation
        if not payment_mode:
            raise self.PaymentModeNotPresent
        if not amount:
            raise self.PaymentAmountNotPresent
        
        o_log = OrderLog.objects.create(order=self, action='payment', profile=profile,
            payment_mode_old=self.payment_mode, payment_mode_new=payment_mode)
        if reject:
            old_payments = self.get_payments(request, filter=dict(
                status__in=['unpaid','info received','pending realization']))
            for payment in old_payments:
                PaymentLog.objects.create(payment=payment, order_log=o_log, status='rejected',
                    notes='Payment mode changed')
            old_payments.update(status='rejected', notes='Payment mode change')
        pa = PaymentAttempt(order=self, amount=amount, payment_mode=payment_mode,
            status='unpaid', action='fulfil')
        pa.create_transaction_id(request, order_id=self.get_id())
        if payment_mode == 'cod':
            pa.status = 'in verification'
        elif payment_mode == 'atom':
            pa.gateway = 'ATOM'
            pa.bank = bank
        elif payment_mode == 'paymate':
            pa.gateway = 'PAYM'
            pa.bank = bank
        elif payment_mode == 'cash-collection':
            pa.gateway = gateway
        pa.save()
        self.payment_mode = payment_mode
        self.save()
        PaymentLog.objects.create(payment=pa, order_log=o_log, status=pa.status, amount=amount)

    
    #not required - prady
    def apply_discount(self,percentage,request,total):
        discount_applicable = (self.top10_discount + total) * percentage/100
        self.apply_order_discount(request,discount_applicable)

    #use this function from a template only. for all other purposes use get_order_items - prady
    def get_items_for_billing(self, *args):
        return self.get_order_items(None, select_related=('seller_rate_chart',),
            exclude=dict(state__in=['cancelled','bundle_item']))
    
    #required - use this to update item info from seller rate chart - prady
    def update_billing_from_src(self,request, **kwargs):
        if self.support_state:
            return      #should update only for cart
        order_items = self.get_order_items(request, select_related=('seller_rate_chart',
            'seller_rate_chart__product','bundle_item'), exclude=dict(state='cancelled'))
        for item in order_items:
            if item.state != 'bundle_item':
                item.update_info_from_src(request, order_items=order_items)
        self.update_billing(request, **kwargs)
   

    #required - prady
    def update_billing(self, request, **kwargs):
        # Coupon Codes - Only Required in Cart Action
        coupon_code = kwargs.get('coupon_code')
        sender = kwargs.get('sender')
        
        list_price_total = Decimal(0)   #MRP sum
        sale_price_total = Decimal(0)   #offer(sale) price sum
        cashback_amount_total = Decimal(0)
        shipping_charges_total = Decimal(0)
        #item_discount_total = Decimal(0)
        taxes = Decimal(0)
        transaction_charges = Decimal(0)
        payable_amount = Decimal(0)         #actual payable amount (amount sent to payment gateway)

        order_items = self.get_order_items(request, exclude=dict(state__in=['cancelled',
            'bundle_item']))
        for item in order_items:
            list_price_total += item.list_price
            sale_price_total += item.sale_price
            #shipping_charges_total += item.shipping_charges
            #item_discount_total += item.discount   #Do not uncomment this - prady
            if item.cashback_amount:
                cashback_amount_total += item.cashback_amount
        
        self.list_price_total = list_price_total
        self.total = sale_price_total
        self.cashback_amount_total = cashback_amount_total
        #shipping_charges_total = shipping_charges_total.quantize(Decimal('1'),
        #    rounding=ROUND_HALF_UP).quantize(Decimal('0.01'))
        self.payable_amount = self.total - self.cashback_amount_total   #shipping charge will be added later
        
        '''
        For *.futurebazaar.com, if order amount < 500, add shipping charges of Rs.50/-
        '''
        #This is needed. What is the logic if item gets cancelled.
        # How do we cancel shipping charges - Anubhav
        additional_shipping_charges = Decimal('0')
        if utils.is_futurebazaar_client(self.client):
            if (self.payable_amount < Decimal('500')) and (shipping_charges_total == Decimal('0')) and order_items:
                additional_shipping_charges = Decimal('50')

        shipping_charges_total += additional_shipping_charges
        self.shipping_charges = shipping_charges_total
        self.payable_amount += self.shipping_charges
        
        # Store as Integer
        self.payable_amount = Decimal(str(round(self.payable_amount)))
        self.coupon_discount = Decimal(str(round(self.coupon_discount)))
        
        self.save()
        self.split_values_across_items(request)
        return response

    def split_values_across_items(self, request, **kwargs):
        order_items = self.get_order_items(request, exclude=dict(state='bundle'))
        if self.support_state in ['booked','paid','cancelled']:
            unlocked_items = [oi.id for oi in order_items if (oi.state != 'cancelled')]
        else:
            unlocked_items = self.get_unlocked_items(request)
        total_discount = self.coupon_discount
        order_total = self.total
        total_shipping = self.shipping_charges
        rem_items = 0
        
        for oi in order_items:
            if oi.state == 'cancelled':
                continue
            if oi.id in unlocked_items:
                rem_items += 1
            else:
                total_discount -= oi.discount
                total_shipping -= oi.shipping_charges
                order_total -= oi.sale_price
        
        if total_discount < 0:
            total_discount = Decimal('0')
        rem_discount = total_discount
        rem_shipping = total_shipping
        for oi in order_items:
            if oi.state == 'cancelled':
                oi.discount = Decimal('0')
                oi.shipping_charges = Decimal('0')
            elif oi.id in unlocked_items:
                if rem_items == 1:
                    oi.discount = rem_discount
                    oi.shipping_charges = rem_shipping
                elif rem_items > 1:
                    oi.discount = ((oi.sale_price/order_total)*total_discount).quantize(
                        Decimal('1'), rounding=ROUND_HALF_UP).quantize(Decimal('0.01'))
                    oi.shipping_charges = (rem_shipping/rem_items).quantize(Decimal('1'),
                        rounding=ROUND_HALF_UP).quantize(Decimal('0.01'))
                oi.discount = min(oi.sale_price - oi.cashback_amount, oi.discount)
                rem_discount -= oi.discount
                rem_shipping -= oi.shipping_charges
                rem_items -= 1
            oi.total_amount = oi.sale_price - oi.cashback_amount + oi.shipping_charges - oi.discount
            oi.save()
    
    
    def remove_coupon(self, request, **kwargs):
        coupon_code = kwargs.get('coupon_code')
        # from update billing validate promotion gets called
        return self.update_billing(request, coupon_code=coupon_code, sender='remove_coupon')
    
    #Not Required - Anubhav
    def remove_or_preserve_coupon(self, request, **kwargs):
        sender = kwargs.get('sender', None)
        amount = None
        
        if self.coupon.applies_to == 'order_total':
            if self.coupon.discount_type == 'percentage':
                percentage = self.coupon.discount_value
                discount_value = self.calculate_discount_value(self.payable_amount, self.coupon.discount_value)
                self.coupon_discount = discount_value

        if self.coupon.applies_to == 'product_offer_price':
                if self.coupon.discount_type == 'percentage':
                    percentage = self.coupon.discount_value
                    discount_value = self.calculate_discount_value(oi.payable_amount_without_discount(),self.coupon.discount_value)
                    self.coupon_discount = discount_value
                elif self.coupon.discount_type == 'fixed':
                    self.coupon_discount = self.coupon.discount_value
            
            #if self.coupon.applies_to == 'product_offer_price':
            #    if sender == 'remove_item':
            #        self.coupon = None
            #        self.coupon_discount = Decimal(0)
            #        return self
            #    if sender in ['add_item','update_item']:
            #        if self.coupon.discount_type == 'percentage':
            #            percentage = self.coupon.discount_value
            #            discount_value = self.calculate_discount_value(oi.payable_amount_without_discount(),self.coupon.discount_value)
            #            self.coupon_discount = discount_value
            #        else:
            #            self.coupon_discount = self.coupon.discount_value * oi.qty

        self.save()
    
    #required - prady
    def remove_item(self,request, **kwargs):
        '''Should be used only for cart'''
        if not self.support_state:
            item_id = kwargs.get('item_id', None)
            try:
                oi = self.get_order_items(request).get(pk=item_id)
                if oi.state == 'bundle_item':
                    exp = self.BundleArticle
                    exp.child=oi.seller_rate_chart
                    raise exp
                if oi.state == 'bundle':
                    bundle_items = self.get_order_items(request,
                        filter=dict(bundle_item__parent_item=oi,
                        state='bundle_item'))
                    bundle_items.delete()
                log.info('Deleting order item %s of %s' % (oi.id, self.id))
                oi.delete()
                self.update_billing(request)
            except OrderItem.DoesNotExist:
                pass
        else:
            raise self.InvalidOperation
        
    #required - prady
    def update_item_quantity(self, request, **kwargs):
        item_id = kwargs.get('item_id', None)
        item_qty = kwargs.get('qty', None)
        profile = kwargs.get('profile', None)
        if item_qty:
            qty = int(item_qty)
            if qty == 0 and (not self.support_state):
                self.remove_item(request, item_id=item_id)
            else:
                order_items = self.get_order_items(request, select_related=('seller_rate_chart',
                    'bundle_item'), exclude=dict(state='cancelled'))
                oi = order_items.get(pk=item_id)
                oi.update_quantity(request, qty=qty, profile=profile, order_items=order_items)
                self.update_billing(request)
        else:
            raise self.ItemQuantityNone

    #required
    def add_item(self, request, **kwargs):
        rate_chart = kwargs.get('rate_chart')
        qty = int(kwargs.get('qty', 0))
        price_list = kwargs.get('price_list')
        is_bulk = kwargs.get('is_bulk',False)
        order_items = self.get_order_items(request, exclude=dict(state='cancelled'),
            select_related=('bundle_item',))
        if not qty or qty == 0:
            raise self.ItemQuantityZero
        oi = None
        for item in order_items:
            if item.seller_rate_chart_id == rate_chart.id:
                oi = item
                if oi.state == 'bundle_item':
                    exp = self.BundleArticle
                    exp.parent=oi.bundle_item.parent_item.seller_rate_chart
                    exp.child=rate_chart
                    raise exp
                break
        if not oi:
            oi = OrderItem()
            oi.qty = 0
        
        oi.qty += qty
        
        
        oi.order = self
        oi.seller_rate_chart = rate_chart
        oi.item_title = rate_chart.product.title
        oi.gift_title = rate_chart.gift_title
        
        if not rate_chart.is_available_for_sale(request, qty=oi.qty) and\
            not request.client.client == utils.get_chaupaati_marketplace():
            if oi.qty > 1:
                return 'Article %s with %s quantities is no longer available for sale. ' \
                        'Please update the quantity or remove the item.' \
                        % (oi.item_title, oi.qty)
            else:
                return 'Article %s is currently out of stock.'  \
                        % oi.item_title
        elif oi.qty > 12 and not is_bulk:
            return 'More than 12 quantities are not purchaseable for article %s' \
                    % oi.item_title
        
        priceInfo = None
        if price_list:
            priceInfo = rate_chart.getPriceByPriceList(request, price_list)
        
        if not priceInfo:
            priceInfo = rate_chart.getPriceInfo(request)
        
        list_price = priceInfo['list_price']
        offer_price = priceInfo['offer_price']
        cashback_amount = priceInfo['cashback_amount']
        
        oi.list_price = list_price * oi.qty
        oi.sale_price = offer_price * oi.qty
        #oi.shipping_charges = rate_chart.shipping_charges * oi.qty
        oi.cashback_amount = cashback_amount * oi.qty if cashback_amount else Decimal('0')
        oi.total_amount = oi.sale_price - oi.cashback_amount  #added by prady

        if oi.seller_rate_chart.is_bundle:
            oi.state = 'bundle'
            oi.save()
            oi.update_bundle_items(request, order_items=order_items)
        else:
            oi.save() 
        utils.track_add_to_cart_usage(request, rate_chart.product)
        self.update_billing(request)
    
    #required - prady 
    def validate_items(self, request):
        ''' Validates the items of the cart. Checks if
            - Product is saleable (out of stock etc.)
            - Bundle is active
            - Bundle has not been modified
        '''

        order_items = self.get_order_items(request,
            select_related=('seller_rate_chart',),
            exclude=dict(state__in=['cancelled','bundle_item']))
        errors = []
        if utils.get_chaupaati_marketplace() != request.client.client:
            for item in order_items:
                if not item.seller_rate_chart.is_available_for_sale(request, qty=item.qty):
                    errors.append('%s is out of stock. \
                    Please remove this item from your cart' % item.item_title)
                elif item.state == 'bundle':
                    if not item.seller_rate_chart.is_bundle:
                        errors.append('The offer on %s has expired  \
                        Please refer the product details page for more \
                        details ' % item.item_title)
                    elif not item.validate_bundle_items(request):
                        errors.append('We have changed the offer on %s. \
                        Please refer the product details page for more \
                        details ' % item.item_title)
        
        if utils.is_franchise(request):
            if order_items:
                from web.views.franchise_views import calculate_commission_value_for_product
                if order_items.count() != 0 and order_items.count() > 1:
                    errors.append('You cannot purchase more than one product at a time')
                else:
                    for item in order_items:
                        commission_dict = calculate_commission_value_for_product(request, item)
                        if 'error' in  commission_dict:
                            errors.append('"%s" is not available for sale.' %item.item_title)
                            break
        return errors

    def clone(self, support_state=None):
        cloned = Order()

        cloned.client = self.client
        cloned.user = self.user
        cloned.state = ''
        cloned.support_state = support_state
        cloned.list_price_total = self.list_price_total
        cloned.total = self.total
        cloned.cashback_amount_total = self.cashback_amount_total
        cloned.shipping_charges = self.shipping_charges
        cloned.taxes = self.taxes
        cloned.transaction_charges = self.transaction_charges
        cloned.coupon_discount = self.coupon_discount
        cloned.auto_promotions_discount = self.auto_promotions_discount
        cloned.payable_amount = self.payable_amount
        cloned.top10_discount = self.top10_discount
        cloned.coupon = self.coupon
        cloned.payment_mode = self.payment_mode
        #cloned.payment_realized_mode = self.payment_realized_mode - field not used
        #cloned.booking_agent = self.booking_agent if self.booking_agent else self.agent - data not present here
        #cloned.agent = self.agent - field not used
        #cloned.medium = self.medium
        cloned.call_id = self.call_id
        cloned.payback_id = self.payback_id
        #cloned.payment_realized_on = self.payment_realized_on - data not be present here
        cloned.save()

        order_items = self.get_order_items(None, select_related=('bundle_item',)).order_by('id')
        cloned_items = []
        for oi in order_items:
            parent = None
            if oi.state == 'bundle_item':
                if not (parent and \
                    oi.bundle_item.parent_item.seller_rate_chart_id == parent.seller_rate_chart_id):
                    for ci in cloned_items:
                        if ci.seller_rate_chart_id == oi.bundle_item.parent_item.seller_rate_chart_id:
                            parent = ci
                            break
            cloned_oi = oi.clone(order=cloned, parent=parent)
            cloned_items.append(cloned_oi)
            if cloned.support_state == 'booked' and oi.state != 'bundle_item':
                cloned_oi.seller_rate_chart.product.pending_order_count += 1
                cloned_oi.seller_rate_chart.product.save()
            cloned_oi.clone_item_relationships()
        return cloned

    def sync_non_item_info(self, request, **kwargs):
        di = None
        order = kwargs.get('order')
        di = order.get_address(request, type='delivery')
        this_di = None
        try:
            this_di = self.get_address(request, type='delivery')
        except Exception, e:
            this_di = DeliveryInfo(order=self)
         
        if this_di and di:
            if not this_di.address_id:
                address = Address() #VERY IMPORTANT, need new foreign key object
                address.type = 'delivery'
            else:
                address = this_di.address
            this_di.notes = di.notes
            this_di.gift_notes = di.gift_notes
            if di.address:
                address.first_name = di.address.first_name
                address.last_name = di.address.last_name
                address.address = di.address.address
                address.city = di.address.city
                address.state = di.address.state
                address.country = di.address.country
                address.pincode = di.address.pincode
                #address.name = di.address.name
                address.phone = di.address.phone
                address.email = di.address.email
                address.save()
                this_di.address = address
            this_di.save()

    def is_same_order(self, order):
        if self.user.id != order.user.id:
            return False
        if self.list_price_total != order.list_price_total:
            return False
        if self.total != order.total:
            return False
        if self.shipping_charges != order.shipping_charges:
            return False
        if self.transaction_charges != order.transaction_charges:
            return False
        if self.coupon_discount != order.coupon_discount:
            return False
        if self.auto_promotions_discount != order.auto_promotions_discount:
            return False
        if self.top10_discount != order.top10_discount:
            return False
        if self.payable_amount != order.payable_amount:
            return False
        if self.client != order.client:
            return False

        current_items = self.get_order_items(None,
            exclude=dict(state='cancelled'))
        order_items = order.get_order_items(None,
            exclude=dict(state='cancelled'))
        current_items_hash = {}
        order_items_hash = {}
        for oi in current_items:
            current_items_hash[oi.seller_rate_chart_id] = oi
        for oi in order_items:
            order_items_hash[oi.seller_rate_chart_id] = oi

        # these two orders dont have exactly the same order items
        if set(current_items_hash.keys()) - set(order_items_hash.keys()):
            return False

        for rc_id in current_items_hash.keys():
            if current_items_hash[rc_id].qty != order_items_hash[rc_id].qty:
                # the items quantity varies
                return False

        return True
   
    #Required - Anubhav
    def get_payment_options(self, request, **kwargs):
        client = self.client
        client_domain = kwargs.get('client_domain', None)
        cod_applicable = True
        fmemi_applicable = True
        cc_emi_applicable = False
        is_offline = False

        if client_domain.type != 'website':
            is_offline = True
       
        order_items = self.get_order_items(request, select_related=('seller_rate_chart',),
            exclude=dict(state__in=['cancelled','bundle_item']))
        
        for item in order_items:
            src = item.seller_rate_chart
            cod_applicable = cod_applicable and src.is_cod_available
            fmemi_applicable = fmemi_applicable and src.is_fmemi_available
        
        if cod_applicable and self.payable_amount > Decimal('18000'):
            cod_applicable = False

        if self.payable_amount > self.client.emi_amount: #(Depends on Client)
            cc_emi_applicable = True

        payment_options = self.get_eligible_payment_options(request, cod_applicable=cod_applicable,
                fmemi_applicable=fmemi_applicable, cc_emi_applicable=cc_emi_applicable, 
                is_online=True, client_domain=client_domain, is_offline=is_offline)

        return payment_options

    #Required - Anubhav
    def get_eligible_payment_options(self, request, **kwargs):
        is_online = kwargs.get('is_online', True) #by default web modes
        is_offline = kwargs.get('is_offline', False) #By default dont show offline payment modes
        cod_applicable = kwargs.get('cod_applicable', False)
        fmemi_applicable = kwargs.get('fmemi_applicable', False)
        cc_emi_applicable = kwargs.get('cc_emi_applicable', False)
        client_domain = kwargs.get('client_domain', None)
        
        from accounts.models import DomainPaymentOptions
        payback_coupon = getattr(settings, 'PAYBACK_COUPON_CODE', 'PAYBACK')
        payment_options = []
            
        if self.coupon and self.coupon.code.upper() == payback_coupon:
            dpo = DomainPaymentOptions.objects.select_related('payment_option', 
                    'payment_option__payment_mode').get(client_domain__domain=client_domain, 
                            payment_option__payment_mode__code='payback')
            
            payment_options.append(dpo.payment_option)
            return payment_options
       
        #Dynamic Payment Modes Check:
        dpm_modes = []
        if cc_emi_applicable:
            dpm_modes.append('credit-card-emi-web')
            dpm_modes.append('credit-card-emi-ivr')
        
        if fmemi_applicable:
            dpm_modes.append('fmemi')

        if cod_applicable:
            dpm_modes.append('cod')

        
        default_q = Q(client_domain__domain = client_domain, is_active=True, 
                is_dynamic_pm_active=False, payment_option__is_active=True)
        

        dpm_q =  Q(client_domain__domain = client_domain, is_active=True, 
                is_dynamic_pm_active=True, payment_option__is_active=True, 
                payment_option__payment_mode__code__in=dpm_modes)
        
        dpo = DomainPaymentOptions.objects.select_related('payment_option', 
            'payment_option__payment_mode').filter(dpm_q | default_q).order_by('payment_option__sort_order')
        
        for option in dpo:
            payment_options.append(option.payment_option)
    
        return payment_options
    
    #required - prady
    def all_items_invoiced(self, request):
        order_items = self.get_order_items(request, exclude=dict(state__in=['cancelled','bundle']))
        for item in order_items:
            if not item.is_invoiced(request):
                return False
        return True
    
    #required - prady
    def all_items_shipped(self, request):
        order_items = self.get_order_items(request, exclude=dict(state__in=['cancelled','bundle']))
        for item in order_items:
            if not item.is_shipped(request):
                return False
        return True
    
    #required - prady
    def all_items_delivered(self, request):
        order_items = self.get_order_items(request, exclude=dict(state__in=['cancelled','bundle']))
        for item in order_items:
            if not item.is_delivered(request):
                return False
        return True
    
    #required - prady
    def all_items_undeliverable(self, request):
        order_items = self.get_order_items(request, exclude=dict(state__in=['cancelled','bundle']))
        for item in order_items:
            if not item.is_undeliverable(request):
                return False
        return True
    
    #required - prady
    def all_items_returned(self, request):
        order_items = self.get_order_items(request, exclude=dict(state__in=['cancelled','bundle']))
        for item in order_items:
            if not item.is_returned(request):
                return False
        return True
    
    #required - prady
    def is_payment_done(self, request, *args, **kwargs):
        total = self.get_payments(request, filter=dict(status='paid')).aggregate(amount=Sum('amount'))
        if total['amount'] == self.payable_amount:
            return True, 0
        elif total['amount'] > self.payable_amount:
            return True, (total['amount'] - self.payable_amount)
        else:
            return False, ((self.payable_amount - total['amount']) if total['amount'] else self.payable_amount)


    #required - prady
    def is_confirm_allowed(self, request, *args, **kwargs):
        if self.payment_mode.lower() != 'cod':
            total = self.get_payments(request, filter=dict(status='paid'),
                exclude=dict(payment_mode='cod')).aggregate(amount=Sum('amount'))
        else:
            total = self.get_payments(request, filter=dict(payment_mode='cod',
                status__in=['pending realization','paid'])).aggregate(amount=Sum('amount'))
        if total['amount'] == self.payable_amount:
            return True, 0
        elif total['amount'] > self.payable_amount:
            return True, (total['amount'] - self.payable_amount)
        else:
            return False, ((self.payable_amount - total['amount']) if total['amount'] else self.payable_amount)


    def confirm(self, request, *args, **kwargs):
        today = datetime.now()
        confirming_user = kwargs.get('profile', None)   #for orders confirmed by agents
        payment_mode = kwargs.get('payment_mode', None)
        payment_date = kwargs.get('payment_date', today)
        o_log = kwargs.get('order_log')
         
        if self.support_state not in ['booked','paid']:
            raise self.InvalidOperation
        payment_done, delta = self.is_confirm_allowed(request)
        if not payment_done:
            e = self.InsufficientPayment
            e.delta = delta
            raise e
        
        if payment_mode == 'cod':
            response = self.update_billing(request, sender='check_promotion')
            if response == 'INVALID_COUPON':
                raise self.InsufficientPayment


        user = self.user
        client_flag = False
        if request:
            if utils.is_future_ecom(self.client):
                client_flag = True
        medium_flag = False
        if self.medium == 'web':
            medium_flag = True
        dailydeal = None
        try:
            dailydeal = DailyDeal.objects.get(starts_on__lte = today,ends_on__gte = today)
        except:
            log.info("dailydeal does_notexist for date %s" % repr(today))
        
        order_items = self.get_order_items(request, select_related=('seller_rate_chart__product',),
            exclude=dict(state='cancelled'))
        sap_sno = 10
        for oi in order_items:
            if oi.state != 'bundle':
                oi.seller_rate_chart.product.confirmed_order_count += 1
                oi.seller_rate_chart.product.save()
                oi.save()
                if not oi.expected_stock_arrival:
                    if not oi.expected_delivery_date:
                        status = 'no stock'
                    else:
                        status = 'awaiting delivery creation'
                else:
                    status = 'stock expected'
                dc, lsp, physical_stock = oi.get_resolved_dc_lsp()
                SAPOrderItem.objects.create(order=self, order_item=oi, sno=sap_sno, status=status, dc=dc, lsp=lsp,
                    revised_stock_arrival=oi.expected_stock_arrival) #inserting into SAP orderitem table
                sap_sno += 10
                OrderItemLog.objects.create(order_item=oi, order_log=o_log, action='status',
                    status = status, expected_stock_arrival=oi.expected_stock_arrival,
                    expected_delivery_date=oi.expected_delivery_date)
            if oi.state != 'bundle_item':
                if client_flag and medium_flag:
                    astream = write_to_as(user, request.client, 'Buy', oi.seller_rate_chart)
                if dailydeal:
                    if oi.seller_rate_chart and oi.seller_rate_chart == dailydeal.rate_chart:
                        dailydeal.n_orders += oi.qty 
                        dailydeal.save()
                utils.track_product_booked_usage(request, oi.seller_rate_chart.product) #track product booked usage
        
        self.support_state = 'confirmed'
        
        if payment_mode:
            self.payment_mode = payment_mode
        self.payment_realized_on = payment_date
        self.confirming_timestamp = today
        self.confirming_agent = confirming_user
        
        #order_items = order_items.exclude(state='bundle_item')
        self.set_max_days_for_delivery(request, order_items=order_items)
        self.save()
        
        #Save User Address to Address Book
        try:
            info_obj = self.get_address(request, type='delivery')
            address = info_obj.address
            self.user.add_address(request, address=address) 
        except Exception, e:
            log.exception("Unable to save user address to addressbook")
        
        # raise an order confirmed signal
        try:
            confirmed_order_signal.send(self, order=self)
            log.info('Raised confirmed order signal')
        except Exception, e:
            log.exception('Error raising confirmed order signal for %s - %s' %
                (self.id, repr(e)))
        try:
            self.notify_confirmed_order(request)
        except Exception, e:
            log.exception('Error notifying for confirmation for %s - %s' %
                (self.id,repr(e)))
        
        #Open refund if excess payment is made
        if delta and self.payment_mode != 'cod':
            self.openRefund(request, profile=confirming_user, amount=delta, notes='Excess payment',
                order_log=o_log)
        
        if self.payback_id and self.payment_mode != 'cod':
            points_header = PointsHeader(order=self)
            points_header.earn_points(request)
            o_log.earn_points = self.get_payback_earn_points()

        o_log.status = 'confirmed'
        o_log.save()
        
        items_with_physical_stock = self.get_items_with_physical_stock(request)
        if utils.is_future_ecom(self.client) and items_with_physical_stock:
            #create xml for items whose booking is done against physical stock 
            self.create_xml(request, type='new', items=items_with_physical_stock)
        return

    #required - prady
    def is_delivery_created(self, request, **kwargs):
        if self.shipments.exclude(status='deleted').count():
            return True
        return False
    
    #return line item ids on which modification is not allowed - prady
    #this function gives the id of bundle product and not the respective bundle items
    def get_locked_items(self, request, **kwargs):
        shipment_items = ShipmentItem.objects.filter(order_item__order=self).exclude(
            shipment__status='deleted').select_related('order_item__bundle_item')
        items = []
        for s_item in shipment_items:
            item_id = None
            if s_item.order_item.state == 'bundle_item':
                item_id = s_item.order_item.bundle_item.parent_item_id
            else:
                item_id = s_item.order_item_id
            if item_id not in items:
                items.append(item_id)
        return items
    
    #return line items on which discount can be split - prady
    #this function gives the id of bundle item and not the bundle product
    def get_unlocked_items(self, request, **kwargs):
        order_items = self.get_order_items(request, exclude=dict(
            state__in=['bundle','cancelled']))
        locked_items = self.get_locked_items(request)
        unlocked_items = []
        for oi in order_items:
            if oi.state == 'bundle_item':
                if not oi.shipment_items.exclude(
                    shipment__status='deleted').count():
                    unlocked_items.append(oi.id)
            elif oi.id not in locked_items:
                unlocked_items.append(oi.id)
        return unlocked_items
    
    #required - prady
    def is_cancelled(self, request, **kwargs):
        if self.state == 'cancelled' or self.support_state == 'cancelled':
            return True
        return False

    #required - prady
    def update_billing_address(self, request, **kwargs):
        profile = kwargs.get('profile', None)
        self.save_address(request, type='billing', **kwargs)
        return
    
    #required - prady
    def update_shipping_address(self, request, **kwargs): 
        profile = kwargs.get('profile', None)
        #TODO IFS Deliverability check
        return self.save_address(request, type='delivery', **kwargs)
    
    #required - anubhav
    def set_max_days_for_delivery(self, request, **kwargs):
        order_items = kwargs.get('order_items')
        timestamp = []
        is_cod = 0
        if self.support_state == 'booked':
            if self.payment_mode == 'cod':
                is_cod = 1
            from orders.check_availability import check_availability_new
            pincode = self.get_address(request, type="delivery").address.pincode
            for item in order_items:
                rate_chart = item.seller_rate_chart
                #json = check_availability_new(rate_chart.article_id, rate_chart.id, pincode, item.qty,
                #            self.client.id, is_cod, int(item.sale_price))
                #timestamp.append(json.get('items')[0].get('totalDeliveryTime', 7))
                timestamp.append(7)
        else:
            for item in order_items:
                if item.state == 'bundle':
                    continue
                if item.expected_delivery_date:
                    if self.confirming_timestamp:
                        diff = item.expected_delivery_date - self.confirming_timestamp
                        timestamp.append(diff.days)
                    else:
                        diff = item.expected_delivery_date - self.payment_realized_on
                        timestamp.append(diff.days)
                else:
                    log.error("Expected delivery date not set for %s %s" % (
                        self.id, item.id))
                    timestamp.append(10)

        max_days = max(timestamp)
        for item in order_items:
            item.delivery_days = max_days
            item.save()

        #loop and get max
    #required - anubhav, prady
    def save_address(self, request, **kwargs):
        '''save Address (delivery/billing) and add to addressBook if not exists
        '''
        profile = kwargs.get('profile')
        if (self.sap_date and self.state == 'failed') or \
            self.state == 'processing xml':
            raise self.OrderInProcessing
        
        type = kwargs.get('type', 'delivery')               #delivery/billing
        address_details = kwargs.get('%s_address'%type)     #dictionary
        create_log = kwargs.get('create_log',False)
        
        o_log = None 
        if create_log:
            o_log = OrderLog(order=self, profile=profile, action='modify')
        
        address_old = '' 
        if address_details:
            email = address_details.get('%s_email'%type, None)
            phone = address_details.get('%s_phone'%type, None)
            try:
                info_obj = self.get_address(request, type=type)
                address = info_obj.address
                if type == 'delivery':
                    address_old = info_obj.get_printable_address()
            except DeliveryInfo.DoesNotExist:
                info_obj = DeliveryInfo()
                address = Address()
            except BillingInfo.DoesNotExist:
                info_obj = BillingInfo()
                address = Address()
            address.address = address_details.get('%s_address'%type, None)
            address.pincode = address_details.get('%s_pincode'%type, None)

            country_name = address_details.get('%s_country'%type, None)
            country = utils.get_or_create_country(country_name, True)

            state_name = address_details.get('%s_state'%type, None)
            state = utils.get_or_create_state(state_name, country, True)

            city_name = address_details.get('%s_city'%type, None)
            city = utils.get_or_create_city(city_name, state, True)

            address.city = city
            address.state = state
            address.country = country
            address.type = type
            address.first_name = address_details.get('%s_first_name'%type, None)
            address.last_name = address_details.get('%s_last_name'%type, None)
            address.phone = phone
            address.email = email
            address.save()
            info_obj.address = address
            if type == 'delivery':
                info_obj.notes = address_details.get('%s_notes'%type, None)
                info_obj.gift_notes = address_details.get('%s_gift_notes'%type, None)
            info_obj.order = self
            info_obj.save()
            if type == 'delivery':
                address_new = info_obj.get_printable_address()
                if o_log:
                    o_log.address_old = address_old
                    o_log.address_new = address_new
                    o_log.save()
        return o_log


    #required - prady
    def cancel(self, request, **kwargs):
        if self.support_state in ['cancelled','shipped','delivered']:
            raise self.InvalidOperation
        
        if self.is_delivery_created(request):
            raise self.DeliveryExists
        
        if self.state in ['failed','processing xml']:
            raise self.OrderInProcessing
        
        earn_reversal = True
        if self.support_state in ['booked','paid']:
            earn_reversal = False
         
        profile = kwargs.get('profile')
        reason = kwargs.get('reason')
        refundable = kwargs.get('refundable', True)
        out_of_stock = kwargs.get('out_of_stock', False)
        o_log = kwargs.get('order_log')

        if not o_log:
            o_log = OrderLog.objects.create(order=self, profile=profile, action='cancel')

        order_items = self.get_order_items(request, exclude=dict(state__in=['cancelled','bundle_item']),
            select_related=('sap_order_item',))
        refund_amount = Decimal('0')
        refund_items = []
        bundle_items = []
        for item in order_items:
            refund_items.append({'order_item':item, 'qty':item.qty, 'amount':item.payable_amount()})
            if item.state == 'bundle':
                deltas = item.cancel_bundle_items(request)
                bundle_items.extend(deltas)
            elif item.sap_order_item:
                item.sap_order_item.status = 'cancelled'
                item.sap_order_item.save()
            OrderItemLog.objects.create(order_item=item, order_log=o_log, action='status',
                status='cancelled')
            item.state = 'cancelled'
            item.save()
        if refund_items:
            refund_amount = self.payable_amount
        
        payment_done, d = self.is_payment_done(request)
        self.state = 'cancelled'
        self.support_state = 'cancelled'
        #open refund if payment is done
        if (self.support_state != 'booked') and refund_amount and refundable and payment_done:
            self.openRefund(request, profile=profile, refund_items=refund_items,
                amount=refund_amount, notes='Order cancellation', earn_reversal=earn_reversal,
                order_log=o_log)

        if refundable and (out_of_stock or self.support_state == 'booked'):
            #partial payment could be done.. refund that amount
            refund_amount = Decimal(0)
            if payment_done:
                refund_amount = self.payable_amount + d
            else:
                refund_amount = self.payable_amount - d
            if refund_amount:
                self.openRefund(request, profile=profile, refund_items=refund_items,
                    amount=refund_amount, notes='Order cancelled: Out of stock',
                    earn_reversal=False, order_log=o_log)
        
        if self.client_domain.type == 'franchise' and refund_items:
            self.update_commission(refund_items[0]['order_item'], refund_items[0]['qty'])
        
        refund_items.extend(bundle_items)
        
        #free up inventory
        #this function will fail silently if inventory is not allocated for this order
        if refund_items:
            self.update_inventory(request, action='add', delta=refund_items)
        
        #TODO add code to free up promotions used on this order - prady
        
        self.save()
        #Create cancel order xml for confirmed orders
        if utils.is_future_ecom(self.client):
            if self.is_xml_created(request):
                self.create_xml(request, type='cancel', reason=reason)
            if self.coupon:
                with transaction.commit_on_success():
                    self.update_promotion_params(request, type='cancel')
        
        CancelledOrder.objects.create(order=self, user=profile, refund_amount=refund_amount,
            notes=reason)

        o_log.status = 'cancelled'
        o_log.notes = reason
        if self.payback_id:
            o_log.earn_points = 0
        if self.payment_mode == 'payback':
            o_log.burn_points = 0
        o_log.save()

        cancelled_items = self.get_order_items(request, select_related=('seller_rate_chart',))
        self.notify_cancelled_order(request, cancelled_items,
            refund_amount=(refund_amount if payment_done else 0))
        return
    
    #not required - prady
    def add_order_history(self, request, **kwargs):
        profile = kwargs.get('profile',None)
        state = kwargs.get('state', None)
        OrderHistory.objects.create(order=self, payable_amount=self.payable_amount, shipping_charges=self.shipping_charges,
            updated_by=profile, state=state, coupon=self.coupon)
        return

    def confirm_to_seller(self):
        self.notify_confirmed_order_to_seller()

    def get_or_create_pending_order(self, request, **kwargs):
        client = kwargs.get('client', None)
        po_set = Order.objects.filter(user=self.user, support_state='booked', client=client).order_by('-timestamp')
        pending_order = None 
        created_new_po = False
        if po_set:
            po = po_set[0]
            payment_mode = po.payment_mode
            if (payment_mode not in utils.DEFERRED_PAYMENT_MODES) and \
                po.is_same_order(self) and (request.client.client.id == 1 or
                    utils.is_ezoneonline(request.client.client) or
                        utils.is_future_ecom(request.client.client)):
                pending_order = po
                pending_order.timestamp = datetime.now()
            else:
                pending_order = self.clone(support_state='booked')
                created_new_po = True
        else:
            pending_order = self.clone(support_state='booked')
            created_new_po = True

        if hasattr(request,'call'):
            pending_order.call_id = request.call['id']
            user_info= utils.get_user_info(request)
            #pending_order.agent = user_info['profile']

        if self.state == 'guest_cart':
            pending_order.medium = 'guest'
        elif self.state == 'temporary_cart':
            pending_order.medium = 'temporary'
        else:
            pending_order.medium = 'normal'
        pending_order.support_state = 'booked'
        if utils.is_future_ecom(request.client.client):
            pending_order.state = 'awaiting xml creation'
        pending_order.payback_id = self.payback_id
        pending_order.client_domain = request.client
        pending_order.save()

        call = getattr(request, 'call', {})
        if created_new_po and call:
            # raise signal for new pending order
            try:
                pending_order_signal.send(sender = self,
                    call = getattr(request, 'call', {}),
                    order = pending_order,
                    user = request.user)
                log.info('Raised po signal')
            except Exception, e:
                log.exception('Error raising po signal %s' % repr(e))
            # We will consider an order as booked if we create a new po
            po_order_items = pending_order.get_order_items(request,
                exclude=dict(state__in=['cancelled','bundle_item']),
                select_related=('seller_rate_chart__product',))
            for oi in po_order_items:
                utils.track_product_booked_usage(request,
                    oi.seller_rate_chart.product)

        # copy not item info (addresses, notes, etc. to pending order)
        pending_order.sync_non_item_info(request, order=self)
        return pending_order

    def notify_pending_order(self, request, groups = ['seller','buyer','admin']):
        if self.coupon:
            # Coupon has been applied on this order
            with transaction.commit_on_success():
                self.update_promotion_params(request, type='order_placed')
        if self.payment_mode != 'cash-at-store':
            from notifications.pendingordernotification import PendingOrderNotification
            notification_obj = PendingOrderNotification(self, request, **dict(groups=groups))
            notification_obj.send()
    
    def notify_pending_order_sms(self, groups = ['seller','buyer','admin']):
        from notifications.pendingordernotification import PendingOrderNotification
        notification_obj = PendingOrderNotification(self, **dict(groups=groups))
        notification_obj.sendSMS()

    def notify_confirmed_order(self, request, groups = ['seller','buyer','admin']):
        if self.payment_mode not in utils.DEFERRED_PAYMENT_MODES and self.coupon:
            # Coupon has been applied on this order
            with transaction.commit_on_success():
                self.update_promotion_params(request, type='order_placed')
        from notifications.confirmedordernotification import ConfirmedOrderNotification
        notification_obj = ConfirmedOrderNotification(self, request, **dict(groups=groups))
        notification_obj.send()

    def notify_cancelled_order(self, request, items, groups = ['seller','buyer','admin'], **kwargs):
        from notifications.cancelledordernotification import CancelledOrderNotification
        notification_obj = CancelledOrderNotification(self, items, request, groups=groups, **kwargs)
        notification_obj.send()
    
    def notify_confirmed_order_to_seller(self, groups = ['seller','buyer','admin']):
        from notifications.sellerordernotification import SellerOrderNotification
        notification_obj = SellerOrderNotification(self, **dict(groups=groups))
        notification_obj.send()

    def notify_shipped_order(self, request, shipment):
        from notifications.shippedordernotification import ShippedOrderNotification
        notification_obj = ShippedOrderNotification(self, request, **dict(shipment=shipment))
        notification_obj.send()


    def clear_items(self, request):
        for oi in self.get_order_items(request):
            oi.delete(using='default')
        self.coupon = None
        self.coupon_discount = Decimal(0)
        self.top10_discount = Decimal(0)
        self.auto_promotions_discount = Decimal(0)
        self.shipping_charges = Decimal(0)
        self.reference_order_id = ''
        self.payment_mode = ''
        self.payment_realized_mode = ''
        self.payback_id = None
        self.update_billing(request)
    
    #required - Anubhav
    def apply_discount_value(self, request, **kwargs):
        discount_value = kwargs.get('discount_value')
        discount_type = kwargs.get('discount_type')
        applies_to = kwargs.get('applies_to')
        
        amount = Decimal(0)
        if applies_to == 'order_total':
            if discount_type == 'percentage':
                discount_value = Decimal((self.payable_amount * discount_value)/100)
        elif applies_to == 'product_offer_price':
            #amount = self.payable_amount_without_discount()
            amount = self.total
        elif applies_to == 'order_shipping_charge':
            if discount_type == 'percentage':
                discount_value = Decimal((self.shipping_charges * discount_value)/100)

        if discount_value > self.payable_amount:
            discount_value = self.payable_amount
        self.coupon_discount = discount_value
        self.payable_amount -= self.coupon_discount

    
    def calculate_discount_value(self,payable_amount,percentage):
        discount_value = Decimal(str(payable_amount * (Decimal(percentage)/100))).quantize(Decimal('1'), rounding=ROUND_UP)
        return discount_value

    def apply_coupon(self,request, **kwargs):
        coupon_code = kwargs.get('coupon_code')
        # From update billing validate promotion is called
        return self.update_billing(request, coupon_code=coupon_code, 
            sender='apply_coupon')

    
    #def fb_product_availability(self):
    #    zipcode = self.get_delivery_info().address.pincode
    #    not_available_items = []
    #    for item in self.get_order_items(request, exclude=dict(state__in=['cancelled',
    #        'bundle'])):
    #        json = check_availability(item.seller_rate_chart.sku, zipcode, item.qty)
    #        if 'Error' in json or not json:
    #            not_available_items.append({'item':item,'error':json})
    #    return not_available_items 

    def booking_date(self):
        return self.timestamp.strftime('%d-%m-%y')
    
    def order_date(self):
        return self.payment_realized_on.strftime('%d-%m-%y')
    
    def phone(self):
        return self.user.primary_phone
    
    def name(self):
        return self.user.full_name
    
    def city(self):
        return self.get_delivery_city()
    
    def set_tracked(self):
        self.ga_tracked = True
        self.save()
        return ''

    # Please don't pass request to this function. Called from template
    def printable_payment_mode(self):
        return PaymentAttempt.PAYMENT_MODES_MAP.get(self.payment_mode, self.payment_mode)

    def save_history(self, request):
        oh = OrderHistory()
        for field in self._meta.fields:
            setattr(oh,field.name,getattr(self, field.name))
        oh.id = None
        oh.revision_time = datetime.now()
        oh.revised_by = utils.get_user_profile(request.user)
        oh.save()
        for oi in self.get_order_items(request, exclude=dict(state='bundle_item')):
            oi.save_history(request)
    
    # Not required here since it is not related to order - Anubhav
    # Used directly in views
    def get_shipping_delivery_info(self, request, **kwargs):
        addressbook_id = kwargs.get('addressbook_id', None)
        delivery_info = None
        if addressbook_id:
            selected_user_address = AddressBook.objects.get(id=addressbook_id)
            if utils.is_future_ecom(self.client) or utils.is_ezoneonline(self.client):
                from integrations.fbapi import fbapiutils
                state = fbapiutils.STATES_MAP[selected_user_address.state.name]
            else:
                state = selected_user_address.state.name
            delivery_info = {'delivery_state':state,
                    'delivery_first_name':selected_user_address.first_name,
                    'delivery_last_name':selected_user_address.last_name,
                    'delivery_address': selected_user_address.address,
                    'delivery_city':selected_user_address.city.name,
                    'delivery_country':'India',
                    'delivery_pincode':selected_user_address.pincode,
                    'delivery_email':selected_user_address.email,
                    'delivery_phone':selected_user_address.phone}
        return delivery_info

    #TODO Please check for shipping charges. Since it is on order level and not item level currently - Anubhav
    #Payback earning and burning will directly take the amount sent - Anubhav
    def openRefund(self, request, **kwargs):
        if not utils.is_future_ecom(self.client):
            return
        profile = kwargs.get('profile', None)
        amount = kwargs.get('amount', None)
        #list of dictionaries. [{order_item, amount, qty},...]
        refund_items = kwargs.get('refund_items', [])
        notes = kwargs.get('notes', None)
        earn_reversal = kwargs.get('earn_reveral',True)
        o_log = kwargs.get('order_log')

        from payments.models import Refund, RefundItem
        if amount<=0:
            raise self.InvalidRefundAmount
        
        if self.payback_id and earn_reversal:
            points_header = PointsHeader(order=self)
            points_header.earn_reversal(request, refund_items=refund_items,
                amount=amount, notes=notes)
        
        if self.payment_mode == 'payback':
            points_header = PointsHeader(order=self)
            points_header.burn_reversal(request, refund_items=refund_items,
                amount=amount, notes=notes)
            return
        
        if not o_log:
            o_log = OrderLog.objects.create(order=self, profile=profile, action='refund')

        refund = Refund.objects.create(order=self, notes=notes, amount=amount, opened_by=profile)
        for item in refund_items:
            if item['order_item'].state == 'bundle':
                continue
            RefundItem.objects.create(refund=refund, order_item=item['order_item'],
                qty=item['qty'], amount=item['amount'])
        
        RefundLog.objects.create(refund=refund, order_log=o_log, amount=amount, notes=notes,
            status='open') 
    
    def get_order_log(self, request, **kwargs):
        from fulfillment.models import ShipmentLog
        log_info_dict = {}
        o_logs = self.order_log.select_related('profile','coupon_old','coupon_new'
            ).all().order_by('id')
        for o_log in o_logs:
            log_info_dict[o_log.id] = (o_log, [])
        item_logs = OrderItemLog.objects.select_related('order_item').filter(
            order_log__in=o_logs).order_by('id')
        payment_logs = PaymentLog.objects.filter(order_log__in=o_logs).order_by('id')
        shipment_logs = ShipmentLog.objects.filter(order_log__in=o_logs).order_by('id')
        refund_logs = RefundLog.objects.filter(order_log__in=o_logs).order_by('id')
        log_items = []
        for item_log in item_logs:
            log_items.append(item_log)
        for payment_log in payment_logs:
            log_items.append(payment_log)
        for shipment_log in shipment_logs:
            log_items.append(shipment_log)
        for refund_log in refund_logs:
            log_items.append(refund_log)
        log_items.sort(key=lambda log: log.timestamp, reverse=True)
        
        for log_item in log_items:
            o_log_id = log_item.order_log_id
            ol, l = log_info_dict[o_log_id]
            l.append(log_item)
            log_info_dict[o_log_id] = (ol, l)
        
        keys = log_info_dict.keys()
        keys.sort(reverse=True)
        log_info = [log_info_dict[k] for k in keys]
        return log_info

    #not required - prady
    def next_order_state(self, payment_attempt_state):
        try:
            payment_attempt = self.paymentattempt_set.all().order_by('-id')[0]
            if payment_attempt.status.lower() == 'in verification':
                return 'paid'
            if self.state.lower() == 'paid':
                return 'confirmed'
            if payment_attempt.payment_mode.lower() == 'cod' and payment_attempt.status.lower() == 'pending realization':
                return 'paid'
            else:
                return 'booked'
        except:
            log.info(":: No Payment Attempt Exists. Add More State ::: ")
            
    def update_promotion_params(self, request, **kwargs):        
        type = kwargs.get('type', None)
        if not self.coupon or not type:
            return 
        coupon = self.coupon
        promo_coupons = PromoCoupon.objects.select_related('promotion').filter(coupon_code=coupon.code)
        if promo_coupons:
            # increment total_uses of this promotion
            promotion = promo_coupons[0].promotion
            if type == 'order_placed':
                if not promotion.total_uses:
                    promotion.total_uses = 1
                else:
                    promotion.total_uses += 1
            elif type == 'cancel':
                if not promotion.total_uses or promotion.total_uses <= 0:
                    log.exception("Found invalid total_uses for promotion: %s" % promotion)
                else:
                    promotion.total_uses -= 1
            promotion.save()
        return
    
    #for franchise orders
    def update_commission(self, order_item, quant_delta):
        try:
            from web.views.franchise_views import FranchiseCommissionOnItem
            commission_on_item = FranchiseCommissionOnItem.objects.select_related('FranchiseOrder', 'OrderItem').get(order_item = order_item)
            
            if quant_delta > 0:
                if commission_on_item.order_item.state == 'cancelled':
                    new_comm_total_fran = 0
                    new_comm_total_ntwk = 0 #old_quant = quant_delta
                else:
                    new_quant = commission_on_item.order_item.qty
                    old_quant = new_quant + quant_delta
                    
                    old_comm_per_prod_fran = round(float(commission_on_item.franc_commission_amnt / old_quant) ,2)
                    new_comm_total_fran = round(float(old_comm_per_prod_fran * new_quant) ,2)
                    
                    old_comm_per_prod_ntwk = round(float(commission_on_item.network_commission_amnt / old_quant) ,2)
                    new_comm_total_ntwk = round(float(old_comm_per_prod_ntwk * new_quant) ,2)
                
                    #print "updation required ... old_quant = ",old_quant, " new_quant = ",new_quant, " old_comm_per_prod_fran = ",old_comm_per_prod_fran, " new_comm_total_fran = ",new_comm_total_fran, " old_comm_per_prod_ntwk= ", old_comm_per_prod_ntwk, " new_comm_total_ntwk= ", new_comm_total_ntwk
                try:
                    commission_on_item.franc_commission_amnt = new_comm_total_fran
                    commission_on_item.network_commission_amnt = new_comm_total_ntwk
                    commission_on_item.save()
                    
                    commission_on_item.franchise_order.franc_commission_amnt = new_comm_total_fran
                    commission_on_item.franchise_order.network_commission_amnt = new_comm_total_ntwk
                    commission_on_item.franchise_order.save()
                    return True
                except:
                    pass
            else:
                pass
            return False
        except:
            return False
    
    def save(self, *args, **kwargs):
        super(Order, self).save(*args, **kwargs)
        if utils.is_ezoneonline_id(self.client_id) and not self.reference_order_id:
            newid = '1%03d%s' % (self.client_id, self.id)
        if not (self.reference_order_id and self.support_state):
            newid = '%s%s' % (self.client.order_prefix, self.id)
            self.reference_order_id = newid
                

def on_pre_delete_handler(sender, **kwargs):
    obj = kwargs['instance']
    if isinstance(obj, Order):
        raise Exception("Cannot delete order %s" % obj.id)
models.signals.pre_delete.connect(on_pre_delete_handler, sender=Order)
models.signals.post_save.connect(indexer.post_save_handler, sender=Order)

#will not be using this table - prady
class OrderHistory(models.Model):
    order = models.ForeignKey(Order)
    state = models.CharField(max_length=20)
    payable_amount = models.DecimalField(max_digits=22,decimal_places=2,blank=True,null=True,default=Decimal(0))
    shipping_charges = models.DecimalField(max_digits=22,decimal_places=2,blank=True,null=True,default=Decimal(0))
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey('users.Profile', null=True, blank=True)
    coupon = models.ForeignKey('promotions.Coupon',blank=True,null=True)


class OrderLog(models.Model):
    order = models.ForeignKey(Order, related_name='order_log')
    timestamp = models.DateTimeField(auto_now_add=True)
    profile = models.ForeignKey('users.Profile', null=True, blank=True, default=None, related_name='+')
    action = models.CharField(max_length=50, choices=(
        ('modify','modify'),        #modification
        ('cancel','cancel'),        #cancellation
        ('order item','order item'),#order item update
        ('payment','payment'),      #payment update
        ('shipment','shipment'),    #shipment update
        ('refund','refund')))       #refund update
    status = models.CharField(max_length=30, null=True, blank=True, default=None)
    payment_mode_old = models.CharField(max_length=15, null=True, blank=True, default=None)
    payment_mode_new = models.CharField(max_length=15, null=True, blank=True, default=None)
    coupon_old = models.ForeignKey('promotions.Coupon', null=True, blank=True, default=None, related_name='+')
    coupon_new = models.ForeignKey('promotions.Coupon', null=True, blank=True, default=None, related_name='+')
    discount_old = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True, default=None)
    discount_new = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True, default=None)
    auto_promotions_discount_old = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True, default=None)
    auto_promotions_discount_new = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True, default=None)
    shipping_charges_old = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True, default=None)
    shipping_charges_new = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True, default=None)
    payable_amount = models.DecimalField(max_digits=22, decimal_places=2, null=True, blank=True, default=None)
    earn_points = models.IntegerField(null=True, blank=True, default=None)
    burn_points = models.IntegerField(null=True, blank=True, default=None)
    address_old = models.TextField(null=True, blank=True, default=None)
    address_new = models.TextField(null=True, blank=True, default=None)
    notes = models.TextField(null=True, blank=True, default=None)


class OrderItem(models.Model):
    # to which order does this item belong
    order = models.ForeignKey(Order)
    state = models.CharField(max_length=100,blank=True,choices=(
        ('pending','Pending'), # pending order items
        ('confirmed','Confirmed'), # confirmed order items
        ('cancelled','Cancelled'), # cancelled
        ('shipped','Shipped'),
        ('delivered','Delivered'),
        ('refunded','Refunded')))
    seller_rate_chart = models.ForeignKey('catalog.SellerRateChart',blank=True,null=True)
    item_title = models.CharField(max_length=500)
    gift_title = models.CharField(max_length=500,blank=True)
    #list price * qty
    list_price = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    #offer price * qty
    sale_price = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0),verbose_name='Offer price')
    #cashback amount * qty
    cashback_amount = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0),verbose_name='Cashback', null=True, blank=True)
    #shipping charges * qty
    shipping_charges = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0),verbose_name='Shipping')
    #item level discount * qty (used for bundle products)
    discount = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
    #actual payable amount = sale price - cashback amount + shipping charges - discount (added on 25-12-2011)
    total_amount = models.DecimalField(max_digits=22, decimal_places=2, default=Decimal(0))
    qty = models.IntegerField(default=1)
    #not used
    offer = models.ForeignKey('promotions.Offer', blank=True, null=True)
    created_on = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    modified_on = models.DateTimeField(auto_now=True, blank=True, null=True)
    is_inventory_blocked = models.BooleanField(default=False)
    # shipping related fields
    delivery_days = models.IntegerField(default=Decimal(0), blank=True, null=True)
    #expected stock arrival date (given by category team, if orderitem is in awaiting stock state)
    expected_stock_arrival = models.DateTimeField(blank=True,null=True)
    #used to store IFS committed delivery date (before a shipment is created). Once shipment is created use/update value from shipment
    expected_delivery_date = models.DateTimeField(blank=True, null=True)
    #currently used to store cancellation reason
    notes = models.TextField(default=None, null=True, blank=True)
    
    #dispatch_due_on, dispatched_on, delivered_on: not used (use shipment table for these values)
    #dispatch_due_on = models.DateTimeField(blank=True,null=True)
    #dispatched_on = models.DateTimeField(blank=True,null=True)
    #delivered_on = models.DateTimeField(blank=True,null=True)
    
    #additional OrderItem Exceptions
    QuantityIncrease = type('QuantityIncrease', (Exception,), {})
    InvalidOperation = type('InvalidOperation', (Exception,), {})
    InsufficientData = type('InsufficientData', (Exception,), {})
    NoCancellationReason = type('InsufficientData', (Exception,), {})

    def item_info(self):
        info = ''
        info += 'title:%s, sku:%s, qty:%s' % (self.item_title, self.seller_rate_chart.sku, self.qty)
        return info

    def index(self, **kw):
        ''' Indexes the orderitem object in solr '''
        from utils import solrutils 
        orderitem_doc = self.get_orderitem_solr_doc()

        order_doc = kw.get('order_doc')
        if not order_doc:
            order_doc = self.order.get_order_solr_doc()

        orderitem_doc.update(order_doc)
        orderitem_doc['doc_type'] = 'orderitem'
        orderitem_doc['unique_key'] = '%s%s' % (orderitem_doc['doc_type'], self.id)

        solrutils.order_add_data(orderitem_doc)

    def get_orderitem_solr_doc(self):
        z = Decimal('0')

        orderitem_doc = {
            'order_id': self.order_id,
            'doc_type': 'orderitem',
            'item_pk': self.id,
            'item_title': self.item_title,
            'item_seller_rate_chart_id': self.seller_rate_chart.id,
            'item_article_id': self.seller_rate_chart.article_id,
            'item_state': self.state,
            'item_qty': self.qty,
            'item_list_price': '%.2f' % (self.list_price or z),
            'item_sale_price': '%.2f' % (self.sale_price or z),
            'item_cashback_amount': '%.2f' % (self.cashback_amount or z),
            'item_shipping_charges': '%.2f' % (self.shipping_charges or z),
            'item_discount': '%.2f' % (self.discount or z),
            'item_total_amount': '%.2f' % (self.total_amount or z),
            'item_category_id': self.seller_rate_chart.product.category_id,
            'item_brand_id': self.seller_rate_chart.product.brand_id,
            'item_brand': self.seller_rate_chart.product.brand.name,
            'item_sku': self.seller_rate_chart.sku,
            'item_sku_with_title': self.seller_rate_chart.sku + '__' + self.item_title,
        }

        parent_category_ids = []
        for p in self.seller_rate_chart.product.category.get_all_parents():
            parent_category_ids.append(p.id)
        parent_category_ids.append(orderitem_doc['item_category_id'])
        orderitem_doc['item_category_ids'] = parent_category_ids

        if self.expected_stock_arrival:
            orderitem_doc[
                'item_expected_stock_arrival'] = self.expected_stock_arrival
        if self.expected_delivery_date:
            orderitem_doc[
                'item_expected_delivery_date'] = self.expected_delivery_date
        if self.delivery_days:
            orderitem_doc['item_delivery_days'] = self.delivery_days
        try:
            if self.sap_order_item:
                orderitem_doc['item_sap_status'] = self.sap_order_item.status
            if self.sap_order_item.lsp:
                orderitem_doc['item_lsp'] = self.sap_order_item.lsp.name
                orderitem_doc['flf_lsp'] = self.sap_order_item.lsp.name
            if self.sap_order_item.dc:
                orderitem_doc['item_dc'] = self.sap_order_item.dc.code
                orderitem_doc['flf_dc'] = self.sap_order_item.dc.code 
        except:
            pass



        if self.order.confirming_timestamp:

            fulfillment_status = 'stock expected'
            flf_ship_before = None
            delta_to_add = 1

            if self.state == 'cancelled':
                fulfillment_status = 'cancelled'

            ilog = self.inventorylog_set.all().order_by('-created_on')
            if ilog:
                if ilog[0].inventory:
                    if ilog[0].inventory.type == 'physical':
                        fulfillment_status = 'to be dispatched'
                        flf_ship_before = self.order.confirming_timestamp + timedelta(days=1)
                    else:
                        if ilog[0].inventory.expected_in:
                            fulfillment_status = 'to be picked'
                            flf_ship_before = self.order.confirming_timestamp + timedelta(days=3)
                            delta_to_add = 3
                        else:
                            fulfillment_status = 'stock expected'
                            if self.expected_stock_arrival:
                                flf_ship_before = self.expected_stock_arrival + timedelta(days=1)

            # Get the shipments, the last shipment created for this item
            shipmentitems = self.shipment_items.exclude(
                shipment__status='deleted').order_by('-shipment')

            shipment = None
            if shipmentitems:
                shipmentitem = shipmentitems[0]
                shipment = shipmentitem.shipment
                fulfillment_status = 'to be dispatched'

                if shipmentitem.shipment.status == 'shipped':
                    fulfillment_status = 'shipped'
                elif shipmentitem.shipment.status == 'delivered':
                    fulfillment_status = 'delivered'
                elif shipmentitem.shipment.status == 'undeliverable':
                    fulfillment_status = 'undeliverable'
                elif shipmentitem.shipment.status  == 'returned':
                    fulfillment_status = 'returned'

            if shipment:
                shipment_doc = shipment.get_shipment_solr_doc()
                if shipment_doc:
                    del shipment_doc['doc_type']
                orderitem_doc.update(shipment_doc)
                orderitem_doc['flf_dc'] = shipment.dc.code 
                if shipment.lsp:
                    orderitem_doc['flf_lsp'] = shipment.lsp.name

            orderitem_doc['flf_status'] = fulfillment_status
            orderitem_doc['flf_del_before'] = self.expected_delivery_date

            if flf_ship_before:
                if flf_ship_before < self.order.confirming_timestamp:
                    flf_ship_before = self.order.confirming_timestamp + timedelta(days=delta_to_add)
                orderitem_doc['flf_ship_before'] = flf_ship_before 
            else:
                orderitem_doc['flf_ship_before'] = self.order.confirming_timestamp + timedelta(days=delta_to_add)
                
            
        # Get the order related fields
        return orderitem_doc

    def clone(self, order=None, parent=None):
        if not order:
            return
        cloned = OrderItem(order=order)
        cloned.seller_rate_chart = self.seller_rate_chart
        cloned.item_title = self.item_title
        cloned.state = self.state
        cloned.gift_title = self.gift_title
        cloned.list_price = self.list_price
        cloned.sale_price = self.sale_price
        cloned.cashback_amount = self.cashback_amount
        cloned.shipping_charges = self.shipping_charges
        cloned.discount = self.discount
        cloned.total_amount = self.total_amount
        cloned.qty = self.qty
        cloned.delivery_days = self.delivery_days
        cloned.expected_delivery_date = self.expected_delivery_date
        #cloned.dispatch_due_on = self.dispatch_due_on - not used
        #cloned.dispatched_on = self.dispatched_on - not used
        #cloned.delivered_on = self.delivered_on - not used
        cloned.save()

        if parent:
            BundleItem.objects.create(order=order, bundle_item=cloned, parent_item=parent,
                qty=self.bundle_item.qty)
        return cloned

    def clone_item_relationships(self):
        for sdetails in self.subscriptiondetails_set.all():
            cloned_sd = sdetails.clone()
            cloned_sd.order_item = self
            cloned_sd.save()

        for shdetails in self.shippingdetails_set.all():
            cloned_sh = shdetails.clone()
            cloned_sh.order_item = self
            cloned_sh.save()

    def article_id(self):
        return self.seller_rate_chart.article_id

    def customer_address(self):
        from locations.models import Address
        address = Address.objects.filter(profile = self.order.user)
        if address:
            address = address[0]
            return address.get_customer_address()
        else:
            return ''
    
    #not required - prady
    def spl_discount(self):
        coupon_discount = self.order.coupon_discount
        total_items = self.qty
        if self.order.total > 0:
            item_discount = self.sale_price/self.order.total * coupon_discount
        else:
            item_discount = 0
        return item_discount
        #return float("%.2f" % item_discount.__float__())
    
    #required
    def payable_amount(self):
        #discount = self.spl_discount()
        if self.total_amount:
            return self.total_amount
        else:
            return self.sale_price + self.shipping_charges
        #payable_amount = payable_amount.__float__() - discount
        #return float("%.2f" % payable_amount)
    
    #required
    def payable_amount_without_discount(self):
        payable_amount = self.sale_price + self.shipping_charges
        return payable_amount

    #required
    def payable_amount_with_discount(self):
        discount = self.spl_discount()
        payable_amount = self.sale_price + self.shipping_charges - discount
        return payable_amount 

    #required
    def update_info_from_src(self, request, **kwargs):
        src = self.seller_rate_chart
        qty = self.qty
        priceInfo = src.getPriceInfo(request)
        self.item_title = src.product.title
        self.list_price = priceInfo['list_price'] * qty
        self.sale_price = priceInfo['offer_price'] * qty
        self.cashback_amount = priceInfo.get('cashback_amount',Decimal(0)) * qty
        #self.shipping_charges = src.shipping_charges * qty
        self.total_amount = self.sale_price - self.cashback_amount
        self.save()
        if self.state == 'bundle':
            self.update_bundle_items(request, **kwargs)

    #required
    def update_quantity(self, request, **kwargs):
        '''
        This function will not call coupon validation code and order level
        update code. These functions need to be called from order model itself
        '''
        qty = kwargs.get('qty',0)
        order_items = kwargs.get('order_items')     #used for bundle products
        reason = kwargs.get('reason','')
        bundle_items = []                           #bundle item deltas
        o_log = kwargs.get('order_log')
        qty_old = self.qty
        
        if self.state == 'bundle_item':
            raise BundleArticle(child=self.seller_rate_chart)
        if self.seller_rate_chart.min_qty > qty:
            exp = self.seller_rate_chart.MinimumQuantity
            exp.min_qty = self.seller_rate_chart.min_qty
            exp.item = self.item_title
            raise exp
        
        is_bundle = False
        if self.state == 'bundle':
            is_bundle = True
        if self.order.support_state:
            #Pending order created
            if self.qty:
                list_price = self.get_unit_list_price()
                offer_price = self.get_unit_price()
                cashback_amount = self.get_unit_cashback_amount()
                #shipping_charges = self.get_unit_shipping_charges()
        else:
            #cart
            rate_chart = self.seller_rate_chart
            priceInfo = rate_chart.getPriceInfo(request)
            offer_price = priceInfo['offer_price']
            list_price = priceInfo['list_price']
            cashback_amount = priceInfo['cashback_amount']
            if not cashback_amount:
                cashback_amount = Decimal('0')
            #shipping_charges = rate_chart.shipping_charges
        if qty <= 0:
            qty = 0
        self.qty = qty
        
        self.list_price = list_price * self.qty
        self.sale_price = offer_price * self.qty
        self.cashback_amount = cashback_amount * self.qty
        #self.shipping_charges = shipping_charges * self.qty
        if self.qty == 0:
            self.state = 'cancelled'
            self.notes = 'Item quantity zero'
            if is_bundle:
                bundle_items = self.cancel_bundle_items(request)
            elif self.sap_order_item:
                self.sap_order_item.status = 'cancelled'
                self.sap_order_item.save()
        elif (not is_bundle):
            self.state = 'modified'
        self.total_amount = self.sale_price - self.cashback_amount
        self.notes = reason
        self.save()
        if is_bundle:
            bundle_items = self.update_bundle_items(request, order_items=order_items)
        
        if o_log:
            OrderItemLog.objects.create(order_item=self, order_log=o_log, action='modify',
                qty_old=qty_old, qty_new=self.qty, notes=reason)
        return bundle_items

    def update_bundle_items(self, request, **kwargs):
        bundle_items = []
        total_sale_price = Decimal(0)
        if self.order.support_state:
            #order
            bundle_products = BundleItem.objects.select_related('bundle_item','bundle_item__seller_rate_chart'
                ).filter(parent_item=self)
            for product in bundle_products:
                bundle_items.append({'src':product.bundle_item.seller_rate_chart, 'qty':product.qty,
                    'list_price':product.bundle_item.get_unit_list_price(),
                    'sale_price':product.bundle_item.get_unit_price()})
                total_sale_price += (product.bundle_item.get_unit_price() * product.qty)
        else:
            #cart
            bundle_products = BundleProducts.objects.select_related('bundle_src','bundle_src__product').filter(
                rate_chart=self.seller_rate_chart, active=True)
            for product in bundle_products:
                src = product.bundle_src
                p_info = src.getPriceInfo(request)
                bundle_items.append({'src':src, 'qty':product.qty, 'list_price':p_info['list_price'],
                    'sale_price':p_info['offer_price']})
                total_sale_price += (p_info['offer_price'] * product.qty)
        total_sale_price *= self.qty
        return self.update_bundle_billing(request, bundle_items=bundle_items, total_sale_price=total_sale_price,
            **kwargs)
       
    def update_bundle_billing(self, request, **kwargs):
        order_items = kwargs.get('order_items')
        bundle_items = kwargs.get('bundle_items')
        total_sale_price = kwargs.get('total_sale_price')

        #total_discount = total_sale_price - self.sale_price
        #rem_discount = total_discount
        rem_sale_price = self.sale_price
        total_cashback = self.cashback_amount
        rem_cashback = total_cashback
        #total_shipping = self.shipping_charges
        #rem_shipping = total_shipping
        num = len(bundle_items)
        deltas = []             #for bundle item deltas
        for i, item in enumerate(bundle_items):
            src = item['src']
            oi = None
            for o_i in order_items:
                if o_i.seller_rate_chart_id == src.id:
                    oi = o_i
                    if not oi.bundle_item:
                        exp = Order.BundleItemAlreadyAdded
                        exp.parent=self.seller_rate_chart
                        exp.child=src
                        raise exp
                    elif oi.bundle_item.parent_item_id != self.id:
                        exp = Order.BundleItemConflict
                        exp.new_src=self.seller_rate_chart
                        exp.old_src=oi.bundle_item.parent_item.seller_rate_chart
                        raise exp
                    break
            if not oi:
                oi = OrderItem()
                oi.order = self.order
                oi.seller_rate_chart = src
                oi.qty = 0
                oi.state = 'bundle_item'
            new_qty = item['qty'] * self.qty
            delta_qty = oi.qty - new_qty
            oi.qty = new_qty
            old_amount = oi.payable_amount()
            
            if not (oi.id or oi.order.support_state):
                oi.item_title = src.product.title
                oi.gift_title = src.gift_title
            
            oi.list_price = item['list_price'] * oi.qty
            oi.sale_price = item['sale_price'] * oi.qty
            if i != num-1:
                ratio = oi.sale_price/total_sale_price
                d = (self.sale_price*ratio).quantize(Decimal('.01'), rounding=ROUND_UP)
                oi.sale_price = d
                rem_sale_price -= d
                #d = (total_discount*ratio).quantize(Decimal('.01'), rounding=ROUND_UP)
                #oi.discount = d
                #rem_discount -= d
                d = (total_cashback*ratio).quantize(Decimal('.01'), rounding=ROUND_UP)
                oi.cashback_amount = d
                rem_cashback -= d
                #d = (total_shipping*ratio).quantize(Decimal('.01'), rounding=ROUND_UP)
                #oi.shipping_charges = d
                #rem_shipping -= d
            else:
                #oi.discount = rem_discount
                oi.sale_price = rem_sale_price
                oi.cashback_amount = rem_cashback
                #oi.shipping_charges = rem_shipping
            oi.total_amount = oi.sale_price - oi.cashback_amount #added by prady
            delta_amount = old_amount - oi.total_amount
            if oi.id:
                oi.save()   #orderitem already exists
                if delta_qty>0:
                    deltas.append({'order_item':oi, 'amount':delta_amount, 'qty':delta_qty, 'qty_new':oi.qty})
            else:
                #orderitem is newly created. create bundleitem
                oi.save()
                BundleItem.objects.create(order=self.order, parent_item=self, bundle_item=oi, qty=item['qty'])
        return deltas
    
    def cancel_bundle_items(self, request, **kwargs):
        deltas = []
        bundle_items = self.order.get_order_items(request, select_related=('sap_order_item',),
            filter=dict(bundle_item__parent_item=self, state='bundle_item'))
        for item in bundle_items:
            if item.sap_order_item:
                item.sap_order_item.status = 'cancelled'
                item.sap_order_item.save()
            deltas.append({'order_item':item, 'amount':item.payable_amount(), 'qty':item.qty, 'qty_new':0})
            item.state = 'cancelled'
            item.save()
        #c = bundle_items.update(state='cancelled')
        #log.info('bundle items updated - %s' % (c))
        return deltas
     
    def validate_bundle_items(self, request):
        curr_items = BundleItem.objects.select_related('bundle_item').filter(parent_item=self)
        bundle_items = BundleProducts.objects.filter(rate_chart=self.seller_rate_chart, active=True)
        if len(curr_items) != len(bundle_items):
            return False
        for item in curr_items:
            b_item = None
            for bi in bundle_items:
                if item.bundle_item.seller_rate_chart_id == bi.bundle_src_id:
                    b_item = bi
                    break
            if (not b_item) or (b_item.qty != item.qty):
                return False
        return True

    def reference_order_id(self):
        return self.order.reference_order_id

    def order_date(self):
        return self.order.payment_realized_on

    def agent(self):
        return self.order.agent

    def booking_agent(self):
        return self.order.booking_agent

    def delivery_address(self):
        delivery_info = DeliveryInfo.objects.select_related('address').get(order=self.order)
        return delivery_info.address.get_customer_address()

    def payment_mode(self):
        if self.order.state == 'confirmed':
            return self.order.payment_realized_mode
        elif self.order.state == 'pending_order':
            return self.order.payment_mode

    def delivery_notes(self):
        try:
            delivery_info = DeliveryInfo.objects.get(order=self.order)
            return delivery_info.notes
        except DeliveryInfo.DoesNotExist:
            return ''

    def gift_notes(self):
        try:
            gift_info = GiftInfo.objects.get(order=self.order)
            return gift_info.notes
        except GiftInfo.DoesNotExist:
            return ''

    def payment_notes(self):
        payment_attempt = self.order.get_payments(None,filter=dict(status='paid')).only('notes')
        if payment_attempt:
            return payment_attempt[0].notes
        else:
            return ''

    def transaction_no(self):
        payment_attempt = self.order.get_payments(None,filter=dict(status='paid')).only('pg_transaction_id')
        if payment_attempt:
            return payment_attempt[0].pg_transaction_id
        else:
            return ''

    def seller(self):
        return self.seller_rate_chart.seller

    def user_name(self):
        return self.order.user

    def user_phone(self):
        if self.order.user:
            phones = self.order.user.get_primary_phones()
            if phones:
                return phones[0]
            return ''

    def user_email(self):
        if self.order.user:
            emails = self.order.user.get_primary_emails()
            if emails:
                return emails[0]
            return ''

    def shipping_details(self):
        return self.shippingdetails_set.all()

    def which_top10_list(self):
        list_items = ListItem.objects.filter(sku=self.seller_rate_chart,list__type='top_10')
        lists = []
        for item in list_items:
            lists.append(item.list)
        return lists

    def set_src_list_price(self, list_price, dont_save=False):
        self.list_price = list_price * self.qty
        if not dont_save:
            self.save()

    def set_src_offer_price(self, offer_price, dont_save=False):
        self.sale_price = offer_price * self.qty
        if not dont_save:
            self.save()

    def set_src_shipping_price(self, dont_save=False):
        shipping_charges = self.seller_rate_chart.shipping_charges * self.qty
        self.shipping_charges = shipping_charges
        if not dont_save:
            self.save()

    def get_unit_price(self):
        if self.qty > 0:
            return self.sale_price / self.qty
        return Decimal('0')
        
    def get_unit_list_price(self):
        if self.qty > 0:
            return self.list_price / self.qty
        return Decimal('0')
        
    def get_unit_cashback_amount(self):
        if self.qty > 0 and self.cashback_amount:
            return self.cashback_amount / self.qty
        return Decimal('0')
        
    def get_unit_shipping_charges(self):
        if self.qty > 0:
            return self.shipping_charges / self.qty
        return Decimal('0')
        
    def get_unit_discount(self):
        if self.qty > 0:
            return self.discount / self.qty
        return Decimal('0')
    
    def is_invoiced(self, request):
        if self.state in ['cancelled','bundle']:
            return True
        shipment_items = self.shipment_items.exclude(Q(shipment__invoice_number=None)|Q(shipment__invoice_number='')|
            Q(shipment__status='deleted')).aggregate(qty=Sum('quantity'))
        if shipment_items['qty'] == self.qty:
            return True
        return False

    def is_shipped(self, request):
        if self.state in ['cancelled','bundle']:
            return True
        shipment_items = self.shipment_items.exclude(Q(shipment__status='deleted')|
            Q(shipment__pickedup_on=None)).aggregate(qty=Sum('quantity'))
        if shipment_items['qty'] == self.qty:
            return True
        return False

    def is_delivered(self, request):
        if self.state in ['cancelled','bundle']:
            return True
        shipment_items = self.shipment_items.filter(shipment__status='delivered').aggregate(
            qty=Sum('quantity'))
        if shipment_items['qty'] == self.qty:
            return True
        return False

    def is_undeliverable(self, request):
        if self.state in ['cancelled','bundle']:
            return True
        shipment_items = self.shipment_items.filter(shipment__status='undeliverable').aggregate(
            qty=Sum('quantity'))
        if shipment_items['qty'] == self.qty:
            return True
        return False

    def is_returned(self, request):
        if self.state in ['cancelled','bundle']:
            return True
        shipment_items = self.shipment_items.filter(shipment__status='returned').aggregate(
            qty=Sum('quantity'))
        if shipment_items['qty'] == self.qty:
            return True
        return False

    def fill_line_item_details(self, request, **kwargs):
        type = kwargs.get('type','new')
        op = kwargs.get('op','U')
        reason_code = kwargs.get('reason_code','')
        line_item_nodes = []
        sap_article_id = '%018d' % long(self.seller_rate_chart.article_id)
        dc = self.sap_order_item.dc
        lsp = self.sap_order_item.lsp
        if not (dc or lsp):
            dc, lsp, physical_stock = self.get_resolved_dc_lsp()

        if type == 'new' or type == 'cancel':
            line_item_nodes = [('ItemSno',str(self.sap_order_item.sno)), ('ItemID',sap_article_id),
                                ('ItemDesc','%s - %s' % (self.item_title,self.seller_rate_chart.sku)), ('RefID',''),
                                ('ShipGroupCode',''), ('Quantity','%s' % self.qty),
                                ('ReqDelivDate',''), ('ItemState',''), ('SalesUnit',''),
                                ('ItemCategory',''), ('isThirdParty','false'), ('Vendor',''),
                                ('MRP','%.2f' % self.get_unit_list_price()), ('SalesPrice','%.2f' % self.get_unit_price()),
                                ('OfferPrice','%.2f' % self.get_unit_price()), ('Amount', '%.2f' % self.payable_amount()),
                                ('Discount','%.2f' % self.discount),
                                ('ItemCommisionAmount','%.2f' % self.get_unit_commission()),
                                ('NLC',''), ('Plant',dc.code), ('Catalogs','|FutureBazaar'), ('ProductGroupId',''),
                                ('ModeOfTransport',''), ('ShippingMode',''),
                                ('LSP','%010d'%long(lsp.code)), ('ShipCharge','%.2f' % self.shipping_charges),
                                ('EANUPC',''), ('Reason',reason_code), ('Notes',''),
                                ('ItemSno1',''), ('GV',''), ('Bundle',''),
                              ]
        elif type == 'modified':
            line_item_nodes = [('itemDesc',self.item_title), ('itemID',sap_article_id),
                                ('lineItemId',str(self.sap_order_item.sno)), ('itemState',''),
                                ('lspName',lsp.name), ('lspNumber','%010d'%long(lsp.code)),
                              ]
            try:
                shipment = self.get_shipments(request)[0]
                line_item_nodes.extend([('deliveryNumber',shipment.delivery_number),
                                        ('invoiceNumber',shipment.invoice_number),
                                        ('invoiceDate',shipment.invoiced_on.strftime('%Y%m%d')),
                                        ('trackingNumber',shipment.tracking_number),
                                       ])
            except:
                line_item_nodes.extend([('deliveryNumber',''), ('invoiceNumber',''), ('invoiceDate',''), ('trackingNumber','')])
            line_item_nodes.extend([('quantity','%s' % self.qty), ('reasonOfCancellation',reason_code),
                                    ('operation',op), ('plant',dc.code), ('salesPrice','%.2f' % self.get_unit_price()),
                                    ('discount','%.2f' % self.discount),
                                    ('ItemCommisionAmount','%.2f' % self.get_unit_commission()),
                                    ('listPrice','%.2f' % self.get_unit_price()),
                                    #('listPrice','%.2f' % self.get_unit_list_price()),
                                    ('shippingPrice','%.2f' % self.shipping_charges),
                                    ('isThirdParty','false'), ('vendor',''), ('nlc','0.0'), ('EANUPC',''),
                                    ('onSale',''), ('bundle',''), ('gvClaimCodes',''), ('requiredDeliveryDate',''),
                                   ])
        return line_item_nodes

    #not required - prady
    def save_history(self, request):
        oh = OrderItemHistory()
        for field in self._meta.fields:
            setattr(oh, field.name, getattr(self, field.name))
        oh.itemid = getattr(self,'id')
        oh.id = None
        oh.revision_time = datetime.now()
        oh.revised_by = utils.get_user_profile(request.user)
        oh.save()
    
    #not required - prady
    def add_history(self, request, **kwargs):
        profile = kwargs.get('profile', None)
        OrderItemHistory.objects.create(order_item=self, qty=self.qty, offer=self.offer, state=self.state,
            shipping_charges=self.shipping_charges, updated_by=profile)
    
   
models.signals.post_save.connect(indexer.post_save_handler, sender=OrderItem)


#will not be using this model - prady
class OrderItemHistory(models.Model):
    order_item = models.ForeignKey(OrderItem)
    state = models.CharField(max_length=20,blank=True,choices=(
        ('new','New'),
        ('cancelled','Cancelled'),
        ('modified','Modified'),
        ('returned','Returned'),
        ('refunded','Refunded')))
    shipping_charges = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0),verbose_name='Shipping')
    qty = models.IntegerField(default=1)    #current orderitem quantity
    offer = models.ForeignKey('promotions.Offer', blank=True, null=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey('users.Profile', null=True, blank=True)


class OrderItemLog(models.Model):
    order_item = models.ForeignKey(OrderItem, related_name='item_log')
    order_log = models.ForeignKey(OrderLog, related_name='item_log')
    timestamp = models.DateTimeField(auto_now_add=True)
    action = models.CharField(max_length=50, choices=(
        ('modify','modify'),    #modification
        ('cancel','cancel'),    #cancellation
        ('status','status')))   #status change
    status = models.CharField(max_length=30, null=True, blank=True, default=None)
    qty_old = models.IntegerField(null=True, blank=True, default=None)
    qty_new = models.IntegerField(null=True, blank=True, default=None)
    expected_stock_arrival = models.DateTimeField(null=True, blank=True, default=None)
    expected_delivery_date = models.DateTimeField(null=True, blank=True, default=None)
    po_number = models.CharField(max_length=30, null=True, blank=True, default=None)
    po_date = models.DateField(null=True, blank=True, default=None)
    notes = models.TextField(null=True, blank=True, default=None)
    
    def get_class_name(self):
        return 'OrderItemLog'

class DeliveryInfo(models.Model):
    address = models.ForeignKey('locations.Address')
    notes = models.TextField(null=True, blank=True, verbose_name='Delivery Notes')
    order = models.OneToOneField(Order, related_name='delivery_info', verbose_name='Order Delivery')
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)
    gift_notes = models.TextField(blank=True, null=True, verbose_name='Gift Notes')
    
    #Exception
    InvalidAddress = type('InvalidAddress', (Exception, ), {}) 

    def clone(self):
        cloned = DeliveryInfo()
        cloned.address = self.address.clone(save=True)
        cloned.notes = self.notes
        return cloned
    
    def get_printable_address(self):
        addr = self.address
        printable_address = ''
        printable_address += '%s %s, ' % (addr.first_name, addr.last_name)
        printable_address += '%s, ' % addr.address
        printable_address += '%s - %s, %s, %s. ' % (addr.city.name, addr.pincode,
            addr.state.name, addr.country.name)
        printable_address += '%s, %s' % (addr.phone, addr.email)
        return printable_address

class BillingInfo(models.Model):
    '''
    This is now similar to DeliveryInfo class. A foreign key to order added for correct retrieval.
    First name, last name, phone and user fields will not be used anymore. Name and phone can be
    found in address foreign key
    '''
    address = models.ForeignKey('locations.Address')
    first_name = models.CharField(max_length=200, blank=True, null=True)   #Not used anymore - prady (14-12-2011)
    last_name = models.CharField(max_length=200, blank=True, null=True)    #Not used
    phone = models.CharField(max_length=100, blank=True, null=True)        #Not used
    user = models.ForeignKey('users.Profile', blank=True, null=True)       #Not used
    order = models.OneToOneField(Order, related_name='billing_info', null=True, blank=True)
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)

    #Exception
    InvalidAddress = type('InvalidAddress', (Exception, ), {}) 
    
    def clone(self):
        cloned = BillingInfo()
        cloned.address = self.address.clone(save=True)
        return cloned

class ShippingDetails(models.Model):
    tracking_no = models.CharField(max_length=100, blank=True)
    tracking_url = models.URLField(blank=True)
    courier = models.CharField(max_length=100, blank=True)
    notes = models.TextField(blank=True)
    order_item = models.ForeignKey(OrderItem)
    status = models.CharField(max_length=100,default="processing",verbose_name='Status',choices=(
        ('processing','Processing'),
        ('shipped','Shipped'),
        ('delivered','Delivered')))
    shipper_status = models.CharField(max_length=100,blank=True)
    modified_on = models.DateTimeField(blank=True, null=True, auto_now=True)
    
    def clone(self):
        cloned = ShippingDetails()
        cloned.tracking_no = self.tracking_no
        cloned.tracking_url = self.tracking_url
        cloned.courier = self.courier
        cloned.notes = self.notes
        cloned.status = self.status
        return cloned

class GiftInfo(models.Model):
    notes = models.TextField(verbose_name='Gift Notes',blank=True)
    order = models.ForeignKey(Order,verbose_name='Order Gift')

    def clone(self):
        cloned = GiftInfo()
        cloned.notes = self.notes
        return cloned

class ConfirmedOrder(Order):
    class Meta:
        proxy = True

class ConfirmedOrderItem(OrderItem):
    class Meta:
        proxy = True

class PendingOrder(Order):
    class Meta:
        proxy = True

class PendingOrderItem(OrderItem):
    class Meta:
        proxy = True
class ShippingTracker(ShippingDetails):
    class Meta:
        proxy = True

class OrderDailyCount(models.Model):
    date = models.DateTimeField()
    product = models.ForeignKey('catalog.Product')
    order_count = models.DecimalField(max_digits=8, decimal_places=0, default=Decimal(0))
    client = models.ForeignKey('accounts.Client', null=True, blank=True)
   
class OrderCount(models.Model):
    product = models.ForeignKey('catalog.Product', db_index=True)
    order_count = models.DecimalField(max_digits=8, decimal_places=0, default=Decimal(0), db_index=True)
    client = models.ForeignKey('accounts.Client', db_index=True, null=True, blank=True)

class OrderCountByState(models.Model):
    product = models.ForeignKey('catalog.Product', db_index=True)
    order_count = models.DecimalField(max_digits=8, decimal_places=0, default=Decimal(0))
    state = models.CharField(max_length=20,choices=(
        ('pending_order','Pending'),
        ('confirmed','Confirmed')),db_index=True, default='pending_order')
    client = models.ForeignKey('accounts.Client', db_index=True, null=True, blank=True)
    def __unicode__(self):
        return "%s - %s" % (self.product, self.state)

#To store cancelled order details
class CancelledOrder(models.Model):
    order = models.ForeignKey(Order)
    timestamp = models.DateTimeField(auto_now=True)
    user = models.ForeignKey('users.Profile')
    notes = models.TextField(null=True, blank=True)
    refund_amount = models.DecimalField(max_digits=22, decimal_places=2,default=Decimal(0))
