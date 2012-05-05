from django import template
from django.conf import settings
register = template.Library()

@register.inclusion_tag('ppd/sections_menu.html')
def sections_menu(request):
	menu_items = []
        menu_items.append(dict(name='Analytics', url='http://analytics.futurebazaar.com'))
        menu_items.append(dict(name='Response', url='http://response.futurebazaar.com'))
        menu_items.append(dict(name='Sellers Hub', url='http://sellers.futurebazaar.com'))
        menu_items.append(dict(name='Support', url='http://support.futurebazaar.com'))
        #menu_items.append(dict(name='Solution',url='/solution.html'))
	#menu_items.append(dict(name='Platform',url='/platform.html'))
	#menu_items.append(dict(name='Brands',url='/brands.html'))
	#menu_items.append(dict(name='Case Studies',url='/casestudies.html',prefix='/case'))
	#menu_items.append(dict(name='About',url='/about.html'))
	#for item in menu_items:
	#	item['selected'] = request.path.startswith(item['url'])
	#	if item.get('prefix',''):
	#		if request.path.startswith(item['prefix']):
	#			item['selected'] = True
        loggedin = False
        if request.user.is_authenticated():
            loggedin = True
        return dict(menu_items=menu_items, request=request, loggedin=loggedin)

def options_from_grouped(mode, current_seller_id):
    from accounts.models import Account, PaymentOption, PaymentMode 
    current_seller = Account.objects.get(id=current_seller_id)
    options = PaymentOption.objects.filter(payment_mode__group_code=mode.group_code, account=current_seller, payment_mode__client=current_seller.client)
    return dict(options=options)
register.inclusion_tag('ppd/mixed_modes_display.html')(options_from_grouped)


@register.simple_tag
def is_selected(data, key, value):
    if not data:
        return ''
    if data.get(key,'') == value:
        return 'checked="checked"'
    if value in data.getlist(key):
        return 'checked="checked"'
    return ''

@register.simple_tag
def ppd_url(request, user=None):
    if user:
        try:
            from users.models import Profile
            profile = user.get_profile()
            #ppdadminuser = PpdAdminUser.objects.get(profile=user.get_profile())
            #canvas_page = ppdadminuser.canvas_page
            profile_id = profile.id
            return '/user/%s/' % (profile_id)
        except:
            return '/'
    else:
        return '/'

@register.simple_tag
def display_value_new(form_event, counter):
    choices= form_event.field.choices
    counter=counter-1
    return choices[counter][1]

#@register.filter
#def display_options_form_field(mode_code,field):
#    if mode_code.startswith("deposit") or mode_code.startswith("transfer"):
#        if (field=="bank_branch" or field=="bank_ac_name" or field=="bank_ac_type" or field=="bank_ac_no" or field=="bank_ifsc" or field=="bank_address"):
#            return True
#        else:
#            return False
#    if mode_code=="web" or mode_code=="credit-card-emi-ivr" or mode_code=="cod" or mode_code=="card-web" or mode_code=="card-moto":
#        return False
#
#    if mode_code=="cheque" or mode_code=="dd" or mode_code=="cash":
#        if (field=="payment_delivery_address" or field=="bank_ac_name"):
#            return True
#        else:
#            return False
#
#    return True
#
@register.filter
def enable_or_disable_option(option, client_id):
    from accounts.models import *
    client = Client.objects.get(id=client_id)
    try:
        pay_option = PaymentOption.objects.get(payment_mode=option, client=client)
        if pay_option.is_active == True:
            return True
        else:
            return False
    except:
        return False

@register.filter(name='display')
def display_value(form_event):
    form_dict = dict(form_event.field.choices).get(form_event.data, '')
    return form_dict

@register.filter
def enable_or_disable_domain_payment_option(domain_payment_option):
    return domain_payment_option.is_active

@register.filter
def is_timed_pricelist(price_list_name):
    from django.conf import settings
    if price_list_name in settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL:
        return False
    return True

@register.filter
def is_delete_option(price_list_name):
    from django.conf import settings
    if price_list_name in settings.NO_DELETE_OPTION_PRICELISTS:
        return True
    return False

@register.filter
def compare_dates(date1, date2):
    from datetime import datetime
    date2 = datetime.strptime(date2,'%Y-%m-%d %H:%M:%S') 
    if date1 == date2:
        return True
    else:
        return False

@register.filter
def compare_prices(price1, price2):
    if not(price1 and price2):
        return False
    else:
        if str(price1).split('.')[0] == str(price2).split('.')[0]:
            return True
        else:
            return False

@register.filter
def role(request):
    if 'role' in request.session:
        return request.session['role']
    else:
        return ''

@register.filter
def tabs(request):
    if 'tabs' in request.session:
        return request.session['tabs']
    else:
        return ''

@register.filter
def check_client(client_name):
    selected_client = Client.objects.get(id=client_id)
    if utils.is_ezoneonline(selected_client) or utils.is_future_ecom(selected_client):
        return True
    else:
        return False
