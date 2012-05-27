# Create your views here.
from django.http import HttpResponse, Http404
#from dialer.models import Campaign, Response, Attempt, ResponseStatus, ResponseOrders
#from catalog.models import Brand
#from asterisk.models import Agent, Task, Call
from datetime import datetime, timedelta
import random
import logging
from django.utils import simplejson
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.exceptions import ValidationError
#from bl.orders import getOrdersByCallId
#from ui.views import attach_response_to_user
#from apiutils import normalize_phone
from users.models import Profile, Phone, Email as UserEmail, NewsLetter, DailySubscription
from utils import utils
from web.forms import FBRegisterForm
import re

log = logging.getLogger('ccc')
API_KEYS = {'6a1f7254d4d0229d3207c9079e7cb3f5': {'secret':'2cf1338762fe5f89a3d5ffeccff5bdf1','brand_id':1}}

#def return_api_response(request, status, msg_code, msg, http_code, data=None):
#    resp = dict(msg_code = msg_code, msg = msg, status = status)
#    if data:
#        resp['data'] = data
#    return HttpResponse(simplejson.dumps(resp), mimetype="application/json",
#            status=http_code)
#
#def validate_api_request(request, *args, **kwargs):
#    if request.method != 'POST':
#        return return_api_response(request, 'FAIL', 'HTTP_METHOD_ERROR',
#                'Invalid HTTP Method. Method should be post', 400)
#    if 'HTTP_X_CHP_API_KEY' not in request.META:
#        return return_api_response(request, 'FAIL', 'UNAUTHORIZED',
#                'You have not supplied api key', 401)
#    api_key = request.META.get('HTTP_X_CHP_API_KEY','')
#    if not api_key or api_key not in API_KEYS.keys():
#        return return_api_response(request, 'FAIL', 'UNAUTHORIZED',
#                'Incorrect api key.', 401)
#    if not request.POST:
#        return return_api_response(request, 'FAIL', 'NO_DATA',
#                'No data posted.', 400)
#    try: 
#        # cool, lets return the json. we can put encryption at late stage
#        json = simplejson.loads(request.POST.keys()[0])
#        return json
#    except simplejson.decoder.JSONDecodeError, e:
#        log.exception('Error parsing json %s', repr(e))
#        return return_api_response(request, 'FAIL', 'INVALID_JSON',
#                'Not able to parse json. Please check post data.', 400)
#
#def response_info(request, *args, **kwargs):
#    attempt = Attempt.objects.get(pk=int(attempt_id))
#    response = attempt.response
#    campaign = response.campaign
#    brand = response.brand
#    statuses = [status for status in ResponseStatus.objects.filter(campaign=campaign)]
#    previous_attempts = Attempt.objects.filter(response=response).exclude(pk=int(attempt_id))
#    results = [attempt, response, campaign, brand] + statuses + previous_attempts
#    json = serializers.serialize('json',results)
#    return HttpResponse(json)
#
#def post_responses(request, *args, **kwargs):
#    resp = {}
#    try: 
#        json = validate_api_request(request, *args, **kwargs)
#        if not isinstance(json, dict): return json
#        responses = json.get('responses',[])
#        if not insintance(responses, list):
#            return return_api_response(request, 'FAIL', 'INVALID_JSON',
#                    'Responses is not an array', 400)
#        brand_id = API_KEYS[request.META.get('HTTP_X_CHP_API_KEY')]['brand_id']
#        brand = Brand.objects.get(pk=brand_id)
#        campaign = Campaign.objects.get(brand=brand,status=
#                'Active', type='Outbound')[0]
#        to_add = []
#        for response in responses:
#            r = Response()
#            r.phone = response.get('phone','')[:15]
#            r.name = response.get('name', '')[:26]
#            r.email = response.get('email', '')[:75]
#            r.address_line1 = response.get('address_line1','')[:300]
#            r.address_line2 = response.get('address_line2','')[:300]
#            r.location = response.get('location','')[:100]
#            r.city = response.get('city','')[:100]
#            r.province = response.get('province','')[:100]
#            r.country = reponse.get('country','india')[:100]
#            r.pin = response.get('pin','')[:10]
#            r.message = response.get('message', '')
#            # add a brand to response
#            r.brand = brand
#            # add a campaign to response
#            r.campaign = campaign 
#            # add response to the db.
#            try:
#                r.full_clean()
#            except ValidationError, ve:
#                return return_api_response(request, 'FAIL', 'VALIDATION_ERROR',
#                    'Invalid data %s ' % str(response), 500)
#            to_add.append(r)
#        for obj in to_add:
#            obj.save()
#    except Exception, e:
#        log.exception('Error posting responses %s', repr(e))
#        return return_api_response(request, 'FAIL', 'SYSTEM_ERROR',
#                'Sorry. Our system is behaving badly. Please try later.', 500)
#
#def extract_user(request):
#    is_manager = request.user.has_perm('dialer.add_campaign')
#    agent = None
#    if not is_manager:
#        agent = Agent.objects.get(name=request.user.username)
#    if request.user.is_superuser:
#        try:
#            agent = Agent.objects.get(name=request.user.username)
#        except Agent.DoesNotExist:
#            pass
#    return (is_manager,agent)
#
#def call_response(request, response_id):
#    if not request.method == 'POST':
#        return return_api_response(request, 'FAIL', 'INVALID_HTTP_METHOD',
#                'Invalid http method. Method should be post', 400) 
#    is_manager, agent = extract_user(request)
#    if not agent:
#        return return_api_response(request, 'FAIL', 'NO_AGENT_ATTACHED',
#                'Cannot place call, you dont have attached agent id.', 400) 
#    try:
#        response = Response.objects.get(pk=response_id)
#        task = Task(agent=agent, response=response, type='call_by_agent_to_response')
#        task.save()
#        return return_api_response(request, 'SUCCESS', 'CALL_PLACED',
#                'Call placed', 200)
#    except Response.DoesNotExist:
#        return return_api_response(request, 'FAIL', 'NO_SUCH_RESPONSE',
#                'Cannot place call, unable to find requested response.', 404)
#    except Exception, e:
#        log.exception('error calling response %s' % repr(e))
#        return return_api_response(request, 'FAIL', 'SYSTEM_ERROR',
#                'Cannot place call. Please try later.', 500)
#
#def close_response_on_order_confirmed(response, request):
#    try:
#        confirmed_status = ResponseStatus.objects.get(campaign=response.campaign, name='Confirmed', type='Order')
#        response.state = 'Order'
#        response.status = confirmed_status
#        response.save()
#        return return_api_response(request, 'SUCCESS', 'CLOSED_RESPONSE',
#                'Closed response on confirmed orders', 200)
#    except Exception, e:
#        log.exception('error closing response after confirmed order %s' % repr(e))
#        return return_api_response(request, 'FAIL', 'UKNOWN_ERROR',
#                'Error closing response', 500)
#        
#def order_confirmed_get(request):
#    try:
#        order_id = request.GET.get('order','')
#        call_id = request.GET.get('call','')
#        if not order_id:
#            return HttpResponse('done')
#        try:
#            ros = ResponseOrders.objects.get(order_id = order_id)
#            return close_response_on_order_confirmed(ros.response, request)
#        except ResponseOrders.DoesNotExist:
#            # no order is attached to this order. try looking at the attempts
#            if call_id:
#                try:
#                    attempt = Attempt.objects.get(call_id=call_id)
#                    return close_response_on_order_confirmed(attempt.response, request)
#                except Attempt.DoesNotExist:
#                    return HttpResponse('done')
#            return HttpResponse('No order')
#    except Exception, e:
#        log.exception('error reacting to order confirmed event %s' % repr(e))
#        return HttpResponse('error')
#
#def order_confirmed(request):
#    try:
#        json = simplejson.loads(request.POST.keys()[0])
#        call_id = json.get('callId','')
#        order_id = json.get('orderId','')
#        try:
#            ros = ResponseOrders.objects.get(order_id = order_id)
#            return close_response_on_order_confirmed(ros.response, request)
#        except ResponseOrders.DoesNotExist:
#            # no order is attached to this order. try looking at the attempts
#            if call_id:
#                try:
#                    attempt = Attempt.objects.get(call_id=call_id)
#                    return close_response_on_order_confirmed(attempt.response, request)
#                except Attempt.DoesNotExist:
#                    return HttpResponse('done')
#    except Exception, e:
#        log.exception('error reacting to order confirmed event %s' % repr(e))
#        return HttpResponse('done')
#
#def attempt_detail(request, attempt_id):
#    # given an attempt, return details of attempt
#    try:
#        attempt = Attempt.objects.select_related(
#                'response','response__status','response__campaign','pre_response_status'
#                ).get(pk=attempt_id)
#        campaign = attempt.response.campaign
#        resp_statuses = ResponseStatus.objects.filter(campaign=campaign)
#        # weed out response statuses which cannot be set
#        log.info(attempt.response)
#        allowed_statuses = [ status for status in resp_statuses 
#                if (attempt.response.can_go_to(status) and status.type != 'Attempted' and status.type != 'New' and status.type != 'Shipped' and status.type !='Delivered')]
#        attempt_statuses = [ status for status in resp_statuses
#                if status.type == 'Attempted' ]
#
#        data = {}
#        data['attempt_id'] = attempt_id
#        data['current_status'] = dict(id = attempt.pre_response_status.id, name = attempt.pre_response_status.name)
#        data['next_statuses'] = [dict(name=status.name, id=status.id, type=status.type) for status in allowed_statuses]
#        data['campaign'] = dict(name = campaign.name, script = campaign.script) 
#        data['attempt_statuses'] = [dict(name=status.name, id=status.id, type=status.type) for status in attempt_statuses]
#
#        data['attempt_history'] = []
#
#        return return_api_response(request, 'SUCCESS', 'SUCCESS',
#                '', 200, data)
#    except Attempt.DoesNotExist:
#        return return_api_response(request, 'FAIL', 'NO_SUCH_ATTEMPT',
#                'Cannot get attempt details, no such attempt.', 404)
#    except Exception, e:
#        log.exception('error fetching attempt details %s' % repr(e))
#        return return_api_response(request, 'FAIL', 'SYSTEM_ERROR',
#                'Cannot get attempt details', 500)
#
#def update_attempt(request, attempt_id):
#    try:
#        attempt = Attempt.objects.get(pk=attempt_id)
#        response = attempt.response
#        campaign = response.campaign
#        json = simplejson.loads(request.POST.keys()[0])
#        log.info(str(json))
#
#        call_id = json.get('call_id','')
#        call_status = json.get('call_status','')
#        new_status = None
#        if call_status != 'Answered':
#            # get the status associated
#            new_status = ResponseStatus.objects.get(campaign=campaign, type='Attempted', name=call_status)
#        else:
#            new_status = ResponseStatus.objects.get(pk=json.get('resp_status',''))
#
#        if call_status == 'Answered':
#            if not response.can_go_to(new_status):
#                return return_api_response(request, 'FAIL', 'BAD_REQUEST',
#                    'Cannot set response status from %s to %s' % (response.status.name, new_status.name), 400)
#        if response.closed:
#            return return_api_response(request, 'FAIL', 'BAD_REQUEST',
#                'This response is already closed', 400)
#        if not attempt.is_open():
#            return return_api_response(request, 'FAIL', 'BAD_REQUEST',
#                'This attempt is already closed', 400)
#
#
#        attempt.state = call_status
#        attempt.comments = json.get('comments','')
#        if call_id:
#            attempt.call_id = call_id
#
#        if attempt.type  == 'agent_first':
#            response.last_called_by = attempt.agent
#
#        fmt = '%m/%d/%Y %I:%M %p'
#        if json.get('next') and json.get('next') != ' 10:00 AM':
#            next_call = datetime.strptime(json.get('next',''), fmt)
#            response.next_call = next_call
#
#        response.last_call = attempt.time
#
#        pending_order_generated = False
#        if call_status != 'Answered':
#            if call_status != 'Congestion':
#                response.attempts += 1
#                if response.attempts % 5 == 0 and response.attempts > 1:
#                    response.closed = True
#            else:
#                attempt.valid = False
#        else:
#            # call is answered, lets check if any orders are generated
#            response.attempts += 1
#            response.connections += 1
#            # no locks!!
#            # response.borrowed_by = attempt.agent
#            try:
#                orders = getOrdersByCallId(call_id, 'pending_order')
#                log.info(orders)
#                if orders:
#                    pending_order_generated = True
#                    for order in orders:
#                        try:
#                            ro = ResponseOrders(order_id=order['id'], response=response)
#                            ro.save()
#                        except Exception, roex:
#                            log.exception('error saving order created in response %s' % repr(e))
#            except Exception, e:
#                log.exception('error getting order items for call %s' % repr(e))
#
#        if attempt.valid:
#            # invalid attempts should not change status
#            response.status = new_status
#            response.state = new_status.type
#            if pending_order_generated:
#                if response.state in ['Attempted','Connected','Product Details']:
#                    # response is still not qualified.
#                    if new_status.type != 'Pending Order':
#                        # we know that response is qualifed, but agent doesnt seem to think so
#                        # we override agent's decision here.
#                        response.state = 'Pending Order'
#                        new_status = ResponseStatus.objects.get(campaign=campaign, type='Pending Order', name='Sent')
#                        response.status = new_status
#
#            response.closed = new_status.close_response
#        # its okay to save what agent tried to, even if the attempt is invalid
#        attempt.post_response_status = new_status
#        attempt.post_pipeline_status = new_status.type
#
#        response.wip = False
#        attempt.save()
#        response.save()
#
#        return return_api_response(request, 'SUCCESS', 'SUCCESS',
#                '', 200)
#    except Attempt.DoesNotExist:
#        return return_api_response(request, 'FAIL', 'NO_SUCH_ATTEMPT',
#                'Cannot get attempt details, no such attempt.', 404)
#    except Exception, e:
#        log.exception('error fetching attempt details %s' % repr(e))
#        return return_api_response(request, 'FAIL', 'SYSTEM_ERROR',
#                'Cannot get attempt details', 500)
#
#def add_response(request):
#    try:
#        if not request.method == 'POST':
#            return return_api_response(request, 'FAIL', 'BAD_REQUEST',
#                    'Invalid HTTP method.', 400)
#        json = simplejson.loads(request.POST.keys()[0])
#        campaign = Campaign.objects.select_related('brand').get(pk=json['campaign_id'])
#        default_status = ResponseStatus.objects.get(campaign=campaign, name='New', type='New')
#        response = Response()
#        response.medium = 'Database'
#        response.name = json.get('name','')
#        response.email = json.get('email','')
#        response.phone = normalize_phone(json.get('phone',''))
#        response.message = json.get('message','')
#        response.brand = campaign.brand
#        response.campaign = campaign
#        response.status = default_status 
#        response.state = 'New'
#        try:
#            duplicate = Response.objects.filter(phone=response.phone,
#                    brand = campaign.brand,
#                    campaign = campaign)
#            if duplicate:
#                return_api_response(request,'SUCCESS','SUCCESS',
#                        'Added response', 200)
#        except Response.DoesNotExist:
#            pass
#
#        response.save()
#        attach_response_to_user(response)
#        return return_api_response(request, 'SUCCESS', 'SUCCESS',
#                'Added response', 200)
#    except Exception, e:
#        log.exception('error adding response %s' % repr(e))
#        return return_api_response(request, 'FAIL', 'SYSTEM_ERROR',
#                'Error adding response', 500)
#
#def get_response_info(response):
#    resp_statuses = ResponseStatus.objects.select_related('status','campaign').filter(campaign=response.campaign)
#    # weed out response statuses which cannot be set
#    allowed_statuses = [ status for status in resp_statuses 
#            if (response.can_go_to(status) and status.type != 'Attempted' and status.type != 'New' and status.type != 'Shipped' and status.type != 'Delivered')]
#    attempt_statuses = [ status for status in resp_statuses
#            if status.type == 'Attempted' ]
#
#    data = {}
#    data['current_status'] = dict(id = response.status.id, name = response.status.name, type = response.status.type)
#    data['next_statuses'] = [dict(name=status.name, id=status.id, type=status.type) for status in allowed_statuses]
#    data['campaign'] = dict(name = response.campaign.name, script = response.campaign.script) 
#    data['attempt_statuses'] = [dict(name=status.name, id=status.id, type=status.type) for status in attempt_statuses]
#    data['name'] = response.name
#    data['id'] = response.id
#    data['phone'] = response.phone
#
#    attempts = []
#    fmt = '%a %b %d %Y %I:%M %p'
#    for attempt in Attempt.objects.select_related('agent',
#            'pre_response_status',
#            'post_response_status').filter(
#                    response=response,
#                    valid=True).order_by('-time'):
#        attempt_info = dict(id=attempt.id, time=attempt.time.strftime(fmt),
#                            call_id=attempt.call_id, state = attempt.state,
#                            pre_pipeline_status = attempt.pre_pipeline_status,
#                            post_pipeline_status = attempt.post_pipeline_status,
#                            comments = attempt.comments)
#        if attempt.pre_response_status:
#            attempt_info['pre_response_status'] = dict(id=attempt.pre_response_status.id, name=attempt.pre_response_status.name)
#        if attempt.next_call:
#            attempt_info['next_call'] = attempt.next_call.strftime(fmt)
#        if attempt.post_response_status:
#            attempt_info['post_response_status'] = dict(id=attempt.post_response_status.id, name=attempt.post_response_status.name)
#        attempts.append(attempt_info)
#        attempt_info['answered'] = (attempt.state == 'Answered')
#        if attempt.type == 'inbound':
#            attempt_info['dir'] = 'inbound'
#        else:
#            attempt_info['dir'] = 'outbound'
#        if attempt.state != 'Answered' and attempt.type == 'inbound':
#            attempt_info['dir'] = 'abandoned'
#        if attempt.agent:
#            attempt_info['name'] = attempt.agent.name
#
#    data['attempt_history'] = attempts
#
#    return data
#
#
#DEFAULT_INBOUND_CAMPAIGN = Campaign.objects.select_related('brand').get(name='Inbound',status='Active',type='Inbound')
#DEFAULT_INBOUND_STATUS = ResponseStatus.objects.get(campaign=DEFAULT_INBOUND_CAMPAIGN, name='New', type='New')
#
#def get_or_create_attempt_for_call(call_id, call_type='hard'):
#    try:
#        attempt = Attempt.objects.select_related('agent').get(call_id=call_id)
#        return attempt
#    except Attempt.DoesNotExist:
#        attempt = Attempt(call_id=call_id, time=datetime.now())
#        attempt.state = 'In Queue'
#        if call_type == 'soft':
#            attempt.type = 'soft_call'
#        attempt.save()
#        return attempt
#
#def get_open_responses(phone):
#    responses = Response.objects.select_related('campaign','brand').filter(
#            phone=phone, closed=False)
#    return responses
#
#def get_untagged_status(campaign):
#    return ResponseStatus.objects.get(campaign=campaign,
#            type='Connected',
#            name='Untagged')
#
#def attach_agent_to_attempt(call_id, agent):
#    try:
#        attempt = Attempt.objects.select_related('response',
#                'response__campaign').get(call_id=call_id)
#        attempt.agent = agent
#        attempt.state = 'Answered'
#        if attempt.response:
#            response = attempt.response
#            if response.state == 'Attempted':
#                response.state = 'Connected'
#                response.status = get_untagged_status(response.campaign)
#                response.connections += 1
#                response.save()
#        attempt.save()
#        return attempt
#    except Attempt.DoesNotExist:
#        pass
#
#def get_campaign_to_create_response(dni):
#    campaign = DEFAULT_INBOUND_CAMPAIGN
#    dni_campaigns = Campaign.objects.select_related('brand').filter(
#            type='Inbound',status='Active')
#    if dni:
#        dni_campaigns = dni_campaigns.filter(dni=dni)
#    if dni_campaigns:
#        campaign = dni_campaigns[0]
#    return campaign
#
#def get_in_queue_status(campaign):
#    return ResponseStatus.objects.get(campaign = campaign, type = 'Attempted',
#            name = 'In Queue')
#
#def get_abandoned_status(campaign):
#    return ResponseStatus.objects.get(campaign = campaign, type = 'Attempted',
#            name = 'Abandoned')
#
#def create_new_response(phone, dni, status=None):
#    campaign = get_campaign_to_create_response(dni)
#    response = Response(campaign=campaign, phone=phone, brand=campaign.brand)
#    response.status = status or get_in_queue_status(campaign)
#    response.state = response.status.type
#    response.save()
#    return response
#
#def get_or_create_responses(phone, dni):
#    responses = get_open_responses(phone)
#    if not responses:
#        return [create_new_response(phone, dni)]
#    else:
#        return responses
#
#def get_or_create_response(request):
#    dni = request.GET.get('dni',None)
#    phone = request.GET.get('phone')
#    call_id = request.GET.get('call','')
#    agent_name = request.GET.get('agent',None)
#    call_type = request.GET.get('type','hard')
#    return get_or_create_response_for_call(request, phone, call_id,
#        agent_name, dni, type)
#
#
#def get_or_create_response_for_call(request, phone, call_id,
#        agent_name = None, dni = None, call_type = 'hard'):
#    ''' Gives out any open responses in the system for the given phone number
#        If no responses match, we create a new response and an empty attempt
#    '''
#
#    if not phone:
#        return return_api_response(request, 'FAILURE', 'FAILURE', 'Phone not supplied', 400)
#
#    if '.' not in call_id:
#        call_type = 'soft_call'
#
#    suggested = None
#    responses = None
#    attempt = None
#    agent = None
#
#    phone = normalize_phone(phone)
#    if len(phone) != 10:
#        return return_api_response(request, 'FAILURE', 'FAILURE', 'Invalid phone number', 400)
#
#    try:
#        if agent_name:
#            agent = Agent.objects.get(name=agent_name)
#    except Agent.DoesNotExist:
#        pass
#
#    attempt = get_or_create_attempt_for_call(call_id, call_type)
#    responses = get_open_responses(phone)
#
#    suggested_idx = 0
#    if responses:
#        # we have open responses. we will have to split them into suggested
#        # and others.
#        ordered_responses = [response for response in responses]
#        i = -1
#        for response in responses:
#            i += 1
#            if response.campaign.dni == dni:
#                suggested = response
#                suggested_idx = i
#                break
#        if suggested:
#            ordered_responses = [ordered_responses.pop(suggested_idx)] + ordered_responses
#    else:
#        # no open responses for given phone number. we have to create one
#        # there is no use case for creating a new response for soft calls
#        response = create_new_response(phone, dni)
#        attempt.response = response
#        attempt.save()
#        ordered_responses = [response]
#        if attempt.type != 'soft_call':
#            # increment counters only for hard calls
#            response.attempts += 1
#            response.save()
#
#    return return_api_response(request, 'SUCCESS', 'SUCCESS', 'Found responeses', 200,
#            [get_response_info(response) for response in ordered_responses])
#
#
#def get_agent_by_name(agent_name):
#    try:
#        if not agent_name:
#            return None
#        agent = Agent.objects.get(name=agent_name)
#        return agent
#    except Agent.DoesNotExist:
#        return None
#
#def check_pending_orders(call_id, response):
#    pending_order_generated = False
#    try:
#        orders = getOrdersByCallId(call_id, 'pending_order')
#        if orders:
#            pending_order_generated = True
#            for order in orders:
#                try:
#                    ro = ResponseOrders(order_id=order['id'], response=response)
#                    ro.save()
#                except Exception, roex:
#                    log.exception('error saving order created in response %s' % repr(e))
#    except Exception, e:
#        log.exception('error getting order items for call %s' % repr(e))
#
#    if pending_order_generated:
#        if response.state in ['Attempted','Connected','Product Details']:
#            # response is still not qualified.
#            if new_status.type != 'Pending Order':
#                # we know that response is qualifed, but agent doesnt seem to think so
#                # we override agent's decision here.
#                response.state = 'Pending Order'
#                new_status = ResponseStatus.objects.get(campaign=campaign, type='Pending Order', name='Sent')
#                response.status = new_status
#    return pending_order_generated
#
#def close_inbound_call(request):
#    try:
#        json = simplejson.loads(request.POST.keys()[0])
#        log.info('Request to close call %s ' % repr(json))
#
#        call_id = json.get('call_id','')
#        call_status = json.get('call_status','')
#        if call_status != 'Answered':
#            # nothing to do
#            return return_api_response(request, 'SUCCESS', 'SUCCESS', '', 200)
#        log.info('Request to close answered call %s ' % repr(json))
#        comments = json.get('comments','')
#        agent = get_agent_by_name(json.get('agent_name',''))
#        response = None
#        try:
#            response = Response.objects.get(pk=json.get('response_id',''))
#        except response.DoesNotExist:
#            return return_api_response(request, 'FAIL', 'NO_SUCH_RESPONSE',
#                    'Cannot close call, no such response', 500)
#
#        new_status = None
#        try:
#            new_status = ResponseStatus.objects.get(pk=json.get('resp_status',''))
#        except ResponseStatus.DoesNotExist:
#            return return_api_response(request, 'FAIL', 'NO_SUCH_RESPONSE_STATUS',
#                    'Cannot close call, no such response status', 500)
#
#
#        fmt = '%m/%d/%Y %I:%M %p'
#        next_call = None
#        if json.get('next') and json.get('next') != ' 10:00 AM':
#            next_call = datetime.strptime(json.get('next',''), fmt)
#            response.next_call = next_call
#
#        attempt = Attempt()
#        is_old_attempt = True
#        try:
#            attempt = Attempt.objects.get(call_id=call_id)
#        except Attempt.DoesNotExist:
#            is_old_attempt = False
#        attempt.response = response
#        attempt.call_id = call_id
#        attempt.state = 'Answered'
#        attempt.pre_pipeline_status = response.state
#        attempt.post_pipeline_status = new_status.type
#        attempt.post_response_status = new_status
#        attempt.pre_response_status = response.status
#        attempt.comments = comments
#        attempt.status = new_status
#        attempt.valid = True
#        if next_call:
#            attempt.next_call = next_call
#            response.next_call = next_call
#        if agent:
#            attempt.agent = agent
#        if attempt.type != 'soft_call':
#            attempt.type = 'inbound'
#
#        # change response status
#        response.status = new_status
#        if not is_old_attempt:
#            response.attempts += 1
#            response.connections += 1
#        response.state = new_status.type
#        response.closed = new_status.close_response
#
#        try:
#            call = Call.objects.select_related('agent').get(uniqueid=call_id)
#            response.last_call = call.starttime
#            attempt.time = call.starttime
#            if call.agent:
#                attempt.agent = agent
#        except Call.DoesNotExist:
#            response.last_call = attempt.time
#
#        po_generated = check_pending_orders(call_id, response)
#        if po_generated:
#            response.borrowed_by = attempt.agent
#        response.wip = False
#        attempt.save()
#        response.save()
#        return return_api_response(request, 'SUCCESS', 'SUCCESS',
#                '', 200)
#    except Exception, e:
#        log.exception('error updating response for inbound call %s' % repr(e))
#        return return_api_response(request, 'FAIL', 'SYSTEM_ERROR',
#                'Sytem error', 500)

