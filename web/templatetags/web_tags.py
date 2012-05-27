from django import template
from django.utils.safestring import mark_safe
import logging
from django.core.cache import cache
from django.db.models import Q
from django.template.loader import render_to_string
from web.forms import SearchForm
from web.models import Announcements
from catalog.models import *
from categories.models import *
from feedback.models import *
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from utils import utils
import re, time
from web.views.order_view import *
from activitystream.models import Activity
from datetime import datetime, timedelta
from users.models import NewsLetter
from decimal import Decimal
from web import search_form_default
from pricing.models import *
from web import search_form_default
from communications.models import Email as LEmail
from accounts.models import Account
from promotions.models import FeaturedCategories
from django.core.cache import cache
#from scripts.upload_clearance import format_tag
 

register = template.Library()

import logging
from django.conf import settings
log = logging.getLogger('request')



@register.filter
def is_user_authenticated(request):
    if request.user.is_authenticated():
        return True
    return False

@register.filter
def is_future_ecommerce(request):
    return utils.is_future_ecom(request.client.client)

@register.filter
def cart_display(path):
    if path.startswith('/orders/cancel'):
        return False
    else:
        return True

@register.simple_tag
def get_username(request):
    if request.user.is_authenticated():
        user = request.user
        profile = utils.get_user_profile(request.user)
        if str(profile.full_name).strip():
            return profile.full_name
        else:
            return user.username
    return ''


def daterange(title, search_trend, from_date, to_date, request,args=None, client_name=None):
    url = request.path
    url += '?'
    return dict(title=title, search_trend=search_trend, to_date=to_date, from_date=from_date, request=request, url=url, args=args, client_name=client_name)
register.inclusion_tag('reports/daterange.html')(daterange)

def feature_tag(product,show_title=None):
    if show_title == "False":
        show_title = False
    else:
        show_title =True
    if not product.product_type:
        return {}
    feature_grp = FeatureGroup.objects.filter(product_type = product.product_type).order_by('sort_order')
    datas = []
    features = product.productfeatures_set.select_related(
        'feature',
        'feature__group').all().order_by(
        'feature__group__sort_order',
        'feature__sort_order')
    for grp in feature_grp:
        data = []
        for feature in features:
            if not feature.feature.group:
                continue
            if feature.feature.group.id != grp.id:
                continue
            feature_content = {}
            content = ''
            if feature.feature.type == 'number':
                try:
                    content = ("%.1f" % feature.value).replace('.0','')  + ' ' + feature.feature.unit.name
                except:
                    content = ("%.1f" % feature.value).replace('.0','')
            elif feature.feature.type == 'text':
                try:
                    content = feature.data
                except:
                    pass
            elif feature.feature.type == 'boolean':
                if feature.bool:
                    content = 'Yes'
                else:
                    content = 'No'
            try:
                feature_content = dict(name=feature.feature.name,value=content)
            except:
                pass
            data.append(feature_content)
        group = {}
        group['name'] = grp.name
        group['features'] = data
        if features and data:
            datas.append(group)
    return dict(datas=datas,product_name=product.title,show_title=show_title)
register.inclusion_tag('products/features_specify.html')(feature_tag)

def battle_section_tag(request, products, earmark_tags):
    return dict(products=products,request=request, earmark_tags=earmark_tags)
register.inclusion_tag('lists/battle_section.html')(battle_section_tag)


@register.simple_tag
def hide_subscribe(request):
    if request.user.is_authenticated():
        user_info = utils.get_user_info(request)
        user = user_info['user']
        profile = user_info['profile']
        try:
            subscribed_user = DailySubscription.objects.filter(user=user)
            return True
        except:
            return False
    else:
        return True

@register.simple_tag
def add_class(class_name, counter):
    class_name = class_name + '_' + str(counter)
    return class_name

def seller_drop(seller,seller_id):
    return dict(seller=seller,seller_id=seller_id)
register.inclusion_tag('reports/seller_drop.html')(seller_drop)

@register.simple_tag
def filter_href(request, filter_key, filter_value):
    p = re.compile(filter_key + '=[^&]*')
    full_path = request.get_full_path()
    matches = p.findall(full_path)
    for match in matches:
        full_path = full_path.replace(match, '%s=%s' % (filter_key, filter_value))
    if not matches:
        if request.GET:
            full_path = '%s&%s=%s' % (full_path, filter_key, filter_value)
        else:
            full_path = '%s?%s=%s' % (full_path, filter_key, filter_value)
    return full_path

@register.simple_tag
def category_href(request, filter_key, filter_value):
    q = re.compile('q=[^&]*')
    full_path = request.get_full_path()
    paths = full_path.split("/")[:-1]
    request_path = ''
    for path in paths:
        if path:
            request_path += "/%s" % (path)
    matches = q.findall(full_path)
    match = None#matches[0] if matches else None
    request_path += '/'
    arg_path = ''
    filter = "%s=%s" % (filter_key, filter_value)
    if match:
        request_path += "?%s" % (match)
        if filter_key:
            request_path += "&%s" % (filter)
    elif filter_key:
        request_path += "?%s" % (filter)
    return request_path

@register.simple_tag
def category_href_seo(request, filter_key, filter_value):
    q = re.compile('q=[^&]*')
    full_path = request.get_full_path()
    paths = full_path.split("/")[:-1]
    request_path = ''
    if not request.GET.get('c'):
    #    paths.append(filter_name.split("(")[0].strip())
        if filter_value:
            paths.append(Category.objects.get(pk = filter_value).slug)
    else:
        paths.pop()
        if filter_value:
            paths.append(Category.objects.get(pk = filter_value).slug)
    for path in paths:
        if path:
            request_path += "/%s" % (path)
    matches = q.findall(full_path)
    match = None#matches[0] if matches else None
    request_path += '/'
    arg_path = ''
    filter = "%s=%s" % (filter_key, filter_value)
    if match:
        request_path += "?%s" % (match)
        if filter_key:
            request_path += "&%s" % (filter)
    elif filter_key:
        request_path += "?%s" % (filter)
    return request_path


@register.simple_tag
def link_filter_href(request, filter_key, filter_value):
    p = re.compile(filter_key + '=[^&]*')
    full_path = request.get_full_path()
    matches = p.findall(full_path)
    for match in matches:
        full_path = filter_value and full_path.replace(match, '%s=%s' % (filter_key, filter_value)) or full_path.replace(request.GET and '' or '&'+ match, '')
    if not matches and filter_value:
        full_path = '%s%s%s=%s' % (full_path, request.GET and '&' or '?', filter_key, filter_value)
    pg = re.compile('[&?]page=[^&]*')
    page_match = pg.findall(full_path)
    if page_match:
        full_path = full_path.replace(request.GET and '' or page_match[0], '')
        full_path = full_path.replace("/&", "/?")
    return full_path


@register.simple_tag
def filter_class(pos, request, filter_key, filter_value):
    params = request.GET
    if request.GET.get(filter_key, None) != None:
        if str(request.GET[filter_key]) == str(filter_value):
            return "selected_link"
    else:
        if filter_value == "" or pos == "d":
            return "selected_link"
    return "link"

@register.simple_tag
def wstore_logo(request):
    if request.client.type in ['website','cc']:
        return '%s-logo.gif' % request.client.code
    if request.client.type in ['mobileweb']:
        return '%s-mlogo.gif' % request.client.code

@register.simple_tag
def render_favicon(request):
    return '/media/images/favicon.ico'

@register.simple_tag
def page_title(request):
    return request.client.client.name

@register.simple_tag
def book_js(request):
    if utils.is_future_ecom(request.client.client) or utils.is_ezoneonline(request.client.client):
        return '/media/js/book_fb.js'
    elif utils.is_holii_client(request.client.client):
        return '/media/js/book_holii.js'
    return '/media/js/book_chaupaati.js'


@register.filter
def has_param(request,param):
    if request.GET.get(param,None):
        return True
    else:
        return False

@register.filter
def mod(value, arg):
    return value % arg

@register.filter
def split_text(string, delimiter=' '):
    return re.split(r'[%s]+' % delimiter,string)

@register.filter
def truncate(value, arg):
    try:
        ending = '..'
        if len(value) > arg:
            r = range(arg)
            r.reverse()
            for x in r:
                if value[x] == '':
                    return value[:x-1] + ending
            return value[:arg-1] + ending
        else:
            return value
    except:
        return value

@register.filter
def truncate_category(value, arg):
    value += " Deals"
    try:
        ending = '..'
        if len(value) > arg:
            r = range(arg)
            r.reverse()
            for x in r:
                if value[x] == '':
                    return value[:x-1] + ending
            return value[:arg-1] + ending
        else:
            return value
    except:
        return value

@register.filter
def limit_chars(value, arg):
    value = value.upper()
    try:
        if len(value) > arg:
            r = range(arg)
            r.reverse()
            for x in r:
                if value[x] == '':
                    return value[:x-1] + ending
            return value[:arg-1]
        else:
            return value
    except:
        return value

def render_search_form(request):
    if request.method == 'post':
        params = request.POST
    else:
        params = request.GET
    if search_form_default.has_key(request.client.client.name):
        placeholder = {
            'placeholder' : search_form_default[request.client.client.name]
            }
    else:
        placeholder = {}

    search_form = SearchForm(params, **placeholder)
    return {'search_form':search_form,'request':request}
register.inclusion_tag('web/searchForm.html')(render_search_form)

def render_search_form_fb(request):
    if request.method == 'post':
        params = request.POST
    else:
        params = request.GET
    if search_form_default.has_key(request.client.client.name):
        placeholder = {
            'placeholder' : search_form_default[request.client.client.name]
            }
    else:
        placeholder = {}

    search_form = SearchForm(params, **placeholder)
    return {'search_form':search_form,'request':request}
register.inclusion_tag('web/searchForm.html')(render_search_form_fb)

