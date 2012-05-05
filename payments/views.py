# Create your views here.

from utils import utils
from orders.models import Order, OrderItem
from payments.models import *
from accounts.models import PaymentOption
from users.models import Profile, Phone, Email

from django.views.decorators.cache import never_cache
from django.http import HttpResponse, HttpResponseRedirect, HttpResponseBadRequest, HttpResponsePermanentRedirect
from django.utils.safestring import mark_safe
from django.shortcuts import render_to_response, get_object_or_404, redirect
from django.template import RequestContext
from django.db import transaction
from django.conf import settings
from decimal import Decimal, ROUND_FLOOR
from django.core.urlresolvers import reverse
import time
import logging

payment_log = logging.getLogger('fborder')
request_log = logging.getLogger('request')

@never_cache
def process_payment_payback(request):
    # loyaltyTerminalid, sessionid, message, status OR
    # transactionid
    params = request.GET
    if request.method == 'POST':
        params = request.POST
    payment_log.info("Response from payback %s" % params)
    try:
        pa = PaymentAttempt.objects.select_related('order').get(id=params.get('sessionid'))
        if pa.status == 'paid':
            if pa.order.support_state == 'confirmed':
                if request.path.startswith('/w/'):
                    return HttpResponseRedirect(request.path.replace(
                        'process_payment_payback','%s/confirmation' % pa.order.id))
                return HttpResponseRedirect('/orders/%s/confirmation' % pa.order.id)
            else:
                import time
                time.sleep(2)
                if request.path.startswith('/w/'):
                    return HttpResponseRedirect(request.path.replace(
                        'process_payment_payback','%s/confirmation' % pa.order.id))
                return HttpResponseRedirect('/orders/%s/confirmation' % pa.order.id)

    except PaymentAttempt.DoesNotExist:
        request.session['payback_failed_payment'] = "failed"
        return HttpResponseRedirect('/orders/payment_mode')
    pa.process_response(request, params=params)
    return payment_status(request,pa)

@never_cache
def process_payment_ccavanue(request):
    params = request.POST
    payment_log.info("Response from ccavenue %s" % params)
    if request.method == 'GET':
        params = request.GET
    if not params:
        return HttpResponseBadRequest()
    try:
        payment_attempt = PaymentAttempt.objects.select_related('order').get(transaction_id=params['Merchant_Param'])

        if payment_attempt.status != 'pending realization':
            # Wait to avoid race conditions
            time.sleep(1)
            return payment_status(request, payment_attempt)
    except PaymentAttempt.DoesNotExist:
        return HttpResponseBadRequest()

    payment_attempt.process_response(request, params=params)
    return payment_status(request, payment_attempt)

@never_cache
def process_payment_hdfc(request):
    if request.method == 'POST':
        params = request.POST
        payment_log.info("Response from hdfc %s" % params)
        try:
            from payments import hdfcpg
            payment_attempt = PaymentAttempt.objects.select_related('order').get(transaction_id = params.get('trackid',None))
            if payment_attempt.status != 'pending realization':
                # Wait to avoid race conditions
                time.sleep(1)
                return payment_status(request, payment_attempt)
            payment_attempt.process_response(request, params=params)
            return payment_status(request, payment_attempt)
        except PaymentAttempt.DoesNotExist:
            return HttpResponseBadRequest()


@never_cache
def process_payment_citibank(request):
    params = request.POST.get('CititoMall')
    # "0410|813197934204|1|11229118|502200000000|100.00|N:|000000|773882|"
    # "msg code| checksum|1|merchant code| order id| amount|auth des|auth
    # code|trace no|"
    if params.find('||'):
        params = params.replace('||','|ND|')
    param_list = params.split('|')
    trace_number = param_list[8]
    reference_order_id = param_list[4]
    try:
        payment_attempt = PaymentAttempt.objects.select_related('order').get(
                order__reference_order_id=reference_order_id,
                citibanktracenumber__id = int(trace_number),
                )

        if payment_attempt.status != 'pending realization':
            # Wait to avoid race conditions
            time.sleep(1)
            return payment_status(request, payment_attempt)
    except PaymentAttempt.DoesNotExist:
        return HttpResponseBadRequest()
    payment_attempt.process_response(request, params=params)
    return payment_status(request, payment_attempt)

