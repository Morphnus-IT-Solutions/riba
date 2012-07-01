import hashlib
import logging
from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect
from django.template import RequestContext
from django.utils.safestring import mark_safe
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.core import serializers
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
from django.contrib.auth import authenticate, login as auth_login
from django.views.decorators.csrf import csrf_protect
from django.contrib.sites.models import Site, RequestSite
from django.contrib.auth import REDIRECT_FIELD_NAME
from django.utils import simplejson
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.cache import cache
from catalog.models import *
from categories.models import *
from web.models import Banner
from orders.models import *
from utils import utils
from lists.models import *
from tracking.models import ViewUsage
import logging
from datetime import datetime,timedelta
from django.views.decorators.cache import never_cache
from feedback.models import *
from decimal import Decimal
from django.contrib.auth.forms import AuthenticationForm
import itertools
import Cookie

log = logging.getLogger('request')

@login_required
def reports_home(request):
    return render_to_response(request.client.custom_home_page,
        None,
        context_instance=RequestContext(request))


def get_banners(request):
    ban = Banner.objects.filter(client = request.client.client).order_by('sort_order')
    return ban

def futurebazaar_home_page_context(request):
    _client = request.client.client
    '''
    Check if user logged in by FaceBook
    And get Recommendation if User is logged in by FaceBook
    '''
    logged_through_facebook = False
    users_recommendations = []
    '''
    if request.user.is_authenticated() and 'logged_through_facebook' in request.session:
        logged_through_facebook = True
        recommended_ids = utils.get_recommendations(request)
        if recommended_ids:
            recommended_ids = recommended_ids[:4]
            users_recommendations = create_context_for_search_results(recommended_ids, request)
    '''
    home_page_ctxt_key = 'homepage#%s' % (request.client.client.id)
    home_page_context = cache.get(home_page_ctxt_key)
    if not home_page_context:
        '''
        Get Daily Deals Context
        '''