@register.simple_tag
def order_items(request):
    if 'cart_id' in request.session:
        order_id = request.session['cart_id']
    else:
        order_id = None
    order_items = []
    if order_id:
        from orders.models import OrderItem
        order_items = OrderItem.objects.filter(order__id=order_id)
    return len(order_items)

@register.filter
def is_email_subscribed(email,request):
    client = request.client.client
    user_info = utils.get_user_info(request)
    user = user_info['user']
    profile = user_info['profile']
    daily_subscriptions = DailySubscription.objects.filter(newsletter__client=client,email_alert_on__user=profile,email_alert_on__email=email)
    if daily_subscriptions:
        return daily_subscriptions[0].is_email_alert
    else:
        return False

@register.filter
def is_phone_subscribed(phone,request):
    client = request.client.client
    user_info = utils.get_user_info(request)
    user = user_info['user']
    profile = user_info['profile']
    daily_subscriptions = DailySubscription.objects.filter(newsletter__client=client,sms_alert_on__user=profile,sms_alert_on__phone=phone)
    if daily_subscriptions:
        return daily_subscriptions[0].is_sms_alert
    else:
        return False

def product_images(product):
    return dict(images=ProductImage.objects.filter(product=product))
register.inclusion_tag('products/images.html')(product_images)

def render_ppd_header(request):
    profile = request.user.get_profile()
    client_name=profile.managed_clients()[0].slug
    return dict(request=request,show_signin=True,show_menu=False,show_search=False, phonepedeal=True, client_name=client_name)
register.inclusion_tag('web/ppd_header.html')(render_ppd_header)

def render_cs_header(request):
    if utils.is_cs(request):
        return dict(request=request, show_signin=True, show_menu=True, show_search=True)
register.inclusion_tag('cs/header.html')(render_cs_header)

def render_header(request):
    #if request.client.client == utils.get_future_ecom() and request.client.type == 'mobileweb':
    if utils.is_future_ecom(request.client.client) and request.client.type == 'mobileweb':
        return dict(request=request,show_signin=True,show_menu=False,show_search=True)
    #if request.client.type not in ['cc'] and request.client.client == utils.get_future_ecom():
    if not utils.is_cc(request) and utils.is_future_ecom(request.client.client) and not request.user.is_authenticated():
        return dict(request=request,show_signin=False,show_menu=False, show_search=False)
#    if request.path.startswith('/a/'):
#        return dict(request=request,show_signin=True,show_menu=False,show_search=False, phonepedeal=True)
    if utils.is_franchise(request) and utils.is_future_ecom(request.client.client):
        return dict(request=request,show_signin=True,show_menu=True,show_search=True)
    else:
        return dict(request=request, show_signin=True, show_menu=True, show_search=True)
register.inclusion_tag('web/header.html')(render_header)

def render_ppd_footer(request):
    return dict(request=request, show_footer=True,show_signin=True)
register.inclusion_tag('web/ppd_footer.html')(render_ppd_footer)

def render_footer(request):
    app_settings = {}#{'facebook_app_id':settings.FACEBOOK_APPLICATION_ID}
    return dict(request=request, show_footer=True,show_signin=True, app_settings=app_settings)
register.inclusion_tag('web/footer.html')(render_footer)

def render_admin_footer(request):
    if utils.is_future_ecom(request.client.client) and request.client.type == 'mobileweb':#hasattr(request,'mex_seller'):
        return dict(request=request, show_footer=True,show_signin=False)
    if utils.is_future_ecom(request.client.client):
        return dict(request=request, show_footer=True,future_ecom=True,show_sigin=False)
    else:
        return dict(request=request, show_footer=True,show_signin=True)
register.inclusion_tag('web/admin_footer.html')(render_admin_footer)

def feature_icons(product):
    try:
        feature = ProductFeatures.objects.get(
                feature__use_for_icons = True, product=product)
        pfsc_set = feature.productfeatureselectedchoice_set.select_related('choice').all()
        if not pfsc_set:
            choices = None
        else:
            choices = [pfsc.choice for pfsc in pfsc_set]
        return dict(choices=choices, product=product)
    except ProductFeatures.DoesNotExist:
        return dict(choices = None, product=product)
register.inclusion_tag('products/feature_icons.html')(feature_icons)

def variant_features(product):
    if not product.type == 'variant':
        return dict(features = None)
    try:
        variant_set = ProductVariant.objects.filter(variant=product)
        if not variant_set:
            return dict(features=None)
        variant = variant_set[0]
        variable_features = ProductFeatures.objects.filter(product=variant.blueprint,type='variable')
        features = ProductFeatures.objects.filter(product=product,feature__in=[x.feature for x in variable_features])
        return dict(features=features)
    except ProductFeatures.DoesNotExist:
        return dict(features=None)
register.inclusion_tag('products/variant_features.html')(variant_features)


def product_variants(product, request):
    if product.type == 'variable':
        return dict(
                product = product,
                variants = product.variants.select_related('variant').all(),
                request = request
                )
    if product.type == 'variant':
        blueprint = ProductVariant.objects.filter(variant=product)
        if blueprint:
            blueprint = blueprint[0].blueprint
            return dict(
                    product = product,
                    variants = blueprint.variants.select_related(
                        'variant').all(),
                    request = request
                    )
    return dict(variants=None, product=product, request=request)
register.inclusion_tag('products/variants.html')(product_variants)

def product_features(product):
    features = product.productfeatures_set.select_related(
            'feature','feature__group').filter(
            feature__is_visible=True).order_by(
                    'feature__group__sort_order', 'feature__sort_order')
    groups = []
    last_group = None
    running_group = None
    for pf in features:
        if not pf.feature.group:
            continue
        if pf.feature.group != last_group:
            if running_group:
                groups.append(running_group)
            last_group = pf.feature.group
            running_group = dict(group=pf.feature.group, features=[pf])
        else:
            running_group['features'].append(pf)
    return dict(product=product, groups=groups)
register.inclusion_tag('products/features.html')(product_features)


def product_key_features(product):
    try:
        feature = ProductFeatures.objects.get(
                feature__use_as_key_features = True, product=product)
        return dict(product = product, features = feature.to_python_value())
    except ProductFeatures.DoesNotExist:
        return dict(features = None, product=product)
register.inclusion_tag('products/key_features.html')(product_key_features)

def product_key_features_inline(product):
    try:
        feature = ProductFeatures.objects.get(
                feature__use_as_key_features = True, product=product)
        return dict(product = product, features = ", ".join(feature.to_python_value()))
    except ProductFeatures.DoesNotExist:
        return dict(features = None, product=product)
register.inclusion_tag('products/key_features_inline.html')(product_key_features_inline)

@register.filter
def divisibleby(value, arg):
    return value % arg == 0

def checkout_tabs(request, tab):
    tab = request.path.split('/')[-1]
    tabs = []
    digits = re.compile('\d+')
    if digits.match(tab):
        tabs.append(dict(name=str(tab), text='Confirm your Phone Number'))
        return dict(request=request, tab=tab, tabs=tabs)
    # always show cart
    if request.path.startswith('/orders/admin/'):
        tabs.append(dict(name='confirm', text='Confirm the Order ID'))
        tabs.append(dict(name='mycart', text='Review the Order'))
    elif utils.is_cc(request):
        tabs.append(dict(name='mycart', text='Review the Cart'))
    elif request.path.startswith('/cancel-order/admin/'):
        tabs.append(dict(name="mycart", text="Select item(s) for cancellation"))
    elif request.path.startswith('/orders/cancel'):
        tabs.append(dict(name="mycart", text="Select item(s) to cancel"))
    else:
        tabs.append(dict(name='mycart', text='Review your Cart'))
    # show signin for unauthenticated web users
    if (not request.user.is_authenticated() and not utils.is_cc(request) ) or utils.is_franchise(request):
        tabs.append(dict(name='signin', text='Email or Mobile Number'))
    if request.path.startswith('/orders/signup') and tab == 'signup':
        tab = 'signin'
    # always show shipping
    if request.path.startswith('/orders/admin/') or utils.is_cc(request):
        tabs.append(dict(name='shipping', text='Review Shipping Details'))
    elif request.path.startswith('/cancel-order/admin/'):
        tabs.append(dict(name='cancellation_info',text='Fill Cancellation Info'))
    elif request.path.startswith('/orders/cancel'):
        tabs.append(dict(name='cancellation_info', text='Confirm selected items'))
    else:
        tabs.append(dict(name='shipping', text='Shipping Details'))
    # show book order screen for call center
    if utils.is_cc(request):
        tabs.append(dict(name='book', text='Book or Confirm Order'))
    elif request.path.startswith('/orders/admin/'):
        tabs.append(dict(name="payment_info", text="Fill Payment Details"))
    elif request.path.startswith('/cancel-order/admin/'):
        pass
    elif request.path.startswith('/orders/cancel'):
    #    tabs.append(dict(name="cancelled", text="Change Confirmed"))
        pass
    elif request.path.startswith('/orders/payment_mode'):
        tabs.append(dict(name="payment_mode", text="Secure Payment"))
    else:
        tabs.append(dict(name="payment_info", text="Secure Payment"))
    tab_click = True
    for t in tabs:
        if t['name'] == tab:
            tab_click = False
        t['tab_click'] = tab_click
    if utils.is_new_fb_version(request) and utils.get_future_ecom_prod() == request.client.client:
        for i in range(len(tabs)):
            if tabs[i]['name'] == 'mycart':
                del tabs[i]
                break
    return dict(request=request, tab=tab, tabs=tabs)
register.inclusion_tag('order/checkout_tabs.html')(checkout_tabs)

def product_summary_grid(product, request, counter, products):
    size = len(products)
    last_row = False
    if size < 5:
        last_row = True
    else:
        last_n = size % 5
        if size - counter < last_n:
            last_row = True
        if last_n == 0:
            if size - counter < 5:
                last_row = True
    return dict(product=product, request=request, counter=counter,last_row=last_row)
register.inclusion_tag('products/grid_item.html')(product_summary_grid)

