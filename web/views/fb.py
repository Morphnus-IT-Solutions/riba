from django.contrib import auth
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect, Http404 
from django.core.mail import send_mail
from django.core import serializers
from notifications.notification import Notification
from web.forms import FBRegisterForm, DealRegisterForm
from users.models import Profile, Phone, Subscription
from users.models import Email as UserEmail
from accounts.models import *
from django.contrib.auth.models import User
from django.utils import simplejson
from utils import utils
from utils.utils import *
from restapi.APIManager import *
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
from django.views.decorators.cache import never_cache
import random

log = logging.getLogger('request')

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

def subscribe_user(request, name, email_id, mobile_no, source=None):
    info = {}
    info['error'] = ''
    info['image_url'] = ''
    domain = request.client
    # Check if email_id is subscribed for the Deal on a requestes Domain
    # Invalidate the user if already subscribed
    emails = Subscription.objects.filter(contact_type='email', contact=email_id, source=source)
    if emails:
        email = emails[0]
        if not email.verified_on:
            send_subscription_email(request, email)
            info['email_status'] = 'ok'
        else:
            info['email_status'] = 'fail'
    else:
        # subscribe user email
        email = Subscription(contact_type='email', source=source)
        email.contact = email_id
        newsletter = NewsLetter.objects.get(newsletter='DailyDeals',client=request.client.client)
        email.newsletter = newsletter
        if name:
            email.name = name
        email.save()
        send_subscription_email(request, email)
        info['email_status'] = 'ok'
    if mobile_no:
        phones = Subscription.objects.filter(contact_type='phone', contact=mobile_no, source=source)
        if phones:
            phone = phones[0]
            if phone.verified_on:
                info['phone_status'] = 'fail'
                return info
        else:
            phone = Subscription(contact_type='phone', source=source)
            newsletter = NewsLetter.objects.get(newsletter='DailyDeals',client=request.client.client)
            phone.newsletter = newsletter
            phone.contact = mobile_no
            if name:
                phone.name = name
            phone.save()
            # Send deal subscription confirmation sms
    #        utils.subscribe_send_sms(mobile_no)
            
        # call zip dial for phone verification
        jsonDict = {}
        jsonDict['userEnteredMobileNumber'] = mobile_no
        jsonDict['zipDialCallerID'] = 'subscription'
        jsonStr = simplejson.dumps(jsonDict)
        #jsonStr = "{\"userEnteredMobileNumber\":\"" + str(mobile_no) + "\"}"
        try:
            s1 = subscribeUser(jsonStr)
            s = simplejson.loads(s1)
            if(s['status'] == '1'):
                info['image_url'] = s['img']
                info['verification_code'] = s['transaction_token']
                
                # update verification_code in the subscription table
                phone.verification_code = s['transaction_token']
                phone.save()
                info['phone_status'] = 'ok'
            else:
                log.info("==== ZIP DIAL has returned empty string or failed status")
                info['phone_status'] = 'error'
             #   info['error'] = 'Sorry we can not verify your phone number now. Please try again later'
        except Exception as e:
            log.info("==== ZIP DIAL has returned exception: %s" % e)
            info['phone_status'] = 'error'
            #info['error'] = 'Sorry we can not verify your phone number now. Please try again later'
            
    return info

def send_subscription_email(request, subscribe_email):
    subscribe_email.verification_code = get_random_alphabets(length=40)
    subscribe_email.save()
    # Send verification email to user
    utils.subscribe_send_email(request, subscribe_email.contact, subscribe_email.name, subscribe_email)

def render_subscription(request, render_to_html, source=None):
    errors = []
    if request.method == 'POST':
        form = FBRegisterForm(request.POST)
        if form.is_valid():            
            name = form.cleaned_data['name'].strip()
            email_id  = form.cleaned_data['email'].strip()
            mobile_no = form.cleaned_data['mobile'].strip()
            info = subscribe_user(request, name, email_id, mobile_no, source)
            if info['is_valid']:
                log.info("Email:%s and Mobile:%s subscribed for %s" % (email_id, mobile_no, source))
                return HttpResponseRedirect('/') 
            errors = info['errors']
    else:
        form = FBRegisterForm() 
    return render_to_response(render_to_html,
        {
            'form':form,
            'errors':errors,
        },context_instance=RequestContext(request))

