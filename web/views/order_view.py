from orders.models import *
from users.helper import *
from utils import utils
from utils.utils import check_dates
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponsePermanentRedirect
from django.template import RequestContext
from catalog.models import *
from locations.models import *
from orders.forms import *
from users.models import Profile, Email as UserEmail,Phone
from feedback.models import Feedback
from django.contrib import auth
from django.contrib.auth.models import User
from django.core.mail import EmailMessage, send_mail
from payments.models import PaymentAttempt
from promotions.models import Coupon, ScratchCard
from django.contrib.auth.decorators import login_required
from payments import hdfcpg
from django.template.loader import get_template
from django.template import Context, Template
import re
import pyExcelerator
from payments import ccAvenue
import logging
from django.utils import simplejson
from datetime import datetime,timedelta
from django.db.models import Sum
from lists.models import *
import operator
import gviz_api
import random
from django.views.decorators.cache import never_cache
from notifications.notification import Notification
from notifications.email import Email
from notifications.sms import SMS
from django.utils.safestring import mark_safe
from django.views.decorators.cache import cache_control
from django.conf import settings
import random
from django.http import HttpResponseRedirect
from decimal import Decimal, ROUND_FLOOR

log = logging.getLogger('fborder')

def get_or_create_user_cart(request, user, **kwargs):
    profile = utils.get_user_profile(user)
    try:
        orders = Order.objects.filter(user=profile,state='cart',client=request.client.client)[:1]
        if orders:
            return orders[0]
    except Order.DoesNotExist:
        pass
    if kwargs.get('create', True):
        # Create by default
        cart = Order(state='cart', user=profile,client=request.client.client)
        cart.save() 
    else:
        # Do not create if not asked for
        return None
    return cart

def create_new_cart(request):
    cart = Order(state='cart',client=request.client.client)
    cart.save()
    return cart

def next_checkout_action(request, admin_order_id=None):
    # options for tab are
    # mycart, shipping, payment_info in the admin process
    # mycart, signin, shipping, process_payment in web process
    # mycart, shipping, book in call center process
    domain = request.META['HTTP_HOST']
    ADMIN = 'auth'
    MYCART = 'mycart'
    SHIPPING = 'shipping'
    SIGNIN = 'signin'
    BOOK = 'book'
    PROCESSPAYMENT = 'process_payment'
    PAYMENTINFO = 'payment_info'
    BOOKED = 'booked'
    CONFIRMATION = 'confirmation'
    CANCELLATIONINFO = 'cancellation_info'
    sp = request.path.split('/')
    tab = sp[-1]
    action = ''
    if tab == MYCART:
        if not request.user.is_authenticated():
            if utils.is_cc(request):
                action = SHIPPING
            if request.path.startswith('/orders/auth/'):
                action = SHIPPING
            else:
                action = SIGNIN
        else:
            if request.path.startswith('/orders/cancel/'):
                action = CANCELLATIONINFO
            elif domain in utils.MOBILE_DOMAIN:
                action = SIGNIN
            else:
                action = SHIPPING
    if tab == SIGNIN:
        action = SHIPPING

    if tab == SHIPPING:
        if utils.is_cc(request):
            action = BOOK
        if request.path.startswith('/orders/auth/'):
            action = PAYMENTINFO
        action = SHIPPING
    if request.path.startswith('/orders/auth'):
        return 'orders/auth/%s/%s' % (admin_order_id,action)
    elif request.path.startswith('/orders/cancel'):
        return 'orders/cancel/%s/%s' % (admin_order_id,action)
    else:
        if not action:
            if request.user.is_authenticated():
                action = SHIPPING
            else:
                action = SIGNIN
        return 'orders/%s' % action

