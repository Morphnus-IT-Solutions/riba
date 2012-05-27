# Create your views here.
from django.http import HttpResponse
from django.template import RequestContext
from django.shortcuts import render_to_response
from catalog.models import *
from django.contrib.auth.decorators import login_required
from accounts.models import Account
from utils import *
from ccm.models import Agent
from web.views.user_views import *
from web.views.home import futurebazaar_home_page_context, get_banners, ezoneonline_home_page_context, old_ezoneonline_home_page_context
import random

@login_required
def dump_call_info(request):
    dni = request.call['dni']
    id = request.call['id']
    phone = request.call['cli']
    ctxt = {}
    if utils.is_future_ecom(request.client.client):
        ctxt = futurebazaar_home_page_context(request)
    elif utils.is_old_ezoneonline(request.client.client):
        ctxt = old_ezoneonline_home_page_context(request)
    elif utils.is_ezoneonline(request.client.client):
        ctxt = ezoneonline_home_page_context(request)
    elif utils.is_holii_client(request.client.client):
        ctxt = {'banners' : get_banners(request)}
    try:
        account = Account.objects.get(dni=dni)
    except Account.DoesNotExist:
        account = None
    ctxt['account'] = account
    return render_to_response(request.client.custom_home_page,
        ctxt,
        context_instance=RequestContext(request))

def cc_agent_performance(request):
    def median(iterable):
        n = len(iterable)
        iterable = sorted(iterable)
        if n % 2:
            return iterable[n/2]
        return (iterable[n/2-1] + iterable[n/2])/2

    def get_performance(request):
        try:
            agent = Agent.objects.get(user = request.user)
            #sales = [ag.get_daily_sales() for ag in all_agents]
            #total_sales = sum(sales)
            #highest_sales = max(sales)
            #avg_sales = "%.02f" % (median(sales))
            return {'cc_agent' : agent,
                    'total_sales' : '0', #total_sales,
                    'avg_sales' : '0', #avg_sales,
                    'highest_sales' : '0'} #highest_sales}
        except:
            raise
        return {'cc_agent' : None,
                'total_sales' : 0,
                'avg_sales' : 0,
                'highest_sales' : 0
                }

    if utils.is_cc(request) or request.is_auth:
        if not 'agent_performance' in request.session:
            request.session['agent_performance'] = get_performance(request)
        return request.session['agent_performance']
    if 'agent_performance' in request.session:
        del request.session['agent_performance']
    return {}

@login_required
def start_soft_call(request):
    ctxt = None
    if utils.is_future_ecom(request.client.client):
        if utils.is_cc(request):
            if request.call['id']:
                user,profile = user_context(request)
        ctxt = futurebazaar_home_page_context(request)
        return render_to_response(request.client.custom_home_page,
            ctxt,
            context_instance=RequestContext(request))
    elif utils.is_old_ezoneonline(request.client.client):
        ctxt = old_ezoneonline_home_page_context(request.client.client)
        return render_to_response(request.client.custom_home_page,
            ctxt,
            context_instance=RequestContext(request))
    elif utils.is_ezoneonline(request.client.client):
        ctxt = ezoneonline_home_page_context(request.client.client)
        return render_to_response(request.client.custom_home_page,
            ctxt,
            context_instance=RequestContext(request))
    elif utils.is_holii_client(request.client.client):
        ctxt = {'banners' : get_banners(request)}
        return render_to_response(request.client.custom_home_page, 
                                  ctxt, 
                                  context_instance=RequestContext(request))
    return render_to_response('web/home/home.html',
        None,
        context_instance=RequestContext(request))
