# Create your views here.
from datetime import datetime,timedelta
import hashlib
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect
from django.template import RequestContext
from django.db.models import Count, Sum
from django.db import models

from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from django.views.generic.list_detail import object_list
from decimal import *

from ccm.models import *
from communications.models import *
import gviz_api

def check_dates(request):
    from_date = request.GET.get('from','')
    to_date = request.GET.get('to','')
    search_trend = request.GET.get('search_trend','')
    errors = ""
    if search_trend:
        to_date = datetime.now()
        if search_trend == "day":
            from_date = to_date + timedelta(days=-0)
        elif search_trend == "week":
            from_date = to_date + timedelta(days=-6)
        elif search_trend == "month":
            from_date = to_date + timedelta(days=-29)
        to_date = to_date + timedelta(days=+1)
        return dict(from_date=from_date,to_date=to_date,search_trend=search_trend)

    if from_date== None or from_date == "" or to_date==None or to_date== "":
        to_date = datetime.now()
        from_date = to_date + timedelta(days=-6)
        to_date = to_date + timedelta(days=+1)
        return dict(from_date=from_date,to_date=to_date,search_trend=None)

    if from_date and to_date:
        from_date = datetime.strptime(from_date,'%d %b, %Y').date()
        to_date = datetime.strptime(to_date,'%d %b, %Y').date()
        to_date = to_date + timedelta(days=+1)
        return dict(from_date=from_date,to_date=to_date,search_trend=None)

def call_report(request):
    params=request.GET
    agents = Agent.objects.values('name')
    date_check=check_dates(request)
    to_show=True
    from_date,to_date=date_check['from_date'],date_check['to_date']
    search_trend = date_check['search_trend']
    to=to_date    
    get_agent,qs=request.GET.get('agent',''),None
    show_table = request.GET.get('view','')
    if not show_table:
        show_table = False
    elif show_table == "table":
        show_table = True
    if get_agent and get_agent != 'All':
        agent = Agent.objects.get(name=get_agent)
        qs=Call.objects.filter(answered_by=agent)
    else:
        qs=Call.objects
    chart_incalls = []
    chart_inabnd = []
    max_incall = 0
    chart_outcalls = []
    chart_outabnd = []
    max_outcall = 0
    visual_data=[] 
    description = {"Date": ("date", "date"),"inbound":("number","Inbound Calls"),"outbound":("number","Outbound Calls")}
    dates=[]
    diff = ((to_date - from_date).days)
    for i in range(0,diff): dates.append(from_date+timedelta(days=i))
    dates.reverse()
    total_calls,did_no =[],request.GET.get('did_no','')
    for date in dates:
        answered_inbound = qs.filter(called_on__gte = date,called_on__lte = (date+timedelta(days=1)),status = 'answered',type='inbound')
        if did_no:  answered_inbound = answered_inbound.filter(did_number=did_no)
            
        abandoned_inbound = qs.filter(called_on__gte = date,called_on__lte = (date+timedelta(days=1)),status='abandoned',type='inbound')
        if did_no:  abandoned_inbound = abandoned_inbound.filter(did_number=did_no)
        
        answered_outbound = qs.filter(called_on__gte = date,called_on__lte = (date+timedelta(days=1)),status='answered').filter(Q(type='outbound_manual') or Q(type='outbound_dialer'))
        if did_no:  answered_outbound = answered_outbound.filter(did_number=did_no)

        abandoned_outbound = qs.filter(called_on__gte = date,called_on__lte = (date+timedelta(days=1)),status='abandoned').filter(Q(type='outbound_manual') or Q(type='outbound_dialer'))
        if did_no:  abandoned_outbound = abandoned_outbound.filter(did_number=did_no)
        
        total_in = answered_inbound.count()+abandoned_inbound.count()
        chart_incalls.append(total_in)
        if total_in:
            inbound_percen = abandoned_inbound.count()*100/(total_in)
        else:
            inbound_percen = 0
        chart_inabnd.append(inbound_percen)
        if total_in > max_incall:
            max_incall = total_in

        total_out = answered_outbound.count()+abandoned_outbound.count()
        chart_outcalls.append(total_out)
        if total_out:
            outbound_percen = abandoned_outbound.count()*100/(total_out)
        else:
            outbound_percen = 0
        chart_outabnd.append(outbound_percen)
        if total_out > max_outcall:
            max_outcall = total_out

        total_calls.append([date,answered_inbound.count(),abandoned_inbound.count(),answered_outbound.count(),abandoned_outbound.count()])
        visual_data.append({"Date":date,"inbound":total_in,"outbound":total_out})
    visual_data.reverse()
    data_table = gviz_api.DataTable(description)
    data_table.LoadData(visual_data)
    jscode = data_table.ToJSCode("jscode_data",columns_order=("Date","inbound","outbound"))
    max_incall *= 1.2
    max_outcall *= 1.2
    chart_incalls.reverse()
    chart_inabnd.reverse()
    chart_outcalls.reverse()
    chart_outabnd.reverse()
    if chart_inabnd:
        for i in range(len(chart_inabnd)):
            chart_inabnd[i] = int((chart_inabnd[i]*max_incall)/100)
    if chart_outabnd:
        for i in range(len(chart_outabnd)):
            chart_outabnd[i] = int((chart_outabnd[i]*max_outcall)/100)
    chart_data = dict(chart_incalls = chart_incalls,chart_inabnd = chart_inabnd, max_incall = max_incall, chart_outcalls = chart_outcalls, chart_outabnd = chart_outabnd, max_outcall = max_outcall)
    to_date = to_date + timedelta(days=-1)
    return render_to_response('asterisk_api/cc_report.html',
                                {
                                    'from_date':from_date,    
                                    'to_date' : to_date,
                                    'total_calls': total_calls,
                                    'to_show': to_show,
                                    'did_no': did_no,
                                    'agents': agents,
                                    'selected_agent':get_agent,
                                    'search_trend':search_trend,
                                    'jscode':jscode,
                                    'chart_data':chart_data,
                                    'show_table':show_table
                                },
                                context_instance = RequestContext(request))

    