#def get_cart(request, admin_order_id=None, **kwargs):
#    ''' Add an item to cart. There are various flows starting here
#        1. User is signedin: In this case, we add the item to user's cart
#           If user does not have a cart, we create one and add the item.
#        2. User is not signedin: In this case, if there is a cartId in the
#           cookie, we add the item to that cart. Otherwise we create a new
#           cart and add the item.
#        3. Callcenter: As callcenter agent can add to cart only if user is
#           selected (on-call), this is similar to the first flow, with the
#           exception that user is not the signedin user, but the user on
#           call.
#    '''
#
#    cart_id = None
#    cart = None
#    if utils.is_cc(request):
#        # call center request
#        if request.call['id'] in request.session:
#            # has a call session
#            cart_id = request.session[request.call['id']].get('cart_id',None)
#            if not cart_id:
#                # but no cart_id in the session, lets try users cart
#                user = request.session[request.call['id']]['user']
#                return get_or_create_user_cart(request, user, **kwargs)
#            else:
#                return Order.objects.get(id=cart_id,client=request.client.client)
#        else:
#            if kwargs.get('create', True):
#                # Create by default
#                return create_new_cart(request)
#            else:
#                # Dont create if asked not to
#                return None
#    elif request.path.startswith('/orders/auth/'):
#        if utils.is_future_ecom(request.client.client) or utils.is_ezoneonline(request.client.client):
#            order = Order.objects.filter(reference_order_id=admin_order_id,state='pending_order').order_by('-id')
#            if order:
#                order = order[0]
#                return order
#            else:
#                raise Http404
#        else:
#            return Order.objects.get(id=admin_order_id)
#    elif request.path.startswith('/orders/cancel/'):
#        if utils.is_future_ecom(request.client.client) or utils.is_ezoneonline(request.client.client):
#            order = Order.objects.filter(reference_order_id=admin_order_id,state__in = ['confirmed', 'modified']).order_by('-id')
#            if order:
#                order = order[0]
#                return order
#            else:
#                raise Http404
#        else:
#            return Order.objects.get(id=admin_order_id)
#    else:
#        if 'cart_id' in request.session:
#            cart = Order.objects.get(id=request.session['cart_id'])
#            return cart
#        else:
#            if request.user.is_authenticated():
#                return get_or_create_user_cart(request, request.user, **kwargs)
#            else:
#                cart_id = request.COOKIES.get('orderId', None)
#                if cart_id:
#                    return Order.objects.get(id=cart_id)
#                else:
#                    if kwargs.get('create', True):
#                        # Create by default
#                        return create_new_cart(request)
#                    else:
#                        # Do not create if not asked for
#                        return None
#
#def get_cart_and_save_in_session(request, admin_order_id = None, **kwargs):
#    cart = get_cart(request, admin_order_id, **kwargs)
#    if utils.is_cc(request):
#        if request.call['id'] in request.session and cart:
#            call_session = request.session[request.call['id']]
#            call_session['cart_id'] = cart.id
#            request.session[request.call['id']] = call_session
#    elif request.path.startswith('/orders/auth/'):
#        return cart
#    else:
#        if cart:
#            request.session['cart_id'] = cart.id
#    return cart
#
#def add_to_cart(request, admin_order_id=None):
#    cart = get_cart_and_save_in_session(request, admin_order_id)
#    rate_chart_id = request.POST.get('rate_chart_id','')
#    rate_chart = SellerRateChart.objects.get(id=rate_chart_id)
#    res = cart.add_item(request,rate_chart)
#    utils.track_add_to_cart_usage(request, rate_chart.product)
#    next_step = next_checkout_action(request, admin_order_id)
#    if res:
#        if res['responseCode'] != 'OM_ADDED_ITEM_TO_CART':
#            response = render_to_response('order/mycart.html',
#                    {
#                        'order':cart,
#                        'orderItems':cart.get_items_for_billing(request),
#                        'next_action':next_step,
#                        'post_back':request.path,
#                        'error_msg': res['responseMessage'],
#                        'apply_coupon':True,
#                    },
#                context_instance=RequestContext(request))
#            return response
#
#    next_step = next_checkout_action(request, admin_order_id)
#    utils.set_cart_count(request,cart)
#    return HttpResponseRedirect(request.path)
#
def update_item_quantity(request, admin_order_id=None):
    order = get_cart_and_save_in_session(request, admin_order_id)
    oi = order.get_items_for_billing(request).filter(
        id=request.POST.get('itemid',''))
    if oi:
        oi = oi[0]
        order = oi.order
        try:
            qty = int(request.POST.get('%s_qty' % oi.id, oi.qty))
        except:
            qty = 1
        if qty <= 0:
            qty = 1
        order.update_item_quantity(request,oi.id, qty)
        next_step = next_checkout_action(request, admin_order_id)
        utils.set_cart_count(request,order)
        return render_to_response('order/mycart.html',
            {
                'order':order,
                'orderItems':order.get_items_for_billing(request),
                'next_action':next_step,
                'post_back': request.path,
            },
            context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(request.path)


def remove_from_cart(request, admin_order_id=None):
    oi = OrderItem.objects.select_related('order').filter(
            id=request.POST.get('itemid',''))
    if oi:
        oi = oi[0]
        order = oi.order
        order.remove_item(request,oi)
        next_step = next_checkout_action(request, admin_order_id)
        utils.set_cart_count(request,order)
        return render_to_response('order/mycart.html',
            {
                'order':order,
                'orderItems':order.get_items_for_billing(request),
                'next_action': next_step,
                'post_back': request.path,
            },
            context_instance=RequestContext(request))
    else:
        return HttpResponseRedirect(request.path)

def cc_login_failure(request, redirect_to_page, *args, **kwargs):
    def parse_get_string(get_string):
        if not get_string:
            return {}
        params = get_string.split("&")
        return dict(
                [tuple(i.split("=")) for i in params])

    referer = request.META.get('HTTP_REFERER', "")
    get_params = {"cc" : "1"}
    if referer:
        url_parts = referer.split("?")
        if url_parts >= 2:
            redirect_to, get_param_string = url_parts[0], "?".join(url_parts[1:])
            get_params.update(parse_get_string(get_param_string))
        else:
            redirect_to = referer
    else:
        redirect_to = "/"

    if redirect_to_page:
        redirect_to = redirect_to_page

    get_param_string = "&".join(["%s=%s" % (k, v) for k, v in get_params.iteritems()])
    return HttpResponseRedirect("%s?%s" % (redirect_to, get_param_string))


def view_cart(request, admin_order_id = None, **kwargs):
    cart = get_cart_and_save_in_session(request, admin_order_id)
    log.info('Before Updating cart %s with the latest seller rate chart, Cart total %s' % (cart.id,cart.payable_amount))
    #if cart.state not in ['pending_order', 'confirmed', 'cancelled', 'modified']:
    cart.client = request.client.client
    cart.update_billing_from_src(request)
    log.info('After updating cart %s, Total is %s' % (cart.id, cart.payable_amount))
    if cart.state == 'temporary_cart' and utils.is_future_ecom(request.client.client):
        # TODO merge carts here
        pass 
    #cart.save()    no updates done.. so no save needed - prady
    item_found_msg = []
    readonly = False
    if utils.is_future_ecom(cart.client) or utils.is_ezoneonline(cart.client):
        if request.path.startswith("/orders/auth") or request.path.startswith("/orders/cancel"):
            readonly = True
        if utils.is_cc(request):
            id  = request.call['id']
            if id not in request.session:
                from web.views.user_views  import user_context
                user_context(request)
    next_step = next_checkout_action(request, admin_order_id)
    orderItems = cart.get_items_for_billing(request)
    utils.set_cart_count(request,cart)
    ctxt =  {
                'order':cart,
#                'orderItems':cart.orderitem_set.exclude(Q(state='cancelled') | Q(state='refunded')),
                'orderItems':orderItems,
                'next_action':next_step,
                'post_back':request.path,
                'apply_coupon':True,
                'readonly' : readonly,
            }
    get_context = kwargs.get("get_context", False)
    if get_context:
        return ctxt
    response = render_to_response('order/mycart.html',ctxt,
        context_instance=RequestContext(request))
    return response

@never_cache
@cache_control(private=True)
@cc_login_required(cc_login_failure)
def cart_actions(request, admin_order_id=None):
    if request.method == 'POST':
        action = request.POST.get('action','')
        #if not (action == 'apply_payback') and request.session.get('payback_msg'):
        #    del(request.session['payback_msg'])
        if action == 'add_to_cart':
            return add_to_cart(request, admin_order_id)
        if action == 'update_cart_item':
            return update_item_quantity(request, admin_order_id)
        if action == 'remove_cart_item':
            return remove_from_cart(request, admin_order_id)
        if action == 'remove_fb_coupon':
            if utils.is_future_ecom(request.client.client):
                return remove_fb_coupon(request)
            else:
                return remove_coupon(request)
        if action == 'apply_coupon':
            if utils.is_future_ecom(request.client.client):
                return apply_fb_coupon(request)
            else:
                return apply_coupon(request)
        if action == 'add_to_wishlist':
            return add_to_wishlist(request, admin_order_id)
        if action == 'apply_payback':
            return apply_payback(request)

    return view_cart(request, admin_order_id)


def fetch_state_country_city_by_pincode(request,params, cart):
    pincode = params['zip']
    name = params['name']
    requesturl = 'http://api.geonames.org/postalCodeLookupJSON?postalcode=' + pincode  + '&country=IN&username=shagun'
    import urllib2
    doc = urllib2.urlopen(requesturl)

    decoder = simplejson.JSONDecoder()
    json = decoder.decode(doc.read())
    postal_codes = json['postalcodes']
    if postal_codes:
        state_name = postal_codes[0]['adminName1']
        city_name = postal_codes[0]['adminName2']
        country_name = 'India'
        try:
            delivery_info = DeliveryInfo.objects.select_related('address').get(order=cart)
            address = delivery_info.address
        except DeliveryInfo.DoesNotExist:
            delivery_info = DeliveryInfo()
            address = Address()
        address.pincode = pincode

        country = utils.get_or_create_country(country_name, True)

        state = utils.get_or_create_state(state_name, country, True)

        city = utils.get_or_create_city(city_name, state, True)

        address.city = city
        address.state = state
        address.country = country
        address.type = 'delivery'
        address.name = name
        address.phone = params['mobile'] if 'mobile' in params  else request.user.username
        address.created_on = datetime.now()
        address.save()
        delivery_info.address = address
        delivery_info.order = cart
        delivery_info.save()

def validate_signin_for_mobile_web(params):
    error = None
    if 'mobile_web' in params:
        name = params['name']
        pincode = params['zip']
        if not name:
            return 'Please enter your name'
        if not pincode:
            return 'Please enter your pincode'
    mobile = params.get('mobile','')
    if not utils.is_valid_mobile(mobile)  and not utils.is_valid_email(mobile):
        error = 'Please enter a valid 10 digit mobile or email.'
    return error


def signup(request):
    from web.views import user_views
    error, redirect_to, usr = user_views.validate_signup(request)
    if not error:
        # Signup done lets add items from guest cart into atg cart
        profile = Profile.objects.get(user=usr)
        cart = get_cart_and_save_in_session(request)
        cs = utils.get_session_obj(request)
        fbapi = FuturebazaarAPI(request,profile,cart)
        user_cart = get_or_create_user_cart(request, usr)
        cs['cart_id'] = user_cart.id
        utils.set_session_obj(request,cs)
        resp, redirect_to_mycart = fbapi.sync_cart_for_checkout(request, cart, user_cart)
        cs = utils.get_session_obj(request)
        cs['fbapiobj'] = fbapi
        if resp:
            cs['sync_errors'] = resp
        utils.set_session_obj(request,cs)
        cart.user = profile
        cart.save()
        return user_views.login_and_redirect(request, usr, '/orders/shipping', **dict(is_redirect=True))
    response = render_to_response('order/signin.html', {
            'signup_error': error,
            'next':redirect_to,
            'signup_username': usr
        },
        context_instance=RequestContext(request)
        )
    return response


@never_cache
def signin(request):
    if request.user.is_authenticated():
        response = HttpResponseRedirect(request.path.replace('signin','shipping'))
        return response
    cart = get_cart_and_save_in_session(request)
    if not cart.get_items_for_billing(request):        
        next_request_path = get_mycart_next_url(request, "signin")
        response = HttpResponseRedirect(next_request_path)
        return response

    if request.method == 'POST' and request.user.is_authenticated() and 'mobile_web' in request.POST:
        params = request.POST
        error = None
        error = validate_signin_for_mobile_web(params)
        if error:
            return render_to_response('order/signin.html',
               {'error':error},
                context_instance=RequestContext(request))
        if 'mobile_web' in params:
            name = params['name']
            profile = utils.get_user_profile(request.user)
            if not profile.full_name:
                profile.full_name = name
                profile.save()
            cart.user = profile
            cart.save()
        if 'mobile_web' in params:
            fetch_state_country_city_by_pincode(request,params, cart)
        else:
            profile = utils.get_user_profile(request.user)
            if utils.is_future_ecom(request.client.client):
                cs = utils.get_session_obj(request)
                cs['atg_username'] = params['mobile']
                fbapi = FuturebazaarAPI(request,profile,cart)
                for item in cart.get_items_for_billing(request).iterator():
                    fbapi.add_item_to_fb_cart(request,item.seller_rate_chart,item.qty)
                #fbapi.sync_cart(request,cart)
                cs['fbapiobj'] = fbapi
                utils.set_session_obj(request,cs)
                #utils.initialize_fb_api(request,profile)
        response = HttpResponseRedirect(request.path.replace('signin','shipping'))
        return response
    elif request.method == 'POST' and 'mobile' in request.POST:
        log.info('request params %s' % request.POST)
        params = request.POST
        action = params.get('action', 'guest-user')
        mobile = params.get('mobile','')
        error = None

        error = validate_signin_for_mobile_web(params)
        if error:
            return render_to_response('order/signin.html',
               {'error':error},
                context_instance=RequestContext(request))
        input_type = "id"
        continue_with = request.POST.get('continue_with','')
        if utils.is_valid_email(mobile):
            input_type = 'email'
            if continue_with == 'Continue with your order now':
                action = 'guest-user'
                try:
                    profile = Profile.objects.get(user__username__exact = mobile)
                    if not profile.verify_code:
                        verify_code = random.getrandbits(20)
                        profile.verify_code = verify_code
                    profile.save()
                    link = request.get_host()
                    link = "http://%s/%s/?id=%s&code=%s" % (link,'user/resetpassword',profile.id,profile.verify_code)

                    emails = UserEmail.objects.filter(user=profile)
                    t_body = get_template('notifications/users/forgotpassword.email')
                    email_body = {}
                    email_body['profile'] = profile
                    email_body['link'] = mark_safe(link)
                    email_body['verify_code'] = profile.verify_code
                    email_body['signature'] = request.client.client.signature
                    c_body = Context(email_body)
                    t_subject = get_template('notifications/users/forgotpassword_sub.email')
                    email_from = {}
                    email_subject = {}
                    c_subject = Context(email_subject)
                    mail_obj = Email()
                    mail_obj._from = request.client.client.noreply_email
                    mail_obj.body = t_body.render(c_body)
                    mail_obj.subject = t_subject.render(c_subject)
                    u_emails = ""
                    for x in emails:
                        u_emails = "%s,%s" %(x.email,u_emails)
                    u_emails = u_emails.strip(',')
                    mail_obj.to = u_emails
                    mail_obj.send()
                except:
                    profile =None
        elif utils.is_valid_mobile(mobile):
            input_type = "mobile"
            if continue_with == 'Continue with your order now':
                action = 'guest-user'
                try:
                    profile = Profile.objects.get(user__username__exact = mobile)
                    phones = Phone.objects.filter(user=profile)
                    if not profile.verify_code:
                        verify_code = random.getrandbits(20)
                        profile.verify_code = verify_code
                    profile.save()
                    forgotpwd_send_sms(request,profile,phones)
                    t_sms = get_template('notifications/users/forgotpassword.sms')
                    sms_content = {}
                    sms_content['profile'] = profile
                    c_sms = Context(sms_content)
                    sms_text = t_sms.render(c_sms)
                    sms = SMS()
                    sms.mask = request.client.client.sms_mask
                    sms.text = sms_text
                    u_phones = ""
                    for x in phones:
                        u_phones = "%s,%s" %(u_phones,x.phone)
                    u_phones = u_phones.strip(',')
                    sms.to = u_phones
                    sms.send()
                except:
                    profile = None
        else:
            input_type = "id"
        if input_type == "id" or not mobile:
            error = 'Please enter a valid Email / Mobile'

        if error:
            return render_to_response('order/signin.html',
                {'error':error},
                context_instance=RequestContext(request))
        if action == 'guest-user':
            mobile = params['mobile']
            error = validate_signin_for_mobile_web(params)
            if error:
                return render_to_response('order/signin.html',
                    {'error':error},
                    context_instance=RequestContext(request))
            usr, profile = utils.get_or_create_user(mobile)
            user_cart = Order.objects.filter(user=profile, state='cart',client=request.client.client)
            if user_cart:
                # user already has a cart, so lets proceed as a guest_cart
                cart.state = 'guest_cart'
            if 'mobile_web' in params:
                name = params['name']
                profile.full_name = name
                profile.save()
            request.session['guest_user'] = usr
            cart.user = profile
            cart.save()
            if 'mobile_web' in params:
                fetch_state_country_city_by_pincode(request,params, cart)
            if utils.is_future_ecom(request.client.client):
                cs = utils.get_session_obj(request)
                cs['atg_username'] = mobile
                fbapi = FuturebazaarAPI(request,profile,cart)
                for item in cart.get_items_for_billing(request).iterator():
                    fbapi.add_item_to_fb_cart(request,item.seller_rate_chart,item.qty)
                #fbapi.sync_cart(request,cart)
                cs['fbapiobj'] = fbapi
                utils.set_session_obj(request,cs)
            #utils.initialize_fb_api(request,profile)

        elif action == 'sign-in':
            mobile = params['mobile']
            password = params['password']
            if utils.is_valid_email(mobile):
                mobile = utils.check_special_characters(mobile)
            usr = auth.authenticate(username=mobile,password=password,**dict(request=request))
            if usr is not None and usr.is_active:
                try:
                    auth.login(request, usr)
                    profile = utils.get_user_profile(usr)
                    if utils.is_future_ecom(request.client.client):
                        cs = utils.get_session_obj(request)
                        cs['atg_username'] = mobile
                        fbapi = FuturebazaarAPI(request,profile,cart)
                        user_cart = get_or_create_user_cart(request, usr)
                        cs['cart_id'] = user_cart.id
                        utils.set_session_obj(request,cs)
                        resp, redirect_to_mycart = fbapi.sync_cart_for_checkout(request, cart, user_cart)
                        cs = utils.get_session_obj(request)
                        cs['fbapiobj'] = fbapi
                        if resp:
                            cs['sync_errors'] = resp
                        utils.set_session_obj(request,cs)
                        cart.user = profile
                        cart.save()
                        if redirect_to_mycart:
                            if utils.get_future_ecom_prod() == request.client.client:
                                next_path = 'shipping'  
                                request.session['show_fbcart'] = True
                            else:
                                next_path = 'mycart'
                            response = HttpResponseRedirect(request.path.replace('signin', next_path))
                            return response
                    else:
                        user_cart = Order.objects.filter(user=profile, state='cart',client=request.client.client)
                        if user_cart:
                            # User has cart, so lets make this a temporary_cart
                            cart.state = 'temporary_cart'
                        cart.user = profile
                        cart.save()
                except Exception, e:
                    log.exception('Error initializing api %s' % repr(e))
                    auth.logout(request)
                    # logout flushes the session. Lets put the cart back in session
                    request.session['cart_id'] = cart.id
                    # Lets also detach the user and set the cart state back
                    cart.user = None
                    cart.state = 'cart'
                    cart.save()
                    return render_to_response("order/signin.html",
                        {
                            'error': 'Sorry, we are unable to log you in. Please try again.'
                        },
                        context_instance = RequestContext(request))
            else:
                error = 'Please enter valid Email/Mobile and password.'
                response = render_to_response('order/signin.html',
                    {'error':error},
                    context_instance=RequestContext(request))
                return response
        response = HttpResponseRedirect(request.path.replace('signin','shipping'))
        return response
    else:
        cart = get_cart_and_save_in_session(request)
        action = next_checkout_action(request)
        response  = render_to_response('order/signin.html',
                dict(action="orders/shipping", order=cart),
                context_instance = RequestContext(request))
        return response

def validate_mobile_web_shipping(params):
    address = params['delivery_address']
    city = params['delivery_city']
    country = params['delivery_country']
    if not address:
        return 'Please enter delivery address'
    if not city:
        return 'Please enter delivery city'
    if not country:
        return 'Please enter delivery country'
    return None

@never_cache
def shipping_detail(request, admin_order_id=None):
    order = get_cart_and_save_in_session(request, admin_order_id)
    order_items = order.get_items_for_billing(request)
    if not order_items:
        next_request_path = get_mycart_next_url(request, "shipping")
        response = HttpResponseRedirect(next_request_path)
        return response
    allowed = True
    domain = request.META['HTTP_HOST']
    for item in order_items:
        if item.seller_rate_chart.product.currency == 'usd':
            allowed = False
            break
    if request.path.startswith('/orders/auth/'):
        allowed = True
    profile = order.user
    failed_payment = request.session.get('failed_payment',None)
    if failed_payment:
        del request.session['failed_payment']
    if (domain in utils.MOBILE_DOMAIN or domain in utils.MEX_DOMAINS) and request.POST and 'Proceed' not in request.POST:
        params = request.POST
        shipping_info_form = ShippingInfoForm(request, order, None, domain, request.POST)
        next_step = next_checkout_action(request, admin_order_id)
        if shipping_info_form.is_valid():
            address, delivery_info = save_delivery_info_mobile(order,params)
            add_address_to_user(address,profile)
            order.payment_mode = 'mobile'
            order.save()
            if domain in utils.MEX_DOMAINS:
                add_to_cart_response = add_items_to_fb_cart(request,'mobile-user',order)
                if add_to_cart_response['responseCode'] != 'OM_ADDED_ITEM_TO_CART':
                        response  = render_to_response('order/shipping_info.html',
                            {'shipping_info_form':shipping_info_form,
                            'order': order,
                            'next_action': next_step,
                            'post_back' : request.path,
                            'order_response':add_to_cart_response},
                            context_instance = RequestContext(request))
                        return response
            res = book_mobile_order(order,request)
            if 'error' in res:
                response = render_to_response('order/shipping_info.html',
                    {'shipping_info_form':shipping_info_form,
                    'order':order,
                    'next_action':next_step,
                    'order_response':res['error'],
                    'post_back':request.path},
                    context_instance = RequestContext(request))
                return response
            else:
                return res
        else:
            response  = render_to_response('order/shipping_info.html',
                {'shipping_info_form':shipping_info_form,
                'order': order,
                'next_action':next_step,
                'post_back': request.path},
                context_instance = RequestContext(request))
            return response


    if request.POST and 'del_address' in request.POST:
        shipping_info_form = ShippingInfoForm(request, order, None,domain, request.POST)
        delivery_notes_form = DeliveryNotesForm(request.POST)
        # clean up notes, there are no validaton errors to handle for notes
        # mandatory call so that we get the cleaned data
        delivery_notes_form.is_valid()
        is_valid_shipping_address = False
        addressbook_id = None
        if request.POST['del_address'] == 'new':
            if 'old_address' in request.POST:
                delivery_address_id = request.POST['old_address']
            '''add new delivery address and redirect to pg'''
            delivery_info = None
            if shipping_info_form.is_valid():
                is_valid_shipping_address = True
                if profile:
                    email = shipping_info_form.cleaned_data['email']
                    pincode = shipping_info_form.cleaned_data['delivery_pincode']
                    if pincode:
                        pincodes = AvailabilityConstraint.objects.filter(zipcode=pincode)
                    if email:
                        emails = UserEmail.objects.filter(email=email,user=profile)
                        if not emails:
                            try:
                                e = UserEmail(user=profile,type='primary',email=email)
                                e.save()
                            except:
                                pass

                address, delivery_info = save_delivery_info(request,order,shipping_info_form,delivery_notes_form, profile)
                add_address_to_user(address,profile)
        else:
            selected_user_address = AddressBook.objects.get(id=request.POST['del_address'])
            if utils.is_future_ecom(request.client.client) or utils.is_ezoneonline(request.client.client):
                if fbapiutils.STATES_MAP.get(selected_user_address.state.name):
                    state = fbapiutils.STATES_MAP[selected_user_address.state.name]
                else:
                    state = ''
            else:
                state = selected_user_address.state.name
            data = {'delivery_state':state,'delivery_first_name':selected_user_address.first_name,
                'delivery_last_name':selected_user_address.last_name, 'delivery_address': selected_user_address.address,
                'delivery_city':selected_user_address.city.name, 'delivery_country':'India',
                'delivery_pincode':selected_user_address.pincode, 'delivery_phone':selected_user_address.phone}
            shipping_info_form = ShippingInfoForm(request, order, None, domain, data)
            if shipping_info_form.is_valid():
                is_valid_shipping_address = True
                notes = delivery_notes_form.cleaned_data['delivery_notes']
                address,delivery_info = add_selected_user_address_to_order(order,selected_user_address,notes,profile)
        if not is_valid_shipping_address:
            if order.state == 'guest_cart':
                user_addresses = []
            else:
                user_addresses = AddressBook.objects.filter(profile=profile).order_by('-id')[:3]
            try:
                delivery_info = DeliveryInfo.objects.get(order=order)
            except DeliveryInfo.DoesNotExist:
                delivery_info = None
            try:
                gift_info = GiftInfo.objects.get(order=order)
            except GiftInfo.DoesNotExist:
                gift_info = None
            next_step = next_checkout_action(request, admin_order_id)
            if request.POST['del_address'] != 'new':
                addressbook_id = request.POST['del_address']
            response  = render_to_response('order/shipping_info.html',
                {'shipping_info_form':shipping_info_form,
                'delivery_notes_form':delivery_notes_form,
                'delivery_info':delivery_info,
                'gift_info':gift_info,
                'order': order,
                'failed_payment': failed_payment,
                'user_addresses':user_addresses,
                'next_action': next_step,
                'post_back' : request.path,
                'addressbook_id': addressbook_id,
                'allowed':allowed},
                context_instance = RequestContext(request))
            return response
        try:
            gift_info = GiftInfo.objects.get(order=order)
        except GiftInfo.DoesNotExist:
            gift_info  = GiftInfo()
        gift_info.notes = delivery_notes_form.cleaned_data['delivery_gift_notes']
        gift_info.order = order
        gift_info.save()
        if utils.is_cc(request):
            # on callcenter, we proceed to booking order
            availability_errors = None
            if utils.is_tinla_only_client(order.client):
                availability_errors = utils.check_availability_for_tinla_clients(request, order)
            elif utils.is_future_ecom(order.client):
                availability_errors = utils.check_availability(request, order)
            
            if availability_errors:
                user_addresses = AddressBook.objects.filter(profile=profile).order_by('-id')[:3]
                next_step = next_checkout_action(request, admin_order_id)
                response  = render_to_response('order/shipping_info.html',
                    {'shipping_info_form':shipping_info_form,
                    'delivery_notes_form':delivery_notes_form,
                    'delivery_info':delivery_info,
                    'gift_info':gift_info,
                    'order': order,
                    'user_addresses':user_addresses,
                    'next_action': next_step,
                    'availability_errors':availability_errors,
                    'post_back' : request.path},
                    context_instance = RequestContext(request))
                return response
            if not utils.is_franchise(request):
                return HttpResponseRedirect(request.path.replace('shipping','book'))
        if request.path.startswith('/orders/auth/'):
            # on order auth, we proceed to collecting payment_info
            if request.client.is_second_factor_auth_reqd:
                if utils.is_future_ecom(request.client.client) or utils.is_ezoneonline(request.client.client):
                    order = Order.objects.filter(reference_order_id=admin_order_id, state='pending_order').order_by('-id')
                    if order:
                        order = order[0]
                    else:
                        raise Http404
                else:
                    order = Order.objects.filter(id=admin_order_id)

# no more verification code needed. agents will confirm order using transaction password
#                verify_code = None
#                if order.verify_code:
#                    verify_code = order.verify_code
#                else:
#                    verify_code = random.getrandbits(15)
#                    order.verify_code = verify_code
#                    order.save()
#                log.info('Verification code for auth is %s' % verify_code)
#                profile = Profile.objects.get(user=request.user)
#                phones = Phone.objects.filter(user=profile)
#                log.info(phones)
#                verification_code_sms(order,phones)
            return HttpResponseRedirect(request.path.replace('shipping','payment_info'))
       
        availability_errors = None
        if utils.is_tinla_only_client(order.client) and not utils.is_usholii_client(order.client):
            availability_errors = utils.check_availability_for_tinla_clients(request, order)
        elif utils.is_future_ecom(order.client):
            availability_errors = utils.check_availability(request, order)

        if availability_errors:
            user_addresses = AddressBook.objects.filter(profile=profile).order_by('-id')[:3]
            next_step = next_checkout_action(request, admin_order_id)
            response  = render_to_response('order/shipping_info.html',
                {'shipping_info_form':shipping_info_form,
                'delivery_notes_form':delivery_notes_form,
                'delivery_info':delivery_info,
                'gift_info':gift_info,
                'order': order,
                'user_addresses':user_addresses,
                'next_action': next_step,
                'availability_errors':availability_errors,
                'post_back' : request.path},
                context_instance = RequestContext(request))
            return response
       
        if utils.is_franchise(request):
            gateway = 'itz-cash'
            pending_order = order.get_or_create_pending_order(request)
            pending_order.payment_mode = 'Itz'
            pending_order.sync_non_item_info(order)
            pending_order.save()
            json = pending_order.create_payment_attempt(request, gateway)
            if json:
                return render_to_response('order/itz_redirect.html',
                                          {'json':json},
                                          context_instance = RequestContext(request))
        elif utils.is_cc(request):
            # on callcenter, we proceed to booking order
            return HttpResponseRedirect(request.path.replace('shipping','book'))
        elif utils.is_future_ecom(order.client) or utils.is_ezoneonline(order.client):
            # enforce https on payment page
            domain = request.client.domain
            path = request.path.replace('shipping','payment_mode')
            redirect_url = '%s://%s%s' % (settings.PAYMENT_PAGE_PROTOCOL, domain, path)
            return HttpResponseRedirect(redirect_url)
        else:
            print "STOP HIM HERE"
            # on web for chaupaati, we proceed to payment gateway
            #gateway = request.POST['gateway']

#            errors = []
#            if utils.is_tinla_only_client(request.client.client):
#                #Update the inventory just before we move to order booking page 
#                errors = order.update_inventory('deplete')
#
#            if errors:
#                print 'hereeeeeeeeee - %s' % errors
#                response  = render_to_response('order/shipping_info.html',
#                    {'shipping_info_form':shipping_info_form,
#                    'delivery_notes_form':delivery_notes_form,
#                    'delivery_info':delivery_info,
#                    'gift_info':gift_info,
#                    'order': order,
#                    'failed_payment': failed_payment,
#                    'user_addresses':user_addresses,
#                    'next_action':next_step,
#                    'post_back': request.path,
#                    'readonly' : readonly,
#                    'allowed':allowed,
#                    'error':errors[0]},
#                    context_instance = RequestContext(request))
#                return response

            gateway = 'icici'
            pending_order = order.get_or_create_pending_order(request)
            pending_order.payment_mode = 'credit-card'
            pending_order.sync_non_item_info(order)
            pending_order.save()
            payment_attempt = pending_order.create_payment_attempt(request, gateway)
            if payment_attempt.redirect_url:
                return HttpResponseRedirect(payment_attempt.redirect_url)
            else:
                # Retry again
                payment_attempt = pending_order.create_payment_attempt(request, gateway)
                if payment_attempt.redirect_url:
                    return HttpResponseRedirect(payment_attempt.redirect_url)
    else:
       
        if order.state == 'guest_cart':
            user_addresses = []
        else:
            user_addresses = AddressBook.objects.filter(profile=profile).order_by('-id')[:3]
            if utils.is_future_ecom(order.client) or utils.is_ezoneonline(order.client):
                user_addresses = valid_fb_address(user_addresses)
        try:
            delivery_info = DeliveryInfo.objects.filter(order=order)
            delivery_info = delivery_info[0]
            d_notes = delivery_info.notes
        except:
            delivery_info = None
            d_notes = None
        try:
            gift_info = GiftInfo.objects.filter(order=order)
            gift_info = gift_info[0]
            g_notes = gift_info.notes
        except:
            gift_info = None
            g_notes = None
        delivery_notes_form = DeliveryNotesForm({'delivery_notes':d_notes,'delivery_gift_notes':g_notes})
        shipping_info_form = ShippingInfoForm(request, order, delivery_info, domain)
        next_step = next_checkout_action(request, admin_order_id)
        readonly = False
        if request.path.startswith('/orders/auth') and utils.is_future_ecom(order.client):
            readonly = True

        response  = render_to_response('order/shipping_info.html',
            {'shipping_info_form':shipping_info_form,
            'delivery_notes_form':delivery_notes_form,
            'delivery_info':delivery_info,
            'gift_info':gift_info,
            'order': order,
            'failed_payment': failed_payment,
            'user_addresses':user_addresses,
            'next_action':next_step,
            'post_back': request.path,
            'readonly' : readonly,
            'allowed':allowed},
            context_instance = RequestContext(request))
        return response

#def verification_code_sms(order,phones):
#    t_sms = get_template('notifications/users/verifycode.sms')
#    sms_content = {}
#    sms_content['order'] = order
#    c_sms = Context(sms_content)
#    sms_text = t_sms.render(c_sms)
#    sms = SMS()
#    sms.text = sms_text
#    sms.mask = order.client.sms_mask
#    u_phones = ""
#    for x in phones:
#        u_phones = str(x.phone)
#        sms.to = u_phones
#        log.info("SMS Sending to: %s" % u_phones)
#        sms.send()

def valid_fb_address(user_addresses):
    valid_addresses = []
    for address in user_addresses:
        if not address.address:
            continue
        elif not address.state:
            continue
        elif not address.city:
            continue
        elif not address.state.name in fbapiutils.STATES_MAP:
            continue
        elif not address.pincode:
            continue
        else:
            valid_addresses.append(address)
    return valid_addresses

def add_selected_user_address_to_order(order,user_address,notes,profile):
    check_address = check_address_present(user_address,profile)
    address_book = user_address.clone()
    address_book.save()
    if check_address['address']:
        address = check_address['addr_obj']
    else:
        address = Address()
        address.address = address_book.address
        address.city = address_book.city
        address.country = address_book.country
        address.pincode = address_book.pincode
        address.state = address_book.state
        address.profile = address_book.profile
        #address.name = address_book.name
        address.first_name = address_book.first_name
        address.last_name = address_book.last_name
        address.phone = address_book.phone
        address.email = address_book.email
        address.defaddress = address_book.defaddress
        address.save()

    try:
        delivery_info = DeliveryInfo.objects.select_related('address').get(order=order)
    except DeliveryInfo.DoesNotExist:
        delivery_info = DeliveryInfo()

    address = user_address.clone()
    address.type = 'delivery'
    address.save()

    delivery_info.order = order
    delivery_info.address = address
    delivery_info.notes = notes
    delivery_info.save()

    return address,delivery_info

def add_address_to_user(delivery_address,profile):
    address = delivery_address.clone()
    address.type = 'user'
    address.profile = profile
    address.save()


def save_delivery_info_mobile(order,data):
    try:
        delivery_info = DeliveryInfo.objects.select_related('address').get(order=order)
        address = delivery_info.address
    except DeliveryInfo.DoesNotExist:
        delivery_info = DeliveryInfo()
        address = Address()
    address.address = data['delivery_address']

    country_name = data['delivery_country']
    country = utils.get_or_create_country(country_name, True)

    city_name = data['delivery_city']
    city = utils.get_or_create_city(city_name, address.state, True)

    address.city = city
    address.country = country
    address.type = 'delivery'
    address.created_on = datetime.now()

    to_save = check_address_present(address,profile)
    if not to_save['address']:
        address.save()
    elif to_save['address']:
        address = to_copy['addr_obj']
    delivery_info.address = address
    delivery_info.order = order
    delivery_info.save()

    return address, delivery_info

def save_delivery_info(request, order,order_shipping_form,delivery_notes_form, profile):
    try:
        delivery_info = DeliveryInfo.objects.select_related('address').get(order=order)
        address = delivery_info.address
    except DeliveryInfo.DoesNotExist:
        delivery_info = DeliveryInfo()
        address = Address()

    address.address = order_shipping_form.cleaned_data['delivery_address']
    address.pincode = order_shipping_form.cleaned_data['delivery_pincode']

    country_name = order_shipping_form.cleaned_data['delivery_country']
    country = utils.get_or_create_country(country_name, True)

    state_name = order_shipping_form.cleaned_data['delivery_state']
    if (utils.is_future_ecom(order.client) or utils.is_ezoneonline(order.client) or utils.is_usholii_client(order.client) or utils.is_indiaholii_client(order.client)) and state_name:
        if utils.is_usholii_client(order.client):
            state_map = fbapiutils.US_STATES_MAP
        else:
            state_map = fbapiutils.STATES_MAP
        reverse_map = {}
        for state in state_map:
            reverse_map[state_map[state]] = state
        state_name = reverse_map[state_name]

    if state_name:
        state = utils.get_or_create_state(state_name, country, True)
    else:
        state = ''

    city_name = order_shipping_form.cleaned_data['delivery_city']
    city = utils.get_or_create_city(city_name, state, True)

    address.city = city
    if state: address.state = state
    address.country = country
    address.type = 'delivery'
    #address.name = order_shipping_form.cleaned_data['delivery_name']
    address.first_name = order_shipping_form.cleaned_data['delivery_first_name']
    address.last_name = order_shipping_form.cleaned_data['delivery_last_name']
    address.phone = order_shipping_form.cleaned_data['delivery_phone']
    address.email = order_shipping_form.cleaned_data['email']
    address.created_on = datetime.now()

    #to_save = check_address_present(address,profile)
    #if not to_save['address']:
    address.save()
    #elif to_save['address']:
    #    address = to_save['addr_obj']
    delivery_info.address = address
    delivery_info.notes = delivery_notes_form.cleaned_data['delivery_notes']
    delivery_info.order = order
    delivery_info.save()
    if request.method == 'POST' and 'update_addressbook_id' in request.POST:
        if request.POST['update_addressbook_id']:
            try:
                user_address = AddressBook.objects.get(id=request.POST['update_addressbook_id'])
                user_address.first_name = address.first_name
                user_address.last_name = address.last_name
                user_address.address =  address.address
                user_address.city = address.city
                user_address.state = address.state
                user_address.country = address.country
                user_address.pincode = address.pincode
                user_address.phone = address.phone
                user_address.email = address.email
                user_address.save()
            except Exception, e:
                log.info('Failed to update address book: %s' % repr(e))
    return address, delivery_info

def check_address_present(address,profile):
    address_string = address.get_address_to_check()
    get_addresses = Address.objects.filter(profile=profile)
    to_copy = {}
    to_copy['addr_obj'] = None
    to_copy['address'] = False
    for addr in get_addresses:
        addr_string = addr.get_address_to_check()
        if addr_string == address_string:
            to_copy['addr_obj'] = addr
            to_copy['address'] = True   # IN Address
    return to_copy


#@user_passes_test(lambda u: u.has_perm('orders.can_confirm_order'))
@never_cache
@login_required
def auth_order_admin(request):
    if request.path.startswith('/orders/cancel/'):
        if request.user.has_perm('orders.can_cancel_order'):
            action = '/orders/cancel/'
            order_state = ['confirmed', 'modified']
        else:
            return HttpResponseRedirect('/')
    else:
        if request.user.has_perm('orders.can_confirm_order'):
            action = '/orders/auth/'
            order_state = ['pending_order']
        else:
             return HttpResponseRedirect('/')

    if request.method == 'POST':
        order_id = request.POST.get('order_id','').strip()
        try:
            if request.client.client == utils.get_chaupaati_marketplace() or utils.is_holii_client(request.client.client):
                order = Order.objects.get(id=order_id)
            elif utils.is_future_ecom(request.client.client) or utils.is_ezoneonline(request.client.client):
                order = Order.objects.filter(reference_order_id=order_id,state__in = order_state).order_by("-id")
                if order:
                    order = order[0]
                else:
                    raise Order.DoesNotExist
            error = None
            if request.path.startswith('/orders/cancel'):
                if order.state in ('cancelled',):
                    error = 'This order has already been cancelled. Please check the refund status.'
                elif order.state not in order_state:
                    error = 'Please enter a valid confirmed/modified order id to cancel'
                else:
                    return HttpResponseRedirect('/orders/cancel/' + order_id + '/mycart')
            else:
                if order.state not in ('pending_order',):
                    error = 'Please enter a valid pending order id to confirm'
                else:
                    return HttpResponseRedirect('/orders/auth/' + order_id + '/mycart')
            if error:
                response  = render_to_response('order/admin.html',
                    {'order_id':order_id,'error':error},
                    context_instance = RequestContext(request))
                return response

        except Order.DoesNotExist:
            error = 'Order Id does not exists'
            response  = render_to_response('order/admin.html',
                {'order_id':order_id,'error':error,'action':action},
                context_instance = RequestContext(request))
            return response
    response  = render_to_response('order/admin.html',
        {'action':action},
        context_instance = RequestContext(request))
    return response


@never_cache
def cancellation_info(request, admin_order_id=None):
    cart = get_cart_and_save_in_session(request, admin_order_id)
    order_cancellation_form = OrderCancellationForm()
    error = None
    cancelled_items = request.POST['cancelled_items'].split(',')
    order_notification = []
    order_items = cart.orderitem_set.filter(id__in=cancelled_items)
    if request.method == 'POST' and 'cancellation_notes' in request.POST:
        order_cancellation_form = OrderCancellationForm(request.POST)
        if order_cancellation_form.is_valid():
            next_action = order_cancellation_form.cleaned_data.get('next_action', 'action_1')
            #cart.state = 'cancelled'
            #cart.save()
            try:
                error = cart.cancel(request)
                if error:
                    raise CancelOrderFailed

                cart.save_history(request)
                for order_item in order_items:
                    order_item.state = 'cancelled'
                    cancelled_order_item = CancelledOrderItem()
                    cancelled_order_item.order_item = order_item
                    cancelled_order_item.notes = order_cancellation_form.cleaned_data['cancellation_notes']
                    cancelled_order_item.refundable_amount = Decimal(str(order_item.payable_amount()))
                    if next_action == 'action_1':
                        cancelled_order_item.refund_status = 'pending'
                    if next_action == 'action_2':
                        cancelled_order_item.refund_status = 'not_required'
                    if next_action == 'action_3':
                        cancelled_order_item.refund_status = 'refunded'
                    cancelled_order_item.save()
                    order_item.save()
                #order_items = cart.orderitem_set.all()
                all_cancelled = True
                for order_item in cart.orderitem_set.all():
                    if order_item.state != 'cancelled':
                        all_cancelled = False
                cart.modified_on = datetime.now()
                if all_cancelled:
                    cart.state = 'cancelled'
                else:
                    cart.state = 'modified'
                cart.save()
                cart.notify_cancelled_order(order_items, request)
                #cart.update_blling()
                return HttpResponseRedirect('/orders/cancel/%s/cancelled' % (cart.id))
            except CancelOrderFailed:
                log.exception("Order Cancellation failed for %s : %s" % (
                        str(admin_order_id), error))

    return render_to_response('order/cancel_order.html',
            dict(
                order_cancellation_form = order_cancellation_form,
                order = cart,
                error = error,
                cancelled_items = cancelled_items,
                order_items = order_items,
                ),
        context_instance = RequestContext(request))

def refund_dashboard(request, admin_order_id=None):
    if request.POST and request.path.startswith('/orders/refund_dashboard'):
        item_id = request.POST['item']
        item = CancelledOrderItem.objects.get(id= item_id)
        if item.refund_status == 'pending':
            item.refund_status = 'processing'
            item.action = 'None'
            item.save()
            return HttpResponse(item)

    for item in CancelledOrderItem.objects.iterator():
        if item.refund_status == 'pending':
            item.action = 'Process the refund'
        if item.refund_status == 'refunded':
            item.action = 'None'
        if item.refund_status == 'processing':
            item.action = 'None'
        if item.refund_status == 'not_required':
            item.action = 'None'

    return render_to_response('order/refund_dashboard.html',
            dict(
                order_items = order_items,
                ),
        context_instance = RequestContext(request))

@never_cache
def order_details(request, admin_order_id=None):
    sp = request.path.split('/')
    id = sp[-1]
    order = Order.objects.get(id = id)
    order_items = order.get_items_for_billing(request)
    order_details_dict={'order':order, 'order_items':order_items}
    try:
        delivery_info = DeliveryInfo.objects.get(order=order)
        order_details_dict['delivery_info']=delivery_info
    except:
        pass
    return render_to_response('order/order_details.html',
            order_details_dict,
        context_instance = RequestContext(request))

@never_cache
def payment_info(request, admin_order_id=None):
    cart = get_cart_and_save_in_session(request, admin_order_id)
    if request.path.startswith("/orders/auth") and utils.is_future_ecom(cart.client):
        readonly = True
    else:
        readonly = False
    if not cart.get_items_for_billing(request):
        response = HttpResponseRedirect(request.path.replace('payment_info','mycart'))
        return response
    payment_options_form = AdminPaymentOptionsForm(request, cart)
    error = None
                
    if request.method == 'POST' and 'payment_mode' in request.POST:
        payment_options_form = AdminPaymentOptionsForm(request,cart,request.POST)
        if payment_options_form.is_valid():
            if not request.client.type in ['cc', 'store'] or request.client.client == utils.get_chaupaati_marketplace():
                payment_attempt = cart.create_payment_attempt(request, Order.GATEWAY[payment_options_form.cleaned_data['payment_mode']])
                payment_attempt.transaction_id = payment_options_form.cleaned_data['transaction_no']
                payment_attempt.response_detail = payment_options_form.cleaned_data['transaction_notes']
            cart.payment_realized_mode = payment_options_form.cleaned_data['payment_mode']

            if cart.state in ('pending_order',):
                try:
                    error = cart.confirm(request)
                    if error:
                        raise ConfirmOrderFailed
                    if not request.client.type in ['cc', 'store'] or request.client.client == utils.get_chaupaati_marketplace():
                        payment_attempt.status = 'approved'
                        payment_attempt.save()
                    utils.clear_cart(request,cart)
                    confirmed_orders_in_session = request.session.get(
                            'confirmed_orders', [])
                    confirmed_orders_in_session.append(cart.id)
                    request.session['confirmed_orders'] = confirmed_orders_in_session
                    return HttpResponseRedirect('/orders/auth/%s/confirmation' % (cart.id))

                except ConfirmOrderFailed:
                    log.exception("Order Confirmation failed for %s : %s" % (
                            str(admin_order_id), error))
            else:
                error = 'This order is already confirmed'
    
    return render_to_response('order/confirm.html',
            dict(
                action = "orders/" + admin_order_id + "/book",
                payment_options_form = payment_options_form,
                order = cart,
                error = error,
                total_items = cart.get_item_count(),
                delivery_info = cart.get_delivery_info(),
                readonly = readonly,
                ),
        context_instance = RequestContext(request))

def ebs_pass(request,card_no,order,card_type):
    cs = utils.get_session_obj(request)
    fbapi = cs['fbapiobj']
    fb_order_response = fbapi.add_to_cart_response
    cookie_file = fbapi.cookie_file
    order_id = None
    if order.reference_order_id:
        order_id = order.reference_order_id
    else:
        order_id = fbapi.add_to_cart_response['items'][0]['orderId']
        order.reference_order_id = order_id
        order.save()
    #fbapi.update_user(request, 'web-user', order)
    delivery_info = order.get_delivery_info()
    billing_info = BillingInfo.objects.filter(user=order.user).order_by('-id')

    billing_name = ''
    if billing_info:
        billing_info = billing_info[0]
        billing_name = '%s %s' % (billing_info.first_name,billing_info.last_name)
    else:
        billing_info = BillingInfo()
        address = delivery_info.address
        address.id=None
        address.type = 'billing'
        address.user = order.user
        address.save()
        billing_info.address = address
        billing_info.user = order.user
        billing_info.phone = address.phone
        billing_info.first_name = address.first_name
        billing_info.last_name = address.last_name
        billing_info.save()
    cs = utils.get_session_obj(request)

    info = {'profileId':fbapi.fb_user['items'][0]['profileId'],
            'cardNo':card_no,
            'remoteAddress':request.META['REMOTE_ADDR'],
            'headerVal':'',
            'userAgent':'',
            'orderId': order.reference_order_id,
            'cardType':card_type,
            'cardBillingName':billing_name,
            'totalAmount':str(order.payable_amount),
            'shippingAddress': {
                'firstName': delivery_info.address.first_name,
                'lastName': delivery_info.address.last_name,
                'address1': delivery_info.address.address,
                'city': delivery_info.address.city.name,
                'country': 'IN',
                'state': fbapiutils.STATES_MAP[delivery_info.address.state.name],
                'postalCode': delivery_info.address.pincode,
                'phoneNumber': delivery_info.address.phone,
                'email': delivery_info.address.email
            },
            'billingAddress': {
                'firstName': billing_info.first_name,
                'lastName': billing_info.last_name,
                'address1': billing_info.address.address,
                'city': billing_info.address.city.name,
                'country': 'IN',
                'state': fbapiutils.STATES_MAP[billing_info.address.state.name],
                'postalCode': billing_info.address.pincode,
                'phoneNumber': billing_info.address.phone,
                'email': billing_info.address.email
            }
            }

    # EBS check Rest API parameters.
    shipping_name = '%s %s' % (delivery_info.address.first_name,delivery_info.address.last_name)
    product_info=''
    for oi in order.get_items_for_billing(request):
        if product_info=='':
            product_info += str(oi.qty) + ' X ' + str(oi.seller_rate_chart.product.title);
        else:
            product_info += '|' +  str(oi.qty) + ' X ' + str(oi.seller_rate_chart.product.title);
    ebs_check_params = {'profileId':fbapi.fb_user['items'][0]['profileId'],
            'cardNumber':card_no,
            'ipAddress':request.META['REMOTE_ADDR'],
            'headerValue':'',
            'userAgent':'',
            'orderId': order.reference_order_id,
            'cardType':card_type,
            'cardBillingName':billing_name,
            'totalAmount':str(order.payable_amount),
            'billingCurrencyCode':'',
            'billingAddress': billing_info.address.address,
            'billingCity': billing_info.address.city.name,
            'billingState':fbapiutils.STATES_MAP[billing_info.address.state.name],
            'billingPostalCode':billing_info.address.pincode,
            'billingCountry':'IN',
            'billingEmail': billing_info.address.email,
            'billingPhone':billing_info.address.phone,
            'shippingName':shipping_name,
            'shippingAddress':delivery_info.address.address,
            'shippingCity':delivery_info.address.city.name,
            'shippingState':fbapiutils.STATES_MAP[delivery_info.address.state.name],
            'shippingPostalCode':delivery_info.address.pincode,
            'shippingCountry':'IN',
            'shippingEmail':delivery_info.address.email,
            'shippingPhone':delivery_info.address.phone,
            'txnId':'',
            'productInformation':product_info,
            'rmsRiskBox':'',
        }

    try:
        response = fbapi.ebs_check(ebs_check_params, 'web', request)
        log.info('EBS Check Response: %s' % response)
        status = response['Status']
		
        if status in ('Review', 'Approved', 'Approve',):
            return True
        else:
            return False
    except Exception,e:
        log.exception('%s' % repr(e))

    return False

def ebs_check(request,card_no,order,card_type):
    cs = utils.get_session_obj(request)
    fbapi = cs['fbapiobj']
    fb_order_response = fbapi.add_to_cart_response
    cookie_file = fbapi.cookie_file
    order_id = None
    if order.reference_order_id:
        order_id = order.reference_order_id
    else:
        order_id = fbapi.add_to_cart_response['items'][0]['orderId']
        order.reference_order_id = order_id
        order.save()
    #fbapi.update_user(request, 'web-user', order)
    delivery_info = order.get_delivery_info()
    billing_info = BillingInfo.objects.filter(user=order.user).order_by('-id')

    billing_name = ''
    if billing_info:
        billing_info = billing_info[0]
        billing_name = '%s %s' % (billing_info.first_name,billing_info.last_name)
    else:
        billing_info = BillingInfo()
        address = delivery_info.address
        address.id=None
        address.type = 'billing'
        address.user = order.user
        address.save()
        billing_info.address = address
        billing_info.user = order.user
        billing_info.phone = address.phone
        billing_info.first_name = address.first_name
        billing_info.last_name = address.last_name
        billing_info.save()
    cs = utils.get_session_obj(request)

    rmsRiskBox_param = None
    if 'rmsID' in request.session:
        rmsRiskBox_param = request.session['rmsID']
    info = {'profileId':fbapi.fb_user['items'][0]['profileId'],
            'cardNo':card_no,
            'remoteAddress':request.META['REMOTE_ADDR'],
            'headerVal':'',
            'userAgent':'',
            'orderId': order.reference_order_id,
            'cardType':card_type,
            'cardBillingName':billing_name,
            'totalAmount':str(order.payable_amount),
            'shippingAddress': {
                'firstName': delivery_info.address.first_name,
                'lastName': delivery_info.address.last_name,
                'address1': delivery_info.address.address,
                'city': delivery_info.address.city.name,
                'country': 'IN',
                'state': fbapiutils.STATES_MAP[delivery_info.address.state.name],
                'postalCode': delivery_info.address.pincode,
                'phoneNumber': delivery_info.address.phone,
                'email': delivery_info.address.email
            },
            'billingAddress': {
                'firstName': billing_info.first_name,
                'lastName': billing_info.last_name,
                'address1': billing_info.address.address,
                'city': billing_info.address.city.name,
                'country': 'IN',
                'state': fbapiutils.STATES_MAP[billing_info.address.state.name],
                'postalCode': billing_info.address.pincode,
                'phoneNumber': billing_info.address.phone,
                'email': billing_info.address.email
            }
            }

    # EBS check Rest API parameters.
    shipping_name = '%s %s' % (delivery_info.address.first_name,delivery_info.address.last_name)
    product_info=''
    for oi in order.get_items_for_billing(request):
        if product_info=='':
            product_info += str(oi.qty) + ' X ' + str(oi.seller_rate_chart.product.title);
        else:
            product_info += '|' +  str(oi.qty) + ' X ' + str(oi.seller_rate_chart.product.title);
 	
    ebs_check_params = {'profileId':fbapi.fb_user['items'][0]['profileId'],
            'cardNumber':card_no,
            'ipAddress':request.META['REMOTE_ADDR'],
            'headerValue':'',
            'userAgent':'',
            'orderId': order.reference_order_id,
            'cardType':card_type,
            'cardBillingName':billing_name,
            'totalAmount':str(order.payable_amount),
            'billingCurrencyCode':'',
            'billingAddress': billing_info.address.address,
            'billingCity': billing_info.address.city.name,
            'billingState':fbapiutils.STATES_MAP[billing_info.address.state.name],
            'billingPostalCode':billing_info.address.pincode,
            'billingCountry':'IN',
            'billingEmail': billing_info.address.email,
            'billingPhone':billing_info.address.phone,
            'shippingName':shipping_name,
            'shippingAddress':delivery_info.address.address,
            'shippingCity':delivery_info.address.city.name,
            'shippingState':fbapiutils.STATES_MAP[delivery_info.address.state.name],
            'shippingPostalCode':delivery_info.address.pincode,
            'shippingCountry':'IN',
            'shippingEmail':delivery_info.address.email,
            'shippingPhone':delivery_info.address.phone,
            'txnId':'',
            'productInformation':product_info,
            'rmsRiskBox': rmsRiskBox_param,
            }

    try:
        response = fbapi.ebs_check(ebs_check_params, 'web', request)
        log.info('EBS Check Response: %s' % response)
        status = response.get('Status', 'Approved')	
        return status 	
    except Exception,e:
        log.exception('%s' % repr(e))

    return 'Rejected'



def validate_card_info(request,payment_options_form,cart,payment_mode):
    validation_response = None
    card_details = None
    is_valid = True
    payment_option_id = payment_options_form.cleaned_data['payment_mode'].split('#')[1]
    payment_option = PaymentOption.objects.get(id=payment_option_id)
    payment_mode_obj = payment_option.payment_mode
    card_form = CreditCardForm(request.POST)
    error = None
    if not card_form.is_valid():
        is_valid = False
    else:
        card_details = card_form.cleaned_data
        if request.client.domain == utils.VISA_DOMAIN:
            if card_details['card_no'][0] != '4':
                is_valid = False
                error = 'Enter a Valid VISA card no.'
    if not is_valid:
        try:
            billing_info = BillingInfo.objects.get(user=cart.user)
        except BillingInfo.DoesNotExist:
            billing_info = None
        domain = request.META['HTTP_HOST']
        shipping_address = cart.get_delivery_info()
        if payment_option.payment_mode.validate_billing_info:
            billing_info_form = BillingInfoForm(request,billing_info,domain)
            ctxt = Context({'card_form':card_form,'billing_info_form':billing_info_form})
        else:
            ctxt = Context({'card_form':card_form})
        html = "order/%s" % payment_page_html(payment_mode)
        template = get_template(html)
        html_file = template.render(ctxt)
        validation_response =  render_to_response('order/online_payment_modes.html',
                dict(payment_options_form = payment_options_form,
                payment_mode_html = html_file,
                card_form = card_form,
                payment_mode=payment_options_form.cleaned_data['payment_mode'],
                order=cart,
                error=error),
            context_instance = RequestContext(request))
    return card_details,validation_response,is_valid

@never_cache
def payment_mode(request):
    cart = get_cart_and_save_in_session(request)
    if not cart.get_items_for_billing(request):
        next_request_path = get_mycart_next_url(request, "payment_mode")
        response = HttpResponseRedirect(next_request_path)
        return response
    payment_options_form = OnlinePaymentOptionsForm(request, cart)
    payment_mode_org = payment_options_form.fields['payment_mode'].choices[0][0]
    card_details = None
    if request.method == 'POST':
        payment_options_form = OnlinePaymentOptionsForm(request, cart, request.POST)
        payment_mode_org = request.POST['payment_mode'].split('#')[0]
        request.session['payment_mode'] = request.POST['payment_mode'] 
        if payment_options_form.is_valid():
            payment_mode_org = payment_options_form.cleaned_data['payment_mode']
            payment_option_id = payment_mode_org.split('#')[1]
            payment_mode = payment_mode_org.split('#')[0]
            if 'payment_group_member' in request.POST:
                payment_mode = request.POST['payment_group_member']
            if utils.is_future_ecom(request.client.client):
                cs = utils.get_session_obj(request)
                cs['payment_options_form'] = payment_options_form
                cs['card_details'] = card_details
                utils.set_session_obj(request,cs)
                cs = utils.get_session_obj(request)
                fbapi = cs['fbapiobj']

            ##Offline payment modes
            #for cheque/dd submit the cart to ATG and book the order
            if payment_mode in ('cheque', 'suvidha', 'easybill', 'Itz',
                    'ICICICash', 'fmemi',):
                if payment_mode == 'fmemi':
                    card_form = FMEMIForm(request.POST)
                    if not card_form.is_valid():
                        html = "order/%s" % payment_page_html(payment_mode)
                        template = get_template(html)
                        ctxt = Context({'card_form':card_form})
                        html_file = template.render(ctxt)
                        return render_to_response('order/online_payment_modes.html',
                                dict(payment_options_form = payment_options_form,
                                payment_mode_html = html_file,
                                card_form = card_form,
                                payment_mode=payment_options_form.cleaned_data['payment_mode'],
                                order=cart),
                            context_instance = RequestContext(request))
                    else:
                        card_details = card_form.cleaned_data

                errors = []
                if utils.is_tinla_only_client(request.client.client):
                    #Update the inventory just before we move to order booking page 
                    errors = cart.update_inventory('deplete')

                if errors:
                    return render_to_response('order/online_payment_modes.html',
                        dict(payment_options_form = payment_options_form,
                            order=cart,
                            error = errors[0],
                            payment_mode = payment_options_form.cleaned_data['payment_mode']),
                            context_instance = RequestContext(request))

                if utils.is_future_ecom(request.client.client):
                    fbapi.sync_cart_before_submit(request, cart)
                    agent = utils.get_agent_for_fb_api(request)
                    resp = fbapi.update_user(request, agent, cart, payment_options_form)
                    fbapi.submit_fb_cart(request,cart,cart,payment_options_form,payment_mode,"orders/payment_mode","order/online_payment_modes.html",**dict(card_details=card_details))
                    if fbapi.submit_cart_response:
                        return fbapi.submit_cart_response
                pending_order = cart.get_or_create_pending_order(request)
                request.session['pending_order'] = pending_order
                if cart.state == 'pending_order':
                    cart.reference_order_id = ''
                    cart.save()
                pending_order.payment_mode = payment_mode
                pending_order.sync_non_item_info(cart)
                pending_order.save()
                pending_order.notify_pending_order(request)
                utils.clear_cart(request,pending_order)
                confirmed_orders_in_session = request.session.get(
                        'confirmed_orders', [])
                confirmed_orders_in_session.append(pending_order.id)
                request.session['confirmed_orders'] = confirmed_orders_in_session

                return HttpResponseRedirect(request.path.replace('payment_mode','%s/confirmation' % (pending_order.id)))

            log.info('Before checking availailbity. Payment mode is %s' % payment_mode)

            if payment_mode == 'cod':
                if utils.is_future_ecom(request.client.client):
                    fbapi.sync_cart_before_submit(request, cart)
                    agent = utils.get_agent_for_fb_api(request)
                    resp = fbapi.update_user(request, agent, cart, payment_options_form)
                    fbapi.submit_fb_cart(request,cart,cart,payment_options_form,payment_mode,"orders/payment_mode","order/online_payment_modes.html",**dict(card_details=card_details))
                    if fbapi.submit_cart_response:
                        return fbapi.submit_cart_response
                pending_order = cart.get_or_create_pending_order(request)
                request.session['pending_order'] = pending_order
                if cart.state == 'pending_order':
                    cart.reference_order_id = ''
                    cart.save()
                pending_order.payment_mode = payment_mode
                pending_order.payment_realized_mode = payment_mode
                pending_order.payment_realized_on = datetime.now()
                pending_order.sync_non_item_info(cart)
                pending_order.save()
                pending_order.confirm(request)
                utils.clear_cart(request,pending_order)
                confirmed_orders_in_session = request.session.get(
                        'confirmed_orders', [])
                confirmed_orders_in_session.append(pending_order.id)
                request.session['confirmed_orders'] = confirmed_orders_in_session

                return HttpResponseRedirect(request.path.replace('payment_mode','%s/confirmation' % (pending_order.id)))
               

            if payment_mode in ('netbanking', 'credit-card',
                    'credit-card-emi-web', 'debit-card', 'payback',):
                pending_order = cart.get_or_create_pending_order(request)
                if cart.state == 'pending_order':
                    cart.reference_order_id = ''
                    cart.save()
                pending_order.payment_mode = payment_mode
                pending_order.sync_non_item_info(cart)
                pending_order.save()
                if utils.is_future_ecom(request.client.client):
                    cs = utils.get_session_obj(request)
                    fbapi = cs['fbapiobj']
                    agent = utils.get_agent_for_fb_api(request)
                    resp = fbapi.update_user(request, agent, pending_order, payment_options_form)
                    # Check if the cart is serviceable
                    fbapi.sync_cart_before_submit(request,pending_order)

            if payment_mode == 'netbanking':
                #put dummy card info to use api'
                #using CCAvanue for netbanking
                card_details = {'card_no':'1234567890123456','cvv':'323','name_on_card':'Nilesh Padariya','exp_month':'02','exp_year':'2020'}
                cs = utils.get_session_obj(request)
                cs['card_details'] = card_details
                utils.set_session_obj(request,cs)
                gateway = 'cc_avenue'

                errors = []
                if utils.is_tinla_only_client(request.client.client):
                    #Update the inventory just before we move to order booking page 
                    errors = pending_order.update_inventory('deplete')

                if errors:
                    return render_to_response('order/online_payment_modes.html',
                        dict(payment_options_form = payment_options_form,
                            order=cart,
                            error = errors[0],
                            payment_mode = payment_mode),
                            context_instance = RequestContext(request))
                else:
                    form = pending_order.create_payment_attempt(request, gateway)
                    return render_to_response('order/wait.html',
                        dict(payment_form=form),
                        context_instance=RequestContext(request))

            if payment_mode == 'payback':
                gateway = payment_mode
                card_details = {'card_no':'1234567890123456','cvv':'323','name_on_card':'Nilesh Padariya','exp_month':'02','exp_year':'2020'}
                cs = utils.get_session_obj(request)
                cs['card_details'] = card_details
                utils.set_session_obj(request,cs)

                errors = []
                if utils.is_tinla_only_client(request.client.client):
                    #Update the inventory just before we move to order booking page 
                    errors = pending_order.update_inventory('deplete')

                if errors:
                    return render_to_response('order/online_payment_modes.html',
                        dict(payment_options_form = payment_options_form,
                            order=cart,
                            error = errors[0],
                            payment_mode = payment_mode),
                            context_instance = RequestContext(request))
                else:
                    json = pending_order.create_payment_attempt(request, gateway)
                    if 'error' not in json:
                        redirect_url = json.get('redirectUrl')
                        return_url = json.get('returnUrl')
                        return render_to_response('order/payback_redirect.html',
                                {'redirect_url': redirect_url},
                            context_instance = RequestContext(request))
                    else:
                        return render_to_response('order/online_payment_modes.html',
                            dict(payment_options_form = payment_options_form,
                                order = cart,
                                error = json.get('error'),
                                payment_mode = payment_mode),
                            context_instance = RequestContext(request))

            #for credit-card and debit-card validate card info and proceed
            if payment_mode in ('credit-card', 'debit-card', 'credit-card-emi-web',):
                # card_details = {'card_no':'1234567890123456','cvv':'323','name_on_card':'Nilesh Padariya','exp_month':'02','exp_year':'2020'}
                # cs = utils.get_session_obj(request)
                # cs['card_details'] = card_details
                # utils.set_session_obj(request,cs)
                # Can be used to for api call 
                if request.POST.get('bank') == 'citi' and payment_mode == 'credit-card-emi-web':
                    gateway = 'citi-emi'

                    errors = []
                    if utils.is_tinla_only_client(request.client.client):
                        #Update the inventory just before we move to order booking page 
                        errors = pending_order.update_inventory('deplete')

                    if errors:
                        return render_to_response('order/online_payment_modes.html',
                            dict(payment_options_form = payment_options_form,
                                order=cart,
                                error = errors[0],
                                payment_mode = payment_mode),
                                context_instance = RequestContext(request))
                    else:
                        resp = pending_order.create_payment_attempt(request, gateway)
                        if 'error' not in resp:
                            return render_to_response('order/citi_redirect.html',
                                {'redirect_url': resp.get('redirectUrl'),
                                'citi_param_value': resp.get('citi_param_value'),
                                },
                                context_instance = RequestContext(request))
                        else:
                            return render_to_response('order/online_payment_modes.html',
                                dict(payment_options_form = payment_options_form,
                                    order = cart,
                                    error = resp.get('error'),
                                    payment_mode = payment_mode),
                                context_instance = RequestContext(request))
            
                if request.POST.get('bank') == 'icici' and payment_mode == 'credit-card-emi-web':
                    gateway = 'icici-emi'
                    card_details = {'card_no':'1234567890123456','cvv':'323','name_on_card':'Nilesh Padariya','exp_month':'02','exp_year':'2020'}
                    cs = utils.get_session_obj(request)
                    cs['card_details'] = card_details
                    utils.set_session_obj(request,cs)
                    errors = []
                    if utils.is_tinla_only_client(request.client.client):
                        #Update the inventory just before we move to order booking page 
                        errors = pending_order.update_inventory('deplete')

                    if errors:
                        return render_to_response('order/online_payment_modes.html',
                            dict(payment_options_form = payment_options_form,
                                order=cart,
                                error = errors[0],
                                payment_mode = payment_mode),
                                context_instance = RequestContext(request))
                    else:
                        #Can be used to for api call 
                        resp = pending_order.create_payment_attempt(request, gateway)
                        if resp.get('redirectUrl') and 'error' not in resp:
                            return HttpResponseRedirect(resp.get('redirectUrl'))
                        else:
                            return render_to_response('order/online_payment_modes.html',
                                dict(payment_options_form = payment_options_form,
                                    order = cart,
                                    error = resp.get('error'),
                                    payment_mode = payment_mode),
                                context_instance = RequestContext(request))

                if payment_mode in ('credit-card', 'debit-card') and utils.is_ezoneonline(request.client.client):
                    gateway = 'icici-card'
                    card_details = {'card_no':'1234567890123456','cvv':'323','name_on_card':'Nilesh Padariya','exp_month':'02','exp_year':'2020'}
                    cs = utils.get_session_obj(request)
                    cs['card_details'] = card_details
                    utils.set_session_obj(request,cs)
                    errors = []
                    if utils.is_tinla_only_client(request.client.client):
                        #Update the inventory just before we move to order booking page 
                        errors = pending_order.update_inventory('deplete')

                    if errors:
                        return render_to_response('order/online_payment_modes.html',
                            dict(payment_options_form = payment_options_form,
                                order=cart,
                                error = errors[0],
                                payment_mode = payment_mode),
                                context_instance = RequestContext(request))
                    else:
                        resp = pending_order.create_payment_attempt(request, gateway)
                        if resp.get('redirectUrl') and 'error' not in resp:
                            return HttpResponseRedirect(resp.get('redirectUrl'))
                        else:
                            return render_to_response('order/online_payment_modes.html',
                                dict(payment_options_form = payment_options_form,
                                    order = cart,
                                    error = resp.get('error'),
                                    payment_mode = payment_mode),
                                context_instance = RequestContext(request))

                card_details,card_validation_response,is_valid = validate_card_info(request,payment_options_form,cart,payment_mode)

                if not is_valid: #card info validation failed
                    return card_validation_response
                status=None    
                if payment_mode in ('credit-card', 'credit-card-emi-web',):
                    #Fraud Detection via EBS
                    if utils.is_future_ecom(request.client.client):
                        status = ebs_check(request, card_details['card_no'], pending_order, request.POST['cardtype'])
                        if status in ['Rejected']:
                            gateway = 'hdfc-emi' if payment_mode == 'credit-card-emi-web' else 'hdfc-card'
                            cart.create_payment_attempt_for_ebs(request,gateway,**dict(fraud_status='Rejected'))

                            return render_to_response('order/online_payment_modes.html',
                                dict(payment_options_form = payment_options_form,
                                    order=cart,
                                    error = 'Your card has been rejected by the payment gateway. Please try again, with a different card',
                                    payment_mode = payment_mode_org),
                                context_instance = RequestContext(request))

                gateway = 'hdfc-emi' if payment_mode == 'credit-card-emi-web' else 'hdfc-card'
                
                errors = []
                if utils.is_tinla_only_client(request.client.client):
                    #Update the inventory just before we move to order booking page 
                    errors = cart.update_inventory('deplete')
                
                if errors:
                    return render_to_response('order/online_payment_modes.html',
                                dict(payment_options_form = payment_options_form,
                                    order=cart,
                                    error = errors[0],
                                    payment_mode = payment_mode),
                            context_instance = RequestContext(request))
                else:
                    json = pending_order.create_payment_attempt(request, gateway,**dict(card_details=card_details,fraud_status=status))
                    data = None
                    is_data = False
                    if 'json' in json:
                        data = json['json']
                        if 'pareq' in data and 'payment_id' in data:
                            is_data = True
                    if 'error' not in json and is_data:
                        cs = utils.get_session_obj(request)
                        cs['card_details'] = card_details
                        utils.set_session_obj(request,cs)
                        payment_attempt = json['payment_attempt']
                        term_url = 'http://%s/orders/process_payment_hdfc' % request.client.domain
                        return render_to_response('order/hdfc_redirect.html',
                                dict(redirect_url=payment_attempt.redirect_url,
                                    pareq=json['json']['pareq'],
                                    payment_id=json['json']['payment_id'],
                                    term_url=term_url
                                    ),
                            context_instance = RequestContext(request))
                    else:
                        return render_to_response('order/online_payment_modes.html',
                                dict(payment_options_form = payment_options_form,
                                    order=cart,
                                    error = 'Your payment has been rejected by the payment gateway. Your card has not been charged Please try again, perhaps with a different card',
                                    payment_mode = payment_mode_org),
                            context_instance = RequestContext(request))

        else:
            payment_mode_org = payment_options_form.fields['payment_mode'].choices[0][0]
    pending_payment = None
    price_mismatch_error = None
    failed_payment = None
    payment_mode = payment_mode_org
    if 'payment_mode' in request.session:
        payment_mode = request.session['payment_mode']
        del request.session['payment_mode']
    if 'pending_payment' in request.session:
        pending_payment = request.session['pending_payment']
        del request.session['pending_payment']
    if 'price_mismatch_error' in request.session:
        price_mismatch_error = request.session['price_mismatch_error']
        del request.session['price_mismatch_error']
    if 'failed_payment' in request.session:
        failed_payment = request.session['failed_payment']
        del request.session['failed_payment']
    return render_to_response('order/online_payment_modes.html',
            dict(payment_options_form = payment_options_form,
                order=cart,
                payment_mode = payment_mode,
                pending_payment = pending_payment,
                failed_payment = failed_payment,
                price_mismatch_error = price_mismatch_error),
        context_instance = RequestContext(request))

def book_mobile_order(order,request):
    pending_order = order.get_or_create_pending_order(request)
    delivery_info = pending_order.get_delivery_info()
    pending_order.reference_order_id = order.reference_order_id
    pending_order.save()
    if order.state == 'pending_order':
        order.reference_order_id = ''
        order.save()
    pending_order.payment_mode = order.payment_mode
    pending_order.save()
    request.session['pending_order'] = pending_order
    if utils.is_future_ecom(pending_order.client):
        cs = utils.get_session_obj(request)
        fbapi = cs['fbapiobj']
        cookie_file = fbapi.cookie_file #cs['fb_cookie_file']
        fb_order_respons = fbapi.add_to_cart_response #cs['fb_order_response']
        billing_info = fbapi.fb_user['items'][0]['billingInfo']
        order_response = fbapi.submit_order_to_fb(request,'mobile-user',fb_order_response,billing_info,pending_order,pending_order.payment_mode,cookie_file)
        if order_response['responseCode'] != 'OM_SUBMITTED_CART':
            log.info('Order was not submitted : %s' % order_response)
            return {'error':order_response}
        else:
            fb_order_id = order_response['items'][0]['orderId']
            order.reference_order_id = fb_order_id
            order.save()
    pending_order.notify_pending_order(request)
    return HttpResponseRedirect(request.path.replace('shipping','booked'))


def book(request):
    cart = get_cart_and_save_in_session(request)
    print "cart-",cart
    if not cart.get_items_for_billing(request):
        response = HttpResponseRedirect(request.path.replace('book','mycart'))
        return response
    payment_options_form = PaymentOptionsForm(request,cart)
    if request.method == 'POST':
        payment_options_form = PaymentOptionsForm(request,cart,request.POST)
        if payment_options_form.is_valid():
            payment_mode = None
            temp_payment_mode_ls = payment_options_form.cleaned_data['payment_mode'].split('#')
            temp_payment_mode = payment_options_form.cleaned_data['payment_mode'].split('#')
            po = PaymentOption.objects.get(id=temp_payment_mode_ls[1])
            if po.payment_mode.is_grouped and request.POST.has_key('payment_group_member'):
                cleaned_payment_mode = request.POST['payment_group_member']
                payment_mode = cleaned_payment_mode
            else:
                payment_mode = payment_options_form.cleaned_data['payment_mode'].split('#')[0]
            cart.payment_mode = payment_mode
            cart.save()
            if 'confirmnow.x' in request.POST or 'link_confirmnow' in request.POST:
                if utils.is_tinla_only_client(request.client.client):
                    #Update the inventory.
                    errors = cart.update_inventory('deplete')
                    #If no errors, then send notifications and book the order.
                    if errors:
                        #Order cannot be fulfilled
                        return render_to_response('order/book.html',
                                dict(action="orders/booked",
                                    payment_options_form = payment_options_form,
                                    errors=errors,
                                    order=cart),
                            context_instance = RequestContext(request))

                order = cart.create_payment_received_order(request)
                order.payment_mode = cart.payment_mode
                order.payment_realized_mode = cart.payment_mode
                order.save()

                payment_attempt = order.create_payment_attempt(request, Order.GATEWAY[payment_mode])
                payment_attempt.transaction_id = request.POST['transaction_no']#payment_options_form.cleaned_data['transaction_no']
                payment_attempt.response_detail = request.POST['transaction_notes'] #payment_options_form.cleaned_data['transaction_notes']
                if utils.get_ezoneonline() == request.client.client:
                    cs = utils.get_session_obj(request)
                    fbapi = cs['fbapiobj']
                    fbapi.submit_fb_cart(request,order,cart,payment_options_form,payment_mode,"orders/booked","order/book.html")
                    #submit_res = submit_fb_cart(request,pending_order,cart,payment_options_form,payment_mode,"orders/booked","order/book.html")
                    if fbapi.submit_cart_response:
                        return fbapi.submit_cart_response
                if order.state in ('pending_order',):
                    order.confirm(request)
                    payment_attempt.status = 'approved'
                    payment_attempt.save()
                    utils.clear_cart(request,order)
                    confirmed_orders_in_session = request.session.get(
                            'confirmed_orders', [])
                    confirmed_orders_in_session.append(payment_attempt.order.id)
                    request.session['confirmed_orders'] = confirmed_orders_in_session
                    return HttpResponseRedirect(request.path.replace('book','%s/confirmation' % (order.id)))

            elif 'bookorder.x' in request.POST or 'link_confirmlater' in request.POST or 'confirmlater.x' in request.POST:
                if utils.is_tinla_only_client(request.client.client):
                    #Update the inventory.
                    errors = cart.update_inventory('deplete')
                    #If no errors, then send notifications and book the order.
                    if errors:
                        #Order cannot be fulfilled
                        return render_to_response('order/book.html',
                                dict(action="orders/booked",
                                    payment_options_form = payment_options_form,
                                    errors=errors,
                                    order=cart),
                            context_instance = RequestContext(request))

                pending_order = cart.get_or_create_pending_order(request)
                if utils.is_future_ecom(request.client.client):
                    pending_order.reference_order_id = cart.reference_order_id
                pending_order.save()
                if cart.state == 'pending_order':
                    cart.reference_order_id = ''
                    cart.save()
                pending_order.payment_mode = cart.payment_mode
                if request.client.type in ['cc', 'store']:
                    pending_order.booking_agent = utils.get_user_profile(request.user)
                    pending_order.booking_timestamp = datetime.now()
                pending_order.save()
                request.session['pending_order'] = pending_order
                #For offline payments call submit_fb_cart
                if utils.is_future_ecom(request.client.client):
                    cs = utils.get_session_obj(request)
                    fbapi = cs['fbapiobj']
                    card_details = {}
                    card_details['cardtype'] = payment_options_form.cleaned_data.get('cardtype', '')
                    card_details['last4digits'] = payment_options_form.cleaned_data.get('last4digits', '1234')
                    resp = fbapi.update_user(request, utils.get_agent_for_fb_api(request), cart, payment_options_form)
                    fbapi.submit_fb_cart(request, pending_order, cart,
                            payment_options_form, payment_mode,
                            "orders/booked", "order/book.html",
                            card_details = card_details)
                    #submit_res = submit_fb_cart(request,pending_order,cart,payment_options_form,payment_mode,"orders/booked","order/book.html")
                    if fbapi.submit_cart_response:
                        return fbapi.submit_cart_response
                    else:
                        utils.clear_cart(request,pending_order)
                
                pending_order.notify_pending_order(request)
                return HttpResponseRedirect(request.path.replace('book','booked'))
    return render_to_response('order/book.html',
            dict(action="orders/booked",
                payment_options_form = payment_options_form,
                order=cart),
        context_instance = RequestContext(request))


def add_items_to_fb_cart(request,user_agent,pending_order):
    domain = request.META['HTTP_HOST']
    delivery_info = pending_order.get_delivery_info()
    if utils.is_cc(request):
        id = request.call['id']
        cs = request.session[id]
    else:
        cs = request.session
    try:
        cookie_file = cs['fb_cookie_file']
    except Exception,e:
        log.exception('%s' % repr(e))
        log.info('Session data on order for : %s' % (cs))
    current_user = pending_order.user
    fb_user = cs['fb_user']
    if fb_user['responseCode'] == fbapiutils.ERROR:
        return fb_user

    if not delivery_info.address.state:
        return dict(responseCode='STATE_NOT_SELECTED',responseMessage='Please select delivery state')
    if not delivery_info.address.city:
        return dict(responseCode='CITY_NOT_SELECTED',responseMessage='Please select delivery city')
    if fb_user['responseCode'] == fbapiutils.USER_FOUND:
        billing_info = fb_user['items'][0]['billingInfo']
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
    if not billing_info['city'] and not billing_info['country'] and not billing_info['postalCode'] and not billing_info['address1']:
        billing_info['city'] = delivery_info.address.city.name
        billing_info['country'] = 'IN'
        billing_info['postalCode'] = delivery_info.address.pincode
        billing_info['address1'] = delivery_info.address.address


    log.info('Updating user...')
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
        cookie_file)
    log.info('User updated: %s' % resp)

    fb_order_response = None
    items_to_delete = []