#        todays_deals = DailyDeal.objects.select_related('id', 'type').filter(status='published',\
#                      starts_on__lte=datetime.now(),ends_on__gte=datetime.now(), client=_client)
#        daily_deal_ids = []
#        steal_of_the_day = None
#        daily_deals = None
#        clearance_daily_deal = None
#        product_deals = DailyDealProduct.objects.filter(daily_deal__in=todays_deals)
#        hero_deal = []
#        clearance_daily_deal_products = []
#        daily_deals_products = []
#        for deal in todays_deals:
#            deal_type = deal.type
#            if deal_type == 'hero_deal':
#                steal_of_the_day = deal
#                hero_deal = product_deals.select_related('product').filter(daily_deal=deal)
#            elif deal_type == 'todays_deals':
#                daily_deals = deal
#                daily_deals_products = product_deals.select_related('product').filter(daily_deal=deal).order_by('order')[:5]
#            elif deal_type == 'clearance_deals':
#                clearance_daily_deal = deal
#                clearance_daily_deal_products = product_deals.select_related('product').filter(daily_deal=deal).order_by('order')[:5]
#        '''
#        Get Hero Deal of the Day
#        '''
#        hero_deal_product_ids = []
#        hero_deals_count = 0
#        if hero_deal:
#            hero_deals_count = hero_deal.count()
#            for deal in hero_deal:
#                daily_deal_ids.append(deal.product.id)
#                hero_deal_product_ids.append(deal.product.id)
#        '''
#        Get Todays Deal of the Day
#        '''
#        for p in daily_deals_products:
#            daily_deal_ids.append(p.product.id)
#        daily_deals_start = 0
#        daily_deals_end = daily_deals_start + len(daily_deals_products)
#        '''
#        Get Clearance Deals Of the Day
#        '''
#        for p in clearance_daily_deal_products:
#            daily_deal_ids.append(p.product.id)
#        clearance_deals_context = None
#        clearance_start = 0
#        clearance_end = 0
#        '''
#        Get Top Sellers of Previous 7 Days
#        '''
#        top_sellers_ids = utils.get_top_sellers(request)
#        top_sellers_ids = top_sellers_ids[:5]
#        if hero_deal_product_ids:
#            try:
#                for prod_id in hero_deal_product_ids:
#                    top_sellers_ids.remove(prod_id)
#            except ValueError:
#                pass
#        for id in top_sellers_ids:
#            daily_deal_ids.append(int(id))
#        '''
#        Get New Arrivals
#        '''
#        new_arrival_ids = utils.get_new_arrivals(request, 5, **{'exclude_ids':daily_deal_ids})
#        for id in new_arrival_ids:
#            daily_deal_ids.append(int(id))
#        new_arrivals_context = None
#        new_arrivals_start = 0
#        new_arrivals_end = 0
#        '''
#        Get Products Context for product ids in Current Deals
#        '''
#        daily_deal_ids = daily_deal_ids[hero_deals_count:]
#        deals_context = create_context_for_search_results(daily_deal_ids, request) 
#        daily_deals_context = deals_context[daily_deals_start:daily_deals_end]
#        for deal_ctxt in daily_deals_context:
#            deal_ctxt['deal_type'] = 'todays_deal'
#        hero_deal = {'main_banner':None, 'menu_banner':None}
#        top_sellers = []
#        if steal_of_the_day:
#            hero_deal_image = None
#            try:
#                hero_deal_image = DailyDealImage.objects.get(daily_deal=steal_of_the_day)
#            except DailyDealImage.MultipleObjectsReturned:
#                hero_deal_image = DailyDealImage.objects.filter(daily_deal=steal_of_the_day).order_by('order')[0]
#            except DailyDealImage.DoesNotExist:
#                pass
#            if hero_deal_image:
#                hero_deal['main_banner'] = hero_deal_image.banner
#
#        if clearance_daily_deal:
#            clearance_start = daily_deals_end
#            clearance_end = clearance_start + len(clearance_daily_deal_products)
#            top_sellers_start = clearance_end
#            clearance_deals_context = deals_context[clearance_start:clearance_end]
#            for clearance in clearance_deals_context:
#                clearance['deal_type'] = 'home_clearance'
#                clearance['retailer'] = None
#                tag_set = clearance.get('tagset',[])
#                for tag in tag_set:
#                    if tag.type == 'new_clearance_sale':
#                         clearance['retailer'] = tag.tag
#        else:
#            top_sellers_start = daily_deals_end
#        if top_sellers_ids:
#            top_sellers_end = top_sellers_start + len(top_sellers_ids)
#            top_sellers = deals_context[top_sellers_start:top_sellers_end]
#            new_arrivals_start = top_sellers_end
#        else:
#            new_arrivals_start = top_sellers_start
#
#        if new_arrival_ids:
#            new_arrivals_end = new_arrivals_start + len(new_arrival_ids) 
#            new_arrivals_context = deals_context[new_arrivals_start:new_arrivals_end]

        '''
        Get Banners
        '''
        banners = get_banners(request) 

        home_page_context = {
#            'deal' : steal_of_the_day,
#            'hero_deal' : hero_deal,
#            'daily_deals_context' : daily_deals_context,
#            'clearance_deals_context' : clearance_deals_context,
#            'top_sellers' : top_sellers,
#            'new_arrivals_context' : new_arrivals_context,
            'banners' : banners
        }
        '''
        Caching home page context for 10 Minutes
        '''
        cache.set(home_page_ctxt_key, home_page_context, 600)
    try:
        promotion_offer = List.objects.get(type='promotion_offer',starts_on__lte = datetime.now(), ends_on__gte = datetime.now())
    except List.DoesNotExist:
        promotion_offer = None
    except List.MultipleObjectsReturned:
        promotion_offer = List.objects.filter(type='promotion_offer',starts_on__lte = datetime.now(), ends_on__gte = datetime.now()).order_by("-id")[0]
    try:
        promotion = List.objects.get(type='promotions',starts_on__lte = datetime.now(), ends_on__gte = datetime.now())
    except List.DoesNotExist:
        promotion = None
    except List.MultipleObjectsReturned:
        promotion = List.objects.filter(type='promotions',starts_on__lte = datetime.now(), ends_on__gte = datetime.now()).order_by("-id")[0]
    home_page_context['users_recommendations'] = users_recommendations
    home_page_context['logged_through_facebook'] = logged_through_facebook
    home_page_context['promotion_offer'] = promotion_offer
    home_page_context['promotion'] = promotion
    return home_page_context

