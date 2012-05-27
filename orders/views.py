# Create your views here.

from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.http import HttpResponseBadRequest, HttpResponsePermanentRedirect
from django.template import RequestContext
from django.views.decorators.cache import never_cache, cache_control
from django.contrib import auth
from django.template.loader import get_template
from django.template import Context, Template
from django.utils.safestring import mark_safe
from django.core.urlresolvers import reverse
from django.core.exceptions import *
from django.db import transaction
from django.contrib.auth.decorators import *

from orders.models import Order, OrderItem, BillingInfo, DeliveryInfo
from users.models import Profile, Email as UserEmail, Phone as UserPhone
import logging
from utils import utils
# XXX Do not import *. It is slower. Please import whats needed
from orders.forms import *
from payments.forms import *
from payments.models import *
from locations.models import Address, AddressBook
from catalog.models import SellerRateChart
from notifications.email import Email
from notifications.sms import SMS
from users.helper import cc_login_required

import logging
import simplejson
import re
import random

order_log = logging.getLogger('fborder')
request_log = logging.getLogger('request')


def get_cart(request, **kwargs):
    '''
    All the possible cart flows.
    Refer http://corp.futurebazaar.com/index.php/Cart_Flow
    
    Scenario 1
    Customer signs in, adds (2) items to cart, signs out. 
    (2) Items stay in the cart till the customer removes them 
    in subsequent sign ins.

    Scenario 2
    Customer signs in, has existing (2) items in cart, 
    adds (3) new items to cart and proceeds to pay. 
    He is now paying for all (5) items in the cart.

    Scenario 3
    Customer has (2) items in cart, adds (3) new items to cart 
    and proceeds to pay. Customer uses Guest Checkout.
    Customer is now paying only for the (3) new items in the cart.

    Scenario 4
    Customer has (2) items in cart, adds (3) new items to cart
    and proceeds to pay. Customer signs in during the checkout flow.
    Customer is now paying only for the (3) new items in the cart.
    Customer still has the initial (2) items in the cart after he pays
    for the (3) new items.

    Scenario 5
    Customer has (2) items in cart, adds (3) new items to cart 
    and proceeds to pay. Customer abandons the payment and signs in.
    He is now seeing the (2) initial items in his cart.

    Scenario 6
    Customer has (2) items in cart, adds (3) new items to cart and proceeds
    to pay. Customer signs in during checkout flow and abandons the payment. 
    Customer is now seeing all (5) items in his cart. 

    Scenario 7
    New customer add (2) items to cart. He then signs up . 
    He should see the 2 items after sign up is complete 

    Add an item to cart. There are various flows starting here
        1. User is signedin: In this case, we add the item to user's cart
           If user does not have a cart, we create one and add the item.
        2. User is not signedin: In this case, if there is a cartId in the
           cookie, we add the item to that cart. Otherwise we create a new
           cart and add the item.
        3. Callcenter: As callcenter agent can add to cart only if user is
           selected (on-call), this is similar to the first flow, with the
           exception that user is not the signedin user, but the user on
           call.
    '''
    cart_id = kwargs.get('admin_order_id', None)
    cart = None
    profile = None
    session = utils.get_session_obj(request)
    cart_id = session.get('cart_id')
    user = request.user
    if cart_id:
		try:
			# XXX We should also have check that its a cart
			cart = Order.objects.get(id=cart_id)
		except Exception, e:
			# XXX Again, should create a new cart only for does not exist
			order_log.exception(
				"Error fetching cart from session's cart_id %s. Creating new cart for user %s" % (cart_id, user))
			# XXX We should prehaps call get_or_create_user_cart
			cart = create_new_cart(request, user=user)
    elif user.is_authenticated():
        # Cart id is not present, fallback to DB to get the user's cart
        cart = get_or_create_user_cart(request, user=user) 
    else:
        cart = create_new_cart(request, user=user)
    session['cart_id'] = cart.id

    # XXX There are cases where we are not able to get the cart. Should prehaps
    # XXX raise an exception like CannotGetCart and let the callers handle it
    return cart

def create_new_cart(request, **kwargs):
    ''' Creates a new cart. Does not check if user already has a cart.
        Use with care
    '''
    try:
        user = kwargs.get('user')
        profile = utils.get_user_profile(user) #Need to get an existing user
    except Exception, e:
        # XXX There is no need to use markers in the logging like :::
        # XXX or ---- or ====. Writing crisp and correct log message is 
        # XXX extremely important. Please understand that others are more
        # XXX likely to read your logs than yourself. They should be able to
        # XXX to understand what you are saying. Leaving your current log so
        # XXX that you can understand what I was talking about.
        #order_log.info(":::: Profile Error create_new_cart  %s %s"  % (request.user, repr(e)))
        order_log.exception(
            'Cannot create new cart for %s. Error fetching profile. Ignoring user param.' % request.user)
        profile = None
    state = 'cart'
    if not profile:
        state = 'guest_cart'
    cart = Order.objects.create(state=state, client=request.client.client,
        user=profile, support_state=None)
    return cart

def get_or_create_user_cart(request, **kwargs):
    user = kwargs.get('user')
    profile = utils.get_user_profile(user)
    if not profile:
        # XXX profile is not found, create_new_cart again searches for this
        # XXX profile which is useless. Removing the kwargs param. Commenting
        # XXX out the line that was before the change for reference
        #return create_new_cart(request, user=request.user)
        return create_new_cart(request)

    # Get carts for the user in reverse chrono order. Pick the first one
    carts = Order.objects.filter(user=profile, state='cart',
        support_state=None, client=request.client.client
        ).order_by('-timestamp')[:2] # XXX Added a limit of 2
    if carts:
        cart = carts[0]
        if len(carts) > 1:
            log.warning('Multiple carts found for user %s' % user.id)
        # XXX Commenting out the deleteing carts part for now. Lets manually
        # XXX observe this log for a few days, delete the carts and automate
        #old_carts = carts.exclude(id = cart.id)
        #for old_cart in old_carts:
        #    old_cart.delete()
    else:
        cart = create_new_cart(request, user=request.user)
    return cart

@never_cache
@cache_control(private=True)
def cart_actions(request, **kwargs):
    return cart_actions_wo_cache(request, **kwargs)

