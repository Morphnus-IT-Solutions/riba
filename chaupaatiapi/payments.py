from chaupaatiapi.api import APIRequest, APIResponse, makeAPIUrl, getApiResponse
from django.utils import simplejson
import logging
from chaupaatiapi.entities.payment import Payment

log = logging.getLogger('pl')

def createRequest(payment_req, usr, call_session, *args, **kwargs):
    '''creates a payment request'''
    components = [str(usr['ID']), str(call_session['ID']), '*', '*', '*', '*', \
            '*', '*', '*', '*', '*', '*', '*', '*', '*']
    data = payment_req.toJSONStr()
    url = makeAPIUrl(components, None)
    req = APIRequest(url, data)
    res = getApiResponse(req)
    if res.getStatus() == 200:
        payment_req.fromJSONObj(res.getJSONData())
        return payment_req

def getPayment(order_id, channel):
    '''gets the payment with given order_id and channel'''
    components = ['*', '*', '*', '*', '*', '*', \
            '*', '*', '*', '*', '*', '*', '*', '*', '*']
    url = makeAPIUrl(components, dict(orderid=order_id,channel=channel))
    req = APIRequest(url, None)
    res = getApiResponse(req)
    if res.getStatus() == 200:
        payment_req = Payment()
        payment_req.fromJSONObj(res.getJSONData()['items'][0])
        return payment_req

def updatePayment(payment_req, *args, **kwargs):
    '''creates a payment request'''
    components = ['*', '*', '*', '*', '*', '*', \
            '*', '*', '*', '*', '*', '*', '*', '*', '*']
    payment_info = payment_req.toJSONObj()
    payment_info['orderId'] = payment_req['ORDER_ID']
    data = {'update':payment_info}
    encoder = simplejson.JSONEncoder()
    jsonStr =encoder.encode(data)
    url = makeAPIUrl(components, None)
    req = APIRequest(url, jsonStr)
    res = getApiResponse(req)
    if res.getStatus() == 200:
        payment_req.fromJSONObj(res.getJSONData())
        return payment_req

def createICICIPaymentReq(params):
    components = ['*', '*', '*', '*', '*', '*', \
            '*', '*', '*', '*', '*', '*', '*', '*', '*']
    data = {'action':'create_icici_request'}
    data['ip'] = params['ip']
    data['detectFraud'] = False
    data['storeBillingShipping'] = False
    data['useragent'] = params['useragent']
    data['acceptHeader'] = params['acceptheader']
    data['returnUrl'] = params['returnUrl']

    data['paymentAction'] = params['paymentAction']
    data['paymentParam'] = params['paymentParam']
    data['payableAmount'] = params['payableAmount']
    data['reqType'] = 'req.Preauthorization'
    data['userId'] = params['userId']

    encoder = simplejson.JSONEncoder()
    jsonStr =encoder.encode(data)
    url = makeAPIUrl(components, None)
    req = APIRequest(url, jsonStr)
    res = getApiResponse(req)
    payment_req = Payment()
    if res.getStatus() == 200:
        payment_req.fromJSONObj(res.getJSONData()['payment'])
        return dict(payment=payment_req, redirect_url=res.getJSONData()['redirectUrl'])
