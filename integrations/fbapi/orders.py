from integrations.fbapi import fbapiutils as futils, users
import datetime
from django.utils import simplejson
import logging
from restapi import APIManager

log = logging.getLogger('fbapiorder')


def get_order_by_orderid(order_id, agent, cookie_file, request, enableSecurity="false"):
    json = futils.get_api_response(request, agent, 'order/', cookie_file, 'get', {'orderId':order_id,"enableSecurity":enableSecurity})
    return json

def get_order_by_user(profile_id, agent, cookie_file, request, startOrderIndex=0, numoforders=1, enableSecurity="false"): 
    #get_user = users.get_user_by_login(login, agent, cookie_file, request)
    json = futils.get_api_response(request, agent, 'order/', cookie_file, 'get', 
        {'startOrderIndex':startOrderIndex, 
        'profileId':profile_id,
        'numberOfOrders':numoforders,
        'enableSecurity':enableSecurity})
    return json

def issue_coupon(email_id, agent, cookie_file, store, request):
    json = futils.get_api_response(request, agent, 'order/', cookie_file, 'post',{}, 
        {'action':'ASSIGN_COUPON',
        'data':{
                'login':email_id,
                'store':store,
               }
        })
    return json

def create_order_for_user(profile_id):
    create_order_client = futils.get_client('order','createOrderForUser')
    order_id = create_order_client.service.createOrderForUser(
            profile_id, None)
    return order_id

def get_cart(agent,cookie_file,mobile,profile, request):
    json = futils.get_api_response(request, agent,'order/', cookie_file , 'get', {'phone':mobile,'currentProfileId':profile})
    return json
    
def add_to_cart(skuId, productId, quantity,agent,profile,cookie_file, request):
    json = futils.get_api_response(request, agent,'order/', cookie_file, 'post', {}, {
        'action': 'ADD_TO_CART',
        'data': {
            'profileId': profile,
            'skuId': skuId,
            'productId': productId,
            'quantity': quantity,
            }
        })
    return json


def update_item_quantity(sku_id, qty, order_id, request):
    pass

def remove_from_cart(commerceItemId, productId, agent, profile, cookie_file, request):
    json = futils.get_api_response(request, agent,'order/', cookie_file, 'post', {}, {
        'action': 'REMOVE_ITEM',
        'data': {
            'profileId': profile,
            'skuId': commerceItemId,
            'commerceItemId': commerceItemId,
            'productId': productId,
            }
        })
    return json

def ebs_check(info,agent,cookie_file, request):
  
    json = {}
    try:	
        infoStr = simplejson.dumps(info)
        log.info('EBS API Request : ' + infoStr)
        response = APIManager.ebs_check(infoStr)
        json = simplejson.loads(response)
        log.info('EBS API Response : ' + response)
    except Exception,e:
        log.exception('Exception in EBS Rest API call %s' % repr(e))
    return json

def ifs_check(info):
    json = {}
    try:	
        infoStr = simplejson.dumps(info)
        log.info('IFS API Request : ' + infoStr)
        response = APIManager.ifs_check(infoStr)
        json = simplejson.loads(response)
        log.info('IFS API Response : ' + response)
    except Exception,e:
        log.exception('Exception in IFS Rest API call %s' % repr(e))
    return json

def apply_coupon(agent,coupon_code, profile, cookie_file, request):
    json = futils.get_api_response(request, agent,'order/', cookie_file, 'post', {}, {
        'action': 'APPLY_COUPON',
        'data': {
            'profileId': profile,
            'couponCode': coupon_code
            }
        })
    return json

def remove_coupon(agent, coupon_code, profile, cookie_file, request):
    json = futils.get_api_response(request, agent, 'order/', cookie_file, 'post', {}, {
        'action': 'REMOVE_COUPON',
        'data': {
            'profileId': profile,
            'couponCode': coupon_code
            }
        })
    return json

def apply_order_discount(agent, discount_amount, profile, cookie_file, request, description=None):
    json = futils.get_api_response(request, agent,'order/', cookie_file, 'post', {}, {
        'action': 'APPLY_ORDER_DISCOUNT',
        'data': {
            "profileId": profile,
            "discountAmount": str(discount_amount),
            "discountDescription":"Applying Discount for Top10",
            }
        })
    return json

def auth_order(orderId, agent, action, request, orderAmount, store_id = "-1", auth_code = '000'):
    json = futils.get_api_response(request, agent,'order/', '', 'post', {}, {
        'action': "ORDER_MODIFY",
        'data' : {
            'action' : action,
            'storeId' : store_id,
            'orderId' : orderId,
            'authCode' : auth_code,
            'orderAmount' : orderAmount,
            'conformAgentId' : agent,
            }
        })
    return json

def add_edit_order_shipping_info(shipping_info, order_id, request):
    pass

def add_edit_order_payment_info(payment_info, order_id, request):
    pass



def book_order(order_id, request):
    pass


def refund_order(order_id, request):
    pass