def cart_actions_wo_cache(request, **kwargs):
    response = {}
    redirect_to = None
    cart = None
    express_checkout = None

    cart = get_cart(request, **kwargs)
    validation_errors = []
    if request.method == 'POST':
        params = request.POST
        action = params.get('action', '')
        express_checkout = request.POST.get('express_checkout', None)
                
        if action in ['apply_coupon','apply_payback','remove_payback']:
            try:
                validation_errors = cart.validate_items(request)
            except Exception, e:
                order_log.exception("Error validating cart %s during %s" % (
                    cart.id, action))

        if action == 'add_to_cart':
            response = add_to_cart(request, cart=cart)
        
        elif action == 'update_cart_item' and not validation_errors:
            response = update_item_quantity(request, cart=cart)
        
        elif action == 'remove_cart_item':
            response = remove_from_cart(request, cart=cart)
        
        elif action == 'remove_fb_coupon':
            # XXX This action should be renamed to remove_coupon
            response = remove_coupon(request, cart=cart)
            redirect_to = request.POST.get('redirect_to')
        
        elif action == 'apply_coupon' and not validation_errors:
            response =  apply_coupon(request, cart=cart)
            # XXX Need an elegant way to do this. redirect_to is clumsy
            redirect_to = request.POST.get('redirect_to')
        
        if action in ['update_cart_item', 'add_to_cart','remove_cart_item','remove_fb_coupon']:
            try:
                validation_errors = cart.validate_items(request)
            except Exception, e:
                order_log.exception("Error validating cart %s during %s" % (
                    cart.id, action))
    elif cart:
        try:
            validation_errors = cart.validate_items(request)
        except Exception, e:
            order_log.exception("Error validating cart %s during %s" % (
                cart.id, action))
        
        response = view_cart(request, cart=cart)
    
    # XXX Find a way to get rid of this
    if redirect_to:
        return HttpResponseRedirect(redirect_to)

    # XXX How will we end up here? Is it an error or expected behavior
    # XXX I am guessing its an error, we should log it if thats the case
    if not response:
        return HttpResponseRedirect(request.path)
   
    # XXX next_action can perhaps be extended to cover redirect_to cases
    # XXX I am assuiming that redirect_to came into existence because we
    # XXX moved coupon to the payments page
    next_action = next_checkout_action(request, **kwargs)
    post_back = request.path
    
    if cart:
        response.update({
            'order':cart,
            'orderItems':cart.get_order_items(request,
                exclude=dict(state__in=['cancelled','bundle_item']))
                })
    
    response.update({'next_action':next_action, 'post_back':post_back})

    errors = response.get('errors',[])
    if validation_errors:
        # XXX Should be moved to debug after stabilization
        order_log.info("Cart %s validation failed due to  %s" % (
            cart.id, validation_errors))
        validation_errors.extend(errors)
        response['errors'] = validation_errors
        # XXX Why is this an extra flag? Should it not be blocked if there
        # XXX are errors
        response['block_shipping'] = True
    
    return render_to_response('order/mycart.html', response,
            context_instance = RequestContext(request))


NU_RE = re.compile('\d+$')
def add_to_cart(request, **kwargs):
    # XXX Should make cart a first order parameter. Not part of kwargs
    cart = kwargs['cart']
    rate_chart_id = request.POST['rate_chart_id']
    qty = request.POST.get('qty', '1') 
    response = {'apply_coupon':True}
    errors = []

    if not NU_RE.match(qty):
        return response

    try:
        rate_chart = SellerRateChart.objects.using('default').get(
            id=rate_chart_id)
        if qty < rate_chart.min_qty:
            qty = rate_chart.min_qty
        #with transaction.commit_on_success():
        #    error = cart.add_item(request, rate_chart=rate_chart, qty=qty)
        #    if error:
        #        errors.append(error)
    except Order.BundleArticle, e:
        # Bundle with same src is already present in the cart
        # Adding src which is already a part of one of the bundles in cart
        order_log.warning("BUNDLE: %s already in cart under bundle %s" % (
            e.child, e.parent))
        errors.append('%s is already part of bundle %s. You cannot purchase \
            both at same time. Please remove %s if you wish to \
            buy %s' % (e.child.product.title, e.parent.product.title,
            e.parent.product.title, e.child.product.title))
    except Order.BundleItemAlreadyAdded, e:
        # src added. bundle which contains same src is being added.
        # reverse case of BundleArticle exception
        order_log.warning("BUNDLE: %s bundle item src - %s already in cart" %
            (e.parent, e.child))
        errors.append('%s and %s cannot be purchased together as %s contains \
            the same bundled product' % (e.parent.product.title, 
            e.child.product.title, e.child.product.title))
    except Order.BundleItemConflict, e:
        # bundle being added, but conflicts as this bundle contains an src
        # which is already part of one of the bundles in the cart
        order_log.warning("BUNDLE: src - %s conflicts with bundle src %s" %
            (e.new_src, e.old_src))
        errors.append('%s and %s cannot be purchased together as they contain \
            the same bundled product' % (e.new_src.product.title,
            e.old_src.product.title))
    except SellerRateChart.DoesNotExist:
        order_log.warning(
            'Skipping add to cart. Rate chart %s not found' % rate_chart_id)
    except Exception, e:
        # XXX There might be other exceptions to catch. Like out of stock
        # XXX product is not active, product is not active for this client
        # XXX and a bunch of other businesss rules. 
        order_log.exception("Error adding item to cart %s. Cart: %s" % (
            rate_chart_id, cart.id))
        errors.append('Sorry we were unable to add the product to your cart. \
            Please try again')

    response.update(errors=errors)
    return response

def update_item_quantity(request, **kwargs):
    # XXX Should make cart a first order parameter. Not part of kwargs
    cart = kwargs['cart']
    item_id = request.POST['itemid']
    qty = request.POST.get('%s_qty' % item_id)
    if int(qty) > 12:
        # Limit max qty to be purchased to 10. Might need to limit this to web
        qty = '12' # to ensure the next function calls dont break.
    response = {}
    errors = []
   
    response.update(errors=errors)
    return response

def remove_coupon(request, **kwargs):
    # XXX Should make cart a first order parameter. Not part of kwargs
    cart = kwargs['cart']
    # XXX Should make coupon_code a first order param. Not optional
    response = {}
    errors = []
    try:
        # XXX Write a proper method in the order object which
        # XXX can remove a coupon and calls update billing. It should
        # XXX also raise proper exceptions.
        # XXX Use transactions
        if not cart.coupon:
            return response
        coupon_code = cart.coupon.code
        cart.remove_coupon(request, coupon_code=coupon_code)
    except Exception, e:
        order_log.exception("Error removing coupon  %s %s" % (
            cart.id, cart.coupon.code))
        errors.append('Unable to remove coupon %s. \
            Please try again' % cart.coupon.code)

    response.update(errors=errors)
    return response

