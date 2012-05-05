from notifications.notification import Notification
from notifications.email import Email
from notifications.sms import SMS
from orders.models import  *
from catalog.models import *
from django.template import Context, Template
from django.template.loader import get_template
from datetime import datetime
from utils.utils import *

class SellerOrderNotification(Notification):
    source = 'web'
    def __init__(self,order,*args,**kwargs):
        self.order = order
        if 'groups' in kwargs:
            self.groups = kwargs['groups']
    
    def format_money(self,currency,money):
        return '%s %s' % (currency,formatMoney(money))
    
    def get_payment_mode_string(self,payment_mode):
        map = {'card-web':'Web',
            'card-moto':'Phone',
            'card-ivr':'Phone',
            'deposit-hdfc':'Deposit',
            'deposit-icici':'Deposit',
            'deposit-axis':'Deposit',
            'transfer-hdfc':'Deposit',
            'transfer-icici':'Deposit',
            'transfer-axis':'Deposit',
            'mail':'Mail',
            'cod':'COD'}
        return map[payment_mode]
 
    def fill_attributes(self,order,product,body_st,subject_st,
        buyer,products_map,seller_map,seller,qty,seller_total_map,\
        seller_products_map,seller_coupon_map,seller_mrp_map,\
        seller_discount_map,seller_shipping_charges_map):

        body_st['order_id'] = order.id
        subject_st['order_id'] = order.id
        body_st['customer_name'] = buyer.full_name
        body_st['customer_phone'] = buyer.primary_phone
        
        delivery_info = DeliveryInfo.objects.select_related('address').filter(order=order)
        if delivery_info:
            body_st['customer_delivery_city'] = delivery_info[0].address.city
        if buyer.primary_email:
            body_st['customer_email'] = buyer.primary_email
        if not seller:
            body_st['qty'] = qty

        subject_st['ad_title'] = product.title

        body_st['order_payable_total'] = self.format_money(product.formatted_currency() , order.payable_amount)
        if order.get_discount():
            body_st['discount'] = self.format_money(product.formatted_currency(), order.get_discount())
        special_discount = order.coupon_discount
        is_coupon_discount = True
        discount = True
        if order.shipping_charges:
            body_st['order_shipping_charges'] = self.format_money(product.formatted_currency() , order.shipping_charges)
        if order.coupon_discount:
            body_st['special_discount'] = self.format_money(product.formatted_currency(),order.coupon_discount)
        body_st['order_mrp_total'] = self.format_money(product.formatted_currency(),order.list_price_total)
        body_st['payment_mode_string'] = self.get_payment_mode_string(order.payment_realized_mode)
        body_st['payment_mode'] = order.payment_realized_mode
        body_st['order_payment_date'] = datetime.date(order.payment_realized_on)
       
        delivery_info_dict = {}
        delivery_info = delivery_info[0]
        if delivery_info:
            if delivery_info.address and delivery_info.address.name: 
                body_st['delivery_name'] = delivery_info.address.name
                delivery_info_dict['delivery_name'] = delivery_info.address.name
            else:
                body_st['delivery_name'] = delivery_info.address.name or ''
                delivery_info_dict['delivery_name'] = delivery_info.address.name or ''
            body_st['delivery_address']  = delivery_info.address.address.strip()
            delivery_info_dict['delivery_address'] = delivery_info.address.address.strip()
            body_st['delivery_city'] = delivery_info.address.city
            delivery_info_dict['delivery_city'] = delivery_info.address.city
            body_st['delivery_country'] = delivery_info.address.country
            delivery_info_dict['delivery_country'] = delivery_info.address.country
            body_st['delivery_pincode'] = delivery_info.address.pincode
            delivery_info_dict['delivery_pincode'] = delivery_info.address.pincode
            body_st['delivery_notes'] = delivery_info.notes
            delivery_info_dict['delivery_notes'] = delivery_info.notes
            body_st['delivery_state'] = delivery_info.address.state
            delivery_info_dict['delivery_state'] = delivery_info.address.state
            if delivery_info.address and delivery_info.address.phone:
                body_st['delivery_phone'] = delivery_info.address.phone
                delivery_info_dict['delivery_phone'] = delivery_info.address.phone
            else:
                body_st['delivery_phone'] = ''
                delivery_info_dict['delivery_phone'] = ''
        try:
            gift_info = GiftInfo.objects.get(order=order)
            body_st['delivery_giftmessage'] = gift_info.notes
            delivery_info_dict['delivery_giftmessage'] = gift_info.notes
        except GiftInfo.DoesNotExist:
            pass
        body_st['delivery_info'] = delivery_info_dict
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

        order_items = OrderItem.objects.select_related('seller_rate_chart').filter(order=order)
        if len(order_items) > 1:
            body_st['multiple'] = True
        else:
            body_st['multiple'] = False
        for item in order_items:
            item_info = {}
            item_product = item.seller_rate_chart.product
            title = item.item_title
            item_info['title'] = title
            item_info['seller'] = item.seller_rate_chart.seller.name
            item_info['price'] = self.format_money(item_product.formatted_currency() , item.list_price)
            item_info['qty'] = item.qty
            item_info['shipping_duration'] = item.seller_rate_chart.shipping_duration
            item_info['sku'] = item.seller_rate_chart.sku
            item_info['gift'] = item.gift_title   
            item_info['preOrder'] = False if item.seller_rate_chart.stock_status == 'instock' else True
            
            buyer_order_items.append(item_info)
            if seller and item.seller_rate_chart.seller == seller:
                seller_order_items.append(item_info)
                qty = item.qty

        seller_name = 'Chaupaati.in'

        if seller:
            body_st['shop_name'] = seller.name
            body_st['seller_total'] = self.format_money(product.formatted_currency(), seller_total_map[seller.id])
            body_st['seller_mrp_total'] = self.format_money(product.formatted_currency() , seller_mrp_map[seller.id])
            seller_discount = seller_discount_map[seller.id]
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

            body_st['ad_title'] = seller_products_map[seller.id][0].title
            body_st['item_price'] = self.format_money(product.formatted_currency(), seller_total_map[seller.id])
            subject_st['item_price'] = self.format_money(product.formatted_currency() , seller_total_map[seller.id])

            body_st['qty'] = qty
        
        else:
            body_st['title'] = product.title
            if len(seller_map) == 1:
                primary_seller = seller_map[order_items[0].seller_rate_chart.seller.id]
                if primary_seller:
                    seller_name = primary_seller.name
            subject_st['seller_name'] = seller_name

        body_st['buyer_items'] = buyer_order_items
        body_st['seller_items'] = seller_order_items

    
    def getNotifications(self):
        notifications = []
        buyer = self.order.user
        order_items = OrderItem.objects.select_related('seller_rate_chart').filter(order=self.order)
        product = order_items[0].seller_rate_chart.product
        qty = order_items[0].qty

        products_map = {}
        sellers_map = {}
        sellers_order_item_map = {}
        seller_total_map = {}
        seller_mrp_map = {}
        seller_discount_map = {}
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

            if seller_id in seller_discount_map:
                seller_discount_map[seller_id] += (item.list_price - item.sale_price)
            else:
                seller_discount_map[seller_id] = (item.list_price - item.sale_price)
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

        
        for seller_id in sellers_map:
            current_seller = sellers_map[seller_id]
            seller_body = {}
            seller_sub = {}
            self.fill_attributes(self.order, product, seller_body,\
                seller_sub, buyer, products_map, sellers_map, current_seller, qty, seller_total_map,\
                seller_product_map, seller_coupon_map, seller_mrp_map, seller_discount_map, seller_shipping_charges_map)
            
            t_body = get_template('order/seller_confirmed_order.email')
            ctxt_body = seller_body
            seller_sub['client_name'] = self.order.client.name
            c_body = Context(ctxt_body)
            t_sub = get_template('order/seller_confirmed_order_sub.email')
            ctxt_sub = seller_sub
            c_sub = Context(ctxt_sub)
            seller_emails = current_seller.get_confirmed_order_notification_email_addresses()
            tmp_emails = seller_emails.split(',')[1:]
            seller_emails = ','.join(email for email in tmp_emails)
            if seller_emails:
                email = Email()
                email.body = t_body.render(c_body)
                email.subject = t_sub.render(c_sub)
                email.to = seller_emails
                email.bcc = "customerservice@chaupaati.in"
                email._from = "Chaupaati Bazaar<order@chaupaati.com>"
                notifications.append(email)
            else:
                email = Email()
                email.body = t_body.render(c_body)
                email.subject = t_sub.render(c_sub)
                email.to = "customerservice@chaupaati.in"
                email._from = "Chaupaati Bazaar<order@chaupaati.com>"
                notifications.append(email)
        
        return notifications
