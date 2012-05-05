import urllib, urllib2
from django.utils import simplejson
import logging
from django.conf import settings

log = logging.getLogger('request')

def create_request(request, **kwargs):
    card_details = kwargs.get('card_details')
    payment_attempt = kwargs.get('payment_attempt')
    data = {'action':'create_new'}
    data['ip'] = request.META.get('REMOTE_ADDR','')
    data['useragent'] = request.META.get('HTTP_USER_AGENT','')
    data['acceptHeader'] = request.META.get('HTTP_ACCEPT','')
    data['returnUrl'] = 'https://%s/orders/process_payment_hdfc' % request.client.domain 
    data['transactionId'] = payment_attempt.transaction_id
    data['orderId'] = payment_attempt.order.reference_order_id if payment_attempt.order.reference_order_id else payment_attempt.order.id
    data['paymentAction'] = 'fulfil'
    data['paymentParam'] = payment_attempt.order.id
    data['payableAmount'] = '%s' % payment_attempt.amount
    data['amount'] = '%s' % payment_attempt.amount
    data['reqType'] = 'req.Preauthorization'
    data['userId'] = payment_attempt.order.user.id
    data['gateway'] = payment_attempt.gateway
    data['name'] = card_details.get('name_on_card')
    data['currcd'] = '356'
    data['expmm'] = card_details.get('exp_month')
    data['expyy'] = card_details.get('exp_year')
    data['pan'] = card_details.get('card_no')
    data['cvv'] = card_details.get('cvv')
    data['pg_action'] = "1" #Purchase
    #"4" #Authorization
    if data['gateway'] == 'hdfc-emi':
        data['emi_plan'] = payment_attempt.emi_plan

    url = settings.PG_SERVER_URL 
    return get_response(url , data)

def process_response(payment_attempt,info):
    data = {'action':'process_payment'}
    data['gateway'] = 'hdfc-card'
    if payment_attempt.emi_plan:
        data['gateway'] = 'hdfc-emi'
    data['emi_plan'] = payment_attempt.emi_plan
    data['MD'] = info['MD']
    data['PaRes'] = info['PaRes']
    url = settings.PG_SERVER_URL 
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
        log.exception('Error creating hdfc payment request %s' % repr(e))
