import logging, re
from datetime import datetime, date, timedelta
import xml.etree.ElementTree as xml
from decimal import Decimal
from django import forms
from django.db import transaction
from django.db.models import Q, F
from django.http import HttpResponse, HttpResponseRedirect
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import Group, User as AuthUser
from django.contrib import messages
from django.db import IntegrityError
from django.core.cache import cache
from orders.models import (Order, OrderItem, ThirdPartyOrders, OrderXML, DeliveryInfo,
    BillingInfo, ReturnOrder, SAPOrderItem, OrderLog, OrderItemLog)
from complaints.models import Complaint, Update
from complaints.forms import ComplaintAddForm, ComplaintUpdateForm, ComplaintFilterForm
from orders.forms import ShippingInfoForm, BillingInfoForm, DeliveryNotesForm
from payments.models import PaymentAttempt, Refund, RefundItem
from users.models import Email, Phone, Profile
from fulfillment.models import Shipment, ShipmentItem, Dc, ShipmentLog, Lsp
from utils import utils
from utils import solrutils
from analytics_utils.utils import save_excel_file
from support.decorators import check_role
from support.models import User, Team, State, SubState, ActionFlow, InformationFlow
from support.forms import *
from accounts.models import Client, Account, PaymentGateways, PaymentMode
from catalog.models import SellerRateChart, Product
from categories.models import Category, CategoryGraph
from support.exceptions import *
from django.utils import simplejson
import operator

LSP_CODES = {'DL':'delivered', 'RT':'returned', 'INT':'in transit', 
        'UD':'undeliverable', }

fb_log = logging.getLogger('fborder')
sap_log = logging.getLogger('sap')

def http_error_page(request, error_code=403):
    resp = render_to_response('support/%s.html'%error_code, context_instance=RequestContext(request))
    resp.status_code = error_code
    return resp


@login_required
def homepage_redirect(request):
    #return HttpResponseRedirect('/team')
    return HttpResponseRedirect('/order')


@login_required
@check_role([])
def team_add(request):
    error = False
    if request.method == 'POST':
        form = TeamForm(request.POST)
        if form.is_valid():
            team = form.save()
            return HttpResponse('Team added successfully')
        error = True
    else:
        form = TeamForm()
    resp = render_to_response('support/team_add.html', {'form':form}, context_instance=RequestContext(request))
    if error:
        resp.status_code = 400
    return resp


@login_required
@check_role([])
def team_edit(request, team_id=None):
    try:
        team = Team.objects.get(pk=team_id)
    except Team.DoesNotExist:
        return http_error_page(request, error_code=404)

    if request.method == 'POST':
        form = TeamForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/team/%s/' % team.id)
    else:
        form = TeamForm(instance=team)
        form.fields['name'].initial = team.name
    return render_to_response('support/team.html', {'form':form, 'team':team}, context_instance=RequestContext(request))


@login_required
@check_role([])
def team(request, team_id=None):
    if team_id:
        try:
            team = Team.objects.get(pk=team_id)
        except Team.DoesNotExist:
            return http_error_page(request, error_code=404)
        members = team.members.all().select_related('user').order_by('user__first_name')
        return render_to_response('support/team.html', {'team':team, 'members':members}, context_instance=RequestContext(request))

    else:
        team_list = Team.objects.all()
        return render_to_response('support/team_list.html', {'team_list':team_list}, context_instance=RequestContext(request))


@login_required
@check_role([])
def user_add(request):
    error = False
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            try:
                auth_user = AuthUser.objects.get(username=username)
            except AuthUser.DoesNotExist:
                resp = HttpResponse('No user exists with the username - %s' % username)
                resp.status_code = 203
                return resp
            user = User(user=auth_user, team=form.cleaned_data['team'], role=form.cleaned_data['role'])
            try:
                user.save()
            except IntegrityError:
                resp = HttpResponse('User with username - %s already exists in the system')
                resp.status_code = 203
                return resp
            return HttpResponse('User added successfully')
        error = True
    else:
        form = UserForm()
    resp = render_to_response('support/user_add.html', {'form':form}, context_instance=RequestContext(request))
    if error:
        resp.status_code = 400
    return resp


@login_required
@check_role([])
def user_edit(request, user_id=None):
    try:
        user = User.objects.select_related('user').get(pk=user_id)
    except User.DoesNotExist:
        return http_error_page(request, error_code=404)
    
    if request.method == 'POST':
        form = UserForm(request.POST)
        if form.is_valid():
            user.team = form.cleaned_data['team']
            user.role = form.cleaned_data['role']
            user.save()
            return HttpResponseRedirect('/user/%s' % user.id)
        else:
            form.fields['username'].widget = forms.HiddenInput()
    else:
        form = UserForm()
        form.fields['username'].initial = user.user.username
        form.fields['username'].widget = forms.HiddenInput()
        form.fields['team'].initial = user.team.id
        form.fields['role'].initial = user.role
    return render_to_response('support/user.html', {'form':form, 'user':user}, context_instance=RequestContext(request))


@login_required
@check_role([])
def user(request, user_id=None):
    if user_id:
        try:
            user = User.objects.select_related('user','team').get(pk=user_id)
        except User.DoesNotExist:
            return http_error_page(request, error_code=404)
        return render_to_response('support/user.html', {'user':user}, context_instance=RequestContext(request))
    else:
        user_list = User.objects.all().select_related('user','team').order_by('user__first_name')
        return render_to_response('support/user_list.html', {'user_list':user_list}, context_instance=RequestContext(request))


@login_required
@check_role([])
def state_add(request):
    error = False
    if request.method == 'POST':
        form = StateForm(request.POST)
        if form.is_valid():
            state = form.save()
            return HttpResponse('State added successfully')
        error = True
    else:
        form = StateForm()
    resp = render_to_response('support/state_add.html', {'form':form}, context_instance=RequestContext(request))
    if error:
        resp.status_code = 400
    return resp


@login_required
@check_role([])
def state_edit(request, state_id=None):
    try:
        state = State.objects.get(pk=state_id)
    except State.DoesNotExist:
        return http_error_page(request, error_code=404)
    
    if request.method == 'POST':
        form = StateForm(request.POST, instance=state)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/state/%s' % state.id)
    else:
        form = StateForm(instance=state)
    return render_to_response('support/state.html', {'form':form, 'state':state}, context_instance=RequestContext(request))


@login_required
@check_role([])
def state(request, state_id=None):
    if state_id:
        try:
            state = State.objects.select_related('responsible_team').get(pk=state_id)
        except State.DoesNotExist:
            return http_error_page(request, error_code=404)
        substates = state.substates.all().select_related('acting_team')
        return render_to_response('support/state.html', {'state':state, 'substates':substates}, context_instance=RequestContext(request))
    else:
        state_list = State.objects.all().select_related('responsible_team').order_by('name')
        return render_to_response('support/state_list.html', {'state_list':state_list}, context_instance=RequestContext(request))


@login_required
@check_role([])
def substate_add(request):
    error = False
    if request.method == 'POST':
        form = SubStateForm(request.POST)
        entity = None
        if form.is_valid():
            substate = form.save(commit=False)
            state = substate.state.name
            if state in ['Booked','Paid']:
                entity = 'PaymentAttempt'
            elif state == 'Confirmed':
                entity = 'OrderItem'
            elif state in ['Invoiced','Shipped']:
                entity = 'Shipment'
            substate.entity = request.session['content_types'][entity]
            substate.save()
            return HttpResponse('Substate added successfully')
        error = True
    else:
        form = SubStateForm()
        content_types = []
        for key,val in request.session['content_types'].iteritems():
            content_types.append((val.id,val.name))
    resp = render_to_response('support/substate_add.html', {'form':form}, context_instance=RequestContext(request))
    if error:
        resp.status_code = 400
    return resp


@login_required
@check_role([])
def substate_edit(request, substate_id=None):
    try:
        substate = SubState.objects.get(pk=substate_id)
    except SubState.DoesNotExist:
        return http_error_page(request, error_code=404)
    
    if request.method == 'POST':
        form = SubStateForm(request.POST, instance=substate)
        if form.is_valid():
            substate = form.save(commit=False)
            state = substate.state.name
            if state in ['Booked','Paid']:
                entity = 'PaymentAttempt'
            elif state == 'Confirmed':
                entity = 'OrderItem'
            elif state in ['Invoiced','Shipped']:
                entity = 'Shipment'
            substate.entity = request.session['content_types'][entity]
            substate.save()
            return HttpResponseRedirect('/substate/%s' % substate.id)
    else:
        form = SubStateForm(instance=substate)
        content_types = []
        for key,val in request.session['content_types'].iteritems():
            content_types.append((val.id,val.name))
    return render_to_response('support/substate.html', {'form':form, 'substate':substate}, context_instance=RequestContext(request))


@login_required
@check_role([])
def substate(request, substate_id=None):
    if substate_id:
        try:
            substate = SubState.objects.select_related('state','acting_team','entity').get(pk=substate_id)
        except SubState.DoesNotExist:
            return http_error_page(request, error_code=404)
        return render_to_response('support/substate.html', {'substate':substate}, context_instance=RequestContext(request))
    else:
        substate_list = SubState.objects.all().select_related('state','acting_team','entity').order_by('name')
        return render_to_response('support/substate_list.html', {'substate_list':substate_list}, context_instance=RequestContext(request))


@login_required
@check_role([])
def actionflow_add(request):
    error = False
    if request.method == 'POST':
        form = ActionFlowForm(request.POST)
        if form.is_valid():
            flow = form.save()
            return HttpResponse('Action Flow added successfully')
        error = True
    else:
        form = ActionFlowForm()
    substates = SubState.objects.all().select_related('state').order_by('state__name','name')
    state_list, substate_list, s = [], [], []
    for substate in substates:
        if (not state_list) or (state_list[-1][1]!=substate.state.name):
            state_list.append((substate.state.id, substate.state.name))
            if s:
                substate_list.append(s)
                s = []
        s.append((substate.id, substate.name))
    substate_list.append(s)
    if state_list:
        form.fields['initial_state'].choices = state_list
        form.fields['initial_substate'].choices = substate_list[0]
        form.fields['final_state'].choices = state_list
        form.fields['final_substate'].choices = substate_list[0]
    resp = render_to_response('support/actionflow_add.html', {'form':form, 'state_list':state_list, 'substate_list':substate_list},
        context_instance=RequestContext(request))
    if error:
        resp.status_code = 400
    return resp


@login_required
@check_role([])
def actionflow_edit(request, flow_id=None):
    try:
        flow = ActionFlow.objects.select_related().get(pk=flow_id)
    except ActionFlow.DoesNotExist:
        return http_error_page(request, error_code=404)
    
    if request.method == 'POST':
        form = ActionFlowForm(request.POST, instance=flow)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/actionflow/%s' % flow.id)
    else:
        form = ActionFlowForm(instance=flow)
    substates = SubState.objects.all().select_related('state').order_by('state__name','name')
    state_list, substate_list, s = [], [], []
    i, istate, fstate = 0, 0, 0
    for substate in substates:
        if (not state_list) or (state_list[-1][1]!=substate.state.name):
            state_list.append((substate.state.id, substate.state.name))
            if substate.state.id == flow.initial_state.id:
                istate = i
            if substate.state.id == flow.final_state.id:
                fstate = i
            i += 1
            if s:
                substate_list.append(s)
                s = []
        s.append((substate.id, substate.name))
    substate_list.append(s)
    form.fields['initial_state'].choices = state_list
    form.fields['initial_substate'].choices = substate_list[istate]
    form.fields['final_state'].choices = state_list
    form.fields['final_substate'].choices = substate_list[fstate]
    return render_to_response('support/actionflow.html', {'form':form, 'flow':flow,
        'state_list':state_list, 'substate_list':substate_list}, context_instance=RequestContext(request))


@login_required
@check_role([])
def actionflow(request, flow_id=None):
    if flow_id:
        try:
            flow = ActionFlow.objects.select_related('initial_state','initial_substate','final_state','final_substate').get(pk=flow_id)
        except ActionFlow.DoesNotExist:
            return http_error_page(request, error_code=404)
        return render_to_response('support/actionflow.html', {'flow':flow}, context_instance=RequestContext(request))
    else:
        flow_list = ActionFlow.objects.all().select_related('initial_state','initial_substate',
            'final_state','final_substate').order_by('name')
        return render_to_response('support/actionflow_list.html', {'flow_list':flow_list}, context_instance=RequestContext(request))


def get_actionflows(entity=None, valid_states=None):
    if not entity:
        return {}
    flows = ActionFlow.objects.select_related('initial_substate','final_substate').filter(
        initial_substate__entity=entity).order_by('name')
    flow_dict = {}
    if (valid_states != None) and (not valid_states):
        return flow_dict
    for flow in flows:
        l = flow_dict.get(flow.initial_substate.name.lower(),[])
        if valid_states != None:
            if flow.final_substate.name.lower() in valid_states:
                l.append([int(flow.id),flow.name,flow.group])
        else:
            l.append([int(flow.id),flow.name,flow.group])
        flow_dict[flow.initial_substate.name.lower()] = l
    return flow_dict


@login_required
@check_role([])
def informationflow_add(request):
    error = False
    if request.method == 'POST':
        form = InformationFlowForm(request.POST)
        if form.is_valid():
            flow = form.save()
            return HttpResponse('Information Flow added successfully')
        error = True
    else:
        form = InformationFlowForm()
    substates = SubState.objects.all().select_related('state').order_by('state__name','name')
    state_list, substate_list, s = [], [], []
    for substate in substates:
        if (not state_list) or (state_list[-1][1]!=substate.state.name):
            state_list.append((substate.state.id, substate.state.name))
            if s:
                substate_list.append(s)
                s = []
        s.append((substate.id, substate.name))
    substate_list.append(s)
    if state_list:
        form.fields['state'].choices = state_list
        form.fields['substate'].choices = substate_list[0]
    resp = render_to_response('support/informationflow_add.html', {'form':form, 'state_list':state_list, 'substate_list':substate_list},
        context_instance=RequestContext(request))
    if error:
        resp.status_code = 400
    return resp


@login_required
@check_role([])
def informationflow_edit(request, flow_id=None):
    try:
        flow = InformationFlow.objects.select_related().get(pk=flow_id)
    except InformationFlow.DoesNotExist:
        return http_error_page(request, error_code=404)
    
    if request.method == 'POST':
        form = InformationFlowForm(request.POST, instance=flow)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/informationflow/%s' % flow.id)
    else:
        form = InformationFlowForm(instance=flow)
    substates = SubState.objects.all().select_related('state').order_by('state__name','name')
    state_list, substate_list, s = [], [], []
    i, state = 0, 0
    for substate in substates:
        if (not state_list) or (state_list[-1][1]!=substate.state.name):
            state_list.append((substate.state.id, substate.state.name))
            if substate.state.id == flow.state.id:
                state = i
            i += 1
            if s:
                substate_list.append(s)
                s = []
        s.append((substate.id, substate.name))
    substate_list.append(s)
    form.fields['state'].choices = state_list
    form.fields['substate'].choices = substate_list[state]
    return render_to_response('support/informationflow.html', {'form':form, 'flow':flow,
        'state_list':state_list, 'substate_list':substate_list}, context_instance=RequestContext(request))


