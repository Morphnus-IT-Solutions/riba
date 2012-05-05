<<<<<<< Updated upstream
import urllib, urllib2
from django.utils import simplejson
import logging
from django.conf import settings

log = logging.getLogger('request')

CATALOG_NAME = {
        'Future Bazaar': 'futurebazaar',
        'Ezone': 'ezoneonline',
        'Ezoneonline': 'ezoneonline',
        }

def create_request(payment_attempt, request):
    data = {'action':'create_new'}
    data['catalogName'] = CATALOG_NAME.get(request.client.client.name)
    log.info(request.client.client.name)
    data['ip'] = request.META.get('REMOTE_ADDR','')
    data['detectFraud'] = False
    data['storeBillingShipping'] = False
    data['useragent'] = request.META.get('HTTP_USER_AGENT','')
    data['acceptHeader'] = request.META.get('HTTP_ACCEPT','')
    domain = request.client.domain
    data['returnUrl'] = 'http://%s/orders/process_payment' % domain
    if request.path.startswith('/w/'):
        data['returnUrl'] = 'http://%s%s' % (domain, 
                request.path.replace('shipping','process_payment'))
    merchant_txn_no = payment_attempt.order.id
    if payment_attempt.order.reference_order_id:
        merchant_txn_no = payment_attempt.order.reference_order_id
    data['transactionId'] = payment_attempt.transaction_id 
    data['orderId'] = merchant_txn_no
    data['paymentAction'] = 'fulfil'
    data['paymentParam'] = payment_attempt.order.id
    data['payableAmount'] = '%s' % payment_attempt.amount
    data['amount'] = '%s' % payment_attempt.amount
    # data['amount'] = '1.00' #for test purpose use live card and check only for 1 re
    data['reqType'] = 'req.Sale'
    data['userId'] = payment_attempt.order.user.id
    data['gateway'] = payment_attempt.gateway
    data['emi_plan'] = request.POST.get('emi_plan')
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

=======
import urllib, urllib2
from django.utils import simplejson
import logging
from django.conf import settings

log = logging.getLogger('request')

def create_request(payment_attempt, request):
    data = {'action':'create_new'}
    data['ip'] = request.META.get('REMOTE_ADDR','')
    data['detectFraud'] = False
    data['storeBillingShipping'] = False
    data['useragent'] = request.META.get('HTTP_USER_AGENT','')
    data['acceptHeader'] = request.META.get('HTTP_ACCEPT','')
    domain = request.client.domain
    data['returnUrl'] = 'http://%s/orders/process_payment' % domain
    if request.path.startswith('/w/'):
        data['returnUrl'] = 'http://%s%s' % (domain, 
                request.path.replace('shipping','process_payment'))
    data['transactionId'] = payment_attempt.transaction_id
    data['orderId'] = payment_attempt.order.id
    data['paymentAction'] = 'fulfil'
    data['paymentParam'] = payment_attempt.order.id
    data['payableAmount'] = '%s' % payment_attempt.amount
    data['amount'] = '%s' % payment_attempt.amount
    data['reqType'] = 'req.Preauthorization'
    data['userId'] = payment_attempt.order.user.id
    data['gateway'] = payment_attempt.gateway

    url = settings.PG_SERVER_URL 
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
        return json.get('redirectUrl','')
    except IOError, e:
        log.exception('Error creating icici payment request %s' % repr(e))

>>>>>>> Stashed changes
