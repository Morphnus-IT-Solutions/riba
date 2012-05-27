from django.conf import settings
import urllib2
import urllib
from django.utils import simplejson
import socket
import logging
from chaupaatiapi.errors import *
from django.conf import settings

PROTO = "http://"
SERVER = settings.API_SERVER
PORT = settings.API_PORT
PREFIX = settings.API_PREFIX

logger = logging.getLogger('request')

def log(file, level, message):
    logger.info(message)
    method = getattr(logger, level)
    method(message)

class APIRequest():

    def __init__(self, url, data, type='get'):
	self.type = type or 'get'
        if url:
            self.url = url
        else:
            raise APIError('url is required to initialize api request')
        self.data = data

    def getUrl(self):
        '''Returns the url of the request'''
        return self.url

    def getData(self):
        '''Returns the data of the request'''
        return self.data;

    def getType(self):
        '''Returns the type of the request'''
        return self.type
    def __repr__(self):
            return self.type + " : " + self.url + " : " + ( self.data or "")
class RequestWithMethod(urllib2.Request):
    def __init__(self, url, data, method, *args, **kwargs):
        self._method = method
        urllib2.Request.__init__(self, url, data)

    def get_method(self):
        return self._method

class APIResponse():

    def __init__(self, request, response):
        self.request = request
        self.status = None
        if hasattr(response, 'code'):
            self.status = response.code
            self.json = None
            self.data = None
            if response:
                self.data = response.read()
                if response.code in [200]:
                    #log('request', 'debug', 'got api response: ' +self.data)
                    decoder = simplejson.JSONDecoder()
                    if self.data.startswith('{id:'):
                        self.data = self.data.replace('id', '"id"')
                    if self.data:
                        try:
                            if request.getType().lower() == 'delete':
                                self.json = {}
                            else:
                                self.json = decoder.decode(self.data)
                        except ValueError:
                            try:
                                keys = [u'\xef',u'\xa0',u'\xa1',u'\xa2',u'\xa3',u'\xa4',u'\xa5',u'\xa6',u'\xa7',u'\xa8',u'\xa9',u'\xaa',u'\xab',u'\xac',u'\xad',u'\xae',u'\xaf',u'\xb0',u'\xb1',u'\xb2',u'\xb3',u'\xb4',u'\xb5',u'\xb6',u'\xb7',u'\xb8',u'\xb9',u'\xba',u'\xbb',u'\xbc',u'\xbd',u'\xbe',u'\xbf',u'\xef']
                                ucontent = unicode(self.data, 'latin-1')
                                for key in keys:
                                    ucontent = ucontent.replace(key, u'')
                                self.data = ucontent.encode('utf-8')
                                self.json = decoder.decode(self.data)
                            except ValueError:
                                raise APIParseError('unable to parse json: %s' % self.data)
                    else:
                        self.json = {}

    def getStatus(self):
        '''Returns the status code'''
        return self.status

    def getRawData(self):
        '''Returns the raw data'''
        return self.data

    def getJSONData(self):
        '''Returns the decoded JSON constructed out of raw response'''
        return self.json

    def getRequest(self):
        '''Returns the api request'''
        return self.request

    def getHeader(self):
        '''Returns the JSON response header'''
        pass # TODO api doesnt return any header yet

    def getResults(self):
        '''Returns the JSON results set'''
        return self.json

def getApiResponse(api_req):
    ''' Makes the API request and returns the response. The response is an APIResponse object.
        Raises APIError on error conditions. The error conditions and the error raised are -
        - APIParseError : Error parsing response. When response is not valid JSON with HTTP 200
        - APIBadReqError   : Error if request is malformed
        - APIUnauthorizedError  : API returned 403
        - APIUnauthenticatedError : API returned 401
        - APIServerError : API returned 5xx
    '''
    res = None
    try:
        data = None
        url = api_req.getUrl()
        req = None
        if api_req.getData():
            data = api_req.getData()
            headers = {'Content-Type':'application/json; charset=UTF-8'}
            req = urllib2.Request(url, data, headers)
            #logging.getLogger('pl').info(url)
            #logging.getLogger('pl').info(data)
        else:
            if api_req.type.lower() == 'delete':
                req = RequestWithMethod(url, data, api_req.getType())
            else:
                req = urllib2.Request(url, data)
        #logging.getLogger('pl').info('testing')
        #log('request','info','making api request - %s' % repr(api_req))
        res = urllib2.urlopen(req)
    except IOError, e:
        logging.getLogger('pl').exception('error making api request')
        if hasattr(e, 'reason'):
            # unknown error, log it
            log('error','exception','error conversing with api %s %s' % (repr(api_req), repr(e)) )
            raise APIError(e.reason) 
        if hasattr(e, 'code'):
            # log all errors
            log('error','exception','http error conversing with api %s %s' % (repr(api_req), repr(e)) )
            expected_error_codes = [400, 401, 403, 404, 500, 501, 502, 503, 504, 505]
            if e.code not in expected_error_codes:
                raise APIError('invalid response from server')
            else:
                if e.code == 400:
                    badRequest = APIBadReqError('bad request : %s' % repr(api_req))
                    resp = e.read()
                    log('error','error','Bad request in API usage %s' % resp)
                    decoder = simplejson.JSONDecoder()
                    resJson = decoder.decode(resp)
                    badRequest.json = resJson
                    raise badRequest
                if e.code == 401:
                    raise APIUnauthenticatedError('not authenticated : %s' % repr(api_req))
                if e.code == 403:
                    raise APIUnauthorizedError('not authorized : %s' % repr(api_req))
                if e.code == 404:
                    raise APINotFoundError('resource not found : %s' % repr(api_req))
                # server error
                raise APIServerError('server error during api req : %s' % repr(api_req))
    else:
        # no errors. lets try to construct the response
        # creating APIResponse object would raise an error if response is not valid JSON
        return APIResponse(api_req, res)


def initAPIParser():
    # set socket time out
    return 

def makeAPIUrl(components, qs, api_prefix="api"):
    ''' makes the api url from a list of componens and a dict of query string params'''

    # the base url
    url = PROTO + SERVER + ":" + PORT + PREFIX
    # add the api prefix
    url += api_prefix
    
    # append the components
    for x in components:
        url += "/" + urllib2.quote(x,'*') #ignore * in encoding

    # append qs values
    if qs:
        url += "?"
        for k, v in qs.iteritems():
            url += k + "=" + urllib2.quote(str(v)) + "&"

    return url

#initAPIParser()