@login_required
@check_role([])
def informationflow(request, flow_id=None):
    if flow_id:
        try:
            flow = InformationFlow.objects.select_related('state','substate','acting_team').get(pk=flow_id)
        except InformationFlow.DoesNotExist:
            return http_error_page(request, error_code=404)
        return render_to_response('support/informationflow.html', {'flow':flow}, context_instance=RequestContext(request))
    else:
        flow_list = InformationFlow.objects.all().select_related('state','substate','acting_team').order_by('name')
        return render_to_response('support/informationflow_list.html', {'flow_list':flow_list}, context_instance=RequestContext(request))


def filter_and_sort(request, model, **kwargs):
    qs = kwargs.get('qs', model.objects.all())
    sort = kwargs.get('sort', '-id')
    page = kwargs.get('page', 1)
    if request.GET:
        filters = {}
        for key, value in request.GET.items():
            filters[key] = value
        sort = filters.pop('sort', sort) # Default sort by id
        search = filters.pop('q', '')
        page = filters.pop('page', page)
        ignore_keys = kwargs.get('ignore_keys',[])
        for key in ignore_keys:
            if key in filters:
                filters.pop(key)
        if filters:
            qs = qs.filter(**filters)
    qs = qs.order_by(sort)
    return qs


@login_required
@check_role([])
def order_list(request):
    qs = []
    if request.method == 'GET' and request.GET:
        filter_form = OrderFilterForm(request.GET)
        if filter_form.is_valid():
            qs = Order.objects.filter(client=request.client.client).exclude(
                Q(support_state=None) | Q(payment_mode='') | Q(payment_mode=None))
            name = filter_form.cleaned_data['name']
            phone = filter_form.cleaned_data['phone']
            email = filter_form.cleaned_data['email']
            order_id = filter_form.cleaned_data['order_id']
            state = filter_form.cleaned_data['state']
            start_date = filter_form.cleaned_data['start_date']
            end_date = filter_form.cleaned_data['end_date']
            no_user = False
            if name:
                name = name.strip()
            if name:
                qs = qs.filter(user__in = [p.id for p in Profile.objects.filter(
                    full_name__icontains = name)])
            if phone and not no_user:
                phone = phone.strip()
                try:
                    ph = Phone.objects.get(phone=phone)
                    qs = qs.filter(user=ph.user)
                except Phone.DoesNotExist:
                    qs = []
                    no_user = True
            if email and not no_user:
                email = email.strip()
                try:
                    e = Email.objects.get(email=email)
                    qs = qs.filter(user=e.user)
                except Email.DoesNotExist:
                    qs = []
                    no_user = True
            if order_id and not no_user:
                order_id = re.sub(r'\s','',order_id)
                if order_id.endswith(','):
                    order_id = order_id[:-1]
                if order_id:
                    order_list = order_id.split(',')
                    if len(order_list) > 1:
                        qs = qs.filter(reference_order_id__in=order_list)
                    else:
                        qs = qs.filter(reference_order_id=order_id)
            if state and not no_user:
                qs = qs.filter(support_state=state)
            if start_date and not no_user:
                qs = qs.filter(timestamp__gte=start_date)
            if end_date and not no_user:
                qs = qs.filter(timestamp__lte=(end_date+timedelta(days=1)))
            if not no_user:
                qs = qs.select_related('user').order_by('-id')
    else:
        filter_form = OrderFilterForm()
    states = State.objects.all().order_by('name')
    filter_form.fields['state'].widget = forms.widgets.Select(choices = [
        ('','---------')] + [(state.name.lower(),state.name) for state in states])
    return render_to_response('support/order/order_list.html', {'orders':qs, 'items_per_page':20,
        'filter_form':filter_form}, context_instance = RequestContext(request))

@login_required
@check_role([])
def order_detail(request, order_id=None):
    try:
        try:
            order = Order.objects.select_related('user','agent','coupon').get(pk=order_id,
                client=request.client.client)
        except Order.DoesNotExist:
            order = Order.objects.select_related('user','agent','coupon').get(reference_order_id=order_id,
                client=request.client.client)
            order_id = order.id
        exclude = None
        order_items = order.get_order_items(request, select_related=('sap_order_item','seller_rate_chart',
            'seller_rate_chart__product','bundle_item')).order_by('id')
        
        payments = order.get_payments(request).order_by('-id')
        shipments = order.get_shipments(request, select_related=('lsp',), 
                exclude=dict(status='deleted')).order_by('id')
        shipment_items = ShipmentItem.objects.select_related('order_item').filter(shipment__order=order).exclude(
            shipment__status='deleted').order_by('shipment')
        customer_name, customer_phone, customer_email = '', '', ''
        customer_name = order.user.full_name
        phones = Phone.objects.filter(user=order.user).order_by('-id')[:1]
        if phones:
            customer_phone = phones[0].phone
        emails = Email.objects.filter(user=order.user).order_by('-id')[:1]
        if emails:
            customer_email = emails[0].email
        refunds = order.get_refunds(request, select_related=('opened_by','closed_by')).order_by('-id')
        refund_items = RefundItem.objects.select_related('order_item').filter(refund__order=order).order_by('refund')
        shipping_info = order.get_address(request, type='delivery')
        try:
            billing_info = order.get_address(request, type='billing')
        except BillingInfo.DoesNotExist:
            billing_info = None
    except Exception, e:
        fb_log.info('Support: order_detail %s - %s' % (order_id, repr(e)))
        return http_error_page(request, error_code=404)
    
    modify_allowed = True
    cancel_allowed = True
    modify_allowed_on = []
    locked_items = order.get_locked_items(request)
    for item in order_items:
        if (item.state not in ['cancelled','bundle_item']) and (item.id not in locked_items):
            modify_allowed_on.append(item.id)

    if (not modify_allowed_on) or order.support_state == 'cancelled':
        modify_allowed = False
    if locked_items or order.support_state == 'cancelled':
        cancel_allowed = False
    #modify_allowed, cancel_allowed = True, True
    #if order.is_delivery_created(request) or order.support_state == 'cancelled':
    #    modify_allowed = False
    #    cancel_allowed = False
         
    lock_order = False
    if order.state in ['failed','processing xml']:
        #no changes allowed on the order
        lock_order = True
    
    shipment_items_dict = {}
    for s_item in shipment_items:
        l = shipment_items_dict.get(s_item.shipment_id,[])
        l.append(s_item)
        shipment_items_dict[s_item.shipment_id] = l

    refund_items_dict = {}
    for r_item in refund_items:
        l = refund_items_dict.get(r_item.refund_id,[])
        l.append(r_item)
        refund_items_dict[r_item.refund_id] = l
    valid_states = None
    payment_flows, order_item_flows, shipment_flows = {}, {}, {}
    if not lock_order:
        if order.support_state == 'cancelled':
            valid_states = ['rejected','refunded']
            if order.payment_mode != 'cod':
                valid_states.append('paid')
        payment_flows = get_actionflows(entity=request.session['content_types']['PaymentAttempt'],
            valid_states=valid_states)
        #order_item_flows = get_actionflows(entity=request.session['content_types']['OrderItem'])

    # Append complaints
    complaint_logs = []
    updates = Update.objects.select_related('complaint').filter(complaint__order=order).order_by('-complaint__id','-id')
    prev_complaint,l = None, []
    for update in updates:
        if update.complaint != prev_complaint:
            if l:
                complaint_logs.append((prev_complaint,l))
            prev_complaint = update.complaint
            l = []
        l.append(update)
    if prev_complaint:
        complaint_logs.append((prev_complaint,l))

    cancellation_choices = utils.SAP_CANCELLATION_CODES.keys()
    order_log = order.get_order_log(request)

    template = "support/order/detail.html"
    if request.GET.get('snippet'):
        template = "support/order/snippet.html"

    return render_to_response(template, {"order": order, "order_items":order_items,
        "shipping_info":shipping_info, "billing_info":billing_info, "payments":payments,
        "shipments":shipments, "modify_allowed":modify_allowed, "payment_flows":payment_flows,
        "order_item_flows":order_item_flows, "shipment_items_dict":shipment_items_dict,
        "shipment_flows":shipment_flows, "c_name":customer_name, "c_phone":customer_phone,
        "c_email":customer_email, "refunds":refunds, "refund_items_dict":refund_items_dict,
        "cancellation_choices":cancellation_choices, "lock_order":lock_order, "cancel_allowed":cancel_allowed,
        "complaint_logs":complaint_logs, "order_log":order_log},
        context_instance = RequestContext(request))


@login_required
@check_role([])
def order_modify(request, order_id=None):
    try:
        try:
            order = Order.objects.exclude(support_state='cancelled').get(pk=order_id,
                client=request.client.client)
        except Order.DoesNotExist:
            order = Order.objects.exclude(support_state='cancelled').get(reference_order_id=order_id,
                client=request.client.client)
            order_id = order.id
        order_items = order.get_order_items(request, select_related=('sap_order_item','seller_rate_chart',
            'seller_rate_chart__product'), exclude=dict(state__in=['cancelled','bundle_item']))
        customer_name = order.user.full_name
    except Exception, e:
        fb_log.info('Support: order_modify - %s' % repr(e))
        return http_error_page(request, error_code=404)
    
    if order.state in ['failed','processing xml']:
        return HttpResponse('Awaiting response from SAP. Please try after some time')
    
    modify_allowed_on = []
    locked_items = order.get_locked_items(request)
    for item in order_items:
        if item.id not in locked_items:
            modify_allowed_on.append(item.id)
    if not modify_allowed_on:
        return HttpResponse('Please delete delivery in SAP to modify this order')
    
    #if order.is_delivery_created(request):
    #    return HttpResponse('Please delete all deliveries to modify this order')
    
    cancellation_choices = utils.SAP_CANCELLATION_CODES.keys()
    
    shipping_form = None
    error = False
    shipping_address_change = False
    if request.method == 'POST':
        updated_items = []
        delivery_address = {}
        if request.POST.get('modify'):
            for item in order_items:
                if item.id not in modify_allowed_on:
                    continue
                try:
                    updated_qty = int(request.POST.get('%s_qty'%item.id, item.qty))
                except ValueError:
                    messages.error(request, 'Please enter a number in order item quantity')
                    error = True
                    break
                reason = request.POST.get('%s_reason'%item.id)    #cancellation reason
                if updated_qty > 0 and updated_qty <= item.qty:
                    if not reason and (updated_qty!=item.qty):
                        messages.error(request, 'Please specify item cancellation reason')
                        error = True
                        break
                    updated_items.append((item,updated_qty,'MODIFIED',reason))
                elif updated_qty > item.qty:
                    messages.error(request, 'Order Item quantity can not be increased')
                    error = True
                    break
                elif updated_qty <= 0:
                    if not reason:
                        messages.error(request, 'Please specify item cancellation reason')
                        error = True
                        break
                    updated_items.append((item,-1,'CANCELLED',reason))
            if request.POST.get('shipping_form'):
                if request.POST.get('shipping_address_change') == '1':
                    shipping_address_change = True
                shipping_form = ShippingInfoForm(request.POST)
                if shipping_form.is_valid():
                    for fieldname in shipping_form.fields:
                        delivery_address[fieldname] = shipping_form.cleaned_data[fieldname]
                else:
                    messages.error(request, 'Please enter valid shipping details')
                    error = True
            if not error:
                #data validation successful. open modification confirmation dialog
                if shipping_form:
                    shipping_form.fields['delivery_country'].widget.attrs['readonly'] = True
                return render_to_response("support/order/modify.html", {"order":order, "order_items":order_items,
                    "updated_items":updated_items, "shipping_form":shipping_form, "delivery_address":delivery_address,
                    "confirmation_alert":True, "c_name":customer_name, "cancellation_choices":cancellation_choices,
                    "shipping_address_change":shipping_address_change, "modify_allowed_on":modify_allowed_on},
                    context_instance = RequestContext(request))
        elif request.POST.get('confirm'):
            profile = utils.get_user_profile(request.user)
            for item in order_items:
                if item.id not in modify_allowed_on:
                    continue
                try:
                    updated_qty = int(request.POST.get('%s_qty'%item.id, item.qty))
                    #if updated_qty != item.qty:
                    #    reason = request.POST.get('%s_reason'%item.id)    #cancellation reason
                    #    updated_items.append((item.id,updated_qty,reason))
                    reason = request.POST.get('%s_reason'%item.id)    #cancellation reason
                    updated_items.append((item.id,updated_qty,reason))
                except ValueError:
                    error = True
                    messages.error(request, 'Please enter a number in order item quantity')
                    break
            shipping_form = ShippingInfoForm(request.POST)
            if request.POST.get('shipping_address_change') == '1':
                shipping_address_change = True
                if shipping_form.is_valid():
                    for fieldname in shipping_form.fields:
                        delivery_address[fieldname] = shipping_form.cleaned_data[fieldname]
                else:
                    messages.error(request, 'Please enter valid shipping details')
                    error = True
            if not error:
                try:
                    with transaction.commit_on_success():
                        #start transaction
                        o_log = None
                        if shipping_address_change:
                            o_log = order.update_shipping_address(request, delivery_address=delivery_address,
                                profile=profile, create_log=True)
                        #if updated_items:
                        #    order.modify(request, updated_items=updated_items, profile=profile, order_log=o_log)
                        order.modify(request, updated_items=updated_items, profile=profile, order_log=o_log)
                        #end transaction
                except Order.OrderInProcessing:
                    fb_log.exception('Support: order_modify %s - Order in processing' % order.id)
                    messages.error(request, 'Order is in process in SAP. Please try again after some time')    
                except Order.InvalidOperation:
                    fb_log.exception('Support: order_modify %s - Delivery exists for this order' % order.id)
                    messages.error(request, 'Invalid Operation')    
                except Order.DeliveryExists:
                    fb_log.exception('Support: order_modify %s - Delivery exists for this order' % order.id)
                    messages.error(request, 'Delivery already created for this order. Delete delivery from SAP to modify this order')
                except OrderItem.QuantityIncrease:
                    fb_log.exception('Support: order_modify %s - Increase in item quantity' % order.id)
                    messages.error(request, 'Order Item quantity can not be increased')
                except Order.InvalidRefundAmount:
                    fb_log.exception('Support: order_modify %s - Invalid refund amount' % order.id)
                    messages.error(request, 'Refund initiation failed')
                except Order.RefundWithoutPayment:
                    fb_log.exception('Support: order_modify %s - Refund attempted without payment' % order.id)
                    messages.error(request, 'Refund initiation failed. No payment done')
                except DeliveryInfo.DoesNotExist:
                    fb_log.exception('Support: order_modify %s - DeliveryInfo not found' % order.id)
                    messages.error(request, 'Shipping Info does not exist')
                except Order.InventoryError, e:
                    fb_log.exception('Support: order_cancel %s - Inventory error %s' % (order.id, e.errors))
                    for er in e.errors:
                        messages.error(request, er)
                except OrderItem.NoCancellationReason:
                    fb_log.exception('Support: order_modify %s - Item cancellation reason not given' % order.id)
                    messages.error(request, 'Please give order item cancellation reason')
                except Order.AmountIncreaseAfterModification:
                    fb_log.exception('Support: order_modify %s - Amount increase after modification' % order.id)
                    messages.error(request, 'Order payable amount has increased')
                except SellerRateChart.MinimumQuantity, e:
                    fb_log.exception('Support: order_modify %s - Minimum quantity for %s is %s' % (order.id, e.item, e.min_qty))
                    messages.error(request, 'Minimum orderable quantity for %s is %s' % (e.item, e.min_qty))
                except Exception, e:
                    fb_log.exception('Support: order_modify %s - %s' % (order.id, repr(e)))
                    messages.error(request, 'Order Modification Failed')
                else:
                    messages.info(request, 'Order Modification Successful')
                    return HttpResponseRedirect('/order/%s'%order.id)
    else:
        try:
            shipping_info = order.get_address(request, type='delivery')
        except DeliveryInfo.DoesNotExist:
            fb_log.exception('Support: order_modify %s - DeliveryInfo not found' % order.id)
            return http_error_page(request, error_code=404)
        except Exception, e:
            fb_log.exception('Support: order_modify %s - %s' % (order.id, repr(e)))
            return http_error_page(request, error_code=404)
        shipping_form = ShippingInfoForm(info=shipping_info)
    if shipping_form:
        shipping_form.fields['delivery_country'].widget.attrs['readonly'] = True
    
    return render_to_response("support/order/modify.html", {"order": order, "order_items":order_items,
        "shipping_form":shipping_form, "c_name":customer_name, "cancellation_choices":cancellation_choices,
        "modify_allowed_on":modify_allowed_on},
        context_instance = RequestContext(request))


