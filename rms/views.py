import logging
import xlrd
import math
from datetime import datetime, timedelta, date

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.template import RequestContext
from django.db import connection, transaction, IntegrityError
from django.db.models import Count, Q
from django.utils import simplejson
from django.contrib.auth.models import User, Group
from django import forms
from utils.utils import check_dates, get_or_create_user, normalize_phone
from utils.counter import Counter
from ccm.models import Agent
from users.models import Profile, Phone, Email, Permission
from asterisk.models import Task, Call
from rms.models import Funnel, FunnelState, FunnelSubState, Campaign, Response, Interaction
from rms.forms import CampaignForm, XlsInputForm, DateRangeForm, CallCloseForm, CampaignAgentForm, AddUserForm, EditUserForm
from rms.decorators import check_role

log = logging.getLogger('request')
fb_log = logging.getLogger('fborder')

def http_error_page(request, error_code=403):
    resp = render_to_response('rms/%s.html'%error_code, context_instance=RequestContext(request))
    resp.status_code = error_code
    return resp


@login_required
@check_role(['CallCenter','CC Manager','RMS Client'])
def homepage_redirect(request):
    if request.session['role'] == 'CallCenter':
        return HttpResponseRedirect('/agent')
    #if request.session['role'] == 'RMS Admin':
    #    return HttpResponseRedirect('/user')
    return HttpResponseRedirect('/campaign')


@login_required
@check_role(['CC Manager','RMS Client'])
def campaign_add(request, demo_id=None, campaign_id=None):
    """Adds a campaign
    Step 1 (campaign_id=None): Display CampaignForm (when no POST request) and then create a campaign with the form data.
    Then redirect to /campaign/<funnel id>/<campaign id>/
    
    Step 2 (campaign_id=<id of the new campaign>): Now we modify the funnelsubstates of the campaign. First display the
    appropriate funnel using the demo_id=<funnel id selected>. Then process the POST data to create substates.
    POST data contains keys (for each state) 'state_0', 'state_1' and so on, each containing a list of substates (in order)
    for the respective states.
    """
    if not campaign_id:   #STEP 1: Campaign details
        if request.method == 'POST':
            form = CampaignForm(request.POST)
            if form.is_valid():
                campaign = form.save(commit=False)
                campaign.funnel = form.cleaned_data['campaign_type'].funnel
                if request.POST.get('submit') == 'Create':
                    campaign.draft = False
                else:
                    campaign.draft = True   #Create campaign as draft
                campaign.save()
                return HttpResponseRedirect('/campaign/add/%s/%s' % (form.cleaned_data['campaign_type'].pk, campaign.pk))
        else:
            form = CampaignForm()
        return render_to_response('rms/campaign_add.html', {'form': form, 'funnels': get_funnel()}, context_instance=RequestContext(request))
    else:
        #STEP 2: Funnel substates editing
        campaign_id = int(campaign_id)
        demo_id = int(demo_id)
        funnel = get_funnel(campaign_id=int(demo_id))[0]
        if request.method == 'POST':
            for (i,st) in enumerate(funnel['states']):
                substates = request.POST.getlist('state_%s'%i)
                index = 1
                for subst in substates:
                    if subst != '':
                        substate = FunnelSubState(name=subst, funnel_state_id=st['id'], campaign_id=campaign_id, index=index)
                        for template_substate in st['substates']:
                            if substate.name == template_substate['name']:
                                substate.exit_substate = template_substate['exit_substate']
                                substate.is_active = template_substate['active']
                                break
                        substate.save()
                        index += 1
            #Give permissions on this campaign to this user
            permission = Permission(user=request.user, system='rms', content_type=request.session['type_campaign'], object_id=int(campaign_id))
            permission.save()
            campaign_list = request.session['campaign_ids']
            campaign_list.append(int(campaign_id))
            request.session['campaign_ids'] = campaign_list
            return HttpResponseRedirect('/campaign/%s'%campaign_id)
        else:
            return render_to_response('rms/edit_funnel.html', {'funnel': funnel}, context_instance=RequestContext(request))


def get_funnel(campaign_id=None):
    """Returns the funnel for a specific campaign.
    If no campaign is specified, returns a list of funnel templates (from demo campaigns).

    The object returned is a list of funnels (even for a single funnel). Each funnel is a dictionary
    containing the funnel name, id and a list of funnel states. Each funnel state is also a dictionary
    containing the state name, id and a list of funnel substates. The substates is a list containing
    the name of the substates.
    
    return [Funnel]
    Funnel = {name=<name>, id=<pk>, states=[State]}
    State = {name=<name>, id=<pk>, substates=[Substate]}
    Substate = {name=<name>, id=<pk>, exit_substate=<exit_substate>, active=<is_active>}
    """
    funnels = []
    campaign_list = Campaign.objects.select_related('funnel')

    if campaign_id is None:
        campaign_list = campaign_list.filter(demo=True)
    else:
        campaign_list = campaign_list.filter(pk=campaign_id)
    
    for c in campaign_list:
        funnel = {}
        funnel['name'] = c.funnel.name
        funnel['id'] = c.funnel.pk
        states = []
        for st in c.funnel.funnel_states.all().order_by('id'):
            state = {}
            state['name'] = st.name
            state['id'] = st.pk
            substates = []
            for subst in st.funnel_sub_states.filter(campaign=c).order_by('index'):
                substate = {}
                substate['name'] = subst.name
                substate['id'] = subst.pk
                substate['exit_substate'] = subst.exit_substate
                substate['active'] = subst.is_active
                substates.append(substate)
            if substates:   #checking for empty list of substates
                state['substates'] = substates
                states.append(state)
            else:
                continue    #no substates belonging to this campaign. this is an erroneous state
        funnel['states'] = states
        funnels.append(funnel)
    return funnels


