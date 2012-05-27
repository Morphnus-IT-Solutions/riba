from utils import utils
from users.models import Email as UserEmail
from users.models import Phone
from integrations.fbapi import users, orders, fbapiutils
from catalog.models import SellerRateChart
from accounts.models import Account,PaymentMode,PaymentOption
from orders.models import Order, OrderItem, BillingInfo
from decimal import Decimal
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
import time
from integrations.fbapi.stringcookiejar import StringCookieJar
from datetime import datetime, timedelta
import re
import logging
from django.utils import simplejson
from restapi import APIManager

log = logging.getLogger('fborder')

class SessionExpired(Exception):
    pass

class PriceMismatchException(Exception):
    pass

class CreateUserFailed(Exception):
    pass

class CancelOrderFailed(Exception):
    pass

class ConfirmOrderFailed(Exception):
    pass

class FuturebazaarAPI:
    cookie_file = None
    fb_user = None
    is_cart_synced = False
    add_to_cart_response = {}
    submit_cart_response = {}
    promotions_into_effect = {}
    coupons_into_effect = {}

    def __init__(self,request,profile,cart):
        log.debug('Initializing futurebazaar api')
        cs = utils.get_session_obj(request)
        if 'fbapiobj' in cs:
            old_fbapi = cs['fbapiobj']
            fbapiutils.logoff(old_fbapi.cookie_file, request)

        #initialize api
        cookie_file = fbapiutils.init(request)
        self.cookie_file = cookie_file
        PHONE_RE = re.compile('\d{10}')

        cs = utils.get_session_obj(request)
        #get or create user 
        username = profile.user.username
        try:
            username = cs['atg_username']
        except:
            log.exception('SESSION_EXPIRED: atg_username not found in request.session in API init.')
            raise SessionExpired('Your session expired. Please start again')
        agent = utils.get_agent_for_fb_api(request)
        fb_user = users.get_user_by_mobile(username, agent, self.cookie_file, request)
        self.record_last_request(request)
        self.fb_user = fb_user
        cs['fbapiobj'] = self
        utils.set_session_obj(request,cs)
        if fb_user['responseCode'] == fbapiutils.ERROR:
            log.error('Error fetching user %s:%s ' % (username, fb_user))
            self.fb_user = None
            cs = utils.get_session_obj(request)
            cs['fbapiobj'] = self
            utils.set_session_obj(request,cs)
            raise Exception('Error fetching user %s:%s' % (username, fb_user))
    
        if fb_user['responseCode'] == fbapiutils.USER_NOT_FOUND:
            log.info('User %s not found in atg' % username)
            phone = ''
            email = username
            if PHONE_RE.match(username):
                phone = username
                email = ''
            # atg creates user based on phone or email. phone takes precedence
            fb_user = users.create_user(phone, email, agent, self.cookie_file, request)
            if fb_user['responseCode'] == 'UM_CREATE_USER_FAILED':
                raise CreateUserFailed(fb_user['responseMessage'])
            self.fb_user = fb_user
            cs = utils.get_session_obj(request)
            cs['fbapiobj'] = self
            utils.set_session_obj(request,cs)
            log.info('New user %s created' % username)
            log.info('%s' % fb_user)
        if fb_user['responseCode'] == fbapiutils.USER_FOUND:
            log.info('User %s found in atg' % username)
            log.info('%s' % fb_user)
            fb_user_info = fb_user['items'][0]
            if fb_user_info['firstName'] and (not profile.full_name):
                profile.full_name =  '%s %s' % (fb_user_info['firstName'],fb_user_info['lastName'])
            primary_email = fb_user_info['email'] if fb_user_info['email'] else None
            primary_phone = fb_user_info['mobileNumber'] if fb_user_info['mobileNumber'] else None
            if primary_phone:
                phones = Phone.objects.filter(user=profile,phone=primary_phone)
                if not phones:
                    try:
                        phone = Phone(user=profile,type='primary',phone=primary_phone)
                        phone.save()
                    except:
                        pass
            if primary_email:
                emails = UserEmail.objects.filter(user=profile,email=primary_email)
                if not emails:
                    try:
                        emails = UserEmail(user=profile,type='primary',email=primary_email)
                        emails.save()
                    except:
                        pass
            
            profile.save()
            log.info('%s' % request.POST)
            #if 'next' in request.POST:   
            #    self.is_cart_synced = False 
            #    self.sync_cart(request,cart)
            

            #update user's Address
            from locations.models import Address
            try:
                user_address = Address(type='billing',profile=profile)
            except Address.DoesNotExist:
                user_address = Address()
            user_address.address = fb_user_info['billingInfo']['address1']
            user_address.pincode = fb_user_info['billingInfo']['postalCode']
            user_address.country = utils.get_or_create_country('India')
            state_map = fbapiutils.STATES_MAP
                
            reverse_map = {}
            for state in state_map:
                reverse_map[state_map[state]] = state
            if fb_user_info['billingInfo']['state']:
                if fb_user_info['billingInfo']['state'] not in reverse_map:
                    state_name = 'Andaman and Nicobar'
                else:
                    state_name = reverse_map[fb_user_info['billingInfo']['state']]
                user_address.state = utils.get_or_create_state(state_name,user_address.country)
            if fb_user_info['billingInfo']['city']:
                if user_address.state:
                    state = user_address.state
                else:
                    state = None
                user_address.city = utils.get_or_create_city(fb_user_info['billingInfo']['city'],state)
            user_address.type = 'billing'
            user_address.profile = profile
            user_address.save()
            
        cs['profile'] = profile
        utils.set_session_obj(request,cs)

    def get_cart(self, request):
        self.check_atg_session(request)
        user_agent = utils.get_agent_for_fb_api(request)
        fb_cart = orders.get_cart(user_agent,self.cookie_file,'9870696051',self.fb_user['items'][0]['profileId'],request)
        self.record_last_request(request)
        return fb_cart
   
    def sync_cart_before_submit(self, request, pending_order):
        user_agent = utils.get_agent_for_fb_api(request)
        fb_cart = self.get_cart(request)
        self.add_to_cart_response = fb_cart
        #fb_cart = orders.get_cart(user_agent,self.cookie_file,'9870696051',self.fb_user['items'][0]['profileId'],request)
        self.check_profileid(fb_cart)
        fb_order_id = fb_cart['items'][0]['orderId']
        if fb_order_id != pending_order.reference_order_id:
            log.info('ORDER_ID_CHANGED_BEFORE_SUBMIT_CART: from %s to %s' % (pending_order.reference_order_id,fb_order_id))
            log.info('ORDER_ID_CHANGED_BEFORE_SUBMIT_CART: Tinla order: %s, ATG Order: %s' % (pending_order.get_order_info(), fb_cart))
        fb_items = {}
        tinla_items = {}
        for item in pending_order.orderitem_set.iterator():
            tinla_items[str(item.seller_rate_chart.sku)] = item
        if fb_cart['items']:
            for f_item in fb_cart['items'][0]['items']:
                fb_items[str(f_item['skuId'])] = f_item
        if not fb_items and not tinla_items:
            log.exception('NO_ITEM_IN_CART_BEFORE_SUBMIT_CART: %s' % pending_order.id)
        if not fb_items:
            log.info('DID_NOT_FIND_ANY_ITEM_IN_ATG_CART before submit: %s' % pending_order.id)
            for item in pending_order.orderitem_set.iterator():
                response = orders.add_to_cart(item.seller_rate_chart.sku, item.seller_rate_chart.external_product_id, item.qty,'nilesh',self.fb_user['items'][0]['profileId'],self.cookie_file,request)
                self.check_profileid(response)
                if response['responseCode'] == 'OM_ADDED_ITEM_TO_CART':
                    self.add_to_cart_response = response
                    self.promotions_into_effect = self.add_to_cart_response['items'][0]['globalPromotions']
                    self.coupons_into_effect = self.add_to_cart_response['items'][0]['couponsAttachedToOrder']
                elif response['responseCode'] == 'GN_UNKNOWN_ERROR':
                    log.error('Error adding item to cart %s: %s' % (rate_chart.sku, response))
                    raise Exception('Unable to add item %s to cart' % rate_chart.sku)
                else:
                    self.add_to_cart_response['responseMessage'] = response['responseMessage']
                    self.add_to_cart_response['responseCode'] = response['responseCode']
        #Find the Delta Between two carts, at this point, the source of truth is Tinla Cart
        # First we will remove the items from atg cart which are not in tinla cart
        for sku in fb_items:
            if sku not in tinla_items:
                log.error("In atg not in tinla. Order: %s, Sku: %s" % (fb_order_id,
                    sku))
                row = fb_items[sku]
                response = orders.remove_from_cart(row['commerceItemId'], 
                    row['productId'], user_agent,
                    self.fb_user['items'][0]['profileId'],self.cookie_file,
                    request)
                self.check_profileid(response)
                if response['responseCode'] == 'OM_REMOVED_ITEM_FROM_CART':
                    self.add_to_cart_response = response
                    self.promotions_into_effect = self.add_to_cart_response['items'][0]['globalPromotions']
                    self.coupons_into_effect = self.add_to_cart_response['items'][0]['couponsAttachedToOrder']
                elif response['responseCode'] == 'GN_UNKNOWN_ERROR':
                    log.error('Error removing item from cart to sync')
                    raise Exception('Unable to remove item %s to cart.' % sku)
                else:
                    self.add_to_cart_response['responseMessage'] = response['responseMessage']
                    self.add_to_cart_response['responseCode'] = response['responseCode']
                

        # Now we will add the items to atg cart which are in tinla cart and not in atg cart
        log.info('fb_items %s, tinla_items %s' % (fb_items, tinla_items))
        for sku in tinla_items:
            if sku not in fb_items: 
                response = self.add_item_to_fb_cart(request, pending_order, tinla_items[sku].seller_rate_chart, tinla_items[sku].qty)
                if response['responseCode'] == 'OM_ADDED_ITEM_TO_CART':
                    self.add_to_cart_response = response
                    self.promotions_into_effect = self.add_to_cart_response['items'][0]['globalPromotions']
                    self.coupons_into_effect = self.add_to_cart_response['items'][0]['couponsAttachedToOrder']
                elif response['responseCode'] == 'GN_UNKNOWN_ERROR':
                    log.error('Error adding item to cart %s: %s' % (sku, response))
                    raise Exception('Unable to add item %s to cart' % sku)
                else:
                    self.add_to_cart_response['responseMessage'] = response['responseMessage']
                    self.add_to_cart_response['responseCode'] = response['responseCode']
            elif int(tinla_items[sku].qty) != int(fb_items[str(sku)]['qty']):
                log.info("Fixing qty mismatch for order %s" % pending_order.reference_order_id)
                self.update_item_quantity(request, pending_order, tinla_items[sku])
        log.info('addtocart response  %s' % self.add_to_cart_response)
        atg_order_amount = Decimal(str(self.add_to_cart_response['items'][0]['orderAmount']))
        diff = pending_order.payable_amount - atg_order_amount
        if not (diff >= Decimal('-1.00')  and diff <= Decimal('1.00')):
        #if str(pending_order.payable_amount) != self.add_to_cart_response['items'][0]['orderAmount']:
            # Try to recover from slot price mismatches
            recovered = False
            for sku in tinla_items:
                try:
                    remove_response = self.remove_item_from_cart(request,
                        pending_order, tinla_items[sku])
                    add_response = self.add_item_to_fb_cart(request, pending_order,
                        tinla_items[sku].seller_rate_chart, tinla_items[sku].qty)
                    if add_response['responseCode'] == 'OM_ADDED_ITEM_TO_CART':
                        self.add_to_cart_response = add_response
                        self.promotions_into_effect = self.add_to_cart_response['items'][0]['globalPromotions']
                        self.coupons_into_effect = self.add_to_cart_response['items'][0]['couponsAttachedToOrder']
                    elif add_response['responseCode'] == 'GN_UNKNOWN_ERROR':
                        log.error('Error adding item to cart in recovering price mismatch %s: %s' % (sku,
                            add_response))
                        raise Exception('Unable to add item %s to cart' % sku)
                    else:
                        self.add_to_cart_response['responseMessage'] = add_response['responseMessage']
                        self.add_to_cart_response['responseCode'] = add_response['responseCode']
                    atg_order_amount_after_recovery = Decimal(str(self.add_to_cart_response['items'][0]['orderAmount']))
                    diff_after_recover = pending_order.payable_amount - atg_order_amount_after_recovery
                    atg_order_amount = atg_order_amount_after_recovery
                    if atg_order_amount < Decimal('1.00'):
                        # Hack to avoid divide by zero execeptions
                        atg_order_amount = Decimal('1.00')
                    diff = diff_after_recover
                    if not (diff_after_recover >= Decimal('-1.00')  and diff_after_recover <= Decimal('1.00')):
                        recovered = False
                    else:
                        recovered = True
                except Exception, e:
                    log.exception('Error recovering from price mismatch %s' % repr(e))
                break
            if not recovered:
                log.exception("PRICE_MISMATCH_BEFORE_SUBMIT_CART: Tinla Cart %s, Amount %s, ATG Cart %s, Amount %s" % (pending_order.id,pending_order.payable_amount, self.add_to_cart_response['items'][0]['orderId'], self.add_to_cart_response['items'][0]['orderAmount']))
                log.exception("PRICE_MISMATCH_BEFORE_SUBMIT_CART: Tinla Cart %s, ATG Cart %s" % (pending_order.get_order_info(),
                    self.add_to_cart_response))

            # Always fail if difference is too large
            try:
                if abs(diff) > Decimal('1000') or abs(diff/atg_order_amount_after_recovery) > Decimal('0.5'):
                    log.exception("PRICE_MISMATCH_BEFORE_SUBMIT_CART: Failing as delta is too large. Tinla Cart %s, Amount %s, ATG Cart %s, Amount %s" % (pending_order.id,pending_order.payable_amount, self.add_to_cart_response['items'][0]['orderId'], self.add_to_cart_response['items'][0]['orderAmount']))
                    raise PriceMismatchException('Price Did not match before submit cart')
            except ZeroDivisionError, e:
                log.exception(" Dividing by zero %s" % repr(e))
                raise PriceMismatchException('Price Did not match before submit cart: Atg amount is Zero')
                

    def sync_cart_for_checkout(self,request,temp_cart, cart):
        # 1. Fetch ATG Cart
        # 2. Clear Tinla Cart (order.state='cart')
        # 3. Add ATG Cart items to Tinla Cart
        #    ---If failed to add item to Tinla Cart (Could happen if sku not found in Tinla):
        #     --------Remove the same item(sku) from ATG Cart
        # 4. Add temp_cart items to ATG Cart : if failed remove it from temp_cart as well
        redirect_to_mycart = True
        add_to_cart_errors = []
        user_agent = utils.get_agent_for_fb_api(request)
        if utils.is_future_ecom(request.client.client):
            # 1. Fetch ATG Cart
            log.info('Getting cart...')
            fb_cart = self.get_cart(request)
            #fb_cart = orders.get_cart(user_agent,self.cookie_file,'9870696051',self.fb_user['items'][0]['profileId'], request)
            self.check_profileid(fb_cart)
            self.add_to_cart_response = fb_cart

            cs = utils.get_session_obj(request)
            cs['fbapiobj'] = self
            utils.set_session_obj(request,cs)
            log.info('FB cart %s' % fb_cart)
            if fb_cart['items']:
                # 2. Clear Tinla Cart (order.state='cart')
                # log the state of Tinla Cart Before clear
                cart.clear_items(request)
                log.info('%s' % cart.get_item_count())

                self.promotions_into_effect = fb_cart['items'][0]['globalPromotions']
                self.coupons_into_effect = fb_cart['items'][0]['couponsAttachedToOrder']
                fb_cart_items = fb_cart['items'][0]
                # 3. Add ATG Cart items to Tinla Cart
                for f_item in fb_cart_items['items']:
                    try:
                        #seller = Account.objects.get(name=utils.FECOM_SELLERS[request.client.domain])
                        src = SellerRateChart.objects.get(sku=f_item['skuId'],seller__client = request.client.client)
                        oi = OrderItem(qty=0)
                        oi.order = cart
                        oi.seller_rate_chart = src
                        oi.item_title = src.product.title
                        oi.gift_title = src.gift_title
                        oi.qty = f_item['qty']
                        oi.list_price = src.list_price * f_item['qty']  #Get list price from ATG Cart
                        oi.sale_price = src.offer_price * f_item['qty'] #Get offer price from ATG Cart
                        oi.shipping_charges = src.shipping_charges * f_item['qty']
                        oi.save()
                        cart.remove_or_preserve_coupon(request, 'add_item', oi)
                        cart.update_blling(request)
                    except SellerRateChart.DoesNotExist:
                        #Remove item from fb cart
                        log.exception('Seller Rate Chart Not Found %s' % f_item['skuId'])
                        response = orders.remove_from_cart(f_item['commerceItemId'],f_item['productId'],user_agent,
                            self.fb_user['items'][0]['profileId'],self.cookie_file, request)
                        self.add_to_cart_response = response
                        self.promotions_into_effect = response['items'][0]['globalPromotions']
                        self.coupons_into_effect = response['items'][0]['couponsAttachedToOrder']
                        cs = utils.get_session_obj(request)
                        cs['fbapiobj'] = self
                        utils.set_session_obj(request,cs)
                # 4. Add temp_cart items to ATG Cart & Tinla Cart: if failed remove it from temp_cart as well
                for item in temp_cart.orderitem_set.iterator():
                    resp = self.add_item_to_fb_cart(request, cart, item.seller_rate_chart,item.qty)
                    if resp['responseCode'] != 'OM_ADDED_ITEM_TO_CART':
                        add_to_cart_errors.append(resp)
                    else:
                        cart.reference_order_id = resp['items'][0]['orderId']
                        cart.save()
                        src = item.seller_rate_chart
                        oi = cart.orderitem_set.filter(seller_rate_chart = item.seller_rate_chart)
                        if oi:
                            oi = oi[0]
                        else:
                            oi = OrderItem(qty=0)
                        oi.order = cart
                        oi.seller_rate_chart = src
                        oi.item_title = src.product.title
                        oi.gift_title = src.gift_title
                        oi.qty += item.qty
                        oi.list_price = src.list_price * oi.qty  #Get list price from ATG Cart
                        oi.sale_price = src.offer_price * oi.qty #Get offer price from ATG Cart
                        oi.shipping_charges = src.shipping_charges * oi.qty
                        oi.save()
                        cart.remove_or_preserve_coupon(request, 'add_item', oi)
                        cart.update_blling(request)


                cs = utils.get_session_obj(request)
                cs['fbapiobj'] = self
                utils.set_session_obj(request,cs)
            else:
                redirect_to_mycart = False

            self.record_last_request(request)
            return add_to_cart_errors, redirect_to_mycart
 
    def sync_cart_for_signin(self,request,cart):
        # 1. Fetch ATG Cart
        # 2. Clear Tinla Cart (order.state='cart')
        # 3. Add ATG Cart items to Tinla Cart
        #    ---If failed to add item to Tinla Cart (Could happen if sku not found in Tinla):
        #     --------Remove the same item(sku) from ATG Cart

        user_agent = utils.get_agent_for_fb_api(request)
        if utils.is_future_ecom(request.client.client):
            # 1. Fetch ATG Cart
            log.info('Getting cart...')
            fb_cart = self.get_cart(request)
            #fb_cart = orders.get_cart(user_agent,self.cookie_file,'9870696051',self.fb_user['items'][0]['profileId'],request)
            self.check_profileid(fb_cart)
            self.add_to_cart_response = fb_cart

            cs = utils.get_session_obj(request)
            cs['fbapiobj'] = self
            utils.set_session_obj(request,cs)
            log.info('FB cart %s' % fb_cart)
            if fb_cart['items']:
                # 2. Clear Tinla Cart (order.state='cart')
                # log the state of Tinla Cart Before clear
                cart.clear_items(request)
                log.info('%s' % cart.get_item_count())

                self.promotions_into_effect = fb_cart['items'][0]['globalPromotions']
                self.coupons_into_effect = fb_cart['items'][0]['couponsAttachedToOrder']
                fb_cart_items = fb_cart['items'][0]
                for f_item in fb_cart_items['items']:
                    try:
                        #seller = Account.objects.get(name=utils.FECOM_SELLERS[request.client.domain])
                        src = SellerRateChart.objects.get(sku=f_item['skuId'],seller__client = request.client.client)
                        oi = OrderItem(qty=0)
                        oi.order = cart
                        oi.seller_rate_chart = src
                        oi.item_title = src.product.title
                        oi.gift_title = src.gift_title
                        oi.qty = f_item['qty']
                        oi.list_price = src.list_price * f_item['qty'] # Get list price from ATG Cart
                        oi.sale_price = src.offer_price * f_item['qty'] # Get offer price from ATG Cart
                        oi.shipping_charges = src.shipping_charges * f_item['qty']
                        oi.save()
                    except SellerRateChart.DoesNotExist:
                        log.exception('Seller Rate Chart Not Found %s' % f_item['skuId'])
                        #Remove item from fb cart
                        response = orders.remove_from_cart(f_item['commerceItemId'],f_item['productId'],user_agent,
                            self.fb_user['items'][0]['profileId'],self.cookie_file, request)
                        self.add_to_cart_response = response
                        self.promotions_into_effect = response['items'][0]['globalPromotions']
                        self.coupons_into_effect = response['items'][0]['couponsAttachedToOrder']
                        cs = utils.get_session_obj(request)
                        cs['fbapiobj'] = self
                        utils.set_session_obj(request,cs)
                cart.remove_or_preserve_coupon(request, 'add_item', None)
                cart.update_blling(request)

                cart.reference_order_id = self.add_to_cart_response['items'][0]['orderId']
                cart.save()
                cs = utils.get_session_obj(request)
                cs['fbapiobj'] = self
                utils.set_session_obj(request,cs)
        self.record_last_request(request)

    def add_item_to_fb_cart(self,request, cart, rate_chart,qty):
        self.check_atg_session(request)
        user_agent = utils.get_agent_for_fb_api(request)
        log.info('Adding sku: %s to cart' % rate_chart.sku)
        response = orders.add_to_cart(rate_chart.sku, rate_chart.external_product_id, qty,user_agent,self.fb_user['items'][0]['profileId'],self.cookie_file, request)
        self.check_profileid(response)
        if response['responseCode'] == 'OM_ADDED_ITEM_TO_CART':
            if self.add_to_cart_response and 'items' in self.add_to_cart_response and len(self.add_to_cart_response['items']) > 0:
                if self.add_to_cart_response['items'][0]['orderId'] != response['items'][0]['orderId']:
                    log.exception('ORDER_ID_CHANGED_ADD_TO_CART: from %s to %s' 
                        % (self.add_to_cart_response['items'][0]['orderId'], response['items'][0]['orderId']))
                    log.exception('ORDER_ID_CHANGED_ADD_TO_CART: Tinla Cart %s, ATG Cart %s' % (cart.get_order_info(),
                        response))
            self.add_to_cart_response = response
            self.promotions_into_effect = self.add_to_cart_response['items'][0]['globalPromotions']
            self.coupons_into_effect = self.add_to_cart_response['items'][0]['couponsAttachedToOrder']
        elif response['responseCode'] == 'GN_UNKNOWN_ERROR':
            log.error('Error adding item to cart %s: %s' % (rate_chart.sku, response))
            raise Exception('Unable to add item %s to cart' % rate_chart.sku)
        else:
            self.add_to_cart_response['responseMessage'] = response['responseMessage']
            self.add_to_cart_response['responseCode'] = response['responseCode']


        self.record_last_request(request)
        cs = utils.get_session_obj(request)
        cs['fbapiobj'] = self
        utils.set_session_obj(request,cs)
        log.info('response %s' % self.add_to_cart_response)
        return response
    
    def remove_coupon(self, request, coupon):
        self.check_atg_session(request)
        agent = utils.get_agent_for_fb_api(request)
        response = orders.remove_coupon(agent,coupon.code,self.fb_user['items'][0]['profileId'],self.cookie_file, request)
        if response['responseCode'] == 'OM_REMOVE_COUPON':
            self.promotions_into_effect = response['items'][0]['globalPromotions']
            self.coupons_into_effect = response['items'][0]['couponsAttachedToOrder']
            cs = utils.get_session_obj(request)
            cs['fbapiobj'] = self
            utils.set_session_obj(request,cs)
        try:
            if self.add_to_cart_response:
                if self.add_to_cart_response['items'][0]['orderId'] != response['items'][0]['orderId']:
                    log.exception('ORDER_ID_CHANGED_REMOVE_COUPON: from %s to %s' 
                        % (self.add_to_cart_response['items'][0]['orderId'], response['items'][0]['orderId']))
        except Exception,e:
            log.exception('Exception in remove_coupon %s' % repr(e))
        self.check_profileid(response)
        self.record_last_request(request)
        return response

    def remove_item_from_cart(self,request,cart,oi):
        self.check_atg_session(request)
        agent = utils.get_agent_for_fb_api(request)
        fb_cart  = self.get_cart(request)
        #fb_cart = orders.get_cart(agent,self.cookie_file,'9870696051',self.fb_user['items'][0]['profileId'], request)
        self.check_profileid(fb_cart)
        log.info('FB cart %s' % fb_cart)
        fb_cart = self.add_to_cart_response
        response = None
        if fb_cart['items']:
            fb_cart_items = fb_cart['items'][0]
            for item in fb_cart_items['items']:
                if oi.seller_rate_chart.sku == item['skuId']:
                    response = orders.remove_from_cart(item['commerceItemId'],item['productId'],agent,self.fb_user['items'][0]['profileId'],self.cookie_file, request)
                    self.check_profileid(response)

                    if self.add_to_cart_response:
                        if self.add_to_cart_response['items'][0]['orderId'] != response['items'][0]['orderId']:
                            log.exception('ORDER_ID_CHANGED_REMOVE_ITEM_FROM_CART: from %s to %s' 
                                % (self.add_to_cart_response['items'][0]['orderId'], response['items'][0]['orderId']))

                    self.add_to_cart_response = response
                    try:
                        self.promotions_into_effect = response['items'][0]['globalPromotions']
                        self.coupons_into_effect = response['items'][0]['couponsAttachedToOrder']
                    except:
                        log.exception('Exception in remove item %s : %s' % (item['productId'],response))

                    cs = utils.get_session_obj(request)
                    cs['fbapiobj'] = self
                    utils.set_session_obj(request,cs)
                    log.info('Item removed %s' % response)
                    break
        self.record_last_request(request)
        return response

    def confirm_fb_order(self,request,pending_order):
        self.check_atg_session(request)
        agent = utils.get_agent_for_fb_api(request)
        order_response = orders.confirm_order(pending_order.reference_order_id,agent,self.fb_user['items'][0]['profileId'],self.cookie_file, request)
        self.check_profileid(order_response)
        #TODO send email notification if api fails to confirm the order on ATG
        self.record_last_request(request)

 

    def update_user(self,request,user_agent,pending_order,payment_options_form):
        self.check_atg_session(request)
        user_agent = utils.get_agent_for_fb_api(request)
        domain = request.META['HTTP_HOST']
        delivery_info = pending_order.get_delivery_info()
        daddress = delivery_info.address
        if not daddress.first_name  and not daddress.last_name:
            ls = daddress.name.split(' ')
            first_name = ''
            last_name = ''
            if len(ls)>1:
                first_name = ls[0]
                last_name = ls[1]
            else:
                first_name = ls[0]
            daddress.first_name = first_name
            daddress.last_name = last_name
            daddress.save()
        current_user = pending_order.user
        fb_user = self.fb_user
        if fb_user['responseCode'] == fbapiutils.ERROR:
            raise Exception('Cannot update user %s' % fb_user)
        if not delivery_info.address.state:
            return dict(responseCode='STATE_NOT_SELECTED',responseMessage='Please select delivery state')
        if not delivery_info.address.city:
            return dict(responseCode='CITY_NOT_SELECTED',responseMessage='Please select delivery city')

        payment_option_id = payment_options_form.cleaned_data['payment_mode'].split('#')[1]
        payment_option = PaymentOption.objects.get(id=payment_option_id)
        bi = BillingInfo.objects.filter(user=pending_order.user)
        if payment_option.payment_mode.validate_billing_info and bi:
            bi = bi[0]
            billing_info={}
            billing_info['firstName'] = bi.first_name
            billing_info['lastName'] = bi.last_name
            billing_info['address1'] = bi.address.address
            billing_info['city'] = bi.address.city.name
            billing_info['state'] = fbapiutils.STATES_MAP[bi.address.state.name]
            billing_info['country'] = 'IN'
            billing_info['postalCode'] = bi.address.pincode
            billing_info['phoneNumber'] = bi.address.phone
        else:
            billing_info={}
            billing_info['firstName'] = delivery_info.address.first_name
            billing_info['lastName'] = delivery_info.address.last_name
            billing_info['address1'] = delivery_info.address.address
            billing_info['city'] = delivery_info.address.city.name
            billing_info['state'] = fbapiutils.STATES_MAP[delivery_info.address.state.name]
            billing_info['country'] = 'IN'
            billing_info['postalCode'] = delivery_info.address.pincode
            billing_info['phoneNumber'] = delivery_info.address.phone
        if not billing_info['city'] and not billing_info['country'] and not billing_info['postalCode'] and not billing_info['address1'] and not billing_info['state']:
            billing_info['city'] = delivery_info.address.city.name
            billing_info['country'] = 'IN'
            billing_info['postalCode'] = delivery_info.address.pincode
            billing_info['address1'] = delivery_info.address.address
            billing_info['state'] = fbapiutils.STATES_MAP[delivery_info.address.state.name]


        log.info('Updating profile id %s' % self.fb_user['items'][0]['profileId'])
        resp = users.update_user({
                'first_name': delivery_info.address.first_name,
                'last_name': delivery_info.address.last_name,
                'address': delivery_info.address.address,
                'city': delivery_info.address.city.name,
                'state': fbapiutils.STATES_MAP[delivery_info.address.state.name],
                'country': 'IN',
                'postal_code': delivery_info.address.pincode,
                'phone_number': delivery_info.address.phone
            },
            {
                'first_name': billing_info['firstName'],
                'last_name': billing_info['lastName'] if  'lastName' in billing_info  else '',
                'address': billing_info['address1'],
                'city': billing_info['city'],
                'state': billing_info['state'],
                'country': billing_info['country'],
                'postal_code': billing_info['postalCode'],
                'phone_number': billing_info['phoneNumber']
            },
            user_agent,
            self.fb_user['items'][0]['profileId'],
            self.cookie_file, request)
        if resp['responseCode'] in ['OM_NO_PROFILE_ID', 'OM_ANONYMOUS_PROFILE', 'OM_PROFILE_MISMATCH',
            'UM_NO_PROFILE_ID', 'UM_PROFILE_MISMATCH', 'UM_ANONYMOUS_PROFILE']:
            log.info('UNABLE_TO_UPDATE_USER_BEFORE_SUBMIT_CART for %s' % self.add_to_cart_response['items'][0]['orderId'])

        self.check_profileid(resp)
        self.record_last_request(request)
        before_profileid = self.fb_user['items'][0]['profileId']
        if resp['responseCode'] == 'UM_UPDATED_USER':
            after_profileid = resp['items'][0]['profileId']
            if before_profileid != after_profileid:
                log.info('PROFILE_ID_CHANGED: Profile id before update %s, Profile id after update %s' % (before_profileid, after_profileid))
                log.info('PROFILE_ID_CHANGED: Login before update: %s, Login before update: %s' % (self.fb_user['items'][0]['login'],resp['items'][0]['login']))

        self.fb_user = resp
        cs = utils.get_session_obj(request)
        cs['fbapiobj'] = self
        utils.set_session_obj(request,cs)
        log.info('User updated: %s' % resp)


    def submit_fb_cart(self,request,pending_order,cart,payment_options_form,payment_mode,action,html,**kwargs):
        self.check_atg_session(request)
        if utils.is_future_ecom(pending_order.client):
            fb_order_response = self.add_to_cart_response #cs['fb_order_response']
            agent = utils.get_agent_for_fb_api(request)

            if pending_order.top10_discount:
                res = self.apply_order_discount(request,str(pending_order.top10_discount))
                self.record_last_request(request)
                if res['responseCode'] != 'OM_APPLIED_ORDER_DISCOUNT':
                    log.info('Failed to apply Top10 discount for order %s:' % (pending_order.id))
                else:
                    log.info('Getting cart...')
                    fb_cart  = self.get_cart(request)
                    #fb_cart = orders.get_cart(agent,self.cookie_file,'9870696051',self.fb_user['items'][0]['profileId'], request)
                    self.check_profileid(fb_cart)
                    self.add_to_cart_response = fb_cart
                    self.promotions_into_effect = fb_cart['items'][0]['globalPromotions']
                    self.coupons_into_effect = fb_cart['items'][0]['couponsAttachedToOrder']
                    cs = utils.get_session_obj(request)
                    cs['top10_discount_applied'] = pending_order.top10_discount
                    utils.set_session_obj(request,cs)
                    self.save_to_session(request)

            order_response = self.submit_order_to_fb(request,agent,fb_order_response,pending_order,payment_mode,**kwargs)
            if order_response['responseCode'] != 'OM_SUBMITTED_CART':
                if order_response['responseCode'] == 'OM_SUBMIT_CART_ABORTED_DUE_TO_MISMATCH':
                    order_response['responseMessage'] = "Sorry. We are unable to confirm your order. We are processing your payment and will notify you once completed."
                if payment_mode in ['netbanking', 'credit-card', 'debit-card', 'credit-card-emi-web', 'payback']:
                    self.create_interaction_or_send_email_for_failed_order_submission(request, order_response, pending_order)
                    pa_id = None
                    if 'pa' in kwargs:
                        pa = kwargs['pa']
                        pa_id = pa.id
                    log.info('SUBMIT_CART_FAILED_AFTER_PAYMENT: for Tinla id:%s, ATG Order Id:%s, Payment Attempt:%s' % 
                            (pending_order.id, pending_order.reference_order_id, pa_id))
                log.info('Order was not submitted : %s' % order_response)
                if order_response['responseCode'] == 'GN_UNKNOWN_ERROR':
                    order_response['responseMessage'] = 'Sorry. We were not able to process your payment. Your money is safe with us. We will notify you once we process your payment.'
                log.info('payment_mode:%s' % payment_mode)
                self.submit_cart_response = render_to_response(html,
                        dict(action=action,
                            payment_options_form = payment_options_form,
                            fb_error = order_response['responseMessage'],
                            order=cart,
                            payback_points = order_response.get('paybackPoints'),
                            payment_mode=payment_options_form.cleaned_data['payment_mode']),
                    context_instance = RequestContext(request))
            else:
                fb_order_id = order_response['items'][0]['orderId']
                if fb_order_id != self.add_to_cart_response['items'][0]['orderId']:
                    log.info('ORDER_ID_CHANGED_AFTER_SUBMIT_CART: from %s to %s' % (self.add_to_cart_response['items'][0]['orderId'],fb_order_id))
                pending_order.reference_order_id = fb_order_id
                pending_order.save()
                self.submit_cart_response = None
                self.add_to_cart_response = {}

            cs = utils.get_session_obj(request)
            cs['fbapiobj'] = self
            utils.set_session_obj(request,cs)

    def create_interaction_or_send_email_for_failed_order_submission(self, request, order_response, pending_order):
        # Create RMS Response if order is not submitted 
        from rms.models import Campaign, Response, Interaction
        from users.models import Phone
        phone = None
        user = pending_order.user
        medium = pending_order.medium
        order_id = pending_order.get_id()
        profile_id = user.id
        amount = pending_order.payable_amount
        payment_mode = pending_order.payment_mode
        gateway = None
        payment_status = None
        email = None
        payment_attempt = pending_order.paymentattempt_set.all().order_by('-id')
        atg_username = request.session.get('atg_username')
        if payment_attempt:
            payment_attempt = payment_attempt[0]
            gateway = payment_attempt.gateway
            payment_status = payment_attempt.status

        name = user.full_name if user.full_name else None

        message = '''Order Id : %s 
                Atg_Username : %s
                Profile Id : %s 
                Total Amount : %s
                Payment Mode : %s
                Payment Status : %s \n
                ''' %(order_id, atg_username, profile_id, amount, payment_mode, payment_status)

        po_details = " \n Item Level Details \n"
        ######### Pending Order Details #####
        for item in pending_order.orderitem_set.all():
            sale_price = item.sale_price
            title = item.item_title
            sku = item.seller_rate_chart.sku
            article_id = item.seller_rate_chart.article_id
            shipping_charge = item.shipping_charges
            cashback_amount = item.cashback_amount
            list_price = item.list_price
            item_details = ''' Sku : %s
                        Article Id : %s
                        Title : %s 
                        Sale Price : %s
                        List Price : %s
                        Shipping Charge : %s
                        CashBack Amount : %s \n
                        ''' %(sku, article_id, title, sale_price, list_price, shipping_charge, cashback_amount)
            
            po_details = po_details + item_details
                
        message = message + po_details
        
        user_phone_obj = Phone.objects.filter(user=user)[:1]
        if user_phone_obj:
            phone = user_phone_obj[0]
        else:
            try:
                from orders.models import BillingInfo
                billing_info = BillingInfo.objects.filter(user=user).order_by('-id')[:1]
                if billing_info:
                    billing_info = billing_info[0]
                    if not name:
                        name = '%s %s' %(billing_info.first_name, billing_info.last_name)
                    
                    billing_phone = billing_info.phone
                    if billing_phone:
                        billing_phone_obj = None
                        try:
                            billing_phone_obj = Phone.objects.get(phone=billing_phone)
                        except Phone.DoesNotExist:
                            billing_phone_obj = Phone.objects.create(phone=billing_phone, user=user)
                        phone = billing_phone_obj
            except Exception, e:
                log.exception("::: No Phone Objects for RMS Response :::: %s" % repr(e))

        if phone:
            log.info(" Phone Number Found for phone id : %s and phone no : %s " % (phone, phone.phone))
            try:
                from users.models import Email
                email = Email.objects.filter(user=user)[:1]
                if email:
                    email = email[0]
                else:
                    email = user.primary_email
                message += '''Phone: %s
                    Name: %s
                    Email: %s
                    ''' % (phone.phone, name, email)
                
                campaign = Campaign.objects.get(id=32)
                from rms.views import get_or_create_response
                response = get_or_create_response(campaign=campaign, phone=phone, type='outbound')
                interaction = Interaction.objects.create(response=response, notes=message)
            except Exception, e:
                log.exception("::: Error Creating Response Or Interaction :::: %s" % repr(e))
            
        # Send Mail Everytime the order is not submitted
        try:
            from users.models import Email
            from settings import ORDER_SUBMISSION_FAILED_EMAILS #Group of Emails
            email = Email.objects.filter(user=user)[:1]
            if email:
                email = email[0]
            else:
                email = user.primary_email
            message += '''Name: %s
                Email: %s
                ''' % (name, email)
            
            log.info("Trying to Send Email with email %s" % email)
            
            from notifications.email import Email
            mail_obj = Email()
            mail_obj._from = "noreply@futurebazaar.com"
            mail_obj.body = message
            mail_obj.subject = "Order Id:%s Submission Failed" %(order_id)
            mail_obj.to = ORDER_SUBMISSION_FAILED_EMAILS
            mail_obj.send()
            log.info("Email sent with email %s" % email)
        
        except Exception, e:
            log.info(":::: No alert can be raised for Order Id %s with Email %s :::: %s" % (order_id, email, repr(e)))


    def get_fb_payment_mode(self,payment_mode):
        fb_payment_mode = fbapiutils.PAYMENT_MODE_MAP[payment_mode]
        sub_pay_type = ''
        if fb_payment_mode in ['EasyBill', 'Suvidha', 'ICICICash', 'Itz']:
            sub_pay_type = fb_payment_mode
            fb_payment_mode = 'CASH'
        if fb_payment_mode == 'PAYBYEMI':
            sub_pay_type = 'FM-EMI'
        return fb_payment_mode, sub_pay_type

    def get_submit_cart_method(self, payment_mode):
        return {
                'CAST' : users.submit_store_cart_cash,
                'CCST' : users.submit_store_cart_card
                }.get(payment_mode, users.submit_cart)

    def submit_order_to_fb(self,request,user_agent,fb_order_response,pending_order,payment_mode,**kwargs):
        self.check_atg_session(request)
        user_agent = utils.get_agent_for_fb_api(request)
        fb_payment_mode,sub_pay_type = self.get_fb_payment_mode(payment_mode)
        #pm = PaymentMode.objects.get(code=payment_mode)
        billingInfoObject = pending_order.user.billinginfo_set.all().order_by('-id')
        delivery_info = pending_order.get_delivery_info()
        if not billingInfoObject:
            data = {}
            data['billing_address'] = delivery_info.address.address
            data['billing_country'] = delivery_info.address.country.name
            data['billing_city'] = delivery_info.address.city.name
            data['billing_state'] = delivery_info.address.state.name
            data['billing_first_name'] = delivery_info.address.first_name
            data['billing_last_name'] = delivery_info.address.last_name
            data['billing_pincode'] = delivery_info.address.pincode
            data['billing_phone'] = delivery_info.address.phone
            data['email'] = delivery_info.address.email
            baddress, billingInfoObject = utils.save_billing_info(request, pending_order.user, data, **dict(not_reverse=True)) 
        else:
            billingInfoObject = billingInfoObject[0]
        billingAddressObject =  billingInfoObject.address
        billing_state = billingAddressObject.state or delivery_info.address.state
        billing_city = billingAddressObject.city or delivery_info.address.city
        billing_address = billingAddressObject.address or delivery_info.address.address
        billingAddress = {
            'first_name': billingInfoObject.first_name,
            'last_name': billingInfoObject.last_name,
            'address': billing_address,
            'city': billing_city.name,
            'state': fbapiutils.STATES_MAP[billing_state.name],
            'country': 'IN',
            'postal_code': billingAddressObject.pincode,
            'phone_number': billingAddressObject.phone,
        }
        pg_name = fb_payment_mode
        pg_response = {}
        emi_details = {}
        if payment_mode == 'fmemi':
            card_details = kwargs['card_details']
            emi_details = {
                'subPayType':'FM-EMI',
                'cardIssuingBankName':card_details['issuing_bank'],
                'last4Digits':card_details['last_4_digits'],
                'cardIssueDateMonth':card_details['issue_month'],
                'cardIssueDateYear':card_details['issue_year'],
                'cardExpiryDateMonth':card_details['exp_month'],
                'cardExpiryDateYear':card_details['exp_year'],
                'nameOnCard':card_details['name_on_card']}

        if payment_mode == 'card-at-store':
            card_details = kwargs['card_details']
            pg_response = {
                    'cardNo' : card_details['last4digits'],
                    'cardType' : card_details['cardtype']}
        #Added for 12th august, 2011 12th lucky customer
        #free_order = False
        if payment_mode in ['netbanking', 'credit-card', 'debit-card', 'credit-card-emi-web', 'payback']:
            log.info('before submit cart %s' % kwargs)
            if 'card_details' in kwargs:
                if kwargs['card_details']:
                    card_details = kwargs['card_details']
                    amount = fb_order_response['items'][0]['orderAmount']
                    pg_amount = amount
                    if payment_mode == 'netbanking':
                        pg_name = 'CCAV'
                    if payment_mode == 'credit-card':
                        pg_name = 'HDPC'
                    if payment_mode == 'debit-card':
                        pg_name = 'HDPC'
                    if payment_mode == 'credit-card-emi-web':
                        pg_name = 'HDPC'
                    if 'pa' in kwargs:
                        pa = kwargs['pa']
                        pg_amount = str(pa.amount)
                        if payment_mode == 'credit-card-emi-web':
                            if pa.emi_plan == '3':
                                pg_name = 'HDF3'
                            if pa.emi_plan == '6':
                                pg_name = 'HDF6'
                            if pa.emi_plan == '9':
                                pg_name = 'HDF9'
                        if payment_mode == 'credit-card-emi-web':
                            if pa.gateway == 'hdfc-emi':
                                if pa.emi_plan == '3':
                                    pg_name = 'HDF3'
                                if pa.emi_plan == '6':
                                    pg_name = 'HDF6'
                                if pa.emi_plan == '9':
                                    pg_name = 'HDF9'
                            if pa.gateway == 'icici-emi':
                                if pa.emi_plan == '3':
                                    pg_name = 'ICI3'
                                if pa.emi_plan == '6':
                                    pg_name = 'ICI6'
                                if pa.emi_plan == '9':
                                    pg_name = 'ICI9'
                            if pa.gateway == 'citi-emi':
                                if pa.emi_plan == '3':
                                    pg_name = 'CIT3'
                                if pa.emi_plan == '6':
                                    pg_name = 'CIT6'
                    pg_response = {'cardNo':card_details['card_no'],'cardCvv':card_details['cvv'],'cardHoldersName':card_details['name_on_card'],'cardExpMon':card_details['exp_month'],'cardExpYear':card_details['exp_year'],'amountRecievedFromPG':pg_amount,'currentPriceList':request.client.get_sale_pricelist(),'orderAmount':amount,'paymentMode':pg_name,'orderId':self.add_to_cart_response['items'][0]['orderId'],'primaryResponse':'0','authRefNumber':pending_order.reference_order_id,'rrn':str(pa.id),'transactionId':pending_order.reference_order_id,'extField1':pa.transaction_id,'pgName':pg_name,'status':pa.status}

                    #freeOrder=True for August 12, 2011 Free Order offer on www.futurebazaar.com, else freeOrder=False
                    #start_time = datetime(2011,8,12,0,0,0,0)
                    #end_time = datetime(2011,8,12,23,59,59,59)
                    #now = datetime.now()
                    #free_order = False
                    #if (request.client == utils.get_future_ecom_prod_domain()) and (start_time < now) and (end_time > now):
                    #    free_order = True

                    amount = Decimal(amount)
                    if 'pa' in kwargs:
                        pa = kwargs['pa']
                        pg_response['transaction_id'] = pa.transaction_id
                        pg_response['response_message'] = pa.response
                        pg_response['response_detail'] = pa.response_detail
                        if amount != pa.amount:
                            log.info('AMOUNT_MISMATCH for Tinla Id:%s, Atg order Id:%s, Atg cart amount:%s, payment received:%s' % (pa.order.id, fb_order_response['items'][0]['orderId'],amount, pa.amount))
                    else:
                        if amount != pending_order.payable_amount:
                            log.info('AMOUNT_MISMATCH for Tinal Id:%s, Atg order Id:%s, Atg cart amount:%s, payment received:%s' % (pending_order.id, fb_order_response['items'][0]['orderId'],amount, pending_order.payable_amount))
                else:
                    card_details = None