@never_cache
def process_payment_icici(request):
    if request.method == 'POST':
        params = request.POST
        payment_log.info("Got response for icici payment %s" % request.POST)
        try:
            payment_attempt = PaymentAttempt.objects.select_related('order').get(transaction_id=params.get('TxnID',None))

            if payment_attempt.status != 'pending realization':
                # Wait to avoid race conditions
                time.sleep(1)
                return payment_status(request, payment_attempt)
            payment_attempt.process_response(request, params=params)
            return payment_status(request,payment_attempt)
        except PaymentAttempt.DoesNotExist:
            return HttpResponseBadRequest()
    else:
        return HttpResponseBadRequest()

@never_cache
def process_payment_innoviti(request):
    try:
        params = request.POST.get('transresponse')
        payment_log.info("Response from innoviti %s" % params)
        start = params.find('<orderId>')
        start = start + len('<orderId>')
        end = params.find('</orderId>')
        transaction_id = params[start:end]
        payment_attempt = PaymentAttempt.objects.select_related('order').get(transaction_id=transaction_id)
        if payment_attempt.status != 'pending realization':
            # Wait to avoid race conditions
            time.sleep(1)
            return payment_status(request, payment_attempt)
        payment_attempt.process_response(request, params=params)
        return payment_status(request,payment_attempt)
    
    except PaymentAttempt.DoesNotExist:
        return HttpResponseBadRequest()
    except Exception, e:
        return HttpResponseBadRequest()


@never_cache
def process_payment_axis(request):
    if request.method == 'GET':
        params = request.GET
        try:
            merchant_txn_reference = params.get('vpc_MerchTxnRef', None)
            payment_attempt = PaymentAttempt.objects.select_related('order').get(transaction_id=merchant_txn_reference)
            if payment_attempt.status != 'pending realization':
                # Wait to avoid race conditions
                time.sleep(1)
                return payment_status(request, payment_attempt)
            payment_attempt.process_response(request, params=params)
            return payment_status(request,payment_attempt)
        except PaymentAttempt.DoesNotExist:
            return HttpResponseBadRequest()
    else:
        return HttpResponseBadRequest()

@never_cache
def process_payment_amex(request):
    if request.method == 'GET':
        params = request.GET
        try:
            merchant_txn_reference = params.get('vpc_MerchTxnRef', None)
            payment_attempt = PaymentAttempt.objects.select_related('order').get(transaction_id=merchant_txn_reference)
            if payment_attempt.status != 'pending realization':
                # Wait to avoid race conditions
                time.sleep(1)
                return payment_status(request, payment_attempt)
            payment_attempt.process_response(request, params=params)
            return payment_status(request,payment_attempt)
        except PaymentAttempt.DoesNotExist:
            return HttpResponseBadRequest()
    else:
        return HttpResponseBadRequest()

@never_cache
def process_request_paymate(request):
    # XXX What are we trying to do here?
    payment_log.info("paymate Request DATA %s" % request.GET)
    if request.GET:
        params = request.GET
        reference_order_id = params.get('orderId')
        payment_mode = params.get('vendorId')

        pas = PaymentAttempt.objects.select_related('order', 
                'order__user').filter(payment_mode=payment_mode,
                order__reference_order_id=reference_order_id).order_by('-id')[:1]
        if pas:
            pa = pas[0]
            order = pa.order
            done, delta = order.is_payment_done(request)
            if done:
                return HttpResponse('ORDER STATE : %s' % order.support_state)
            
            amount = order.payable_amount
            profile = pa.order.user
            
            phone = profile.get_phone()
            if phone:
                return HttpResponse("000 | %s | %s" % (amount, phone))
            else:
                shipping_phone = order.get_address(request, type='delivery').address.phone
                if shipping_phone:
                    return HttpResponse("000 | %s | %s" % (amount, shipping_phone))
                else:
                    return HttpResponse("05 | Failure")        
        else:
            return HttpResponse("Order is not forwarded to SAP because Order Id is invalid")
    else:
        return HttpResponse("05 | Failure")


