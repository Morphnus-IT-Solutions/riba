import re
from django.contrib.auth.models import User
from users.models import Profile, Email
from locations.models import City, State, Country,AddressBook, Address
from django.core.cache import cache
from django.core.validators import email_re
from users.models import Email as UserEmail,Phone
import logging
from accounts.models import Client, ClientDomain
from notifications.notification import Notification
from notifications.email import Email as EmailAddress
from notifications.sms import SMS
from django.template import Context, Template
from django.template.loader import get_template
from django.conf import settings
from catalog.models import Product, ProductVariant, SellerRateChart, ProductTags, Brand, Tag, ProductImage
from categories.models import CategoryGraph, Category
from pricing.models import Price
from tracking.models import ViewUsage
import pyExcelerator
from django.http import HttpResponse
from django.utils.encoding import smart_unicode, smart_str
from django.utils import simplejson as json
import operator
import base64
import hashlib
import hmac
from datetime import datetime, timedelta

fb_log = logging.getLogger('fborder')
request_log = logging.getLogger('request')
log = logging.getLogger('request')


phone_nu_re = re.compile('\d+$')

def get_session_obj(request):
    cs = request.session
    return cs

def is_mobileweb(request):
    try:
        if request.client.type in ['mobileweb'] and not request.is_auth:
            return True
        else:
            return False
    except:
        return False


def set_cart_count(request,cart):
    cart_count = len(cart.get_items_for_billing(request))
    #cart_count = cart.orderitem_set.all().count()
    request.session['cart_count'] = cart_count
    request.session['cart_total'] = cart.payable_amount


def getOptInt(dict, key, default):
    if not key in dict:
        return default
    
    if re.match("^[0-9]+$", dict[key]):
        return int(dict[key])
    else:
        return default

def check_dates(request):
    start_date = request.GET.get('from',None)
    end_date = request.GET.get('to',None)
    search_trend = request.GET.get('search_trend',None)
    if start_date or end_date:
        if start_date:
            start_date = datetime.strptime(start_date,'%d %b %Y').date()
            if end_date:
                end_date = datetime.strptime(end_date,'%d %b %Y').date()
            else:
                end_date = datetime.now().date()

    else:
        end_date = datetime.now().date()
        if search_trend == 'day':
            start_date = end_date + timedelta(days=-0)
        elif search_trend == 'week':
            start_date = end_date + timedelta(days=-6)
        elif search_trend == 'month':
            start_date = end_date + timedelta(days=-30)
        elif search_trend == 'mtd':
            start_date = end_date + timedelta(days=-(end_date.day-1))
        
    return dict(start_date=start_date,end_date=end_date, search_trend=search_trend)


def getPaginationContext(cur_page, total_pages, base_url, *args, **kwargs):
    '''creates the context for pagination'''

    # pagination scheme
    # prev first_set [sep] prev_set cur_page next_set [sep] last_set next
    context = {}

    first_set = [] # the first set of pages
    last_set = [] # the last set of pages

    prev_set = [] # the prev set of pages
    next_set = [] # the last set of pages

    next_set = [ x for x in range(cur_page+1, cur_page+5) if x < total_pages ]
    prev_set = [ x for x in range(cur_page-4, cur_page) if x > 1 ]

    context['show_sep1'] = False
    context['show_sep2'] = False

    if prev_set:
        if prev_set[0] > 2:
            context['show_sep1'] = True

    if next_set:
        if next_set[len(next_set)-1] < total_pages - 2:
            context['show_sep2'] = True

    if cur_page > 1:
        context['enable_prev'] = True
        first_set = [1]
    else:
        context['enable_prev'] = False

    if cur_page < total_pages:
        context['enable_next'] = True
        last_set = [total_pages]
    else:
        context['enable_next'] = False

    context['base_url'] = base_url
    context['first_set'] = first_set
    context['last_set'] = last_set
    context['prev_set'] = prev_set
    context['next_set'] = next_set
    context['cur_page'] = cur_page
    context['next_page'] = cur_page + 1
    context['prev_page'] = cur_page - 1

    return context

def ternary(condition, true_val, false_val):
    if condition:
        return true_val
    else:
        return false_val

MOBILE_RE = re.compile('^\d{10}$')
def is_valid_mobile(mobile):
    if not MOBILE_RE.match(mobile):
        return False
    else:
        return True

def is_valid_email(email):
    if email_re.match(email):
        return True
    return False


