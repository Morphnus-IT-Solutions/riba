from django.conf import settings
from feeds.models import APIResponse
import urllib, urllib2
import cookielib
from django.utils import simplejson
import tempfile
import random, hashlib
import logging
import httplib
from cookielib import CookieJar
import cPickle as pickle
import time
from stringcookiejar import StringCookieJar
import socket
from datetime import datetime

log = logging.getLogger('fborder')

API_URL = settings.FB_API_URL
FB_API_URL = settings.FB_API_URL
FB_API_OTHER_URLS = getattr(settings, 'FB_API_OTHER_URLS', '') 
FB_API_PORT = getattr(settings, 'FB_API_PORT', '80')
USER_NOT_FOUND = 'UM_NO_SUCH_USER'
USER_FOUND = 'UM_FOUND_USER'
ERROR = 'GN_UNKNOWN_ERROR'
OUT_OF_STOCK = 'OM_ITEM_OUT_OF_STOCK'

PROMOTION_TYPES_MAP = {'Item Discount - Percent Off':{'applies_to':'product_offer_price','discount_type':'percentage'},
            'Item Discount - Amount Off':{'applies_to':'product_offer_price','discount_type':'fixed'},
            'Item Discount - Fixed Price':{'applies_to':'product_offer_price','discount_type':'fixed'},
            'Shipping Discount - Percent Off':{'applies_to':'order_shipping_charge','discount_type':'percentage'},
            'Shipping Discount - Amount Off':{'applies_to':'order_shipping_charge','discount_type':'fixed'},
            'Shipping Discount - Fixed Price':{'applies_to':'order_shipping_charge','discount_type':'fixed'},
            'Order Discount - Percent Off':{'applies_to':'order_total','discount_type':'percentage'},
            'Order Discount - Amount Off':{'applies_to':'order_total','discount_type':'fixed'},
            'Order Discount - Fixed Price':{'applies_to':'order_total','discount_type':'fixed'}}

SAP_PAYMENT_CODES = {'cheque':'CHEQ',
            'cod':'COD',
            'cash':'CASH',
            'fmemi':'FEMI',
            }

STATES_MAP = {'Andaman and Nicobar':'26',
            'Andhra Pradesh':'01',
            'Arunachal Pradesh':'02',
            'Assam':'03',
            'Bihar':'04',
            'Chandigarh':'27',
            'Chhattisgarh':'33',
            #'Chhaatisgarh':'33', - do not uncomment - prady
            'Dadra and Nagar Haveli':'28',
            'Daman and Diu':'29',
            'Delhi':'30',
            'Goa':'05',
            'Gujarat':'06',
            'Haryana':'07',
            'Himachal Pradesh':'08',
            'Jammu and Kashmir':'09',
            'Jharkhand':'34',
            'Karnataka':'10',
            'Kerala':'11',
            'Lakshadweep':'31',
            'Madhya Pradesh':'12',
            'Maharashtra':'13',
            #'Maharastra':'13', - do not uncomment - prady
            'Manipur':'14',
            'Meghalaya':'15',
            'Mizoram':'16',
            'Nagaland':'17',
            'New Delhi':'30',
            'Orissa':'18',
            'Pondicherry':'32',
            'Punjab':'19',
            'Rajasthan':'20',
            'Sikkim':'21',
            'Tamil Nadu':'22',
            #'Tamilnadu':'22', - do not uncomment - prady
            'Tripura':'23',
            'Uttar Pradesh':'24',
            'Uttaranchal':'35',
            'West Bengal':'25'}

