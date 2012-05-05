# Create your views here.
from django.http import HttpResponse
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from datetime import datetime
from catalog.models import Product, ProductImage
from django.views.decorators.cache import never_cache
from django.http import HttpResponsePermanentRedirect
from django.core.cache import cache
from django.template import Context, Template
from django.template.loader import get_template
from django.conf import settings
from django.template.defaultfilters import slugify

def robots(request):
    if request.client.domain in ['nu.futurebazaar.com','stg.futurebazaar.com','staging.futurebazaar.com']:
        str = '''User-agent: *
    Disallow: /'''
    else:
        str = '''User-agent: *
    Disallow: /user
    Disallow: /auth
    Disallow: /orders
    Disallow: /order
    Disallow: /payment
    Disallow: /admin
    Disallow: /cc
    Disallow: /login
    Disallow: /analytics
    Disallow: /tinymce
    Disallow: /accounts
    Disallow: /payouts
    Disallow: /catalog
    Disallow: /help'''
    return HttpResponse(str,status=200,mimetype='text/plain') 

def verify_msn(request):
    str = '''<?xml version="1.0"?>
<users>
<user>DD314114389E1C399426534EE8C58CF6</user>
</users>'''
    return HttpResponse(str, status=200, mimetype='text/xml')


def get_solr_feeds(request, solr_query, **kwargs):
    client_domain = request.client
    sort = 'score'
    sort_order = 'asc'
    q = solr_query
    offer_price = "offerprice_%s" % client_domain.id
    list_price = "listprice_%s" % client_domain.id
    is_dgm_feeds = kwargs.get('dgm_feeds',None)
    params = {}
    entries = 20
    params['rows'] = entries

    solr_result = solr_search(q, fields='title, %s, %s, category, category_id, id, sku, currency, brand, tags' % (offer_price, list_price), highlight=None,score=True, sort=sort, sort_order=sort_order, **params)
    
    if solr_result.numFound > entries:
        params['rows'] = solr_result.numFound
        solr_result = solr_search(q, fields='title, %s, %s, category, category_id, id, sku, currency, brand, tags' % (offer_price, list_price), highlight=None,score=True, sort=sort, sort_order=sort_order, **params)

    datas = []
    for result in solr_result.results:
        data = {}
        data['productname'] = result['title']
        if list_price in result:
            data['mrp'] = result[list_price]
        if offer_price in result:
            data['saleprice'] = result[offer_price]

        data['category'] = result['category']
        data['category'] = []
        cat_name = 'category'
        for cat in result['category']:
             cat_data = {}
             cat_data['name'] = cat_name
             cat_data['category'] = cat
             cat_name = 'sub' + cat_name
             data['category'].append(cat_data)

        data['category_id'] = []
        cat_name = 'category_id'
        for cat_id in result['category_id']:
             cat_data = {}
             cat_data['name'] = cat_name
             cat_data['category_id'] = cat_id
             cat_name = 'sub' + cat_name
             data['category_id'].append(cat_data)
        
        data['category_url'] = []
        cat_name = 'category_url'
        for (counter, cat_id) in enumerate(result['category_id']):
             cat_data = {}
             cat_data['name'] = cat_name
             slug = slugify(result['category'][counter])
             id_no = cat_id
             cat_data['category_url'] = "http://%s/%s/ch/%s/" % (client_domain.domain, slug, id_no)
             cat_name = 'sub' + cat_name
             data['category_url'].append(cat_data)

        data['tags'] = []
        if 'tags' in result:
            for tag in result['tags']:
                data['tags'].append(tag)

        data['score'] = result['score']
        data['productid'] = result['id']
        data['skuid'] = result['sku']
        data['brand'] = result['brand']
        data['currency'] = []
        if 'currency' in result:
            data['currency'] = result['currency']
        product = Product.objects.get(id=data['productid']) 
        if is_dgm_feeds:
            data['modelnumber'] = product.model
            data['description'] = product.description
            src = product.primary_rate_chart()
            if not src:
                continue
            data['features'] = ''
            if src.key_feature:
                data['features'] = src.key_feature  
        data['productlink'] = "http://%s/%s" % (client_domain.domain, product.url())
        prod_image = ProductImage.objects.filter(product=product)
        if prod_image:
            prod_image = prod_image[0]
            data['imagelink'] = prod_image.get_display_url()
        datas.append(data)
    return datas

def gen_omg_feeds(request):
    from datetime import datetime
    client_domain = request.client
    category_name = ''
    if category_name:
        q = "category:%s AND client_id:%s" % (category_name, client_domain.client.id)
    else:
        q = "category:[* TO *] AND client_id:%s" % (client_domain.client.id)
    datas = get_solr_feeds(request, q)
    datetime = datetime.now()
    templ = get_template('web/omg_feeds.xml')
    ctxt = Context({"datas":datas, "client_domain":client_domain})
    data = templ.render(ctxt)
    f = open('%s/feeds/omg_feeds.xml' % settings.UPLOAD_ROOT, 'w')
    f.writelines(data)
    f.close()

def gen_web_feeds(request, partner):
    client_domain = request.client
    category_name = ''
    if category_name:
        q = "category:%s AND client_id:%s" % (category_name, client_domain.client.id)
    else:
        q = "category:[* TO *] AND client_id:%s" % (client_domain.client.id)
    datas = get_solr_feeds(request, q, **{'dgm_feeds':True})
    templ = get_template('web/%s_feeds.xml' % partner)
    ctxt = Context({"datas":datas, "client_domain":client_domain})
    data = templ.render(ctxt)
    f = open('%s/feeds/%s_feeds.xml' % (settings.UPLOAD_ROOT, partner), 'w')
    f.writelines(data)
    f.close()