@login_required
@check_role([])
def order_cancel(request, order_id=None):
    try:
        try:
            order = Order.objects.exclude(support_state='cancelled').get(pk=order_id,
                client=request.client.client)
        except Order.DoesNotExist:
            order = Order.objects.exclude(support_state='cancelled').get(reference_order_id=order_id,
                client=request.client.client)
            order_id = order.id
    except Order.DoesNotExist:
        return http_error_page(request, error_code=404)
    if order.is_delivery_created(request):
        return HttpResponse('Please delete deliveries to cancel this order')
    if order.state in ['failed','processing xml']:
        return HttpResponse('Awaiting response from SAP. Please try after some time')
    if not request.method == 'POST':
        return
    reason = request.POST.get('reason')
    profile = utils.get_user_profile(request.user)
    try:
        with transaction.commit_on_success():
            #start transaction
            order.cancel(request, profile=profile, reason=reason)
            #end transaction
    except Order.OrderInProcessing:
        fb_log.exception('Support: order_cancel %s - Order in processing' % order.id)
        messages.error(request, 'Order is in process in SAP. Please try again after some time')    
    except Order.InvalidOperation:
        fb_log.exception('Support: order_cancel %s - Invalid operation' % order.id)
        messages.error(request, 'Invalid Operation')
    except Order.DeliveryExists:
        fb_log.exception('Support: order_cancel %s - Delivery exists for this order' % order.id)
        messages.error(request, 'Delivery already created for this order. Delete delivery from SAP to cancel this order')
    except Order.XMLCreationFailure:
        fb_log.exception('Support: order_cancel %s - XML creation failure' % order.id)
        messages.error(request, 'Order Cancellation Failed')
    except Order.InvalidRefundAmount:
        fb_log.exception('Support: order_cancel %s - Invalid refund amount' % order.id)
        messages.error(request, 'Invalid Refund Amount')
    except Order.RefundWithoutPayment:
        fb_log.exception('Support: order_cancel %s - Refund initiated without payment' % order.id)
        messages.error(request, 'Refund Initiated Without Payment')
    except Order.InventoryError, e:
        fb_log.exception('Support: order_cancel %s - Inventory error %s' % (order.id, e.errors))
        for er in e.errors:
            messages.error(request, er)
    except Exception, e:
        fb_log.exception('Support: order_cancel %s - %s' % (order.id, repr(e)))
        messages.error(request, 'Order Cancellation Failed')
    else:
        messages.info(request, 'Order Cancelled Successfully')
    return HttpResponseRedirect('/order/%s'%order.id)


@login_required
@check_role([])
def order_change_payment(request, order_id=None):
    try:
        order = Order.objects.get(pk=order_id)
        if order.support_state != 'booked':
            return HttpResponse('Can not change the payment mode since order is %s' % order.support_state)
    except Exception, e:
        fb_log.info('Support: order_change_payment (%s) - %s' % (order_id, repr(e)))
        return http_error_page(request, error_code=404)
    
    error = False
    if request.method == 'POST':
        form = PaymentChangeForm(request.POST)
        data = {}
        data['profile'] = utils.get_user_profile(request.user)
        if form.is_valid():
            for fieldname in form.fields:
                data[fieldname] = form.cleaned_data[fieldname]
            try:
                with transaction.commit_on_success():
                    #start transaction
                    order.change_payment_mode(request, **data)
                    #end transaction
            except order.InvalidOperation, e:
                fb_log.info('Support: order_change_payment (%s) - %s' % (order_id, repr(e)))
                resp = HttpResponse('Invalid Operation')
                resp.status_code = 400
                return resp
            except order.PaymentModeNotPresent, e:
                fb_log.info('Support: order_change_payment (%s) - %s' % (order_id, repr(e)))
                resp = HttpResponse('Please select a payment mode')
                resp.status_code = 400
                return resp
            except order.PaymentAmountNotPresent, e:
                fb_log.info('Support: order_change_payment (%s) - %s' % (order_id, repr(e)))
                resp = HttpResponse('Please enter payment amount')
                resp.status_code = 400
                return resp
            except Exception, e:
                fb_log.info('Support: order_change_payment (%s) - %s' % (order_id, repr(e)))
                resp = HttpResponse('Failed to change payment mode')
                resp.status_code = 400
                return resp
            else:
                return HttpResponse('Payment Mode Changed Successfully')
        else:
            error = True
    else:
        form = PaymentChangeForm()
        form.fields['amount'].initial = order.payable_amount
    resp = render_to_response("support/order/change_payment_form.html", {"order":order, "form":form},
        context_instance = RequestContext(request))
    if error:
        resp.status_code = 400
    return resp


@login_required
@check_role([])
def order_upload(request):
    qs, errors = [], []
    if request.FILES:
        try:
            file_form = BulkUploadForm(request.POST, request.FILES)
            if file_form.is_valid():
                try:
                    uploaded_file = request.FILES['uploaded_file']
                    qs, errors = process_bulk_file(request, uploaded_file=uploaded_file, 
                        bulk_type='order')
                except Exception, e:
                    fb_log.info("Exception %s " % repr(e))
                    errors.append(e.message)
            else:
                fb_log.info("Wrong  File %s " % file_form.errors)
        except Exception, e:
            fb_log.info("Error Reading File %s " % repr(e))
            errors.append(e.message)
    else:
        file_form = BulkUploadForm()
    return render_to_response('support/order/order_upload.html', {'orders':qs, 'items_per_page':20,
        'file_form':file_form, 'errors':errors}, context_instance = RequestContext(request))


@login_required
@check_role([])
def process_bulk_file(request, uploaded_file, bulk_type):
    import xlrd
    VALID_COLUMN_NAMES = None
    
    if bulk_type == 'payment':
        VALID_COLUMN_NAMES = ['date', 'payment_mode', 'order_id', 'bank', 
                'txn_id', 'txn_date', 'amount', 'state', 'notes']
    
    elif bulk_type == 'order':
        VALID_COLUMN_NAMES = ['S.No', 'Date', 'ReceiptNo', 'First Name', 'Last Name', 'Email ID', 'Address',
                'City', 'State', 'Pin Code', 'Product ID', 'Item Purchased', 'Qty', 
                'Order Value (Rs.)', 'Amount Paid (Rs.)', 'Mode Of Payment', 'Payment detail', 
                'Order Location', 'Mobile No', 'Telephone No (STD cde)', 'Created By Order', 'CreditCard Number', 
                'Card Verification number', 'Expiration DayofMonth', 'Expiration Month', 'Expiration Year', 
                'CreditCard Type', 'Bank Account Number', 'Bank Name', 'Cheque Date', 'Cheque number', 'Cheque Status', 
                'NetBanking CreditCard Number', 'NetBanking Card Verification number', 'NetBanking Expiration Month',
                'NetBanking Expiration Year', 'NetBanking Expiration DayofMonth', 'NetBanking CreditCard Type', 'BPNumber', 
                'Price List', 'Group Id', 'Catalog', 'Third Party Order Number', 'Notes']

    elif bulk_type == 'shipment':
        VALID_COLUMN_NAMES = ['order_id', 'product_id', 'scm_comment', 'category_comment', 
                'scm_issue', 'csr_action', 'category_issue', 'category_action']
    
    elif bulk_type == 'lsp_update':
        VALID_COLUMN_NAMES = ['Delivery No', 'Awb No', 'Status', 'Date', 'LSP']
    
    book = xlrd.open_workbook(file_contents = uploaded_file.read())
    sheet = book.sheet_by_index(0)
    headers = sheet.row(0)
    workbook_map = {}
    all_errors = []
    qs = []
    previous_receipt_no = None
    
    if sheet.ncols == len(VALID_COLUMN_NAMES):
        for column_num in range(sheet.ncols):
            column_name = headers[column_num].value.strip()
            if not (column_name in VALID_COLUMN_NAMES):
                raise Exception('Please give proper column Name, valid names are %s ' % VALID_COLUMN_NAMES)
            else:
                workbook_map[column_name] = column_num
            
        for row_num in range(1, sheet.nrows): #Oth row contains column Header Name
            data = {}
            row = sheet.row(row_num)
            order_items = []
            order_row = row_num + 1
            
            for column_name in VALID_COLUMN_NAMES:
               data[column_name] = row[workbook_map[column_name]].value
            if bulk_type == 'order':
                if (row[workbook_map['ReceiptNo']].value != ''):
                    item_row_num = 0
                    item_row = sheet.row(row_num)
                    while ((item_row_num == 0) or (not item_row[workbook_map['ReceiptNo']].value)):
                        item_data = {}
                        item_data['Product ID'] = item_row[workbook_map['Product ID']].value
                        item_data['Qty'] = item_row[workbook_map['Qty']].value
                        item_data['Item Purchased'] = item_row[workbook_map['Item Purchased']].value
                        item_data['item_row'] = row_num
                        order_items.append(item_data)
                        row_num = row_num + 1 
                        item_row_num = 1
                        if row_num < sheet.nrows:
                            item_row = sheet.row(row_num)
                        else:
                            break
                    
                    row_num = row_num - 1
                    try:
                        with transaction.commit_on_success():
                            order = process_bulk_order(request, order_items=order_items, bulk_data=data, order_row=order_row)
                            qs.append(order)
                    except Exception, e:
                        all_errors.append(e.message)
            
            elif bulk_type == 'payment':
                try:
                    with transaction.commit_on_success():
                        payment_attempt = process_bulk_payment(request, bulk_data=data, 
                                row_num=row_num)
                        qs.append(payment_attempt) 
                except Exception, e:
                    all_errors.append(e.message)

            elif bulk_type == 'lsp_update':
                try:
                    with transaction.commit_on_success():
                        lsp_update = process_lsp_updates(request, bulk_data=data, 
                                row_num=row_num)
                        qs.append(lsp_update) 
                except Exception, e:
                    all_errors.append(e.message)
            
            elif bulk_type == 'shipment':
                pass
        
        return qs, all_errors
    raise Exception(" Columns are not Proper")


def process_bulk_order(request, bulk_data, order_items, order_row):
    fb_log.info("####################Data ############# %s " % bulk_data)
    fb_log.info("Item_Data %s " % order_items)
    errors_header = 'Error(s) in Address at row %s' % order_row
    errors = []
    client = None
    order = None
    # create user
    
    receipt_no = bulk_data.get('ReceiptNo')
    if not receipt_no:
        errors.append('Please enter a receipt No at row_num %s' % order_row)
    
    bp_number = bulk_data.get('BPNumber')
    if not bp_number:
        errors.append('No BP Number Found. Please enter a BP Number at row %s' % order_row)
    bp_number = str(int(bp_number))    
    try:
        email_id = bulk_data.get('Email ID').strip()
        if not utils.is_valid_email(email_id):
            errors.append('Invalid Email ID Specified')
    except AttributeError, e:
        errors.append('Please enter a valid email at row_num %s' % order_row)
    
    user, profile = utils.get_or_create_user(email_id, first_name = bulk_data.get('First Name'), 
            last_name = bulk_data.get('Last Name'))
    
    # save order with order items   
    payment_mode_code = bulk_data.get('Mode Of Payment').lower()
    
    client = request.client.client
    date = bulk_data.get('Date')
    
    try:
        third_party_details = ThirdPartyOrders.objects.get(bp_number=bp_number, receipt_no=receipt_no)
        errors.append('Order No %s Already Exists for recipt no %s'% (third_party_details.order.reference_order_id, 
                receipt_no))
        e = InvalidData
        e.message = errors
        raise e
    
    except ThirdPartyOrders.DoesNotExist:
        third_party_details = ThirdPartyOrders(bp_number=bp_number, receipt_no=receipt_no)

    order = Order(client=client, user=profile)
    try:
        order_datetime = datetime.strptime(date, '%Y-%m-%d') #Gives ValueError
    except ValueError, e:
        errors.append('Please enter a valid date format(yyyy-mm-dd) at row %s' % order_row)
    
    VALID_PAYMENT_MODES = ('credit card', 'cheque', 'cash on delivery', 'netbanking', 'cash', 'debit card', 
            'credit card emi', 'payback', 'itz')
   
    pa = None
    is_paid = False
    gateway = None
    if payment_mode_code.lower() not in VALID_PAYMENT_MODES:
        errors.append("Invalid Payment Mode %s. Valid Payment Modes are %s" % (payment_mode_code, 
            VALID_PAYMENT_MODES))
    else:
        if payment_mode_code.lower()  in ('cheque', 'itz', 'payback', 
                'netbanking'):
            payment_mode_code = payment_mode_code.lower()
        elif payment_mode_code.lower()== 'cash on delivery':
            payment_mode_code = 'cod'
        elif payment_mode_code.lower() == 'credit card':
            payment_mode_code = 'credit-card'
        elif payment_mode_code.lower() == 'debit card':
            payment_mode_code = 'dedit-card'
        elif payment_mode_code.lower() == 'credit card emi':
            payment_mode_code = 'credit-card-emi-web'
        elif payment_mode_code.lower() == 'Cash':
            payment_mode_code = 'cash-collection'
        
        if payment_mode_code in ('credit-card-emi-web', 'credit-card', 'debit-card'):
            gateway = 'AXIC' #By Defaul axis
            is_paid = True
        elif payment_mode_code == 'netbanking':
            gateway = 'CCAV'
            is_paid = True
        elif payment_mode_code == 'payback':
            gateway = 'PAYB'
            is_paid = True
        elif payment_mode_code == 'cash-collection':
            #It also checks if hand cash is there
            #No Need to change any thing
            gateway = 'ICCA' #By Default ICICICash
            is_paid = True
        else:
            gateway = payment_mode_code
    
    
    order.timestamp = order_datetime
    order.support_state  = 'booked'
    order.notes = bulk_data.get('Notes', None)
    order.payment_mode = payment_mode_code
    order.medium = 'support'
    order.client_domain = request.client
    order.save()
    price_list = {'price_list':bulk_data.get('Price List')}
    for item in order_items:
        item_row = item.get('item_row')
        try:
            seller = Account.objects.get(name = bulk_data.get('Catalog'))
            rate_chart = SellerRateChart.objects.get(sku=int(item.get('Product ID')), seller=seller)
            response = order.add_item(request, rate_chart=rate_chart, qty=item.get('Qty'), price_list=price_list, is_bulk=True) 
            if response:
                errors.append(response)
        except Account.DoesNotExist:
            errors.append('No item exists for seller %s at row %s' % (bulk_data.get('Order Location'), order_row+item_row-1))
        except SellerRateChart.DoesNotExist:
            errors.append('No item exists for sku %s at row %s' % (bulk_data.get('Product ID'), order_row+item_row-1))
        except Exception, e:
            fb_log.info('Bulk Order Add Item Exception %s' % repr(e))
            errors.append('Unable to add item for sku %s at row %s' % (item.get('Product ID'), order_row+item_row-1))

    cart_items = order.get_order_items(request, 
            exclude=dict(state__in=['cancelled','bundle_item']))
    
    amount_paid = bulk_data.get('Amount Paid (Rs.)')
    if int(order.payable_amount) != int(amount_paid):
        errors.append(" Amount Mismatch: Amount Paid is %s, order total is %s" \
                    % (amount_paid, order.payable_amount))

    # Create delivery info and billing info and validate else return errors
    pincode = str(int(bulk_data.get('Pin Code'))) 
        
    address = {'email':email_id}
    address['phone'] = str(int(bulk_data.get('Mobile No')))
    address['address'] = bulk_data.get('Address')
    address['pincode'] = pincode
    address['country'] = bulk_data.get('Country', 'India')
    address['state'] = bulk_data.get('State')
    address['city'] = bulk_data.get('City')
    address['first_name'] = bulk_data.get('First Name')
    address['last_name'] = bulk_data.get('Last Name')
    address['name'] = '%s %s' % (address['first_name'], address['last_name'])
   
    address_error = False
    for address_type in ['delivery', 'billing']:
        if not address_error:
            address_info = '%s_address' % address_type
            address_details =  dict((('%s_%s') % (address_type, key), 
                address[key]) for key, value in address.items())
            
            if address_type == 'delivery':
                delivery_form = ShippingInfoForm(address_details)
                if not delivery_form.is_valid():
                    address_error = True
                    for error in delivery_form.errors:
                        errors.append(delivery_form.errors[error])
                else:
                    order.save_address(request, type=address_type, delivery_address=address_details)

            if address_type == 'billing':
                billing_form = BillingInfoForm(address_details)
                if not billing_form.is_valid():
                    address_error = True
                    for error in billing_form.errors:
                        errors.append(billing_form.errors[error])
                else:
                    order.save_address(request, type=address_type, billing_address=address_details)
    
   # create payment attempt

    pa = order.create_payment_attempt(request, payment_mode_code=payment_mode_code, domain=request.client)
    pa.notes = bulk_data.get('Payment detail')
    pa.gateway = gateway
    pa.amount = order.payable_amount
    if payment_mode_code == 'cheque':
        cheque_status = bulk_data.get('Cheque Status')
        VALID_CHEQUE_STATUS = ['ChequeRealized', 'AwaitingCheque']
        if cheque_status not in VALID_CHEQUE_STATUS:
            errors.append('%s not a valid cheque status. Valid states are %s' \
                    % (cheque_status, VALID_CHEQUE_STATUS))
        if cheque_status == 'ChequeRealized':
            cheque_date = bulk_data.get('Cheque Date')
            try:
                pa.instrument_no = int(bulk_data.get('Cheque number'))
                payment_datetime = datetime.strptime(cheque_date, '%Y-%m-%d') #Gives ValueError
                pa.payment_realized_on = payment_datetime
            except ValueError, e:
                errors.append('Please enter a valid date format(yyyy-mm-dd) at row %s' % order_row)
            is_paid = True
    pa.save() 
    if errors:
        errors.insert(0, errors_header)
        e = InvalidData
        e.message = errors
        raise e
    else:
        try:
            agent = utils.get_user_profile(request.user)
        except:
            agent = None
        third_party_details.order = order
        third_party_details.third_party_order = bulk_data.get('Third Party Order Number')
        third_party_details.save()
        
        pa.move_payment_state(request, agent=agent, is_paid=is_paid)
        return order