@login_required
@check_role(['CallCenter','CC Manager','RMS Client'])
def campaign_list(request):
    """Display campaign list filtered on start date, end date and campaign type (active/draft). If agent is logged in, only display
    campaigns for which the agent is assigned to.
    Logic with start and end date: campaign start date >= selected start date and campaign end date <= selected end date
    If start date and/or end date are not selected, then the respective condition is not applied
    """
    
    campaigns = Campaign.objects.filter(demo=False).select_related('client').order_by('id')
    if request.session['role'] != 'RMS Admin':
        campaigns = campaigns.filter(id__in=request.session['campaign_ids'])
    #Response summary MTD
    end_date = datetime.now()
    start_date = end_date.date() + timedelta(days=-(end_date.day-1))
    cursor = connection.cursor()
    cursor.execute("SELECT a.campaign_id, a.total, (b.num*100/a.total) percentage FROM (SELECT r1.campaign_id, COUNT(r1.id) total FROM rms_response AS r1 WHERE (r1.last_interacted_on BETWEEN %s AND %s) OR (r1.last_interacted_on IS NULL AND r1.created_on BETWEEN %s AND %s) GROUP BY r1.campaign_id) AS a LEFT JOIN (SELECT r.campaign_id, COUNT(r.id) num FROM rms_response AS r, rms_funnelstate AS f WHERE r.funnel_state_id = f.id AND f.name=%s AND ((r.last_interacted_on BETWEEN %s AND %s) OR (r.last_interacted_on IS NULL AND r.created_on BETWEEN %s AND %s)) GROUP BY r.campaign_id) AS b ON a.campaign_id = b.campaign_id ORDER BY campaign_id",
        [start_date, end_date, start_date, end_date, 'Order', start_date, end_date, start_date, end_date])
    rows = cursor.fetchall()
    
    campaign_list = []
    i, row_count = 0, len(rows) 
    for campaign in campaigns:
        while i<row_count and rows[i][0]<campaign.id:
            i += 1
        if i<row_count:
            if rows[i][0] == campaign.id:
                campaign_list.append((campaign,rows[i][1],rows[i][2]))
                i += 1
            else:
                campaign_list.append((campaign,0,0))
        else:
            campaign_list.append((campaign,0,0))
    
    CCManager, Client, Admin = False, False, False
    if request.session['role'] == 'CC Manager':
        CCManager = True
    elif request.session['role'] == 'RMS Client':
        Client = True
    elif request.session['role'] == 'RMS Admin':
        Admin = True
    return render_to_response('rms/campaign_list.html', {'campaign_list':campaign_list, 'CCManager':CCManager, 'Client':Client, 'Admin':Admin},
        context_instance=RequestContext(request))


@login_required
@check_role(['CC Manager','RMS Client'])
def campaign_edit(request, campaign_id=None):
    """Edit campaign details.
    Campaign name, type, client and funnel structure are not editable
    """
    if campaign_id:
        campaign_id = int(campaign_id)
    
    if not ((request.session['role'] == 'RMS Admin') or (campaign_id in request.session['campaign_ids'])):
        return http_error_page(request)

    try:
        campaign = Campaign.objects.get(pk=campaign_id, demo=False)
    except:
        return http_error_page(request, error_code=404)

    if request.method == 'POST':
        if request.POST.get('submit') == 'Save':
            campaign.draft = False
        else:
            campaign.draft = True
        form = CampaignForm(request.POST, instance=campaign)
        form.fields['campaign_type'].required = False
        
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/campaign/%s' % campaign_id)
        else:
            #Validation error, hide the readonly fields for this form instance
            form.fields['name'].widget = forms.HiddenInput()
            form.fields['type'].widget = forms.HiddenInput()
    else:
        form = CampaignForm(instance=campaign)
        #Hide readonly fields
        form.fields['name'].widget = forms.HiddenInput()
        form.fields['type'].widget = forms.HiddenInput()
        del form.fields['campaign_type'] #This field is not required for this form
    return render_to_response('rms/campaign.html', {'form':form, 'campaign':campaign}, context_instance=RequestContext(request))


@login_required
@check_role(['CC Manager'])
def campaign_agents(request, campaign_id=None):
    """Assign inbound and outbound agents to a campaign
    """
    if campaign_id:
        campaign_id = int(campaign_id)
    
    try:
        campaign = Campaign.objects.get(pk=campaign_id, demo=False)
    except:
        return http_error_page(request, error_code=404)

    if not ((request.session['role'] == 'RMS Admin') or (campaign_id in request.session['campaign_ids'])):
        return http_error_page(request)

    if request.method == 'POST':
        form = CampaignAgentForm(request.POST, instance=campaign)
        
        if form.is_valid():
            form.save()
            agents = list(form.cleaned_data['inbound_agents'])
            agents.extend(list(form.cleaned_data['outbound_agents']))
            for agent in agents:
                try:
                    new_permission = Permission(user=agent.user, content_object=campaign, system='rms')
                    new_permission.save()
                except IntegrityError:
                    #Ignore integrity errors
                    pass
            return HttpResponseRedirect('/campaign/%s' % campaign_id)
    else:    
        form = CampaignAgentForm(instance=campaign)
    grouping = list(Agent.objects.exclude(report_to=None).values('report_to__name').annotate(number=Count('id')).order_by('report_to__name'))
    count = []
    if grouping:
        count.append(grouping[0]['number']-1)
        s = count[0]
        for group in grouping[1:]:
            s += group['number']
            count.append(s)
    return render_to_response('rms/campaign_agents.html', {'form':form, 'campaign':campaign, 'grouping':grouping, 'count':count}, context_instance=RequestContext(request))


@login_required
@check_role(['CallCenter','CC Manager','RMS Client'])
def campaign(request, campaign_id=None):
    """Display campaign details
    Agent can only see the details of assigned campaigns
    Funnel summary can be filtered by start and end dates (POST data)
    """
    if campaign_id:
        campaign_id = int(campaign_id)

    error = False
    try:
        campaign = Campaign.objects.select_related('client').get(pk=campaign_id, demo=False)
    except:
        return http_error_page(request, error_code=404)
   
    if not ((request.session['role'] == 'RMS Admin') or (campaign_id in request.session['campaign_ids'])):
        return http_error_page(request)

    dates = check_dates(request)
    start_date = dates['start_date']
    end_date = dates['end_date']
    search_trend = dates['search_trend']

    response_summary = funnel_summary(campaign_id, get_funnel(campaign_id=campaign_id)[0], start_date, end_date)
    
    CCManager, Client, Admin = False, False, False
    users = None
    if request.session['role'] == 'CC Manager':
        CCManager = True
    elif request.session['role'] == 'RMS Client':
        Client = True
    elif request.session['role'] == 'RMS Admin':
        Admin = True
        users = campaign.users.all()
    return render_to_response('rms/campaign.html', {'campaign':campaign, 'response_summary':response_summary, 'users':users,
        'CCManager':CCManager, 'Client':Client, 'Admin':Admin, 'search_trend':search_trend, 'start_date':start_date,
        'end_date':end_date, 'error':error}, context_instance=RequestContext(request))


