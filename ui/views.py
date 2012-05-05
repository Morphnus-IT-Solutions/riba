# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect
from dialer.models import Campaign, Response, Attempt, ResponseStatus
from asterisk.models import Agent, Call, Task
from users.models import Profile
from datetime import datetime, timedelta
from asterisk.views import originate
import random
import logging
from django.utils import simplejson
from django.core import serializers
from django.contrib.auth.decorators import login_required
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.db.models import Count
from operator import itemgetter
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from dialer.forms import CampaignForm, MiniResponseForm, ResponseForm, UploadFileForm
from bl.errors import *
from bl.user import User
from bl import users
from ui.forms import CloseAttemptForm
from bl.orders import getOrdersByCallId
from django.core.mail import send_mail
from django.core.mail import EmailMessage, EmailMultiAlternatives
from django.template.loader import render_to_string
import xlrd
from utils.utils import normalize_phone

log = logging.getLogger('ccc')

def extract_user(request):
    is_manager = request.user.has_perm('dialer.add_campaign')
    agent = None
    try:
        profile = Profile.objects.get(user=request.user)
        agent = Agent.objects.get(user=profile)
    except Agent.DoesNotExist:
        pass
    return (is_manager,agent)

def get_user_campaigns(is_manager, agent):
    if not is_manager:
        return Campaign.objects.filter(agents=agent,status='Active')
    else:
        return Campaign.objects.filter(status='Active')

@login_required
def home(request):
    is_manager, agent = extract_user(request)
    campaigns = get_user_campaigns(is_manager, agent)
    return render_to_response('rms/home.html', dict(agent=agent, campaigns=campaigns),
            context_instance=RequestContext(request))

def mail_summary_report(request, campaign_id ):
    campaign = Campaign.objects.get(pk=campaign_id)
    body = render_to_string('campaigns/summary_mail.html', dict(campaign=campaign),
            context_instance=RequestContext(request)).strip()
    subject = 'Daily Report | %s | %s' % (campaign.name, datetime.now().strftime('%Y%m%d'))
    msg = EmailMessage(subject, body, 'Chaupaati Bazaar<bot@chaupaati.com>',
            ['reports@chaupaati.in'])
    msg.content_subtype = 'html'
    msg.send()
    return HttpResponse('done')

@login_required
def responses_home(request):
    # home screen for responses
    # agents can see responses assigned to them, handled by them
    # managers can see all the responses, access reports
    pass

@login_required
def edit_response(request, response_id):
    pass

@login_required
def add_response(request):
    pass

@login_required
def response_detail(request, response_id):
    pass

def get_page_no(request):
    try:
        return int(request.GET.get('page', '1'))
    except ValueError:
        return 1

def get_page_objects(request, paginator):
    page = get_page_no(request)
    try:
        return paginator.page(page)
    except (EmptyPage, InvalidPage):
        return paginator.page(paginator.num_pages)

@login_required
def campaigns_home(request):
    is_manager, agent = extract_user(request)
    campaigns = get_user_campaigns(is_manager, agent)
    paginator = Paginator(campaigns, 10)
    paginated_campaigns = get_page_objects(request, paginator)
    return render_to_response('campaigns/home.html', dict(campaigns=campaigns), context_instance=RequestContext(request))

def create_user_from_response(response):
    u,p = utils.create_user(response.name,response.email)
    p.primary_phone = response.phone
    p.full_name = response.name
    p.primary_email = response.email
    address = Address()
    address.address = response.address
    address.pincode = response.pin
    try:
       city = City.objects.get(name=response.city)
       address.city = city
    except:
        pass
    try:
        state = State.objects.get(name=response.province)
        address.state = state
    except:
        pass
    p.save()
    address.type = 'user'
    address.profile = p
    address.name = response.name
    address.phone = response.phone
    address.save()
    return u

def save_uploaded_file(f):
    path = str(random.randint(10000000,99999999))
    destination = open('/tmp/' + path, 'wb+')
    for chunk in f.chunks():
        destination.write(chunk)
    destination.close()
    return '/tmp/' + path
 