def get_user_profile(user):
    ''' Returns user profile. Creates one if needed '''
    if not (user and user.is_authenticated()):
        return None
    pr = cache.get('users_profile:auth_user=%s'%user.id, None)
    if pr:
        return pr
    pr = get_profile_by_email_or_phone(user.username)
    if not pr:
        pr = Profile.objects.filter(user=user).order_by('id')[:2]
        if len(pr) > 1:
            fb_log.info('Multiple profiles for user: %s' % user.username)            
        if pr:
            pr = pr[0]
        if not pr:
            pr = Profile(user=user)
            pr.created_on = datetime.now()
            pr.save()
            if is_valid_email(user.username):
                try:
                    email = Email(email=user.username,user=pr,type='primary')
                    email.save()
                except:
                    pass
            if is_valid_mobile(user.username):
                try:
                    phone = Phone(phone-user.username,user=pr,type='primary')
                    phone.save()
                except:
                    pass
    cache.set('users_profile:auth_user=%s'%user.id, pr)
    return pr

def get_or_create_country(name, user_created=False):
    try:
        return Country.objects.get(name=name)
    except Country.DoesNotExist:
        new = Country(name=name, user_created=user_created)
        new.save()
        return new

def get_or_create_state(name, country, user_created=False):
    if not country:
        country = 1 # Default to India
    try:
        return  State.objects.get(country=country, name=name)
    except State.DoesNotExist:
        if not country:
            return None
        else:
            new = State(name=name, country=country, user_created=user_created)
            new.save()
            return new
    except State.MultipleObjectsReturned:
        return State.objects.filter(country=country, name=name).order_by(
            'id')[0]

def get_or_create_city(name, state, user_created=False):
    try:
        return City.objects.get(name=name, state=state)
    except City.DoesNotExist:
        new = City(name=name, state=state, user_created=user_created)
        new.save()
        return new
    except Exception,e:
        print 'exception',e

def create_user(username,email_id='',password=None, first_name='', last_name=''):
    ''' This function called for new user sign up on p. interface. Thus username should be a valid phone number.'''
    usr = None
    profile = None
    if not username:
        return usr, profile
    username = username.strip()
    is_type = "id"
    if is_valid_mobile(username):       
        is_type = "mobile"
        try:
            usr = User(username=username,email='')
            if password is None or password == '':
                #use set_unusable_password to allow user to set his password in future
                usr.set_unusable_password()
            else:
                usr.set_password(password)
            if first_name:
                usr.first_name=first_name
            if last_name:
                usr.last_name=last_name
            usr.save()
            profile = Profile(user=usr,created_on=datetime.now(),primary_phone='',primary_email='',secondary_email='')
            if first_name and last_name:
                profile.full_name='%s %s' % (first_name, last_name)
            profile.save()
            phone = Phone(user=profile,phone=username,type='primary')
            phone.is_verified = True
            phone.verified_on = datetime.now()
            phone.save()
        except Exception,e:
            log.exception('Error create_user username: %s  Exception: %s' % (username,repr(e)))
            return None,None

    log.info('create_user is_type is %s' % is_type)
    return usr,profile