@login_required
@check_role([])
def order_item_form(request, item_id=None):
    try:
        sap_order_item = SAPOrderItem.objects.select_related('order','order_item').get(pk=item_id)
        order_item = sap_order_item.order_item
        order = sap_order_item.order
        action_id = int(request.GET.get('action_id',None))
        actionflow = ActionFlow.objects.select_related('initial_substate',
            'final_substate').get(pk=action_id)
        old_state = actionflow.initial_substate.name.lower()
        new_state = actionflow.final_substate.name.lower()
        agent = utils.get_user_profile(request.user)
        form, data = None, {}
    except Exception, e:
        fb_log.exception('Support: order_item_form - %s' % repr(e))
        return http_error_page(request, error_code=404)
  
    if old_state != sap_order_item.status:
        return HttpResponse('Invalid Operation')
     
    from orders.views import get_order_item_form
    error = False
    if request.method == 'POST':
        form = get_order_item_form(request, data=request.POST, new_state=new_state)
        if form.is_valid():
            for fieldname in form.fields:
                data[fieldname] = form.cleaned_data[fieldname]
        else:
            error = True
    else:
        form = get_order_item_form(request, new_state=new_state)
    
    if form and (not data):
        resp = render_to_response('support/order_item/form.html', {'form':form, 'entity':'orderitem',
            'pk':sap_order_item.id, 'action_id':action_id}, context_instance = RequestContext(request))
        resp.status_code = 202
        if error:
            resp.status_code = 400
        return resp
    
    shipment_item, shipment, shipment_log = None, None, None
    if new_state == 'delivery created':
        delivery_no = data['delivery_no']
        shipment = get_or_create_shipment(order=order, delivery_number=delivery_no, save=False)
        if not shipment.id:
            shipment_log = ShipmentLog(action='status', status='delivery created',
                delivery_number=delivery_no)
        try:
            shipment_item = shipment.shipment_items.get(sap_order_item=sap_order_item)
        except ShipmentItem.DoesNotExist:
            #shipment item to be added. increment shipment amount
            shipment.amount += order_item.total_amount
        except Exception, e:
            fb_log.info('Support: get_order_item_form - order_item: %s - %s' %
                (order_item, repr(e)))
    try:
        with transaction.commit_on_success():
            #start transaction
            if new_state == 'delivery created':
                shipment.save() #save shipment before creating new shipment item
                if not shipment_item:
                    #create a shipment item if not found
                    shipment_item = ShipmentItem.objects.create(shipment=shipment, order_item=order_item,
                        sap_order_item=sap_order_item, quantity=order_item.qty)
            o_log = sap_order_item.move_state(request, new_state=new_state, agent=agent, data=data)
            if shipment_log:
                shipment_log.shipment = shipment
                shipment_log.order_log = o_log
                shipment_log.save()
            #end transaction
    except Order.OrderInProcessing:
        resp = HttpResponse('Order is in process in SAP. Please try again after some time')
        resp.status_code = 400
        return resp
    except OrderItem.InvalidOperation:
        resp = HttpResponse('Invalid Operation')
        resp.status_code = 400
        return resp
    except OrderItem.InsufficientData:
        resp = HttpResponse('Insufficient Data')
        resp.status_code = 400
        return resp
    except Exception, e:
        fb_log.exception('Support: order_item_form - %s' % repr(e))
        resp = HttpResponse('Error in processing state change')
        resp.status_code = 400
        return resp
    else: 
        return HttpResponse('Order Item Update Successful')
    return http_error_page(request, error_code=400)


def process_lsp_updates(request, bulk_data, row_num):
    fb_log.info("LSP Bulk Data %s " % bulk_data)
    process_data = {}
    errors = []
    errors_header = 'Error(s) found at row %s' % row_num
    shipment = None
    try:
        delivery_no = bulk_data['Delivery No']
        awb_no = bulk_data['Awb No']
        status = bulk_data['Status']
        lsp = bulk_data['LSP']
        date = bulk_data['Date']

        shipment = Shipment.objects.get(delivery_number = delivery_no)
        courier = Lsp.objects.get(name__iexact=lsp)
        shipment.lsp = courier
        shipment.tracking_number = awb_no

        
        shipment_status = LSP_CODES.get(status, '')
        
        if shipment_status:
            if shipment_status == 'delivered':
                shipment.delivered_on = date
            elif shipment_status == 'returned':
                shipment.returned_on = date
            
            shipment.status = shipment_status
        else:
            errors.append('Status is not Proper =  %s' % status)

    except Shipment.DoesNotExist, e:
        errors.append('Invalid Delivery No : %s' % delivery_no)
   
    except Lsp.DoesNotExist, e:
        errors.append('Invalid lsp name : %s' % lsp)
    
    except ValidationError, e:
        errors.append('Invalid Date : %s shoud be in YYY-MM-dd' % date)
    
    except Exception,  e:
        errors.append('Unable to change shipment status for delivery no : `%s' % delivery_number)
    
    if errors:
        errors.insert(0, errors_header)
        e = InvalidData
        e.message = errors
        raise e
    else:
        shipment.save()
        return shipment


@login_required
@check_role([])
def process_bulk_payment(request, bulk_data, row_num):
    fb_log.info("Data %s " % bulk_data)
    process_data = {}
    payment_attempt = None
    errors = []
    errors_header = 'Error(s) found at row %s' % row_num
    agent = None
    reference_order_id = ''
   
    try:
        reference_order_id = str(long(bulk_data.get('order_id')))
        order = Order.objects.select_related('user').get(reference_order_id=reference_order_id)
    except Exception, e:
        errors.append(errors_header)
        errors.append('Order %s not found' % reference_order_id)
        e = InvalidData
        e.message = errors
        raise e
        
    bulk_form = BulkPaymentForm(bulk_data)
    if bulk_form.is_valid():
        if order.support_state in ['paid', 'confirmed']:
           errors.append('Payment Already Done for order %s at row %s' % (reference_order_id,
               row_num))
        payment_mode = bulk_form.cleaned_data['payment_mode'].lower()
        process_data['payment_mode']  = payment_mode
        process_data['gateway'] = bulk_form.cleaned_data['bank']
        process_data['amount'] = Decimal(bulk_form.cleaned_data['amount'])
        payments = order.get_payments(request, filter = process_data)
        
        if payments:
            payment_attempt = payments[0]
            new_state = bulk_form.cleaned_data['state']
            agent = utils.get_user_profile(request.user)
            
            if payment_mode == 'cheque':
                process_data['pg_transaction_id'] = bulk_form.cleaned_data['txn_id']
                process_data['instrument_no'] = bulk_data.get('instument_no')
                process_data['instrument_issue_bank'] = bulk_data.get('issue_bank')
                process_data['instrument_date'] = bulk_data.get('txn_date')
                process_data['notes'] = bulk_data.get('notes')

        else :
            errors.append('No Payment Found for order %s' % reference_order_id)

    
    if errors or not payment_attempt:
        errors.insert(0, errors_header)
        e = InvalidData
        for error in bulk_form.errors:
            errors.append(bulk_form.errors)
        e.message = errors
        raise e

    else:
        payment_attempt.move_payment_state(request, new_state=new_state, 
                agent=agent, data=process_data)
        return payment_attempt
    


@login_required
@check_role([])
def payment_list(request):
    qs, action_flows = [], {}
    errors = []
    
    if request.FILES:
        try:
            file_form = BulkUploadForm(request.POST, request.FILES)
            
            if file_form.is_valid():
                uploaded_file = request.FILES['uploaded_file']
                with transaction.commit_on_success():
                    qs = process_bulk_file(request, uploaded_file, bulk_type='payment')
            else:
                fb_log.info("Wrong File %s " % file_form.errors)
                for error in file_form.errors:
                    errors.append(file_form.errors[error])
        
        except InvalidData, e:
            errors = e.message
        except Exception, e:
            fb_log.info("Exception in Processing File %s " % repr(e))
            errors.append('Unable to Process File. Something wicked happened %s' % e)
    
    if request.method == 'GET' and request.GET:
        filter_form = PaymentFilterForm(request.GET)
        if filter_form.is_valid():
            qs = PaymentAttempt.objects.filter(order__client=request.client.client)
            name = filter_form.cleaned_data['name']
            phone = filter_form.cleaned_data['phone']
            email = filter_form.cleaned_data['email']
            order_id = filter_form.cleaned_data['order_id']
            transaction_id = filter_form.cleaned_data['transaction_id']
            method = filter_form.cleaned_data['method']
            substate = filter_form.cleaned_data['state']
            start_date = filter_form.cleaned_data['start_date']
            end_date = filter_form.cleaned_data['end_date']
            no_user = False
            if name:
                name = name.strip()
            if name:
                qs = qs.filter(order__user__in = [p.id for p in Profile.objects.filter(
                    full_name__icontains = name)])
            if phone and not no_user:
                phone = phone.strip()
                try:
                    ph = Phone.objects.get(phone=phone)
                    qs = qs.filter(order__user=ph.user)
                except Phone.DoesNotExist:
                    qs = []
                    no_user = True
            if email and not no_user:
                email = email.strip()
                try:
                    e = Email.objects.get(email=email)
                    qs = qs.filter(order__user=e.user)
                except Email.DoesNotExist:
                    qs = []
                    no_user = True
            if order_id and not no_user:
                order_id = re.sub(r'\s','',order_id)
                if order_id.endswith(','):
                    order_id = order_id[:-1]
                if order_id:
                    order_list = order_id.split(',')
                    if len(order_list) > 1:
                        qs = qs.filter(order__reference_order_id__in=order_list)
                    else:
                        qs = qs.filter(order__reference_order_id=order_id)
            if transaction_id and not no_user:
                transaction_id = re.sub(r'\s','',transaction_id)
                if transaction_id.endswith(','):
                    transaction_id = transaction_id[:-1]
                if transaction_id:
                    transaction_list = transaction_id.split(',')
                    if len(transaction_list) > 1:
                        qs = qs.filter(Q(transaction_id__in=transaction_list) | Q(
                            pg_transaction_id__in=transaction_list))
                    else:
                        qs = qs.filter(Q(transaction_id=transaction_id) | Q(
                            pg_transaction_id=transaction_id))
            if method and not no_user:
                qs = qs.filter(payment_mode=method)
            if substate and not no_user:
                substate = substate.strip()
                qs = qs.filter(status=substate)
            if start_date and not no_user:
                qs = qs.filter(created_on__gte=start_date)
            if end_date and not no_user:
                qs = qs.filter(created_on__lte=(end_date+timedelta(days=1)))
            if not no_user:
                qs = qs.select_related('order').order_by('-id')
        #action_flows = get_actionflows(entity=request.session['content_types']['PaymentAttempt'])
    else:
        filter_form = PaymentFilterForm()
    filter_form.fields['state'].widget = forms.widgets.Select(choices = [('','---------')] + [(substate.name.lower(),substate.name)
        for substate in SubState.objects.filter(entity=request.session['content_types']['PaymentAttempt']).order_by('name')])

    return render_to_response('support/payment/payment_list.html', {'payments': qs, 'items_per_page': 20,
        'filter_form':filter_form, 'action_flows':action_flows, 'errors':errors}, 
        context_instance = RequestContext(request))


