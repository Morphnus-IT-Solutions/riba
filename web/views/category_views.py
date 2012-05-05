# Create your views here.
import datetime
import hashlib
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect
from django.template import RequestContext

from django.utils.safestring import mark_safe
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.core import serializers
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
from django.contrib.auth import authenticate, login
from django.utils import simplejson
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse

from web.forms import *
from catalog.models import *
from categories.models import *
from django.views.generic.list_detail import object_list
from utils.solrutils import *
from utils.utils import *
from web import search_form_default
import re
import math


log = logging.getLogger('request')

def category_home(request, slug, id):
    usr = request.user
    category =  Category.objects.get(pk=id)
    if category.slug != slug:
        return HttpResponsePermanentRedirect(reverse('category-home-url',None,kwargs={'slug':category.slug,'id':id}))
    queryDict = {'category':id,'q':''}
    return doSearch(request,id)


def search(request):
    return doSearch(request,'')

def doSearch(request,categoryId):
    if search_form_default.has_key(request.client.client.name):
        placeholder = {
                'placeholder' : search_form_default[request.client.client.name]
                }
    else:
        placeholder = {}

    search_form = SearchForm(**placeholder)

    category_form = CategoryForm()
    filter_form = CategoryFilterForm(None,None)
    products = []
    prods = []
    if categoryId:
        category = Category.objects.select_related('store').get(id=categoryId)
    else:
        category = None
    if request.GET and not categoryId:
        search_form = SearchForm(request.GET, **placeholder)
        category_form = CategoryForm(request.GET)
    else:
        if category and category.store:
            search_form = SearchForm({
                'store':category.store.id,
                'q':'',
                'category':category.id,
                }, **placeholder)
            category_form = CategoryForm({'store':category.store.id,'q':'','category':category.id})

    category_form.is_valid()
    search_form.is_valid()
    
    store = search_form.cleaned_data.get('store',None)
    q = search_form.cleaned_data['query']
    filter_queries = []
    if set(request.GET.keys()) - set(['q','store']):
        if category:
            filter_form = CategoryFilterForm(category,q,request.GET)
        else:
           
            filter_form = SearchFilterForm(q, request.GET)
        filter_form.is_valid()
        if hasattr(filter_form, 'cleaned_data'):
            filter_queries = filter_form.cleaned_data.get('filter_queries',[])
    else:
        if category:
            filter_form = CategoryFilterForm(category,q)
        else:
            filter_form = SearchFilterForm(q)
    params = {}
    
    if filter_queries:
        params['fq'] = filter_queries
    page_no = getOptInt(request.GET,'page',1)
    params['start'] = (page_no -1) * 20
    params['rows'] = 20
    pagination = None
    if not q and not category:
        q = '*:*'
    q += ' AND type: (variant OR normal)'
    filters = {'price':{'original':'priceasc','opposite':'pricedesc'},'popular':{'original':'relasc','opposite':'reldesc'}}
    if 'sort' in request.GET:
        sortType = request.GET['sort']
        if sortType == 'priceasc':
            sort = 'price'
            sort_order = 'asc'
            filters['price'] = {'original':'priceasc','opposite':'pricedesc'}
        elif sortType == 'pricedesc':
            sort = 'price'
            sort_order = 'desc'
            filters['price'] = {'original':'pricedesc','opposite':'priceasc'}
        elif sortType == 'relasc':
            sort = 'score'
            sort_order = 'asc'
            filters['popular'] = {'original':'relasc','opposite':'reldesc'}
        elif sortType == 'reldesc':
            sort = 'score'
            sort_order = 'desc'
            filters['popular'] = {'original':'reldesc','opposite':'relasc'}
        else:
            sort = 'score'
            sort_order = 'asc'
    else:
        sort = 'score'
        sort_order = 'asc'
    solr_result = solr_search(q, fields='id', highlight=None,
            score=True, sort=sort, sort_order=sort_order, **params)
    ids = [doc['id'] for doc in solr_result.results]
    product_list = Product.objects.filter(id__in = ids)
    pids = {}
    for p in product_list:
        pids[p.id] = p

    p_list = []
    for id in ids:
        if id in pids:
            p_list.append(pids[id])
    total_pages = int(math.ceil(int(solr_result.numFound)/20 + 1))
    total_results = int(solr_result.numFound)
    base_url = request.get_full_path()

    page_pattern = re.compile('[&?]page=\d+')
    base_url = page_pattern.sub('',base_url)
    if base_url.find('?') == -1:
        base_url = base_url + '?'
    else:
        base_url = base_url + '&'
    pagination = getPaginationContext(page_no, total_pages, base_url)
    pagination['result_from'] = (page_no-1) * 20 + 1
    pagination['result_to'] = ternary(page_no*20 > total_results, total_results, page_no*20)

    try:
        page = int(request.GET.get('page','1'))
    except ValueError:
        page = 1
    prods = []
    for product in p_list:
        images = ProductImage.objects.filter(product=product)
        blueprint = product
        try:
            sellerRateChart = SellerRateChart.objects.get(product=product,is_prefered=True)
        except SellerRateChart.DoesNotExist:
            log.error('Error finding preferred ratechart for %s' % product.title)
            continue

        if images:
            thumbnail = images[0].thumbnail_image.name
        else:
            thumbnail = None

        prods.append({'product':product,'blueprint':blueprint, 'image':thumbnail,'rateChart':sellerRateChart})
        
    return render_to_response("categories/category.html", {
                "search_form": search_form,
                "category_form":category_form,
                "filter_form": filter_form,
                "products": prods,
                "total_results": total_results,
                "total_pages": total_pages,
                "prods":products,
                "base_url":base_url,
                "pagination":pagination,
                "filters":filters,
                "store":store
            },
            context_instance=RequestContext(request))

