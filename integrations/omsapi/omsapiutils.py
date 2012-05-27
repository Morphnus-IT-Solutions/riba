import urllib, urllib2
from django.utils import simplejson
import logging

log = logging.getLogger('fborder')

API_URL = 'http://oms.futurebazaar.com'

def get_api_response(path, method='get', params={}, post_data=None):
    url = '%s/api/%s' % (API_URL, path)
    print url
    opener = urllib2.build_opener()
    if method == 'get' and params:
        url = '%s?%s' % (url, urllib.urlencode(params))
        req = urllib2.Request(url, None)

    if method == 'post' and post_data:
        log.info('POST DATA: %s' % post_data)
        headers = {
                'Content-Type':'application/json; charset=UTF-8',
                }
        data = urllib.urlencode(post_data)
        req = urllib2.Request(url)
    
    response = urllib2.urlopen(req,data)
    response_str = response.read()
    return response_str