def get_or_create_user(username,email_id='',password=None, first_name='', last_name=''):
    usr = None
    profile = None
    if not username:
        return usr, profile
    username = username.strip()
    is_type = "id"
    if is_valid_mobile(username):       
        is_type = "mobile"
        try:
            phone = Phone.objects.get(phone=username)
            profile = phone.user
            usr = profile.user
        except Phone.DoesNotExist:
            try:
                usr = User.objects.get(username=username)
            except User.DoesNotExist:
                usr = User(username=username,email='')
                if password is None or password == '':
                    #use set_unusable_password to allow user to set his password in future
                    usr.set_unusable_password()
                else:
                    usr.set_password(password)
            if first_name:
                usr.first_name=first_name
            if last_name:
                usr.last_name=last_name
            usr.save()
            try:
                profile = Profile.objects.get(user=usr)
            except Profile.DoesNotExist:
                profile = Profile(user=usr,created_on=datetime.now(),primary_phone='',primary_email='',secondary_email='')
                profile.full_name='%s %s' % (first_name, last_name)
            if first_name and last_name:
                profile.full_name='%s %s' % (first_name, last_name)
            profile.save()
            phone = Phone(user=profile,phone=username,type='primary')
            phone.save()
        except Exception,e:
            log.exception('Error get_or_create_user %s' % repr(e))
            return None,None

    if is_valid_email(username):
        is_type = "email"
        clean_username = get_cleaned_email(username)
        try:
            email = Email.objects.get(cleaned_email=clean_username)
            profile = email.user
            usr = profile.user
        except Email.DoesNotExist:
            # cant use OR in above query coz it might return multiple results.
            # Eg.: email_1 - abc.xyz@gmail.com has cleaned_email - abcxyz@gmail.com.
            # But email_2 - abcxyz@gmail.com does not have cleaned email since it's duplicate of above email.
            # email_2 was a valid email in old system.
            try:
                email = Email.objects.get(email=username)
                email.cleaned_email = clean_username
                email.save()
                profile = email.user
                usr = profile.user
            except Email.DoesNotExist:
                try:
                    usr = User.objects.get(username=username)
                except User.DoesNotExist:
                    usr = User(username=username,email=username)
                    if password is None or password == '':
                        usr.set_unusable_password()
                    else:
                        usr.set_password(password)
                if first_name:
                    usr.first_name=first_name
                if last_name:
                    usr.last_name=last_name
                usr.save()
                try:
                    profile = Profile.objects.get(user=usr)
                except Profile.DoesNotExist:
                    profile = Profile(user=usr,created_on=datetime.now())
                    profile.full_name='%s %s' % (first_name, last_name)
                if first_name and last_name:
                    profile.full_name ='%s %s' % (first_name, last_name)
                profile.save()
                email = Email(user=profile,email=username,type='primary',cleaned_email=clean_username)
                email.save()
        except Exception,e:
            log.exception('Error get_or_create_user %s' % repr(e))
            return None,None
    log.info('get_or_create_user is_type is %s' % is_type)
    return usr,profile

def formatMoney(value):
    try:
        str_value = str(value).split('.')[0]
        dec = ''
        if len(str(value).split('.')) > 1:
            dec += '.' + str(value).split('.')[1][:2]
        if dec == '.00' or dec == '.0':
            dec = ''
        if len(str_value) < 4:
            return str_value + dec
        if len(str_value) < 5:
            return str_value[:len(str_value)-3] + ',' + str_value[-3:] + dec
        steps = [3]
        seq_steps = range(5, len(str_value)+1, 2)
        steps += seq_steps
        formatted_str = ''
        last = 0
        for x in steps:
            if last != 0:
                formatted_str = ',' + str_value[-x:-last] + formatted_str
            else:
                formatted_str = ',' + str_value[-x:] + formatted_str
            last = x
        if last < len(str_value):
            formatted_str = str_value[:len(str_value)-last] + formatted_str
        return formatted_str.strip(',') + dec
    except Exception, e:
        return value

def normalize_phone(phone):
    cleaned = ''
    
    # if the input field has seperators, we read data till first seperator
    separators = ',/'
    for seperator in separators:
        if seperator in phone:
            phone = phone[:phone.index(seperator)]

    for char in phone:
        if char in '0123456789':
            cleaned += char

    if len(cleaned) == 11 and cleaned[:1]== '0':
        # phone is prefixed with country code, remove it
        return cleaned[1:]
    elif len(cleaned) == 12 and cleaned[:2] == '91':
        # phone is prefixed with zero, remove it
        return cleaned[2:]
    elif len(cleaned) == 13 and cleaned[:3] == '091':
        # phone is prefixed with zero and country code
        return cleaned[3:]
    elif len(cleaned) == 14 and cleaned[:4] == '0091':
        # phone is prefixed with zero and country code
        return cleaned[4:]
    elif len(cleaned) > 10:
        # did not match any condition. just return last 10 digits
        return cleaned[-10:0]

    return cleaned
    
def is_address_book_present(address_book,profile):
    address_string = address_book.get_address_to_check()
    address_books = AddressBook.objects.filter(profile=profile)
    for addr in address_books:
        addr_string = addr.get_address_to_check()
        if addr_string == address_string:
            return True #duplicate found
    return False


def get_from_cache(key):
    try:
        return cache.get(key)
    except:
        pass

def set_in_cache(key, obj, expire):
    try:
        cache.set(key, obj, expire)
    except:
        pass

# Truncate characters after plus(+) in email
def check_special_characters(email):
    u = email.split('@')
    if len(u) > 1:
        user, domain = u[0], u[1]
        user = user.split('+')[0]
        cleaned_email = '%s@%s' % (user, domain)
        return cleaned_email
    else:
        return email
   
