from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Avg, Max, Min, Count
from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader
from django.http import Http404, HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import *
from django.contrib.auth import login as auth_login
from django.contrib  import auth
from django.core.mail import send_mail
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings
from django.db.models import Q, Sum
from django import forms
from django.forms.models import modelformset_factory
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
#from accounts.forms importseller_namefrom locations.forms import *
from payouts.forms import  *
from utils import utils
from utils.utils import smart_unicode
from utils.utils import getPaginationContext, check_dates, create_context_for_search_results, get_excel_status, save_excel_file
from web.forms import *
from web.views.order_view import operator
from web.views.user_views import is_new_user, set_logged_in_user, set_eligible_user, user_order_details, show_agent_order_history
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
import simplejson
import xlrd
from xlrd import XLRDError


def all_prices(request, **kwargs):
    from accounts.models import Client
    from pricing.models import Price, PriceVersion, PriceList
    rate_chart = None
    prices = None
    skuid = ""
    article_id = ""
    searched_by = ""
    pricelist_options = ""
    errors = []
    all_prices, catalog_specific_prices, anonymous_prices = None, None, None
    delete_prices, update_prices, anonymous_update_price = [], [], []
    updated_price, no_update_in_atg, prices_rejected = [], [], []
    prices_approved, failed_to_update_in_atg = [], []
    product = None
    product_image = None
    flag = ""
    pricing_job_id = None
    pricing_job = None
    list_price, updated_list_price = None, None
    client_pricelist_mapping = settings.CLIENT_PRICELIST_MAPPING
    if_any_changes = False
    is_pricing_tool_supported = False
    all_valid_prices = None
    url = ""
    pagination = {}
    save_excel = get_excel_status(request, "excel")
    client = request.client.client
    seller = kwargs.get('seller',  None)
    is_pricing_tool_supported = utils.is_pricing_tool_supported(client)

    if not is_pricing_tool_supported:
        errors.append('Pricing tool is currently does not have support for selected client!!!')
    else:
        article_id = request.GET.get('articleid',None)
        if (not article_id) and request.method == 'POST':
            article_id = request.POST.get('articleid',None)
        if article_id:
            no_article_id_matching_entry = False
            no_sku_matching_entry = False
            try:
                rate_chart = SellerRateChart.objects.get(article_id=article_id.strip(), seller__client__id=client.id)
                searched_by = 'article_id'       
            except SellerRateChart.MultipleObjectsReturned:
                errors.append('Multiple article maintained for Articleid: %s' % article_id)
            except SellerRateChart.DoesNotExist:
                no_article_id_matching_entry = True

            try:
                rate_chart = SellerRateChart.objects.get(sku=article_id.strip(), seller__client__id=client.id)
                searched_by = 'article_id'       
            except SellerRateChart.MultipleObjectsReturned:
                errors.append('Multiple article maintained for Articleid: %s' % article_id)
            except SellerRateChart.DoesNotExist:
                no_sku_matching_entry = True
                
            if no_article_id_matching_entry and no_sku_matching_entry:
                errors.append('No active articles maintained for Articleid or SKU: %s' % article_id)

        if rate_chart or request.method == 'POST':
            check = request.POST.get('name', None)
            if check != 'change':
                treat_as_fixed_pricelists = settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL

                #Client level applicable pricelists for option of adding new prices
                client_level_applicable_pricelists = settings.CLIENT_LEVEL_APPLICABLE_PRICELISTS
                applicable_pricelists = client_level_applicable_pricelists[client.name]
                #Now, generate the HTML dropdown code for showing dropdown menu.
                if applicable_pricelists:
                    for item in applicable_pricelists:
                        pricelist_options += "<option> %s </option>" % item 

                if rate_chart:
                    flag = "searched"
                    
                    #First check, if there are any pending PriceVersion jobs pending for aaproval. 
                    #If yes, then prompt error message. If no, then proceed.

                    #No more checks for price versions as there is no maker-checker model now.
                    #price_versions = PriceVersion.objects.filter(rate_chart = rate_chart, status='pending')
                    price_versions = None

                    if price_versions:
                        errors.append('Prices pending for approval!!! First, approve/rejects those!!!')
                        product = price_versions[0].rate_chart.product
                        product_image = ProductImage.objects.filter(product=product)
                        if product_image:
                            product_image = product_image[0]
                    else:
                        all_prices = Price.objects.filter(
                            rate_chart = rate_chart).exclude(
                            Q(price_type='timed', end_time__lt=datetime.datetime.now())|
                            Q(price_list__name__contains='Anonymous'))
                        
                        for price in all_prices:
                            if price.price_list.name.__contains__(client_pricelist_mapping[client.id]):
                                list_price = price.list_price
                                break

                        anonymous_list_price = None

                        if all_prices:
                            for price in all_prices:
                                product = price.rate_chart.product
                                if product:
                                    product_image = ProductImage.objects.filter(product=product)

                                if product_image:
                                    product_image = product_image[0]

                                if product and product_image:
                                    break

                            if request.POST.get("update", None) == "Update":
                                flag = "updated"
                                
                                if request.POST.get('list_price',None):
                                    list_price_str = request.POST.get('list_price')
                                    try:
                                        list_price_int = Decimal(str(list_price_str))
                                        if list_price_int == Decimal('0'):
                                            errors.append('Cannot set M.R.P. to 0!!!')
                                    except Exception,e:
                                        errors.append('Wrong value set for M.R.P. = %s' % list_price_str)
                                        log.info(e)
                                else:
                                    errors.append('Wrong value set for M.R.P.!!!')

                                for price in all_prices:
                                    if request.POST.get("%s#offer_price" % price.id):
                                        offer_price_str = request.POST.get("%s#offer_price" % price.id)
                                        try:
                                            offer_price_int = Decimal(str(offer_price_str))
                                            if offer_price_int == Decimal('0'):
                                                errors.append('Offer Price cannot be set to 0!!!')
                                        except Exception,e:
                                            errors.append('Wrong value set for Sale Price = %s' % offer_price_str)
                                            log.info(e)
                                    else:
                                        errors.append('Wrong value set for Saleprice!!!')

                                    if request.POST.get("%s#cashback_amount" % price.id):
                                        cashback_amount_str = request.POST.get("%s#cashback_amount" % price.id)
                                        try:
                                            cashback_amount_int = Decimal(str(cashback_amount_str))
                                        except Exception,e:
                                            errors.append('Wrong value set for Cashback Amount = %s' % cashback_amount_str)
                                            log.info(e)

                                    if request.POST.get("%s#starts_on" % price.id):
                                        start_time = request.POST.get("%s#starts_on" % price.id) + " "
                                        start_time += request.POST.get("%s#starts_on#hr" % price.id) + ":"
                                        start_time += request.POST.get("%s#starts_on#min" % price.id)
                                        try:
                                            start_time = datetime.datetime.strptime(start_time,'%d-%m-%Y %H:%M')
                                        except Exception,e:
                                            errors.append('Wrong value set for Start Time = %s' % start_time)

                                    if request.POST.get("%s#ends_on" % price.id):
                                        end_time = request.POST.get("%s#ends_on" % price.id) + " "
                                        end_time += request.POST.get("%s#ends_on#hr" % price.id) + ":"
                                        end_time += request.POST.get("%s#ends_on#min" % price.id)
                                        try:
                                            end_time = datetime.datetime.strptime(end_time,'%d-%m-%Y %H:%M')
                                        except Exception,e:
                                            errors.append('Wrong value set for End Time = %s' % end_time)
                                           
                                if not errors:
                                    updated_list_price = request.POST.get('list_price')
                                    if not Decimal(str(updated_list_price)) == all_prices[0].list_price:
                                        if_any_changes = True

                                    for price in all_prices:
                                        if request.POST.get("%s#checkbox" % price.id) == "deleted":
                                            price_info = {
                                                'price':price,
                                                'action':'Delete',
                                                }
                                            update_prices.append(price_info)
                                            delete_prices.append(price)
                                            if_any_changes = True
                                        else:
                                            offer_price_changed = False
                                            if request.POST.get("%s#offer_price" % price.id) and not Decimal(str(request.POST.get("%s#offer_price" % price.id))) == price.offer_price:
                                                offer_price_changed = True
                                            
                                            cashback_amount_changed = False
                                            if request.POST.get("%s#cashback_amount" % price.id) and (((not price.cashback_amount) and (not request.POST.get("%s#cashback_amount" % price.id))) or (price.cashback_amount and not Decimal(str(request.POST.get("%s#cashback_amount" % price.id))) == price.cashback_amount)):
                                                cashback_amount_changed = True
                                            
                                            starts_on_changed = False
                                            starts_on = None
                                            if request.POST.get("%s#starts_on" % price.id):
                                                starts_on = request.POST.get("%s#starts_on" % price.id) + " "
                                                starts_on += request.POST.get("%s#starts_on#hr" % price.id) + ":"
                                                starts_on += request.POST.get("%s#starts_on#min" % price.id)
                                                starts_on = datetime.datetime.strptime(starts_on,'%d-%m-%Y %H:%M')
                                                if not starts_on == price.start_time:
                                                    starts_on_changed = True

                                            ends_on_changed = False
                                            ends_on = None
                                            if request.POST.get("%s#ends_on" % price.id):
                                                ends_on = request.POST.get("%s#ends_on" % price.id) + " "
                                                ends_on += request.POST.get("%s#ends_on#hr" % price.id) + ":"
                                                ends_on += request.POST.get("%s#ends_on#min" % price.id)
                                                ends_on = datetime.datetime.strptime(ends_on,'%d-%m-%Y %H:%M')
                                                if not ends_on == price.start_time:
                                                    ends_on_changed = True

                                            if offer_price_changed or cashback_amount_changed or starts_on_changed or ends_on_changed:
                                                price_info = {
                                                    'price':price,
                                                    'offer_price':request.POST.get("%s#offer_price" % price.id),
                                                    'cashback_amount':request.POST.get("%s#cashback_amount" % price.id),
                                                    'starts_on':starts_on,
                                                    'ends_on':ends_on,
                                                    'action':'Update',
                                                    }
                                                update_prices.append(price_info)
                                                if_any_changes = True
                                            else:
                                                price_info = {
                                                    'price':price,
                                                    'action':'No Change',
                                                    }
                                                update_prices.append(price_info)
                          
                            elif request.POST.get("confirm") and request.POST.get("confirm") == "Confirm":
                                flag = "confirmed"
                                current_list_price = request.POST.get("list_price")
                                new_list_price = request.POST.get("updated_list_price")
                                for price in all_prices:
                                    if request.POST.get("%s#delete_price" % price.id):
                                        try:
                                            price_version = set_price_version(price, 'delete', request.user.username, datetime.datetime.now())
                                            updated_price, no_update_in_atg = approve_single_price(request, price_version, client)
                                            if updated_price:
                                                prices_approved.append(updated_price[0])
                                            if no_update_in_atg:
                                                failed_to_update_in_atg.append(no_update_in_atg[0])
                                        except Exception, e:
                                            prices_rejected.append(price.rate_chart.article_id)
                                            log.info(e)

                                    elif (current_list_price != new_list_price) or (request.POST.get("%s#offer_price" % price.id) and not Decimal(str(request.POST.get("%s#offer_price" % price.id))) == price.offer_price)or (request.POST.get("%s#offer_price" % price.id) and not Decimal(str(request.POST.get("%s#cashback_amount" % price.id))) == price.cashback_amount) or (request.POST.get("%s#starts_on" % price.id) and not request.POST.get("%s#starts_on" % price.id) == str(price.start_time)) or (request.POST.get("%s#ends_on" % price.id) and not request.POST.get("%s#starts_on" % price.id) == str(price.end_time)):
                                        new_offer_price = request.POST.get("%s#offer_price" % price.id)
                                        new_cashback_amount = request.POST.get("%s#cashback_amount" % price.id)
                                        if not new_cashback_amount:
                                            new_cashback_amount = '0'
                                        
                                        new_starts_on = None
                                        if request.POST.get("%s#starts_on" % price.id) and request.POST.get("%s#starts_on" % price.id) != 'None':
                                            new_starts_on = request.POST.get("%s#starts_on" % price.id)
                                            new_starts_on = datetime.datetime.strptime(new_starts_on,'%Y-%m-%d %H:%M:%S')
                                            
                                        new_ends_on = None
                                        if request.POST.get("%s#ends_on" % price.id, None) and request.POST.get("%s#ends_on" % price.id, None) != 'None':
                                            new_ends_on = request.POST.get("%s#ends_on" % price.id)
                                            new_ends_on = datetime.datetime.strptime(new_ends_on,'%Y-%m-%d %H:%M:%S')

                                        try:
                                            price_version = set_price_version(price, 'update', request.user.username, datetime.datetime.now(), new_list_price, new_offer_price, new_cashback_amount, new_starts_on, new_ends_on)
                                            updated_price, no_update_in_atg = approve_single_price(request, price_version, client)
                                            if updated_price:
                                                prices_approved.append(updated_price[0])
                                            if no_update_in_atg:
                                                failed_to_update_in_atg.append(no_update_in_atg[0])
                                        except Exception, e:
                                            prices_rejected.append(price.rate_chart.article_id)
                                            log.info(e)

                                all_valid_prices = []#Price.objects.select_related('rate_chart__article_id').filter(rate_chart__seller=seller).exclude(Q(price_type='timed',end_time__lt=datetime.datetime.now())|Q(price_list__name__contains='Anonymous')).order_by('rate_chart__article_id')
                else:
                    errors.append('No active price maintained for this article!!!')
                    log.info('Rate chart does not exist either for sku=%s or article_id=%s' % (skuid, article_id))
        else:
            all_valid_prices = []#Price.objects.select_related('rate_chart__article_id').filter(rate_chart__seller=seller).exclude(Q(price_type='timed',end_time__lt=datetime.datetime.now())|Q(price_list__name__contains='Anonymous')).order_by('rate_chart__article_id')

        if all_valid_prices:
            if save_excel == True:
                excel_header = ['Articleid','SKU','Product Name','Catalog','M.R.P.','Offer Price','Cashback Amount']
                excel_data = []
                for valid_price in all_valid_prices:
                    excel_data.append([valid_price.rate_chart.article_id, valid_price.rate_chart.sku, valid_price.rate_chart.product.title, valid_price.price_list.name, valid_price.list_price, valid_price.offer_price, valid_price.cashback_amount])
                
                return save_excel_file(excel_header, excel_data)
   
            import re
            page_no = request.GET.get('page',1)
            page_no = int(page_no)
            items_per_page = 100
            total_results = len(all_valid_prices)
            total_pages =int(math.ceil(Decimal(total_results)/Decimal(items_per_page)))

            base_url = request.get_full_path()

            page_pattern = re.compile('[&?]page=\d+')
            base_url = page_pattern.sub('',base_url)
            page_pattern = re.compile('[&?]per_page=\d+')
            base_url = page_pattern.sub('',base_url)
            if base_url.find('?') == -1:
                base_url = base_url + '?'
            else:
                base_url = base_url + '&'
            pagination = getPaginationContext(page_no, total_pages, base_url)

            all_valid_prices = all_valid_prices[((page_no-1)*items_per_page):(page_no*items_per_page)]
   
    url = request.get_full_path()
    prices_dict = {
        'article_id':article_id,
        'sku':skuid,
        'pricelist_options':pricelist_options,
        'all_prices':all_prices,
        'all_valid_prices':all_valid_prices,
        'list_price':list_price,
        'updated_list_price':updated_list_price,
        'searched_by':searched_by,
        'product':product,
        'product_image':product_image,
        'update_prices':update_prices,
        'delete_prices':delete_prices,
        'if_any_changes':if_any_changes,
        'is_pricing_tool_supported':is_pricing_tool_supported,
        'errors':errors,
        'flag':flag,
	    'url':url,
        'pagination':pagination,
        'prices_approved':prices_approved,
        'failed_to_update_in_atg':failed_to_update_in_atg,
        'prices_rejected':prices_rejected,
        }
    
    prices_dict['client_display_name']=client.name
    return render_to_response('prices/all_prices.html', prices_dict, context_instance=RequestContext(request))

