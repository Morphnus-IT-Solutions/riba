# Create your views here.
from datetime import datetime
from users.models import Profile,DailySubscription,NewsLetter,Phone
from users.models import Email as UserEmail
from users.models import Profile, PpdAdminUser
from locations.models import Address, AddressBook
import hashlib
import logging
import random
from django.template.loader import get_template
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, Http404
from django.template import RequestContext
from django.contrib.auth import login as auth_login
from django.utils.safestring import mark_safe
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Q,Count
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.core import serializers
from django.forms.models import modelformset_factory
from django.forms.models import inlineformset_factory
from django.forms.formsets import formset_factory
from django.contrib  import auth
from django.utils import simplejson
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from users.forms import *
from accounts.forms import *
from locations.forms import *
from django.contrib.auth.forms import AuthenticationForm
from orders.models import *
from orders.forms import BasePaymentOptionFormSet
from feedback.forms import *
from django.contrib.auth.decorators import login_required
from users.helper import *
from utils import utils
from web.views.response_views import *
from orders.views import get_cart
from django.core.mail import send_mail
from notifications.notification import Notification
from notifications.email import Email as EmailAddress
from notifications.sms import SMS
from lists.models import List, ListItem
import random
from django.template import Context, Template
from django.template.loader import get_template
from decimal import Decimal
from accounts.models import Client
from django.core.cache import cache
from django.template.defaultfilters import slugify
from django.http import Http404, HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect
from django.core.urlresolvers import reverse

log = logging.getLogger('request')
fb_log = logging.getLogger('fborder')

@login_required
def user_profile(request):
    if request.user.is_authenticated():
        user_info = utils.get_user_info(request)
        user = user_info['user']
        profile = user_info['profile']
        errors = []
        if request.method == "POST":#If the form has been submitted
            form = MyProfileForm(request.POST, instance = profile)
            if form.is_valid():
                primary_email = form.cleaned_data.get('primary_email',None)
                primary_phone = form.cleaned_data.get('primary_phone',None)
                secondary_phone = form.cleaned_data.get('secondary_phone',None)
                if primary_email:
                    try:
                        email = UserEmail.objects.get(email=primary_email,user=profile)
                    except UserEmail.DoesNotExist:
                        check_email = UserEmail.objects.filter(email=primary_email)
                        if not check_email:
                            email = UserEmail(email=primary_email,user=profile,type='secondary')
                            email.save()
                        else:
                            errors.append('email')
                if primary_phone:
                    try:
                        phone = Phone.objects.get(phone=primary_phone,user=profile)
                    except Phone.DoesNotExist:
                        check_phone = Phone.objects.filter(phone=primary_phone)
                        if not check_phone:
                            phone = Phone(phone=primary_phone,user=profile,type='secondary')
                            phone.save()
                        else:
                            #form.cleaned_data['primary_phone'] = None
                            errors.append('primary_phone')
                if secondary_phone:
                    try:
                        phone = Phone.objects.get(phone=secondary_phone,user=profile)
                    except Phone.DoesNotExist:
                        check_phone = Phone.objects.filter(phone=primary_phone)
                        if not check_phone:
                            phone = Phone(phone=secondary_phone,user=profile,type='secondary')
                            phone.save()
                        else:
                            errors.append('secondary_phone')
                if not errors:
                    status = form.save(commit=False)
                    status.id = profile.id
                    status.user_id = request.user.id
                    status.created_on = datetime.now()
                    status.save()

        else: #If the form has not been submitted
            form = MyProfileForm(instance = profile)

        my_acct_ctxt = getMyAccountContext(request)
        return render_to_response('user/profile.html',
        {
            'form': form,
            'acc':my_acct_ctxt,
            'errors':errors,
        },
        context_instance=RequestContext(request))
    else:
        return HttpResponse("New user")

@login_required
def show_address(request):
    user_info = utils.get_user_info(request)
    user = user_info['user']
    profile = user_info['profile']
    addresses = AddressBook.objects.filter(profile=profile).order_by('-id')
    my_acct_ctxt = getMyAccountContext(request)
    if request.method == "POST":        #If the form has been submitted
        id = request.POST.get("address_id")
        form = MyAddressForm(request,request.POST)
        if form.is_valid():
            formtemp = form.save(commit=False)
            countrytemp = form.cleaned_data["countryname"]
            statetemp = form.cleaned_data["statename"]
            citytemp = form.cleaned_data["cityname"]

            formtemp.country = utils.get_or_create_country(countrytemp)
            formtemp.state = utils.get_or_create_state(statetemp, formtemp.country)
            formtemp.city = utils.get_or_create_city(citytemp, formtemp.state)
            formtemp.type =  'user'
            formtemp.profile = profile
            formtemp.address = form.cleaned_data["address"]
            formtemp.phone = form.cleaned_data["phone"]
            formtemp.pincode = form.cleaned_data["pincode"]
            if id:
                formtemp.id = id
            if formtemp.defaddress:
                addresses = AddressBook.objects.filter(profile=profile)
                for address in addresses:
                    address.defaddress = False
                    address.save()
                formtemp.defaddress = True
            formtemp.created_on = datetime.now()
            formtemp.save()
            return HttpResponseRedirect(request.path)
        else:    #If the form is not valid
            return render_to_response('user/address.html',
            {
                'addresses':addresses,
                'form':form,
                'acc':my_acct_ctxt,
            },
            context_instance=RequestContext(request))

    else: 
        form = MyAddressForm(request)  #Fresh form with no entries
        return render_to_response('user/address.html',
        {
            'addresses':addresses,
            'form':form,
            'acc':my_acct_ctxt,
            'addr_id':0,
        },
        context_instance=RequestContext(request))

def get_address_info(request):
    id = request.GET.get('id','')
    form = MyAddressForm(request)  #Fresh form with no entries
    if id:
            address = AddressBook.objects.get(id=id)
            form = MyAddressForm(request,instance=address)  
    return render_to_response('user/address_details.html',
                {
                    'form':form,
                },
            context_instance=RequestContext(request))


@login_required
def user_editaddress(request):
    my_acct_ctxt = getMyAccountContext(request)
    if request.method == "POST":        #If the form has been submitted
        user_info = utils.get_user_info(request)
        user = user_info['user']
        profile = user_info['profile']
        id = request.POST.get("old_address")
        form = MyAddressForm(request,request.POST)
        if form.is_valid():
            formtemp = form.save(commit=False)
            countrytemp = form.cleaned_data["countryname"]
            statetemp = form.cleaned_data["statename"]
            citytemp = form.cleaned_data["cityname"]

            formtemp.country = utils.get_or_create_country(countrytemp)
            formtemp.state = utils.get_or_create_state(statetemp, formtemp.country)
            formtemp.city = utils.get_or_create_city(citytemp, formtemp.state)
            formtemp.type =  'user'
            formtemp.profile = profile
            formtemp.address = form.cleaned_data["address"]
            formtemp.phone = form.cleaned_data["phone"]
            formtemp.pincode = form.cleaned_data["pincode"]
            if id:
                formtemp.id = id
            if (request.POST.get("default_addr")=='1'):
                addresses = AddressBook.objects.filter(profile=profile)
                for address in addresses:
                    address.defaddress = False
                    address.save()
                formtemp.defaddress = True
            formtemp.created_on = datetime.now()
            formtemp.save()
            return HttpResponse(simplejson.dumps(dict(status="ok")))
        else:    #If the form is not valid
            return HttpResponse(simplejson.dumps(dict(status='error',error=form.errors)))
    else:  # If request.method is not POST
        id = request.GET['id']

        if id == '-1': # New address being added
            form = MyAddressForm(request)  #Fresh form with no entries
            return render_to_response('user/popup.html',
            {
                'form':form,
                'acc':my_acct_ctxt,
            },
            context_instance=RequestContext(request))

        else: # Address being edited
            addr = AddressBook.objects.get(id = id)
            form = MyAddressForm(request,instance =addr)
            return render_to_response('user/popup.html',
            {
                'form':form,
                'idget':id,
                'acc':my_acct_ctxt,
                'default_addr':addr.defaddress,
            },
            context_instance=RequestContext(request))

def user_deleteaddress(request):
    if request.method == 'POST':
        id = request.POST['id']
        addr_obj = AddressBook.objects.get(pk=id)
        addr_obj.delete(using='default')
        return HttpResponse("deleted")

@login_required
def user_notification(request):
    user_info = utils.get_user_info(request)
    user = user_info['user']
    profile = user_info['profile']
    user_exist = False
    newsletter = NewsLetter.objects.get(client=request.client.client,newsletter='DailyDeals')

    email_subscriptions = DailySubscription.objects.filter(newsletter=newsletter,email_alert_on__user=profile)
    sms_subscriptions = DailySubscription.objects.filter(newsletter=newsletter,sms_alert_on__user=profile)
    if request.method == "POST":
        email_alerts = request.POST.getlist('email_alerts')
        sms_alerts = request.POST.getlist('sms_alerts')
        #remove subscriptions
        for email in email_subscriptions:
            try:
                if email.email_alert_on.email not in email_alerts:
                    subscription = DailySubscription.objects.filter(newsletter=newsletter,email_alert_on__user=profile,email_alert_on=email.email_alert_on)
                    if subscription:
                        subscription = subscription[0]
                        subscription.is_email_alert = False
                        subscription.save()
            except Exception,e:
                pass
        for phone in sms_subscriptions:
            try:
                if phone.sms_alert_on.phone not in sms_alerts:
                    subscription = DailySubscription.objects.filter(newsletter__client=request.client.client,sms_alert_on__user=profile,sms_alert_on=phone.sms_alert_on)
                    if subscription:
                        subscription = subscription[0]
                        subscription.is_sms_alert = False
                        subscription.save()
            except Exception,e:
                pass
        #TODO add subscriptions
        for email in email_alerts:
            u_email = UserEmail.objects.get(email=email)
            subscription = DailySubscription.objects.filter(newsletter=newsletter,email_alert_on=u_email)
            if not subscription:
                subscription = DailySubscription(newsletter=newsletter,email_alert_on=u_email)
                subscription.save()
            else:
                subscription = subscription[0]
                subscription.is_email_alert = True
                subscription.save()

        for phone in sms_alerts:
            u_phone = Phone.objects.get(phone=phone)
            subscription = DailySubscription.objects.filter(newsletter=newsletter,sms_alert_on=u_phone)
            if not subscription:
                subscription = DailySubscription(newsletter=newsletter,sms_alert_on=u_phone)
                subscription.save()
            else:
                subscription = subscription[0]
                subscription.is_sms_alert = True
                subscription.save()
    else:
        user_exist = request.GET.get('user',False)
    emails = UserEmail.objects.filter(user=profile)
    phones = Phone.objects.filter(user=profile)
    my_acct_ctxt = getMyAccountContext(request)
    message = ''
    if user_exist == 'exist':
        message = "Contact already exist for another user. Cannot be added to your profile."
    elif user_exist == 'added':
        message = 'Contact has been registered to your subscription profile.'
    elif user_exist == 'same':
        message = 'Contact has been already registered for your subscription profile.'
    return render_to_response('user/notification.html',
       {
           'emails':emails,
           'phones':phones,
           'acc':my_acct_ctxt,
           'message':message,
       },
       context_instance=RequestContext(request))

