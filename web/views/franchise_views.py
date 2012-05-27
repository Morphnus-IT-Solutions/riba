from django.conf import settings
from django.contrib.auth.models import User
from django.template import RequestContext
from django.contrib.auth import login as auth_login
from django.shortcuts import render_to_response
from django.db.models import Q,Count
from django.contrib.auth.decorators import login_required
from django.contrib import auth
from django.utils import simplejson
from django.template import Context, Template
from django.core.cache import cache
from django.http import Http404, HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect
import hashlib
import math
import logging
import math
from decimal import Decimal
from utils import utils
from utils.utils import is_franchise, getPaginationContext, get_profile_by_email_or_phone, get_or_create_user, save_excel_file, get_categories_by_id
from catalog.models import MegaDropDown, Category, Tag, SellerRateChart
from lists.models import List
from franchise.models import *
from orders.models import Order,OrderItem, DeliveryInfo
from web.views.user_views import validate_username_and_password
from web.views.sbf_views import search_browser_filter
log = logging.getLogger('request')
from datetime import datetime,timedelta
from utils import utils
from utils.utils import check_dates
from utils.solrutils import solr_search

def calculate_commission_value_per_product(request, product):
    #to calculate commission before placing order (take inputs from seller_rate_chart)
    all_commissions = {'total_commision': 0,
        'network_commision': 0, 'franchise_commision': 0}
    
    if 'is_franchise' in request.session and 'is_network' in request.session and 'network' in request.session:
        network = request.session['network']
        try:
            commision_on = CommisionOn.objects.get(network = network, seller_rate_chart__product=product)
            
            from web.templatetags.web_tags import get_price_info
            price = get_price_info(request, product.primary_rate_chart() , 'offer_price')
            total_commision = round(float(calulate_perc(price, commision_on.commision.percentage)), 2)
            all_commissions['total_commision'] = total_commision
    
            if 'network_share' in request.session:
                all_commissions['network_commision'] = round(float(calulate_perc(total_commision, request.session['network_share'])),2)
                all_commissions['franchise_commision'] = total_commision - all_commissions['network_commision']
            else:
                all_commissions['error'] = "network_share not set properly in session"
        except:
            all_commissions['error'] = '"%s" is not available for sale.' %product
    else:
        all_commissions['error'] = "is_network/is_franchise/network not set properly in session"
    return all_commissions

def calculate_commission_value_for_product(request, order_item):
    #calculate commission after placing order
    commission_val_dict = {}
    if request.session['is_franchise'] or request.session['is_network']:
        network = request.session['network']
        commission_val_dict['network'] = network
        if request.session['is_franchise']:
            commission_val_dict['franchise'] = request.session['franchise']
        try:
            commision_on = CommisionOn.objects.select_related('seller_rate_chart', 'commision').get(network = network, seller_rate_chart = order_item.seller_rate_chart)
            price = order_item.sale_price
            total_commision = round(float(calulate_perc(price, commision_on.commision.percentage) ),2) #* order_item.qty
            commission_val_dict['total_commision'] = total_commision
            commission_val_dict['merchant_key_and_perc'] = commision_on.commision

            network_commision = round(float(calulate_perc(total_commision, request.session['network_share']) ),2) #* order_item.qty
            franchise_commision = total_commision - network_commision
            
            commission_val_dict['network_commision'] = network_commision
            commission_val_dict['franchise_commision'] = franchise_commision
        except:
            commission_val_dict['error'] = 'No commission set for this product'
            commission_val_dict['total_commision'] = 0
            commission_val_dict['network_commision'] = 0
            commission_val_dict['franchise_commision'] = 0
    else:
        commission_val_dict['error'] = 'ICW Session lost. Please try again.'
    return commission_val_dict


def calulate_perc(num , perc):
    num = str(num).replace(',','')
    return  (float(num) * float(perc)) / 100