def funnel_summary(campaign_id, funnel, start_date, end_date):
    """Returns the funnel summary for a campaign filtered on start and end dates.
    'last_interacted_on' is used to filter on date range. If 'last_interacted_on' is NULL, then 'created_on' is used to filter on date range
    Return value is the same funnel dictionary [see get_funnel() for structure explanation] with an additional key 'responses' in each
    state and substate containing the number of responses for the respective state/substate.
    The responses in a state the cumulative sum of its own responses and those from the states after it
    i.e. For 'n' states, no. of responses for state 'i' = sum[state_n, state_n-1, state_n-2, ... , state_i+1, state_i]
    """
    if end_date:
        end_date += timedelta(days=1)

    summary = Response.objects
    if start_date:
        summary = summary.filter(Q(last_interacted_on__gte=start_date) |
                        Q(Q(last_interacted_on=None) & Q(created_on__gte=start_date)))
    if end_date:
        summary = summary.filter(Q(last_interacted_on__lte=end_date) |
                        Q(Q(last_interacted_on=None) & Q(created_on__lte=end_date)))

    summary = summary.filter(campaign__id=campaign_id).values('funnel_state', 'funnel_sub_state').annotate(responses=Count('id')).order_by('funnel_state','funnel_sub_state')
    
    i,j,new = 0,0,0
    if summary and not summary[i]['funnel_state']:
        new = summary[i]['responses']
        i += 1
    
    cumulative_count = []
    for state in funnel['states']:
        for substate in state['substates']:
            if i < len(summary) and state['id'] == summary[i]['funnel_state'] and substate['id'] == summary[i]['funnel_sub_state']:
                substate['responses'] = summary[i]['responses']  #No. of responses for each substate
                j += summary[i]['responses']
                i += 1
            else:
                substate['responses'] = 0
        cumulative_count.append(j)      #No. of responses for each state
        j = 0

    funnel['new'] = new                                 #New responses
    funnel['responses'] = sum(cumulative_count)+new     #Total no. of responses
    funnel['untagged'] = Response.objects.filter(campaign__id=campaign_id, call_in_progress=True).count()
    
    #Find the cumulative count for the no. of responses for each state
    cumulative_count.reverse()
    for i,val in enumerate(cumulative_count):
        if i != 0:
            cumulative_count[i] += cumulative_count[i-1]
    cumulative_count.reverse()

    for state,val in zip(funnel['states'],cumulative_count):
        state['responses'] = val
    
    return funnel


@login_required
@check_role(['CallCenter','CC Manager','RMS Client'])
def campaign_response_list(request, campaign_id=None):
    """Returns the responses of a campaign, filtered on start, end dates, state and substate (passed as a GET variables)
    Agent can only see the responses of assigned campaigns
    Note: state=0 means we are requesting for new responses (outgoing campaigns)
    """
    if campaign_id:
        campaign_id = int(campaign_id)
        
    try:
        campaign = Campaign.objects.get(pk=campaign_id, demo=False)
        
        if not ((request.session['role'] == 'RMS Admin') or (campaign_id in request.session['campaign_ids'])):
            return http_error_page(request)
        
        state = request.GET.get('state',None)
        substate = request.GET.get('substate',None)
        start_date = request.GET.get('start',None)
        end_date = request.GET.get('end',None)
        
        response_list = Response.objects
        try:
            start_date = datetime.strptime(start_date,'%Y-%m-%d')
            response_list = response_list.filter(Q(last_interacted_on__gte=start_date) |
                        Q(Q(last_interacted_on=None) & Q(created_on__gte=start_date)))
        except:
            start_date = None
        try:
            end_date = datetime.strptime(end_date,'%Y-%m-%d')
            response_list = response_list.filter(Q(last_interacted_on__lte=end_date+timedelta(days=1)) |
                        Q(Q(last_interacted_on=None) & Q(created_on__lte=end_date+timedelta(days=1))))
        except:
            end_date = None
        response_list = response_list.filter(campaign=campaign)

        if state != None:
            if state == '0':
                #New responses
                response_list = response_list.filter(funnel_state=None)
            else:
                state = FunnelState.objects.get(pk=int(state))
                response_list = response_list.filter(funnel_state=state).order_by('funnel_sub_state')
        elif substate != None:
            substate = FunnelSubState.objects.select_related('funnel_state').get(pk=int(substate))
            state = substate.funnel_state
            response_list = response_list.filter(funnel_sub_state=substate).order_by('funnel_sub_state')
        else:
            response_list = response_list.order_by('funnel_state').order_by('funnel_sub_state')

        response_list = response_list.select_related('campaign', 'phone__user', 'funnel_state', 'funnel_sub_state',
                'last_interacted_by', 'last_interaction').order_by('-id')
    except:
        return http_error_page(request, error_code=404)

    return render_to_response('rms/campaign_response_list.html', {'response_list':response_list, 'campaign':campaign,
        'state':state, 'substate':substate, 'start_date':start_date, 'end_date':end_date}, context_instance=RequestContext(request))


@login_required
@check_role(['CC Manager','RMS Client'])
def upload_responses(request, campaign_id=None):
    """Upload responses for an outbound campaign from an excel (.xls only) file.
    Column Format: Mobile, Name, Email, City, Address, Pin, Alternate phone
    Users are created automatically when a new phone number is present.
    Checks for duplicate/invalid/blank phone numbers is also done
    """
    if campaign_id:
        campaign_id = int(campaign_id)
        
    try:
        campaign = Campaign.objects.get(pk=campaign_id, demo=False)
    except:
        return http_error_page(request, error_code=404)

    if not ((request.session['role'] == 'RMS Admin') or (campaign_id in request.session['campaign_ids'])):
        return http_error_page(request)
    
    if request.method=='POST':
        form = XlsInputForm(request.POST, request.FILES)
        error = False
        if form.is_valid():
            input_excel=request.FILES['input_excel']
            book = xlrd.open_workbook(file_contents=input_excel.read()) #Open excel file
            s=book.sheet_by_index(0)    #Read data from file
            repeat = 0
            
            invalid_phone = []  #Stores the row number containing invalid phone numbers
            overlap = []    #Stores the phone number and number of times it is repeated (as a list of tuples)
            phone_number_list, row_data, excel_data = [], [],[]
            for row in range(0,s.nrows):
                if s.cell(row,0).value == str(s.cell(row,0).value): #checks if string
                    invalid_phone.append(row+1)
                    error = True
                else:
                    #Normalize phone number. remove 0, 091, 91 etc. and return a 10 digit number
                    norm_phone = normalize_phone(str(int(s.cell(row,0).value)))
                    if len(norm_phone) != 10:
                        invalid_phone.append(row+1)
                        error = True
                    else:
                        phone_number_list.append(norm_phone)

            repeated = Counter(phone_number_list)   #Counter finds the frequency of occurence of each element in a list
            for item,count in repeated.items():
                if count > 1:   #Count>1 means there is a repetition
                    overlap.append((item,count))
                    error = True
            if error:
                return render_to_response('rms/upload_responses.html', {'campaign':campaign, 'form':form, 'status':1,
                            'invalid_phone':invalid_phone, 'overlap':overlap}, context_instance = RequestContext(request))

            for row in range(0,s.nrows):
                for col in range(0,s.ncols):
                    if col==0 or col ==6:
                        if s.cell(row,col).value != str(s.cell(row,col).value):
                            row_data.append(normalize_phone(str(int(s.cell(row,col).value))))
                        else:
                            row_data.append(s.cell(row,col).value)
                    elif col == 5:
                        if s.cell(row,col).value !=str(s.cell(row,col).value):
                            row_data.append(int(s.cell(row,col).value))
                        else:
                            row_data.append(s.cell(row,col).value)
                    else:
                        row_data.append(str(s.cell(row,col).value))
                excel_data.append(row_data)
                row_data = []
                
            for row in range(0,s.nrows):
                phone_from_excel = excel_data[row][0]
                email_from_excel = excel_data[row][2]
                name_from_excel  = excel_data[row][1]
                user,profile = get_or_create_user(phone_from_excel, email_from_excel, None, name_from_excel, None)
                phone_from_table = Phone.objects.get(phone = phone_from_excel)
             
                try:
                    email = Email.objects.get(email = email_from_excel)
                except:
                    email = Email()
                    email.email=email_from_excel
                    email.user = profile
                    email.save()

                get_or_create_response(campaign=campaign, phone=phone_from_table, type='outbound', medium='database')

            return render_to_response('rms/upload_responses.html', {'campaign':campaign, 'status':2}, context_instance = RequestContext(request))
        else:
            return render_to_response('rms/upload_responses.html', {'campaign':campaign, 'form':form, 'status':1}, context_instance = RequestContext(request))
    
    form = XlsInputForm()
    return render_to_response('rms/upload_responses.html', {'campaign':campaign, 'form':form, 'status':0}, context_instance = RequestContext(request))


