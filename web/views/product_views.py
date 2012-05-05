# Create your views here.
import datetime
import hashlib
import logging
from django.template.defaultfilters import slugify
from django.conf import settings
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, Http404
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
from users.models import Profile,Email
from django.core.cache import cache
from decimal import Decimal
from pricing.models import *
from promotions.models import *
from utils.utils import create_context_for_search_results,track_product_view_usage
import math
from datetime import datetime, timedelta
log = logging.getLogger('request')



def product_detail(request, slug, id):
    try:
        product = Product.objects.get_product(id, request)
    except Product.DoesNotExist:
        raise Http404
    _client = request.client.client
    # raise 404 if there is no such product
    if not product:
        raise Http404
    else:
        primary_rate_chart = product.primary_rate_chart()
        if not primary_rate_chart:
            raise Http404
        if not primary_rate_chart.seller.client == request.client.client:
            raise Http404
        
    # to ensure proper seo rank, we redirect to url based on current slug
    if product.slug != slug:
        return HttpResponsePermanentRedirect(
                reverse(
                    'product-detail-url',
                    None,
                    kwargs={'slug':product.slug,'id':id}
                    )
                )
    if request.method == 'GET':
        sort=request.GET.get('sort',"MostHelpful")
        utils.track_product_view_usage(request, product)
    avg_rating = 0
    rating_list=[0,0,0,0,0]
    bar_width=[0,0,0,0,0]
    product_reviews = Review.objects.filter(product=product, status__in = ['approved']).order_by('-no_helpful','no_not_helpful','-reviewed_on')
    total_reviews=len(product_reviews)
    if product_reviews:
        for review in product_reviews:
            avg_rating += review.rating
            if review.rating == 5:
                rating_list[0]+=1  
            elif review.rating == 4:
                rating_list[1]+=1  
            elif review.rating == 3:
                rating_list[2]+=1  
            elif review.rating == 2:
                rating_list[3]+=1  
            else:
                rating_list[4]+=1
        for a in [0,1,2,3,4]:
            bar_width[a]=Decimal(rating_list[a]/Decimal(len(product_reviews)))*160
        avg_rating = Decimal(avg_rating)/Decimal(len(product_reviews))
        upper_limit = Decimal(str(math.ceil(avg_rating))) - (avg_rating)
        if upper_limit >= Decimal('0.75'):
            avg_rating = int(avg_rating) + 0.25
        elif upper_limit >= Decimal('0.5'):
            avg_rating = int(avg_rating) + 0.5
        elif upper_limit >= Decimal('0.25'):
            avg_rating = int(avg_rating) + 0.75
        elif upper_limit < Decimal('0.25') and upper_limit != Decimal('0.0'):
            avg_rating = int(avg_rating) + 1
        avg_rating = float(avg_rating)
    product_reviews=product_reviews[0:5]
    pdp_review_length=len(product_reviews)
    rated_check={}
    if request.user.is_authenticated():
        profiles = Profile.objects.filter(user=request.user).order_by('id')
        profile = profiles[0]
        for review in product_reviews:
            helpfulness = ReviewHelpfulness.objects.filter(review=review,user=profile)
            try:
                helpfulness=helpfulness[0]
            except:
                pass
            if helpfulness:
                rated_check[review.id]=helpfulness.status
            else:
                rated_check[review.id]='NULL'
        offer_price = product.primary_rate_chart().offer_price

    product_images = product.get_product_images()

    offer_price = product.primary_rate_chart().offer_price
    priceInfo = {}

    priceInfo = product.primary_rate_chart().getPriceInfo(request)
    offer_price = priceInfo['offer_price']
    emi = None
    emi = utils.compute_emi(offer_price)
    similar_products = product.similar_products(request)[:5]
    sProds = similar_products

    rating_dict={}
    for a in range(0,5):
        rating_dict[a] = [rating_list[a],bar_width[a]]
    product_dict={
            "product_images": product_images,
            "product":product,
            "rate_chart": product.primary_rate_chart(),
            "similarProducts":sProds,
            "emi":emi,
#            "form":form,
            "product_reviews":product_reviews,
            "total_reviews":total_reviews,
            "avg_rating":avg_rating,
            "price_info":priceInfo,
            "sort":sort, 
            "rating_dict":rating_dict, 
            "rated_check":rated_check,
            "pdp_review_length":pdp_review_length,
            "slug":slug }

    return render_to_response('products/product.html',product_dict,context_instance=RequestContext(request))