def itz_homepage(request):
    error = ''
    itz_offer = {}
    hero_deal = {}
    mega_menu_categories = ''
    _client = request.client.client
    
    net_details = save_franc_network_in_dict(request)
    if not 'is_network' in net_details or not 'is_franchise' in net_details or net_details['is_network']:
        return HttpResponseRedirect('/accounts/login/')

    home_page_ctxt_key = 'itz_homepage#%s' % (_client.id)
    home_page_context = cache.get(home_page_ctxt_key)
    
    if not home_page_context:
        tag = Tag.objects.filter(tag='itz')
        if tag:
            tag = tag[0]
            q = 'tag_id:%s' % tag.id
            params = {}
            params['rows'] = 1000
            itz_solr_result = solr_search(q, fields='id', **params)
            #itz_categories_solr = search_browser_filter(request, **{'tag_ids' : tag.id })
        else:
            error = "No Itz tag found"
            home_page_context = {'error':error,}
        if error or itz_solr_result.numFound == 0:
            error = "No Itz products found. Add products from admin site."
            home_page_context = {'error':error,}
        else:
            itz_product_ids = [res['id'] for res in itz_solr_result.results]
            itz_seller_charts = SellerRateChart.objects.filter(product__in=itz_product_ids)
            
            mega_menu_categories = MegaDropDown.objects.select_related("category").filter(type="menu_level2_category", client=_client).order_by('sort_order')
            for cat in mega_menu_categories:
                itz_offer[cat.category.id] = {}
                temp_dict = search_browser_filter(request,**{ 'category': cat.category })
                if 'total_results' in temp_dict:
                    itz_offer[cat.category.id]['total_results'] = temp_dict['total_results']
                if 'filter_form' in temp_dict:
                    itz_offer[cat.category.id]['gmin'] = temp_dict['filter_form'].gmin
                if 'products' in temp_dict:
                    itz_offer[cat.category.id]['products'] = temp_dict['products']
            
            from dealprops.models import DailyDeal, DailyDealImage
            hero_deals = DailyDeal.objects.select_related('id', 'type').filter(status='published', starts_on__lte=datetime.now(),ends_on__gte=datetime.now(), client=_client, type = 'hero_deal').order_by('-starts_on')[:1]
            
            if hero_deals:
                hero_deal_obj = hero_deals[0]
                
                if hero_deal_obj:
                    hero_deal_rate_chart = None
                    daily_deal_products = hero_deal_obj.dailydealproduct_set.all()
                    
                    if daily_deal_products:
                        daily_deal_product = daily_deal_products[0]
                        hero_deal_rate_chart = daily_deal_product.product.primary_rate_chart()
                        
                        if hero_deal_rate_chart in itz_seller_charts:
                            hero_deal['deal'] = hero_deal_obj
                            hero_deal['url'] = hero_deal_rate_chart.product.url()
                            
                            try:
                                hero_deal_image = DailyDealImage.objects.get(daily_deal=hero_deal_obj)
                            except DailyDealImage.MultipleObjectsReturned:
                                hero_deal_image = DailyDealImage.objects.filter(daily_deal=hero_deal_obj).order_by('order')[0]
                            except DailyDealImage.DoesNotExist:
                                pass
                            if hero_deal_image:
                                hero_deal['main_banner'] = hero_deal_image.banner
            home_page_context = {
                                    'net_details':net_details,
                                    'error':error,
                                    'itz_offer':itz_offer,
                                    'mega_menu_categories':mega_menu_categories,
                                    'hero_deal':hero_deal,
                                }
            cache.set(home_page_ctxt_key, home_page_context, 1800)

    home_page_context['request'] = request
    return render_to_response('itz_homepage.html', home_page_context,
        context_instance=RequestContext(request))
    
def switch_franchise_permissions(request, franchise_id):
    error = ''
    is_active = 'no_action'
    if 'req_status' in request.GET:
        req_status = request.GET.get('req_status')
        if utils.is_franchise(request) and 'is_network' in request.session and request.session['is_network'] and 'network' in request.session :
            try:
                franchise = Franchise.objects.select_related('franchise').get(id=franchise_id, network = request.session['network'])
                
                if franchise.is_active and req_status == 'deactivate':
                    franchise = Franchise.objects.filter(id=franchise_id).update(is_active= False)
                    is_active = 'deactivated'
                elif not franchise.is_active and req_status == 'activate':
                    franchise = Franchise.objects.filter(id=franchise_id).update(is_active= True)
                    is_active = 'activated'
            except:
                error= 'No such ICW exists'
        else:
            error= 'You do not have an access'
    else:
        error = 'Not sure whether to activate or deactivate. Please try later.'

    if error:
        ajax_response = dict(status='failed', error=error)
    else:
        ajax_response = dict(status='success', is_active=is_active)
    return HttpResponse(simplejson.dumps(ajax_response))
    