@register.filter
def show_or_hide_cart(request):
    if request.path.startswith('/orders/refund_dashboard'):
        return False
    elif request.path.startswith('/a/'):
        return False
    else:
        return True

@register.filter
def order_state_conf_or_mod_or_canc(order_state):
    if order_state in ['confirmed','modified','cancelled']:
        return True
    else:
        return False

@register.filter
def order_state_conf_or_mod(order_state):
    if order_state in ['confirmed','modified']:
        return True
    else:
        return False

@register.filter
def order_state_canc_or_mod(order_state):
    if order_state in ['cancelled','modified']:
        return True
    else:
        return False

@register.filter
def request_path_start(request_path):
    if request_path.startswith('/orders/cancel'):
        return True
    else:
        return False

@register.filter
def item_state_canc_or_ref(item_state):
    if item_state in ['cancelled','refunded']:
        return True
    else:
        return False

def product_home_page_grid(product, request, counter, products):
    size = len(products)
    last_row = False
    if size - counter < 4:
        if counter > 5 and size > 5:
            last_row = True
    if size < 5:
        last_row = True
    return dict(product=product, request=request, counter=counter,last_row=last_row)
register.inclusion_tag('products/home_page_grid.html')(product_home_page_grid)

def product_summary_list(product, request, counter, products):
    size = len(products)
    last_row = False
    if size - counter < 4:
        if counter > 5 and size > 5:
            last_row = True
    if size < 5:
        last_row = True
    return dict(product=product, request=request, counter=counter,last_row=last_row)
register.inclusion_tag('products/list_item.html')(product_summary_list)

def add_to_cart(request, product, rate_chart, format=None, css=None, id=None):
    return dict(request=request, product=product,
            rate_chart=rate_chart, format=format,
            css=css, id=id)
register.inclusion_tag('products/add_to_cart.html')(add_to_cart)

def store_category_list(request):
    from web.templatetags.menu_tags import get_menu_items
    ctxt = get_menu_items(request)
    menuitems = ctxt['menuitems'][:5]
    ctxt['menuitems'] = menuitems
    return ctxt
register.inclusion_tag('web/store_category_list.html')(store_category_list)



#def render_order_snippet(order):
#    if order:
#        order_items = order.get_order_items(request, 
#                exclude=dict(state__in=['cancelled', 'bundle_item']))
#    else:
#        order_items = []
#    return dict(order=order, order_items=order_items, total_items = order.get_item_count(), 
#            delivery_info = order.get_address(None, type='delivery'))
#register.inclusion_tag('order/snippet.html')(render_order_snippet)

def render_page_title(filter_form):
    page_title = ''
    if filter_form.category:
        store = None
        if filter_form.category.store:
            store = filter_form.category.store.name
        category = filter_form.category.name
        if not store:
            return dict(page_title='Online Shopping India : Chaupaati Bazaar')
        if store == 'Books':
            page_title = "Online %s Store India, Buy Cheap %s Online" % (category,category)
        if store == 'Mobiles':
            page_title = "Online %s Shopping in India, Buy %s Online" % (category,category)
        if store == 'Magazines':
            page_title = "Online %s Magazines Subscription in India, Buy %s Magazines online. Subscribe Online" % (category, category)
        if store == 'Computers':
            page_title = "Online %s Shopping in India, Buy %s Online" % (category, category)
        if store == 'Gifts':
            page_title = "Online %s Shopping in India, Buy %s Online" % (category, category)
        if store == 'Toys':
            page_title = "Online %s Shopping in India, Buy %s Online" % (category, category)
        if store == 'Electronics':
            page_title = "Online %s Shopping in India, Buy %s Online" % (category, category)

    return dict(page_title=page_title)
register.inclusion_tag('categories/page_title.html')(render_page_title)

def render_page_desc(filter_form):
    page_desc = ''
    if filter_form.category:
        category = filter_form.category.name
        store = None
        if filter_form.category.store:
            store = filter_form.category.store.name
        if not store:
            return dict(page_desc="India's phone bazaar. Find best deals on books, magazines, computers, mobiles, home electronics, home appliances. Call 922 222 1947 to buy directly from brands.")
        if store == 'Books':
            page_desc = "chaupaati.in: Online %s Shopping in India. %s online shop. Buy latest %s at Lowest Price on India's Online Discount Store." % (category, category, category)
        if store == 'Mobiles':
            page_desc = "chaupaati.in: Online %s Store India. %s online shop. Buy latest %s at Lowest Price on India's Online Discount Store. Purchase Cheap %s, Compare Price, Features" % (category, category, category, category)
        if store == 'Magazines':
            page_desc = "chaupaati.in: Online %s Magazines Store India. Subscribe %s Magazine Online. Buy %s Magazines. We sale Magazines on Automobiles, Business, Technology, Lifestyle, Fashion, Travel, Education at best price." % (category, category, category)
        if store == 'Computers':
            page_desc = "chaupaati.in: Online %s Store in India. %s online shop. Buy latest %s at Lowest Price on India's Online Discount Store. Purchase Cheap %s, Compare Price, Features" % (category, category, category, category)
        if store == 'Gifts':
            page_desc = "chaupaati.in: Online %s Store India. %s online shop. Buy attractive %s at Lowest Price on India's Online Discount Store" % (category, category, category)
        if store == 'Toys':
            page_desc = "chaupaati.in: Online %s Store India. %s online shop. Buy %s at Lowest Price on India's Online Discount Store. Purchase Cheap %s, Compare Price, Features" % (category, category, category, category)
        if store == 'Electronics':
            page_desc = "chaupaati.in: Online %s Store India. %s online shop. Buy latest %s at Lowest Price on India's Online Discount Store. Purchase Cheap %s, Compare Price, Features" % (category, category, category, category)

    return dict(page_desc=page_desc)
register.inclusion_tag('categories/page_desc.html')(render_page_desc)

def render_page_tags(filter_form):
    page_tags = ''
    if filter_form.category:
        category = filter_form.category.name
        store = None
        if filter_form.category.store:
            store = filter_form.category.store.name
        if not store:
            return dict(page_tags="Chaupaati Bazaar, Online Shopping, Store Online, Buy Books, Subscribe Magazines, Buy Computer, Mobiles, Electronics, Toys, Gifts, Low Price, Purchase On Web, Cheap product, india")
        if store == 'Books':
            page_tags = "chaupaati.in: Online %s Store India, %s online shop, Buy latest %s at Lowest Price on India's Online Discount Store." % (category, category, category)
        if store == 'Mobiles':
            page_tags = "chaupaati.in: Online %s Store India, %s online shop, Buy latest %s at Lowest Price on India's Online Discount Store. Purchase Cheap %s, Compare Price, Features" % (category, category, category, category)
        if store == 'Magazines':
            page_tags = "chaupaati.in: Online %s Magazines Store India, Subscribe %s Magazine online, Buy %s Magazines, We sale Magazines on Automobiles, Business, Technology, Lifestyle, Fashion, Travel, Education at best price." % (category, category, category)
        if store == 'Computers':
            page_tags = "chaupaati.in: Online %s Store India, %s online shop, Buy latest %s at Lowest Price on India's Online Discount Store. Purchase Cheap %s, Compare Price, Features" % (category, category, category, category)
        if store == 'Gifts':
            page_tags = "chaupaati.in: Online %s Store India, %s online shop, Buy latest %s at Lowest Price on India's Online Discount Store. Purchase Cheap %s, Compare Price" % (category, category, category, category)
        if store == 'Toys':
            page_tags = "chaupaati.in: Online %s Store India, %s online shop, Buy latest %s at Lowest Price on India's Online Discount Store. Purchase Cheap %s, Compare Price, Features" % (category, category, category, category)
        if store == 'Electronics':
            page_tags = "chaupaati.in: Online %s Store India, %s online shop, Buy latest %s at Lowest Price on India's Online Discount Store. Purchase Cheap %s, Compare Price, Features" % (category, category, category, category)

    return dict(page_tags=page_tags)
register.inclusion_tag('categories/page_tags.html')(render_page_tags)

def render_store_page_title(store):
    page_title = ''
    if store.name == 'Books':
        page_title = "Online Book Store India, Buy Books Online in India"
    if store.name == 'Magazines':
        page_title = "Online Magazine Subscription in India, Buy Magazines Online, Store Online"
    if store.name == 'Computers':
        page_title = "Online Computers Shopping in India, Buy Computers, Laptops PC Online"
    if store.name == 'Mobiles':
        page_title = "Online Mobiles Shopping in India, Buy Mobile Phones online at Best Prices"
    if store.name == 'Electronics':
        page_title = "Online Electronics Shopping in India, Buy Electronics Online at Lowest Prices"
    if store.name == 'Toys':
        page_title = "Online Toys Shopping in India, Buy Toys Online in India, Toy Store"
    if store.name == 'Gifts':
        page_title = "Buy & Send Gift to India Online, Best Online Store to Buy Gifts in India"
    return dict(page_title=page_title)
register.inclusion_tag('categories/page_title.html')(render_store_page_title)

def render_store_page_desc(store):
    page_desc = ''
    if store.name == 'Books':
        page_desc = "chaupaati.in: Online Book Store India, Buy Books on online store from any where in India. Find Best Selling Books, Latest Books, Popular Books of all categories. Discount Book Seller India of all Publications."
    if store.name == 'Magazines':
        page_desc = "chaupaati.in: Online Magazines Store India, Subscribe Magazines Online. Buy Magazines, We sale Magazines on Automobiles, Business, Technology, Lifestyles, Fashion, Travel, Education, at best price."
    if store.name == 'Computers':
        page_desc = "chaupaati.in: Online Computers Store India, Computer online shop. Buy latest Computer, Laptops, Desktop PC, Software, Hardware at Lowest Price on India's Online Discount Store. Find Laptop PC online of all Brands."
    if store.name == 'Mobiles':
        page_desc = "chaupaati.in: Online Mobile Store India, Buy Mobiles on online store. Find Best Selling Mobiles, Latest Mobiles Models, Discount Mobile Seller India of all Brands. Online Mobile Shop. Compare Mobiles."
    if store.name == 'Electronics':
        page_desc = "chaupaati.in: Online Electronics Store India, Buy Electronics products online. Find  AC, Home Theaters, Printers, Fridge, DVD Player & more, Compare price and shop online. Find Best deal, Cheap Products."
    if store.name == 'Toys':
        page_desc = "chaupaati.in: Online Toy Store India, Buy Toys online. Buy Toys for Kids. Search for Games, Gaming Consoles, Gaming Accessories, Toys & Games from our Online Shopping Mall. Best Price Toys."
    if store.name == 'Gifts':
        page_desc = "chaupaati.in: Shop Online. Online Gifts Store India, Buy Gifts, Health care, Personal, Sweets, T-Shirts, Watches,  at lowest Price, Best deal. Cheap Products. Gift Store Online, Clothing Store Online."
    return dict(page_desc=page_desc)