def gen_daily_deal_feed(request, feed_for):
    client_domain = request.client
    deal = DailyDeal.objects.filter(status='published', starts_on__lte=datetime.now(),ends_on__gte=datetime.now(),
        client=client_domain.client, type='hero_deal')
    datas = []
    if deal:
        deal = deal[0]
        deal_products = deal.dailydealproduct_set.all()
        product_ids = [str(p.product.id) for p in deal_products]
        product_ids = "(" + " OR ".join(product_ids) + ")"
        q = "id:%s AND client_id:%s" % (product_ids, client_domain.client.id)
        if feed_for == 'dgm':
            datas = get_solr_feeds(request, q, **{'dgm_feeds':True})
        else:
            datas = get_solr_feeds(request, q)
        for data in datas:
            product = Product.objects.get(id=data['productid'])
            data['startson'] = deal.starts_on
            data['endson'] = deal.ends_on

    template = 'stealoftheday/dailydeal.xml'
    if feed_for != "general":
        template = template.replace('dailydeal', 'dailydeal_%s' % feed_for) 
    templ = get_template(template)
    ctxt = Context({"datas":datas, "client_domain":client_domain})
    data = templ.render(ctxt)
    f = open('%s/feeds/%s' % (settings.UPLOAD_ROOT, template), 'w')
    f.writelines(data)
    f.close()

def gen_sitemap(request):
    from catalog.models import SellerRateChart
    products = SellerRateChart.objects.exclude(
        product__type='variable').filter(
        seller__client=request.client.client,product__status='active').values(
        'product__id','product__slug')
    url_list = []
    for product in products:
        url_list.append(dict(loc='http://%s/%s/pd/%s' % (request.client.domain,product['product__slug'], product['product__id'])))
    templ = get_template('sitemap.xml')
    ctxt = Context({"url_list":url_list})
    data = templ.render(ctxt)
    f = open('%s/feeds/sitemap.xml' % settings.UPLOAD_ROOT, 'w')
    f.writelines(data)
    f.close()

def gen_category_feeds(request):
    client_domain = request.client
    category_name = ''
    if category_name:
        q = "category:%s AND client_id:%s" % (category_name, client_domain.client.id)
    else:
        q = "category:[* TO *] AND client_id:%s" % (client_domain.client.id)
    datas = get_solr_feeds(request, q)
    templ = get_template('category_feeds.xml')
    ctxt = Context({"datas":datas, "client_domain":client_domain})
    data = templ.render(ctxt)
    f = open('%s/feeds/feeds.xml' % settings.UPLOAD_ROOT, 'w')
    f.writelines(data)
    f.close()

def sitemap(request):
    return HttpResponsePermanentRedirect('/media/u/feeds/sitemap.xml')

def category_feeds(request):
    return HttpResponsePermanentRedirect('/media/u/feeds/feeds.xml')

def dgm_feeds(request):    
    return HttpResponsePermanentRedirect('/media/u/feeds/dgm.xml')

def omg_feeds(request):
    return HttpResponsePermanentRedirect('/media/u/feeds/omg_feeds.xml')

def ninedot_feeds(request):    
    return HttpResponsePermanentRedirect('/media/u/feeds/9dot_feeds.xml')

def vc_feeds(request):    
    return HttpResponsePermanentRedirect('/media/u/feeds/vc_feeds.xml')

def daily_deal_feeds(request):
    return HttpResponsePermanentRedirect(
        '/media/u/feeds/stealoftheday/dailydeal.xml')

def daily_deal_feeds_dgm(request):
    return HttpResponsePermanentRedirect(
        '/media/u/feeds/stealoftheday/dailydeal_dgm.xml')

def daily_deal_feeds_omg(request):
    return HttpResponsePermanentRedirect(
        '/media/u/feeds/stealoftheday/dailydeal_omg.xml')

def daily_deal_feeds_9dot(request):
    return HttpResponsePermanentRedirect(
        '/media/u/feeds/stealoftheday/dailydeal_9dot.xml')

def print_request(request):
    return HttpResponse(str(request))

def cache_moderate(request):
    messages = []
    memcache_content = {}
    if request.method == 'POST':
        key = request.POST.get("key", None).strip()
        if not key:
            messages.append("Please enter cache key.")
        else:
            # POST params contains "key_content" only when
            # user requests to fetch the content of the particular keys
            key_content = request.POST.get("key_content", None)
            if key_content:
                # User can provide multiple keys separated by space
                cache_keys = []
                for cache_key in key.split(" "):
                    # Providing non-empty keys to get_many fn
                    if cache_key:
                        cache_keys.append(cache_key)
                # Fetch cached content of the keys in cache_keys
                memcache_content = cache.get_many(cache_keys)
                if not memcache_content:
                    # Provided keys are not cached 
                    messages = ["Provided keys are not cached."]
                for cache_key in cache_keys:
                    if cache_key not in memcache_content:
                        messages.append("KEY: <b>%s</b>, not cached in memcache." % cache_key)
            else:
                if key == 'clear_all':
                    # Flush memcache memory 
                    flush_memcache()
                    messages.append("Flushed Memcache Memory.")
                else:
                    # Deletes the cached content of the provided key
                    del_key_from_cache(key)
                    messages.append("KEY: <b>%s</b>, cleared from memcache" % key)
    return render_to_response("web/cache_moderate.html",
            {
                'messages': messages,
                'memcache_content':memcache_content,
            },
            context_instance = RequestContext(request))

def del_key_from_cache(key):
    # Deletes the cached content of the provided key
    cache.delete(key)

def flush_memcache():
    # Flush memcache memory 
    cache.clear()