def offer_futurebazaar(request, offer_no=None):
    errors = []
    if request.method == 'POST':
        form = FBRegisterForm(request.POST)
        if form.is_valid():            
            name = form.cleaned_data['name'].strip()
            email_id  = form.cleaned_data['email'].strip()
            mobile_no = form.cleaned_data['mobile'].strip()
            source = 'offer-%s' % offer_no
            info = subscribe_user(request, name, email_id, mobile_no, source)
            if info['is_valid']:
                log.info("Email:%s and Mobile:%s subscribed for offer.futurebazaar.com" % (email_id, mobile_no))
                return render_to_response('web/thank_you.html',None,context_instance=RequestContext(request))
            errors = info['errors']
    else:
        form = FBRegisterForm() 
    return render_to_response('web/welcome.html',
        {
            'form':form,
            'errors':errors,
        },context_instance=RequestContext(request))

def subscribe_for_deals(request, source=None):
    affiliate = Affiliate.objects.filter(name=source)
    if not affiliate:
        return HttpResponseRedirect('/') 
    render_to_html = 'fb/deal_subscription.html'
    return render_subscription(request, render_to_html, source)

def subscribe_for_specialdeals(request):
    render_to_html = 'fb/special_offer.html'
    source = 'jay-hind'
    return render_subscription(request, render_to_html, source)

def subscribe_for_fridaydeals(request):
    render_to_html = 'fb/special_friday_offer.html'
    source = 'freaking-friday'
    return render_subscription(request, render_to_html, source)

def get_video_items(request):
    page = request.GET.get('page',1)
    page = int(page)
    data = [
        {'link':'http://www.youtube.com/watch?v=MFFCTPPzxQA', 'title':'James Bond / Koi Mil Gaya / SRK Mash up!', 'image_url':'/media/images/you-tube5.jpg'},
        {'link':'http://www.youtube.com/watch?v=C9dZpKfXXwo', 'title':'FutureBazaar.Com Ad In Tamil', 'image_url':'/media/images/you-tube6.jpg'},
        {'link':'http://www.youtube.com/watch?v=cVwuQrGvIUE', 'title':'Swasta Aani Masta!', 'image_url':'/media/images/you-tube7.jpg'},
        {'link':"http://www.youtube.com/watch?v=fUZOPw01ixw", 'title':"It's All About Deals!", 'image_url':'/media/images/you-tube8.jpg'},
        {'link':"http://www.youtube.com/watch?v=EEoDV_j8VkM", 'title':"Bachelors Ki Set Ho Gayi!", 'image_url':'/media/images/you-tube9.jpg'},
        {'link':"http://www.youtube.com/watch?v=l-vZR4zGVVE", 'title':"Video Kya Dekh Raho Ho!", 'image_url':'/media/images/you-tube10.jpg'},
        {'link':"http://www.youtube.com/watch?v=f0xTkxUSLIs", 'title':"Aiyya Kiti Bhari Deals!", 'image_url':'/media/images/you-tube11.jpg'},
        {'link':"http://www.youtube.com/watch?v=IHY9cRQFDbQ", 'title':"Itkya Kami Kimmatit Phone!", 'image_url':'/media/images/you-tube12.jpg'},
        {'link':"http://www.youtube.com/watch?v=NKUT_3Q9ICQ", 'title':"Mujhe Camera Chahiye!", 'image_url':'/media/images/you-tube13.jpg'},
        {'link':"http://www.youtube.com/watch?v=Lb4Nrippa2Y", 'title':"Pareshaan Ho Gaya Hoon!", 'image_url':'/media/images/you-tube14.jpg'},
        {'link':"http://www.youtube.com/watch?v=l8ltVG-uMQs", 'title':"Yaar! Yaar! Yaar!", 'image_url':'/media/images/you-tube15.jpg'},
        {'link':"http://www.youtube.com/watch?v=5zuY2bSi72I", 'title':"So Many *Beeps*!", 'image_url':'/media/images/you-tube16.jpg'}
    ]
    total = len(data)
    start = (page - 1) * 4
    end = start + 4
    current_data = data[start:end]
    enable_next = True
    if end >= total:
        enable_next = False
    return render_to_response('fb/get_videos_special_offer.html',
            {                
                'enable_next':enable_next,
                'data':current_data,
            },
            context_instance = RequestContext(request))

