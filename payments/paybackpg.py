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
def create_request(payment_attempt, request):
    log.info("Entered create_request")
    data = {'action':'create_new',
            'gateway': 'payback',
            'transactionId': payment_attempt.id,
            'sessionId': payment_attempt.id,
            'catalogName': CATALOG_NAME.get(request.client.client.name),
            'points': "%i" % (4*payment_attempt.amount)
            }
    url = settings.KHAZANA_SERVER_URL
    return get_response(url,data)

def process_response(payment_attempt, rawdata):
    log.info('Payback process response data: %s' % rawdata)
    return rawdata

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

