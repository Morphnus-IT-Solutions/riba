import urllib, urllib2
import hashlib
from django.utils import simplejson
import logging
from django.conf import settings
import time
from datetime import datetime

log = logging.getLogger('request')

CATALOG_NAME = {
        'Future Bazaar': 'futurebazaar',
        'Ezone': 'ezoneonline',
        }
def create_request(payment_attempt, request):
    log.info("Entered create_request")
    data = {'action':'create_new',
            'gateway': 'citi-emi',
            'orderId': payment_attempt.order.reference_order_id,
            'catalogName': CATALOG_NAME.get(request.client.client.name),
            'transactionId': payment_attempt.transaction_id,
            'amount': payment_attempt.payable_amount,
            'emi_plan': request.POST.get('emi_plan', '3'),
            'trace_no': payment_attempt.get_citibanktracenumber(),
            }
    url = settings.KHAZANA_SERVER_URL
    return get_response(url,data)

def process_response(payment_attempt, response):
    dt = payment_attempt.created_on
    utc_struct_time = time.gmtime(time.mktime(dt.timetuple()))
    utc_dt = datetime.fromtimestamp(time.mktime(utc_struct_time))
    txn_date_time = utc_dt.strftime("%d%m%Y%H%M%S")
    data = {'action':'process_payment', 
            'CititoMall': response.POST.get('CititoMall'),
            'gateway': payment_attempt.gateway,
            'txn_date_time': txn_date_time, 
            'emi_plan':payment_attempt.emi_plan,
            'catalogName':CATALOG_NAME.get(payment_attempt.order.client)}
    url = settings.KHAZANA_SERVER_URL 
    return get_response(url , data)

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
        log.info('Got response for create payment request %s' % res_data)
        json = simplejson.loads(res_data)
        return json
        #return json.get('redirectUrl','')
    except IOError, e:
        log.exception('Error creating citi payment request %s' % repr(e))

