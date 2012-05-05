from bl.user import User
from bl.api import APIRequest, APIResponse, getApiResponse, makeAPIUrl
from bl.errors import *
import logging

log = logging.getLogger('ccc')

def getUserByMobile(mobile, *args, **kwargs):
    '''gets the user for a mobile number'''
    u = User()
    url = makeAPIUrl(['*'],dict(mobile=mobile, apiuser='hemanth'))
    req = APIRequest(url, None)
    res = getApiResponse(req)
    if res.getStatus() == 200:
        # valid response
        u.fromJSONObj(res.getJSONData()['users'][0])
    return u

def add(usr, *args, **kwargs):
    '''adds a user to the system'''
    url = makeAPIUrl(['*'], dict(session='dialer_session', apiuser='hemanth'))
    log.info(url)
    usr['LEAD_CONTACT_PREFS'] = 'mobile,mobile2,email,email2'
    usr['ORDER_CONTACT_PREFS'] = 'mobile,mobile2,email,email2'
    usr['NOTIFICATION_CONTACT_PREFS'] = 'mobile,mobile2,email,email2'
    usr['DEAL_ALERT_CONTACT_PREFS']= 'mobile,mobile2'
    data = usr.toJSONStr()
    log.info(data)
    req = APIRequest(url, data)
    res = getApiResponse(req)
    log.info('Response Status: %s' % res.getStatus())
    log.info('Response Raw Data: %s' % res.getRawData())
    log.info('Response Json Data: %s' % res.getJSONData())
    if res.getStatus() == 200:
        # valid response
        usr['ID'] = res.getJSONData()['id']
    return usr