def itz_order_details(request, order_id):
    net_details = save_franc_network_in_dict(request)
    error = ''
    try:
        order = Order.objects.get(id=order_id,client=request.client.client)
    except Order.DoesNotExist:
        raise Http404
    
    franchise_commission_on_item = FranchiseCommissionOnItem.objects.select_related('franchise_order', 'order_item','franchise').filter(order_item__order__id=order_id)
    
    try:
        delivery_info = DeliveryInfo.objects.get(order=order)
    except DeliveryInfo.DoesNotExist:
        delivery_info = ''

    return render_to_response('itz_order_details.html',
        {
            'request':request,
            'delivery_info':delivery_info,
            'order' :order,
            'franchise_commission_on_item':franchise_commission_on_item,
            'net_details':net_details,
            'error':error,
        },
        context_instance=RequestContext(request))

@login_required
def itz_account(request):
    error = ''
    network_commision = ''
    franchise_commision = ''
    order_id = ''
    sort_option ='time'
    asc_or_desc = 'desc'
    date_range = False
    from_date = ''
    to_date = ''
    pagination = {}
    items_per_page = 10
    search_trend= ''
    show_excel_option = False
    save_excel = request.GET.get('excel', False)
    
    net_details = save_franc_network_in_dict(request)
    
    if not 'is_network' in net_details or not 'is_franchise' in net_details:
        return HttpResponseRedirect('/accounts/login/')
    elif net_details['is_network']:
        show_excel_option = True
    
    if 'order_id' in request.POST:
        order_id = request.POST['order_id'].strip()
        if not order_id or order_id =='Enter Order Id':
            error = 'Please enter order id'
        elif net_details['is_network'] or net_details['is_franchise'] or net_details['network']:
            try:
                franchise_commision = FranchiseOrder.objects.select_related('user', 'order','franchise').filter(order__reference_order_id=order_id).order_by('-order__timestamp')
                if not franchise_commision:
                    error = 'No order found with order id "%s"'%order_id
                if net_details['is_network']:
                    network_commision = franchise_commision
            except:
                pass
    else:
        if ('from' in request.GET and 'to' in request.GET) or 'search_trend' in request.GET:
            date_range = True
            sort_by_text = 'order__timestamp'
            asc_or_desc_sign = '-'
            asc_or_desc = 'desc'
            if 'search_trend' in request.GET:
                search_trend = request.GET.get('search_trend')
                if search_trend == 'day':
                    from_date, to_date = datetime.strptime( str(datetime.now().date()),'%Y-%m-%d' ), datetime.strptime( str(datetime.now().date()),'%Y-%m-%d' )
                elif search_trend == 'week':
                    from_date, to_date = datetime.strptime( str(datetime.now().date()),'%Y-%m-%d' )+timedelta(days=-7), datetime.strptime( str(datetime.now().date()),'%Y-%m-%d' )
                elif search_trend == 'mtd':
                    first_day = str(datetime.now().date()).replace( str(datetime.now().date())[-2:] ,'01')
                    from_date, to_date = datetime.strptime( first_day,'%Y-%m-%d' ), datetime.strptime( str(datetime.now().date()),'%Y-%m-%d' )

            elif 'from' in request.GET and 'to' in request.GET:
                if not request.GET.get('from') or not request.GET.get('to'):
                    error = 'Please select date range correctly'
                try:
                    from_date, to_date = datetime.strptime(request.GET.get('from','time'),'%d %b %Y'), datetime.strptime(request.GET.get('to','time'),'%d %b %Y')
                except:
                    date_range = False
            
        if not date_range and 'sort_option' in request.GET:
            sort_option = request.GET.get('sort_option','time')
            if sort_option == 'time':
                sort_by_text = 'order__timestamp'
            elif sort_option == 'order_value':
                sort_by_text = 'order__payable_amount'
            elif sort_option == 'icw_name':
                sort_by_text = 'franchise__user__email'
            elif sort_option == 'customer':
                sort_by_text = 'order__user__email'            
            elif sort_option == 'commission':
                if net_details['is_franchise']:
                    sort_by_text = 'franc_commission_amnt'
                elif net_details['is_network']:
                    sort_by_text = 'network_commission_amnt'
            elif sort_option == 'status':
                sort_by_text = 'order__state'
            else:
                sort_by_text = 'order__timestamp'
        else:
            sort_by_text = 'order__timestamp'
        
        if not date_range and 'asc_or_desc' in request.GET:
            asc_or_desc = request.GET.get('asc_or_desc','desc')
            if asc_or_desc == 'asc':
                asc_or_desc_sign = ''
            else:
                asc_or_desc_sign = '-'
        else:
            asc_or_desc_sign = '-'
        
        if net_details['is_network'] or net_details['is_franchise'] or net_details['network']:
            if date_range:
                if net_details['is_network']:
                    network_francs = Franchise.objects.filter(network = net_details['network'])
                    network_commision = FranchiseOrder.objects.filter(franchise__in=( network_francs ), order__timestamp__lte=to_date+timedelta(days=1), order__timestamp__gte=from_date)
                    total_results = network_commision.count()
                elif net_details['is_franchise']:
                    franchise_commision = FranchiseOrder.objects.filter(franchise=net_details['franchise'], order__timestamp__lte=to_date+timedelta(days=1), order__timestamp__gte=from_date)
                    total_results = franchise_commision.count()
                    
            elif net_details['is_network']:
                network_francs = Franchise.objects.filter(network = net_details['network'])
                network_commision = FranchiseOrder.objects.filter(franchise__in=( network_francs )).order_by('%s%s'%(asc_or_desc_sign, sort_by_text))
                total_results = network_commision.count()
            elif net_details['is_franchise']:
                franchise_commision = FranchiseOrder.objects.filter(franchise=net_details['franchise']).order_by('%s%s'%(asc_or_desc_sign, sort_by_text))
                total_results = franchise_commision.count()
            
            if total_results and total_results > 0 and not save_excel:
                try:
                    page_no = request.GET.get('page',1)
                    page_no = int(page_no)
                    
                    total_pages = int(math.ceil(Decimal(total_results)/Decimal(items_per_page)))
                    pagination = utils.getPaginationContext(page_no, total_pages, '')
                    startOrderIndex = (page_no-1) * items_per_page
                    
                    if date_range:
                        if net_details['is_network']:
                            network_commision = FranchiseOrder.objects.select_related('user', 'order', 'franchise','network').filter(franchise__in=( network_francs ), order__timestamp__lte=to_date+timedelta(days=1), order__timestamp__gte=from_date).order_by('%s%s'%(asc_or_desc_sign, sort_by_text))[startOrderIndex:startOrderIndex+items_per_page]
                        elif net_details['is_franchise']:
                            franchise_commision = FranchiseOrder.objects.select_related('user', 'order','franchise').filter(franchise=net_details['franchise'], order__timestamp__lte=to_date+timedelta(days=1), order__timestamp__gte=from_date).order_by('%s%s'%(asc_or_desc_sign, sort_by_text))[startOrderIndex:startOrderIndex+items_per_page]
                    
                    elif net_details['is_network']:
                        network_commision = FranchiseOrder.objects.select_related('user', 'order', 'franchise','network').filter(franchise__in=( network_francs )).order_by('%s%s'%(asc_or_desc_sign, sort_by_text))[startOrderIndex:startOrderIndex+items_per_page]
                    elif net_details['is_franchise']:
                        franchise_commision = FranchiseOrder.objects.select_related('user', 'order','franchise').filter(franchise=net_details['franchise']).order_by('%s%s'%(asc_or_desc_sign, sort_by_text))[startOrderIndex:startOrderIndex+items_per_page]
                except Exception,e:
                    log.exception('Exception while rendering order history: %s' % repr(e))
                    pass
            elif save_excel:
                pass
            else:
                error= 'No orders placed'
        else:
            franchise_commision = ''
            network_commision = ''
            error = "Session parameters not set. Please login again."
    
    if 'is_franchise' in net_details and net_details['is_franchise'] and franchise_commision:
        try:
            if franchise_commision[0].franchise.role == 'fb':
                show_excel_option = True
        except Franchise.DoesNotExist:
            pass
    # export this report as excel
    if save_excel and not error:
        excel_data = []
        if net_details['is_network']:
            excel_header = ['ICW dealer id', 'ICW Code', 'ICW Email id', 'ItzCash Transaction Id', 'Order id(future Bazaar)',\
                            'Product Name', 'Transaction Date','Gross Amount', 'Amount Collected', 'Total Comm.','ICW Comm.', \
                            'ItzCash Comm.', 'TDS charged','Customer Name', 'Mobile No.', 'Address of the customer', 'Delivery Satus']
            order_excel_details = network_commision
        elif net_details['is_franchise']:
            excel_header = ['ItzCash Transaction Id', 'Order id(future Bazaar)',\
                            'Product Name', 'Transaction Date','Gross Amount', 'Amount Collected', 'ICW Comm.',\
                            'TDS charged','Customer Name', 'Mobile No.', 'Address of the customer', 'Delivery Satus']
            order_excel_details = franchise_commision
        from payments.models import PaymentAttempt
        for itz_order in order_excel_details:
            item = itz_order.order.orderitem_set.all()
            
            itzCash_transaction_id = ''
            pa = PaymentAttempt.objects.filter(order = itz_order.order).order_by('-modified_on')
            itzCash_transaction_id = pa[0].transaction_id
            
            if net_details['is_network']:
                total_commission =  float(itz_order.franc_commission_amnt) + float(itz_order.network_commission_amnt)
                tds = round(float(calulate_perc(total_commission, 10 )),2)
                total_collected = float(itz_order.order.payable_amount) - float(total_commission)
            elif net_details['is_franchise']:
                total_commission =  float(itz_order.franc_commission_amnt) + float(itz_order.network_commission_amnt)
                tds = round(float(calulate_perc(itz_order.franc_commission_amnt, 10 )),2)
                total_collected = float(itz_order.order.payable_amount) - float(itz_order.franc_commission_amnt)
            dinfo = DeliveryInfo.objects.filter(order=itz_order.order)
            #if dinfo and dinfo.address:
            if net_details['is_network']:
                excel_data.append([itz_order.franchise.dealer_id, itz_order.franchise.dealer_code, itz_order.franchise.user.username,\
                                   itzCash_transaction_id, itz_order.order.get_id(), item[0].seller_rate_chart.product, itz_order.order.timestamp,\
                                   itz_order.order.payable_amount, total_collected, total_commission, itz_order.franc_commission_amnt,\
                                   itz_order.network_commission_amnt, tds, dinfo[0].address.first_name+ ' ' + dinfo[0].address.last_name,\
                                   dinfo[0].address.phone, dinfo[0].address.address+ ' '+ \
                                   itz_order.order.get_delivery_state() + ' '+ dinfo[0].address.pincode, itz_order.order.support_state ])
                                   #itz_order.order.get_delivery_city()+ ' ' +
            elif net_details['is_franchise']:
                excel_data.append([itzCash_transaction_id, itz_order.order.get_id(), item[0].seller_rate_chart.product, itz_order.order.timestamp,\
                                   itz_order.order.payable_amount, total_collected, itz_order.franc_commission_amnt,\
                                   tds, dinfo[0].address.first_name+ ' ' + dinfo[0].address.last_name, dinfo[0].address.phone,\
                                   dinfo[0].address.address+' '+itz_order.order.get_delivery_state() + ' '+ \
                                   dinfo[0].address.pincode, itz_order.order.support_state ]) #itz_order.order.get_delivery_city()+' '+
        return save_excel_file(excel_header, excel_data)
    
    return render_to_response('itz_account.html',
        {
            'request':request,
            'pagination':pagination,
            'net_details':net_details,
            'network_commision':network_commision,
            'franchise_commision':franchise_commision,
            'show_excel_option':show_excel_option,
            'order_id':order_id,
            'sort_option':sort_option,
            'asc_or_desc':asc_or_desc,
            'error':error,
            'tab' : 1,
            'from_date':from_date,
            'to_date':to_date,
            'search_trend' :search_trend,
        },
        context_instance=RequestContext(request))

