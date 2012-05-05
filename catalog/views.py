# Create your views here.
from accounts.models import Account
from catalog.models import SellerRateChart
from django.shortcuts import render_to_response
from django.template import RequestContext
from catalog.forms import *
from catalog.models import *
from categories.models import Category,Feature,FeatureChoice
from django.http import HttpResponse
from django.utils import simplejson
from django.forms.models import inlineformset_factory

import logging

log = logging.getLogger('request')

def show_dashboard(request):
    ctxt = {}
    user = request.user
    log.info('request user %s' % user) 
    accounts = Account.objects.filter(managers=user)
    log.info('accounts %s' % accounts)
    #ctxt['accounts'] = accounts
    acc = []
    for account in accounts:
        details = {}
        details['account'] = account
        products = SellerRateChart.objects.filter(seller=account,stock_status='instock').count()
        details['product_count'] = products
        log.info('products %s' % details)
        acc.append(details)

    ctxt['accounts'] = acc
    return render_to_response('catalog/dashboard.html',ctxt,context_instance=RequestContext(request))


def add_product(request):
    ctxt = {}
    form = ProductForm()

    ctxt['product'] = form
    ctxt['seller_formset'] = productSellerFormSet(instance=Product())
    ctxt['shipping_formset'] = productShippingFormSet(instance=Product())
    ctxt['variant_formset'] = productVariantFormSet(instance=Product())
    ctxt['features_formset'] = productFeatureFormSet(instance=Product())
    ctxt['image_formset'] = productImageFormSet(instance = Product())
    

    return render_to_response('catalog/add_product.html',ctxt,context_instance=RequestContext(request))

def add(request):
    ctxt = {}
    if request.method == 'POST':
        productForm = ProductForm(request.POST)
        #productFeaturesForm = ProductFeaturesForm(request.POST)
        if productForm.is_valid():
            product = productForm.save(commit=False)
            feature_formset = productFeatureFormSet(request.POST,instance=product)
            image_formset = productImageFormSet(request.POST,request.FILES,instance=product)
            seller_formset = productSellerFormSet(request.POST, instance = product)
            shipping_formset = productShippingFormSet(request.POST, instance=product)
            variant_formset = productVariantFormSet(request.POST, instance=product)
            if feature_formset.is_valid() and seller_formset.is_valid() and shipping_formset.is_valid() and variant_formset.is_valid():
                product.save()
                feature_formset.save()
                image_formset.save()
                seller_formset.save()
                shipping_formset.save()
                variant_formset.save()
                return HttpResponse('posted')
            else:
                ctxt = {}
                ctxt['product'] = productForm
                ctxt['seller_formset'] = seller_formset
                ctxt['shipping_formset'] = shipping_formset
                ctxt['variant_formset'] = variant_formset
                ctxt['features_formset'] = feature_formset
                ctxt['image_formset'] = image_formset
                return render_to_response('catalog/add_product.html',ctxt,context_instance=RequestContext(request))

        else:
            return render_to_response('catalog/add_product.html',{'product':productForm},context_instance=RequestContext(request))

def save_product(product,form):
    product.sku = form.cleaned_data['sku']
    product.old_id = form.cleaned_data['old_id']
    product.title = form.cleaned_data['title']
    product.description = form.cleaned_data['description']
    product.currency = form.cleaned_data['currency']
    product.brand = form.cleaned_data['brand']
    product.model = form.cleaned_data['model']
    product.sku_type = form.cleaned_data['sku_type']
    #category = Category.objects.get(pk=form.cleaned_data['category'])
    product.category = form.cleaned_data['category']
    #product.timestamp = form.cleaned_data['timestamp']
    product.slug = form.cleaned_data['slug']
    product.is_active = form.cleaned_data['is_active']
    product.meta_description = form.cleaned_data['meta_description']
    product.view_count = form.cleaned_data['view_count']
    product.cart_count = form.cleaned_data['cart_count']
    product.pending_order_count = form.cleaned_data['pending_order_count']
    product.confirmed_order_count = form.cleaned_data['confirmed_order_count']
    product.type = form.cleaned_data['type']

def save_product_features(feature,form):
    feature.feature = form.cleaned_data['feature']
    feature.data = form.cleaned_data['data']
    feature.value = form.cleaned_data['value']
    feature.type = form.cleaned_data['feature_type']

def test(request):
    if request.method == 'POST':
        params = request.POST
        log.info('params %s' % params)
        featureId = params['featureId']
        json = dict(status='ok',data=featureId)
        res = HttpResponse(simplejson.dumps(json))
        log.info('response %s' % res)
        return res

def render_feature_object(request):
    if request.method == 'GET':
        params = request.GET
        log.info('params %s' % params)
        featureId = params['featureId']
        feature  = Feature.objects.get(pk=featureId)
        log.info('feature %s' % feature)
        json = dict(status='ok',data=feature)
        feature_choices = FeatureChoice.objects.filter(feature_id=featureId)
        log.info('feature choices %s' % feature_choices)
        log.info('json %s' % simplejson.dumps(json))
        res = HttpResponse(simplejson.dumps(json))
        return res

def get_feature_info(request):
    if request.method == 'GET':
        params = request.GET
        log.info('params %s' % params)
        featureId = params['featureId']
        log.info('featureid %s' % featureId)
        feature = Feature.objects.select_related('unit').get(pk=featureId)
        log.info('feature %s' % feature)
        feature_choices = FeatureChoice.objects.filter(feature=featureId)
        choices = []
        if feature_choices:
            for choice in feature_choices:
                choices.append(choice.name)

        log.info('feature choices %s' % choices)
        unit_name = feature.unit.name if feature.unit else ''
        unit_code = feature.unit.code if feature.unit else ''
        json = {'status':'ok','display_type':feature.type,'allow_multiple_select':feature.allow_multiple_select,'unit_name':unit_name,'unit_code':unit_code,'choices':choices}
        res = HttpResponse(simplejson.dumps(json))
        return res
