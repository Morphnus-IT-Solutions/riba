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
from accounts.models import Account
from web.sbf_forms import SearchForm, FilterForm, SortForm, FileUploadForm
from catalog.models import *
from categories.models import *
from orders.models import *
from django.views.generic.list_detail import object_list
from web.views.order_view import * 
from utils.utils import *
import re
import math
from lists.models import List
import tempfile
import pyExcelerator
import xlrd
from datetime import datetime
from django.core.cache import cache
from django.template.defaultfilters import slugify

log = logging.getLogger('request')


#def promotions_detail(request):
#    tag = Tag.objects.filter(tag='promotions')
#    list = List.objects.filter(type="promotions", starts_on__lte=datetime.now(),ends_on__gte=datetime.now()).order_by('-id')
#    if not tag or not list:
#        raise Http404
#    tag = tag[0]
#    list = list[0]
#    ctxt['promotion'] = list
#    ctxt['title'] = list.title
#    if request.is_ajax():
#        return ctxt
#    return render_to_response('categories/category.html',ctxt,context_instance = RequestContext(request))

#def promotion_offer_detail(request, slug=None, id=None):
#    tag = Tag.objects.filter(tag='promotion_offer')
#    list = List.objects.filter(type="promotion_offer", starts_on__lte=datetime.now(),ends_on__gte=datetime.now()).order_by('-id')
#    if not tag or not list:
#        raise Http404
#    tag = tag[0]
#    list = list[0]
#    ctxt = search_browser_filter(request,**{'tag_ids':tag.id})
#    ctxt['promotion_offer'] = list
#    ctxt['title'] = list.title
#    if request.is_ajax():
#        return ctxt
#    return render_to_response('categories/category.html',ctxt,context_instance = RequestContext(request))

def get_products_by_ids(request, list):
    products = [item.sku.product for item in list.listitem_set.select_related(
        'sku', 'sku__product').filter(status='active')]
    product_ids = []
    productvariants = ProductVariant.objects.select_related('blueprint', 'variant').filter(variant__in=products)
    variant_product_map = {}
    for pv in productvariants:
        variant_product_map[pv.variant] = pv.blueprint
    for product in products:
        prod_id = product.id
        if product.type == 'variant':
            try:
                prod_id = variant_product_map[product].id
            except KeyError:
                continue
        if str(prod_id) not in product_ids:
            product_ids.append(str(prod_id))

    prod_ids = " OR ".join(product_ids)
    prod_ids = "(" + str(prod_ids) + ")"
    ctxt = search_browser_filter(request,**{'product':prod_ids})
    return ctxt


def create_tab(name, list):
    tab = BattleTab.objects.filter(list=list,name=name.upper())
    if not tab:
        tabs = BattleTab.objects.filter(list=list).order_by('-sort_order')
        if tabs:
            sort_order = tabs[0].sort_order + 1
        else:
            sort_order = 1
        tab = BattleTab()
        tab.name = name.upper()
        tab.list = list
        tab.sort_order = sort_order
        tab.save()

def update_listitem(request, item, list):
    listitem = ListItem()
    listitem.list = list
    try:
        sku = SellerRateChart.objects.get(article_id=item['article_no'], seller__client=request.client.client)
        listitem.sku = sku
        listitem.status = "active"    
        listitem.sequence = item['row_no']
        listitem.user_title = item['display_name']
        listitem.user_features = item['features']
        if 'start_time' in item:
            if item['start_time']:
                listitem.starts_on = datetime.strptime(item['start_time'],'%d-%m-%Y %I:%M:%S %p')
        if 'end_time' in item:
            if item['end_time']:
                listitem.ends_on = datetime.strptime(item['end_time'],'%d-%m-%Y %I:%M:%S %p')
        listitem.save()
        for i in range(len(item['filters'])):
            item['filter'] = str(item['filters'][i])
            if list.type != 'friday_deal':
                tags = item['filter'].split('+')
            else:
                tags = [item['filter']]
            for tag in tags:
                tag_1 = get_or_create_tag(tag)
                create_product_tag(sku.product, tag_1, list, item['tabs'][i], item['default_type'])
        item['extra_tagging'] = str(item['extra_tagging'])
    
        battle_tag = get_or_create_tag(list.type)
        create_product_tag(sku.product,battle_tag,list)
        if item['extra_tagging']:
            tags = item['extra_tagging'].split('+')
            for tag in tags:
                extra_tag = get_or_create_tag(tag)
                create_product_tag(sku.product,extra_tag,list)
    except SellerRateChart.DoesNotExist:
        log.info("Article %s not present." % item['article_no'])

    
def create_product_tag(product, tag, list, tab=None, default_type=None):
    try:
        product_tag = ProductTags.objects.get(tag=tag, product=product)
    except:
        product_tag = ProductTags()
        product_tag.product = product
        product_tag.tag = tag
        product_tag.type = list.type
    product_tag.starts_on = list.starts_on
    product_tag.ends_on = list.ends_on
    if default_type and default_type.strip().lower() in ['true', '1']:
        product_tag.show_default = True
    if tab:
        tab = BattleTab.objects.filter(name=tab['filter'].upper(),list=list)
        product_tag.tab = tab[0]
    product_tag.save()
    
def get_or_create_tag(name):
    name = str(name)
    name = format_string(name)
    expression = ['+', '"']
    tag_name = name
    #for exp in expression:
    #    tag_name = tag_name.replace(exp,'-')
    tag_name = tag_name.replace('"','-')
    tag_name = slugify(tag_name)
    tag = Tag.objects.filter(tag=tag_name)
    if not tag:
        tag = Tag()
        tag.display_name = name.upper()
        tag.tag = tag_name
        tag.save()
    else:
        tag = tag[0]
    return tag

def format_string(name):
    start = -1
    formatted_name = ''
    j = 0
    if name[j] == ' ':
        while name[j] == ' ':
            j += 1
        name = name[j:]
    j = len(name) - 1
    if name[j] == ' ':
        while name[j] == ' ':
            j -= 1
        name = name[:j+1]
    j = 0
    for i in range(len(name)):
        if name[i] == ' ':
            j = i
            while (j<len(name) and name[j] == ' '):
                j += 1
            j -= 1
        if i >= j:
            formatted_name += name[i]
    return formatted_name

def get_temporary_file_path():
    tf = tempfile.NamedTemporaryFile()
    path = tf.name
    tf.close()
    return path

def save_uploaded_file(f):
    path_to_save = get_temporary_file_path()
    fp = open(path_to_save, 'w')
    for chunk in f.chunks():
        fp.write(chunk)
    fp.close()
    return path_to_save
