from notifications.notification import Notification
from notifications.email import Email as CEmail
from notifications.sms import SMS
from communications.models import Email as LEmail
from notifications import PAYMENT_MODE_STRINGS
from orders.models import  *
from catalog.models import *
from django.template import Context, Template
from django.template.loader import get_template
from datetime import datetime
from utils.utils import *
from django.utils.safestring import mark_safe
from accounts.models import *

class CancelledOrderNotification(Notification):
    source = 'web'
    def __init__(self, order, cancelled_items, request, *args,**kwargs):
        self.order = order
        self.order_items = cancelled_items
        self.request = request
        if 'groups' in kwargs:
            self.groups = kwargs['groups']
        self.refund = kwargs.get('refund_amount',0)
    
    def format_money(self,currency,money):
        return '%s %s' % (currency,formatMoney(money))
    
    def get_payment_mode_string(self,payment_mode):
        return PAYMENT_MODE_STRINGS.get(payment_mode, "")
 
    def fill_attributes(self,order,product,body_st,subject_st,
        buyer,products_map,seller_map,seller,qty,seller_total_map,\
        seller_products_map,seller_coupon_map,seller_mrp_map,\
        seller_discount_map,seller_shipping_charges_map):

        body_st['order_id'] = order.get_id()
        subject_st['order_id'] = order.get_id()
        if buyer.full_name.strip():
            body_st['customer_name'] = buyer.full_name
        else:
            body_st['customer_name'] = 'Customer'
        body_st['customer_phone'] = buyer.primary_phone
        
        if buyer.primary_email:
            body_st['customer_email'] = buyer.primary_email
        if not seller:
            body_st['qty'] = qty

        subject_st['ad_title'] = mark_safe(product.title)

        body_st['order_state'] = order.support_state
        special_discount = order.coupon_discount
        if order.auto_promotions_discount:
            #this is added separately because auto_promotions_discount can be
            #None and addition fails - prady
            special_discount += order.auto_promotions_discount
        is_coupon_discount = True
        discount = True
        if order.shipping_charges:
            body_st['order_shipping_charges'] = self.format_money(product.formatted_currency() , order.shipping_charges)
        if order.coupon_discount:
            body_st['special_discount'] = self.format_money(product.formatted_currency(),order.coupon_discount)
        body_st['payment_mode_string'] = self.get_payment_mode_string(order.payment_mode)
        #body_st['payment_mode'] = order.payment_realized_mode
        payment_mode = None
        payment_option = None
        try:
            payment_mode = PaymentMode.objects.get(code=order.payment_mode)
            payment_option = PaymentOption.objects.get(payment_mode__client = order.client, payment_mode = payment_mode)
        except:
            pass
        body_st['payment_option'] = payment_option
        body_st['helpline'] = self.order.client.confirmed_order_helpline
        body_st['signature'] = self.order.client.signature
        body_st['client'] = self.order.client

        body_st['order_payment_date'] = order.payment_realized_on.date() if order.payment_realized_on else None
        buyer_order_items = []
        seller_order_items = []

        coupon = False
        coupon_code = 'coupon'

        if seller:
            if seller.id in seller_coupon_map:
                coupon = True
                coupon_code = seller_coupon_map[seller.id]

        body_st['coupon'] = coupon
        body_st['coupon_code'] = coupon_code
        
        #order_items = order.get_order_items(None, exclude=dict(state__in=['cancelled',
        #    'bundle_item']))

        if len(self.order_items) > 1:
            body_st['multiple'] = True
        else:
            body_st['multiple'] = False
        order_mrp_total=0
        order_discount=0
        shipping_charges=0
        order_payable_total=0
        #if self.refund == None:
        #    refund = 0
        seller_refund=0
        for item in self.order_items:
            item_info = {}
            item_product = item.seller_rate_chart.product
            title = item.item_title
            item_info['title'] = mark_safe(title)
            item_info['seller'] = item.seller_rate_chart.seller.name
            item_info['price'] = self.format_money(item_product.formatted_currency() , item.list_price/item.qty)
            item_info['offer_price'] = self.format_money(item_product.formatted_currency() , item.sale_price/item.qty)
            item_info['total_item_offer_price'] = self.format_money(item_product.formatted_currency() , item.sale_price)
            item_info['state'] = item.state
            item_info['qty'] = item.qty
            item_info['shipping_duration'] = item.seller_rate_chart.shipping_duration
            item_info['sku'] = item.seller_rate_chart.sku
            item_info['gift'] = mark_safe(item.gift_title)   
            item_info['preOrder'] = False if item.seller_rate_chart.stock_status == 'instock' else True
            order_mrp_total += item.list_price
            order_discount += item.list_price - item.sale_price
            shipping_charges += item.shipping_charges
            order_payable_total += item.sale_price + item.shipping_charges 
            #refund = refund + item.sale_price + item.shipping_charges
            
            buyer_order_items.append(item_info)
            if seller and item.seller_rate_chart.seller == seller:
                seller_order_items.append(item_info)
                qty = item.qty
                seller_refund=seller_refund + item.sale_price + item.shipping_charges
        seller_name = 'Chaupaati.in'
        body_st['order_mrp_total'] = self.format_money(product.formatted_currency(), order_mrp_total)
        if order_discount>0:
            body_st['discount'] = self.format_money(product.formatted_currency(), order_discount)
        if shipping_charges>0:
            body_st['shipping_charges'] = self.format_money(product.formatted_currency(), shipping_charges)
        body_st['order_payable_total'] = self.format_money(product.formatted_currency(), order_payable_total)
        body_st['order_offer_price_total'] = self.format_money(product.formatted_currency(),order.total)
        body_st['refund'] = self.format_money(product.formatted_currency() , self.refund)
        body_st['seller_refund'] = self.format_money(product.formatted_currency() , seller_refund)

        if seller:
            body_st['shop_name'] = seller.name
            body_st['seller_total'] = self.format_money(product.formatted_currency(), seller_total_map[seller.id])
            body_st['seller_mrp_total'] = self.format_money(product.formatted_currency() , seller_mrp_map[seller.id])
            if seller_shipping_charges_map[seller.id]:
                body_st['seller_shipping_charges'] = self.format_money(product.formatted_currency() , seller_shipping_charges_map[seller.id])
            seller_discount = seller_discount_map[seller.id]
            body_st['is_seller_discount'] = True if seller_discount  else False
            body_st['seller_discount'] = self.format_money(product.formatted_currency(), seller_discount)
            seller_shipping_charges = seller_shipping_charges_map[seller.id]
            additional_discount = seller_mrp_map[seller.id] - seller_total_map[seller.id] - seller_discount_map[seller.id]
            if additional_discount > 0:
                body_st['seller_coupon_discount'] = self.format_money(product.formatted_currency(), additional_discount)
            if seller_discount > 0:
                body_st['seller_discount'] = self.format_money(product.formatted_currency(), seller_discount)
            if seller_shipping_charges > 0:
                body_st['seller_shipping_charges'] = self.format_money(product.formatted_currency(),seller_shipping_charges)


            if len(seller_products_map[seller.id]) > 1:
                body_st['seller_multiple_items'] = True
            else:
                body_st['seller_multiple_items'] = False

            body_st['ad_title'] = mark_safe(seller_products_map[seller.id][0].title)
            body_st['item_price'] = self.format_money(product.formatted_currency(), seller_total_map[seller.id])
            subject_st['item_price'] = self.format_money(product.formatted_currency() , seller_total_map[seller.id])

            body_st['qty'] = qty
        
        else:
            body_st['title'] = mark_safe(product.title)
            if len(seller_map) == 1:
                primary_seller = seller_map[self.order_items[0].seller_rate_chart.seller.id]
                if primary_seller:
                    seller_name = primary_seller.name
            subject_st['seller_name'] = seller_name

        body_st['buyer_items'] = buyer_order_items
        body_st['seller_items'] = seller_order_items
        subject_st['client_name'] = self.order.client.name
    
    def getNotifications(self):
        notifications = []
        buyer = self.order.user
