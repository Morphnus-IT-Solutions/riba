from django.contrib import auth
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404 
from django.core.mail import send_mail
from django.core import serializers
from notifications.notification import Notification
from notifications.sms import SMS
from web.forms import FBRegisterForm
from users.models import Profile,Phone
from users.models import Email as UserEmail
from accounts.models import *
from django.contrib.auth.models import User
from django.utils import simplejson
from utils import utils
from utils.utils import *
from promotions.models import *
from affiliates.models import *
from web.views.user_views import set_logged_in_user
from django.db.models import Q
from notifications.email import Email
from django.template import Context, Template
from django.template.loader import get_template
from notifications.notification import Notification
from notifications.email import Email as EmailAddress
from notifications.sms import SMS
from django.template.loader import render_to_string
from lists.models import *

def get_user_by_email_or_mobile(email, mobile):
    email_user = None
    phone_user = None
    email_alert_on = None
    sms_alert_on = None

    try:
        e = UserEmail.objects.get(email=email)
        email_user = e.user
        email_alert_on = e
    except UserEmail.DoesNotExist:
        pass

    try:
        p  = Phone.objects.get(phone=mobile)
        phone_user = p.user
        sms_alert_on = p
    except Phone.DoesNotExist:
        pass

    return email_user, phone_user, email_alert_on, sms_alert_on

def register_for_deals(request):
    form = FBRegisterForm()
    if request.method == 'POST':
        form = FBRegisterForm(request.POST)
        error=''
        if form.is_valid():
            f=form.cleaned_data
            email_id = f['email']
            mobile_no = f['mobile']

            user_info = get_user_by_email_or_mobile(email_id, mobile_no)
            email_user, phone_user, email_alert_on, sms_alert_on = user_info

            if not email_user and not phone_user:
                #new user
                user = User.objects.create_user(email_id,email_id,None)
                user.first_name = f['name']
                user.save()

                profile = Profile(user=user,full_name=user.first_name)
                profile.save()

                email = UserEmail(user=profile,type='primary',email=email_id)
                email.save()
                email_alert_on = email
                phone = Phone(user=profile,type='primary',phone=mobile_no)
                phone.save()
                sms_alert_on = phone

            if not email_user and phone_user:
                # user with phone number already exist, update his email address only
                email = UserEmail(user=phone_user,type='primary',email=email_id)
                email.save()
                email_alert_on = email

            if not phone_user and email_user:
                # user with email already exist, update his phone number only
                phone = Phone(user=email_user,type='primary',phone=mobile_no)
                phone.save()
                sms_alert_on = phone
            if f['name']:
                u_name = f['name'][0].upper() + f['name'][1:]
            else:
                u_name = None
            utils.subscribe_send_email(request,email_id, u_name)
            utils.subscribe_send_sms(mobile_no)
            try:
                newsletter = NewsLetter.objects.get(newsletter='DailyDeals',client=request.client.client)
                existing_subscription = DailySubscription.objects.filter(newsletter=newsletter,sms_alert_on=sms_alert_on,email_alert_on=email_alert_on)
                if existing_subscription:
                    return HttpResponse(simplejson.dumps(dict(status='ok',msg='subscribed')))
                else:
                    subscribe = DailySubscription()
                    subscribe.newsletter = newsletter
                    subscribe.sms_alert_on = sms_alert_on
                    subscribe.email_alert_on = email_alert_on
                    subscribe.save()
                    return HttpResponse(simplejson.dumps(dict(status='ok',msg='subscribed')))
            except NewsLetter.DoesNotExist:
                return HttpResponse(simplejson.dumps(dict(status='ok',msg='newsletter does not exists')))

        else:
            errors = []
            # we are restricting to on error per field.
            for e in form['email'].errors[:1]:
                errors.append(e)
            for e in form['mobile'].errors[:1]:
                errors.append(e)
            return HttpResponse(simplejson.dumps(dict(status='failed',error=errors)))


    return render_to_response('fb/popup.html',
            {'form':form},
            context_instance = RequestContext(request))