def remove_from_cart(request, **kwargs):
    # XXX Should be first order parameter
    cart = kwargs['cart']
    item_id = request.POST['itemid']
    response = {}
    errors = []

    try:
        # XXX Use transactions
        cart.remove_item(request, item_id=item_id)
        response['status'] = 'Item Removed'
    except Order.BundleArticle, e:
        order_log.error("BUNDLE: %s is bundle article" % e.child)
        # XXX Prady, plese check if the e.child and e.parent stuff is right
        errors.append('Cannot remove %s as it is part of bundle. \
            Please remove %s if you wish to remove %s' % (
            e.child.title, e.parent.title, e.child.title))
    except Exception, e:
        order_log.exception(
            "Error removing item %s from %s" % (item_id, cart.id))
        errors.append('Unable to remove item. Please try again.')

    response.update(errors=errors)
    return response

def apply_coupon(request, **kwargs):
    # XXX Should be first order praameter
    cart = kwargs['cart']
    coupon_code = request.POST.get('coupon_code', None)
    response = {}
    errors = []

    if cart.coupon:
        promo_response = 'You can apply only one coupon at a time. \
            Please remove coupon %s if you wish to apply %s' % (
            cart.coupon, coupon_code)
        errors.append(promo_response)
        # XXX Why set this in session?
        request.session['applied_coupon_msg'] = promo_response
    elif coupon_code:
        try:
            promo_response = cart.apply_coupon(request, coupon_code=coupon_code)
            request.session['applied_coupon_msg'] = promo_response
        except Exception, e:
            order_log.error("::: Unable to Apply Coupon ::: %s %s" % (coupon_code, repr(e)))
            errors.append('Coupon not applied')
    else:
        if coupon_code:
            try:
                # XXX Cannot call update billing from here. It should be
                # XXX wrapped in a method in orders object to apply coupon
                # XXX Use transactions
                promo_response = cart.update_billing(request, coupon_code=coupon_code, sender='apply_coupon')
                request.session['applied_coupon_msg'] = promo_response
            except Exception, e:
                order_log.exception('Error applying coupon %s on %s' % (
                    coupon_code, cart.id))
                errors.append("Unable to apply coupon %s. \
                    Please try again" % coupon_code)
        else:
            errors.append('Please enter a valid coupon')
            # XXX Why set this in session?
            request.session['applied_coupon_msg'] ='Please enter a valid coupon'

    response.update(errors=errors)
    return response


def view_cart(request, **kwargs):
    cart = kwargs['cart']
    response = {}
    messages = []

    try:
        #with transaction.commit_on_success():
    	order_log.info('Before Updating cart %s with the \
		latest seller rate chart, Cart total %s' % (
		cart.id,cart.payable_amount))

    	# XXX Cannot call update billing from here. We can call
    	# XXX update billing from src
    	previous_total = cart.payable_amount
    	cart.update_billing_from_src(request, sender='view_cart')
    	new_total = cart.payable_amount
    	order_log.info('After updating cart %s, Total is %s' % (
		cart.id, cart.payable_amount))

    	if new_total != previous_total:
		messages.append('Your cart total has changed from %s to %s' % (
		utils.formatMoney(previous_total), 
		utils.formatMoney(new_total)))
    except Exception, e:
        order_log.exception("Error showing cart %s" % cart.id)

    response.update({
        'apply_coupon':True,
        'readonly' : False,
        'messages': messages
        })
    return response

def next_checkout_action(request, **kwargs):
    # options for tab are
    # mycart, shipping, payment_info in the admin process
    # mycart, signin, shipping, process_payment in web process
    # mycart, shipping, book in call center process
    
    MYCART = 'mycart'
    SHIPPING = 'shipping'
    SIGNIN = 'signin'
    BOOK = 'book'
    PROCESSPAYMENT = 'process_payment'
    PAYMENTINFO = 'payment_info'
    BOOKED = 'booked'
    CONFIRMATION = 'confirmation'
    CANCELLATIONINFO = 'cancellation_info'

    domain = request.META['HTTP_HOST']
    tab = request.path.split('/')[-1]
    action = None
    if tab == MYCART:
        if not request.user.is_authenticated():
            if request.client.type in ['cc', 'store']:
                action = SHIPPING
            else:
                action = SIGNIN
        else:
            if domain in utils.MOBILE_DOMAIN:
                action = SIGNIN
            else:
                action = SHIPPING
    if tab == SIGNIN:
        action = SHIPPING

    if tab == SHIPPING:
        if utils.is_cc(request):
            action = BOOK
        elif request.path.startswith('/orders/auth/'):
            action = PAYMENTINFO
    else:
        if not action:
            if request.user.is_authenticated():
                action = SHIPPING
            else:
                action = SIGNIN
    if request.is_auth:
        # required for order confirmation and cancellation interface
        # slicing at end will remove '/' at start of request.path
        # please don't remove this -- saumil
        return request.path.replace(tab, action)[1:]
    else:
        return 'orders/%s' % action

@never_cache
def shipping_detail(request, **kwargs):
    return shipping_detail_wo_cache(request, **kwargs)
    