@never_cache
def process_response_paymate(request):
    payment_log.info("paymate Response DATA %s" % request.GET)
    if request.GET:
        params = request.GET
        reference_order_id = params.get('orderId')
        payment_mode = params.get('vendorId')
        amount = params.get('TxAmt')
        pas = PaymentAttempt.objects.filter(payment_mode=payment_mode, 
                order__reference_order_id = reference_order_id).order_by('-id')[:1]
        if pas:
            pa = pas[0]
            order = pa.order
            order_amount = order.payable_amount
            done, delta = order.is_payment_done(request)
            if int(order_amount) != int(Decimal(amount)):
                payment_log.info(" Order Amount %s Tx Amount %s" % (order_amount, amount))
                return HttpResponse("Order amount MisMatch ")
            if done:
                return HttpResponse("Order is not forwarded to SAP because either the order needs\
                    to be verified or the order is already submitted")
            try:
                pa.process_response(request, params=params)
                if pa.status == 'paid':
                    return HttpResponse("00 | Success")
                else:
                    return HttpResponse("05 | Failure")
            except Exception, e:
                payment_log.exception("Unable to process paymate order")
                return HttpResponse("05 | Failure")
                
        else:
            #Check this reponse Message
            return HttpResponse("Order is not forwarded to SAP because either the \
                    order needs to be verified or the order is already submitted")
    else:
        return HttpResponse("05 | Failure")


@never_cache
def process_request_atom(request):
    payment_log.info("ATOM Request DATA %s" % request.GET)
    if request.GET:
        params = request.GET
        reference_order_id = params.get('orderId')
        payment_mode = params.get('vendorId')

        pas = PaymentAttempt.objects.select_related('order', 
                'order__user').filter(payment_mode=payment_mode,
                order__reference_order_id=reference_order_id).order_by('-id')[:1]
        if pas:
            pa = pas[0]
            order = pa.order
            done, delta = order.is_payment_done(request)
            if done:
                return HttpResponse('ORDER STATE : %s' % order.support_state)
            
            amount = order.payable_amount
            profile = pa.order.user
            
            email = profile.get_email() 
            if email:
                bank_id = 20
                return HttpResponse("%s | %s | %s" % (amount, email, bank_id))

            else:
                return HttpResponse("Insufficient Data")        
        else:
            return HttpResponse("001 | INVALID ORDER ID")
    else:
        return HttpResponse("Error while retrieving data, please try after some time.")


@never_cache
def process_response_atom(request):
    payment_log.info("ATOM Respone DATA %s" % request.GET)
    if request.GET:
        params = request.GET
        reference_order_id = params.get('orderId')
        payment_mode = params.get('vendorId')
        amount = params.get('TxAmt')
        pas = PaymentAttempt.objects.filter(payment_mode=payment_mode, 
                order__reference_order_id = reference_order_id).order_by('-id')[:1]
        if pas:
            pa = pas[0]
            order = pa.order
            order_amount = order.payable_amount
            done, delta = order.is_payment_done(request)
            if int(order_amount) != int(Decimal(amount)):
                payment_log.info(" Order Amount %s Tx Amount %s" % (order_amount, amount))
                return HttpResponse("Order amount MisMatch ")
            if done:
                return HttpResponse("Order is not forwarded to SAP because either the order needs\
                    to be verified or the order is already submitted")
            try:
                pa.process_response(request, params=params)
                if pa.status == 'paid':
                    return HttpResponse("Success : ORDER IS FORWARDED TO SAP")
                else:
                    return HttpResponse("Order is not forwarded to SAP because either the order needs \
                        to be verified or the order is already submitted")
            except Exception, e:
                payment_log.exception("Unable to process Atom order")
                return HttpResponse("Failure")
                
        else:
            #Check this reponse Message
            return HttpResponse("Incorrect Order Details")
    else:
        return HttpResponse("Error while retrieving data, please try after some time.")


@never_cache
def process_parameters_itz(request):
    payment_log.info(" Itz Server response %s" % request.POST)
    params = request.POST
    pa = None
    description = { '0'    : "Success",
                    '3100' : "Transaction is already confirmed",
                    '-3100': "Communication Error at the Merchant's End",
                    '-3101': "Internal Error at the Merchant's End",
                    '-3103': "Transaction Confirmation Error at the Merchant's End",
                    '-3105': "Invalid Order ID",
                    '-3106': "Invalid Request/Action Type",
                    '-3107': "Invalid Request Data - Product cost doesn't match",
                   }
    response_code = "-3101"
    if params:
        try:
            pa = PaymentAttempt.objects.get(id=int(params.get('orderid')))
            if str(int(pa.amount*100)) != str(params.get('productcost')):
                response_code = '-3107'
            else:
                order = pa.order
                if order.state == "confirmed":
                    response_code = '3100'
                else:
                    response_code = '0'
                    pa.response = '0'
                    pa.save()
        except Exception, e:
            response_code = "-3105"
    else:
        response_code = '-3106'
    payment_log.info("Response code sent to ITZ %s" % response_code)
    return HttpResponse('%s,%s' %(response_code, description.get(response_code)))