register.inclusion_tag('categories/page_desc.html')(render_store_page_desc)

def render_store_page_tags(store):
    page_tags = ''
    if store.name == 'Books':
        page_tags = "Book Store, Buy Books, Science Books, Novels, Travels & Living Books, Comics Books, Fiction Books, Non Fiction, Autobiography, Best Selling, Popular, online Book Store, Cheap"
    if store.name == 'Magazines':
        page_tags = "Online Magazines, Buy Magazine, Magazines on Automobiles, Business, Technology, Lifestyles, Fashion, Travel, Education, Subscribe Magazine, Magazines Deal, Best Price, Offer Price"
    if store.name == 'Computers':
        page_tags = "Online Computer Store, Buy Computer, Software, Hardware, RAM, Web cam, Speakers, Routers, Modems, Printers, PC, Branded PC, OS"
    if store.name == 'Mobiles':
        page_tags = "Buy Mobiles, Samsung Mobiles, Nokia Mobiles, Micromax, Max, Vodafone, Blackbery, Reliance, Tata, Virgin, Latest Models, Latest Offers, Features, Compare Price, Discount. Save"
    if store.name == 'Electronics':
        page_tags = "Online Electronics, Low Price, Discount Price, Buy,  AC, Home Theaters, Printers, Fridge, DVD Player, Washing Machine, Set Top Box, TV, Food Processor, Water Purifiers"
    if store.name == 'Toys':
        page_tags = "Buy Toys, Cheap toys, Games, Gaming Consoles, Gaming Accessories, Toys & Games, Disney Fairies, Scrabble, Sony, Best Deal, Offer Price, Discount, Send Gift"
    if store.name == 'Gifts':
        page_tags = "Online Gifts Store,  Buy Gifts, Health care, Personal, Sweets, T-Shirts, Watches, lowest Price, Best deal. Cheap Products. Online Mall, Shopping on website"
    return dict(page_tags=page_tags)
register.inclusion_tag('categories/page_tags.html')(render_store_page_tags)

def render_product_page_title(product, request=None):
    page_title = ''
    category = product.category.name
    brand = product.brand.name
    try:
        store = product.category.store.name
    except:
        store = ''
    currency = "Rs. "# if product.currency == 'inr' else "$"
    if store == 'Mobiles':
        page_title = "%s %s: Buy %s at Lowest Price %s%s in India | Chaupaati.in" % (brand, category, product.title, currency, utils.formatMoney(product.primary_rate_chart().offer_price))
    if store == 'Books':
        page_title = "Books: Buy %s By %s Online | Chaupaati.in" % (product.title, product.primary_rate_chart().seller.name)
    if store == 'Magazines':
        page_title = "Magazines: Buy %s online. Subscribe Magazine on %s | Chaupaati.in" % (product.title, category)
    if store == 'Computers':
        page_title = "%s %s: Buy %s at Lowest Price %s%s in India | Chaupaati.in" % (brand, category, product.title, currency, utils.formatMoney(product.primary_rate_chart().offer_price))
    if store == 'Electronics':
        page_title = "%s %s: Buy %s at Lowest Price %s%s in India | Chaupaati.in" % (brand, category, product.title, currency, utils.formatMoney(product.primary_rate_chart().offer_price))
    if store == 'Toys':
        page_title = "%s %s: Buy %s at Lowest Price %s%s in India | Chaupaati.in" % (brand, category, product.title, currency, utils.formatMoney(product.primary_rate_chart().offer_price))
    if store == 'Gifts':
        page_title = "%s %s: Buy %s at Lowest Price %s%s in India | Chaupaati.in" % (brand, category, product.title, currency, utils.formatMoney(product.primary_rate_chart().offer_price))

    if request:
        if utils.is_future_ecom(request.client.client):
            page_title = "%s %s: Buy %s at Lowest Price %s%s in India | FutureBazaar.com" % (brand, category, product.title, currency, utils.formatMoney(product.primary_rate_chart().offer_price))

    return dict(page_title=page_title)
register.inclusion_tag('categories/page_title.html')(render_product_page_title)

def render_product_page_desc(product, request=None):
    page_desc = ''
    category = product.category.name
    brand = product.brand.name
    try:
        store = product.category.store.name
    except:
        store = ''
    currency = "Rs. "# if product.currency == 'inr' else "$"
    discount = product.primary_rate_chart().getDiscount()
    discount_text = " & get %s%% discount" % (discount)# if discount > 0 else ""
    savings = product.primary_rate_chart().getSavings()
    savings_text = " Save %s%s." % (currency, utils.formatMoney(savings))# if discount > 0 else ""
    if store == 'Mobiles':
        page_desc = "Online %s shopping in India, Buy %s cell phones%s. Best deal in India. Our offer price %s%s.%s Compare prices, features. Purchase cheapest %s on website." % (category, product.title,discount_text, currency, utils.formatMoney(product.primary_rate_chart().offer_price), savings_text, category)
    if store == 'Books':
        page_desc = "Online Book Store: %s by %s. Category: %s Publication: %s. MRP %s%s Our Price %s%s %s %s" % (product.title, product.primary_rate_chart().seller.name, category, product.primary_rate_chart().seller.name,currency, utils.formatMoney(product.primary_rate_chart().list_price), currency, utils.formatMoney(product.primary_rate_chart().offer_price), discount_text, savings_text)
    if store == 'Magazines':
        page_desc = "Online Magazine Store: %s online. Magazine on %s. MRP %s%s Our Price %s%s %s %s. Subscribe %s Magazine on our online Shopping Store and get maximum discount." % (product.title, category, currency, utils.formatMoney(product.primary_rate_chart().list_price), currency, utils.formatMoney(product.primary_rate_chart().offer_price), discount_text, savings_text, product.title)
    if store == 'Computers':
        page_desc = "Online %s shopping in India. Buy %s%s. Best deal in India. Our Offer Price %s%s.%s Compare prices, features, purchase cheapest %s on website" % (category, product.title,discount_text, currency, utils.formatMoney(product.primary_rate_chart().offer_price),savings_text,category)
    if store == 'Electronics':
        page_desc = "Online %s shopping in India. Buy %s%s. Best deal in India. Our Offer Price %s%s.%s Compare prices, features, purchase cheapest %s on website" % (category, product.title,discount_text, currency, utils.formatMoney(product.primary_rate_chart().offer_price),savings_text,category)
    if store == 'Toys':
        page_desc = "Online %s shopping in India. Buy %s%s. Best deal in India. Our Offer Price %s%s.%s Compare prices, features, purchase cheapest %s on website" % (category, product.title,discount_text, currency, utils.formatMoney(product.primary_rate_chart().offer_price),savings_text,category)
    if store == 'Gifts':
        page_desc = "Online %s shopping in India. Buy %s%s. Best deal in India. Our Offer Price %s%s.%s Compare prices, features, purchase cheapest %s on website" % (category, product.title,discount_text, currency, utils.formatMoney(product.primary_rate_chart().offer_price),savings_text,category)

    if request:
        if utils.is_future_ecom(request.client.client):
            page_desc = "Online %s shopping in India. Buy %s%s. Best deal in India. Our Offer Price %s%s.%s Compare prices, features, purchase cheapest %s on website" % (category, product.title,discount_text, currency, utils.formatMoney(product.primary_rate_chart().offer_price),savings_text,category)

    return dict(page_desc=page_desc)
register.inclusion_tag('categories/page_desc.html')(render_product_page_desc)


def render_product_page_tags(product, request=None):
    page_tags = ''
    category = product.category.name
    brand = product.brand.name
    try:
        store = product.category.store.name
    except:
        store = ''
    currency = "Rs. "# if product.currency == 'inr' else "$"
    discount = product.primary_rate_chart().getDiscount()
    discount_text = " & get %s%% discount" % (discount)# if discount > 0 else ""
    savings = product.primary_rate_chart().getSavings()
    savings_text = " Save %s%s." % (currency, utils.formatMoney(savings))# if discount > 0 else ""
    if store == 'Mobiles':
        page_tags = "Online %s shopping in India, Buy %s cell phones%s. Best deal in India. Our offer price %s%s.%s Compare prices, features. Purchase cheapest %s on website." % (category, product.title,discount_text, currency, utils.formatMoney(product.primary_rate_chart().offer_price), savings_text, category)
    if store == 'Books':
        page_tags = "Online Book Store: %s by %s. Category: %s Publication: %s. MRP %s%s Our Price %s%s %s %s" % (product.title, product.primary_rate_chart().seller.name, category, product.primary_rate_chart().seller.name,currency, utils.formatMoney(product.primary_rate_chart().list_price), currency, utils.formatMoney(product.primary_rate_chart().offer_price), discount_text, savings_text)
    if store == 'Magazines':
        page_tags = "Online Magazine Store: %s online. Magazine on %s. MRP %s%s Our Price %s%s %s %s. Subscribe %s Magazine on our online Shopping Store and get maximum discount." % (product.title, category, currency, utils.formatMoney(product.primary_rate_chart().list_price), currency, utils.formatMoney(product.primary_rate_chart().offer_price), discount_text, savings_text, product.title)
    if store == 'Computers':
        page_tags = "Online %s shopping in India. Buy %s%s. Best deal in India. Our Offer Price %s%s.%s Compare prices, features, purchase cheapest %s on website" % (category, product.title,discount_text, currency, utils.formatMoney(product.primary_rate_chart().offer_price),savings_text,category)
    if store == 'Electronics':
        page_tags = "Online %s shopping in India. Buy %s%s. Best deal in India. Our Offer Price %s%s.%s Compare prices, features, purchase cheapest %s on website" % (category, product.title,discount_text, currency, utils.formatMoney(product.primary_rate_chart().offer_price),savings_text,category)
    if store == 'Toys':
        page_tags = "Online %s shopping in India. Buy %s%s. Best deal in India. Our Offer Price %s%s.%s Compare prices, features, purchase cheapest %s on website" % (category, product.title,discount_text, currency, utils.formatMoney(product.primary_rate_chart().offer_price),savings_text,category)
    if store == 'Gifts':
        page_tags = "Online %s shopping in India. Buy %s%s. Best deal in India. Our Offer Price %s%s.%s Compare prices, features, purchase cheapest %s on website" % (category, product.title,discount_text, currency, utils.formatMoney(product.primary_rate_chart().offer_price),savings_text,category)

    if request:
        if utils.is_future_ecom(request.client.client):
            page_tags = "Online %s shopping in India. Buy %s%s. Best deal in India. Our Offer Price %s%s.%s Compare prices, features, purchase cheapest %s on website" % (category, product.title,discount_text, currency, utils.formatMoney(product.primary_rate_chart().offer_price),savings_text,category)

    return dict(page_tags=page_tags)