def calls_volume_report(request):
    params=request.GET
    agents = Agent.objects.values('name')
    date_check=check_dates(request)
    from_date,to_date=date_check['from_date'],date_check['to_date']
    search_trend = date_check['search_trend']
    to_show=True
    to=to_date    
    get_agent,get_call_type,qs=request.GET.get('agent',''),request.GET.get('call_type',''),None
    if get_agent and get_agent != 'All':
        agent = Agent.objects.get(name=get_agent)
        qs=Call.objects.filter(answered_by=agent)
    else:
        qs=Call.objects

    if get_call_type != 'All':
        qs = qs.filter(type__contains = get_call_type)
    dates=[]
    diff = ((to_date - from_date).days)+1
    for i in range(0,diff): dates.append(from_date+timedelta(days=i))
    dates.reverse()
    call_data = []
    for date in dates:
        calls=qs.filter(called_on__gte = date,called_on__lte = (date+timedelta(days=1)))
        ans = calls.filter(status = 'answered')
        abnd = calls.filter(status = 'abandoned')
        ans_wt_time = ans.aggregate(Sum('wait_duration'))
        abnd_wt_time = abnd.aggregate(Sum('wait_duration'))
        total_callduration = ans.aggregate(Sum('call_duration'))
        #answered wait time-average
        if calls.count() and ans_wt_time['wait_duration__sum']:
            avg_ans_wt_time = round((ans_wt_time['wait_duration__sum']/calls.count()),2)
        else: avg_ans_wt_time = 0

        #abandoned wait time - average
        if calls.count() and abnd_wt_time['wait_duration__sum']:
            avg_abnd_wt_time = round((abnd_wt_time['wait_duration__sum']/calls.count()),2)
        else:
            avg_abnd_wt_time = 0

        if total_callduration['call_duration__sum'] and ans_wt_time['wait_duration__sum']:
            total_talk_time = (total_callduration['call_duration__sum']- ans_wt_time['wait_duration__sum'])
        elif total_callduration['call_duration__sum']:
            total_talk_time = total_callduration['call_duration__sum']
        else:   total_talk_time = 0

        if calls.count():
            avg_ttt = round((total_talk_time/calls.count()),2)
        else:   avg_ttt = 0

        if calls.count():
            percent_abnd = round((abnd.count()*100/Decimal(calls.count())),2)
        else:
            percent_abnd = 0

        total_talk_time = round((total_talk_time/3600.00),2)
        
        call_data.append([date,calls.count(),ans.count(),abnd.count(),percent_abnd,avg_ans_wt_time,avg_abnd_wt_time,total_talk_time,avg_ttt])
    to_date = to_date + timedelta(days=-1)
    return render_to_response('asterisk_api/calls_volume_report.html',
                                {
                                    'from_date':from_date,    
                                    'to_date' : to_date,
                                    'call_data': call_data,
                                    'to_show': to_show,
                                    'agents': agents,
                                    'selected_agent':get_agent,
                                    'selected_call_type': get_call_type,
                                    'search_trend':search_trend,
                                },
                                context_instance = RequestContext(request))