#    for item in pending_order.orderitem_set.all():
#        log.info('Adding sku: %s to cart' % item.seller_rate_chart.sku)
#        fb_order_response = orders.add_to_cart(item.seller_rate_chart.sku, item.seller_rate_chart.external_product_id, item.qty,user_agent,cookie_file)
#        log.info('response %s' % fb_order_response)
#        if not fb_order_response['responseCode'] == 'OM_ADDED_ITEM_TO_CART':
#            items_to_delete.append(item)
#            return fb_order_response
#        elif fb_order_response['responseCode'] == 'OM_ADDED_ITEM_TO_CART':
#            pending_order.reference_order_id = fb_order_response['items'][0]['orderId']
#            pending_order.save()
#            fb_items = fb_order_response['items'][0]['items']
#            for f_item in fb_items:
#                if f_item['skuId'] == item.seller_rate_chart.sku:
#                    if str(f_item['qty']) != str(item.qty):
#                        log.info('Removing item from cart: %s' % f_item)
#                        remove_item_response = orders.remove_from_cart(f_item['commerceItemId'],f_item['productId'],user_agent,cookie_file)
#                        log.info('Item Removed %s' % remove_item_response)
#                        fb_order_response = orders.add_to_cart(item.seller_rate_chart.sku, item.seller_rate_chart.external_product_id, item.qty,user_agent,cookie_file)

    cs = utils.get_session_obj(request)
    cs['fb_order_response'] = fb_order_response
    if utils.is_cc(request):
        call_id = request.call['id']
        request.session[call_id] = cs
        request.session.modified = True
    return fb_order_response

