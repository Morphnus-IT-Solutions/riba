from notifications.notification import Notification
from notifications.email import Email as NEmail
from notifications.sms import SMS
from communications.models import Email as LEmail
from notifications import PAYMENT_MODE_STRINGS
from orders.models import  *
from catalog.models import *
from django.template import Context, Template
from django.template.loader import get_template
from utils.utils import *
from django.utils.safestring import mark_safe
from accounts.models import *
from datetime import datetime
import logging

log = logging.getLogger('request')

class PendingOrderNotification(Notification):
    source = 'web'
    def __init__(self,order,request,*args,**kwargs):
        self.order = order
        self.request = request
        if 'groups' in kwargs:
            self.groups = kwargs['groups']
    
    def format_money(self,currency,money):
        return '%s %s' % (currency,formatMoney(money))
    
    def get_payment_mode_string(self,payment_mode):
        return PAYMENT_MODE_STRINGS.get(payment_mode, "")

    def fill_attributes(self,order,order_item,product,body_st,subject_st,
        buyer,products_map,seller_map,seller,qty,seller_total_map,\
        seller_products_map,seller_coupon_map,seller_mrp_map, seller_offer_price_map,\
        seller_discount_map,seller_cashback_map,seller_shipping_charges_map):

        body_st['order_id'] = order.get_id()
        body_st['order'] = order
        subject_st['order_id'] = order.get_id()
        body_st['current_date'] = datetime.now().strftime('%dth %B %Y')
        body_st['order_book_date'] = order.booking_date()
        body_st['absolute_url'] = 'http://www.futurebazaar.com/' 
        if buyer.full_name.strip():
            body_st['customer_name'] = buyer.full_name
        else:
            body_st['customer_name'] = 'Customer'
        if buyer.get_primary_phones():
            body_st['customer_phone'] = buyer.get_primary_phones()[0].phone
        
        delivery_info = DeliveryInfo.objects.select_related('address').filter(order=order)
        if delivery_info:
            body_st['customer_delivery_city'] = delivery_info[0].address.city
        if buyer.get_primary_emails():
            body_st['customer_email'] = buyer.get_primary_emails()[0].email

        if not seller:
            body_st['qty'] = qty

        subject_st['ad_title'] = mark_safe(product.title)
        subject_st['item_price'] = self.format_money(product.formatted_currency() ,  order_item.sale_price)
        if not seller:
            body_st['item_price'] = self.format_money(product.formatted_currency() , order_item.sale_price)

        body_st['order_payable_total'] = self.format_money(product.formatted_currency() , order.payable_amount)
        if order.get_discount():
            body_st['discount'] = self.format_money(product.formatted_currency(), order.get_discount())
        if order.cashback_amount_total:
            body_st['cashback'] = self.format_money(product.formatted_currency(), order.cashback_amount_total)
        special_discount = order.coupon_discount
        is_coupon_discount = True
        discount = True

        if order.shipping_charges:
            body_st['order_shipping_charges'] = self.format_money(product.formatted_currency() , order.shipping_charges)
        if order.coupon_discount:
            body_st['special_discount'] = self.format_money(product.formatted_currency(),order.coupon_discount)
        body_st['order_mrp_total'] = self.format_money(product.formatted_currency(),order.list_price_total)
        body_st['order_offer_price_total'] = self.format_money(product.formatted_currency(),order.total)
        body_st['payment_mode_string'] = self.get_payment_mode_string(order.payment_mode)
        payment_option = PaymentOption.objects.get(payment_mode__code=order.payment_mode, client=order.client)
        body_st['payment_option'] = payment_option
        body_st['payment_mode'] = payment_option.payment_mode
        payments = order.get_payments(None).order_by('-id')[:1]
        if payments:
            payment = payments[0]
            body_st['gateway'] = payment.gateway

        body_st['helpline'] = self.order.client.pending_order_helpline
        body_st['signature'] = self.order.client.signature
        body_st['client'] = self.order.client

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

        order_items = order.get_order_items(None, exclude=dict(state__in=['cancelled',
            'bundle_item']))
        if len(order_items) > 1:
            body_st['multiple'] = True
        else:
            body_st['multiple'] = False
        count = 1
        for item in order_items:
            item_info = {}
            item_product = item.seller_rate_chart.product
            title = item.item_title
            item_info['title'] = mark_safe(title)
            item_info['seller'] = item.seller_rate_chart.seller.name
            item_info['price'] = self.format_money(item_product.formatted_currency() , item.list_price/item.qty)
            item_info['offer_price'] = self.format_money(item_product.formatted_currency() , item.sale_price/item.qty)
            item_info['total_item_price'] = self.format_money(item_product.formatted_currency() , item.list_price)
            item_info['total_item_offer_price'] = self.format_money(item_product.formatted_currency() , item.sale_price)
            item_info['qty'] = item.qty
            #item_info['shipping_duration'] = item.seller_rate_chart.shipping_duration
            #diff = order.booking_timestamp - item.expected_delivery_date
            item_info['delivery_days'] = item.delivery_days
            item_info['sku'] = item.seller_rate_chart.sku
            item_info['preOrder'] = False if item.seller_rate_chart.stock_status == 'instock' else True
            item_info['gift'] = mark_safe(item.gift_title)
            item_info['sr_no'] = count
            dc = item.inventorydclspresolution_set.select_related('dc').order_by('-created_on')
            item_info['fulfillment_dc'] = dc[0].dc.name if dc else ''
            count += 1
            buyer_order_items.append(item_info)
            if seller and item.seller_rate_chart.seller == seller:
                seller_order_items.append(item_info)
                qty = item.qty
        seller_name = 'Chaupaati.in'
        if seller:
            body_st['shop_name'] = seller.name
            body_st['seller_total'] = self.format_money(product.formatted_currency(), seller_total_map[seller.id])
            body_st['seller_mrp_total'] = self.format_money(product.formatted_currency() , seller_mrp_map[seller.id])
            body_st['seller_offer_price_total'] = self.format_money(product.formatted_currency() , seller_offer_price_map[seller.id])
            if seller_shipping_charges_map[seller.id]:
                body_st['seller_shipping_charges'] = self.format_money(product.formatted_currency() , seller_shipping_charges_map[seller.id])
            seller_discount = seller_discount_map[seller.id]
            body_st['is_seller_discount'] = True if seller_discount  else False
            body_st['seller_discount'] = self.format_money(product.formatted_currency(), seller_discount)
            seller_cashback = seller_cashback_map[seller.id]
            body_st['is_seller_cashback'] = True if seller_cashback  else False
            body_st['seller_cashback'] = self.format_money(product.formatted_currency(), seller_cashback)
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
                primary_seller = seller_map[order_items[0].seller_rate_chart.seller.id]
                if primary_seller:
                    seller_name = primary_seller.name
            subject_st['seller_name'] = seller_name

        body_st['buyer_items'] = buyer_order_items
        body_st['seller_items'] = seller_order_items
        subject_st['client_name'] = self.order.client.name
    
    def getNotifications(self):
        notifications = []
        buyer = self.order.user
        #if self.order.payment_mode in ['cash-at-store', 'card-at-store']:
            # Skip notifications for cash and card at store now
            # Might need to reenable them. Need to move this
            # checking to domain payment options.
        #    return []
        order_items = OrderItem.objects.select_related('seller_rate_chart').filter(order=self.order)
        product = order_items[0].seller_rate_chart.product
        qty = order_items[0].qty

        products_map = {}
        sellers_map = {}
        sellers_order_item_map = {}
        seller_total_map = {}
        seller_mrp_map = {}
        seller_offer_price_map = {}
        seller_discount_map = {}
        seller_cashback_map ={}
        seller_shipping_charges_map = {}
        seller_product_map = {}
        seller_coupon_map = {}
        for item in order_items:
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
            if seller_id in seller_offer_price_map:
                seller_offer_price_map[seller_id] += item.sale_price
            else:
                seller_offer_price_map[seller_id] =  item.sale_price
            if seller_id in seller_discount_map:
                seller_discount_map[seller.id] += (item.list_price - item.sale_price)
            else:
                seller_discount_map[seller.id] = (item.list_price - item.sale_price)

            if seller_id in seller_cashback_map:
                seller_cashback_map[seller.id] += item.cashback_amount
            else:
                seller_cashback_map[seller.id] = item.cashback_amount
                
            if seller_id in seller_product_map:
                seller_product_map[seller_id].append(product)
            else:
                seller_product_map[seller_id] = [product]
            


        buyer_st = {}
        subject_st = {}
        buyer_sms_st = {}
        subject_sms_st = {}

        self.fill_attributes(self.order, order_items[0], product, buyer_st, subject_st,\
            buyer, products_map, sellers_map, None, qty, seller_total_map, seller_product_map,\
            seller_coupon_map, seller_mrp_map, seller_offer_price_map, seller_discount_map, seller_cashback_map, seller_shipping_charges_map)

        self.fill_attributes(self.order, order_items[0], product, buyer_sms_st, subject_sms_st,\
            buyer, products_map, sellers_map, None, qty, seller_total_map, seller_product_map,\
            seller_coupon_map, seller_mrp_map, seller_offer_price_map, seller_discount_map, seller_cashback_map, seller_shipping_charges_map)

        t_body = get_template('notifications/order/buyer_pending_order.email')
        t_sub = get_template('notifications/order/buyer_pending_order_sub.email')
        ctxt_body = buyer_st
        ctxt_body['clientdomain_name'] = 'www.%s' % self.order.client.clientdomain_name
        c_body = Context(ctxt_body)
        ctxt_sub = subject_st
        c_sub = Context(ctxt_sub)
        log.info('emails %s' % buyer.get_primary_emails())

        email_sent_from =  "%s<lead@%s>" % (self.order.client.name,
            self.order.client.clientdomain_name)
        email_body = t_body.render(c_body)
        email_subject = t_sub.render(c_sub)
        if buyer.get_primary_emails():
            emails = ''
            for email in buyer.get_primary_emails():
                emails += email.email + ','
            emails = emails.strip(',')
            email_to = emails
            log.info('to%s' % email_to)
            email_bcc = "presales@%s" % self.order.client.clientdomain_name
        else:
            email_to = "presales@%s" % self.order.client.clientdomain_name
            email_bcc = ''

        bemail = NEmail()
        bemail._from = email_sent_from
        bemail.body =  email_body
        bemail.subject = email_subject
        bemail.isHtml = True
        bemail.to = email_to
        bemail.bcc = email_bcc
        email_to = email_to[:1000] 
        email_log = LEmail(client_domain = self.request.client,
                          order = self.order,
                          profile = self.order.user,
                          sent_to = email_to[:999],
                          bccied_to = email_bcc,
                          sent_from = email_sent_from,
                          subject = email_subject,
                          body = email_body,
                          status = 'in_queue',
                          type = 'buyer_pending_order')
        email_log.save()
        bemail.email_log_id = email_log.id

        if 'buyer' in self.groups:
            notifications.append(bemail)