def agent_login_logout_report(request):
    agents_list = Agent.objects.values('name')
    from_date = request.GET.get('from','')
    if from_date != '':
        from_date = datetime.strptime(request.GET.get('from',''),'%m/%d/%Y').date()
    else:
        from_date = datetime.now()
    #to_date = datetime.strptime(request.GET.get('to',''),'%d/%m/%Y').date()
    #to_date = to_date + timedelta(days=1)
    agents = agents_list
    get_agent = request.GET.get('agent','')
    if get_agent != 'All' and get_agent != '':
        agents = [{'name':get_agent}]
    print agents
    time,time_hours,login_timestamp,logout_timestamp = 0,0,None,None
    agent_loginlogout_data = []
    for agent in agents:
        login_received,logout_received,time,login_time,logout_time,time_diff,login_timestamp,logout_timestamp = 0,0,0,None,None,None,None,None
        time_hours = 0
        agt = Agent.objects.get(name = agent['name'])
        #qs = AgentLoginLogout.objects.filter(agent_id = agt,time__gte = datetime.now().date(),time__lte = datetime.now().date() + timedelta(days=1))
        qs = AgentLoginLogout.objects.filter(agent_id = agt,time__gte = from_date,time__lte = from_date + timedelta(days=1))
        for loginlogout in qs:
            time_diff = None
            if loginlogout.action == 'Login':
                if not login_timestamp:
                    login_timestamp = loginlogout.time
                login_received = 1
                logout_received = 0
                login_time = loginlogout.time
                continue
            if loginlogout.action == 'Logout':
                if login_received == 0:
                    continue
                logout_received = 1
                login_received = 0
                if logout_received != 1 :
                    continue
                logout_time = loginlogout.time
                
                if login_time and logout_time:
                    time_diff = logout_time - login_time
                    time += time_diff.seconds
        if time:
            time_hours = round((time/3600.00),2)

        for loginlogout in qs.order_by('-id'):
            if loginlogout.action == 'Logout':
                logout_timestamp = loginlogout.time
                break
        agent_loginlogout_data.append([agent['name'],login_timestamp,logout_timestamp,time_hours])
        
    return render_to_response('asterisk_api/agent_login_logout.html/',
                                {
                                    #'from_data': from_date,
                                    #'to_date': to_date,
                                    'logged_in': agent_loginlogout_data,
                                    'agents': agents,
                                    'selected_agent':get_agent,
                                },
                                context_instance = RequestContext(request))
        

                    

        
    



    
    
            