US_STATES_MAP = {
            'Alabama':'01',
            'Arizona':'02',
            'Arkansas':'03',
            'California':'04',
            'Colorado':'05',
            'Connecticut':'06',
            'D.C.':'07',
            'Delaware.':'08',
            'Florida':'09',
            'Georgia':'10',
            'Idaho':'11',
            'Illinois':'12',
            'Indiana':'13',
            'Iowa':'14',
            'Kansas':'15',
            'Kentucky':'16',
            'Louisiana':'17',
            'Maine':'18',
            'Maryland':'19',
            'Massachusetts':'20',
            'Michigan':'21',
            'Minnesota':'22',
            'Mississippi':'23',
            'Missouri':'24',
            'Montana':'25',
            'Nebraska':'26',
            'Nevada':'27',
            'New Hamshire':'28',
            'New Mexico':'29',
            'New York':'30',
            'New Jersey':'31',
            'North Carolina':'32',
            'North Dakota':'33',
            'Ohio':'34',
            'Oklahoma':'35',
            'Oregon':'36',
            'Pennsylvania':'37',
            'Rhode Islan':'38',
            'South Carolina':'39',
            'South Dakota':'40',
            'Tennessee':'41',
            'Texas':'42',
            'Utah':'43',
            'Vermont':'44',
            'Virginia':'45',
            'Washington':'46',
            'West Virginia':'47',
            'Wisconsin':'48',
            'Wyoming':'49',
            }

class APIError(Exception):
    pass