# Ignore dots(.) from email
def get_cleaned_email(email):
    u = email.split('@')
    if len(u) > 1:
        user, domain = u[0], u[1]
        user = re.sub('[\.]', '', user)
        user = user.split('+')[0]       # additional check to eliminate characters afer plus(+).
        cleaned_email = '%s@%s' % (user, domain)
        return cleaned_email.lower()
    else:
        return None

def get_profile_by_email_or_phone(email_or_phone):
    if not email_or_phone:
        return None
    if is_valid_mobile(email_or_phone):
        try:
            p = get_from_cache('users:phone:p:%s' % email_or_phone)
            if p:
                return p.user
            p = Phone.objects.get(phone=email_or_phone)
            set_in_cache('users:phone:p:%s' % email_or_phone, p, 10*60)
            return p.user
        except Phone.DoesNotExist:
            return None
    elif is_valid_email(email_or_phone):
        e = get_from_cache('users:email:e:%s' % email_or_phone)
        if e:
            return e.user
        c = get_cleaned_email(email_or_phone)
        if c:
            try:
                e = Email.objects.get(cleaned_email = c)
                set_in_cache('users:email:e:%s' % email_or_phone, e, 10*60)
                return e.user
            except Email.DoesNotExist:
                # cant use OR in above query coz it might return multiple results.
                # Eg.: email_1 - abc.xyz@gmail.com has cleaned_email - abcxyz@gmail.com.
                # But email_2 - abcxyz@gmail.com does not have cleaned email since it's duplicate of above email.
                # email_2 was a valid email in old system.
                try:
                    e = Email.objects.get(email=email_or_phone)
                    e.cleaned_email = c
                    e.save()
                    set_in_cache('users:email:e:%s' % email_or_phone, e, 10*60)
                    return e.user
                except Email.DoesNotExist:
                    return None
        else:
            return None
    return None

def save_billing_info(request, user, data, **kwargs):
    from orders.models import BillingInfo
    try:
        billing_info = BillingInfo.objects.select_related('address').get(user=user)
        address = billing_info.address
    except BillingInfo.DoesNotExist:
        billing_info = BillingInfo()
        address = Address()
        address.created_on = datetime.now()
    address.profile = user
    address.address = data['billing_address']

    country_name = data['billing_country']
    country = get_or_create_country(country_name, True)

    city_name = data['billing_city']
    city = get_or_create_city(city_name, address.state, True)

    address.city = city
    address.country = country
    address.phone = data['billing_phone']
    address.pincode = data['billing_pincode']
    address.first_name = data['billing_first_name']
    address.last_name = data['billing_last_name']
    if data['billing_state']:
        state_name = data['billing_state']
        is_reverse = True
        if 'not_reverse' in kwargs:
            is_reverse = False
        state = get_or_create_state(state_name, country, True)
        address.state = state
    if data['email']:
        address.email = data['email']
    address.type = 'billing'
    address.save()

    billing_info.address = address
    billing_info.user = user
    billing_info.phone = data['billing_phone']
    billing_info.first_name  = data['billing_first_name']
    billing_info.last_name  = data['billing_last_name']

    billing_info.save()
    return address, billing_info