def shipping_detail_wo_cache(request, **kwargs):
    cart = get_cart(request, **kwargs)
    express_checkout = kwargs.get('express_checkout', None)
    
    failed_payment = request.session.get('failed_payment',None)
    if failed_payment:
        del request.session['failed_payment']
    
    if cart:
        cart_items = cart.get_order_items(request,
            exclude=dict(state__in=['cancelled','bundle']))
        # XXX Restrictions should be much more rigid. We should not allow
        # XXX GET requests on this page or make restrictions more rigid.
        if not cart_items:
            return HttpResponseRedirect(
                request.path.replace('shipping', 'mycart'))
    else:
        return HttpResponseRedirect(request.path.replace('shipping', 'mycart'))
    
    user = cart.user

    # XXX This check seems faulty. Don't remember the reason for having this
    # XXX world.holii pays in USD and we should allow it. The only check
    # XXX which makes sense to keep is if cart has items in multiple currencies

    allowed = True
    currencies = {}
    for item in cart_items:
        if item.seller_rate_chart.product.currency not in currencies:
            currencies[item.seller_rate_chart.product.currency] = 1
    if len(currencies.keys()) > 1:
        allowed = False

    availability_errors = []
    gateway_error = None
    shipping_form_errors = None
    inventory_errors = None

    domain = request.client
    next_step = next_checkout_action(request, **kwargs)
    is_valid_shipping_address = False
    
    delivery_notes_form = DeliveryNotesForm()
    delivery_info = None
    try:
        # XXX This can also be temporary cart. Registered user proceeding as
        # XXX guest
        if cart.state != 'guest_cart':
            # XXX What is the reason to ignore this for guest carts?
            # XXX If the reason is to not show the address, then we are still
            # XXX vulnerable to bad address for this order.
            delivery_info = cart.get_address(request, type='delivery')
    except DeliveryInfo.DoesNotExist:
        pass

    shipping_info_form = ShippingInfoForm(info=delivery_info, 
        client=request.client.client)
    
    if request.POST and 'del_address' in request.POST:
        try:
            is_valid_shipping_address = False
                
            if is_valid_shipping_address:
                pincode  = cart.get_address(request, type='delivery').address.pincode
            
            if is_valid_shipping_address:
                availability_errors = None
                if not availability_errors:
                    # XXX Next page agter shipping is payment. We should
                    # XXX have got this from previous call for
                    # XXX next_checkout_action. right?
                    return next_page_after_shipping(request, cart)
        
        except PaymentAttempt.NoResponseFromPG, e:
            gateway_error = e.message
        
        except Order.InventoryError, e:
            inventory_errors = e.errors
        
        except Exception, e:
            order_log.exception(
                "Error saving shipping details for %s" % cart.id)

    if not user or cart.state == 'guest_cart':
        # XXX This can also be temporary cart. Registered user proceeding as
        # XXX guest
        user_addresses = []
    else:
        try:
            user_addresses = user.get_addresses(request, client=cart.client)
            if len(user_addresses) > 3:
                user_address = user_addresses[:3]
        except cart.UserDoesNotExist:
            # XXX Wow. I think we should log and die if we still do not have
            # XXX a user attached to the cart
            user_address = []
    
    shipping_dict = {
            'shipping_info_form':shipping_info_form,
            'delivery_notes_form':delivery_notes_form,
            'order':cart,
            'failed_payment':failed_payment,
            'user_addresses':user_addresses,
            'availability_errors':availability_errors,
            'inventory_errors':inventory_errors,
            'gateway_error':gateway_error,
            'shipping_form_errors':shipping_form_errors,
            'next_action':next_step,
            'post_back':request.path,
            'allowed':allowed
        }
    
    return render_to_response('order/shipping_info.html',
        shipping_dict,
        context_instance = RequestContext(request))

def validate_and_save_delivery_info(request, **kwargs):
    order = kwargs['order']
    is_valid_shipping_address = False
    addressbook_id = None
    delivery_details = {}
    address = None
    delivery_info = None
    client = order.client

    shipping_info_form = ShippingInfoForm(request.POST, client=client)
    delivery_notes_form = DeliveryNotesForm(request.POST)
    
    # clean up notes, there are no validaton errors to handle for notes
    # mandatory call so that we get the cleaned data
    delivery_notes_form.is_valid()
    
    try:
        for field in delivery_notes_form.fields:
            delivery_details.update({
                field:delivery_notes_form.cleaned_data[field]})
    except Exception, e:
        order_log.exception(
            "Error saving delivery notes to cart %s" % order.id)
        delivery_details = {}

    if request.POST['del_address'] == 'new':
        if shipping_info_form.is_valid():
            is_valid_shipping_address = True
            for field in shipping_info_form.fields:
                delivery_details.update({
                    field:shipping_info_form.cleaned_data[field]})
            order.save_address(request, delivery_address=delivery_details,
                type='delivery')
    else:
        addressbook_id = request.POST.get('del_address', None)
        try:
            # XXX We should ensure that addresses in address book
            # XXX confirm to the validation rules of new addresses
            addressbook = AddressBook.objects.get(id=addressbook_id)
            shipping_info_form = ShippingInfoForm(addressbook=addressbook)
            for field in shipping_info_form.fields:
                delivery_details.update({
                    field:shipping_info_form.fields[field].initial})
            order.save_address(request, delivery_address=delivery_details,
                type='delivery')
            is_valid_shipping_address = True
        except Exception, e:
            order_log.exception(
                "Error saving address to cart %s from addressbook %s" % (
                order.id, addressbook_id))
    
    return (is_valid_shipping_address, shipping_info_form.errors, 
        shipping_info_form)

def validate_card_info(request, **kwargs):
    payment_attempt = kwargs.get('payment_attempt', None)

    user_ip = request.META.get('REMOTE_ADDR', None)
    # We set the X-REAL-IP header as the webservers are located behind
    # loadblancers and reverse proxies. REMOTE_ADDR is always local ip
    if 'X-REAL-IP' in request.META:
        user_ip = request.META['X-REAL-IP']
    card_type = request.POST.get('card_type')

    is_valid = True
    status = 'Review'
    validation_response = None

    card_details = None
    card_form = CreditCardForm(request.POST)
    errors = []
    
    if not card_form.is_valid():
        is_valid = False
        for error in card_form.errors:
            errors.append(card_form.errors[error])
    
    else:
        card_details = card_form.cleaned_data
        if request.client.domain == utils.VISA_DOMAIN:
            if card_details['card_no'][0] != '4':
                is_valid = False
                errors.append('You have to pay using a VISA card. \
                The card you have supplied is not a VISA card')
    
        if is_valid:
            if payment_attempt and payment_attempt.amount >= Decimal('2500'):
                # Check if risk management system okays the card and stuff
                try:
                    # XXX ebs_check should be renamed to risk_check
                    status = payment_attempt.check_risk(
                        request, card_details=card_details,
                        card_type=card_type, user_ip=user_ip)
                    if status == 'Rejected':
                        is_valid = False
                        errors.append("We are not able to verify your \
                        card's billing info. Please try with a different card")
                except Exception, e:
                    order_log.exception("Error during risk management check")
                
    return is_valid,  errors, card_details