@login_required
@check_role([])
def payment_form(request, payment_id=None):
    try:
        payment = PaymentAttempt.objects.select_related('order').get(pk=payment_id)
        action_id = int(request.GET.get('action_id',None))
        actionflow = ActionFlow.objects.select_related('initial_substate',
            'final_substate').get(pk=action_id)
        old_state = actionflow.initial_substate.name.lower()
        new_state = actionflow.final_substate.name.lower()
        agent = utils.get_user_profile(request.user)
        form, data = None, {}
    except Exception, e:
        fb_log.exception('Support: payment_form - %s' % repr(e))
        return http_error_page(request, error_code=404)
    
    if old_state != payment.status:
        return HttpResponse('Invalid Operation')
        
    from payments.views import get_payment_form
    error = False
    if request.method == 'POST':
        form = get_payment_form(request, payment=payment, data=request.POST,
            new_state=new_state)
        if form.is_valid():
            for fieldname in form.fields:
                data[fieldname] = form.cleaned_data[fieldname]
        else:
            error = True
    else:
        form = get_payment_form(request, payment=payment, new_state=new_state)
    
    if form and (not data):
        resp = render_to_response('support/payment/form.html', {'form':form, 'entity':'payment',
            'pk':payment.id, 'action_id':action_id}, context_instance = RequestContext(request))
        resp.status_code = 202  #to not refresh the page
        if error:
            resp.status_code = 400
        return resp
    message = ''
    try:
        with transaction.commit_on_success():
            #start transaction
            try:
                payment.move_payment_state(request, new_state=new_state, agent=agent,
                    data=data)
            except Order.CouponAlreadyAttached:
                message = 'Sorry! This coupon is already been used. Please remove the coupon'
            except Order.InvalidOperation:
                message = 'Order not confirmed'
            except Order.InsufficientPayment, e:
                message = 'Order not confirmed. Pending payment - INR %.2f' % e.delta
            except Order.InventoryError, e:
                message = 'Order not confirmed.<br />'
                for er in e.errors:
                    message += (er+'</br>')
            #end transaction
    except Order.OrderInProcessing:
        resp = HttpResponse('Order is in process in SAP. Please try again after some time')
        resp.status_code = 400
        return resp
    except PaymentAttempt.InvalidOperation:
        resp = HttpResponse('Invalid Operation')
        resp.status_code = 400
        return resp
    except PaymentAttempt.InsufficientData:
        resp = HttpResponse('Insufficient Data')
        resp.status_code = 400
        return resp
    except Exception, e:
        fb_log.exception('Support: payment_form - %s' % repr(e))
        resp = HttpResponse('Error in processing payment')
        resp.status_code = 400
        return resp
    else: 
        return HttpResponse('Payment Update Successful. %s' % message)
    return http_error_page(request, error_code=400)


@login_required
@check_role([])
def shipment_list(request):
    qs, action_flows = [], {}
    errors = []
    
    if request.FILES and 'lsp' in request.POST:
        try:
            file_form = BulkUploadForm(request.POST, request.FILES)
            
            if file_form.is_valid():
                uploaded_file = request.FILES['uploaded_file']
                with transaction.commit_on_success():
                    qs = process_bulk_file(request, uploaded_file, bulk_type='lsp_update')
            else:
                fb_log.info("Wrong  File %s " % file_form.errors)
                errors = file_form.errors

        except InvalidData, e:
            errors = e.message
        
        except Exception, e:
            fb_log.info("Error Reading File %s " % repr(e))
            errors.append(e.message)
    
    if request.GET:
        filter_form = ShipmentFilterForm(request.GET)
        if filter_form.is_valid():
            qs = Shipment.objects.all()
            order_id = filter_form.cleaned_data['order_id']
            delivery_number = filter_form.cleaned_data['delivery_number']
            invoice_number = filter_form.cleaned_data['invoice_number']
            lsp = filter_form.cleaned_data['lsp']
            tracking_number = filter_form.cleaned_data['tracking_number']
            status = filter_form.cleaned_data['status']
            start_date = filter_form.cleaned_data['start_date']
            end_date = filter_form.cleaned_data['end_date']
            if order_id:
                order_id = re.sub(r'\s','',order_id)
                if order_id.endswith(','):
                    order_id = order_id[:-1]
                if order_id:
                    order_list = order_id.split(',')
                    if len(order_list) > 1:
                        qs = qs.filter(order__reference_order_id__in=order_list)
                    else:
                        qs = qs.filter(order__reference_order_id=order_id)
            if delivery_number:
                delivery_number = re.sub(r'\s','',delivery_number)
                if delivery_number.endswith(','):
                    delivery_number = delivery_number[:-1]
                if delivery_number:
                    delivery_list = delivery_number.split(',')
                    if len(delivery_list) > 1:
                        qs = qs.filter(delivery_number__in=delivery_list)
                    else:
                        qs = qs.filter(delivery_number=delivery_number)
            if tracking_number:
                tracking_number = re.sub(r'\s','',tracking_number)
                if tracking_number.endswith(','):
                    tracking_number = tracking_number[:-1]
                if tracking_number:
                    tracking_list = tracking_number.split(',')
                    if len(tracking_list) > 1:
                        qs = qs.filter(tracking_number__in=tracking_list)
                    else:
                        qs = qs.filter(tracking_number=tracking_number)
            if invoice_number:
                invoice_number = re.sub(r'\s','',invoice_number)
                if invoice_number.endswith(','):
                    invoice_number = invoice_number[:-1]
                if invoice_number:
                    invoice_list = invoice_number.split(',')
                    if len(invoice_list) > 1:
                        qs = qs.filter(invoice_number__in=invoice_list)
                    else:
                        qs = qs.filter(invoice_number=invoice_number)
            if lsp:
                qs = qs.filter(lsp=lsp)
            if status:
                qs = qs.filter(status=status)
            if start_date:
                qs = qs.filter(created_on__gte=start_date)
            if end_date:
                qs = qs.filter(created_on__lte=(end_date+timedelta(days=1)))
            qs = qs.select_related('order').order_by('-id')
    else:
        filter_form = ShipmentFilterForm()
    #filter_form.fields['status'].widget = forms.widgets.Select(choices = [('','---------')] + [(substate.name.lower(),substate.name)
    #    for substate in SubState.objects.filter(entity=request.session['content_types']['PaymentAttempt']).order_by('name')])

    return render_to_response('support/shipment/shipment_list.html', {'shipments': qs, 'items_per_page': 20,
        'filter_form':filter_form, 'action_flows':action_flows, 'errors':errors}, context_instance = RequestContext(request))


def get_or_create_shipment(order=None, delivery_number=None, save=True):
    if not delivery_number:
        return None
    params = {'delivery_number':delivery_number}
    if order:
        params['order'] = order
    shipment = None
    try:
        shipment = Shipment.objects.select_related('order').get(~Q(status='deleted'), **params)
    except Shipment.DoesNotExist:
        if order:
            shipment = Shipment(order=order, delivery_number=delivery_number)
            if save:
                shipment.save()
        else:
            fb_log.info('Support: get_or_create_shipment - Order not present, del_no %s' %
                delivery_number)
    except Exception, e:
        fb_log.info('Support: get_or_create_shipment - orderId: %s, del_no: %s - %s' %
            (order.id, delivery_number, repr(e)))
    return shipment


def order_ack(request):
    if request.method != 'POST':
        sap_log.info('Support: Order Ack Error - Invalid request method')
        return http_error_page(request, error_code=404)

    sap_log.info('order_ack')
    sap_log.info('%s' % request.POST)
    form = OrderAckForm(request.POST)
    if form.is_valid():
        header = form.cleaned_data['header']
        if header in ['ORDER_ACK','CAN_ACK','MOD_ACK']:
            type = 'new'
            order_state = ''
            if header == 'MOD_ACK':
                type = 'modify'
                order_state = 'modified'
            elif header == 'CAN_ACK':
                type = 'cancel'
                order_state = 'cancelled'
            try:
                o_xml = OrderXML.objects.select_related('order').get(reference_order_id=form.cleaned_data['orderId'],
                    pk=form.cleaned_data['id'], type=type, status='submitted')
                order = o_xml.order
                status = 'failed' if (form.cleaned_data['orderState']=='Failed') else 'successful'
                error_type = 'sap' if (status=='failed') else ''
            except OrderXML.DoesNotExist:
                sap_log.info('Support: Order Ack - order xml does not exist - id - %s, type - %s' %
                    (form.cleaned_data['id'], type))
                raise
            except Exception, e:
                sap_log.exception('Support: Order Ack Error (%s) - %s' % (form.cleaned_data['id'], repr(e)))
                raise
            else:
                try:
                    with transaction.commit_on_success():
                        #start transaction
                        if status == 'failed':
                            order.state = 'failed'
                            sap_log.info('Support: order_ack failed from SAP (%s) - %s' % (form.cleaned_data['orderId'],
                                form.cleaned_data['orderDesc']))
                        else:
                            order.state = order_state
                        order.save()
                        
                        o_xml.status = status
                        o_xml.reason = form.cleaned_data['orderDesc']
                        o_xml.attempts += 1
                        o_xml.error_type = error_type
                        o_xml.save()
                        #end transaction
                except Exception, e:
                    sap_log.exception('Support: Error processing order_ack (%s), rollback transaction - %s' %
                        (form.cleaned_data['orderId'],repr(e)))
                    raise
                else:
                    return HttpResponse('Processed Successfully')
        else:
            sap_log.info('Support: Incorrect header in order_ack - %s' % request.POST.get('header',None))
    else:
        sap_log.info('Support: Form validation failed in order_ack - %s' % request.POST.get('orderId',None))
        sap_log.info('Form errors - %s' % form.errors)
    
    sap_log.info('Support: Order Ack Error- %s' % request.POST)
    return http_error_page(request, error_code=500)


def item_ack(request):
    if request.method != 'POST':
        sap_log.info('Support: Item Ack Error - Invalid request method')
        return http_error_page(request, error_code=404)
    
    sap_log.info('item_ack')
    sap_log.info('%s' % request.POST)
    form = ItemAckForm(request.POST)
    if form.is_valid():
        if form.cleaned_data['header'] == 'ITEM_ACK':
            ref_order_id = form.cleaned_data['orderId']
            line_item_id = form.cleaned_data['atgDocumentId']
            delivery_no = form.cleaned_data['deliveryNumber']
            invoice_no = form.cleaned_data['invoiceNumber']
            try:
                sap_order_item = SAPOrderItem.objects.select_related('order','order_item').get(
                    order__reference_order_id=ref_order_id, sno=line_item_id)
                order = sap_order_item.order
                order_item = sap_order_item.order_item
                #item_status = 'no stock'
                data = {}
                shipment_log, o_log = None, None
                if delivery_no:
                    if sap_order_item.order_item.state == 'cancelled':
                        sap_log.info('Support: item ack error - delivery for cancelled orderitem - del_no - %s, \
                            order_item - %s' % (delivery_no, order_item.id))
                    shipment = get_or_create_shipment(order=order, delivery_number=delivery_no, save=False)
                    plant = Dc.objects.get(code=form.cleaned_data['plantId'], client=order.client)
                    lsp_name = form.cleaned_data['lspName']
                    lsp = None
                    if lsp_name:
                        lsp = Lsp.objects.get(name__iexact=form.cleaned_data['lspName'])
                    #shipment.dc = plant
                    data['dc'] = plant
                    data['delivery_number'] = delivery_no
                    data['invoice_number'] = invoice_no
                    data['invoiced_on'] = form.cleaned_data['invoiceDate']
                    data['tracking_number'] = form.cleaned_data['awbNumber']
                    data['lsp'] = lsp
                    shipment_status = 'delivery created'
                    if invoice_no:
                        shipment_status = 'invoiced'
                    
                    #if shipment.status == shipment_status:
                    #    shipment_log = ShipmentLog.objects.select_related('order_log').get(action='status',
                    #        status=shipment_status, shipment=shipment)
                    #    o_log = shipment_log.order_log
                    #else:
                    #    shipment_log = ShipmentLog(action='status', status=shipment_status,
                    #        delivery_number=delivery_no)
                    #    o_log = OrderLog.objects.create(order=order, action='shipment')
                    
                    #shipment.invoice_number = invoice_no
                    #shipment.invoiced_on = form.cleaned_data['invoiceDate']
                    #shipment.pickedup_on = form.cleaned_data['pgiCreationDate'] - this is not shipping date
                    
                    shipment_item = None
                    try:
                        shipment_item = shipment.shipment_items.get(sap_order_item=sap_order_item)
                    except ShipmentItem.DoesNotExist:
                        #shipment item to be added. increment shipment amount
                        shipment.amount += (order_item.total_amount/order_item.qty)*form.cleaned_data['quantity']
            except SAPOrderItem.DoesNotExist:
                sap_log.info('Support: SAPOrderItem not found in item_ack - sno: %s, order_id:%s' %
                    (line_item_id, ref_order_id))
                raise
            except Dc.DoesNotExist:
                sap_log.info('Support: Dc not found in item_ack - code - %s, client - %s' %
                    (form.cleaned_data['plantId'], order.client))
                raise
            except Exception, e:
                sap_log.exception('Support: Error in processing item_ack - orderId: %s, sno: %s - %s' %
                    (ref_order_id, line_item_id, repr(e)))
                raise
            else:
                try:
                    with transaction.commit_on_success():
                        #start transaction
                        if delivery_no:
                            shipment.save()             #save shipment before creating new shipment item
                            if not shipment_item:       #create a shipment item if not found
                                shipment_item = ShipmentItem.objects.create(shipment=shipment, order_item=order_item,
                                    sap_order_item=sap_order_item, quantity=form.cleaned_data['quantity'])
                            
                            shipment.move_shipment_state(request, new_state=shipment_status, data=data,
                                shipment_item=shipment_item)
                            #o_log.save()
                            #shipment_log.shipment = shipment
                            #shipment_log.order_log = o_log
                            #shipment_log.dc = plant
                            #shipment_log.save()
                            #if invoice_no and shipment.status != 'invoiced':
                            #    pass
                            #else:
                            #    if not o_log:
                            #        o_log = OrderLog.objects.create(order=order, action='shipment')
                            #    shipment_log.shipment = shipment
                            #    shipment_log.order_log = o_log
                            #    shipment_log.dc = plant
                            #    shipment_log.save()
                            
                        #end transaction
                except Shipment.InvalidOperation, e:
                    sap_log.exception('Support: Error in processing item_ack - del_no: %s - Invalid Operation - %s' %
                        (delivery_no, repr(e)))
                    return HttpResponse('processed successfully')
                except Exception, e:
                    sap_log.exception('Support: Error in processing item_ack, rollback transaction - order_item: %s - %s' %
                        (order_item.id, repr(e)))
                    raise
                else:
                    return HttpResponse('Processed Successfully')
        else:
            sap_log.info('Support: Incorrect header in item_ack - %s' % request.POST.get('header',None))
    else:
        sap_log.info('Support: Form validation failed in item_ack - orderID: %s, itemID: %s' %
            (request.POST.get('orderId',None), request.POST.get('atgDocumentId',None)))
        sap_log.info('Form errors - %s' % form.errors)
    
    sap_log.info('Support: Item Ack Error- %s' % request.POST)
    return http_error_page(request, error_code=500)