def third_party_register_for_deals(request, source):
    form = DealRegisterForm()
    errors = []
    if request.method == 'POST':
        form = DealRegisterForm(request.POST)
        if form.is_valid():
            name = form.cleaned_data['name'].strip()
            email_id  = form.cleaned_data['email'].strip()
            mobile_no = form.cleaned_data['mobile'].strip()
            info = subscribe_user(request, name, email_id, mobile_no, source)
            log.info("Email:%s and Mobile:%s subscribed via %s" % (email_id, mobile_no, source))
            utils.set_user_subscribed_for_deals(request)
            return render_to_response('fb/%s-register-success.html' % source)
        else:
            # we are restricting to on error per field.
            for e in form['email'].errors[:1]:
                errors.append(e)
            for e in form['mobile'].errors[:1]:
                errors.append(e)

    return render_to_response('fb/%s-register.html' % source,
                {
                    'form':form,
                    'errors': errors
                },
                context_instance = RequestContext(request))
    

def register_for_deals(request):
    form = DealRegisterForm()
    if request.method == 'POST':
        form = DealRegisterForm(request.POST)
        error = []
        if form.is_valid():
            name = form.cleaned_data['name'].strip()
            email_id  = form.cleaned_data['email'].strip()
            mobile_no = form.cleaned_data['mobile'].strip()
            info = subscribe_user(request, name, email_id, mobile_no, None)
#            if info['is_valid']:
            log.info("Email:%s and Mobile:%s subscribed " % (email_id, mobile_no))
#                response = HttpResponse(simplejson.dumps(dict(status='ok',msg='subscribed')))
            info['status'] = 'ok'
            temp = render_to_string('fb/subscription_popup.html', info)
            info['html'] = temp
            response = HttpResponse(simplejson.dumps(info))
            utils.set_user_subscribed_for_deals(request)
            utils.set_cookie(request, response, 'nevermissadeal', True)
            return response
#            errors = info['errors']
#            return HttpResponse(simplejson.dumps(dict(status='failed',error=errors)))
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
            email_id = f['email'].strip()
            mobile_no = f['mobile'].strip()

            user_info = get_user_by_email_or_mobile(email_id, mobile_no)
            email_user, phone_user, email_alert_on, sms_alert_on = user_info

            if not email_user and not phone_user:
                #new user
                user = User.objects.create_user(email_id,email_id,None)
                user.first_name = f['name'].strip()
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
        user = auth.authenticate(facebook_user=user,**dict(request=request))
        request.session['logged_through_facebook'] = True
        if user:
            request.session['atg_username'] = user.username
            set_logged_in_user(request, user)
            log.info("FACEBOOK USER LOGGED IN: %s" % user)
            return HttpResponse("OK") 
    else:
        return HttpResponse("OK") 
    return HttpResponse("FAILED") 