@never_cache
def process_payment_payback(request):
    # loyaltyTerminalid, sessionid, message, status OR
    # transactionid
    params = request.GET
    if request.method == 'POST':
        params = request.POST
    try:
        pa = PaymentAttempt.objects.get(id=params.get('sessionid'))
        if pa.order.state == 'confirmed':
            if request.path.startswith('/w/'):
                return HttpResponseRedirect(request.path.replace(
                    'process_payment_payback','%s/confirmation' % pa.order.id))
            return HttpResponseRedirect('/orders/%s/confirmation' % pa.order.id)
    except PaymentAttempt.DoesNotExist:
        request.session['payback_failed_payment'] = "failed"
        return HttpResponseRedirect('/orders/payment_mode')
    pa.process_response(params)
    return payment_status(request,pa)

@never_cache
def process_parameters_itz(request):
    log.info(" Itz Server response %s" % request.POST)
    params = request.POST
    description = { '0'    : "Success",
                    '3100' : "Transaction is already confirmed",
                    '-3100': "Communication Error at the Merchant's End",
                    '-3101': "Internal Error at the Merchant's End",
                    '-3103': "Transaction Confirmation Error at the Merchant's End",
                    '-3105': "Invalid Order ID",
                    '-3106': "Invalid Request/Action Type",
                    '-3107': "Invalid Request Data - Product cost doesn't match",
                   }
    response_code = "-3101"
    if params:
        try:
            pa = PaymentAttempt.objects.get(id=int(params.get('orderid', 0)))
            if str(int(pa.amount*100)) != str(params.get('productcost')):
                response_code = '-3107'
            else:
                order = pa.order
                if order.state == "confirmed":
                    response_code = '3100'
                else:
                    response_code = '0'
        except Exception, e:
            response_code = "-3105"
    else:
        response_code = '-3106'
    log.info("Response code sent to ITZ %s \n" % response_code)
    return HttpResponse('%s,%s' %(response_code, description.get(response_code)))

