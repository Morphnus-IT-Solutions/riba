from django import template
from django.utils.safestring import mark_safe
import logging
from django.core.cache import cache
from django.template.loader import render_to_string
from web.views.user_views import *
from ccm.models import Agent
import random
from utils import *
from franchise.models import *
from web.templatetags.web_tags import get_price_info
register = template.Library()

@register.simple_tag
def cc_url(request, path, append=None):
    if path == 'orders/mycart' and request.path.startswith('/orders/cancel'):
        path = request.path.split('/')
        path = path[1] + '/' + path[2] + '/' +  path[3] + '/mycart'
        return '/%s' % path
    if append:
        path = '%s%s' % (path, str(append))
    if utils.is_cc(request) or utils.is_cs(request) or utils.is_support(request):
        modified_path = path
        if hasattr(request, 'call') and request.call['url_token']:
            modified_path = '/%s/%s' % (request.call['url_token'], path)
        else:
            modified_path = '/%s' % path
        return modified_path
    elif request.wstore_slug:
        return '/w/%s/%s' % (request.wstore_slug, path)
    else:
        return '/%s' % path

@register.filter
def begins_with_HDF(request):
    text = "HDF"
    try:
        if request.startswith(text):
            return True
        else:
            return False
    except:
        return False

@register.filter
def begins_with_ATM(request):
    text = "ATM"
    try:
        if request.startswith(text):
            return True
        else:
            return False
    except:
        return False

@register.filter
def is_cc(request,show_left_panel=True):
    return utils.is_cc(request)
    
@register.filter
def is_franchise(request,show_left_panel=True):
    return utils.is_franchise(request)
    
@register.filter
def user_is_network(request):
    return utils.user_is_network(request)
    
@register.filter
def is_analytics(request):
    return utils.is_analytics(request)

@register.filter
def is_store(request,show_left_panel=True):
    return utils.is_store(request)
    
@register.filter
def is_rms(request):
    return utils.is_rms(request)

@register.filter
def is_support(request):
    return utils.is_support(request)

@register.filter
def is_cs(request,show_left_panel=True):
    return utils.is_cs(request)

@register.filter
def is_platform(request):
    return utils.is_platform(request)
    
@register.filter
def is_confirm_order(request):
    try:
        if request.path.startswith('/orders/admin/'):
            return True
        else:
            return False
    except:
        return False
@register.filter
def is_exclusive_seller(request):
    exclusive_seller,src = utils.get_exclusive_seller_from_request(request)
    if exclusive_seller:
        return True
    else:
        return False

@register.filter
def is_future_ecom(request):
    if utils.is_future_ecom(request.client.client):
        return True
    else:
        return False


@register.simple_tag
def default_dni(request):
    try:
        if is_future_ecom(request):
            return '1947'
    except Exception,e:
        pass
    return '0000'

@register.simple_tag
def first_name(request):
    try:
        first_name = request.split(' ')[0]
        return first_name
    except:
        return request
        
@register.simple_tag
def last_name(request):
    try:
        last_name = request.split(' ')[1]
        return last_name
    except:
        return ''
        
@register.filter
def append(str, arg):
    return '%s%s' % (str, arg)

@register.filter(name='money')
def formatMoney(value):
    return utils.formatMoney(value)

def render_left_panel(request):

    if utils.is_cc(request):
        id = request.call['id']
        is_dialer = False
        cli_status = 'Unverified'
        if not id:

            id = random.randrange(99999999,999999999)
            while id in request.session:
                id = random.randrange(99999999,99999999)
            request.session[id] = {}

            return dict(callid=id,request=request,user='temp')
        else:
            #if 'user' not in request.session[id] or 'profile' not in request.session[id] :
            #    user,profile = user_context(request)
            #else:
            try:
                user = request.session[id]['user']
                profile = request.session[id]['profile']
            except:
                user,profile = user_context(request)
            try:
                phone = Phone.objects.get(phone=request.call['cli'])
                if phone.is_verified:
                    cli_status = 'Verified'
            except Phone.DoesNotExist:
                cli_status = 'New'
                
            if request.call['attempt_id']:
                is_dialer = True
            return dict(profile=profile, user=user, request=request,is_dialer=is_dialer,callid=id, call_obj=request.call, cli_status=cli_status)
    else:
        return dict(user=None,request=request)
register.inclusion_tag('cc/left_panel.html')(render_left_panel)

def render_responses(request):
    if utils.is_cc(request):
        id = request.call['id']
        if 'RESPONSES' in request.session[id]:
            responses = request.session[id]['RESPONSES']
            return dict(responses=responses)
        else:
            return dict(responses=[])
    else:
        return dict(responses=[])
register.inclusion_tag('cc/responses.html')(render_responses)

@register.simple_tag
def get_franchise_username(request):
    if request.user.is_authenticated():
        profile = utils.get_user_profile(request.user)
        if str(profile.full_name).strip():
            return profile.full_name
        else:
            return request.user.username
    return ""

@register.filter
def division(value,arg):
    return value/arg

@register.filter
def mod(value, arg):
    return value % arg

def show_excel_link(request, excel):
    full_path=request.get_full_path()
    return dict(request=request, full_path=full_path, excel=excel)
register.inclusion_tag('reports/show_excel_link.html')(show_excel_link)