def get_gateway_request(request, **kwargs):
    # XXX I think this should be split into two parts
    # XXX one to call the PG handshake and other to redirect
    gateway = kwargs.get('gateway')
    bank = kwargs.get('bank', None)
    payment_attempt = kwargs.get('payment_attempt', None)
    
    card_details = None
    gateway_request = None
    errors = []
    is_valid = True # By default set true
    prefix = 'payments'
    if gateway in ('hdfc-emi', 'hdfc-card'):
        is_valid, validation_errors, card_details = validate_card_info(
            request, payment_attempt=payment_attempt)
        if not is_valid:
            # XXX Whats the case for is_valid False and no validation_errors
            validation_errors = validation_errors #if validation_errors else utils.DEFAULT_PAYMENT_PAGE_ERROR
    	    errors = validation_errors

    if is_valid:
        payment_request = payment_attempt.get_gateway_request(
            request, gateway=gateway, 
            bank=bank, card_details=card_details)
        if payment_request:
            if gateway == 'cc_avenue':
                gateway_request = render_to_response(
                    '%s/%s' % (prefix, 'cc_avenue.html'),
                        dict(payment_form=payment_request),
                        context_instance=RequestContext(request))
            
            elif gateway in ('hdfc-emi', 'hdfc-card'):
                term_url = 'http://%s/orders/process_payment_hdfc' % request.client.domain
                gateway_request = render_to_response(
                    '%s/%s' % (prefix, 'hdfc_redirect.html'),
                    dict(redirect_url=payment_request.get('redirectUrl'),
                        pareq=payment_request.get('pareq'),
                        payment_id=payment_request.get('payment_id'),
                        term_url= term_url,
                        ),
                    context_instance=RequestContext(request))
            
            elif gateway.startswith('innoviti') or gateway.startswith('axis') or gateway.startswith('amex'):
                html = None
                if gateway.startswith('innoviti'):
                    html = 'innoviti_redirect.html'
                elif gateway.startswith('axis'):
                    html = 'axis_redirect.html'
                elif gateway.startswith('amex'):
                    html = 'amex_redirect.html'
                
                gateway_request = render_to_response(
                    '%s/%s' % (prefix, html),
                    dict(json = payment_request),
                    context_instance=RequestContext(request))
            
            elif gateway in ('citi-emi', 'citi-card'):
                gateway_request = render_to_response(
                    '%s/%s' % (prefix, 'citi_redirect.html'),
                    dict(
                    redirect_url = payment_request.get('redirect_url'),
                    citi_param_value = payment_request.get('citi_param_value'),
                    ),
                    context_instance=RequestContext(request))
            
            elif gateway in ('ATOM', 'PAYM'):
                return payment_request, errors

            #For all other payment gateway, directly get the redirect url
            else:
                gateway_request = HttpResponseRedirect(payment_request)
    return gateway_request, errors
    

def get_deferred_payment_response(request, **kwargs):
    pending_order = kwargs.get('pending_order')
    payment_attempt = kwargs.get('payment_attempt')
    payment_mode_code = kwargs.get('payment_mode_code')
    gateway = request.POST.get('payment_gateway', payment_mode_code)
    bank  = request.POST.get('bank')
    page = kwargs.get('page')
    deferred_payment_response = None
    deferred_payment_error = None
    
    payment_attempt.bank = bank
    if payment_mode_code == 'atom':
        gateway = 'ATOM'
    elif payment_mode_code == 'paymate':
        gateway = 'PAYM'
    payment_attempt.gateway = gateway
    if payment_mode_code == 'cod':
        payment_attempt.gateway = 'COD'
    elif payment_mode_code == 'cheque':
        payment_attempt.gateway == 'CHEQ'
    payment_attempt.payment_mode = payment_mode_code
    # No need to save payment_attempt as it is saved when move state is called 
    payment_attempt.move_payment_state(request,
        agent=utils.get_user_profile(request.user),
        payment_mode_code=payment_mode_code, action='booked')

    confirmed_orders_in_session = request.session.get(
            'confirmed_orders', [])
    confirmed_orders_in_session.append(pending_order.id)
    request.session['confirmed_orders'] = confirmed_orders_in_session
    utils.clear_cart(request, pending_order)
    
    # Set max delivery days
    order_items = pending_order.get_order_items(request,
        select_related=('seller_rate_chart__product',),
        exclude=dict(state__in=['cancelled','bundle']))
    pending_order.set_max_days_for_delivery(request, order_items=order_items)
    
    if payment_mode_code not in ('cod', 'card-moto'):
        # no need to send pending order notification for cod because order 
        # will be confirmed
        try:
            pending_order.notify_pending_order(request)
        except Exception, e:
            order_log.exception("Unable to send pending order notification'")

    if page == 'book':
        deferred_payment_response = HttpResponseRedirect(
            request.path.replace(page,'%s/booked' % pending_order.id))
    else:
        # XXX Assuming page = payment_mode
        deferred_payment_response = HttpResponseRedirect(
            request.path.replace('payment_mode', '%s/confirmation' % pending_order.id))
    return deferred_payment_response
            
    