@login_required
def upload_campaign_responses(request, campaign_id):
    is_manager, agent = extract_user(request)
    campaign = Campaign.objects.get(pk=campaign_id)
    new_status = ResponseStatus.objects.get(campaign=campaign, type='New', name='New')
    brand = campaign.brand
    errors = []
    action = request.path
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        if form.is_valid():
            path = save_uploaded_file(request.FILES['file'])
            wb = xlrd.open_workbook(path)
            sheet = wb.sheet_by_index(0)
            nrows = sheet.nrows
            headers = sheet.row(0)
            accepted_headers = ['phone','email','name','message','address','city','state','pincode']
            header_index_map = {}
            for row_id in range(1, nrows):
                data = sheet.row(row_id)
                rs = Response(campaign=campaign, state='New', status=new_status, brand=brand)
                for key, value in zip(headers, data):
                    if str(key.value).lower() in accepted_headers:
                        setattr(rs, str(key.value.lower()), str(value.value))
                rs.phone = normalize_phone(rs.phone.split('.')[0])
                try:
                    r = Response.objects.get(phone=rs.phone, closed=False)
                except Response.DoesNotExist:
                    rs.save()
                    attach_response_to_user(rs)
            return HttpResponseRedirect('/rms/ui/campaigns')
        else:
            return render_to_response('campaigns/upload_responses.html',
                dict(form=form, campaign=campaign, action=action),
                context_instance=RequestContext(request))
    else:
        form = UploadFileForm()
        return render_to_response('campaigns/upload_responses.html',
            dict(form=form, campaign=campaign, action=action),
            context_instance=RequestContext(request))

#def attach_response_to_user(response):
#    try:
#        u = users.getUserByMobile(response.phone)
#        response.user_id = u['ID']
#        response.save()
#    except APINotFoundError, e:
#        log.info('User not found')
#        try:
#            u = create_user_from_response(response)
#            users.add(u)
#            response.user_id = u['ID']
#            response.save()
#        except APIError, e2:
#            log.info('General api error adding user')
#            log.exception(repr(e2))
#    except APIError, e3:
#        log.info('General api error')
#        log.exception(repr(e3))
#        try:
#            u = create_user_from_response(response)
#            users.add(u)
#            response.user_id = u['ID']
#            response.save()
#        except APIError, e2:
#            log.info('General api error adding user')
#            log.exception(repr(e2))
#    except:
#        log.info('General error')
#        log.exception(repr(e3))
#        try:
#            u = create_user_from_response(response)
#            users.add(u)
#            response.user_id = u['ID']
#            response.save()
#        except APIError, e2:
#            log.info('General api error adding user')
#            log.exception(repr(e2))
def attach_response_to_user(response):
    try:
        u = Profile.objects.get(primary_phone=response.phone)
        #u = users.getUserByMobile(response.phone)
        response.user = u
        response.save()
    except ProfileDoesNotExists, e:
        log.info('User not found')
        try:
            u = create_user_from_response(response)
            #users.add(u)
            response.user = u
            response.save()
        except APIError, e2:
            log.info('General api error adding user')
            log.exception(repr(e2))
    except APIError, e3:
        log.info('General api error')
        log.exception(repr(e3))
        try:
            u = create_user_from_response(response)
            #users.add(u)
            response.user = u
            response.save()
        except APIError, e2:
            log.info('General api error adding user')
            log.exception(repr(e2))
    except:
        log.info('General error')
        log.exception(repr(e3))
        try:
            u = create_user_from_response(response)
            #users.add(u)
            response.user = u
            response.save()
        except APIError, e2:
            log.info('General api error adding user')
            log.exception(repr(e2))

@login_required
def manage_campaign_responses(request, campaign_id):
    is_manager, agent = extract_user(request)
    campaign = Campaign.objects.get(pk=campaign_id)
    addform = None
    if request.method == 'POST':
        addform = MiniResponseForm(request.POST)
        if addform.is_valid:
            response = addform.save()
            attach_response_to_user(response)
            return HttpResponseRedirect('/rms/ui/campaigns')
    else:
        addform = MiniResponseForm()
    responses = Response.objects.filter(campaign=campaign)
    paginator = Paginator(responses, 10)
    paginated_responses = get_page_objects(request, paginator)
    return render_to_response('campaigns/manage_responses.html',
            dict(campaign=campaign, responses=responses, addform=addform), 
            context_instance=RequestContext(request))

@login_required
def manage_campaign_response_statuses(request, campaign_id):
    is_manager, agent = extract_user(request)
    campaign = Campaign.objects.get(pk=campaign_id)
    pass