def get_or_create_response(campaign=None, phone=None, dni=None, phone_number=None, type='inbound', medium=None):
    """Get an open response (by phone number or phone object) from a campaign (by dni or campaign object). If no response is present, create and return it
    For a new response, the default state and substate are the first state and substates of the campaign funnel
    """
    if (not (phone_number or phone)) or (not (campaign or dni)):
        #Phone number or phone must be present
        #Campaign or dni must be present
        return None

    try:
        if not phone:
            phone_number = normalize_phone(phone_number)
            user, profile = get_or_create_user(phone_number)
            phone = Phone.objects.get(phone = phone_number)
        
        if not campaign:
            curr_time = datetime.now()
            qs = Campaign.objects.filter(type=type, draft=False, dni_number=dni, starts_on__lte=curr_time, demo=False).exclude(ends_on__lte=curr_time)
            if qs and len(qs) > 0:                                             
                campaign = qs[0]
            else:
                return None
        
        try:
            response = Response.objects.filter(campaign=campaign, phone=phone, is_closed=False).order_by('-created_on')[0]
            fb_log.info('RMS: existing response: %s, dni: %s, phone: %s' % (response.id, campaign.dni_number, phone.phone))
            #Get an open response. If more than one response exists, retrieve the latest one
        except:
            response = Response()
            response.campaign = campaign
            response.phone = phone
            if type == 'inbound':
                response.medium = 'inbound'
                response.funnel_state = FunnelState.objects.filter(funnel=campaign.funnel).order_by('id')[0]
                response.funnel_sub_state = FunnelSubState.objects.filter(funnel_state=response.funnel_state, campaign=campaign).order_by('id')[0]
            else:
                response.medium = medium
            response.save()
            fb_log.info('RMS: new response: %s, dni: %s, phone: %s' % (response.id, campaign.dni_number, phone.phone))
        return response
    except Exception, e:
        fb_log.exception('RMS: %s' % repr(e))
    return None


@login_required
def add_interaction(request, response_id=None):
    """Add an interaction after closing a call from call close popup (set call_in_progress=False)
    Only the states and substates after the current substate are shown for selection. State and substate will change
    only if call status is 'answered'. Putting a call on hold means call_in_progress=False but assigned_to will be unchanged.
    An interaction can be added to a response only if its call is in progress.
    After an interaction is created, it needs to be attached to an asterisk call object (update the Interaction foreign key
    in asterisk_call table). For this, the call instance needs to be fetched using the (response,agent) combination, filtered
    on interaction=None and in the descending order of endtime (latest call entry first)
    """
    agent = request.session.get('agent', None)
    if not agent:
        try:
            agent = Agent.objects.get(user=request.user)
        except:
            return http_error_page(request)
    call = getattr(request, 'call', None)
    type = request.GET.get('type', None)
    callid = None

    if response_id:
        #Call Close request from RMS interface
        response_id = int(response_id)
        response = Response.objects.select_related('campaign','funnel_state','funnel_sub_state','last_interaction').get(pk=response_id)
        if response.last_interaction:
            callid = response.last_interaction.callid
    elif call:
        #Call request from p. interface
        callid = call.get('id')
        if (not callid) or ('.' not in callid):
            fb_log.info('RMS: Not attached to a call, agent: %s'%agent.name)
            return HttpResponse('Not attached to a call')
        dni = call.get('dni')
        phone_number = call.get('cli')
        response_id = call.get('response_id')
        if response_id:
            response_id = int(response_id)
            response = Response.objects.select_related('campaign','funnel_state','funnel_sub_state',
                'last_interaction').get(pk=response_id)
            type = 'outbound'
        else:
            response = get_or_create_response(dni=dni, phone_number=phone_number)
            type = 'inbound'
            if not response:
                fb_log.info('RMS: Not attached to a response, agent: %s, call: %s, dni: %s' % (agent.name, callid, dni))
                return HttpResponse('Not attached to a response')
            else:
                response_id = response.id
    else:
        return http_error_page(request, error_code=403)
        
    curr_state = response.funnel_state
    curr_substate = response.funnel_sub_state
    error = False       #Indicates error in form validation
    
    if request.method == 'POST':
        fb_log.info('RMS: Call close submitted: response - %s, agent - %s' % (response.id, agent))
        if response.call_in_progress == False:
            fb_log.info('RMS: Call already closed for response: %s, agent - %s' % (response.id, agent))
            return HttpResponse('Call already closed for this response')
        
        if request.POST.get('submit') == 'hold':    #Call put on hold
            response.on_hold = True
            response.call_in_progress = False
            response.save()
            return HttpResponse('Response put on Hold')

        form = CallCloseForm(request.POST)
        if form.is_valid():
            try:
                new_state = FunnelState.objects.get(pk=int(form.cleaned_data['state']))
                new_substate = FunnelSubState.objects.get(pk=int(form.cleaned_data['substate']))
                move_response(response=response, state=new_state, substate=new_substate,
                    agent=agent, form=form, callid=callid)
                return HttpResponse('Interaction updated successfully')
            except Exception, e:
                fb_log.info('RMS1: Error selecting funnel state and substate - %s' %e)
        else:
            error = True
            fb_log.info('RMS: Error in form submission - agent: %s' % agent)
    
    #Get the campaign funnel
    funnel = get_funnel(campaign_id = response.campaign.id)[0]
    state_list = []
    substate_list = []
    for state in funnel['states']:
        if (not curr_state) or state['id'] >= curr_state.id:
            #Only the states after the current state (including itself) are selectable
            substates = []
            for substate in state['substates']:
                if not substate['active']:
                    #Ignore untaggable (inactive) substates
                    continue
                substates.append((substate['id'],substate['name']))
            if substates:
                #Add a state to the dropdown only if it has some substates which can be tagged
                substate_list.append(substates)
                state_list.append((state['id'],state['name']))

    if not error:
        form = CallCloseForm()
        form.fields['state'].widget = forms.Select(choices=state_list)  #Update state_list in the form
        form.fields['substate'].widget = forms.Select(choices=substate_list[0])
        if response.funnel_sub_state and response.funnel_sub_state.is_active:
            form.fields['substate'].initial = response.funnel_sub_state.id  #Set initial sub_state as the current sub_state
        #if type == 'inbound':
        #    form.fields['call_status'].initial = 'answered'             #Set initial call_status as answered for inbound calls
    
    form.fields['communication'].widget = forms.HiddenInput()       #This field is not being used currently
    fb_log.info('RMS: Call popup rendered for response - %s'% response_id)
    return render_to_response('rms/add_interaction.html', {'form':form, 'state_list':state_list,
        'substate_list':substate_list, 'type':type}, context_instance = RequestContext(request))