@never_cache
def process_payment_itz(request):
    if request.POST:
        params = request.POST
        try:
            #url_token = params.get('url_token')
            #request.call['url_token'] = url_token
            #request.call[id] = url_token.split('-')[3]
            #log.info(" url token is %s " % url_token)
            response_code = params.get('responsecode')
            pa = PaymentAttempt.objects.get(id=params.get('orderid'))
        except PaymentAttempt.DoesNotExist:
            request.session['failed_payment'] = "ITZ Payment Failed"
            return HttpResponseRedirect('orders/shipping')
        except Exception, e:
            return HttpResponseBadRequest()
        
        pa.process_response(request)
        return payment_status(request,pa)
    
    else:
        return HttpResponseBadRequest()

@never_cache
def process_payment_suvidha(request):
    payment_log.info("Suvidha Payment Request %s" % request.GET)
    if request.method != 'GET':
        resp = HttpResponse('04', 'System failure. Please try again after some time')
        return resp
    
    order_id = None
    payment = None
    try:
        order_id = request.GET.get('orderId','')
        payment_log.info("Payment Request Check%s" % order_id)
        try:
            atg_payment_url = getattr(settings, 'ATG_PAYMENT_URL', '')
            start_index = int(order_id[:3])
            if start_index < 505:
                return redirect("http://%s/payments/sv/request?orderId=%s" \
                        % (atg_payment_url, order_id))
        except:
            return HttpResponse('02','Invalid Order ID')
        
        if not order_id.isdigit():
            return HttpResponse('03', 'Invalid Order ID')
        
        order = Order.objects.get(reference_order_id=order_id)
        if order.support_state == 'cancelled':
            return HttpResponse('02', 'Order is cancelled')
        if order.support_state != 'booked':
            return HttpResponse('03','Invalid order ID')
        if order.payment_mode != 'cash-collection':
            return HttpResponse('06', 'Payment type for the requested order is not Suvidha')

        payments = order.get_payments(request, filter=dict(status__in=['unpaid','info received'],
            payment_mode='cash-collection', gateway='SUVI'))[:1]
        if payments:
            payment = payments[0]
        else:
            return HttpResponse('06', 'Payment type for the requested order is not Suvidha')
    except Order.DoesNotExist:
        return HttpResponse('02','Invalid Order ID')
    except Exception, e:
        payment_log.exception('Support: order confirmation (%s) - %s' % (order_id,
            repr(e)))
        return HttpResponse('04', 'System failure. Please try again after some time')
    
    try:
        new_state = 'paid'
        payment_done, delta = order.is_confirm_allowed(request)
        amount = delta
        data = dict(amount=amount, notes='Payment confirmation from suvidha',
            payment_realized_on=datetime.now())
        with transaction.commit_on_success():
            #start transaction
            payment.move_payment_state(request, data=data, suvidha=True, new_state=new_state)
    except PaymentAttempt.InvalidOperation:
        payment_log.exception('Support: order_confirm %s - Invalid payment operation' % order.id)
    except PaymentAttempt.InsufficientData:
        payment_log.exception('Support: order_confirm %s - Insufficient data' % order.id)
    except Order.InvalidOperation:
        payment_log.exception('Support: order_confirm %s - Invalid order operation' % order.id)
    except Order.InsufficientPayment, e:
        payment_log.exception('Support: order_confirm %s - Insufficient Payment (%.2f)' % (order.id, e.delta))
    except Order.XMLCreationFailure:
        payment_log.exception('Support: order_confirm %s - XML creation failure' % order.id)
    except Exception, e:
        payment_log.exception('Support: order_confirm %s - %s' % (order.id, repr(e)))
    else:
        message = '01, Successful'
        message += '<br />Order ID: %s' % order.id
        message += '<br />Customer Name: %s' % order.user.full_name
        message += '<br />Amount: %.2f' % amount
        return HttpResponse(message)
    return HttpResponse('System failure. Please try again after some time')