def daily_deals_registration(request):
    form = FBRegisterForm()
    valid=False
    if request.method == 'POST':
        form = FBRegisterForm(request.POST)
        error=''
        if form.is_valid():
            valid = True
            f=form.cleaned_data
            email_id = f['email']
            mobile_no = f['mobile']

            user_info = get_user_by_email_or_mobile(email_id, mobile_no)
            email_user, phone_user, email_alert_on, sms_alert_on = user_info

            if not email_user and not phone_user:
                #new user
                user = User.objects.create_user(email_id,email_id,None)
                user.first_name = f['name']
                user.save()

                profile = Profile(user=user,full_name=user.first_name)
                profile.save()

                email = UserEmail(user=profile,type='primary',email=email_id)
                email.save()
                email_alert_on = email
                phone = Phone(user=profile,type='primary',phone=mobile_no)
                phone.save()
                sms_alert_on = phone

            if not email_user and phone_user:
                # user with phone number already exist, update his email address only
                email = UserEmail(user=phone_user,type='primary',email=email_id)
                email.save()
                email_alert_on = email

            if not phone_user and email_user:
                # user with email already exist, update his phone number only
                phone = Phone(user=email_user,type='primary',phone=mobile_no)
                phone.save()
                sms_alert_on = phone
            if f['name']:
                u_name = f['name'][0].upper() + f['name'][1:]
            else:
                u_name = None
            utils.subscribe_send_email(request,email_id, u_name)
            utils.subscribe_send_sms(mobile_no)
            try:
                newsletter = NewsLetter.objects.get(newsletter='DailyDeals',client=request.client.client)
                existing_subscription = DailySubscription.objects.filter(newsletter=newsletter,sms_alert_on=sms_alert_on,email_alert_on=email_alert_on)
                if existing_subscription:
                    return render_to_response('fb/subscription_thankyou.html',
                            {'form':form,'valid':valid},
                            context_instance = RequestContext(request))
                else:
                    subscribe = DailySubscription()
                    subscribe.newsletter = newsletter
                    subscribe.sms_alert_on = sms_alert_on
                    subscribe.email_alert_on = email_alert_on
                    subscribe.save()
                    return render_to_response('fb/subscription_thankyou.html',
                            {'form':form,'valid':valid},
                            context_instance = RequestContext(request))
            except NewsLetter.DoesNotExist:
                return render_to_response('fb/subscription_thankyou.html',
                        {'form':form,'valid':valid},
                        context_instance = RequestContext(request))

        else:
            valid=False
            return render_to_response('fb/dailydeals_popup.html',
                    {'form':form,'valid':valid},
                    context_instance = RequestContext(request))

    return render_to_response('fb/dailydeals_popup.html',
            {'form':form,'valid':valid},
            context_instance = RequestContext(request))

def subscribe_via_facebook(request):
    if request.method=="POST":
        data = request.POST
        facebookid = data['id']
        email = data['email']
        first_name = data['first_name']
        last_name = data['last_name']
        user,profile =  get_or_create_user(username=email,email_id='',password=None, first_name=first_name, last_name=last_name)
        email = UserEmail.objects.get(email=email)
        try:
            newsletter = NewsLetter.objects.get(newsletter='DailyDeals',client=request.client.client)
            existing_subscription = DailySubscription.objects.filter(newsletter=newsletter,email_alert_on=email,source='facebook')
            if existing_subscription:
                return HttpResponse("OK") 
            else:
                subscribe = DailySubscription()
                subscribe.newsletter = newsletter
                subscribe.email_alert_on = email
                subscribe.source = 'facebook'
                subscribe.save()
                return HttpResponse("OK") 
        except NewsLetter.DoesNotExist:
            return HttpResponse("OK") 
    return render_to_response('fb/subscription_thankyou.html',None,context_instance = RequestContext(request))
            
def attach_fb(request):
    if request.method=="POST":
        data = request.POST
        facebookid = data['id']
        email = data['email']
        first_name = data['first_name']
        last_name = data['last_name']
        
        user, profile = None, None
        u_email = None
        try:
            u_email = UserEmail.objects.get(email=email)
            profile = u_email.user
            user = profile.user
        except UserEmail.DoesNotExist:
            try:
                user = User.objects.get(Q(email=email) | Q(username=email))
            except User.DoesNotExist:
                user = User.objects.create_user(email,email,None)
                user.first_name = first_name
                user.last_name = last_name
                user.save()
        if not user.first_name:
            user.first_name = first_name
            user.save()
        if not user.last_name:
            user.last_name = last_name
            user.save()

        try:
            profile = Profile.objects.get(user=user)
        except Profile.DoesNotExist:
            profile = Profile(user=user, full_name='%s %s' % (first_name, last_name))
        #if not profile.full_name: overwrite facebook name
        profile.full_name='%s %s' % (first_name, last_name)
        profile.facebook=facebookid
        profile.save()
        if not u_email:
            u_email = UserEmail(email=email,user=profile,type='subscription')
            u_email.save()
        if request.user:
            auth.logout(request)
            request.session.flush()
            user = auth.authenticate(facebook_user=user)
            set_logged_in_user(request, user)
        return HttpResponse("OK") 
    else:
        return HttpResponse("OK") 

