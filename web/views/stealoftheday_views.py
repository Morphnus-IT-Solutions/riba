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
from web.sbf_forms import SearchForm, FilterForm, SortForm
from orders.views import get_cart
from catalog.models import *
from categories.models import *
from django.views.generic.list_detail import object_list
from utils.solrutils import *
from utils.utils import *
import solr
import re
import math
from dealprops.models import DailyDeal, FridayDeal, FridayDealProducts
from decimal import Decimal
from datetime import datetime
from django.views.decorators.cache import never_cache

log = logging.getLogger('request')

def detail(request, slug, id):
    if request.method == "POST":
        log.info('params %s' % request.POST)
        #selected_variants = request.POST.getlist('selected_variants')
        variant_ids = []
        for v in request.POST:
            if v.startswith('deal_'):
                vls = v.split('_')
                variant_ids.append(vls[1])
        log.info('variants id %s' % variant_ids)
        cart = get_cart(request)
        for p in variant_ids:
    	    rate_chart = SellerRateChart.objects.filter(product__id=p)
            if rate_chart:
                cart.add_item(request, rate_chart[0])
        return HttpResponseRedirect('/orders/mycart')
                    
    _client = request.client.client
    try:
        # Check for currently running daily_deal
        deal = DailyDeal.objects.get(client=request.client.client, type="hero_deal",
            starts_on__lte = datetime.now(), ends_on__gte = datetime.now(), status = "published")
    except (DailyDeal.DoesNotExist, DailyDeal.MultipleObjectsReturned) :
        raise Http404
    deal_rate_charts = []
    deal_products = []
    if deal:
        # Get all daily deal products
        deal_products = [deal_product.product for deal_product in deal.dailydealproduct_set.all()]
        if not deal_products:
            raise Http404
        ids = []
        if len(deal_products) > 1:
            # Deal has multiple products,
            # render it to SRP
            from web.views.sbf_views import search_browser_filter
            for product in deal_products:
                if product.type == 'variant':
                    variant = ProductVariant.objects.filter(variant=product)
                    if variant:
                        variant = variant[0]
                        ids.append(str(variant.blueprint.id))
                else:
                    ids.append(str(product.id))
            prod_ids = " OR ".join(ids)
            prod_ids = "(" + str(prod_ids) + ")"
            ctxt = search_browser_filter(request,**{'product':prod_ids})
            ctxt['daily_deal'] = True
            if request.is_ajax():
                return ctxt
            return render_to_response('categories/category.html',ctxt,context_instance=RequestContext(request))
        else:
            # Deal has only one product
            # render it to PDP
            product = deal_products[0]
            return HttpResponseRedirect('%s' % (get_cc_url(request, product.url())))
    raise Http404
    
    in_box_content = ''
    if deal.in_box_accessories:
        in_box_content = deal.in_box_accessories
    else:
        feature_grp = FeatureGroup.objects.filter(product_type = deal_product.product_type)
        for grp in feature_grp:
            if grp.name == 'Accessories':        
                feature_all = deal_product.productfeatures_set.all()
                features = feature_all.filter(feature__group = grp).order_by('feature__sort_order')
                for feature in features:
                    feature_content = {}
                    try:
                        in_box_content = str(feature.data)
                    except:
                        pass
    prod_list = []
    if deal.type == "multiple":
        for deal_prod in deal_products:
            
            product = Product.objects.get(id=deal_prod.product.id)
            images = product.productimage_set.all().order_by('id')
            blueprint = product
            try:
                sellerRateChart = product.primary_rate_chart()
            except SellerRateChart.DoesNotExist:
                log.error('Error finding preferred ratechart for %s' % product.title)
                continue
            if images:
                thumbnail = images[0].thumbnail_image.name
            else:
                thumbnail = None
            sizes = []
            product_variant = ProductVariant.objects.filter(variant=product)
            if product_variant:
                product_variant = product_variant[0].blueprint
                for pv in product_variant.variants.iterator():
                    try:
                        feature = pv.variant.productfeatures_set.get(feature__id=1701)
                        sizes.append({'size':feature.data,'variant':pv.variant})
                    except:
                        pass
            prod_list.append({'product':product,'blueprint':blueprint, 'image':thumbnail, 'product_images':images,'rateChart':sellerRateChart,'sizes':sizes})
    return render_to_response(
            "stealoftheday/detail.html",
            {
                'deal':deal,
                'in_box_content':in_box_content,
                'deal_rate_chart':deal_rate_chart,
                'deal_product':deal_product,
                'prod_list':prod_list,
            },
            context_instance = RequestContext(request))

