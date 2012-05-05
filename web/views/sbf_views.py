from datetime import datetime
import hashlib
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect, Http404
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
from web.sbf_forms import SearchForm, FilterForm, SortForm
from catalog.models import *
from categories.models import *
from django.views.generic.list_detail import object_list
from utils.solrutils import *
from utils.utils import *
from lists.models import *
from decimal import Decimal
import re
import math
log = logging.getLogger('request')
search_log = logging.getLogger('search')

def shop_by_price(request):    
    params = request.GET
    price = {}
    price['min'] = str(params.get('min_p','0'))
    price['max'] = str(params.get('max_p','*'))
    price['label'] = "offerprice_%s" % request.client.id
    ctxt = search_browser_filter(request, **{'price':price})
    if request.is_ajax():
        return ctxt
    html_page = 'categories/category.html'
    if not ctxt.get('products',[]):
        html_page = 'categories/zero_result.html'

    return render_to_response(html_page,
            ctxt,
            context_instance = RequestContext(request))

def shop_by_discount(request):
    params = request.GET
    discount = {}
    discount['min'] = str(params.get('min_d','0'))
    discount['max'] = str(params.get('max_d','*'))
    discount['label'] = "discount_%s" % request.client.id
    ctxt = search_browser_filter(request, **{'discount':discount})
    if request.is_ajax():
        return ctxt
    html_page = 'categories/category.html'
    if not ctxt.get('products',[]):
        html_page = 'categories/zero_result.html'

    return render_to_response(html_page,
            ctxt,
            context_instance = RequestContext(request))

def category_home(request, slug, id):
    if is_future_ecom(request.client.client):
        old_new_cat_map = getattr(settings, 'OLD_NEW_CATEGORY_MAP', '')
        if old_new_cat_map and long(id) in old_new_cat_map:
            return HttpResponsePermanentRedirect(
                    reverse('category-home-url', 
                    None,
                    kwargs={'slug':slug,'id':old_new_cat_map[long(id)]})
                )
    usr = request.user
    try:
        category =  Category.objects.get(pk=id)
    except Category.DoesNotExist:
        raise Http404
    if category.slug != slug:
        return HttpResponsePermanentRedirect(reverse('category-home-url',None,kwargs={'slug':category.slug,'id':id}))
    show_compare = True
    if is_future_ecom(request.client.client):
        show_compare = category.show_compare
    ctxt = ''#search_browser_filter(request, **{'category':category, 'show_compare':show_compare})
    ctxt['is_category_page'] = True
    if request.is_ajax():
        return ctxt
    html_page = 'categories/category.html'
    if not ctxt['products']:
        html_page = 'categories/zero_result.html'
    ctxt['show_compare'] = show_compare
    leaf_category = not(CategoryGraph.objects.filter(parent=category).exists())
    category_graph = CategoryGraph.objects.filter(category=category)
    ctxt['leaf_category'] = leaf_category
    ctxt['category'] = category
    ctxt['show_price_filter'] = True if category_graph and category_graph[0].parent else False
    ctxt['title'] = category.name
    return render_to_response(html_page,
            ctxt,
            context_instance = RequestContext(request))

