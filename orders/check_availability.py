import urllib, urllib2
import sys, getopt
from django.utils import simplejson
import logging
from django.conf import settings
from integrations.fbapi import orders

log = logging.getLogger('fborder')
FB_API_PORT = getattr(settings, 'FB_API_PORT', '80')

def check_availability(sku, pincode, qty=1, store=''):
    catalog_name = 'FutureBazaar'
    if 'ezone' in store.lower():
        catalog_name = 'Ezone'
    if 'bigbazaar' in store.lower():
        catalog_name = 'BigBazaar'
    
    if 'ezoneonline.in' in store:
        store = 'ezone.futurebazaar.com'
    if 'bigbazaar.com' in store:
        store = 'www.bigbazaar.com'

    values = {'skuId': sku, 'zipCode': pincode, 'qty': qty, 'storeId': store, 'responseMode': 'JSON'}
    values['catalog'] = catalog_name
    log.info('availability check for : %s' % values)
    url = '%s:%s/logistics/dcDeterminationServlet' % (settings.FB_API_URL, FB_API_PORT)
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    res = urllib2.urlopen(req)
    page = res.read()
    json = simplejson.loads(page)
    log.info('response: %s' % json)
    return json

def check_availability_new(article_id, ratechart_id, pincode, qty= "1", client_id=5, isCod=0, itemPrice=0):
   # cs = utils.get_session_obj(request)
   # fbapi = cs['fbapiobj']
    values = {'articleId': article_id, 'rateChartId':ratechart_id, 'pincode': pincode, 'qty': int(qty), 'client': client_id, "isCod":isCod, 'responseMode': 'JSON', 'itemPrice':itemPrice}
    log.info('availability check for : %s' % values)
    json = orders.ifs_check(values)
   # url = '%s:%s/logistics/dcDeterminationServlet' % (settings.FB_API_URL, FB_API_PORT)
   # url = 'http://10.202.12.184:8080/colada-0.0.1/ifs/postFulfilmentScanner'
   # data = urllib.urlencode(values)
   # req = urllib2.Request(url, data)
   # res = urllib2.urlopen(req)
   # page = res.read()
   # json = simplejson.loads(page)
    log.info('response: %s' % json)
    return json

def usage():
    print 'Script to check availability of a product for future bazaar'
    print '-s, --sku        Product SKU to check availability for. Mandatory Parameter'
    print '-p, --pincode    Pincode where delivery of the product is required. Manadatory Parameter'
    print '-q, --qty        Qty of product requred. Defaults to 1'
    print '-t, --store      Store affiliation for the product'

def main():
    try:
        opts, args = getopt.getopt(sys.argv[1:], 's:p:q:t:',
            ["sku", "pincode", "qty", "store"])
    except getopt.GetoptError, err:
        print str(err)
        usage()
        sys.exit(2)

    qty = 1
    store = ''
    sku = None
    pincode = None
    for o, a in opts:
        if o in ['-s', '--sku']:
            sku = a
        if o in ['-p', '--pincode']:
            pincode = a
        if o in ['-q', '--qty']:
            qty = a
        if o in ['-t', '--store']:
            store = a
    if not sku:
        print 'SKU not entered'
        usage()
        sys.exit(2)
    if not pincode:
        print 'Pinvode not entered'
        usage()
        sys.exit(2)

    check_availability(sku, pincode, qty, store)

    
if __name__ == "__main__":
    main()