def icw_list(request):
    franchise_email = ''
    franchise_list = ''
    franc_pagination = ''
    error = ''
    start_sr_number = ''
    franc_list_per_page = 10
    
    net_details = save_franc_network_in_dict(request)
    
    if 'is_network' in net_details and net_details['is_network']:
        if 'franchise_email' in request.POST:
            franchise_email = request.POST['franchise_email']
            franchise_list = Franchise.objects.select_related('user','network').filter(user__email=franchise_email)
            if not franchise_list:
                franchise_list = Franchise.objects.select_related('user','network').filter(user__username=franchise_email)
                if not franchise_list:
                    error = 'ICW not found'
        else:
            franc_list_page_no = request.GET.get('page',1)
            franc_list_page_no = int(franc_list_page_no)
            network_francs_total = Franchise.objects.filter(network=net_details['network'])
            total_francs = network_francs_total.count()
            total_pages_for_franc = int(math.ceil(Decimal(total_francs)/Decimal(franc_list_per_page)))
            franc_pagination = utils.getPaginationContext(franc_list_page_no, total_pages_for_franc, '')        
            startOrderIndex_franc = (franc_list_page_no-1) * franc_list_per_page
            franchise_list = Franchise.objects.select_related('network').filter(network=net_details['network'])[startOrderIndex_franc : startOrderIndex_franc + franc_list_per_page]
            if not franchise_list:
                error = 'Franchises not found'
            else:
                start_sr_number = franc_list_per_page * (franc_list_page_no-1)
    else:
        return HttpResponseRedirect('/accounts/login/')
    return render_to_response('performance/icw_list.html',
        {
            'request':request,
            'error' : error,
            'net_details':net_details,
            'franchise_email':franchise_email,
            'franchise_list':franchise_list,
            'pagination':franc_pagination,
            'start_sr_number':start_sr_number,
            'tab':2,
        },
        context_instance=RequestContext(request))