@login_required
def review_page(request,id):
    product = Product.objects.select_related('category', 'brand').filter(pk=id)
    product=product[0]
    primary_rate_chart = product.primary_rate_chart()
    users = Profile.objects.filter(user=request.user).order_by('id')
    user = users[0]
    product_images = ProductImage.objects.filter(product = product).order_by('id')
    slug=slugify(product.title)
    if product.type == 'variable' and not product_images:
        dv = product.default_variant()
        product_images = ProductImage.objects.filter(product = dv).order_by('id')
    if request.method == 'POST':
        form = ReviewForm(request.POST)
        rating = request.POST.get('rating',0)
        name = request.POST['name'].strip()
        name_error=""
        review_dict={"form":form}
        if form.is_valid() and name !="":
            obj = form.save(commit=False)
            obj.product_id=id
            obj.user_id=user.id 
            obj.rate_chart=primary_rate_chart
            obj.product_image=product_images
            obj.reviewed_on=datetime.now()
            obj.modified_on=datetime.now()
            flag=request.POST.get('checkbox', None)
            if flag:
			    obj.display_name="Anonymous"
            elif name == "display_name" and not flag:
                obj.display_name=user.full_name
            elif name != "" and not flag:
                obj.display_name=request.POST['name']   
            else:
                obj.display_name="Anonymous"
            obj.save()
            review_dict={'form':form,'obj':obj,'slug':slug,'product':product,'product_images':product_images}
            return HttpResponseRedirect("/review/write/%s/thanks/" %obj.id)
#            return render_to_response("reviews/review_submitted.html",review_dict,context_instance=RequestContext(request))	
        else: 
            if name =="":
                name_error="Enter Your Name"
            review_dict = {'form':form,'product':product,'slug':slug,'product_images':product_images,'display_name':user.full_name.strip(),'name_error':name_error,'name':name,'rating':rating}
            return render_to_response('reviews/enter_review.html',review_dict,context_instance=RequestContext(request))
    else:  
        form=ReviewForm()
#        import pdb
#        pdb.set_trace()
        review_dict = {'form':form,'product':product,'slug':slug,'product_images':product_images,'display_name':user.full_name.strip()}
        return render_to_response('reviews/enter_review.html',review_dict,context_instance=RequestContext(request))

def thanks_page(request, review_id):
    obj=Review.objects.get(id=review_id)
    product = Product.objects.get(id=obj.product_id)
    slug=slugify(product.title)
    return render_to_response("reviews/review_submitted.html",{'obj':obj,'slug':slug},context_instance=RequestContext(request))	
 