def generate_pricing_report(request, **kwargs):
    client = request.client.client
    seller = kwargs.get('seller', None)
    from web.sbf_forms import FileUploadForm
    import os
    errors, message = [], None
    all_prices = None
    form = None
    to_update = None
    path_to_save = None
    flag = None
    
    if request.method == 'POST':
        check = request.POST.get('name', None)
        if request.POST.get("upload") == 'Generate Report':
            import xlrd
            form = FileUploadForm(request.POST, request.FILES)
            if form.is_valid():
                path_to_save = save_uploaded_file(request.FILES['status_file'])
                all_prices = get_current_prices(path_to_save, seller)
            else:
                errors.append('Please select the excel file and then click upload!!!')
                form = FileUploadForm()
                flag = 'new'               

            #Delete the uploaded excel file
            if path_to_save:
                os.remove(path_to_save)
    else:
        flag = "new"
        form = FileUploadForm()
    prices_dict = {
        'flag':flag,
        'forms':form,
        'errors':errors,
        'all_prices':all_prices,
        'pagination':pagination,
        }
    prices_dict['client_display_name']=client.name
    return render_to_response('prices/report.html', prices_dict, context_instance=RequestContext(request))   

def get_pricing_info_for_job(job_id):
    all_price_versions = PriceVersion.objects.filter(pricing_job__id=job_id)
    add_price_versions = []
    delete_price_versions = []
    update_catalog_specific_price_versions = []
    update_anonymous_price_versions = []

    for pv in all_price_versions:
        if pv.action == 'add':
            add_price_versions.append(pv)
        elif pv.action == 'delete':
            delete_price_versions.append(pv)
        elif pv.action == 'update':
            if pv.price_list.name.__contains__('Anonymous'):
                update_anonymous_price_versions.append(pv)
            else:
                update_catalog_specific_price_versions.append(pv)

    return add_price_versions, delete_price_versions, update_catalog_specific_price_versions, update_anonymous_price_versions

def xml_string_for_updating_atg_prices(price, article_id, start_time, end_time, atg_price_list):
    xml_string = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>"
    xml_string += "<array-list>"
    xml_string += "<price-article-data xmlns:xsi=\"http://www.w3.org/2001/XMLSchema-instance\" xsi:type=\"java:com.fb.bulkupload.csv.vo.price.PriceArticleData\">"
    xml_string += "<display-name></display-name>"
    if end_time:
        xml_string += "<list-price-end-date>%s</list-price-end-date>" % datetime.datetime.strftime(end_time,'%d-%m-%Y %H:%M:%S')
    xml_string += "<list-price>%s</list-price>" % price
    xml_string += "<article-id>%s</article-id>" % article_id
    if start_time:
        xml_string += "<list-price-start-date>%s</list-price-start-date>" % datetime.datetime.strftime(start_time,'%d-%m-%Y %H:%M:%S')
    xml_string += "<last-modified-date>%s</last-modified-date>" % datetime.datetime.strftime(datetime.datetime.now(),'%d-%m-%Y %H:%M:%S')
    xml_string += "<base-price-list>%s</base-price-list>" % atg_price_list
    xml_string += "</price-article-data>"
    xml_string += "</array-list>"
    return xml_string

