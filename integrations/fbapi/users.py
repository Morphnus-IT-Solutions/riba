from integrations.fbapi import fbapiutils as futils
import logging
from utils.fields import phone_regex
from django.core.validators import email_re
from riba.users.models import Email, Phone
import datetime
import utils
from django.utils import simplejson
log = logging.getLogger('request')

def get_user_by_mobile(mobile, agent, cookie_file, request):
    json = futils.get_api_response(request, agent, 'user/', cookie_file, 'get', {'phone':mobile})
    return json

def get_user_by_login(login, agent, cookie_file, request):
    json = futils.get_api_response(request, agent, 'user/', cookie_file, 'get', {'phone':login})
    return json

def get_user_by_email(email, agent, cookie_file, request):
    json = futils.get_api_response(request, agent, 'user/', cookie_file, 'get', {'phone':email})
    return json

def create_user(phone, email, agent, cookie_file, request, password='kms829%HJ', confirm_password='kms829%HJ'):
    json = futils.get_api_response(request, agent, 'user/', cookie_file, 'post', {}, {
        'action': 'create_user',
        'data': {
            'mobileNumber': phone,
            'email': email,
            'password': password,
            'confirmPassword': confirm_password, 
            }
        })
    return json

def logoff(profile, agent, cookie_file, request):
    # logs off the current user
    json = futils.get_api_response(request, agent, 'user/', cookie_file, 'post', {}, {
        'action': 'logout',
        'data': {
            'profileId':profile
            }
        })
    return json

def submit_cart(params, agent, profile, cookie_file, request):
    params = simplejson.loads(simplejson.dumps(params))
    json = futils.get_api_response(request, agent, 'user/', cookie_file, 'post', {}, {
        'action': 'submit_cart',
        'data': {
            'profileId': profile,
            'orderNote': params.get('order_note',''),
            'paymentMode': params.get('payment_mode', ''),
            'receivedBy': params.get('received_by',''),
            'emiDetails':params.get('emi_details',{}),
            'subPayType': params.get('sub_pay_type',''),
            'currentPriceList': params.get('current_price_list',''),
            'orderAmount': params.get('order_amount',''),
            'transactionAmount': params.get('order_amount',''),
            'pointsTransactionId': "%s" % params.get('sessionid',''),
            'terminalId': "%s" % params.get('loyaltyTerminalid'),
            'status': params.get('status'),
            'pinCode': "%s" % params.get('pincode',''),
            'pgResponse': params.get('pg_response',{}),
            'shippingPostalCode': "%s" % params.get('shipping_postal_code', ''),
            'freeOrder': params.get('free_order',''),
            'loyaltyCardNumber': params.get('payback_id', ''),
            'Status':params.get('Status',''),
            }
        })
    return json

def submit_store_cart_card(params, agent, profile, cookie_file, request, store_id="-1", auth_code='000'):
    json = futils.get_api_response(request, agent, 'user/', cookie_file, 'post', {}, {
        'action': 'submit_store_cart',
        'data': {
            'paymentMode': params.get('payment_mode', ''),
            'currentPriceList': params.get('current_price_list',''),
            'orderAmount': params.get('order_amount',''),
            'pgResponse':params.get('pg_response',{}),
            'profileId': profile,
            'action' : 'Booked',
            'orderAmount' : params.get('order_amount',''),
            'storeId' : store_id,
            'dateTime': str(datetime.datetime.now()),
            'bookAgentId' : agent,
            'authCode':auth_code,
            'orderId':params.get('order_id',''),
            }
        })
    return json

def submit_store_cart_cash(params, agent, profile, cookie_file, request, store_id="-1", auth_code='000'):
    json = futils.get_api_response(request, agent, 'user/', cookie_file, 'post', {}, {
        'action': 'submit_store_cart',
        'data': {
            'profileId': profile,
            'paymentMode': params.get('payment_mode', ''),
            'receivedBy': params.get('received_by',''),
            'currentPriceList': params.get('current_price_list','plist130003'),
            'orderAmount': params.get('order_amount',''),
            'pinCode':params.get('pincode',''),
            'shippingPostalCode': params.get('shipping_postal_code', ''),
            'storeId' : store_id,
            'dateTime': str(datetime.datetime.now()),
            'bookAgentId' : agent,
            'authCode':auth_code,
            'action':'Booked',
            'orderId':params.get('order_id',''),
            }
        })
    return json

def update_user(shipping_address, billing_address, agent, profile, cookie_file, request):
    json = futils.get_api_response(request, agent, 'user/', cookie_file, 'post', {}, {
        'action': 'update_user',
        'data': {
                'profileId': profile,
                'shippingAddress': {
                    'firstName':  shipping_address['first_name'],
                    'lastName': shipping_address['last_name'],
                    'address1': shipping_address['address'],
                    'city': shipping_address['city'],
                    'state': shipping_address['state'],
                    'country': shipping_address['country'],
                    'postalCode': shipping_address['postal_code'],
                    'phoneNumber': shipping_address['phone_number'],
                },
                'billingAddress': {
                    'firstName':  billing_address['first_name'],
                    'lastName': billing_address['last_name'],
                    'address1': billing_address['address'],
                    'city': billing_address['city'],
                    'state': billing_address['state'],
                    'country': billing_address['country'],
                    'postalCode': billing_address['postal_code'],
                    'phoneNumber': billing_address['phone_number'],
                }
            }
        })
    return json

def authenticate_user(login, password, agent, cookie_file, request):
    json = futils.get_api_response(request, agent, 'user/', cookie_file, 'post', {}, {
        'action': 'login_pwd',
        'data': {
            'login':login,
            'password':password
            }
        })
    return json

def sync_atg_user(atg_user_name, profile=None):
    from tinla.users.models import Email, Phone
    if not atg_user_name:
        return
    try:
        if not profile:
            if email_re.match(atg_user_name):
                try:
                    e = Email.objects.get(email=atg_user_name)
                    profile = e.user
                except Email.DoesNotExist:
                    pass
            elif phone_regex.match(atg_user_name):
                try:
                    p = Phone.objects.get(phone=atg_user_name)
                    profile = p.user
                except Phone.DoesNotExist:
                    pass
            if not profile:
                # not able to find a matching user in tinla database
                # create new profile and user
                user, profile = utils.utils.get_or_create_user(atg_user_name)
        profile.atg_username = atg_user_name
        profile.save()
        return profile
    except Exception, e:
        log.exception('Error syncing atg user %s' % repr(e))
    return None

def sync_user(atg_user_json, profile=None):
    if not atg_user_json:
        return
    return sync_atg_user(atg_user_json.get('login',''))