def get_random_alphabets(length=40):
    allowedChars = "abcdefghijklmnopqrstuvwzyzABCDEFGHIJKLMNOPQRSTUVWZYZ0123456789"
    word = ""
    for i in range(0, length):
            word = word + allowedChars[random.randint(0,0xffffff) % len(allowedChars)]
    return word

def user_change_password(request):
   return render_to_response('user/change_password.html',
       None,
       context_instance=RequestContext(request))


def user_help(request):
    return render_to_response('user/help.html',
        None,
        context_instance=RequestContext(request))

def user_help_status(request):
    return render_to_response('user/help_status.html',
        None,
        context_instance=RequestContext(request))

def user_order_confirmation(request):
    return render_to_response('user/order_confirmation.html',
        None,
        context_instance=RequestContext(request))

def get_agent_order_history(request,startOrderIndex,items_per_page,agent=None,from_date=None,to_date=None):
    from django.db import connections
    cursor = connections['atg'].cursor()
    if agent:
        order_items = OrderItem.objects.filter(Q(order__booking_agent=agent) | Q(order__confirming_agent=agent), order__timestamp__gte=from_date, order__timestamp__lte=to_date+timedelta(days=1))
    else:
        order_items = OrderItem.objects.filter(order__timestamp__gte=from_date, order__timestamp__lte=to_date+timedelta(days=1))
    
    row = cursor.fetchall()
    order_history = []
    payment_modes = {'creditCard':'Credit Card', 'cashPayment':'Cash'}
    for i in row:
        order = {}
        order['orderId'] = i[0]

        if not i[1]:
            order['orderBookingDate'] = '--'
        else:
            order['orderBookingDate'] = str(i[1])
        
        if not i[2]:
            order['orderConfirmationDate'] = '--'
        else:
            order['orderConfirmationDate'] = str(i[2])
        
        order['articleId'] = i[3]
        order['skuId'] = i[4]
        order['productId'] = i[5]
        order['quantity'] = i[6]
        order['orderTime'] = i[7]
        order['lineItemPrice'] = i[8] 
        order['totalAmount'] = i[9]
        order['modeOfPayment'] = payment_modes[i[10]]
        
        if not i[11]:
            order['confirmAgentId'] = '--'
        else:
            order['confirmAgentId'] = i[11]

        if not i[12]:
            order['bookAgentId'] = '--'
        else:
            order['bookAgentId'] = i[12]
        order_history.append(order)

    return order_history

def get_total_number_of_orders(request, client_id, sid, medium, agent=None,from_date=None,to_date=None):
    key = None
    if agent:
        key = '%s#ezone' % agent.id
    else:
        key = 'all#ezone'

    orderitems = cache.get(key)
    if not orderitems:
        if agent:
            orderitems = OrderItem.objects.filter(order__client=client_id, seller_rate_chart__seller=sid, order__medium=medium).filter(Q(order__booking_agent=agent)|Q(order__confirming_agent=agent)).filter(Q(order__payment_realized_on__gte=from_date)|Q(order__timestamp__gte=from_date),Q(order__payment_realized_on__lte=to_date)|Q(order__timestamp__lte=to_date))
        else:
            orderitems = OrderItem.objects.filter(order__client=client_id, seller_rate_chart__seller=sid, order__medium=medium).filter(Q(order__payment_realized_on__gte=from_date)|Q(order__timestamp__gte=from_date),Q(order__payment_realized_on__lte=to_date)|Q(order__timestamp__lte=to_date))
        cache.set(key, orderitems, 1200)   
    return orderitems

@login_required
def show_agent_order_history(request):
    agent = request.user.username
    if not agent:
        raise Http404
    
    pagination = {}
    order_history = []
    #if not utils.is_future_ecom(request.client.client):
        #To be added later
    #    pass
    #else:
    '''if utils.is_future_ecom(request.client.client):
        try:
            page_no = request.GET.get('page',1)
            page_no = int(page_no)
            items_per_page = 15
            total_results = get_total_number_of_orders(request,agent)
            total_pages = int(math.ceil(Decimal(total_results)/Decimal(items_per_page)))
            pagination = utils.getPaginationContext(page_no, total_pages, '')
            startOrderIndex = ((page_no-1) * items_per_page + 1)
            order_history = get_agent_order_history(request,startOrderIndex,items_per_page,agent)
            fb_log.info('Order History for agent %s : %s' % (agent,order_history))
        except Exception,e:
            log.exception('Exception while rendering order history: %s' % repr(e))
            pass
    '''    
    my_acct_ctxt = getMyAccountContext(request)
    return render_to_response('user/agentperformance.html',
        {'orders':order_history,
        'acc':my_acct_ctxt,
        'pagination':pagination,
        },
        context_instance=RequestContext(request))


@login_required
def show_user_orders(request):
    user_info = utils.get_user_info(request)
    profile = user_info['profile']
    user = user_info['user']
    atg_order_info = []
    if not user:
        raise Http404
    orders = []
    suggestion = {}
    #if not utils.is_future_ecom(request.client.client):
    if request.method == 'POST':
        order_id = request.POST['order_id']
        try:
            orders = Order.objects.filter(id=order_id,user=profile,
                client=request.client.client).order_by('-timestamp').exclude(support_state = None)
        except:
            pass
    else:
        orders = Order.objects.filter(user=profile,
            client=request.client.client).order_by('-timestamp').exclude(Q(support_state = None)| \
                    Q(payment_mode = None)|Q(payment_mode = ''))
    
    order_details = orders
    if orders:
        for order in order_details:
            if order.payment_mode not in utils.DEFERRED_PAYMENT_MODES and order.support_state == 'booked':
                orders.exclude(id=order.id)
    
    total_results = orders.count()
    page_no = request.GET.get('page',1)
    page_no = int(page_no)
    items_per_page = 5
    total_pages = int(math.ceil(Decimal(total_results)/Decimal(items_per_page)))
    pagination = utils.getPaginationContext(page_no, total_pages, '')
    start = items_per_page * (page_no - 1)
    end = start + items_per_page
    orders = orders[start:end]
    
    if page_no >= total_pages or total_results == 0: 
        # Last page of order summary or 0 orders in TINLA db
        # check in user has orders in ATG db
        try:
            username = profile.atg_login
            profile_id = DpsUser.objects.get(login=profile.atg_login).dps_id
            orders_info = orders_api.get_order_by_user(profile_id, '', '', request)
            if orders_info:
                total_atg_results = orders_info['items'][0]['totalNoOfOrdersInProfile']
                if total_atg_results > 0:
                    if total_results == 0:
                        # User has orders only in ATG and not in TINLA
                        # redirect to ATG's order summary
                        url = utils.get_cc_url(request, 'user/orders_old/')
                        return HttpResponseRedirect(url)    
                    # User also has orders in ATG db
                    # suggest a link for redirection to ATG's  order summary
                    suggestion.update({'link':"user/orders_old/", 'data':"More Orders"})
        except Exception,e:
            pass
    my_acct_ctxt = getMyAccountContext(request)
    return render_to_response('user/orders.html',
        {
            'orders':orders,
            'acc':my_acct_ctxt,
            'pagination':pagination,
            'suggestion':suggestion, 
            'detail_redirection':'orders',
        },
        context_instance=RequestContext(request))


def show_seller_orders(request):
    user_dict = get_user_dict(request) 
    if not user:
        raise Http404
    state = 'confirmed'
    user_info = utils.get_user_info(request)
    profile = user_info['profile']
    user = user_info['user']
    account = profile.managed_accounts.all()[0]
    if request.method == 'POST':
        order_id  = request.POST['order_id']
        try:
            order_items = OrderItem.objects.filter(seller_rate_chart__seller=account,order__state=state,order__id=order_id).order_by('-order__payment_realized_on')
        except:
            order_items = []
    else:
        order_items = OrderItem.objects.filter(seller_rate_chart__seller=account,order__state=state).order_by('-order__payment_realized_on')
    orders = []

    o_dict={}
    for order_item in order_items:
        try:
            order = order_item.order
        except:
            continue
        if order_item.order.id in o_dict:
            obj = o_dict[order_item.order.id]
        else:
            o_dict[order_item.order.id] = {}
            obj = {'list_price_total':Decimal(0),'shipping_charges':Decimal(0),'payable_amount':0.00,'get_discount':Decimal(0),'coupon_discount':0.00,'payment_realized_on':order_item.order.payment_realized_on,'id':order_item.order.id,'formatted_currency':order_item.order.formatted_currency()}
        obj['list_price_total'] += order_item.list_price
        obj['shipping_charges'] += order_item.shipping_charges
        obj['payable_amount'] +=  order_item.payable_amount()
        obj['get_discount'] += (order_item.list_price - order_item.sale_price)
        obj['coupon_discount'] += order_item.spl_discount()
        obj['state'] = 'confirmed'
        orders.append(obj)

    my_acct_ctxt = getMyAccountContext(request)
    
    return render_to_response('user/orders.html',
        {'orders':orders,
        'acc':my_acct_ctxt,
        'state':state},
        context_instance=RequestContext(request))

def order_auth(request,order_id):
    response = None
    if request.POST:
        user_info = utils.get_user_info(request)
        profile = user_info['profile']
        user = user_info['user']
        mobile = request.POST['mobile']
        phone_number = re.compile('\d{10}')
        if not phone_number.match(mobile):
            error = 'Please enter a 10 digit phone number'
            response = render_to_response('user/auth.html',
                {'error':error,'order_id':order_id},
                context_instance = RequestContext(request))
            return response
        try:
            user = User.objects.get(username=mobile)
        except User.DoesNotExist:
            error = 'Please use the 10 digit phone number you used to book your order'
            response = render_to_response('user/auth.html',
            {'error':error,'order_id':order_id},
            context_instance = RequestContext(request))
            return response
        usr = auth.authenticate(username=mobile,orderid=order_id,**dict(request=request))
        if usr is not None and usr.is_active:
            auth.login(request,usr)
        else:
            error = 'Please use the 10 digit phone number you used to book your order'
            response =  render_to_response('user/auth.html',
            {'order_id':order_id,'error':error},
            context_instance = RequestContext(request))
            return response
    else:
        user_info = utils.get_user_info(request)
        user = user_info['user']
        if user:
            profile = user_info['profile']
            try:
                order  = Order.objects.get(id=order_id)
            except Order.DoesNotExist:
                raise Http404
            if order.user.id != profile.id:
                raise Http404
        else:
            response =  render_to_response('user/auth.html',
            {'order_id':order_id},
            context_instance = RequestContext(request))
            return response
    return response

