import re
import math
from datetime import datetime,timedelta
from django.db import models
from django.db.models import Max,Sum,Count,Avg
from django.db.models import Q
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect
from analytics.models import *
from django.template import RequestContext
from django.conf import settings
from django.shortcuts import render_to_response, get_object_or_404
from decimal import *


def check_dates(request):
    from_date = request.GET.get('from','')
    to_date = request.GET.get('to','')
    errors = ""
    if from_date== None or from_date == "" or to_date==None or to_date== "":
        errors = "Please select date range"
        return False,errors

    if from_date and to_date:
        from_date = datetime.strptime(from_date,'%m/%d/%Y').date()
        to_date = datetime.strptime(to_date,'%m/%d/%Y').date()
        if to_date < from_date:
            errors = "Please Select a Valid Date Range"
            return False,errors
        else: return True,from_date,to_date



def search_trend(request):
    domains = SearchLog.objects.exclude(domain='').values('domain').distinct() 
    params=request.GET
    if len(params) >= 1:
        date_check=check_dates(request)
        if not date_check[0]:
            return render_to_response("analytics/search_trend.html",{'domains':domains,'errors':date_check[1]},RequestContext(request))
        else:
            from_date,to_date=date_check[1],date_check[2]
        to=to_date + timedelta(days=1)
        get_domain=request.GET.get('domaindropdown','')
        
        qs=SearchLog.objects.filter(Q(date__gte = from_date) & Q(date__lte = to) & Q(domain = get_domain)).exclude(keyword='').exclude(user_agent__contains='bot')
        searches=qs.values('keyword').annotate(avg_results=Avg('total_results'),total_searches=Count('keyword'))
        for search in searches: round(search['avg_results'],2)
        
        url=request.get_full_path()
        pattern=re.compile('[&?]sort=[-]{0,1}\d+')
        base_url=pattern.sub('',url)
        
        
        sort=request.GET.get('sort','-3')
        if sort == '1': searches=sorted(searches,key=lambda n:n['keyword'] )
        if sort == '2':   searches=sorted(searches,key=lambda n:n['total_searches'] )
        if sort == '3':   searches=sorted(searches,key=lambda n:n['avg_results'] )
        if sort == '-1':  searches=sorted(searches,key=lambda n:n['keyword'],reverse=True )
        if sort == '-2':  searches=sorted(searches,key=lambda n:n['total_searches'],reverse=True )
        if sort == '-3':  searches=sorted(searches,key=lambda n:n['avg_results'],reverse=True )

        return render_to_response('analytics/search_trend.html',
                                {
                                    'selected_domain':get_domain,
                                    'domains':domains,
                                    'search_list':searches,
                                    'sort':sort,
                                    'base_url':base_url,
                                    'from_date':from_date,
                                    'to_date':to_date
                                },context_instance = RequestContext(request))
    return render_to_response('analytics/search_trend.html',
                                {
                                    'domains':domains,
                                },context_instance = RequestContext(request))

def search_score(request):
    domains = SearchLog.objects.exclude(domain='').values('domain').distinct() 
    params=request.GET
    if len(params) >= 1:
        date_check=check_dates(request)
        if not date_check[0]:
            return render_to_response("analytics/search_score.html",{'domains':domains,'errors':date_check[1]},RequestContext(request))
        else:
            from_date,to_date=date_check[1],date_check[2]
        to=to_date + timedelta(days=1)
        
        get_domain=request.GET.get('domaindropdown','')
        qs=SearchLog.objects.filter(Q(date__gte = from_date) & Q(date__lte = to)& Q(domain=get_domain)).exclude(keyword='').exclude(user_agent__contains='bot')
        searches=qs.values('keyword').annotate(avg_results=Avg('total_results'),total_searches=Count('keyword'))
        
        search_list=[]
        wanted_score=0
        for searchlog in qs:
            for search_dict in searches: 
                if search_dict['keyword'] == searchlog.keyword:
                    if int(searchlog.total_results):
                        try:
                            search_dict['division'] += Decimal(1)/Decimal(searchlog.total_results)
                        except:
                            search_dict['division'] = Decimal(1)/Decimal(searchlog.total_results)
                    else:
                        try:
                            search_dict['division'] += 0
                        except:
                            search_dict['division'] = 0
        
        for search in searches:
            try:
                if search['total_searches']:
                    search['wanted_score'] = round(search['division']/Decimal(search['total_searches']),2)
                else:
                    search['wanted_score']=0
            except:
                if search['total_searches']:
                    search['wanted_score'] = round(search['division']/Decimal(search['total_searches']),2)
                else:
                    search['wanted_score']=0

        for search in searches: round(search['avg_results'],2)
            
        url=request.get_full_path()
        pattern=re.compile('[&?]sort=[-]{0,1}\d+')
        base_url=pattern.sub('',url)
        
        
        sort=request.GET.get('sort','-3')
        if sort == '1': searches=sorted(searches,key=lambda n:n['keyword'] )
        if sort == '2':   searches=sorted(searches,key=lambda n:n['wanted_score'] )
        if sort == '3':   searches=sorted(searches,key=lambda n:n['avg_results'] )
        if sort == '-1':  searches=sorted(searches,key=lambda n:n['keyword'],reverse=True )
        if sort == '-2':  searches=sorted(searches,key=lambda n:n['wanted_score'],reverse=True )
        if sort == '-3':  searches=sorted(searches,key=lambda n:n['avg_results'],reverse=True )
        
        return render_to_response('analytics/search_score.html',
                                {
                                    'selected_domain':get_domain,
                                    'domains':domains,
                                    'search_list':searches,
                                    'sort':sort,
                                    'base_url':base_url,
                                    'from_date':from_date,
                                    'to_date':to_date
                                },context_instance = RequestContext(request))
    return render_to_response("analytics/search_score.html",{'domains':domains},RequestContext(request))


    
    