@never_cache
def process_payment_itz(request):
    if request.POST:
        params = request.POST
        try:
            #url_token = params.get('url_token')
            #request.call['url_token'] = url_token
            #request.call[id] = url_token.split('-')[3]
            pa = PaymentAttempt.objects.get(id=params.get('orderid'))
        except PaymentAttempt.DoesNotExist:
            request.session['failed_payment'] = "ITZ Payment Failed"
            return HttpResponseRedirect('%s/orders/shipping' % url_token)
        except Exception, e:
            pass
        pa.process_response(request)
        return payment_status(request,pa)
    else:
        return HttpResponseBadRequest()

@never_cache
def process_payment_ccavanue(request):
    params = request.POST
    if request.method == 'GET':
        params = request.GET
    merchant_id = params.get('Merchant_Id','')
    auth_desc = params.get('AuthDesc','')
    if merchant_id == ccAvenue.__merchantId:
        checksum = params['Checksum']
    try:
        pa = PaymentAttempt.objects.get(transaction_id=params['Merchant_Param'])
    except PaymentAttempt.DoesNotExist:
        return HttpResponseBadRequest()

    pa.process_response(params)
    return payment_status(request,pa)

@never_cache
def process_payment_hdfc(request):
    if request.method == 'POST':
        try:
            from payments import hdfcpg
            payment_attempt = PaymentAttempt.objects.get(transaction_id = request.POST.get('MD',None))
            data = {'MD':request.POST['MD'],'PaRes':request.POST['PaRes'],'emi_plan':payment_attempt.emi_plan}
            response = hdfcpg.process_response(payment_attempt,data)
            if not response:
                payment_attempt.status = 'rejected'
                payment_attempt.save()
            else:
                payment_attempt.process_response(response)
            return payment_status(request,payment_attempt)
        except PaymentAttempt.DoesNotExist:
            return HttpResponseBadRequest()