def move_response(response=None, state=None, substate=None, callid=None, agent=None, form=None):
    if (not response) or (response.funnel_state and state and state.id < response.funnel_state.id):
        #Cannot move a response backwards
        fb_log.info('RMS: Error - Moving response backwards - %s, call - %s' % (response.id, callid))
        return

    if not agent:
        #Confirmed order signal
        response.funnel_state = state
        response.funnel_sub_state = substate
        if substate:
            response.is_closed = substate.exit_substate
        response.closed_on = datetime.now()
        response.followup_on = None
        response.assigned_to = None
        response.save()
        fb_log.info('RMS: Confirmed order for response - %s' % response.id)
        return
    
    response.call_in_progress = True
    response.assigned_to = agent
    interaction = None
    try:
        if callid:
            interaction = Interaction.objects.get(response=response, callid=callid)
            interaction.post_funnel_state = state
            interaction.post_funnel_sub_state = substate
            interaction.agent = agent
            fb_log.info('RMS: Existing interaction picked up for response - %s, call - %s' % (response.id, callid))
    except Interaction.DoesNotExist:
        pass
    except Exception, e:
        fb_log.info('RMS: Error in move_response. response - %s, call - %s' % (response.id, callid))
        return

    if not interaction:
        interaction = Interaction(response=response, agent=agent, callid=callid, pre_funnel_state=response.funnel_state,
            pre_funnel_sub_state=response.funnel_sub_state, post_funnel_state=state, post_funnel_sub_state=substate)
        interaction.communication_mode = 'call'
        response.attempts += 1
        response.connections += 1
        fb_log.info('RMS: Interaction created for response: %s, call - %s' % (response.id, callid))

    if form:
        interaction.notes = form.cleaned_data['notes']
        interaction.followup_on = form.cleaned_data['followup_on']
        if not interaction.followup_on:
            interaction.followup_on = datetime.now() + timedelta(days=1)
        response.call_in_progress = False
        response.on_hold = False
        response.assigned_to = agent

    if interaction.post_funnel_sub_state and interaction.post_funnel_sub_state.exit_substate:
        interaction.followup_on = None
        response.is_closed = True
        response.closed_on = datetime.now()
        response.closed_by = agent
        response.assigned_to = None
    else:
        response.is_closed = False
        response.closed_on = None
        response.closed_by = None

    interaction.save()
    response.funnel_state = interaction.post_funnel_state
    response.funnel_sub_state = interaction.post_funnel_sub_state
    response.last_interaction = interaction
    response.last_interacted_by = interaction.agent
    response.last_interacted_on = interaction.timestamp
    if interaction.followup_on:
        response.followup_on = interaction.followup_on
    response.save()

    try:
        #Attach call to interaction, if not done already
        call = Call.objects.get(uniqueid=callid, interaction=None)
        call.interaction = interaction
        call.save()
        fb_log.info('RMS: Call attached to interaction: call - %s, interaction - %s' % (callid, interaction.id))
    except Exception, e:
        fb_log.info('RMS: Adding call to interaction failed - %s, call - %s: %s' % (interaction.id, callid, e))


