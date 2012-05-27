from datetime import datetime
import time
from cookielib import CookieJar
import cPickle as pickle
import urllib
import urllib2

class StringCookieJar(CookieJar):
    def __init__(self, string=None, policy=None):
        CookieJar.__init__(self, policy)
        if string:
            self._cookies = pickle.loads(string)

    def dump(self):
        return pickle.dumps(self._cookies)

API_URL = "http://www.futurebazaar.com"

def init():
    url = '%s/page.jsp' % API_URL
    #url = '%s/js/mainscript.js' % API_URL
    cj = StringCookieJar()
    print cj._cookies
    # ignore all proxies. put an entry in /etc/hosts and use no proxy
    proxy_support = urllib2.ProxyHandler({})
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cj),proxy_support)
    req = urllib2.Request(url, None, {'User-agent' : 'Mozilla/4.0 (compatible; MSIE 5.5; Windows NT)'})
    try:
        response = opener.open(req)
    except urllib2.URLError:
        time.sleep(3)
        response = opener.open(req)
    html = response.read()
    print dir(cj)
    print cj._cookies
    print cj._cookies
    cookies = cj.dump()
    while True:
        time.sleep(300)
        ncj = StringCookieJar(cookies)
        print ncj._cookies

if __name__ == '__main__':
    init()