@never_cache
def process_request_itzcash(request):
    payment_log.info("ITZ CASH Request DATA %s" % request.GET)
    if request.GET:
        params = request.GET
        reference_order_id = params.get('orderId')
        vendor = params.get('vendorId')
        try:
            atg_payment_url = getattr(settings, 'ATG_PAYMENT_URL', '')
            start_index = int(reference_order_id[:3])
            if start_index < 505:
                return redirect("http://%s/b2c/order/vendor/request?orderId=%s&vendorId=%s" \
                        % (atg_payment_url, reference_order_id, vendor))
        except:
            return HttpResponse("007 | INTERNAL SERVER ERROR")

        if vendor == 'itz':
            payment_mode = 'cash-collection'
            pas = PaymentAttempt.objects.select_related('order', 
                    'order__user').filter(gateway='ITZC', payment_mode=payment_mode,
                    order__reference_order_id=reference_order_id).order_by('-id')[:1]
            if pas:
                pa = pas[0]
                order = pa.order
                done, delta = order.is_payment_done(request)
                if done:
                    return HttpResponse("004 | ORDER CONFIRMED")
                
                amount = order.payable_amount
                profile = pa.order.user
                
                phone = profile.get_phone() 
                if phone:
                    return HttpResponse("000 | %s | %s | %s" % (amount, phone, order.support_state.upper()))
                else:
                    shipping_phone = order.get_address(request, type="delivery").address.phone
                    if shipping_phone:
                        return HttpResponse("000 | %s | %s | %s" % (amount, shipping_phone, order.support_state.upper()))
                    else:
                        payment_log.info("No phone found for user %s" % order.user)
                        return HttpResponse("Insufficient Data")        
            else:
                return HttpResponse("001 | INVALID ORDERID")
        else:
            return HttpResponse("001 | INVALID ORDERID")
    else:
        return HttpResponse("Insufficient Data")


@never_cache
def process_response_itzcash(request):
    payment_log.info("ITZ CASH Response DATA %s" % request.GET)
    if request.GET:
        params = request.GET
        reference_order_id = params.get('orderId')
        vendor = params.get('vendorId')
        amount = params.get('TxAmt')
        try:
            start_index = int(reference_order_id[:3])
            if start_index < 505:
                atg_payment_url = getattr(settings, 'ATG_PAYMENT_URL', '')
                return redirect("http://%s/b2c/order/vendor/response?\
                        orderId=%s&authCode=%s&PgTxId=%s&ITZTxId=%s&TxAmt=%s&Rrn=%s&ResCode=%s&vendorId=%s"\
                        % (atg_payment_url, reference_order_id, params.get('authCode'), params.get('PgTxId'), 
                            params.get('ITZTxId'), amount, params.get('Rrn'), params.get('ResCode'), vendor))
        except:
            return HttpResponse("007 | INTERNAL SERVER ERROR")
        
        if vendor == 'itz':
            payment_mode = 'cash-collection'
            pas = PaymentAttempt.objects.select_related('order').filter(gateway='ITZC', 
                    payment_mode=payment_mode, 
                    order__reference_order_id=reference_order_id).order_by('-id')[:1]
            if pas:
                pa = pas[0]
                order = pa.order
                order_amount = order.payable_amount
                done, delta = order.is_payment_done(request)
                if int(order_amount) != int(Decimal(amount)):
                    payment_log.info(" Order Amount %s Tx Amount %s" % (order_amount, amount))
                    return HttpResponse("002 | ORDER AMOUNT MISMATCH")
                if done:
                    return HttpResponse("004 | PAYMENT IS ALREADY RECEIVED")
                else:
                    try:
                        pa.process_response(request, params=params)
                        if pa.status == 'paid':
                            return HttpResponse("000 | ORDER IS FORWARDED TO SAP")
                        else:
                            return HttpResponse("004 | PAYMENT IS ALREADY RECEIVED")
                    except:
                        return HttpResponse("007 | INTERNAL SERVER ERROR")
                    
            else:
                return HttpResponse("001 | INVALID ORDERID")
        else:
            return HttpResponse("001 | INVALID ORDERID")
    else:
        return HttpResponse("007 | INTERNAL SERVER ERROR")