@never_cache
def payment_mode(request, **kwargs):
    page = None
    if 'payment_mode' in request.path:
        page = 'payment_mode'
    elif 'book' in request.path:
        page = 'book'

    cart = get_cart(request)
    # XXX How can the client be changed at time of booking?
    # XXX If the cart does not belong to this client, then even the items
    # XXX perhaps do not belong to this client. Allowing for change of client
    # XXX is very dangerous. Commenting out reading client from request. 

    # Do not use client from cart as it can be changed at the time of booking
    #client = request.client.client
    client = cart.client

    # XXX Whats this? When is this possible? Why raise an error
    # XXX catch it and redirect? Why not redirect inside the if statement
    if not cart.get_item_count():
        order_log.error("No items in cart %s in payment page. \
            Redirecting to mycart" % cart.id)
        return HttpResponseRedirect(request.path.replace(page, 'mycart'))
    
    gateway_errors = []
    inventory_errors = []
    form_errors = []
    
    # No exception since cart already exists 
    # XXX Why pass the client parameter?
    pending_order = cart.get_or_create_pending_order(request, client=client)
    address_info = pending_order.get_address(request, type='delivery').address

    # PaymentModes that are eligible for cart (fmemi, cod, cc emi)
    # XXX What are we doing here? Are we enabling conditional payment modes?
    # XXX what is the purpose of getting only first payment_option?
    payment_options = pending_order.get_payment_options(request,
        client_domain=request.client)
    payment_mode_code = None
    if payment_options:
        payment_mode_code = payment_options[0].payment_mode.code
    
    if request.method == 'POST':
        payment_mode_code = request.POST['payment_mode']
        try:
            #with transaction.commit_on_success():
            #    pending_order.payment_mode = payment_mode_code
            #    pending_order.save()
                # XXX Saving in session will cause CC orders to fail.
                # XXX Imagine what happens when agent is playing around with
                # XXX two calls
            #    request.session['payment_mode_code'] = payment_mode_code
            #    order_log.info(
            #        "Before checking availabilty payment_mode is %s" % payment_mode_code)

                # XXX I think this should not be commented or is it obsolete?
                #inventory_errors = deplete_inventory(request, pending_order)

                # XXX payment_mode is not defined yet. Surprised that it did
                # XXX not break yet -- or I missed something
                if (payment_mode_code not in utils.DEFERRED_PAYMENT_MODES) and \
                    (utils.get_chaupaati_marketplace() != pending_order.client):
                    #try:
                        # XXX It is better to write a deplete_inventory or
                        # XXX block inventory call rather than call 
                        # XXX update inventory with an action parameter
                        pending_order.update_inventory(request, action='deplete')
                    #except Order.InventoryError, e:
                    #    inventory_errors = e.errors
                    #    raise e
               
                # XXX inventory_errors get set in an exception, which is then
                # XXX raised. So if inventory_errors are present, then this
                # XXX code will never be hit, which means there is no need
                # XXX for if check here. Commenting it out
                #if not inventory_errors:
                if utils.is_cc(request): #p. clients
                    return book_order(request, pending_order, 
                        payment_mode_code)
                else:
                    payment_attempt = pending_order.create_payment_attempt(
                        request, domain=request.client, 
                        payment_mode_code=payment_mode_code,
                        emi_plan=request.POST.get('emi_plan', ''))
                    
                    # XXX I think the previous check should also be for
                    # XXX payment_mode_code. You were checking for payment_mode
                    if (payment_mode_code in utils.DEFERRED_PAYMENT_MODES) or \
                        (payment_mode_code == 'cod'):
                        defer_payment_resp = get_deferred_payment_response(
                            request, 
                            payment_attempt = payment_attempt,
                            payment_mode_code = payment_mode_code,
                            pending_order=pending_order)
                        return defer_payment_resp

                    else:
                        # Instant payments without inventory errors
                        bank, gateway = get_bank_and_gateway(request,
                            payment_mode_code, client)
                        response, gr_errors = get_gateway_request(request, gateway=gateway, 
                                payment_attempt=payment_attempt, bank=bank)
                        if not response:
                            gateway_errors.extend(gr_errors)
                        else:
                            return response
                            
        except cart.CouponAlreadyAttached, e:
            gateway_errors.append(e.message) 
        except FieldError, e:
            form_errors = e.message
        except Order.InventoryError, e:
            order_log.exception("Inventory errors for cart %s. %s" % (
                pending_order.id,
                e.errors))
            inventory_errors = e.errors
        except PaymentAttempt.NoResponseFromPG, e:
            order_log.exception(
                "Error creating payment attempt with PG: %s %s %s" % (payment_mode_code, 
                    gateway, e.message))
            gateway_errors.append(e.message)

        except Exception, e:
            # catch all the exception and return to either shipping page 
            # or payment page base on request method and with proper errors
            order_log.exception(
                "Unknown error in %s page for order: %s" % (
                    page, pending_order.id))
            if page == 'book':
                gateway_errors.append(
                    "We are unable to book this order. Please try again")
            else:
                gateway_errors.append(
                    "We are unable to process this order. Please try again")
                

    pending_payment = None
    price_mismatch_error = None
    failed_payment = None
    html = 'online_payment_modes.html'
    
    if utils.is_cc(request):
        html = 'book.html'
    
    if 'payment_mode_code' in request.session:
        # XXX Should not store in session directly. Use utils.get_session_obj
        payment_mode_code = request.session['payment_mode_code']
        del request.session['payment_mode_code']

    if 'failed_payment' in request.session:
        # XXX Should not store in session directly. Use utils.get_session_obj
        failed_payment = request.session['failed_payment']
        del request.session['failed_payment']
        gateway_errors.append(failed_payment)

    return render_to_response('payments/%s' % html,
            dict(payment_options = payment_options,
                order=pending_order,
                payment_mode_code = payment_mode_code,
                form_errors = form_errors,
                errors = gateway_errors,
                inventory_errors = inventory_errors,
                address_info = address_info, 
                ),
        context_instance = RequestContext(request))

def get_bank_and_gateway(request, payment_mode_code, client):
    bank = request.POST.get('bank',None)
    card_type = request.POST.get('cardtype', 'master-card')
    gateway = None
    
    order_log.info("Payment code is %s" % payment_mode_code)
    if payment_mode_code == 'netbanking':
        gateway = 'cc_avenue'

    elif payment_mode_code == 'payback':
        gateway='payback'

    elif payment_mode_code in ('credit-card-emi-web', 'credit-card', 'debit-card'):
        if payment_mode_code == 'credit-card-emi-web':
            if bank:
                if bank == 'citi':
                    gateway = 'citi-emi'
                elif bank in ('icici', 'stanchart') :
                    gateway = 'icici-emi'
                elif bank == 'hdfc':
                    gateway = 'hdfc-emi'
                elif bank.startswith('innoviti'):
                    gateway = 'innoviti'
                    bank = bank.split('-')[1]
                else:
                    gateway = bank
            else:
                #gateway = 'hdfc-emi'
                gateway = 'icici-emi'

        elif payment_mode_code in ('credit-card', 'debit-card'):
            default_gateway = 'icici-card'
            gateway = None
            if card_type:
                if card_type == 'amex-card':
                    gateway = 'amex-card'
            
            elif bank:
                if bank == 'citi':
                    gateway = 'citi-card'
                elif bank == 'icici':
                    gateway = 'icici-card'
                elif bank == 'hdfc':
                    gateway = 'hdfc-card'
                elif bank == 'axis':
                    gateway = 'axis-card'
                elif bank == 'amex':
                    gateway = 'amex-card'

            else:
                if utils.is_ezoneonline(client):
                    gateway = 'icici-card'

            if not gateway:
                #gateway = 'axis-card'
                #gateway = 'hdfc-card'
                gateway = default_gateway
        
    elif payment_mode_code in ('atom', 'paymate'):
        gateway = payment_mode_code
    
    return bank, gateway