@login_required
@check_role(['CallCenter','CC Manager'])
def get_agent_responses(request):
    """Assign outbound responses to an agent or return already assigned responses
    If the agent already has assigned responses, return those without assigning any new ones.
    Responses can be of 3 types: new, onhold and inbound (specified by GET variable). New responses are outgoing responses which
    have been assigned to the agent and not attempted yet. Onhold responses are the outgoing responses which were put on hold by
    the agent. Inbound responses are generated by incoming calls to this agent.
    Responses will be assigned only if the agent asks for them (POST data). Followup responses have the highest priority, followed by
    campaign priority. If all assigned campaigns have followup responses, then responses from all these campaigns will be assigned,
    based on the campaign priority. A campaign with priority 3 (lowest) gets 1 response, priority 2 gets 2 and priority 1 gets 3
    responses assigned and this process is repeated till 10 responses have been assigned.
    """
    agent = request.session['agent']
    if not agent:
        try:
            agent = Agent.objects.get(user=request.user)
        except:
            return http_error_page(request)
    
    #choice = request.GET.get('choice','new')
    choice = request.GET.get('choice','followup')
    num = 10                        #By default, assign 10 new responses
    curr_datetime = datetime.now()
    assigned_responses = []         #List of assigned reponses (max = num)
    response_count = {}             #Contains number of responses assigned from each campaign, keyed on campaign.id
    additional_responses = {}       #Contains list of responses (not assigned yet), keyed on campaign.id
    cursor = connection.cursor()    #Database connection for RAW SQL
    num_responses_assigned = 0
    
    #Check if responses have already been assigned to this agent (not closed yet)
    '''
    assigned_responses = Response.objects.filter(assigned_to=agent,
        followup_on__lte=(curr_datetime+timedelta(minutes=30))).select_related('campaign', 'phone__user', 'funnel_state',
        'funnel_sub_state', 'last_interacted_by', 'last_interaction').order_by('followup_on')
    if choice == 'onhold':
        assigned_responses = assigned_responses.filter(on_hold=True)
    elif assigned_responses:
        assigned_responses = assigned_responses.filter(on_hold=False)
    num_responses_assigned = len(assigned_responses)
    if num_responses_assigned:
        return render_to_response('rms/agent_response_list.html', {'assigned_responses':assigned_responses, 'choice':choice},
                context_instance=RequestContext(request))
    '''
    if choice != 'new':
        assigned_responses = Response.objects.filter(assigned_to=agent,
            followup_on__lte=(curr_datetime+timedelta(minutes=30))).exclude(funnel_state=None).select_related('campaign', 'phone__user', 'funnel_state',
            'funnel_sub_state', 'last_interacted_by', 'last_interaction').order_by('followup_on')
        if choice == 'onhold':
            assigned_responses = assigned_responses.filter(on_hold=True)
        elif assigned_responses:
            assigned_responses = assigned_responses.filter(on_hold=False)
        return render_to_response('rms/agent_response_list.html', {'assigned_responses':assigned_responses, 'choice':choice},
                    context_instance=RequestContext(request))

    else:
        assigned_responses = Response.objects.filter(assigned_to=agent,
            followup_on__lte=(curr_datetime+timedelta(minutes=30)),funnel_state=None).select_related('campaign', 'phone__user', 'funnel_state',
            'funnel_sub_state', 'last_interacted_by', 'last_interaction').order_by('followup_on')
        num_responses_assigned = len(assigned_responses)
        if num_responses_assigned:
            return render_to_response('rms/agent_response_list.html', {'assigned_responses':assigned_responses, 'choice':choice},
                    context_instance=RequestContext(request))
        
    if not request.POST.get('submit',None):
    #Agent does not want new responses, clean=True
        return render_to_response('rms/agent_response_list.html', {'clean':True, 'choice':choice}, context_instance=RequestContext(request))
    else:
        assigned_responses = []         # should be a list (not QuerySet object) as later responses are appended to this list
        #Agent has requested for new responses
        assigned_campaigns = agent.outbound_campaigns.filter(starts_on__lte=curr_datetime, draft=False,
                demo=False).exclude(ends_on__lte=curr_datetime).order_by('priority')
        if not assigned_campaigns:
            return render_to_response('rms/agent_response_list.html', {'assigned_responses':assigned_responses, 'choice':choice},
                context_instance=RequestContext(request))

        # assign responses from P0 priority campaign first (if assigned)        
        from heapq import heappush, heappop
        other_campaigns = []    # used for p0 priority campaigns
        max_priority = 1
        pq=[]       # priority queue
        num_responses_remaining = num
        for campaign in assigned_campaigns:
            if campaign.priority == 0:
                responses = Response.objects.filter(campaign=campaign, is_closed=False, assigned_to=None,
                    call_in_progress=False, followup_on__lte=curr_datetime+timedelta(minutes=30)).order_by('followup_on')[:num_responses_remaining]
                for response in responses:
                    cursor.execute("UPDATE rms_response SET assigned_to_id = %s WHERE (id = %s AND (assigned_to_id IS NULL))", [agent.id, response.id])
                    transaction.commit_unless_managed()
                    #The above query acts as a lock which prevents the same response from being assigned to multiple agents
                    if cursor.rowcount:
                        assigned_responses.append(response)   #Not assigned to any agent
            
                num_responses_assigned = len(assigned_responses)        
                if num  == num_responses_assigned:
                    return render_to_response('rms/agent_response_list.html', {'assigned_responses':assigned_responses, 'choice':choice},
                        context_instance=RequestContext(request))
                else:
                    num_responses_remaining = num - num_responses_assigned
            else:
                other_campaigns.append(campaign)
                if campaign.priority > max_priority:
                    max_priority = campaign.priority
                heappush(pq,(campaign.priority,campaign))

        num = num - num_responses_assigned  # num is now the number of remaining responses to be assigned
        
        if(other_campaigns):
            # now assign responses from other_campaigns
            count = num
            campaign_share = {}
            for campaign in other_campaigns:
                campaign_share ['%d'%campaign.id] = 0
            while count > 0:
                if pq:
                    temp = heappop(pq)  # pop up highest priority campaign
                    count -= 1
                    campaign_share['%d'%temp[1].id] += 1
                    if temp[0] < max_priority:
                        heappush(pq,((temp[0] + 1), temp[1]))
                else:
                    for campaign in other_campaigns:
                        heappush(pq,(campaign.priority,campaign))
                
            # assign responses as per campaign shares
            diff = num
            for campaign in other_campaigns:
                if diff == 0:
                    break
                additional_responses['%d'%campaign.id] = []
                share = campaign_share['%d'%campaign.id]
                responses = Response.objects.filter(campaign=campaign, is_closed=False, assigned_to=None,
                    call_in_progress=False, followup_on__lte=curr_datetime+timedelta(minutes=30)).order_by('followup_on')[:diff]
                
                count = 0
                for response in responses:
                    if diff > 0 and share > 0:
                        cursor.execute("UPDATE rms_response SET assigned_to_id = %s WHERE (id = %s AND (assigned_to_id IS NULL))", [agent.id, response.id])
                        transaction.commit_unless_managed()
                        #The above query acts as a lock which prevents the same response from being assigned to multiple agents
                        if cursor.rowcount:
                            assigned_responses.append(response)   #Not assigned to any agent
                            share -= 1
                            diff -= 1
                    else:
                        additional_responses['%d'%campaign.id] = responses[count:]
                        break
                    count += 1

            #Required number of responses not met still
            #Add responses independent of campaign priority
            flag = True     #Becomes false if no more responses can be added
            while diff > 0 and flag:
                flag = False
                for campaign in other_campaigns:
                    if diff == 0:
                        break
                    else:
                        if additional_responses['%d'%campaign.id]:
                            flag = True
                            response = additional_responses['%d'%campaign.id].pop(0)
                            cursor.execute("UPDATE rms_response SET assigned_to_id = %s WHERE (id = %s AND (assigned_to_id IS NULL))", [agent.id, response.id])
                            transaction.commit_unless_managed()
                            #The above query acts as a lock which prevents the same response from being assigned to multiple agents
                            if cursor.rowcount:
                                assigned_responses.append(response)   #Not assigned to any agent
                                diff -= 1


        return render_to_response('rms/agent_response_list.html', {'assigned_responses':assigned_responses, 'choice':choice},
                context_instance=RequestContext(request))
    '''
    assigned_responses = []         # should be a list (not QuerySet object) as later responses are appended to this list
    #No existing assigned responses. Check if the agent wants to get new responses
    if not request.POST.get('submit',None):
    #Agent does not want new responses, clean=True
        return render_to_response('rms/agent_response_list.html', {'clean':True, 'choice':choice}, context_instance=RequestContext(request))
    
    #Agent has requested for new responses
    assigned_campaigns = agent.outbound_campaigns.filter(starts_on__lte=curr_datetime, draft=False,
            demo=False).exclude(ends_on__lte=curr_datetime).order_by('priority')
    if not assigned_campaigns:
        return render_to_response('rms/agent_response_list.html', {'assigned_responses':assigned_responses, 'choice':choice},
            context_instance=RequestContext(request))

    #Decide max number of responses to pick from each campaign based on priority
    max_responses = []
    for campaign in assigned_campaigns:
        max_responses.append(int(campaign.priority))
    min_p = min(max_responses)-1
    if min_p:
        f = lambda x: int(x-min_p)
        max_responses = map(f, max_responses)           #Shift the priority values such that the highest one starts from 1
    s = sum(max_responses)
    f = lambda x: int(math.ceil(x*float(num)/s))
    max_responses = map(f, max_responses) 
    max_responses.reverse()                 #Reverse list because 1 represents highest priority
    s = sum(max_responses)
    for i in range(len(max_responses)):
        if s == num:
            break
        max_responses[i] -= 1
        s -= 1
    
    #Get followup responses
    for max_r,campaign in reversed(zip(max_responses,assigned_campaigns)):
        response_count['%d'%campaign.id] = 0
        additional_responses['%d'%campaign.id] = []
        
        # set query_set filter parameters
        responses = Response.objects.filter(campaign=campaign, is_closed=False, assigned_to=None, last_interacted_by=agent,
                call_in_progress=False, followup_on__lte=(curr_datetime+timedelta(minutes=30))).order_by('followup_on', 'id')
        
        # select foreign key objects to be retrieved
        responses = responses.select_related('campaign', 'phone__user', 'funnel_state',
                'funnel_sub_state', 'last_interacted_by', 'last_interaction')
        
        for i,response in enumerate(responses):
            if response_count['%d'%campaign.id] < max_r:
                cursor.execute("UPDATE rms_response SET assigned_to_id = %s WHERE (id = %s AND (assigned_to_id IS NULL))", [agent.id, response.id])
                transaction.commit_unless_managed()
                #The above query acts as a lock which prevents the same response from being assigned to multiple agents
                if cursor.rowcount:
                    assigned_responses.append(response)   #Not assigned to any agent
                    response_count['%d'%campaign.id] += 1
                    num_responses_assigned += 1
            else:
                #Response was already assigned, so drop this
                additional_responses['%d'%campaign.id] = responses[i:]
                break

    diff = num - num_responses_assigned
    #Check if required number of responses have been assigned
    #Add more followup responses independent of campaign priority
    flag = True     #Becomes False if no more followup responses are present
    while (diff > 0 and flag):
        flag = False
        for campaign in assigned_campaigns:
            if diff == 0:
                break
            else:
                if additional_responses['%d'%campaign.id]:
                    flag = True
                    response = additional_responses['%d'%campaign.id].pop(0)
                    cursor.execute("UPDATE rms_response SET assigned_to_id = %s WHERE (id = %s AND (assigned_to_id IS NULL))", [agent.id, response.id])
                    transaction.commit_unless_managed()
                    if cursor.rowcount:
                        assigned_responses.append(response)     #Not assigned to any agent
                        response_count['%d'%campaign.id] += 1
                        diff -= 1
                        num_responses_assigned += 1
    
    #Finished adding followup responses
    #Add more responses (if needed), without exceeding priority limits
    for max_r,campaign in zip(max_responses,assigned_campaigns):
        if diff == 0:
            break
        #set query_set filter parameters
        responses = Response.objects.filter(campaign=campaign, is_closed=False, assigned_to=None,
            call_in_progress=False, followup_on__lte=curr_datetime+timedelta(minutes=30)).order_by('followup_on')
        
        #select foreign key objects to be retrieved
        responses = responses.select_related('campaign', 'phone__user', 'funnel_state',
                'funnel_sub_state', 'last_interacted_by', 'last_interaction')
        
        for i,response in enumerate(responses):
            if (diff > 0) and (response_count['%d'%campaign.id] < max_r):
                cursor.execute("UPDATE rms_response SET assigned_to_id = %s WHERE (id = %s AND (assigned_to_id IS NULL))", [agent.id, response.id])
                transaction.commit_unless_managed()
                if cursor.rowcount:
                    assigned_responses.append(response)     #Not assigned to any agent
                    response_count['%d'%campaign.id] += 1 
                    diff -= 1
                    num_responses_assigned += 1
            else:
                additional_responses['%d'%campaign.id] = responses[i:]
                break

    #Required number of responses not met still
    #Add responses independent of campaign priority
    flag = True     #Becomes false if no more responses can be added
    while diff > 0 and flag:
        flag = False
        for campaign in assigned_campaigns:
            if diff == 0:
                break
            else:
                if additional_responses['%d'%campaign.id]:
                    flag = True
                    response = additional_responses['%d'%campaign.id].pop(0)
                    cursor.execute("UPDATE rms_response SET assigned_to_id = %s WHERE (id = %s AND (assigned_to_id IS NULL))", [agent.id, response.id])
                    transaction.commit_unless_managed()
                    if cursor.rowcount:
                        assigned_responses.append(response)     #Not assigned to any agent
                        response_count['%d'%campaign.id] += 1
                        diff -= 1
                        num_responses_assigned += 1
    
    return render_to_response('rms/agent_response_list.html', {'assigned_responses':assigned_responses, 'choice':choice},
            context_instance=RequestContext(request))
'''

