import httplib
from urllib import urlencode
from httplib2 import Http
import urllib
import urllib2

from django.conf import settings
APIserver = "127.0.0.1"
APIport = '8080'


def getPromotionById(pid):
    path = '/' +settings.PROMOTIONS_API_ROOT + '/promotions/getbyid/' + str(pid)
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('GET', path)
    return readResponse(httpServ)

#def getPromotionsByOrderId(pid):
#    path = '/colada/promotions/getbyorderid/?order_id=' + str(pid)
#    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
#    httpServ.connect()
#    httpServ.request('GET', path)
#    return readResponse(httpServ)

def getAllPromotions(nFrom, nTo):
    path = '/'+settings.PROMOTIONS_API_ROOT+'/promotions/getall/?from=' + str(nFrom) + '&' + 'to=' + str(nTo)

    print 'Request to rest server : ' + path
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('GET', path)
    return readResponse(httpServ)

def getHoliiAutoPromotion():
    path = '/'+settings.PROMOTIONS_API_ROOT+'/promotions/getHoliiAutoPromotion/'
    print 'Request to rest server : ' + path
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('GET', path)
    return readResponse(httpServ)


def savePromotion(jsonString):
    path = '/'+settings.PROMOTIONS_API_ROOT + '/promotions/save'
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('POST', path, jsonString)
    return readResponse(httpServ)

def updatePromotionList(jsonString):
    path = '/'+settings.PROMOTIONS_API_ROOT + '/promotions/updatepromotionlist'
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('POST', path, jsonString)
    return readResponse(httpServ)



def getPromotionsByCouponCode(orderId,couponCode, order_amount):
    path = '/'+settings.PROMOTIONS_API_ROOT+'/promotions/getbycouponcode/?order_id=' + str(orderId) + '&' + \
        'coupon_code=' + str(couponCode) + '&' + 'order_amount=' + str(int(order_amount))

    print 'Request to rest server : ' + path
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('GET', path)
    return readResponse(httpServ)

def ifs_check(jsonString):
    path = '/'+ settings.IFS_API_ROOT + '/ifs/postFulfilmentScanner'
    httpServ = httplib.HTTPConnection(settings.IFS_API_SERVER, settings.IFS_API_PORT)
    httpServ.connect()
    httpServ.request('POST', path, jsonString)
    return readResponse(httpServ)

#def deletePromotionById(pid):
#    path = '/colada/promotions/deletebyid/?id=' + str(pid)
#    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
#    httpServ.connect()
#    httpServ.request('DELETE', path)
#    return readResponse(httpServ)
#
#def addPromotion(jsonString):
#    path = '/colada/promotions/add/'
#    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
#    httpServ.connect()
#    httpServ.request('PUT', path, jsonString)
#    return readResponse(httpServ)

def updatePromotion(jsonString):
    path = '/colada/promotions/update/'
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('POST', path, jsonString)
    return readResponse(httpServ)

def getPromotionsForOrder(jsonString):
    path = '/colada/promotions/getApplicablePromotionsForOrder/'
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('POST', path, jsonString)
    return readResponse(httpServ)

def applyPromotionOnOrder(jsonString):
    path = '/colada/promotions/applyPromotionOnOrder/'
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('POST', path, jsonString)
    return readResponse(httpServ)

def subscribeUser(jsonString):
    path = '/colada-0.0.1/subscription/startTransaction/'
    httpServ = httplib.HTTPConnection(settings.SUBSCRIPTIONS_API_SERVER, settings.SUBSCRIPTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('POST', path, jsonString)
    return readResponse(httpServ)

def readResponse(httpServ):
    response = httpServ.getresponse()
    s=''
    if response.status == httplib.OK:
        s = response.read()
    httpServ.close()
    return s


APIserver = "127.0.0.1"
APIport = '8081'

def getPromotionsById(pid):
    path = '/colada/promotions/getbyid/?id=' + str(pid)
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('GET', path)
    return readResponse(httpServ)

def getPromotionsByOrderId(pid):
    path = '/colada/promotions/getbyorderid/?order_id=' + str(pid)
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('GET', path)
    return readResponse(httpServ)


def ebs_check(jsonString):
    path = '/'+settings.EBS_API_ROOT + '/ebs/callEBS'
    httpServ = httplib.HTTPConnection(settings.EBS_API_SERVER, settings.EBS_API_PORT)
    httpServ.connect()
    httpServ.request('POST', path, jsonString)
    return readResponse(httpServ)
	

def deletePromotionById(pid):
    path = '/colada/promotions/deletebyid/?id=' + str(pid)
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('DELETE', path)
    return readResponse(httpServ)

def addPromotion(jsonString):
    path = '/colada/promotions/add/'
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('PUT', path, jsonString)
    return readResponse(httpServ)

def updatePromotion(jsonString):
    path = '/colada/promotions/update/'
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('POST', path, jsonString)
    return readResponse(httpServ)

def getPromotionsForOrder(jsonString):
    path = '/colada/promotions/getApplicablePromotionsForOrder/'
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('POST', path, jsonString)
    return readResponse(httpServ)

def applyPromotionOnOrder(jsonString):
    path = '/colada/promotions/applyPromotionOnOrder/'
    httpServ = httplib.HTTPConnection(settings.PROMOTIONS_API_SERVER, settings.PROMOTIONS_API_PORT)
    httpServ.connect()
    httpServ.request('POST', path, jsonString)
    return readResponse(httpServ)

def readResponse(httpServ):
    response = httpServ.getresponse()
    s=''
    if response.status == httplib.OK:
        s = response.read()
    httpServ.close()
    return s

#def addPromotion(jsonString):
#	path = '/colada/promotions/add/'
#        httpServ = httplib.HTTPConnection(APIserver, APIport)
#        httpServ.connect()
#        httpServ.request('PUT', path, jsonString)
#        return readResponse(httpServ)
#def updatePromotion(jsonString):
#	path = '/colada/promotions/update/'
#        httpServ = httplib.HTTPConnection(APIserver, APIport)
#        httpServ.connect()
#        httpServ.request('POST', path, jsonString)
#        return readResponse(httpServ)
#
#def getPromotionsForOrder(jsonString):
#	path = '/colada/promotions/getApplicablePromotionsForOrder/'
#        httpServ = httplib.HTTPConnection(APIserver, APIport)
#        httpServ.connect()
#        httpServ.request('POST', path, jsonString)
#        return readResponse(httpServ)
#
#def applyPromotionOnOrder(jsonString):
#        path = '/colada/promotions/applyPromotionOnOrder/'
#        httpServ = httplib.HTTPConnection(APIserver, APIport)
#        httpServ.connect()
#        httpServ.request('POST', path, jsonString)
#        return readResponse(httpServ)
#
#def readResponse(httpServ):
#	response = httpServ.getresponse()
#	s=''
#        if response.status == httplib.OK:
#            s = response.read()
#
#        httpServ.close()
#        return s
#