def del_ack(request):
    if request.method != 'POST':
        sap_log.info('Support: Del Ack Error - Invalid request method')
        return http_error_page(request, error_code=404)
    
    sap_log.info('del_ack')
    sap_log.info('%s' % request.POST)
    form = DelAckForm(request.POST)
    if form.is_valid():
        if form.cleaned_data['header'] == 'DEL_ACK':
            delivery_no = form.cleaned_data['deliveryNumber']
            ref_order_id = form.cleaned_data['orderId']
            try:
                shipment = Shipment.objects.select_related('order').get(~Q(status='deleted'),
                    delivery_number=delivery_no, order__reference_order_id=ref_order_id)
                order = shipment.order
                #shipment_items = shipment.shipment_items.select_related('sap_order_item').all()
                #o_log = OrderLog(order=order, action='shipment')
                #shipment_log = ShipmentLog(shipment=shipment, action='status', status='deleted')
            except Shipment.DoesNotExist:
                sap_log.info('Support: Shipment not found in del_ack - order_id - %s, del_no -%s' %
                    (ref_order_id, delivery_no))
                raise
            except Exception, e:
                sap_log.exception('Support: Error in processing del_ack - orderId: %s, del_no: %s - %s' %
                    (ref_order_id, delivery_no, repr(e)))
                raise
            else:
                try:
                    with transaction.commit_on_success():
                        #start transaction
                        shipment.move_shipment_state(request, new_state='deleted')
                        #if order.support_state != 'confirmed':
                        #    order.support_state = 'confirmed'
                        #    order.save()
                        #    o_log.status = 'confirmed'
                        #o_log.save()
                        #
                        #shipment.status = 'deleted'
                        #shipment.save()
                        #shipment_log.order_log = o_log
                        #shipment_log.save()
                        #
                        #for shipment_item in shipment_items:
                        #    shipment_item.sap_order_item.status = 'awaiting delivery creation'
                        #    shipment_item.sap_order_item.save()
                        #    OrderItemLog.objects.create(order_item=shipment_item.order_item, order_log=o_log,
                        #        action='status', status='awaiting delivery creation')
                        #end transaction
                except Exception, e:
                    sap_log.exception('Support: Error in processing del_ack, rollback transaction - orderId: %s, del_no: %s - %s' %
                        (order.id, delivery_no, repr(e)))
                    raise
                else:
                    return HttpResponse('processed successfully')
        else:
            sap_log.info('Support: Incorrect header in del_ack - %s' % request.POST.get('header',None))
    else:
        sap_log.info('Support: Form validation failed in del_ack - orderID: %s, delivery_no: %s' %
            (request.POST.get('orderId',None), request.POST.get('deliveryNumber',None)))
        sap_log.info('Form errors - %s' % form.errors)

    sap_log.info('Support: Del Ack Error- %s' % request.POST)
    return http_error_page(request, error_code=500)


def invoice_ack(request):
    #invoice cancellation ack
    if request.method != 'POST':
        sap_log.info('Support: Invoice Ack Error - Invalid request method')
        return http_error_page(request, error_code=404)
    
    sap_log.info('invoice_ack')
    sap_log.info('%s' % request.POST)
    form = InvoiceCancelForm(request.POST)
    if form.is_valid():
        if form.cleaned_data['header'] == 'INV_CAN':
            delivery_no = forms.cleaned_data['deliveryNumber']
            invoice_no = forms.cleaned_data['invoiceNumber']
            try:
                shipment = Shipment.objects.get(~Q(status='deleted'), delivery_number=delivery_no,
                    invoice_number=invoice_no)
                order = shipment.order
                shipment_items = shipment.shipment_items.select_related('sap_order_item').all()
                o_log = OrderLog(order=order, action='shipment')
                shipment_log = ShipmentLog(shipment=shipment, action='status', status='invoice deleted')
            except Exception, e:
                sap_log.info('Support: Error in processing inv_can - del_no: %s, inv_no: %s - %s' %
                    (delivery_no, invoice_no, repr(e)))
                raise
            try:
                with transaction.commit_on_success():
                    #start transaction
                    if order.support_state != 'confirmed':
                        order.support_state = 'confirmed'
                        order.save()
                        o_log.status = 'confirmed'
                    o_log.save()
                    
                    shipment.status = 'invoice deleted'
                    shipment.save()
                    shipment_log.order_log = o_log
                    shipment_log.save()
                    #end transaction
            except Exception, e:
                sap_log.exception('Support: Error in processing inv_ack, rollback transaction - invoice_no: %s, del_no: %s - %s' %
                    (invoice_no, delivery_no, repr(e)))
                raise
            else:
                return HttpResponse('processed successfully')
        else:
            sap_log.info('Support: Incorrect header in inv_can - %s' % request.POST.get('header',None))
    else:
        sap_log.info('Support: Form validation failed in inv_can - del_no: %s, invoice_no: %s' %
            (request.POST.get('deliveryNumber',None), request.POST.get('invoiceNumber',None)))
        sap_log.info('Form errors - %s' % form.errors)

    return http_error_page(request, error_code=500)


def lsp_ack(request):
    if request.method != 'POST':
        sap_log.info('Support: LSP Ack Error - Invalid request method')
        return http_error_page(request, error_code=404)
    
    sap_log.info('lsp_ack')
    sap_log.info('%s' % request.POST)
    form = LSPAckForm(request.POST)
    if form.is_valid():
        if form.cleaned_data['header'] == 'LSP_ACK':
            processing_type = form.cleaned_data['processingType']
            if processing_type == 'Pre-Assigned':
                return HttpResponse('processed successfully')
            
            delivered_on = form.cleaned_data['deliveryDate']
            delivery_no = form.cleaned_data['deliveryNumber']
            tracking_no = form.cleaned_data['trackingNumber']
            lsp_code = form.cleaned_data['lspCode']     #this is lsp name
            try:
                shipment = Shipment.objects.select_related('order').get(~Q(status='deleted'),
                    delivery_number=delivery_no)
                lsp = Lsp.objects.get(name__iexact=lsp_code)
            except Shipment.DoesNotExist:
                sap_log.info('Support: No shipment found in lsp_ack - del_no: %s' % delivery_no)
                return HttpResponse('Processed successfully')
            except Exception, e:
                sap_log.exception('Support: Error in processing lsp_ack - del_no: %s, lsp_code - %s, %s' %
                    (delivery_no, lsp_code, repr(e)))
                raise
            
            data = {}
            data['tracking_number'] = form.cleaned_data['trackingNumber']
            data['lsp'] = lsp
            data['delivered_on'] = delivered_on
            
            if processing_type == 'Warehouse Update':
                with transaction.commit_on_success():
                    shipment.change_lsp(request, data=data)
                return HttpResponse('processed successfully')
            
            data['pickedup_on'] = form.cleaned_data['pickupDate']
            status = form.cleaned_data['itemState']
            new_state = shipment.status
            if status == 'UNDELIVERED':
                new_state = 'undeliverable'
            elif status == 'RETURNED':
                new_state = 'returned'
            elif status == 'DELIVERED':
                new_state = 'delivered'
            elif status == 'INTRANSIT' or data['pickedup_on']:
                new_state = 'shipped'

            try:
                with transaction.commit_on_success():
                    #start transaction
                    if shipment.status == new_state:
                        shipment.tracking_number = data['tracking_number']
                        shipment.lsp = lsp
                        shipment.pickedup_on = data['pickedup_on']
                        shipment.save()
                    else:
                        shipment.move_shipment_state(request, new_state=new_state, data=data)
                    #end transaction
            except Shipment.InvalidOperation, e:
                sap_log.exception('Support: Error in processing lsp_ack - del_no: %s - Invalid Operation - %s' %
                    (delivery_no, repr(e)))
                return HttpResponse('processed successfully')
            except Exception, e:
                sap_log.exception('Support: Error in processing lsp_ack, rollback transaction - del_no: %s, tracking_no: %s, lsp_code - %s, %s' %
                    (delivery_no, tracking_no, lsp_code, repr(e)))
                raise
            else:
                return HttpResponse('processed successfully')
        else:
            sap_log.info('Support: Incorrect header in lsp_ack - %s' % request.POST.get('header'))
    else:
        sap_log.info('Support: Form validation failed in lsp_ack - del_no: %s, tracking_no: %s' %
            (request.POST.get('deliveryNumber'), request.POST.get('trackingNumber')))
        sap_log.info('Form errors - %s' % form.errors)

    return http_error_page(request, error_code=500)


def inv_print_ack(request):
    return HttpResponse('processed successfully')


@login_required
@check_role([])
def refund_list(request):
    qs, action_flows = [], {}
    errors = []
    download = request.GET.get('download')
    today = datetime.now()
    
    if request.method == 'GET' and request.GET:
        filter_form = RefundFilterForm(request.GET)
        if filter_form.is_valid():
            qs = Refund.objects.filter(order__client=request.client.client)
            name = filter_form.cleaned_data['name']
            phone = filter_form.cleaned_data['phone']
            email = filter_form.cleaned_data['email']
            order_id = filter_form.cleaned_data['order_id']
            substate = filter_form.cleaned_data['state']
            payment_mode = filter_form.cleaned_data['payment_mode']
            start_date = filter_form.cleaned_data['start_date']
            end_date = filter_form.cleaned_data['end_date']
            no_user = False
            if name:
                name = name.strip()
            if name:
                qs = qs.filter(order__user__in = [p.id for p in Profile.objects.filter(
                    full_name__icontains = name)])
            if phone and not no_user:
                phone = phone.strip()
                try:
                    ph = Phone.objects.get(phone=phone)
                    qs = qs.filter(order__user=ph.user)
                except Phone.DoesNotExist:
                    qs = []
                    no_user = True
            if email and not no_user:
                email = email.strip()
                try:
                    e = Email.objects.get(email=email)
                    qs = qs.filter(order__user=e.user)
                except Email.DoesNotExist:
                    qs = []
                    no_user = True
            if order_id and not no_user:
                order_id = re.sub(r'\s','',order_id)
                if order_id.endswith(','):
                    order_id = order_id[:-1]
                if order_id:
                    order_list = order_id.split(',')
                    if len(order_list) > 1:
                        qs = qs.filter(order__reference_order_id__in=order_list)
                    else:
                        qs = qs.filter(order__reference_order_id=order_id)
            if substate and not no_user:
                qs = qs.filter(status=substate)
            if payment_mode:
                qs = qs.filter(order__payment_mode=payment_mode)
            if start_date and not no_user:
                qs = qs.filter(created_on__gte=start_date)
            if end_date and not no_user:
                qs = qs.filter(created_on__lte=(end_date+timedelta(days=1)))
            if not no_user:
                qs = qs.select_related('order').order_by('-id')
            
            if download:
                filename = 'refunds_%s.csv' % today.strftime('%H%M_%d%b')
                f = open('/tmp/%s' % filename, 'w')
                line = '"Order","Order Status","Payment Mode","Refund Amount","Opened On","Refund Status","Notes"\n'
                f.write(line)
                for refund in qs:
                    line = '"%s","%s","%s","%.2f","%s","%s","%s"\n' % (
                        refund.order.reference_order_id, refund.order.support_state,
                        refund.order.payment_mode, refund.amount, refund.created_on,
                        refund.status, refund.notes.replace('"','""') if refund.notes else '')
                    f.write(line)
                f.close()
                response = HttpResponse(file('/tmp/%s' % filename).read(), mimetype='text/csv')
                response['Content-Disposition'] = 'attachment; filename=%s' % filename
                return response
    else:
        filter_form = RefundFilterForm()

    return render_to_response('support/payment/refund_list.html', {'refunds': qs, 'items_per_page': 20,
        'filter_form':filter_form, 'action_flows':action_flows, 'errors':errors}, 
        context_instance = RequestContext(request))


@login_required
@check_role([])
def refund_form(request, refund_id=None):
    try:
        refund = Refund.objects.get(pk=refund_id)
        new_state = request.GET.get('state','')
        agent = utils.get_user_profile(request.user)
        form, data = None, {}
    except Exception, e:
        fb_log.exception('Support: payment_form - %s' % repr(e))
        return http_error_page(request, error_code=404)
    
    if (not new_state) or (refund.status == new_state):
        resp = HttpResponse('Invalid Operation')
        resp.status_code = 400
        return resp

    from payments.views import get_refund_form 
    error = False
    if request.method == 'POST':
        form = get_refund_form(request, refund=refund, data=request.POST, new_state=new_state)
        if form.is_valid():
            for fieldname in form.fields:
                data[fieldname] = form.cleaned_data[fieldname]
        else:
            error = True
    else:
        form = get_refund_form(request, refund=refund, new_state=new_state)
    if form and (not data):
        resp = render_to_response('support/refund/form.html', {'form':form, 'entity':'refund',
            'pk':refund.id, 'state':new_state}, context_instance = RequestContext(request))
        resp.status_code = 202
        if error:
            resp.status_code = 400
        return resp
    message = ''
    try:
        with transaction.commit_on_success():
            #start transaction
            refund.move_refund_state(request, new_state=new_state, agent=agent,
                data=data)
            #end transaction
    except Refund.InvalidOperation:
        resp = HttpResponse('Invalid Operation')
        resp.status_code = 400
        return resp
    except Refund.InsufficientData:
        resp = HttpResponse('Insufficient Data')
        resp.status_code = 400
        return resp
    except Exception, e:
        fb_log.exception('Support: refund_form - %s' % repr(e))
        resp = HttpResponse('Error in processing state change')
        resp.status_code = 400
        return resp
    else: 
        return HttpResponse('Refund update successful')
    return http_error_page(request, error_code=400)


@login_required
@check_role([])
def fulfillment_home(request):
    return render_to_response('support/fulfillment/home.html', {}, context_instance = RequestContext(request))


def get_value(obj, attrs):
    val = obj
    for attr in attrs:
        if isinstance(val,dict) and (attr in val):
            val = val[attr]
        elif hasattr(val,attr):
            val = getattr(val,attr)
            if hasattr(val, '__call__'):
                val = val()
    return val
 