@never_cache
def process_payment_axis(request):
    if request.method == 'GET':
        try:
            from payments import hdfcpg
            payment_attempt = PaymentAttempt.objects.get(transaction_id = request.POST.get('MD',None))
            data = {'MD':request.POST['MD'],'PaRes':request.POST['PaRes'],'emi_plan':payment_attempt.emi_plan}
            response = hdfcpg.process_response(payment_attempt,data)
            payment_attempt.process_response(response)
            return payment_status(request,payment_attempt)
        except PaymentAttempt.DoesNotExist:
            return HttpResponseBadRequest()

@never_cache
def process_payment_citibank(request):
    params = request.POST.get('CititoMall')
    # "0410|813197934204|1|11229118|502200000000|100.00|N:|000000|773882|"
    # "msg code| checksum|1|merchant code| order id| amount|auth des|auth
    # code|trace no|"
    if params.find('||'):
        params = params.replace('||','|ND|')
    param_list = params.split('|')
    trace_number = param_list[8]
    reference_order_id = param_list[4]
    try:
        pa = PaymentAttempt.objects.get(
                order__reference_order_id=reference_order_id,
                citibanktracenumber__id = int(trace_number),
                )
    except PaymentAttempt.DoesNotExist:
        return HttpResponseBadRequest()
    pa.process_response(request)
    return payment_status(request,pa)