def subscribe_email_link(request, alliance_name=None):
    form = FBRegisterForm()
    url = request.get_full_path()
    if not alliance_name:
        raise Http404
    else:
        affiliate_name = alliance_name.strip()
    try:
        affiliate_subscription = SubscriptionLink.objects.get(path='/'+affiliate_name)
    except:
        raise Http404
    affiliate = affiliate_subscription.affiliate
    affiliate_logo = affiliate.logo
    affiliate_text = affiliate.text
    newsletter = affiliate_subscription.newsletter
    do_post = True
    show_avail_coupon = affiliate.is_coupon_avail
    if affiliate_name == "afaqs":
        do_post = False
    errors = []
    welcome_html = 'fb/register_for_deals.html'
    special_offers = ['gift']
    if affiliate_name in special_offers:
        welcome_html = 'fb/register_for_special_offers.html'
    if request.method == 'POST':
        form = FBRegisterForm(request.POST)
        error=''
        already_subscribed = False
        if form.is_valid():
            f=form.cleaned_data
            email_id = f['email'].strip()
            mobile_no = f['mobile'].strip()
            name = f['name'].strip()
            email_user,phone_user,email_alert_on,sms_alert_on = get_user_by_email_or_mobile(email_id,mobile_no)
            html_page = 'fb/discount-%s.html' % affiliate_name

            is_valid = True
            _coupon = Voucher.objects.filter(affiliate= affiliate, status="active").order_by('id')
            text = 'your' 
            total_coupon_codes ={}
            if affiliate.is_coupon_avail:
                if _coupon:
                    _coupon = _coupon[0]
                    total_coupon_codes[affiliate_name] = _coupon.code
                else:
                    errors.append("Sorry!! Coupons are not available")
                    is_valid = False
                if affiliate_name == 'esc':
                    total_coupon_codes = assign_coupons(affiliate)
            if is_valid:
                if not email_user and not phone_user: #new user
                    user,profile = utils.get_or_create_user(email_id, email_id, None, name)

                    email = UserEmail.objects.get(user=profile,type='primary',email=email_id)
                    email_alert_on = email
                    phone = Phone(user=profile,type='primary',phone=mobile_no)
                    phone.save()
                    sms_alert_on = phone
                elif email_user and phone_user:
                    if phone_user == email_user:
                        is_valid = True
                    else:
                        errors.append('Email id and Phone are not registered for the same user.')
                        is_valid = False
                elif not email_user and phone_user: #user with phone number already exist, update his email address only
                    errors.append('Mobile number is already subscribed.')
                    is_valid = False
                elif not phone_user and email_user: #user with email already exist, update his phone number only
                    errors.append('Email address is already subscribed.')
                    is_valid = False
                
            if not is_valid:
                return render_to_response(welcome_html,
                    {
                        'form':form,
                        'affiliate_logo':affiliate_logo,
                        'affiliate_text':affiliate_text,
                        'affiliate_name':affiliate_name,
                        'do_post':do_post,
                        'errors':errors,
                    },context_instance = RequestContext(request))
            url = request.get_full_path()
            existing_subscription_email = DailySubscription.objects.filter(newsletter=newsletter,email_alert_on=email_alert_on,source = affiliate_name)
            existing_subscription_phone = DailySubscription.objects.filter(newsletter=newsletter,sms_alert_on=sms_alert_on,source = affiliate_name)
            if affiliate_name in ["vcomm",'affinity','tyroo']:
                existing_subscription_email = DailySubscription.objects.filter(email_alert_on=email_alert_on)
                existing_subscription_phone = None
            if not existing_subscription_email and not existing_subscription_phone:
                subscribe = DailySubscription()
                subscribe.newsletter = newsletter
                subscribe.sms_alert_on = sms_alert_on
                subscribe.email_alert_on = email_alert_on
                subscribe.source = affiliate_name
                subscribe.save()

                if request.POST.get("selected_affiliates","") == "selected_affiliates":

                    t_body = get_template('notifications/users/affiliates_afaqs.email')
                    email_body = {}
                    email_body['request'] = request
                    email_body['name'] = name
                    c_body = Context(email_body)
                    t_subject = get_template('notifications/users/subscribe_sub.email')
                    email_from = {}
                    email_subject = {}
                    c_subject = Context(email_subject)
                    mail_obj = EmailAddress()
                    if is_future_ecom(request.client.client):
                        mail_obj.isHtml = True
                    mail_obj._from = request.client.client.promotions_email
                    mail_obj.body = t_body.render(c_body)
                    mail_obj.subject = t_subject.render(c_subject)
                    u_emails = ""
                    email = str(email_id)
                    u_emails = email.strip(',')
                    mail_obj.to = u_emails
                    mail_obj.send()

                    utils.subscribe_send_sms(mobile_no)
                    return HttpResponseRedirect("/")
                
                if not affiliate.is_coupon_avail:
                    if affiliate_name in special_offers:
                        send_coupons_by_email(request, total_coupon_codes, affiliate_name, email_alert_on, show_avail_coupon)
                        send_coupons_by_sms(request, total_coupon_codes, affiliate_name, sms_alert_on, show_avail_coupon)
                    else:
                        utils.subscribe_send_email(request,email_id, name)
                        utils.subscribe_send_sms(mobile_no)
                    return render_to_response('fb/thankyou-%s.html' % affiliate_name,{'email_id':email_id},context_instance = RequestContext(request))
                    
                if email_alert_on:
                    send_coupons_by_email(request, total_coupon_codes, affiliate_name, email_alert_on, show_avail_coupon)

                if sms_alert_on:
                    send_coupons_by_sms(request, total_coupon_codes, affiliate_name, sms_alert_on, show_avail_coupon)

                if affiliate_name != 'esc': 
                    _coupon.status = "inactive"
                    _coupon.save()
            else:
                errors.append("You have already subscribed for the deal.")
                already_subscribed = True
                is_valid = False

            if affiliate_name in ["vcomm",'affinity','tyroo']:
                return render_to_response('fb/subscribed.html',
                    {'affiliate_name':affiliate_name,'already_subscribed':already_subscribed},
                    context_instance = RequestContext(request))
    
            if is_valid: 
                return render_to_response(html_page,
                    {'affiliate_name':affiliate_name,'coupon_codes':total_coupon_codes, 'already_subscribed':already_subscribed},
                    context_instance = RequestContext(request))
    return render_to_response(welcome_html,
        {
            'form':form,
            'affiliate_logo':affiliate_logo,
            'affiliate_text':affiliate_text,
            'affiliate_name':affiliate_name,
            'do_post':do_post,
            'errors':errors,
            'show_avail_coupon':show_avail_coupon,
        },
        context_instance = RequestContext(request))