def render_online_payment_page(request):
    params = None
    if request.POST:
        params = request.POST
    else:
        params=request.GET
    payment_mode_code = params.get('payment_mode_code')
    client = request.client.client
    domain = request.client
    html = payment_page_html(request, payment_mode_code=payment_mode_code,
        domain=domain)
    gateway_options = None
    card_form = None
    # XXX order_id is not optional
    order_id = params.get('order_id')
    order = Order.objects.get(id=order_id)

    if payment_mode_code in ("cash-collection", "atom", "paymate", "deposit"):
        gateway_options = PaymentGateways.objects.filter(
            payment_mode__code = payment_mode_code)
        emi_1500_exclude_list = ['HDF3', 'HDF6', 'HDF9', 'ICI3', 'ICI6', 'ICI9']
        if order.payable_amount < 1500:
            gateway_options = gateway_options.exclude(code__in=emi_1500_exclude_list) #for gateway in gateway_options:
    else:
        # XXX I was expecting that this block will do some thing on
        # XXX on gateway_options. But it does something completely different
        # XXX Though this code works, its completely unreadable. Please avoid
        # XXX writing code like this. You can set the card_form when
        # XXX payment_mode_code is credit card.
        card_form = CreditCardForm()
    
    # XXX should be cached
    po = PaymentOption.objects.get(client=client,
        payment_mode__code=payment_mode_code)
    billing_info_form = None
    shipping_address = None
    
    # for cod mode
    mobile_num = None
    cod_status = 'neutral'
    if payment_mode_code == 'cod':
        # check if user is cod verified. if verified let him place order 
        # directly without zipdial verification.
        profile = order.user 
        cod_status = profile.cod_status
        if cod_status == 'neutral':
            if utils.is_cc(request):
                cod_status = 'whitelisted'
            else:
                # XXX We are not maintaining this field. Not sure if we should
                # XXX read from it
                mobile_num = profile.primary_phone
                
    if po.payment_mode.validate_billing_info:
        try:
            shipping_address = order.get_address(request, type='delivery')
            billing_info = order.get_address(request, type='billing')
        except BillingInfo.DoesNotExist:
            billing_info = None
        except Exception, e:
            order_log.warning(
                "Error getting order addresses for %s. \
                Setting billing info to None" % order.id)
            billing_info = None
        billing_info_form = BillingInfoForm(info=billing_info)
    return render_to_response('%s' % html,
            {'card_form': card_form,
                'shipping_address':shipping_address,
                'billing_info_form': billing_info_form,
                'order':order,
                'po':po,
                'gateway_options':gateway_options,
                'points': "%i" % (order.payable_amount*4,),
                'order_amount':order.payable_amount,
                'phone': mobile_num,
                'cod_status': cod_status,
            },
            context_instance=RequestContext(request))

def get_emi_options(request):
    params = request.GET
    bank = params.get('bank', None)
    amount = int(params.get('amount', 0))
    if not bank or not amount:
        return HttpResponse("")
    transaction_charges = {
        'innoviti-axis':{             
            '3months':1.85,
            '6months':3.75,
            '9months':6.10,
        },
        'innoviti-citi':{
            '3months':1.45,
            '6months':3.45,
        },
        'hdfc':{             
            '3months':0,
            '6months':4.20,
            '9months':6.85,
        },
        'icici':{
            '3months':0,
            '6months':4.20,
            '9months':6.30,
        },
        'stanchart':{
            '3months':0,
            '6months':4.20,
            '9months':6.30,
        },
        'innoviti-kotak':{
            '3months':1.80,
            '6months':3.50,
            '9months':6.25,
        },
        'innoviti-sbi':{
            '3months':1.75,
            '6months':3.80,
            '9months':6.25,
        },
        'innoviti-hsbc':{
            '3months':2.00,
            '6months':4.00,
        },
    }

    applicable_months = []
    emi_plans = utils.compute_emi(amount)
    emi_datas = []
    if bank == 'innoviti-citi' or bank == 'innoviti-hsbc':
        applicable_months = [3, 6]        
    else:
        applicable_months = [3, 6, 9]
    transaction_charge = transaction_charges[bank]
    for month in applicable_months:
        data = {}
        data['month'] = month
        data['emi_plan'] = emi_plans['%smonths' %  month]
        data['transaction_charge'] = int(round((transaction_charge['%smonths' % month]/100) * amount))
        emi_datas.append(data)

    return render_to_response('payments/innoviti_emi_options.html',
            {
                'emi_datas':emi_datas,
            },
            context_instance=RequestContext(request))

def payment_page_html(request, **kwargs):
    payment_mode_code = kwargs.get('payment_mode_code')
    prefix = 'payments'
    if utils.is_cc(request):
        prefix='payments/book'
    html = '%s.html' % payment_mode_code
    
    if payment_mode_code == 'credit-card':
        html = 'credit_card.html'
    
    if payment_mode_code == 'debit-card':
        html = 'debit_card.html'
    
    if payment_mode_code == 'fmemi':
        html = 'fmemi.html'
    
    if payment_mode_code == 'credit-card-emi-web':
        html = 'credit_card_emi_web.html'
    
    if payment_mode_code == 'netbanking':
        html = 'netbanking.html'
    
    if payment_mode_code == 'cod':
        html = 'cod.html'

    if payment_mode_code == 'cash-collection':
        html = 'cash-collection.html'
    
    if payment_mode_code == 'payback':
        html = 'payback.html'
    
    if payment_mode_code in ('atom', 'paymate'):
        html = 'ivr.html'
    
    return '%s/%s' %(prefix,html)

@never_cache
def validate_billing_info(request):
    # XXX Is this called through ajax?
    billing_info_form = BillingInfoForm(request.POST)
    billing_address = {}
    order_id = request.POST.get('order_id')
    if billing_info_form.is_valid():
        for field in billing_info_form.fields:
            billing_address.update(
                {field:billing_info_form.cleaned_data[field]})
        try:
            order = Order.objects.get(id=order_id)
            order.save_address(request, type='billing',
                billing_address=billing_address)
        except Exception, e:
            order_log.exception(
                "Error saving billing address to order %s" % order_id)
            return HttpResponse(simplejson.dumps(
                dict(
                status="error", 
                errors={
                'error':'We are unable to process your order. Please try again'}
                )))

        return HttpResponse(simplejson.dumps(dict(status="ok")))
    
    else:
        #if billing info form is not valid
        return HttpResponse(simplejson.dumps(dict(
            status="error", error=billing_info_form.errors)))


@never_cache
def signin(request):
    return signin_wo_cache(request)