register.inclusion_tag('categories/page_tags.html')(render_product_page_tags)

def load_product (productitem, request):
    products=productitem
    return dict(products=products,request=request)
register.inclusion_tag('stores/popular_products.html')(load_product)

@register.filter
def time_ago(value):
    tdiff = (int(time.time()) - value)
    ret_str = ''
    if tdiff < 60:
        ret_str = '%s Seconds ago' % int(tdiff)
    elif tdiff < 3600:
        ret_str = '%s Minutes ago' % int(tdiff/60)
    elif tdiff < 86400:
        ret_str = '%s Hours ago' % int(tdiff/3600)
    else:
        ret_str = '%s Days ago' % int(tdiff/86400)

    return ret_str

def time_left(end_time):
    from datetime import datetime
    tdiff = end_time - datetime.now()
    hours,reminder = divmod(tdiff.seconds,3600)
    minutes,seconds = divmod(reminder,60)
    return dict(hours=hours,minutes=minutes,seconds=seconds)
register.inclusion_tag('web/deal_time_left.html')(time_left)

def load_ppd_product (productitem, request):
    products=productitem
    return dict(products=products,request=request)
register.inclusion_tag('ppd/display_products.html')(load_ppd_product)

def render_home_buzz(request):
    act_objs = Activity.objects.filter(aclientdomain=request.client).order_by('-atime')[:5]
    return { 'act_objs' : act_objs ,'request':request}
register.inclusion_tag('activitystream/homestream.html')(render_home_buzz)

def render_dailydeal_buzz(request):
    steal_of_the_day = DailyDeal.objects.filter(type='hero_deal', client=request.client.client, 
        status='published', starts_on__lte=datetime.now(),ends_on__gte=datetime.now())
    if steal_of_the_day:
        steal_of_the_day = steal_of_the_day[0]
        act_objs = Activity.objects.filter(aclientdomain=request.client, asrc=steal_of_the_day.rate_chart).order_by('-atime')[:5]
    else:
        act_objs = Activity.objects.filter(aclientdomain=request.client).order_by('-atime')[:5]
    return { 'act_objs' : act_objs ,'request':request}
register.inclusion_tag('activitystream/homestream.html')(render_dailydeal_buzz)

def render_recently_stolen(request):
    from web.views.home import get_recently_stolen_products
    unique_activities = get_recently_stolen_products(request)
    return { 'act_objs' : unique_activities ,'request':request}
register.inclusion_tag('web/home/recently_stolen.html')(render_recently_stolen)

def show_recently_stolen_products(activity_objs, request):
    return { 'act_objs' : activity_objs, 'request':request}
register.inclusion_tag('web/home/recently_stolen_products.html')(show_recently_stolen_products)


def get_announcements(request):
    announcements = Announcements.objects.filter(domain=request.client,starts_on__lte=datetime.now()).order_by('sort_order')
    return {'announcements':announcements}
register.inclusion_tag('web/announcements.html')(get_announcements)

@register.simple_tag
def scene7_image(current_url,height=150,width=150):
    p1 = re.compile('wid=\d+')
    p2 = re.compile('hei=\d+')
    url = p1.sub('wid=%s' % width,current_url)
    url = p2.sub('hei=%s' % height,url)
    return url
    pass

# get_astream # {{{
@register.filter
def get_astream(asobj):
    aslimit = 28
    user_str = 'Anonymous'
    if asobj.user:
        if asobj.user.full_name:
            user_str = asobj.user.full_name
        elif asobj.user.user.first_name:
            user_str = asobj.user.user.first_name
    else:
        user_str = 'Private user'
    if not user_str or user_str == " ":
        user_str = 'Anonymous'

    asrc_str = "miss"
    if asobj.asrc:
        asrc_str = '<a href="/%s">%s</a>' % (asobj.asrc.product.url(), asobj.asrc.product.title)

    astream = ''
    if asobj.atype == 'Buy':
        astream = '%s bought ' % user_str
    elif asobj.atype == 'Like':
        astream = '%s likes ' % user_str
    elif asobj.atype == 'Review':
        astream = '%s wrote a review of ' % user_str
    elif asobj.atype == 'Rating':
        astream = '%s has rated ' % user_str
    else:
        astream = '%s wrote a feedback' % user_str

    if 'wrote a feedback' in astream:
        return astream

    astemp = "%s%s" % (astream, asobj.asrc.product.title)
    if len(astemp) <= aslimit:
        astream = "%s%s" % (astream, asrc_str)
        return astream

    astemp_list = astemp.split(' ')
    first_line, wp, second_line = '', 0, ''
    for i in astemp_list:
        if not first_line:
            first_line = i
            continue
        if len("%s %s" % (first_line, i)) <= aslimit:
            first_line = "%s %s" % (first_line, i)
        else:
            wp = astemp_list.index(i)
            break
    for i in astemp_list[wp:]:
        if len("%s %s" % (second_line, i)) <= aslimit:
            second_line = "%s %s" % (second_line, i)
        else:
            second_line = "%s%s" % (second_line, "..")
            break
    astemp = "%s%s" % (first_line, second_line)
    prod_title_str = astemp.partition(astream)[2]
    prod_url_str = '<a href="/%s">%s</a>' % (asobj.asrc.product.url(), prod_title_str)
    astream = "%s%s" % (astream, prod_url_str)
    return astream
get_astream.is_safe = True

def product_tags(product,request):
    show_tag = False
    tags = product.producttags_set.filter(starts_on__lte=datetime.now(), ends_on__gte=datetime.now())
    mid_day_logo = False
    for tag in tags:
        if tag.tag.tag in ('free_shipping','steal','battle','top_10'):
            show_tag = True
    try:
        mid_day = MidDayDeal.objects.filter(status="published",starts_on__lte=datetime.now(),ends_on__gte=datetime.now()).order_by('-id')
        if mid_day:
            mid_day = mid_day[0]
            mid_day_products = mid_day.middayproducts_set.all().values('sku__product')
            for prod in mid_day_products:
                if product.id == prod['sku__product']:
                    show_tag = True
                    mid_day_logo = True
    except:
        pass
    return dict(tags=tags,show_tag=show_tag,request=request, mid_day_logo=mid_day_logo)
register.inclusion_tag('products/product_tags.html')(product_tags)

@register.filter
def is_user_subscribed(request):
    if request.user.is_authenticated():
        try:
            user_info = utils.get_user_info(request)
            user = user_info['user']
            profile = user_info['profile']
            newsletter = NewsLetter.objects.get(newsletter='DailyDeals',client=request.client.client)
            return DailySubscription.objects.filter(
                    Q(is_sms_alert=True) | Q(is_email_alert=True),
                    newsletter=newsletter,
                    sms_alert_on__user=profile).exists()
        except Exception,e:
	    log.info('subscription error %s' % repr(e))
            return False
    else:
        return False

@register.simple_tag
def media_url(request, path):
    media_url = settings.MEDIA_URL
    is_https = 'HTTPS' in request.META['SERVER_PROTOCOL']
    # Disable https for media if set in settings
    if not getattr(settings, 'ALLOW_HTTPS_FOR_MEIDA', True):
        is_https = False
    if is_https:
        media_url = media_url.replace('http://','https://')

    if 'http' not in path:
        # Hack to ensure double media does not get out.
        media_url = '%s%s' % (media_url, path)
    else:
        # if path contains http://.. , then dont append media before path
        media_url = path
    media_url = media_url.replace("media//media", "media")

    # Ensure https for order pages
    if request.path.startswith('/orders/payment'):
        media_url = media_url.replace('http://', 'https://')
        media_url = media_url.replace('fbcdn.mediafb.com',
            'www.futurebazaar.com')
    return media_url

@register.simple_tag
def get_proto(request):
    is_https = 'HTTPS' in request.META['SERVER_PROTOCOL']
    is_https = True
    # Disable https for media if set in settings
    if not getattr(settings, 'ALLOW_HTTPS_FOR_MEIDA', True):
        is_https = False
    if request.path.startswith('/orders/'):
        is_https = True
    if is_https:
        return 'https'
    return 'http'

def top_categories(request, top_items):
    return dict(request=request,top_items=top_items)
register.inclusion_tag('web/home/top_categories.html')(top_categories)

def most_viewed_items(request, items):
    return dict(request=request,most_viewed=items)
register.inclusion_tag('web/home/most_viewed.html')(most_viewed_items)