def create_context_for_search_results(product_ids, request, **kwargs):
    from django.db.models import Q
    ''' Create context for search results from the list of product ids
        Creates the context from minimal db queries for better perf
    '''
    # We need to get the products, product images, rate charts and prices
    # Doing one query per product_id is going to result in 4N queries
    # Typically N is around 10 to 25. Thats around 40 to 100 queries
    # Multipy this with number of simultaneous requests we want to serve
    # If we want to serve around 100 simultaneous requests per sec, that is
    # 10K db queries per sec. Not really the thing we should be doing if we
    # can avoid it.

    # The product ids given can be mix of variants, variables and normal
    # products. Ratecharts are typically attached to variants or normal
    # products. We need to get the default variant for a variable product

    # ProductVariant table stores the links for variables and their variants
    productvariants = ProductVariant.objects.filter(
        is_default_product = True,
        blueprint__in = product_ids)

    blueprints = ProductVariant.objects.filter(
        variant__in = product_ids)
    blueprint_map = {}
    blueprint_ids = []
    for pv in blueprints:
        if pv.variant_id not in blueprint_map:
            blueprint_map[pv.variant_id] = [pv.blueprint_id]
        else:
            blueprint_map[pv.variant_id].append(pv.blueprint_id)
        blueprint_ids.append(pv.blueprint_id)
    pv = None

    # All product_ids might not be variables, so we need to get the final
    # list of product_ids which will have rate charts
    productvariants_map = {}
    for pv in productvariants:
        if pv.blueprint_id not in productvariants_map:
            productvariants_map[pv.blueprint_id] = pv.variant_id

    ids_to_fetch = []
    # Holds the supplied id to transformed id map
    # id is transfromed to default variant if given id is
    # a variable
    transform_map = {}
    ctxt = {}
    for id in product_ids:
        transformed_id = id
        if long(id) in productvariants_map:
            transformed_id = productvariants_map[long(id)]
        ctxt[transformed_id] = {'original': id}
        transform_map[id] = transformed_id
        ids_to_fetch.append(transformed_id)

    images = ProductImage.objects.filter(
        product__in = ids_to_fetch).order_by('id')
    rate_charts = SellerRateChart.objects.select_related(
        'product', 'seller').filter(
        is_prefered = True,
        product__in = ids_to_fetch)

    # Commenting out getting prices are they are going to be cached
    # anyway for 10 mins
    #from django.db.models import Q
    #prices = Price.objects.select_related(
    #    'price_list').filter(
    #    rate_chart__in = [rc.id for rc in rate_charts]).exclude(
    #    Q(price_type='timed', start_time__gte=datetime.now())|
    #    Q(price_type='timed', end_time__lte=datetime.now()))

    # Tags have started becoming important annotations for the product
    # Sometimes, tags are also applied on the blueprints
    tags = ProductTags.objects.select_related('tag__tag').filter(
        product__in = ids_to_fetch + blueprint_ids)
        
    # Lets being stitching the output.
    tags_product_map = {}
    for tag in tags:
        if tag.product_id not in tags_product_map:
            tags_product_map[tag.product_id] = [tag]
        else:
            tags_product_map[tag.product_id].append(tag)

    #rate_chart_price_map = {}
    #for price in prices:
    #    rate_chart_prices = rate_chart_price_map.get(price.rate_chart_id, [])
    #    rate_chart_prices.append(price)
    #    rate_chart_price_map[price.rate_chart_id] = rate_chart_prices

    for img in images:
        product_images = ctxt[img.product_id].get('product_images', [])
        product_images.append(img)
        ctxt[img.product_id]['product_images'] = product_images

    for rc in rate_charts:
        blueprint_product = rc.product
        ctxt[rc.product.id]['tagset'] = tags_product_map.get(
            rc.product.id, [])
        ctxt[rc.product.id]['product'] = blueprint_product
        ctxt[rc.product.id]['rate_chart'] = rc
        ctxt[rc.product.id]['price_info'] = rc.getPriceInfo(
            request,
            None)
        if ctxt[rc.product.id].get('product_images',[]):
            ctxt[rc.product.id]['image'] = ctxt[rc.product.id][
                'product_images'][0]
    # Lets construct the context in the order of ids given to us
    products_context = []
    for id in product_ids:
        # if any tags are attached to the original ids, we should
        # add that to the context here
            
        extra_tags = []
        if long(id) in blueprint_map:
            for bp_id in blueprint_map[long(id)]:
                extra_tags = extra_tags + tags_product_map.get(long(bp_id), [])
        c = ctxt[transform_map[id]]
        if 'product' not in c:
            continue
        c['tagset'] = c['tagset'] + extra_tags
        products_context.append(c)
    return products_context

def get_blueprint_product(product):
    if product.type == 'variant':
        variant = ProductVariant.objects.select_related('blueprint').filter(variant=product)
        if variant:
            variant = variant[0]
            blueprint_product = Product.objects.get(id=variant.blueprint.id)
        else:
            return None
    else:
        blueprint_product = product
    return blueprint_product


#Required - Anubhav
def clear_cart(request, order):
    from orders.models import Order
    all_carts = Order.objects.filter(user=order.user,
        state__in = ['cart', 'guest_cart', 'temporary_cart'],
        client = request.client.client).order_by('-id', 'state') # TODO pick client from order
    
    guest_flag = 0
    temporary_flag = 0
    
    for cart in all_carts:
        if cart.state == 'temporary_cart' and temporary_flag == 0:
            temporary_flag = 1;
            cart.clear_items(request)
        
        elif cart.state == 'guest_cart' and guest_flag == 0:
            guest_flag = 1;
            cart.clear_items(request)
        
        elif cart.state == 'cart':
            if cart.is_same_order(order) and cart.id != order.id:
                cart.clear_items(request)

