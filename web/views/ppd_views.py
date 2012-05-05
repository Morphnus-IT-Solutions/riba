from django.db.models import Avg, Max, Min, Count
from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader
from django.http import Http404, HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.decorators import *
from django.contrib.auth.models import *
from django.contrib.auth import login as auth_login
from django.contrib  import auth
from django.core.mail import send_mail
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings
from django.db.models import Q, Sum
from django import forms
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
from django.forms.models import BaseModelFormSet
from users.models import *
from orders.models import *
from accounts.models import *
from catalog.models import *
from categories.models import *
from payouts.models import *
from datetime import date, datetime, timedelta
from orders.forms import BasePaymentOptionFormSet
from users.forms import *
from accounts.forms import *
from locations.forms import *
from sellers.forms import ListsForm
#from accounts.forms importseller_namefrom locations.forms import *
from payouts.forms import  *
from utils import utils
from utils.utils import smart_unicode
from utils.utils import getPaginationContext, check_dates, create_context_for_search_results, get_excel_status, save_excel_file
from web.forms import *
from web.models import *
from web.views.order_view import operator
from web.views.user_views import is_new_user, set_logged_in_user, set_eligible_user, user_order_details, show_agent_order_history
from web.views.pricing_views import all_prices, upload_price_xls, save_uploaded_file, get_temporary_file_path
from decimal import Decimal, ROUND_UP
import operator
import gviz_api
import calendar
import re
import ast
import operator
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from sellers.decorators import check_role
import xlrd
from xlrd import XLRDError
from lists.models import List, ListItem
from django.utils import simplejson
#from web.views.content_views import *

def http_error_page(request, error_code=403):
    resp = render_to_response('ppd/%s.html'%error_code, context_instance=RequestContext(request))
    resp.status_code = error_code
    return resp

def homepage_redirect(request):
    return HttpResponseRedirect("/accounts/login/?next=/")

def login(request):
    if request.user.is_authenticated():
        return HttpResponseRedirect("/a")
    type = request.path.split('/')[-2]
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
                return render_to_response('ppd/signin.html',
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
                return render_to_response('ppd/signin.html',
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
                user = auth.authenticate(username=u.username,password=password)
                if user is not None and user.is_active:
# Valid User, so logged in...
                    if user.has_perm('users.access_ppd'):
                        set_logged_in_user(request,user)
                        profile = cache.get('profile-'+str(request.user.id))
                        if not profile:
                            profile = utils.get_user_profile(request.user)
                            cache.set('profile-'+str(request.user.id),profile,1800)
                        return HttpResponseRedirect("/user/" + str(profile.id) + "?sid=0&search_trend=day");
                    else:
                        error = 'You are not authorized to login for Phone Pe Deal. Please go to Chaupaati home and log in.'
                        return render_to_response('ppd/signin.html',
                            {'error':error,
                             'type':type,
                             'status':'failed',
                             'username':username},
                            context_instance=RequestContext(request))
                else:
# Username and password not matching
                    error = 'The Email / Mobile and password you entered do not match.'
            else:
                error = 'Invalid username or password. Please try again'
                return HttpResponse(simplejson.dumps(dict(status='failed',error=error,username=username,password=password)))

            #if domain in utils.MOBILE_DOMAIN:
            return render_to_response('ppd/signin.html',
                {'error':error,
                'type':type,
                'status':'failed'
                },
                context_instance=RequestContext(request))
            #return HttpResponse(simplejson.dumps(dict(status='failed',error=error)))
        else:
#if request method is not POST
            next = request.GET.get('next','/')
            response = render_to_response('ppd/signin.html',
            {'error':error,'type':type,'next':next},
             context_instance=RequestContext(request))
            return response
    except Exception,e:
        log.exception('Error logging in user %s' % repr(e))

def logout(request):
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    
    for client in clients:
        cache.delete('accounts-'+str(client.id)+str(request.user.id))
    cache.delete('clients-'+str(request.user.id))
    cache.delete('profile-'+str(request.user.id))
    
    auth.logout(request)
    request.session.flush()
    params = request.GET
    return HttpResponseRedirect("/")

def seller_signup(request):
    if request.method == "GET":
        form = PpdAdminUserSignupForm()
        seller_signup_dict = {
            'form':form,
        }
        return render_to_response('ppd/signup.html', seller_signup_dict, context_instance=RequestContext(request))

def get_user_dict(request, acc_section=None, *args, **kwargs):
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    my_acct_ctxt = getMyAccountContext(request)
    cid = int(request.GET.get('cid','1'))
    user_dict = {
        'request':request,
        'acc':my_acct_ctxt,
        'state':'confirmed',
        'loggedin':True,
    }
    account_id = request.GET.get('sid','1')#kwargs['current_seller_id']
    try:
        account = Account.objects.get(id=account_id)
        accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
        if not accounts:
            accounts = profile.managed_accounts.filter(client__id = account.client.id)
            cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
        user_dict['accounts']=accounts
    except:
        account = 0
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    user_dict['current_seller_id']=account_id
    user_dict['selected_account']=account
    user_dict['clients']=clients
    user_dict['cid']=cid
    
    if acc_section:
        user_dict['acc_section'] = acc_section

    try:
        user_dict['acc_section_type'] = kwargs['acc_section_type']
    except:
        pass
    return user_dict

def home(request, *args, **kwargs):
    return render_to_response('ppd/home.html', context_instance=RequestContext(request))

def user_home(request, *args, **kwargs):
    if request.user.is_authenticated():
        if not request.user.has_perm('users.access_ppd') and not request.user.has_perm('users.access_ifs'):
            return render_to_response('ppd/user_home.html',dict(view_not_allowed=True,loggedin=True),context_instance=RequestContext(request))
        profile = cache.get('profile-'+str(request.user.id))
        if not profile:
            profile = utils.get_user_profile(request.user)
            cache.set('profile-'+str(request.user.id),profile,1800)
        accounts = profile.managed_accounts.all()
        if accounts:
            seller_id = accounts[0].id
        else:
            if request.user.has_perm('users.access_ifs'):
                return render_to_response('ifs/ifs_home.html',dict(loggedin=True),context_instance=RequestContext(request))    
            else:
                return render_to_response('ppd/home.html', context_instance=RequestContext(request))
        acc_section = "profile"
        url="/a/" + acc_section + "/" + str(seller_id)
        return HttpResponseRedirect(url)

    else:
        return render_to_response('ppd/home.html', dict(loggedin=False),context_instance=RequestContext(request))

@login_required
@check_role('Orders')
def promotions_list(request,client_name, seller_name,fromindex, *args, **kwargs):
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('promotions-list',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers','fromindex':0,}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('promotions-list',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,'fromindex':0,}))
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)

    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
        
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('promotions-list',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers','fromindex':0,})) 
    
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)

    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
    
    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('promotions-list',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),'fromindex':0,})) 
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('promotions_list',None,kwargs={'client_name':client_name,'seller_name':'all-sellers','fromindex':0,})) 

    promotionsJsonStr = APIManager.getAllPromotions(fromindex, 10)
    promotionsJson = simplejson.loads(promotionsJsonStr)
    

    i=1
    for promo in promotionsJson['promotions'] :
        promo['url'] = '/show_promotion/'+client_name+'/'+seller_name+'/'+str(promo['promotionId'])+'/'  
        promo['onbutton'] = str(promo['promotionId']) + 'on' 
        promo['onnotbutton'] =  str(promo['promotionId']) + 'onnot' 
        promo['buttonname'] = str(promo['promotionId'])
        promo['index'] = 'promo' + str(i)
        promo['len'] = len(promo['coupons'])
        if(len(promo['coupons'])>0):
            promo['firstcoupon'] = promo['coupons'][0]
        else:
            promo['firstcoupon'] = ''
        i=i+1
        

    i=1
    for promo in promotionsJson['promotions'] :
        promo['url'] = '/show_promotion/'+client_name+'/'+seller_name+'/'+str(promo['promotionId'])+'/'  
        promo['onbutton'] = str(promo['promotionId']) + 'on' 
        promo['onnotbutton'] =  str(promo['promotionId']) + 'onnot' 
        promo['buttonname'] = str(promo['promotionId'])
        promo['index'] = 'promo' + str(i)
        i=i+1
    
    fromindex_next = int(fromindex) + 10
    fromindex_prev = int(fromindex) - 10
    if fromindex_prev < 0:
        fromindex_prev = 0    

    promotions_list_dict = {
        'loggedin':True,
        'clients':clients,
        'accounts':accounts,
        'client_name':client_name,
        'seller_name':seller_name,
        'promotions':promotionsJson,
        'fromindex_next':fromindex_next,
        'fromindex_prev':fromindex_prev,
        'fromindex':fromindex,
        'client_display_name':Client.objects.filter(slug=client_name)[0].name
    }

    return render_to_response('ppd/promotions_list.html',promotions_list_dict, context_instance=RequestContext(request))



def create_new_promotion(request,client_name, seller_name,  *args, **kwargs):
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('create-new-promotion',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('create-new-promotion',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
        
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('create-new-promotion',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers',})) 
    
    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('create-new-promotion',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),})) 
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('create-new-promotion',None,kwargs={'client_name':client_name,'seller_name':'all-sellers',})) 
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)

    
    create_promotions_dict = {
        'loggedin':True,
        'clients':clients,
        'accounts':accounts,
        'client_name':client_name,
        'seller_name':seller_name,
        'client_display_name':Client.objects.filter(slug=client_name)[0].name
    }
    
    return render_to_response('ppd/create_new_promotion.html',create_promotions_dict, context_instance=RequestContext(request))

def save_promotion(request,client_name, seller_name,  *args, **kwargs):
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('save-promotion',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('save-promotion',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
        
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('save-promotion',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers',})) 
    
    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('save-promotion',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),})) 
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('save-promotion',None,kwargs={'client_name':client_name,'seller_name':'all-sellers',})) 
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)


    promotions_dict={}
    if request.method == "POST":
        promotion_name = request.POST.get('profile-name', None)
        promotion_type = request.POST.get('promotion-type',None)
        promotion_start_date = request.POST.get('start-date',None)
        promotion_end_date = request.POST.get('end-date',None)
        promotion_discount_type = request.POST.get('discount-type',None)
        promotion_discount_value = request.POST.get('discount-value',None)
        promotion_applies_on = request.POST.get('applies-on',None)
        promotion_user_type = request.POST.get('user-type',None)
        promotion_n_coupons = request.POST.get('n-coupons',None)
        promotion_min_order_value = request.POST.get('min-order-value',None)
        if len(promotion_min_order_value)==0:
            promotion_min_order_value=0

        promotions_dict = {
            'promotion_name':promotion_name,
            'promotion_type':promotion_type,
            'promotion_start_date':promotion_start_date,
            'promotion_end_date':promotion_end_date,
            'promotion_discount_type':promotion_discount_type,
            'promotion_discount_value':promotion_discount_value,
            'promotion_applies_on':promotion_applies_on,
            'promotion_user_type':promotion_user_type,
            'promotion_min_order_value':promotion_min_order_value,
            'promotion_n_coupons':promotion_n_coupons
        }
        promotions_dict_json = simplejson.dumps(promotions_dict)
        promotionId = APIManager.savePromotion(promotions_dict_json)


    save_promotion_dict = {
        'loggedin':True,
        'clients':clients,
        'accounts':accounts,
        'client_name':client_name,
        'seller_name':seller_name,
        'promotion':promotions_dict
    }

    if len(promotionId)!=0 :
        redirectUrl = '/show_promotion/'+ client_name + '/' + seller_name + '/' + promotionId + '/'
    else:
        redirectUrl = '/create_new_promotion/'+ client_name + '/' + seller_name
        
    from django.shortcuts import redirect
    return redirect(redirectUrl)

def save_promotion_list(request,client_name, seller_name,fromindex,  *args, **kwargs):
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('save-promotion-list',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers','fromindex':fromindex,}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('save-promotion-list',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,'fromindex':fromindex,}))
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
        
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('save-promotion-list',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers','fromindex':fromindex,})) 
    
    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('save-promotion-list',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),'fromindex':fromindex,})) 
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('save-promotion-list',None,kwargs={'client_name':client_name,'seller_name':'all-sellers','fromindex':fromindex,})) 
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)

    active_promotion_dict={}
    active_promotion_ids = []
    if request.method == "POST":
        for k in range(1,11):
            promotionId = request.POST.get('promo'+str(k),None)
            promotionActive = request.POST.get(str(promotionId))
            active_promotion_dict[promotionId] = promotionActive
            active_promotion_ids.append(promotionId)

    active_promotion_dict['keys'] = active_promotion_ids
    active_promotion_dict_str = simplejson.dumps(active_promotion_dict)

    print active_promotion_dict_str
    APIManager.updatePromotionList(active_promotion_dict_str)
    
    save_promotion_list_dict = {
        'loggedin':True,
        'clients':clients,
        'accounts':accounts,
        'client_name':client_name,
        'seller_name':seller_name,
        #'promotion':promotions_dict
    }
    redirectUrl = "/promotions_list/" + client_name +"/" +seller_name +"/" +fromindex + "/" 
    from django.shortcuts import redirect
    return redirect(redirectUrl)



def show_promotion(request,client_name, seller_name,promotionid,  *args, **kwargs):
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('show-promotion',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('show-promotion',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
        
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('show-promotion',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers',})) 
    
    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('show-promotion',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),})) 
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('show-promotion',None,kwargs={'client_name':client_name,'seller_name':'all-sellers',})) 
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)


    jsonString = APIManager.getPromotionById(promotionid)
    promotionsJson= simplejson.loads(jsonString)
    if(len(promotionsJson['coupons'])>0):
        first_coupon =  promotionsJson['coupons'][0]
    else:
        first_coupon = ''

   
    promotions_dict = {
        'promotion_id':promotionsJson['promotionId'],
        'promotion_name':promotionsJson['promotionName'],
        'promotion_type':promotionsJson['promotionType'],
        'promotion_start_date':promotionsJson['startDate'],
        'promotion_end_date':promotionsJson['endDate'],
        'promotion_discount_type':promotionsJson['discountType'],
        'promotion_discount_value':promotionsJson['discountValue'],
        'promotion_applies_on':promotionsJson['appliesOn'],
        'promotion_min_order_value':promotionsJson['minAmountValue'],
        'promotion_active':promotionsJson['active'],
        'promotion_coupons':promotionsJson['coupons'],
        'len':len(promotionsJson['coupons']),
        'first_coupon':first_coupon
    }

    show_promotion_dict = {
        'loggedin':True,
        'clients':clients,
        'accounts':accounts,
        'client_name':client_name,
        'seller_name':seller_name,
        'promotion':promotions_dict,
        'client_display_name':Client.objects.filter(slug=client_name)[0].name
    }


    return render_to_response('ppd/promotion.html',show_promotion_dict, context_instance=RequestContext(request))


def show_coupons(request,client_name, seller_name,promotionid,  *args, **kwargs):
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('show-coupons',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('show-coupons',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
        
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('show-coupons',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers',})) 
    
    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('show-coupons',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),})) 
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('show-coupons',None,kwargs={'client_name':client_name,'seller_name':'all-sellers',})) 
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)


    jsonString = APIManager.getPromotionById(promotionid)
    promotionsJson= simplejson.loads(jsonString)

   
    show_coupons_dict = {
        'loggedin':True,
        'clients':clients,
        'accounts':accounts,
        'client_name':client_name,
        'seller_name':seller_name,
        'promotion_coupons':promotionsJson['coupons']
    }


    return render_to_response('ppd/coupons.html',show_coupons_dict, context_instance=RequestContext(request))



def acc_sections(request, *args, **kwargs):
    if request.user.is_authenticated():
        acc_section = kwargs['acc_section']
        current_seller_id = kwargs['current_seller_id']
        acc_sections_dict = {
            'acc_section':acc_section,
            'current_seller_id':current_seller_id,
        }
        return render_to_response('ppd/acc_section_display.html', acc_sections_dict, context_instance=RequestContext(request))
    else:
        return render_to_response('ppd/home.html', dict(loggedin=False),context_instance=RequestContext(request))

def client_account_display_action(request):
    if request.user.is_authenticated():
        if request.method == "POST":
            client_name = request.POST['user_clients']
            return HttpResponseRedirect(url)
    else:
        return render_to_response('ppd/dashboard.html', dict(loggedin=False),context_instance=RequestContext(request))

def seller_account_display_action(request):
    if request.user.is_authenticated():
        try:
            page = request.POST['page']
        except:
            pass
        if request.method == "POST":
            client_id = "0"
            seller_id = request.POST['sid']
            url = request.POST['url']
            try:
                cid = request.POST['old_cid']
                sid = request.POST['old_sid']
                page = request.POST['page']
            except:
                pass
            try:
                account = Account.objects.get(id=seller_id)
                client_id = unicode(account.client.id)
            except:
                pass

            if "seller/orders" in url or "user/orders" in url:
                url = "/a/orders/confirmed/?cid="+client_id+"&sid="+seller_id+"&search_trend=day"
            
            if "cid=" not in url and "sid=" not in url:
                if "?" not in url:
                    if client_id !="0":
                        url += "?cid=" + client_id + "&sid=" + seller_id
                else:
                    if client_id !="0":
                        url +=  "&cid=" + client_id + "&sid=" + seller_id
            
            elif "cid=" in url and "sid=" not in url:
                url += "&sid=" + seller_id
            
                
            elif "cid=" in url and "sid=" in url:
                url = url.replace("sid="+sid,"sid="+seller_id)
                url = url.replace("cid=1"+cid,"cid="+client_id)

            elif "cid=" not in url and "sid=" in url:
                url = url.replace("sid="+sid,"sid="+seller_id)
                url +=  "&cid=" + client_id 
            
            if "page" in url:
                url = url.replace("&page="+page, "")
            return HttpResponseRedirect(url)

def requires_login(view, *args, **kwargs):
    def new_view(request, *args, **kwargs):
        if request.user.is_authenticated():
            loggedin = True
        else:
            loggedin = False
            return HttpResponseRedirect('/accounts/login/')
        if request.user.has_perm('users.access_ppd'):
            account = Account.objects.get(id = kwargs['current_seller_id'])
            if account in utils.get_user_profile(request.user).managed_accounts.all():
                return view(request, *args, **kwargs)
            else:
                login_dict = {
                    'loggedin': loggedin,
                    'view_not_allowed': True,
                }
                return render_to_response('web/ppd_base.html', login_dict, context_instance=RequestContext(request))
        else:
            login_dict = {
                'loggedin': loggedin,
                'view_not_allowed': True,
            }
            return render_to_response('web/ppd_base.html', login_dict, context_instance=RequestContext(request))
    return new_view

@login_required   
def user_login_page(request, client_name, seller_name):
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
    if request.method == "POST":
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            return HttpResponsePermanentRedirect(reverse('ppd-user-login-page',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            return HttpResponsePermanentRedirect(reverse('ppd-user-login-page',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('ppd-user-login-page',None,kwargs={'client_name':profile.managed_clients()[0].slug,'seller_name':'all-sellers',})) 
    if seller_name=='all-sellers':
        current_seller_id = 0
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('ppd-user-login-page',None,kwargs={'client_name':client_name,'seller_name':'all-sellers',})) 
    login_dict = {
            'loggedin':True, 
            'client_name':client_name, 
            'seller_name':seller_name,
            'clients':clients,
            'client_display_name':Client.objects.filter(slug=client_name)[0].name,
            'accounts':accounts
            }
    return render_to_response('ppd/user_login_page.html', login_dict, context_instance=RequestContext(request))

#@login_required
#@check_role([])
#def user_deletelists(request,client_name, seller_name, ID, *args, **kwargs):
#	url=request.get_full_path()
#	html = "<html><body>sdfg </body</html>"
#	return HttpResponse(html)


@login_required
@check_role([])
def user_editlists(request, client_name, seller_name, ID, *args, **kwargs):
	url = request.get_full_path()
	if request.method=="POST":
		check = request.POST.get('name', None)
		try:
			new_client_name = request.POST['user_clients']
		except:
			new_client_name= client_name
		if new_client_name != client_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-lists', None, kwargs={'client_name':new_client_name,'seller_name':'all-sellers'}))
		try:
			new_seller_name= request.POST['user_sellers']
		except:
			new_seller_name = "All Sellers"
		if new_seller_name!=seller_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None, kwargs = {'client_name':client_name, 'seller_name':new_seller_name,}))
		
		#getting ids from client_name and seller_name
	client = Client.objects.select_related('id').filter(slug=client_name)
	profile = request.user.get_profile()
	clients = profile.managed_clients()
	accounts = profile.managed_accounts.filter(client__slug = client_name)
	if client:
		client_id = client[0].id
	else:
		return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers'}))
	seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)
	flag=0
	listitem12=[]
	listitemobj=[]
	dflag=0
	errorflag=0
	objflag=0
	#coordflag=0
	if request.method == "POST":
		a = List.objects.get(id=ID)
		form=ListsForm(request.POST,request.FILES, instance=a)
		b=ListItem.objects.filter(list=a)
		l = len(b)
		iteminlineformset = inlineformset_factory(List, ListItem, form=ListItemForm, max_num=0)
		#if request.POST.get("id")=="Delete":
		if "dellist" in request.POST:

			formset = iteminlineformset(request.POST,request.FILES, instance=a)
			flag=2
			a = List.objects.get(id=ID)
			b = ListItem.objects.filter(list=a)
			a.delete()
			b.delete()
			client_obj = Client.objects.get(name=client[0].name)
			list_obj = List.objects.filter(client=client_obj.id)

		elif "save" in request.POST:
			#print "a----------------", a
			#print "b----------------", b
			formset = iteminlineformset(request.POST,request.FILES, instance=a)
			flag=1
			errorflag=0
			#print "erorflag in save-------------", errorflag
			if form.is_valid():
				errorflag=0
				#print "errorlfag in form.isvalid------------", errorflag
				clientobj = Client.objects.get(name = client[0].name)
				objlist= List.objects.get(id=ID)
				old_starts_on=objlist.starts_on
				old_ends_on=objlist.ends_on
				title = form.cleaned_data['title']
				type= form.cleaned_data['type']
				objlist.title = form.cleaned_data['title']
				objlist.slug = form.cleaned_data['slug']
				objlist.client = clientobj
				form.client = clientobj
				objlist.type = form.cleaned_data['type']
				objlist.template_type = form.cleaned_data['template_type']
				objlist.description = form.cleaned_data['description']
				objlist.starts_on = request.POST.get('starts_on',None)
				objlist.ends_on = request.POST.get('ends_on',None)
				#objlist.is_featured = form.cleaned_data['is_featured']
				#objlist.visibility = form.cleaned_data['visibility']
				objlist.banner_image=form.cleaned_data['banner_image']
				if objlist.banner_image==False:
					objlist.banner_image=None
				print "objlist.banner_image---------------", 	objlist.banner_image
				#objlist.tagline=form.cleaned_data['tagline']
				#objlist.sort_order=form.cleaned_data['sort_order']
				objlist.redirect_to=form.cleaned_data['redirect_to']
				objlist.banner_type=form.cleaned_data['banner_type']
				if objlist.starts_on:
					if objlist.ends_on:
						pass
					else:
						objlist.ends_on=old_ends_on
				else:
					objlist.starts_on=old_starts_on
					objlist.ends_on=old_ends_on

				for i in formset.forms:
					if i.is_valid():
						seq = i.cleaned_data['sequence']
						if seq<>None:
							print "sequence not none"
							if seq<=0:
								print "my sequence is", seq
								errorflag=1
								print "my error is------------", errorflag
					else:
						objflag=1
				#print "objflag before saving-----------", objflag
				#print "errorflag before saving-----------", errorflag
				if objflag==0 and errorflag==0:
					#print "objflag==", objflag
					#if errorflag==0:
					objlist.save()

				#objlist.save()
				client_obj = Client.objects.get(name=client[0].name)
				list_obj = List.objects.filter(client=client_obj.id)
				listobj = List.objects.get(id=ID)
				listitem12=ListItem.objects.filter(list=listobj)
				listitemobj=[]
				count=0
				for i in formset.forms:
					#print "edit in for--------_", i
					if i.is_valid():
						errorflag=0
						#print "is valid"
						try:
							#print "edit in try----------"
							sku = i.cleaned_data['sku']
							#print "sku-----", sku.id
							listitem =ListItem()
							listitem.list = listobj
							listitem.sku_id = sku.id
							listitem.sequence = i.cleaned_data['sequence']
							if listitem.sequence==None:
								listitem.sequence=999
							if listitem.sequence <=0:
								errorflag=1
							listitem.user_description = i.cleaned_data['user_description']
							listitem.user_title = i.cleaned_data['user_title']
							listitem.user_features = i.cleaned_data['user_features']
							listitem.starts_on = objlist.starts_on
							listitem.ends_on = objlist.ends_on
							listitem.status = i.cleaned_data['status']
							listitem.user_image = i.cleaned_data['user_image']

							if listitem.user_image==False:
								listitem.user_image=None
							listitem.redirect_to = i.cleaned_data['redirect_to']
							#print "listiemffuawer image------", listitem.user_image
							listitemobj.append(listitem)
							count=count+1
							#listitemobj.save()
						except Exception ,e:
							#print "exception 1", e
							pass
					else:
						errorflag=1
						#print "errorflag-------------", errorflag
						#print "i invalid, i errors %s" % repr(i.errors)
			else:
				errorflag=1
				#print "errorflag==", errorflag
				#print "forminvlaid %s" % repr(form.errors)
			if errorflag==0 and objflag==0:
				for i in listitem12:
					#print "hahahaaa---", i
					i.delete()
				for i in listitemobj:
					#print i
					i.save()

		elif "additem" in request.POST:
			flag=1
			errorflag=1
			#print "flag in additem post edit----", flag
			#print "errorflag in additem post edit------------", errorflag
			dflag=1

			formset = iteminlineformset(request.POST,request.FILES, instance=a)
			#print "calling additem in request.post"
			a = List.objects.get(id=ID)
			form=ListsForm(request.POST,request.FILES, instance=a)
			b=ListItem.objects.filter(list=a)
			l = len(b)
			iteminlineformset = inlineformset_factory(List, ListItem, form=ListItemForm)
			cp=request.POST.copy()
			np = request.POST.copy()
			cp['listitem_set-TOTAL_FORMS']=int(cp['listitem_set-TOTAL_FORMS'])+1
			formset=iteminlineformset(cp,request.POST , instance=a)
		#print "flag just before edit_dict---------------", flag
		#print "erorflag just before edit_dict---------------", errorflag
		edit_dict = {
			'form': form,
			'formset':formset,
			'size': l,
			'client_name':client_name,
			'seller_name':seller_name,
			'ID':ID,
			'flag':flag,
			'dflag':dflag,
            'errorflag':errorflag,
			#'coordflag':coordflag,
			'obj':a,
			'loggedin':True,
			'pg':1,
			'url':url,
			'accounts':accounts,
			'clients':clients,
			}
		edit_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
		return render_to_response('lists/edit_lists.html', edit_dict, context_instance=RequestContext(request))

	else:
		a = List.objects.get(id=ID)
		form =ListsForm(instance=a)
		b = ListItem.objects.filter(list=a)
		l =len(b)
		flag=1
		errorflag=1
		#print "flag in get========", flag
		#print "errorflag in get---------", errorflag
		iteminlineformset = inlineformset_factory(List, ListItem, form = ListItemForm, max_num=0)
		formset = iteminlineformset(instance =a)
		edit_dict = {	
			'client_name':client_name,
			'seller_name':seller_name,
			'ID':ID,
            'errorflag':errorflag,
			'flag':flag,
			'dflag':dflag,
			#'coordflag':coordflag,
			'loggedin':True,
			'form':form,
			'formset':formset,
			'size':l,
			'obj':a,
			'url':url,
			'clients':clients,
			'accounts':accounts,
		}
		edit_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
	return render_to_response('lists/edit_lists.html', edit_dict, context_instance=RequestContext(request))

@login_required
@check_role([])
def user_view_coordinates(request, client_name, seller_name, ID, *args, **kwargs):
	url = request.get_full_path()
	if request.method=="POST":
		check = request.POST.get('name', None)
		try:
			new_client_name = request.POST['user_clients']
		except:
			new_client_name= client_name
		if new_client_name != client_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-view-coordinates', None, kwargs={'client_name':new_client_name,'seller_name':'all-sellers'}))
		try:
			new_seller_name= request.POST['user_sellers']
		except:
			new_seller_name = "All Sellers"
		if new_seller_name!=seller_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-view-coordinates',None, kwargs = {'client_name':client_name, 'seller_name':new_seller_name,}))
		
		#getting ids from client_name and seller_name
	client = Client.objects.select_related('id').filter(slug=client_name)
	profile = request.user.get_profile()
	clients = profile.managed_clients()
	accounts = profile.managed_accounts.filter(client__slug = client_name)
	if client:
		client_id = client[0].id
	else:
		return HttpResponsePermanentRedirect(reverse('ppd-user-view-coordinates',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers'}))
	listobj=List.objects.get(id=ID)
	coordobj=Coordinates.objects.filter(list=listobj)
	view_coordinates_dict = {
		#'form': form,
		'client_name':client_name,
		'seller_name':seller_name,
		'ID':ID,
		'loggedin':True,
		'url':url,
		'accounts':accounts,
		'clients':clients,
		'listobj':listobj,
		'coordobj':coordobj,
		}
	view_coordinates_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
	return render_to_response('lists/view_coordinates.html', view_coordinates_dict, context_instance=RequestContext(request))


@login_required
@check_role([])
def user_coordinates(request, client_name, seller_name, ID, *args, **kwargs):
	url = request.get_full_path()
	if request.method=="POST":
		check = request.POST.get('name', None)
		try:
			new_client_name = request.POST['user_clients']
		except:
			new_client_name= client_name
		if new_client_name != client_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-coordinates', None, kwargs={'client_name':new_client_name,'seller_name':'all-sellers'}))
		try:
			new_seller_name= request.POST['user_sellers']
		except:
			new_seller_name = "All Sellers"
		if new_seller_name!=seller_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-coordinates',None, kwargs = {'client_name':client_name, 'seller_name':new_seller_name,}))
		
		#getting ids from client_name and seller_name
	client = Client.objects.select_related('id').filter(slug=client_name)
	profile = request.user.get_profile()
	clients = profile.managed_clients()
	accounts = profile.managed_accounts.filter(client__slug = client_name)
	if client:
		client_id = client[0].id
	else:
		return HttpResponsePermanentRedirect(reverse('ppd-user-coordinates',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers'}))
	nflag=0
	if request.method=="POST":
		errorflag=0
		coordformset = modelformset_factory(Coordinates, max_num=0, extra=4)
		#coordformset=formset_factory(CoordinatesForm, max_num=0, extra=4)
		data = {
			'coord-TOTAL_FORMS':u'4',
			'coord-INITIAL_FORMS':u'4',
			'coord-MAX_NUM_FORMS':u'4',
			}

		#formset = coordformset(request.POST, data, prefix='coord')
		formset = coordformset(request.POST, prefix='coord')
		coordlist=[]
		#form=CoordinatesForm(request.POST, prefix="coordinates")
		for i in formset.forms:
			if i.is_valid():
				nflag=1
				#print "i valid"
				try:
					#print "try------"
					coordobj= Coordinates()
					listobj = List.objects.get(id=ID)
					#print "listobj--------------_in coord", listobj
					coordobj.list=listobj
					coordobj.sequence=i.cleaned_data['sequence']
					#print "reading data----------", coordobj.sequence
					if coordobj.sequence<=0 and coordobj.sequence>=10:
						errorflag=1
						#print "erroflag and sequence---------", errorflag, coordobj.sequence
					#print "coordobj.sequence--------", coordobj.sequence
					coordobj.co_ordinates=i.cleaned_data['co_ordinates']
					coordobj.link=i.cleaned_data['link']
					if coordobj.sequence:
						coordlist.append(coordobj)
				except Exception, e:
					#print "whye---------", e
					pass
			else:
				k=i.errors
				for j in k:
					if j.find('sequence'):
						#print "j has sequence---------"
						pass
				errorflag=1
				#print "repreprepreprpereprpe", repr(i.errors)
		listobj = List.objects.get(id=ID)
		#print "listobj coord---------", listobj
		try:
			queryset = Coordinates.objects.filter(list=listobj)
			if errorflag==0:
				for i in queryset:
					#print "deleting-----------"
					i.delete()
		except Exception, e:
			#print "exception-----454545", e
			pass
		if errorflag==0:
			for i in coordlist:
				i.save()
			nflag=1
		coordinates_dict = {
			#'form': form,
			'formset':formset,
			'client_name':client_name,
			'seller_name':seller_name,
			'ID':ID,
			'loggedin':True,
			'url':url,
			'ID':listobj.id,
			'accounts':accounts,
			'clients':clients,
			'listobj':listobj,
			'nflag':nflag,
			'errorflag': errorflag,
			}
		coordinates_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
		return render_to_response('lists/coordinates.html', coordinates_dict, context_instance=RequestContext(request))
	else:
		nflag=1
		errorflag=1 
		coordformset = modelformset_factory(Coordinates, form=CoordinatesForm, extra=4)
		#coordformset=formset_factory(CoordinatesForm, extra=4)
		listobj=List.objects.get(id=ID)
		#print "coordformset-----------,", coordformset
		data = {
			'coord-TOTAL_FORMS':u'4',
			'coord-INITIAL_FORMS':u'4',
			'coord-MAX_NUM_FORMS':u'4',
			#'coord-0-sequence':u'1',
			#'coord-0-co_ordinates':u'1',
			#'coord-0-link':u'1',
		}
		try:
			queryset12 = Coordinates.objects.filter(list=listobj) 
#			formset = coordformset(data, prefix='coord', queryset=queryset12)
			formset = coordformset(prefix='coord', queryset=queryset12)
		except Exception, e:
#			formset = coordformset(data, prefix='coord')
			print "exception676767-----------", e
			formset = coordformset(prefix='coord')

		#print "formset=-----", formset
		for i in formset:
			try:
				pass
				#print i.is_valid()
			except Exception,e:
				pass
				#print "eeeeeeeeeee is ",e
			#print "form.sequence---------", i
		coordinates_dict = {
			#'form': form,
			'loggedin':True,
			'formset':formset,
			'url':url,
			'listobj':listobj,
			'ID':listobj.id,
			'clients':clients,
			'accounts':accounts,
			'client_name':client_name,
			'seller_name':seller_name,
			'nflag':nflag,
			'errorflag':errorflag,
        }
	coordinates_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
	return render_to_response('lists/coordinates.html', coordinates_dict, context_instance=RequestContext(request))
	
@login_required
@check_role([])
def user_addlists(request, client_name,seller_name, *args, **kwargs):

	url = request.get_full_path()
	if request.method=="POST":
		check = request.POST.get('name', None)
		try:
			new_client_name = request.POST['user_clients']
		except:
			new_client_name= client_name
		if new_client_name != client_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-addlists', None, kwargs={'client_name':new_client_name,'seller_name':'all-sellers'}))
		try:
			new_seller_name= request.POST['user_sellers']
		except:
			new_seller_name = "All Sellers"
		if new_seller_name!=seller_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-addlists',None, kwargs = {'client_name':client_name, 'seller_name':new_seller_name,}))
		
		#getting ids from client_name and seller_name
	client = Client.objects.select_related('id').filter(slug=client_name)
	profile = request.user.get_profile()
	clients = profile.managed_clients()
	accounts = profile.managed_accounts.filter(client__slug = client_name)
	if client:
		client_id = client[0].id
	else:
		return HttpResponsePermanentRedirect(reverse('ppd-user-addlists',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers'}))

	seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)
	flag=0
	dflag=0
	errorflag=0
	#coordflag=0
	ID=0
	if request.method == "POST":#If the form has been submitted
		#print "post----"
		form = ListsForm(request.POST, request.FILES, prefix="lists")
		iteminlineformset = inlineformset_factory(List, ListItem, form = ListItemForm, extra  = 2)
		#formset = iteminlineformset(request.POST, request.FILES, instance = None)
		#coordformset = CoordinatesForm(request.POST,prefix="coordinates")
		#coordinlineformset = inlineformset_factory(List, Coordinates, form =CoordinatesForm, extra=1) 
		#coordformset = coordinlineformset(request.POST, instance=None, prefix="coordinates")

		if 'additem' in request.POST:
			dflag=1
			flag=1
			errorflag=1
			cp=request.POST.copy()
			cp['listitem_set-TOTAL_FORMS']=int(cp['listitem_set-TOTAL_FORMS'])+1
			formset=iteminlineformset(cp,  instance=None)
		elif 'save' in request.POST:
			flag=1
			errorflag=0
			objflag=0
			#print "save--------------"
			formset = iteminlineformset(request.POST,request.FILES, instance = None)
			if form.is_valid():
				#print "formset-----------", formset
				flag=1
				clientobj = Client.objects.get(name = client[0].name)
				obj=List()
				objlist = List()
				title = form.cleaned_data['title']
				objlist.title = form.cleaned_data['title']
				objlist.slug=slugify(title)
				objlist.client = clientobj
				form.client = clientobj
				objlist.starts_on = request.POST.get('lists-starts_on', None)
				objlist.ends_on = request.POST.get('lists-ends_on',None)
				if objlist.starts_on:
					if objlist.ends_on:
						pass
					else:
						objlist.ends_on=None
				else:
					objlist.starts_on=None
					objlist.ends_on=None
				type = form.cleaned_data['type'] 
				client_obj = Client.objects.get(name=client[0].name)
				objlist.type = form.cleaned_data['type']
				objlist.template_type = form.cleaned_data['template_type']
				objlist.description = form.cleaned_data['description']
				#objlist.visibility = form.cleaned_data['visibility']
				objlist.banner_image=form.cleaned_data['banner_image']
				#print "objlist.banner/_image in add------------------------", objlist.banner_image
				#objlist.tagline=form.cleaned_data['tagline']
				#objlist.sort_order=form.cleaned_data['sort_order']
				objlist.redirect_to=form.cleaned_data['redirect_to']
				objlist.banner_type=form.cleaned_data['banner_type']
				#print "objlist.banner_type---------", objlist.banner_type
				#if objlist.banner_type=='image_mapping':
			#		coordflag=1
		#			print "suceess------"
				for i in formset.forms:
					if i.is_valid():
						seq = i.cleaned_data['sequence']
						if seq<>None:
							print "sequence not none"
							if seq<=0:
								print "my sequence is", seq
								errorflag=1
								print "my error is------------", errorflag
					else:
						objflag=1
				#print "objflag before saving-----------", objflag
				#print "errorflag before saving-----------", errorflag
				if objflag==0 and errorflag==0:
					#print "objflag==", objflag
					#if errorflag==0:
					objlist.save()
					objlist=List.objects.get(title=title, type=type, client = client_obj.id)
					ID = objlist.id
					list_obj = List.objects.filter(client=client_obj.id)
					
				for i in formset.forms:
					#print "in for"
					if i.is_valid():
						#print "i valid"
						try:
							#print "in try---------"
							listitemobj = ListItem()
							listobj = List.objects.filter(type=type, client = client_obj, title=title)
							#print "listobj is----------------", listobj
							#print "error after this"
							id1 = listobj[0].id
							#print "error before this"
							i.list_id = id1
							listitemobj.list = listobj[0]
							sku = i.cleaned_data['sku']
							#sku= 6056
							#print "sku--------", sku
							listitemobj.sku_id = sku.id
							#listitemobj.sku_id=6056
							listitemobj.sequence = i.cleaned_data['sequence']
							if listitemobj.sequence==None:
								listitemobj.sequence=999
							if listitemobj.sequence <=0:
								#print "sequence error"
								errorflag=1
							listitemobj.user_description = i.cleaned_data['user_description']
							listitemobj.user_title = i.cleaned_data['user_title']
							user_features = i.cleaned_data['user_features']
							listitemobj.starts_on = objlist.starts_on
							listitemobj.ends_on = objlist.ends_on
							listitemobj.status = i.cleaned_data['status']
							listitemobj.user_image=i.cleaned_data['user_image']
							#print "listitemobj.banner/_image in add------------------------", listitemobj.user_image
							listitemobj.redirect_to=form.cleaned_data['redirect_to']
							#print "listitemobj-------------", listitemobj
							listitemobj.save()
						except Exception,e:
							#print "2222222222222except, ", e
							pass
					else:
						errorflag=1
						#print "i invalid, i errors %s" % repr(i.errors)
				if errorflag==0:
					pass
					#objlist.save()
			else:
				errorflag=1
		lists_dict = {
			'form': form,
			#'coordformset':coordformset,
			'formset':formset,
			'client_name':client_name,
			'seller_name':seller_name,
			'ID':ID,
			'loggedin':True,
			'url':url,
			'flag':flag,
			'errorflag':errorflag,
			'dflag':dflag,
			#'coordflag':coordflag,
			'accounts':accounts,
			'clients':clients,
			'pg':1,
			}
		lists_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
		return render_to_response('lists/lists.html', lists_dict, context_instance=RequestContext(request))
	else:
		flag=1
		errorflag=1
		#print "flag in addlist get-----------", flag
		#print "errorflag in addlist get------------", errorflag 
		#print "get--------------------------"
		"""data={
			'title':' ',
			'description':' ',
			'redirect_to':' ',
			'type':'wishlist',
			'template_type':'static',
			'banner_image':' ',
			'banner_type':'image_mapping',
			'starts_on':'Select a Date',
			'ends_on':'Select a Date',
			}
			"""

		form = ListsForm(prefix="lists")
		#coordformset =CoordinatesForm(prefix="coordinates")
		#dflag=0
		#coordflag=0
		iteminlineformset = inlineformset_factory(List, ListItem, form = ListItemForm, extra=2)
		formset = iteminlineformset(instance = None)
		#coordinline = inlineformset_factory(List, Coordinates, form =CoordinatesForm, extra=1) 
		"""data= {'form-TOTAL_FORMS':u'1',
				'form-INITIAL_FORMS':u'0',
				'form-MAX_NUM_FORMS': u'',
				'form-TOTAL_FORM_COUNT':u'1',
			}
			"""
		#coordformset = coordinline(data, prefix="coordinates")
		lists_dict = {
			'form': form,
			#'coordformset':coordformset,
			'formset': formset,
			'loggedin':True,
			'url':url,
			'flag':flag,
			#'dflag':dflag,
			'errorflag':errorflag,
			#'coordflag':coordflag,
			'clients':clients,
			'accounts':accounts,
			'client_name':client_name,
			'seller_name':seller_name,
			'pg':1,
		}
	lists_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
	return render_to_response('lists/lists.html', lists_dict, context_instance=RequestContext(request))

def skupagination(request, client_name,seller_name, pg, *args, **kwargs):
	pagination = {}
	srcitems =[]
	src_page=[]
	search_page=[]
	url = request.get_full_path()
	sku_id=0
	sku_items1=[]
	sku_items2=[]
	sku_items=[]
	profile = request.user.get_profile()
	clients = profile.managed_clients()
	sku_id = request.GET.get('sku_id')
	try:
		medium = request.GET.get('medium', 'cc')
		items_per_page =20
		if sku_id:
			try:
				sku_items1 = SellerRateChart.objects.select_related('id', 'product' ,'sku').filter(Q(id__icontains = sku_id)|Q(sku__icontains=sku_id))
				for i in sku_items1:
					sku_items.append(i)
			except:
				pass
			k = Product.objects.filter(title__icontains= sku_id)
			for i in k:
				sku_items2 = SellerRateChart.objects.select_related('id', 'product', 'sku').filter(Q(product=i))
				for j in sku_items2:
					sku_items.append(j)	
			paginator = Paginator(sku_items, items_per_page)
		else:
			srcitems = []
			#srcitems = SellerRateChart.objects.filter()
			paginator = Paginator(srcitems, items_per_page)
		try:
			page = int(request.GET.get('page',1))
		except ValueError:
			page=1
		base_url=request.get_full_path()
		page_pattern = re.compile('[&?]page=\d+')
		base_url = page_pattern.sub('', base_url)
		if base_url.find('?')==-1:
			base_url = base_url+'?'
		else:
			base_url = base_url+'&'
		pagination = getPaginationContext(page, paginator.num_pages, base_url)

		try:
			src_page = paginator.page(page)
		except(emptyPage, InvalidPage):
			src_page = paginator.page(paginator.num_pages)
	except Exception, e:
		log.exception('Exception while rendering items %s' % repr(e))


	# inital pagination of all items
	"""try:
		#page_no = int (request.GET.get('page',1))
		#print "page-no", page_no
		medium = request.GET.get('medium', 'cc')
		items_per_page = 20
		srcitems = SellerRateChart.objects.filter()
		#print "srcitems ----------------------------------", srcitems
		paginator = Paginator (srcitems, items_per_page)
		try:
			page = int(request.GET.get('page', 1))
		except ValueError:
			page =1
	
		base_url = request.get_full_path()
		page_pattern = re.compile('[&?]page=\d+')
		base_url = page_pattern.sub('', base_url)
		if base_url.find('?') == -1:
			base_url = base_url + '?'
		else:
			base_url = base_url + '&'
		pagination = getPaginationContext(page, paginator.num_pages, base_url)
	
		try:
			src_page = paginator.page(page)
			print "src_page------------------------------", src_page
		except (EmptyPage, InvalidPage):
			src_page = paginator.page(paginator.num_pages)
			print "src_page------------------------------------------------------------------------", src_page
	except Exception, e:
		log.exception('Exception while rendering items %s' % repr(e))
		"""
		
	skupage_dict ={
		'pagination':pagination,
		#'search_pagination':search_pagination,
		'loggedin': True,
		'srcitems': src_page,
		#'searchitems':search_page,
		'client_name':client_name,
		'seller_name':'all-sellers',
		'clients':clients,
		#'sku_items':sku_items,
		#'pg':'1'
	}
	skupage_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name

	return render_to_response('lists/skupage.html', skupage_dict, context_instance=RequestContext(request))
"""def user_additems(request, client_name,seller_name, ID, *args, **kwargs):
	url = request.get_full_path()
	if request.method=="POST":
		check = request.POST.get('name', None)
		try:
			new_client_name = request.POST['user_clients']
		except:
			new_client_name= client_name
		if new_client_name != client_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-lists', None, kwargs={'client_name':new_client_name,'seller_name':'all-sellers'}))
		try:
			new_seller_name= request.POST['user_sellers']
		except:
			new_seller_name = "All Sellers"
		if new_seller_name!=seller_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None, kwargs = {'client_name':client_name, 'seller_name':new_seller_name,}))
		
		#getting ids from client_name and seller_name
	profile = request.user.get_profile()
	clients = profile.managed_clients()
	accounts = profile.managed_accounts.filter(client__slug = client_name)
	client = Client.objects.select_related('id').filter(slug=client_name)
	if client:
		client_id = client[0].id
	else:
		return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers'}))
	seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)
	
	
#pagination starts
	try:
		page_no = int (request.GET.get('page',1))
		print "page-no", page_no
		medium = request.GET.get('medium', 'cc')
		items_per_page = 20
		srcitems = SellerRateChart.objects.filter()
		print "srcitems ----------------------------------", srcitems
		paginator = Paginator (srcitems, 20)
		try:
			page = int(request.GET.get('page', 1))
		except ValueError:
			page =1
	
		base_url = request.get_full_path()
		page_pattern = re.compile('[&?]page=\d+')
		base_url = page_pattern.sub('', base_url)
		if base_url.find('?') == -1:
			base_url = base_url + '?'
		else:
			base_url = base_url + '&'
		pagination = getPaginationContext(page, paginator.num_pages, base_url)
	
		try:
			src_page = paginator.page(page)
			print "src_page------------------------------", src_page
		except (EmptyPage, InvalidPage):
			src_page = paginator.page(paginator.num_pages)
			print "src_page------------------------------------------------------------------------", src_page
	except Exception, e:
		log.exception('Exception while rendering order history: %s' % repr(e))
		

	if request.method == "POST":#If the form has been submitted
		form = ListItemForm(request.POST,prefix="listitem")
		if form.is_valid():
			#form.save()
			listobj = List.objects.filter(id=ID)
			obj = ListItem()
			obj.list = listobj[0]
			obj.sku = form.cleaned_data['sku']
			obj.sequence = form.cleaned_data['sequence']
			obj.user_description = form.cleaned_data['user_description']
			obj.user_title = form.cleaned_data['user_title']
			obj.user_features = form.cleaned_data['user_features']
			obj.starts_on = form.cleaned_data['starts_on']
			obj.ends_on = form.cleaned_data['ends_on']
			obj.status = form.cleaned_data['status']
			obj.save()
			client_obj = Client.objects.get(name=client[0].name)
			list_obj = List.objects.filter(client=client_obj.id)
			lists_intro_dict = {	
			'client_name':client_name,
			'seller_name':seller_name,
			'pagination':pagination,
			'loggedin':True,
			'accounts': accounts,
			'url':url,
			'clients':clients,
			'list_objects':list_obj,
		}
			lists_intro_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
			return render_to_response('ppd/lists_intro.html', lists_intro_dict, context_instance=RequestContext(request))
		listitem_dict = {
			'form': form,
			'loggedin':True,
			#'pagination':pagination,
			#'srcitems':src_page,
			'url':url,
			'accounts':accounts,
			'clients': clients,
			'client_name':client_name,
			'seller_name':seller_name,
			'pg':1,
        }
		listitem_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name

	else: 
		form = ListItemForm(prefix = "listitem")
		client_obj = Client.objects.get(name=client[0].name)
		list_obj = List.objects.filter(client=client_obj.id)
		listitem_dict = {
			'form': form,
			'loggedin':True,
			'url':url,
			#'pagination':pagination,
			#'srcitems': src_page,
			'accounts':accounts,
			'clients':clients,
			'client_name':client_name,
			'pg':1,
			'seller_name':seller_name,
        }
	listitem_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
	return render_to_response('ppd/listitem.html', listitem_dict, context_instance=RequestContext(request))
	"""

def user_list_display(request, client_name,seller_name, ID, *args, **kwargs):
	url = request.get_full_path()
	if request.method == "POST":
		check = request.POST.get('name', None)
		try:
			new_client_name=request.POST['user_clients']
		except:
			new_client_name=client_name
		if new_client_name != client_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
		try:
			new_seller_name=request.POST['user_sellers']
		except:
			new_seller_name="All Sellers"
		if new_seller_name!=seller_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
		
	profile = request.user.get_profile()
	clients = profile.managed_clients()
	accounts = profile.managed_accounts.filter(client__slug = client_name)
	client = Client.objects.select_related('id').filter(slug=client_name)
	if client:
		client_id = client[0].id
	else:
		return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers'}))
	coordflag=0
	seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)
	client_obj = Client.objects.get(name=client[0].name)
	list_obj = List.objects.filter(client=client_obj.id)
	listobj = List.objects.get(id = ID)
	print "listobj in list display-------", listobj
	coordobj = Coordinates.objects.filter(list=listobj)
	#print "coordobj in list_display----------", coordobj
	#print coordobj[0].sequence
	if listobj.banner_type=='image_mapping':
		coordflag=1
	#print "listobj is----------", listobj
	listitemobj = ListItem.objects.filter(list = listobj)
	srcobj=[]
	for i in listitemobj:
		#print "i.sku.id-------------", i.sku.id
		src = SellerRateChart.objects.get(id=i.sku.id)
		srcobj.append(src)
	#print "srcobj----------", srcobj
	#print "listitem objects----------", listitemobj
	#for i in listitemobj:
		#print "i.sku-----------_", i.sku
		#print "i.sku.id------------_", i.sku.id
		#newobj = SellerRateChart.objects.get(id=i.sku)
		#print "newobj---------", newobj
	l = len(listitemobj)
	list_display_dict = {	
			'client_name':client_name,
			'seller_name':seller_name,
			'loggedin':True,
            'coordflag':coordflag,
			'url':url,
			'len':l,
			'srcobj':srcobj,
			'ID': ID,
			'accounts':accounts,
			'clients':clients,
			'list_objects':listobj,
			'listitemobj':listitemobj,
			'coordobj': coordobj,
		}
	list_display_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
	return render_to_response('lists/list_display.html', list_display_dict, context_instance=RequestContext(request))

def user_itemdel(request, client_name, seller_name, *args, **kwargs):
	url=request.get_full_path()
	print "url--------------", url
	if request.method=="POST":
		check = request.POST.get('name', None)
		try:
			new_client_name = request.POST['user_clients']
		except:
			new_client_name= client_name
		if new_client_name != client_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-lists', None, kwargs={'client_name':new_client_name,'seller_name':'all-sellers'}))
		try:
			new_seller_name= request.POST['user_sellers']
		except:
			new_seller_name = "All Sellers"
		if new_seller_name!=seller_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None, kwargs = {'client_name':client_name, 'seller_name':new_seller_name,}))
		
		#getting ids from client_name and seller_name
	profile = request.user.get_profile()
	clients = profile.managed_clients()
	accounts = profile.managed_accounts.filter(client__slug = client_name)
	client = Client.objects.select_related('id').filter(slug=client_name)
	if client:
		client_id = client[0].id
	else:
		return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers'}))
	seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)
	f = request.GET.get("sku")
	listid= request.GET.get("id")
	arr=[]
	k  = str(f)
	while True:
		a= k.partition(',')[0]
		b=k.partition(',')[1]
		c=k.partition(',')[2]
		arr.append(a)
		if(b):
			k=c
		else:
			break
	listobj= List.objects.get(id=listid)
	for i in arr:
		srcobj = SellerRateChart.objects.filter(sku=i)
		listitemobj=ListItem.objects.filter(list=listobj, sku=i)
		listitemobj.delete()
	client_obj = Client.objects.get(name=client[0].name)
	list_obj = List.objects.filter(client=client_obj.id)
	lists_intro_dict = {	
		'client_name':client_name,
		'seller_name':seller_name,
		'loggedin':True,
		'url':url,
		'clients':clients,
		'accounts':accounts,
		'list_objects':list_obj,
		}	
	lists_intro_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
	return render_to_response('ppd/lists_intro.html', lists_intro_dict, context_instance=RequestContext(request))

"""def user_delconfirm(request, client_name, seller_name, *args, **kwargs):
	url = request.get_full_path()
	if request.method=="POST":
		check = request.POST.get('name', None)
		try:
			new_client_name = request.POST['user_clients']
		except:
			new_client_name= client_name
		if new_client_name != client_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-lists', None, kwargs={'client_name':new_client_name,'seller_name':'all-sellers'}))
		try:
			new_seller_name= request.POST['user_sellers']
		except:
			new_seller_name = "All Sellers"
		if new_seller_name!=seller_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None, kwargs = {'client_name':client_name, 'seller_name':new_seller_name,}))
		
		#getting ids from client_name and seller_name
	profile = request.user.get_profile()
	clients = profile.managed_clients()
	accounts = profile.managed_accounts.filter(client__slug = client_name)
	client = Client.objects.select_related('id').filter(slug=client_name)
	if client:
		client_id = client[0].id
	else:
		return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers'}))
	seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)
	if request.method=="POST":
		pass
		"""

def user_mdel(request, client_name, seller_name, *args, **kwargs):
	url = request.get_full_path()
	if request.method=="POST":
		check = request.POST.get('name', None)
		try:
			new_client_name = request.POST['user_clients']
		except:
			new_client_name= client_name
		if new_client_name != client_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-lists', None, kwargs={'client_name':new_client_name,'seller_name':'all-sellers'}))
		try:
			new_seller_name= request.POST['user_sellers']
		except:
			new_seller_name = "All Sellers"
		if new_seller_name!=seller_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None, kwargs = {'client_name':client_name, 'seller_name':new_seller_name,}))
	profile = request.user.get_profile()
	clients = profile.managed_clients()
	accounts = profile.managed_accounts.filter(client__slug = client_name)
	client = Client.objects.select_related('id').filter(slug=client_name)
	if client:
		client_id = client[0].id
	else:
		return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers'}))
	seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)

	f = request.GET.get("id")
	arrlist=[]
	arritem=[]
	k  = str(f)
	while True:
		a= k.partition(',')[0]
		b=k.partition(',')[1]
		c=k.partition(',')[2]
		arrlist.append(a)
		if(b):
			k=c
		else:
			break
	for i in arrlist:
		listobj = List.objects.get(id=i)
		listitemobj=ListItem.objects.filter(list=listobj)
		arritem.append(listitemobj)
		listobj.delete()
		listitemobj.delete()
	delete_confirm_dict ={
		'client_name':client_name,
		'seller_name':seller_name,
		'loggedin':True,
		'url':url,
		'clients':clients,
		'accounts':accounts,
		'arrlist':arrlist,
		'arritem':arritem,
	}
	delete_confirm_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
	client_obj = Client.objects.get(name=client[0].name)
	list_obj = List.objects.filter(client=client_obj.id)
	lists_intro_dict = {	
		'client_name':client_name,
		'seller_name':seller_name,
		'loggedin':True,
		'url':url,
		'clients':clients,
		'accounts':accounts,
		'list_objects':list_obj,
		}	
	lists_intro_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
	return render_to_response('ppd/lists_intro.html', lists_intro_dict, context_instance=RequestContext(request))
	

def user_lists(request, client_name,seller_name,  *args, **kwargs):
	url = request.get_full_path()
	if request.method == "POST":
		check = request.POST.get('name', None)
		try:
			new_client_name=request.POST['user_clients']
		except:
			new_client_name=client_name
		if new_client_name != client_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
		try:
			new_seller_name=request.POST['user_sellers']
		except:
			new_seller_name="All Sellers"
		if new_seller_name!=seller_name:
			if check == "change":
				return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
		
	profile = request.user.get_profile()
	clients = profile.managed_clients()
	accounts = profile.managed_accounts.filter(client__slug = client_name)
	client = Client.objects.select_related('id').filter(slug=client_name)
	if client:
		client_id = client[0].id
	else:
		return HttpResponsePermanentRedirect(reverse('ppd-user-lists',None,kwargs={'client_name':profile.managed_client()[0].slug,'seller_name':'all-sellers'}))

	seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)
			
	#profile_exists, profile = profile_exists_or_not(current_seller_id)

	client_obj = Client.objects.get(name=client[0].name)
	list_obj = List.objects.filter(client=client_obj.id)
	typelist=[]
	titlelist=[]
	starts_onlist=[]
	ends_onlist=[]
	lenlist=[]
	idlist=[]
	count=0
	"""for i in list_obj:
		p=i.get_type_display()
		typelist.append(p)
		titlelist.append(i.title)
		starts_onlist.append(i.starts_on)
		ends_onlist.append(i.ends_on)
		idlist.append(i.id)
		lenlist.append(count)
		count=count+1
	print "typelist--------------", typelist
	l = len(list_obj)
	print "len-------------", l
	print "lenlist------------_", lenlist
	#print "list_obj.type---------_", list_obj[0].type
	print "list.object.type.fjngerjtgt", list_obj[0].get_type_display()
	print "list_objects.0------------", list_obj[0]
	"""
	lists_intro_dict = {	
		'client_name':client_name,
		'seller_name':seller_name,
		'loggedin':True,
		'url':url,
		'lenlist':lenlist,
		'clients':clients,
		'accounts':accounts,
		'list_objects':list_obj,
		'typelist':typelist,
		'titlelist':titlelist,
		'starts_onlist':starts_onlist,
		'ends_onlist':ends_onlist,
		'idlist':idlist,
		'len': len(list_obj),
		}
	lists_intro_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
	return render_to_response('lists/lists_intro.html', lists_intro_dict, context_instance=RequestContext(request))

@login_required   
@check_role('Reports')
def user_dashboard(request,client_name,seller_name, **kwargs):
    url = request.get_full_path()
    if 'search_trend' not in url and "from" not in url:
        return HttpResponseRedirect(url+ '?search_trend=day&source=url')
    if request.method == "POST":
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            return HttpResponsePermanentRedirect(reverse('ppd-user-dashboard',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            return HttpResponsePermanentRedirect(reverse('ppd-user-dashboard',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
    
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('ppd-user-dashboard',None,kwargs={'client_name':profile.managed_clients()[0].slug,'seller_name':'all-sellers',})) 
    
    if seller_name=='all-sellers':
        current_seller_id = 0
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('ppd-user-dashboard',None,kwargs={'client_name':client_name,'seller_name':'all-sellers',})) 

    dates = check_dates(request)
    from_date, to_date, search_trend = dates['start_date'], dates['end_date'], dates['search_trend']
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)

    # for All Sellers:
    if current_seller_id==0:
        order_items = Order.objects.using('tinla_slave').select_related('payable_amount').filter(state='confirmed', client=client_id, payment_realized_on__gte=from_date, payment_realized_on__lte=to_date+timedelta(days=1))
        #booking =   Order.objects.select_related('payable_amount').filter(state__in = ['confirmed','pending_order'], client=client_id, timestamp__gte=from_date, timestamp__lte=to_date+timedelta(days=1))
        cc_booking = Order.objects.using('tinla_slave').select_related('payable_amount').filter(Q(state='confirmed',payment_realized_on__lte=to_date+timedelta(days=1), payment_realized_on__gte=from_date)|Q(state='pending_order',timestamp__gte=from_date, timestamp__lte=to_date+timedelta(days=1)), client=client_id, medium='cc').aggregate(Sum('payable_amount'))
        web_booking = Order.objects.using('tinla_slave').select_related('payable_amount').filter(Q(state='confirmed',payment_realized_on__lte=to_date+timedelta(days=1), payment_realized_on__gte=from_date)|Q(state='pending_order',timestamp__gte=from_date, timestamp__lte=to_date+timedelta(days=1)), client=client_id, medium='web').aggregate(Sum('payable_amount'))
        store_booking = Order.objects.using('tinla_slave').select_related('payable_amount').filter(Q(state='confirmed',payment_realized_on__lte=to_date+timedelta(days=1), payment_realized_on__gte=from_date)|Q(state='pending_order',timestamp__gte=from_date, timestamp__lte=to_date+timedelta(days=1)), client=client_id, medium='store').aggregate(Sum('payable_amount'))
        booking = Order.objects.using('tinla_slave').select_related('payable_amount').filter(Q(state='confirmed',payment_realized_on__lte=to_date+timedelta(days=1), payment_realized_on__gte=from_date)|Q(state='pending_order',timestamp__gte=from_date, timestamp__lte=to_date+timedelta(days=1)), client=client_id).aggregate(Sum('payable_amount'))
        
        total_booking = 0
        
        cc_booking = cc_booking['payable_amount__sum']
        web_booking = web_booking['payable_amount__sum']
        store_booking = store_booking['payable_amount__sum']
        total_booking = booking['payable_amount__sum']

        #calculations for sales:
        cc = order_items.filter(medium='cc')
        web = order_items.filter(medium='web')
        store = order_items.filter(medium='store')
        cc_sales = cc.aggregate(Sum('payable_amount'))
        web_sales = web.aggregate(Sum('payable_amount'))
        store_sales = store.aggregate(Sum('payable_amount'))
        total_sales = order_items.aggregate(Sum('payable_amount'))
        cc_sales = cc_sales['payable_amount__sum']
        web_sales = web_sales['payable_amount__sum']
        store_sales = store_sales['payable_amount__sum']
        total_sales = total_sales['payable_amount__sum']

        #caclulating average values: 
        avg_cc_sales, avg_web_sales, avg_store_sales, avg_total_sales = 0,0,0,0
        if cc_sales:        avg_cc_sales = cc_sales/len(cc)
        if web_sales:       avg_web_sales = web_sales/len(web)
        if store_sales:     avg_store_sales = store_sales/len(store)
        if total_sales:     avg_total_sales = total_sales/len(order_items)
        passing_dict = {
            'total_sales':total_sales,'cc_sales':cc_sales,'web_sales':web_sales,'store_sales':store_sales,
            'total_orders':order_items.count(),'cc_orders':cc.count(),'web_orders':web.count(),'store_orders':store.count(),
            'avg_total_sales':avg_total_sales,'avg_cc_sales':avg_cc_sales,'avg_web_sales':avg_web_sales,'avg_store_sales':avg_store_sales,
            'total_booking':total_booking,'web_booking':web_booking,'cc_booking':cc_booking,'store_booking':store_booking,
            'url':request.get_full_path(),'acc_section':'sellers_hub_home',
            'search_trend':search_trend, 'from_date':from_date, 'to_date':to_date, 
            'loggedin':True,'accounts':accounts,'clients':clients,
            'client_name':client_name,'seller_name':seller_name, 'client_display_name':Client.objects.filter(slug=client_name)[0].name
                    }
       
    # for particular seller:
    else:
        order_items = OrderItem.objects.using('tinla_slave').select_related('order__payable_amount','seller_rate_chart__seller__id','order_state','order_client','order__payment_realized_on','order__timestamp').filter(seller_rate_chart__seller__id = current_seller_id , order__state='confirmed', order__client__id=client_id, order__payment_realized_on__gte=from_date, order__payment_realized_on__lte=to_date+timedelta(days=1))
        #booking = OrderItem.objects.select_related('order__payable_amount').filter(seller_rate_chart__seller=current_seller_id, order__state__in = ['confirmed','pending_order'], order__client=client_id, order__timestamp__gte=from_date, order__timestamp__lte=to_date+timedelta(days=1))
        booking = OrderItem.objects.using('tinla_slave').select_related('order__payable_amount','seller_rate_chart__seller__id','order_state','order_client','order__payment_realized_on','order__timestamp').filter(Q(order__state='confirmed',order__payment_realized_on__lte=to_date+timedelta(days=1), order__payment_realized_on__gte=from_date)|Q(order__state='pending_order',order__timestamp__gte=from_date, order__timestamp__lte=to_date+timedelta(days=1)),order__client=client_id, seller_rate_chart__seller__id=current_seller_id).aggregate(Sum('order__payable_amount'))
        cc_booking = OrderItem.objects.using('tinla_slave').select_related('order__payable_amount','seller_rate_chart__seller__id','order_state','order_client','order__payment_realized_on','order__timestamp').filter(Q(order__state='confirmed',order__payment_realized_on__lte=to_date+timedelta(days=1), order__payment_realized_on__gte=from_date)|Q(order__state='pending_order',order__timestamp__gte=from_date, order__timestamp__lte=to_date+timedelta(days=1)),order__client=client_id, seller_rate_chart__seller__id=current_seller_id, order__medium='cc').aggregate(Sum('order__payable_amount'))
        web_booking = OrderItem.objects.using('tinla_slave').select_related('order__payable_amount','seller_rate_chart__seller__id','order_state','order_client','order__payment_realized_on','order__timestamp').filter(Q(order__state='confirmed',order__payment_realized_on__lte=to_date+timedelta(days=1), order__payment_realized_on__gte=from_date)|Q(order__state='pending_order',order__timestamp__gte=from_date, order__timestamp__lte=to_date+timedelta(days=1)),order__client=client_id, seller_rate_chart__seller__id=current_seller_id,order__medium='web').aggregate(Sum('order__payable_amount'))
        store_booking = OrderItem.objects.using('tinla_slave').select_related('order__payable_amount','seller_rate_chart__seller__id','order_state','order_client','order__payment_realized_on','order__timestamp').filter(Q(order__state='confirmed',order__payment_realized_on__lte=to_date+timedelta(days=1), order__payment_realized_on__gte=from_date)|Q(order__state='pending_order',order__timestamp__gte=from_date, order__timestamp__lte=to_date+timedelta(days=1)),order__client=client_id, seller_rate_chart__seller__id=current_seller_id,order__medium='store').aggregate(Sum('order__payable_amount'))
  
        oi = []
        for d in order_items:
            if d.order not in oi:
                oi.append(d.order)

        # calculations for bookings:
        total_booking = 0
        total_sales_booking = booking
        
        cc_booking = cc_booking['order__payable_amount__sum']
        web_booking = web_booking['order__payable_amount__sum']
        store_booking = store_booking['order__payable_amount__sum']
        total_booking = total_sales_booking['order__payable_amount__sum']

        #calculations for sales:
        cc = order_items.filter(order__medium='cc')
        web = order_items.filter(order__medium='web')
        store = order_items.filter(order__medium='store')
        cc_sales = cc.aggregate(Sum('order__payable_amount'))
        web_sales = web.aggregate(Sum('order__payable_amount'))
        store_sales = store.aggregate(Sum('order__payable_amount'))
        total_sales = order_items.aggregate(Sum('order__payable_amount'))
        cc_sales = cc_sales['order__payable_amount__sum']
        web_sales = web_sales['order__payable_amount__sum']
        store_sales = store_sales['order__payable_amount__sum']
        total_sales = total_sales['order__payable_amount__sum']

        #caclulating average values: 
        avg_cc_sales, avg_web_sales, avg_store_sales, avg_total_sales = 0,0,0,0
        if cc_sales:        avg_cc_sales = cc_sales/len(cc)
        if web_sales:       avg_web_sales = web_sales/len(web)
        if store_sales:     avg_store_sales = store_sales/len(store)
        if total_sales:     avg_total_sales = total_sales/len(order_items)
        o1 = []
        for d in cc:
            if d.order not in o1:
                o1.append(d.order)
        o2 = []
        for d in web:
            if d.order not in o2:
                o2.append(d.order)
        o3 = []
        for d in store:
            if d.order not in o3:
                o3.append(d.order)
        passing_dict = {
            'total_sales':total_sales,'cc_sales':cc_sales,'web_sales':web_sales,'store_sales':store_sales,
            'total_orders':len(oi),'cc_orders':len(o1),'web_orders':len(o2),'store_orders':len(o3),
            'avg_total_sales':avg_total_sales,'avg_cc_sales':avg_cc_sales,'avg_web_sales':avg_web_sales,'avg_store_sales':avg_store_sales,
            'total_booking':total_booking,'web_booking':web_booking,'cc_booking':cc_booking,'store_booking':store_booking,
            'url':request.get_full_path(),'acc_section':'sellers_hub_home',
            'search_trend':search_trend, 'from_date':from_date, 'to_date':to_date, 
            'loggedin':True,'accounts':accounts,'clients':clients,
            'client_name':client_name,'seller_name':seller_name, 'client_display_name':Client.objects.filter(slug=client_name)[0].name
                    }
    return render_to_response('ppd/dashboard.html',passing_dict, context_instance=RequestContext(request))

@login_required
@check_role('Catalog')
def user_products(request,client_name,seller_name,*args, **kwargs):
    if request.method == "POST":
        check = request.POST.get('name', None)
        new_client_name = request.POST.get('user_clients',None)
        new_seller_name = request.POST.get('user_sellers',None)
        if new_client_name:
            return HttpResponsePermanentRedirect(reverse('ppd-user-products',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
        if new_seller_name:
            return HttpResponsePermanentRedirect(reverse('ppd-user-products',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
    
    if seller_name == 'all-sellers':
        current_seller_id = 0
    else:
        current_seller_id = Account.objects.select_related('id').filter(slug = seller_name)[0].id

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

    if current_seller_id!=0:
        account = Account.objects.get(id=current_seller_id)
        sellerratecharts = SellerRateChart.objects.select_related('product__id').filter(seller=account,product__status='active',stock_status='instock')
    else:
        sellerratecharts = SellerRateChart.objects.select_related('product__id').filter(seller__in=accounts,product__status='active',stock_status='instock')
    products = []
    product_ids = [s.product.id for s in sellerratecharts]
    product_context = create_context_for_search_results(product_ids, request)
    products_dict = {
        'products': product_context,
        'loggedin': True,
        'client_name':client_name,
        'seller_name':seller_name,
        'accounts':accounts,
        'url':request.get_full_path(),
        'accounts':accounts,
        'clients':clients,
        'client_display_name':Client.objects.filter(slug=client_name)[0].name
        }
    return render_to_response('ppd/products.html', products_dict, context_instance=RequestContext(request))   

@login_required
@check_role('Orders')
def user_orders(request,order_state,client_name,seller_name, *args, **kwargs):
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
    
    url = request.get_full_path()
    
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    
    if 'search_trend' not in url and "from" not in url:# or "order_id" not in url:
        if "?" in url:
            return HttpResponseRedirect(url+ '&search_trend=day&source=url')
        else:
            return HttpResponseRedirect(url+ '?search_trend=day&source=url')
    
    if request.method == "POST":
        check = request.POST.get('name', None)
        new_client_name = request.POST.get('user_clients',None)
        new_seller_name = request.POST.get('user_sellers',None)
        if new_client_name:
            return HttpResponsePermanentRedirect(reverse('ppd-user-orders',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers','order_state':order_state}))
        if new_seller_name:
            return HttpResponsePermanentRedirect(reverse('ppd-user-orders',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,'order_state':order_state}))
    
    if seller_name == 'all-sellers':
        current_seller_id = 0
    else:
        current_seller_id = Account.objects.select_related('id').filter(slug = seller_name)[0].id

    client_id = Client.objects.filter(slug = client_name)[0].id
    
    account = None
    order_page_list, orders = [],[]
    order_id = 0
    order_details, orders_dict ={},{}
    valid_query_or_no_query = True
    dates = check_dates(request)
    search_trend, from_date, to_date = dates['search_trend'], dates['start_date'], dates['end_date']
    save_excel = get_excel_status(request, "excel")
    items_per_page = 20
    page = int(request.GET.get('page',1))
# sorting result in accordance with date, id or payable amount
    sort_by = request.GET.get('sortby','date_asc')
    if sort_by == 'date_asc':
        if order_state == 'confirmed':
            order_by = 'payment_realized_on'
        else:
            order_by = 'timestamp'
    elif sort_by == 'date_dsc':
        if order_state == 'confirmed':
            order_by = '-payment_realized_on'
        else:
            order_by = '-timestamp'
    elif sort_by == 'id_asc':
        order_by = 'id'
    elif sort_by == 'id_dsc':
        order_by = '-id'
    elif sort_by == 'amt_asc':
        order_by = 'payable_amount'
    elif sort_by == 'amt_dsc':
        order_by = '-payable_amount'
    else:
        order_by = 'payment_realized_on'
        sort_by = 'date_asc'

    url = request.get_full_path()
    if "sortby=date_asc" in url:
        url = url.replace("&sortby=date_asc", "")
    elif "sortby=date_dsc" in url:
        url = url.replace("&sortby=date_dsc", "")
    elif "sortby=id_asc" in url:
        url = url.replace("&sortby=id_asc", "")
    elif "sortby=id_dsc" in url:
        url = url.replace("&sortby=id_dsc", "")
    elif "sortby=amt_asc" in url:
        url = url.replace("&sortby=amt_asc", "")
    elif "sortby=amt_dsc" in url:
        url = url.replace("&sortby=amt_dsc", "")

# fetching required data from database
    order_id = request.GET.get('order_id', None)
    if order_id:
        from_date = datetime.datetime.now()
        to_date = from_date
        if current_seller_id !=0:
            order_items = Order.objects.using('tinla_slave').select_related('support_state','payable_amount','timestamp','confirming_timestamp', 'orderitem__seller_rate_chart__seller').filter((Q(id=order_id) | Q(reference_order_id=order_id)),orderitem__seller_rate_chart__seller = current_seller_id, client=client_id, support_state=order_state)
        else:
            order_items = Order.objects.using('tinla_slave').select_related('support_state','payable_amount','timestamp','confirming_timestamp', 'orderitem__seller_rate_chart__seller').filter(Q(id=order_id) | Q(reference_order_id=order_id),client=client_id, support_state=order_state)
    else:
        if current_seller_id!=0:
            if order_state == 'confirmed':
                order_items = Order.objects.using('tinla_slave').select_related('support_state','payable_amount','timestamp','confirming_timestamp', 'orderitem__seller_rate_chart__seller').filter(support_state=order_state, confirming_timestamp__gte=from_date,confirming_timestamp__lte=to_date+timedelta(days=1), orderitem__seller_rate_chart__seller=current_seller_id,client=client_id).distinct().order_by(order_by)
            else:
                order_items = Order.objects.using('tinla_slave').select_related('support_state','payable_amount','timestamp','confirming_timestamp', 'orderitem__seller_rate_chart__seller').filter(support_state=order_state, timestamp__gte=from_date,timestamp__lte=to_date+timedelta(days=1), orderitem__seller_rate_chart__seller=current_seller_id, client=client_id).distinct().order_by(order_by)
        else:
            if order_state == 'confirmed':
                order_items = Order.objects.using('tinla_slave').select_related('support_state','payable_amount','timestamp','confirming_timestamp').filter(support_state=order_state, confirming_timestamp__gte=from_date, confirming_timestamp__lte=to_date+timedelta(days=1), client=client_id).distinct().order_by(order_by)            
            else:
                order_items = Order.objects.using('tinla_slave').select_related('support_state','payable_amount','timestamp','confirming_timestamp').filter(support_state=order_state, timestamp__gte=from_date,timestamp__lte=to_date+timedelta(days=1), client=client_id).distinct().order_by(order_by)

# export this report as excel        
    if save_excel == True:
        excel_header = ['Customer Name', 'Customer Phone', 'Order ID.', 'Transaction No.', 'Payment Notes','Order Date','Seller', 'Item Title','Item Qty', 'MRP','Offer Price','Discount', 'Order Amount','Booking Agent', 'Confirming Agent', 'Delivery Notes', 'Gift Notes', 'Payment Mode', 'Delivery Address','City', 'Pincode']
        excel_data = []
        for order in order_items:
            for item in order.orderitem_set.all():
                dinfo = DeliveryInfo.objects.get(order=order)
                if dinfo and dinfo.address:
                    selected_client = Client.objects.get(id=client_id)
                    if order_state == 'confirmed':
                        excel_data.append([dinfo.address.first_name+ ' ' + dinfo.address.last_name, dinfo.address.phone, order,item.transaction_no(),item.payment_notes(), item.order.payment_realized_on, item.seller_rate_chart.seller.name,item.item_title,item.qty,int(item.list_price),int(item.sale_price),int(item.list_price)-int(item.sale_price),int(item.order.payable_amount),item.order.booking_agent, item.order.confirming_agent,item.delivery_notes(),item.gift_notes(),item.order.payment_mode,dinfo.address.address,dinfo.address.city,dinfo.address.pincode])
                    else:
                        excel_data.append([dinfo.address.first_name+ ' ' + dinfo.address.last_name, dinfo.address.phone, item.order.get_id(),item.transaction_no(),item.payment_notes(), item.order.timestamp, item.seller_rate_chart.seller.name,item.item_title,item.qty,int(item.list_price),int(item.list_price)-int(item.sale_price),int(item.order.payable_amount),item.order.booking_agent, item.order.confirming_agent,item.delivery_notes(),item.gift_notes(),item.order.payment_mode,dinfo.address.address,dinfo.address.city,dinfo.address.pincode])
            
        return save_excel_file(excel_header, excel_data)

    orders_dict = {
        'valid_query_or_no_query':valid_query_or_no_query,
        'search_trend':search_trend,
        'from_date':from_date,
        'to_date':to_date,
        'cid':client_id,
        'sid':current_seller_id,
        'loggedin':True,
        'clients':clients,
        'accounts':accounts,
        'client_name':client_name,
        'seller_name':seller_name,
        'order_state':order_state,
        'orders':order_items,
            }
    selected_client = Client.objects.get(id=client_id)
    if utils.is_ezoneonline(selected_client) or utils.is_future_ecom(selected_client):
        client_type = True
    else:
        client_type = False
    if 'page='+str(page)+'&' in url:
        url = url.replace('page='+str(page),'')
    orders_dict['url'] = url
    orders_dict['sortby'] = sort_by
    orders_dict['client_type'] = client_type
    orders_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
    orders_dict['order_page_list']=order_page_list
    return render_to_response('ppd/orders.html',orders_dict, context_instance=RequestContext(request))   

       
def sellers_from_clients(request):
    client_id = request.GET['client_id']
    #canvas_page = request.GET['canvas_page']
    acc_section = request.GET['acc_section']
    acc_section_type = request.GET.get('acc_section_type','')
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = account.client.id)
        cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
    selected_account = accounts[0]
    seller_dict = {
        'clients':clients,   
        'accounts':accounts, 
        'acc_section':acc_section,
        'acc_section_type':acc_section_type,
        'selected_account': selected_account,
    }
    return render_to_response("ppd/client_account_display.html", seller_dict, context_instance = RequestContext(request))

def profile_exists_or_not(account):
    try:
        profile = Profile.objects.get(acquired_through_account = account)
        return True, profile
    except:
        return False, ''

def login_result(login_form, account):
    if login_form.is_valid():
        username = login_form.cleaned_data.get('username', '')
        password = login_form.cleaned_data.get('password','')
        new_password = login_form.cleaned_data.get('new_password', '')
        confirm_password = login_form.cleaned_data.get('confirm_password', '')
        error = ''
        user = ''
        profile_exists, profile = profile_exists_or_not(account)
        if profile_exists:
            if new_password:
                if not username:
                    error = 'Please enter username'
                elif not password:
                    error = 'Please enter password'
                elif not confirm_password:
                    error = 'Please confirm password'
                elif new_password != confirm_password:
                    error = 'New password and confirm password entries do not match'
                elif profile.user.username != username:
                    error = 'Entered username does not belong to this account'
                elif not profile.user.check_password(password):
                    error = 'Please enter the correct password for this entry'
                else:
                    profile.user.set_password(new_password)
                    profile.user.save()

        else:
            if password:
                if not username:
                    error = 'Please enter username'
                elif not password:
                    error = 'Please enter password'
                elif not confirm_password:
                    error = 'Please confirm password'
                elif password != confirm_password:
                    error = 'Password and confirm password entries do not match'
                else:
                    is_new, u, has_password = is_new_user(username)
                    if not is_new:
                        error = 'This username already exists for another user. Please enter a different username'
                    else:
                        input_type = False
                        if utils.is_valid_email(username):
                            input_type = "email"
                        elif utils.is_valid_mobile(username):
                            input_type = "mobile"
                        else:
                            input_type = "id"
                        if input_type == 'id':
                            error = 'Please enter a valid Email / Mobile'
                        else:
                            user, profile = utils.get_or_create_user(username, '', password)
                            profile.full_name = account.name
                            profile.acquired_through_account = account
                            profile.save()
        return error,user,profile

@login_required
@check_role('Profile')
def user_profile(request,client_name, seller_name, *args, **kwargs):
    url = request.get_full_path()
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
        
    clients = cache.get('clients')
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients',clients,1800)

    if request.method == "POST":
        new_client_name = request.POST.get('user_clients',None)
        new_seller_name = request.POST.get('user_sellers',None)
        if new_client_name:
            accounts = cache.get('accounts-'+new_client_name + str(request.user.id))
            if not accounts:
                accounts = profile.managed_accounts.filter(client__slug = client_name)
                cache.set('accounts-'+new_client_name+str(request.user.id),accounts,1800)
            return HttpResponsePermanentRedirect(reverse('ppd-user-profile',None,kwargs={'client_name':new_client_name,'seller_name':slugify(accounts[0].name),}))
        if new_seller_name:
            if new_seller_name == 'all-sellers':
                return HttpResponsePermanentRedirect(reverse('ppd-user-profile',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),}))
            else:
                return HttpResponsePermanentRedirect(reverse('ppd-user-profile',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
    
    if seller_name == 'all-sellers':
        return HttpResponsePermanentRedirect(reverse('ppd-user-profile',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),}))
    else:
        current_seller_id = Account.objects.select_related('id').filter(slug = seller_name)[0].id

    client_id = Client.objects.filter(slug = client_name)[0].id
    account = Account.objects.get(id=current_seller_id)
    profile_exists, profile = profile_exists_or_not(current_seller_id)
    if request.method == "POST":
        login_form = SellerLoginForm(request.POST, prefix = "login")
        login_form_error, user, profile = login_result(login_form, account)
        form = SellerProfileForm(request.POST, instance=account, prefix="profile")
        if form.is_valid():
            form.save()
        profile_dict = {
            'form': form,
            'accounts':accounts,
            'form_errors': form.errors,
            'login_form': login_form,
            'login_form_error': login_form_error,
            'profile_exists': profile_exists,
            'client_name':client_name,
            'seller_name':seller_name,
            'loggedin':True,
            'clients':clients,
            'url':url,
        }
        profile_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
        return render_to_response('ppd/profile.html', profile_dict, context_instance=RequestContext(request))
    
    else: #If the form has not been submitted 
        form = SellerProfileForm(instance = account, prefix="profile")
        login_form = SellerLoginForm(prefix="login")
        profile_dict = {
            'form': form,
            'accounts':accounts,
            'login_form': login_form,
            'profile_exists': profile_exists,
            'loggedin':True,
            'url':url,
            'clients':clients,
            'client_name':client_name,
            'seller_name':seller_name,
        }

        profile_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
        return render_to_response('ppd/profile.html', profile_dict, context_instance=RequestContext(request))


def create_formfield(field):
    if field.name == "payment_delivery_address":
        return field.formfield(widget = forms.Textarea(attrs={'rows':4}))
    else:
        return field.formfield()

@login_required
@check_role('Profile')
def user_notification(request,client_name, seller_name, *args, **kwargs):
    client_name = slugify(client_name)
    seller_name = slugify(seller_name)
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name',None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ppd-user-notifications',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ppd-user-notifications',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
        
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('ppd-user-notifications',None,kwargs={'client_name':profile.managed_clients[0].slug,'seller_name':'all-sellers',})) 
    
    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('ppd-user-notifications',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),})) 
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('ppd-user-profile',None,kwargs={'client_name':client_name,'seller_name':'all-sellers',})) 
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    account = Account.objects.get(id=current_seller_id)
    from django.forms.formsets import formset_factory
    try:
        notification_queryset = NotificationSettings.objects.filter(account = account)
    except:
        notification_queryset = None
    new_fields = False
    if notification_queryset:
        SellerNotificationFormSet = modelformset_factory(NotificationSettings,
        extra = 0,
        fields = ("event", "on_primary_email", "on_secondary_email", "on_primary_phone", "on_secondary_phone")
        )
    else:
        SellerNotificationFormSet = modelformset_factory(NotificationSettings,
        extra = 3,
        fields = ("event", "on_primary_email", "on_secondary_email", "on_primary_phone", "on_secondary_phone")
        )

    if request.method == "POST":#If the form has been submittedi
        if check != "change":
            formset = SellerNotificationFormSet(request.POST)
            for form in formset.forms:
                if form.is_valid():
                    formtemp=form.save(commit=False)
                    formtemp.account= account
                    formtemp.save()
            notification_dict = {
                'formset': formset,
                'new_fields':new_fields,
                'clients':clients,
                'accounts':accounts,
                'loggedin':True,
            }
            notification_dict['url']=url
            notification_dict['seller_name']=seller_name
            notification_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
            notification_dict['client_name']=client_name
            if check != "change":
                return render_to_response('ppd/notification.html', notification_dict, context_instance=RequestContext(request))
        
    else: #If the form has not been submitted 
        if notification_queryset:
            formset = SellerNotificationFormSet(queryset=notification_queryset)
        else:
            formset = SellerNotificationFormSet(queryset=NotificationSettings.objects.none(), initial = [{"event":'general'},{"event":'pending_order_event'},{"event":'order_confirmed_event'}])
        new_fields = True
        notification_dict = {
            'formset': formset,
            'new_fields':new_fields,
            'loggedin':True,
            'clients':clients,
            'accounts':accounts,
        }
        notification_dict['seller_name']=seller_name
        notification_dict['client_name']=client_name
        notification_dict['url']=url
        notification_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
        return render_to_response('ppd/notification.html', notification_dict, context_instance=RequestContext(request))

def get_pay_dict(request, client_id, user_dict):
    payment_options = PaymentOption.objects.select_related('payment_mode').filter(client=client_id).order_by('-is_active')
    domain_payment_options_list = []
    client_domains = None
    if request.get_full_path().count('/payment/options'):
        payment_options = payment_options.filter(is_active=True)
        client_domains = ClientDomain.objects.filter(client=client_id,is_channel=1)
        domain_payment_options = DomainPaymentOptions.objects.select_related('client_domain', 'payment_option').filter(client_domain__in=client_domains, payment_option__in=payment_options, payment_option__is_active=True)

        for po in payment_options:
            for cd in client_domains:
                for dpo in domain_payment_options:
                    if dpo.payment_option == po and dpo.client_domain == cd:
                        domain_payment_options_list.append(dpo)
    user_temp_dict = {
                'payment_options':payment_options,
                'client_domains':client_domains, #client_domains,
                'domain_payment_options_list':domain_payment_options_list,
                'request':request,
        }   
    return user_temp_dict

@login_required
@check_role('Payment')
def payment_options(request, client_name, seller_name, *args, **kwargs):
    url = request.get_full_path()
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
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ppd-user-payment-options',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ppd-user-payment-options',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('ppd-user-payment-options',None,kwargs={'client_name':profile.managed_clients[0].slug,'seller_name':'all-sellers',})) 
    
    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('ppd-user-payment-options',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),})) 
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('ppd-user-payment-options',None,kwargs={'client_name':client_name,'seller_name':'all-sellers',})) 
    
    user_dict = get_user_dict(request, "payments", *args, **kwargs)
    user_dict.update(get_pay_dict(request,client_id, user_dict))
    user_dict['client_id'] = client_id
    user_dict['client_name']=client_name
    user_dict['seller_name']=seller_name
    user_dict['url']=url
    user_dict['accounts']=accounts
    user_dict['clients']=clients
    user_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name       
    return render_to_response('ppd/settings_on_off_display.html', user_dict, context_instance=RequestContext(request))

@login_required
@check_role('Payment')
def payment_settings(request,client_name, seller_name,  *args, **kwargs):
    url = request.get_full_path()
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
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ppd-user-payment-settings',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ppd-user-payment-settings',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
    #getting ids from client_name and seller_name
    client = Client.objects.filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('ppd-user-payment-settings',None,kwargs={'client_name':profile.managed_clients[0].slug,'seller_name':'all-sellers',})) 
    
    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('ppd-user-payment-settings',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),})) 
    else:
        seller = Account.objects.filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('ppd-user-payment-settings',None,kwargs={'client_name':client_name,'seller_name':'all-sellers',})) 
    user_dict = get_user_dict(request, "payments", *args, **kwargs)
    pdict = get_pay_dict(request, client_id, user_dict)
    user_dict.update(pdict)
    products_dict = {}
    products_dict.update(user_dict)
    products_dict['client_name']=client_name
    products_dict['client_id']=client_id
    products_dict['seller_name']=seller_name
    products_dict['clients']=clients
    products_dict['accounts']=accounts
    products_dict['url']=url
    products_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name       
    return render_to_response('ppd/settings.html', products_dict, context_instance=RequestContext(request))

def edit_deposit_option(request):
    if request.method == "POST":
        deposit_po = DepositPaymentOptions.objects.get(id=request.POST['dpo_id'])
        deposit_form = get_payment_options_form_obj(request, deposit_po)
        form = deposit_form['form']
        errors=None
        if form.errors:
            errors = form.errors
        else:
            form.save()
        deposit_options = DepositPaymentOptions.objects.filter(client=deposit_po.client,
            payment_mode=deposit_po.payment_mode)
        option = DepositPaymentOptions(client=deposit_po.client,
                  payment_mode=deposit_po.payment_mode)
        po_form = get_payment_options_form_obj(request, option)
        return render_to_response('ppd/deposit_form.html',
            {'po_form':po_form,
              'deposit_options':deposit_options,
              'errors':errors,
            },
            context_instance=RequestContext(request))
    else:
        deposit_po = DepositPaymentOptions.objects.get(id=request.GET['id'])
        deposit_form = get_payment_options_form_obj(request, deposit_po)
        return render_to_response('ppd/forms/deposit_payment_form.html',
                {'po_form':deposit_form, 
                },
                context_instance=RequestContext(request))
                

@login_required
def payment_form_fields(request, *args, **kwargs):
    if request.method == "POST":
        form_id = request.POST['form_pm']
        pm = form_id.split('_')[0]
        client_id = int(form_id.split('_')[1])
        client = Client.objects.get(id=client_id)
        deposit_options = None
        payment_mode = PaymentMode.objects.filter(code=pm)
        payment_mode = payment_mode[0]
        if payment_mode.code in ('deposit-transfer'):
            option = DepositPaymentOptions(client=client,
                    payment_mode=payment_mode)
            po_form = get_payment_options_form_obj(request, option)
            form = po_form['form']
            errors=None
            if form.errors:
                errors = form.errors
            else:
                form.save()
                try:
                    po = PaymentOption.objects.get(payment_mode=payment_mode,
                            client=client)
                except:
                    PaymentOption(payment_mode=payment_mode,
                            client=client).save()
            deposit_options = DepositPaymentOptions.objects.filter(client=client,
                    payment_mode=payment_mode)
            return render_to_response('ppd/deposit_form.html',
                {'po_form':po_form,
                 'deposit_options':deposit_options,
                 'errors':errors,
                },
                context_instance=RequestContext(request))
        else:
            try:
                option = PaymentOption.objects.get(client=client,
                    payment_mode=payment_mode)
            except:
                option = PaymentOption(client=client, payment_mode=payment_mode)
        form_obj = get_payment_options_form_obj(request, option)
        if form_obj['type']!= 'empty':
            form = form_obj['form']
            if form.errors:
                return HttpResponse(simplejson.dumps(dict(status="error",
                    errors=form.errors)))
            else:
                form.save()
        else:
            form.save()
        return HttpResponse(simplejson.dumps(dict(status='ok')))
    else:
        code = request.GET['pm_id']
        pm = PaymentMode.objects.filter(code=code)
        pm = pm[0]
        client_id = request.GET['cid']
        client = Client.objects.get(id=client_id)
        html = 'ppd/settings_mode_display.html'
        if code in ('deposit-transfer'):
            html='ppd/deposit_form.html'
            po_form = None
            option_dt = DepositPaymentOptions.objects.filter(client=client,
                        payment_mode=pm)
            option = DepositPaymentOptions(client=client, payment_mode=pm)
            po_form = get_payment_options_form_obj(request, option)
            return render_to_response(html,
                {'po_form':po_form,
                 'deposit_options':option_dt,
                },
                context_instance=RequestContext(request))
        try:
            option = PaymentOption.objects.get(client=client, payment_mode = pm) 
        except PaymentOption.DoesNotExist:
            option = PaymentOption(client=client, payment_mode = pm)
        form_obj = get_payment_options_form_obj(request, option)
        return render_to_response(html,
                {'po_form':form_obj,
                }, 
                context_instance=RequestContext(request))

@login_required
@check_role('Catalog')
def user_reviews(request,client_name, seller_name, status, *args, **kwargs):
    sku = request.GET.get('sku',None)
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

    from django.db.models import Q
    client_name = slugify(client_name)
    seller_name = slugify(seller_name)
    url = request.get_full_path()
    if 'search_trend' not in url and "from" not in url and not sku:
        if "?" in url:
            return HttpResponseRedirect(url+ '&search_trend=day&source=url')
        else:
            return HttpResponseRedirect(url+ '?search_trend=day&source=url')

    if request.method == "POST":
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            return HttpResponsePermanentRedirect(reverse('ppd-user-reviews',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers','status':status}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            return HttpResponsePermanentRedirect(reverse('ppd-user-reviews',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),'status':status}))
    
        
    #getting ids from client_name and seller_name
    client = Client.objects.filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('ppd-user-reviews',None,kwargs={'client_name':clients[0].slug,'seller_name':'all-sellers','status':status})) 
    
    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('ppd-user-reviews',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),'status':status})) 
    else:
        seller = Account.objects.filter(slug=seller_name, client__slug=client_name) 
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('ppd-user-reviews',None,kwargs={'client_name':client_name,'seller_name':'all-sellers','status':status})) 
    
    dates = check_dates(request)
    from_date, to_date, search_trend = dates['start_date'], dates['end_date'], dates['search_trend']
    accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = client_id)
        cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
    #search by skuid    
    if sku:
        srcs = SellerRateChart.objects.filter(sku=sku)
        rcs_prods = srcs.values_list('product', flat=True).distinct()
        rcs_prods = list(rcs_prods)
        product_reviews = Review.objects.filter(product__in = rcs_prods, rate_chart__seller=current_seller_id).order_by('-reviewed_on')
        print rcs_prods, current_seller_id
        from_date = to_date
    else:    
        if status=='pending' or status=='new':
            product_reviews = Review.objects.filter(
                rate_chart__seller__id=current_seller_id, 
                rate_chart__seller__client=client_id,
                reviewed_on__gte=from_date, reviewed_on__lte=to_date+timedelta(days=1)).order_by('-reviewed_on')
        else:
            product_reviews = Review.objects.filter(
                rate_chart__seller__id=current_seller_id, 
                rate_chart__seller__client=client_id,
                reviewed_on__gte=from_date, reviewed_on__lte=to_date+timedelta(days=1)).order_by('-modified_on')
    if "&status=approved" in url:
        url=url.replace("&status=approved", "")
    if "&status=pending" in url:
        url=url.replace("&status=pending", "")
    if "&status=flagged" in url:
        url=url.replace("&status=flagged", "")
    new, approved, rejected, flagged = None, None, None, None
    if product_reviews:
        new = product_reviews.filter(status='new')
        approved = product_reviews.filter(status='approved')
        rejected = product_reviews.filter(status='removed')
        flagged = product_reviews.filter(status='flagged')
        product_reviews = product_reviews.filter(status=status)
    product_reviews_dict = {
                            'url':url,
                            'status':status, 
                            "product_reviews":product_reviews,
                            "total_reviews":len(product_reviews),
                            'client_name':client_name,
                            'seller_name':seller_name,
                            'search_trend':search_trend,
                            'from_date':from_date,
                            'to_date':to_date,
                            'loggedin':True,
                            'clients':clients,
                            'client_display_name':Client.objects.filter(slug=client_name)[0].name,
                            'accounts':accounts,
                            'new':new,
                            'approved':approved,
                            'rejected':rejected,
                            'flagged':flagged, 
                            'page':(int(request.GET.get('page',1))-1),
                            'sku':sku
                            }
    
    return render_to_response('reviews/approval.html', product_reviews_dict, context_instance=RequestContext(request))

def approve_or_disapprove_review(request):
    from datetime import datetime
    review_id = request.POST['on_id']
    on_or_off = request.POST['on_or_off']
    url = request.POST['url']
    review = Review.objects.get(id=review_id)
    if on_or_off == 'on':
        review.status='approved'
    if on_or_off == 'off':
        review.status = 'removed'
    if on_or_off == 'flag':
        review.status = 'flagged'
    review.modified_on = datetime.now()
    review.reviewed_by = utils.get_user_profile(request.user).full_name
    review.save()
    return HttpResponseRedirect(url)

def get_seller_payout_and_process(seller, month, year):
    c = calendar.monthrange(int(year),int(str(month)))
    last_day = c[1]
    gte_date = '%s-%s-01' % (str(year),str(month))
    lte_date = '%s-%s-%s' % (str(year),str(month),last_day)
    order_items = OrderItem.objects.filter(seller_rate_chart__seller=seller,order__payment_realized_on__gte=gte_date,order__payment_realized_on__lte=lte_date,state__in=['confirmed','shipped','delivered',None])
    
    try:
        seller_configurations = SellerConfigurations.objects.get(seller=seller)
        percentage_commission = seller_configurations.percentage_commission
        collected_by = seller_configurations.amount_collected_by
        if collected_by == 'chaupaati':
            pass
        else:
            pass
        #calculate transfer price based on percentage commission
        configurations = Configurations.objects.all()
        service_tax = configurations[0].service_tax / Decimal("100")
    except:
        return None
    #payout components
    total_sale_price = Decimal(0)
    total_shipping_charges = Decimal(0)
    total_payment_gateway_charges = Decimal(0)
    chaupaati_discount = Decimal(0)
    seller_discount = Decimal(0)
    total_collected_amount = Decimal(0)
    total_applicable_amount = Decimal(0)
    commission_in_amount = Decimal(0)
    gross_payout = Decimal(0)
    chaupaati_commision_invoice = Decimal(0)
    net_payout = Decimal(0)

    seller_payout_details = SellerPayoutDetails.objects.using('default').filter(month=month,year=year,seller=seller)
    seller_payout_details.delete()

    for order_item in order_items:
        #item wise payout details
        total_sale_price += order_item.sale_price
        total_shipping_charges += order_item.shipping_charges
        discount = Decimal("%.15g" % order_item.spl_discount())
        chaupaati_discount += discount
        #seller_discount +=
        #total_payment_gateway_charges += order_item.
        payable_amount = Decimal("%.15g" % order_item.payable_amount())
        total_collected_amount += payable_amount
        total_applicable_amount += ( payable_amount + discount)
        commission_in_amount += (order_item.seller_rate_chart.transfer_price)

        #save payout details for each item
        seller_payout_details = SellerPayoutDetails()
        seller_payout_details.year = year
        seller_payout_details.month = month
        seller_payout_details.order_item = order_item
        seller_payout_details.seller = seller
        seller_payout_details.sale_price = order_item.sale_price
        seller_payout_details.shipping_charges = order_item.shipping_charges
        #seller_payout_details.gateway_charges
        seller_payout_details.chaupaati_discount = Decimal("%.15g" % order_item.spl_discount())
        #seller_payout_details.seller_discount =
        seller_payout_details.collected_amount = Decimal("%.15g" % order_item.payable_amount())
        seller_payout_details.applicable_amount = seller_payout_details.collected_amount + seller_payout_details.chaupaati_discount
        seller_payout_details.commision_amount = order_item.seller_rate_chart.transfer_price
        seller_payout_details.gross_payout = seller_payout_details.collected_amount - seller_payout_details.commission_amount
        seller_payout_details.commission_invoice_amount = seller_payout_details.commission_amount + (seller_payout_details.commission_amount * service_tax)
        seller_payout_details.net_payout = seller_payout_details.applicable_amount - seller_payout_details.commission_invoice_amount
        seller_payout_details.save()


    gross_payout = total_applicable_amount - commission_in_amount
    chaupaati_commision_invoice = commission_in_amount + (commission_in_amount * service_tax)
    net_payout = total_applicable_amount - chaupaati_commision_invoice

    #payout totals
    try:
        seller_payout = SellerPayout.objects.get(month=month,year=year,seller=seller)
        seller_payout.delete(using='default')
        seller_payout = SellerPayout()
    except:
        seller_payout = SellerPayout()
    seller_payout.seller = seller
    seller_payout.month = month
    seller_payout.year = year
    seller_payout.sale_price = total_sale_price
    seller_payout.shipping_charges = total_shipping_charges
    seller_payout.gateway_charges = total_payment_gateway_charges
    seller_payout.chaupaati_discount = chaupaati_discount
    seller_payout.seller_discount = seller_discount
    seller_payout.collected_amount = total_collected_amount
    seller_payout.applicable_amount = total_collected_amount + chaupaati_discount
    seller_payout.commission_amount = commission_in_amount
    seller_payout.gross_payout = gross_payout
    seller_payout.commission_invoice_amount = chaupaati_commision_invoice
    seller_payout.net_payout = net_payout
    seller_payout.save()
    return seller_payout

@login_required
@check_role('Payment')
def user_payouts(request,client_name, seller_name,  *args, **kwargs):
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ppd-user-payouts',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ppd-user-payouts',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
        
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('ppd-user-payouts',None,kwargs={'client_name':profile.managed_clients[0].slug,'seller_name':'all-sellers',})) 
    
    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('ppd-user-payouts',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),})) 
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('ppd-user-payouts',None,kwargs={'client_name':client_name,'seller_name':'all-sellers',})) 
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    seller = Account.objects.get(id=current_seller_id) 

    if request.method == "GET":
        payout_home_form = PayoutHomeForm() 
        month = date.today().month
        year = date.today().year
        seller_payout = get_seller_payout_and_process(seller, month, year)
        payouts_dict = {
            'payout_home_form':payout_home_form,
            'seller_payout': seller_payout,
            'month': month,
            'year': year,
            'seller': seller,
            'client_name':client_name,
            'clients':clients,
            'accounts':accounts,
            'seller_name':seller_name,
            'loggedin':True, 
            'url':request.get_full_path()
        }
        payouts_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
        return render_to_response('ppd/payouts.html', payouts_dict, context_instance=RequestContext(request))
    
    if request.method == 'POST':
        check = request.POST.get('name', None)
        if check != 'change':
            payout_home_form = PayoutHomeForm(request.POST)
            if payout_home_form.is_valid():
                month = payout_home_form.cleaned_data['month']
                year = payout_home_form.cleaned_data['year']
                seller_payout = get_seller_payout_and_process(seller, month, year)
                payouts_dict = {
                    'payout_home_form':payout_home_form,
                    'seller_payout': seller_payout,
                    'month': month,
                    'year': year,
                    'seller': seller,
                    'client_name':client_name, 
                    'seller_name':seller_name,
                    'loggedin':True,
                    'url':request.get_full_path(),
                    'clients':clients,
                    'accounts':accounts,
                }
                payouts_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
                response = render_to_response('ppd/payouts.html', payouts_dict, context_instance = RequestContext(request))
                return response
            else:
                payouts_dict = {
                    'payout_home_form':payout_home_form,
                }
                payouts_dict.update(user_dict)
                payouts_dict['cid']=client_id
                payouts_dict['sid']=current_seller_id
                payouts_dict['url']=url
                return render_to_response('ppd/payouts.html', payouts_dict, context_instance=RequestContext(request))

def ppd_booked_item_range(source, seller, from_date,to_date,request):
    qs_oi = OrderItem.objects.filter(Q(order__timestamp__gte = from_date) & Q(order__timestamp__lte = to_date))
    if seller and seller!=unicode(0):
        qs_oi = qs_oi.filter(seller_rate_chart__seller=seller)
    qs_oi = qs_oi.filter(Q(order__state = "pending_order") | Q(order__state = "confirmed"))
    return dict(qs=qs_oi)

def ppd_confirmed_item_range(source, seller, from_date,to_date,request):
    qs_oi = OrderItem.objects.filter(Q(order__payment_realized_on__gte = from_date) & Q(order__payment_realized_on__lte = to_date) & Q(order__state = "confirmed"))
    if seller and seller!=unicode(0):
        qs_oi = qs_oi.filter(seller_rate_chart__seller=seller)
    return dict(qs=qs_oi)

@login_required
@never_cache
@check_role('Pricing')
def client_pricing(request, client_name, seller_name, update_type,  *args, **kwargs):
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ppd-user-pricing',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers','update_type':update_type}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ppd-user-pricing',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,'update_type':update_type}))
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
        
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('ppd-user-pricing',None,kwargs={'client_name':profile.managed_clients[0].name,'seller_name':'all-sellers','update_type':update_type})) 
    
    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('ppd-user-pricing',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),'update_type':update_type})) 
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('ppd-user-pricing',None,kwargs={'client_name':client_name,'seller_name':'all-sellers','update_type':update_type})) 
    seller = Account.objects.get(id=current_seller_id)
    count = 0
    #Populating the required fields for rendering Seller's Hub Pages
    if update_type == 'search_by_sku':
        return search_by_sku(request,client_name, seller, client_id, current_seller_id, count, profile)
    if update_type == 'upload_xls':
        return upload_price_xls(request, client_name, seller, client_id, current_seller_id, count, profile)
    if update_type == 'approve_pricing_job':
        return approve_pricing_job(request,client_name, seller_name, seller, client_id, current_seller_id, profile)
    if update_type == 'gen_reprt':
        return generate_pricing_report(request, client_name, seller, client_id,current_seller_id, count, profile)
    if update_type == 'all_prices':
        return all_prices(request, client_name, seller, client_id,current_seller_id, count, profile)

#def all_prices(request, client_name, seller, client_id, current_seller_id, count, profile):
#    from accounts.models import Client
#    from pricing.models import Price, PriceVersion, PriceList
#    rate_chart = None
#    prices = None
#    skuid = ""
#    article_id = ""
#    searched_by = ""
#    pricelist_options = ""
#    errors = []
#    all_prices, catalog_specific_prices, anonymous_prices = None, None, None
#    delete_prices, update_prices, anonymous_update_price = [], [], []
#    updated_price, no_update_in_atg, prices_rejected = [], [], []
#    prices_approved, failed_to_update_in_atg = [], []
#    product = None
#    product_image = None
#    flag = ""
#    pricing_job_id = None
#    pricing_job = None
#    list_price, updated_list_price = None, None
#    client_pricelist_mapping = settings.CLIENT_PRICELIST_MAPPING
#    accounts = cache.get('accounts-'+str(client_id))
#    if not accounts:
#        accounts = profile.managed_accounts.filter(client__id = client_id)
#        cache.set('accounts-'+str(client_id),accounts,1800)
#    clients = cache.get('clients')
#    if not clients:
#        clients = profile.managed_clients()
#        cache.set('clients',clients,1800)
#    if_any_changes = False
#    is_pricing_tool_supported = False
#    all_valid_prices = None
#    url = ""
#    pagination = {}
#    save_excel = get_excel_status(request, "excel")
#
#    client = Client.objects.get(id = client_id)
#    is_pricing_tool_supported = utils.is_pricing_tool_supported(client)
#
#    if not is_pricing_tool_supported:
#        errors.append('Pricing tool is currently does not have support for selected client!!!')
#    else:
#        article_id = request.GET.get('articleid',None)
#        if (not article_id) and request.method == 'POST':
#            article_id = request.POST.get('articleid',None)
#        if article_id:
#            no_article_id_matching_entry = False
#            no_sku_matching_entry = False
#            try:
#                rate_chart = SellerRateChart.objects.get(article_id=article_id.strip(), seller__client__id=client_id)
#                searched_by = 'article_id'       
#            except SellerRateChart.MultipleObjectsReturned:
#                errors.append('Multiple article maintained for Articleid: %s' % article_id)
#            except SellerRateChart.DoesNotExist:
#                no_article_id_matching_entry = True
#
#            try:
#                rate_chart = SellerRateChart.objects.get(sku=article_id.strip(), seller__client__id=client_id)
#                searched_by = 'article_id'       
#            except SellerRateChart.MultipleObjectsReturned:
#                errors.append('Multiple article maintained for Articleid: %s' % article_id)
#            except SellerRateChart.DoesNotExist:
#                no_sku_matching_entry = True
#                
#            if no_article_id_matching_entry and no_sku_matching_entry:
#                errors.append('No active articles maintained for Articleid or SKU: %s' % article_id)
#
#        if rate_chart or request.method == 'POST':
#            check = request.POST.get('name', None)
#            if check != 'change':
#                treat_as_fixed_pricelists = settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL
#
#                #Client level applicable pricelists for option of adding new prices
#                client_level_applicable_pricelists = settings.CLIENT_LEVEL_APPLICABLE_PRICELISTS
#                applicable_pricelists = client_level_applicable_pricelists[seller.client.name]
#                #Now, generate the HTML dropdown code for showing dropdown menu.
#                if applicable_pricelists:
#                    for item in applicable_pricelists:
#                        pricelist_options += "<option> %s </option>" % item 
#
#                if rate_chart:
#                    flag = "searched"
#                    
#                    #First check, if there are any pending PriceVersion jobs pending for aaproval. 
#                    #If yes, then prompt error message. If no, then proceed.
#
#                    #No more checks for price versions as there is no maker-checker model now.
#                    #price_versions = PriceVersion.objects.filter(rate_chart = rate_chart, status='pending')
#                    price_versions = None
#
#                    if price_versions:
#                        errors.append('Prices pending for approval!!! First, approve/rejects those!!!')
#                        product = price_versions[0].rate_chart.product
#                        product_image = ProductImage.objects.filter(product=product)
#                        if product_image:
#                            product_image = product_image[0]
#                    else:
#                        all_prices = Price.objects.filter(
#                            rate_chart = rate_chart).exclude(
#                            Q(price_type='timed', end_time__lt=datetime.datetime.now())|
#                            Q(price_list__name__contains='Anonymous'))
#                        
#                        for price in all_prices:
#                            if price.price_list.name.__contains__(client_pricelist_mapping[client_id]):
#                                list_price = price.list_price
#                                break
#
#                        anonymous_list_price = None
#
#                        if all_prices:
#                            for price in all_prices:
#                                product = price.rate_chart.product
#                                if product:
#                                    product_image = ProductImage.objects.filter(product=product)
#
#                                if product_image:
#                                    product_image = product_image[0]
#
#                                if product and product_image:
#                                    break
#
#                            if request.POST.get("update", None) == "Update":
#                                flag = "updated"
#                                
#                                if request.POST.get('list_price',None):
#                                    list_price_str = request.POST.get('list_price')
#                                    try:
#                                        list_price_int = Decimal(str(list_price_str))
#                                        if list_price_int == Decimal('0'):
#                                            errors.append('Cannot set M.R.P. to 0!!!')
#                                    except Exception,e:
#                                        errors.append('Wrong value set for M.R.P. = %s' % list_price_str)
#                                        log.info(e)
#                                else:
#                                    errors.append('Wrong value set for M.R.P.!!!')
#
#                                for price in all_prices:
#                                    if request.POST.get("%s#offer_price" % price.id):
#                                        offer_price_str = request.POST.get("%s#offer_price" % price.id)
#                                        try:
#                                            offer_price_int = Decimal(str(offer_price_str))
#                                            if offer_price_int == Decimal('0'):
#                                                errors.append('Offer Price cannot be set to 0!!!')
#                                        except Exception,e:
#                                            errors.append('Wrong value set for Sale Price = %s' % offer_price_str)
#                                            log.info(e)
#                                    else:
#                                        errors.append('Wrong value set for Saleprice!!!')
#
#                                    if request.POST.get("%s#cashback_amount" % price.id):
#                                        cashback_amount_str = request.POST.get("%s#cashback_amount" % price.id)
#                                        try:
#                                            cashback_amount_int = Decimal(str(cashback_amount_str))
#                                        except Exception,e:
#                                            errors.append('Wrong value set for Cashback Amount = %s' % cashback_amount_str)
#                                            log.info(e)
#
#                                    if request.POST.get("%s#starts_on" % price.id):
#                                        start_time = request.POST.get("%s#starts_on" % price.id) + " "
#                                        start_time += request.POST.get("%s#starts_on#hr" % price.id) + ":"
#                                        start_time += request.POST.get("%s#starts_on#min" % price.id)
#                                        try:
#                                            start_time = datetime.datetime.strptime(start_time,'%d-%m-%Y %H:%M')
#                                        except Exception,e:
#                                            errors.append('Wrong value set for Start Time = %s' % start_time)
#
#                                    if request.POST.get("%s#ends_on" % price.id):
#                                        end_time = request.POST.get("%s#ends_on" % price.id) + " "
#                                        end_time += request.POST.get("%s#ends_on#hr" % price.id) + ":"
#                                        end_time += request.POST.get("%s#ends_on#min" % price.id)
#                                        try:
#                                            end_time = datetime.datetime.strptime(end_time,'%d-%m-%Y %H:%M')
#                                        except Exception,e:
#                                            errors.append('Wrong value set for End Time = %s' % end_time)
#                                           
#                                if not errors:
#                                    updated_list_price = request.POST.get('list_price')
#                                    if not Decimal(str(updated_list_price)) == all_prices[0].list_price:
#                                        if_any_changes = True
#
#                                    for price in all_prices:
#                                        if request.POST.get("%s#checkbox" % price.id) == "deleted":
#                                            price_info = {
#                                                'price':price,
#                                                'action':'Delete',
#                                                }
#                                            update_prices.append(price_info)
#                                            delete_prices.append(price)
#                                            if_any_changes = True
#                                        else:
#                                            offer_price_changed = False
#                                            if request.POST.get("%s#offer_price" % price.id) and not Decimal(str(request.POST.get("%s#offer_price" % price.id))) == price.offer_price:
#                                                offer_price_changed = True
#                                            
#                                            cashback_amount_changed = False
#                                            if request.POST.get("%s#cashback_amount" % price.id) and (((not price.cashback_amount) and (not request.POST.get("%s#cashback_amount" % price.id))) or (price.cashback_amount and not Decimal(str(request.POST.get("%s#cashback_amount" % price.id))) == price.cashback_amount)):
#                                                cashback_amount_changed = True
#                                            
#                                            starts_on_changed = False
#                                            starts_on = None
#                                            if request.POST.get("%s#starts_on" % price.id):
#                                                starts_on = request.POST.get("%s#starts_on" % price.id) + " "
#                                                starts_on += request.POST.get("%s#starts_on#hr" % price.id) + ":"
#                                                starts_on += request.POST.get("%s#starts_on#min" % price.id)
#                                                starts_on = datetime.datetime.strptime(starts_on,'%d-%m-%Y %H:%M')
#                                                if not starts_on == price.start_time:
#                                                    starts_on_changed = True
#
#                                            ends_on_changed = False
#                                            ends_on = None
#                                            if request.POST.get("%s#ends_on" % price.id):
#                                                ends_on = request.POST.get("%s#ends_on" % price.id) + " "
#                                                ends_on += request.POST.get("%s#ends_on#hr" % price.id) + ":"
#                                                ends_on += request.POST.get("%s#ends_on#min" % price.id)
#                                                ends_on = datetime.datetime.strptime(ends_on,'%d-%m-%Y %H:%M')
#                                                if not ends_on == price.start_time:
#                                                    ends_on_changed = True
#
#                                            if offer_price_changed or cashback_amount_changed or starts_on_changed or ends_on_changed:
#                                                price_info = {
#                                                    'price':price,
#                                                    'offer_price':request.POST.get("%s#offer_price" % price.id),
#                                                    'cashback_amount':request.POST.get("%s#cashback_amount" % price.id),
#                                                    'starts_on':starts_on,
#                                                    'ends_on':ends_on,
#                                                    'action':'Update',
#                                                    }
#                                                update_prices.append(price_info)
#                                                if_any_changes = True
#                                            else:
#                                                price_info = {
#                                                    'price':price,
#                                                    'action':'No Change',
#                                                    }
#                                                update_prices.append(price_info)
#                          
#                            elif request.POST.get("confirm") and request.POST.get("confirm") == "Confirm":
#                                flag = "confirmed"
#                                current_list_price = request.POST.get("list_price")
#                                new_list_price = request.POST.get("updated_list_price")
#                                for price in all_prices:
#                                    if request.POST.get("%s#delete_price" % price.id):
#                                        try:
#                                            price_version = set_price_version(price, 'delete', request.user.username, datetime.datetime.now())
#                                            updated_price, no_update_in_atg = approve_single_price(request, price_version, client)
#                                            if updated_price:
#                                                prices_approved.append(updated_price[0])
#                                            if no_update_in_atg:
#                                                failed_to_update_in_atg.append(no_update_in_atg[0])
#                                        except Exception, e:
#                                            prices_rejected.append(price.rate_chart.article_id)
#                                            log.info(e)
#
#                                    elif (current_list_price != new_list_price) or (request.POST.get("%s#offer_price" % price.id) and not Decimal(str(request.POST.get("%s#offer_price" % price.id))) == price.offer_price)or (request.POST.get("%s#offer_price" % price.id) and not Decimal(str(request.POST.get("%s#cashback_amount" % price.id))) == price.cashback_amount) or (request.POST.get("%s#starts_on" % price.id) and not request.POST.get("%s#starts_on" % price.id) == str(price.start_time)) or (request.POST.get("%s#ends_on" % price.id) and not request.POST.get("%s#starts_on" % price.id) == str(price.end_time)):
#                                        new_offer_price = request.POST.get("%s#offer_price" % price.id)
#                                        new_cashback_amount = request.POST.get("%s#cashback_amount" % price.id)
#                                        if not new_cashback_amount:
#                                            new_cashback_amount = '0'
#                                        
#                                        new_starts_on = None
#                                        if request.POST.get("%s#starts_on" % price.id) and request.POST.get("%s#starts_on" % price.id) != 'None':
#                                            new_starts_on = request.POST.get("%s#starts_on" % price.id)
#                                            new_starts_on = datetime.datetime.strptime(new_starts_on,'%Y-%m-%d %H:%M:%S')
#                                            
#                                        new_ends_on = None
#                                        if request.POST.get("%s#ends_on" % price.id, None) and request.POST.get("%s#ends_on" % price.id, None) != 'None':
#                                            new_ends_on = request.POST.get("%s#ends_on" % price.id)
#                                            new_ends_on = datetime.datetime.strptime(new_ends_on,'%Y-%m-%d %H:%M:%S')
#
#                                        try:
#                                            price_version = set_price_version(price, 'update', request.user.username, datetime.datetime.now(), new_list_price, new_offer_price, new_cashback_amount, new_starts_on, new_ends_on)
#                                            updated_price, no_update_in_atg = approve_single_price(request, price_version, client)
#                                            if updated_price:
#                                                prices_approved.append(updated_price[0])
#                                            if no_update_in_atg:
#                                                failed_to_update_in_atg.append(no_update_in_atg[0])
#                                        except Exception, e:
#                                            prices_rejected.append(price.rate_chart.article_id)
#                                            log.info(e)
#
#                                #Commenting show all prices code
#                                all_valid_prices = []#Price.objects.select_related('rate_chart__article_id').filter(rate_chart__seller=seller).exclude(Q(price_type='timed',end_time__lt=datetime.datetime.now())|Q(price_list__name__contains='Anonymous')).order_by('rate_chart__article_id')
#                else:
#                    errors.append('No active price maintained for this article!!!')
#                    log.info('Rate chart does not exist either for sku=%s or article_id=%s' % (skuid, article_id))
#        else:
#            #Commenting show all prices code
#            all_valid_prices = []#Price.objects.select_related('rate_chart__article_id').filter(rate_chart__seller=seller).exclude(Q(price_type='timed',end_time__lt=datetime.datetime.now())|Q(price_list__name__contains='Anonymous')).order_by('rate_chart__article_id')
#
#        if all_valid_prices:
#            if save_excel == True:
#                excel_header = ['Articleid','SKU','Product Name','Catalog','M.R.P.','Offer Price','Cashback Amount']
#                excel_data = []
#                for valid_price in all_valid_prices:
#                    excel_data.append([valid_price.rate_chart.article_id, valid_price.rate_chart.sku, valid_price.rate_chart.product.title, valid_price.price_list.name, valid_price.list_price, valid_price.offer_price, valid_price.cashback_amount])
#                
#                return save_excel_file(excel_header, excel_data)
#   
#            import re
#            page_no = request.GET.get('page',1)
#            page_no = int(page_no)
#            items_per_page = 100
#            total_results = len(all_valid_prices)
#            total_pages =int(math.ceil(Decimal(total_results)/Decimal(items_per_page)))
#
#            base_url = request.get_full_path()
#
#            page_pattern = re.compile('[&?]page=\d+')
#            base_url = page_pattern.sub('',base_url)
#            page_pattern = re.compile('[&?]per_page=\d+')
#            base_url = page_pattern.sub('',base_url)
#            if base_url.find('?') == -1:
#                base_url = base_url + '?'
#            else:
#                base_url = base_url + '&'
#            pagination = getPaginationContext(page_no, total_pages, base_url)
#
#            all_valid_prices = all_valid_prices[((page_no-1)*items_per_page):(page_no*items_per_page)]
#   
#    url = request.get_full_path()
#    prices_dict = {
#        'article_id':article_id,
#        'sku':skuid,
#        'pricelist_options':pricelist_options,
#        'all_prices':all_prices,
#        'all_valid_prices':all_valid_prices,
#        'list_price':list_price,
#        'updated_list_price':updated_list_price,
#        'searched_by':searched_by,
#        'product':product,
#        'product_image':product_image,
#        'update_prices':update_prices,
#        'delete_prices':delete_prices,
#        'if_any_changes':if_any_changes,
#        'is_pricing_tool_supported':is_pricing_tool_supported,
#        'errors':errors,
#        'flag':flag,
#        'seller_name':slugify(seller),
#        'client_name':client_name,
#	'accounts':accounts,
#        'clients':clients,
#	'url':url,
#        'loggedin':True,
#        'pagination':pagination,
#        'prices_approved':prices_approved,
#        'failed_to_update_in_atg':failed_to_update_in_atg,
#        'prices_rejected':prices_rejected,
#        }
#    
#    prices_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
#    return render_to_response('prices/all_prices.html', prices_dict, context_instance=RequestContext(request))
#
#def generate_pricing_report(request, client_name, seller, client_id, current_seller_id, count, profile):
#    from web.sbf_forms import FileUploadForm
#    import os
#    errors, message = [], None
#    all_prices = None
#    form = None
#    to_update = None
#    path_to_save = None
#    flag = None
#    accounts = cache.get('accounts-'+str(client_id))
#    if not accounts:
#        accounts = profile.managed_accounts.filter(client__id = client_id)
#        cache.set('accounts-'+str(client_id),accounts,1800)
#    clients = cache.get('clients')
#    if not clients:
#        clients = profile.managed_clients()
#        cache.set('clients',clients,1800)
#    pagination = {}
#    
#    if request.method == 'POST':
#        check = request.POST.get('name', None)
#        if check!='change':
#            flag = "report"
#            if request.POST.get("upload") == 'Generate Report':
#                import xlrd
#                form = FileUploadForm(request.POST, request.FILES)
#                if form.is_valid():
#                    path_to_save = save_uploaded_file(request.FILES['status_file'])
#                    all_prices = get_current_prices(path_to_save, seller)
#                else:
#                    errors.append('Please select the excel file and then click upload!!!')
#                    form = FileUploadForm()
#                    flag = 'new'               
#
#                #Delete the uploaded excel file
#                if path_to_save:
#                    os.remove(path_to_save)
#    else:
#        flag = "new"
#        form = FileUploadForm()
#    prices_dict = {
#	    'accounts':accounts,
#        'clients':clients, 
#        'seller_name':slugify(seller),
#        'client_name':client_name,
#        'flag':flag,
#        'forms':form,
#        'errors':errors,
#        'all_prices':all_prices,
#        'url':request.get_full_path(),
#        'loggedin':True,
#        'pagination':pagination,
#        }
#    prices_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
#    return render_to_response('prices/report.html', prices_dict, context_instance=RequestContext(request))   
#
#def get_pricing_info_for_job(job_id):
#    all_price_versions = PriceVersion.objects.filter(pricing_job__id=job_id)
#    add_price_versions = []
#    delete_price_versions = []
#    update_catalog_specific_price_versions = []
#    update_anonymous_price_versions = []
#
#    for pv in all_price_versions:
#        if pv.action == 'add':
#            add_price_versions.append(pv)
#        elif pv.action == 'delete':
#            delete_price_versions.append(pv)
#        elif pv.action == 'update':
#            if pv.price_list.name.__contains__('Anonymous'):
#                update_anonymous_price_versions.append(pv)
#            else:
#                update_catalog_specific_price_versions.append(pv)
#
#    return add_price_versions, delete_price_versions, update_catalog_specific_price_versions, update_anonymous_price_versions
#
#def xml_string_for_updating_atg_prices(price, article_id, start_time, end_time, atg_price_list):
#    xml_string = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
#    xml_string += "<array-list>"
#    xml_string += "<price-article-data xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:type=\"java:com.fb.bulkupload.csv.vo.price.PriceArticleData\">"
#    xml_string += "<display-name></display-name>"
#    if end_time:
#        xml_string += "<list-price-end-date>%s</list-price-end-date>" % datetime.datetime.strftime(end_time,'%d-%m-%Y %H:%M:%S')
#    xml_string += "<list-price>%s</list-price>" % price
#    xml_string += "<article-id>%s</article-id>" % article_id
#    if start_time:
#        xml_string += "<list-price-start-date>%s</list-price-start-date>" % datetime.datetime.strftime(start_time,'%d-%m-%Y %H:%M:%S')
#    xml_string += "<last-modified-date>%s</last-modified-date>" % datetime.datetime.strftime(datetime.datetime.now(),'%d-%m-%Y %H:%M:%S')
#    xml_string += "<base-price-list>%s</base-price-list>" % atg_price_list
#    xml_string += "</price-article-data>"
#    xml_string += "</array-list>"
#    return xml_string
#
# update_price(xml_string):
#    import urllib, urllib2
#    from django.utils import simplejson
#
#    values = {'xmlData':xml_string,"voType":"PriceArticleData"}
#    try:
#        url = '%s:%s/Future_Management/UpdateService' % (settings.ATG_PRICE_UPDATE_URL, settings.ATG_PRICE_UPDATE_PORT)
#        encoder = simplejson.JSONEncoder()
#        data = urllib.urlencode(values)
#        req = urllib2.Request(url, data)
#        res = urllib2.urlopen(req)
#        if res.getcode() == 200:
#            return True
#        else:
#            return False
#    except Exception as e:
#        return False
#
#def update_atg_price(update_dict, delete_slot_price=False):
#    update_list_price, update_offer_price = False, False
#    list_pricelist_mapping = settings.TINLA_TO_ATG_LIST_PRICELIST_MAPPING
#    atg_price_list = list_pricelist_mapping.get(update_dict['catalog'],'')
#
#    if atg_price_list:
#        xml_string = xml_string_for_updating_atg_prices(update_dict['list_price'], update_dict['article_id'], update_dict['start_time'], update_dict['end_time'], atg_price_list)
#        update_list_price = update_price(xml_string)
#    else:
#        update_list_price = True
#
#    offer_pricelist_mapping = settings.TINLA_TO_ATG_SALE_PRICELIST_MAPPING
#    atg_price_list = offer_pricelist_mapping.get(update_dict['catalog'],'')
#    #Deleting FB slot price from ATG
#    if atg_price_list == 'SlotPriceList' and delete_slot_price:
#        atg_price_list = 'DeleteSlotPriceList'
#
#    if atg_price_list:
#        xml_string = xml_string_for_updating_atg_prices(update_dict['offer_price'], update_dict['article_id'], update_dict['start_time'], update_dict['end_time'], atg_price_list)
#        update_offer_price = update_price(xml_string)
#    else:
#        update_offer_price = True
#
#    return update_list_price and update_offer_price
#
#def approve_single_price(request, price_version, selected_client):
#    from django.db.models import Q
#    pv = price_version
#    treat_as_fixed_pricelists =settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL
#    approved_by = request.user.username
#    approved_on = datetime.datetime.now()
#    start_time = approved_on
#    end_time = datetime.datetime(9999,12,31,0,0,0)
#    prices_approved, failed_to_update_in_atg = [], []
#
#    if pv.price_list.name in treat_as_fixed_pricelists:
#        if pv.action == 'add':
#            response = True
#            if utils.is_future_ecom(selected_client):
#                update_dict = {
#                     'article_id':pv.rate_chart.article_id,
#                     'list_price':pv.new_list_price,
#                     'offer_price':pv.new_offer_price,
#                     'start_time':start_time,
#                     'end_time':end_time,
#                     'catalog':pv.price_list.name,
#                     }
#                response = update_atg_price(update_dict)
#
#            if response:
#                price = Price.objects.filter(
#                    rate_chart = pv.rate_chart,
#                    price_list = pv.price_list,
#                    price_type = 'timed',
#                    start_time = start_time,
#                    end_time = end_time,
#                    )
#                if price:
#                    delete_unwanted_prices_in_same_timeslot = price[1:]
#                    price = price[0]
#                    price.list_price = pv.new_list_price
#                    price.offer_price = pv.new_offer_price
#                    price.cashback_amount = pv.new_cashback_amount
#                    price.save()
#                    prices_approved.append(price.rate_chart.article_id)
#
#                    for item in delete_unwanted_prices_in_same_timeslot:
#                        item.delete(using='default')
#                else:
#                    price = Price()
#                    price.rate_chart = pv.rate_chart
#                    price.price_list = pv.price_list
#                    price.list_price = pv.new_list_price
#                    price.offer_price = pv.new_offer_price
#                    price.cashback_amount = pv.new_cashback_amount
#                    price.price_type = 'timed'
#                    price.start_time = start_time
#                    price.end_time = end_time
#                    price.save()
#                    prices_approved.append(price.rate_chart.article_id)
#
#                pv.status = 'approved'
#            else:
#                failed_to_update_in_atg.append(pv.rate_chart.article_id)
#        elif pv.action == 'update':
#            try:
#                response = True
#                if utils.is_future_ecom(selected_client):
#                    update_dict = {
#                        'article_id':pv.rate_chart.article_id,
#                        'list_price':pv.new_list_price,
#                        'offer_price':pv.new_offer_price,
#                        'start_time':start_time,
#                        'end_time':end_time,
#                        'catalog':pv.price_list.name,
#                        }
#                    response = update_atg_price(update_dict)
#                
#                if response:
#                    price = Price.objects.select_related('rate_chart','price_list').get(
#                        rate_chart = pv.rate_chart,
#                        price_list = pv.price_list,
#                        list_price = pv.current_list_price,
#                        offer_price = pv.current_offer_price,
#                        cashback_amount =pv.current_cashback_amount,
#                        price_type = pv.price_type,
#                        start_time = pv.current_start_time,
#                        end_time = pv.current_end_time
#                        )
#
#                    if price.end_time:
#                        price.end_time = start_time +timedelta(microseconds=1)
#                        price.save()
#                        prices_approved.append(price.rate_chart.article_id)
#                    else:
#                        price.price_type = 'timed'
#                        price.start_time =datetime.datetime(1111,1,1,0,0,0)
#                        price.end_time = start_time +timedelta(microseconds=1)
#                        price.save()
#                        prices_approved.append(price.rate_chart.article_id)
#
#                    price = Price()
#                    price.rate_chart = pv.rate_chart
#                    price.price_list = pv.price_list
#                    price.list_price = pv.new_list_price
#                    price.offer_price = pv.new_offer_price
#                    price.cashback_amount =pv.new_cashback_amount
#                    price.price_type = 'timed'
#                    price.start_time = start_time
#                    price.end_time = end_time
#                    price.save()
#                    prices_approved.append(price.rate_chart.article_id)
#
#                    pv.status = 'approved'
#                else:
#                    failed_to_update_in_atg.append(pv.rate_chart.article_id)
#
#            except Price.DoesNotExist:
#                errors.append('in update_cat_specific,Unable to find price having sku=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
#                pv.status = 'rejected'
#        elif pv.action == 'delete':
#            try:
#                response = True
#                if utils.is_future_ecom(selected_client):
#                    #In ATG, we can't delete the price, so set it to FB price.
#                    price_fb = Price.objects.filter(
#                        rate_chart = pv.rate_chart,
#                        price_list__name = 'Future Bazaar',
#                        ).exclude(
#                        Q(price_type='timed',start_time__gte=datetime.datetime.now())| 
#                        Q(price_type='timed', end_time__lte=datetime.datetime.now())
#                        )
#                    if price_fb:
#                        update_dict = {
#                            'article_id':price_fb[0].rate_chart.article_id,
#                            'list_price':price_fb[0].list_price,
#                            'offer_price':price_fb[0].offer_price,
#                            'start_time':pv.new_start_time,
#                            'end_time':pv.new_end_time,
#                            'catalog':pv.price_list.name,
#                            }
#                        response = update_atg_price(update_dict, True)
#                
#                if response:
#                    price = Price.objects.get(
#                        rate_chart = pv.rate_chart,
#                        price_list = pv.price_list,
#                        list_price = pv.new_list_price,
#                        offer_price = pv.new_offer_price,
#                        cashback_amount =pv.new_cashback_amount,
#                        price_type = pv.price_type,
#                        start_time = pv.new_start_time,
#                        end_time = pv.new_end_time)
#                    price.delete(using='default')
#                    prices_approved.append(price.rate_chart.article_id)
#
#                    pv.status = 'approved'
#                else:
#                    failed_to_update_in_atg.append(pv.rate_chart.article_id)
#
#            except Price.DoesNotExist:
#                errors.append('in delete_cat,Unable to find price having rate_chart_id=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
#                pv.status = 'rejected'
#    else:
#        if pv.action == 'add':
#            response = True
#            if utils.is_future_ecom(selected_client):
#                update_dict = {
#                    'article_id':pv.rate_chart.article_id,
#                    'list_price':pv.new_list_price,
#                    'offer_price':pv.new_offer_price,
#                    'start_time':pv.new_start_time,
#                    'end_time':pv.new_end_time,
#                    'catalog':pv.price_list.name,
#                    }
#                response = update_atg_price(update_dict)
#            
#            if response:
#                price = Price()
#                price.rate_chart = pv.rate_chart
#                price.price_list = pv.price_list
#                price.list_price = pv.new_list_price
#                price.offer_price = pv.new_offer_price
#                price.cashback_amount = pv.new_cashback_amount
#                price.price_type = pv.price_type
#                price.start_time = pv.new_start_time
#                price.end_time = pv.new_end_time
#                price.save()
#                prices_approved.append(price.rate_chart.article_id)
#
#                pv.status = 'approved'
#            else:
#                failed_to_update_in_atg.append(pv.rate_chart.article_id)
#        elif pv.action == 'update':
#            try:
#                response = True
#                if utils.is_future_ecom(selected_client):
#                    update_dict = {
#                        'article_id':pv.rate_chart.article_id,
#                        'list_price':pv.new_list_price,
#                        'offer_price':pv.new_offer_price,
#                        'start_time':pv.new_start_time,
#                        'end_time':pv.new_end_time,
#                        'catalog':pv.price_list.name,
#                        }
#                    response = update_atg_price(update_dict)
#
#                    #Delete the existing time slot from ATG if slot price.
#                    response1 = True
#                    if pv.price_list.name == 'Timed FB Price':
#                        update_dict = {
#                            'article_id':pv.rate_chart.article_id,
#                            'list_price':pv.new_list_price,
#                            'offer_price':pv.new_offer_price,
#                            'start_time':pv.current_start_time,
#                            'end_time':pv.current_end_time,
#                            'catalog':pv.price_list.name,
#                            }
#                        response1 = update_atg_price(update_dict, True)
#
#                    response = response and response1
#                
#                if response:
#                    price = Price.objects.select_related('rate_chart','price_list').get(
#                        rate_chart = pv.rate_chart,
#                        price_list = pv.price_list,
#                        list_price = pv.current_list_price,
#                        offer_price = pv.current_offer_price,
#                        cashback_amount =pv.current_cashback_amount,
#                        price_type = pv.price_type,
#                        start_time = pv.current_start_time,
#                        end_time = pv.current_end_time
#                        )
#
#                    if price.price_type == 'fixed':
#                        price.list_price = pv.new_list_price
#                        price.offer_price = pv.new_offer_price
#                        price.cashback_amount =pv.new_cashback_amount
#                        price.save()
#                        prices_approved.append(price.rate_chart.article_id)
#                    elif price.price_type == 'timed':
#                        #price.end_time = pv.new_start_time+ timedelta(microseconds=1)
#                        #price.save()
#                        #prices_approved.append(price.rate_chart.article_id)
#
#                        #price = Price()
#                        price.rate_chart = pv.rate_chart
#                        price.price_list = pv.price_list
#                        price.list_price = pv.new_list_price
#                        price.offer_price = pv.new_offer_price
#                        price.cashback_amount =pv.new_cashback_amount
#                        price.price_type = pv.price_type
#                        price.start_time = pv.new_start_time
#                        price.end_time = pv.new_end_time
#                        price.save()
#                        prices_approved.append(price.rate_chart.article_id)
#
#                    pv.status = 'approved'
#                else:
#                    failed_to_update_in_atg.append(pv.rate_chart.article_id)
#
#            except Price.DoesNotExist:
#                errors.append('Unable to find price having sku=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
#                pv.status = 'rejected'
#        elif pv.action == 'delete':
#            try:
#                response = True
#                if utils.is_future_ecom(selected_client):
#                    #In ATG, we can't delete the price, so set it to FB price.
#                    price_fb = Price.objects.filter(
#                        rate_chart = pv.rate_chart,
#                        price_list__name = 'Future Bazaar',
#                        ).exclude(
#                        Q(price_type='timed',start_time__gte=datetime.datetime.now())| 
#                        Q(price_type='timed', end_time__lte=datetime.datetime.now())
#                        )
#
#                    if price_fb:
#                        update_dict = {
#                            'article_id':price_fb[0].rate_chart.article_id,
#                            'list_price':price_fb[0].list_price,
#                            'offer_price':price_fb[0].offer_price,
#                            'start_time':pv.new_start_time,
#                            'end_time':pv.new_end_time,
#                            'catalog':pv.price_list.name,
#                            }
#                        response = update_atg_price(update_dict, True)
#                
#                if response:
#                    price = Price.objects.get(
#                        rate_chart = pv.rate_chart,
#                        price_list = pv.price_list,
#                        list_price = pv.new_list_price,
#                        offer_price = pv.new_offer_price,
#                        cashback_amount =pv.new_cashback_amount,
#                        price_type = pv.price_type,
#                        start_time = pv.new_start_time,
#                        end_time = pv.new_end_time)
#                    price.delete(using='default')
#                    prices_approved.append(price.rate_chart.article_id)
#
#                    pv.status = 'approved'
#                else:
#                    failed_to_update_in_atg.append(pv.rate_chart.article_id)
#            except Price.DoesNotExist:
#                errors.append('in delete_cat,Unable to find price having rate_chart_id=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
#                pv.status = 'rejected'
#
#    pv.approved_by = approved_by
#    pv.approved_on = approved_on
#    pv.save()
#
#    #Update solr index.
#    #Make product available on site, if-
#    #1) Valid price is maintained.(--Already mainained above, so no need to chec again)
#    #2) Pricelist priorities are maintained.
#    #3) Valid stock is maintained.
#    product = pv.rate_chart.product
#    rate_chart = pv.rate_chart
#    rate_chart.stock_status = 'outofstock'
#    pricelist_priority_maintained = False
#    domain_level_applicable_pricelists = DomainLevelPriceList.objects.filter(domain__client=pv.rate_chart.seller.client)
#    if domain_level_applicable_pricelists:
#        pricelist_priority_maintained = True
#    else:
#        client_level_applicable_pricelists = ClientLevelPriceList.objects.filter(client=pv.rate_chart.seller.client)
#        if client_level_applicable_pricelists:
#            pricelist_priority_maintained = True
#
#    if pricelist_priority_maintained:
#        if utils.is_future_ecom(selected_client):
#            #As we are not currently using inventory module for FB,
#            #relaxing the check for inventory for FB.
#            rate_chart.stock_status = 'instock'
#        else:
#            inventory = Inventory.objects.filter(rate_chart = pv.rate_chart)
#            if inventory:
#                for item in inventory:
#                    if item.stock > Decimal('0'):
#                        rate_chart.stock_status = 'instock'
#                        break
#    rate_chart.save()
#    product.update_solr_index()
#
#    return prices_approved, failed_to_update_in_atg
#
#def approve_pricing_job(request,client_name, seller_name, seller, cid, current_seller_id, profile):
#    clients = cache.get('clients')
#    if not clients:
#        clients = profile.managed_clients()
#        cache.set('clients',clients,1800)
#    flag = ""
#    price_versions = None
#    rate_charts = None
#    treat_as_fixed_pricelists =settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL
#    errors = []
#    pagination = {}
#    accounts = cache.get('accounts-'+str(cid))
#    if not accounts:
#        accounts = profile.managed_accounts.filter(client__id = cid)
#        cache.set('accounts-'+str(cid),accounts,1800)
#    display_name_code = None
#    prices_approved, prices_rejected, failed_to_update_in_atg = [], [], []
#    response = True
#
#    selected_client = Client.objects.get(id = cid)
#     
#    if request.method == 'POST':
#        price_versions =PriceVersion.objects.select_related('rate_chart__article_id').filter(
#            status='pending',
#            rate_chart__seller__client__id=cid
#            ).order_by('rate_chart__article_id')
#        #price_versions =PriceVersion.objects.filter(status='pending').order_by('rate_chart__article_id')
#        approved_by = request.user.username
#        approved_on = datetime.datetime.now()
#        start_time = approved_on
#        end_time = datetime.datetime(9999,12,31,0,0,0)
#        rate_charts = get_pending_rate_charts_for_approval(cid)
#
#        for rc in rate_charts:
#            price_versions = PriceVersion.objects.select_related('rate_chart','price_list','price_list__name').filter(rate_chart=rc,status='pending')
#
#            if request.POST.get(str(rc.id), None) == 'approve':
#                for pv in price_versions:
#                    if pv.price_list.name in treat_as_fixed_pricelists:
#                        if pv.action == 'add':
#                            response = True
#                            if utils.is_future_ecom(selected_client) or utils.is_holii_client(selected_client) or is_wholii_client(selected_client):
#                                update_dict = {
#                                     'article_id':pv.rate_chart.article_id,
#                                     'list_price':pv.new_list_price,
#                                     'offer_price':pv.new_offer_price,
#                                     'start_time':start_time,
#                                     'end_time':end_time,
#                                     'catalog':pv.price_list.name,
#                                     }
#                                response = update_atg_price(update_dict)
#
#                            if response:
#                                price = Price.objects.filter(
#                                    rate_chart = pv.rate_chart,
#                                    price_list = pv.price_list,
#                                    price_type = 'timed',
#                                    start_time = start_time,
#                                    end_time = end_time,
#                                    )
#                                if price:
#                                    delete_unwanted_prices_in_same_timeslot = price[1:]
#                                    price = price[0]
#                                    price.list_price = pv.new_list_price
#                                    price.offer_price = pv.new_offer_price
#                                    price.cashback_amount = pv.new_cashback_amount
#                                    price.save()
#
#                                    for item in delete_unwanted_prices_in_same_timeslot:
#                                        item.delete(using='default')
#                                else:
#                                    price = Price()
#                                    price.rate_chart = pv.rate_chart
#                                    price.price_list = pv.price_list
#                                    price.list_price = pv.new_list_price
#                                    price.offer_price = pv.new_offer_price
#                                    price.cashback_amount = pv.new_cashback_amount
#                                    price.price_type = 'timed'
#                                    price.start_time = start_time
#                                    price.end_time = end_time
#                                    price.save()
#
#                                pv.status = 'approved'
#                            else:
#                                failed_to_update_in_atg.append(pv.rate_chart.article_id)
#                        elif pv.action == 'update':
#                            try:
#                                response = True
#                                if utils.is_future_ecom(selected_client):
#                                    update_dict = {
#                                        'article_id':pv.rate_chart.article_id,
#                                        'list_price':pv.new_list_price,
#                                        'offer_price':pv.new_offer_price,
#                                        'start_time':start_time,
#                                        'end_time':end_time,
#                                        'catalog':pv.price_list.name,
#                                        }
#                                    response = update_atg_price(update_dict)
#                                
#                                if response:
#                                    price = Price.objects.select_related('rate_chart','price_list').get(
#                                        rate_chart = pv.rate_chart,
#                                        price_list = pv.price_list,
#                                        list_price = pv.current_list_price,
#                                        offer_price = pv.current_offer_price,
#                                        cashback_amount =pv.current_cashback_amount,
#                                        price_type = pv.price_type,
#                                        start_time = pv.current_start_time,
#                                        end_time = pv.current_end_time
#                                        )
#
#                                    if price.end_time:
#                                        price.end_time = start_time +timedelta(microseconds=1)
#                                        price.save()
#                                    else:
#                                        price.price_type = 'timed'
#                                        price.start_time =datetime.datetime(1111,1,1,0,0,0)
#                                        price.end_time = start_time +timedelta(microseconds=1)
#                                        price.save()
#
#                                    price = Price()
#                                    price.rate_chart = pv.rate_chart
#                                    price.price_list = pv.price_list
#                                    price.list_price = pv.new_list_price
#                                    price.offer_price = pv.new_offer_price
#                                    price.cashback_amount =pv.new_cashback_amount
#                                    price.price_type = 'timed'
#                                    price.start_time = start_time
#                                    price.end_time = end_time
#                                    price.save()
#
#                                    pv.status = 'approved'
#                                else:
#                                    failed_to_update_in_atg.append(pv.rate_chart.article_id)
#
#                            except Price.DoesNotExist:
#                                errors.append('in update_cat_specific,Unable to find price having sku=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
#                                pv.status = 'rejected'
#                        elif pv.action == 'delete':
#                            try:
#                                response = True
#                                if utils.is_future_ecom(selected_client):
#                                    update_dict = {
#                                        'article_id':pv.rate_chart.article_id,
#                                        'list_price':pv.new_list_price,
#                                        'offer_price':pv.new_offer_price,
#                                        'start_time':pv.new_start_time,
#                                        'end_time':start_time,
#                                        'catalog':pv.price_list.name,
#                                        }
#                                    response = update_atg_price(update_dict)
#                                
#                                if response:
#                                    price = Price.objects.get(
#                                        rate_chart = pv.rate_chart,
#                                        price_list = pv.price_list,
#                                        list_price = pv.new_list_price,
#                                        offer_price = pv.new_offer_price,
#                                        cashback_amount =pv.new_cashback_amount,
#                                        price_type = pv.price_type,
#                                        start_time = pv.new_start_time,
#                                        end_time = pv.new_end_time)
#                                    price.delete(using='default')
#
#                                    pv.status = 'approved'
#                                else:
#                                    failed_to_update_in_atg.append(pv.rate_chart.article_id)
#
#                            except Price.DoesNotExist:
#                                errors.append('in delete_cat,Unable to find price having rate_chart_id=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
#                                pv.status = 'rejected'
#                    else:
#                        if pv.action == 'add':
#                            response = True
#                            if utils.is_future_ecom(selected_client) or utils.is_holii_client(selected_client) or utils.is_wholii_client(selected_client):
#                                update_dict = {
#                                    'article_id':pv.rate_chart.article_id,
#                                    'list_price':pv.new_list_price,
#                                    'offer_price':pv.new_offer_price,
#                                    'start_time':pv.new_start_time,
#                                    'end_time':pv.new_end_time,
#                                    'catalog':pv.price_list.name,
#                                    }
#                                response = update_atg_price(update_dict)
#                            
#                            if response:
#                                price = Price()
#                                price.rate_chart = pv.rate_chart
#                                price.price_list = pv.price_list
#                                price.list_price = pv.new_list_price
#                                price.offer_price = pv.new_offer_price
#                                price.cashback_amount = pv.new_cashback_amount
#                                price.price_type = pv.price_type
#                                price.start_time = pv.new_start_time
#                                price.end_time = pv.new_end_time
#                                price.save()
#
#                                pv.status = 'approved'
#                            else:
#                                failed_to_update_in_atg.append(pv.rate_chart.article_id)
#                        elif pv.action == 'update':
#                            try:
#                                response = True
#                                if utils.is_future_ecom(selected_client):
#                                    update_dict = {
#                                        'article_id':pv.rate_chart.article_id,
#                                        'list_price':pv.new_list_price,
#                                        'offer_price':pv.new_offer_price,
#                                        'start_time':pv.new_start_time,
#                                        'end_time':pv.new_end_time,
#                                        'catalog':pv.price_list.name,
#                                        }
#                                    response = update_atg_price(update_dict)
#                                
#                                if response:
#                                    price = Price.objects.select_related('rate_chart','price_list').get(
#                                        rate_chart = pv.rate_chart,
#                                        price_list = pv.price_list,
#                                        list_price = pv.current_list_price,
#                                        offer_price = pv.current_offer_price,
#                                        cashback_amount =pv.current_cashback_amount,
#                                        price_type = pv.price_type,
#                                        start_time = pv.current_start_time,
#                                        end_time = pv.current_end_time
#                                        )
#
#                                    if price.price_type == 'fixed':
#                                        price.list_price = pv.new_list_price
#                                        price.offer_price = pv.new_offer_price
#                                        price.cashback_amount =pv.new_cashback_amount
#                                        price.save()
#                                    elif price.price_type == 'timed':
#                                        price.end_time = pv.new_start_time+ timedelta(microseconds=1)
#                                        price.save()
#
#                                        price = Price()
#                                        price.rate_chart = pv.rate_chart
#                                        price.price_list = pv.price_list
#                                        price.list_price = pv.new_list_price
#                                        price.offer_price = pv.new_offer_price
#                                        price.cashback_amount =pv.new_cashback_amount
#                                        price.price_type = pv.price_type
#                                        price.start_time = pv.new_start_time
#                                        price.end_time = pv.new_end_time
#                                        price.save()
#
#                                    pv.status = 'approved'
#                                else:
#                                    failed_to_update_in_atg.append(pv.rate_chart.article_id)
#
#                            except Price.DoesNotExist:
#                                errors.append('in update_cat_specific,Unable to find price having sku=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
#                                pv.status = 'rejected'
#                        elif pv.action == 'delete':
#                            try:
#                                response = True
#                                if utils.is_future_ecom(selected_client):
#                                    update_dict = {
#                                        'article_id':pv.rate_chart.article_id,
#                                        'list_price':pv.new_list_price,
#                                        'offer_price':pv.new_offer_price,
#                                        'start_time':pv.new_start_time,
#                                        'end_time':start_time,
#                                        'catalog':pv.price_list.name,
#                                        }
#                                    response = update_atg_price(update_dict)
#                                
#                                if response:
#                                    price = Price.objects.get(
#                                        rate_chart = pv.rate_chart,
#                                        price_list = pv.price_list,
#                                        list_price = pv.new_list_price,
#                                        offer_price = pv.new_offer_price,
#                                        cashback_amount =pv.new_cashback_amount,
#                                        price_type = pv.price_type,
#                                        start_time = pv.new_start_time,
#                                        end_time = pv.new_end_time)
#                                    price.delete(using='default')
#
#                                    pv.status = 'approved'
#                                else:
#                                    failed_to_update_in_atg.append(pv.rate_chart.article_id)
#                            except Price.DoesNotExist:
#                                errors.append('in delete_cat,Unable to find price having rate_chart_id=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
#                                pv.status = 'rejected'
#
#                    pv.approved_by = approved_by
#                    pv.approved_on = approved_on
#                    pv.save()
#
#                    #Update solr index.
#                    #Make product available on site, if-
#                    #1) Valid price is maintained.(--Already mainained above, so no need to chec again)
#                    #2) Pricelist priorities are maintained.
#                    #3) Valid stock is maintained.
#                    #
#                    product = pv.rate_chart.product
#                    pv.rate_chart.stock_status = 'outofstock'
#                    pricelist_priority_maintained = False
#                    domain_level_applicable_pricelists = DomainLevelPriceList.objects.filter(domain__client=pv.rate_chart.seller.client)
#                    if domain_level_applicable_pricelists:
#                        pricelist_priority_maintained = True
#                    else:
#                        client_level_applicable_pricelists = ClientLevelPriceList.objects.filter(client=pv.rate_chart.seller.client)
#                        if client_level_applicable_pricelists:
#                            pricelist_priority_maintained = True
#
#                    if pricelist_priority_maintained:
#                        inventory = Inventory.objects.filter(rate_chart = pv.rate_chart)
#                        if inventory:
#                            for item in inventory:
#                                if item.stock > Decimal('0'):
#                                    pv.rate_chart.stock_status = 'instock'
#                                    break
#
#                    product.update_solr_index()
#
#                    if (not pv.rate_chart.article_id in prices_approved) and response:
#                        prices_approved.append(pv.rate_chart.article_id)
#            elif request.POST.get(str(rc.id), None) == 'reject':
#                for pv in price_versions:
#                    pv.status = 'rejected'
#                    pv.approved_by = approved_by
#                    pv.approved_on = approved_on
#                    pv.save()
#                    if not pv.rate_chart.article_id in prices_rejected:
#                        prices_rejected.append(pv.rate_chart.article_id)
#
#
#     #Get all the price versions pending for approval/rejection.
##    price_versions = PriceVersion.objects.select_related('rate_chart__article_id').filter(
##        status='pending',
##        rate_chart__seller__client__id=cid,
##        ).order_by('rate_chart__article_id')
#    rate_charts = get_pending_rate_charts_for_approval(cid)
#
#    import re
#    page_no = request.GET.get('page',1)
#    page_no = int(page_no)
#    items_per_page = 20
#    total_results = len(rate_charts)
#    total_pages =int(math.ceil(Decimal(total_results)/Decimal(items_per_page)))
#
#    base_url = request.get_full_path()
#
#    page_pattern = re.compile('[&?]page=\d+')
#    base_url = page_pattern.sub('',base_url)
#    page_pattern = re.compile('[&?]per_page=\d+')
#    base_url = page_pattern.sub('',base_url)
#    if base_url.find('?') == -1:
#        base_url = base_url + '?'
#    else:
#        base_url = base_url + '&'
#    pagination = getPaginationContext(page_no, total_pages, base_url)
#
#    rate_charts =rate_charts[((page_no-1)*items_per_page):(page_no*items_per_page)]
#
#    approve_jobs_dict = {
#        'accounts':accounts,
#        'loggedin':True,
#        'rate_charts':rate_charts,
#        'prices_approved':prices_approved,
#        'prices_rejected':prices_rejected,
#        'failed_to_update_in_atg':failed_to_update_in_atg,
#        'pagination':pagination,
#        'errors':errors,
#        'clients':clients,
#        'client_name':client_name, 
#        'seller_name':seller_name,
#        'url':request.get_full_path(),
#        'flag':flag,
#        'client_display_name':Client.objects.filter(slug=client_name)[0].name,
#        }
#    return render_to_response('prices/approve_pricing_jobs.html', approve_jobs_dict, context_instance=RequestContext(request))
#
#def get_pending_rate_charts_for_approval(cid):
#    distinct_rate_charts = PriceVersion.objects.filter(
#        status='pending',
#        rate_chart__seller__client__id=cid
#        ).distinct('rate_chart').values('rate_chart')
#
#    rate_chart_ids = []
#    for rc in distinct_rate_charts:
#        rate_chart_ids.append(rc['rate_chart'])
#
#    rate_charts = SellerRateChart.objects.filter(id__in=rate_chart_ids)
#    return rate_charts
#
#def price_version_details(request):
#    rc_id = request.GET.get('rc_id')
#    #num = request.GET.get('num',0)
#    price_versions = PriceVersion.objects.filter(rate_chart__id=rc_id, status='pending').order_by('created_on')
#    return render_to_response('prices/price_version_details.html', {'price_versions':price_versions},
#                context_instance=RequestContext(request))
#
#def get_temporary_file_path():
#    import tempfile
#    tf = tempfile.NamedTemporaryFile()
#    path = tf.name
#    tf.close()
#    return path
#
#def save_uploaded_file(f):
#    path_to_save = get_temporary_file_path()
#    fp = open(path_to_save, 'w')
#    for chunk in f.chunks():
#        fp.write(chunk)
#    fp.close()
#    return path_to_save
#
#def get_account(price_list_name):
#    pricelist_to_account_mapping = settings.PRICELIST_TO_ACCOUNT_MAPPING
#    return utils.get_seller(pricelist_to_account_mapping[price_list_name])
#
#def get_current_prices(path_to_save, seller):
#    import xlrd
#    from django.db.models import Q
#    book = xlrd.open_workbook(path_to_save)
#    sh = book.sheet_by_index(0)
#    header = sh.row(0)
#    map = {}
#    idx = 0
#    for idx in range(sh.ncols):
#        map[header[idx].value.strip().lower()] = idx
#    errors = []
#    to_update = []
#    skip_prices = []
#    update_prices = []
#    client_level_applicable_pricelists = settings.CLIENT_LEVEL_APPLICABLE_PRICELISTS
#
#    for row_count in range(1, sh.nrows):
#        row = sh.row(row_count)
#        try:
#            article_id = row[map['articleid']].value
#            to_update.append({
#                'article_id': str(int(article_id)).split('.')[0],
#            })
#        except KeyError:
#            errors.append('Unsupported excel file.')
#            break
#
#    if to_update:
#        from pricing.models import Price,PriceList
#        all_prices = []
#        for item in to_update:
#            rate_chart = None
#            try:
#                rate_chart = SellerRateChart.objects.get(article_id = item['article_id'], seller=seller) 
#            except SellerRateChart.DoesNotExist:
#                log.info('SellerRateChart for article id - %s does not exist' % item['article_id'])
#            except SellerRateChart.MultipleObjectsReturned:
#                log.info('Multiple articles maitained for article id - %s' % item['article_id'])
#
#            if rate_chart:
#                for pl in client_level_applicable_pricelists:
#                    price_versions = PriceVersion.objects.filter(
#                        rate_chart = rate_chart, 
#                        price_list__name = pl,
#                        status = 'approved').order_by('-approved_on')
#                    
#                    if price_versions:
#                        price_info = {
#                            'article_id':item['article_id'],
#                            'product_name':rate_chart.product.title,
#                            'catalog':price_versions[0].price_list.name,
#                            'price_versions':price_versions[:5],
#                            }
#                        all_prices.append(price_info)
#
#    return all_prices
#
#def validate_excel_entry(article_id, list_price, offer_price, display_name, start_time, end_time, cashback_amount):
#    errors = []
#    price_lists_dir = settings.PRICE_LISTS_DIRECTORY 
#    article_id_validated = False
#    try:
#        article_id_int = int(article_id)
#        article_id_validated = True
#    except:
#        errors.append("Wrong value %s in the 'Articleid' column!!! Please correct it and try to re-upload!!!" % article_id)
#
#    list_price_validated = False
#    try:
#        list_price_int = int(list_price)
#        list_price_validated = True
#    except:
#        errors.append("Wrong value %s in the 'MRP' column!!! Please correct it and try to re-upload!!!" % list_price)
#       
#    offer_price_validated = False
#    try:
#        offer_price_int = int(offer_price)
#        offer_price_validated = True
#    except:
#        errors.append("Wrong value %s in the 'Salesprice' column!!! Please correct it and try to re-upload!!!" % offer_price)
#
#    cashback_amount_validated = False
#    try:
#        cashback_int = int(cashback_amount)
#        cashback_amount_validated = True
#    except:
#        errors.append("Wrong value %s in the 'Cashback Amount' column!!! Please correct it and try to re-upload!!!" % cashback_amount)
#
#    start_time_validated = False
#    try:
#        start_time_date = datetime.datetime.strptime(str(start_time),'%Y-%m-%d %H:%M:%S')
#        start_time_validated = True
#    except:
#        errors.append("Wrong value %s in the 'Starttime' column!!! Please correct it and try to re-upload!!!" % start_time)
#        
#    end_time_validated = False
#    try:
#        end_time_date = datetime.datetime.strptime(str(end_time),'%Y-%m-%d %H:%M:%S')
#        end_time_validated = True
#    except:
#        errors.append("Wrong value %s in the 'Endtime' column!!! Please correct it and try to re-upload!!!" % end_time)
#       
#    catalog_name_validated = False
#    try:
#        catalog_name = price_lists_dir[str(display_name).strip().lower()]
#        catalog_name_validated = True
#    except:
#        errors.append("Wrong value %s in the 'Catalog' column!!! Please correct it and try to re-upload!!!" % display_name)
#
#    entry_validated = False
#    if article_id_validated and list_price_validated and offer_price_validated and cashback_amount_validated and start_time_validated and end_time_validated and catalog_name_validated:
#        entry_validated = True
#    return errors, entry_validated
#
#def get_prices(path_to_save, seller):
#    import xlrd
#    from django.db.models import Q
#    from django.utils import simplejson
#    book = xlrd.open_workbook(path_to_save)
#    sh = book.sheet_by_index(0)
#    header = sh.row(0)
#    map = {}
#    idx = 0
#    for idx in range(sh.ncols):
#        map[header[idx].value.strip().lower()] = idx
#    errors, to_update, skip_prices, update_prices, article_id_list = [], [], [], [], []
#    seller_rate_chart_dict = {}
#    price_lists_dir = settings.PRICE_LISTS_DIRECTORY 
#    treat_as_fixed_pricelist = settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL
#
#    for row_count in range(1, sh.nrows):
#        row = sh.row(row_count)
#        try:
#            article_id = str(int(row[map['articleid']].value))
#            print article_id, "#$#$#$#$#$#$#$#$#$#$#$#$#$#$#$#$#$#$#$#$#$#$#$#"
#            list_price = row[map['mrp']].value
#            offer_price = row[map['salesprice']].value
#            display_name = row[map['catalog']].value
#            start_time = row[map['starttime']].value
#            end_time = row[map['endtime']].value
#            cashback_amount = row[map['cashback amount']].value
#            
#            error_in_entry_validation, entry_validated = validate_excel_entry(article_id, list_price, offer_price, display_name, start_time, end_time, cashback_amount)
#            errors += error_in_entry_validation
#            if entry_validated:
#                add_dict = {
#                    'article_id': str(int(article_id)).strip().split('.')[0],
#                    'list_price': list_price,
#                    'offer_price' : offer_price,
#                    'display_name' : display_name.strip().lower(),
#                    'cashback_amount' : cashback_amount,
#                    'start_time':start_time,
#                    'end_time':end_time,
#                    }
#
#                repeated = False
#                for item in to_update:
#                    if (item['article_id'] == add_dict['article_id']) and (item['display_name'] == add_dict['display_name']):
#                        if price_lists_dir[add_dict['display_name']] in treat_as_fixed_pricelist:
#                            errors.append("Duplicate Entries for Articleid-'%s' and Catalog-'%s' combination!!!" % (add_dict['article_id'],add_dict['display_name']))
#                            repeated = True
#                            break
#                        else:
#                            if (item['start_time'] == add_dict['start_time']) and (item['end_time'] == add_dict['end_time']):
#                                errors.append("Overlapping timeslot entries for Articleid-'%s' and Catalog-'%s' combination!!!" % (add_dict['article_id'],add_dict['display_name']))
#                                repeated = True
#                                break
#
#                if not repeated:
#                    to_update.append(add_dict)
#                    if not add_dict['article_id'] in article_id_list:
#                        article_id_list.append(add_dict['article_id'])
#        except KeyError:
#            errors.append('Unsupported excel file. Please check the sample template format!!!')
#            break
#    
#    #seller = None
#    if to_update:        
#        to_update.sort()
#        #seller = get_account(price_lists_dir[to_update[0]['display_name']])
#
#    #Fetch seller rate charts for all the article ids in excel file.
#    multiple_rate_charts_found = []
#    if seller and article_id_list:
#        all_seller_rate_charts = SellerRateChart.objects.filter(
#            article_id__in=article_id_list, 
#            seller=seller)
#        if all_seller_rate_charts:
#            for item in all_seller_rate_charts:
#                if item.article_id in seller_rate_chart_dict:
#                    errors.append('Multiple active articles maintained for Articleid - %s' % item.article_id)
#                    del seller_rate_chart_dict[item.article_id] 
#                    multiple_rate_charts_found.append(item.article_id)
#                else:
#                    seller_rate_chart_dict[item.article_id] = item
#
#    if to_update:
#        from pricing.models import Price,PriceList
#        all_prices = []
#        #update_prices = []
#        #skip_prices = []
#        for item in to_update:
#            #try:
#            price_list = PriceList.objects.get(name=price_lists_dir[item['display_name']])
#            #seller = get_account(price_lists_dir[item['display_name']])
#            rate_chart = seller_rate_chart_dict.get(item['article_id'],None)
#            if (not rate_chart) and (not item['article_id'] in multiple_rate_charts_found):
#                errors.append('No active article maintained for Articleid - %s' % item['article_id'])
#
#            if rate_chart:
#                price = None
#                check_overlapped_prices = True
#                if price_lists_dir[item['display_name']] in treat_as_fixed_pricelist:
#                    check_overlapped_prices = False
#
#                overlapped_price = None
#                if check_overlapped_prices:
#                    start_time = datetime.datetime.strptime(item['start_time'],'%Y-%m-%d %H:%M:%S')
#                    end_time = datetime.datetime.strptime(item['end_time'],'%Y-%m-%d %H:%M:%S')
#                    overlapped_price = Price.objects.select_related('rate_chart','price_list').filter(
#                        rate_chart=rate_chart, 
#                        price_list=price_list).exclude(
#                        Q(price_type = 'timed', start_time__gt = end_time) | 
#                        Q(price_type = 'timed', end_time__lt = start_time)
#                        )
#                if check_overlapped_prices and overlapped_price:
#                    price_info = {
#                        'article_id':item['article_id'],
#                        'catalog':price_lists_dir[item['display_name']],
#                        'list_price':item['list_price'],
#                        'offer_price':item['offer_price'],
#                        'cashback_amount':item['cashback_amount'],
#                        'start_time':item['start_time'],
#                        'end_time':item['end_time'],
#                        'conflicts':overlapped_price,
#                        'rowspan':len(overlapped_price),
#                        'action':'Skip',
#                        }
#                    skip_prices.append(price_info)
#                else:
#                    try:
#                        if price_lists_dir[item['display_name']] in treat_as_fixed_pricelist:
#                            price = Price.objects.select_related('rate_chart','price_list').filter(
#                                rate_chart=rate_chart, 
#                                price_list=price_list, 
#                                ).exclude(
#                                Q(price_type='timed',start_time__gte=datetime.datetime.now())| 
#                                Q(price_type='timed', end_time__lte=datetime.datetime.now())
#                                )
#                            if price:
#                                price = price[0]
#                        else:
#                            price = Price.objects.select_related('rate_chart','price_list').get(
#                                rate_chart=rate_chart, 
#                                price_list=price_list, 
#                                price_type='timed', 
#                                start_time=start_time, 
#                                end_time=end_time,
#                                )
#                            
#                        if price:
#                            action = ''
#                            if price.list_price != Decimal(str(item['list_price'])) or price.offer_price != Decimal(str(item['offer_price'])) or price.cashback_amount != Decimal(str(item['cashback_amount'])):
#                                action = 'Update'
#                            elif not price_lists_dir[item['display_name']] in treat_as_fixed_pricelist:
#                                if price.start_time != start_time or price.end_time != end_time:
#                                    action = 'Update'
#                                else:
#                                    action = 'No Action'
#                            else:
#                                    action = 'No Action'
#
#                            price_info = {
#                                'price':price,
#                                'list_price':Decimal(str(item['list_price'])),
#                                'offer_price':Decimal(str(item['offer_price'])),
#                                'cashback_amount':Decimal(str(item['cashback_amount'])),
#                                'start_time':item['start_time'],
#                                'end_time':item['end_time'],
#                                'action':action,
#                                }
#                        else:
#                            price = Price(rate_chart=rate_chart, price_list=price_list, list_price=Decimal(str(item['list_price'])), offer_price=Decimal(str(item['offer_price'])),cashback_amount=Decimal(str(item['cashback_amount'])))
#                            if not price_lists_dir[item['display_name']] in treat_as_fixed_pricelist:
#                                price.price_type = 'timed'
#                                price.start_time = start_time
#                                price.end_time = end_time
#
#                            price_info = {
#                                'price':price,
#                                'list_price':Decimal(str(item['list_price'])),
#                                'offer_price':Decimal(str(item['offer_price'])),
#                                'cashback_amount':Decimal(str(item['cashback_amount'])),
#                                'start_time':item['start_time'],
#                                'end_time':item['end_time'],
#                                'action':'Add',
#                               }
#                        update_prices.append(price_info)
#                    except Price.DoesNotExist:
#                        price = Price(rate_chart=rate_chart, price_list=price_list,list_price=Decimal(str(item['list_price'])), offer_price=Decimal(str(item['offer_price'])),cashback_amount=Decimal(str(item['cashback_amount'])))
#                        if not price_lists_dir[item['display_name']] in treat_as_fixed_pricelist:
#                            price.price_type = 'timed'
#                            price.start_time = start_time
#                            price.end_time = end_time
#
#                        price_info = {
#                            'price':price,
#                            'list_price':Decimal(str(item['list_price'])),
#                            'offer_price':Decimal(str(item['offer_price'])),
#                            'cashback_amount':Decimal(str(item['cashback_amount'])),
#                            'start_time':item['start_time'],
#                            'end_time':item['end_time'],
#                            'action':'Add',
#                           }
#                        update_prices.append(price_info)
#    else:
#        if not errors:
#            log.info('no prices to upload in the sheet!!!')
#            errors.append('No prices to upload in the excel!!!')
#
#    #Creating json for update_prices to render between the templates
#    add_price_json = []
#    update_price_json = []
#    for i in update_prices:
#        if i['action'] == 'Add':
#            temp_dict= {}
#            temp_dict['list_price'] = str(i['list_price'])
#            temp_dict['offer_price'] = str(i['offer_price'])
#            temp_dict['cashback_amount'] = str(i['cashback_amount'])
#            temp_dict['start_time'] = str(i['start_time'])
#            temp_dict['end_time'] = str(i['end_time'])
#            temp_dict['price_list'] = i['price'].price_list.name
#            temp_dict['rate_chart'] = i['price'].rate_chart.id
#            add_price_json.append(temp_dict)
#        elif i['action'] == 'Update':
#            temp_dict= {}
#            temp_dict['list_price'] = str(i['list_price'])
#            temp_dict['offer_price'] = str(i['offer_price'])
#            temp_dict['cashback_amount'] = str(i['cashback_amount'])
#            temp_dict['start_time'] = str(i['start_time'])
#            temp_dict['end_time'] = str(i['end_time'])
#            temp_dict['price'] = i['price'].id
#            update_price_json.append(temp_dict)
#
#    all_prices_json = {'add_price':add_price_json, 'update_price':update_price_json}
#    all_prices_json = simplejson.dumps(all_prices_json)
#    all_prices = {'skip':skip_prices, 'update':update_prices}
#    return errors, all_prices, all_prices_json
#
#def set_price_version(price, action, created_by, created_on, new_list_price=None, new_offer_price=None, new_cashback_amount=None, new_starts_on=None, new_ends_on=None):
#    price_version = PriceVersion()
#    price_version.rate_chart = price.rate_chart
#    price_version.price_list = price.price_list
#    
#    price_version.current_list_price = price.list_price
#    if new_list_price:
#        price_version.new_list_price = Decimal(str(new_list_price)).quantize(Decimal('1.'), rounding=ROUND_UP)
#    else:
#        price_version.new_list_price = price.list_price
#        
#    price_version.current_offer_price = price.offer_price
#    if new_offer_price:
#        price_version.new_offer_price = Decimal(str(new_offer_price)).quantize(Decimal('1.'), rounding=ROUND_UP)
#    else:
#        price_version.new_offer_price = price.offer_price
#
#    price_version.current_cashback_amount = price.cashback_amount
#    if new_cashback_amount != None:
#        price_version.new_cashback_amount = Decimal(str(new_cashback_amount)).quantize(Decimal('1.'), rounding=ROUND_UP)
#    else:
#        price_version.new_cashback_amount = price.cashback_amount
#
#    price_version.current_start_time = price.start_time
#    if new_starts_on:
#        #price_version.new_start_time = datetime.datetime.strptime(new_starts_on,'%Y-%m-%d %H:%M:%S')
#        price_version.new_start_time = new_starts_on
#    else:
#        price_version.new_start_time = price.start_time
#    
#    price_version.current_end_time = price.end_time
#    if new_ends_on:
#        #price_version.new_end_time = datetime.datetime.strptime(new_ends_on,'%Y-%m-%d %H:%M:%S')
#        price_version.new_end_time = new_ends_on
#    else:
#        price_version.new_end_time = price.end_time
#        
#    #price_version.pricing_job = pricing_job
#    price_version.price_type = price.price_type
#    #if price.price_list.name in settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL:
#    #    price_version.price_type = 'timed'
#    price_version.action = action
#    price_version.created_by = created_by
#    price_version.created_on = created_on
#    price_version.save()
#    return price_version
#
#def upload_price_xls(request,client_name, seller, cid,seller_id, c, profile):
#    from web.sbf_forms import FileUploadForm
#    from django.utils import simplejson
#    import os
#    errors, message = [], None
#    all_prices, all_prices_json = None, None
#    form = None
#    flag = None
#    to_update = None
#    path_to_save = None
#    accounts = cache.get('accounts-'+str(cid))
#    if not accounts:
#        accounts = profile.managed_accounts.filter(client__id = cid)
#        cache.set('accounts-'+str(cid),accounts,1800)
#    clients = cache.get('clients')
#    if not clients:
#        clients = profile.managed_clients()
#        cache.set('clients',clients,1800)
#    price_lists_dir = settings.PRICE_LISTS_DIRECTORY 
#    updated_price, no_update_in_atg, prices_rejected = [], [], []
#    prices_approved, failed_to_update_in_atg = [], []
#    selected_client = Client.objects.get(id = cid)
#
#    if request.method == 'POST':
#        if request.POST.get("upload") == 'Upload':
#            import xlrd
#            form = FileUploadForm(request.POST, request.FILES)
#            if form.is_valid():
#                path_to_save = save_uploaded_file(request.FILES['status_file'])
#                errors, all_prices, all_prices_json = get_prices(path_to_save, seller)
#
#                #Delete the uploaded excel file
#                if path_to_save:
#                    os.remove(path_to_save)
#
#                if errors:
#                    form = FileUploadForm()
#                    flag = 'new'
#                else:
#                    flag = 'show_details'
#            else:
#                errors.append('Please select the excel file and then click upload!!!')
#                form = FileUploadForm()
#                flag = 'new'
#
#        elif request.POST.get("update") == 'Update':
#            #path_to_save = request.POST.get("path_to_save")
#            all_prices_json = simplejson.loads(request.POST.get("all_prices_json"))
#            add_price_json = all_prices_json['add_price']
#            update_price_json = all_prices_json['update_price']
#            update_prices = []
#
#            if add_price_json:
#                treat_as_fixed_pricelist = settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL
#                for item in add_price_json:
#                    rate_chart = SellerRateChart.objects.get(id=item['rate_chart'])
#                    price_list = PriceList.objects.get(name=item['price_list'])
#                    price = Price(rate_chart=rate_chart, price_list=price_list, list_price=Decimal(str(item['list_price'])), offer_price=Decimal(str(item['offer_price'])),cashback_amount=Decimal(str(item['cashback_amount'])))
#
#                    if not item['price_list'].strip() in treat_as_fixed_pricelist:
#                        price.price_type = 'timed'
#                        price.start_time = item['start_time']
#                        price.end_time = item['end_time']
#
#                    price_info = {
#                        'price':price,
#                        'list_price':Decimal(str(item['list_price'])),
#                        'offer_price':Decimal(str(item['offer_price'])),
#                        'cashback_amount':Decimal(str(item['cashback_amount'])),
#                        'start_time':datetime.datetime.strptime(item['start_time'],'%Y-%m-%d %H:%M:%S'),
#                        'end_time':datetime.datetime.strptime(item['end_time'],'%Y-%m-%d %H:%M:%S'),
#                        'action':'Add',
#                       }
#                    update_prices.append(price_info)
#
#            if update_price_json:
#                for item in update_price_json:
#                    price = Price.objects.select_related('rate_chart','price_list').get(id=item['price'])
#
#                    price_info = {
#                        'price':price,
#                        'list_price':Decimal(str(item['list_price'])),
#                        'offer_price':Decimal(str(item['offer_price'])),
#                        'cashback_amount':Decimal(str(item['cashback_amount'])),
#                        'start_time':datetime.datetime.strptime(item['start_time'],'%Y-%m-%d %H:%M:%S'),
#                        'end_time':datetime.datetime.strptime(item['end_time'],'%Y-%m-%d %H:%M:%S'),
#                        'action':'Update',
#                       }
#                    update_prices.append(price_info)
#
#            all_prices = {'update':update_prices}
#
#            #errors, all_prices = get_prices(path_to_save)
#
#            actions = {'Update':'update','Add':'add'}
#            created_by = request.user.username
#            created_on = datetime.datetime.now()
#
#            if all_prices['update']:
#                for price_info_dict in all_prices['update']:
#                    if price_info_dict['action'] in ['Update','Add']:
#                        price = price_info_dict['price']
#                        new_list_price = price_info_dict['list_price']
#                        new_offer_price = price_info_dict['offer_price']
#                        new_cashback_amount = price_info_dict['cashback_amount']
#                        new_start_time = price_info_dict['start_time']
#                        new_end_time = price_info_dict['end_time']
#                        action = actions[price_info_dict['action']]
#                        try:
#                            price_version = set_price_version(price, action, created_by, created_on, new_list_price, new_offer_price, new_cashback_amount, new_start_time, new_end_time)
#                            updated_price, no_update_in_atg = approve_single_price(request, price_version, selected_client)
#                            if updated_price:
#                                prices_approved.append(updated_price[0])
#                            if no_update_in_atg:
#                                failed_to_update_in_atg.append(no_update_in_atg[0])
#                        except Exception, e:
#                            prices_rejected.append(price.rate_chart.article_id)
#                            log.info(e)
#
#            flag = 'updated'
#            form = FileUploadForm()
#    else:
#        form = FileUploadForm()
#        flag = 'new'
#    prices_dict = {
#	    'accounts':accounts,
#        'clients':clients, 
#        'client_name':client_name, 
#        'seller_name':slugify(seller), 
#        'forms':form,
#        'errors':errors,
#        'all_prices':all_prices,
#        'all_prices_json':all_prices_json,
#        'flag':flag,
#        'path_to_save':path_to_save,
#        'url':request.get_full_path(),
#        'loggedin':True,
#        'prices_approved':prices_approved,
#        'failed_to_update_in_atg':failed_to_update_in_atg,
#        'prices_rejected':prices_rejected,
#        }
#    prices_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
#    return render_to_response('prices/price_bulk_upload.html', prices_dict, context_instance=RequestContext(request))
#
#def get_pricing_info(rate_chart):
#    #from django.db.models import Q
#    catalog_specific_prices, anonymous_prices = [], []
#    all_prices = Price.objects.filter(rate_chart__in = rate_chart).exclude(price_type='timed', end_time__lt=datetime.datetime.now())
#
#    for price in all_prices:
#        if price.price_list.name.__contains__('Anonymous'):
#            anonymous_prices.append(price)
#        else:
#            catalog_specific_prices.append(price)
#
#    return all_prices, catalog_specific_prices, anonymous_prices
#
#def search_by_sku(request,client_name, seller, cid, seller_id, c, profile):
#    rate_chart = None
#    prices = None
#    skuid = ""
#    article_id = ""
#    searched_by = ""
#    pricelist_options = ""
#    errors = []
#    all_prices, catalog_specific_prices, anonymous_prices = None, None, None
#    delete_prices, update_prices, anonymous_update_price = [], [], []
#    product = None
#    product_image = None
#    flag = ""
#    pricing_job_id = None
#    pricing_job = None
#    list_price, updated_list_price = None, None
#    client_pricelist_mapping = settings.CLIENT_PRICELIST_MAPPING
#    accounts = cache.get('accounts-'+str(cid))
#    if not accounts:
#        accounts = profile.managed_accounts.filter(client__id = cid)
#        cache.set('accounts-'+str(cid),accounts,1800)
#    clients = cache.get('clients')
#    if not clients:
#        clients = profile.managed_clients()
#        cache.set('clients',clients,1800)
#    if_any_changes = False
#    is_pricing_tool_supported = False
#
#    from accounts.models import Client
#    client = Client.objects.get(id = cid)
#    is_pricing_tool_supported = utils.is_pricing_tool_supported(client)
#
#    if request.method == 'POST':
#        check = request.POST.get('name', None)
#        if check!='change':
#            from pricing.models import Price
#            treat_as_fixed_pricelists = settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL
#
#    if not is_pricing_tool_supported:
#        errors.append('Pricing tool is currently does not have support for selected client!!!')
#    else:
#        if request.method == 'POST':
#            from pricing.models import Price, PriceVersion, PriceList
#            treat_as_fixed_pricelists = settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL
#
#            #Client level applicable pricelists for option of adding new prices
#            client_level_applicable_pricelists = settings.CLIENT_LEVEL_APPLICABLE_PRICELISTS
#            applicable_pricelists = client_level_applicable_pricelists[seller.client.name]
#            #Now, generate the HTML dropdown code for showing dropdown menu.
#            for item in applicable_pricelists:
#                pricelist_options += "<option> %s </option>" % item 
#
#            skuid = request.POST.get("sku")
#            article_id = request.POST.get("articleid")
#
#            if skuid:
#                try:
#                    rate_chart = SellerRateChart.objects.get(sku=skuid.strip(),seller__client__id=cid)
#                except SellerRateChart.DoesNotExist:
#                    errors.append('No article maintained for SKU - %s' % skuid)
#                except SellerRateChart.MultipleObjectsReturned:
#                    errors.append('Multiple articles maintained for same SKU - %s' % skuid)
#                   
#                if rate_chart:
#                    article_id = rate_chart.article_id
#                searched_by = 'skuid'
#            elif article_id:
#                try:
#                    rate_chart = SellerRateChart.objects.get(article_id=article_id.strip(), seller__client__id=cid)
#                except SellerRateChart.DoesNotExist:
#                    errors.append('No article maintained for Articleid - %s' % article_id)
#                except SellerRateChart.MultipleObjectsReturned:
#                    errors.append('Multiple articles maintained for same Articleid - %s' % article_id)
#
#                if rate_chart:
#                    skuid = rate_chart.sku
#                searched_by = 'article_id'
#
#            if rate_chart:
#                flag = "searched"
#                
#                #First check, if there are any pending PriceVersion jobs pending for aaproval. 
#                #If yes, then prompt error message. If no, then proceed.
#                price_versions = PriceVersion.objects.filter(rate_chart__in = rate_chart, status='pending')
#
#                if price_versions:
#                    errors.append('Prices pending for approval!!! First, approve/rejects those!!!')
#                    product = price_versions[0].rate_chart.product
#                    product_image = ProductImage.objects.filter(product=product)
#                    if product_image:
#                        product_image = product_image[0]
#                else:
#                    all_prices = Price.objects.filter(
#                        rate_chart__in = rate_chart).exclude(
#                        Q(price_type='timed', end_time__lt=datetime.datetime.now())|
#                        Q(price_list__name__contains='Anonymous'))
#                   
#                    for price in all_prices:
#                        if price.price_list.name.__contains__(client_pricelist_mapping[cid]):
#                            list_price = price.list_price
#                            break
#
#                    anonymous_list_price = None
#
#                    if all_prices:
#                        for price in all_prices:
#                            product = price.rate_chart.product
#                            if product:
#                                product_image = ProductImage.objects.filter(product=product)
#
#                            if product_image:
#                                product_image = product_image[0]
#
#                            if product and product_image:
#                                break
#
#                        if request.POST.get("update", None) == "Update":
#                            updated_list_price = request.POST.get('list_price')
#                            if not Decimal(str(updated_list_price)) == all_prices[0].list_price:
#                                if_any_changes = True
#
#                            flag = "updated"
#
#                            if Decimal(str(request.POST.get('list_price',None))) == Decimal('0'):
#                                errors.append('Cannot set M.R.P. to 0!!!')
#
#                            for price in all_prices:
#                                if request.POST.get("%s#offer_price" % price.id) and Decimal(str(request.POST.get("%s#offer_price" % price.id))) == Decimal('0'):
#                                    errors.append('Offer Price cannot be set to 0!!!')
#
#                            if not errors:
#                                for price in all_prices:
#                                    if request.POST.get("%s#checkbox" % price.id) == "deleted":
#                                        price_info = {
#                                            'price':price,
#                                            'action':'Delete',
#                                            }
#                                        update_prices.append(price_info)
#                                        delete_prices.append(price)
#                                        if_any_changes = True
#                                    else:
#                                        offer_price_changed = False
#                                        if request.POST.get("%s#offer_price" % price.id) and not Decimal(str(request.POST.get("%s#offer_price" % price.id))) == price.offer_price:
#                                            offer_price_changed = True
#                                        
#                                        cashback_amount_changed = False
#                                        if request.POST.get("%s#cashback_amount" % price.id) and ((not price.cashback_amount) or (price.cashback_amount and not Decimal(str(request.POST.get("%s#cashback_amount" % price.id))) == price.cashback_amount)):
#                                            cashback_amount_changed = True
#                                        
#                                        starts_on_changed = False
#                                        starts_on = None
#                                        if request.POST.get("%s#starts_on" % price.id):
#                                            starts_on = request.POST.get("%s#starts_on" % price.id) + " "
#                                            starts_on += request.POST.get("%s#starts_on#hr" % price.id) + ":"
#                                            starts_on += request.POST.get("%s#starts_on#min" % price.id)
#                                            starts_on = datetime.datetime.strptime(starts_on,'%d-%m-%Y %H:%M')
#                                            if not starts_on == price.start_time:
#                                                starts_on_changed = True
#
#                                        ends_on_changed = False
#                                        ends_on = None
#                                        if request.POST.get("%s#ends_on" % price.id):
#                                            ends_on = request.POST.get("%s#ends_on" % price.id) + " "
#                                            ends_on += request.POST.get("%s#ends_on#hr" % price.id) + ":"
#                                            ends_on += request.POST.get("%s#ends_on#min" % price.id)
#                                            ends_on = datetime.datetime.strptime(ends_on,'%d-%m-%Y %H:%M')
#                                            if not ends_on == price.start_time:
#                                                ends_on_changed = True
#
#                                        if offer_price_changed or cashback_amount_changed or starts_on_changed or ends_on_changed:
#                                            price_info = {
#                                                'price':price,
#                                                'offer_price':request.POST.get("%s#offer_price" % price.id),
#                                                'cashback_amount':request.POST.get("%s#cashback_amount" % price.id),
#                                                'starts_on':starts_on,
#                                                'ends_on':ends_on,
#                                                'action':'Update',
#                                                }
#                                            update_prices.append(price_info)
#                                            if_any_changes = True
#                                        else:
#                                            price_info = {
#                                                'price':price,
#                                                'action':'No Change',
#                                                }
#                                            update_prices.append(price_info)
#                      
#                        elif request.POST.get("confirm") and request.POST.get("confirm") == "Confirm":
#                            flag = "confirmed"
#                            current_list_price = request.POST.get("list_price")
#                            new_list_price = request.POST.get("updated_list_price")
#                            for price in all_prices:
#                                if request.POST.get("%s#delete_price" % price.id):
#                                    set_price_version(price, 'delete', request.user.username, datetime.datetime.now())
#                                elif (current_list_price != new_list_price) or (request.POST.get("%s#offer_price" % price.id) and not Decimal(str(request.POST.get("%s#offer_price" % price.id))) == price.offer_price)or (request.POST.get("%s#offer_price" % price.id) and not Decimal(str(request.POST.get("%s#cashback_amount" % price.id))) == price.cashback_amount) or (request.POST.get("%s#starts_on" % price.id) and not request.POST.get("%s#starts_on" % price.id) == str(price.start_time)) or (request.POST.get("%s#ends_on" % price.id) and not request.POST.get("%s#starts_on" % price.id) == str(price.end_time)):
#                                    new_offer_price = request.POST.get("%s#offer_price" % price.id)
#                                    new_cashback_amount = request.POST.get("%s#cashback_amount" % price.id)
#                                    
#                                    new_starts_on = None
#                                    if request.POST.get("%s#starts_on" % price.id):
#                                        new_starts_on = request.POST.get("%s#starts_on" % price.id)
#                                        new_starts_on = datetime.datetime.strptime(new_starts_on,'%Y-%m-%d %H:%M:%S')
#                                        
#                                    new_ends_on = None
#                                    if request.POST.get("%s#ends_on" % price.id):
#                                        new_ends_on = request.POST.get("%s#ends_on" % price.id)
#                                        new_ends_on = datetime.datetime.strptime(new_ends_on,'%Y-%m-%d %H:%M:%S')
#
#
#                                    set_price_version(price, 'update', request.user.username, datetime.datetime.now(), new_list_price, new_offer_price, new_cashback_amount, new_starts_on, new_ends_on)
#            else:
#                errors.append('No active price maintained for this article!!!')
#                log.info('Rate chart does not exist either for sku=%s or article_id=%s' % (skuid, article_id))
#    
#    url = request.get_full_path()
#    prices_dict = {
#        'article_id':article_id,
#        'sku':skuid,
#        'pricelist_options':pricelist_options,
#        'all_prices':all_prices,
#        'list_price':list_price,
#        'updated_list_price':updated_list_price,
#        'searched_by':searched_by,
#        'product':product,
#        'product_image':product_image,
#        'update_prices':update_prices,
#        'delete_prices':delete_prices,
#        'if_any_changes':if_any_changes,
#        'is_pricing_tool_supported':is_pricing_tool_supported,
#        'errors':errors,
#        'flag':flag,
#        'seller_name':slugify(seller),
#        'client_name':client_name,
#	    'accounts':accounts,
#        'clients':clients,
#	    'url':url,
#        'loggedin':True
#        }
#    prices_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
#    return render_to_response('prices/search_by_sku.html', prices_dict, context_instance=RequestContext(request))


@never_cache
@login_required
@check_role('Reports')
def user_reports(request, client_name, seller_name, report_type, *args, **kwargs):
    url = request.get_full_path()
    if 'search_trend' not in url and "from" not in url and "order_id" not in url:
        if "?" in url:
            return HttpResponseRedirect(url+ '&search_trend=day&source=url')
        else:
            return HttpResponseRedirect(url+ '?search_trend=day&source=url')
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ppd-user-reports',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers','report_type':report_type}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ppd-user-reports',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,'report_type':report_type,}))
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
        
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('ppd-user-reports',None,kwargs={'client_name':profile.managed_clients[0].slug,'seller_name':'all-sellers','report_type':report_type})) 
    
    if seller_name=='all-sellers':
        if report_type != 'channel':
            return HttpResponsePermanentRedirect(reverse('ppd-user-reports',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),'report_type':report_type})) 
        else:
            current_seller_id = 0
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('ppd-user-reports',None,kwargs={'client_name':client_name,'seller_name':'all-sellers','report_type':report_type,})) 
    #seller = Account.objects.get(id=current_seller_id) 
    ### calling other fuctions
    if report_type == 'best_performing_sellers':
        return best_performing_sellers(request, client_name, seller_name, client_id, current_seller_id)
    elif report_type == 'seller_report':
        return seller_report(request,client_name, seller_name, client_id, current_seller_id)
    elif report_type == 'client_report':
        return client_report(request, client_name, seller_name, client_id, current_seller_id)
    elif report_type == 'store_report':
        return sales_by_agent_report_for_store(request, client_name, seller_name, client_id, current_seller_id)
    elif report_type == 'channel':
        return user_dashboard(request, client_name, seller_name)
    elif report_type == 'geography':
        return report_by_geography(request, client_name, seller_name, client_id, current_seller_id)
    elif report_type == 'category':
        return report_by_category(request, client_name, seller_name, client_id, current_seller_id)
    elif report_type == 'fulfilment':
        return user_report_by_fulfilment(request, client_name, seller_name)

def report_by_geography(request, client_name, seller_name, client_id, current_seller_id):
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
    pincodes, final_dict = {}, {}
    sales_pincodes, bookings, sales, avg_order, orders_count, city_list, city = [], [], [], [], [],[], {}
    dates = check_dates(request)
    from_date, to_date, search_trend = dates['start_date'], dates['end_date'], dates['search_trend']
    pincode_from_get = request.GET.get('pincode', 0)
    if pincode_from_get:
        delivery_info = DeliveryInfo.objects.using('tinla_slave').select_related('order__payable_amount').filter(address__pincode=pincode_from_get, order__state__in=['confirmed','pending_order'], order__client=client_id, order__orderitem__seller_rate_chart__seller=current_seller_id)
        total_booking_amount = delivery_info.aggregate(Sum('order__payable_amount'))['order__payable_amount__sum']
        delivery_info = DeliveryInfo.objects.using('tinla_slave').select_related('order__payable_amount').filter(address__pincode=pincode_from_get, order__state__in=['confirmed'], order__client=client_id, order__orderitem__seller_rate_chart__seller=current_seller_id)
        counter = delivery_info.count()
        total_sales_amount =delivery_info.aggregate(Sum('order__payable_amount'))['order__payable_amount__sum']
        if total_sales_amount:
            avg_order.append(total_sales_amount/counter)
        orders_count.append(counter)
        bookings.append(total_booking_amount)
        sales.append(total_sales_amount)
        sales_pincodes.append(pincode_from_get)
    else:
        order_items = OrderItem.objects.using('tinla_slave').select_related('order_id').filter(seller_rate_chart__seller=current_seller_id, order__client=client_id, order__state='confirmed', order__timestamp__lte=to_date+timedelta(days=1), order__timestamp__gte=from_date)
        for item in order_items:
            try:
                dinfo = item.order.get_delivery_info()
            except:
                dinfo = None
            if dinfo:
                pincode = dinfo.address.pincode
                if pincode not in pincodes:
                    pincodes[pincode]=1
                else:
                    check = pincodes[pincode]
                    pincodes[pincode] = check+1
        items = [(v,k) for k,v in pincodes.items()]
        items.sort()
        items.reverse()
        items = [(k,v) for (v,k) in items]
        for ele in items:
            pins = Pincode.objects.all()
            for pin in pins:
                if pin.pincode == ele[0]:
                    #if pin.city not in city_list:
                    city[pin.pincode] = pin.city
                    sales_pincodes.append(ele[0])
            if len(city)==20:
                break 
        count = 0
        for ele in sales_pincodes:
            delivery_info = DeliveryInfo.objects.using('tinla_slave').select_related('order__payable_amount').filter(address__pincode=sales_pincodes[count], order__state__in=['confirmed','pending_order'], order__client=client_id, order__orderitem__seller_rate_chart__seller=current_seller_id, order__timestamp__lte=to_date+timedelta(days=1), order__timestamp__gte=from_date)
            total_booking_amount = delivery_info.aggregate(Sum('order__payable_amount'))['order__payable_amount__sum']
            delivery_info = DeliveryInfo.objects.using('tinla_slave').select_related('order__payable_amount').filter(address__pincode=sales_pincodes[count], order__state__in=['confirmed'], order__client=client_id, order__orderitem__seller_rate_chart__seller=current_seller_id, order__timestamp__lte=to_date+timedelta(days=1), order__timestamp__gte=from_date)
            counter = delivery_info.count()
            total_sales_amount =delivery_info.aggregate(Sum('order__payable_amount'))['order__payable_amount__sum']
            orders_count.append(counter)
            bookings.append(total_booking_amount)
            sales.append(total_sales_amount)
            count = count+1
        
        count = 0
        for ele in sales_pincodes:
            if city[ele] in final_dict:
                final_dict[city[ele]] = (final_dict[city[ele]][0]+bookings[count], final_dict[city[ele]][1]+sales[count], final_dict[city[ele]][2]+orders_count[count], ((final_dict[city[ele]][1]+sales[count])/(final_dict[city[ele]][2]+orders_count[count])))
            else:
                final_dict[city[ele]] = (bookings[count], sales[count], orders_count[count], (sales[count]/orders_count[count]))
                count +=1
    
    save_excel = request.GET.get('excel')
    if save_excel == "True":
        excel_header = ['Pincodes', 'Bookings(Rs)', 'Sales(Rs)', 'Orders(#)','Avg Order(Rs)']       
        excel_data = []
        count = 0
        for a,b in final_dict.iteritems():
            excel_data.append((a, int(b[0]),int(b[1]),int(b[2]),int(b[3])))
        return save_excel_file(excel_header, excel_data)

    passing_dict={
            'pincode':pincode_from_get,
            'final_dict':final_dict,
            'loggedin':True,
            'orders_count':orders_count,
            'bookings':bookings,
            'sales':sales,
            'avg_order':avg_order,
            'search_trend':search_trend,
            'from_date':from_date,
            'to_date':to_date,
            'pincodes':sales_pincodes,
            'client_name':client_name,
            'seller_name':seller_name,
            'clients':clients,
            'accounts':accounts,
            'url':request.get_full_path()
            }
    passing_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
    return render_to_response('reports/report_by_geography.html',passing_dict, context_instance=RequestContext(request))

def report_by_category(request, client_name, seller_name, client_id, current_seller_id):
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
    categories, sales, bookings, orders_count, avg_order, categories_list, check = [], [], [], [], [],[], []
    cat_length = 0
    order_items_dict = {}
    dates = check_dates(request)
    from_date, to_date, search_trend = dates['start_date'], dates['end_date'], dates['search_trend']
    category_list = OrderItem.objects.select_related('seller_rate_chart__product__category__name').filter(seller_rate_chart__seller=current_seller_id, order__client=client_id, order__timestamp__lte=to_date, order__timestamp__gte=from_date, order__state='confirmed').values_list('seller_rate_chart__product__category__name', flat=True).distinct()
    flag=0 
    for category in category_list:
        order_items = OrderItem.objects.using('tinla_slave').select_related('order__payable_amount').filter(order__state='confirmed', seller_rate_chart__seller=current_seller_id, order__client=client_id, seller_rate_chart__product__category__name=category, order__timestamp__lte=to_date+timedelta(days=1), order__timestamp__gte=from_date)
        booking_items = OrderItem.objects.using('tinla_slave').select_related('order__payable_amount').filter(seller_rate_chart__seller=current_seller_id, order__client=client_id, seller_rate_chart__product__category__name=category).filter(Q(order__state='confirmed', order__payment_realized_on__gte=from_date, order__payment_realized_on__lte=to_date)|Q(order__state='pending_order', order__timestamp__gte=from_date, order__timestamp__lte=to_date))
        if order_items.count() != 0:
            categories_list.append(category_list[flag])
            orders_count.append(order_items.count())
            counter = order_items.count()
            order_items = order_items.aggregate(Sum('order__payable_amount'))['order__payable_amount__sum']
            avg_order.append(order_items/counter)
            booking_items = booking_items.aggregate(Sum('order__payable_amount'))['order__payable_amount__sum']
            sales.append(order_items) 
            bookings.append(booking_items)
        flag +=1
    url = request.get_full_path()
    save_excel = request.GET.get('excel')
     
    if save_excel == "True":
        excel_header = ['Categories', 'Bookings(Rs)', 'Sales(Rs)', 'Orders(#)','Avg Order(Rs)']       
        excel_data = []
        count = 0
        for ele in orders_count:
            excel_data.append([category_list[count],math.ceil(bookings[count]),math.ceil(sales[count]),orders_count[count],math.ceil(avg_order[count])])
            count +=1
        return save_excel_file(excel_header, excel_data)

    passing_dict = {
            'categories_list':category_list,
            'sales':sales,
            'bookings':bookings,
            'orders_count':orders_count,
            'avg_order':avg_order,
            'loggedin':True,
            'search_trend':search_trend,
            'from_date':from_date,
            'to_date':to_date,
            'accounts':accounts,
            'clients':clients,
            'client_name':client_name,
            'seller_name':seller_name,
            'url':url,
            'check':check,
            }
    passing_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
    return render_to_response('reports/report_by_category.html',passing_dict, context_instance=RequestContext(request))

def best_performing_sellers(request, client_name, seller_name, client_id, seller_id ):
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = client_id)
        cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
    dates = check_dates(request)
    from_date, to_date, search_trend = dates['start_date'], dates['end_date'], dates['search_trend']
    #source = cid 
    #client = cid#seller.client
    qs_oi = OrderItem.objects.filter(Q(order__timestamp__gte = from_date) & Q(order__timestamp__lte = to_date+timedelta(days=1)))
    qs_oi_book = qs_oi.filter(Q(order__state = "pending_order") | Q(order__state = "confirmed"))
    qs_oi_book = qs_oi_book.filter(seller_rate_chart__seller__in = utils.get_user_profile(request.user).managed_accounts.all())
    qs_oi_confirm = OrderItem.objects.filter(Q(order__payment_realized_on__gte = from_date) & Q(order__payment_realized_on__lte = to_date + timedelta(days=1)) & Q(order__state = "confirmed"))
    qs_oi_confirm = qs_oi_confirm.filter(seller_rate_chart__seller__in = utils.get_user_profile(request.user).managed_accounts.all())
    confirm_seller_info = {} #[seller_name, value]
    confirm_seller_volume = {}
    confirm_seller_order = []
    vol_data = {}
    show_volume = True
    for qs in qs_oi_confirm:
        if confirm_seller_info and qs.seller_rate_chart.seller.name in confirm_seller_info:
            confirm_seller_info[qs.seller_rate_chart.seller.name] += qs.payable_amount()
            if (qs.order_id,qs.seller_rate_chart.seller) not in confirm_seller_order:
                confirm_seller_order.append((qs.order_id,qs.seller_rate_chart.seller))
                confirm_seller_volume[qs.seller_rate_chart.seller.name] += 1
        else:
            confirm_seller_info[qs.seller_rate_chart.seller.name] = qs.payable_amount()
            confirm_seller_order.append((qs.order_id,qs.seller_rate_chart.seller))
            confirm_seller_volume[qs.seller_rate_chart.seller.name] = 1
    confirm_seller_info = sorted(confirm_seller_info.iteritems(),key=operator.itemgetter(1),reverse=True)
    confirm_seller_volume = sorted(confirm_seller_volume.iteritems(),key=operator.itemgetter(1),reverse=True)
    confirm_seller_info = confirm_seller_info[:5]
    confirm_seller_volume = confirm_seller_volume[:5]
    confirm_vol_name = ""
    confirm_vol_count = []
    vol_data['confirm_max_seller_vol'] = 0
    if confirm_seller_volume:
        vol_data['confirm_max_seller_vol'] = float(confirm_seller_volume[0][1])*1.2
    for c in confirm_seller_volume:
        confirm_vol_name = str(c[0]) + '|' + confirm_vol_name
        confirm_vol_count.append(c[1])
    vol_data['confirm_vol_name'] = confirm_vol_name[0:-1]
    vol_data['confirm_vol_count'] = confirm_vol_count
    confirm_max_seller = 0
    if confirm_seller_info:
        confirm_max_seller = float(confirm_seller_info[0][1])*1.2
    confirm_seller_name = ""
    confirm_seller_value = []
    for s in confirm_seller_info:
        confirm_seller_name = str(s[0]) + "|" + confirm_seller_name
        tmp = round(s[1]/1000,2)
        confirm_seller_value.append(tmp)
    confirm_seller_name = confirm_seller_name[0:-1]
    confirm_seller = [confirm_seller_name,confirm_seller_value]

    book_seller_info = {} #[seller_name, value]
    book_seller_order = []
    book_seller_volume = {}
    for qs in qs_oi_book:
        if book_seller_info and qs.seller_rate_chart.seller.name in book_seller_info:
            book_seller_info[qs.seller_rate_chart.seller.name] += qs.payable_amount()
            if (qs.order_id,qs.seller_rate_chart.seller) not in book_seller_order:
                book_seller_order.append((qs.order_id,qs.seller_rate_chart.seller))
                book_seller_volume[qs.seller_rate_chart.seller.name] += 1
        else:
            book_seller_info[qs.seller_rate_chart.seller.name] = qs.payable_amount()
            book_seller_order.append((qs.order_id,qs.seller_rate_chart.seller))
            book_seller_volume[qs.seller_rate_chart.seller.name] = 1
    book_seller_info = sorted(book_seller_info.iteritems(),key=operator.itemgetter(1),reverse=True)
    book_seller_volume = sorted(book_seller_volume.iteritems(),key=operator.itemgetter(1),reverse=True)
    book_seller_info = book_seller_info[:5]
    book_seller_volume = book_seller_volume[:5]
    book_vol_name = ""
    book_vol_count = []
    vol_data['book_max_seller_vol'] = 0
    if book_seller_volume:
        vol_data['book_max_seller_vol'] = float(book_seller_volume[0][1])*1.2
    for b in book_seller_volume:
        book_vol_name = str(b[0]) + '|' + book_vol_name
        book_vol_count.append(b[1])
    vol_data['book_vol_name'] = book_vol_name[0:-1]
    vol_data['book_vol_count'] = book_vol_count
    book_max_seller = 0
    if book_seller_info:
        book_max_seller = float(book_seller_info[0][1])*1.2
    book_seller_name = ""
    book_seller_value = []
    for s in book_seller_info:
        book_seller_name = str(s[0]) + "|" + book_seller_name
        tmp = round(s[1]/1000,2)
        book_seller_value.append(tmp)
    book_seller_name = book_seller_name[0:-1]
    book_seller = [book_seller_name,book_seller_value]
    tick = [8,29,50,71,92]
    make_tick = [tick[:len(book_seller[1])], tick[:len(confirm_seller[1])], tick[:len(vol_data['book_vol_count'])], tick[:len(vol_data['confirm_vol_count'])]]
    confirm_max_seller = confirm_max_seller/1000
    book_max_seller = book_max_seller/1000
    max_data = dict(confirm_max_seller=confirm_max_seller,book_max_seller=book_max_seller)
    data = dict(confirm_seller=confirm_seller,book_seller=book_seller)
    stores = Client.objects.all()
    url = request.get_full_path()
    reports_dict = {
        'show_volume':show_volume,
        'clients':clients,
        'accounts':accounts,
        'data':data,
        'max_data':max_data,
        'tick':make_tick,
        'stores':stores,
        'vol_data':vol_data,
        'from_date':from_date,
        'to_date':to_date,
        'seller_id':seller_id,
        'search_trend':search_trend,
        'url':url,
        'client_name':client_name,
        'seller_name':seller_name,
        'loggedin':True,
    }
    reports_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
    return render_to_response('ppd/best_performing_sellers.html', reports_dict, context_instance=RequestContext(request))

def seller_report(request, client_name, seller_name, client_id, seller_id):
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = account.client.id)
        cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
    dates = check_dates(request)
    from_date, to_date, search_trend = dates['start_date'], dates['end_date'], dates['search_trend']
    qs = ppd_booked_item_range(seller_name, seller_id, from_date,to_date,request)
    qs_oi_book = qs['qs']
    qs = ppd_confirmed_item_range(seller_name, seller_id, from_date,to_date,request)
    qs_oi_confirm = qs['qs']
    confirm_seller_info = {} #[seller_name, value]
    confirm_seller_volume = {}
    confirm_seller_order = []
    vol_data = {}
    show_volume = True

    for qs in qs_oi_confirm:
        if confirm_seller_info and qs.seller_rate_chart.seller.name in confirm_seller_info:
            confirm_seller_info[qs.seller_rate_chart.seller.name] += qs.payable_amount()
            if (qs.order_id,qs.seller_rate_chart.seller) not in confirm_seller_order:
                confirm_seller_order.append((qs.order_id,qs.seller_rate_chart.seller))
                confirm_seller_volume[qs.seller_rate_chart.seller.name] += 1
        else:
            confirm_seller_info[qs.seller_rate_chart.seller.name] = qs.payable_amount()
            confirm_seller_order.append((qs.order_id,qs.seller_rate_chart.seller))
            confirm_seller_volume[qs.seller_rate_chart.seller.name] = 1
    confirm_seller_info = sorted(confirm_seller_info.iteritems(),key=operator.itemgetter(1),reverse=True)
    confirm_seller_volume = sorted(confirm_seller_volume.iteritems(),key=operator.itemgetter(1),reverse=True)
    confirm_seller_info = confirm_seller_info[:5]
    confirm_seller_volume = confirm_seller_volume[:5]
    confirm_vol_name = ""
    confirm_vol_count = []
    vol_data['confirm_max_seller_vol'] = 0
    if confirm_seller_volume:
        vol_data['confirm_max_seller_vol'] = float(confirm_seller_volume[0][1])*1.2
    for c in confirm_seller_volume:
        confirm_vol_name = str(c[0]) + '|' + confirm_vol_name
        confirm_vol_count.append(c[1])
    vol_data['confirm_vol_name'] = confirm_vol_name[0:-1]
    vol_data['confirm_vol_count'] = confirm_vol_count
    confirm_max_seller = 0
    if confirm_seller_info:
        confirm_max_seller = float(confirm_seller_info[0][1])*1.2
    confirm_seller_name = ""
    confirm_seller_value = []
    for s in confirm_seller_info:
        confirm_seller_name = str(s[0]) + "|" + confirm_seller_name
        tmp = round(s[1]/1000,2)
        confirm_seller_value.append(tmp)
    confirm_seller_name = confirm_seller_name[0:-1]
    confirm_seller = [confirm_seller_name,confirm_seller_value]
    book_seller_info = {} #[seller_name, value]
    book_seller_order = []
    book_seller_volume = {}
    for qs in qs_oi_book:
        if book_seller_info and qs.seller_rate_chart.seller.name in book_seller_info:
            book_seller_info[qs.seller_rate_chart.seller.name] += qs.payable_amount()
            if (qs.order_id,qs.seller_rate_chart.seller) not in book_seller_order:
                book_seller_order.append((qs.order_id,qs.seller_rate_chart.seller))
                book_seller_volume[qs.seller_rate_chart.seller.name] += 1
        else:
            book_seller_info[qs.seller_rate_chart.seller.name] = qs.payable_amount()
            book_seller_order.append((qs.order_id,qs.seller_rate_chart.seller))
            book_seller_volume[qs.seller_rate_chart.seller.name] = 1
    book_seller_info = sorted(book_seller_info.iteritems(),key=operator.itemgetter(1),reverse=True)
    book_seller_volume = sorted(book_seller_volume.iteritems(),key=operator.itemgetter(1),reverse=True)
    book_seller_info = book_seller_info[:5]
    book_seller_volume = book_seller_volume[:5]
    book_vol_name = ""
    book_vol_count = []
    vol_data['book_max_seller_vol'] = 0
    if book_seller_volume:
        vol_data['book_max_seller_vol'] = float(book_seller_volume[0][1])*1.2
    for b in book_seller_volume:
        book_vol_name = str(b[0]) + '|' + book_vol_name
        book_vol_count.append(b[1])
    vol_data['book_vol_name'] = book_vol_name[0:-1]
    vol_data['book_vol_count'] = book_vol_count
    book_max_seller = 0
    if book_seller_info:
        book_max_seller = float(book_seller_info[0][1])*1.2
    book_seller_name = ""
    book_seller_value = []
    for s in book_seller_info:
        book_seller_name = str(s[0]) + "|" + book_seller_name
        tmp = round(s[1]/1000,2)
        book_seller_value.append(tmp)
    book_seller_name = book_seller_name[0:-1]
    book_seller = [book_seller_name,book_seller_value]
    tick = [8,29,50,71,92]
    make_tick = [tick[:len(book_seller[1])], tick[:len(confirm_seller[1])], tick[:len(vol_data['book_vol_count'])], tick[:len(vol_data['confirm_vol_count'])]]
    confirm_max_seller = confirm_max_seller/1000
    book_max_seller = book_max_seller/1000
    max_data = dict(confirm_max_seller=confirm_max_seller,book_max_seller=book_max_seller)
    data = dict(confirm_seller=confirm_seller,book_seller=book_seller)
    stores = Client.objects.all()
    title = "Seller report for " + "seller's name" 
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    url = request.get_full_path()
    client_id = int(request.GET.get('cid','1'))
    current_seller_id = request.GET.get('sid','1')
    typ = request.GET.get('typ')
    reports_dict = {
        'show_volume':show_volume,
        'url':url,
        'accounts':accounts,
        'clients':clients,
        'data':data,
        'max_data':max_data,
        'tick':make_tick,
        'stores':stores,
        'vol_data':vol_data,
        'from_date':from_date,
        'to_date':to_date,
        'search_trend':search_trend,
        'title':title,
        'client_name':client_name,
        'seller_name':seller_name,
        'loggedin':True
    } 
    reports_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
    return render_to_response('ppd/seller_report.html', reports_dict, context_instance=RequestContext(request))

def ppd_booked_order_range(show_for,seller,from_date,to_date,request):
    cid = request.GET.get('cid')
    source = cid#seller.client
    if show_for == "client":
        if source and source!=unicode(0):
            qs_book = Order.objects.filter(Q(state = "pending_order")|Q(state = "confirmed"),client = source, wstore__in = utils.get_user_profile(request.user).managed_accounts.all())
        else:
            qs_book = Order.objects.filter(Q(state = "pending_order") | Q(state = "confirmed"))
    if show_for == "seller":
        qs_book = Order.objects.filter(Q(state = "pending_order") | Q(state = "confirmed"),wstore=seller)

    qs = qs_book.filter(Q(timestamp__gte = from_date) & Q(timestamp__lte = to_date))
    return dict(qs=qs)

def ppd_confirmed_order_range(show_for,seller,from_date,to_date,request):
    cid = request.GET.get('cid')
    source = cid#seller.client
    if show_for == "client":
        if source and source!=unicode(0):
            qs_confirm = Order.objects.filter(state = "confirmed", client=source, wstore__in = utils.get_user_profile(request.user).managed_accounts.all())
        else:
            qs_confirm = Order.objects.filter(state = "confirmed")
    if show_for == "seller":
        qs_confirm = Order.objects.filter(state="confirmed", wstore=seller)
    qs = qs_confirm.filter(Q(payment_realized_on__gte = from_date) & Q(payment_realized_on__lte = to_date))
    return dict(qs=qs)

def client_report(request, client_name, seller_name, client_id, seller_id):
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = account.client.id)
        cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
    show_for = request.GET.get('show_for','client')
    dates = check_dates(request)
    from_date, to_date, search_trend = dates['start_date'], dates['end_date'], dates['search_trend']
    source = client_id 
    qs = ppd_booked_order_range(show_for,seller_id,from_date,to_date,request)
    qs_book = qs['qs']
    qs = ppd_confirmed_order_range(show_for,seller_id,from_date,to_date,request)
    qs_confirm = qs['qs']
    count = [qs_book.count(),qs_confirm.count()]
    max_index = count.index(max(count))
    max_count = 0
    if count[max_count]:
        max_count = count[max_index]*1.2
    values_book = qs_book.aggregate(Sum('payable_amount'))
    values_book = values_book['payable_amount__sum']
    values_confirm = qs_confirm.aggregate(Sum('payable_amount'))
    values_confirm = values_confirm['payable_amount__sum']
    values = [values_book,values_confirm]
    max_index = values.index(max(values))
    max_values = 0
    if values[max_index]:
        max_values = float(values[max_index])*1.2
    value_label = "Rs"
    if values[max_index]>100000:
        value_label = "Rs (lakh)"
        for i in range(2):
            if values[i]:
                values[i] /= 100000
            else:
                values[i] = 0
        max_values /= 100000
    tot_dates = (to_date-from_date).days
    dates = [from_date + timedelta(days=+x) for x in range(tot_dates)]
    visual_data=[]
    visual_data1=[]
    description = {"Date": ("date", "date"),"Volumeb":("number","Booked"),"Volumec":("number","Confirmed")}
    description1 = {"Date": ("date", "date"),"Valueb":("number","Booked"),"Valuec":("number","Confirmed")}
    for dd in dates:
        qs_confirm_daily = qs_confirm.filter(payment_realized_on__day = dd.day,payment_realized_on__month = dd.month, payment_realized_on__year = dd.year)
        qs_book_daily = qs_book.filter(timestamp__day = dd.day, timestamp__month = dd.month, timestamp__year = dd.year)
        v_confirm = qs_confirm_daily.aggregate(Sum('payable_amount'))
        v_confirm = v_confirm['payable_amount__sum']
        v_book = qs_book_daily.aggregate(Sum('payable_amount'))
        v_book = v_book['payable_amount__sum']
        if not v_book:
            v_book = 0
        if not v_confirm:
            v_confirm = 0
        visual_data.append({"Date":dd,"Volumeb":qs_book_daily.count(),"Volumec":qs_confirm_daily.count()})
        visual_data1.append({"Date":dd,"Valueb":int(v_book),"Valuec":int(v_confirm)})
    data_table = gviz_api.DataTable(description)
    data_table1 = gviz_api.DataTable(description1)
    data_table.LoadData(visual_data)
    data_table1.LoadData(visual_data1)
    jscode = data_table.ToJSCode("jscode_data",columns_order=("Date","Volumeb","Volumec"))
    jscode1 = data_table1.ToJSCode("jscode_data1",columns_order=("Date","Valueb","Valuec"))
    max_data = dict(max_count=max_count,max_values=max_values)
    data = dict(count=count,values=values)
    #stores = Client.objects.all()
    if show_for == "client":
        title = "Booked and Confirmed Orders for sellers of client: " + "client name" 
    elif show_for == "seller":
        title = "Booked and Confirmed Orders for seller: " + seller.name
    url = request.get_full_path()
    client_id = int(request.GET.get('cid','1'))
    current_seller_id = request.GET.get('sid','1')
    typ = request.GET.get('typ')
    reports_dict = {
        'data':data,
        'max_data':max_data,
        'label':value_label,
        'title':title,
        'typ':typ,
        'show_for_option':show_for,
        'jscode':jscode,
        'jscode1':jscode1,
        'from_date':from_date,
        'to_date':to_date,
        'search_trend':search_trend,
        'url':url,
        'clients':clients,
        'accounts':accounts,
        'client_name':client_name,
        'seller_name':seller_name,
        'loggedin':True
    }
    reports_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
    return render_to_response('ppd/client_report.html', reports_dict, context_instance=RequestContext(request))

def manage_seller_payouts(request):
    #perm = Permission.objects.get(name="Can change seller configurations")
    if request.user.has_perm('payouts.change_sellerconfigurations'):
        #Check if the user has permission
        SellerConfigurationsFormSet = modelformset_factory(SellerConfigurations, exclude=('seller',), extra=0)
        if request.method == "GET":
            formset = SellerConfigurationsFormSet()
        else:
            formset = SellerConfigurationsFormSet(request.POST)
            if formset.is_valid():
                formset.save()
        manage_seller_payouts_dict = {
            'formset': formset,
        }
        return render_to_response('ppd/manage_seller_payouts.html', manage_seller_payouts_dict, context_instance=RequestContext(request))
    else:
        manage_seller_payouts_dict = {
            'view_not_allowed': True,
        }
        return render_to_response('web/ppd_base.html', manage_seller_payouts_dict, context_instance=RequestContext(request))


def get_payment_options_form_obj(request, option):#option contains payment mode instance
    if option.payment_mode.code in ("deposit-transfer"):
        if request.method == "POST":
            if option.is_active == True:
                form = DepositForm(request.POST, instance = option, prefix = option.payment_mode.code)  
            else:
                form = DepositForm(instance=option, prefix = option.payment_mode.code)
        else:
            form =  DepositForm(instance=option, prefix = option.payment_mode.code)
        return {'form':form, 'type':'filled', 'payment_mode': option.payment_mode, 'client':option.client}

    if option.payment_mode.code == "cash":
        if request.method == "POST":
            if option.is_active == True:
                form = CashCollectionForm(request.POST, instance = option, prefix = option.payment_mode.code)  
            else:
                form = CashCollectionForm(instance=option, prefix = option.payment_mode.code)
        else:
            form = CashCollectionForm(instance=option, prefix = option.payment_mode.code)
        return {'form':form, 'type':'filled', 'payment_mode': option.payment_mode, 'client':option.client}
   
    if option.payment_mode.code == "cheque":
        if request.method == "POST":
            if option.is_active == True:
                form = ChequeForm(request.POST, instance = option, prefix = option.payment_mode.code)  
            else:
                form = ChequeForm(instance=option, prefix = option.payment_mode.code)
        else:
            form = ChequeForm(instance=option, prefix = option.payment_mode.code)
        return {'form':form, 'type':'filled', 'payment_mode': option.payment_mode, 'client':option.client}

    if option.payment_mode.code in ['store', 'card-at-store', 'cash-at-store',
            'cash-at-office']:
        if request.method == "POST":
            if option.is_active == True:
                form = StoreForm(request.POST, instance = option, prefix = option.payment_mode.code)  
            else:
                form = StoreForm(instance=option, prefix = option.payment_mode.code)
        else:
            form = StoreForm(instance=option, prefix = option.payment_mode.code)
        return {'form':form, 'type':'filled', 'payment_mode': option.payment_mode, 'client':option.client}
        


    if option.payment_mode.code in ["credit-card", "payback", "netbanking", "card-ivr", 
            "credit-card-emi-web","credit-card-emi-ivr", "debit-card", "cod", "cash-collection"]:
        return { 'type':'empty', 'payment_mode':option.payment_mode}

    else:
        if request.method == "POST":
            form = PaymentOptionForm(request.POST, instance = option, prefix = option.payment_mode.code)
        else:
            form = PaymentOptionForm(instance=option, prefix = option.payment_mode.code)
        return {'form':form, 'type':'filled', 'payment_mode': option.payment_mode, 'client':option.client}

def mixed_modes_popup(request,*args,**kwargs):
    option_id = kwargs['option_id']
    option = PaymentOption.objects.get(id=option_id)
    if request.method == 'GET':
        form_obj = get_payment_options_form_obj(request, option)
        return render_to_response('ppd/mixed_modes_popup.html',dict(form_obj=form_obj, option_id=option_id),context_instance=RequestContext(request))
    if request.method == 'POST':
        form_obj = get_payment_options_form_obj(request, option)
        if form_obj['type'] == "empty":
            return HttpResponse(simplejson.dumps(dict(status="ok",group_code=group_code)))
        if form_obj['form'].is_valid():
            mode = option.payment_mode
            option_form = form_obj['form'].save(commit=False)
            option_form.payment_mode = mode
            option_form.save()
            group_code=mode.group_code
            return HttpResponse(simplejson.dumps(dict(status="ok",group_code=group_code)))
        else:    #If the form is not valid
            return HttpResponse(simplejson.dumps(dict(status="error",error=form.errors)))

def grouped_modes_content(request, *args, **kwargs):
    code = kwargs['code']
    current_seller_id = kwargs['current_seller_id']
    current_seller = Account.objects.get(id=current_seller_id)
    option = PaymentOption.objects.get(payment_mode__code=code, account=current_seller, payment_mode__client=current_seller.client)
    group_code = option.payment_mode.group_code
    options = PaymentOption.objects.filter(payment_mode__group_code=group_code, account=current_seller, payment_mode__client=current_seller.client)
    return render_to_response('ppd/mixed_modes_display.html', dict(options=options, selected_option=option), context_instance=RequestContext(request))

def payment_option_on_or_off(request):
    option_code = request.POST['option']
    current_seller_id = request.POST['current_seller_id']
    option_grouped = request.POST['option_grouped']
    on_or_off = request.POST['on_or_off']
    domain_payment_option = DomainPaymentOptions.objects.get(id=option_code)
    # domain_payment_option = DomainPaymentOptions.objects.get(id=option_code)
    if on_or_off == 'on':
        domain_payment_option.is_active = True
        domain_payment_option.save()
    if on_or_off == 'off':
        domain_payment_option.is_active = False
        domain_payment_option.save()

    return HttpResponse('ok')

def activate_payment_option(request):
    option_id = request.POST['option']
    #client_id = request.POST['cid']
    is_active = request.POST['activate']
    is_active = True if is_active == 'True' else False
    #pm = PaymentMode.objects.get(id=option_id)
    po = PaymentOption.objects.get(id=option_id)
    po.is_active = is_active
    po.save()
    if not is_active:
        dpo = DomainPaymentOptions.objects.filter(payment_option__id=option_id)
        for d in dpo:
            d.is_active = False
            d.save()
    #except:
    #    if pm.code in ('cod','credit-card','payback','credit-card-emi-web','debit-card',
    #        'card-ivr', 'credit-card-emi-ivr', 'cash-collection') or is_active == False:
    #            po = PaymentOption(payment_mode_id=option_id, client_id=client_id)
    #            po.is_active = is_active
    #            po.save()
    #    elif pm.code in ('deposit-transfer') and is_active==True:
    #        deposit_po = DepositPaymentOptions.objects.filter(payment_mode=option_id, client=client_id)
    #        if deposit_po:
    #            PaymentOption(payment_mode=option_id, client=client_id).save()
    return HttpResponse('ok')


def order_taking_option(request):
    dpoid = request.POST['opid']
    option = request.POST['order_taking_option']
    #dpo = DomainPaymentOptions.objects.get(id=dpoid)
    dpo = DomainPaymentOptions.objects.get(id=dpoid)
    dpo.order_taking_option = option
    dpo.save()
    return HttpResponse('ok')


def second_factor_auth(request):
    clientdomain_id = request.POST['cd_id']
    second_auth = request.POST['second_factor_auth']
    cd = ClientDomain.objects.get(id=clientdomain_id)
    cd.is_second_factor_auth_reqd = (second_auth=='On') and True or False
    cd.save()
    return HttpResponse('ok')


def approve_or_disapprove_review(request):
    from datetime import datetime
    review_id = request.POST['on_id']
    on_or_off = request.POST['on_or_off']
    url = request.POST['url']
    review = Review.objects.get(id=review_id)
    if on_or_off == 'on':
        review.status='approved'
    if on_or_off == 'off':
        review.status = 'removed'
    review.modified_on = datetime.now()
    review.reviewed_by = utils.get_user_profile(request.user).full_name
    review.save()
    return HttpResponseRedirect(url)


def getMyAccountContext(request):
    path = request.path.split('/')
    ctxt = {'section':'settings'}
    if len(path)>4:
        tab = path[4]
        ctxt['section'] = tab 
    return ctxt

def handle_post(request, *args, **kwargs):
    page = request.path 
    template = page[1:] 
    if template not in ['activate.html']:
        raise Http404
    form = {}
    form['errors'] = []
    validators = {}

    # add validators 
    # contact information
    validators['name'] = dict(required=True, re=re.compile('^[a-zA-Z ]+$'))
    validators['mobile'] = dict(required=True, re=re.compile('^\d{10}$'))
    validators['email'] = dict(required=True, re=re.compile('^[a-zA-Z0-9._%-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$'))
    validators['company'] = dict(required=True, re=re.compile('^[a-zA-Z0-9 ]+$'))
    validators['category'] = dict(required=True, verb='select', field='Products you sell')

    keys = ['name','mobile','email','company','category']
    for key in keys:
        is_required = validators[key].get('required', False)
        verb = validators[key].get('verb', 'enter')
        field = validators[key].get('field','') or key.title().replace('_','')
        if is_required:
            if not request.POST.get(key,'').strip():
                form['errors'].append('Please %s %s' % (verb, field))
            else:
                if validators[key].get('re', None):
                    r = validators[key]['re']
                    if not r.match(request.POST.get(key,'')):
                        form['errors'].append('Please enter a valid %s' % field)

    if form['errors']:
        return render_to_response(template, dict(form=form),context_instance=RequestContext(request))
    else:
        body = ''
        keys = ['name', 'mobile', 'email', 'company', 'website', 'category', 'average_price', 'average_commissions', 'daily_responses', 'delivery_time', 'stocking', 'remarks']
        for key in request.POST.keys():
            body += key.title().replace('_','') + ': ' + request.POST[key] + '\n'
        # email to us
        send_mail('Phonepedeal | Activation Enquiry', body, 'noreply@chaupaati.com', settings.ENQUIRIES_TO)
        # email to them
        t = loader.get_template('contact_info.email')
        c = Context({'customer': dict(name=request.POST.get('name','Customer'), info=body)})
        contact_info = t.render(c) 
        send_mail('Phonepedeal | Activation Enquiry', contact_info, 'noreply@chaupaati.com', [request.POST['email']])
        return render_to_response('post-activate.html', dict(data=request.POST),
                context_instance=RequestContext(request))

def serve_static(request, *args, **kwargs):
    '''serves the static pages'''
    if 'page' not in kwargs:
        raise Http404

    if request.method == 'POST':
        return handle_post(request, *args, **kwargs)

    page = kwargs['page']

    # get the template
    if not page:
        page = 'home.html'

    template = 'ppd/' + page + '.html'
    return render_to_response(template, context_instance=RequestContext(request)) 

def robots(request):
    robots_txt = '''User-agent: *
Allow: /'''
    return HttpResponse(robots_txt, mimetype='text/plain')

def sitemap(request):
    sitemap = '''http://phonepedeal.com/
http://phonepedeal.com/solution.html
http://phonepedeal.com/platform.html
http://phonepedeal.com/casestudies.html
http://phonepedeal.com/about.html
http://phonepedeal.com/activate.html
http://phonepedeal.com/casestudy-ack.html'''
    return HttpResponse(sitemap, mimetype='text/plain')

def sales_by_agent_report_for_store(request, client_name, seller_name, client_id, sid, *args,**kwargs):
    save_excel = get_excel_status(request, "excel")
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = account.client.id)
        cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
    dates = check_dates(request)
    from_date, to_date, search_trend = dates['start_date'], dates['end_date'], dates['search_trend']

    pagination = {}
    order_items = []
    orderitems=[], 
    order_page_list=[]
    
    user_dict = get_user_dict(request, "prices", *args, **kwargs)
    account = Account.objects.get(id=sid)
    url = request.get_full_path()

    if utils.is_future_ecom(account.client):
        try:
            from web.views import user_views
            import re
            page_no = int(request.GET.get('page',1))
            medium = request.GET.get('medium','cc')
            items_per_page = 15
            orderitems = user_views.get_total_number_of_orders(request,client_id,sid, medium, None,from_date,to_date)
            paginator = Paginator(orderitems, 20) # Show 20 order_page_list per page
            try:
                page = int(request.GET.get('page', '1'))
            except ValueError:
                page = 1
        
            base_url = request.get_full_path()
            page_pattern = re.compile('[&?]page=\d+')
            base_url = page_pattern.sub('',base_url)
            page_pattern = re.compile('[&?]per_page=\d+')
            base_url = page_pattern.sub('',base_url)
            if base_url.find('?') == -1:
                base_url = base_url + '?'
            else:
                base_url = base_url + '&'
        
            pagination = getPaginationContext(page, paginator.num_pages, base_url) 
            try:
                order_page_list = paginator.page(page)
            except (EmptyPage, InvalidPage):
                order_page_list = paginator.page(paginator.num_pages)
          # total_pages = orderitems.count()/items_per_page
           # base_url = request.get_full_path()
           # page_pattern = re.compile('[&?]page=\d+')
           # base_url = page_pattern.sub('',base_url)
           # page_pattern = re.compile('[&?]per_page=\d+')
           # base_url = page_pattern.sub('',base_url)
           # if base_url.find('?') == -1:
           #     base_url = base_url + '?'
           # else:
           #     base_url = base_url + '&'
           # pagination = getPaginationContext(page_no, total_pages, base_url)
           # pagination['result_from'] = (page_no-1) * items_per_page + 1
           # pagination['result_to'] = utils.ternary(page_no*items_per_page > orderitems.count(), orderitems, page_no*items_per_page)
           # pagination = utils.getPaginationContext(page_no, total_pages, request.path)
           # startOrderIndex = ((page_no-1) * items_per_page + 1)
        except Exception,e:
            log.exception('Exception while rendering order history: %s' % repr(e))
            pass
    else:
        #Code to be added for generating reports for Holii, Hometown, etc.
        pass
   
    save_excel=request.GET.get('excel', None)
    if save_excel:
        excel_header = ['Order No', 'Article Id', 'SKU', 'Product Id', 'Quantity', 'Item Price', 'Total Amount', 'Payment Mode', 'Booking Date', 'Booking Agent', 'Order Confirmation Date', 'Confirming Agent']
        excel_data = []
        for order in order_page_list.object_list:
            excel_data.append([order.order, order.seller_rate_chart.article_id, order.seller_rate_chart.sku, order.seller_rate_chart.product.id,order.qty, order.sale_price, order.order.payable_amount,order.order.payment_mode, order.order.timestamp, order.order.booking_agent.name, order.order.confirming_date, order.order.confirming_agent.name])
        return save_excel_file(excel_header, excel_data)
    else:
        user_dict = get_user_dict(request, "storereport", *args, **kwargs) 
        order_history_dict = {
            'orderitems':order_page_list, 
            'clients':clients,
            'pagination':pagination,
            'title':'Store Report',
            'search_trend':search_trend,
            'from_date':from_date,
            'to_date':to_date,
            'url':url,
            'accounts':accounts,
            'client_name':client_name,
            'seller_name':seller_name,
            'loggedin':True,
            }
        order_history_dict['client_display_name']=Client.objects.filter(slug=client_name)[0].name
        return render_to_response('ppd/store_report.html', order_history_dict, context_instance=RequestContext(request))

@never_cache
@check_role('Inventory')
def inventory_module(request, client_name, seller_name, update_type,*args, **kwargs):
    client_name = slugify(client_name)
    seller_name = slugify(seller_name)
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ppd-user-inventory',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers','update_type':update_type}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ppd-user-inventory',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,'update_type':update_type}))
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
        
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('ppd-user-inventory',None,kwargs={'client_name':profile.managed_clients[0].slug,'seller_name':'all-sellers','update_type':update_type})) 
    
    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('ppd-user-inventory',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name),'update_type':update_type})) 
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            seller = seller[0]
            current_seller_id = seller.id
        else:
            return HttpResponsePermanentRedirect(reverse('ppd-user-inventory',None,kwargs={'client_name':client_name,'seller_name':'all-sellers','update-type':update_type})) 
    user_dict = get_user_dict(request, "prices", *args, **kwargs)
    
    #Populating the required fields for rendering Seller's Hub Pages
    count = 0
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    if update_type == 'inventory_bulk_upload':
        return inventory_bulk_upload(request, client_name, seller_name, seller, client_id, profile)
    if update_type == 'inventory_upload_success':
        return inventory_upload_success(request, client_name, seller_name, seller, client_id, profile)
    if update_type == 'inventory_articlelevel_update':
        return update_articlelevel_inventory(request, seller, client_id, client_name, seller_name, count, profile)
    #if update_type == 'otc_upload':
    #    return upload_otc_pincodes(request, seller, client_id, count, user_dict, profile)
    if update_type == 'slo_upload':
        return upload_pincodes(request, client_name, seller_name,seller, client_id, count, profile)
    if update_type == 'gen_reprt':
        return generate_inventory_report(request,client_name, seller_name,  seller, client_id, count, profile)
    if update_type == 'all_inventory':
        return show_all_inventory_levels(request,client_name, seller_name,  seller, client_id, profile)
    if update_type == 'edit_virtual_inventory':
        return edit_virtual_inventory(request,client_name, seller_name,  seller, client_id, profile)
    if update_type == 'add_vi':
        return add_virtual_inventory(request,client_name, seller_name,  seller, client_id, profile)
    if update_type == 'delete_vi':
        return delete_virtual_inventory(request,client_name, seller_name,  seller, client_id, profile)
    if update_type == 'edit_physical_inventory':
        return edit_physical_inventory(request,client_name, seller_name,  seller, client_id, profile)
    if update_type == 'edit_backorder':
        return edit_backorderable_entry(request,client_name, seller_name,  seller, client_id, profile)
    if update_type == 'sto':
        return sto_report(request,client_name, seller_name,  seller, client_id, profile)

#def show_all_inventory_levels(request,client_name, seller_name,  seller, client_id, count, profile):
#    #Show all the articles maintained for this client with increasing order of inventory levels.
#    accounts = profile.managed_accounts.filter(client__id = client_id)
#    clients = profile.managed_clients()
#
#    rate_chart = None
#    skuid = ""
#    article_id = ""
#    searched_by = ""
#    flag = ""
#    inventory = None
#    product_image = None
#    update_dict = None
#    is_clearance_item = False
#    delivery_time = None
#    errors = []
#    profile = request.user.get_profile() 
#    clients = profile.managed_clients()
#    accounts = profile.managed_accounts.filter(client__id = client_id)
#    is_clearance_item = False
#    all_inventory = None
#    is_global_dc_supported = utils.is_global_dc_maintained(seller.client)
#    
#    article_id = request.GET.get("articleid")
#    if not article_id and request.method == 'POST':
#        article_id = request.POST.get("articleid")
#
#    if article_id:
#        no_article_id_matching_entry = False
#        no_sku_matching_entry = False
#        try:
#            rate_chart = SellerRateChart.objects.get(article_id=article_id.strip(), seller=seller)
#            searched_by = 'article_id'
#        except SellerRateChart.DoesNotExist:
#            no_article_id_matching_entry = True
#        except SellerRateChart.MultipleObjectsReturned:
#            errors.append('Multiple articles maintained for Articleid - %s' % article_id)      
#
#        try:
#            rate_chart = SellerRateChart.objects.get(sku=article_id.strip(), seller=seller)
#            searched_by = 'article_id'
#        except SellerRateChart.DoesNotExist:
#            no_sku_matching_entry = True
#        except SellerRateChart.MultipleObjectsReturned:
#            errors.append('Multiple articles maintained for Articleid - %s' % article_id)      
#
#        if no_article_id_matching_entry and no_sku_matching_entry:
#            errors.append('No active article maintained for Articleid or SKU : %s' % article_id)
#        
#        if rate_chart:
#            flag = "searched"
#            #First, handling catalog specific prices               
#            try:
#                inventory = Inventory.objects.get(rate_chart=rate_chart)
#            except Inventory.DoesNotExist:
#                inventory = Inventory(rate_chart=rate_chart, stock=0)
#                inventory.save()
#
#    #                delivery_time_obj = None
#    #                try:
#    #                    delivery_time_obj = DeliveryTime.objects.get(inventory=inventory)
#    #                except DeliveryTime.DoesNotExist:
#    #                    delivery_time_obj = DeliveryTime(inventory=inventory, delivery_time=0)
#    #                    delivery_time_obj.save()
#    #
#    #                delivery_time = delivery_time_obj.delivery_time
#
#            product_image = ProductImage.objects.filter(product=rate_chart.product)
#            if product_image:
#                product_image = product_image[0]
#
#            clearance_list = None
#            is_clearance_item = False
#            
#            if utils.get_future_ecom_prod() == seller.client:
#                pass
#            else:
#                try:
#                    clearance_list = List.objects.get(type='clearance', client=seller.client)
#                except List.DoesNotExist:
#                    log.info('Clearance list does not exist!!')
#
#            if clearance_list:
#                try:
#                    listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
#                    is_clearance_item = True
#                except ListItem.DoesNotExist:
#                    pass 
#
#            if request.method == 'POST':
#                check = request.POST.get('name',None)
#                if check != 'change':
#                    if rate_chart:
#                        if request.POST.get("update") and request.POST.get("update") == "Update":
#                            flag = "updated"
#                            updated_stock = request.POST.get("stock")
#
#                            if is_global_dc_supported:
#                                updated_deliverytime = request.POST.get("delivery_time")
#
#                                if int(str(updated_deliverytime)) == 0:
#                                    errors.append('You cannot set delivery time to 0!!! Please go back and select appropriate value!!!')
#                            else:
#                                updated_virtual_stock = ''
#                                if request.POST.get('virtual_stock',''):
#                                    updated_virtual_stock = Decimal(str(request.POST.get('virtual_stock')))
#
#                                updated_expected_on = ''
#                                if request.POST.get('expected_on',''):
#                                    updated_expected_on = request.POST.get('expected_on') + ' '
#
#                                    if request.POST.get('expected_on#hr').strip():
#                                        updated_expected_on += request.POST.get('expected_on#hr')
#                                    else:
#                                        updated_expected_on += '00:'
#                                    
#                                    if request.POST.get('expected_on#min').strip():
#                                        updated_expected_on += request.POST.get('expected_on#min')
#                                    else:
#                                        updated_expected_on += '00'
#                                    
#                                    updated_expected_on = datetime.datetime.strptime(updated_expected_on,'%d-%m-%Y %H:%M')
#
#                                updated_expires_on = ''
#                                if request.POST.get('expires_on',''):
#                                    updated_expires_on = request.POST.get('expires_on') + ' '
#                                    if request.POST.get('expires_on#hr').strip():
#                                        updated_expires_on += request.POST.get('expires_on#hr') + ':'
#                                    else:
#                                        updated_expires_on += '00:'
#
#                                    if request.POST.get('expires_on#min').strip():
#                                        updated_expires_on += request.POST.get('expires_on#min')
#                                    else:
#                                        updated_expires_on += '00'
#                                    updated_expires_on = datetime.datetime.strptime(updated_expires_on,'%d-%m-%Y %H:%M')
#
#                                if not ((updated_virtual_stock and updated_expected_on and updated_expires_on) or (not updated_virtual_stock and not updated_expected_on and not updated_expires_on)):
#                                    errors.append('Please maintain values for all the three fields: "Virtual Stock", "Expected On" and "Expires On". [Note: If you do not want to maintain virtual stock, simply keep all the three fields blank!!!]')
#                                else:
#                                    if updated_expected_on and (updated_expected_on <= datetime.datetime.now()):
#                                        errors.append('Please maintain "Expected On" as some future time slot!!!')
#                                    if updated_expires_on and (updated_expires_on <= datetime.datetime.now()):
#                                        errors.append('Please maintain "Expires On" as some future time slot!!!')
#
#                                updated_threshold_stock = ''
#                                if request.POST.get('threshold_stock'):
#                                    updated_threshold_stock = Decimal(str(request.POST.get('threshold_stock')))
#
#                            updated_so = False
#                            if request.POST.get("so") == 'selected':
#                                updated_so = True
#
#                            updated_cod = False
#                            if request.POST.get("cod") == 'selected':
#                                updated_cod = True
#
#                            updated_clearance = False
#                            if request.POST.get("clearance") == 'selected':
#                                updated_clearance = True
#
#                            update_dict = {
#                                'stock':Decimal(str(updated_stock).strip()),
#                                'so':updated_so,
#                                'cod':updated_cod,
#                                'clearance':updated_clearance,
#                                }
#
#                            if is_global_dc_supported:
#                                update_dict.update({'delivery_time':int(str(updated_deliverytime).strip())})
#                            else:
#                                extra_params = {
#                                    'virtual_stock':Decimal(str(updated_virtual_stock).strip()) if updated_virtual_stock else '--',
#                                    'expires_on':updated_expires_on if updated_expires_on else '--',
#                                    'expected_on':updated_expected_on if updated_expected_on else '--',
#                                    'threshold_stock':Decimal(str(updated_threshold_stock).strip()) if updated_threshold_stock else '--',
#                                    }
#                                update_dict.update(extra_params)
#
#                        if request.POST.get("confirm") and request.POST.get("confirm") == "Confirm":
#                            inventory_log = InventoryLog()
#                            flag = "confirmed"
#                            updated_stock = request.POST.get("stock")
#                            inventory_log.was_physical_stock = inventory.stock
#                            inventory_log.new_physical_stock = updated_stock
#                            if is_global_dc_supported:
#                                updated_deliverytime = request.POST.get("delivery_time")
#                            else:
#                                updated_virtual_stock = None
#                                if request.POST.get('virtual_stock').strip() != '--':
#                                    updated_virtual_stock = Decimal(str(request.POST.get('virtual_stock')))
#                                inventory_log.was_virtual_stock = inventory.virtual_stock
#                                inventory_log.new_virtual_stock = updated_virtual_stock
#
#                                updated_expected_on = None
#                                if request.POST.get('expected_on').strip() != '--':
#                                    updated_expected_on = datetime.datetime.strptime(request.POST.get('expected_on'),'%Y-%m-%d %H:%M:%S')
#                                inventory_log.was_expected_on = inventory.expected_on
#                                inventory_log.new_expected_on = updated_expected_on
#
#                                updated_expires_on = None
#                                if request.POST.get('expires_on').strip() != '--':
#                                    updated_expires_on = datetime.datetime.strptime(request.POST.get('expires_on'),'%Y-%m-%d %H:%M:%S')
#                                inventory_log.was_expires_on = inventory.expires_on
#                                inventory_log.new_expires_on = updated_expires_on
#
#                                updated_threshold_stock = None
#                                if request.POST.get('threshold_stock').strip() != '--':
#                                    updated_threshold_stock = Decimal(str(request.POST.get('threshold_stock')))
#                                inventory_log.was_threshold_stock = inventory.threshold_stock
#                                inventory_log.new_threshold_stock = updated_threshold_stock
#
#                                inventory_log.rate_chart = inventory.rate_chart
#                                inventory_log.dc = inventory.dc
#                                inventory_log.was_overbooked = inventory.overbooked
#                                inventory_log.new_overbooked = inventory.overbooked
#                                inventory_log.user = request.user
#                                inventory_log.modified_by = 'admin'
#
#        #                    updated_otc = False
#        #                    if request.POST.get("otc") == 'selected':
#        #                        updated_otc = True
#
#                            updated_so = False
#                            if request.POST.get("so") == 'selected':
#                                updated_so = True
#                             
#                            updated_cod = False
#                            if request.POST.get("cod") == 'selected':
#                                updated_cod = True               
#
#                            inventory.stock = Decimal(str(updated_stock))
#                            if not is_global_dc_supported:
#                                inventory.virtual_stock = updated_virtual_stock
#                                inventory.expected_on = updated_expected_on
#                                inventory.expires_on = updated_expires_on
#                                inventory.threshold_stock = updated_threshold_stock
#                            inventory_log.save()
#                            inventory.save()
#
#        #                    delivery_time_obj.delivery_time = int(str(updated_deliverytime))
#        #                    delivery_time_obj.save()
#
#                            #rate_chart.otc = updated_otc
#                            rate_chart.ship_local_only = updated_so
#                            rate_chart.is_cod_available = updated_cod
#                            if is_global_dc_supported:
#                                rate_chart.shipping_duration = Decimal(str(updated_deliverytime))
#                            if inventory.stock:
#                                rate_chart.stock_status = 'instock'
#                            else:
#                                rate_chart.stock_status = 'outofstock'
#                            
#                            rate_chart.save()
#
#                            #Update solr index.
#                            product = rate_chart.product
#                            product.update_solr_index()
#
#                            if request.POST.get("clearance") == 'selected':
#                                #Check whether product belongs to clearance sale or not
#                                if clearance_list:
#                                    try:
#                                        listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
#                                    except ListItem.DoesNotExist:
#                                        #Listitem does not exist, so add new one
#                                        max_seq = clearance_list.listitem_set.all().aggregate(max=Max('sequence'))
#                                        listitem = ListItem(list=clearance_list, sku=rate_chart, sequence=max_seq.get('max',0)+1)
#                                        listitem.save()
#                            else:
#                                try:
#                                    listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
#                                    listitem.delete()
#                                except ListItem.DoesNotExist:
#                                    log.info('listitem object does not exist in clarance list')
#                            all_inventory = Inventory.objects.select_related('rate_chart','rate_chart__article_id').filter(rate_chart__seller=seller).order_by('stock','rate_chart__article_id')
#        else:
#            log.info('Rate chart does not exist either for sku=%s or article_id=%s' % (skuid, article_id))
#            if not errors:
#                errors.append('No inventory levels maintained for this article!!!')
#    else:
#        all_inventory = Inventory.objects.select_related('rate_chart','rate_chart__article_id').filter(rate_chart__seller=seller).order_by('stock','rate_chart__article_id')
#
#    inventory_dict = {
#        'accounts' : accounts,
#        'url' : request.get_full_path(),
#        'article_id':article_id,
#        'sku':skuid,
#        'inventory':inventory,
#        'rate_chart':rate_chart,
#        'is_clearance_item':is_clearance_item,
#        'all_inventory':all_inventory,
#        'product_image':product_image,
#        'updates':update_dict,
#        'searched_by':searched_by,
#        'flag':flag,
#        'errors':errors,
#        'client_name':client_name,
#        'seller_name':seller_name,
#        'loggedin':True,
#        'clients':clients,
#        'client_display_name':Client.objects.filter(slug=client_name)[0].name,
#        'is_global_dc_supported' : is_global_dc_supported,
#    }
#    return render_to_response('inventory/all_inventory1.html', inventory_dict, context_instance=RequestContext(request))  
#      
#def generate_inventory_report(request, client_name, seller_name, seller, client_id, count,profile):
#    from web.sbf_forms import FileUploadForm
#    import os
#    errors, message = [], None
#    current_inventory = None
#    form = None
#    to_update = None
#    path_to_save = None
#    flag = None
#    accounts = profile.managed_accounts.filter(client__id = client_id)
#    clients = profile.managed_clients()
#    
#    if request.method == 'POST':
#        flag = "report"
#        if request.POST.get("upload") == 'Generate Report':
#            import xlrd
#            form = FileUploadForm(request.POST, request.FILES)
#            if form.is_valid():
#                path_to_save = save_uploaded_file(request.FILES['status_file'])
#                errors, current_inventory = get_current_inventory(path_to_save, seller)
#            else:
#                errors.append('Please select the excel file and then click upload!!!')
#                form = FileUploadForm()
#                flag = 'new'            
#            #Delete the uploaded excel file
#            if path_to_save:
#                os.remove(path_to_save)
#    else:
#        flag = "new"
#        form = FileUploadForm()
#    
#    inventory_dict = {
#	    'accounts':accounts,
#        'clients':clients,
#        'client_name':client_name,
#        'seller_name':seller_name,
#        'flag':flag,
#        'forms':form,
#        'errors':errors,
#        'current_inventory':current_inventory,
#        'url':request.get_full_path(),
#        'loggedin':True,
#        }
#    return render_to_response('inventory/report.html', inventory_dict, context_instance=RequestContext(request)) 
#
#def get_current_inventory(path_to_save, seller):
#    import xlrd
#    from django.db.models import Q
#    book = xlrd.open_workbook(path_to_save)
#    sh = book.sheet_by_index(0)
#    header = sh.row(0)
#    map = {}
#    idx = 0
#    for idx in range(sh.ncols):
#        map[header[idx].value.strip().lower()] = idx
#    errors = []
#    to_update = []
#    consolidated_updates = []
#    action_dict = {True:'YES', False:'NO'}
#
#    for row_count in range(1, sh.nrows):
#        row = sh.row(row_count)
#        try:
#            article_id = row[map['articleid']].value
#
#            to_update.append({
#                'article_id': str(article_id).split('.')[0],
#            })
#        except KeyError:
#            errors.append('Unsupported excel file.')
#            break
#            
#    if to_update:
#        consolidated_updates = []
#        for item in to_update:
#            try:
#                rate_chart = SellerRateChart.objects.get(article_id=item['article_id'], seller=seller)
#
#                inventory = None
#                stock = 0
#                try:
#                    inventory = Inventory.objects.get(rate_chart=rate_chart)
#                    stock = inventory.stock
#                except Inventory.DoesNotExist:
#                    log.info('Inventory not maintained for article-id=%s' % item['article_id'])
#
#                inventory_dict = {
#                    'product_name' : rate_chart.product.title,
#                    'article_id' : item['article_id'],
#                    'current_stock' : stock,
#                    'current_otc' : action_dict.get(rate_chart.otc,'--'),
#                    'current_cod' : action_dict.get(rate_chart.is_cod_available,'--'),
#                    'current_so' : action_dict.get(rate_chart.ship_local_only,'--'),
#                    }
#
#                consolidated_updates.append(inventory_dict)
#
#            except SellerRateChart.DoesNotExist:
#                errors.append('No active article maintained for Articleid - %s' % item['article_id'])
#            except SellerRateChart.MultipleObjectsReturned:
#                errors.append('Multiple articles maintained for Articleid - %s' % item['article_id'])
#    else:
#        log.info('no prices to upload in the sheet!!!')
#        errors.append('no prices to upload in the sheet!!!')
#
#    return errors, consolidated_updates
#
#def upload_pincodes(request,client_name, seller_name,  seller, cid, c, profile):
#    from web.sbf_forms import FileUploadForm
#    from django.utils import simplejson
#    errors, message = [], None
#    consolidated_updates = None
#    form = None
#    flag = None
#    to_update, to_update_json = None, None
#    path_to_save = None
#    accounts = profile.managed_accounts.filter(client__id = cid)
#    clients = profile.managed_clients()
#    consolidated_so_updates, consolidated_otc_updates = [],[]
#
#    if request.method == 'POST':
#        if request.POST.get("upload") == 'Upload':
#            import xlrd
#            form = FileUploadForm(request.POST, request.FILES)
#            if form.is_valid():
#                path_to_save = save_uploaded_file(request.FILES['status_file'])
#                error, to_update = get_parsed_upload_pins_excel(path_to_save)
#                to_update_json = simplejson.dumps(to_update)
#                if not error:
#                    error, consolidated_so_updates, consolidated_otc_updates = get_pincodes(to_update, seller, False)
#            
#                if error:
#                    errors.append(error)
#                flag = 'show_details'
#            else:
#                errors.append('Please select the excel file and then click upload!!!')
#                form = FileUploadForm()
#                flag = 'new'
#
#        elif request.POST.get("update") == 'Update':
#            #path_to_save = request.POST.get("path_to_save")
#            to_update_json = request.POST.get("to_update_json")
#            to_update = simplejson.loads(to_update_json)
#            error, consolidated_so_updates, consolidated_otc_updates = get_pincodes(to_update, seller, True)
#            
#            if error:
#                errors.append(error)
#            flag = 'updated'
#            form = FileUploadForm()
#    else:
#        form = FileUploadForm()
#        flag = 'new'
#    
#    so_dict = {
#	    'accounts' : accounts,
#        'clients':clients,
#        'forms' : form,
#        'client_name':client_name,
#        'seller_name':seller_name,
#        'errors' : errors,
#        'to_update_json':to_update_json,
#        'consolidated_so_updates' : consolidated_so_updates,
#        'consolidated_otc_updates' : consolidated_otc_updates,
#        'flag' : flag,
#        'path_to_save' : path_to_save,
#        'url' : request.get_full_path(),
#        'loggedin':True,
#        }
#    return render_to_response('inventory/so_upload.html', so_dict, context_instance=RequestContext(request))
#
#def get_parsed_upload_pins_excel(path_to_save):
#    import xlrd
#    try:
#        book = xlrd.open_workbook(path_to_save)
#    except XLRDError:
#        return 'Inalid File Format','Inalid File Format'
#    sh = book.sheet_by_index(0)
#    header = sh.row(0)
#    map = {}
#    idx = 0
#    for idx in range(sh.ncols):
#        map[header[idx].value.strip().lower()] = idx
#    errors = []
#    to_update = []
#
#    for row_count in range(1, sh.nrows):
#        row = sh.row(row_count)
#        try:
#            article_id = str(int(row[map['articleid']].value))
#            action = row[map['action']].value
#            dc = row[map['dc']].value
#            stock = str(row[map['physical_stock']].value)
#
#            virtual_stock = ''
#            try:
#                virtual_stock = row[map['virtual_stock']].value
#            except KeyError:
#                pass
#
#            expires_on = ''
#            try:
#                expires_on = row[map['expires_on']].value
#            except KeyError:
#                pass
#            
#            expected_on = ''
#            try:
#                expected_on = row[map['expected_on']].value
#            except KeyError:
#                pass
#           
#            threshold_stock = ''
#            try:
#                threshold_stock = row[map['threshold_stock']].value
#            except KeyError:
#                pass
#
#            otc = 'no'
#            try:
#                otc = row[map['otc']].value
#            except KeyError:
#                pass
#            
#            cod = 'no'
#            try:
#                cod = row[map['cod']].value
#            except KeyError:
#                pass
#
#            so = 'no'
#            try:
#                so = row[map['so']].value
#            except KeyError:
#                pass
#
#            clearance = 'no'
#            try:
#                clearance = row[map['clearance']].value
#            except KeyError:
#                pass
#
#            delivery_time = ''
#            try:
#                delivery_time = int(row[map['delivery time']].value)
#            except KeyError:
#                pass
#            
#            add_dict = {
#                'article_id': str(article_id).strip().split('.')[0],
#                'action': action.strip().lower(),
#                'stock' : str(stock).strip().split('.')[0],
#                'virtual_stock' : str(virtual_stock).strip().split('.')[0],
#                'expires_on' : expires_on,
#                'expected_on' : expected_on,
#                'threshold_stock' : str(threshold_stock).strip().split('.')[0],
#                'dc' : str(dc).strip().split('.')[0],
#                'otc' : otc.strip().lower(),
#                'cod': cod.strip().lower(),
#                'so': so.strip().lower(),
#                'clearance': clearance.strip().lower(),
#                'delivery_time' : delivery_time,
#                }
#
#            repeated = False
#            for item in to_update:
#                if (item['article_id'] == add_dict['article_id']) and (item['dc'] == add_dict['dc']):
#                    repeated = True
#                    break
#
#            if not repeated:
#                to_update.append(add_dict)
#                if not add_dict['article_id'] in article_id_list:
#                    article_id_list.append(add_dict['article_id'])
#            else:
#                errors.append('Duplicate entry for Articleid: %s and DC: %s combination!!! Please correct the error and and try to upload again!!!' % (item['article_id'],item['dc']))
#        except KeyError:
#            errors.append('Unsupported excel file.')
#            break
#
#    return errors, to_update
#
#def get_pincodes(to_update, seller, save_changes):
##    import xlrd
#    from django.db.models import Q
#    from catalog.models import Pincode
##
##    book = xlrd.open_workbook(path_to_save)
##    sh = book.sheet_by_index(0)
##    header = sh.row(0)
##    map = {}
##    idx = 0
##    for idx in range(sh.ncols):
##        map[header[idx].value.strip().lower()] = idx
#    errors = []
##    to_update = []
#    consolidated_so_updates = []
#    consolidated_otc_updates = []
##
##    for row_count in range(1, sh.nrows):
##        row = sh.row(row_count)
##        try:
##            pincode = row[map['pincode']].value
##            type = row[map['type']].value
##            action = row[map['action']].value
##            to_update.append({
##                'pincode': str(pincode).split('.')[0],
##                'type': str(type).split('.')[0].upper(),
##                'action': action.strip().upper(),
##            })
##        except KeyError:
##            errors.append('Unsupported excel file.')
##            break
#            
#    if to_update:
#        consolidated_updates = []
#        for item in to_update:
#            servicable_pincode,current_status = None, None
#            try:
#                servicable_pincode = ServicablePincodes.objects.get(pincode__pin=item['pincode'], client=seller.client, service_type=item['type'])
#                current_status = 'Yes'
#            except ServicablePincodes.DoesNotExist:
#                current_status = 'No'
#
#            if save_changes:
#                if item['action'] == 'ADD':
#                    if servicable_pincode:
#                        pass #As it is already under list of servicable pincodes, do nothing
#                    else:
#                        pincode = None
#                        try:
#                            pincode = Pincode.objects.get(pin=item['pincode'])
#                        except Pincode.DoesNotExist:
#                            pincode = Pincode(pin=item['pincode'])
#                            pincode.save()
#
#                        servicable_pincode = ServicablePincodes(pincode=pincode, client=seller.client, service_type=item['type'])
#                        servicable_pincode.save()
#                elif item['action'] == 'DELETE':
#                    if servicable_pincode:
#                        servicable_pincode.delete()
#                    else:
#                        pass #Do nothing as pincode is not listed in servicable pincodes
#
#            
#            if item['type'] == 'SO':
#                so_dict = {
#                    'pincode': item['pincode'],
#                    'action':item['action'],
#                    'current_status':current_status,
#                    }
#
#                consolidated_so_updates.append(so_dict)
#            elif item['type'] == 'OTC':
#                otc_dict = {
#                    'pincode': item['pincode'],
#                    'action':item['action'],
#                    'current_status':current_status,
#                    }
#
#                consolidated_otc_updates.append(otc_dict)
#    else:
#        log.info('no prices to upload in the sheet!!!')
#
#    return errors, consolidated_so_updates, consolidated_otc_updates
#
#def update_articlelevel_inventory(request, seller, client_id, client_name, seller_name, c, profile):
#    rate_chart = None
#    skuid = ""
#    article_id = ""
#    searched_by = ""
#    flag = ""
#    inventory = None
#    product_image = None
#    update_dict = None
#    is_clearance_item = False
#    delivery_time = None
#    errors = []
#    profile = request.user.get_profile() 
#    clients = profile.managed_clients()
#    accounts = profile.managed_accounts.filter(client__id = client_id)
#    is_clearance_item = False
#    is_global_dc_supported = utils.is_global_dc_maintained(seller.client)
#    if request.method == 'POST':
#        check = request.POST.get('name',None)
#        if check != 'change':
#            from pricing.models import Price
#
#            skuid = request.POST.get("sku")
#            article_id = request.POST.get("articleid")
#
#            if not (skuid or article_id):
#                errors.append('Please enter either SKU or Article id and then click search!!!')
#
#            if skuid:
#                try:
#                    rate_chart = SellerRateChart.objects.get(sku=skuid.strip(), seller=seller)
#                    searched_by = 'skuid'
#                    article_id = rate_chart.article_id
#                except SellerRateChart.DoesNotExist:
#                    errors.append('No active article maintained for SKU - %s' % skuid)
#                except SellerRateChart.MultipleObjectsReturned:
#                    errors.append('Multiple active articles maintained for SKU - %s' % skuid)
#            elif article_id:
#                try:
#                    rate_chart = SellerRateChart.objects.get(article_id=article_id.strip(), seller=seller)
#                    searched_by = 'article_id'
#                    skuid = rate_chart.sku
#                except SellerRateChart.DoesNotExist:
#                    errors.append('No active article maintained for Articleid - %s' % article_id)
#                except SellerRateChart.MultipleObjectsReturned:
#                    errors.append('Multiple active articles maintained for Articleid - %s' % article_id)
#               
#            if rate_chart:
#                flag = "searched"
#                #First, handling catalog specific prices               
#                try:
#                    inventory = Inventory.objects.get(rate_chart=rate_chart)
#                except Inventory.DoesNotExist:
#                    inventory = Inventory(rate_chart=rate_chart, stock=0)
#                    inventory.save()
#
##                delivery_time_obj = None
##                try:
##                    delivery_time_obj = DeliveryTime.objects.get(inventory=inventory)
##                except DeliveryTime.DoesNotExist:
##                    delivery_time_obj = DeliveryTime(inventory=inventory, delivery_time=0)
##                    delivery_time_obj.save()
##
##                delivery_time = delivery_time_obj.delivery_time
#
#                product_image = ProductImage.objects.filter(product=rate_chart.product)
#                if product_image:
#                    product_image = product_image[0]
#
#                clearance_list = None
#                is_clearance_item = False
#                
#                if utils.get_future_ecom_prod() == seller.client:
#                    pass
#                else:
#                    try:
#                        clearance_list = List.objects.get(type='clearance', client=seller.client)
#                    except List.DoesNotExist:
#                        log.info('Clearance list does not exist!!')
#
#                if clearance_list:
#                    try:
#                        listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
#                        is_clearance_item = True
#                    except ListItem.DoesNotExist:
#                        pass 
#
#                if request.POST.get("update") and request.POST.get("update") == "Update":
#                    flag = "updated"
#                    updated_stock = request.POST.get("stock")
#                    updated_deliverytime = request.POST.get("delivery_time")
#
#                    if int(str(updated_deliverytime)) == 0:
#                        errors.append('You cannot set delivery time to 0!!! Please go back and select appropriate value!!!')
##                    updated_otc = False
##                    if request.POST.get("otc") == 'selected':
##                        updated_otc = True
#
#                    updated_so = False
#                    if request.POST.get("so") == 'selected':
#                        updated_so = True
#
#                    updated_cod = False
#                    if request.POST.get("cod") == 'selected':
#                        updated_cod = True
#
#                    updated_clearance = False
#                    if request.POST.get("clearance") == 'selected':
#                        updated_clearance = True
#
#                    update_dict = {
#                        'stock':Decimal(str(updated_stock).strip()),
#                        'delivery_time':int(str(updated_deliverytime).strip()),
#                        #'otc':updated_otc,
#                        'so':updated_so,
#                        'cod':updated_cod,
#                        'clearance':updated_clearance,
#                        }
#
#
#                if request.POST.get("confirm") and request.POST.get("confirm") == "Confirm":
#                    flag = "confirmed"
#                    updated_stock = request.POST.get("stock")
#                    updated_deliverytime = request.POST.get("delivery_time")
##                    updated_otc = False
##                    if request.POST.get("otc") == 'selected':
##                        updated_otc = True
#
#                    updated_so = False
#                    if request.POST.get("so") == 'selected':
#                        updated_so = True
#                     
#                    updated_cod = False
#                    if request.POST.get("cod") == 'selected':
#                        updated_cod = True               
#
#                    inventory.stock = Decimal(str(updated_stock))
#                    inventory.save()
#
##                    delivery_time_obj.delivery_time = int(str(updated_deliverytime))
##                    delivery_time_obj.save()
#
#                    #rate_chart.otc = updated_otc
#                    rate_chart.ship_local_only = updated_so
#                    rate_chart.is_cod_available = updated_cod
#                    rate_chart.shipping_duration = Decimal(str(updated_deliverytime))
#                    if inventory.stock:
#                        rate_chart.stock_status = 'instock'
#                    else:
#                        rate_chart.stock_status = 'outofstock'
#                    
#                    rate_chart.save()
#
#                    #Update solr index.
#                    product = rate_chart.product
#                    product.update_solr_index()
#
#                    if request.POST.get("clearance") == 'selected':
#                        #Check whether product belongs to clearance sale or not
#                        if clearance_list:
#                            try:
#                                listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
#                            except ListItem.DoesNotExist:
#                                #Listitem does not exist, so add new one
#                                max_seq = clearance_list.listitem_set.all().aggregate(max=Max('sequence'))
#                                listitem = ListItem(list=clearance_list, sku=rate_chart, sequence=max_seq.get('max',0)+1)
#                                listitem.save()
#                    else:
#                        try:
#                            listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
#                            listitem.delete()
#                        except ListItem.DoesNotExist:
#                            log.info('listitem object does not exist in clarance list')
#
#                    #flag = 'new'
#                    #show_all_inventory_levels(request,client_name, seller_name,  seller, client_id, c, profile, flag)
#
#            else:
#                log.info('Rate chart does not exist either for sku=%s or article_id=%s' % (skuid, article_id))
#                if not errors:
#                    errors.append('No inventory levels maintained for this article!!!')
#           
#    inventory_dict = {
#        'accounts' : accounts,
#        'url' : request.get_full_path(),
#        'article_id':article_id,
#        'sku':skuid,
#        'inventory':inventory,
#        'rate_chart':rate_chart,
#        'is_clearance_item':is_clearance_item,
#        #'delivery_time':delivery_time,
#        'product_image':product_image,
#        'updates':update_dict,
#        'searched_by':searched_by,
#        'flag':flag,
#        'errors':errors,
#        'client_name':client_name,
#        'seller_name':seller_name,
#        'loggedin':True,
#        'clients':clients,
#        'client_display_name':Client.objects.filter(slug=client_name)[0].name
#    }
#    return render_to_response('inventory/search_by_sku.html', inventory_dict, context_instance=RequestContext(request))
#
#def check_dc_validity(to_update, seller):
#    from fulfillment.models import Dc
#    #Get list of dc
#    dc_in_excel = []
#    dc_not_present = []
#
#    for item in to_update:
#        if not item['dc'] in dc_in_excel:
#            dc_in_excel.append(item['dc'])
#
#    if dc_in_excel:
#        available_dc = Dc.objects.filter(code__in=dc_in_excel, client=seller.client).values('code')
#
#    if available_dc:
#        if len(available_dc) == len(dc_in_excel):
#            pass
#        else:
#            for dc_in_excel_item in dc_in_excel:
#                found = False
#                for available_dc_item in available_dc:
#                    if dc_in_excel_item == available_dc_item:
#                        found = True
#                        break
#
#                if not found:
#                    dc_not_present.append(dc_in_excel_item)
#
#    return dc_not_present
#
#def upload_bulk_inventory(request, seller, client_id,client_name, seller_name, c, profile):
#    from django.utils import simplejson
#    from web.sbf_forms import FileUploadForm
#    profile = request.user.get_profile() 
#    clients = profile.managed_clients()
#    errors, message = [], None
#    consolidated_updates = None
#    parsed_excel_json = None
#    form = None
#    flag = None
#    to_update = None
#    path_to_save = None
#    dc_not_present = []
#    accounts = profile.managed_accounts.filter(client__id = client_id)
#    if request.method == 'POST':
#        if request.POST.get("upload") == 'Upload':
#            import xlrd
#            form = FileUploadForm(request.POST, request.FILES)
#            if form.is_valid():
#                path_to_save = save_uploaded_file(request.FILES['status_file'])
#                errors, to_update = get_parsed_inventory_excel(path_to_save)
#                if not errors:
#                    dc_not_present = check_dc_validity(to_update, seller)
#                    if dc_not_present:
#                        dc_not_present_string = ''
#                        for item in dc_not_present:
#                            dc_not_present_string += item + ','
#                        dc_not_present_string = dc_not_present_string[:len(dc_not_present_string-1)]
#                        errors.append('Entries not found for DC Codes - %s. Please correct the DC Entries and then try to upload again!!!' % dc_not_present_string)
#                        form = FileUploadForm()
#                        flag = 'new'
#                    else:
#                        errors, consolidated_updates = get_inventory_updates(to_update, seller, False)
#                        parsed_excel_json = simplejson.dumps(to_update)
#                        flag = 'show_details'
#                else:
#                    form = FileUploadForm()
#                    flag = 'new'
#
#                #Delete the uploaded excel file
#                if path_to_save:
#                    os.remove(path_to_save)
#            else:
#                errors.append('Please select the excel file and then click upload!!!')
#                form = FileUploadForm()
#                flag = 'new'
#        elif request.POST.get("update") == 'Update':
#            #path_to_save = request.POST.get("path_to_save")
#            parsed_excel_json = request.POST.get("parsed_excel_json")
#            to_update = simplejson.loads(parsed_excel_json)
#            errors, consolidated_updates = get_inventory_updates(to_update, seller, True, request.user)
#            flag = 'updated'
#            form = FileUploadForm()
#    else:
#        form = FileUploadForm()
#        flag = 'new'
#
#    is_global_dc_supported = utils.is_global_dc_maintained(seller.client)
#
#    inventory_dict = {
#	    'accounts' : accounts,
#        'is_global_dc_supported':is_global_dc_supported,
#        'forms' : form,
#        'errors' : errors,
#        'consolidated_updates' : consolidated_updates,
#        'parsed_excel_json' : parsed_excel_json,
#        'flag' : flag,
#        'path_to_save' : path_to_save,
#        'url' : request.get_full_path(),
#        'client_name':client_name,
#        'seller_name':seller_name,
#        'loggedin':True,
#        'clients':clients,
#        'client_display_name':Client.objects.filter(slug=client_name)[0].name,
#        }
#    return render_to_response('inventory/inventory_upload.html', inventory_dict, context_instance=RequestContext(request))
#
#def get_parsed_inventory_excel(path_to_save):
#    import xlrd
#    try:
#        book = xlrd.open_workbook(path_to_save)
#    except XLRDError:
#        return ['invalid file format'],['invalid file format']
#    sh = book.sheet_by_index(0)
#    header = sh.row(0)
#    map = {}
#    idx = 0
#    for idx in range(sh.ncols):
#        map[header[idx].value.strip().lower()] = idx
#    errors = []
#    to_update = []
#    consolidated_updates = []
#    article_id_list = []
#
#    for row_count in range(1, sh.nrows):
#        row = sh.row(row_count)
#        try:
#            article_id = str(int(row[map['articleid']].value))
#            action = row[map['action']].value
#            dc = row[map['dc']].value
#            stock = str(row[map['physical_stock']].value)
#
#            virtual_stock = ''
#            try:
#                virtual_stock = row[map['virtual_stock']].value
#            except KeyError:
#                pass
#
#            expires_on = ''
#            try:
#                expires_on = row[map['expires_on']].value
#            except KeyError:
#                pass
#            
#            expected_on = ''
#            try:
#                expected_on = row[map['expected_on']].value
#            except KeyError:
#                pass
#           
#            threshold_stock = ''
#            try:
#                threshold_stock = row[map['threshold_stock']].value
#            except KeyError:
#                pass
#
#            otc = 'no'
#            try:
#                otc = row[map['otc']].value
#            except KeyError:
#                pass
#            
#            cod = 'no'
#            try:
#                cod = row[map['cod']].value
#            except KeyError:
#                pass
#
#            so = 'no'
#            try:
#                so = row[map['so']].value
#            except KeyError:
#                pass
#
#            clearance = 'no'
#            try:
#                clearance = row[map['clearance']].value
#            except KeyError:
#                pass
#
#            delivery_time = ''
#            try:
#                delivery_time = int(row[map['delivery time']].value)
#            except KeyError:
#                pass
#            
#            add_dict = {
#                'article_id': str(article_id).strip().split('.')[0],
#                'action': action.strip().lower(),
#                'stock' : str(stock).strip().split('.')[0],
#                'virtual_stock' : str(virtual_stock).strip().split('.')[0],
#                'expires_on' : expires_on,
#                'expected_on' : expected_on,
#                'threshold_stock' : str(threshold_stock).strip().split('.')[0],
#                'dc' : str(dc).strip().split('.')[0],
#                'otc' : otc.strip().lower(),
#                'cod': cod.strip().lower(),
#                'so': so.strip().lower(),
#                'clearance': clearance.strip().lower(),
#                'delivery_time' : delivery_time,
#                }
#
#            repeated = False
#            for item in to_update:
#                if (item['article_id'] == add_dict['article_id']) and (item['dc'] == add_dict['dc']):
#                    repeated = True
#                    break
#
#            if not repeated:
#                to_update.append(add_dict)
#                if not add_dict['article_id'] in article_id_list:
#                    article_id_list.append(add_dict['article_id'])
#            else:
#                errors.append('Duplicate entry for Articleid: %s and DC: %s combination!!! Please correct the error and and try to upload again!!!' % (item['article_id'],item['dc']))
#        except KeyError:
#            errors.append('Unsupported excel file.')
#            break
#
#    return errors, to_update
#
#def get_inventory_updates(to_update, seller, save_changes, user=None):
#    from django.db.models import Q
#    from catalog.models import InventoryLog
#    errors = []
#    consolidated_updates = []
#    action_dict = {True:'YES', False:'NO'}
#    if_any_updates = False
#    is_global_dc_supported = utils.is_global_dc_maintained(seller.client)
#    updated_virtual_stock, updated_expires_on, updated_expected_on = None, None, None
#    updated_threshold_stock = None
#    inventory_log = None
#
#    if to_update:
#        consolidated_updates = []
#        for item in to_update:
#            try:
#                rate_chart = SellerRateChart.objects.get(article_id=item['article_id'], seller=seller)
#
#                inventory = None
#                try:
#                    inventory = Inventory.objects.get(rate_chart=rate_chart, dc__client=seller.client, dc__code=item['dc'])
#                except Inventory.DoesNotExist:
#                    dc = None
#                    try:
#                        dc = Dc.objects.get(code=item['dc'], client=seller.client)
#                    except Dc.DoesNotExist:
#                        log.info('No DC found for client=%s and code=%s combination' % (seller.client, item['dc']))
#                    if dc:
#                        inventory = Inventory(rate_chart=rate_chart, stock=0, dc=dc)
#                        inventory.save()
#
#                #Check whether product belongs to clearance sale or not
#                clearance_list = None
#                current_clearance_status = 'NO'
#                if utils.get_future_ecom_prod() == seller.client:
#                    pass
#                else:
#                    clearance_list = None
#                    try:
#                        clearance_list = List.objects.get(type='clearance', client=seller.client)
#                    except:
#                        log.info('No clearance list maintained for %s' % seller.client)
#
#                    clearance_list_items = None
#                    if clearance_list:
#                        clearance_list_items = clearance_list.listitem_set.all()
#
#                        for listitem in clearance_list_items:
#                            if rate_chart == listitem.sku:
#                                current_clearance_status = 'YES'
#                    
#                inventory_dict = {
#                    'product_name' : rate_chart.product.title,
#                    'article_id' : item['article_id'],
#                    'current_otc' : action_dict.get(rate_chart.otc,'--'),
#                    'updated_otc': item['otc'].upper(),
#                    'current_cod' : action_dict.get(rate_chart.is_cod_available,'--'),
#                    'updated_cod': item['cod'].upper(),
#                    'current_so' : action_dict.get(rate_chart.ship_local_only,'--'),
#                    'updated_so': item['so'].upper(),
#                    'current_clearance' : current_clearance_status,
#                    'updated_clearance': item['clearance'].upper(),
#                    }
#
#                if is_global_dc_supported:
#                    if rate_chart.shipping_duration:
#                        delivery_time = str(rate_chart.shipping_duration)
#                    else:
#                        delivery_time = '--'
#
#                    extra_params = {
#                        'current_deliverytime':delivery_time,
#                        'updated_deliverytime': Decimal(str(item['delivery_time'])),
#                        }
#                    inventory_dict.update(extra_params)
#
#                if item['action'] == 'update':
#                    #If action=update, overwrite the current inventory.
#                    if save_changes:
#                        inventory_log = InventoryLog()
#                        inventory_log.was_physical_stock = inventory.stock
#
#                        inventory.stock = Decimal(str(item['stock']))
#                        if inventory.stock < Decimal('0'):
#                            inventory.stock = Decimal('0')
#                        inventory.save()
#
#                        inventory_log.new_physical_stock = inventory.stock
#
#                    extra_params = {
#                        'current_stock' : inventory.stock,
#                        'updated_stock' : Decimal(str(item['stock'])),
#                        }
#                    inventory_dict.update(extra_params)
#                elif item['action'] == 'add':
#                    # stock = current stock + additional stock
#                    updated_stock = 0
#                    if inventory.stock:
#                        updated_stock = inventory.stock + Decimal(str(item['stock']))
#                    else:
#                        updated_stock = Decimal(str(item['stock']))
#
#                    if save_changes:
#                        inventory_log = InventoryLog()
#                        inventory_log.was_physical_stock = inventory.stock
#                        inventory.stock = updated_stock
#                        inventory.save()
#                        inventory_log.new_physical_stock = inventory.stock
#                    
#                    extra_params = {
#                        'current_stock' : inventory.stock,
#                        'updated_stock' : updated_stock,
#                        }
#                    inventory_dict.update(extra_params)
#
#                if item['virtual_stock'] and item['expires_on'] and item['expected_on']:
#                    current_virtual_stock, current_expires_on, current_expected_on = None, None, None 
#                    if inventory.expires_on  and (inventory.expires_on < datetime.datetime.now()):
#                        current_virtual_stock = '--'
#                        current_expires_on = '--'
#                        current_expected_on = '--'
#                    else:
#                        current_virtual_stock = '--'
#                        if inventory.virtual_stock:
#                            current_virtual_stock = inventory.virtual_stock
#                        current_expires_on = '--'
#                        if inventory.expires_on:
#                            current_expires_on = inventory.expires_on
#                        current_expected_on = '--'
#                        if inventory.expected_on:
#                            current_expected_on = inventory.expected_on
#
#                    updated_virtual_stock = Decimal(str(item['virtual_stock']))
#                    updated_expires_on = item['expires_on']
#                    updated_expected_on = item['expected_on']
#
#                    extra_params = {
#                        'current_virtual_stock' : current_virtual_stock,
#                        'updated_virtual_stock' : updated_virtual_stock,
#                        'current_expected_on' : current_expected_on,
#                        'updated_expected_on' : datetime.datetime.strptime(item['expected_on'],'%Y-%m-%d %H:%M:%S'),
#                        'current_expires_on' : current_expires_on,
#                        'updated_expires_on' : datetime.datetime.strptime(item['expires_on'],'%Y-%m-%d %H:%M:%S'),
#                        }   
#                    inventory_dict.update(extra_params)
#                
#                if item['threshold_stock']:
#                    current_threshold_stock = '--'
#                    if inventory.threshold_stock:
#                        current_threshold_stock = inventory.threshold_stock
#                    updated_threshold_stock = Decimal(str(item['threshold_stock']))
#                    
#                    extra_params = {
#                        'current_threshold_stock' : current_threshold_stock,
#                        'updated_threshold_stock' : updated_threshold_stock,
#                        }
#                    inventory_dict.update(extra_params)
#
#                consolidated_updates.append(inventory_dict)
#
#                if save_changes:
#                    #Update inventory related stuff.
#                    if item['virtual_stock'] and item['expires_on'] and item['expected_on']:
#                        inventory_log.was_virtual_stock = inventory.virtual_stock
#                        inventory_log.was_expires_on = inventory.expires_on
#                        inventory_log.was_expected_on = invetory.expected_on
#
#                        inventory.virtual_stock = Decimal(str(item['virtual_stock']))
#                        inventory.expires_on = datetime.datetime.strptime(item['expires_on'],'%Y-%m-%d %H:%M:%S')
#                        inventory.expected_on = datetime.datetime.strptime(item['expected_on'],'%Y-%m-%d %H:%M:%S')
#                        inventory.save()
#
#                        inventory_log.new_virtual_stock = inventory.virtual_stock
#                        inventory_log.new_expires_on = inventory.expires_on
#                        inventory_log.new_expected_on = inventory.expected_on
#
#                    if item['threshold_stock']:
#                        inventory_log.was_threshold_stock = inventory.threshold_stock
#
#                        inventory.threshold_stock = Decimal(str(item['threshold_stock']))
#                        inventory.save()
#
#                        inventory_log.new_threshold_stock = inventory.threshold_stock
#
#                    if inventory_log:
#                        inventory_log.rate_chart = inventory.rate_chart
#                        inventory_log.dc = inventory.dc
#                        inventory_log.modified_by = 'admin'
#                        inventory_log.user = user
#                        inventory_log.save()
#
#                    #Now, update the rate chart entires
#                    if item['otc'] == 'yes':
#                        rate_chart.otc = True
#                    elif item['otc'] == 'no':
#                        rate_chart.otc = False
#                    
#                    if item['cod'] == 'yes':
#                        rate_chart.is_cod_available = True
#                    elif item['cod'] == 'no':
#                        rate_chart.is_cod_available = False
#
#                    if item['so'] == 'yes':
#                        rate_chart.ship_local_only = True
#                    elif item['so'] == 'no':
#                        rate_chart.ship_local_only = False
#
#                    if item['clearance'] == 'yes':
#                        if not clearance_list:
#                            clearance_list = List(type='clearance', client=seller.client)
#                            clearance_list.save()
#
#                        try:
#                            listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
#                        except ListItem.DoesNotExist:
#                            #Listitem does not exist, so add new one
#                            max_seq = clearance_list.listitem_set.all().aggregate(max=Max('sequence'))
#                            if max_seq['max'] == None: max_seq['max'] = 0
#                            listitem = ListItem(list=clearance_list, sku=rate_chart, sequence=(max_seq['max']+1))
#                            listitem.save()
#                    elif item['clearance'] == 'no':
#                        if clearance_list:
#                            try:
#                                listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
#                                listitem.delete()
#                            except ListItem.DoesNotExist:
#                                log.info('listitem object does not exist in clarance list')
#
#                    if is_global_dc_supported:
#                        rate_chart.shipping_duration = str(item['delivery_time'])
#                        
#                    rate_chart.save()
#                    
#                    #Update solr index.
#                    #Make product available on site, if-
#                    #1) Valid price is maintained.(--Already mainained above, so no need to check again)
#                    #2) Pricelist priorities are maintained.
#                    #3) Valid stock is maintained.
#                    product = rate_chart.product
#                    rate_chart.stock_status = 'outofstock'
#
#                    if inventory.stock:
#                        if not (utils.is_holii_client(seller.client) or utils.is_wholii_client(seller.client)): 
#                            prices_maintained_for_src = Price.objects.filter(
#                                rate_chart=rate_chart).exclude(
#                                Q(price_type='timed',start_time__gte=datetime.datetime.now())| 
#                                Q(price_type='timed', end_time__lte=datetime.datetime.now())
#                                )
#
#                            if prices_maintained_for_src:
#                                domain_level_applicable_pricelists = DomainLevelPriceList.objects.filter(domain__client=rate_chart.seller.client)
#                        
#                                if domain_level_applicable_pricelists:
#                                    rate_chart.stock_status = 'instock'
#                                else:
#                                    client_level_applicable_pricelists = ClientLevelPriceList.objects.filter(client=rate_chart.seller.client)
#                                    if client_level_applicable_pricelists:
#                                        rate_chart.stock_status = 'instock'
#                        else:
#                            rate_chart.stock_status = 'instock'
#
#                    rate_chart.save()
#                    product.update_solr_index()
#            except SellerRateChart.DoesNotExist:
#                errors.append('No active article maintained for Articleid - %s' % item['article_id'])
#            except SellerRateChart.MultipleObjectsReturned:
#                errors.append('Multiple articles maintained for Articleid - %s' % item['article_id'])
#            except Exception,e:
#                log.info("Exception = %s" % repr(e))
#    else:
#        log.info('no data to upload in the sheet!!!')
#
#    return errors, consolidated_updates

def ifs_home(request, client_name, seller_name, *args, **kwargs):
    client_name = slugify(client_name)
    seller_name = slugify(seller_name)
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ifs-home',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers'}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ifs-home',None,kwargs={'client_name':client_name,'seller_name':new_seller_name}))    
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
    #getting ids from client_name and seller_name
    client = Client.objects.filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('ifs-home',None,kwargs={'client_name':profile.managed_clients[0].slug,'seller_name':'all-sellers'}))

    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('ifs-home',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name)}))
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            seller = seller[0]
            current_seller_id = seller.id
        else:
            return HttpResponsePermanentRedirect(reverse('ifs-home',None,kwargs={'client_name':client_name,'seller_name':'all-sellers'}))
    return render_to_response('ifs/ifs_home.html',
                {'loggedin':True,
                'client_name':client_name,
                'seller_name':seller_name,
                'accounts':accounts,
                'clients':clients,
                },
                context_instance=RequestContext(request))            

def ifs_table_action_map():
    action_list = ['View', 'Insert', 'Update', 'Delete']
    action_list_view = ['View','Insert']
    table_dict = {
        'Lsp_Master':action_list_view,
        'DC_Master':action_list_view,
        'DC_Zipgroup_LSP_Local_Ship':action_list_view,
        'Zipgroup_LSP_Map':action_list_view, 
        'Pincode_Zipgroup_Map':action_list,
        'ProductGroup_Master':action_list_view,
        'Article_ProductGroup_Map':action_list,
        'DC_Zipgroup_LSP_Map':action_list,
    }
    return table_dict

def ifs_select(request, client_name, seller_name, *args, **kwargs):
    client_name = slugify(client_name)
    seller_name = slugify(seller_name)
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ifs-select',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers'}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('ifs-select',None,kwargs={'client_name':client_name,'seller_name':new_seller_name}))    
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
    #getting ids from client_name and seller_name
    client = Client.objects.filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('ifs-select',None,kwargs={'client_name':profile.managed_clients[0].slug,'seller_name':'all-sellers'}))

    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('ifs-select',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name)}))
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            seller = seller[0]
            current_seller_id = seller.id
        else:
            return HttpResponsePermanentRedirect(reverse('ifs-select',None,kwargs={'client_name':client_name,'seller_name':'all-sellers'}))
    table_dict = ifs_table_action_map() 
    selected_table = ''
    selected_action = ''
    if request.method == "POST":
        try:
            selected_table = request.POST['table']
        except:
            selected_table='Lsp_Master'
        try:
            selected_action = request.POST['action']
        except:
            selected_action = ['View']
        return HttpResponsePermanentRedirect(reverse('upload-ifs',None,kwargs={'client_name':client_name, 'seller_name':seller_name,'selected_table':selected_table,'selected_action':selected_action}))

    return render_to_response('ifs/ifs_select.html',
            {'loggedin':True,
            'selected_table':selected_table,
            'client':client,
            'clients':clients,
            'url':request.get_full_path(),
            'accounts':accounts,
            'client_name':client_name,
            'seller_name':seller_name,
            'table_dict':table_dict,
            'client_display_name':Client.objects.filter(slug=client_name)[0].name
            },
            context_instance=RequestContext(request))            

def lsp_view(action, content):
    action = action.lower()
    errors = []
    updates = []
    try:
        lsps = Lsp.objects.all()
        if action == 'view':
            header_list = ['Lsp name','Lsp Code'] 
            lsp_list = []
            for lsp in lsps:
                lsp_list.append([lsp.name, lsp.code])
            return lsp_list, header_list
		
        elif action == 'insert':
            for item in content:
                err = []
                try:
                    lsp = Lsp.objects.get(code=item['lsp_code'])
                    err = 'Lsp with code %s already exists in database' % lsp.code
                    errors.append(err)
                except:
                    p = Lsp()
                    p.code = item['lsp_code']
                    p.name = item['lsp_name']
                    p.save()
            return errors, updates 
                  
        else:
            errors.append('This action is not supported!!')
            return errors 
    except Exception, e:
       s = str(e) + "Something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 
        
def dc_view(action, content):
    action = action.lower()
    errors = []
    updates = []
    try:
        dcs = Dc.objects.select_related('client')
        if action == 'view':
            header_list = ['Dc name','Dc Code','Client','Cod flag','Dc Address'] 
            dc_list = []
            for dc in dcs:
                dc_list.append([dc.name, dc.code, dc.client.name, dc.cod_flag, dc.address])
            return dc_list, header_list
        
        elif action == 'insert':
            for item in content:
                err = []
                try:
                    dcs = Dc.objects.get(code=item['code'], client=item['client'])
                    err = 'DC with code %s and client %s already exists in database' % (dc.code, dc.client.name)
                    errors.append(str(err))
                except Exception, e:
                    p = Dc()
                    p.code = item['code']
                    p.name = item['name']
                    p.address = item['address']
                    if item['cod'] == "1":
                        p.cod_flag = True
                    else:
                        p.cod_flag = False
                    p.client = item['client']
                    p.save()
            return errors, updates 
        
        else:
            errors.append('This action is not supported!!')
            return errors
    except Exception,e:
       s = str(e) + "Something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 

def dc_local(action, content):
    action = action.lower()
    errors = []
    updates = []
    try:
        dc_locals = DcZipgroup.objects.select_related('zipgroup__lsp','dc')
        if action == 'view':
            header_list = ['DC Code','Zipgroup Code','LSP Code'] 
            dc_local_list = []
            for dc_local in dc_locals:
                dc_local_list.append([dc_local.dc.code, dc_local.zipgroup.zipgroup_code, dc_local.zipgroup.lsp.code])
            return dc_local_list, header_list
        
        elif action == 'insert':
            for item in content:
                err = ""
                try:
                    dc_local = DcZipgroup.objects.get(dc__code=item['dc'], zipgroup__zipgroup_code=item['zipgroup'])
                    err = 'DC with code %s  already has entry for zipgroup %s' % (dc_local.dc.code, dc_local.zipgroup.zipgroup_code)
                    errors.append(str(err))
                except:
                    try:
                        ls = Lsp.objects.get(code=item['lsp'])                            
                        dco = Dc.objects.get(code=item['dc'], client=item['client'])
                        zips = LspZipgroup.objects.get(zipgroup_code=item['zipgroup'])
                        p = DcZipgroup()
                        p.lsp = ls 
                        p.dc = dco
                        p.zipgroup = zips
                        p.save()
                    except Exception,e:
                        err = 'Dc %s Zipgroup %s or Lsp %s does not exist!' % (item['dc'], item['zipgroup'], item['lsp'])
                        errors.append(str(err))
            return errors, updates 
        else:
            errors.append('This action is not supported!!')
    except Exception,e:
       s = str(e) + "Something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 

def zip_lsp(action, content):
    action = action.lower()
    errors = []
    updates = []
    try:
        ziplsps = LspZipgroup.objects.select_related('lsp')
        if action == 'view':
            header_list = ['LSP Code','Zipgroup Code','Zipgroup Name',] 
            ziplsp_list = []
            for ziplsp in ziplsps:
                ziplsp_list.append([ziplsp.lsp.code, ziplsp.zipgroup_code, ziplsp.zipgroup_name])
            return ziplsp_list, header_list
        elif action == 'insert':
            for item in content:
                err = []
                try:
                    ziplsp = LspZipgroup.objects.get(lsp__code=item['lsp'], zipgroup_code=item['zipcode'])
                    err = 'Zipgroup with code %s  already has entry for Lsp %s' % (item['zipcode'], item['lsp'])
                    errors.append(str(err))
                except:
                    p = LspZipgroup()
                    p.zipgroup_name = item['zipname']
                    p.zipgroup_code = item['zipcode']
                    
                    try:
                        ls = Lsp.objects.get(code=item['lsp'])
                        p.lsp = ls
                        p.save()
                    except Exception,e:
                        err = 'Lsp %s does not exist!, error with Zipgroup %s Zipcode %s' % (item['lsp'], item['zipname'], item['zipcode'])
                        errors.append(str(err))
            return errors, updates 
        else:
            errors.append('This action is not supported!!')    
    except Exception,e:
       s = str(e) + "Something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 

def pin_zip(action, content, params_dict):
    action = action.lower()
    errors = []
    updates = []
    try:
        if action == 'view':
            page = params_dict['page'] 
            pin = params_dict['pincode'] 
            lsp_code = params_dict['lsp_code'] 
            zip_code = params_dict['zipgroup_code'] 
            pinzips = PincodeZipgroupMap.objects.all().select_related('zipgroup__lsp')
            if pin or lsp_code or zip_code:
                if pin:
                    pinzips = pinzips.filter(pincode=pin)
                if lsp_code:
                    pinzips = pinzips.filter(zipgroup__lsp__code=lsp_code)
                if zip_code:
                    pinzips = pinzips.filter(zipgroup__zipgroup_code=zip_code)
            else:
                pinzips = PincodeZipgroupMap.objects.select_related('zipgroup__lsp')[(page-1)*100:page*100]
            header_list = ['Pincode','Zipgroup Code','LSP_Code','LSP Priority','COD Flag','HighValue Flag','Supported ProductGroup'] 
            pinzip_list = []
            for pinzip in pinzips:
                pinzip_list.append([pinzip.pincode, pinzip.zipgroup.zipgroup_code, pinzip.zipgroup.lsp.code, pinzip.lsp_priority, pinzip.cod_flag, pinzip.high_value, pinzip.supported_product_groups,])
            return pinzip_list, header_list
        elif action == 'update' or action == 'delete' or action == 'insert':
            for item in content:
                err = []
                pinzip = None
                try:
                    pinzip = PincodeZipgroupMap.objects.get(pincode=item['pincode'], zipgroup__zipgroup_code=item['zipgroup'], zipgroup__lsp__code=item['lsp'])
                except:
                    pass
                if action == 'insert':
                    if pinzip:
                        err = 'Entry already exists for Pincode %s Zipgroup code %s Lsp %s' % (item['pincode'], item['zipgroup'], item['lsp']) 
                        errors.append(str(err))
                    else:
                        p = PincodeZipgroupMap()
                        p.pincode = item['pincode']
                        if item['cod'] == "1":
                            p.cod_flag = True
                        else:
                            p.cod_flag = False
                        if item['high_val'] == "1":
                            p.high_value = True
                        else:
                            p.high_value = False
                        p.lsp_priority = item['lsp_priority'] 
                        p.supported_product_groups = item['prod_grps']
                        try:
                            zipgrp = LspZipgroup.objects.get(lsp__code=item['lsp'], zipgroup_code=item['zipgroup'])
                            p.zipgroup = zipgrp
                            p.save()
                        except:
                            err = 'Zipgroup code %s and LSP % combination does not exist!' % (item['zipgroup'], item['lsp'])
                            errors.append(str(err))
                elif action == 'update':
                    #Note that only Product groups, Lsp priority COD flag and High value can be updated
                    if not pinzip:
                        err = 'Entry does not exist for Pincode %s Zipgroup code %s Lsp %s, hence update is not possible. Note that Product Groups, High value flag, LSP priority and COD flag fields can be updated.' % (item['pincode'], item['zipgroup'], item['lsp']) 
                        errors.append(str(err))
                    else:
                        p = pinzip
                        p.lsp_priority = item['lsp_priority'] 
                        p.supported_product_groups = item['prod_grps']
                        if item['cod'] == "1":
                            p.cod_flag = True
                        else:
                            p.cod_flag = False
                        if item['high_val'] == "1":
                            p.high_value = True
                        else:
                            p.high_value = False
                        p.save()
                elif action == 'delete':
                    # Deletion based on Pincode, Lsp, Zipgroup 
                    if not pinzip:
                        err = 'Entry does not exist for Pincode %s Zipgroup code %s Lsp %s, hence delete is not possible.' % (item['pincode'], item['zipgroup'], item['lsp']) 
                        errors.append(str(err))
                    else:
                        pinzip.delete()
        return errors, updates 
    except Exception,e:
       s = str(e) + "Something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 

def prod_grp_view( action, content):
    action = action.lower()
    errors = []
    updates = []
    try:
        prodgrps = ProductGroup.objects.select_related('client')
        if action == 'view':
            header_list = ['ProductGroup', 'ProductGroup Name', 'ShipLocal Flag', 'Transport Mode', 'HighValue Flag', 'Threshold Value','Client'] 
            prodgrp_list = []
            for prodgrp in prodgrps:
                prodgrp_list.append([prodgrp.name, prodgrp.description, prodgrp.local_tag, prodgrp.ship_mode, prodgrp.high_value_flag, prodgrp.threshold_amount, prodgrp.client.name])
            
            return prodgrp_list, header_list
        elif action == 'insert':
            for item in content:
                err = []
                try:
                    prodgrp = ProductGroup.objects.get(name=item['prod_grp_id'])
                    err = 'Product Group %s already exists' % prodgrp.name
                    errors.append(str(err))
                except: 
                    p = ProductGroup()
                    p.name = item['prod_grp_id']
                    p.description = item['prod_grp_name']
                    p.client = item['client']
                    if item['ship_local'] == "1":
                        p.local_tag = True
                    else:
                        p.local_tag = False
                    if item['high_val'] == "1":
                        p.high_value_flag = True
                    else:
                        p.high_value_flag = False
                    p.ship_mode = item['transport_mode']
                    p.threshold_amount = item['threshold_amt']
                    p.save()
            return errors, updates 
        else:
            errors.append('This action is not supported!!')
    except Exception,e:
       s = str(e) + "Something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 

def article_prod_grp(action, content, params_dict):
    action = action.lower()
    errors = []
    updates = []
    try:
        if action == 'view':
            page = params_dict['page'] 
            articleid = params_dict['article_id'] 
            prod_grp = params_dict['prod_grp'] 
            art_prods = ArticleProductgroup.objects.all().select_related('product_group')
            if articleid or prod_grp:
                if articleid:
                    art_prods = art_prods.filter(article_id=articleid)
                if prod_grp:
                    art_prods = art_prods.filter(product_group__name=prod_grp)
            else:
                art_prods = ArticleProductgroup.objects.select_related('product_group')[(page-1)*100:page*100]
            header_list = ['SAP Article','ProductGroup'] 
            art_prod_list = []
            for art_prod in art_prods:
               art_prod_list.append([art_prod.article_id, art_prod.product_group,])
            return art_prod_list, header_list
        elif action == 'update' or action == 'delete' or action == 'insert':
            for item in content:
                err = ""
                art_prod = None
                try:
                    art_prod  = ArticleProductgroup.objects.get(article_id=item['articleid'])
                except:
                    pass
                if action == 'insert':
                    if art_prod:
                        err = 'Article %s is already mapped to Product Group  %s' % (art_prod.article_id, art_prod.product_group)
                        errors.append(str(err))
                    else:
                        p = ArticleProductgroup()
                        p.article_id = item['articleid']
                        try:
                            prod = ProductGroup.objects.get(name=item['prod_grp'], client=item['client'])
                            p.product_group = prod
                            p.save()
                        except:
                            err = 'Product Group  %s does not exist!' % item['prod_grp']
                            errors.append(str(err))
                elif action == 'update':
                    #Note that only change of Product Group for article is allowed
                    if not art_prod:
                        err = 'Article %s cannot be found in database!' % item['articleid']
                        errors.append(str(err))
                    else:
                        try:
                            prod = ProductGroup.objects.get(name=item['prod_grp'], client=item['client'])
                            p = art_prod
                            p.product_group = prod
                            p.save()
                        except:
                            err = 'Product Group  %s does not exist!' % item['prod_grp']
                            errors.append(err)
                elif action == 'delete':
                    # Only article based deletion allowed
                    if not art_prod:
                        err = 'Article %s cannot be found in database!' % item['articleid']
                        errors.append(err)
                    else:
                        art_prod.delete()
            return errors, updates 
    except Exception,e:
       s = str(e) + " -- something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 

def delv_chart(action, content, params_dict):
    errors = []
    updates = []
    action = action.lower()
    try:
        if action == 'view':
            page = params_dict['page'] 
            dc_code = params_dict['dc_code'] 
            lsp_code = params_dict['lsp_code'] 
            zip_code = params_dict['zipgroup_code'] 
            delv_charts = LspDeliveryChart.objects.all().select_related('zipgroup__lsp','dc')
            if dc_code or lsp_code or zip_code:
                if dc_code:
                    delv_charts = delv_charts.filter(dc__code=dc_code)
                if lsp_code:
                    delv_charts = delv_charts.filter(zipgroup__lsp__code=lsp_code)
                if zip_code:
                    delv_charts = delv_charts.filter(zipgroup__zipgroup_code=zip_code)
            else:
                delv_charts = LspDeliveryChart.objects.select_related('zipgroup__lsp','dc')[(page-1)*100:page*100]
            header_list = ['Dc Code','Zipgroup Code','LSP Code','Mode of Transport','Transit Time'] 
            delv_charts_list = []
            for delv_chart in delv_charts:
                delv_charts_list.append([delv_chart.dc.code, delv_chart.zipgroup.zipgroup_code, delv_chart.zipgroup.lsp.code, delv_chart.ship_mode, delv_chart.transit_time])
            return delv_charts_list, header_list
        
        elif action == 'update' or action == 'delete' or action == 'insert':
            for item in content:
                err = []
                delv_chart = None
                try:
                    delv_chart = LspDeliveryChart.objects.get(dc__code=item['dc'], zipgroup__zipgroup_code=item['zipgroup'], zipgroup__lsp__code=item['lsp'], ship_mode=item['transport_mode'])
                except:
                    pass
                if action == 'insert':
                    if delv_chart:
                        err = 'Entry already exists for Dc %s Zipgroup code %s Lsp %s Transportation mode %s' % (item['dc'], item['zipgroup'], item['lsp'], item['transport_mode']) 
                        errors.append(str(err))
                    else:
                        p = LspDeliveryChart()
                        p.ship_mode = item['transport_mode']
                        p.transit_time = item['delivery_time']
                        try:
                            dc = Dc.objects.get(code=item['dc'], client=item['client'])
                            zipgrp = LspZipgroup.objects.get(lsp__code=item['lsp'], zipgroup_code=item['zipgroup'])
                            p.dc = dc
                            p.zipgroup = zipgrp
                            p.save()
                        except:
                            err = 'Dc %s does not exist!' % item['dc']
                            errors.append(str(err))
                            err = 'Zipgroup code %s and LSP %s combination does not exist!' % (item['zipgroup'], item['lsp'])
                            errors.append(str(err))
                elif action == 'update':
                    #Note that only delivery time can be updated
                    if not delv_chart:
                        err = 'Entry does not exist for Dc %s Zipgroup code %s Lsp %s Transportation mode %s, hence update is not possible. Note that only Transit/Delivery time can be updated.' % (item['dc'], item['zipgroup'], item['lsp'], item['transport_mode']) 
                        errors.append(str(err))
                    else:
                        p = delv_chart 
                        p.transit_time = item['delivery_time']
                        p.save()
                elif action == 'delete':
                    # Deletion based on Dc, Lsp, Zipgroup and Transport mode combinations
                    if not delv_chart:
                        err = 'Entry does not exist for Dc %s Zipgroup code %s Lsp %s Transportation mode %s, hence delete is not possible.' % (item['dc'], item['zipgroup'], item['lsp'], item['transport_mode']) 
                        errors.append(str(err))
                    else:
                        delv_chart.delete()
            return errors, updates 
    except Exception,e:
       s = str(e) + "something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 

#@check_role(['IFS'])
def ifs_actions(request, client_name, seller_name, selected_table, selected_action):
    client_name = slugify(client_name)
    seller_name = slugify(seller_name)
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('upload-ifs',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers', 'selected_table':selected_table,'selected_action':selected_action}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('upload-ifs',None,kwargs={'client_name':client_name,'seller_name':new_seller_name, 'selected_table':selected_table,'selected_action':selected_action}))    
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
    #getting ids from client_name and seller_name
    client = Client.objects.filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('upload-ifs',None,kwargs={'client_name':profile.managed_clients[0].slug,'seller_name':'all-sellers', 'selected_table':selected_table,'selected_action':selected_action}))

    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('upload-ifs',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name), 'selected_table':selected_table,'selected_action':selected_action}))
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            seller = seller[0]
            current_seller_id = seller.id
        else:
            return HttpResponsePermanentRedirect(reverse('upload-ifs',None,kwargs={'client_name':client_name,'seller_name':'all-sellers', 'selected_table':selected_table,'selected_action':selected_action}))
    title_table = selected_table.replace('_',' ')
    table_dict = ifs_table_action_map()
    content_list = []
    url = request.get_full_path()
    header_list = []
    display_list = []
    #When it enters the view for first time, flag is new
    flag = 'new' 
    content = {}    
    entries = 100
    pincode = ""
    zipgroup_code = ""
    lsp_code = ""
    article_id = ""
    prod_grp = "" 
    dc_code = ""
    pagination = {}
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    if selected_action.lower() == 'view':
        
        if selected_table.lower() == 'lsp_master':
             content_list, header_list = lsp_view(selected_action, content)
        elif selected_table == 'DC_Master':
             content_list, header_list = dc_view(selected_action, content)
        elif selected_table == 'DC_Zipgroup_LSP_Local_Ship':
             content_list, header_list = dc_local(selected_action, content)
        elif selected_table == 'Zipgroup_LSP_Map':
             content_list, header_list = zip_lsp(selected_action, content)
        elif selected_table == 'Pincode_Zipgroup_Map':
            count = PincodeZipgroupMap.objects.count()
            pincode = request.POST.get("pincode", "")
            lsp_code = request.POST.get("lsp_code", "")
            zipgroup_code = request.POST.get("zipgroup_code", "")
            params_dict = {'page':page, 'pincode':pincode, 'lsp_code':lsp_code, 'zipgroup_code':zipgroup_code }
            content_list, header_list = pin_zip(selected_action, content, params_dict)
            if not pincode and not lsp_code and not zipgroup_code:    
                paginator = Paginator(content_list, 1) # Show 30 items per page
                base_url = request.get_full_path()
                page_pattern = re.compile('[&?]page=\d+')
                base_url = page_pattern.sub('',base_url)
                page_pattern = re.compile('[&?]per_page=\d+')
                base_url = page_pattern.sub('',base_url)
                if base_url.find('?') == -1:
                    base_url = base_url + '?'
                else:
                    base_url = base_url + '&'
                pagination = getPaginationContext(page, (count/entries + 1), base_url) 
                try:
                   display_list = paginator.page(page)
                except (EmptyPage, InvalidPage):
                   display_list = paginator.page(paginator.num_pages)
        elif selected_table == 'ProductGroup_Master':
             content_list, header_list = prod_grp_view( selected_action, content)
        elif selected_table == 'Article_ProductGroup_Map':
             count = ArticleProductgroup.objects.count()
             article_id = request.POST.get("article_id", "")
             prod_grp = request.POST.get("prod_grp", "")
             params_dict = {'page':page, 'prod_grp':prod_grp, 'article_id':article_id, }
             content_list, header_list = article_prod_grp( selected_action, content, params_dict)
             if not article_id and not prod_grp:
                 paginator = Paginator(content_list, 1) # Show 30 items per page
                 base_url = request.get_full_path()
                 page_pattern = re.compile('[&?]page=\d+')
                 base_url = page_pattern.sub('',base_url)
                 page_pattern = re.compile('[&?]per_page=\d+')
                 base_url = page_pattern.sub('',base_url)
                 if base_url.find('?') == -1:
                     base_url = base_url + '?'
                 else:
                     base_url = base_url + '&'
                
                 pagination = getPaginationContext(page, (count/entries + 1), base_url) 
                 try:
                    display_list = paginator.page(page)
                 except (EmptyPage, InvalidPage):
                    display_list = paginator.page(paginator.num_pages)
        elif selected_table == 'DC_Zipgroup_LSP_Map':
             count = LspDeliveryChart.objects.count()
             dc_code = request.POST.get("dc_code", "")
             lsp_code = request.POST.get("lsp_code", "")
             zipgroup_code = request.POST.get("zipgroup_code", "")
             params_dict = {'page':page, 'dc_code':dc_code, 'lsp_code':lsp_code, 'zipgroup_code':zipgroup_code }
             content_list, header_list = delv_chart(selected_action, content, params_dict)
             if not dc_code and not lsp_code and not zipgroup_code:    
                 paginator = Paginator(content_list, 1) # Show 30 items per page
                 base_url = request.get_full_path()
                 page_pattern = re.compile('[&?]page=\d+')
                 base_url = page_pattern.sub('',base_url)
                 page_pattern = re.compile('[&?]per_page=\d+')
                 base_url = page_pattern.sub('',base_url)
                 if base_url.find('?') == -1:
                     base_url = base_url + '?'
                 else:
                     base_url = base_url + '&'
                
                 pagination = getPaginationContext(page, (count/entries + 1), base_url) 
                 try:
                    display_list = paginator.page(page)
                 except (EmptyPage, InvalidPage):
                    display_list = paginator.page(paginator.num_pages)
        
        return render_to_response('ifs/ifs_view.html',
            {'loggedin':True,
             'title_table':title_table,
             'lsp_code':lsp_code,
             'zipgroup_code':zipgroup_code,
             'pincode':pincode,
             'article_id':article_id,
             'prod_grp':prod_grp,
             'clients':clients,
             'accounts':accounts,
             'dc_code':dc_code,  
             'url':request.get_full_path(),
             'pagination':pagination,        
             'selected_action':selected_action,
             'display_list':display_list,
             'header_list':header_list,
             'content_list':content_list,
             'client_name':client_name,
             'seller_name':seller_name,
            },
            context_instance=RequestContext(request))   
    
    elif selected_action.lower() == 'update' or selected_action.lower() == 'insert' or selected_action.lower() == 'delete':
        from web.sbf_forms import FileUploadForm
        errors, message = [], None
        consolidated_updates = None
        form = None
        flag = None
        to_update = None
        path_to_save = None

        if request.method == 'POST':
            if request.POST.get("upload") == 'Upload':
                import xlrd
                form = FileUploadForm(request.POST, request.FILES)
                if form.is_valid():
                    path_to_save = save_uploaded_file(request.FILES['status_file'])
                    errors, consolidated_updates = get_ifs_updates(request, client_name, path_to_save, selected_table, selected_action, False)
                    if not errors:
                        flag = 'updated'
                    else:
                        flag='upload_errors'
                else:
                    errors.append(['Please select the excel file and then click upload!!!'])
                    form = FileUploadForm()
                    flag = 'new'

        else:
            form = FileUploadForm()
            flag = 'new'
            
        ifs_dict = {
            'forms' : form,
            'errors' : errors,
            'clients':clients,
            'accounts':accounts,
            'consolidated_updates' : consolidated_updates,
            'url':request.get_full_path(),
            'flag' : flag,
            'path_to_save' : path_to_save,
            'loggedin':True,
            'title_table':title_table,
            'selected_action':selected_action,
            'client_name':client_name,
            'seller_name':seller_name,
            #'header_list':header_list,
            #'content_list':content_list,
            }
        return render_to_response('ifs/ifs_upload.html', ifs_dict, context_instance=RequestContext(request))  

@login_required    
@check_role('Fulfillment')
def fulfillment_check(request, client_name, seller_name, *args, **kwargs):
    client_name = slugify(client_name)
    seller_name = slugify(seller_name)
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('fulfillment',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers'}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('fulfillment',None,kwargs={'client_name':client_name,'seller_name':new_seller_name}))    
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
        
    #getting ids from client_name and seller_name
    client = Client.objects.filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('fulfillment',None,kwargs={'client_name':profile.managed_clients[0].slug,'seller_name':'all-sellers'}))

    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('fulfillment',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name)}))
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            seller = seller[0]
            current_seller_id = seller.id
        else:
            return HttpResponsePermanentRedirect(reverse('fulfillment',None,kwargs={'client_name':client_name,'seller_name':'all-sellers'}))
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    clientname = client[0].name
    errors = []
    input_fault = ""
    if request.method == 'POST':
        pincode = request.POST['pincode']
        paytype = request.POST['paytype']
        article_id = request.POST['article_id']
        skuId = request.POST['skuId']
        quantity = request.POST['quantity']
        flag = "submitted"
        if paytype == 'cod':
            isCod = 1
        else:
            isCod = 0
        input_fault = validate_fulfillment_input(pincode, article_id, skuId, quantity)
        client_id = client[0].id
        if skuId:
            prods = SellerRateChart.objects.filter(sku=skuId, seller__client=client[0])
            if prods:
                article_id = prods[0].article_id
            else:
                input_fault = input_fault + "Product with entered Sku/Article Id does not exist."
        elif article_id:
            prods = SellerRateChart.objects.filter(article_id=article_id, seller__client=client[0])
            if prods:
                skuId = prods[0].sku
            else:
                input_fault = input_fault + "Product with entered Sku/Article Id does not exist."
        else:    
            input_fault = input_fault + "Product with entered Sku/Article Id does not exist."
        if input_fault:
            errors.append(input_fault)
            ifserr_dict = {'loggedin':True, 
                'errors':errors, 
                'flag':flag,
                'skuId':skuId,
                'pincode':pincode,
                'url':request.get_full_path(),
                'clients':clients,
                'accounts':accounts,
                'article_id':article_id,
                'paytype':paytype,
                'client_name':client_name,
                'seller_name':seller_name,
                'client':client[0],
                'quantity':quantity,
                }
            return render_to_response('ifs/fulfillment_check.html', ifserr_dict, context_instance=RequestContext(request))
        from orders.check_availability import check_availability_new
        json_response = check_availability_new(article_id, prods[0].id, pincode, quantity, client_id, isCod)
        log.info('Checking availability for %s: %s' % (article_id, json_response))
        if not json_response or not json_response['responseCode'].lower()=='success':
            if not json_response:
                errors.append('Did not receive a response in API call! Could not connect via Restful Web service!')
            elif not json_response['responseCode'].lower()=='success':
                errDisp = errorDesc(json_response['responseCode'])
                errors.append(errDisp)
                errors.append('Sorry. We cannot ship %s to %s' % (article_id, pincode))            
            ifserr_dict = {'loggedin':True, 
                'errors':errors, 
                'client_name':client_name,
                'seller_name':seller_name,
                'flag':flag, 
                'skuId':skuId,
                'pincode':pincode,
                'url':request.get_full_path(),
                'article_id':article_id,
                'clients':clients,
                'accounts':accounts,
                'paytype':paytype,
                'client':client[0],
                'quantity':quantity,
                }
            return render_to_response('ifs/fulfillment_check.html/', ifserr_dict, context_instance=RequestContext(request))
        ifs_bo = json_response['items']
        ifs_bo = ifs_bo[0]
        pinzips = PincodeZipgroupMap.objects.filter(pincode=pincode).select_related('zipgroup')
        zipgroups = []
        for zipgrp in pinzips:    
            zipgroups.append(zipgrp.zipgroup.zipgroup_name + " - " + zipgrp.zipgroup.zipgroup_code)
        primaryDCLsp = ifs_bo['primaryDCLSP'].split("_")
        dcLspList = stringtoList(ifs_bo['dcLspSequenceString'])
        dcStockString = stringtoList(ifs_bo['dcStockString'])
        dcPhysicalStockString = stringtoList(ifs_bo['dcPhysicalStockString'])
        dclsp = primaryDCLsp[0]+"-"+primaryDCLsp[1]
       # json_response['status_code'], 
       # json_response['status'], 
       # json_response['status_message'], 
       # json_response['num_returned'], 
       # json_response['num_found'], 
       # json_response['errors'], 
       # json_response['startIndex'],
       # print ifs_bo['skuID'], 
        fulfillment_dict = {
            'totalDeliveryTime':ifs_bo['totalDeliveryTime'], 
            'isBackorderable':ifs_bo['isBackorderable'], 
            'defaultDC':ifs_bo['defaultDC'], 
            'deliveryTime':ifs_bo['deliveryTime'], 
            'totalQuantityFound':ifs_bo['totalQuantityFound'], 
            'primaryDCLsp':dclsp,
            'skuId':skuId,
            'isHighValue':ifs_bo['isHighValue'],
            'dcStockString':dcStockString,
            'dcPhysicalStockString':dcPhysicalStockString,
            'inventoryTime':ifs_bo['inventoryTime'],
            'flfMessages':ifs_bo['flfMessages'], 
            'isShipLocalOnly':ifs_bo['isShipLocalOnly'], 
            'isInvCheck':ifs_bo['isInvCheck'], 
            'dcLspSequence':dcLspList, 
            'modeOfTransport':ifs_bo['modeOfTransport'], 
            'isAllQuantityFulfilled':ifs_bo['isAllQuantityFulfilled'],
            'productgroup':ifs_bo['productGroup'],
            'zipgroups':zipgroups,
            'loggedin':True,
            'url':request.get_full_path(),
            'clients':clients,
            'accounts':accounts,
            'client':clientname,
            'client_name':client_name,
            'seller_name':seller_name,
            'flag':flag,
            'pincode':pincode,
            'article_id':article_id,
            'paytype':paytype,
            'client':client[0],
            'quantity':quantity,
            'errors':errors,
        }
        return render_to_response('ifs/fulfillment_check.html', fulfillment_dict, context_instance=RequestContext(request))
    else:
    # Not post method    
        return render_to_response('ifs/fulfillment_check.html',
                 {'loggedin':True,
                  'client':clientname,
                  'clients':clients,
                  'accounts':accounts,
                  'url':request.get_full_path(),
                  'client_name':client_name,
                  'seller_name':seller_name,
                 },               
                 context_instance=RequestContext(request))

def get_ifs_updates(request, client_name, path_to_save, selected_table, selected_action, save_changes):
    import xlrd
    from django.db.models import Q
    book = xlrd.open_workbook(path_to_save)
    sh = book.sheet_by_index(0)
    header = sh.row(0)
    map = {}
    params_dict = {}
    idx = 0
    for idx in range(sh.ncols):
        map[header[idx].value.strip()] = idx
    errors = []
    err =[]
    to_update = []
    consolidated_updates = []
    action_dict = {True:'YES', False:'NO'}
    if_any_updates = False

    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    client_obj = Client.objects.get(slug = client_name)
    try:
        if selected_table.lower() == 'lsp_master':
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                lsp_name = row[map['LSP_Name']].value
                lsp_code = int(row[map['LSP_Code']].value)
            
                to_update.append({
                    'lsp_code': str(lsp_code).strip().split('.')[0],
                    'lsp_name': lsp_name.strip().lower(),
                })
            err, updates = lsp_view( selected_action, to_update)    
            if err:
                errors.append(err)
            else:
                pass
        elif selected_table == 'DC_Master':
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                name = row[map['DC_Name']].value
                code = int(row[map['DC_Code']].value)
                address = row[map['DC_Address']].value
                client = row[map['Client']].value 
                cod = row[map['COD_Flag']].value
                 
                to_update.append({
                    'code': str(code).strip().split('.')[0],
                    'name': name.strip().lower(),
                    'address': address.strip().lower(),
                    'cod': str(cod).strip().lower(),
                    'client':client_obj
                })
            err, updates = dc_view(selected_action, to_update)
            if err:
                errors.append(err)
            else:
                pass
                
        elif selected_table == 'DC_Zipgroup_LSP_Local_Ship':
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                lsp = int(row[map['LSP_Code']].value)
                dc = int(row[map['DC_Code']].value)
                zipgroup = int(row[map['Zipgroup_Code']].value)
                to_update.append({
                    'lsp': str(lsp).strip().split('.')[0],
                    'dc': str(dc).strip().split('.')[0],
                    'zipgroup': str(zipgroup).strip().split('.')[0],
                    'client':client_obj
                })
            err, updates = dc_local(selected_action, to_update)
            if err:
                errors.append(err)
            else:
                pass
        elif selected_table == 'Zipgroup_LSP_Map':
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                lsp = int(row[map['LSP_Code']].value)
                zipname = row[map['Zipgroup_Name']].value
                zipcode = int(row[map['Zipgroup_Code']].value)
                to_update.append({
                    'lsp': str(lsp).strip().split('.')[0],
                    'zipname': zipname.strip().lower(),
                    'zipcode': str(zipcode).strip().split('.')[0],
                    'client':client_obj
                })
            err, updates = zip_lsp( selected_action, to_update)
            if err:
                errors.append(err)
            else:
                pass
        elif selected_table == 'Pincode_Zipgroup_Map':
            prods = ProductGroup.objects.all()
            prod_list = []
            for prod in prods:
                prod_list.append(prod.name)
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                lsp = int(row[map['LSP_Code']].value)
                zipgroup = int(row[map['Zipgroup_Code']].value)
                pincode = int(row[map['Pincode']].value)
                cod = row[map['COD_Flag']].value
                high_val = row[map['HighValue_Flag']].value 
                lsp_priority = int(row[map['LSP_Priority']].value)
                prod_grps = str(row[map['Supported_ProductGroup']].value).replace(" ","")
                err = validate_prodgrps(prod_grps, prod_list) 
                err1 = validate_pincode(str(pincode))
                if not err and not err1:
                    to_update.append({
                        'lsp': str(lsp).strip().split('.')[0],
                        'zipgroup': str(zipgroup).strip().split('.')[0],
                        'pincode': str(pincode).strip().split('.')[0],
                        'cod': str(cod).strip().lower(),
                        'high_val': str(high_val).strip().lower(),   
                        'lsp_priority': lsp_priority,           
                        'prod_grps':prod_grps,
                        'client':client_obj
                     })
                else:
                    if err:
                        errors.append(err)
                    if err1:
                        errors.append(err1)
            err, updates = pin_zip( selected_action, to_update, params_dict)
            if err:
                errors.append(err)
            else:
                pass
        elif selected_table == 'ProductGroup_Master':
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                prod_grp_id = row[map['ProductGroup_ID']].value 
                prod_grp_name = row[map['ProductGroup_Name']].value 
                transport_mode = row[map['Transport_Mode']].value
                high_val = row[map['HighValue_Flag']].value 
                ship_local = row[map['ShipLocal_Flag']].value
                threshold_amt =  Decimal(str(row[map['Threshold_Value']].value))
                to_update.append({
                    'high_val': str(high_val).strip().lower(),   
                    'ship_local': str(ship_local).strip().lower(),   
                    'transport_mode': transport_mode.strip().lower(),   
                    'prod_grp_id':prod_grp_id,
                    'threshold_amt': str(threshold_amt).strip().split('.')[0],
                    'prod_grp_name':prod_grp_name,
                    'client':client_obj,
                 })
            err, updates = prod_grp_view(selected_action, to_update)    
            if err:
                errors.append(err)
            else:
                pass
        elif selected_table == 'Article_ProductGroup_Map':
            prods = ProductGroup.objects.all()
            prod_list = []
            for prod in prods:
                prod_list.append(prod.name)
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                articleid = int(row[map['SAP_Article_ID']].value)
                prod_grp = row[map['ProductGroup_ID']].value
                err = validate_prodgrp(prod_grp, prod_list)
                if not err:
                    to_update.append({
                        'articleid': str(articleid).strip().split('.')[0],
                        'prod_grp': str(prod_grp).strip().split('.')[0],
                        'client':client_obj,
                    })
                else:
                    errors.append(err)
            err, updates = article_prod_grp( selected_action, to_update, params_dict)
            if err:
                errors.append(err)
            else:
                pass
        elif selected_table == 'DC_Zipgroup_LSP_Map':
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                lsp = int(row[map['LSP_Code']].value)
                dc = int(row[map['DC_Code']].value)
                zipgroup = int(row[map['Zipgroup_Code']].value)
                transport_mode = row[map['Transport_Mode']].value
                delivery_time = int(row[map['Transit_Time']].value)
                to_update.append({
                    'transport_mode': transport_mode.strip().lower(),   
                    'lsp': str(lsp).strip().split('.')[0],
                    'dc': str(dc).strip().split('.')[0],
                    'zipgroup': str(zipgroup).strip().split('.')[0],
                    'delivery_time':delivery_time,
                    'client':client_obj
                })  
            err, updates = delv_chart(selected_action, to_update, params_dict)
            if err:
                errors.append(err)
            else:
                pass
    except KeyError:
        errors.append(['Unsupported excel file. Please check if headers are in the prescribed format.'])

    if to_update:
        pass
    else:
        log.info('No details found to upload in the sheet!!!')

    return errors, consolidated_updates

def validate_pincode(pin):
    errors = ""
    import re
    ptrn = re.compile('^[1-9]{1}[0-9]{5}$') 
    if ptrn.match(pin):
        return errors
    else:    
        errors = 'Invalid pincode. '
    return errors    

def validate_prodgrp(prod_grp, prod_list):
    errors = []
    import re
    ptrn = re.compile('^C\d+') 
    if ptrn.match(prod_grp):
        return
    else:    
        errors.append('Invalid Productgroup. ')
    return errors    

def validate_prodgrps(prod_grps, prod_list):
    result = 0
    err = []
    errors = []
    import re
    ptrn = re.compile('C\d+,')
    ptrn1 = re.compile('[\w,]+,$')
    grps = ptrn.finditer(prod_grps)
    for grp in grps:
        grp_name = grp.group().replace(",","")
        if grp_name in prod_list:
            result = result + 1
        else:
            log.info('Product group in Pincode Product group maping does not exist in Product Group master. ')
    if (not ptrn1.match(prod_grps)) or (result+1) != len(prod_grps.split(",")):
        err = "Error in Product group entry %s . " % prod_grps
        errors.append(err)
    return errors

def errorDesc(errorCode):
    errorCode = errorCode.lower()
    if errorCode == "err_prodgrp":
        errDesc = "Product group was not found for the given article"
        return errDesc
    elif errorCode == "err_inv":
        errDesc = "Inventory not found for the article."
        return errDesc
    elif errorCode == "err_local":
        errDesc = "Product is Ship-Local type, but the pincode does not come under local coverage area of any of the DCs. "
        return errDesc
    elif errorCode == "err_delv":
        errDesc = "No entry of DC, LSP and Pincode in LSP-DC-Zipgroup Map table (Delivery chart), hence cannot be delivered. "
        return errDesc
    elif errorCode == "err_inv_local":
        errDesc = "Inventory not available for Ship-local only case."
        return errDesc
    elif errorCode == "failure":
        errDesc = "Cannot fulfill - Failed."
        return errDesc
    elif errorCode == "err_cvg_area":
        errDesc = "This pincode doesnt come under our coverage area."
        return errDesc
    elif errorCode == "err_inv_cod":
        errDesc = "No LSP found for COD at the pincode."
        return errDesc
    elif errorCode == "err_lsp_hv":
        errDesc = "Cannot fulfill due to High value of Product."
        return errDesc
    elif errorCode == "err_lsp_cod":
        errDesc = "No LSP supports COD at this pincode."
        return errDesc
    elif errorCode == "err_inv_cod_local":
        errDesc = "Inventory not available for both COD and Ship Local case."
        return errDesc

def validate_fulfillment_input(pincode, article_id, skuId, quantity):
    s1 = ""
    s2 = ""
    s3 = ""
    s1 = validate_pincode(pincode)
    if not article_id.isdigit() and not skuId.isdigit():
        s2 = "\n Please enter correct Article or SKU ID."
    if not quantity.isdigit() or quantity=="0":   
        s3 = "\nPlease enter correct quantity."
    return (s1 + s2 + s3)

def skuToArticleId(skuId, prods):
    if prods:
        article_id = prods[0].article_id
        return article_id
    return ""

def stringtoList(s):
    if s == "" or s == None:
        return None
    list1 = s.split(',')
    finalList = []
    for ele in list1:
        element = ele.split("_")
        key1 = element[0]
        key2 = element[1]
        finalList.append([key1, key2])
    return finalList

@login_required
@check_role('Users')
def users(request,client_name, seller_name):
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)

    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
    url = request.get_full_path()
    
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == 'change':
                return HttpResponsePermanentRedirect(reverse('ppd-users',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == 'change':
                return HttpResponsePermanentRedirect(reverse('ppd-users',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
        
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('ppd-users',None,kwargs={'client_name':profile.managed_accounts()[0].slug,'seller_name':'all-sellers',})) 
    
    if seller_name=='all-sellers':
        current_seller_id = 0
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('ppd-users',None,kwargs={'order_state':order_state,'client_name':client_name,'seller_name':'all-sellers',})) 
    
    group = {}
    
    group_in_url = request.GET.get('group',None)
    if group_in_url:
        group_in_url.replace('%20',' ')
        usrs = User.objects.distinct().filter(groups__name=group_in_url).order_by('-last_login')
        for user in usrs:
            group[user] = group_in_url
    
    if not group_in_url:
        group_list = ['Sellers Admin','Sellers Manager','Sellers User','Sellers Client','Sellers Agent','IFS']
        usrs = User.objects.distinct().filter(groups__name__in=group_list).order_by('-last_login')
        for user in usrs:
            grps = Group.objects.filter(user=user)
            for ele in grps:
                if ele.name in group_list:
                    group[user] = ele
    
    passing_dict = {
                    'users':usrs,
                    'url':request.get_full_path(),
                    'group':group,
                    'accounts':accounts,
                    'clients':clients,
                    'loggedin':True,
                    'client_name':client_name,
                    'seller_name':seller_name,
                    }
    return render_to_response('ppd/users.html', passing_dict,context_instance=RequestContext(request))

@login_required
@check_role('Users')
def create_user(request,client_name,seller_name):
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)

    accounts = cache.get('accounts-'+client_name + str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__slug = client_name)
        cache.set('accounts-'+client_name+str(request.user.id),accounts,1800)
    url = request.get_full_path()
    
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == 'change':
                return HttpResponsePermanentRedirect(reverse('ppd-create-user',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers',}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == 'change':
                return HttpResponsePermanentRedirect(reverse('ppd-create-user',None,kwargs={'client_name':client_name,'seller_name':new_seller_name,}))
        
    #getting ids from client_name and seller_name
    client = Client.objects.select_related('id').filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('ppd-create-user',None,kwargs={'client_name':profile.managed_accounts()[0].slug,'seller_name':'all-sellers',})) 
    
    if seller_name=='all-sellers':
        current_seller_id = 0
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            current_seller_id = seller[0].id
        else:
            return HttpResponsePermanentRedirect(reverse('ppd-create-user',None,kwargs={'order_state':order_state,'client_name':client_name,'seller_name':'all-sellers',})) 
    

    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                    return HttpResponse('No user exists with username - %s' % username)
            profile = utils.get_user_profile(user)
            
            group_list = ['Sellers Admin','Sellers Manager','Sellers User','Sellers Client','Sellers Agent','IFS']
            if user.groups.filter(name__in=group_list):
                if request.GET.get('action','add') == 'edit':
                    for existing_group in user.groups.filter(name__in=group_list):
                        user.groups.remove(existing_group)
                else:
                    return HttpResponse('User already exists')
            user.groups.add(form.cleaned_data['role'])
            user.save()
           
            user_tabs = UserTab.objects.filter(user=profile)
            if user_tabs:
                if request.GET.get('action','add') == 'edit':
                    for user_tab in user_tabs:
                        user_tab.delete()
                else:
                    return HttpResponse('User already exists')
            tabs = form.cleaned_data['tabs']
            for tab in tabs:
                user_tab = UserTab()
                user_tab.tab = tab
                user_tab.user=profile
                user_tab.save()
            
            managed_accounts = profile.managed_accounts.all()
            if managed_accounts:
                if request.GET.get('action','add') == 'edit':
                    profile.managed_accounts = []
                    profile.save()
                else:
                    return HttpResponse('User already exists')
            accs = form.cleaned_data['accounts']
            for acc in accs:
                profile.managed_accounts.add(acc)
                profile.save()
            if request.GET.get('action','add') == 'edit':
                return HttpResponse('User Edited')
            if request.GET.get('action','add') == 'add':
                return HttpResponse('User Added')
        else:
            print "not a valid form"
    else:
        form = AddUserForm()
    
    passing_dict = {'loggedin':True,
                    'client_name':client_name,
                    'seller_name':seller_name,
                    'form':form,
                    'action':request.GET.get('action'),
                    'url':request.get_full_path,
                    'clients':clients,
                    'accounts':accounts,
                    'username':request.GET.get('user')
                    }
    return render_to_response('ppd/create_user.html',passing_dict,context_instance=RequestContext(request))