@login_required
@check_role(['CC Manager'])
def get_untagged_responses(request, campaign_id=None):
    """View all untagged responses (responses which are assigned to an agent) for a campaign
    """
    if campaign_id:
        campaign_id = int(campaign_id)
    
    try:
        campaign = Campaign.objects.get(pk=campaign_id, demo=False)
        if not ((request.session['role'] == 'RMS Admin') or (campaign_id in request.session['campaign_ids'])):
            return http_error_page(request)
        response_list = Response.objects.filter(campaign=campaign, call_in_progress=True).select_related('campaign',
                'phone__user', 'assigned_to')
    except:
        return http_error_page(request, error_code=404)
    return render_to_response('rms/untagged_response_list.html', {'response_list':response_list, 'campaign':campaign}, context_instance=RequestContext(request))


def get_response_list_forJS(request):
    """Returns a string containing a javascript list of assigned response_ids for an agent.
    Javascript polls this view every 30 secs and updates agent home screen
    """
    agent = request.session['agent'] 
    if not agent:
        return HttpResponse([])
    choice = request.GET.get('choice','new')
    assigned_responses = []
    assigned_responses = Response.objects.filter(assigned_to=agent)
    if choice == 'onhold':
        assigned_responses = assigned_responses.filter(on_hold=True)
    else:
        assigned_responses = assigned_responses.filter(on_hold=False)
    
    response_ids = ','.join([str(response.id) for response in assigned_responses])
    return HttpResponse(response_ids)


@login_required
@check_role(['CallCenter','CC Manager','RMS Client'])
def get_interactions(request, response_id=None):
    """Return the list of interactions for a response
    """
    
    num = request.GET.get('num',0)
    interaction_list = Interaction.objects.filter(response__id=response_id, invalid=False).order_by('-timestamp').select_related('agent',
        'pre_funnel_state', 'pre_funnel_sub_state', 'post_funnel_state', 'post_funnel_sub_state')
    if num:
        interaction_list = interaction_list[:num]
    return render_to_response('rms/interaction_list.html', {'interaction_list':interaction_list, 'response_id':response_id},
                context_instance=RequestContext(request))