def icw_add(request):
    net_details = save_franc_network_in_dict(request)
    if 'is_network' in net_details and not net_details['is_network']:
        return HttpResponseRedirect('/accounts/login/')
    return render_to_response('performance/icw_add.html',
        {
            'request':request,
            'net_details':net_details,
            'tab':3,
        },
        context_instance=RequestContext(request))

def icw_catalog(request):
    net_details = save_franc_network_in_dict(request)
    commision_on= []
    pagination = {}
    sku = ''
    error = ''
    show_add_product = False
    items_per_page = 10
    
    if 'is_franchise' in net_details and net_details['is_franchise']:
        try:
            franc_role = Franchise.objects.get(id = net_details['franchise'].id)
            if franc_role.role == 'fb':
                show_add_product = True
        except Franchise.DoesNotExist:
            pass
    
    if 'is_network' in net_details and 'is_franchise' in net_details and (net_details['is_network'] or net_details['is_franchise']):
        if 'sku' in request.POST:
            sku = request.POST['sku'].strip()
            if not sku:
                error = 'Please enter order id'
            else:
                commision_on = CommisionOn.objects.select_related('seller_rate_chart', 'product', 'commision').filter(network = net_details['network'], seller_rate_chart__sku = sku)
                if not commision_on:
                    error = 'Product not found with SKU "%s"'%sku
        else:
            try:
                commision_on = CommisionOn.objects.filter(network = net_details['network'] )
                total_results = commision_on.count()
                
                if total_results and total_results > 0:
                    try:
                        page_no = request.GET.get('page',1)
                        page_no = int(page_no)
                        total_pages = int(math.ceil(Decimal(total_results)/Decimal(items_per_page)))
                        pagination = utils.getPaginationContext(page_no, total_pages, '')
                        startOrderIndex = (page_no-1) * items_per_page
                        commision_on = CommisionOn.objects.select_related('seller_rate_chart', 'product', 'commision').filter(network = net_details['network'])[startOrderIndex : startOrderIndex + items_per_page]
                    except Exception,e:
                        log.exception('Exception while itz product history: %s' % repr(e))
                        pass
                else:
                    error = 'No Itz products found'
            except:
                error = 'Something went wrong in getting itz products '
        
        tag_hero = Tag.objects.filter(tag="itz_hero")
        if tag_hero:
            tag_hero = tag_hero[0]
        from utils.solrutils import solr_search
        params = {'rows':200}
        q = 'tag_id:%s' % tag_hero.id
        solr_result = solr_search(q, **params)
        prod_ids_in_solr = [int(doc['id']) for doc in solr_result.results]
        
    else:
        return HttpResponseRedirect('/accounts/login/')
    return render_to_response('performance/icw_catalog.html',
        {
            'request':request,
            'error':error,
            'prod_ids_in_solr':prod_ids_in_solr,
            'show_add_product' : show_add_product,
            'pagination':pagination,
            'net_details':net_details,
            'commision_on':commision_on,
            'sku':sku,
            'tab':4,
        },
        context_instance=RequestContext(request))

