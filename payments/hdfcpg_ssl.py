import urllib, urllib2
from django.utils import simplejson
import logging
from django.conf import settings

log = logging.getLogger('request')

def create_request(request, **kwargs):
    data = {'action':'create_new', 
            'catalog': 'futurebazaar'} 
    payment_attempt = kwargs.get('payment_attempt')
    order = payment_attempt.order
    gateway = 'hdfc-card'
    if payment_attempt.emi_plan:
        gateway = 'hdfc-emi'
        data['emi_plan'] = payment_attempt.emi_plan
    data['gateway'] = gateway
    data['currcd'] = "356"
    data['langauge_id'] = "USA"
    data['response_url'] = 'https://%s/orders/process_payment_hdfc' % request.client.domain 
    data['error_url'] = 'https://%s/orders/process_payment_hdfc' % request.client.domain 
    #data['error_url'] = 'http://117.205.17.191:8080/Example/FailedTRAN.jsp' 
    #data['response_url'] = 'http://117.205.17.191:8080/Example/GetHandleRESponse.jsp' 
    data['udf1'] = order.reference_order_id if order.reference_order_id else order.id
    data['udf2'] = '%s' % payment_attempt.id
    data['udf3'] = '%s' % order.user.id
    data['udf4'] = '%s' %  request.session['atg_username']
    data['udf5'] = ""
    data['track_id'] = '%s%s' % (payment_attempt.id, data['udf1'])
    data['amount'] = '%s' % payment_attempt.amount
    data['pg_action'] = "1" #Purchase
    #"4" #Authorization

    url = settings.KHAZANA_SERVER_URL 
    return get_response(url , data)

def process_response(payment_attempt, params):
    data = {'action':'process_payment', 
            'catalog': 'futurebazaar'} 
    data['gateway'] = 'hdfc-card'
    if payment_attempt.emi_plan:
        data['gateway'] = 'hdfc-emi'
    data['emi_plan'] = payment_attempt.emi_plan
    for key in params.iterkeys():
        data[key] = params[key]
    data['amount'] = '%s' % payment_attempt.amount
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
        log.exception('Error creating hdfc payment request %s' % repr(e))
