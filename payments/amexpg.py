import urllib, urllib2
from django.utils import simplejson
import logging
from django.conf import settings

log = logging.getLogger('request')

CATALOG_NAME = {
        'Future Bazaar': 'futurebazaar',
        'Ezone': 'ezoneonline',
        'Ezoneonline': 'ezoneonline',
        'chaupaati':'chaupaati'
        }

def create_request(request, payment_attempt, gateway):
    order = payment_attempt.order
    data = {'action':'create_new'}
    data['gateway'] = 'amex'
    data['catalogName'] = CATALOG_NAME.get(order.client.name, 'c')
    data['transaction_id'] = payment_attempt.transaction_id
    data['order_id'] = '%s' % order.get_id()
    data['amount'] = '%s' % int(round(payment_attempt.amount*100))
    data['locale'] = 'en' # Can be changed according to langauge
    data['protocol'] = 'ssl';
    data['card_type'] = 'Amex';
    data['return_url'] = 'http://%s/orders/process_payment_amex' % request.META['HTTP_HOST']
   
    url = settings.KHAZANA_SERVER_URL 
    return get_response(url , data)

def process_response(request, payment_attempt, params):
    order = payment_attempt.order
    data = {'action':'process_payment'}
    data['catalogName'] = CATALOG_NAME.get(order.client.name, 'futurebazaar')
    data['gateway'] = 'amex'
    data['amount'] = '%s' % int(round(payment_attempt.amount*100))
    data['use_proxy'] = 'false'
    if data['use_proxy'] == 'true':
        data['proxy_host'] = ''
        data['proxy_port'] = ''
    data['vpc_AVSResultCode'] = params.get('vpc_AVSResultCode');
    data['vpc_TransactionNo'] = params.get('vpc_TransactionNo');
    data['vpc_TxnResponseCode'] = params.get('vpc_TxnResponseCode');
    data['vpc_Message'] = params.get('vpc_Message');
    data['vpc_SecureHash'] = params.get('vpc_SecureHash');
    data['transaction_id'] = payment_attempt.transaction_id
    response_data = {}
    response_msg = ""

    for key in sorted(params):
        if key == 'vpc_SecureHash':
            continue
        response_msg = '%s%s' %(response_msg, params.get(key))

    data['response_msg'] = response_msg

    url = settings.KHAZANA_SERVER_URL 
    return get_response(url , data)

def get_response(url, data):
    try:
        headers = {'Content-Type':'application/json; charset=UTF-8'}
        data = simplejson.dumps(data)
        req = urllib2.Request(url, data, headers)
        res = urllib2.urlopen(req)
        res_data = res.read()
        log.info('Got response for create payment request %s' % res_data)
        json = simplejson.loads(res_data)
        return json
    except IOError, e:
        log.exception('Error creating icici payment request %s' % repr(e))