def show_offer_items(request):
    from web.views.home import get_offer_items
    offer_items = get_offer_items(request)
    return dict(request=request,offer_items=offer_items)
register.inclusion_tag('web/home/offer_products.html')(show_offer_items)

def get_new_arrivals(request, items):
    return dict(request = request, new_items = items)
register.inclusion_tag('web/home/new_arrivals.html')(get_new_arrivals)

def download_catalogue(request, categories):
    return dict(request = request, categories = categories, media_url = settings.MEDIA_URL)
register.inclusion_tag('web/home/download_catalogue.html')(download_catalogue)

def customer_testimonials(request, testimonials):
    return dict(request = request, testimonials = testimonials)
register.inclusion_tag('web/home/top_testimonials.html')(customer_testimonials)

def show_brands(request, items):
    return dict(request=request,brands=items)
register.inclusion_tag('web/home/show_brands.html')(show_brands)

def brands_section(request, brands):
    return dict(request=request,brands=brands)
register.inclusion_tag('web/home/brands.html')(brands_section)

def get_categories(request):
    _client = request.client.client
    items1, items2 = [], []
    category_level_1 = MegaDropDown.objects.filter(type = "category", category__client = _client).order_by('sort_order')
    for r1 in category_level_1:
        category_level_2 = CategoryGraph.objects.filter(parent = r1.category).order_by('sort_order')
        items1.append({'parent': r1, 'children': category_level_2})
        for r2 in category_level_2:
            category_level_3 = CategoryGraph.objects.filter(parent = r2.category).order_by('sort_order')
            if category_level_3:
                items2.append(str(r1.category.name))
    return {'categories': items1, 'sub_categories': items2}


def render_navigation_bar(request):
    menu_key = 'navigationmenu#%s' % (request.client.client.id)
    menu_context = cache.get(menu_key)
    if not menu_context:
        menu_context = get_categories(request)
        cache.set(menu_key, menu_context, 3600)
    return menu_context 
register.inclusion_tag('web/home/navigation_bar.html')(render_navigation_bar)

def render_announcements(request):
    _client = request.client.client
    anno = Announcements.objects.filter(domain__client = _client,starts_on__lte=datetime.now()).order_by('sort_order')[:1]
    print anno, request.client
    return dict(request=request, announcements = anno)
register.inclusion_tag('web/home/announcements.html')(render_announcements)

def get_testimonial(request):
    testimonial_key = 'testimonial#%s' % (request.client.client.id)
    testimonials = cache.get(testimonial_key)
    if not testimonials:
        testimonials = Feedback.objects.select_related('name', 'feedback', 'city').filter(type='testimonial',client=request.client.client, publish_it=True)
        '''
        Caching testimonials for 6 Hours
        '''
        cache.set(testimonial_key, testimonials, 21600)
    return dict(testimonials=testimonials,request=request)
register.inclusion_tag('web/home/testimonial.html')(get_testimonial)

def get_deals_and_promotions(request):
    deals = {}
    _client = request.client.client
    steal_of_the_day = DailyDeal.objects.filter(type='hero_deal', status='published', starts_on__lte=datetime.now(),ends_on__gte=datetime.now(),
            client=_client)
    battle = List.objects.filter(type="battle",starts_on__lte=datetime.now(),ends_on__gte=datetime.now())
    top10 = List.objects.filter(type="top_10",is_featured=True).order_by('-id')
    if top10:
        top10 = top10[0]
        deals['top10'] = top10.url()
    if steal_of_the_day:
        deals['daily_deal'] = steal_of_the_day[0].get_url()
    if battle:
        deals['battle'] = battle[0].get_url()
    return dict(deals=deals)
register.inclusion_tag('web/home/get_footer_deals.html')(get_deals_and_promotions)

@register.simple_tag
def applied_coupon_code_message(request):
    if 'applied_coupon_msg' in request.session:
        msg = request.session['applied_coupon_msg']
        del request.session['applied_coupon_msg']
        return msg
    return None

@register.simple_tag
def applied_payback_message(request):
    if 'payback_msg' in request.session:
        msg = request.session['payback_msg']
        del request.session['payback_msg']
        return msg
    return None

@register.simple_tag
def flush_element_from_session(request, var_name):
    if var_name in request.session:
        del request.session[var_name]
    return None

@register.filter
def get_help_summation(review):
    return review.no_helpful+review.no_not_helpful

def read_product_reviews(product_reviews):
    page_no = 1
    items_per_page = 5
    total_results = len(product_reviews)
    total_pages = int(math.ceil(Decimal(len(product_reviews))/Decimal(items_per_page)))
    pagination = utils.getPaginationContext(page_no, total_pages, '')
    pagination['result_from'] = (page_no-1) * items_per_page + 1
    pagination['result_to'] = utils.ternary(page_no*items_per_page > total_results, total_results, page_no*items_per_page)
    product_reviews = product_reviews[:5]
    pagination['show_pagination'] = True
    if total_results <= 5 :
        pagination['show_pagination'] = False
    if product_reviews:
        product_id = product_reviews[0].product.id
    return dict(product_reviews=product_reviews,pagination=pagination,product_id=product_id)
register.inclusion_tag('products/read_review.html')(read_product_reviews)

def approve_product_reviews(request, product_reviews):
    url = request.get_full_path()
    if "status=new" in url:
        page_no = 1
        items_per_page = 25
        total_results = len(product_reviews)
        total_pages = int(math.ceil(Decimal(len(product_reviews))/Decimal(items_per_page)))
        pagination = utils.getPaginationContext(page_no, total_pages, '')
        pagination['result_from'] = (page_no-1) * items_per_page + 1
        pagination['result_to'] = utils.ternary(page_no*items_per_page > total_results, total_results, page_no*items_per_page)
        product_reviews = product_reviews[:25]
        pagination['show_pagination'] = True
        if total_results <= 25 :
            pagination['show_pagination'] = False
        return dict(product_reviews=product_reviews,pagination=pagination,url=url, request=request)
    else:
        paginator = Paginator(product_reviews, 20) # Show 20 order_page_list per page
# Make sure page request is an int. If not, deliver first page.
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
        pagination = utils.getPaginationContext(page, paginator.num_pages, base_url)
# I page request (9999) is out of range, deliver last page of results.
        try:
            product_reviews = paginator.page(page)
        except (EmptyPage, InvalidPage):
            product_reviews = paginator.page(paginator.num_pages)
        return dict(url=url,product_reviews=product_reviews,pagination=pagination, request = request)
register.inclusion_tag('reviews/approve_reviews.html')(approve_product_reviews)

def get_price_versions(rate_chart_id):
    price_versions = PriceVersion.objects.filter(rate_chart__id=rate_chart_id, status='pending').order_by('created_on')
    return dict(price_versions=price_versions)
register.inclusion_tag('prices/price_version_details.html')(get_price_versions)

def show_pricing_info(prices):
    return dict(prices=prices)
register.inclusion_tag('prices/pricing_info.html')(show_pricing_info)

@register.simple_tag
def show_price_info(rate_chart_id, price_list):
    from pricing.models import PriceVersion
    price_versions = PriceVersion.objects.filter(
        rate_chart__id = rate_chart_id,
        price_list__name = price_list,
        status = 'approved').order_by('-approved_on')
    log.info('price_versions=%s' % price_versions)
    return dict(prices=price_versions)
register.inclusion_tag('prices/pricing_info.html')(show_price_info)

def fill_address_details(form):
    return dict(form=form)
register.inclusion_tag('user/address_details.html')(fill_address_details)

def get_banner_content(request, deal, page):
    deal_rate_chart = None
    deal_product = None
    if deal:
        deal_rate_chart = deal.dailydealproduct_set.all()[0].product.primary_rate_chart()
        deal_product = deal.dailydealproduct_set.all()[0].product
    return dict(request=request, deal=deal, page=page,deal_images=deal.dailydealimage_set.all(), deal_rate_chart=deal_rate_chart,deal_product=deal_product)
register.inclusion_tag('stealoftheday/banner_content.html')(get_banner_content)

@register.simple_tag
def get_price_info(request, rate_chart, info, **kwargs):
    priceInfo = rate_chart.getPriceInfo(request)
    if kwargs.get('dont_format', False):
        return priceInfo[info]
    if info == '3months_emi':
        return utils.formatMoney(int(priceInfo['offer_price']/3))
    elif info in ('offer_price', 'list_price', 'payback_points', 'cashback_amount'):
        return utils.formatMoney(priceInfo[info])
    else:
        return priceInfo[info]

@register.filter
def get_offer_price(request, rate_chart):
    offer_price = get_price_info(request, rate_chart, 'offer_price', dont_format=True)
    return offer_price

@register.filter
def is_3months_emi(request, rate_chart):
    priceInfo = rate_chart.getPriceInfo(request)
    return (priceInfo['offer_price'] > 1500)

@register.simple_tag
def getSavings(request, rate_chart):
    priceInfo = rate_chart.getPriceInfo(request)
    return utils.formatMoney(priceInfo['list_price'] - priceInfo['offer_price'])

@register.simple_tag
def getDiscount(request, rate_chart):
    priceInfo = rate_chart.getPriceInfo(request)
    return int(round((Decimal(priceInfo['list_price']-priceInfo['offer_price'])/Decimal(priceInfo['list_price']))*100))

@register.filter
def getDiscountPercent(request, rate_chart):
    priceInfo = rate_chart.getPriceInfo(request)
    return int(round((Decimal(priceInfo['list_price']-priceInfo['offer_price'])/Decimal(priceInfo['list_price']))*100))


@register.filter
def isAnySaving(request, rate_chart):
    priceInfo = rate_chart.getPriceInfo(request)
    return (Decimal(priceInfo['list_price'])) > (Decimal(priceInfo['offer_price']))

@register.filter
def isAnyEMI(request, rate_chart):
    priceInfo = rate_chart.getPriceInfo(request)
    offer_price = priceInfo['offer_price']
    if utils.is_ezoneonline(request.client.client):
        if offer_price < 3000:
            return False
        else:
            return True
    else:
        return True