@login_required
@check_role([])
def procurement_list(request):
    view = request.GET.get('view','cumulative')
    sort = request.GET.get('sort')
    sort_order = request.GET.get('s_ord','asc')
    download = request.GET.get('download')
    today = datetime.now()
    
    filter_form = None
    category, dc, state, article_id = None, None, '', ''
    start_date, end_date = None, None
    exclude_sto = False
    filter_form = ProcurementFilterForm(request.GET)
    if filter_form.is_valid():
        category = filter_form.cleaned_data['category']
        dc = filter_form.cleaned_data['dc']
        state = filter_form.cleaned_data['state']
        article_id = filter_form.cleaned_data['article_id']
        start_date = filter_form.cleaned_data['start_date']
        end_date = filter_form.cleaned_data['end_date']
        exclude_sto = filter_form.cleaned_data['exclude_sto']

    filter_kwargs = {}
    if category:
        filter_kwargs.update(seller_rate_chart__product__category=category)
    if dc:
        filter_kwargs.update(sap_order_item__dc=dc)
    if state:
        filter_kwargs.update(sap_order_item__status=state)
    else: 
        filter_kwargs.update(sap_order_item__status__in=['no stock','stock expected',
            'stock requested'])
    if article_id:
        article_id = re.sub(r'\s','',article_id)
        if article_id.endswith(','):
            article_id = article_id[:-1]
        if article_id:
            article_list = article_id.split(',')
            if len(article_list) > 1:
                filter_kwargs.update(seller_rate_chart__article_id__in=article_list)
            else:
                filter_kwargs.update(seller_rate_chart__article_id=article_id)
    if start_date:
        filter_kwargs.update(expected_stock_arrival__gte=start_date)
    if end_date:
        filter_kwargs.update(expected_stock_arrival__lte=end_date)
    
    order_items = OrderItem.objects.select_related('order','sap_order_item',
        'sap_order_item__dc','seller_rate_chart','seller_rate_chart__product__category'
        ).filter(order__support_state='confirmed', order__client=request.client.client, **filter_kwargs)
    
    if view == 'items':
        if sort:
            order_items = order_items.order_by('%s%s' % ('-' if (sort_order == 'desc') else '', sort))
        qs = order_items
    
    if view == 'cumulative':
        articles = {}
        for item in order_items:
            # Skip items if they are waiting for sto on physical stock
            skip = False
            stolog = item.inventorystolog_set.select_related(
                'from_dc', 'to_dc').all().order_by('-created_on')
            if stolog:
                if stolog[0].stock_to_be_allocated > 0:
                    if stolog[0].stock_allocated == False:
                        skip = False
                    else:       
                        skip = True
                else:
                    skip = True
            if skip and exclude_sto:
                continue

            key = '%s_%s_%s' % (item.seller_rate_chart_id, item.sap_order_item.dc_id, item.sap_order_item.status)
            val = articles.get(key,{})
            if not val:
                val['seller_rate_chart'] = item.seller_rate_chart
                val['item_title'] = item.item_title
                val['get_unit_price'] = item.get_unit_price()
                val['sale_price'] = item.sale_price
                val['sap_order_item'] = item.sap_order_item
                val['expected_stock_arrival'] = item.expected_stock_arrival
                val['qty'] = item.qty
            else:
                val['qty'] += item.qty
                if (not val['expected_stock_arrival']) or (item.expected_stock_arrival and \
                    (item.expected_stock_arrival < val['expected_stock_arrival'])):
                    val['expected_stock_arrival'] = item.expected_stock_arrival
            articles[key] = val
        qs = []
        for key,val in articles.iteritems():
            qs.append(val)
        
        if sort:
            keys = sort.split('__')
            qs.sort(key=lambda x:get_value(x, keys), reverse=True if sort_order=='desc' else False)
    
    if download:
        filename = 'procurement_%s.csv' % today.strftime('%H%M_%d%b')
        f = open('/tmp/%s' % filename, 'w')
        if view == 'items':
            line = '"Article ID","Name","Category","Unit Price","Qty","Total Value","DC","Order","Confimation Date",'
            line += '"Delivery Date","Stock Expected Date","Revised Stock Expected Date","Promised shipping date","State","Notes"\n'
            f.write(line)
            for item in qs:
                soi = item.sap_order_item
                src = item.seller_rate_chart
                line = '"%s","%s","%s","%.2f","%s","%.2f","%s","%s","%s","%s","%s","%s","%s","%s","%s"\n' % (
                    src.article_id, item.item_title.replace('"','""'), src.product.category.name,
                    item.get_unit_price(), item.qty, item.sale_price, soi.dc.code if soi.dc else '',
                    item.order.reference_order_id, item.order.confirming_timestamp.date(),
                    item.expected_delivery_date.date() if item.expected_delivery_date else '',
                    item.expected_stock_arrival.date() if item.expected_stock_arrival else '',
                    soi.revised_stock_arrival if soi.revised_stock_arrival else '', 
                    item.expected_stock_arrival.date() if item.expected_stock_arrival else '',
                    soi.status,
                    soi.notes.replace('"','""') if soi.notes else '')
                f.write(line)
        elif view == 'cumulative':
            line = '"Article ID","Name","Category","Unit Price","Qty","Total Value","DC","Stock Expected Date",'
            line += '"Revised Stock Expected Date","State"\n'
            f.write(line)
            for item in qs:
                soi = item['sap_order_item']
                src = item['seller_rate_chart']
                line = '"%s","%s","%s","%.2f","%s","%.2f","%s","%s","%s","%s"\n' % (
                    src.article_id, item['item_title'].replace('"','""'), src.product.category.name,
                    item['get_unit_price'], item['qty'], item['sale_price'], soi.dc.code if soi.dc else '',
                    item['expected_stock_arrival'].date() if item['expected_stock_arrival'] else '',
                    soi.revised_stock_arrival if soi.revised_stock_arrival else '', soi.status)
                f.write(line)
        f.close()
        response = HttpResponse(file('/tmp/%s' % filename).read(), mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s' % filename
        return response
    
    order_item_flows = get_actionflows(entity=request.session['content_types']['OrderItem'])
    return render_to_response('support/fulfillment/procurement_list.html', {'qs': qs, "items_per_page": 20,
        "view":view, "sort":sort, "s_ord":sort_order, "filter_form":filter_form, "order_item_flows":order_item_flows},
        context_instance = RequestContext(request))


@login_required
@check_role([])
def procurement_form(request, item_id=None):
    try:
        action_id = int(request.GET.get('action_id'))
        actionflow = ActionFlow.objects.select_related('initial_substate',
            'final_substate').get(pk=action_id)
        old_state = actionflow.initial_substate.name.lower()
        new_state = actionflow.final_substate.name.lower()
        agent = utils.get_user_profile(request.user)
        form, data = None, {}
        view = request.GET.get('view','cumulative')
    except Exception, e:
        fb_log.exception('Support: procurement_form - %s' % repr(e))
        return http_error_page(request, error_code=404)
    
    from orders.views import get_order_item_form
    error = False
    items = []
    if request.method == 'POST':
        form = get_order_item_form(request, data=request.POST, new_state=new_state)
        items = request.POST.getlist('items')
        if not items:
            resp = HttpResponse('No item selected')
            resp.status_code = 400
            return resp
        if form.is_valid():
            for fieldname in form.fields:
                data[fieldname] = form.cleaned_data[fieldname]
        else:
            error = True
    else:
        form = get_order_item_form(request, new_state=new_state)
    
    if form and (not data):
        resp = render_to_response('support/fulfillment/procurement_form.html', {'form':form, 'pk':item_id,
            'action_id':action_id, "view":view}, context_instance = RequestContext(request))
        resp.status_code = 202  #to not refresh the page
        if error:
            resp.status_code = 400
        return resp
    message = ''
    try:
        if view == 'items':
            sap_order_items = SAPOrderItem.objects.select_related('order').filter(id__in=items,
                order__support_state='confirmed', order__client=request.client.client)
            
            for item in sap_order_items:
                try:
                    with transaction.commit_on_success():
                        #start transaction
                        item.move_state(request, new_state=new_state, agent=agent, data=data)
                        #end transaction
                except Exception, e:
                    fb_log.exception('Support: procurement_form, item %s - %s' %
                        (item.id, repr(e)))
                    message += '%s, ' % item.order.reference_order_id
        
        elif view == 'cumulative':
            selected_items = SAPOrderItem.objects.select_related('order_item').filter(id__in=items)
            for sel_item in selected_items:
                filter_kwargs = {}
                filter_kwargs.update(order_item__seller_rate_chart = sel_item.order_item.seller_rate_chart)
                filter_kwargs.update(dc = sel_item.dc)
                filter_kwargs.update(status = sel_item.status)
                sap_order_items = SAPOrderItem.objects.select_related('order').filter(
                    order__support_state='confirmed', order__client=request.client.client,
                    **filter_kwargs)
                
                for item in sap_order_items:
                    try:
                        with transaction.commit_on_success():
                            #start transaction
                            item.move_state(request, new_state=new_state, agent=agent, data=data)
                            #end transaction
                    except Exception, e:
                        fb_log.exception('Support: procurement_form, item %s - %s' %
                            (item.id, repr(e)))
                        message += '%s, ' % item.order.reference_order_id
    except Exception, e:
        fb_log.exception('Support: procurement_form - %s' % repr(e))
        resp = HttpResponse('Error in processing')
        resp.status_code = 400
        return resp
    else: 
        if message:
            return HttpResponse('State change failed for orders:<br />%s' % message)
        return HttpResponse('State Change Successful')
    return http_error_page(request, error_code=400)

def suggest(request):
    q = request.GET.get('term', None)
    if q:
        try:
            response = solrutils.order_solr_suggest(q)
            if response: 
                terms = simplejson.loads(response)
                return HttpResponse(
                    simplejson.dumps(terms['terms']['suggest'][0::2]),
                    mimetype='application/json')
        except:
            pass
    return HttpResponse(simplejson.dumps([]), mimetype='application/json')


def get_c1_categories():
    qs = cache.get('c1_categories:5')
    if qs:
        return qs
    qs = CategoryGraph.objects.select_related('category').filter(parent=None,
        category__client=5)
    if qs:
        cache.set('c1_categories:5', [x.category for x in qs])
    return qs


def to_solr_date(d):
    v = datetime.strptime(d, '%d %b %Y %H:%M:%S') 
    return v.strftime('%Y-%m-%dT%H:%M:%S.000Z')

@login_required
def search(request):
    q = request.GET.get('q', '')
    doc_type = request.GET.get('t', None)
    page = request.GET.get('page', 1)
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')

    if doc_type == 'fulfillment':
        if request.path.startswith('/search/'):
            return HttpResponseRedirect(
                request.get_full_path().replace(
                    '/search/', '/fulfillment/dashboard/'))

    try:
        page = int(page)
    except ValueError:
        page = 1

    results = []
    found = 0
    total_pages = 1
    items_per_page = 20
    pagination = {}
    facets = []
    total_amount = Decimal('0.0')

    query = q
    if doc_type:
        if q:
            query = '%s AND doc_type:%s' % (q, doc_type)
        else:
            query = 'doc_type:%s' % doc_type

    if start_date:
        start_date = '%s 00:00:00' % start_date
    if end_date:
        end_date = '%s 23:59:59' % end_date
    if start_date and end_date:
        query += ' AND booking_timestamp: [%s TO %s]' % (
            to_solr_date(start_date), to_solr_date(end_date))

    if start_date and not end_date:
        query += ' AND booking_timestamp: [%s TO %s]' % (
            to_solr_date(start_date), '*')

    if end_date and not start_date:
        query += ' AND booking_timestamp: [%s TO %s]' % (
            '*', to_solr_date(end_date))

    params = {}
    params['start'] = (page -1) * items_per_page
    params['rows'] = items_per_page
    params['facet'] = 'true'
    params['facet_mincount'] = 1
    params['facet_limit'] = '-1'
    params['stats'] = 'true'

    stats = 'payable_amount'
    # Common facet fields
    facet_fields = ['support_state', 'payment_mode']
    if doc_type == 'orderitem':
        facet_fields.extend(['item_category_ids', 'item_sap_status', 'item_dc'])
        facet_names = ['Order state', 'Payment Mode']
        stats = 'item_sale_price'
    if doc_type == 'shipment':
        facet_fields.extend(['shipment_status', 'shipment_dc', 'shipment_lsp'])
        stats = 'shipment_amount'
    if doc_type == 'refund':
        facet_fields.extend(['refund_status'])
        stats = 'refund_amount'
    if doc_type == 'payment':
        facet_fields.extend(['payment_status', 'payment_payment_mode'])
        stats = 'payment_amount'
    params['facet_field'] = facet_fields
    params['stats_field'] = stats

    facet_names = {
        'support_state': 'Order state',
        'payment_mode': 'Payment Mode',
        'item_sap_status': 'Item status',
        'item_dc': 'Assigned DC',
        'shipment_status': 'Shipment status',
        'shipment_dc': 'DC',
        'shipment_lsp': 'LSP',
        'refund_status': 'Refund status',
        'payment_status': 'Payment status',
        'payment_payment_mode': 'Payment method',
        'item_category_ids': 'Category',
        }

    # Get the filter queries to be added
    filter_queries = []
    for facet_name in facet_fields:
        if facet_name in request.GET:
            if request.GET.getlist(facet_name):
                fq = ' OR '.join(
                    ['"%s"' % x for x in request.GET.getlist(facet_name)])
                fq = '%s:(%s)' % (facet_name, fq)
                filter_queries.append(fq)
    if filter_queries:
        params['fq'] = filter_queries
                 

    response = solrutils.order_solr_search(query, fields='*', highlight=None,
        score=True, sort='score', sort_order='desc', operation='/select',
        **params)

    if response:
        found = int(response.numFound)
        total_pages = found/items_per_page
        if found % items_per_page > 0:
            total_pages += 1
        base_url = request.get_full_path()

        page_pattern = re.compile('[&?]page=\d+')
        base_url = page_pattern.sub('',base_url)
        page_pattern = re.compile('[&?]per_page=\d+')
        base_url = page_pattern.sub('',base_url)
        if base_url.find('?') == -1:
            base_url = base_url + '?'
        else:
            base_url = base_url + '&'

        pagination = utils.getPaginationContext(page, total_pages, base_url)
        pagination['result_from'] = (page-1) * items_per_page + 1
        pagination['result_to'] = utils.ternary(page*items_per_page > found, found, page*items_per_page)
        results = response.results
        facet_results = response.facet_counts
        stats_results = response.stats
        if stats_results and stats in stats_results['stats_fields']:
            total_amount = stats_results['stats_fields'][stats]['sum']
            total_amount = utils.formatMoney(total_amount)

        if 'facet_fields' in facet_results:
            for facet_name in facet_fields:
                facet = {}
                facet['name'] = facet_names[facet_name]
                values = []
                for key, value in facet_results['facet_fields'][facet_name].iteritems():
                    facet_data = {'data': key,
                        'value': key,
                        'count': value,
                        'selected': key in request.GET.getlist(facet_name),
                        'key': facet_name}

                    skip = False
                    if facet_name == 'item_category_ids':
                        facet_data['data'] = Category.objects.get(pk=key)
                        facet_data['name'] = facet_data['data'].name
                        skip = facet_data['data'] not in get_c1_categories()
                            
                    if not skip:
                        values.append(facet_data)
                if facet_name == 'item_category_ids':
                    values.sort(key = operator.itemgetter('name'))
                else:
                    values.sort(key = operator.itemgetter('data'))
                facet['values'] = values 
                facets.append(facet)

    return render_to_response('support/search.html',
        {
            "results": results,
            "q": q,
            "doc_type": doc_type,
            "found": found,
            "page": page,
            "total_pages": total_pages,
            "total_amount": total_amount,
            "items_per_page": items_per_page,
            "pagination": pagination,
            "facets": facets
        },
        context_instance = RequestContext(request))

@login_required
@check_role([])
def dispatch_list(request):
    qs = []
    errors = []
    
    if request.method == 'GET' and request.GET:
        filter_form = DispatchFilterForm(request.GET)
        if filter_form.is_valid():
            qs = Shipment.objects.exclude(status__in=['deleted','shipped','delivered']
                ).filter(order__client=request.client.client)
            order_id = filter_form.cleaned_data['order_id']
            delivery_number = filter_form.cleaned_data['delivery_number']
            invoice_number = filter_form.cleaned_data['invoice_number']
            dc = filter_form.cleaned_data['dc']
            lsp = filter_form.cleaned_data['lsp']
            substate = filter_form.cleaned_data['state']
            start_date = filter_form.cleaned_data['start_date']
            end_date = filter_form.cleaned_data['end_date']
            if order_id:
                order_id = re.sub(r'\s','',order_id)
                if order_id.endswith(','):
                    order_id = order_id[:-1]
                if order_id:
                    order_list = order_id.split(',')
                    if len(order_list) > 1:
                        qs = qs.filter(order__reference_order_id__in=order_list)
                    else:
                        qs = qs.filter(order__reference_order_id=order_id)
            if delivery_number:
                delivery_number = re.sub(r'\s','',delivery_number)
                if delivery_number.endswith(','):
                    delivery_number = delivery_number[:-1]
                if delivery_number:
                    delivery_list = delivery_number.split(',')
                    if len(delivery_list) > 1:
                        qs = qs.filter(delivery_number__in=delivery_list)
                    else:
                        qs = qs.filter(delivery_number=delivery_number)
            if invoice_number:
                invoice_number = re.sub(r'\s','',invoice_number)
                if invoice_number.endswith(','):
                    invoice_number = invoice_number[:-1]
                if invoice_number:
                    invoice_list = invoice_number.split(',')
                    if len(invoice_list) > 1:
                        qs = qs.filter(invoice_number__in=invoice_list)
                    else:
                        qs = qs.filter(invoice_number=invoice_number)
            if dc:
                qs = qs.filter(dc=dc)
            if lsp:
                qs = qs.filter(lsp=lsp)
            if substate:
                qs = qs.filter(status=substate)
            if start_date:
                qs = qs.filter(created_on__gte=start_date)
            if end_date:
                qs = qs.filter(created_on__lte=(end_date+timedelta(days=1)))
            qs = qs.select_related('order','dc','lsp').order_by('-id')
    else:
        filter_form = DispatchFilterForm()
    
    return render_to_response('support/fulfillment/dispatch_list.html', {"shipments": qs, "items_per_page": 20,
        "filter_form":filter_form}, context_instance = RequestContext(request))

@login_required
@check_role([])
def add_complaint(request):
    if request.method == 'POST':
        level = request.POST.get('level')
        order_id = request.POST.get('order')
        order = Order.objects.get(pk=order_id);
        order_items = order.get_order_items(request, select_related=('seller_rate_chart__product'))
        products = []
        for oi in order_items:
            products.append((oi.seller_rate_chart.product.id, oi.seller_rate_chart.product))
        form = ComplaintAddForm(products, request.POST)
        if form.is_valid():
            notes = form.cleaned_data['notes']
            category = form.cleaned_data['category']
            status = form.cleaned_data['status']
            source = form.cleaned_data['source']
            prods = form.cleaned_data['products']
            try:
                complaint = Complaint(order=order, user=order.user, status=status, category=category, level=level, source=source)
                days = Complaint.CATEGORY_TAT_MAP[category]
                tat = datetime.now()
                for i in range(0, days):
                    tat += timedelta(days=1)
                    if tat.weekday() == 6:  # excluding Sunday
                        tat += timedelta(days=1)
                complaint.TAT = tat
                complaint.save()
                products = Product.objects.filter(pk__in=prods)
                for p in products:
                    complaint.products.add(p)
                profile = utils.get_user_profile(request.user)
                update = Update(complaint=complaint, category=category, level=level, notes=notes, added_by=profile)
                update.save() 

                return HttpResponse('Complaint Added Successfully')

            except Exception, e:
                fb_log.info('Support: add_complaint order %s user %s - %s' % (order_id,profile, repr(e)))
                return http_error_page(request, error_code=404)
        else:
            resp = render_to_response("support/complaint/complaint_form.html", {"form":form, 'level':level},
                context_instance = RequestContext(request))
            resp.status_code = 203
            return resp
    if request.method == 'GET':
        order_id = request.GET.get('order_id','')
        status = request.GET.get('status','')
        level = request.GET.get('level')
        order = Order.objects.get(pk=order_id);
        order_items = order.get_order_items(request, select_related=('seller_rate_chart__product'))
        products = []
        for oi in order_items:
            products.append((oi.seller_rate_chart.product.id, oi.seller_rate_chart.product))
        form = ComplaintAddForm(choices=products, initial={'order':order_id, 'status':status})
        resp = render_to_response("support/complaint/complaint_form.html", {"form":form, 'level':level},
            context_instance = RequestContext(request))
        return resp
    else:
        return http_error_page(request, error_code=404)

@login_required
@check_role([])
def update_complaint(request):
    if request.method == 'POST':
        form = ComplaintUpdateForm(request.POST)
        level = request.POST.get('level')
        if form.is_valid():
            notes = form.cleaned_data['notes']
            category = form.cleaned_data['category']
            status = form.cleaned_data['status']
            complaint_id = form.cleaned_data['complaint']
            try:
                complaint = Complaint.objects.get(id=complaint_id)
                complaint.category = category
                if status == 'followup' and not complaint.moved_to_followup:
                    complaint.moved_to_followup = datetime.now()
                if status == 'closed' and not complaint.closed_on:
                    complaint.closed_on = datetime.now()
                complaint.status = status
                complaint.level = level
                complaint.save()
                
                profile = utils.get_user_profile(request.user)
                update = Update(complaint=complaint, category=category, level=level, notes=notes, added_by=profile)
                update.save() 

                return HttpResponse('Complaint Updated Successfully')

            except Exception, e:
                fb_log.info('Support: update_complaint complaint %s - %s' % (complaint_id, repr(e)))
                return http_error_page(request, error_code=404)
        else:
            resp = render_to_response("support/complaint/complaint_form.html", {"form":form, "level":level},
                context_instance = RequestContext(request))
            resp.status_code = 203
            return resp
    if request.method == 'GET':
        complaint_id = request.GET.get('complaint_id','')
        category = request.GET.get('category','')
        status = request.GET.get('status','')
        level = request.GET.get('level','green')
        form = ComplaintUpdateForm(initial={'complaint':complaint_id, 'category':category, 'status':status})
        resp = render_to_response("support/complaint/complaint_form.html", {"form":form, 'level':level},
            context_instance = RequestContext(request))
        return resp
    else:
        return http_error_page(request, error_code=404)

@login_required
@check_role([])
def complaint_list(request):
    errors, qs =[],[]
    if request.method == 'GET' and request.GET:
        filter_form = ComplaintFilterForm(request.GET)
        if filter_form.is_valid():
            phone = filter_form.cleaned_data['phone']
            email = filter_form.cleaned_data['email']
            order_id = filter_form.cleaned_data['order_id']
            complaint_id = filter_form.cleaned_data['complaint_id']
            category = filter_form.cleaned_data['category']
            status = filter_form.cleaned_data['status']
            level = filter_form.cleaned_data['level']
            no_user = False
            qs = Complaint.objects.all().order_by('-id')
            if complaint_id:
                qs = qs.filter(pk=complaint_id)
            if category:
                qs = qs.filter(category=category)
            if status:
                qs = qs.filter(status=status)
            if phone and not no_user:
                phone = phone.strip()
                try:
                    ph = Phone.objects.get(phone=phone)
                    qs = Complaint.objects.filter(user=ph.user)
                except Phone.DoesNotExist:
                    qs = []
                    no_user = True
            if email and not no_user:
                email = email.strip()
                try:
                    e = Email.objects.get(email=email)
                    qs = qs.filter(user=e.user)
                except Email.DoesNotExist:
                    qs = []
                    no_user = True
            if level:
                qs = qs.filter(level=level)
            if order_id and not no_user:
               order = Order.objects.filter(reference_order_id=order_id)
               qs = qs.filter(order=order)
            export = request.GET.get('export')
            if export == 'excel':
                excel_header = ['Complaint ID','Order Id','Products','User','Status','Category','Level','Source','Created On','Moved To Followup','Closed On','TAT','Notes']
                excel_data = []
                for q in qs:
                    li = []
                    li.extend([q.id, q.order.reference_order_id])
                    prods = q.products.all()
                    products = ''
                    for p in prods:
                        products += p.title + ', '
                    li.append(products)
                    li.extend([q.user,q.status,q.category,q.level,q.source,q.created_on,q.moved_to_followup,q.closed_on,q.TAT])
                    ups = q.updates.all()
                    notes = ''
                    for u in ups:
                        notes += u.notes + ', '
                    li.append(notes)
                    excel_data.append(li)
                return save_excel_file(excel_header=excel_header, excel_data=excel_data)
    else:
        filter_form = ComplaintFilterForm()
    return render_to_response('support/complaint/complaint_list.html', {'complaints':qs,'items_per_page':20,
        'filter_form':filter_form, 'errors':errors}, context_instance = RequestContext(request))
    
    
def fulfillment_dashboard(request):
    q = request.GET.get('q', '')
    page = request.GET.get('page', 1)
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    sort = request.GET.get('sort', 'flf_ship_before')
    sort_order = request.GET.get('s_ord', 'asc')
    download = request.GET.get('download')
    doc_type = 'orderitem'

    try:
        page = int(page)
    except ValueError:
        page = 1

    results = []
    found = 0
    total_pages = 1
    items_per_page = 20
    pagination = {}
    facets = []
    total_amount = Decimal('0.0')

    query = q
    if q:
        query = '%s AND doc_type:%s' % (q, doc_type)
    else:
        query = 'doc_type:%s' % doc_type

    query = '%s AND -support_state:(booked OR cancelled) AND -item_state:(cancelled OR bundle)' % query


    if not start_date:
        # Stop docs before 24th Feb
        start_date = '24 Feb 2012'

    if start_date:
        start_date = '%s 00:00:00' % start_date
    if end_date:
        end_date = '%s 23:59:59' % end_date

    if start_date and end_date:
        query += ' AND confirming_timestamp: [%s TO %s]' % (
            to_solr_date(start_date), to_solr_date(end_date))

    if start_date and not end_date:
        query += ' AND confirming_timestamp: [%s TO %s]' % (
            to_solr_date(start_date), '*')

    if end_date and not start_date:
        query += ' AND confirming_timestamp: [%s TO %s]' % (
            '*', to_solr_date(end_date))

    params = {}
    params['start'] = (page -1) * items_per_page
    params['rows'] = items_per_page
    params['facet'] = 'true'
    params['facet_mincount'] = 1
    params['facet_limit'] = '-1'
    params['stats'] = 'true'

    stats = 'item_sale_price'
    facet_fields = ['support_state', 'payment_mode','item_category_ids',
        'flf_status', 'flf_dc', 'flf_lsp', 'shipment_status']
    params['facet_field'] = facet_fields
    params['stats_field'] = stats

    facet_names = {
        'support_state': 'Order state',
        'flf_status': 'Item Status',
        'shipment_status': 'Shipment status',
        'flf_dc': 'Site Code',
        'flf_lsp': 'LSP',
        'item_category_ids': 'Category',
        'payment_mode': 'Payment Mode',
        'shipment_status': 'Shipment Status',
        }

    # Get the filter queries to be added
    filter_queries = []
    for facet_name in facet_fields:
        if facet_name in request.GET:
            if request.GET.getlist(facet_name):
                fq = ' OR '.join(
                    ['"%s"' % x for x in request.GET.getlist(facet_name)])
                fq = '%s:(%s)' % (facet_name, fq)
                filter_queries.append(fq)
    if filter_queries:
        params['fq'] = filter_queries
                 

    response = solrutils.order_solr_search(query, fields='*', highlight=None,
        score=True, sort=sort, sort_order=sort_order, operation='/select',
        **params)

    if response:
        found = int(response.numFound)
        total_pages = found/items_per_page
        if found % items_per_page > 0:
            total_pages += 1
        base_url = request.get_full_path()

        page_pattern = re.compile('[&?]page=\d+')
        base_url = page_pattern.sub('',base_url)
        page_pattern = re.compile('[&?]per_page=\d+')
        base_url = page_pattern.sub('',base_url)
        if base_url.find('?') == -1:
            base_url = base_url + '?'
        else:
            base_url = base_url + '&'

        pagination = utils.getPaginationContext(page, total_pages, base_url)
        pagination['result_from'] = (page-1) * items_per_page + 1
        pagination['result_to'] = utils.ternary(page*items_per_page > found, found, page*items_per_page)
        results = response.results
        facet_results = response.facet_counts
        stats_results = response.stats
        if stats_results and stats in stats_results['stats_fields']:
            total_amount = stats_results['stats_fields'][stats]['sum']
            total_amount = utils.formatMoney(total_amount)

        if 'facet_fields' in facet_results:
            for facet_name in facet_fields:
                facet = {}
                facet['name'] = facet_names[facet_name]
                values = []
                for key, value in facet_results['facet_fields'][facet_name].iteritems():
                    facet_data = {'data': key,
                        'value': key,
                        'count': value,
                        'selected': key in request.GET.getlist(facet_name),
                        'key': facet_name}

                    skip = False
                    if facet_name == 'item_category_ids':
                        facet_data['data'] = Category.objects.get(pk=key)
                        facet_data['name'] = facet_data['data'].name
                        skip = facet_data['data'] not in get_c1_categories()
                            
                    if not skip:
                        values.append(facet_data)
                if facet_name == 'item_category_ids':
                    values.sort(key = operator.itemgetter('name'))
                else:
                    values.sort(key = operator.itemgetter('data'))
                facet['values'] = values 
                facets.append(facet)

    if download:
        filename = utils.get_temporary_file_path()
        f = open(filename, 'w')
        line = '"Order","Order Date","Ship Before","Deliver Before","Shipped On",'
        line += '"Delivered On","Site Code","Delivery No.","Article Id","Product",'
        line += '"Qty","Amount","Invoice Number","Invoiced No","AWB No.",'
        line += '"Customer","Ship To","Phones","Emails",'
        line += '"Status"\n'
        f.write(line)

        del params['facet']
        del params['stats']

        # Cut into batches of 500
        batch_size = 500
        start = 0
        remaining = found
        written = {}

        while remaining > 0:
            params['start'] = start
            params['rows'] = batch_size
            response = solrutils.order_solr_search(query, fields='*', highlight=None,
                score=True, sort=sort, sort_order=sort_order, operation='/select',
                **params)
            start += batch_size
            remaining -= batch_size
            lines = []
            for doc in response.results:
                if doc['item_pk'] in written:
                    continue

                ship_to = doc['delivery_address'].replace('"','""') + " " 
                ship_to += doc['delivery_city'].replace('"','""')  + " "
                ship_to += doc['delivery_state'].replace('"','""') + " " 
                ship_to += doc['delivery_pincode'].replace('"','""')
                ship_to = ship_to.replace('\n',' ')

                line = '"%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%s","%.2f","%s","%s","%s","%s","%s","%s","%s","%s"\n' % (
                    doc['reference_order_id'], doc['confirming_timestamp'],
                    doc.get('flf_ship_before',''), doc.get('flf_del_before',''),
                    doc.get('shipment_pickedup_on',''),
                    doc.get('shipment_delivered_on',''),
                    doc.get('flf_dc',''), doc.get('shipment_delivery_number',''),
                    doc['item_article_id'], doc['item_title'].replace('"','""') , doc['item_qty'],
                    doc['item_sale_price'], doc.get('shipment_invoice_number',''),
                    doc.get('shipment_invoiced_on',''),
                    doc.get('shipment_tracking_number',''),
                    doc.get('user_name',''), ship_to.replace('"','""'),
                    ",".join(doc.get('user_phones', [])[:5]),
                    ",".join(doc.get('user_emails', [])[:5]).replace('"','""') ,
                    doc.get('flf_status',''),
                    )

                lines.append(str(line.encode('ascii','ignore')))
                written[doc['item_pk']] = True
            f.writelines(lines)

        response = HttpResponse(file(filename).read(), mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=fulfillment.csv' 
        f.close()
        return response

    return render_to_response('support/fulfillment/dashboard.html',
        {
            "results": results,
            "q": q,
            "doc_type": 'fulfillment',
            "found": found,
            "page": page,
            "total_pages": total_pages,
            "total_amount": total_amount,
            "items_per_page": items_per_page,
            "pagination": pagination,
            "facets": facets,
            "sort": sort,
            "s_ord": sort_order,
            "view": request.GET.get('view', ''),
        },
        context_instance = RequestContext(request))