def payment_status(request,payment_attempt):
    if payment_attempt.status in ('approved','captured'):
        if (not utils.is_franchise(request)) and utils.is_future_ecom(request.client.client):
            cs = utils.get_session_obj(request)
            payment_options_form = cs.get('payment_options_form')
            card_details = cs.get('card_details')
            #For online payments call submit cart api after you receive the payment and it will confirm the order to ATG. No need to call confirm order API
            fbapi = cs['fbapiobj']
            if payment_attempt.order.payment_mode in ('credit-card','credit-card-emi-web'):
                fbapi.submit_fb_cart(request,payment_attempt.order,payment_attempt.order,payment_options_form,payment_attempt.order.payment_mode,"orders/payment_mode","order/online_payment_modes.html",**dict(card_details=card_details,pa=payment_attempt,Status=payment_attempt.fraud_status))
            else: 	
                fbapi.submit_fb_cart(request,payment_attempt.order,payment_attempt.order,payment_options_form,payment_attempt.order.payment_mode,"orders/payment_mode","order/online_payment_modes.html",**dict(card_details=card_details,pa=payment_attempt))
            #submit_res = submit_fb_cart(request,payment_attempt.order,payment_attempt.order,payment_options_form,payment_attempt.order.payment_mode,"orders/payment_mode","order/online_payment_modes.html",**dict(card_details=card_details))
            if fbapi.submit_cart_response:
                return fbapi.submit_cart_response
        if payment_attempt.order.payment_mode in ('credit-card', 'debit-card',
                'credit-card-emi-web', 'netbanking', 'card-web', 'payback', 'Itz'):
            if payment_attempt.order.payment_mode  == 'card-web':
                payment_mode = 'credit-card'
            else:
                payment_mode = payment_attempt.order.payment_mode
            payment_attempt.order.payment_realized_mode = payment_mode
        else:
            payment_attempt.order.payment_realized_mode = 'credit-card'
        payment_attempt.order.save()
        payment_attempt.order.confirm(request)
        utils.clear_cart(request, payment_attempt.order)
        confirmed_orders_in_session = request.session.get(
                'confirmed_orders', [])
        confirmed_orders_in_session.append(payment_attempt.order.id)
        request.session['confirmed_orders'] = confirmed_orders_in_session
        if utils.is_franchise(request):
            return HttpResponseRedirect('/orders/%s/confirmation' % payment_attempt.order.id)
        if request.path.startswith('/w/'):
            return HttpResponseRedirect(request.path.replace(
                'process_payment','%s/confirmation' % payment_attempt.order.id))
        return HttpResponseRedirect('/orders/%s/confirmation' % payment_attempt.order.id)
    if payment_attempt.status == 'rejected':
        request.session['failed_payment'] = request.POST.get('Message','Payment Failed. Please try again with another card')
        if utils.is_franchise(request):
            return HttpResponseRedirect('/orders/shipping')
        elif utils.is_future_ecom(request.client.client):
            return HttpResponseRedirect('/orders/payment_mode')
        return HttpResponseRedirect('/orders/shipping')
    if payment_attempt.status == 'pending':
        log.info('CCAVANUE PENDING STATUS: %s' % request.POST)
        request.session['pending_payment'] = payment_attempt
        return HttpResponseRedirect('/orders/payment_mode')

@never_cache
def process_payment(request):
    if request.method == 'POST':
        try:
            payment_attempt = PaymentAttempt.objects.get(transaction_id=request.POST.get('TxnID',None))
            payment_attempt.process_response(request)
            return payment_status(request,payment_attempt)
        except PaymentAttempt.DoesNotExist:
            return HttpResponseBadRequest()
    else:
        return HttpResponseBadRequest()

@never_cache
def admin_confirmation(request, admin_order_id):
    order = Order.objects.get(id=admin_order_id)

    return render_to_response("order/confirmed.html",
            {
                "order": order,
                "total_items": order.get_item_count(),
                "delivery_info": order.get_delivery_info(),
                "confirmed": True
            },
            context_instance = RequestContext(request))

@never_cache
def admin_cancelled(request, admin_order_id):
    order = Order.objects.get(id=admin_order_id)
    #Update inventory
    if utils.is_tinla_only_client(request.client.client):
        order.update_inventory('add')

    return render_to_response("order/cancelled.html",
            {
                "order": order
            },
            context_instance = RequestContext(request))

@never_cache
def order_cancelled(request, admin_order_id):
    order = Order.objects.get(id=admin_order_id)
    #Update inventory
    try:
        deliveryinfo = order.deliveryinfo_set.all()[:1].select_related(
                'address__first_name', 'address__last_name', 'address__address',
                'address__city', 'address__pincode', 'address__state',
                'address__country', 'address__phone').get()
    except DeliveryInfo.DoesNotExist:
        deliveryinfo = None
    if utils.is_tinla_only_client(request.client.client):
        order.update_inventory('add')

        #send email order modification to seller and customer.
    return render_to_response("order/order_cancelled.html",
            {
                "order": order,
                "total_items":order.get_item_count(),
                "deliveryinfo":deliveryinfo,

            },
            context_instance = RequestContext(request))

@never_cache
def confirmation(request, order_id):
    order = Order.objects.get(id=order_id)
    # check if this order_id exists in confirmed orders in this session
    if order.id not in request.session.get('confirmed_orders',[]):
#       # users can still visit confirmation page of their own orders
        if request.user.is_authenticated() and request.user.id != order.user.user.id:
#           # not confirmed in this session, does not belong to this user either. lets lie
            raise Http404
    try:
        deliveryinfo = order.deliveryinfo_set.all()[:1].select_related(
                'address__first_name', 'address__last_name', 'address__address',
                'address__city', 'address__pincode', 'address__state',
                'address__country', 'address__phone').get()
    except DeliveryInfo.DoesNotExist:
        deliveryinfo = None
    try:
        order_item = order.get_items_for_billing(request)[:1].get()
    except OrderItem.DoesNotExist:
        order_item = None
    similar_products = order_item.seller_rate_chart.product.similar_products(request)
    if similar_products:
        similar_products = similar_products[:6]
    cart_id = request.session.get('cart_id')
    if cart_id:
        cart = Order.objects.get(id=cart_id)
        if cart.payback_id:
            cart.payback_id = None
            cart.save()
    fb_share_link = "%s/%s/pd/%s/" % (request.get_host(),order_item.seller_rate_chart.product.slug,order_item.seller_rate_chart.product_id)
    dgm_sku_code = None
    if order.coupon:
        dgm_sku_code = 661193132812
    elif order.payable_amount > 250:
        dgm_sku_code = 214361427476
    else:
        dgm_sku_code = 858389242533
    address_info = {
        'first_name':mark_safe(deliveryinfo.address.first_name),
        'last_name':mark_safe(deliveryinfo.address.last_name),
        'address':mark_safe(deliveryinfo.address.address.strip()),
        'city':mark_safe(deliveryinfo.address.city),
        'pincode':mark_safe(deliveryinfo.address.pincode),
        'state':mark_safe(deliveryinfo.address.state),
        'country':mark_safe(deliveryinfo.address.country),
        'phone':mark_safe(deliveryinfo.address.phone),
        }
    payback_points_earned = (order.payable_amount*Decimal('0.03')).quantize(Decimal('1')) if order.payback_id else 0
    total_order_qty = 0
    for item in order.get_items_for_billing(request):
        total_order_qty += item.qty

    # Remove 'rmsID' from session if order in confirmed
    if 'rmsID' in request.session:
        del(request.session['rmsID'])
 
    return render_to_response("order/confirmed.html", {
        "order" :order,
        "deliveryinfo":deliveryinfo,
        "fb_share_link":fb_share_link,
        "similar_products":similar_products,
        "address_info":address_info,
        "confirmed":True,
        "payback_points_earned": payback_points_earned,
        "total_order_qty":total_order_qty,
        "total_items" : order.get_item_count(),
        "dgm_sku_code":dgm_sku_code,
        "delivery_info":deliveryinfo,
        "ga_states":["confirmed", "pending_order"],
        }, context_instance = RequestContext(request))

@never_cache
def booked(request):
    pending_order = None
    if 'pending_order' in request.session:
        pending_order = request.session['pending_order']
        del request.session['pending_order']

    return render_to_response("order/booked.html",
            { "order" : pending_order,
              "pending": True},
            context_instance = RequestContext(request))

def remove_fb_coupon(request):
    redirect_to = '/orders/mycart/'
    if request.method == "POST":
        cart = get_cart(request)
        coupon = cart.coupon
        if 'itemid' in request.POST:
            item_id = request.POST['itemid']
            try:
                oi = OrderItem.objects.get(id=item_id)
            except OrderItem.DoesNotExist:
                return HttpResponseRedirect(redirect_to)
            response = cart.remove_fb_coupon(request, coupon, oi)
        else:
            redirect_to = request.POST.get('redirect_to','/orders/mycart')
            response = cart.remove_fb_coupon(request, coupon)
    return HttpResponseRedirect(redirect_to)

def remove_coupon(request):
    if request.method == "POST":
        cart = get_cart(request)
        coupon = cart.coupon
        redirect_to = request.POST.get('redirect_to','/orders/mycart')
        response = cart.remove_coupon(request)
    return HttpResponseRedirect(redirect_to)

def apply_payback(request):
    if request.method == 'POST':
        redirect_to = request.POST.get('redirect_to','/orders/mycart')
        payback_id = request.POST.get('payback_id')
        cart = get_cart(request)
        if re.match(r'^[0-9]{16}$', payback_id):
            cart.payback_id = payback_id
            cart.save()
            request.session['payback_msg'] = "Payback ID accepted" 
        else:
            request.session['payback_msg'] = "Invalid Payback ID. Please enter a 16 \
                    digit numeric payback ID."
    return HttpResponseRedirect(redirect_to)

def apply_fb_coupon(request):
    if request.method == 'POST':
        code = request.POST['coupon_code']
        cs = utils.get_session_obj(request)
        fbapi = cs['fbapiobj']
        cart = get_cart(request)
        redirect_to = request.POST.get('redirect_to','/orders/mycart') 
        #applicable_top10s_for_all10_discount, applicable_top10s_for_any5_discount = cart.get_eligible_top10_discounts(request)
        #if applicable_top10s_for_all10_discount or applicable_top10s_for_any5_discount:
        #    response = {'responseCode':'COUPON_NOT_APPLICABLE'}
        #else:
        response = fbapi.apply_coupon(request,code,cart)
            
        log.info('Apply coupon response %s' % response)
        if response['responseCode'] == "OM_APPLIED_COUPON":
#            try:
#                coupon = Coupon.objects.get(code=code)
#            except Coupon.DoesNotExist:
#                #TODO once we get discount value from api we should replace the hard code value
#                json = response['items'][0]
#                promo_type = json['promoType']
#                if promo_type in fbapiutils.PROMOTION_TYPES_MAP:
#                    applies_to = fbapiutils.PROMOTION_TYPES_MAP[promo_type]['applies_to']
#                    discount_type = fbapiutils.PROMOTION_TYPES_MAP[promo_type]['discount_type']
#                promo_adjuster = json['promoAdjuster']
#                promo_name = json['promoName']
#                coupon = Coupon(code=code,promo_name=promo_name, status='active',
#                    applies_to = applies_to, discount_type = discount_type,
#                    discount_value = promo_adjuster)
#                coupon.save()
#            cart.apply_coupon(request,coupon)
            cart.remove_or_preserve_coupon(request, 'update_item', None)
            cart.update_blling(request)
            request.session['applied_coupon_msg'] = response['responseMessage']
            #return H("Your Coupon Code has been Accepted!!")
        elif response['responseCode'] == "OM_APPLY_COUPON_FAILED":
            request.session['applied_coupon_msg'] = response['responseMessage']
        elif response['responseCode'] == "OM_COUPON_DISC_NOT_ADJ":
            request.session['applied_coupon_msg'] = response['responseMessage']
        elif response['responseCode'] == "COUPON_NOT_APPLICABLE":
            request.session['applied_coupon_msg'] = "Cannot apply coupon because your cart contains discounted products."
            #return HttpResponse("Invalid Coupon Code.")
    return HttpResponseRedirect(redirect_to)

def apply_coupon(request, **kwargs):
    cart = get_cart(request)
    coupon_code = request.POST.get('coupon_code')
    cart.apply_coupon(request,coupon_code)
    action = next_checkout_action(request)
    return render_to_response('order/mycart.html',
        {'order':cart,'orderItems':cart.get_items_for_billing(request),'next_action':action},
        context_instance=RequestContext(request))

def payment_page_html(payment_mode):
    html = 'credit_card.html'
    if payment_mode == 'credit-card':
        html = 'credit_card.html'
    if payment_mode == 'card-at-store':
        html = 'card-at-store.html'
    if payment_mode == 'debit-card':
        html = 'debit_card.html'
    if payment_mode == 'emi':
        html = 'emi.html'
    if payment_mode == 'fmemi':
        html = 'fmemi.html'
    if payment_mode == 'credit-card-emi-web':
        html = 'credit_card_emi_web.html'
    if payment_mode == 'netbanking':
        html = 'netbanking.html'
    if payment_mode == 'card-web':
        html = 'emi.html'
    if payment_mode == 'cheque':
        html = 'cheque.html'
    if payment_mode == 'cod':
        html = 'cod.html'
    if payment_mode in ('cash', 'easybill', 'ICICICash', 'suvidha', 'Itz'):
        html = 'cash.html'
    if payment_mode == 'payback':
        html = 'payback.html'
    return html