#        order_items = OrderItem.objects.select_related('seller_rate_chart').filter(order=self.order, state='cancelled')

        product = self.order_items[0].seller_rate_chart.product
        qty = self.order_items[0].qty

        products_map = {}
        sellers_map = {}
        sellers_order_item_map = {}
        seller_total_map = {}
        seller_mrp_map = {}
        seller_discount_map = {}
        seller_shipping_charges_map = {}
        seller_product_map = {}
        seller_coupon_map = {}

        for item in self.order_items:
            seller = item.seller_rate_chart.seller
            seller_id = seller.id
            product = item.seller_rate_chart.product
            products_map[product.id] = product
            sellers_map[seller_id] = seller
            sellers_order_item_map[seller_id]  = 1
            if seller_id in seller_total_map:
                seller_total_map[seller_id] += (item.sale_price + item.shipping_charges)
            else:
                seller_total_map[seller_id] = (item.sale_price + item.shipping_charges)
            
            if seller_id in seller_shipping_charges_map:
                seller_shipping_charges_map[seller_id] += (item.shipping_charges)
            else:
                seller_shipping_charges_map[seller_id] = (item.shipping_charges)
            
            if seller_id in seller_mrp_map:
                seller_mrp_map[seller_id] += (item.list_price if item.list_price else item.sale_price)
            else:
                seller_mrp_map[seller_id] =  (item.list_price if item.list_price else item.sale_price)

            if seller_id in seller_discount_map:
                seller_discount_map[seller.id] += (item.list_price - item.sale_price)
            else:
                seller_discount_map[seller.id] = (item.list_price - item.sale_price)

            if seller_id in seller_product_map:
                seller_product_map[seller_id].append(product)
            else:
                seller_product_map[seller_id] = [product]

        buyer_st = {}
        subject_st = {}
        buyer_sms_st = {}
        subject_sms_st = {}

        self.fill_attributes(self.order, product, buyer_st, subject_st,\
            buyer, products_map, sellers_map, None, qty, seller_total_map, seller_product_map,\
            seller_coupon_map, seller_mrp_map, seller_discount_map, seller_shipping_charges_map)

        self.fill_attributes(self.order, product, buyer_sms_st, subject_sms_st,\
            buyer, products_map, sellers_map, None, qty, seller_total_map, seller_product_map,\
            seller_coupon_map, seller_mrp_map, seller_discount_map, seller_shipping_charges_map)

        t_body = get_template('order/buyer_cancelled_order.email')
        t_sub = get_template('order/buyer_cancelled_order_sub.email')
        ctxt_body = buyer_st
        c_body = Context(ctxt_body)
        ctxt_sub = subject_st
        c_sub = Context(ctxt_sub)

        email_sent_from = "%s<order@%s>" % (self.order.client.name, self.order.client.clientdomain_name)
        email_body = t_body.render(c_body)
        email_subject = t_sub.render(c_sub)
        if buyer.get_primary_emails():
            emails = ''
            for email in buyer.get_primary_emails():
                emails += email.email + ','
            emails = emails.strip(',')
            email_to = emails
            email_bcc = "customerservice@%s" % self.order.client.clientdomain_name
        else:
            email_to = "customerservice@%s" % self.order.client.clientdomain_name 
            email_bcc = ""

        bemail = CEmail()
        bemail._from = email_sent_from
        bemail.body =  email_body
        bemail.subject = email_subject
        bemail.isHtml = True
        bemail.to = email_to
        bemail.bcc = email_bcc
        email_log = LEmail(client_domain = self.request.client,
                          order = self.order,
                          profile = self.order.user,
                          sent_to = email_to[:999],
                          bccied_to = email_bcc,
                          sent_from = email_sent_from,
                          subject = email_subject,
                          body = email_body,
                          status = 'in_queue',
                          type = 'buyer_order_cancellation')
        email_log.save()
        bemail.email_log_id = email_log.id
        notifications.append(bemail)

        sms = SMS()
        t_sms_body = get_template('order/buyer_cancelled_order.sms')
        ctxt_sms_body = buyer_sms_st
        c_sms_body = Context(ctxt_sms_body)
        sms.text = t_sms_body.render(c_sms_body)
        sms.to = buyer.primary_phone
        sms.mask = self.order.client.sms_mask
        notifications.append(sms)
        
        for seller_id in sellers_map:
            current_seller = sellers_map[seller_id]
            seller_body = {}
            seller_sub = {}
            self.fill_attributes(self.order, product, seller_body,\
                seller_sub, buyer, products_map, sellers_map, current_seller, qty, seller_total_map,\
                seller_product_map, seller_coupon_map, seller_mrp_map, seller_discount_map, seller_shipping_charges_map)
            
            t_body = get_template('order/seller_cancelled_order.email')
            ctxt_body = seller_body
            c_body = Context(ctxt_body)
            t_sub = get_template('order/seller_cancelled_order_sub.email')
            ctxt_sub = seller_sub
            c_sub = Context(ctxt_sub)
            seller_emails = current_seller.get_confirmed_order_notification_email_addresses()

            email_sent_from = "%s<order@%s>" % (self.order.client.name, self.order.client.clientdomain_name) #self.order.client.pending_order_email
            email_body =  t_body.render(c_body)
            email_subject = t_sub.render(c_sub)
            email_bcc = ''
            if seller_emails:
                email_to = seller_emails
                email_bcc = "fulfillment@%s" % self.order.client.clientdomain_name
            else:
                email_to = "fulfillment@%s" % self.order.client.clientdomain_name

            semail = CEmail()
            semail._from = email_sent_from
            semail.body = email_body
            semail.subject = email_subject
            semail.to = email_to
            semail.isHtml = True
            semail.bcc = email_bcc

            email_log = LEmail(client_domain = self.request.client,
                          order = self.order,
                          profile = self.order.user,
                          sent_to = email_to[:999],
                          bccied_to = email_bcc,
                          sent_from = email_sent_from,
                          subject = email_subject,
                          body = email_body,
                          status = 'in_queue',
                          type = 'seller_order_cancellation')
            email_log.save()
            semail.email_log_id = email_log.id
            notifications.append(semail)
        
        return notifications