def review_display(request,slug,review_id,*args,**kwargs):
    product_review = Review.objects.get(id=review_id)
    product = Product.objects.get(id=product_review.product_id)
    product_images = ProductImage.objects.filter(product = product).order_by('id')
    if product.type == 'variable' and not product_images:
        dv = product.default_variant()
        product_images = ProductImage.objects.filter(product = dv).order_by('id')
    rated_check={}
    if request.user.is_authenticated():
        profile = Profile.objects.get(user=request.user)
        helpfulness = ReviewHelpfulness.objects.filter(review=product_review,user=profile)
        try:
            helpfulness=helpfulness[0]
        except:
            pass         
        if helpfulness:
            rated_check[review_id]=helpfulness.status
        else:
            rated_check[review_id]='NULL'
    avg_rating = 0
    rating_list=[0,0,0,0,0]
    bar_width=[0,0,0,0,0]
    product_reviews = Review.objects.filter(product=product, status__in = ['approved']).order_by('reviewed_on')
    if product_reviews:
        for review in product_reviews:
            avg_rating += review.rating
            if review.rating == 5:
                rating_list[0]+=1  
            elif review.rating == 4:
                rating_list[1]+=1  
            elif review.rating == 3:
                rating_list[2]+=1  
            elif review.rating == 2:
                rating_list[3]+=1  
            else:
                rating_list[4]+=1
        for a in [0,1,2,3,4]:
            bar_width[a]=Decimal(rating_list[a]/Decimal(len(product_reviews)))*160
        avg_rating = Decimal(avg_rating)/Decimal(len(product_reviews))
        upper_limit = Decimal(str(math.ceil(avg_rating))) - (avg_rating)
        if upper_limit >= Decimal('0.75'):
            avg_rating = int(avg_rating) + 0.25
        elif upper_limit >= Decimal('0.5'):
            avg_rating = int(avg_rating) + 0.5
        elif upper_limit >= Decimal('0.25'):
            avg_rating = int(avg_rating) + 0.75
        elif upper_limit < Decimal('0.25') and upper_limit != Decimal('0.0'):
            avg_rating = int(avg_rating) + 1
        avg_rating = float(avg_rating)
    rating_dict={}
    for a in range(0,5):
        rating_dict[a] = [rating_list[a],bar_width[a]]
	slug=slugify(product.title)
    review_dict={'obj':product_review,'slug':slug,'product_images':product_images,'product':product,'rated_check':rated_check,'avg_rating':avg_rating,'bar_width':bar_width,'rating_dict':rating_dict,"total_reviews":len(product_reviews)}
    return render_to_response('reviews/review_display.html',review_dict,context_instance=RequestContext(request))

def product_quick_look(request, slug, id):
    product = Product.objects.select_related('category', 'brand').filter(pk=id)
    _client = request.client.client
    # raise 404 if there is no such product
    if not product:
        raise Http404
    else:
        product = product[0]
        primary_rate_chart = product.primary_rate_chart()
        if not primary_rate_chart:
            raise Http404
        if not primary_rate_chart.seller.client == request.client.client:
            raise Http404
        if is_future_ecom(request.client.client) and product.type == "variable":
            return HttpResponsePermanentRedirect(
                    reverse(
                        'product-quick-look-url',
                        None,
                        kwargs={'slug':primary_rate_chart.product.slug,'id':primary_rate_chart.product.id}
                        )
                    )
    product_id = [product.id]
    product_info = create_context_for_search_results(product_id, request)
    product_info = product_info[0]
    return render_to_response('products/quick_info.html', product_info, context_instance=RequestContext(request))

def update_helpful_yes(request):
    if not request.user.is_authenticated():
        return HttpResponse("Unsuccessful")
    if request.method == "POST":
        id = request.POST['id']
        review = Review.objects.get(id =id)
        profile = Profile.objects.get(user=request.user)
        helpfulness = ReviewHelpfulness.objects.filter(review=review,user=profile)
        try:
            helpfulness=helpfulness[0]
        except:
            pass
        if not helpfulness:
            helpfulness = ReviewHelpfulness(review=review,user=profile,status='helpful')
            helpfulness.save()
            review.no_helpful += 1
            review.save()
        elif(helpfulness.status == 'not_helpful'):
            helpfulness.status='helpful'
            helpfulness.save()
            review.no_helpful+=1
            review.no_not_helpful-=1
            review.save() 
        update_dict={'no_helpful':review.no_helpful,"no_not_helpful":review.no_not_helpful} 
        return HttpResponse(simplejson.dumps(update_dict))
    return HttpResponse("Unsuccessful")