def get_user(request):
    user = None
    if utils.is_cc(request):
        id = request.call['id']
        user = request.session[id]['user']
    else:
        user = request.user
        if user.is_anonymous():
            user = None
    return user


def user_order_details(request, order_id):
    if not request.META.get('HTTP_REFERER'):
        raise Http404
    order = None
    order_items = None
    #if not utils.is_future_ecom(request.client.client):
    try:
        order = Order.objects.get(id=order_id,
            client=request.client.client)
        order_items = order.get_order_items(request, select_related=('sap_order_item','seller_rate_chart',
            'seller_rate_chart__product','bundle_item')).order_by('id')
        try:
            delivery_info = order.get_address(request, type='delivery')
        except DeliveryInfo.DoesNotExist:
            delivery_info = ''
        
        shipments = order.get_shipments(request, select_related=('lsp',), 
                exclude=dict(status='deleted')).order_by('id')
        shipment_items = ShipmentItem.objects.select_related('order_item').filter(shipment__order=order).exclude(
            shipment__status='deleted').order_by('shipment')
        
        my_acct_ctxt = {'section':'orders'}
        return render_to_response('user/order_details.html',
            {
                'order':order,
                'order_items':order_items,
                'delivery_info':delivery_info,
                'shipments':shipments,
                'shipment_items':shipment_items,
                'acc':my_acct_ctxt,
                'order_redirection':'orders',
            },
            context_instance=RequestContext(request))
    
    except Order.DoesNotExist:
        raise Http404

def track_order(request):
    if request.method == 'POST':
        username = request.POST.get('username','')
        error = []
        if not request.user.is_authenticated():
            if utils.is_valid_email(username):
                input_type = "email"
            elif utils.is_valid_mobile(username):
                input_type = "mobile"
            else:
                input_type = "id"
                error.append('Enter a valid Email or Mobile Number.')
        else:
            input_type = "registered"
            try:
                username = utils.get_user_info(request)['profile']
            except:
                raise SessionExpired('Your session expired. Please start again')
        order_id = request.POST.get('order_id','')
        order_id = order_id.encode('ascii','ignore')
        profile = None
        order_status = None
        order_info = []
        address = {}
        if order_id and input_type != "id":
            if not request.user.is_authenticated():
                user_info = utils.get_profile_by_email_or_phone(username)
            else:
                user_info = username
            if utils.is_future_ecom(request.client.client):
                order = Order.objects.filter(reference_order_id = order_id, client = request.client.client)
                order_info = order and order[0] or ''
            else:
                try:
                    order_info = Order.objects.get(id = order_id)
                except Order.DoesNotExist:
                    pass
            try:
                if user_info == order_info.user:
                    return HttpResponseRedirect(request.path.replace('order/track_order','user/orders/%s' % order_info.id))
            except:
                pass
            if utils.is_future_ecom(request.client.client):
                try:
                    atg_username = user_info.atg_login
                    profile_id = DpsUser.objects.get(login=atg_username).dps_id

                    order_infos = orders_api.get_order_by_orderid(order_id, '', '', request)
                    if profile_id == order_infos['items'][0]['profileId']:
                        return HttpResponseRedirect(request.path.replace('order/track_order','user/orders_old/%s' % order_info.id))
                except:
                    pass
            error.append('Order not registered to your profile.')
        else:
            if not order_id:
                error.append('Enter an Order Id')
        return render_to_response('user/track_order.html',{'errors':error,'order_status':None},context_instance=RequestContext(request))
    return render_to_response('user/track_order.html',{'errors':None,'order_status':None},context_instance=RequestContext(request))