def assign_coupons(affiliate):
    text = 'your' 
    offer_available_at = ['bigbazaar','futurebazaar','pantaloon']
    total_coupon_codes = {}
    #total_coupon_codes['bigbazaar'],total_coupon_codes['futurebazaar'],total_coupon_codes['pantaloon']=[],[],[]

    for offer in offer_available_at:
        coupon_types = CouponType.objects.filter(affiliate = affiliate,discount_available_on = offer)
        if coupon_types:
            text = text + ' '+offer+' coupon code/s:'
        for coupon_type in coupon_types:
            voucher = Voucher.objects.filter(affiliate = affiliate, type = coupon_type,status='active').order_by('id')
            if voucher:
                voucher = voucher[0]
                total_coupon_codes[coupon_type.discount_available_on] = voucher.code
                voucher.status = 'inactive'
                voucher.save()
                #text = text + ' ' + voucher.code
                #coupon = voucher
                #coupon.uses += 1
                #coupon.save()
                #if email_alert_on:
                #    voucher_email_map = VoucherEmailMapping()
                #    voucher_email_map.voucher = coupon
                #    voucher_email_map.email = email_alert_on
                #    voucher_email_map.save()
                #if sms_alert_on:
                #    voucher_phone_map = VoucherPhoneMapping()
                #    voucher_phone_map.voucher = coupon
                #    voucher_phone_map.phone = sms_alert_on
                #    voucher_phone_map.save()
    return total_coupon_codes

def send_coupons_by_email(request,coupon,affiliate_name,email_alert_on, show_avail_coupon):
    t_body = get_template('notifications/subscriptions/%s.email' % affiliate_name)
    email_body = {}
    pantaloon_coupon, bigbazaar_coupon, futurebazaar_coupon = None,None,None
    if show_avail_coupon and affiliate_name not in ["afaqs", "vcomm"]:
        try:
            email_body["coupon_code"] = coupon[str(affiliate_name)]
        except KeyError:
            pass
        try:
            email_body['pantaloon'] =  coupon['pantaloon']
        except KeyError:
            pass
        try:
            email_body['bigbazaar'] =  coupon['bigbazaar']
        except KeyError:
            pass
        try:
            email_body['futurebazaar'] =  coupon['futurebazaar']
        except KeyError:
            pass
    
    mail_obj = Email()
    mail_obj._from = "noreply@futurebazaar.com"
    mail_obj.body = t_body.render(Context(email_body))
    mail_obj.subject = "Avail your futurebazaar.com coupon codes."
    mail_obj.to = email_alert_on.email
    mail_obj.send()