def get_categories(request):
    _client = request.client.client
    items = []
    top_categories = [c.category.id for c in FeaturedCategories.objects.select_related("category").filter(category__client = _client, type = 'home_page').order_by('sort_order')]
    parent_category = Category.objects.filter(client=_client, id__in = top_categories).order_by()
    for r1 in parent_category:
        category_level_2 = CategoryGraph.objects.filter(parent = r1).order_by('sort_order')[:5]
        ritems = {'parent': r1, 'children': category_level_2}
        items.append(ritems)
    return items

def get_new_arrivals(request):
    _client = request.client.client
    prod = Product.objects.filter(category__client = _client, status = 'Active').order_by('id')
    return sorted(prod, key = lambda x: x.id, reverse = True)[:5]


def get_customer_testimonials(request):
    _client = request.client.client
    test = Feedback.objects.filter(client = _client, type = 'testimonial').order_by('-id')
    return sorted(test, key = lambda x: x.id, reverse = True)[:5]

def get_featured_categories(request):
    _client = request.client.client
    featured_categories = FeaturedCategories.objects.filter(category__client = _client, type = 'home_page').select_related('category').order_by('sort_order')
    return featured_categories


def get_brands(request):
    q = 'client_id:%s AND -type:variable' % request.client.client.id
    params = {}
    params['rows'] = 200
    solr_result = solr_search(q,**params)
    br = [int(doc['brand_id']) for doc in solr_result.results]
    brands = Brand.objects.filter(id__in=br)
    return brands



@never_cache
def index(request):
    ctxt = ''
    return render_to_response('web/home/home.html',
            ctxt,
            context_instance=RequestContext(request))


@csrf_protect
@never_cache
def login(request, template_name='registration/login.html',
          redirect_field_name=REDIRECT_FIELD_NAME,
          authentication_form=AuthenticationForm):
    """Displays the login form and handles the login action."""
    redirect_to = request.REQUEST.get(redirect_field_name, '')

    error = ''
    if request.method == "POST":
        form = authentication_form(data=request.POST)
        if form.is_valid():
            #Franchise-network e.g. Itz
            if utils.is_franchise(request):
                profile = utils.get_user_profile(form.get_user())
                if not profile:
                    error = "No profile found related to this email"
                elif not is_valid_franchise(profile):
                    error = "You do not have rights to access this interface. Please request your manager to get the rights."
                #else:
                #    perm = 'auth.access_franchise'
                #    if profile and not profile.user.has_perm(perm):
                #        error = 'You do not have rights to access Franchise interface. Please request your manager to get the rights OR Add permissions through admin to this user but dont make superuser.'
            elif utils.is_cc(request):
                #profile = utils.get_profile_by_email_or_phone(form.get_user())
                profile = utils.get_user_profile(form.get_user())
                perm = (request.client.type == 'store') and 'auth.access_store' or 'auth.access_callcenter'
                if profile and not profile.user.has_perm(perm):
                    error = 'You do not have rights to access this interface. Please request your manager to get the rights.'
            #Sellers Hub:
            elif utils.is_platform(request):
                profile = utils.get_user_profile(form.get_user())
                perm1 = 'users.access_ppd'
                perm2 = 'users.access_ifs'
                if profile and not (profile.user.has_perm(perm1) or profile.user.has_perm(perm2)):
                    error = 'You do not have rights to access this interface. Please request your manager to get the rights.'
            if not error:
                if utils.is_platform(request) and profile:
                    redirect_to = "/home"
                # Light security check -- make sure redirect_to isn't garbage.
                if not redirect_to or ' ' in redirect_to:
                    redirect_to = settings.LOGIN_REDIRECT_URL

                # Heavier security check -- redirects to http://example.com should
                # not be allowed, but things like /view/?param=http://example.com
                # should be allowed. This regex checks if there is a '//' *before* a
                # question mark.
                elif '//' in redirect_to and re.match(r'[^\?]*//', redirect_to):
                    redirect_to = settings.LOGIN_REDIRECT_URL
                # Okay, security checks complete. Log the user in.
                auth_login(request, form.get_user())
                if utils.is_platform(request):
                    profile = utils.get_user_profile(request.user)
                    sellers = profile.managed_accounts.filter(client = request.client.client)
                    request.session['all_sellers'] = sellers
                    request.session['seller'] = [sellers[0]]

                if request.session.test_cookie_worked():
                    request.session.delete_test_cookie()
                return HttpResponseRedirect(redirect_to)

    else:
        form = authentication_form(request)

    request.session.set_test_cookie()
    if Site._meta.installed:
        current_site = Site.objects.get_current()
    else:
        current_site = RequestSite(request)
    return render_to_response(template_name, {
        'error': error,
        'form': form,
        'redirect_field_name': redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }, context_instance=RequestContext(request))