def payment_status(request,payment_attempt):
    
    if payment_attempt.status.lower() in ('paid', 'in verification'):
        #payment_attempt.order.confirm(request)
        utils.clear_cart(request, payment_attempt.order)
        confirmed_orders_in_session = request.session.get(
                'confirmed_orders', [])
        confirmed_orders_in_session.append(payment_attempt.order.id)
        request.session['confirmed_orders'] = confirmed_orders_in_session
        if utils.is_franchise(request):
            return HttpResponseRedirect('/orders/%s/confirmation' % payment_attempt.order.id)
        
        elif utils.is_cc(request):
            return HttpResponseRedirect(request.path.replace('book',
                '%s/booked' % payment_attempt.order.id))
        
        elif request.path.startswith('/w/'):
            return HttpResponseRedirect(request.path.replace(
                'process_payment','%s/confirmation' % payment_attempt.order.id))
        else:
            return HttpResponseRedirect('/orders/%s/confirmation' % payment_attempt.order.id)
    else:
        if payment_attempt.status.lower() == 'rejected':
            order = payment_attempt.order
            delta_oi = []
            order_items = order.get_order_items(request, exclude=dict(state__in=['cancelled','bundle_item']))
            for item in order_items:
                delta_oi.append({'order_item':item, 'qty':item.qty, 'amount':item.payable_amount()})
            order.update_inventory(request, action='add', delta=delta_oi)

        if payment_attempt.response == '!YM':
            request.session['failed_payment'] = 'Sorry, your transaction is authorized but could not be processed due to incorrect billing address/pin code entered. The authorized amount will be reversed automatically in your card account. For more details please call your bank.'
        else:
            request.session['failed_payment'] = 'Your payment got Rejected/Cancelled. Please try again with another card'
        
        payment_log.info(" Payment Failed Client is %s " % request.client)
        
        if utils.is_franchise(request):
            return HttpResponseRedirect('/orders/shipping')
        
        elif utils.is_cc(request):
            return HttpResponseRedirect(request.path)
        
        elif utils.is_future_ecom(payment_attempt.order.client):
                request.session['http_referer'] = 'payment_status'
                return HttpResponseRedirect('/orders/payment_mode/')
        else:
            return HttpResponseRedirect('/orders/shipping')


@never_cache
def confirmation(request, order_id):
    from web.views.user_views import signup
    error = None
    is_email_success = False
    if "sign_up" in request.POST:
        return signup(request, page="confirmation")
     
    order = Order.objects.get(id=order_id)
    # check if this order_id exists in confirmed orders in this session
    if order.id not in request.session.get('confirmed_orders',[]):
#       # users can still visit confirmation page of their own orders
        #if request.user.is_authenticated() and request.user.id != order.user.user.id:
