import urllib, urllib2
import sys, getopt
from django.utils import simplejson

def check_availability(sku, pincode, qty=1, store=''):
    values = {'skuId': sku, 'zipCode': pincode, 'qty': qty, 'storeId': store, 'responseMode': 'JSON'}
    url = 'http://10.0.101.19:8080/logistics/dcDeterminationServlet'
    data = urllib.urlencode(values)
    req = urllib2.Request(url, data)
    res = urllib2.urlopen(req)
    page = res.read()
    json = simplejson.loads(page)
    #print json
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
