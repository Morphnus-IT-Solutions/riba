import logging

from django.conf import settings
from datetime import datetime
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect
from django.template import RequestContext
import re
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
from accounts.models import Account, Client, ClientDomain
from lists.models import List
from web.forms import PriceCompareForm
from spider import crawl
from catalog.models import SellerRateChart, Product
from decimal import Decimal

def fbdeals(request):
    context = {}
    products = []
    context['products'] = products
    return render_to_response(
        "pricespider/results.html",
        context,
        context_instance = RequestContext(request))

def compare(request):
    context = {}
    product = {}
    compare_form = PriceCompareForm()
    good_to_go = True
    if request.method == "POST":
        compare_form = PriceCompareForm(request.POST)
        if compare_form.is_valid():
            q = compare_form.cleaned_data['search_for'].strip()
            rc = None
            if re.compile('^\d+$').match(q):
                try:
                    rc = SellerRateChart.objects.get(sku=q,
                        seller__client = request.client.client)
                except SellerRateChart.DoesNotExist:
                    pass
            else:
                rc = SellerRateChart.objects.filter(
                    product__title__icontains = q,
                    seller__client = request.client.client)[:1]
                if rc:
                    rc = rc[0]
                    q = '%s %s' % (rc.product.brand.name, rc.product.model)
            if rc:
                our_title = rc.product.title
                our_price = rc.get_price_for_domain(
                    request.client)['offer_price']
                our_link = rc.product.url()
            else:
                our_title = ''
                our_price = ''
                our_link = ''
            product = {
                'our_title': our_title,
                'our_price': str(our_price).split('.')[0],
                'link': our_link, 
            }

            comparisions = crawl.get_compare_results(q)
            for comparision in comparisions:
                if Decimal(comparision['price']) < our_price:
                    comparision['colour_code'] = 'yellow'
                if Decimal(comparision['price']) == our_price:
                    comparision['colour_code'] = 'white'
                if Decimal(comparision['price']) > our_price:
                    comparision['colour_code'] = 'white'
                if (Decimal(comparision['price'])/our_price) * 100 < 50:
                    comparision['flags'] = 'too_low'
                if comparision.get('flags','') != 'too_low':
                    if comparision.get('colour_code','white') == 'yellow':
                        good_to_go = False
                    
            product['comparisions'] = comparisions

    context['product'] = product
    context['form'] = compare_form
    context['good_to_go'] = good_to_go
    return render_to_response(
        "pricespider/results.html",
        context,
        context_instance = RequestContext(request))