@login_required
@check_role(['CallCenter','CC Manager'])
def call_response(request, response_id=None):
    agent = request.session['agent']
    if not agent:
        try:
            agent = Agent.objects.get(user=request.user)
        except:
            agent = None

    if not request.method == 'POST':
        return return_api_response(request, 'FAIL', 'INVALID_HTTP_METHOD', 'Invalid http method. Method should be post', 400) 
    
    if not agent:
        return return_api_response(request, 'FAIL', 'NO_AGENT_ATTACHED', 'Cannot place call, you dont have attached agent id.', 400) 
    
    try:
        response = Response.objects.get(pk=response_id)
        task = Task(agent=agent, response=response, type='call_by_agent_to_response', status='New')
        task.save()
        return return_api_response(request, 'SUCCESS', 'CALL_PLACED', 'Call placed', 200)
    except Response.DoesNotExist:
        return return_api_response(request, 'FAIL', 'NO_SUCH_RESPONSE', 'Cannot place call, unable to find requested response.', 404)
    except Exception, e:
        return return_api_response(request, 'FAIL', 'SYSTEM_ERROR', 'Cannot place call. Please try later.', 500)


def return_api_response(request, status, msg_code, msg, http_code, data=None):
    resp = dict(msg_code = msg_code, msg = msg, status = status)
    if data:
        resp['data'] = data
    return HttpResponse(simplejson.dumps(resp), mimetype="application/json",
            status=http_code)

@login_required
@check_role([])
def users(request, user_id=None):
    group_list = ['CallCenter','CC Manager','RMS Client','RMS Admin']
    if not user_id:
        users = User.objects.distinct().filter(groups__name__in=group_list).order_by('username')
        return render_to_response('rms/user_list.html', {'users':users, 'group_list':group_list}, context_instance=RequestContext(request))

    try:
        user = User.objects.get(pk=int(user_id))
    except User.DoesNotExist:
        return http_error_page(request, error_code=404)

    try:
        role = user.groups.filter(name__in=group_list)[0]
    except:
        return http_error_page(request, error_code=404)
    ids = Permission.objects.filter(user=user, content_type=request.session['type_campaign'], system='rms').values_list('object_id', flat=True)
    campaigns = Campaign.objects.filter(id__in=ids, demo=False)
    return render_to_response('rms/user.html', {'rms_user':user, 'role':role, 'campaigns':campaigns}, context_instance=RequestContext(request))


@login_required
@check_role([])
def user_add(request):
    if request.method == 'POST':
        form = AddUserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                return HttpResponse('No user exists with username - %s' % username)
            
            group_list = ['CallCenter','CC Manager','RMS Client','RMS Admin']
            if user.groups.filter(name__in=group_list):
                return HttpResponse('User already exists')
            user.groups.add(form.cleaned_data['role'])
            user.save()
            return HttpResponse('User added successfully')
        else:
            return render_to_response('rms/user_add.html', {'form':form}, context_instance=RequestContext(request))
    
    form = AddUserForm()
    return render_to_response('rms/user_add.html', {'form':form}, context_instance=RequestContext(request))


@login_required
@check_role([])
def user_edit(request, user_id=None):
    group_list = ['CallCenter','CC Manager','RMS Client','RMS Admin']
    try:
        user = User.objects.get(pk=int(user_id))
    except User.DoesNotExist:
        return http_error_page(request, error_code=404)
    
    if request.method == 'POST':
        form = EditUserForm(request.POST)
        if form.is_valid():
            existing_group = user.groups.filter(name__in=group_list)[0]
            new_group = form.cleaned_data['role']
            if new_group:
                if existing_group.id != new_group.id:
                    user.groups.remove(existing_group)
                    user.groups.add(new_group)
                    user.save()
            else:
                user.groups.remove(existing_group)
                user.save()
                #Removed user group. Delete the user permissions also
                Permission.objects.using('default').filter(system='rms', user=user).delete()
                return HttpResponseRedirect('/user/')
            
            ids = Permission.objects.filter(user=user, system='rms', content_type=request.session['type_campaign']).values_list('object_id', flat=True)
            existing_campaigns = set(Campaign.objects.filter(id__in=ids, demo=False))
            new_campaigns = set(form.cleaned_data['campaigns'])
            for campaign in (new_campaigns-existing_campaigns):
                try:
                    new_permission = Permission(user=user, content_object=campaign, system='rms')
                    new_permission.save()
                except IntegrityError:
                    #Ignore integrity errors
                    pass
            #Delete old permissions
            Permission.objects.using('default').filter(system='rms', user=user, content_type=request.session['type_campaign'],
                object_id__in=[c.id for c in (existing_campaigns-new_campaigns)]).delete()
            return HttpResponseRedirect('/user/%s' % user.id)
        else:
            return render_to_response('rms/user.html', {'rms_user':user, 'form':form}, context_instance=RequestContext(request))

    try:
        role = user.groups.filter(name__in=group_list)[0]
    except:
        return http_error_page(request, error_code=404)
    campaigns = Permission.objects.filter(user=user, content_type=request.session['type_campaign'], system='rms').values_list('object_id', flat=True)
    form = EditUserForm(initial={'role':role.id, 'campaigns':campaigns})
    return render_to_response('rms/user.html', {'rms_user':user, 'form':form}, context_instance=RequestContext(request))


@login_required
@check_role([])
def user_group(request, group_id=None):
    try:
        group = Group.objects.get(pk=group_id, name__in=['CallCenter','CC Manager','RMS Client','RMS Admin'])
    except:
        return http_error_page(request, error_code=404)

    users = User.objects.filter(groups=group).order_by('first_name')
    return render_to_response('rms/user_group.html', {'group':group, 'users':users}, context_instance=RequestContext(request))


@login_required
@check_role(['CC Manager'])
def backlog(request):
    if request.session['role'] == 'CC Manager':
        manager = Agent.objects.filter(user=request.user)
        teamleads = Agent.objects.filter(role='lead', report_to=manager)
        agents = Agent.objects.filter(role='agent', report_to__in=teamleads).order_by('name')
    else:    
        agents = Agent.objects.all().order_by('name')
#    agent_details = {}
#    timenow = datetime.now()
#    followup_time = timenow - timedelta(minutes=-30)
#    for agent in agents:
#        followups = Response.objects.filter(assigned_to = agent, is_closed=False, followup_on__lt=followup_time).count()
#        agent_details[agent] = followups
#   return render_to_response('rms/agent_backlog.html', {'agents':agent_details}, context_instance=RequestContext(request))
    return render_to_response('rms/agent_backlog.html', {'agents':agents}, context_instance=RequestContext(request))