def category_compare(request, slug, id, id1=None, id2=None, id3=None, id4=None):
    cat_id = id
    category = Category.objects.get(pk=cat_id)
    if category.slug != slug:
        return HttpResponsePermanentRedirect(reverse('category-home-url',None,kwargs={'slug':category.slug,'id':id}))
    ids = []
    if id1:
        ids.append(long(id1))
    if id2:
        ids.append(long(id2))
    if id3:
        ids.append(long(id3))
    if id4:
        ids.append(long(id4))
    product_info = [] 
    product_info = create_context_for_search_results(ids, request)

    products = Product.objects.filter(id__in=ids)
    product = products[0]
    feature_grp = FeatureGroup.objects.filter(product_type = product.product_type).order_by('sort_order')
    datas = []
    for grp in feature_grp:
        data = []
        features = Feature.objects.filter(product_type = product.product_type, group = grp ).order_by('sort_order')
        for feature_type in features:
            values = []
            for prod_id in ids:
                try:
                    feature = ProductFeatures.objects.get(product__id = prod_id, feature = feature_type)
                except:
                    feature = None
                content = ''
                if feature:
                    if feature.feature.type == 'number':
                        try:
                            content = ("%.1f" % feature.value).replace('.0','') + ' ' + feature.feature.unit.name
                        except:
                            content = ("%.1f" % feature.value).replace('.0','')
                    elif feature.feature.type == 'text':
                        try:
                            content = feature.data
                        except:
                            pass
                    elif feature.feature.type == 'boolean':
                        if feature.bool:
                            content = 'Yes'
                        else:
                            content = 'No'
                values.append(content)
            flag = False
            is_different = False
            val = []
            for value in values:
                if value:
                    flag = True
                val.append(value.encode('ascii', 'ignore').lower())
            if val and len(set(val)) > 1:
                is_different = True
            if flag:
                feature_info = dict(name=feature_type.name,values=values,is_different=is_different)
                data.append(feature_info)
        group = {}
        group['name'] = grp.name
        group['features'] = data
        if data:
            datas.append(group)
    return render_to_response("categories/category_compare.html",
        {
            'product_info':product_info,
            'datas':datas,
            'category':category
        },
            context_instance = RequestContext(request))

def brand_home(request, slug, id):
    brand = Brand.objects.get(pk=id)
    client = request.client.client
 
    if is_holii_client(request.client.client):
        products = Product.objects.filter(brand = brand, category__client = client, sellerratechart__stock_status = 'instock')
        ctxt = {'brand'    : brand,
                'products' : products
               }
        return render_to_response('brands/brand.html',
                                   ctxt,
                                   context_instance = RequestContext(request)
                                 )
    else:
        if brand.slug != slug:
            return HttpResponsePermanentRedirect(reverse('brand-home-url',None,kwargs={'slug':brand.slug,'id':id}))
        ctxt = search_browser_filter(request, **{'brand':brand})
        if request.is_ajax():
            return ctxt
        html_page = 'categories/category.html'
        if not ctxt['products']:
            html_page = 'categories/zero_result.html'
        ctxt['title'] = brand.name
        ctxt['is_brand_page'] = True
        return render_to_response(html_page,
                                  ctxt,
                                  context_instance = RequestContext(request))


def search(request):
    ctxt = search_browser_filter(request)
    if request.is_ajax():
        return ctxt
    html_page = 'categories/category.html'
    if not ctxt.get('products', []):
        html_page = 'categories/zero_result.html'
        try:
            if not ctxt.get('spell_suggestion', []):
                html_page = 'categories/zero_result.html'
            else:
                html_page = 'categories/search_suggestion.html'
        except:
            pass
    return render_to_response(html_page,
            ctxt,
            context_instance = RequestContext(request))

def search_tag(request,tag,tag_filter=None):
    battle = None
    if tag == "battle":
        battle = List.objects.filter(type="battle",is_featured=True,starts_on__lte=datetime.now(),ends_on__gte=datetime.now())
        if battle:
            battle = battle[0]
        else:
           battle = None
        if not battle:
            raise Http404
    if tag_filter:
        tag = '(%s AND %s)' %(tag,tag_filter)
    ctxt = search_browser_filter(request,**{'tag':tag})
    tabs = Tab.objects.filter(list__type = 'battle').order_by('sort_order')
    tags = ProductTags.objects.filter(type='battle')
    tag_ids = tags.values('tag').distinct()
    total_pages = range(1,ctxt['total_pages']+1)
    prods2 = []
    prods = ctxt['products']
    items_in_sec1 = 4
    if len(prods)>items_in_sec1:
        length1 = items_in_sec1
        for len2 in range(items_in_sec1,len(prods)):
            prods2.append(prods[len2])
    else:
        length1 = len(prods)
    prods1 = prods[:length1]
    search_url = ctxt['base_url']
    if tag_filter:
        search_url = '/search/t/battle/'
    else:
        search_url = search_url[:-1]
    tag_info = []
    for tag in tag_ids:
        tag = ProductTags.objects.get(id=tag['tag'])
        info = {}
        q = 'tags: (%s AND battle) AND currency:inr' % tag.tag.tag
        solr_result = solr_search(q, fields='id',request=request)
        ids = [int(doc['id']) for doc in solr_result.results]
        info['tag'] = tag
        info['count'] = len(ids)
        tag_info.append(info)
    return render_to_response("categories/battle.html",
            {
                "total_results": ctxt['total_results'],
                "total_pages": total_pages,
                "base_url": ctxt['base_url'],
                "pagination": ctxt['pagination'],
                "filters": ctxt['filters'],
                "tabs":tabs,
                "tags":tag_info,
                "prods1":prods1,
                "prods2":prods2,
                "search_url":search_url,
                "battle":battle
            },
            context_instance = RequestContext(request))