@login_required
def seller_order_details(request, order_id, client_name, seller_name):
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        new_client_name = request.POST.get('user_clients',None)
        new_seller_name = request.POST.get('user_sellers',None)
        if new_client_name:
            return HttpResponsePermanentRedirect(reverse('ppd-user-orders',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers','order_state':'confirmed'}))
        if new_seller_name:
            return HttpResponsePermanentRedirect(reverse('ppd-user-orders',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,'order_state':'confirmed'}))
    
    if seller_name == 'all-sellers':
        current_seller_id = 0
    else:
        current_seller_id = Account.objects.select_related('id').filter(slug = seller_name)[0].id

    client_id = Client.objects.filter(slug = client_name)[0].id
    
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
    
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    my_acct_ctxt = getMyAccountContext(request)
    accounts = profile.managed_accounts.filter(client__id = client_id)
    
    try:
        order = Order.objects.get(id=order_id,client__id=client_id)
    except Order.DoesNotExist:
        raise Http404
    
    selected_client = Client.objects.get(id=client_id)
    if utils.is_ezoneonline(selected_client) or utils.is_future_ecom(selected_client):
        client_type = True
    else:
        client_type = False
    passing_dict = {'order':order,
        'client_type':client_type,
        'loggedin':True,
        'accounts':accounts,
        'current_seller_id':current_seller_id,
        'clients':clients,
        'acc_section_type':'confirmed',
        'client_name':client_name,
        'seller_name':seller_name,
        'url':url,
        }   
    return render_to_response('seller/order_details.html', passing_dict,  context_instance=RequestContext(request))

def getMyAccountContext(request):
    path = request.path.split('/')
    ctxt = {'section':'orders'}
    if len(path) > 2:
        ctxt['section'] = path[-2] or 'orders'
    return ctxt

def set_logged_in_user(request,user, via_checkout = False):
    if not user:
        return

    previous_cart_id = request.session.get('cart_id', None)
    profile = utils.get_user_profile(user)
    if utils.is_cc(request) or utils.is_cs(request):

        call_id = request.call['id']
        if call_id in request.session:
            cs = request.session[call_id]
            if 'user' not in cs or 'profile' not in cs:
                cs['user'] = user
                cs['profile'] = profile
                request.session[request.call['id']] = cs
        else:
            my_acct_ctxt = getMyAccountContext(request)
            request.session[call_id] = {
                'user' : user,
                'profile' : profile,
                'atg_username' : request.call['cli']
                }
    else:
        auth.login(request,user)
        set_eligible_user(request,profile,'normal')
        request.session['facebookid'] = profile.facebook

    # XXX via_checkout gets passed as string False sometimes
    if 'cart_id' in request.session and 'via_checkout' != False:
        # XXX Do not delete the cart id if facebook login is triggered
        # XXX during the checkout process
        del request.session['cart_id']

    if previous_cart_id:
        if request.session.get('cart_id', None) != previous_cart_id:
            if via_checkout != False:
                # XXX Ugly. Need to pass a flag to preserve cart post
                # XXX login. Or treat facebook login as order signin
                request.session['cart_id'] = previous_cart_id

    cart = get_cart(request)
    cart.user = profile
    cart.save()

    utils.set_cart_count(request,cart)
    cs = utils.get_session_obj(request)
    #if utils.is_future_ecom(request.client.client):
    #    fbapi = FuturebazaarAPI(request,profile,cart)
    #    fbapi.sync_cart_for_signin(request, cart)
    #    cs['fbapiobj'] = fbapi
    #    utils.set_session_obj(request,cs)


def clear_call_session(request,id):
    if id in request.session:
        del request.session[id]


def validate_username_and_password(username, password, check_password=None):
    ''' Checks if the given username and password confirm to validations
        - username should not be empty
        - password should not be empty
        - username should be valid email or mobile
        - password should be strong (optional atleast 4 characters. phew!)
        Returns empty string or error message
    '''

    if not username and not password:
        return 'Please enter a valid 10 digit mobile or email'
    elif not username:
        return 'Please enter a valid 10 digit mobile or email'
    elif not password:
        return 'Please enter password'
    elif username:
        if not (
            utils.is_valid_email(username) or utils.is_valid_mobile(username)):
            return 'Please enter a valid 10 digit mobile or email'

    if check_password is not None:
        if len(password) < 4:
            return 'Please enter password of minimum 4 characters'
        if not check_password:
            return 'Please enter confirm password'
        if check_password != password:
            return 'Passwords do not match'

    # All validations passed, return empty string
    return ''

def login_and_redirect(request, user, redirect_to, **kwargs):
    if 'is_redirect' in kwargs:
        # Valid User, so logged in...
        set_logged_in_user(request, user)
        return HttpResponseRedirect(redirect_to)

def signin(request):
    params = request.POST

    username = params.get('username','').strip()
    password = params.get('password','').strip()
    redirect_to = params.get('next','').strip()

    signin_html = 'user/signin.html'
    if request.is_ajax():
        source = params.get('source', None)
        if source == 'refer_friend':
            signin_html = 'user/refer_friend_signin.html'
            request.session['refer_friend'] = True
        else:
            signin_html = 'web/header_signin.html'    
    # Do simple validations to check if username and password are valid
    error = validate_username_and_password(username, password)
    if not error:
        if utils.is_valid_email(username):
            username = utils.check_special_characters(username)
        # good to go, lets try to authenticate
        user = auth.authenticate(username=username, password=password,**dict(request=request))
        if user is not None:
            if user.is_active:
                # XXX Should be removed
                request.session['atg_username'] = username
                utils.set_user_subscribed_for_deals(request)
                try:
                    response = login_and_redirect(request, user, redirect_to, **dict(is_redirect=True))
                    if request.is_ajax():
                        ajax_response = dict(status='ok', html='')
                        return HttpResponse(simplejson.dumps(ajax_response))
                    return response
                except Exception, e:
                    log.exception('Unable to log in user  %s' % repr(e))
                    error = 'Sorry, we are unable to log you in'
                    # Logout user
                    auth.logout(request)
                    # Clear session variables
                    if 'atg_username' in request.session:
                        del request.session['atg_username']
                    if 'fbapiobj' in request.session:
                        del request.session['fbapiobj']            
            else:
                # email login verification pending
                error = 'Please verify your login through verification Email or SMS'
        else:
            error = 'Incorrect password. Please try again'
    context = {
        'signin_error': error,
        'next':redirect_to,
        'username': username,
        'type': 'signin'
    }
    response = render_to_response(signin_html, context, context_instance=RequestContext(request))
    if request.is_ajax():
        signin_info_template = get_template(signin_html)
        signin_info_ctxt = context
        signin_info_ctxt['request'] = request
        signin_info_html_ctxt = Context(signin_info_ctxt)
        signin_info_html = signin_info_template.render(signin_info_html_ctxt)
        ajax_response = dict(status='failed', html=signin_info_html)
        return HttpResponse(simplejson.dumps(ajax_response))
    return response

def validate_signup(request, **kwargs):
    params = request.POST

    username = params.get('username','').strip()
    password = params.get('password','').strip()
    check_password = params.get('cpassword','').strip()
    redirect_to = params.get('next','').strip()
    error = validate_username_and_password(username, password, check_password)
    user=''
    log.info("VALID U P %s" % error)
    if not error:
        if utils.is_valid_email(username):
            username = utils.check_special_characters(username)
        profile = utils.get_profile_by_email_or_phone(username)
        if profile:
            # registered user, might not have set his password already
            # typically users coming through callcenter or subscriptions or guest checkout
            # we allow them to set a password.
            # TODO should probably verify mobile/email in future
            u = profile.user
            if profile.user.has_usable_password():
                error = 'Sorry, %s is not available' % username
                return error, login_and_redirect(request, user, redirect_to, **kwargs), u
            else:
                u.set_password(password)
                if kwargs.get('to_be_verified',''):
                    u.is_active = False
                u.save()		
        else:
            # free to registe, lets create new user and profile
            user, profile = utils.get_or_create_user(username,'',password)
            if kwargs.get('to_be_verified',''):
                user.is_active = False
                user.save()
            profile.atg_username = username
            profile.save()

        user = auth.authenticate(username=username,password=password, **dict(request=request))
        if user is not None and user.is_active:
            # TODO need to find why are we setting user in session 
            # TODO ...only for signup and not in sigin
            request.session['user'] = profile
            request.session['atg_username'] = username
            return error, login_and_redirect(request, user, redirect_to, **kwargs), user
    return error, redirect_to, user

def signup(request, page=None):
    error, redirect_to, username = validate_signup(request, **dict(is_redirect=True,to_be_verified = True))
    signup_html = 'user/signin.html'
    is_email_success  = False
    if not error:
        if utils.is_valid_email(request.POST.get('username','').strip()) and username.is_active == False:
            is_email_success = True
            send_verification_email(request,request.POST.get('username','').strip() , username)
            context = {'is_email' : "true", 'signup_username': username,}
            return render_to_response("user/sms_verification.html", context, context_instance=RequestContext(request))
        if utils.is_valid_mobile(request.POST.get('username','').strip()) and username.is_active == False:
            send_verification_sms(request,request.POST.get('username','').strip() , username)
            context = {'signup_username': username,}
            return render_to_response("user/sms_verification.html", context, context_instance=RequestContext(request))
        if request.is_ajax():
            ajax_response = dict(status='ok', html='')
            return HttpResponse(simplejson.dumps(ajax_response))
        redirect_to = "/"
        return HttpResponseRedirect(redirect_to)
    context = {
        'signup_error': error,
        'next':redirect_to,
        'signup_username': username,
        'type': 'signup'
    } 
    if request.is_ajax():
        signup_html = 'web/header_signup.html'    
        signup_info_template = get_template(signup_html)
        signup_info_ctxt = context
        signup_info_ctxt['request'] = request
        signup_info_html_ctxt = Context(signup_info_ctxt)
        signup_info_html = signup_info_template.render(signup_info_html_ctxt)
        ajax_response = dict(status='failed', html=signup_info_html)
        return HttpResponse(simplejson.dumps(ajax_response))
    return render_to_response(signup_html, context, context_instance=RequestContext(request))
 
def send_verification_email(request,email_id, username):
    try:
        vcode = get_random_alphabets(length=40)
        email_objs = Email.objects.filter(email = email_id)
        email_obj = email_objs[0]
        email_obj.verification_code = vcode
        email_obj.save()
        utils.verification_send_email(request, email_id, email_obj)
    except Exception, e:
        fb_log.exception("Unable to send verification email for Sign Up")

def send_verification_sms(request,phone_no, username):
    try:
        vcode = str(random.getrandbits(20))
        phone_objs = Phone.objects.filter(phone = username)
        phone_obj = phone_objs[0]
        phone_obj.verification_code = vcode
        phone_obj.save()
        utils.verification_send_sms(request, phone_no,vcode)
    except Exception, e:
        fb_log.exception("Unable to send verification SMS for Sign Up")

def new_user_sms_verification(request):
    context = {}
    return render_to_response("user/sms_verification.html", context, context_instance=RequestContext(request))   

def user_email_verification(request):
    if request.method == "GET":
        data = request.GET
        email_id = data.get('verification_id', None)
        verification_msg = data.get('verification_msg', None)
        if not email_id or not verification_msg:
            raise Http404
        try:
            email = Email.objects.get(id=email_id, verification_code=verification_msg)
            email.user.user.is_active = True
            email.user.user.save()
            email.is_verified = True
            email.verified_on = datetime.now()
            email.save()
            return HttpResponseRedirect("/")
        except Email.DoesNotExist:
            raise Http404
    raise Http404

def user_sms_verification(request):
    if request.method == "POST":
        data = request.POST
        username = data.get('username', None)
        verification_msg = data.get('verification_code', None)
        if not username or not verification_msg:
            raise Http404
        profile = utils.get_profile_by_email_or_phone(username)
        phone = Phone.objects.get(phone = username)
        if profile:
            if phone.verification_code == verification_msg:
                profile.user.is_active = True
                profile.user.save()
                phone.is_verified = True
                phone.verified_on = datetime.now()
                phone.save()
                return HttpResponseRedirect("/")
            else:
                raise Http404
        else:
            raise Http404
        
def signin_signup(request):
    if request.method == 'POST':
        if request.POST.get('action') == 'signin':
            return signin(request)
        if request.POST.get('action') == 'signup':
            return signup(request)

    redirect_to = request.GET.get('next','/')
    type = 'signin'
    try: 
        type = request.path.split('/')[-2]
    except:
        pass 
    response = render_to_response('user/signin.html', {
            'next':redirect_to,
            'type':type
        },   
        context_instance=RequestContext(request)
        )    
    return response

def login(request):
    if request.user.is_authenticated():
        if utils.is_holii_client(request.client.client):
            return HttpResponseRedirect("/home")
        else:
            return HttpResponseRedirect("/")
    if utils.is_future_ecom(request.client.client) or utils.is_ezoneonline(request.client.client):
        return signin_signup(request)
    type = request.path.split('/')[-2]
    if type not in ['signin', 'signup']:
        type = 'signin'
    phonepedeal=False
    domain = request.META['HTTP_HOST']
    try:
        error = ''
        if request.method == 'POST':
            next = request.POST.get('next','/')
            if next.startswith('/auth/'):
                next = "/"
            username = request.POST['username']
            password = request.POST['password']
            input_type = False
            is_valid = True
            if not username and not password:
                error = 'Please enter username and password'
                is_valid = False
            elif not username:
                error = 'Please enter username'
                is_valid = False
            elif not password:
                error = 'Please enter password'
                is_valid = False
            elif username:
                if utils.is_valid_email(username):
                    input_type = "email"
                elif utils.is_valid_mobile(username):
                    input_type = "mobile"
                else:
                    input_type = "id"
            if input_type == 'id':
                error = 'Please enter a valid Email / Mobile'
                #if domain in utils.MOBILE_DOMAIN:
                return render_to_response('user/signin.html',
                    {'status':'failed',
                    'error':error,
                    'username':username,
                    'type':type,
                    },
                    context_instance=RequestContext(request))
                #return HttpResponse(simplejson.dumps(dict(status='failed',error=error,username=username)))

            if not is_valid:
# Not valid due to missing parameters...
                #if domain in utils.MOBILE_DOMAIN:
                return render_to_response('user/signin.html',
                    {'error':error,
                     'type':type,
                     'status':'failed',
                     'username':username
                     },
                    context_instance=RequestContext(request))
                #return HttpResponse(simplejson.dumps(dict(status='failed',error=error,username=username)))
            is_new, u, has_password = is_new_user(username)
            if not is_new and has_password:
# Existing User and has password...
                user = auth.authenticate(username=u.username,password=password,**dict(request=request))
                if user is not None and user.is_active:
# Valid User, so logged in...
                    set_logged_in_user(request,user)
                    #if domain in utils.MOBILE_DOMAIN:
                    return HttpResponseRedirect(next)
                    #return HttpResponse(simplejson.dumps(dict(status='ok',msg='loggedin')))
                else:
# Username and password not matching
                    error = 'The Email / Mobile and password you entered do not match.'
            else:
# New User
                cpassword = request.POST['cpassword']
                if cpassword and password:
                    if cpassword != password:
                        error = 'Passwords do not match'
                        #if domain in utils.MOBILE_DOMAIN:
                        return render_to_response('user/signin.html',
                            {'error':error,
                             'type':type,
                             'status':'failed',
                             'username':username},
                            context_instance=RequestContext(request))
                        #return HttpResponse(simplejson.dumps(dict(status='failed',error=error,username=username)))
                    else:
                        if not is_new and not has_password:
                            try:
                                u.set_password(password)
                                u.save()
                                profile = u.get_profile()
                            except Exception,e:
                                pass
                        else:
                            user,profile = utils.get_or_create_user(username,'',password)

                        user = auth.authenticate(username=username,password=password, **dict(request=request))
                        if user is not None and user.is_active:
                            set_logged_in_user(request,user)
                        request.session['user'] = profile
                        #if domain  in utils.MOBILE_DOMAIN:
                        return HttpResponseRedirect(next)

                        #return HttpResponse(simplejson.dumps(dict(status='ok',msg='loggedin')))
                else:
                    error = 'Password can not be blank'
                    #if domain in utils.MOBILE_DOMAIN:
                    return render_to_response('user/signin.html',
                        {'error':error,
                         'type':type,
                         'status':'failed',
                         'username':username
                         },
                        context_instance=RequestContext(request))
                    #return HttpResponse(simplejson.dumps(dict(status='failed',error=error,username=username)))

            #if domain in utils.MOBILE_DOMAIN:
            return render_to_response('user/signin.html',
                {'error':error,
                'type':type,
                'status':'failed'
                },
                context_instance=RequestContext(request))
            #return HttpResponse(simplejson.dumps(dict(status='failed',error=error)))
        else:
#if request method is not POST
            next = request.GET.get('next','/')
            response = render_to_response('user/signin.html',
            {'error':error,'type':type,'next':next},
             context_instance=RequestContext(request))
            return response
    except Exception,e:
        log.exception('Error logging in user %s' % repr(e))

def is_new_user(username):
    isNew = False
    u = None
    has_password = True
    if utils.is_valid_email(username):
        input_type = "email"
    elif utils.is_valid_mobile(username):
        input_type = "mobile"
    else:
        input_type = "id"
    if input_type == 'email':
        try:
            clean_email = utils.get_cleaned_email(username)
            email = UserEmail.objects.get(cleaned_email=clean_email)
            u = email.user.user
            if not email.user.user.has_usable_password():
                has_password = False
        except UserEmail.DoesNotExist:
            isNew=True
            has_password = False
    if input_type == 'mobile':
        try:
            phone = Phone.objects.get(phone=username)
            u = phone.user.user
            if not phone.user.user.has_usable_password():
                has_password = False
        except Phone.DoesNotExist:
            isNew=True
            has_password = False
    if input_type == 'id':
        isNew=True
        has_password = False

    return isNew,u,has_password

def check_user(request):
    try:
        username = request.POST['username']
        is_new, u, has_password = is_new_user(username)
        try:
            full_name = u.get_profile().full_name
        except:
            full_name = None
        json = dict(is_new_user=is_new,full_name=full_name,has_password=has_password)

        return HttpResponse(simplejson.dumps(json))
    except Exception,e:
        pass

def logout(request):
    restore_fb_v2 = False
    if utils.is_new_fb_version(request):
        restore_fb_v2 = True
    auth.logout(request)
    request.session.flush()
    if utils.is_holii_client(request.client.client) and not utils.is_cc(request):
        response = HttpResponseRedirect("/home")
    else:
        response = HttpResponseRedirect("/")
    if restore_fb_v2:
        response = utils.set_fb_v2_cookie(request, response)
        request.session['fb_v2'] = "show_new_version"
    return response

@login_required
def get_or_create_user_context(request):
    user,profile = user_context(request)
    is_dialer = False
    id = request.call['id']
    if request.call['attempt_id']:
        is_dialer = True
    response = render_to_response('cc/left_panel.html',
        {'user':user,
        'profile':profile,
        'is_dialer':is_dialer,
        'call_obj': request.call},
        context_instance=RequestContext(request))
    return response

def signout(request):
    callId = request.call['id']
    if callId in request.session:
        del request.session[callId]
    return HttpResponseRedirect('/')

def user_context(request):
    id = request.call['id']
    cli = request.call['cli']
    agent  = request.call['agent']
    dni = request.call['dni']
    type = request.call['type']
    attempt_id = request.call['attempt_id']
    response_id = request.call['response_id']
    if id in request.session:
        user = request.session[id]['user']
        profile = request.session[id]['profile']
    else:
        profile = utils.get_profile_by_email_or_phone(cli)
        if profile:
            user = profile.user
            try:
                cs = utils.get_session_obj(request)
                if not cs.has_key('atg_username'):
                    set_logged_in_user(request,user)
            except KeyError:
                set_logged_in_user(request, user)
        else:
            user = None
    return user,profile
'''
def user_context(request):
    id = request.call['id']
    cli = request.call['cli']
    agent  = request.call['agent']
    dni = request.call['dni']
    type = request.call['type']
    attempt_id = request.call['attempt_id']
    response_id = request.call['response_id']
    if id in request.session:
        user = request.session[id]['user']
        profile = request.session[id]['profile']
    else:
        user, profile = utils.get_or_create_user(cli)
    try:
        cs = utils.get_session_obj(request)
        if not cs.has_key('atg_username'):
            set_logged_in_user(request,user)
    except KeyError:
        set_logged_in_user(request, user)

    if attempt_id:
        pass
        #attempt_info = getAttemptInfo(attempt_id)
        #cs = request.session[id]
        #cs['ATTEMPT_INFO'] = attempt_info
        #request.session[id] = cs
        #request.session.modified = True
        #log.info('ATTEMPT_INFO %s' % repr(attempt_info))
    else:
        try:
            #responses = getMatchingResponses(cli, dni, id, agent, type)
            #cs = request.session[id]
            #cs['RESPONSES'] = responses
            #request.session[id] = cs
            #if len(responses) == 1:
            #    request.session[id]['SELECTED_RESPONSE_ID'] = responses[0]['id']
            pass
        except Exception,e:
            log.exception('Error fetching rms responses %s' % repr(e))
        pass



    return user,profile
'''

def update_user_profile(request):
    params = request.POST
    full_name = None
    email = None
    info = {}
    info['status'] = 'ok'
    info['email'] = ''
    info['name'] = ''
    if 'full_name' in params:
        full_name = params['full_name']
    if 'email' in params:
        email = params['email']

    if not full_name and not email:
        info['status'] = 'failed'
        return HttpResponse(simplejson.dumps(info))
    
    id = request.call['id']
    if id not in request.session:
        user_context(request)
    profile = request.session[id]['profile']
    if full_name:
        profile.full_name = full_name
        info['name'] = 'User Name Updated Successfully'
    if email:
        pro = utils.get_profile_by_email_or_phone(email)
        if not pro:
            try:
                cleaned_email = utils.get_cleaned_email(email)
                e_obj = Email(email=email, user=profile, cleaned_email=cleaned_email)
                e_obj.save()
                send_verification_email(request, email, profile.user)
                #TODO remove following two lines once the email verification process use Email table only
                pro = utils.get_profile_by_email_or_phone(email)
                profile = pro   # since send_verification_email updates the profile
                profile.primary_email = email
                info['email'] = 'Verification Email has been sent to user'
            except Exception, e:
                log.info("Update profile exception: %s" % repr(e))
                info['email'] = 'Sorry, can not attach email now'
        else:
            info['email'] = 'Email already exists'
    profile.save()
    cs = request.session[id]
    cs['user'] = profile.user
    cs['profile'] = profile
    request.session[id] = cs
    return HttpResponse(simplejson.dumps(info))


def update_dialer_attempt(request, *args, **kwargs):
    params = request.POST
    aid = params.get('aid','')
    call_id = request.call['id']
    call_status = params.get('call_status','')
    resp_status = params.get('resp_status','')
    next = params.get('next','')
    comments = params.get('comments','')
    info = dict(aid=aid, call_id=call_id, call_status=call_status, resp_status=resp_status, next=next, comments=comments)
    try:
        updateDialerAttempt(request, info)
    except APIBadReqError, e:
        return HttpResponse(simplejson.dumps(dict(status='fail',statusCode='400',statusText=e.json.get('msg','Unable to update dialer attempt'))))
    except APIError:
        return HttpResponse(simplejson.dumps(dict(status='fail',statusCode='400',statusText='unable to update dialer attempt')))
    return HttpResponse(simplejson.dumps(dict(status='success',statusCode='200',statusText='updated dialer attempt')))

def cc_verify(request):
    info = {}
    info['status'] = 'ok'
    info['error'] = ''
    if request.method == 'POST':
        try:
            phone = request.POST.get('phone')
            phone = Phone.objects.get(phone=phone)
            phone.is_verified = True
            phone.verified_on = datetime.now()
            phone.save()
            return HttpResponse(simplejson.dumps(info))
        except Exception, e:
            log.info("CC Verify exception: %s" % repr(e))
            info['error'] = 'Unable to verify this user'
            return HttpResponse(simplejson.dumps(info))
    else:
        return HttpResponse('')

def cc_signup(request):
    info = {}
    info['status'] = 'ok'
    info['user'] = 'User created successfully'
    info['email'] = ''
    if request.method == 'POST':
        try:
            username = request.POST.get('username')
            email = request.POST.get('email')
            name = request.POST.get('name')
            user, profile = utils.create_user(username)
            if not user:
                info['user'] = 'Unable to signup this user'
                info['email'] = ''
                return HttpResponse(simplejson.dumps(info))
            if email:
                info['email'] = 'Verification mail has been sent to user'
                # Attach email to user
                pro = utils.get_profile_by_email_or_phone(email)
                if pro:
                    #email already exists
                    info['email'] = 'Email already exists'
                else:
                    try:
                        cleaned_email = utils.get_cleaned_email(email)
                        e_obj = Email(email=email, user=profile, cleaned_email=cleaned_email)
                        e_obj.save()
                        send_verification_email(request, email, user)
                        profile.primary_email = email
                        profile.save()
                    except Exception, e:
                        info['email'] = 'Can not attach email'
            if name:
                profile.full_name = name
                profile.save()
            return HttpResponse(simplejson.dumps(info))
        except Exception, e:
            log.info("CC Signup exception: %s" % repr(e))
            return HttpResponse(simplejson.dumps(info))
    else:
        return HttpResponse('')

def change_user(request):
    params = request.POST
    if 'changeuser' in params:
        id = request.call['id']
        try:
            ccSession = request.session[id]
        except:
            ccSession = {}
        p = utils.get_profile_by_email_or_phone(params['changeuser'])
        if p:
            u = p.user
            ccSession['user'] = u
            ccSession['profile'] = p
        else:
            message = 'invalid_user'
            return HttpResponse(message)
        ccSession['atg_username'] = params['changeuser']
        ccSession['cart_id'] = ''
        request.session['atg_username'] = params['changeuser']
        request.session[id] = ccSession
        request.session.modified = True
        set_logged_in_user(request, u)
        redirect_url = "/%s-%s-%s-%s" % (request.call['incoming_call'],request.call['dni'],request.call['type'],request.call['id'])
        if request.call.get('response_id'):
            redirect_url += '-%s/' % (request.call['response_id'])
        else:
            redirect_url += '/'
        return HttpResponse(redirect_url)

def update_shipping_info(request, order_id, client_name=None):
    try:
        od = Order.objects.get(id = order_id)
    except Order.DoesNotExist:
        try:
            od = Order.objects.get(reference_order_id = order_id)
        except Order.DoesNotExist:
            raise Http404
    #if utils.is_ezoneonline(od.client) or utils.is_future_ecom(od.client):
    if request.method == "POST":
        from django.core.mail import EmailMessage
        user_info = utils.get_user_info(request)
        user = user_info['user']
        profile = user_info['profile']
        order_state = request.POST.get('order_state')
        order_item_ids = request.POST.get('order_item_ids', None).split(',')[:-1]
        if order_state == 'shipped' or order_state == 'delivered':
            courier = request.POST['courier']
            tracking_url = request.POST['tracking_url']
            tracking_no = request.POST['tracking_no']
            notes = request.POST['notes']
            dispatched_on = request.POST['dispatched_on']
        if order_state == 'delivered':
            received_by = request.POST['received_by']
            receivers_contact = request.POST['receivers_contact']
            delivered_on = request.POST['delivered_on']

        if not order_item_ids:
            if utils.is_ezoneonline(od.client) or utils.is_future_ecom(od.client):
                order_items = OrderItem.objects.filter(order__reference_order_id=order_id)
            else:
                order_items = OrderItem.objects.filter(order__id=order_id)
        else:
            order_items = OrderItem.objects.filter(id__in=order_item_ids)
        for order_item in order_items:
            try:
                shipping_details = ShippingDetails.objects.get(order_item=order_item)
            except ShippingDetails.DoesNotExist:
                shipping_details = ShippingDetails()
            shipping_details.courier = courier
            shipping_details.order_item = order_item
            shipping_details.tracking_url = tracking_url
            shipping_details.tracking_no = tracking_no
            shipping_details.notes = notes
            shipping_details.status = 'shipped'
            if order_state == 'delivered':
                shipping_details.status = 'delivered'
                order_item.delivered_on = datetime.strptime(delivered_on,"%d/%m/%Y")
                order_item.received_by = received_by
                order_item.receivers_contact = receivers_contact
                order_item.state = 'delivered'
            elif order_state == 'shipped':
                order_item.received_by = ''
                order_item.receivers_contact = ''
                order_item.delivered_on = None
                order_item.dispatched_on = datetime.strptime(dispatched_on,"%d/%m/%Y")
                order_item.state = 'shipped'
            shipping_details.save()
            order_item.save()
        
        dinfo = DeliveryInfo.objects.get(order=order_items[0].order)
        if utils.is_ezoneonline(od.client) or utils.is_future_ecom(od.client):
            if order_state == 'shipped':
                subject = "Your order with " + order_items[0].order.client.name + " has been shipped [Order id:" + str(order_items[0].order.reference_order_id) + "]"
            elif order_state == 'delivered':
                subject = "Your order with " + order_items[0].order.client.name + " has been delivered [Order id:" + str(order_items[0].order.reference_order_id) + "]"
        else:
            if order_state == 'shipped':
                subject = "Your order with " + order_items[0].order.client.name + " has been shipped [Order id:" + str(order_items[0].order.id) + "]"
            elif order_state == 'delivered':
                subject = "Your order with " + order_items[0].order.client.name + " has been delivered [Order id:" + str(order_items[0].order.id) + "]"

        email_body = {}
        if order_state == 'shipped':
            t_body = get_template('ppd/shipping_email.email')
            email_body['tracking_url'] = tracking_url
            email_body['dispatched_on'] = dispatched_on
        elif order_state == 'delivered':
            email_body['received_by'] = received_by
            email_body['receivers_contact'] = receivers_contact
            email_body['delivered_on'] = delivered_on
            t_body = get_template('ppd/delivered_email.email')
        email_body['order'] = od
        email_body['order_items'] = order_items
        email_body['client'] = od.client
        if utils.is_ezoneonline(od.client) or utils.is_future_ecom(od.client):
            email_body['check'] = True
        else:
            email_body['check'] = False
        email_body['courier'] = courier
        email_body['tracking_no'] = tracking_no
        email_body['dinfo'] = dinfo
        email_to = ''
        if od.user.get_primary_emails():
            emails = ''
            for email in od.user.get_primary_emails():
                emails += email.email + ','
            email_to = emails.strip(',')

        c_body = Context(email_body)
        mail_obj = EmailAddress()
        mail_obj.isHtml = True
        mail_obj.body =t_body.render(c_body)
        mail_obj.subject = subject
        mail_obj.to = email_to
        mail_obj._from = "%s<order@%s>" % (od.client.name, od.client.clientdomain_name)
        mail_obj.send()
        log.info('mail sent or not')
        return HttpResponse(simplejson.dumps(dict(status='updated')))
    else:
        try:
            if utils.is_ezoneonline(od.client) or utils.is_future_ecom(od.client):
                order_item_id = OrderItem.objects.filter(order__reference_order_id=order_id, state='shipped')[0].id
            else:
                order_item_id = OrderItem.objects.filter(order__id=order_id, state='shipped')[0].id
        except:
            if utils.is_ezoneonline(od.client) or utils.is_future_ecom(od.client):
                order_item_id = OrderItem.objects.filter(order__reference_order_id=order_id)[0].id
            else:
                order_item_id = OrderItem.objects.filter(order__id=order_id)[0].id
        order_item = OrderItem.objects.get(id=order_item_id)
        try:
            shipping_details = ShippingDetails.objects.get(order_item=order_item)
        except ShippingDetails.DoesNotExist:
            shipping_details = None
        return render_to_response('seller/shipping_info.html',
            {'shipping_details':shipping_details,
            'order_id':order_id,
            'order_item':order_item,},
            context_instance=RequestContext(request))

def forgotpwd_send_email(request,profile,emails,link):
    t_body = get_template('notifications/users/forgotpassword.email')
    email_body = {}
    email_body['profile'] = profile
    email_body['link'] = mark_safe(link)
    email_body['verify_code'] = profile.verify_code
    email_body['signature'] = request.client.client.signature
    email_body['domain'] = request.client.client.name
    c_body = Context(email_body)
    t_subject = get_template('notifications/users/forgotpassword_sub.email')
    email_from = {}
    email_subject = {'client': request.client.client.name}
    c_subject = Context(email_subject)
    mail_obj = EmailAddress()
    mail_obj._from = request.client.client.get_noreply_from_address()
    mail_obj.body = t_body.render(c_body)
    mail_obj.subject = t_subject.render(c_subject)
    u_emails = ""
    for x in emails:
        u_emails = "%s,%s" %(x.email,u_emails)
    u_emails = u_emails.strip(',')
    mail_obj.to = u_emails
    mail_obj.send()

def forgotpwd_send_sms(profile,phones,client):
    t_sms = get_template('notifications/users/forgotpassword.sms')
    sms_content = {}
    sms_content['profile'] = profile
    sms_content['client'] = client.name
    c_sms = Context(sms_content)
    sms_text = t_sms.render(c_sms)
    sms = SMS()
    sms.text = sms_text
    sms.mask = client.sms_mask
    u_phones = ""
    for x in phones:
        u_phones = "%s,%s" %(u_phones,x.phone)
    u_phones = u_phones.strip(',')
    sms.to = u_phones
    sms.send()

def user_forgot_password(request):
    profile = None
    emails = None
    phones = None
    if request.method == 'POST':
        username = request.POST['info']
        is_new, u, has_password = is_new_user(username)
        if not is_new:
            is_mobile = False
            is_email = False
            if utils.is_valid_email(username):
                email = UserEmail.objects.get(email=username)
                profile = email.user
                is_email = True
            elif utils.is_valid_mobile(username):
                phone = Phone.objects.get(phone=username)
                profile = phone.user
                is_mobile = True
            link = request.get_host()
            try:
                if not profile.verify_code:
                    verify_code = random.getrandbits(20)
                    profile.verify_code = verify_code
                profile.save()
                if is_email:
                    link = "http://%s/%s/?id=%s&code=%s" % (link,'user/resetpassword',profile.id,profile.verify_code)
                    # XXX We should send password only to the requested email
                    # XXX not to all the emails of user. There are also user's
                    # XXX whose profiles are linked to multiple emails
                    forgotpwd_send_email(request,profile,[email],link)
                elif is_mobile:
                    forgotpwd_send_sms(profile,[phone],request.client.client)
            except:
                profile = None
                link = ''
            return render_to_response('user/password_info_sent.html',
                    {
                        'profile':profile,
                        'errors':None
                    },context_instance=RequestContext(request))
        else:
            return render_to_response('user/forgot_password.html',{'warn_it':True},context_instance=RequestContext(request))
    return render_to_response('user/forgot_password.html',{'warn_it':False},context_instance=RequestContext(request))

def user_password_info_sent(request):
    if request.method == 'POST':
        profile_id = request.POST.get('profile','')
        profile_code = request.POST.get('code','')
        numeric_regex = re.compile(r'^\d+')
        if not profile_id:
            return HttpResponseRedirect("/forgotpassword/")
        profile = Profile.objects.get(id=profile_id)
        if not profile_code:
            errors = 'Please enter verification code'
            return render_to_response('user/password_info_sent.html',
                    {
                        'profile':profile,
                        'errors':errors
                    },context_instance=RequestContext(request))
        else:
            # Comparing strings as user might enter any garbage, not 
            # necessarily a number.
            if str(profile.verify_code) != str(profile_code.encode(
                'ascii','ignore')):
                errors = 'The verification code you have entered is incorrect. Please enter the one sent to your email/mobile'
                return render_to_response('user/password_info_sent.html',
                    {
                        'profile':profile,
                        'errors':errors
                    },context_instance=RequestContext(request))
            else:
                return render_to_response('user/reset_password.html',
                            {
                                'profile':profile,
                                'error':None,
                                'warn_it':False
                            },context_instance=RequestContext(request))
    return render_to_response('user/password_info_sent.html',
        {
            'profile':None,
            'errors':None,
        },context_instance=RequestContext(request))

def check_code(request):
    if request.method == 'POST':
        profile_id = request.POST['profile_id']
        verify_code = request.POST['code']
        try:
            profile = Profile.objects.get(id=profile_id)
            try:
                if profile.verify_code == long(verify_code):
                    return HttpResponse(simplejson.dumps(dict(status='ok',error='')))
                else:
                    return HttpResponse(simplejson.dumps(dict(status='failed',error='Invalid Verification Code')))
            except:
                return HttpResponse(simplejson.dumps(dict(status='failed',error='Invalid Verification Code')))
        except:
            profile = None
            return HttpResponse(simplejson.dumps(dict(status='failed',error='Invalid Username')))

def reset_password(request):
    error = ''
    if request.method == 'GET':
        profile_id = request.GET.get('id','')
        profile_code = request.GET.get('code','')
        if not profile_id or not profile_code:
            raise Http404
        profile = Profile.objects.get(id=profile_id)
        if profile.verify_code != long(profile_code):
            raise Http404
    elif request.method == 'POST':
        profile_id = request.POST['profile']
        profile = Profile.objects.get(id=profile_id)    
        password = request.POST['password']
        cpassword = request.POST['cpassword']
        if password == '' or cpassword == '':
            error = "Password or Confirm password cannot be blank."
            return render_to_response('user/reset_password.html',
                {
                    'profile':profile,
                    'error':error,
                    'warn_it':True
                },context_instance=RequestContext(request))
        elif password and len(password) < 4:
            error = 'Please enter password of minimum 4 character'
            return render_to_response('user/reset_password.html',
                    {
                        'profile':profile,
                        'error':error,
                        'warn_it':True,
                    },context_instance=RequestContext(request))
        if password == cpassword and not error:
            profile.user.set_password(password)
            profile.user.save()
            profile.verify_code = None
            profile.atg_password = None
            profile.save()
            username = profile.user.username
            user = auth.authenticate(username=username, password=password,**dict(request=request))
            if utils.is_holii_client(request.client.client):
                redirect_to = '/home'
            else:
                redirect_to = '/'
            if user is not None and user.is_active:
                request.session['atg_username'] = username
                try:
                    response = login_and_redirect(request, user, redirect_to, **dict(is_redirect=True))
                    return response
                except Exception, e:
                    log.exception('Unable to log in user  %s' % repr(e))
                    error = 'Sorry, we are unable to log you in'
                    # Logout user
                    auth.logout(request)
                    # Clear session variables
                    if 'atg_username' in request.session:
                        del request.session['atg_username']
                    if 'fbapiobj' in request.session:
                        del request.session['fbapiobj']            
            else:
                error = 'Incorrect password. Please try again'
            signin_html = 'user/signin.html'
            context = {
                'signin_error': error,
                'next':redirect_to,
                'username': username,
            }
            response = render_to_response(signin_html, context, context_instance=RequestContext(request))
            return response
        else:
            error = "Password and Confirm password didn't match."
            return render_to_response('user/reset_password.html',
                {
                    'profile':profile,
                    'error':error,
                    'warn_it':True
                },context_instance=RequestContext(request))
    return render_to_response('user/reset_password.html',
                {
                    'profile':profile,
                    'error':None,
                    'warn_it':False
                },context_instance=RequestContext(request))

@login_required
def show_wishlist(request):
    user = request.user
    if not user.is_authenticated():
        raise Http404
    try:
        user_info = utils.get_user_info(request)
        user = user_info['user']
        profile = user_info['profile']
        wishlist = List.objects.get(curator=profile,type='wishlist')
        list_items = wishlist.listitem_set.filter(sku__seller__client=request.client.client)
    except List.DoesNotExist:
        wishlist = None
        list_items = None
    my_acct_ctxt = getMyAccountContext(request)
    return render_to_response('user/wishlist.html',
        {'wishlist':wishlist,
        'list_items':list_items,
        'acc':my_acct_ctxt},
        context_instance=RequestContext(request))

@login_required
def remove_wishlist_item(request):
    itemid = request.POST.get('itemid',None)
    try:
        listitem = ListItem.objects.get(id=itemid)
        listitem.delete(using='default')
    except Exception,e:
        pass
    return show_wishlist(request)

@login_required
def make_wishlist_public(request):
    wishlist = None
    user_info = utils.get_user_info(request)
    user = user_info['user']
    profile = user_info['profile']
    try:
        wishlist = List.objects.get(curator=profile,type='wishlist')
    except List.DoesNotExist:
        pass
    if wishlist:
        if not wishlist.slug:
            import time
            wishlist.slug = int(time.time()*1000)
        if wishlist.visibility == 'private':
            wishlist.visibility = 'public'
        else:
            wishlist.visibility = 'private'
        wishlist.save()
    return HttpResponse("OK")

@login_required
def wishlist_actions(request):
    if request.method == 'POST':
        action = request.POST.get('action','')
        if action == 'remove_item':
            return remove_wishlist_item(request)
        if action == 'add_to_wishlist':
            return add_to_wishlist(request)
        if action == 'alter_visibility':
            return make_wishlist_public(request)
        return show_wishlist(request)

    if request.method == 'GET':
        return show_wishlist(request)

def wishlists(request, slug):
    if not slug:
        raise Http404
    list_items = []
    try:
        wishlist = List.objects.get(slug=slug,type='wishlist')
        if wishlist.curator.full_name:
            wishlist_username = wishlist.curator.full_name
        else:
            wishlist_username = wishlist.curator.user.username
        list_items = wishlist.listitem_set.filter(sku__seller__client=request.client.client)
    except List.DoesNotExist:
        raise Http404
    if wishlist.visibility == 'private':
        raise Http404
    return render_to_response(
        'user/wishlists.html', {'wishlist':wishlist,'list_items':list_items, 'wishlist_username':wishlist_username},
        context_instance=RequestContext(request)
    )

def feedback(request):
    return render_to_response('fb/feedback.html',dict(method=request.method),context_instance=RequestContext(request))

def feedback_popup(request):
    email=None
    name=None
    mobile = None
    if request.method == 'GET':
        form = FeedbackForm()
    if request.method == 'POST':
        form = FeedbackForm(request.POST)
        client = request.client.client
        if form.is_valid():
            feedback_form = form.save(commit=False)
            feedback_form.client=client
            feedback_form.save()
            if feedback_form.name:
                name = feedback_form.name
            if feedback_form.email:
                email = feedback_form.email
            if feedback_form.phone:
                mobile = feedback_form.phone
            feedback = feedback_form.feedback
            feedback_email(request,feedback=feedback,mobile = mobile,name = name,email=email)
            return HttpResponse(simplejson.dumps(dict(status="ok")))
        else:    #If the form is not valid
            return HttpResponse(simplejson.dumps(dict(status="error",error=form.errors)))
    return render_to_response('fb/feedback_popup.html',dict(form=form, method=request.method),context_instance=RequestContext(request))


def feedback_email(request,feedback,mobile=None,name=None,email=None,send_to=None, subject=None):
    t_body = get_template('notifications/feedback/user_feedback.email')
    email_body = {}
    email_body['user_email'] =  email
    email_body['user_feedback'] =  feedback
    email_body['user_name'] =  name
    email_body['user_mobile'] =  mobile

    mail_obj = EmailAddress()
    mail_obj._from = email
    mail_obj.body = t_body.render(Context(email_body))
    if subject:
        mail_obj.subject = subject
    else:
        mail_obj.subject = "Feedback from %s" % request.client.client.name
    mail_obj.to = send_to and send_to or request.client.client.feedback_email
    mail_obj.send()


def bulk_order(request):
    email = request.POST['email']
    name = request.POST.get('user_name',None)
    requirement = request.POST['message']
    send_to = request.POST.get('send_to',None)
    subject = request.POST.get('subject',None)
    mobile = request.POST.get('mobile',None)
    feedback_email(request,feedback=requirement, name=name, email=email, send_to=send_to, subject=subject, mobile=mobile)
    return HttpResponse('ok')
    

def add_contact(request):
    user_info = utils.get_user_info(request)
    user = user_info['user']
    profile = user_info['profile']
    contact = request.POST['contact']
    newsletter = NewsLetter.objects.get(client=request.client.client,newsletter='DailyDeals')
    is_type = None
    if utils.is_valid_mobile(contact):
        is_type = "mobile"
    if utils.is_valid_email(contact):
        is_type = "email"
    user_exist = False
    if is_type == "email":
        try:
            email = UserEmail.objects.get(email=contact)
            user_exist = 'exist'
            if email.user == profile:
                user_exist = 'same'
        except UserEmail.DoesNotExist:
            email = UserEmail(email = contact,user=profile)
            email.save()
            user_exist = 'added'
        subscription = DailySubscription.objects.filter(newsletter=newsletter,email_alert_on=email)
        if not subscription:
            subscription = DailySubscription(newsletter=newsletter,email_alert_on=email)
            subscription.save()
            u_name = email.user.full_name[0].upper() + email.user.full_name[1:]
            utils.subscribe_send_email(request,contact, u_name)

    if is_type == "mobile":
        try:
            phone = Phone.objects.get(phone=contact)
            user_exist = 'exist'
            if phone.user == profile:
                user_exist = 'same'
        except Phone.DoesNotExist:
            phone = Phone(phone = contact,user=profile)
            phone.save()
            user_exist = 'added'
        subscription = DailySubscription.objects.filter(newsletter=newsletter,sms_alert_on=phone)
        if not subscription:
            subscription = DailySubscription(newsletter=newsletter,sms_alert_on=phone)
            subscription.save()
            utils.subscribe_send_sms(contact)
    url = utils.get_cc_url(request, 'user/notification/')
    if user_exist:
        return HttpResponseRedirect('%s?user=%s' % (url, user_exist))
    return HttpResponseRedirect(url)

@login_required
def add_to_wishlist(request):
    next = request.POST['next']
    user_info = utils.get_user_info(request)
    user = user_info['user']
    profile = user_info['profile']
    try:
        wishlist = List.objects.get(curator=profile,type='wishlist')
    except List.DoesNotExist:
        wishlist = List(curator=profile,type='wishlist',title='New List', description='My Wishlist')
        wishlist.save()
    except List.MultipleObjectsReturned:
        # XXX Found multiple wishlists for a profile
        # XXX delete the old wishlists
        wishlists = List.objects.filter(curator=profile,type='wishlist').order_by('-id')
        wishlist = wishlists[0]
        wishlists = wishlists[1:]
        for list in wishlists:
            list.delete()
        
    if 'itemid' in request.POST:
        try:
            oi = OrderItem.objects.select_related('order').filter(
                id=request.POST.get('itemid',''))
            oi = oi[0]
            src = oi.seller_rate_chart
            oi.order.remove_item(request,oi)
            utils.set_cart_count(request,oi.order)
        except:
            pass
    else:
        src_id = request.POST.get('src_id')
        src = SellerRateChart.objects.get(id=src_id)
        if not utils.is_holii_client(request.client.client):
            next = "user/wishlist/"
        else:
            next = next[1:]
    list_item = wishlist.add_item(src)

    url = utils.get_cc_url(request, next)
    return HttpResponseRedirect(url)

def login_from_facebook(request, user, username, facebook_info=None,
    via_checkout=False):
    try:
        request.session['atg_username'] = username
        request.session['logged_through_facebook'] = True
        if not facebook_info:
            facebook_info = utils.get_facebook_info(request)
        request.session['facebook_user_info'] = facebook_info
        log.info("Via checkout is %s" % via_checkout)
        set_logged_in_user(request, user, via_checkout)
        return True
    except Exception, e:
        log.exception('Unable to log in user  %s' % repr(e))
        error = 'Sorry, we are unable to log you in'
        # Logout user
        auth.logout(request)
        # Clear session variables
        if 'atg_username' in request.session:
            del request.session['atg_username']
        if 'fbapiobj' in request.session:
            del request.session['fbapiobj']            
        return False
    return False

def link(request):
    facebook_email = request.POST['fbemail']
    facebook_id = request.POST['fbid']
    email_or_phone = request.POST.get('username','')
    password = request.POST.get('password','')
    confirm_password = request.POST.get('confirm_password','')
    verify_code = request.POST.get('verify_code','')
    cont = request.POST.get('cont','')
    deny = request.POST.get('deny','')
    via_checkout = request.POST.get('via_checkout', 'False')

    if deny:
        facebook_info = FacebookInfo.objects.get(email__email=facebook_email)
        facebook_info.linking_denied = True
        facebook_info.save()

        return HttpResponse("", status=204)

    if cont:
        facebook_info = FacebookInfo.objects.get(email__email=facebook_email)
        facebook_info.linking_done = True
        # In continue with facebook account, the account is linked to
        # the email given by facebook
        facebook_info.linked_to = facebook_email
        facebook_info.save()

        user = auth.authenticate(request=request)
        log.info("Via checkout is %s" % via_checkout)
        login_successful = login_from_facebook(request,
            user,
            facebook_info.linked_to,
            facebook_info,
            via_checkout)
        if login_successful:
            return HttpResponse()
        else:
            return HttpResponse(
                "Sorry, we are unable to log you in. Please retry",
                status = 400)

    fbemail = UserEmail.objects.get(email=facebook_email)
    email = None
    phone = None

    # Do the validations
    # 1. email_or_phone is reuired
    # 2. password is required
    # 3. email_or_phone should be registered with us
    # 4. password and confirm password should match if verify_code is given
    # 5. profile.verify_code should match with verify_code if given
    # 6. authentication should be succesful
    
    if not email_or_phone:
        return HttpResponse("Email/mobile is required",
            status=400)
    if not password:
        return HttpResponse("Password is required",
            status=400)

    try:
        email = UserEmail.objects.get(email=email_or_phone)
    except UserEmail.DoesNotExist:
        try:
            phone = Phone.objects.get(phone=email_or_phone)
        except Phone.DoesNotExist:
            pass
            
    profile = None
    if email:
        profile = email.user
    if phone:
        profile = phone.user

    if not profile:
        return HttpResponse("%s is not a registered Email/Mobile" % email_or_phone,
            status=400)

    if verify_code:
        if password != confirm_password:
            return HttpResponse("Passwords do not match",
                status=400)
        if str(profile.verify_code) != str(verify_code):
            return HttpResponse("Verification code does not match",
                status=400)
        profile.user.set_password(password)
        profile.user.save()
        
    user = auth.authenticate(username=email_or_phone, password=password)
    if not user:
        return HttpResponse("Email/mobile and password do not match",
            status=401)

    if profile.user.id == user.id:
        # The user authentication is successful
        # We should now link the facebook email with this profile
        fbprofile = fbemail.user
        fbuser = fbemail.user.user
        if fbprofile.id != profile.id:
            # If the facebook email is linked to a different profile
            # Then we need to link it with the authenticated profile
            # and mark the other profile for deletion
            fbemail.user = profile
            fbemail.save()
            fbprofile.buyer_or_seller = 'Delete'
            # Commenting out turning is_active to False as this is 
            # making some users not able to login. Keeping the marker
            # of Delete is perhaps sufficient to know the merge
            # fbuser.is_active = False
            fbuser.save()
            fbprofile.save()
            merge = UserMerges(user=fbprofile, merged_to=profile, email=fbemail)
            merge.save()
        # Mark the facebook info object as linking done
        facebook_info = FacebookInfo.objects.get(email=fbemail)
        facebook_info.linking_done = True
        # the linked to is the username provided during linking
        facebook_info.linked_to = email_or_phone
        facebook_info.save()
        # The facebook login is now complete, lets log the user in and
        # initialize api
        login_successful = login_from_facebook(request,
            user,
            facebook_info.linked_to,
            facebook_info,
            via_checkout)
        if login_successful:
            return HttpResponse()
        else:
            return HttpResponse(
                "Sorry, we are unable to log you in. Please retry",
                status = 400)
    else:
        # Should not be a real case, adding for completeness.
        # Authenticated user is not same as the profile attached
        # to email_or_phone
        return HttpResponse("Email/mobile and password do not match",
            status=401)


def link_dialog(request):
    facebook_email = request.GET['fe']
    name = request.GET.get('un', '')
    facebook_id = request.GET['id']
    retry_denied = request.GET.get('retry', False)
    via_checkout = request.GET.get('via_checkout', False)
    password_required = False
    email_taken = False
    linking_required = False
    facebook_info = None
    
    try:
        email = UserEmail.objects.get(email=facebook_email)
        email_taken = True
        try:
            # First time facebook connect users will not have an entry in this
            # table. Lets check if thats the case
            facebook_info = FacebookInfo.objects.get(email=email,
                facebook_id = facebook_id) 
        except FacebookInfo.DoesNotExist:
            # First time facebook connect user
            pass

        if facebook_info:
            if facebook_info.is_new_email:
                # This email is created as a part of facebook connect
                # We should treat this a  email not taken
                email_taken = False
            if retry_denied:
                # User want's to retry facebook connect, we will reset
                # the denied status to False and let the code below 
                # decide what should be done
                facebook_info.linking_denied = False
                facebook_info.save()
                linking_required = True
            # If facebook info is present and linking has been denied
            # then we should show link popup to the user
            # and set linking required
            if facebook_info.linking_denied:
                linking_required = True
        # We will require password for all facebook connect users if
        # their email is taken and the profile attached to the email
        # also has other emails attached to it
        password_required = (email.user.email_set.all().count() > 1)

        # By now, we have established if the email is taken, password is needed
        # and if the user is a first time user

        if not facebook_info and not password_required:
            # First time facebook connect for a clean user. Clean user is
            # someone who has only one email address and it matches with
            # the email given by facebook. This is first time connect as
            # we do not have an entry in the FacebookInfo table. We still
            # want to give the user an option to link his facebook profile
            # with a different account
            facebook_info = FacebookInfo(email = email,
                facebook_id = facebook_id,
                linking_done = False)
            facebook_info.save()
            linking_required = True
        elif not facebook_info and password_required:
            facebook_info = FacebookInfo(email = email,
                facebook_id = facebook_id,
                linking_done = False)
            facebook_info.save()
            # First time facebook connect user, with multiple emails
            # linked to the email's profile needs password
            linking_required = True
        elif facebook_info and not password_required:
            # Second request from facebook connect but clean user.
            # The user might have chosen to link or not to link in
            # which case the linking done flag is set to True
            # If the user did not choose, then linking done is False
            # Check linking done flag to decide what to do
            linking_required = not facebook_info.linking_done
        elif facebook_info and password_required:
            # This case comes when we are only half done in the linking
            # process. Facebook connect -> New email -> Cretated user
            # and profile -> Created an entry in facebook info but user
            # abandoned linking without choosing any option. Now in the
            # second attempt, it looks like email exists and an entry
            # exists in facebook info but the linking_done flag will
            # be false for those users
            linking_required = not facebook_info.linking_done
    except UserEmail.DoesNotExist:
        # First time facebook connect user. Email is not taken
        # We save the email, a new user and profile and an entry into
        # facebook info with linking_done as False.
        email = None
        # Save the email to our db and create a user and profile for it
        user, profile = utils.get_or_create_user(facebook_email,'','')
        # Save the name of the user
        profile.full_name = name
        profile.save()
        email = UserEmail.objects.get(email=facebook_email)
        # Add the facebook info for this newly added email
        facebook_info = FacebookInfo(email = email, facebook_id = facebook_id)
        facebook_info.is_new_email = True
        facebook_info.save()
        linking_required = True

    if not linking_required:
        login_through_facebook = True
        if request.user.is_authenticated():
            login_through_facebook = False
            if retry_denied and retry_denied != "login_clicked":
                # User has requested Facebook Login
                # So logout already logged in Non Facebook user
                # Then FacebookAuto Middleware can login Facebook user
                sign_out_response = logout(request)
                log.info("Logging out the Non Facebook User Then login Facebook User")
                login_through_facebook = True
        # Authenticate the user for facebook login
        if login_through_facebook:
            try:
                # Not logged through facebook. Let us check if he should be
                user = auth.authenticate(request=request)
                if user:
                    username = user.atg_username
                    # Complete the login
                    login_from_facebook(request, user, username, 
                        facebook_info, via_checkout)
            except Exception, e:
                log.exception('Error auto login of facebook user %s' % repr(e))
        response = HttpResponse(status=205)
        return response
    ctxt = {
        "facebook_email": facebook_email,
        "facebook_id": facebook_id,
        "name": name,
        "password_required": password_required,
        "email_taken": email_taken,
        "via_checkout": via_checkout,
        }
    return render_to_response("user/link.html", ctxt,
        context_instance = RequestContext(request))

def forgot_password_single(request):
    username = request.POST.get('username', '')
    if not username:
        return HttpResponse("Please provide email/mobile",
            status=400)
    email = None
    phone = None
    profile = None
    try:
        email = UserEmail.objects.select_related('user').get(
            email=username)
        profile = email.user
    except UserEmail.DoesNotExist:
        try:
            phone = Phone.objects.select_related('user').get(
                phone=username)
            profile = phone.user
        except Phone.DoesNotExist:
            pass
    if not profile:
        return HttpResponse("%s is not registered", status=400)

    verify_code = random.getrandbits(20)
    profile.verify_code = verify_code
    profile.save()

    if email:
        forgotpwd_send_email(request, profile, [email], '')
    if phone:
        forgotpwd_send_sms(profile, [phone], request.client.client)

    return HttpResponse("We have sent an account verification code to %s." % username)  

def facebook_authenticate(request):
    try:
        # Not logged through facebook. Let us check if he should be
        user = auth.authenticate(request=request)
        if user:
            username = user.atg_username
            # Complete the login
            from web.views import user_views 
            facebook_info = utils.get_facebook_info(request)
            user_views.login_from_facebook(request, user, username, facebook_info)
    except Exception, e:
        log.exception('Error auto login of facebook user %s' % repr(e))
    return HttpResponseRedirect(request.GET.get('next',
        request.META.get('HTTP_REFERRER','')))

def newsletter(request):
    try:
        username = request.user.name
    except:
        email = None
    contact=None
    end = None
    action = request.GET.get('action','sub')
    user_info = utils.get_user_info(request)
    if user_info:
        profile = user_info['profile']
        try:
            email = Email.objects.filter(user=profile)[0]
            contact = email
        except:
            email, contact = None, None
    try:
        newsletter = NewsLetter.objects.filter(client=request.client.client)[0]
    except:
        newsletter = NewsLetter()
        newsletter.save()
        newsletter.client.add(request.client.client)
        newsletter.newsletter = "newsletter"
        newsletter.save()
    if request.method == 'POST':
        contact = request.POST['email']
        end = 'posted'

    if action == 'unsub':
        subscription = Subscription.objects.get(contact=contact, client=request.client.client)
        subscription.delete(using='default')
    
    if action == 'sub' and contact:
        subscription = Subscription(name='newsletter', source=request.client.type,newsletter=newsletter, contact_type='email', client = request.client.client)
        subscription.contact = contact 
        subscription.save()
    return HttpResponseRedirect(request.GET.get('next','/home'))

def refer_friend(request):
    return render_to_response(
        'user/refer_friend.html', {},
        context_instance=RequestContext(request)
    )