@login_required
def add_campaign(request):
    ctxt = {}
    if not request.user.has_perm('dialer.add_campaign'):
        ctxt['no_perm'] = 'You do not have permission to add a campaign'
        return render_to_response('campaigns/add.html', ctxt, context_instance=RequestContext(request))
    if request.method == 'POST':
        form = CampaignForm(request.POST)
        ctxt['form'] = form
        if form.is_valid():
            campaign = form.save()
            # auto add attempted responses
            response_status_set = [
                    {'name':'New', 'type':'New', 'close_response':False},

                    {'name':'Abandoned', 'type':'Attempted', 'close_response':False},
                    {'name':'Congestion', 'type':'Attempted', 'close_response':False},
                    {'name':'Invalid number', 'type':'Attempted', 'close_response':True},
                    {'name':'No reply', 'type':'Attempted', 'close_response':False},
                    {'name':'Unreachable', 'type':'Attempted', 'close_response':False},
                    {'name':'In Queue', 'type':'Attempted', 'close_response':False},

                    {'name':'No Conversation', 'type':'Connected', 'close_response':False},
                    {'name':'Not interested', 'type':'Connected', 'close_response':True},
                    {'name':'Shipping duration too long', 'type':'Connected', 'close_response':False},
                    {'name':'Price too high', 'type':'Connected', 'close_response':False},
                    {'name':'Product not available', 'type':'Connected', 'close_response':False},
                    {'name':'Interested', 'type':'Connected', 'close_response':False},
                    {'name':'Details shared by email', 'type':'Connected', 'close_response':False},
                    {'name':'Wrong response/lead', 'type':'Connected', 'close_response':True},
                    {'name':'Untagged', 'type':'Connected', 'close_response':False},

                    {'name':'Sent', 'type':'Pending Order', 'close_response':False},
                    {'name':'Not interested', 'type':'Pending Order', 'close_response':True},
                    {'name':'Will pay', 'type':'Pending Order', 'close_response':False},
                    {'name':'Paid and wants confirmation', 'type':'Pending Order', 'close_response':False},
                    {'name':'Payment received', 'type':'Pending Order', 'close_response':False},

                    {'name':'Confirmed', 'type':'Order', 'close_response':False},
                    {'name':'Wants shipping status', 'type':'Order', 'close_response':False},
                    {'name':'Sent shipping status', 'type':'Order', 'close_response':False},
                    {'name':'Other complaint', 'type':'Order', 'close_response':False},
                    {'name':'Wants refund', 'type':'Order', 'close_response':False},
                    {'name':'Incorrect product', 'type':'Order', 'close_response':False},
                    {'name':'Defective product', 'type':'Order', 'close_response':False},
                    {'name':'Incomplete product', 'type':'Order', 'close_response':False},
                    {'name':'Other complain', 'type':'Order', 'close_response':False},
                    {'name':'Satisified with delivery', 'type':'Order', 'close_response':True},
                    {'name':'Feedback', 'type':'Order', 'close_response':True},
                    ]
            for resp in response_status_set:
                rs = ResponseStatus(campaign=campaign, name=resp['name'],
                        type=resp['type'], close_response=resp['close_response'],
                        hidden = True)
                rs.save()
            return HttpResponseRedirect('/rms/ui/campaigns/')
    else:
        form = CampaignForm()
        ctxt['form'] = form
    return render_to_response('campaigns/add.html', ctxt, context_instance=RequestContext(request))

@login_required
def edit_campaign(request, campaign_id):
    campaign = Campaign.objects.get(pk=campaign_id)
    response_statuses = ResponseStatus.objects.filter(campaign=campaign)
    return render_to_response('campaigns/edit.html', ctxt,
            context_instance=RequestContext(context))

@login_required
def campaign_responses(request, campaign_id):
    # agents see campaigns they are part of. borrow respones, read campaign goals, script etc
    # manager can see all campaigns, assign agents to campaigns, access campaign reports
    is_manager, agent = extract_user(request)
    campaign = Campaign.objects.get(pk=int(campaign_id))
    params = dict(campaign=campaign)
    if request.GET.get('status',''):
        params['status'] = int(request.GET['status'])
    if request.GET.get('state',''):
        params['state'] = request.GET['state']
    if request.GET.get('created_on__day',''):
        params['created_on__day'] = int(request.GET['created_on__day'])
    if request.GET.get('created_on__year',''):
        params['created_on__year'] = int(request.GET['created_on__year'])
    if request.GET.get('created_on__month',''):
        params['created_on__month'] = int(request.GET['created_on__month'])

    open_responses = Response.objects.filter(**params).order_by('created_on', 'next_call')
    return render_to_response('campaigns/campaign_agent_detail.html',
            dict(agent=agent, campaign=campaign, follow_ups=None, open_responses=open_responses),
            context_instance=RequestContext(request))

