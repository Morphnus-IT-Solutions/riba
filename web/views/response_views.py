from django.conf import settings
import logging
from django.utils import simplejson
from django.http import HttpResponse

log = logging.getLogger('request')

def rms_api(request):
    if request.method == 'POST':
        params = request.POST
        if 'client' and 'cm' and 'order' and 'mobile' in params:
            if params['client'] == 'fb' and params['cm'] == 'cod-verification':
                campaign_id = 53
                info = {'campaign_id': campaign_id, 'phone':params['mobile'],'message':'Order Id: %s' % params['order']}
                response = add_response(info)
                return HttpResponse(response['status'])
            else:
                return HttpResponse(simplejson.dumps(dict(msg_code='FAILED',msg='Invalid parameters',status='FAILED')),mimetype="application/json")


def getMatchingResponses(phone, dni=None, call=None, agent=None, type=None):
    url = 'http://rms.chaupaati.in/api/response/add_or_get?phone=' + phone
    if dni:
        url = url + '&dni=' + dni
    if call:
        url += '&call=' + call
    if agent:
        url += '&agent=' + agent
    if type:
        url += '&type=' + type
    req = APIRequest(url, None)
    res = getApiResponse(req)
    if res.getStatus() == 200:
        json = res.getJSONData()
        return json['data']
    return {}

def closeCall(request,info):
    url = 'http://rms.chaupaati.in/api/call/close'
    data = simplejson.dumps(info)
    req = APIRequest(url, data)
    res = getApiResponse(req)
    if res.getStatus() == 200:
        json = res.getJSONData()
        return json

def getAttemptInfo(aid):
    url = 'http://rms.chaupaati.in/api/attempt/' + aid
    req = APIRequest(url, None)
    res = getApiResponse(req)
    if res.getStatus() == 200:
        json = res.getJSONData()
        return json['data']
    return {}

def updateDialerAttempt(request, info):
    log.info('updating dialer attempt -- %s' % repr(info))
    url = 'http://rms.chaupaati.in/api/attempt/' + info['aid'] + '/update'
    data = simplejson.dumps(info)
    req = APIRequest(url, data)
    res = getApiResponse(req)
    if res.getStatus() == 200:
        json = res.getJSONData()
        return json

def add_response(info):
    url = 'http://rms.chaupaati.in/api/response/add'
    data = simplejson.dumps(info)
    req = APIRequest(url, data)
    res = getApiResponse(req)
    if res.getStatus() == 200:
        json = res.getJSONData()
        return json

def rapidresponse(request):
    log.info('Incoming rapid response %s' % repr(request.GET))
    return HttpResponse('')
    try:
        phone = request.GET.get('msisdn','')
        message = request.GET.get('message')
        city = request.GET.get('circle','')
        resp = dict(phone=phone, message=message, city=city, medium='SMS')
        if message.lower().startswith('gold'):
            resp['campaign_id'] = 28
        if message.lower().startswith('study'):
            resp['campaign_id'] = 29
        if message.lower().startswith('ack'):
            resp['campaign_id'] = 30
        if message.lower().startswith('robin'):
            resp['campaign_id'] = 34
        if message.lower().startswith('ng'):
            resp['campaign_id'] = 32
        if message.lower().startswith('fit'):
            resp['campaign_id'] = 36
        add_response(resp)
    except Exception, e:
        log.exception('Error adding rapid response %s' % repr(e))
    return HttpResponse('')