def category_menu(request):
    categories =  MegaDropDown.objects.filter(type='menu_level2_category', client=request.client.client).order_by('sort_order')

    return render_to_response('web/category_menu.html',
            {
                'categories':categories,
            },
            context_instance=RequestContext(request))


def suggest(request):
    if request.method == 'GET':
        if 'chars' not in request.GET:
            return HttpResponse()
        q = request.GET['chars']
        from utils.solrutils import solr_search
        q += ' AND currency:inr AND client_id: %s' % request.client.client.id
        search_result = solr_search(q,fields='title')
        titles = [doc['title'] for doc in search_result.results]
        result = []
        for t in titles:
            tt = dict(text = t)
            result.append(tt)
        return HttpResponse(simplejson.dumps(result))
    else:
        return HttpResponse()

def testimonials(request):
    _client = request.client.client
    testimonials = Feedback.objects.filter(client=_client,type="testimonial").order_by('-id')
    page_no = request.GET.get('page',1)
    page_no = int(page_no)
    items_per_page = 10
    total_results = len(testimonials)
    total_pages = int(math.ceil(Decimal(total_results)/Decimal(items_per_page)))
    pagination = utils.getPaginationContext(page_no, total_pages, '')
    pagination['result_from'] = (page_no-1) * items_per_page
    pagination['result_to'] = utils.ternary(page_no*items_per_page > total_results, total_results, page_no*items_per_page)
    testimonials = testimonials[:int(pagination['result_to'])]
    testimonials = testimonials[int(pagination['result_from']):]
    pagination['result_from'] = pagination['result_from'] + 1
    return render_to_response('web/home/detail_testimonials.html',
            {
                'testimonials':testimonials,
                'pagination':pagination,
                'total_results':total_results
            },
            context_instance=RequestContext(request))

def sitemap(request):
    items = []
    if not items:
        items = []
        mega_drops = MegaDropDown.objects.filter(type= "menu_level2_category",client=request.client.client).order_by('category__name')
        items_per_column = int(math.ceil(Decimal(len(mega_drops))/3))
        for item in mega_drops:
            sub_cats = CategoryGraph.objects.filter(parent=item.category)
            active_cats = []
            if item.category.id not in [1097, 974, 976, 962]:
                for cat in sub_cats:
                    if cat.category.has_products():
                        active_cats.append(cat)
                if utils.get_future_ecom_prod() == request.client.client:
                    if len(active_cats) == 1 or item.category.id == 1097:
                        active_cats = []
            mitems = {}
            mitems={'item':item, 'active_cats':active_cats}
            if active_cats:
                items.append(mitems)
        items_first_column = items[:items_per_column]
        items_second_column = items[items_per_column:(2*items_per_column)]
        items_third_column = items[(2*items_per_column):]
    return render_to_response('pages/info/sitemap.html',
            {
                'items_first_column':items_first_column,
                'items_second_column':items_second_column,
                'items_third_column':items_third_column,
                'request':request,
            },
            context_instance=RequestContext(request))



def render_offer_pdp(list):
    datas = []
    if list:
        list = list[0]
        item = None
        listitems = list.listitem_set.filter(status='active', starts_on__lte=datetime.now(),ends_on__gte=datetime.now()).order_by('sequence')
        if listitems:
            item = listitems[0]
        else:
            listitems = list.listitem_set.filter(status='active').order_by('sequence')
            item = listitems[0]

        product = item.sku.product
        product_url = product.url()
        return HttpResponseRedirect("/%s" % product_url)
    return HttpResponseRedirect("http://www.futurebazaar.com/")