def get_excel_status(request, excel):
    if excel in request.GET:
        return True
    else:
        return False

def save_excel_file(excel_header, excel_data):
    workBookDocument = pyExcelerator.Workbook()
    docSheet1 = workBookDocument.add_sheet("sheet1")

    #Create a font object *j
    myFont = pyExcelerator.Font()

    # Change the font
    myFont.name = 'Times New Roman'

    # Make the font bold, underlined and italic
    myFont.bold = True
    myFont.underline = True

# the font should be transformed to style *
    myFontStyle = pyExcelerator.XFStyle()
    myFontStyle.font = myFont

# if you wish to apply a specific style to a specific row you can use the following command
    docSheet1.row(0).set_style(myFontStyle)
#    docSheet1.write(0,column, key,myFontStyle)
    for i in range(len(excel_header)):
        if type(excel_header[i]).__name__ in ["date", "datetime"]:
            entry = str(excel_header[i].day) + '-' + str(excel_header[i].month) + '-' + str(excel_header[i].year)
        else:
            entry = str(excel_header[i])
        docSheet1.write(0, i, entry,myFontStyle)
    row = 0
    for list in excel_data:
        row = row + 1
        for i in range(len(list)):
            if list[i] is not None:
                if type(list[i]).__name__ in ["date", "datetime"]:
                    entry = str(list[i].day) + '-' + str(list[i].month) + '-' + str(list[i].year)
                    docSheet1.write(row,i,entry)
                elif type(list[i]).__name__ in ["unicode"]:
                    entry = smart_unicode(list[i], encoding = 'utf-8', strings_only = False, errors='strict')
#                    entry = unicode(list[i]).encode("iso-8859-1")
                    docSheet1.write(row,i,entry)
                else:
                    docSheet1.write(row,i,str(list[i]))

    filename = "report.xls"
    response = HttpResponse(mimetype = "application/vnd.ms-excel")
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    workBookDocument.save(response)
    return response
    
def get_user_info(request):
    if request.user.is_authenticated():
        user = request.user
        profile = get_user_profile(request.user)
        return dict(user=user, profile=profile)
    return None

def queryset_iterator(queryset, chunksize=1000):
    '''
    Iterate over a Django Queryset ordered by the primary key

    This method loads a maximum of chunksize (default: 1000) rows in it's
    memory at the same time while django normally would load all rows in it's
    memory. Using the iterator() method only causes it to not preload all the
    classes.

    Note that the implementation of the iterator does not support ordered query sets.
    '''
#    pk = 0
#    last_pk = queryset.order_by('-pk')[0].pk
#    queryset = queryset.order_by('pk')
#    while pk < last_pk:
#        for row in queryset.filter(pk__gt=pk)[:chunksize]:
#            pk = row.pk
#            yield row
#        gc.collect()
    last_pk = queryset.order_by('-pk')[0].pk
    queryset = queryset.order_by('pk')
    pk = queryset[0].pk
    while pk < last_pk:
        for row in queryset.filter(pk__gte=pk, pk__lte=last_pk)[:chunksize]:
            yield row
        pk += chunksize

def set_fb_v2_cookie(request, response):
    key = "fb_v2"
    value = "show_new_version"
    response = set_cookie(request, response, key, value)
    return response

def set_cookie(request, response, key, value):
    domain = request.client.domain
    expiration = datetime.now() + timedelta(days=+365)
    expires = expiration.strftime("%a, %d-%b-%Y %H:%M:%S IST")
    response.set_cookie(key, value, max_age=365, expires=expires, domain=domain, secure= None)
    return response

def get_user(request):
    if request.user.is_authenticated():
        if request.client.type == 'cc' or request.client.type == 'franchise' :
            try:
                cs = get_session_obj(request)
                return cs.get('user', None).get_profile()
            except:
                pass
        try:
            return request.user.get_profile()
        except:
            pass
    return None

