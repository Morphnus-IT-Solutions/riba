import urllib, urllib2
import hashlib
from django.utils import simplejson
import logging
from django.conf import settings
from datetime import datetime,timedelta
from franchise.models import CommisionOn

log = logging.getLogger('request')

CATALOG_NAME = {
        'Future Bazaar': 'futurebazaar',
        'Ezone': 'ezoneonline',
        }

def create_request(request, **kwargs):
    log.info("Entered create_request")
    
    payment_attempt = kwargs.get('payment_attempt')
    order = kwargs.get('order')
    merchant_type_key = ''
    for order_item in order.orderitem_set.all():
        commission_ons = CommisionOn.objects.select_related('commision').filter(seller_rate_chart=order_item.seller_rate_chart)
        if commission_ons:
            commission_on = commission_ons[0]
            merchant_type_key = commission_on.commision.key
    
    data = {'orderid': payment_attempt.id,
            'productcost': '%s' % (payment_attempt.amount *100),#'100',
            'merchanttypekey':merchant_type_key,
            #'url_token':'%s' % request.call['url_token'],
            'reference_order_id': order.reference_order_id if order.reference_order_id else order.id,
            'redirect_url':'https://www.itzcash.com/payment/servlet/ITZPaymentServlet',
            }
    return data
    #url = settings.KHAZANA_SERVER_URL
    #return get_response(url,data)

def process_response(request, **kwargs):
    params = request.POST
    log.info('itz-cash process response data within itzpg.py: %s' % params)
    description = { '0'    : "Success",
                    '-3000' : 'Invalid Merchant Type Key',
                    '-3001' : 'Invalid Product Cost',
                    '-3002' : 'ItzCash Transaction Confirmation Error',
                    '-3004' : 'ItzCash Transaction Processing Error',
                    '-3005' : 'Unknown response code received from the Merchant in Processing URL response',
                    '-3006' : 'Invalid Response Format received from the Merchant in Processing URL response',
                    '-3009' : 'ItzCash Configuration Error',
                    '-3014' : 'Duplicate Order ID',
                    '-3020' : 'Data Validation Error',
                    '-3500' : 'ItzCash Transaction Check Error',
                   }
    
    response_code = params.get('responsecode')
    data = {'responseCode':response_code,
            'description':description.get(response_code),
            }
    return data

def save_franchise_commissions(request, **kwargs):
    pa = kwargs.get('payment_attempt')
    params = request.POST
    log.info('save_franchise_commissions within itzpg.py: params= %s' % params)

    if params.get('responsecode') == '0':        
        from orders.models import Order,OrderItem
        from web.views.franchise_views import calculate_commission_value_for_product, Franchise, FranchiseOrder, FranchiseCommissionOnItem
        
        order = pa.order
        
        if 'franchise' in request.session:
            franchise_order = FranchiseOrder()
            franchise_order.franchise = request.session['franchise'] 
            franchise_order.order = order 
            franchise_order.save()
            
            order_items = order.get_items_for_billing(request)
            franchise_order_franchise_total = 0
            franchise_order_network_total = 0
            
            for item in order_items:
                commission_val_dict = calculate_commission_value_for_product(request, item)
                log.info("commission_val_dict for %s --- %s" % ( item.item_title, commission_val_dict) )
                
                if commission_val_dict['total_commision'] and commission_val_dict['franchise_commision'] and commission_val_dict['network_commision']:
                    franchise_commission_on_item = FranchiseCommissionOnItem()
                    franchise_commission_on_item.franchise_order = franchise_order
                    franchise_commission_on_item.order_item = item
                    franchise_commission_on_item.franc_commission_amnt = commission_val_dict['franchise_commision']
                    franchise_commission_on_item.network_commission_amnt = commission_val_dict['network_commision']
                    franchise_commission_on_item.save()
                    
                    franchise_order_franchise_total = franchise_order_franchise_total+commission_val_dict['franchise_commision']
                    franchise_order_network_total = franchise_order_network_total + commission_val_dict['network_commision']
                else:
                    log.info('commission_val_dict in itzpg.py is empty ----- %s' % commission_val_dict)
            
            franchise_order.franc_commission_amnt = franchise_order_franchise_total
            franchise_order.network_commission_amnt = franchise_order_network_total
            franchise_order.booking_timestamp = datetime.now()
            franchise_order.save()
    return True

def get_response(url, data):
    try:
        headers = {'Content-Type':'application/json; charset=UTF-8'}
        data = simplejson.dumps(data)
        req = urllib2.Request(url, data, headers)
        proxy_support = urllib2.ProxyHandler({})
        opener = urllib2.build_opener(proxy_support)
        res = opener.open(req)
        res_data = res.read()
        log.info('Payment request data: %s' % data)
        log.info('Got response for create payback payment request: %s' % res_data)
        return simplejson.loads(res_data)
    except IOError, e:
        log.exception('Error creating payback payment request %s' % repr(e))