def search_browser_filter(request, **kwargs):
    category = kwargs.get('category',None)
    brand = kwargs.get('brand',None)
    tag = kwargs.get('tag',None)
    tag_ids = kwargs.get('tag_ids',None)
    product = kwargs.get('product',None)
    price = kwargs.get('price',None)
    discount = kwargs.get('discount',None)
    clearance_sale = kwargs.get('clearance_sale',False)
    tab = kwargs.get('tab',None)
    deal_type = kwargs.get('deal_type',None)

    # search form shown in the header
    search_form = SearchForm(request)
    # single form to manage all filters
    filter_from = None
    prods = []
    products = []
    total_pages = None
    total_results = None
    base_url = ''
    pagination = None
    store = None
    filters = None
    org_sort = None
    items_per_page = settings.ITEMS_PER_PAGE
    ctxt = None
    if (request.method == 'GET' and request.GET) or category or brand or tag or product or clearance_sale or tag_ids or tab:
        search_form = SearchForm(request,request.GET)
        search_form.is_valid()
        inits = {'category': category, 'brand': brand, 'tags':tag, 'product':product, 'price':price, 'discount':discount, 'clearance_sale':clearance_sale,\
                    'query': search_form.cleaned_data['query'], 'tag_ids':tag_ids, 'tab':tab}
        if set(request.GET.keys()) - set(['q','store','page','sort']):
            filter_form = FilterForm(request,inits, request.GET)
        else:
            inits['q'] = request.GET.get('q','')
            inits['store'] = request.GET.get('store','')
            filter_form = FilterForm(request,inits)
        filter_form.is_valid()
        q = search_form.cleaned_data['query']
        if category:
            q = 'client_id: %s AND category_id: %s' % (request.client.client.id,category.id)
        if brand:
            q = 'client_id: %s AND brand_id: %s' % (request.client.client.id,brand.id)
        if tag:
            q = 'client_id: %s AND tags: %s' % (request.client.client.id,tag)
        if tab:
            q = 'client_id: %s AND tab_id: %s' % (request.client.client.id,tab)
        if product:
            q = 'client_id: %s AND id: %s' % (request.client.client.id,product)
        if tag_ids:
            q = 'client_id: %s AND tag_id: %s' % (request.client.client.id, tag_ids)

        sort = request.GET.get('sort','score')
        org_sort = sort
        filter_queries = None
        
        if hasattr(filter_form, 'cleaned_data'):
            filter_queries = filter_form.cleaned_data.get('filter_queries',[])
        page_no = getOptInt(request.GET,'page',1)
        if 'perpage' in request.GET:
            items_per_page = request.GET['perpage']
        if tag == 'battle':
            items_per_page = 12
        items_per_page = min(int(items_per_page), 60)
        params = {}
        params['start'] = (page_no -1) * items_per_page
        params['rows'] = items_per_page
        pagination = None
        price_label = 'offerprice_%s' % request.client.id
        discount_label = 'discount_%s' % request.client.id
        filters = {'price':{'original':'priceasc','opposite':'pricedesc'},'popular':{'original':'reldesc','opposite':'reldesc'}, 'discount':{'original':'discountdesc','opposite':'discountdesc'}}
        
        if sort == 'priceasc':
            sort = price_label
            sort_order = 'asc'
            filters['price'] = {'original':'priceasc','opposite':'pricedesc'}
        elif sort == 'pricedesc':
            sort = price_label
            sort_order = 'desc'
            filters['price'] = {'original':'pricedesc','opposite':'priceasc'}
        elif sort == 'reldesc':
            sort = 'score'
            sort_order = 'desc'
            filters['popular'] = {'original':'reldesc','opposite':'reldesc'}
        elif sort == 'discountdesc':
            sort = discount_label
            sort_order = 'desc'
            filters['discount'] = {'original':'discountdesc','opposite':'discountdesc'}
        else:
            sort = 'score'
            sort_order = 'desc'
        org_sort = "reldesc" if org_sort == 'score' else org_sort
        hidden_data = []
        if price:
            if not filter_queries:
                filter_queries = []
                filter_queries.append('%s:[%s TO %s] AND category_id:[* TO *] AND brand_id:[* TO *]' % (price['label'], price['min'], price['max']))
            hidden_data.append(['min_p', price['min']])
            hidden_data.append(['max_p', price['max']])

        if discount:
            if not filter_queries:
                filter_queries = []
                filter_queries.append('%s:[%s TO %s] AND category_id:[* TO *] AND brand_id:[* TO *]' % (discount['label'], discount['min'], discount['max']))
            hidden_data.append(['min_d', discount['min']])
            hidden_data.append(['max_d', discount['max']])
        if clearance_sale:
            tag_ids = clearance_sale['format_tag_ids']
            if not filter_queries:
                filter_queries = []
            solr_tag_ids = None
            solr_tag_ids = (" OR ").join(str(x) for x in tag_ids)
            if solr_tag_ids:
                filter_queries.append('category_id:[* TO *] AND brand_id:[* TO *] AND tag_id:(%s)' % (solr_tag_ids))
            if clearance_sale["filter"]:
                q += " AND %s_id:%s" % (clearance_sale["filter"], clearance_sale["filter_id"])
        if filter_queries:
            params['fq'] = filter_queries
        if not is_cc(request):
            q = '%s AND currency:inr' % q

        if is_future_ecom(request.client.client) or is_ezoneonline(request.client.client):
            q = '%s AND -type:variant' % q
        elif is_holii_client(request.client.client) or is_future_gc(request.client.client):
            q = '%s AND -type:variable' % q

        search_log.info('solr_query %s' % q)
        total_results = 0
        try:
            if deal_type == 'new_arrivals':
                if sort == 'score':
                    sort = 'timestamp'
                    sort_order = 'desc'
                solr_result = solr_search(q, fields='id', highlight=None, boost_query='',
                        score=True, sort=sort, sort_order=sort_order, request=request, **params)
            else:
                solr_result = solr_search(q, fields='id', highlight=None,
                        score=True, sort=sort, sort_order=sort_order, request=request, **params)
            total_results = int(solr_result.numFound)
        except solr.SolrException,e:
            search_log.exception("Exception in solr search query: %s" % q)
        if total_results > 0:
            ids = [int(doc['id']) for doc in solr_result.results]
            search_log.info('product ids %s' % ids)

            products_context = create_context_for_search_results(ids, request)

            total_pages = int(math.ceil(Decimal(solr_result.numFound)/Decimal(items_per_page)))
            profile = None
            if is_cc(request):
                id = request.call['id']
                if id in request.session:
                    profile = request.session[id].get('profile',None)
            else:
                if request.user.is_authenticated():
                    try:
                        profile = request.user.get_profile()
                    except:
                        pass
            if profile:
                pr_id = profile.id
            else:
                pr_id = None
            search_q = request.GET.get('q',None)
            search_log.info('User: %s, Domain: %s, User Agent: %s, Keywords: %s, total_results: %s' % (
                pr_id,request.META['HTTP_HOST'], request.META.get(
                    'HTTP_USER_AGENT', 'No-User-Agent'), search_q, total_results))
            base_url = request.get_full_path()
            if search_q:

                profile = None
                if is_cc(request):
                    id = request.call['id']
                    if id in request.session:
                        profile = request.session[id].get('profile',None)
                else:
                    if request.user.is_authenticated():
                        try:
                            profile = request.user.get_profile()
                        except:
                            pass
                if profile:
                    pr_id = profile.id
                else:
                    pr_id = None
                search_log.info('User: %s, Domain: %s, User Agent: %s, Keywords: %s, total_results: %s' % (
                    pr_id,request.META['HTTP_HOST'], request.META.get(
                        'HTTP_USER_AGENT', 'No-User-Agent'), search_q, total_results))

            base_url = request.get_full_path()

            page_pattern = re.compile('[&?]page=\d+')
            base_url = page_pattern.sub('',base_url)
            page_pattern = re.compile('[&?]per_page=\d+')
            base_url = page_pattern.sub('',base_url)
            base_url = base_url.replace("/&", "/?")
            if base_url.find('?') == -1:
                base_url = base_url + '?'
            else:
                base_url = base_url + '&'
            pagination = getPaginationContext(page_no, total_pages, base_url)
            pagination['result_from'] = (page_no-1) * items_per_page + 1
            pagination['result_to'] = ternary(page_no*items_per_page > total_results, total_results, page_no*items_per_page)

            try:
                page = int(request.GET.get('page','1'))
            except ValueError:
                page = 1

            prods = []
            for product_context in products_context:
                if 'rate_chart' not in product_context:
                    continue
                else:
                    # Adding extra keys so that templates don't break
                    product_context['rateChart'] = product_context['rate_chart']
                    product_context['priceInfo'] = product_context['price_info']
                    product_context['blueprint'] = product_context['product']
                prods.append(product_context)
            remaining_items = total_results - pagination['result_to']
            pagination['items_per_page'] = items_per_page
            requested_category_id = request.GET.get('c',None)
            leaf_category = False
            category = None
            show_price_filter = False
            show_compare = False
            if requested_category_id:
                show_price_filter = True
                try:
                    category = Category.objects.get(id=requested_category_id)
                    leaf_category = not(CategoryGraph.objects.filter(parent=category).exists())
                    show_compare = category.show_compare
                except:
                    pass
            hc_count = 0
            if 'hc'in filter_form.fields:
                hc_count = filter_form.fields['hc'].choices.__len__()
            ctxt = {
                        "search_form": search_form,
                        "filter_form": filter_form,
                        "products": prods,
                        "total_results": total_results,
                        "total_pages": total_pages,
                        "prods": products,
                        "base_url": base_url,
                        "pagination": pagination,
                        "filters": filters,
                        "store": store,
                        "sort":org_sort,
                        "perpage":items_per_page,
                        "show_compare":show_compare,
                        "q": request.GET.get('q',''),
                        "hidden_data":hidden_data,
                        "clearance_sale":clearance_sale,
                        "leaf_category":leaf_category,
                        "category":category,
                        "hc_count":hc_count,
                        "show_price_filter":show_price_filter,
                        "title":"Search Results",
                        "c": request.GET.get('c',''),
                    }
        else:
            search_log.info('solr_query for spell check %s' % q)
            params = {}
            params['spellcheck'] = 'true'
            params['spellcheck.collate'] = 'true'
            params['spellcheck.build'] = 'true'
            search_q = str(request.GET.get('q',None)).strip()
            search_q = remove_special_chars(search_q)
            if not search_q:
                ctxt = {
                            "products":'',
                            "spell_suggestion":'',
                       }
                return ctxt
            params['spellcheck.q'] = search_q
            try:
                solr_result = solr_search(q, fields='collation, spellcheck, suggestion', highlight=None,
                    score=True, sort=sort, sort_order=sort_order, operation='/spell', request=request, **params)
            except solr.SolrException,e:
                solr_result = {}
                search_log.exception("Exception in solr spell query: %s" % q)
            spell_suggestion = ''
            if hasattr(solr_result, 'spellcheck') and solr_result.spellcheck['suggestions']:
                suggestions = solr_result.spellcheck['suggestions']
                spell_suggestion = "%s" % suggestions.get('collation', '')
                spell_suggestion = remove_special_chars(spell_suggestion)
                if spell_suggestion:
                    q = "%s AND client_id:%s AND status:active AND inStock:true" % (spell_suggestion, request.client.client.id)
                    search_log.info("Solr query for getting results of spell suggestion:%s " % (spell_suggestion))
                    check_solr_result = solr_search(q, fields='id', highlight=None,
                            score=True, sort=sort, sort_order=sort_order, request=request)
                if not int(check_solr_result.numFound) > 0:
                    spell_suggestion = ''
            ctxt = {
                        "products":'',
                        "spell_suggestion":spell_suggestion,
                   }
    else:
        return {}
    return ctxt