def track_usage(**kwargs):
    try:
        request = kwargs.get('request')
        product = kwargs.get('product')
        usage = kwargs.get('usage')
        ua = request.META.get('HTTP_USER_AGENT','').lower()
        if 'bot' in ua or 'spider' in ua:
            return
        from tracking import models
        usage_model = getattr(models, usage)
        user = get_user(request)
        if not user and usage_model != 'ViewUsage':
            # Skip tracking for anon users
            return
        vu = usage_model(client_domain = request.client,
            product = product,
            session = request.session.session_key,
            user = user)
        vu.save()
        logging.getLogger('request').info(
           'TRACK %s %s %s %s %s %s' % (datetime.now(),
           request.client,
           usage,
           request.session.session_key,
           user.id,
           product.id))
    except Exception, e:
        log.exception('Error tracking usage %s' % repr(e))

def track_product_view_usage(request, product):
    track_usage(**{
        'request': request,
        'product': product,
        'usage': 'ViewUsage'})

def track_add_to_cart_usage(request, product):
    track_usage(**{
        'request': request,
        'product': product,
        'usage': 'AddToCartUsage'})

def track_product_booked_usage(request, product):
    track_usage(**{
        'request': request,
        'product': product,
        'usage': 'BookUsage'})

def track_product_paid_usage(request, product):
    track_usage(**{
        'request': request,
        'product': product,
        'usage': 'PaidUsage'})

def base64_url_decode(inp):
    padding_factor = (4 - len(inp) % 4) % 4
    inp += "="*padding_factor
    return base64.b64decode(
        unicode(inp).translate(dict(zip(map(ord, u'-_'), u'+/'))))

def parse_signed_request(signed_request, secret):
    
    l = signed_request.split('.', 2)
    encoded_sig = l[0]
    payload = l[1]

    sig = base64_url_decode(encoded_sig)
    data = json.loads(base64_url_decode(payload))

    if data.get('algorithm').upper() != 'HMAC-SHA256':
        log.error('Unknown algorithm')
        return None
    else:
        expected_sig = hmac.new(secret, msg=payload, digestmod=hashlib.sha256).digest()

    if sig != expected_sig:
        return None
    else:
        return data

def get_facebook_cookie(request):
    app_id = settings.FACEBOOK_APPLICATION_ID
    cookie = request.COOKIES.get("fbsr_%s" % app_id, None)
    return cookie

def get_facebook_info(request):
    if not request:
        return None

    secret = settings.FACEBOOK_APPLICATION_SECRET
    cookie = get_facebook_cookie(request)

    if not cookie:
        return None
#    params = cookie.split("&")
#    data = {}
#    for item in params:
#        key, value = item.split("=")
#        data[key] = value
    data = parse_signed_request(cookie, secret)
    if not data or data.get('user_id',None) == None:
        return None
    
    try:
        from users.models import FacebookInfo
        facebook_info = FacebookInfo.objects.select_related('email',
            'email_user', 'email_user_user').get(
            facebook_id=data['user_id'])
        return facebook_info
    except FacebookInfo.DoesNotExist:
        return None

    return None

                
def add_timedelta_to_current_time(timedelta1):
    current_time = datetime.now()
    timedelta1 = int(timedelta1)
    new_date = datetime.strptime(current_time.strftime('%Y-%m-%d'),'%Y-%m-%d') + timedelta(days=timedelta1)
    return new_date

def remove_special_chars(value):
    ignored_chars = '^(){{}};<>?/\|+:'
    for char in ignored_chars:
        value = value.replace(char, '')
    return value

def get_temporary_file_path():
    import tempfile
    tf = tempfile.NamedTemporaryFile()
    path = tf.name
    tf.close()
    return path

def get_recently_viewed(request, profile, **kwargs):    
    count = kwargs.get('count', 10)
    from django.db import transaction, connection
    cursor = connection.cursor()
    # Writing raw query
    # since with values(product_id).order_by(-timestamp).distinct()
    # generates query as SELECT distinct product, timestamp, which includes timestamp
    # in select distinct by default
    cursor.execute(" SELECT DISTINCT `tracking_viewusage`.`product_id`\
                     FROM `tracking_viewusage` INNER JOIN `catalog_product` \
                     ON (`tracking_viewusage`.`product_id` = `catalog_product`.`id`)\
                     WHERE `tracking_viewusage`.`user_id` = %s\
                     AND `tracking_viewusage`.`client_domain_id` = %s\
                     AND `catalog_product`.`status` = 'active'\
                     ORDER BY `tracking_viewusage`.`timestamp` DESC\
                     LIMIT 0, %s" % (profile.id, request.client.id, count))
    rows = cursor.fetchall()
    product_ids = []
    for row in rows:
        product_ids.append(row[0])
    return product_ids