def save_franc_network_in_dict(request):
    if 'is_network' in request.session and 'is_franchise' in request.session and 'network' in request.session and 'network_share' in request.session:
        if request.session['is_franchise'] and 'franchise' in request.session:
            net_details = {
                           'is_network': request.session['is_network'],
                           'network' : request.session['network'],
                           'franchise' : request.session['franchise'],
                           'is_franchise': request.session['is_franchise'],
                           'network_share' : request.session['network_share']
                           }
        elif request.session['is_network']:
            net_details = {
                           'is_network': request.session['is_network'],
                           'network' : request.session['network'],
                           'is_franchise': request.session['is_franchise'],
                           'network_share' : request.session['network_share']
                           }
        else:
            return HttpResponseRedirect('/accounts/login/')
        return net_details
    else:
        return HttpResponseRedirect('/accounts/login/')
    
def is_user_entry(username):
    try:
        usr = User.objects.get(Q(username = username) | Q(email = username))
        return True
    except User.DoesNotExist:
        return False
 
def network_or_franchise_email(email):
    try:
        e = Network.objects.get(user__email = email)
        return True
    except Network.DoesNotExist:
        try:
            p = Franchise.objects.get(user__email = email)
            return True
        except Franchise.DoesNotExist:
            return False

def franchise_signup(request):
    params = request.POST
    username = params.get('username','').strip()
    dealer_id = params.get('dealer_id','').strip()
    dealer_code = params.get('dealer_code','').strip()
    password = params.get('password','').strip()
    error = ''
    
    if not utils.is_valid_email(username):
        error = 'Enter a valid e-mail address.'
    else:
        error = validate_username_and_password(username, password, password)
    
    if not error:
        profile = utils.get_profile_by_email_or_phone(username)
        if profile:
            error = 'Sorry, "%s" profile is not available' % username
            user, profile = utils.get_or_create_user(username,'',password)
            print "user--->",user.id,", profile--->",profile.id
            
        else:
            if network_or_franchise_email(username):
                error = "Network or ICW related to this email already exists"
            else:
                if is_user_entry(username):
                    error = "Email already exists in the database"
                else:
                    try:
                        logged_in_network = Network.objects.get(user=request.user)
                        #Some dcode and d-ids already on production which are same. Hence filter and not equal to 0 check
                        franchise_did = Franchise.objects.filter(network=logged_in_network.parent_network, dealer_id = dealer_id)
                        if franchise_did.count() != 0:
                            error = 'Dealer-ID already exists'
                        if not error:
                            franchise_dcode = Franchise.objects.filter(network=logged_in_network.parent_network, dealer_code = dealer_code)
                            if franchise_dcode.count() != 0:
                                error = 'Dealer-CODE already exists'
                    except Network.DoesNotExist:
                        error = 'Please logout and login again.'
    if not error:
        #Add User in first auth-users   / profiles/ email/ phone/
        user, profile = utils.get_or_create_user(username,'',password)
        franchise = Franchise(user=user,network=logged_in_network.parent_network,role='agent', dealer_id = dealer_id, dealer_code = dealer_code)
        franchise.save()
        message = "ICW '%s' added under '%s' network." % (user, logged_in_network)
    
    if error:
        response = dict(status='failed', html=error)
    else:
        response = dict(status='success', html = message)
    return HttpResponse(simplejson.dumps(response))