@login_required
def campaign_detail(request, campaign_id):
    # agents see campaigns they are part of. borrow respones, read campaign goals, script etc
    # manager can see all campaigns, assign agents to campaigns, access campaign reports
    is_manager, agent = extract_user(request)
    campaign = Campaign.objects.get(pk=int(campaign_id))
    follow_ups = None
    open_responses = None
    if not is_manager:
        follow_ups = Response.objects.filter(campaign=campaign,borrowed_by=agent,closed=False).exclude(next_call__gte=datetime.now())
    else:
        follow_ups = Response.objects.filter(campaign=campaign)
    if not follow_ups:
        open_responses = Response.objects.filter(campaign=campaign, borrowed_by=None, closed=False).exclude(next_call__gte=datetime.now())
    return render_to_response('campaigns/campaign_agent_detail.html',
            dict(agent=agent, campaign=campaign, follow_ups=follow_ups, open_responses=open_responses),
            context_instance=RequestContext(request))

def return_json(request, status, msg_code, msg, http_code):
    resp = dict(msg_code = msg_code, msg = msg, status = status)
    return HttpResponse(simplejson.dumps(resp), mimetype="application/json",
            status=http_code)

@login_required
def call_response(request, response_id):
    pass
   # create a task request and return task id 

@login_required
def call_number(request, phone):
    pass

@login_required
def response_attempts(request, response_id):
    attempts = Attempt.objects.select_related('agent','response','pre_response_status','post_response_status').filter(valid=True, response = response_id)
    if request.GET.get('mode','') == 'details_only':
        return render_to_response('attempts/response_attempts_details.html',
                dict(attempts=attempts),
                context_instance=RequestContext(request))
    else:
        return render_to_response('attempts/response_attempts.html',
                dict(attempts=attempts),
                context_instance=RequestContext(request))

@login_required
def close_response_wip(request, response_id):
    pass

@login_required
def close_attempt(request, attempt_id):
    attempt = Attempt.objects.select_related('response', 'response__campaign').get(pk=attempt_id)
    ctxt = {'response':attempt.response, 'attempt':attempt}
    resp_statuses = ResponseStatus.objects.filter(campaign=attempt.response.campaign)

    groups = ['New','Attempted','Connected','Product Details','Pending Order', 'Order', 'Shipped', 'Delivered']
    allowed_statuses = [ status for status in resp_statuses 
            if (attempt.response.can_go_to(status) and status.type != 'Attempted' and status.type != 'New')]
    choices = []
    for group in groups:
        statuses = []
        for st in allowed_statuses:
            if st.type == group:
                statuses.append((str(st.id), st.name))
        if statuses:
            choices.append((group, tuple(statuses)))

    attempt_statuses = [ status for status in resp_statuses
            if status.type == 'Attempted' ]
    form = CloseAttemptForm(dict(response_statuses=choices))
    status_code = 200
    if not attempt.is_open():
        ctxt['error'] = 'This attempt is already closed'
        resp = render_to_response('attempts/close.html', ctxt,
                context_instance = RequestContext(request))
        resp.status_code = status_code
        return resp 
    if request.method == 'POST':
        form = CloseAttemptForm(dict(response_statuses=choices), request.POST)
        ctxt['form'] = form
        if form.is_valid():
            response = attempt.response
            attempt.state = form.cleaned_data['call_status']
            if form.cleaned_data['call_status'] != 'Answered':
                # no contact with customer
                if form.cleaned_data['call_status'] != 'Congestion':
                    response.last_call = attempt.time
                    response.attempts += 1
                    response.wip = False
                    if response.attempts % 5 == 0 and response.attempts > 1:
                        if response.connections == 0:
                            response.closed = True
                else:
                    attempt.valid = False
            else:
                response.attempts += 1
                response.connections += 1
                new_status = ResponseStatus.objects.get(pk=form.cleaned_data['response_status'])
                response.status = new_status 
                response.state = new_status.type
                pending_order_generated = False
                try:
                    orders = getOrdersByCallId(call_id, 'pending_order')
                    log.info(orders)
                    if orders:
                        pending_order_generated = True
                        for order in orders:
                            try:
                                ro = ResponseOrders(order_id=order['id'], response=response)
                                ro.save()
                            except Exception, roex:
                                log.exception('error saving order created in response %s' % repr(e))
                except Exception, e:
                    log.exception('error getting order items for call %s' % repr(e))
                if pending_order_generated:
                    if response.state in ['Attempted','Connected','Product Details']:
                        # response is still not qualified.
                        if new_status.type != 'Pending Order':
                            # we know that response is qualifed, but agent doesnt seem to think so
                            # we override agent's decision here.
                            response.state = 'Pending Order'
                            new_status = ResponseStatus.objects.get(campaign=campaign, type='Pending Order', name='Sent')
                            response.status = new_status

                response.closed = new_status.close_response
                attempt.post_response_status = new_status
                attempt.post_pipeline_status = new_status.type

                response.wip = False

            if 'comments' in form.cleaned_data:
                attempt.comments = form.cleaned_data['comments']
            if 'next_call' in form.cleaned_data and form.cleaned_data['next_call']:
                next_call = form.cleaned_data['next_call']
                fmt = '%m/%d/%Y'
                if 'next_call_hour' in form.cleaned_data and form.cleaned_data['next_call_hour']:
                    next_call += ' ' + form.cleaned_data['next_call_hour']
                    fmt += ' %I'
                if 'next_call_min' in form.cleaned_data and form.cleaned_data['next_call_min']:
                    next_call += ' ' + form.cleaned_data['next_call_min']
                    fmt += ' %M'
                if 'next_call_am_pm' in form.cleaned_data and form.cleaned_data['next_call_am_pm']:
                    next_call += ' ' + form.cleaned_data['next_call_am_pm']
                    fmt += ' %p'
                try:
                    response.next_call = datetime.strptime(
                            next_call, fmt)
                except:
                    status_code = 400
                    error = 'Invalid value for next call %s %s' % (next_call, fmt)
                    ctxt['form'] = form
                    ctxt['error'] = error
                    resp = render_to_response('attempts/close.html', ctxt,
                            context_instance = RequestContext(request))
                    resp.status_code = status_code
                    return resp
                attempt.save()
                response.save()
            resp = HttpResponse('Successfully closed attempt')

        else:
            status_code = 400
            resp = render_to_response('attempts/close.html', ctxt,
                    context_instance = RequestContext(request))
    else:
        ctxt['form'] = form
        resp = render_to_response('attempts/close.html', ctxt,
                context_instance = RequestContext(request))
    resp.status_code = status_code
    return resp