@register.filter
def isAnythingInTheBox(rate_chart):
    product_feature = None
    try:
        product_feature = ProductFeatures.objects.get(feature__product_type=rate_chart.product.product_type,feature__name='Contents', product=rate_chart.product)
        if product_feature.data:
            return True
    except ProductFeatures.DoesNotExist:
        return False
    return False

@register.simple_tag
def inTheBox(rate_chart):
    product_feature = None
    try:
	    product_feature = ProductFeatures.objects.get(feature__product_type=rate_chart.product.product_type,feature__name='Contents', product=rate_chart.product)
    except ProductFeatures.DoesNotExist:
        pass

    if product_feature:
        return product_feature.data
    else:
        return ''

@register.filter
def isAnyCashback(request, rate_chart):
    priceInfo = rate_chart.getPriceInfo(request)
    if priceInfo['cashback_amount']:
        return (Decimal(priceInfo['cashback_amount'])) > Decimal('0.00')
    else:
        return False

@register.simple_tag
def get_amount_with_cashback(request, rate_chart):
    if rate_chart.cashback_amount:
	    return utils.formatMoney(Decimal(rate_chart.sale_price - rate_chart.cashback_amount))
    else:
        return utils.formatMoney(Decimal(rate_chart.sale_price))


@register.filter
def isFreeOrderApplicable(request):
    # TODO: usage of this tag is prime candidate for removal. It will cost
    # queries perpetually in vain.
    start_time = datetime(2011,8,12,0,0,0,0)
    end_time = datetime(2011,8,12,23,59,59,59)
    now = datetime.now()

    if (request.client == utils.get_future_ecom_prod_domain()) and (start_time < now) and (end_time > now):
        return True
    else:
        return False

@register.filter
def is_promotion(coupon):
    if coupon:
        if coupon.code.startswith('fbpromotion'):
            return True
    return False

def get_grid_products(request, products, show_compare, pagination, is_dod=False):
    return dict(request=request, products=products, show_compare=show_compare, pagination = pagination, daily_deal=is_dod)
register.inclusion_tag('categories/grid_products.html')(get_grid_products)

@register.filter
def display_apply_coupon(request):
    if request.path.endswith('confirmation'):
        return False
    cs = utils.get_session_obj(request)
    if 'fbapiobj' in cs:
        return True
    return False

@register.simple_tag
def get_email_content(email_type, order=None):
    if order:
        try:
            email = LEmail.objects.values_list('body', flat=True).filter(order=order,type=email_type)
            email = email[0]
            return email
        except:
            return ''
    return ''

def get_special_products(request, items):
    return dict(request=request, items=items)
register.inclusion_tag('fb/special_products.html')(get_special_products)

@register.filter
def serve_local(url, request):
    '''
    Serve local filter modifies given url to a relative url, so that the
    content is served from local server
    '''
    media_url = '/media/'
    serve_url = url
    if utils.is_new_fb_version(request):
        media_url = '/media/futurebazaar_v2/'
        serve_url = url.replace("/media/", media_url)
    if request.client.type == 'mobile_web':
        media_url = '/media/mobile/'
        serve_url = url.replace("/media/", media_url)
    if '://' in url and media_url in url:
        if 'fbcdn.mediafb' in serve_url:
            return serve_url.replace('http://fbcdn.mediafb.com','')
        return '/%s/%s' % (media_url, url.split(media_url)[1])
    return serve_url

@register.filter
def check_stock_availability(rate_chart):
    stock_count = rate_chart.get_maximum_purchasable_quantity(None)
    if not stock_count:
        stock_count = 0
    else:
        stock_count = int(stock_count)
    return stock_count

@register.simple_tag
def get_greeting_by_dni(request):
    try:
        if not request.call['dni']:
            return ''
        client = Account.objects.get(dni=request.call['dni'])
        return '<br /><p style="text-align:center;font-size:24px !important;color:#aaa !important;">%s</p><br />' % client.greeting_title
    except:
        return ''

@register.filter
def is_sizechart(brand):
    from django.template import TemplateDoesNotExist
    template_name = 'pages/sizechart/%s.html' % brand.slug
    try:
        template.loader.get_template(template_name)
        return True
    except TemplateDoesNotExist:
        return False

def show_friday_deal_products(request, active_products, deactive_products):
    return dict(request=request, active_products=active_products, deactive_products=deactive_products)
register.inclusion_tag('stealoftheday/friday_deal_products.html')(show_friday_deal_products)

@register.filter
def is_friday_deals(dummy):
    # TODO: This is a prime candidate for TEMPLATE_CONTEXT_PROCESSOR rather
    # than a tag
    return List.objects.filter(type="friday_deal",
            starts_on__lte=datetime.now, ends_on__gte=datetime.now).order_by('-id').exists()

@register.filter
def has_access_perm(request, perm):
    if request.user.has_perm(perm):
        return True
    return False

def multipleby(value, arg):
    return int(value*arg)

@register.simple_tag
def getmultiplication(value, arg):
    return int(value*arg)

def show_excel_link(request, excel):
    full_path=request.get_full_path()
    return dict(request=request, full_path=full_path, excel=excel)
register.inclusion_tag('show_excel_link.html')(show_excel_link)

def render_footer_categories(request):
    if utils.is_ezoneonline(request.client.client):
        categories = []
        cat = FeaturedCategories.objects.filter(category__client = request.client.client, type = 'footer').order_by('sort_order')
        for c in cat:
            if c.category.has_products():
                categories.append(c)
    else:
        categories = MegaDropDown.objects.filter(client=request.client.client).order_by('sort_order')
    return dict(request=request, categories=categories)
register.inclusion_tag('web/footer_categories.html')(render_footer_categories)

def get_from_cache(key):
    try:
        return cache.get(key)
    except:
        pass

def set_in_cache(key, obj, expires):
    try:
        cache.set(key, obj, expires)
    except:
        pass

@register.simple_tag
def category_url(request, id):
    try:
        category = get_from_cache('categories:%s' % id)
        if not category:
            category = Category.objects.get(id=id)
            set_in_cache('categories:%s' % id, category, 0)
        cc_url = utils.get_cc_url(request, category.url())
    except:
        cc_url = None
    return cc_url

def render_header_cart(request):
    from orders.views import get_cart
    try:
        cs = utils.get_session_obj(request)
        if 'cart_id' in cs: 
            cart = get_cart(request)
        else:
            cart = None
    except:
        cart = None
    return dict(request=request, cart=cart)
register.inclusion_tag('web/header_cart.html')(render_header_cart)

@register.filter
def is_int_equal(arg1, arg2):
    return (int(arg1) == int(arg2))

def get_remarketing_code(category):
    show_remarketing_code = False
    conversion_label = None
    if category.google_conversion_label:
        show_remarketing_code = True
        conversion_label = category.google_conversion_label
    return dict(conversion_label=conversion_label, show_remarketing_code=show_remarketing_code)
register.inclusion_tag('categories/google_conversion_script.html')(get_remarketing_code)

def render_header_dod(request):
    _client = request.client.client
    hero_deal_key = "hero_deal_ctxt#%s" % _client.id
    hero_deal_ctxt = cache.get(hero_deal_key)
    if not hero_deal_ctxt:
        _client = request.client.client
        deal = DailyDeal.objects.filter(type='hero_deal', status='published', starts_on__lte=datetime.now(),ends_on__gte=datetime.now(),
                client=_client).order_by('-id')
        deal_rate_chart = None
        if deal:
            deal = deal[0]
            deal_products = deal.dailydealproduct_set.all()
            if deal_products:
                deal_rate_chart = deal_products[0].product.primary_rate_chart()
        hero_deal_ctxt = dict(deal_rate_chart=deal_rate_chart, deal=deal)
        '''
            Hero deal ctxt caching for 1 hour
        '''
        cache.set(hero_deal_key, hero_deal_ctxt, 3600)
    hero_deal_ctxt['request'] = request
    return hero_deal_ctxt
register.inclusion_tag('web/header_dod.html')(render_header_dod)

@register.filter
def is_specifications_avail(product):
    feature_grp = FeatureGroup.objects.filter(product_type = product.product_type).order_by('sort_order')
    return feature_grp.exists()

def empty_cart_products(request):
    from orders.models import OrderCountByState
    _client = request.client.client
    paid_products = OrderCountByState.objects.select_related('product')\
                    .filter(client=_client, state="confirmed", product__status='active').order_by("-order_count")[:100]
    product_ids = []
    for prod in paid_products:
        src = prod.product.primary_rate_chart()
        prod_id = prod.product.id
        if src.stock_status == 'instock' and src.offer_price >= 500 and prod_id not in product_ids:
            product_ids.append(prod_id)
            if len(product_ids) >= 3:
                break
    if len(product_ids) < 3:
        products = Product.objects.filter(status='active').order_by('-confirmed_order_count')
        for p in products:
            if p.id not in product_ids:
                product_ids.append(p.id)
                if len(product_ids) >= 3:
                    break
    products_context = utils.create_context_for_search_results(product_ids, request)
    return dict(request=request, products_context=products_context)
register.inclusion_tag('order/zero_cart_products.html')(empty_cart_products)