def update_price(xml_string):
    import urllib, urllib2
    from django.utils import simplejson

    values = {'xmlData':xml_string,"voType":"PriceArticleData"}
    try:
        url = '%s:%s/Future_Management/UpdateService' % (settings.ATG_PRICE_UPDATE_URL, settings.ATG_PRICE_UPDATE_PORT)
        encoder = simplejson.JSONEncoder()
        data = urllib.urlencode(values)
        req = urllib2.Request(url, data)
        res = urllib2.urlopen(req)
        if res.getcode() == 200:
            return True
        else:
            return False
    except Exception, e:
        return False

def update_atg_price(update_dict, delete_slot_price=False):
    update_list_price, update_offer_price = False, False
    list_pricelist_mapping = settings.TINLA_TO_ATG_LIST_PRICELIST_MAPPING
    atg_price_list = list_pricelist_mapping.get(update_dict['catalog'],'')

    if atg_price_list:
        xml_string = xml_string_for_updating_atg_prices(update_dict['list_price'], update_dict['article_id'], update_dict['start_time'], update_dict['end_time'], atg_price_list)
        update_list_price = update_price(xml_string)
    else:
        update_list_price = True

    offer_pricelist_mapping = settings.TINLA_TO_ATG_SALE_PRICELIST_MAPPING
    atg_price_list = offer_pricelist_mapping.get(update_dict['catalog'],'')
    #Deleting FB slot price from ATG
    if atg_price_list == 'SlotPriceList' and delete_slot_price:
        atg_price_list = 'DeleteSlotPriceList'

    if atg_price_list:
        xml_string = xml_string_for_updating_atg_prices(update_dict['offer_price'], update_dict['article_id'], update_dict['start_time'], update_dict['end_time'], atg_price_list)
        update_offer_price = update_price(xml_string)
    else:
        update_offer_price = True

    return update_list_price and update_offer_price