def get_sbf_context_by_products(request, products):
    product_ids = []
    for product in products:        
        prod_id = product.id
        if product.type == 'variant':
            variant = ProductVariant.objects.filter(variant=product)
            if variant:
                variant = variant[0]
                prod_id = variant.blueprint.id
        if str(prod_id) not in product_ids:
            product_ids.append(str(prod_id))
    if product_ids:
        prod_ids = " OR ".join(product_ids)
        prod_ids = "(" + str(prod_ids) + ")"
        from web.views.sbf_views import search_browser_filter
        ctxt = search_browser_filter(request,**{'product':prod_ids})
    else:
        ctxt = dict(products=None)
    return ctxt

def most_viewed_products(request):
    rate_charts = SellerRateChart.objects.select_related('product').filter(seller__client=request.client.client, offer_price__gte=500,\
                    product__status='active', stock_status='instock').order_by('-product__view_count')[:60]
    products = [s.product for s in rate_charts]
    context = get_sbf_context_by_products(request, products)
    html_page = 'categories/category.html'
    if not context['products']:
        html_page = 'categories/zero_result.html'
    return render_to_response(html_page,
            context,
            context_instance = RequestContext(request))

def most_bought_products(request):
    from orders.models import OrderCountByState
    _client = request.client.client
    most_bought_key = 'mostbought#%s' % (_client.id)
    products = cache.get(most_bought_key)
    if not products:
        paid_products = OrderCountByState.objects.select_related('product')\
                        .filter(client=_client, state="confirmed").order_by("-order_count")
        products = []
        for prod in paid_products:
            src = prod.product.primary_rate_chart()
            if prod.product.status == 'active' and src.stock_status == 'instock' and src.offer_price >= 500 and prod not in products:
                products.append(prod_id)
                if len(product_ids) >= 60:
                    break
        if len(products) < 60:
            most_wanted = SellerRateChart.objects.filter(seller__client=_client,
                stock_status='instock').exclude(offer_price__lte = '499.00').order_by('-product__confirmed_order_count')
            for src in most_wanted:
                if src.product not in products:
                    products.append(src.product)
                    if len(products) >= 60:
                        break
        cache.set(most_bought_key, products, 3600)
    context = get_sbf_context_by_products(request, products)
    html_page = 'categories/category.html'
    if not context['products']:
        html_page = 'categories/zero_result.html'
    return render_to_response(html_page,
            context,
            context_instance = RequestContext(request))

def recently_bought_products(request):
    from activitystream.models import Activity
    _client_domain = request.client
    products = []
    act_objs = Activity.objects.select_related("asrc").filter(aclientdomain=_client_domain, atype="Buy", asrc__product__status='active',\
                    asrc__stock_status='instock', asrc__offer_price__gte=500).order_by('-atime')
    for obj in act_objs:
        if obj.asrc.product not in products:
            products.append(obj.asrc.product)
            if len(products) >= 60:
                break
    context = get_sbf_context_by_products(request, products)
    html_page = 'categories/category.html'
    if not context['products']:
        html_page = 'categories/zero_result.html'
    return render_to_response(html_page,
            context,
            context_instance = RequestContext(request))


def get_datetime(value, time_format):
    now = datetime.now()
    try:
        value = int(value)
    except ValueError:
        return None
    if time_format.lower() in ['hour', 'hours']:
        now_datetime = now + timedelta(hours=+value)
        return now_datetime
    if time_format.lower() in ['minute', 'minutes']:
        now_datetime = now + timedelta(minutes=+value)
        return now_datetime
    return None