#        elif 'admin' in self.groups:
#            bemail.to = "presales@%s" % self.order.client.clientdomain_name
#            notifications.append(bemail)

        if 'buyer' in self.groups:
            if buyer.get_primary_phones():
                bsms = SMS()
                t_sms_body = get_template('notifications/order/buyer_pending_order.sms')
                ctxt_sms_body = buyer_sms_st
                c_sms_body = Context(ctxt_sms_body)
                bsms.text = t_sms_body.render(c_sms_body)
                bsms.to = buyer.get_primary_phones()[0].phone
                bsms.mask = self.order.client.sms_mask
                notifications.append(bsms)

        for seller_id in sellers_map:
            current_seller = sellers_map[seller_id]
            seller_body = {}
            seller_sub = {}
            self.fill_attributes(self.order, order_items[0], product, seller_body,\
                seller_sub, buyer, products_map, sellers_map, current_seller, qty, seller_total_map,\
                seller_product_map, seller_coupon_map, seller_mrp_map, seller_offer_price_map, seller_discount_map, seller_cashback_map, seller_shipping_charges_map)
            
            t_body = get_template('notifications/order/seller_pending_order.email')
            ctxt_body = seller_body
            c_body = Context(ctxt_body)
            t_sub = get_template('notifications/order/seller_pending_order_sub.email')
            ctxt_sub = seller_sub
            c_sub = Context(ctxt_sub)
            seller_emails = current_seller.get_pending_order_notification_email_addresses()

            email_sent_from = "%s<lead@%s>" % (self.order.client.name,
                self.order.client.clientdomain_name)
            email_body =  t_body.render(c_body)
            email_subject = t_sub.render(c_sub)
            email_bcc = '' 
            if seller_emails:
                email_to = seller_emails
                email_bcc = "fulfillment@%s" % self.order.client.clientdomain_name
            else:
                email_to = "fulfillment@%s" % self.order.client.clientdomain_name

            semail = NEmail()
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
                          type = 'seller_pending_order')
            email_log.save()
            semail.email_log_id = email_log.id

            if 'seller' in self.groups:
                notifications.append(semail)
#            elif 'admin' in self.groups:
#                notifications.append(semail)
                
        return notifications