@login_required
def call(request):
    is_manager, agent = extract_user(request)
    if agent:
        phone = request.path.split('/')[-1]
        if len(phone) > 10:
            if phone[0] == '0' and len(phone) == 11:
                phone = phone[1:]
            elif phone[:2] == '91' and len(phone) == 13:
                phone = phone[2:]
            else:
                return HttpResponse('Invalid phone')
        task = Task(agent=agent, type='call_by_agent_to_number')
        if phone[0] != '0':
            phone = '0' + phone
        task.data = phone
        task.save()
        return HttpResponse('Calling')
    else:
        return HttpResponse('No agent found')

@login_required
def campaign_daily_breakup(request, campaign_id):
    is_manager, agent = extract_user(request)
    campaign = Campaign.objects.get(pk=campaign_id)
    days = []
    today = datetime.today()
    days = [today - timedelta(days=x) for x in range(0,today.day)]

    return render_to_response('campaigns/datebreakup.html', dict(agent=agent, campaign=campaign, days=days),
            context_instance=RequestContext(request))

@login_required
def followup(request):
    filter_map = {'state':'state','campaign':'campaign_id','agent':'borrowed_by'}
    is_manager, agent = extract_user(request)
    params = dict(closed=False)
    if request.GET.get('campaign') and request.GET['campaign']:
        params['campaign'] = int(request.GET['campaign'])
    if request.GET.get('state','') and request.GET['state']:
        params['state'] = request.GET['state']
    if request.GET.get('status__name','') and request.GET['status__name']:
        params['status__name'] = request.GET['status__name']

    if request.GET.get('next_call__day','') and request.GET['next_call__day']:
        params['next_call__day'] = int(request.GET['next_call__day'])
    if request.GET.get('next_call__year','') and request.GET['next_call__year']:
        params['next_call__year'] = int(request.GET['next_call__year'])
    if request.GET.get('next_call__month','') and request.GET['next_call__month']:
        params['next_call__month'] = int(request.GET['next_call__month'])

    campaigns = Campaign.objects.filter(status='Active',agents=agent)
    states = ['New','Attempted','Connected','Pending Order','Order']
    status_names = ['Abandoned','Untagged']


    open_responses = Response.objects.filter(**params).order_by('created_on', 'next_call')
    paginator = Paginator(open_responses, 50)
    paginated_responses = get_page_objects(request, paginator)
    return render_to_response('responses/followup.html',
            dict(agent=agent, states=states, campaigns=campaigns, status_names=status_names, open_responses=paginated_responses, paginator=paginator),
            context_instance=RequestContext(request))