def send_coupons_by_sms(request, total_coupon_codes, affiliate_name, sms_alert_on, show_avail_coupon):
    t_sms = get_template('notifications/subscriptions/%s.sms' % affiliate_name)
    sms_content = {}
    if show_avail_coupon:
        try:
            sms_content['coupon_code'] = total_coupon_codes[affiliate_name]
        except KeyError:
            pass
        try:
            sms_content['pantaloon'] = total_coupon_codes['pantaloon']
        except KeyError:
            pass
        try:
            sms_content['bigbazaar'] = total_coupon_codes['bigbazaar']
        except KeyError:
            pass
        try:
            sms_content['futurebazaar'] = total_coupon_codes['futurebazaar']
        except KeyError:
            pass
    c_sms = Context(sms_content)
    sms_text = t_sms.render(c_sms)
    sms = SMS()
    sms.text = sms_text
    sms.mask = request.client.client.sms_mask
    sms.to = sms_alert_on.phone
    sms.send()
                
def get_random_alphabets(length=40):
    allowedChars = "abcdefghijklmnopqrstuvwzyzABCDEFGHIJKLMNOPQRSTUVWZYZ0123456789"
    word = ""
    for i in range(0, length):
            word = word + allowedChars[random.randint(0,0xffffff) % len(allowedChars)]
    return word

def subscription_phone_verification(request):
    if request.method == "POST":
        data = request.GET
        verification_code = data.get('transaction_token', None)
        if verification_code:
            try:
                subscription = Subscription.objects.get(verification_code=verification_code, verified_on=None)
                phone = subscription.contact
                subscription.verified_on = datetime.now()
                subscription.save()
                # Send deal subscription confirmation sms
                utils.subscribe_send_sms(phone)
                log.info("phone number %s verified by zip dial" % phone)
            except Subscription.DoesNotExist:
                log.info("===ZIP DIAL VERIFICATION=== subscription does not exist")
        else:
            log.info("===ZIP DIAL VERIFICATION== zip dial url has no transaction_token")
    return HttpResponse('')

def subscription_email_verification(request):
    if request.method == "GET":
        data = request.GET
        subscribe_id = data.get('subscribe_id', None)
        verification_msg = data.get('verification_msg', None)
        if not subscribe_id or not verification_msg:
            raise Http404
        try:
            subscribe = Subscription.objects.get(id=subscribe_id, verification_code=verification_msg, verified_on=None)
            subscribe.verified_on = datetime.now()
            subscribe.save()
            request.session['show_subscription_verification'] = True
            return HttpResponseRedirect("/")
        except Subscription.DoesNotExist:
            raise Http404
    raise Http404

def subscription_email_resend(request):
    if request.method == "GET":
        data = request.GET
        subscribe_id = data.get('subscribe_id', None)
        if not subscribe_id:
            return HttpResponse(simplejson.dumps(dict(status='failed', msg='Sending Email Failed. Please try it later')))
        try:
            subscribe = Subscription.objects.get(id=subscribe_id, verified_on=None, contact_type='email')
            subscribe.verification_code = get_random_alphabets(length=40)
            subscribe.save()
            # Send verification email to user
            utils.subscribe_send_email(request,subscribe.contact, subscribe.name, subscribe)
            msg = 'Verification Email has been sent to your email id'
            return HttpResponse(simplejson.dumps(dict(status='ok', msg=msg)))
        except Subscription.DoesNotExist:
            pass
    msg = 'Sending Email Failed. Please try it later'
    return HttpResponse(simplejson.dumps(dict(status='failed', msg=msg)))

def add_score(request):
    if request.method == 'POST':
        facebook_user = request.POST['fbuserid']
        score = request.POST['score']
        name = request.POST.get('fbusername', '')
        score_obj = FacebookAppScore(facebook_user=facebook_user,
            score=score, facebook_name=name)
        score_obj.save()
        return HttpResponse("OK")
    return HttpResponse("ERROR")

@never_cache
def get_top_scores(request):
    top_scores = FacebookAppScore.objects.all().order_by('-score')[:10]
    out = "|".join(
        ["%s,%s,%s" % (ts.facebook_user, ts.score, ts.facebook_name or '') for ts in top_scores]) 
    return HttpResponse(out)