def init(request):
    import socket
    socket.setdefaulttimeout(10)
    URL = '%s:%s' % (FB_API_URL, FB_API_PORT)
    if request.client.domain in FB_API_OTHER_URLS:
        URL = 'http://%s:%s' % (request.client.domain, FB_API_PORT)
    url = '%s/fulfilment_test.jsp' % URL
    #url = '%s/js/mainscript.js' % API_URL
    cj = StringCookieJar()
    # ignore all proxies. put an entry in /etc/hosts and use no proxy
    proxy_support = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),proxy_support)
    req = urllib2.Request(url, None, {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'})
    try:
        print datetime.now()
        response = opener.open(req)
    except urllib2.URLError, e:
        log.exception('Error initializing api %s' % repr(e))
        time.sleep(0.5) # Don't wait for more than half second
        response = opener.open(req)
    except Exception, e2:
        log.exception('Error initializing api %s' % repr(e2))
        print datetime.now()
        pass
    html = response.read()
    response.close() # Close the connection
    return cj.dump()

def logoff(cookie_file, request):
    import socket
    socket.setdefaulttimeout(600)
    URL = '%s:%s' % (FB_API_URL, FB_API_PORT)
    if request.client.domain in FB_API_OTHER_URLS:
        URL = 'http://%s:%s' % (request.client.domain, FB_API_PORT)
    url = '%s/logoffUser.jsp' % URL
    cj = StringCookieJar(cookie_file)
    proxy_support = urllib2.ProxyHandler({})
    req = urllib2.Request(url, None, {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'})

    class MyHTTPRedirectHandler(urllib2.HTTPRedirectHandler):
        def http_error_302(self, req, fp, code, msg, headers):
            #log.info('Ignoring redirect %s' % (code))
            return None

        http_error_301 = http_error_303 = http_error_307 = http_error_302

    cookieprocessor = urllib2.HTTPCookieProcessor()

    opener = urllib2.build_opener(MyHTTPRedirectHandler, cookieprocessor, proxy_support)
    #opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),proxy_support)
    urllib2.install_opener(opener)
    response = None
    try:
        response = opener.open(req)
        info = response.info()
    except urllib2.URLError, e:
        if getattr(e, 'code', '')  in [301, 302]:
            pass

    if response:
        html = response.read()
        response.close()
    return cookie_file

'''
def logoff(cookie_file, request):
    URL = '%s:%s' % (FB_API_URL, FB_API_PORT)
    if request.client.domain in FB_API_OTHER_URLS:
        URL = 'http://%s:%s' % (request.client.domain, FB_API_PORT)
    url = '%s/logoffUser.jsp' % URL
    cj = StringCookieJar(cookie_file)
    proxy_support = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),proxy_support)
    req = urllib2.Request(url, None, {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'})
    try:
        response = opener.open(req)
    except urllib2.URLError:
        import time
        time.sleep(0.5)
        response = opener.open(req)
    html = response.read()
    response.close()
    return cookie_file
'''

def get_session_id(cj):
    if not cj:
        return ''
    for index, cookie in enumerate(cj):
        if cookie.name == 'ATG_SESSION_ID':
            return cookie.value
    return ''

def get_api_response(request, agent,path, cookie_file, method='get', params={}, post_data=None):
    import socket
    socket.setdefaulttimeout(600)
    URL = '%s:%s' % (FB_API_URL, FB_API_PORT)
    if request.client.domain in FB_API_OTHER_URLS:
        URL = 'http://%s:%s' % (request.client.domain, FB_API_PORT)
    url = '%s/api/%s' % (URL, path)
    cj = StringCookieJar(cookie_file)
    session_id = get_session_id(cj)
    proxy_support = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),proxy_support)

    sha1 = hashlib.sha1()
    sha1.update(str(random.random()))
    data = sha1.hexdigest()
    #api_response = APIResponse()
    #api_response.client = 'FB'
    #api_response.save()
    api_key = 'AAAAB3NzaC1yc2EAAAABIwAAAQEAmj71mIXq6+cUMZ+s/2HPyAHFJh5cpflE+J2h+WBRJlLGJtb/ArvAKszaMO4q/aQpD0lB5s1yhGVNS6Hoq1GHaCSiuF71sV34I4txVfOcvLsXmvW3+8Y5hcAJoWfXPj+oeCLZAhkOhUSANHUc54syk4N8rH8nEP+ank78jvttBoTyIn54z0msO/69kY7w/Q5DcgsGKV/MpPfaVb1gL5ctoB9+2dohhLdYR8nIe1lk1iGzGVmizXJz4T4OJdi4x2ppGjOTDXAFM6hAgAxeHDoDm7DFHfxYyUwM2tzVBoTMiKohIGroZrVPak3KitBkxo/NFA3fPwaeX7ENQJ54mLVyEQ=='
    private_key = 'MIIEoAIBAAKCAQEAmj71mIXq6+cUMZ+s/2HPyAHFJh5cpflE+J2h+WBRJlLGJtb/ArvAKszaMO4q/aQpD0lB5s1yhGVNS6Hoq1GHaCSiuF71sV34I4txVfOcvLsXmvW3+8Y5hcAJoWfXPj+oeCLZAhkOhUSANHUc54syk4N8rH8nEP+ank78jvttBoTyIn54z0msO/69kY7w/Q5DcgsGKV/MpPfaVb1gL5ctoB9+2dohhLdYR8nIe1lk1iGzGVmizXJz4T4OJdi4x2ppGjOTDXAFM6hAgAxeHDoDm7DFHfxYyUwM2tzVBoTMiKohIGroZrVPak3KitBkxo/NFA3fPwaeX7ENQJ54mLVyEQIBIwKCAQBpxMWqanU0DCsatqKDO8GtuBIoxFzJlPwYMZOjr8Kd753RfXuqGlfi1ZzuWiwbo8RiQNy7hZBayR8PSnOorO8i10sCFTrCxBfd2/Xxy56tTReAM3bYh+zuAAaakFkUve/dWblghjXXufGDDno4X3MjUtkl04iAr0Vz3mQKRgGeEPRzg8U+c+gbX4/E4z6MurM7xVWCuTXHb9pI0sSsCg4T0kt0uD74shEyXuNiVVEh0ExqzQnZAyKMm3Hjij0gED+dTk8MP5WOtJz74yQLq3C3hIkVRFFoTJos8rMF3yzEiPytGa6vbrcuQ8lFIiha9A2x8JEKuuFORMlSWU4mXFSrAoGBAM1jDPUsQSpA6eGiT1jkDIbtTBydX6AieUr1gtSGJyj6ga9SziWVx+kgBWnTY6C9L5vy1Pnsnz2+Ffpyz9eESnzJFnHlnIVcax9xVuq0Qz9pt7jNQ5pXmN6VN5kBPhr52A2/Iu6lZiGyJP+QIPWT5z2xcdgvPkYJZ3FdJx+72NgPAoGBAMBBpq6n9M991CpFdDI2cXci6czYB2i/phu2ByzZNrAeCyF81KAZlmto+f24jq3HolJgGaUvA/kWGrhHNJ10XY+LtZiLTBsRyxF0tN7W8hUmV8RnCnJkQ3gZbfbyC+Wa36Lk19sBeGKUsJrLMvRYr1C/HTOKzSUZeqD2CnGPlfPfAoGANNBTygQQwbjrrwx6zbb76C5kB1uq4AjdXGsEYojlf5DfhNrHS35JWTQepi8K/XJ59OaryzzYfZdHeupSs8LulR3D8Wbtu+SQkw6EEHd/Aa14YrhweCUnTy2vNfkBV2TRKBs03kfJziZ+itvrN9WTO7/qEwTVf7lGfDyGZz7unfUCgYAxb/epQSGxsqRFYlEUOeKpm0NvMDxrZHsrsnbfpZG4Qj1gYe2IQRgM/bygVAdug8qnd8wUiG68ZMUK0Hs+bmEzilNEe5c6KSWWxj0jW9fZjYRIckSD0KOiijI4L5yowWy028J6JPMSCPo2bsP1sGeYa6hsVuRLXlK7rPtfB6o3ZQKBgAivtq1I3hoSC+ToZroG3HmoN2PRB3syXjdJs9xnm7243Rg9YH2Qr7Knj8xhTr3nUN8q2Vk4LzNn5uW5zapZz+iiT0vbqdni18DgLWNd6NgjFeNrMyTUFk8cfAmLNAcMyYO2HQMTQTYnn5AGoC5eoQyzTFOaDtEs0TnBsDrOAsgI'
    sha2 = hashlib.sha1()
    sha2.update('%s%s%s' % (data, api_key, private_key))
    signature = sha2.hexdigest()
    tinla_order_ref = ''
    try:
        if 'cart_id' in request.session:
            tinla_order_ref = request.session['cart_id']
        from utils import utils
        cs = utils.get_session_obj(request)
        fbapiobj = cs.get('fbapiobj', None)
        if fbapiobj:
            if fbapiobj.add_to_cart_response:
                tinla_order_ref = fbapiobj.add_to_cart_response['items'][0]['orderId']
    except:
        pass
    if method == 'get' and params:
        #params.update({'requestId':api_response.id})
        headers = {
                'X-FBAPI-KEY': api_key,
                'X-FBAPI-DATA': data,
                'X-FBAPI-SIGNATURE': signature,
                'X-FBAPI-AGENT': agent,
                'X-FBAPI-ID': '0', #str(api_response.id),
                'tinlaHostIPAddr': socket.gethostname(),
                'tinlaSessionId': session_id,
                'tinlaOrderId': str(tinla_order_ref),
                }
        url = '%s?%s' % (url, urllib.urlencode(params))
        req = urllib2.Request(url, None, headers)

    if method == 'post' and post_data:
        #post_data.update({'requestId':api_response.id})
        log.info('Agent: %s, POST DATA: %s' % (agent,post_data))
        headers = {
                'Content-Type':'application/json; charset=UTF-8',
                'X-FBAPI-KEY': api_key,
                'X-FBAPI-DATA': data,
                'X-FBAPI-SIGNATURE': signature,
                'X-FBAPI-AGENT': agent,
                'X-FBAPI-ID': '0', #str(api_response.id),
                'tinlaHostIPAddr': socket.gethostname(),
                'tinlaSessionId': session_id,
                'tinlaOrderId': str(tinla_order_ref)
                }
        encoder = simplejson.JSONEncoder()
        data = encoder.encode(post_data)
        req = urllib2.Request(url, data, headers)

    print datetime.now()
    log.info('API REQUEST %d %s: %s: DATA: %s' % (0, session_id, url, post_data))

    try:
        try:
            response = opener.open(req)
            info = response.info()
            if info.getheaders('Set-Cookie'):
                log.info('Got new cookie for %s - %s' % 
                    (session_id, info.getheaders('Set-Cookie')))
        except urllib2.URLError, e:
            log.exception('Error doing api request: %s' % repr(e))
            import time
            time.sleep(0.5)
            try:
                response = opener.open(req)
                info = response.info()
                if info.getheaders('Set-Cookie'):
                    log.info('Got new cookie for %s - %s' % 
                        (session_id, info.getheaders('Set-Cookie')))
            except urllib2.HTTPError, error:
                raise APIError('Error reading response %s: %s' % (error.read(),
                    repr(error)))
                
        json_str = unicode(response.read(),'utf-8','ignore')
        response.close() # Close response after use
        log.info("API RESPONSE %d %s:%s" % (0, session_id, json_str) )
        try:
            return simplejson.loads(json_str.encode('ascii','ignore'))
        except Exception, json_ex:
            log.exception('Not json response %s' % json_str.encode('ascii',
                'ignore'))
            raise APIError('Not json response %s' % json_str.encode('ascii',
                'ignore'))
    except (httplib.IncompleteRead, httplib.BadStatusLine), e2:
        print datetime.now()
        log.exception('Error doing api request: %s' % repr(e2))
        raise APIError('Skipping async and failing because of %s' % repr(e2))
        #return get_async_api_response(request, agent,cookie_file,int(api_response.id))

def get_async_api_response(request, agent,cookie_file, api_req_id):
    URL = '%s:%s' % (FB_API_URL, FB_API_PORT)
    if request.client.domain in FB_API_OTHER_URLS:
        URL = 'http://%s:%s' % (request.client.domain, FB_API_PORT)
    url = '%s/api/%s' % (URL, 'api/')
    cj = StringCookieJar(cookie_file)
    proxy_support = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),proxy_support)

    sha1 = hashlib.sha1()
    sha1.update(str(random.random()))
    data = sha1.hexdigest()
    api_key = 'AAAAB3NzaC1yc2EAAAABIwAAAQEAmj71mIXq6+cUMZ+s/2HPyAHFJh5cpflE+J2h+WBRJlLGJtb/ArvAKszaMO4q/aQpD0lB5s1yhGVNS6Hoq1GHaCSiuF71sV34I4txVfOcvLsXmvW3+8Y5hcAJoWfXPj+oeCLZAhkOhUSANHUc54syk4N8rH8nEP+ank78jvttBoTyIn54z0msO/69kY7w/Q5DcgsGKV/MpPfaVb1gL5ctoB9+2dohhLdYR8nIe1lk1iGzGVmizXJz4T4OJdi4x2ppGjOTDXAFM6hAgAxeHDoDm7DFHfxYyUwM2tzVBoTMiKohIGroZrVPak3KitBkxo/NFA3fPwaeX7ENQJ54mLVyEQ=='
    private_key = 'MIIEoAIBAAKCAQEAmj71mIXq6+cUMZ+s/2HPyAHFJh5cpflE+J2h+WBRJlLGJtb/ArvAKszaMO4q/aQpD0lB5s1yhGVNS6Hoq1GHaCSiuF71sV34I4txVfOcvLsXmvW3+8Y5hcAJoWfXPj+oeCLZAhkOhUSANHUc54syk4N8rH8nEP+ank78jvttBoTyIn54z0msO/69kY7w/Q5DcgsGKV/MpPfaVb1gL5ctoB9+2dohhLdYR8nIe1lk1iGzGVmizXJz4T4OJdi4x2ppGjOTDXAFM6hAgAxeHDoDm7DFHfxYyUwM2tzVBoTMiKohIGroZrVPak3KitBkxo/NFA3fPwaeX7ENQJ54mLVyEQIBIwKCAQBpxMWqanU0DCsatqKDO8GtuBIoxFzJlPwYMZOjr8Kd753RfXuqGlfi1ZzuWiwbo8RiQNy7hZBayR8PSnOorO8i10sCFTrCxBfd2/Xxy56tTReAM3bYh+zuAAaakFkUve/dWblghjXXufGDDno4X3MjUtkl04iAr0Vz3mQKRgGeEPRzg8U+c+gbX4/E4z6MurM7xVWCuTXHb9pI0sSsCg4T0kt0uD74shEyXuNiVVEh0ExqzQnZAyKMm3Hjij0gED+dTk8MP5WOtJz74yQLq3C3hIkVRFFoTJos8rMF3yzEiPytGa6vbrcuQ8lFIiha9A2x8JEKuuFORMlSWU4mXFSrAoGBAM1jDPUsQSpA6eGiT1jkDIbtTBydX6AieUr1gtSGJyj6ga9SziWVx+kgBWnTY6C9L5vy1Pnsnz2+Ffpyz9eESnzJFnHlnIVcax9xVuq0Qz9pt7jNQ5pXmN6VN5kBPhr52A2/Iu6lZiGyJP+QIPWT5z2xcdgvPkYJZ3FdJx+72NgPAoGBAMBBpq6n9M991CpFdDI2cXci6czYB2i/phu2ByzZNrAeCyF81KAZlmto+f24jq3HolJgGaUvA/kWGrhHNJ10XY+LtZiLTBsRyxF0tN7W8hUmV8RnCnJkQ3gZbfbyC+Wa36Lk19sBeGKUsJrLMvRYr1C/HTOKzSUZeqD2CnGPlfPfAoGANNBTygQQwbjrrwx6zbb76C5kB1uq4AjdXGsEYojlf5DfhNrHS35JWTQepi8K/XJ59OaryzzYfZdHeupSs8LulR3D8Wbtu+SQkw6EEHd/Aa14YrhweCUnTy2vNfkBV2TRKBs03kfJziZ+itvrN9WTO7/qEwTVf7lGfDyGZz7unfUCgYAxb/epQSGxsqRFYlEUOeKpm0NvMDxrZHsrsnbfpZG4Qj1gYe2IQRgM/bygVAdug8qnd8wUiG68ZMUK0Hs+bmEzilNEe5c6KSWWxj0jW9fZjYRIckSD0KOiijI4L5yowWy028J6JPMSCPo2bsP1sGeYa6hsVuRLXlK7rPtfB6o3ZQKBgAivtq1I3hoSC+ToZroG3HmoN2PRB3syXjdJs9xnm7243Rg9YH2Qr7Knj8xhTr3nUN8q2Vk4LzNn5uW5zapZz+iiT0vbqdni18DgLWNd6NgjFeNrMyTUFk8cfAmLNAcMyYO2HQMTQTYnn5AGoC5eoQyzTFOaDtEs0TnBsDrOAsgI'
    sha2 = hashlib.sha1()
    sha2.update('%s%s%s' % (data, api_key, private_key))
    signature = sha2.hexdigest()
    session_id = get_session_id(cj)

    headers = {
            'X-FBAPI-KEY': api_key,
            'X-FBAPI-DATA': data,
            'X-FBAPI-SIGNATURE': signature,
            'X-FBAPI-AGENT': agent,
            'X-FBAPI-ID': '0',
            'tinlaHostIPAddr': socket.gethostname(),
            'tinlaSessionId': session_id,
            'tinlaOrderId': ''
            }
    count = 0
    res = None


    while count < 10: # Limiting to one retry
        count += 1
        url = url.replace('?requestId=%s' % api_req_id,'')
        url = '%s?requestId=%s' % (url,api_req_id)
        req = urllib2.Request(url, None, headers)
        log.info('API REQUEST %d-%s: %s: DATA: %s' % (api_req_id, session_id, url, ''))
        try:
            response = opener.open(req)
            json_str = response.read()
            json_str = unicode(response.read(),'utf-8','ignore')

            res =  simplejson.loads(json_str.encode('ascii','ignore'))
            log.info("API RESPONSE %d-%s:%s" % (api_req_id, session_id, res))
            if res['responseCode'] == 'AM_REQ_ID_NOT_FOUND':
                time.sleep(1)
            elif res['responseCode'] == 'GN_UNKNOWN_ERROR' and 'JSONTokener' in res['responseMessage']:
                time.sleep(1)
            else:
                log.info('Async response for request %s : %s' % (api_req_id,res))
                break
            response.close() # Close the connection
        except (httplib.IncompleteRead, httplib.BadStatusLine):
            continue
        except urllib2.URLError:
            time.sleep(1)
            continue
    if not res:
        log.error('Unable to get async response for %s' % api_req_id)
        raise APIError('Unable to get async response for %s' % api_req_id) 
    return res