def subscription_api(request):
    errors = []
    response_messages = {
        'EMPTY_EMAIL': 'Please enter Email ID',
        'EMPTY_MOBILE': 'Please enter Mobile No.',
        'EMPTY_SOURCE': 'Please provide source',
        'INVALID_EMAIL': 'Please enter valid Email ID',
        'INVALID_MOBILE': 'Please enter valid Mobile No.',
        'INVALID_SOURCE': 'Please provide valid source',
        'MOBILE_SUBSCRIBED': 'Mobile is already subscribed',
        'EMAIL_SUBSCRIBED': 'Email ID is already subscribed',
        'USER_ALREADY_SUBSCRIBED': 'User is already subscribed for the Deal',
        'NOT_SAME_USER': 'Email ID and Mobile are not registered for the same user',
    }
    if request.method == 'POST':
        is_valid = True
        params = request.POST
        source = params.get('source', '').strip()
        status_code = ''
        source_regex = re.compile(r'^offer-\d+')
        errors = []
        response_message = ''
        from affiliates.models import SubscriptionLink
        form = FBRegisterForm(request.POST)
        if form.is_valid():            
            name = form.cleaned_data['name']
            email_id  = form.cleaned_data['email']
            mobile_no = form.cleaned_data['mobile']
        else:
            is_valid = False

        if is_valid:    
            if not source:
                status_code = 'EMPTY_SOURCE'
                is_valid = False
            elif not SubscriptionLink.objects.filter(path='/%s' % source) and source != 'facebook' and not source_regex.match(source):
                status_code = 'INVALID_SOURCE'
                is_valid = False

            from web.views.fb import get_user_by_email_or_mobile
            user_info = get_user_by_email_or_mobile(email_id, mobile_no)
            email_user, phone_user, email_alert_on, sms_alert_on = user_info

            if not email_user and not phone_user: #new user
                user,profile = utils.get_or_create_user(email_id, email_id, None, name)
                email = UserEmail.objects.get(user=profile, type='primary', email=email_id)
                email_alert_on = email
                phone = Phone(user=profile, type='primary' ,phone=mobile_no)
                phone.save()
                sms_alert_on = phone
            elif email_user and phone_user:
                if phone_user == email_user:
                    is_valid = True
                else:
                    status_code = 'NOT_SAME_USER'
                    is_valid = False
            elif not email_user and phone_user: #user with phone number already exist, update his email address only
                status_code = 'MOBILE_SUBSCRIBED'
                is_valid = False
            elif not phone_user and email_user: #user with email already exist, update his phone number only
                status_code = 'EMAIL_SUBSCRIBED'
                is_valid = False
                
        if is_valid:
            if name:
                u_name = name[0].upper() + name[1:]
            else:
                u_name = None
            try:
                newsletter = NewsLetter.objects.get(newsletter='DailyDeals',client=request.client.client)
                existing_subscription = DailySubscription.objects.filter(newsletter=newsletter,sms_alert_on=sms_alert_on,email_alert_on=email_alert_on)
                if not existing_subscription:
                    subscribe = DailySubscription()
                    subscribe.newsletter = newsletter
                    subscribe.sms_alert_on = sms_alert_on
                    subscribe.email_alert_on = email_alert_on
                    subscribe.source = source 
                    subscribe.save()                        
                    utils.subscribe_send_email(request,email_id, u_name)
                    utils.subscribe_send_sms(mobile_no)
                else:
                    status_code = 'USER_ALREADY_SUBSCRIBED'
                    is_valid = False
            except NewsLetter.DoesNotExist:
                log.info("Daily Deals Subscription not available.")
            if is_valid:
                log.info("Email: %s and Mobile: %s subscribed through Source: %s" % (email_id, mobile_no, source))

        if is_valid:
            status = 'SUCCESS'
            response_message = ''
            return render_to_response('web/thank_you.html',{'offer_fb':True},context_instance=RequestContext(request))
        else:
            status = 'FAILED'
            if status_code:
                response_message = response_messages[status_code]
                errors = [response_message]
        response = dict(Status=status, ResponseMessage = response_message, StatusCode = status_code)
    else:
        form = FBRegisterForm() 
        source = None
        response = dict(Status="FAILED", ResponseMessage = "Request Method not POST", StatusCode = "INVALID_REQUEST_METHOD")        
    log.info("SUBSCRIPTION API RESPONSE: %s" % response)
    return render_to_response('web/welcome.html',
        {
            'form':form,
            'errors':errors,
            'source':source,
            'offer_fb':True,
        },context_instance=RequestContext(request))