def icw_add_product(request):
    merchant_type_key = ''
    net_details = save_franc_network_in_dict(request)
    try:
        merchant_type_key = MerchantTypeKey.objects.filter(network = net_details['network']).order_by('percentage')
    except:
        pass 
    
    return render_to_response('performance/icw_add_product.html',
        {
            'request':request,
            'net_details':net_details,
            'merchant_type_key':merchant_type_key,
            'tab':3,
        },
        context_instance=RequestContext(request))

def product_addition_result(request):
    params = request.POST
    key = params.get('key','').strip()
    sku = params.get('sku','').strip()
    error = ''
    net_details = save_franc_network_in_dict(request)
    if 'is_franchise' in net_details and net_details['is_franchise'] and net_details['network']:
        try:
            from catalog.models import SellerRateChart 
            src = SellerRateChart.objects.get(sku=sku, seller__client= 5)
            try:
                commision_on = CommisionOn.objects.get(network = net_details['network'], seller_rate_chart = src)
                error = "'%s' already added for your network" %src.product
            except:
                try:
                    merchant_type_key = MerchantTypeKey.objects.get(key = key)
                except Exception,e:                    
                    error = repr(e)
        except Exception,e:
            error = "SellerRateChart matching query does not exist."
    else:
        return HttpResponseRedirect('/accounts/login/')
    
    if not error:
        commission_on = CommisionOn()
        commission_on.network = net_details['network'] 
        commission_on.commision = merchant_type_key 
        commission_on.seller_rate_chart = src
        commission_on.save()
        message = "'%s' added under ITZ products." % src.product
        response = dict(status='success', html = message)
    else:
        response = dict(status='failed', html = error)
    
    return HttpResponse(simplejson.dumps(response))