def approve_single_price(request, price_version, selected_client):
    from django.db.models import Q
    pv = price_version
    treat_as_fixed_pricelists =settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL
    approved_by = request.user.username
    approved_on = datetime.datetime.now()
    start_time = approved_on
    end_time = datetime.datetime(9999,12,31,0,0,0)
    prices_approved, failed_to_update_in_atg = [], []

    if pv.price_list.name in treat_as_fixed_pricelists:
        if pv.action == 'add':
            response = True
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

            if response:
                price = Price.objects.filter(
                    rate_chart = pv.rate_chart,
                    price_list = pv.price_list,
                    price_type = 'timed',
                    start_time = start_time,
                    end_time = end_time,
                    )
                if price:
                    delete_unwanted_prices_in_same_timeslot = price[1:]
                    price = price[0]
                    price.list_price = pv.new_list_price
                    price.offer_price = pv.new_offer_price
                    price.cashback_amount = pv.new_cashback_amount
                    price.save()
                    prices_approved.append(price.rate_chart.article_id)

                    for item in delete_unwanted_prices_in_same_timeslot:
                        item.delete()
                else:
                    price = Price()
                    price.rate_chart = pv.rate_chart
                    price.price_list = pv.price_list
                    price.list_price = pv.new_list_price
                    price.offer_price = pv.new_offer_price
                    price.cashback_amount = pv.new_cashback_amount
                    price.price_type = 'timed'
                    price.start_time = start_time
                    price.end_time = end_time
                    price.save()
                    prices_approved.append(price.rate_chart.article_id)

                pv.status = 'approved'
            else:
                failed_to_update_in_atg.append(pv.rate_chart.article_id)
        elif pv.action == 'update':
            try:
                response = True
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
                
                if response:
                    price = Price.objects.select_related('rate_chart','price_list').get(
                        rate_chart = pv.rate_chart,
                        price_list = pv.price_list,
                        list_price = pv.current_list_price,
                        offer_price = pv.current_offer_price,
                        cashback_amount =pv.current_cashback_amount,
                        price_type = pv.price_type,
                        start_time = pv.current_start_time,
                        end_time = pv.current_end_time
                        )

                    if price.end_time:
                        price.end_time = start_time +timedelta(microseconds=1)
                        price.save()
                        prices_approved.append(price.rate_chart.article_id)
                    else:
                        price.price_type = 'timed'
                        price.start_time =datetime.datetime(1111,1,1,0,0,0)
                        price.end_time = start_time +timedelta(microseconds=1)
                        price.save()
                        prices_approved.append(price.rate_chart.article_id)

                    price = Price()
                    price.rate_chart = pv.rate_chart
                    price.price_list = pv.price_list
                    price.list_price = pv.new_list_price
                    price.offer_price = pv.new_offer_price
                    price.cashback_amount =pv.new_cashback_amount
                    price.price_type = 'timed'
                    price.start_time = start_time
                    price.end_time = end_time
                    price.save()
                    prices_approved.append(price.rate_chart.article_id)

                    pv.status = 'approved'
                else:
                    failed_to_update_in_atg.append(pv.rate_chart.article_id)

            except Price.DoesNotExist:
                errors.append('in update_cat_specific,Unable to find price having sku=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
                pv.status = 'rejected'
        elif pv.action == 'delete':
            try:
                response = True
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
                
                if response:
                    price = Price.objects.get(
                        rate_chart = pv.rate_chart,
                        price_list = pv.price_list,
                        list_price = pv.new_list_price,
                        offer_price = pv.new_offer_price,
                        cashback_amount =pv.new_cashback_amount,
                        price_type = pv.price_type,
                        start_time = pv.new_start_time,
                        end_time = pv.new_end_time)
                    price.delete()
                    prices_approved.append(price.rate_chart.article_id)

                    pv.status = 'approved'
                else:
                    failed_to_update_in_atg.append(pv.rate_chart.article_id)

            except Price.DoesNotExist:
                errors.append('in delete_cat,Unable to find price having rate_chart_id=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
                pv.status = 'rejected'
    else:
        if pv.action == 'add':
            response = True
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
            
            if response:
                price = Price()
                price.rate_chart = pv.rate_chart
                price.price_list = pv.price_list
                price.list_price = pv.new_list_price
                price.offer_price = pv.new_offer_price
                price.cashback_amount = pv.new_cashback_amount
                price.price_type = pv.price_type
                price.start_time = pv.new_start_time
                price.end_time = pv.new_end_time
                price.save()
                prices_approved.append(price.rate_chart.article_id)

                pv.status = 'approved'
            else:
                failed_to_update_in_atg.append(pv.rate_chart.article_id)
        elif pv.action == 'update':
            try:
                response = True
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
                    #Delete the existing time slot from ATG if slot price.
                    #response1 = True
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

                    #response = response and response1
                
                if response:
                    price = Price.objects.select_related('rate_chart','price_list').get(
                        rate_chart = pv.rate_chart,
                        price_list = pv.price_list,
                        list_price = pv.current_list_price,
                        offer_price = pv.current_offer_price,
                        cashback_amount =pv.current_cashback_amount,
                        price_type = pv.price_type,
                        start_time = pv.current_start_time,
                        end_time = pv.current_end_time
                        )

                    if price.price_type == 'fixed':
                        price.list_price = pv.new_list_price
                        price.offer_price = pv.new_offer_price
                        price.cashback_amount =pv.new_cashback_amount
                        price.save()
                        prices_approved.append(price.rate_chart.article_id)
                    elif price.price_type == 'timed':
                        #price.end_time = pv.new_start_time+ timedelta(microseconds=1)
                        #price.save()
                        #prices_approved.append(price.rate_chart.article_id)

                        #price = Price()
                        price.rate_chart = pv.rate_chart
                        price.price_list = pv.price_list
                        price.list_price = pv.new_list_price
                        price.offer_price = pv.new_offer_price
                        price.cashback_amount =pv.new_cashback_amount
                        price.price_type = pv.price_type
                        price.start_time = pv.new_start_time
                        price.end_time = pv.new_end_time
                        price.save()
                        prices_approved.append(price.rate_chart.article_id)

                    pv.status = 'approved'
                else:
                    failed_to_update_in_atg.append(pv.rate_chart.article_id)

            except Price.DoesNotExist:
                errors.append('Unable to find price having sku=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
                pv.status = 'rejected'
        elif pv.action == 'delete':
            try:
                response = True
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
                if response:
                    price = Price.objects.get(
                        rate_chart = pv.rate_chart,
                        price_list = pv.price_list,
                        list_price = pv.new_list_price,
                        offer_price = pv.new_offer_price,
                        cashback_amount =pv.new_cashback_amount,
                        price_type = pv.price_type,
                        start_time = pv.new_start_time,
                        end_time = pv.new_end_time)
                    price.delete()
                    prices_approved.append(price.rate_chart.article_id)

                    pv.status = 'approved'
                else:
                    failed_to_update_in_atg.append(pv.rate_chart.article_id)
            except Price.DoesNotExist:
                errors.append('in delete_cat,Unable to find price having rate_chart_id=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
                pv.status = 'rejected'

    pv.approved_by = approved_by
    pv.approved_on = approved_on
    pv.save()

    #Update solr index.
    #Make product available on site, if-
    #1) Valid price is maintained.(--Already mainained above, so no need to chec again)
    #2) Pricelist priorities are maintained.
    #3) Valid stock is maintained.

    #XXX Handling currently only for futurebazaar. We will have to change it to 
    #be useful for any client using pricing tool.
    rate_chart = pv.rate_chart
    if utils.is_future_ecom(selected_client) and rate_chart.pricing_maintained == 'no':
        #Check whether price is maintained in FB pricelist of not
        fb_price = Price.objects.filter(rate_chart = rate_chart,
            price_list__name = 'Future Bazaar')
        if fb_price:
            rate_chart.pricing_maintained = 'yes'
            rate_chart.save()
            product = rate_chart.product
            product.update_solr_index()
    #rate_chart.stock_status = 'outofstock'
    #pricelist_priority_maintained = False
    #domain_level_applicable_pricelists = DomainLevelPriceList.objects.filter(domain__client=pv.rate_chart.seller.client)
    #if domain_level_applicable_pricelists:
    #    pricelist_priority_maintained = True
    #else:
    #    client_level_applicable_pricelists = ClientLevelPriceList.objects.filter(client=pv.rate_chart.seller.client)
    #    if client_level_applicable_pricelists:
    #        pricelist_priority_maintained = True

    #if pricelist_priority_maintained:
    #    if utils.is_future_ecom(selected_client):
    #        #As we are not currently using inventory module for FB,
    #        #relaxing the check for inventory for FB.
    #        rate_chart.stock_status = 'instock'
    #    else:
    #        inventory = Inventory.objects.filter(rate_chart = pv.rate_chart)
    #        if inventory:
    #            for item in inventory:
    #                if item.stock > Decimal('0'):
    #                    rate_chart.stock_status = 'instock'
    #                    break
    #rate_chart.save()
    #product.update_solr_index()

    return prices_approved, failed_to_update_in_atg

def approve_pricing_job(request, **kwargs):
    selected_client = request.client.client
    seller = kwargs.get('seller', None)
    flag = ""
    price_versions = None
    rate_charts = None
    treat_as_fixed_pricelists =settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL
    errors = []
    pagination = {}
    display_name_code = None
    prices_approved, prices_rejected, failed_to_update_in_atg = [], [], []
    response = True

     
    if request.method == 'POST':
        price_versions =PriceVersion.objects.select_related('rate_chart__article_id').filter(
            status='pending',
            rate_chart__seller__client__id=selected_client.id
            ).order_by('rate_chart__article_id')
        #price_versions =PriceVersion.objects.filter(status='pending').order_by('rate_chart__article_id')
        approved_by = request.user.username
        approved_on = datetime.datetime.now()
        start_time = approved_on
        end_time = datetime.datetime(9999,12,31,0,0,0)
        rate_charts = get_pending_rate_charts_for_approval(selected_client.id)

        for rc in rate_charts:
            price_versions = PriceVersion.objects.select_related('rate_chart','price_list','price_list__name').filter(rate_chart=rc,status='pending')

            if request.POST.get(str(rc.id), None) == 'approve':
                for pv in price_versions:
                    if pv.price_list.name in treat_as_fixed_pricelists:
                        if pv.action == 'add':
                            response = True
                            if utils.is_future_ecom(selected_client):
                                update_dict = {
                                     'article_id':pv.rate_chart.article_id,
                                     'list_price':pv.new_list_price,
                                     'offer_price':pv.new_offer_price,
                                     'start_time':start_time,
                                     'end_time':end_time,
                                     'catalog':pv.price_list.name,
                                     }
                                response = update_atg_price(update_dict)

                            if response:
                                price = Price.objects.filter(
                                    rate_chart = pv.rate_chart,
                                    price_list = pv.price_list,
                                    price_type = 'timed',
                                    start_time = start_time,
                                    end_time = end_time,
                                    )
                                if price:
                                    delete_unwanted_prices_in_same_timeslot = price[1:]
                                    price = price[0]
                                    price.list_price = pv.new_list_price
                                    price.offer_price = pv.new_offer_price
                                    price.cashback_amount = pv.new_cashback_amount
                                    price.save()

                                    for item in delete_unwanted_prices_in_same_timeslot:
                                        item.delete()
                                else:
                                    price = Price()
                                    price.rate_chart = pv.rate_chart
                                    price.price_list = pv.price_list
                                    price.list_price = pv.new_list_price
                                    price.offer_price = pv.new_offer_price
                                    price.cashback_amount = pv.new_cashback_amount
                                    price.price_type = 'timed'
                                    price.start_time = start_time
                                    price.end_time = end_time
                                    price.save()

                                pv.status = 'approved'
                            else:
                                failed_to_update_in_atg.append(pv.rate_chart.article_id)
                        elif pv.action == 'update':
                            try:
                                response = True
                                if utils.is_future_ecom(selected_client):
                                    update_dict = {
                                        'article_id':pv.rate_chart.article_id,
                                        'list_price':pv.new_list_price,
                                        'offer_price':pv.new_offer_price,
                                        'start_time':start_time,
                                        'end_time':end_time,
                                        'catalog':pv.price_list.name,
                                        }
                                    response = update_atg_price(update_dict)
                                
                                if response:
                                    price = Price.objects.select_related('rate_chart','price_list').get(
                                        rate_chart = pv.rate_chart,
                                        price_list = pv.price_list,
                                        list_price = pv.current_list_price,
                                        offer_price = pv.current_offer_price,
                                        cashback_amount =pv.current_cashback_amount,
                                        price_type = pv.price_type,
                                        start_time = pv.current_start_time,
                                        end_time = pv.current_end_time
                                        )

                                    if price.end_time:
                                        price.end_time = start_time +timedelta(microseconds=1)
                                        price.save()
                                    else:
                                        price.price_type = 'timed'
                                        price.start_time =datetime.datetime(1111,1,1,0,0,0)
                                        price.end_time = start_time +timedelta(microseconds=1)
                                        price.save()

                                    price = Price()
                                    price.rate_chart = pv.rate_chart
                                    price.price_list = pv.price_list
                                    price.list_price = pv.new_list_price
                                    price.offer_price = pv.new_offer_price
                                    price.cashback_amount =pv.new_cashback_amount
                                    price.price_type = 'timed'
                                    price.start_time = start_time
                                    price.end_time = end_time
                                    price.save()

                                    pv.status = 'approved'
                                else:
                                    failed_to_update_in_atg.append(pv.rate_chart.article_id)

                            except Price.DoesNotExist:
                                errors.append('in update_cat_specific,Unable to find price having sku=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
                                pv.status = 'rejected'
                        elif pv.action == 'delete':
                            try:
                                response = True
                                if utils.is_future_ecom(selected_client):
                                    update_dict = {
                                        'article_id':pv.rate_chart.article_id,
                                        'list_price':pv.new_list_price,
                                        'offer_price':pv.new_offer_price,
                                        'start_time':pv.new_start_time,
                                        'end_time':start_time,
                                        'catalog':pv.price_list.name,
                                        }
                                    response = update_atg_price(update_dict)
                                
                                if response:
                                    price = Price.objects.get(
                                        rate_chart = pv.rate_chart,
                                        price_list = pv.price_list,
                                        list_price = pv.new_list_price,
                                        offer_price = pv.new_offer_price,
                                        cashback_amount =pv.new_cashback_amount,
                                        price_type = pv.price_type,
                                        start_time = pv.new_start_time,
                                        end_time = pv.new_end_time)
                                    price.delete()

                                    pv.status = 'approved'
                                else:
                                    failed_to_update_in_atg.append(pv.rate_chart.article_id)

                            except Price.DoesNotExist:
                                errors.append('in delete_cat,Unable to find price having rate_chart_id=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
                                pv.status = 'rejected'
                    else:
                        if pv.action == 'add':
                            response = True
                            if utils.is_future_ecom(selected_client):
                                update_dict = {
                                    'article_id':pv.rate_chart.article_id,
                                    'list_price':pv.new_list_price,
                                    'offer_price':pv.new_offer_price,
                                    'start_time':pv.new_start_time,
                                    'end_time':pv.new_end_time,
                                    'catalog':pv.price_list.name,
                                    }
                                response = update_atg_price(update_dict)
                            
                            if response:
                                price = Price()
                                price.rate_chart = pv.rate_chart
                                price.price_list = pv.price_list
                                price.list_price = pv.new_list_price
                                price.offer_price = pv.new_offer_price
                                price.cashback_amount = pv.new_cashback_amount
                                price.price_type = pv.price_type
                                price.start_time = pv.new_start_time
                                price.end_time = pv.new_end_time
                                price.save()

                                pv.status = 'approved'
                            else:
                                failed_to_update_in_atg.append(pv.rate_chart.article_id)
                        elif pv.action == 'update':
                            try:
                                response = True
                                if utils.is_future_ecom(selected_client):
                                    update_dict = {
                                        'article_id':pv.rate_chart.article_id,
                                        'list_price':pv.new_list_price,
                                        'offer_price':pv.new_offer_price,
                                        'start_time':pv.new_start_time,
                                        'end_time':pv.new_end_time,
                                        'catalog':pv.price_list.name,
                                        }
                                    response = update_atg_price(update_dict)
                                
                                if response:
                                    price = Price.objects.select_related('rate_chart','price_list').get(
                                        rate_chart = pv.rate_chart,
                                        price_list = pv.price_list,
                                        list_price = pv.current_list_price,
                                        offer_price = pv.current_offer_price,
                                        cashback_amount =pv.current_cashback_amount,
                                        price_type = pv.price_type,
                                        start_time = pv.current_start_time,
                                        end_time = pv.current_end_time
                                        )

                                    if price.price_type == 'fixed':
                                        price.list_price = pv.new_list_price
                                        price.offer_price = pv.new_offer_price
                                        price.cashback_amount =pv.new_cashback_amount
                                        price.save()
                                    elif price.price_type == 'timed':
                                        price.end_time = pv.new_start_time+ timedelta(microseconds=1)
                                        price.save()

                                        price = Price()
                                        price.rate_chart = pv.rate_chart
                                        price.price_list = pv.price_list
                                        price.list_price = pv.new_list_price
                                        price.offer_price = pv.new_offer_price
                                        price.cashback_amount =pv.new_cashback_amount
                                        price.price_type = pv.price_type
                                        price.start_time = pv.new_start_time
                                        price.end_time = pv.new_end_time
                                        price.save()

                                    pv.status = 'approved'
                                else:
                                    failed_to_update_in_atg.append(pv.rate_chart.article_id)

                            except Price.DoesNotExist:
                                errors.append('in update_cat_specific,Unable to find price having sku=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
                                pv.status = 'rejected'
                        elif pv.action == 'delete':
                            try:
                                response = True
                                if utils.is_future_ecom(selected_client):
                                    update_dict = {
                                        'article_id':pv.rate_chart.article_id,
                                        'list_price':pv.new_list_price,
                                        'offer_price':pv.new_offer_price,
                                        'start_time':pv.new_start_time,
                                        'end_time':start_time,
                                        'catalog':pv.price_list.name,
                                        }
                                    response = update_atg_price(update_dict)
                                
                                if response:
                                    price = Price.objects.get(
                                        rate_chart = pv.rate_chart,
                                        price_list = pv.price_list,
                                        list_price = pv.new_list_price,
                                        offer_price = pv.new_offer_price,
                                        cashback_amount =pv.new_cashback_amount,
                                        price_type = pv.price_type,
                                        start_time = pv.new_start_time,
                                        end_time = pv.new_end_time)
                                    price.delete()

                                    pv.status = 'approved'
                                else:
                                    failed_to_update_in_atg.append(pv.rate_chart.article_id)
                            except Price.DoesNotExist:
                                errors.append('in delete_cat,Unable to find price having rate_chart_id=%s and pricelist_id=%s' %(pv.rate_chart.id, pv.price_list.id))
                                pv.status = 'rejected'

                    pv.approved_by = approved_by
                    pv.approved_on = approved_on
                    pv.save()

                    #Update solr index.
                    #Make product available on site, if-
                    #1) Valid price is maintained.(--Already mainained above, so no need to chec again)
                    #2) Pricelist priorities are maintained.
                    #3) Valid stock is maintained.
                    #
                    product = pv.rate_chart.product
                    pv.rate_chart.stock_status = 'outofstock'
                    pricelist_priority_maintained = False
                    domain_level_applicable_pricelists = DomainLevelPriceList.objects.filter(domain__client=pv.rate_chart.seller.client)
                    if domain_level_applicable_pricelists:
                        pricelist_priority_maintained = True
                    else:
                        client_level_applicable_pricelists = ClientLevelPriceList.objects.filter(client=pv.rate_chart.seller.client)
                        if client_level_applicable_pricelists:
                            pricelist_priority_maintained = True

                    if pricelist_priority_maintained:
                        inventory = Inventory.objects.filter(rate_chart = pv.rate_chart)
                        if inventory:
                            for item in inventory:
                                if item.stock > Decimal('0'):
                                    pv.rate_chart.stock_status = 'instock'
                                    break

                    product.update_solr_index()

                    if (not pv.rate_chart.article_id in prices_approved) and response:
                        prices_approved.append(pv.rate_chart.article_id)
            elif request.POST.get(str(rc.id), None) == 'reject':
                for pv in price_versions:
                    pv.status = 'rejected'
                    pv.approved_by = approved_by
                    pv.approved_on = approved_on
                    pv.save()
                    if not pv.rate_chart.article_id in prices_rejected:
                        prices_rejected.append(pv.rate_chart.article_id)


     #Get all the price versions pending for approval/rejection.
#    price_versions = PriceVersion.objects.select_related('rate_chart__article_id').filter(
#        status='pending',
#        rate_chart__seller__client__id=cid,
#        ).order_by('rate_chart__article_id')
    rate_charts = get_pending_rate_charts_for_approval(selected_client.id)

    import re
    page_no = request.GET.get('page',1)
    page_no = int(page_no)
    items_per_page = 20
    total_results = len(rate_charts)
    total_pages =int(math.ceil(Decimal(total_results)/Decimal(items_per_page)))

    base_url = request.get_full_path()

    page_pattern = re.compile('[&?]page=\d+')
    base_url = page_pattern.sub('',base_url)
    page_pattern = re.compile('[&?]per_page=\d+')
    base_url = page_pattern.sub('',base_url)
    if base_url.find('?') == -1:
        base_url = base_url + '?'
    else:
        base_url = base_url + '&'
    pagination = getPaginationContext(page_no, total_pages, base_url)

    rate_charts =rate_charts[((page_no-1)*items_per_page):(page_no*items_per_page)]

    approve_jobs_dict = {
        'rate_charts':rate_charts,
        'prices_approved':prices_approved,
        'prices_rejected':prices_rejected,
        'failed_to_update_in_atg':failed_to_update_in_atg,
        'pagination':pagination,
        'errors':errors,
        'flag':flag,
        'client_display_name':selected_client.id,
        }
    return render_to_response('prices/approve_pricing_jobs.html', approve_jobs_dict, context_instance=RequestContext(request))

def get_pending_rate_charts_for_approval(cid):
    distinct_rate_charts = PriceVersion.objects.filter(
        status='pending',
        rate_chart__seller__client__id=cid
        ).distinct('rate_chart').values('rate_chart')

    rate_chart_ids = []
    for rc in distinct_rate_charts:
        rate_chart_ids.append(rc['rate_chart'])

    rate_charts = SellerRateChart.objects.filter(id__in=rate_chart_ids)
    return rate_charts

def price_version_details(request):
    rc_id = request.GET.get('rc_id')
    #num = request.GET.get('num',0)
    price_versions = PriceVersion.objects.filter(rate_chart__id=rc_id, status='pending').order_by('created_on')
    return render_to_response('prices/price_version_details.html', {'price_versions':price_versions},
                context_instance=RequestContext(request))

def get_temporary_file_path():
    import tempfile
    tf = tempfile.NamedTemporaryFile()
    path = tf.name
    tf.close()
    return path

def save_uploaded_file(f):
    path_to_save = get_temporary_file_path()
    fp = open(path_to_save, 'w')
    for chunk in f.chunks():
        fp.write(chunk)
    fp.close()
    return path_to_save

def get_account(price_list_name):
    pricelist_to_account_mapping = settings.PRICELIST_TO_ACCOUNT_MAPPING
    return utils.get_seller(pricelist_to_account_mapping[price_list_name])

def get_current_prices(path_to_save, seller):
    import xlrd
    from django.db.models import Q
    book = xlrd.open_workbook(path_to_save)
    sh = book.sheet_by_index(0)
    header = sh.row(0)
    map = {}
    idx = 0
    for idx in range(sh.ncols):
        map[header[idx].value.strip().lower()] = idx
    errors = []
    to_update = []
    skip_prices = []
    update_prices = []
    client_level_applicable_pricelists = settings.CLIENT_LEVEL_APPLICABLE_PRICELISTS

    for row_count in range(1, sh.nrows):
        row = sh.row(row_count)
        try:
            article_id = row[map['articleid']].value
            to_update.append({
                'article_id': str(int(article_id)).split('.')[0],
            })
        except KeyError:
            errors.append('Unsupported excel file.')
            break

    if to_update:
        from pricing.models import Price,PriceList
        all_prices = []
        for item in to_update:
            rate_chart = None
            try:
                rate_chart = SellerRateChart.objects.get(article_id = item['article_id'], seller=seller) 
            except SellerRateChart.DoesNotExist:
                log.info('SellerRateChart for article id - %s does not exist' % item['article_id'])
            except SellerRateChart.MultipleObjectsReturned:
                log.info('Multiple articles maitained for article id - %s' % item['article_id'])

            if rate_chart:
                for pl in client_level_applicable_pricelists:
                    price_versions = PriceVersion.objects.filter(
                        rate_chart = rate_chart, 
                        price_list__name = pl,
                        status = 'approved').order_by('-approved_on')
                    
                    if price_versions:
                        price_info = {
                            'article_id':item['article_id'],
                            'product_name':rate_chart.product.title,
                            'catalog':price_versions[0].price_list.name,
                            'price_versions':price_versions[:5],
                            }
                        all_prices.append(price_info)

    return all_prices

def validate_excel_entry(article_id, list_price, offer_price, display_name, start_time, end_time, cashback_amount):
    errors = []
    price_lists_dir = settings.PRICE_LISTS_DIRECTORY 
    article_id_validated = False
    try:
        article_id_int = int(article_id)
        article_id_validated = True
    except:
        errors.append("Wrong value %s in the 'Articleid' column!!! Please correct it and try to re-upload!!!" % article_id)

    list_price_validated = False
    try:
        list_price_int = int(list_price)
        list_price_validated = True
    except:
        errors.append("Wrong value %s in the 'MRP' column!!! Please correct it and try to re-upload!!!" % list_price)
       
    offer_price_validated = False
    try:
        offer_price_int = int(offer_price)
        offer_price_validated = True
    except:
        errors.append("Wrong value %s in the 'Salesprice' column!!! Please correct it and try to re-upload!!!" % offer_price)

    cashback_amount_validated = False
    try:
        cashback_int = int(cashback_amount)
        cashback_amount_validated = True
    except:
        errors.append("Wrong value %s in the 'Cashback Amount' column!!! Please correct it and try to re-upload!!!" % cashback_amount)

    start_time_validated = False
    try:
        start_time_date = datetime.datetime.strptime(str(start_time),'%Y-%m-%d %H:%M:%S')
        start_time_validated = True
    except:
        errors.append("Wrong value %s in the 'Starttime' column!!! Please correct it and try to re-upload!!!" % start_time)
        
    end_time_validated = False
    try:
        end_time_date = datetime.datetime.strptime(str(end_time),'%Y-%m-%d %H:%M:%S')
        end_time_validated = True
    except:
        errors.append("Wrong value %s in the 'Endtime' column!!! Please correct it and try to re-upload!!!" % end_time)
       
    catalog_name_validated = False
    try:
        catalog_name = price_lists_dir[str(display_name).strip().lower()]
        catalog_name_validated = True
    except:
        errors.append("Wrong value %s in the 'Catalog' column!!! Please correct it and try to re-upload!!!" % display_name)

    entry_validated = False
    if article_id_validated and list_price_validated and offer_price_validated and cashback_amount_validated and start_time_validated and end_time_validated and catalog_name_validated:
        entry_validated = True
    return errors, entry_validated

def get_prices(path_to_save, seller):
    import xlrd
    from django.db.models import Q
    from django.utils import simplejson
    book = xlrd.open_workbook(path_to_save)
    sh = book.sheet_by_index(0)
    header = sh.row(0)
    map = {}
    idx = 0
    for idx in range(sh.ncols):
        map[header[idx].value.strip().lower()] = idx
    errors, to_update, skip_prices, update_prices, article_id_list = [], [], [], [], []
    seller_rate_chart_dict = {}
    price_lists_dir = settings.PRICE_LISTS_DIRECTORY 
    treat_as_fixed_pricelist = settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL

    for row_count in range(1, sh.nrows):
        row = sh.row(row_count)
        try:
            article_id = row[map['articleid']].value
            list_price = row[map['mrp']].value
            offer_price = row[map['salesprice']].value
            display_name = row[map['catalog']].value
            start_time = row[map['starttime']].value
            end_time = row[map['endtime']].value
            cashback_amount = row[map['cashback amount']].value
            
            error_in_entry_validation, entry_validated = validate_excel_entry(article_id, list_price, offer_price, display_name, start_time, end_time, cashback_amount)
            errors += error_in_entry_validation
            if entry_validated:
                add_dict = {
                    'article_id': str(int(article_id)).strip().split('.')[0],
                    'list_price': list_price,
                    'offer_price' : offer_price,
                    'display_name' : display_name.strip().lower(),
                    'cashback_amount' : cashback_amount,
                    'start_time':start_time,
                    'end_time':end_time,
                    }

                repeated = False
                for item in to_update:
                    if (item['article_id'] == add_dict['article_id']) and (item['display_name'] == add_dict['display_name']):
                        if price_lists_dir[add_dict['display_name']] in treat_as_fixed_pricelist:
                            errors.append("Duplicate Entries for Articleid-'%s' and Catalog-'%s' combination!!!" % (add_dict['article_id'],add_dict['display_name']))
                            repeated = True
                            break
                        else:
                            if (item['start_time'] == add_dict['start_time']) and (item['end_time'] == add_dict['end_time']):
                                errors.append("Overlapping timeslot entries for Articleid-'%s' and Catalog-'%s' combination!!!" % (add_dict['article_id'],add_dict['display_name']))
                                repeated = True
                                break

                if not repeated:
                    to_update.append(add_dict)
                    if not add_dict['article_id'] in article_id_list:
                        article_id_list.append(add_dict['article_id'])
        except KeyError:
            errors.append('Unsupported excel file. Please check the sample template format!!!')
            break
    
    #seller = None
    if to_update:        
        to_update.sort()
        #seller = get_account(price_lists_dir[to_update[0]['display_name']])

    #Fetch seller rate charts for all the article ids in excel file.
    multiple_rate_charts_found = []
    if seller and article_id_list:
        all_seller_rate_charts = SellerRateChart.objects.filter(
            article_id__in=article_id_list, 
            seller=seller)
        if all_seller_rate_charts:
            for item in all_seller_rate_charts:
                if item.article_id in seller_rate_chart_dict:
                    errors.append('Multiple active articles maintained for Articleid - %s' % item.article_id)
                    del seller_rate_chart_dict[item.article_id] 
                    multiple_rate_charts_found.append(item.article_id)
                else:
                    seller_rate_chart_dict[item.article_id] = item

    if to_update:
        from pricing.models import Price,PriceList
        all_prices = []
        #update_prices = []
        #skip_prices = []
        for item in to_update:
            #try:
            price_list = PriceList.objects.get(name=price_lists_dir[item['display_name']])
            #seller = get_account(price_lists_dir[item['display_name']])
            rate_chart = seller_rate_chart_dict.get(item['article_id'],None)
            if (not rate_chart) and (not item['article_id'] in multiple_rate_charts_found):
                errors.append('No active article maintained for Articleid - %s' % item['article_id'])

            if rate_chart:
                price = None
                check_overlapped_prices = True
                if price_lists_dir[item['display_name']] in treat_as_fixed_pricelist:
                    check_overlapped_prices = False

                overlapped_price = None
                if check_overlapped_prices:
                    start_time = datetime.datetime.strptime(item['start_time'],'%Y-%m-%d %H:%M:%S')
                    end_time = datetime.datetime.strptime(item['end_time'],'%Y-%m-%d %H:%M:%S')
                    overlapped_price = Price.objects.select_related('rate_chart','price_list').filter(
                        rate_chart=rate_chart, 
                        price_list=price_list).exclude(
                        Q(price_type = 'timed', start_time__gt = end_time) | 
                        Q(price_type = 'timed', end_time__lt = start_time)
                        )
                if check_overlapped_prices and overlapped_price:
                    price_info = {
                        'article_id':item['article_id'],
                        'catalog':price_lists_dir[item['display_name']],
                        'list_price':item['list_price'],
                        'offer_price':item['offer_price'],
                        'cashback_amount':item['cashback_amount'],
                        'start_time':item['start_time'],
                        'end_time':item['end_time'],
                        'conflicts':overlapped_price,
                        'rowspan':len(overlapped_price),
                        'action':'Skip',
                        }
                    skip_prices.append(price_info)
                else:
                    try:
                        if price_lists_dir[item['display_name']] in treat_as_fixed_pricelist:
                            price = Price.objects.select_related('rate_chart','price_list').filter(
                                rate_chart=rate_chart, 
                                price_list=price_list, 
                                ).exclude(
                                Q(price_type='timed',start_time__gte=datetime.datetime.now())| 
                                Q(price_type='timed', end_time__lte=datetime.datetime.now())
                                )
                            if price:
                                price = price[0]
                        else:
                            price = Price.objects.select_related('rate_chart','price_list').get(
                                rate_chart=rate_chart, 
                                price_list=price_list, 
                                price_type='timed', 
                                start_time=start_time, 
                                end_time=end_time,
                                )
                            
                        if price:
                            action = ''
                            if price.list_price != Decimal(str(item['list_price'])) or price.offer_price != Decimal(str(item['offer_price'])) or price.cashback_amount != Decimal(str(item['cashback_amount'])):
                                action = 'Update'
                            elif not price_lists_dir[item['display_name']] in treat_as_fixed_pricelist:
                                if price.start_time != start_time or price.end_time != end_time:
                                    action = 'Update'
                                else:
                                    action = 'No Action'
                            else:
                                    action = 'No Action'

                            price_info = {
                                'price':price,
                                'list_price':Decimal(str(item['list_price'])),
                                'offer_price':Decimal(str(item['offer_price'])),
                                'cashback_amount':Decimal(str(item['cashback_amount'])),
                                'start_time':item['start_time'],
                                'end_time':item['end_time'],
                                'action':action,
                                }
                        else:
                            price = Price(rate_chart=rate_chart, price_list=price_list, list_price=Decimal(str(item['list_price'])), offer_price=Decimal(str(item['offer_price'])),cashback_amount=Decimal(str(item['cashback_amount'])))
                            if not price_lists_dir[item['display_name']] in treat_as_fixed_pricelist:
                                price.price_type = 'timed'
                                price.start_time = start_time
                                price.end_time = end_time

                            price_info = {
                                'price':price,
                                'list_price':Decimal(str(item['list_price'])),
                                'offer_price':Decimal(str(item['offer_price'])),
                                'cashback_amount':Decimal(str(item['cashback_amount'])),
                                'start_time':item['start_time'],
                                'end_time':item['end_time'],
                                'action':'Add',
                               }
                        update_prices.append(price_info)
                    except Price.DoesNotExist:
                        price = Price(rate_chart=rate_chart, price_list=price_list,list_price=Decimal(str(item['list_price'])), offer_price=Decimal(str(item['offer_price'])),cashback_amount=Decimal(str(item['cashback_amount'])))
                        if not price_lists_dir[item['display_name']] in treat_as_fixed_pricelist:
                            price.price_type = 'timed'
                            price.start_time = start_time
                            price.end_time = end_time

                        price_info = {
                            'price':price,
                            'list_price':Decimal(str(item['list_price'])),
                            'offer_price':Decimal(str(item['offer_price'])),
                            'cashback_amount':Decimal(str(item['cashback_amount'])),
                            'start_time':item['start_time'],
                            'end_time':item['end_time'],
                            'action':'Add',
                           }
                        update_prices.append(price_info)
    else:
        if not errors:
            log.info('no prices to upload in the sheet!!!')
            errors.append('No prices to upload in the excel!!!')

    #Creating json for update_prices to render between the templates
    add_price_json = []
    update_price_json = []
    for i in update_prices:
        if i['action'] == 'Add':
            temp_dict= {}
            temp_dict['list_price'] = str(i['list_price'])
            temp_dict['offer_price'] = str(i['offer_price'])
            temp_dict['cashback_amount'] = str(i['cashback_amount'])
            temp_dict['start_time'] = str(i['start_time'])
            temp_dict['end_time'] = str(i['end_time'])
            temp_dict['price_list'] = i['price'].price_list.name
            temp_dict['rate_chart'] = i['price'].rate_chart.id
            add_price_json.append(temp_dict)
        elif i['action'] == 'Update':
            temp_dict= {}
            temp_dict['list_price'] = str(i['list_price'])
            temp_dict['offer_price'] = str(i['offer_price'])
            temp_dict['cashback_amount'] = str(i['cashback_amount'])
            temp_dict['start_time'] = str(i['start_time'])
            temp_dict['end_time'] = str(i['end_time'])
            temp_dict['price'] = i['price'].id
            update_price_json.append(temp_dict)

    all_prices_json = {'add_price':add_price_json, 'update_price':update_price_json}
    all_prices_json = simplejson.dumps(all_prices_json)
    all_prices = {'skip':skip_prices, 'update':update_prices}
    return errors, all_prices, all_prices_json

def set_price_version(price, action, created_by, created_on, new_list_price=None, new_offer_price=None, new_cashback_amount=None, new_starts_on=None, new_ends_on=None):
    price_version = PriceVersion()
    price_version.rate_chart = price.rate_chart
    price_version.price_list = price.price_list
    
    price_version.current_list_price = price.list_price
    if new_list_price:
        price_version.new_list_price = Decimal(str(new_list_price)).quantize(Decimal('1.'), rounding=ROUND_UP)
    else:
        price_version.new_list_price = price.list_price
        
    price_version.current_offer_price = price.offer_price
    if new_offer_price:
        price_version.new_offer_price = Decimal(str(new_offer_price)).quantize(Decimal('1.'), rounding=ROUND_UP)
    else:
        price_version.new_offer_price = price.offer_price

    price_version.current_cashback_amount = price.cashback_amount
    if new_cashback_amount != None:
        price_version.new_cashback_amount = Decimal(str(new_cashback_amount)).quantize(Decimal('1.'), rounding=ROUND_UP)
    else:
        price_version.new_cashback_amount = price.cashback_amount

    price_version.current_start_time = price.start_time
    if new_starts_on:
        #price_version.new_start_time = datetime.datetime.strptime(new_starts_on,'%Y-%m-%d %H:%M:%S')
        price_version.new_start_time = new_starts_on
    else:
        price_version.new_start_time = price.start_time
    
    price_version.current_end_time = price.end_time
    if new_ends_on:
        #price_version.new_end_time = datetime.datetime.strptime(new_ends_on,'%Y-%m-%d %H:%M:%S')
        price_version.new_end_time = new_ends_on
    else:
        price_version.new_end_time = price.end_time
        
    #price_version.pricing_job = pricing_job
    price_version.price_type = price.price_type
    #if price.price_list.name in settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL:
    #    price_version.price_type = 'timed'
    price_version.action = action
    price_version.created_by = created_by
    price_version.created_on = created_on
    price_version.save()
    return price_version

def upload_price_xls(request, **kwargs):
    from web.sbf_forms import FileUploadForm
    from django.utils import simplejson
    import os
    selected_client = request.client.client
    seller = kwargs.get('seller', None)
    if seller:
        seller = seller[0]
    errors, message = [], None
    all_prices, all_prices_json = None, None
    form = None
    flag = None
    to_update = None
    path_to_save = None
    price_lists_dir = settings.PRICE_LISTS_DIRECTORY 
    updated_price, no_update_in_atg, prices_rejected = [], [], []
    prices_approved, failed_to_update_in_atg = [], []

    if request.method == 'POST':
        if request.POST.get("upload") == 'Upload':
            import xlrd
            form = FileUploadForm(request.POST, request.FILES)
            if form.is_valid():
                path_to_save = save_uploaded_file(request.FILES['status_file'])
                errors, all_prices, all_prices_json = get_prices(path_to_save, seller)

                #Delete the uploaded excel file
                if path_to_save:
                    os.remove(path_to_save)

                if errors:
                    form = FileUploadForm()
                    flag = 'new'
                else:
                    flag = 'show_details'
            else:
                errors.append('Please select the excel file and then click upload!!!')
                form = FileUploadForm()
                flag = 'new'

        elif request.POST.get("update") == 'Update':
            #path_to_save = request.POST.get("path_to_save")
            all_prices_json = simplejson.loads(request.POST.get("all_prices_json"))
            add_price_json = all_prices_json['add_price']
            update_price_json = all_prices_json['update_price']
            update_prices = []

            if add_price_json:
                treat_as_fixed_pricelist = settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL
                for item in add_price_json:
                    rate_chart = SellerRateChart.objects.get(id=item['rate_chart'])
                    price_list = PriceList.objects.get(name=item['price_list'])
                    price = Price(rate_chart=rate_chart, price_list=price_list, list_price=Decimal(str(item['list_price'])), offer_price=Decimal(str(item['offer_price'])),cashback_amount=Decimal(str(item['cashback_amount'])))

                    if not item['price_list'].strip() in treat_as_fixed_pricelist:
                        price.price_type = 'timed'
                        price.start_time = item['start_time']
                        price.end_time = item['end_time']

                    price_info = {
                        'price':price,
                        'list_price':Decimal(str(item['list_price'])),
                        'offer_price':Decimal(str(item['offer_price'])),
                        'cashback_amount':Decimal(str(item['cashback_amount'])),
                        'start_time':datetime.datetime.strptime(item['start_time'],'%Y-%m-%d %H:%M:%S'),
                        'end_time':datetime.datetime.strptime(item['end_time'],'%Y-%m-%d %H:%M:%S'),
                        'action':'Add',
                       }
                    update_prices.append(price_info)

            if update_price_json:
                for item in update_price_json:
                    price = Price.objects.select_related('rate_chart','price_list').get(id=item['price'])

                    price_info = {
                        'price':price,
                        'list_price':Decimal(str(item['list_price'])),
                        'offer_price':Decimal(str(item['offer_price'])),
                        'cashback_amount':Decimal(str(item['cashback_amount'])),
                        'start_time':datetime.datetime.strptime(item['start_time'],'%Y-%m-%d %H:%M:%S'),
                        'end_time':datetime.datetime.strptime(item['end_time'],'%Y-%m-%d %H:%M:%S'),
                        'action':'Update',
                       }
                    update_prices.append(price_info)

            all_prices = {'update':update_prices}

            #errors, all_prices = get_prices(path_to_save)

            actions = {'Update':'update','Add':'add'}
            created_by = request.user.username
            created_on = datetime.datetime.now()

            if all_prices['update']:
                for price_info_dict in all_prices['update']:
                    if price_info_dict['action'] in ['Update','Add']:
                        price = price_info_dict['price']
                        new_list_price = price_info_dict['list_price']
                        new_offer_price = price_info_dict['offer_price']
                        new_cashback_amount = price_info_dict['cashback_amount']
                        new_start_time = price_info_dict['start_time']
                        new_end_time = price_info_dict['end_time']
                        action = actions[price_info_dict['action']]
                        try:
                            price_version = set_price_version(price, action, created_by, created_on, new_list_price, new_offer_price, new_cashback_amount, new_start_time, new_end_time)
                            updated_price, no_update_in_atg = approve_single_price(request, price_version, selected_client)
                            if updated_price:
                                prices_approved.append(updated_price[0])
                            if no_update_in_atg:
                                failed_to_update_in_atg.append(no_update_in_atg[0])
                        except Exception, e:
                            prices_rejected.append(price.rate_chart.article_id)
                            log.info(e)

            flag = 'updated'
            form = FileUploadForm()
    else:
        form = FileUploadForm()
        flag = 'new'
    prices_dict = {
        'forms':form,
        'errors':errors,
        'all_prices':all_prices,
        'all_prices_json':all_prices_json,
        'flag':flag,
        'path_to_save':path_to_save,
        'url':request.get_full_path(),
        'prices_approved':prices_approved,
        'failed_to_update_in_atg':failed_to_update_in_atg,
        'prices_rejected':prices_rejected,
        }
    prices_dict['client_display_name'] = selected_client.name
    return render_to_response('prices/price_bulk_upload.html', prices_dict, context_instance=RequestContext(request))

def get_pricing_info(rate_chart):
    #from django.db.models import Q
    catalog_specific_prices, anonymous_prices = [], []
    all_prices = Price.objects.filter(rate_chart__in = rate_chart).exclude(price_type='timed', end_time__lt=datetime.datetime.now())

    for price in all_prices:
        if price.price_list.name.__contains__('Anonymous'):
            anonymous_prices.append(price)
        else:
            catalog_specific_prices.append(price)

    return all_prices, catalog_specific_prices, anonymous_prices

def search_by_sku(request, **kwargs):
    client = request.client.client
    seller = kwargs.get('seller', None)
    rate_chart = None
    prices = None
    skuid = ""
    article_id = ""
    searched_by = ""
    pricelist_options = ""
    errors = []
    all_prices, catalog_specific_prices, anonymous_prices = None, None, None
    delete_prices, update_prices, anonymous_update_price = [], [], []
    product = None
    product_image = None
    flag = ""
    pricing_job_id = None
    pricing_job = None
    list_price, updated_list_price = None, None
    client_pricelist_mapping = settings.CLIENT_PRICELIST_MAPPING
    if_any_changes = False
    is_pricing_tool_supported = False

    from accounts.models import Client
    is_pricing_tool_supported = utils.is_pricing_tool_supported(client)

    if request.method == 'POST':
        from pricing.models import Price
        treat_as_fixed_pricelists = settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL

    if not is_pricing_tool_supported:
        errors.append('Pricing tool is currently does not have support for selected client!!!')
    else:
        if request.method == 'POST':
            from pricing.models import Price, PriceVersion, PriceList
            treat_as_fixed_pricelists = settings.TREAT_AS_FIXED_PRICELISTS_IN_PRICING_TOOL

            #Client level applicable pricelists for option of adding new prices
            client_level_applicable_pricelists = settings.CLIENT_LEVEL_APPLICABLE_PRICELISTS
            applicable_pricelists = client_level_applicable_pricelists[client.name]
            #Now, generate the HTML dropdown code for showing dropdown menu.
            for item in applicable_pricelists:
                pricelist_options += "<option> %s </option>" % item 

            skuid = request.POST.get("sku")
            article_id = request.POST.get("articleid")

            if skuid:
                try:
                    rate_chart = SellerRateChart.objects.get(sku=skuid.strip(),seller__client__id=client.id)
                except SellerRateChart.DoesNotExist:
                    errors.append('No article maintained for SKU - %s' % skuid)
                except SellerRateChart.MultipleObjectsReturned:
                    errors.append('Multiple articles maintained for same SKU - %s' % skuid)
                   
                if rate_chart:
                    article_id = rate_chart.article_id
                searched_by = 'skuid'
            elif article_id:
                try:
                    rate_chart = SellerRateChart.objects.get(article_id=article_id.strip(), seller__client__id=client.id)
                except SellerRateChart.DoesNotExist:
                    errors.append('No article maintained for Articleid - %s' % article_id)
                except SellerRateChart.MultipleObjectsReturned:
                    errors.append('Multiple articles maintained for same Articleid - %s' % article_id)

                if rate_chart:
                    skuid = rate_chart.sku
                searched_by = 'article_id'

            if rate_chart:
                flag = "searched"
                
                #First check, if there are any pending PriceVersion jobs pending for aaproval. 
                #If yes, then prompt error message. If no, then proceed.
                price_versions = PriceVersion.objects.filter(rate_chart__in = rate_chart, status='pending')

                if price_versions:
                    errors.append('Prices pending for approval!!! First, approve/rejects those!!!')
                    product = price_versions[0].rate_chart.product
                    product_image = ProductImage.objects.filter(product=product)
                    if product_image:
                        product_image = product_image[0]
                else:
                    all_prices = Price.objects.filter(
                        rate_chart__in = rate_chart).exclude(
                        Q(price_type='timed', end_time__lt=datetime.datetime.now())|
                        Q(price_list__name__contains='Anonymous'))
                   
                    for price in all_prices:
                        if price.price_list.name.__contains__(client_pricelist_mapping[client.id]):
                            list_price = price.list_price
                            break

                    anonymous_list_price = None

                    if all_prices:
                        for price in all_prices:
                            product = price.rate_chart.product
                            if product:
                                product_image = ProductImage.objects.filter(product=product)

                            if product_image:
                                product_image = product_image[0]

                            if product and product_image:
                                break

                        if request.POST.get("update", None) == "Update":
                            updated_list_price = request.POST.get('list_price')
                            if not Decimal(str(updated_list_price)) == all_prices[0].list_price:
                                if_any_changes = True

                            flag = "updated"

                            if Decimal(str(request.POST.get('list_price',None))) == Decimal('0'):
                                errors.append('Cannot set M.R.P. to 0!!!')

                            for price in all_prices:
                                if request.POST.get("%s#offer_price" % price.id) and Decimal(str(request.POST.get("%s#offer_price" % price.id))) == Decimal('0'):
                                    errors.append('Offer Price cannot be set to 0!!!')

                            if not errors:
                                for price in all_prices:
                                    if request.POST.get("%s#checkbox" % price.id) == "deleted":
                                        price_info = {
                                            'price':price,
                                            'action':'Delete',
                                            }
                                        update_prices.append(price_info)
                                        delete_prices.append(price)
                                        if_any_changes = True
                                    else:
                                        offer_price_changed = False
                                        if request.POST.get("%s#offer_price" % price.id) and not Decimal(str(request.POST.get("%s#offer_price" % price.id))) == price.offer_price:
                                            offer_price_changed = True
                                        
                                        cashback_amount_changed = False
                                        if request.POST.get("%s#cashback_amount" % price.id) and ((not price.cashback_amount) or (price.cashback_amount and not Decimal(str(request.POST.get("%s#cashback_amount" % price.id))) == price.cashback_amount)):
                                            cashback_amount_changed = True
                                        
                                        starts_on_changed = False
                                        starts_on = None
                                        if request.POST.get("%s#starts_on" % price.id):
                                            starts_on = request.POST.get("%s#starts_on" % price.id) + " "
                                            starts_on += request.POST.get("%s#starts_on#hr" % price.id) + ":"
                                            starts_on += request.POST.get("%s#starts_on#min" % price.id)
                                            starts_on = datetime.datetime.strptime(starts_on,'%d-%m-%Y %H:%M')
                                            if not starts_on == price.start_time:
                                                starts_on_changed = True

                                        ends_on_changed = False
                                        ends_on = None
                                        if request.POST.get("%s#ends_on" % price.id):
                                            ends_on = request.POST.get("%s#ends_on" % price.id) + " "
                                            ends_on += request.POST.get("%s#ends_on#hr" % price.id) + ":"
                                            ends_on += request.POST.get("%s#ends_on#min" % price.id)
                                            ends_on = datetime.datetime.strptime(ends_on,'%d-%m-%Y %H:%M')
                                            if not ends_on == price.start_time:
                                                ends_on_changed = True

                                        if offer_price_changed or cashback_amount_changed or starts_on_changed or ends_on_changed:
                                            price_info = {
                                                'price':price,
                                                'offer_price':request.POST.get("%s#offer_price" % price.id),
                                                'cashback_amount':request.POST.get("%s#cashback_amount" % price.id),
                                                'starts_on':starts_on,
                                                'ends_on':ends_on,
                                                'action':'Update',
                                                }
                                            update_prices.append(price_info)
                                            if_any_changes = True
                                        else:
                                            price_info = {
                                                'price':price,
                                                'action':'No Change',
                                                }
                                            update_prices.append(price_info)
                      
                        elif request.POST.get("confirm") and request.POST.get("confirm") == "Confirm":
                            flag = "confirmed"
                            current_list_price = request.POST.get("list_price")
                            new_list_price = request.POST.get("updated_list_price")
                            for price in all_prices:
                                if request.POST.get("%s#delete_price" % price.id):
                                    set_price_version(price, 'delete', request.user.username, datetime.datetime.now())
                                elif (current_list_price != new_list_price) or (request.POST.get("%s#offer_price" % price.id) and not Decimal(str(request.POST.get("%s#offer_price" % price.id))) == price.offer_price)or (request.POST.get("%s#offer_price" % price.id) and not Decimal(str(request.POST.get("%s#cashback_amount" % price.id))) == price.cashback_amount) or (request.POST.get("%s#starts_on" % price.id) and not request.POST.get("%s#starts_on" % price.id) == str(price.start_time)) or (request.POST.get("%s#ends_on" % price.id) and not request.POST.get("%s#starts_on" % price.id) == str(price.end_time)):
                                    new_offer_price = request.POST.get("%s#offer_price" % price.id)
                                    new_cashback_amount = request.POST.get("%s#cashback_amount" % price.id)
                                    
                                    new_starts_on = None
                                    if request.POST.get("%s#starts_on" % price.id):
                                        new_starts_on = request.POST.get("%s#starts_on" % price.id)
                                        new_starts_on = datetime.datetime.strptime(new_starts_on,'%Y-%m-%d %H:%M:%S')
                                        
                                    new_ends_on = None
                                    if request.POST.get("%s#ends_on" % price.id):
                                        new_ends_on = request.POST.get("%s#ends_on" % price.id)
                                        new_ends_on = datetime.datetime.strptime(new_ends_on,'%Y-%m-%d %H:%M:%S')


                                    set_price_version(price, 'update', request.user.username, datetime.datetime.now(), new_list_price, new_offer_price, new_cashback_amount, new_starts_on, new_ends_on)
            else:
                errors.append('No active price maintained for this article!!!')
                log.info('Rate chart does not exist either for sku=%s or article_id=%s' % (skuid, article_id))
    
    url = request.get_full_path()
    prices_dict = {
        'article_id':article_id,
        'sku':skuid,
        'pricelist_options':pricelist_options,
        'all_prices':all_prices,
        'list_price':list_price,
        'updated_list_price':updated_list_price,
        'searched_by':searched_by,
        'product':product,
        'product_image':product_image,
        'update_prices':update_prices,
        'delete_prices':delete_prices,
        'if_any_changes':if_any_changes,
        'is_pricing_tool_supported':is_pricing_tool_supported,
        'errors':errors,
        'flag':flag,
        }
    prices_dict['client_display_name']=client.name
    return render_to_response('prices/search_by_sku.html', prices_dict, context_instance=RequestContext(request))