def subscribe_email_link(request,alliance):
    form = FBRegisterForm()
    affiliate_name = alliance
    try:
        affiliate_subscription = SubscriptionLink.objects.get(path='/'+affiliate_name)
    except SubscriptionLink.DoesNotExist:
        raise Http404
    affiliate_logo = affiliate_subscription.affiliate.logo
    affiliate_text = affiliate_subscription.affiliate.text
    newsletter = affiliate_subscription.newsletter

    if request.method == 'POST':
        form = FBRegisterForm(request.POST)
        error=''
        already_subscribed = False
        if form.is_valid():
            f=form.cleaned_data
            email_id = f['email']
            mobile_no = f['mobile']
            name = f['name']
            email_user,phone_user,email_alert_on,sms_alert_on = get_user_by_email_or_mobile(email_id,mobile_no)#User.objects.get(username = mobile_no)
            if not email_user and not phone_user: #new user
                user = User.objects.create_user(email_id,email_id,None)
                user.first_name = f['name']
                user.save()

                profile = Profile(user=user,full_name=user.first_name)
                profile.save()

                email = UserEmail(user=profile,type='primary',email=email_id)
                email.save()
                email_alert_on = email
                phone = Phone(user=profile,type='primary',phone=mobile_no)
                phone.save()
                sms_alert_on = phone
            if not email_user and phone_user: #user with phone number already exist, update his email address only
                email = UserEmail(user=phone_user,type='primary',email=email_id)
                email.save()
                email_alert_on = email
            if not phone_user and email_user: #user with email already exist, update his phone number only
                phone = Phone(user=email_user,type='primary',phone=mobile_no)
                phone.save()
                sms_alert_on = phone
            if email_user and phone_user and email_user != phone_user: #phone user and email user are different
                pass

            existing_subscription = DailySubscription.objects.filter(newsletter=newsletter,sms_alert_on=sms_alert_on,email_alert_on=email_alert_on,source ='/'+affiliate_name)
            if not existing_subscription:
                subscribe = DailySubscription()
                subscribe.newsletter = newsletter
                subscribe.sms_alert_on = sms_alert_on
                subscribe.email_alert_on = email_alert_on
                subscribe.source = '/'+ affiliate_name
                subscribe.save()
            else:
                already_subscribed = True
                return render_to_response('fb/subscribed.html',
                    {'affiliate_name':affiliate_name,'already_subscribed':already_subscribed},
                    context_instance = RequestContext(request))
            
            total_coupon_codes,text = assign_coupons(affiliate_subscription.affiliate,email_alert_on,sms_alert_on )
            if alliance == 'icici':
                return render_icici_products(request,total_coupon_codes)
            if email_alert_on:
                send_coupons_by_email(total_coupon_codes,affiliate_subscription.affiliate,email_alert_on)

            if sms_alert_on:
                sms_text = text 
                sms = SMS()
                sms.text = sms_text
                sms.to = sms_alert_on.phone
                sms.send()
                
            return render_to_response('fb/discount.html',
                {'affiliate':affiliate_subscription.affiliate,'coupon_codes':total_coupon_codes, 'already_subscribed':already_subscribed},
                context_instance = RequestContext(request))
        else:
            return render_to_response('fb/register_for_deals.html',
                {'form':form,'affiliate_logo':affiliate_logo,'affiliate_text':affiliate_text},
                context_instance = RequestContext(request))


    else:
        return render_to_response('fb/register_for_deals.html',
            {'form':form,'affiliate_logo':affiliate_logo,'affiliate_text':affiliate_text},
            context_instance = RequestContext(request))

def assign_coupons(affiliate,email_alert_on,sms_alert_on ):
    text = 'your' 
    offer_available_at = ['bigbazaar','futurebazaar','pantaloon']
    total_coupon_codes = {}
    total_coupon_codes['bigbazaar'],total_coupon_codes['futurebazaar'],total_coupon_codes['pantaloon']=[],[],[]

    for offer in offer_available_at:
        coupon_types = CouponType.objects.filter(affiliate = affiliate,discount_available_on = offer)
        if coupon_types:
            text = text + ' '+offer+' coupon code/s:'
        for coupon_type in coupon_types:
            voucher = Voucher.objects.filter(type = coupon_type,status='active').order_by('uses')
            if voucher:
                total_coupon_codes[coupon_type.discount_available_on].append(voucher[0])
                text = text + ' ' + voucher[0].code
                coupon = voucher[0]
                coupon.uses += 1
                coupon.save()
                if email_alert_on:
                    voucher_email_map = VoucherEmailMapping()
                    voucher_email_map.voucher = coupon
                    voucher_email_map.email = email_alert_on
                    voucher_email_map.save()
                if sms_alert_on:
                    voucher_phone_map = VoucherPhoneMapping()
                    voucher_phone_map.voucher = coupon
                    voucher_phone_map.phone = sms_alert_on
                    voucher_phone_map.save()
    return total_coupon_codes,text


def send_coupons_by_email(coupons,affiliate,email_alert_on):
    mail_obj = Email()
    mail_obj.isHtml = True
    mail_obj._from = "noreply@futurebazaar.com"
    mail_obj.body = render_to_string('notifications/subscriptions/alliance_subscription.html',{'affiliate':affiliate,'coupon_codes':coupons})
    mail_obj.subject = "Avail your futurebazaar.com coupon codes."
    mail_obj.to = email_alert_on.email
    mail_obj.send()

def render_icici_products(request,total_coupon_codes):
    lists_obj = List.objects.filter(curator__user__username='icici')
    icici_products = ListItem.objects.filter(list = lists_obj)
    print icici_products
    return render_to_response('fb/icici_products.html',
        {'products':icici_products,'coupon_code':total_coupon_codes},
        context_instance = RequestContext(request))