def del_product(request, commission_on_id):
    error =''
    is_removed = False    
    net_details = save_franc_network_in_dict(request)
    
    try:
        commision_on = CommisionOn.objects.get(network = net_details['network'], id = commission_on_id).delete()
        is_removed = True
        ajax_response = dict(status='success', is_removed = is_removed)
    except:
        error = 'Error while deleting ITZ product from catalog. Try later or refresh the page.'
        ajax_response = dict(status='failed', error=error)
    
    return HttpResponse(simplejson.dumps(ajax_response))

def mark_itz_cat_hero(request, commission_on_id):
    error = ''
    is_marked_hero = False
    tag_hero_name = 'itz_hero'
    list_type = 'itz_offer'
    
    net_details = save_franc_network_in_dict(request)

    tag_hero = Tag.objects.filter(tag=tag_hero_name)
    if tag_hero:
        tag_hero = tag_hero[0]
    else:
        error = "No ITZ hero tag found"
    
    if not error:
        try:
            commision_on = CommisionOn.objects.get(network = net_details['network'], id = commission_on_id)
            this_prod_id = int(commision_on.seller_rate_chart.product.id)
            
            from catalog.models import ProductTags, Product
            try:
                pt = ProductTags.objects.get(type = list_type, product = commision_on.seller_rate_chart.product, tag=tag_hero)
                is_marked_hero = True
            except ProductTags.DoesNotExist:
                pt = ProductTags(type = list_type, product = commision_on.seller_rate_chart.product, tag=tag_hero)
                pt.save()
                is_marked_hero = True
            
                commision_on.seller_rate_chart.product.update_solr_index()
                parent_cat_dict = get_categories_by_id(request, [str(commision_on.seller_rate_chart.product.id)])
                parent_c1_id = parent_cat_dict['c1_categories'][0].id
            
                from utils.solrutils import solr_search
                params = {'rows':200}
                q = 'tag_id:%s AND category_id:%s' % (tag_hero.id, parent_c1_id)
                
                try:
                    solr_result = solr_search(q, **params)
                    prod_ids_in_solr = [int(doc['id']) for doc in solr_result.results]
                    if this_prod_id in prod_ids_in_solr:
                        prod_ids_in_solr.remove(this_prod_id)
                    
                    for prod in prod_ids_in_solr:
                        try:
                            pt = ProductTags.objects.get(type = list_type, product = prod, tag=tag_hero).delete()
                        except:
                            pass
                        try:
                            product = Product.objects.get(id = prod)
                            product.update_solr_index()
                        except:
                            pass
                    
                except:
                    error = "Solr query failed. Query:",q
        except:
            error = 'Itz product not found'
    
    if not error:
        ajax_response = dict(status='success', is_marked_hero = is_marked_hero, error=error)
    else:
        ajax_response = dict(status='failed', error=error)
    
    return HttpResponse(simplejson.dumps(ajax_response))