def signin_wo_cache(request):
    username = None
    profile = None
    if request.user.is_authenticated():
        return HttpResponseRedirect(request.path.replace('signin','shipping'))
    
    cart = get_cart(request)
    if not cart.get_item_count():
        return HttpResponseRedirect(request.path.replace('signin','mycart'))
    else:
        error = None
        next_page = True
        if request.method == 'POST' and 'username' in request.POST:
            params = request.POST
            username = params.get('username', '')

            user_type, is_valid_username = validate_username(
                request, username=username)
            if is_valid_username and user_type:
                cart.state = 'guest_cart'
                have_account = params.get('have_account', False)
                password = params.get('password', None)
                continue_with = params.get('continue_with', None)
                if utils.is_valid_email(username):
                    username = utils.check_special_characters(username)
                if continue_with:
                    # XXX I dont think we should trigger this event here
                    # XXX more because sending sms is network operation
                    # XXX An error in reset password is also not critical
                    # XXX enough to block booking of order. I've turned off
                    # XXX sending error from reset_password

                    # XXX Continue with should be more tolerant to new users
                    # XXX This will stop new users from continuing.
                    profile, error = reset_password(request, username,
                        user_type)
                    # XXX Adding extra checks to make it more tolerant.
                    # XXX Please review
                   
                    if not profile:
                        try:
                            user, profile = utils.get_or_create_user(username)
                        except Exception, e:
                            order_log.exception(
                                'Error fetching user for new user continue with \
                                checkout %s' % username)
                            error = "We are unable to process your order. \
                            Please try again."
                        else:
                            if not (user or profile):
                                order_log.error(
                                    'Error fetching user for guest checkout. \
                                    Username: %s User:%s Profile: %s' % (
                                    username, user, profile))
                                error = "We are unable to process your order. \
                                Please try again later"
                elif have_account:
                    user = auth.authenticate(username=username,
                        password=password, **dict(request=request))
                    if user is not None and user.is_active:
                        try:
                            auth.login(request, user)
                            profile = utils.get_user_profile(user) 
                            cart.state = 'temporary_cart' #User logged in
                        except Exception, e:
                            order_log.exception(
                                'Error in order signin username: %s' % username)
                            error = "We are unable to log you in. \
                            Please try again later"
                    else:
                        if user and not user.is_active:
                            # XXX We should give a way to trigger verification
                            error = 'Your account is not verified, please \
                            verify your account to proceed'
                        else:
                            error = "Incorrect username or password"
                else:
                    # Guest checkout. Create a new user and profile 
                    # and attach with cart
                    try:
                        user, profile = utils.get_or_create_user(username)
                    except Exception, e:
                        order_log.exception(
                            'Error fetching user for guest \
                            checkout %s' % username)
                        error = "We are unable to process your order. \
                        Please try again."
                    else:
                        if not (user or profile):
                            order_log.error(
                                'Error fetching user for guest checkout. \
                                Username: %s User:%s Profile: %s' % (
                                username, user, profile))
                            error = "We are unable to process your order. \
                            Please try again later"
                if not error: 
                    cart.user = profile
                    cart.save()
                    return HttpResponseRedirect('/orders/shipping')
            else:
                error = "Please enter a valid email or mobile"
    
    signin_response = dict(order=cart,
                        error=error, 
                        username=username)
    
    return render_to_response('order/signin.html',
            signin_response,
            context_instance=RequestContext(request))

def validate_username(request, **kwargs):
    username = kwargs.get('username')
    user_type = None
    is_valid = False
    if utils.is_valid_mobile(username):
        user_type = 'phone'
        is_valid = True
    
    elif utils.is_valid_email(username):
        user_type = 'email'
        is_valid = True

    return user_type, is_valid


def reset_password(request, username, user_type):
    from web.views.user_views import forgotpwd_send_email, forgotpwd_send_sms
    profile = None
    error = None
    try:
        profile = Profile.objects.get(user__username = username)
        if not profile.verify_code:
            verify_code = random.getrandbits(20)
            profile.verify_code = verify_code
            profile.save()
        
        if user_type == 'email':
            # XXX This might cause p.futurebazaar links
            domain = request.META['HTTP_HOST']
            link = "http://%s/%s/?id=%s&code=%s" % (domain,
                'user/resetpassword',
                profile.id,
                profile.verify_code)

            # XXX No point blasting emails to all ids for user.
            # XXX Sending to the requested username is sufficient
            emails = UserEmail.objects.filter(user=profile, email=username)
            forgotpwd_send_email(request, profile, emails, link)
            return profile, None
        elif user_type == 'phone':
            phones = UserPhone.objects.filter(user=profile)
            forgotpwd_send_sms(profile, phones, request.client.client)
    except Profile.DoesNotExist:
        pass
    except Exception, e:
        order_log.exception(
            "Unknown error in resetting password for %s" % username)
        # Not rising error if unable to reset password.
        return profile, None
    return None, None

def get_order_item_form(request, **kwargs):
    data = kwargs.get('data') 
    new_state = kwargs.get('new_state')
    
    from orders.forms import OrderItemForm
    form = None
    if new_state not in ['stock expected','delivery created',
        'raised po','po already raised']:
        return form
    form = OrderItemForm(data)
    if new_state == 'stock expected':
        form.fields.pop('delivery_no')
        form.fields.pop('notes')
        form.fields.pop('po_number')
        form.fields.pop('po_date')
    elif new_state == 'delivery created':
        form.fields.pop('expected_stock_arrival')
        form.fields.pop('notes')
        form.fields.pop('po_number')
        form.fields.pop('po_date')
    else:
        form.fields.pop('delivery_no')
    return form

@never_cache
def get_cvv_info(request):
    return render_to_response('order/cvv_info.htm',
        None,
        context_instance=RequestContext(request))


def next_page_after_shipping(request, cart):
    domain = request.client
    # on web for Tinla Client, we proceed to payment gateway
    pending_order = cart.get_or_create_pending_order(request)
    payment_mode_code = 'credit-card'                                    
    pending_order.payment_mode = payment_mode_code
    pending_order.sync_non_item_info(request, order=cart)
    pending_order.save()
    gateway = 'icici-card'
    if not cart.client == utils.get_chaupaati_marketplace():
        pending_order.update_inventory(request, action='deplete')
    pa = pending_order.create_payment_attempt(request, domain=domain, 
            payment_mode_code=payment_mode_code)
    return HttpResponseRedirect(pa.get_gateway_request(request, gateway=gateway))

@never_cache
def initialize_ivr(request):
	pass
