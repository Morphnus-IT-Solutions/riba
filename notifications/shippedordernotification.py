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
from datetime import datetime, timedelta

class ShippedOrderNotification(Notification):
    def __init__(self, order, request, *args,**kwargs):
        self.order = order
        self.request = request
        self.shipment = kwargs.get('shipment')
    
    def format_money(self,currency,money):
        return '%s&nbsp;%s' % (currency,formatMoney(money))
    
    def get_payment_mode_string(self,payment_mode):
        return PAYMENT_MODE_STRINGS.get(payment_mode, "")
 
    def fill_attributes(self, order, product, body_st, subject_st,
        buyer, products_map, qty):
        from datetime import datetime
        body_st['order_id'] = order.get_id()
        subject_st['order_id'] = order.get_id()
        if buyer.full_name.strip():
            body_st['customer_name'] = buyer.full_name
        else:
            body_st['customer_name'] = 'Customer'
        body_st['customer_phone'] = buyer.get_primary_phones()[0].phone if buyer.get_primary_phones() else ''
        
        delivery_info = DeliveryInfo.objects.select_related('address').filter(order=order)
        if buyer.get_primary_emails():
            body_st['customer_email'] = buyer.get_primary_emails()[0].email
        body_st['qty'] = qty

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
        body_st['payment_mode_string'] = self.get_payment_mode_string(order.payment_mode)
        payment_option = PaymentOption.objects.get(client=order.client, payment_mode__code = order.payment_mode)
        body_st['payment_mode'] = payment_option.payment_mode
        body_st['payment_option'] = payment_option
        payments = order.get_payments(None).order_by('-id')[:1]
        if payments:
            payment = payments[0]
            body_st['gateway'] = payment.gateway

        body_st['helpline'] = self.order.client.confirmed_order_helpline
        body_st['signature'] = self.order.client.signature
        body_st['client'] = self.order.client
        if order.payment_realized_on:
            body_st['order_payment_date'] = datetime.date(order.payment_realized_on)
        body_st['client_domain'] = self.order.client.clientdomain_name
        delivery_info = delivery_info[0]
        body_st['delivery_info'] = delivery_info
        body_st['tracking_number'] = self.shipment.tracking_number
        body_st['pickedup_on'] = self.shipment.pickedup_on
        body_st['lsp'] = self.shipment.lsp.name

        try:
            gift_info = GiftInfo.objects.get(order=order)
            body_st['delivery_giftmessage'] = mark_safe(gift_info.notes)
            delivery_info_dict['delivery_giftmessage'] = mark_safe(gift_info.notes)
        except GiftInfo.DoesNotExist:
            pass
        buyer_order_items = []

        coupon = False
        coupon_code = 'coupon'

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
            item_info['price'] = self.format_money(item_product.formatted_currency() , item.sale_price/item.qty)
            item_info['offer_price'] = self.format_money(item_product.formatted_currency() , item.sale_price/item.qty)
            item_info['total_item_price'] = self.format_money(item_product.formatted_currency() , item.list_price)
            item_info['total_item_offer_price'] = self.format_money(item_product.formatted_currency() , item.sale_price)
            item_info['qty'] = item.qty

            item_info['sku'] = item.seller_rate_chart.sku
            item_info['gift'] = mark_safe(item.gift_title)   
            
            item_info['sr_no'] = count
            count += 1
            buyer_order_items.append(item_info)

        body_st['buyer_items'] = buyer_order_items
        subject_st['client_name'] = order.client.name

    
    def getNotifications(self):
        notifications = []
        buyer = self.order.user
        order_items = OrderItem.objects.select_related('seller_rate_chart').filter(order=self.order)
        product = order_items[0].seller_rate_chart.product
        qty = order_items[0].qty

        products_map = {}

        for item in order_items:
            seller = item.seller_rate_chart.seller
            seller_id = seller.id
            product = item.seller_rate_chart.product
            products_map[product.id] = product

        email_body_ctxt = {}
        email_subject_ctxt = {}
        sms_body_ctxt = {}
        sms_subject_ctxt = {}

        self.fill_attributes(self.order, product, email_body_ctxt, email_subject_ctxt,\
            buyer, products_map, qty)

        self.fill_attributes(self.order, product, sms_body_ctxt, sms_subject_ctxt,\
            buyer, products_map, qty)

        t_body = get_template('notifications/order/shipped_order.email')
        t_sub = get_template('notifications/order/shipped_order_sub.email')
        ctxt_body = email_body_ctxt
        c_body = Context(ctxt_body)
        ctxt_sub = email_subject_ctxt
        c_sub = Context(ctxt_sub)

        email_body = t_body.render(c_body)
        email_subject =  t_sub.render(c_sub)
        email_sent_from =  "%s<fulfillment@%s>" % (self.order.client.name, 
            self.order.client.clientdomain_name)
        email_bcc, email_to = '', ''

        if buyer.get_primary_emails():
            emails = ''
            for email in buyer.get_primary_emails():
                emails += email.email + ','
            email_to = emails.strip(',')
            email_bcc = "customerservice@%s" % self.order.client.clientdomain_name
        else:
            email_to = "customerservice@%s" % self.order.client.clientdomain_name
            email_bcc = ""

        bemail = NEmail()
        bemail.body = email_body
        bemail.subject = email_subject
        bemail.to = email_to
        bemail._from = email_sent_from
        bemail.bcc = email_bcc
        bemail.isHtml = True
        email_log = LEmail(client_domain = self.request.client,
                          order = self.order,
                          profile = self.order.user,
                          sent_to = email_to[:999],
                          bccied_to = email_bcc,
                          sent_from = email_sent_from,
                          subject = email_subject,
                          body = email_body,
                          status = 'in_queue',
                          type = 'shipped_order')
        email_log.save()
        bemail.email_log_id = email_log.id
        notifications.append(bemail)
        
        if buyer.get_primary_phones():
            sms = SMS()
            t_sms_body = get_template('notifications/order/shipped_order.sms')
            ctxt_sms_body = sms_body_ctxt
            c_sms_body = Context(ctxt_sms_body)
            sms.text = t_sms_body.render(c_sms_body)
            sms.to = buyer.get_primary_phones()[0].phone
            sms.mask = self.order.client.sms_mask
            notifications.append(sms)
        
        return notifications