#                    if 'pa' in kwargs:
#                        pa = kwargs['pa']
#                        pg_amount = str(pa.amount)
#                        amount = fb_order_response['items'][0]['orderAmount']
#                        if payment_mode == 'credit-card-emi-web':
#                            if pa.gateway == 'hdfc-emi':
#                                if pa.emi_plan == '3':
#                                    pg_name = 'HDF3'
#                                if pa.emi_plan == '6':
#                                    pg_name = 'HDF6'
#                                if pa.emi_plan == '9':
#                                    pg_name = 'HDF9'
#                            if pa.gateway == 'icici-emi':
#                                if pa.emi_plan == '3':
#                                    pg_name = 'ICI3'
#                                if pa.emi_plan == '6':
#                                    pg_name = 'ICI6'
#                                if pa.emi_plan == '9':
#                                    pg_name = 'ICI9'
#                        pg_response['transaction_id'] = pa.transaction_id
#                        pg_response['response_message'] = pa.response
#                        pg_response['response_detail'] = pa.response_detail
#                        pg_response = {'cardNo':'1234567890123456','cardCvv':'123','cardHoldersName':'ANUBHAV JAIN','cardExpMon':'12','cardExpYear':'2015','amountRecievedFromPG':pg_amount,'currentPriceList':request.client.get_sale_pricelist(),'orderAmount':amount,'paymentMode':pg_name,'orderId':self.add_to_cart_response['items'][0]['orderId'],'primaryResponse':'0','authRefNumber':pending_order.reference_order_id,'rrn':str(pa.id),'transactionId':pending_order.reference_order_id,'extField1':pa.transaction_id,'pgName':pg_name,'status':pa.status}

        log.info('pg_response %s' % pg_response)
        if 'items' in self.add_to_cart_response:
            if not self.add_to_cart_response['items']:
                fb_cart  = self.get_cart(request)
                #fb_cart = orders.get_cart(user_agent,self.cookie_file,'9870696051',self.fb_user['items'][0]['profileId'], request)
                self.check_profileid(fb_cart)
                self.add_to_cart_response = fb_cart
                self.promotions_into_effect = fb_cart['items'][0]['globalPromotions']
                self.coupons_into_effect = fb_cart['items'][0]['couponsAttachedToOrder']
                self.record_last_request(request)
                # we are updating attributes here, so we need to call
                # save_to_session.
                self.save_to_session(request)

        if fb_payment_mode in ['CCST', 'CAST']:
            received_by = 'STORE'
        else:
            received_by = sub_pay_type
        if request.POST:
            params = request.POST
        else:
            params = request.GET
        submit_response = self.get_submit_cart_method(fb_payment_mode)({
            'order_note': 'Order submission through phone commerce',
            'payment_mode': str.swapcase(fb_payment_mode) if fb_payment_mode == 'payback' else pg_name,
            'pg_response': pg_response,
            'emi_details': emi_details,
            'sub_pay_type': sub_pay_type,
            'received_by' : received_by,
            'current_price_list': request.client.get_sale_pricelist(),
            'order_amount': self.add_to_cart_response['items'][0]['orderAmount'],
            'billingAddress': billingAddress,
            'pincode': "%s" % delivery_info.address.pincode,
            'shipping_postal_code': "%s" % delivery_info.address.pincode,
            'order_id': pending_order.reference_order_id,
            'payback_id': "%s" % (pending_order.payback_id or ''),
            'sessionid': "%s" % params.get('sessionid',''),
            'loyaltyTerminalid': params.get('loyaltyTerminalid', ''),
            'status': "%s" % params.get('status'),
            'Status':"%s" % kwargs.get('Status',''),
            }, user_agent,
            self.fb_user['items'][0]['profileId'],
            self.cookie_file, request)
        self.check_profileid(submit_response)
        self.record_last_request(request)
        log.info('Response of Submit Cart: %s' % submit_response)
        if submit_response['responseCode'] == 'OM_SUBMITTED_CART':
            fb_order_id = submit_response['items'][0]['orderId']
            os = Order.objects.filter(reference_order_id = fb_order_id,state='pending_order')
            if not os:
                pending_order.reference_order_id = submit_response['items'][0]['orderId']
            else:
                for o in os:
                    if o != pending_order:
                        o.reference_order_id = ''
                        o.save()
                    else:
                        pending_order.reference_order_id = fb_order_id
            
            #Added the code to check 12th august, 2011, 12th lucky customer offer

            #if 'freeOrderResponse' in submit_response['items'][0]:
            #    log.info('freeOrder = %s,  Order id: %s, freeOrderResponse = %s' % (free_order, fb_order_id, submit_response['items'][0]['freeOrderResponse']))
            #    if submit_response['items'][0]['freeOrderResponse'] == 'ACCEPTED':
            #        pending_order.notes = 'APPLICABLE_FOR_AUG_12_2011_12TH_FREE_ORDER'
            #        log.info('Order id: %s is applicable for 12th August 12th lucky customer offer' % fb_order_id)

            pending_order.save()
            log.info('FB Order placed. Tinla Order Id: %s, FB Order Id %s' % (pending_order.id, fb_order_id))
        return submit_response
   
    def update_item_quantity(self,request,cart,oi): 
        self.remove_item_from_cart(request,cart,oi)
        self.add_item_to_fb_cart(request, cart, oi.seller_rate_chart,oi.qty)

    def get_orders_by_user(self,request,user,startOrderIndex=0, numberoforders=1):
        self.check_atg_session(request)
        agent = utils.get_agent_for_fb_api(request)
        response = orders.get_order_by_user(user,agent,self.cookie_file, request, startOrderIndex, numberoforders)
        self.record_last_request(request)
        return response

    def print_diff_atg_rest_response(self,atgres, restres, couponCode, orderId):
        log.info('-----------Delta between rest api and atg api----------- ')
        log.info('OrderId : %s, CouponCode : %s ',orderId, couponCode)
        log.info('Rest response message : %s', restres['responseMessage'])
        log.info('Atg response message : %s', atgres['responseMessage'])

        if(restres['responseCode']!=atgres['responseCode']):
            log.info('rest response code : %s', restres['responseCode'])
            log.info('atg response code : %s', atgres['responseCode'])
        elif atgres['responseCode'] == 'OM_APPLIED_COUPON':
            restCoupon = restres['items'][1]['couponsAttachedToOrder'][0] 
            atgCoupon = atgres['items'][1]['couponsAttachedToOrder'][0]
            if(restCoupon['promoAdjuster'] != atgCoupon['promoAdjuster']):
                log.info('rest promoAdjuster : %s', restCoupon['promoAdjuster'])
                log.info('atg promoAdjuster : %s', atgCoupon['promoAdjuster'])
            if(restCoupon['promoType'] != atgCoupon['promoType']): 
                log.info('rest promoType : %s', restCoupon['promoType'])
                log.info('atg promoType : %s', atgCoupon['promoType'])
	    log.info('--------------------------------------------------------- ')	

   
	
    def apply_coupon(self,request,coupon_code,cart):
        self.check_atg_session(request)
        agent = utils.get_agent_for_fb_api(request)
        res = orders.apply_coupon(agent,coupon_code,self.fb_user['items'][0]['profileId'],self.cookie_file, request)
        try:
            orderId = cart.id
            couponCode = coupon_code
            profileId = self.fb_user['items'][0]['profileId']
            login = self.fb_user['items'][0]['login']	
            restresult = APIManager.getPromotionsByCouponCode(orderId,couponCode,profileId,login)
            restresult = simplejson.loads(restresult)
	
            log.info('Atg API Result %s' %res)
            log.info('')
            log.info('Rest API Result %s ' %restresult)
            self.print_diff_atg_rest_response(res,restresult,couponCode,orderId)
        except Exception,e:
            log.exception('Exception in Rest API call %s' % repr(e))

        try:
            orderId = cart.id
            couponCode = coupon_code
            profileId = self.fb_user['items'][0]['profileId']
            login = self.fb_user['items'][0]['login']	
            restresult = APIManager.getPromotionsByCouponCode(orderId,couponCode,profileId,login)
            restresult = simplejson.loads(restresult)
	
            log.info('Atg API Result %s' %res)
            log.info('')
            log.info('Rest API Result %s ' %restresult)
            self.print_diff_atg_rest_response(res,restresult,couponCode,orderId)
        except Exception,e:
            log.exception('Exception in Rest API call %s' % repr(e))

        try:
            if self.add_to_cart_response:
                if res['responseCode'] == 'OM_APPLIED_COUPON':
                    if self.add_to_cart_response['items'][0]['orderId'] != res['items'][1]['orderId']:
                        log.exception('ORDER_ID_CHANGED_APPLY_COUPON: from %s to %s' 
                            % (self.add_to_cart_response['items'][0]['orderId'], res['items'][1]['orderId']))
        except Exception,e:
            log.exception('Exception in apply_order_discount %s' % repr(e))
        self.check_profileid(res)
        if res['responseCode'] == 'OM_APPLIED_COUPON':
            #self.add_to_cart_response = res
            self.promotions_into_effect = res['items'][1]['globalPromotions']
            self.coupons_into_effect = res['items'][1]['couponsAttachedToOrder']
        self.record_last_request(request)
        return res
    
    def apply_order_discount(self,request,discount_amount, cart, description=""):
        self.check_atg_session(request)
        agent = utils.get_agent_for_fb_api(request)
        response = orders.apply_order_discount(agent,discount_amount,self.fb_user['items'][0]['profileId'], self.cookie_file, request, description)
        if response['responseCode'] != 'OM_APPLIED_ORDER_DISCOUNT':
            log.info('Failed to apply Top10 discount for order')
        else:
            log.info('Getting cart...')
            fb_cart  = self.get_cart(request)
            #fb_cart = orders.get_cart(agent,self.cookie_file,'9870696051',self.fb_user['items'][0]['profileId'], request)
            self.add_to_cart_response = fb_cart
            self.promotions_into_effect = fb_cart['items'][0]['globalPromotions']
            self.coupons_into_effect = fb_cart['items'][0]['couponsAttachedToOrder']
            cs = utils.get_session_obj(request)
            cs['top10_discount_applied'] = cart.top10_discount
            utils.set_session_obj(request,cs)
            self.save_to_session(request)
        try:
            if self.add_to_cart_response:
                if self.add_to_cart_response['items'][0]['orderId'] != response['items'][0]['orderId']:
                    log.exception('ORDER_ID_CHANGED_APPLY_TOP10_DISCOUNT: from %s to %s' 
                        % (self.add_to_cart_response['items'][0]['orderId'], response['items'][0]['orderId']))
        except Exception,e:
            log.exception('Exception in apply_order_discount %s' % repr(e))

        self.check_profileid(response)
        self.record_last_request(request)
        return response

    def get_order_by_orderid(self, request, order_id):
        agent = utils.get_agent_for_fb_api(request)
        response = orders.get_order_by_orderid(order_id, agent, self.cookie_file,request,'true')
        self.record_last_request(request)
        return response

    def get_user_by_login(self, request, login):
        agent = utils.get_agent_for_fb_api(request)
        response = users.get_user_by_login(login, agent, self.cookie_file, request)
        self.record_last_request(request)
        return response

    def ebs_check(self, info, mode, request):
        #self.check_atg_session(request)
        response = orders.ebs_check(info, mode, self.cookie_file, request)
        if('Error' in response):
            raise SessionExpired('Error EBS Check')
        #self.check_profileid(response)
        #self.record_last_request(request)
        return response

    def get_session_id(self, cookie_file):
        cj = StringCookieJar(cookie_file) 
        if not cj:
            return ''
        for index, cookie in enumerate(cj):
            if cookie.name == 'ATG_SESSION_ID':
                return cookie.value
        return ''

    def save_to_session(self, request):
        cs = utils.get_session_obj(request)
        cs['fbapiobj'] = self
        utils.set_session_obj(request,cs)

    def record_last_request(self, request):
        self.last_request_at = datetime.now()
        self.save_to_session(request)
    
    def check_profileid(self,response):
        if response['responseCode'] in ['OM_NO_PROFILE_ID', 'OM_ANONYMOUS_PROFILE', 'OM_PROFILE_MISMATCH',
        'UM_NO_PROFILE_ID', 'UM_PROFILE_MISMATCH', 'UM_ANONYMOUS_PROFILE']:
            log.exception('SESSION_EXPIRED: %s' % response)
            raise SessionExpired('Profile Id did not match')

    def check_atg_session(self, request):
        ''' Checks if atg session is still valid.
            Raises a session expired exception if not valid
        '''
        now = datetime.now()
        if not hasattr(self,'last_request_at'):
            setattr(self,'last_request_at',datetime.now())

        last = self.last_request_at
        elapsed = (now - last)
        time_out = timedelta(seconds = 25 * 60)
        if elapsed < time_out:
            # atg sessions expire after 30 mins
            # we are being conservative by discarding session at 25 mins here
            return 

        sess_id = self.get_session_id(self.cookie_file)
        cs = utils.get_session_obj(request)
        
        try:
            username = cs['atg_username']
        except:
            log.exception('SESSION_EXPIRED: atg_username not found in request.session while reinitializing the session')
            raise SessionExpired('Your session expired. Please start again')

        logoff_response = fbapiutils.logoff(self.cookie_file, request)

        cookie_file = fbapiutils.init(request)
        self.cookie_file = cookie_file
        new_sess_id = self.get_session_id(cookie_file)
        log.info('new session id after init for %s is %s' % (sess_id, new_sess_id))

        response = self.get_user_by_login(request, username)

        log.info('user before session recovery %s' % self.fb_user)


        if response['responseCode'] != 'UM_FOUND_USER':
            log.error("Session recovery error. %s : %s" % (sess_id, response))
            raise SessionExpired('Your session expired. Please start again')

        log.info('Found user in %s after recovery' % new_sess_id)
        log.info('user after session recovery %s' % response)

        self.fb_user = response
        cs['fbapiobj'] = self
        utils.set_session_obj(request,cs)

    def create_user(self, request, username, password='kms829%HJ', confirm_password='kms829%HJ'):
        agent = utils.get_agent_for_fb_api(request)
        request = users.create_user('', username, agent, self.cookie_file, request, password, confirm_password)
        self.record_last_request(request)
        return response

    def issue_coupon(self, request, email_id, store):
        agent = utils.get_agent_for_fb_api(request)
        request = orders.issue_coupon(email_id, agent, self.cookie_file, store, request)
        self.record_last_request(request)
        return response


