# Create your views here.
import datetime
import hashlib
import logging
import time

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect
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
from django.core.cache import cache
from web.sbf_forms import FilterForm
from web.forms import *
from catalog.models import *
from categories.models import *
from orders.models import *

def store_home(request, slug, id):
    storeid = id
    store = Store.objects.get(id=storeid)
    inits = {'store':store}
    filter_form = FilterForm(request,inits)
    my_key = '%s#%s' % (storeid, request.client.client.id)
    store_home_dict = cache.get(my_key)
    if not store_home_dict:
        store = Store.objects.get(id=storeid)
        categs = Category.objects.filter(store=store)
        storetemp={}
        prodcount=0
        len_categ={}
        len_brand={}

        for categ in categs:
            tmp_length = SellerRateChart.objects.filter(product__category=categ,product__status='active',seller__client=request.client.client).count()
            if tmp_length:
                len_categ[categ] = tmp_length

        topdealsproductitem = retrieveTopdealsProduct(storeid, 0)
        latestproductitem = retrieveLatestProduct(storeid, 0)
        popularproductitem = retrievePopularProduct(storeid, 0)
        brands = set(Brand.objects.filter(product__category__store__id = storeid))
        for brand in brands:
            tmp_length = SellerRateChart.objects.filter(product__brand=brand,product__status='active',seller__client=request.client.client).count()
            if tmp_length:
                len_brand[brand] = tmp_length
        store_home_dict = {
            'products':topdealsproductitem,
            'filter_form':filter_form,
            'storetemp':storetemp,
            'store':store,
            'categs':categs,
            'prodcount':prodcount,
            'storeid':storeid,
            'len_categ':len_categ,
            'len_brand':len_brand,
            'popularproductitem':popularproductitem,
            'latestproductitem':latestproductitem,
            'topdealsproductitem':topdealsproductitem}
        cache.set(my_key, store_home_dict, 21600)

    return render_to_response('stores/store.html',
        store_home_dict,
        context_instance=RequestContext(request))

def retrieveNextProduct(request):
    prodcount = int(request.POST['prodcount'])
    storeid = request.POST['storeid']
    name_list = request.POST['name_list']
    some_or_all = request.POST['some_or_all']
    my_key = '%s#%s#%s#%s' % (prodcount, storeid, name_list, some_or_all)
    next_prod_dict = cache.get(my_key)
    if not next_prod_dict:
        next_prod_list = {}
        store = Store.objects.get(id=storeid)
        categs = Category.objects.filter(store=store)
        storetemp={}
        if name_list == 'popular':
            if some_or_all == 'some':
                next_prod_list = retrievePopularProduct(storeid,prodcount+4)
            elif some_or_all == 'back':
                next_prod_list = retrievePopularProduct(storeid,prodcount-4)

        if name_list == 'latest':
            if some_or_all == 'some':
                next_prod_list = retrieveLatestProduct(storeid,prodcount+4)
            elif some_or_all == 'back':
                next_prod_list = retrieveLatestProduct(storeid,prodcount-4)

        if name_list == 'top_deals':
            if some_or_all == 'some':
                next_prod_list = retrieveTopdealsProduct(storeid,prodcount+4)
            elif some_or_all == 'back':
                next_prod_list = retrieveTopdealsProduct(storeid,prodcount-4)

        if (next_prod_list):
            next_prod_dict = {'products':next_prod_list, 'list_remaining':True}
        else:
            next_prod_dict = {'list_remaining':False}

        cache.set(my_key, next_prod_dict, 21600)

    if 'products' in next_prod_dict:
        html = 'stores/popular_products.html'
    else:
        html = 'stores/store.html'

    return render_to_response(html,
        next_prod_dict,
        context_instance=RequestContext(request))

def retrievePopularProduct(storeid, ProdCount):
    popularproductlist = []
    productlist = Product.objects.filter(category__store__id = storeid, status="active").order_by('-view_count')[ProdCount:ProdCount+4]
    popularproductlist = productlist
    popularproductitems = []
    for prod in popularproductlist:
        try:
            sellerRateChart = SellerRateChart.objects.get(product=prod,is_prefered=True)
        except SellerRateChart.DoesNotExist:
            log.error('Error finding preferred ratechart for %s' % prod.title)
            continue
        popularproductitems.append({'product':prod,'rateChart':sellerRateChart})
    return popularproductitems


def retrieveTopdealsProduct(storeid, ProdCount):
    topdealsproductlist = []
    topdealsproductitems = []
    productlist = Product.objects.filter(category__store__id = storeid, status="active").order_by('-confirmed_order_count')[ProdCount:ProdCount+4]
    topdealsproductlist = productlist
    for prod in topdealsproductlist:
        try:
            sellerRateChart = SellerRateChart.objects.get(product=prod,is_prefered=True)
        except SellerRateChart.DoesNotExist:
            log.error('Error finding preferred ratechart for %s' % prod.title)
            continue
        topdealsproductitems.append({'product':prod,'rateChart':sellerRateChart})
    return topdealsproductitems

def retrieveLatestProduct(storeid, ProdCount):
    latestproductlist = []
    productlist = Product.objects.filter(category__store__id = storeid, status="active").order_by('-created_on')[ProdCount:ProdCount+4]
    latestproductlist = productlist
    latestproductitems = []
    for prod in latestproductlist:
        try:
            sellerRateChart = SellerRateChart.objects.get(product=prod,is_prefered=True)
        except SellerRateChart.DoesNotExist:
            log.error('Error finding preferred ratechart for %s' % prod.title)
            continue
        latestproductitems.append({'product':prod,'rateChart':sellerRateChart})
    return latestproductitems


def uniqList(input):
    output = []
    for x in input:
        if x not in output:
            output.append(x)
    return output