@register.simple_tag
def get_agentname(request):
    if request.user.is_authenticated() and utils.is_cs(request):
        agent = Agent.objects.get(user = request.user)
        return agent
    else:
        return ''

def table_display_with_bar(request, table_lists, title, excel_link, bar_field_position=None, seconds_format=None):
    max_val = [0]*(len(table_lists[0]))
    if bar_field_position:
        for i in bar_field_position:
            pindex = i - 1
            for a in table_lists[1:]:
                if a[pindex]>max_val[pindex]:
                    max_val[pindex] = a[pindex]
    return dict(request=request, table_lists=table_lists, title=title, excel_link=excel_link, bar_field_position=bar_field_position, max_val=max_val, seconds_format=seconds_format)
register.inclusion_tag('reports/table_display_with_bar.html')(table_display_with_bar)

@register.simple_tag
def seconds_format_change(counter, seconds_format, m):
    if seconds_format and m:
        if counter in seconds_format:
            return format_seconds(m)
    return m

@register.simple_tag
def width_calculate(m, max_val, counter, mult_by):
    max_of_list = max_val[counter-1]
    if max_of_list == 0:
        return 0
    else:
        width = (m/max_of_list)*mult_by
        return width

@register.simple_tag
def avg_order_value(orders, count):
    avg = int(math.ceil(orders/count))
    return avg

def get_newsletter_box(request):
    return dict(request=request)
register.inclusion_tag('user/newsletter.html')(get_newsletter_box)

def show_commision(request, product, franc_or_network):
    message = {}
    from web.views.franchise_views import calculate_commission_value_per_product
    message = calculate_commission_value_per_product(request, product)
    
    if franc_or_network == 'franchise': #if 'is_franchise' in request.session and request.session['is_franchise']:
        message['network_commision'] = str(message['network_commision']).replace('.', '-')
        message['franchise_commision'] = str(message['franchise_commision']).replace('.', '-')

    return dict(request=request, franc_or_network = franc_or_network, product=product, message = message)
register.inclusion_tag('products/product_commision.html')(show_commision)

def show_cat_overview(request , itz_offer, category):
    total_results = 0
    gmin = 1000
    show_this_cat = False
    max_perc_off = 1
    main_product ={}
    second_prod = {}
    third_prod = {}
    fourth_prod = {}
    
    from catalog.models import Tag
    from utils.solrutils import solr_search
    
    if 'products' in itz_offer[category.id]:
        if 'total_results' in itz_offer[category.id]:
            show_this_cat = True
            total_results = itz_offer[category.id]['total_results']
            gmin = itz_offer[category.id]['gmin']

            tag_hero = Tag.objects.filter(tag="itz_hero")
            if tag_hero:
                tag_hero = tag_hero[0]
            
            params = {'rows':200}
            q = 'tag_id:%s AND category_id:%s' % (tag_hero.id, category.id)
            solr_result = solr_search(q, **params)
            prod_ids_in_solr = [int(doc['id']) for doc in solr_result.results]

            prod_count = 1
            for prods in itz_offer[category.id]['products']:
                for tags in prods['tagset']:
                    if tags.type == 'itz_offer' and 'product' in prods:
                        if prod_ids_in_solr and prod_ids_in_solr[0] == prods['product'].id:
                            main_product = prods
                            prod_count = prod_count-1
                        elif prod_count == 1:
                            second_prod = prods
                            second_prod['is_available'] = True
                        elif prod_count == 2 and 'product' in second_prod and prods['product'].id != second_prod['product'].id:
                            third_prod = prods
                            third_prod['is_available'] = True
                        elif prod_count == 3 and 'product' in third_prod and prods['product'].id != third_prod['product'].id and 'product' in second_prod and prods['product'].id != second_prod['product'].id:
                            fourth_prod = prods
                            fourth_prod['is_available'] = True
                        prod_count = prod_count+1
                
                if prods['price_info']['discount'] and prods['price_info']['discount'] > max_perc_off:
                    max_perc_off = prods['price_info']['discount']
            if not prod_ids_in_solr and second_prod:
                main_product = second_prod
                
    return dict(request=request, 
                itz_offer = itz_offer, 
                category= category, 
                total_results = total_results, 
                show_this_cat = show_this_cat,
                main_product = main_product,
                second_prod = second_prod,
                third_prod = third_prod,
                fourth_prod = fourth_prod,
                gmin = gmin, 
                max_perc_off = max_perc_off)
register.inclusion_tag('web/home_page.html')(show_cat_overview)

def render_itz_perf_tab(request, tab, net_details):
    return dict(request=request,
                net_details = net_details,
                tab = tab,)
register.inclusion_tag('performance/itz_perf_tab.html')(render_itz_perf_tab)

@register.simple_tag
def replace_dot_with_dash(commission_amnt):
    return str(commission_amnt).replace('.', '-')

@register.simple_tag
def get_c1_details(request, prod_id, attribute):
    from utils.utils import get_categories_by_id
    parent_cat_dict = get_categories_by_id(request, [str(prod_id)])
    if parent_cat_dict['c1_categories'] and attribute == "C1_ID":
        return parent_cat_dict['c1_categories'][0].id
    elif parent_cat_dict['c1_categories'] and attribute == "C1_NAME":
        return parent_cat_dict['c1_categories'][0]
    else:
        return None