@never_cache
def render_online_payment_page(request):
    payment_mode = request.GET['payment_mode'].split('#')[0]
    if payment_mode == 'fmemi':
        card_form = FMEMIForm()
    else:
        card_form = CreditCardForm()

    html = payment_page_html(payment_mode)
    order_id = request.GET['order_id']
    po_id = request.GET.get('po_id',None)
    po = None
    if po_id:
        po = PaymentOption.objects.get(id=po_id)
    order = Order.objects.get(id=order_id)
    
    # for cod mode
    mobile_num = None
    cod_status = 'neutral'
    if payment_mode == 'cod':
        # check if user is cod verified. if verified let him place order directly without zipdial verification.
        profile = order.user 
        cod_status = profile.cod_status
        if cod_status == 'neutral':
            mobile_num = profile.primary_phone
            # if order is cod verified allw ot place order.
            try:
                already_verified = CodOrderVerification.objects.get(order=order,
                    reference_order_id=order.reference_order_id).is_verified
                if already_verified:
                    cod_status = 'whitelisted'
            except CodOrderVerification.DoesNotExist:
                pass
            except Exception,e:
                log.info("==== ZIP DIAL COD exception: %s" % repr(e))
            
                
    if po.payment_mode.validate_billing_info:
    #if payment_mode in ['netbanking','credit-card-emi-web','credit-card']:
        shipping_address = order.get_delivery_info()
        try:
            billing_info = BillingInfo.objects.get(user=order.user)
        except BillingInfo.DoesNotExist:
            billing_info = None
        domain = request.META['HTTP_HOST']
        billing_info_form = BillingInfoForm(request,billing_info,domain)
        state_map = simplejson.dumps(fbapiutils.STATES_MAP)
        return render_to_response('order/%s' % html,
                {'card_form': card_form,
                    'shipping_address':shipping_address,
                    'billing_info_form': billing_info_form,
                    'order_user_id': order.user.id,
                    'id_order': order_id,'state_map':state_map,
                    'points': "%i" % (order.payable_amount*4,),
                },
                context_instance=RequestContext(request))
    else:
        return render_to_response('order/%s' % html,
                {'card_form': card_form,
                    'order_user_id': order.user.id,
                    'order':order,'po':po,
                    'points': "%i" % (order.payable_amount*4,),
                    'phone': mobile_num,
                    'cod_status': cod_status,
                },
                context_instance=RequestContext(request))

def cod_verification(request):
    if request.method == "POST":
        info = {}
        verification_code = request.GET.get('transaction_token', None)
        if verification_code:
            log.info(" ZIP DIAL RESPONSE %s " % request.GET)
            try:
                # process response from zipdial
                cod_order_verification = CodOrderVerification.objects.get(verification_code = verification_code) 
                cod_order_verification.is_verified = True
                cod_order_verification.verified_on = datetime.now()
                cod_order_verification.save()
                # update phone table if required
                phone = Phone.objects.get(verification_code=verification_code)
                phone.verified_on = datetime.now()
                phone.is_verified = True
                phone.save()
            except Phone.DoesNotExist:
                pass    #nothing to do. common case once user phone is verified
            except Exception,e:
                log.info("==== ZIP DIAL COD verification code exception: %s" % repr(e))

        else:
            mobile_no = request.POST.get('mobile')
            order_id = request.POST.get('order')
            reference_order_id = request.POST.get('reference_order_id')
            update = request.POST.get('update')
            
            if mobile_no and order_id:
                try:
                    log.info("getting order .......")
                    order = Order.objects.get(id=order_id, reference_order_id=reference_order_id)
                    log.info("got order .......")
                    if update:
                        # update user profile primary phone
                        profile = order.user
                        try:
                            phone = Phone.objects.get(phone = mobile_no)
                            if phone.user == profile:
                                # phone already attached to the user
                                profile.primary_phone = mobile_no
                                profile.save()
                            else:
                                # phone no is already occupied. can not attach to the user
                                phone = None    #set phone to none as phone verification is not required

                        except Phone.DoesNotExist:
                            # create a phone entry for the user?? again we are attaching phones to users without verification
                            phone = Phone(phone=mobile_no,user=profile,type='primary')
                            phone.save()
                            profile.primary_phone = mobile_no
                            profile.save()


                    # connect to zipdial for verification
                    jsonDict = {}
                    jsonDict['userEnteredMobileNumber'] = mobile_no
                    jsonDict['zipDialCallerID'] = 'cod'
                    jsonStr = simplejson.dumps(jsonDict)
                    try:
                        s1 = subscribeUser(jsonStr)
                        s = simplejson.loads(s1)
                        if(s['status'] == '1'):
                            # update CodOrderVerification table
                            try:
                                cod_order_verification = CodOrderVerification.objects.get(order=order,
                                    reference_order_id = order.reference_order_id)
                                cod_order_verification.verification_code = s['transaction_token']
                            except CodOrderVerification.DoesNotExist:
                                cod_order_verification = CodOrderVerification(order=order,
                                    verification_code=s['transaction_token'],
                                    reference_order_id=order.reference_order_id)
                            cod_order_verification.save()
                            # update Phone table if not already verified
                            try:
                                phone = Phone.objects.get(phone = mobile_no)
                                if phone.user == order.user and not phone.is_verified:  # verify phone only if attached to same user
                                    phone.verification_code = s['transaction_token']
                                    phone.save()
                            except Phone.DoesNotExist:
                                # can not attach phone to user
                                pass
                            # set information for zip dial verification
                            info['image_url'] = s['img']
                            info['verification_code'] = s['transaction_token']
                            info['status'] = 'ok'
                        else:
                            log.info("==== ZIP DIAL COD has returned empty string or failed status")
                            info['status'] = 'error'
                         #   info['error'] = 'Sorry we can not verify your phone number now. Please try again later'
                    except Exception,e:
                        log.info("==== ZIP DIAL COD has returned exception: %s" % repr(e))
                        info['status'] = 'error'
                        #info['error'] = 'Sorry we can not verify your phone number now. Please try again later'
                    response = HttpResponse(simplejson.dumps(info))
                    return response
                except Exception,e:
                    log.info("==== ZIP DIAL COD exception: %s" % repr(e))

    return HttpResponse('')

def cod_verification_status_check(request):
    if request.method == "POST":
        info = {}
        order_id = request.POST.get('order')
        reference_order_id = request.POST.get('reference_order_id')
        if order_id:
            order = Order.objects.get(id=order_id)
            try:
                cod_order_verification = CodOrderVerification.objects.get(order=order, 
                    reference_order_id=reference_order_id)
                if cod_order_verification.is_verified == True:
                    info['status'] = 'ok'
                else:
                    info['status'] = 'error'
            except CodOrderVerification.DoesNotExist:
                info['status'] = 'error'
            except Exception,e:
                log.info("==== ZIP DIAL COD exception: %s" % repr(e))
                info['status'] = 'error'
            response = HttpResponse(simplejson.dumps(info))
            return response
    else:
        return HttpResponse('')

@never_cache
def get_cvv_info(request):
    return render_to_response('order/cvv_info.htm',
        None,
        context_instance=RequestContext(request))

@never_cache
def get_book_button(request):
    payment_option = request.POST['payment_option']
    po = PaymentOption.objects.get(id=payment_option)
    state_map = simplejson.dumps(fbapiutils.STATES_MAP)
    return render_to_response('order/book_buttons.html',
        {'state_map':state_map,'po':po,'request':request},
        context_instance=RequestContext(request))

@never_cache
def get_payment_option_page(request):
    payment_option = request.POST['payment_option']
    order_id = request.POST['order_id']
    o = None

    service_providers = []
    from accounts.models import PaymentMode
    payment_modes = PaymentMode.objects.filter(is_grouped = True)
    for payment_mode in payment_modes:
        if payment_mode.service_provider not in service_providers:
            if payment_mode.service_provider != '':
                service_providers.append(payment_mode.service_provider)

    try:
        o = Order.objects.get(id=order_id)
        shipping_address = o.get_delivery_info()
        shipping_address.stateid = fbapiutils.STATES_MAP[shipping_address.address.state.name]
    except Exception,e:
        shipping_address = None
        pass
    try:
        billing_info = BillingInfo.objects.get(user=o.user)
    except BillingInfo.DoesNotExist:
        billing_info = None
    po = PaymentOption.objects.get(id=payment_option)
    grouped_options = []

    domain = request.META['HTTP_HOST']
    billing_info_form = BillingInfoForm(request,billing_info,domain)
    if po.payment_mode.is_grouped:
        domain_payment_options = DomainPaymentOptions.objects.filter(payment_option__account=po.account,
            payment_option__payment_mode__group_code=po.payment_mode.group_code,
            payment_option__payment_mode__is_grouped=True, is_active=True,
            client_domain=request.client)

        for dpo in domain_payment_options:
            grouped_options.append(dpo.payment_option)

        #grouped_options = PaymentOption.objects.filter(account=po.account,
        #    payment_mode__group_code=po.payment_mode.group_code,payment_mode__is_grouped=True)
        return render_to_response('order/payment_options/%s.html' % po.payment_mode.group_code,
            {'po':po,'request':request,'grouped_options':grouped_options,'order':o,'billing_info_form':billing_info_form, 'shipping_address':shipping_address,'order_user_id':o.user.id,'service_providers':service_providers},
            context_instance=RequestContext(request))
    else:
        return render_to_response('order/payment_options/%s.html' % po.payment_mode.code,
            {'po':po,'request':request,'order':o, 'billing_info_form':billing_info_form,'shipping_address':shipping_address, 'order_user_id':o.user.id},
            context_instance=RequestContext(request))

@never_cache
def validate_billing_info_form(request):
    if 'order_user_id' not in request.POST:
        return HttpResponse('not implemented')
    user_id = request.POST['order_user_id']
    user = Profile.objects.get(id = user_id)
    params = request.POST
    domain = request.META['HTTP_HOST']
    try:
        billing_info_form = BillingInfoForm(request, None, domain, request.POST)
    except Exception,e:
        pass
    if billing_info_form.is_valid():
        address, billing_info = utils.save_billing_info(request, user, params)
        return HttpResponse(simplejson.dumps(dict(status="ok")))
        #add_address_to_user(address,profile)
    else: #if billing info form is not valid
        return HttpResponse(simplejson.dumps(dict(status="error", error=billing_info_form.errors)))


def booked_order_range(from_date,to_date,request):
    source = request.GET.get('source','')
    if source and source!=unicode(0):
        source = Client.objects.get(id=source)
        qs_book = Order.objects.filter(Q(state = "pending_order")|Q(state = "confirmed"),client = source)
    else:
        qs_book = Order.objects.filter(Q(state = "pending_order") | Q(state = "confirmed"))
        source = -1
    qs = qs_book.filter(Q(timestamp__gte = from_date) & Q(timestamp__lte = to_date))
    return dict(qs=qs,source=source)

def confirmed_order_range(from_date,to_date,request):
    source = request.GET.get('source','')
    if source and source!=unicode(0):
        source = Client.objects.get(id=source)
        qs_confirm = Order.objects.filter(state = "confirmed", client=source)
    else:
        qs_confirm = Order.objects.filter(state = "confirmed")
        source = -1
    qs = qs_confirm.filter(Q(payment_realized_on__gte = from_date) & Q(payment_realized_on__lte = to_date))
    return dict(qs=qs,source=source)

def booked_item_range(from_date,to_date,request):
    source = request.GET.get('source','')
    seller = request.GET.get('seller','')
    qs_oi = OrderItem.objects.filter(Q(order__timestamp__gte = from_date) & Q(order__timestamp__lte = to_date))
    if source and source!=unicode(0):
        source = Client.objects.get(id=source)
        qs_oi = qs_oi.filter(order__client = source)
    else:
        source = -1
    if seller and seller!=unicode(0):
        seller = Account.objects.get(id=seller)
        qs_oi = qs_oi.filter(seller_rate_chart__seller=seller)
    else:
        seller = -1
    qs_oi = qs_oi.filter(Q(order__state = "pending_order") | Q(order__state = "confirmed"))
    return dict(qs=qs_oi,source=source,seller=seller)

def confirmed_item_range(from_date,to_date,request):
    source = request.GET.get('source','')
    seller = request.GET.get('seller','')
    qs_oi = OrderItem.objects.filter(Q(order__payment_realized_on__gte = from_date) & Q(order__payment_realized_on__lte = to_date) & Q(order__state = "confirmed"))
    if source and source!=unicode(0):
        source = Client.objects.get(id=source)
        qs_oi = qs_oi.filter(order__client = source)
    else:
        source = -1
    if seller and seller!=unicode(0):
        seller = Account.objects.get(id=seller)
        qs_oi = qs_oi.filter(seller_rate_chart__seller=seller)
    else:
        seller = -1
    return dict(qs=qs_oi,source=source,seller=seller)


def get_cart_info(request):
    orderItems = None
    cart_info = {}
    count = 0
    total = 0
    if request.path.startswith('/orders/auth/') or request.path.startswith('/orders/cancel/'):
        count_str = "0 items"
        total_str = utils.formatMoney(total)
        coupon_discount = None
        cart = None
    else:
        # Ensure cart does not get created newly
        cart = get_cart_and_save_in_session(request, **dict(create=False))
        if cart:
            coupon_discount = cart.coupon_discount
            if coupon_discount:
                coupon_discount = utils.formatMoney(coupon_discount)
            if request.path.endswith('confirmation') and cart:
                log.info('clear cart %s' % cart.state)
                utils.clear_cart(request, cart)
            if cart:
                total = cart.payable_amount
                orderItems = cart.get_items_for_billing(request)
                count = len(orderItems)
                orderItems = orderItems[:3]
            count_str = "0 items"
            total_str = utils.formatMoney(total)
            if count > 1 or count == 0:
                count_str = "%s items" % count
            else:
                count_str =  "%s item" % count
        else:
            count_str = "0 items"
            total_str = utils.formatMoney(total)
            coupon_discount = None
    cart_info['cart'] = cart
    cart_info['count'] = count_str
    cart_info['total_amount'] = total_str
    cart_info['order_items'] = orderItems
    cart_info['coupon_discount'] = coupon_discount
    return cart_info

def render_cart_info(request):
    '''
    Rendering the cart information in cart header html
    '''
    cart_info = get_cart_info(request)
    header_cart = get_template('web/header_cart.html')
    cart_ctxt = {}
    cart_ctxt['cart_info'] = cart_info
    cart_ctxt['request'] = request
    cart_html_ctxt = Context(cart_ctxt)
    cart_html = header_cart.render(cart_html_ctxt)
    
    '''
    Rendering Order Summary information in order right html
    '''
    order_info_template = get_template('order/right.html')
    order_info_ctxt = {}
    order_info_ctxt['order'] = cart_info['cart']
    order_info_ctxt['request'] = request
    order_info_html_ctxt = Context(order_info_ctxt)
    order_info_html = order_info_template.render(order_info_html_ctxt)
    
    response = dict(cart_html=cart_html, order_info_html=order_info_html)
    return HttpResponse(simplejson.dumps(response))

def show_cart_popup(request):
    dont_update_cart = request.GET.get('dont_update_cart', False)
    mycart_html = False
    if not dont_update_cart:
        cart_context = view_cart(request, None, **{'get_context':True})
        cart_context['request'] = request
        mycart_template = get_template('order/mycart.html')
        cart_html_ctxt = Context(cart_context)
        mycart_html = mycart_template.render(cart_html_ctxt)
    return render_to_response('order/cart_popup.html',
            {
                'dont_update_cart':dont_update_cart,
                'mycart_html':mycart_html,
            },context_instance=RequestContext(request))

def get_mycart_next_url(request, current_path):
    if utils.get_future_ecom_prod() == request.client.client:
        next_request_path = '/' 
        request.session['show_fbcart'] = True
    else:
        next_request_path = request.path.replace(current_path, 'mycart')
    return next_request_path

def ebs_data(request):
    Data = request.POST.get('data')
    request.session['rmsID'] = Data
    return HttpResponse("success")