def update_helpful_no(request):
    if not request.user.is_authenticated():
        return HttpResponse("Unsuccessful")
    if request.method == "POST":
        id = request.POST['id']
        review = Review.objects.get(id =id)
        profile = Profile.objects.get(user=request.user)
        helpfulness = ReviewHelpfulness.objects.filter(review=review,user=profile)
        try:
            helpfulness=helpfulness[0]
        except:
            pass
        if not helpfulness:
            helpfulness = ReviewHelpfulness(review=review,user=profile,status='not_helpful')
            helpfulness.save()
            review.no_not_helpful += 1
            review.save()
        elif(helpfulness.status == 'helpful'):
            helpfulness.status='not_helpful'
            helpfulness.save()
            review.no_not_helpful+=1
            review.no_helpful-=1
            review.save()       
        update_dict={'no_helpful':review.no_helpful,"no_not_helpful":review.no_not_helpful} 
        return HttpResponse(simplejson.dumps(update_dict))
    return HttpResponse("Unsuccessful")
def update_helpful_cancel(request):
    if not request.user.is_authenticated():
        return HttpResponse("Unsuccessful")
    if request.method == "POST":
        id = request.POST['id']
        review = Review.objects.get(id =id)
        profile = Profile.objects.get(user=request.user)
        helpfulness = ReviewHelpfulness.objects.filter(review=review,user=profile)
        try:
            helpfulness=helpfulness[0]
        except:
            pass
        if not helpfulness:
            return HttpResponse("Your rating has been discarded ! ")
        elif(helpfulness.status == 'helpful'):
            review.no_helpful-=1
            helpfulness.delete() 
        else:
            review.no_not_helpful-=1      
            helpfulness.delete()
        review.save()      
        update_dict={'no_helpful':review.no_helpful,"no_not_helpful":review.no_not_helpful} 
        return HttpResponse(simplejson.dumps(update_dict))       
    return HttpResponse("Unsuccessful")
def all_reviews_page(request,slug,id,*args,**kwargs):
    sort=request.GET.get('sort','MostHelpful')
    product = Product.objects.get(id=id)
    product_images = ProductImage.objects.filter(product = product).order_by('id')
    if product.type == 'variable' and not product_images:
        dv = product.default_variant()
        product_images = ProductImage.objects.filter(product = dv).order_by('id')
    slug=slugify(product.title)
    avg_rating = 0
    rating_list=[0,0,0,0,0]
    bar_width=[0,0,0,0,0]
    product_reviews = Review.objects.filter(product=product, status__in = ['approved']).order_by('reviewed_on')
    if product_reviews:
        for review in product_reviews:
            avg_rating += review.rating
            if review.rating == 5:
                rating_list[0]+=1  
            elif review.rating == 4:
                rating_list[1]+=1  
            elif review.rating == 3:
                rating_list[2]+=1  
            elif review.rating == 2:
                rating_list[3]+=1  
            else:
                rating_list[4]+=1
        for a in [0,1,2,3,4]:
            bar_width[a]=Decimal(rating_list[a]/Decimal(len(product_reviews)))*160
        avg_rating = Decimal(avg_rating)/Decimal(len(product_reviews))
        upper_limit = Decimal(str(math.ceil(avg_rating))) - (avg_rating)
        if upper_limit >= Decimal('0.75'):
            avg_rating = int(avg_rating) + 0.25
        elif upper_limit >= Decimal('0.5'):
            avg_rating = int(avg_rating) + 0.5
        elif upper_limit >= Decimal('0.25'):
            avg_rating = int(avg_rating) + 0.75
        elif upper_limit < Decimal('0.25') and upper_limit != Decimal('0.0'):
            avg_rating = int(avg_rating) + 1
        avg_rating = float(avg_rating)
    rating_dict={}
    for a in range(0,5):
        rating_dict[a] = [rating_list[a],bar_width[a]]
    review_dict={'slug':slug,'product_images':product_images,'product':product,'avg_rating':avg_rating,'bar_width':bar_width,'rating_dict':rating_dict,"total_reviews":len(product_reviews),"sort":sort}
    return render_to_response('reviews/all_reviews.html',review_dict,context_instance=RequestContext(request))