def todays_deals(request, sequence):
    # Set default path to home page
    path = ''
    try:
        deal = DailyDeal.objects.get(client=request.client.client, type="todays_deals",
            starts_on__lte = datetime.now(), ends_on__gte = datetime.now(), status = "published")
    except (DailyDeal.DoesNotExist, DailyDeal.MultipleObjectsReturned) :
        render_url = get_cc_url(request, path)
        return HttpResponseRedirect(render_url)
    deal_products = deal.dailydealproduct_set.select_related("product").all().order_by("order")
    sequence = int(sequence) - 1
    try:
        deal_product = deal_products[sequence].product
        path = deal_product.url()
    except IndexError:
        render_url = get_cc_url(request, path)
        return HttpResponseRedirect(render_url)
    # Render cc_url
    render_url = get_cc_url(request, path)
    return HttpResponseRedirect(render_url)

@never_cache
def friday_deal(request, filter=None):
    deal = FridayDeal.objects.filter(status='published', starts_on__lte=datetime.now(), ends_on__gte=datetime.now()).order_by('-id')

    spalding_article_ids = """300766104003
                            300766104013
                            300766104008
                            300738257004
                            300756510003
                            300756510008
                            300756454008
                            300756454003
                            300756434008
                            300756434003
                            300756470008
                            300756470003
                            300756487008
                            300756487003
                            300756487013
                            300768522004
                            300768522010
                            300768511010
                            300768511004
                            300768481010
                            300768481004
                            300768527010
                            300768527004
                            300768454010
                            300768454004""".split("\n")

    show_static = False
    if filter == 'spalding':
        show_static = True
    if deal:
        deal = deal[0]
        page_no = request.GET.get('page', '1')
        page_no = int(page_no)
        items_per_page = 8
        total_results = deal.fridaydealproducts_set.all().count()
        total_pages = int(math.ceil(Decimal(total_results)/Decimal(items_per_page)))
        active_deals = deal.fridaydealproducts_set.filter(starts_on__lte = datetime.now(), ends_on__gte=datetime.now()).order_by('sequence')
        total_active_count = active_deals.count()
        start = ((page_no - 1) * items_per_page) - total_active_count
        end = (page_no * items_per_page) - total_active_count
        start = 0 if start < 0 else start
        deactive_deals = deal.fridaydealproducts_set.exclude(starts_on__lte = datetime.now(), ends_on__gte=datetime.now()).order_by('sequence')[start:end]
        deactive_ids = []
        if show_static:            
            for a in spalding_article_ids:
                a = a.strip()
                try:
                    src = SellerRateChart.objects.get(article_id=a, seller__client=5)
                    deactive_ids.append(src.product.id)
                except:
                    pass                    
            total_results = len(deactive_ids)
            total_pages = 1
        else:
            deactive_ids = [d.product.id for d in deactive_deals]
        if page_no != 1 or show_static:
            active_deals = []
        active_products = create_context_for_search_results([d.product.id for d in active_deals], request)
        deactive_products = create_context_for_search_results(deactive_ids, request)
        counter = 0
        for product in active_products:
            product['deal'] = active_deals[counter]
            special_price_info = product['rate_chart'].getPriceInfo(request, None, 
                        **{'price_type':'next_price', 'dont_cache':True, 'time_delta':2})
            if special_price_info:
                product['fixed_offer_price'] = special_price_info['offer_price']
            else:
                product['fixed_offer_price'] = None
            counter += 1
        base_url = request.get_full_path()
        page_pattern = re.compile('[&?]page=\d+')
        base_url = page_pattern.sub('',base_url)
        if base_url.find('?') == -1:
            base_url = base_url + '?'
        else:
            base_url = base_url + '&'
        pagination = getPaginationContext(page_no, total_pages, base_url)
        pagination['result_from'] = (page_no - 1) * items_per_page + 1
        pagination['result_to'] = ternary(page_no*items_per_page > total_results, total_results, page_no*items_per_page)
        footwear_src = None
        try:
            footwear_src = SellerRateChart.objects.get(article_id='300766104003', seller__client=5)
        except:
            pass
        if request.is_ajax():
            return render_to_response(
                    "stealoftheday/friday_deal_products.html",
                    {
                        'deal':deal,
                        'active_products':active_products,
                        'deactive_products':deactive_products,
                        'pagination':pagination,
                        'footwear_src':footwear_src,
                        'is_filter':show_static,
                    },
                    context_instance = RequestContext(request))
        else:
            return render_to_response(
                    "stealoftheday/friday_deal.html",
                    {
                        'deal':deal,
                        'active_products':active_products,
                        'deactive_products':deactive_products,
                        'pagination':pagination,
                        'total_pages':total_pages,                    
                        'footwear_src':footwear_src,
                        'is_filter':show_static,
                    },
            context_instance = RequestContext(request))
    else:
        raise Http404
