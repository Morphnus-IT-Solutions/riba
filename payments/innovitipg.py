import urllib, urllib2
import hashlib
from django.utils import simplejson
import logging
from django.conf import settings

log = logging.getLogger('request')

CATALOG_NAME = {
        'Future Bazaar': 'futurebazaar',
        'Ezone': 'ezoneonline',
        }

INNOVITI_BANK_CODES = {
        'hdfc':'1',
        'axis':'2',
        'icici':'3',
        'citi':'5',
        'scb':'6',
        'hsbc':'7',
        'kotak':'8',
        'sbi':'9',
    }

INNOVITI_EMI_CODES = {
        '3':'1',
        '6':'2',
        '9':'3',
        '12':'4',
    }

def create_request(request, **kwargs):
    log.info("Entered create_request")
    payment_attempt = kwargs.get('payment_attempt')
    order = kwargs.get('order')
    bank = kwargs.get('bank')
    data = {'action':'create_new',
            'gateway': 'innoviti',
            'transactionId': '%s%s' % (order.get_id(), payment_attempt.id),
            'pro_sku':order.orderitem_set.all()[0].seller_rate_chart.sku,
            'amount':'%s' % payment_attempt.amount,
            'processing_code':get_processing_code(bank, payment_attempt.emi_plan),
            }
    url = settings.KHAZANA_SERVER_URL
    return get_response(url,data)

def process_response(payment_attempt, params):
    log.info("Entered Process Response")
    data = {'action':'process_payment',
            'gateway': 'innoviti',
            'transactionId': payment_attempt.transaction_id,
            'transresponse':params,
            }
    url = settings.KHAZANA_SERVER_URL
    return get_response(url,data)

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
        log.info('Got response for create Innoviti payment request: %s' % res_data)
        return simplejson.loads(res_data)
    except IOError, e:
        log.exception('Error creating Innoviti payment request %s' % repr(e))

def get_processing_code(bank, emi_plan):
    if not emi_plan:
        return "000000"
    
    bank_code = INNOVITI_BANK_CODES.get(bank)
    bank_emi_code = INNOVITI_EMI_CODES.get(emi_plan)
    return '%s%s0000' % (bank_code, bank_emi_code)