#           # not confirmed in this session, does not belong to this user either. lets lie
        raise Http404
    
    password = None
    username = None
    try:
        profile = order.user
        auth_user = profile.user
        username = auth_user.username
        password = auth_user.password
        if password == '!':
            password = None
        if is_email_success and not error:
            password = None
    except:
        payment_log.exception("Guest User")

    try:
        deliveryinfo = order.get_address(request, type='delivery')
    except DeliveryInfo.DoesNotExist:
        deliveryinfo = None
    
    similar_products = []
    try:
        order_items = order.get_order_items(request, select_related=('seller_rate_chart__product',),
            exclude=dict(state__in=['cancelled','bundle_item']))
        for order_item in order_items:
            rate_chart = order_item.seller_rate_chart
            similar_product = rate_chart.product.similar_products(request)
            if similar_product:
                #similar_products.append(similar_product)
                similar_products.extend(similar_product)
    except OrderItem.DoesNotExist:
        order_item = None
    
    #TODO why is this needed?? Error: order_item not present
    #fb_share_link = "%s/%s/pd/%s/" % (request.get_host(),order_item.seller_rate_chart.product.slug,order_item.seller_rate_chart.product_id)
    fb_share_link = ''

    dgm_sku_code = None
    if order.coupon:
        dgm_sku_code = 661193132812
    elif order.payable_amount > 250:
        dgm_sku_code = 214361427476
    else:
        dgm_sku_code = 858389242533
    
    address_info = {
        'first_name':mark_safe(deliveryinfo.address.first_name),
        'last_name':mark_safe(deliveryinfo.address.last_name),
        'address':mark_safe(deliveryinfo.address.address.strip()),
        'city':mark_safe(deliveryinfo.address.city),
        'pincode':mark_safe(deliveryinfo.address.pincode),
        'state':mark_safe(deliveryinfo.address.state),
        'country':mark_safe(deliveryinfo.address.country),
        'phone':mark_safe(deliveryinfo.address.phone),
        }
    
    earn_map = PointsHeader.EARN_POINTS_MAP
    points_ratio = earn_map.get(order.client.name)
    payback_points_earned = (order.payable_amount*Decimal(points_ratio)).quantize(Decimal('1')) if order.payback_id else 0
    
    total_order_qty = order.get_item_count()
    
    insufficient_payment = request.session.get('insufficent_payment')
    if insufficient_payment:
        del request.session['insufficient_payment']
    # Get recently viewed products
    recently_viewed_products = utils.get_recently_viewed(request, order.user, count=4)
    recently_viewed_ctxt = utils.create_context_for_search_results(recently_viewed_products, request)
    products_ctxt = {}
    if not recently_viewed_ctxt:
        # Get todays deals
        todays_deals = DailyDeal.objects.filter(status='published',type='todays_deals',\
                       starts_on__lte=datetime.now(),ends_on__gte=datetime.now(), client=request.client.client)
        if todays_deals:
            todays_deal = todays_deals[0]
            deal_products = todays_deal.dailydealproduct_set.values('product').all().order_by('order')[:4]
            todays_deals_products = [deal['product'] for deal in deal_products]
            todays_deals_ctxt = utils.create_context_for_search_results(todays_deals_products, request)
            products_ctxt['label'] = "TODAY'S DEALS"
            products_ctxt['data'] = todays_deals_ctxt
    else:
        products_ctxt['label'] = "YOU RECENTLY VIEWED"
        products_ctxt['data'] = recently_viewed_ctxt
                
    return render_to_response("order/confirmed.html", {
        "order" :order,
        "order_items" :order_items,
        "deliveryinfo":deliveryinfo,
        "fb_share_link":fb_share_link,
        "similar_products":similar_products,
        "address_info":address_info,
        "confirmed":True,
        "payback_points_earned": payback_points_earned,
        "total_order_qty":total_order_qty,
        "total_items" : order.get_item_count(),
        "dgm_sku_code":dgm_sku_code,
        "insufficient_payment":insufficient_payment,
        "password":password,
        "username":username,
        "next":request.path,
        "signup_error":error,
        "is_email_success":is_email_success,
        "ga_states":["confirmed", "booked"],
        "products_ctxt":products_ctxt,
        }, context_instance = RequestContext(request))

def get_payment_form(request, **kwargs):
    payment = kwargs.get('payment')
    payment_id = kwargs.get('payment_id')
    data = kwargs.get('data')
    new_state = kwargs.get('new_state')
    if not (payment or payment_id):
        return None
    if not payment:
        payment = PaymentAttempt.objects.get(pk=payment_id)

    from payments.forms import PaymentAttemptForm
    form = None
    if payment.payment_mode not in ['cheque','cash-collection','deposit-transfer']:
        return form
    if new_state in ['info received','pending realization','paid']:
        form = PaymentAttemptForm(data)
        form.fields['instrument_no'].initial = payment.instrument_no
        form.fields['instrument_issue_bank'].initial = payment.instrument_issue_bank
        if payment.instrument_recv_date:
            form.fields['instrument_recv_date'].initial = payment.instrument_recv_date.strftime('%d %b %Y')
        form.fields['amount'].initial = payment.amount
        form.fields['notes'].initial = payment.notes
        if payment.payment_mode in ['cash-collection','deposit-transfer']:
            form.fields.pop('instrument_no')
            form.fields.pop('instrument_issue_bank')
            form.fields.pop('instrument_recv_date')
            if new_state == 'paid':
                form.fields.pop('gateway')
        if payment.payment_mode == 'cheque':
            if new_state == 'info received':
                form.fields.pop('instrument_recv_date')
            if new_state == 'paid':
                form.fields.pop('pg_transaction_id')
        if new_state in ['info received','pending realization']:
            form.fields.pop('pg_transaction_id')
            form.fields.pop('payment_realized_on')
            form.fields.pop('gateway')
    return form

def get_refund_form(request, **kwargs):
    refund = kwargs.get('refund')
    refund_id = kwargs.get('refund_id')
    data = kwargs.get('data')
    new_state = kwargs.get('new_state')
    if not (refund or refund_id):
        return None
    if not refund:
        refund = Refund.objects.get(pk=refund_id)

    data = kwargs.get('data')
    
    from payments.forms import RefundForm
    form = None
    if new_state in ['closed','failed']:
        form = RefundForm(data)
        form.fields['amount'].initial = refund.amount
    return form