def paginate_read_reviews(request):
    if request.method == "GET":
        sort= request.GET.get('sort','MostHelpful') 
        page_no = request.GET['page']
        prod_id = request.GET['product_id']
        page_no = int(page_no)
        product = Product.objects.get(id=prod_id)
        if sort =="MostRecent":
            product_reviews = Review.objects.filter(product=product, status__in=['approved']).order_by('-reviewed_on','rating')
        if sort =="MostHelpful": 
            product_reviews = Review.objects.filter(product=product, status__in=['approved']).order_by('-no_helpful','no_not_helpful')
        if sort =="MostRated":
            product_reviews = Review.objects.filter(product=product, status__in=['approved']).order_by('-rating','-reviewed_on')
        if sort =="LeastRated": 
            product_reviews = Review.objects.filter(product=product, status__in=['approved']).order_by('rating','-reviewed_on')
        items_per_page = 10
        total_results = len(product_reviews)
        total_pages = int(math.ceil(Decimal(len(product_reviews))/Decimal(items_per_page)))
        pagination = utils.getPaginationContext(page_no, total_pages, '')
        pagination['result_from'] = (page_no-1) * items_per_page + 1
        pagination['result_to'] = utils.ternary(page_no*items_per_page > total_results, total_results, page_no*items_per_page)
        product_reviews = product_reviews[:int(pagination['result_to'])]
        product_reviews = product_reviews[(int(pagination['result_from'])-1):]
        pagination['show_pagination'] = True
        rated_check={}
        if request.user.is_authenticated():
            profile = Profile.objects.get(user=request.user)
            for review in product_reviews:
                helpfulness = ReviewHelpfulness.objects.filter(review=review,user=profile)
                try:
                    helpfulness=helpfulness[0]
                except:
                    pass
                if helpfulness:
                    rated_check[review.id]=helpfulness.status
                else:
                    rated_check[review.id]='NULL'
        if total_results <= 10:
            pagination['show_pagination'] = False
        return render_to_response('products/read_review.html',{'product_reviews':product_reviews,'pagination':pagination,'from':pagination['result_from'],'to':pagination['result_to'],'product_id':prod_id,'sort':sort,'rated_check':rated_check,'total_reviews':total_results,'slug':slugify(product.title)},context_instance=RequestContext(request))
    return False


def share_product(request,id):
    if is_cc(request):
        if request.call['id'] in request.session:
            user = request.session[request.call['id']]['user']
            profile = Profile.objects.get(user=user)
            try:
                emails = Email.objects.filter(type='primary',user=profile)
                email = emails[0].email
            except:
                email = None
            product = Product.objects.get(id=id)
            if request.method == "POST":
                product.share(profile)
                return HttpResponse(simplejson.dumps(dict(status='sent')))
            else:
                return render_to_response('products/share_product_info.html',
                    {'product':product,
                    'email':email},
                    context_instance=RequestContext(request))


def get_parent_products(request):
    br = SellerRateChart.objects.filter(seller__client = request.client.client, stock_status = 'instock').values('product__brand')
    brands = Brand.objects.filter(id__in=br)
    #parent_categories = CategoryGraph.objects.filter(category__client = client,parent=None)
    return render_to_response('products/products_per_category.html',{'brands':brands}, context_instance = RequestContext(request))


def get_product_offer(request , src):
    _client = request.client.client
    bundles = Bundle.objects.select_related('offer').filter(offer__client=_client,
        primary_products=src).order_by('id')[:1]
    if bundles:
        return bundles[0]
    return bundles

def flf_msg(status_code):
    errorCode = status_code.lower()
    if errorCode == "err_inv":
        errDesc = "Sorry, we cannot ship this product. This product is currently out of stock."
    elif errorCode == "err_local":
        errDesc = "Sorry, we cannot ship this product. The product qualifies as a bulky item and your Pincode is not covered for it."
    elif errorCode == "err_delv":
        errDesc = "Sorry, we cannot ship this product. Your pincode does not come under our coverage area for the given product. "
    else:
        errDesc = "Sorry, we cannot ship this product at your pincode. "
    return errDesc  