def show_product_tags(request, product):
    is_deal = False
    applicable_price = product['price_info']['applicable_price']
    # Check for New Arrival Deal
    new_arrivals_ids = utils.get_new_arrivals(request, 45)
    is_new_arrival = str(product['original']) in new_arrivals_ids

    # Check for Clearance deal
    product_tag = product.get('tagset',[])
    is_clearance = False
    retailer_tags = {'clearance':False}
    for tag in product_tag:
        if tag.type == 'new_clearance_sale':
            is_clearance = True
            retailer_tags['clearance'] = True
            retailer_tags['retailer_name'] = tag.tag.tag
            break
    # Check for time based Deal
    product_end_time = {}
    if not retailer_tags['clearance'] and applicable_price and applicable_price.price_type == 'timed' and applicable_price.price_list.name in settings.SLOT_PRICE:
        day, hour, minute, second = remaining_time(applicable_price.end_time)
        product_end_time = {
                            'day':day, 
                            'hour':hour,
                            'minute':minute,
                            'second':second,
                           }
    # Check for Popular deal
    top_seller_ids = utils.get_top_sellers(request)
    is_hot_seller = str(product['original']) in top_seller_ids
    # Check for recommendation Deal
    is_recommended = False
    if request.user.is_authenticated() and 'logged_through_facebook' in request.session:
        recommended_ids = utils.get_recommendations(request)
        is_recommended = str(product['original']) in recommended_ids
    # Check for concept Deal
    concept_ids = utils.get_concept_deals(request)
    is_concept_deal = product['original'] in concept_ids
    if product_end_time or is_new_arrival or is_hot_seller or (retailer_tags ['clearance'] and not 'home_clearance' in product) or is_recommended or is_concept_deal:
        is_deal = True

    ctxt = {
                'request':request, 
                'product_context':product, 
                'is_deal':is_deal,
                'product_end_time':product_end_time, 
                'is_new_arrival':is_new_arrival,
                'is_hot_seller':is_hot_seller, 
                'retailer_tags':retailer_tags,
                'is_recommended':is_recommended,
                'is_concept_deal':is_concept_deal,
            }
    return ctxt
register.inclusion_tag('categories/product_tags.html')(show_product_tags)

@register.filter
def is_new_arrival(request, product_id):
    product_ids = utils.get_new_arrivals(request, 45)
    if str(product_id) in product_ids:
        return True
    return False

def remaining_time(time):
    delta = time - datetime.now()
    hours = delta.seconds/3600
    mins = (delta.seconds/60) % 60
    secs = delta.seconds - 60*mins - 3600*hours
    return (delta.days, hours, mins, secs)
    
def render_deals(request, product_context):
    return dict(request=request, products=product_context)
register.inclusion_tag('categories/grid_products.html')(render_deals)

@register.simple_tag
def get_facebook_profile_id(request):
    facebook_info = request.session['facebook_user_info']
    return facebook_info.facebook_id

@register.simple_tag
def get_user_picture(request):
    guest_user_pic = '/media/images/guest-user.jpg'
    user_authenticated = is_user_authenticated(request)
    if not user_authenticated:
        return guest_user_pic
    user_info = utils.get_user_info(request)
    profile = user_info['profile']
    if profile.facebook:
        fb_user_pic = "https://graph.facebook.com/%s/picture" % profile.facebook
        return fb_user_pic
    return guest_user_pic

@register.filter
def user_connected_to_facebook(request):
    facebook_cookie = utils.get_facebook_cookie(request)
    if facebook_cookie:
        return True
    return False

@register.filter
def facebook_user_loggedout(request):
    if not is_user_authenticated(request):
        return False
    if 'logged_through_facebook' in request.session and not user_connected_to_facebook(request):
        return True
    return False

@register.filter
def is_totalprice_lte(order, value):
    total_price = order.payable_amount - order.shipping_charges
    if total_price <= value:
        return True
    return False

@register.filter
def category_heirarchy(category):
    return utils.get_category_hierarchy(category)

@register.filter
def get_diff(total,payable):
    return(total-payable)

@register.filter
def get_range(to_value, from_value=1):
    return range(from_value, to_value+1)

@register.filter
def get_range_from_zero(value):
    return range(0, value+1)

@register.filter
def get_reverse_range_from_zero(value):
    #used in order modification. do not change this function - prady
    l = range(0, value)
    l.reverse()
    return l

@register.filter
def get_facet_class(field):
    field_attrs = (field.field.widget).attrs
    if 'class' not in field_attrs:
        return ""
    class_name = field_attrs['class']
    return class_name

@register.simple_tag
def get_corresponding_field(form, field_name, replace_with, replace_by, append=None):
    corresponding_field_name = field_name.replace(replace_with, replace_by)
    if append:
        corresponding_field_name = "%s%s" % (append, corresponding_field_name)
        return int(getattr(form, corresponding_field_name, ""))
    try:
        return form[corresponding_field_name]
    except KeyError:
        return ""

@register.filter
def is_filter_value_changed(form, field_name):
    gmin = get_corresponding_field(form, field_name, "min", "min", "g")
    gmax = get_corresponding_field(form, field_name, "min", "max", "g")
    cmin = get_corresponding_field(form, field_name, "min", "min", "c")
    cmax = get_corresponding_field(form, field_name, "min", "max", "c")
    if gmin != cmin or cmax != gmax:
        return True
    return False

@register.filter
def divide(num, den):
    if Decimal(str(den)) != 0:
        return Decimal(Decimal(str(num))/Decimal(str(den)))
    return Decimal(str(num))

@register.filter
def multiply(num, den):
    return Decimal(Decimal(str(num))*Decimal(str(den)))

@register.filter
def delete_text(text, pattern):
    return text.replace(pattern, '')

@register.filter
def nbsp(value):
    return value.replace(" ", "&nbsp;")

def check_user_email(request):
    user_info = utils.get_user_info(request)
    user = user_info['user']
    profile = user_info['profile']
    emails = profile.email_set.all()
    return emails.exists()

@register.simple_tag
def get_admagnet_url(category):
    if not category:
        return ""
    cat_heirarchy = utils.get_category_hierarchy(category)    
    categoryId = category.id
    
    RETARGETTING_ADMAGNET_IDS = getattr(settings, 'RETARGETTING_ADMAGNET_IDS', [])
    if not RETARGETTING_ADMAGNET_IDS:
        return ""
    admagnet_dict = {}
    
    categoryId = str(categoryId)
    if categoryId in RETARGETTING_ADMAGNET_IDS:
        admagnet_dict =  RETARGETTING_ADMAGNET_IDS[str(categoryId)]
    elif cat_heirarchy:
        for cat in cat_heirarchy:
            if str(cat[0].id) in RETARGETTING_ADMAGNET_IDS:
                admagnet_dict =  RETARGETTING_ADMAGNET_IDS[str(cat[0].id)]
                break
    
    if admagnet_dict:
        name = admagnet_dict['name']
        zone_id = admagnet_dict['zone_id']
        cb = admagnet_dict['cb']
        z = admagnet_dict['z']
        iframe_script = "<iframe id='%s' name='%s' src='http://n.admagnet.net/d/fr/?n=%s&amp;zoneid=%s&amp;target=_blank&amp;cb=%s&amp;z=%s;' framespacing='0' frameborder='no' scrolling='no' width='1' height='1'></iframe>" % (name, name, name, zone_id, cb,z)
        return iframe_script
    else:
        return ""

@register.filter
def add_days(days, date=""):
    from datetime import datetime, timedelta
    if not date: date = datetime.now()
    return date + timedelta(days = days)

def render_sabse_saste_deals(request, data):
    return dict(request=request, data=data)
register.inclusion_tag('lists/sabse_saste_grid.html')(render_sabse_saste_deals)

@register.simple_tag
def timedelta(td):
    '''prints time delta object'''
    days = td.days
    seconds = td.seconds
    hours, rem = divmod(seconds, 3600)
    minutes, seconds = divmod(rem, 60)
    time = ''
    if days:
        time += ('%s day'%days)
        if days > 1:
            time += 's'
        time += ' '
    if hours:
        time += ('%s hour'%hours)
        if hours > 1:
            time += 's'
        time += ' '
    if minutes:
        time += ('%s minute'%minutes)
        if minutes > 1:
            time += 's'
        time += ' '
    if seconds:
        time += ('%s second'%seconds)
        if seconds > 1:
            time += 's'
    return time

@register.filter
def is_valid_date(date):
    if date:
        return date > datetime.now()
    return False

@register.filter
def profile_id(request):
    try:
        profile = utils.get_user_profile(request.user)
        return profile.id
    except:
        return None

def key(d, key_name):
    try:
        ele = d[key_name]
    except:
        ele = '--'
    return ele
key = register.filter('key', key)


@register.filter
def get_managed_clients(user):
    string = ''
    profile = utils.get_user_profile(user)
    managed_clients = profile.managed_clients()
    for clients in managed_clients:
        string +=  str(clients) + ', '
    return string

@register.filter
def get_days(future_date):
    timestamp = datetime.now()
    diff = future_date - timestamp
    return diff.days


@register.filter
def get_accessible_tabs(user):
    user_tabs = UserTab.objects.filter(user=utils.get_user_profile(user))
    accessible_tabs = []
    for tabs in user_tabs:
        accessible_tabs.append(tabs.tab.tab_name)
    if user_tabs:
        return accessible_tabs
    else:
        return ''

@register.filter
def product_in_wishlist_or_not(request, product):
    if request.user.is_authenticated():
        try:
            src = SellerRateChart.objects.get(product=product)
        except SellerRateChart.DoesNotExist:
            src = None
        user_info = utils.get_user_info(request)
        user = user_info['user']
        profile = user_info['profile']
        try:
            wishlist = List.objects.get(curator=profile,type='wishlist')
        except List.DoesNotExist:
            wishlist = None
        if wishlist:
            listitems = wishlist.listitem_set.filter(sku__seller__client=request.client.client)
            if src:
                for listitem in listitems:
                    if src == listitem.sku:
                        return True
    return False

@register.filter
def diff (first, second):
    return first-second

@register.filter
def is_april_started(value):
    now = datetime.now()
    april = datetime.strptime("01 Apr 12",'%d %b %y')
    return now >= april

@register.simple_tag
def get_payback_points(order):
    from payments.models import PointsHeader
    client_name = order.client.name
    factor = Decimal(str(PointsHeader.EARN_POINTS_MAP.get(client_name, 0)))
    day = datetime.now().strftime("%A")
    if day == 'Friday' and order.is_valid_payback_promotion():
        # Payback Friday offer
        # Earn points will be 2X
        factor *= Decimal('2')
    points = int(round(Decimal(order.payable_amount*Decimal(factor))))
    return points
