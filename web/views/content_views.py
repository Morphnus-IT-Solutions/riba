from django.contrib.auth.decorators import login_required, permission_required
from lxml import etree
from StringIO import StringIO
from django.db.models import Avg, Max, Min, Count
from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader
from django.http import Http404, HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import *
from django.contrib.auth import login as auth_login
from django.contrib  import auth
from django.core.mail import send_mail
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings
from django.db.models import Q, Sum
from django import forms
from django.forms.models import modelformset_factory
from users.models import *
from orders.models import *
from accounts.models import *
from catalog.models import *
from categories.models import *
from fulfillment.models import *
from payouts.models import *
from datetime import date, datetime, timedelta
from orders.forms import BasePaymentOptionFormSet
from users.forms import *
from accounts.forms import *
from locations.forms import *
#from accounts.forms importseller_namefrom locations.forms import *
from payouts.forms import  *
from utils import utils
from utils.utils import smart_unicode
from utils.utils import getPaginationContext, check_dates, create_context_for_search_results, get_excel_status, save_excel_file
from web.forms import *
from web.views.order_view import operator
from web.views.user_views import is_new_user, set_logged_in_user, set_eligible_user, user_order_details, show_agent_order_history
from web.views.pricing_views import all_prices, upload_price_xls, save_uploaded_file, get_temporary_file_path
from web.views.inventory_views import upload_bulk_inventory, show_all_inventory_levels, upload_pincodes
from decimal import Decimal, ROUND_UP
import operator
import gviz_api
import calendar
import re
import ast
import operator
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from ppd.decorators import check_role
import xlrd
from xlrd import XLRDError
from restapi import APIManager
from django.utils import simplejson
from django.db import transaction

def content_preview(request, client_name, seller_name, *args, **kwargs):
    client_name = slugify(client_name)
    seller_name = slugify(seller_name)
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('content-preview',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers'}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('content-preview',None,kwargs={'client_name':client_name,'seller_name':new_seller_name}))    
    profile = request.user.get_profile()
    accounts = profile.managed_accounts.filter(client__slug = client_name)
        
    #getting ids from client_name and seller_name
    client = Client.objects.filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('content-preview',None,kwargs={'client_name':profile.managed_clients[0].slug,'seller_name':'all-sellers'}))

    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('content-preview',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name)}))
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            seller = seller[0]
            current_seller_id = seller.id
        else:
            return HttpResponsePermanentRedirect(reverse('content-preview',None,kwargs={'client_name':client_name,'seller_name':'all-sellers'}))
    clients = profile.managed_clients()
    errors = []
    form = None
    to_update = None
    path_to_save = None
    flag = None
    flag='show_details'
    from web.sbf_forms import FileUploadForm
    
    header_list = ['Article ID','Product Name','Product Type'] 
    preview_list =[]
#    job = ContentJob.objects.get(id=job_id)
#    if request.session['role'] == "Iksula":
#        job_id = kwargs['job_id']
#        entries = ContentVersionTable.objects.filter(job=job_id)
#    elif request.session['role'] == "Category Team":
#        entries = ContentVersionTable.objects.filter(status='previewed')
    job_id = kwargs['job_id']
    entries = ContentVersionTable.objects.filter(job=job_id)
    for entry in entries:
        xml_data = entry.xml_content
        article_entry = entry.article
        prod_obj = article_entry.product
        temp_dict = {}
        temp_dict['article_id'] = article_entry.article_id
        temp_dict['src_id'] = article_entry.id
        temp_dict['prod_name'] = prod_obj.title
        temp_dict['product_type'] = prod_obj.product_type.type
        preview_list.append(temp_dict)
    content_dict = {
        'clients':clients,
        'loggedin':True,
        'accounts':accounts,
        'url':request.get_full_path(),
        'client_name':client_name,
        'seller_name':seller_name,
        'flag' : flag,
        'job_id':job_id,
        'header_list':header_list,
        'preview_list':preview_list,
        }
    return render_to_response('content/content_preview.html', content_dict, context_instance=RequestContext(request))


def content_upload(request, client_name, seller_name, *args, **kwargs):
    client_name = slugify(client_name)
    seller_name = slugify(seller_name)
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('content-upload',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers'}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('content-upload',None,kwargs={'client_name':client_name,'seller_name':new_seller_name}))    
    profile = request.user.get_profile()
    accounts = profile.managed_accounts.filter(client__slug = client_name)
        
    #getting ids from client_name and seller_name
    client = Client.objects.filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('content-upload',None,kwargs={'client_name':profile.managed_clients[0].slug,'seller_name':'all-sellers'}))

    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('content-upload',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name)}))
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            seller = seller[0]
            current_seller_id = seller.id
        else:
            return HttpResponsePermanentRedirect(reverse('content-upload',None,kwargs={'client_name':client_name,'seller_name':'all-sellers'}))
    clients = profile.managed_clients()
    
    errors = []
    form = None
    to_update = None
    path_to_save = None
    flag = None
    from web.sbf_forms import FileUploadForm
    if request.method == 'POST':
        if request.POST.get("upload") == 'Upload':
            form = FileUploadForm(request.POST, request.FILES)
            if form.is_valid():
                path_to_save = save_uploaded_file(request.FILES['status_file'])
                errors, job = validate_and_split_xml(request, path_to_save)
                if not errors:
                    job_id = job.id
                    return content_preview(request, client_name, seller_name, job_id=job_id)
                else:
                    form = FileUploadForm()
                    flag = 'new'
            else:
                errors.append(['Please select the appropriate excel file and click upload!!!'])
                form = FileUploadForm()
                flag = 'new'
        elif request.POST.get("article_preview") == 'Preview':
            #Form has been submitted so parsed_excel_json is directly available, do not parse xml again
            #parsed_excel_json = request.POST.get('parsed_excel_json', None)
            job_id = request.POST.get('job_id', None)
            src_id = request.POST.get('selected_article',None)
            return article_preview(request, client_name, seller_name, src_id, job_id)
        elif request.POST.get("article_approve") == 'Approve':
            #Form has been submitted so parsed_excel_json is directly available, do not parse xml again
            #parsed_excel_json = request.POST.get('parsed_excel_json', None)
            src_id = request.POST.get('selected_article',None)
            write_content_updates(src_id)
            return content_preview(request, client_name, seller_name, src_id, job_id)
            #return article_preview(request, client_name, seller_name, src_id, job_id)
        elif request.POST.get("content_preview") == 'Back':
            #parsed_excel_json = request.POST.get('parsed_excel_json', None)
        #    return content_preview(request, client_name, seller_name, updates = parsed_excel_json)
            job_id = request.POST.get('job_id', None)
            return content_preview(request, client_name, seller_name, job_id=job_id)
            
        elif request.POST.get("update") == 'Confirm':
            #path_to_save = request.POST.get("path_to_save")
#            parsed_excel_json = request.POST.get("parsed_excel_json")
            job_id = request.POST.get('job_id', None)
#            errors = write_content_updates(client_id, parsed_excel_json)
#            if errors:
#                errors.append(['An error occured while updating to database, please try again or contact the developer.'])
#                form = FileUploadForm()
#                flag = 'new'
#            else:    
            content_dict = {
                'clients':clients,
                'loggedin':True,
                'accounts':accounts,
                'url':request.get_full_path(),
                'client_name':client_name,
                'seller_name':seller_name,
                'job_id':job_id,
                }
            entries = ContentVersionTable.objects.filter(job=job_id)
            for entry in entries:
                entry.status = 'previewed'
                entry.save()
            return render_to_response('content/content_job_approved.html', content_dict, context_instance=RequestContext(request))
        elif request.POST.get("deny") == 'Deny':
            form = FileUploadForm()
            flag = 'new'
    else:
        form = FileUploadForm()
        flag = 'new'
    content_dict = {
        'clients':clients,
        'loggedin':True,
        'accounts':accounts,
        'url':request.get_full_path(),
        'client_name':client_name,
        'seller_name':seller_name,
        'forms' : form,
        'errors' : errors,
        'flag' : flag,
        'path_to_save' : path_to_save,
        }
    
    return render_to_response('content/content_upload.html', content_dict, context_instance=RequestContext(request))

    
def save_uploaded_file(f):
    path_to_save = get_temporary_file_path()
    fp = open(path_to_save, 'w')
    for chunk in f.chunks():
        fp.write(chunk)
    fp.close()
    return path_to_save
 
def get_temporary_file_path():
    import tempfile
    tf = tempfile.NamedTemporaryFile()
    path = tf.name
    tf.close()
    return path

def article_preview(request, client_name, seller_name, src_id, job_id, **kwargs):
    client_name = slugify(client_name)
    seller_name = slugify(seller_name)
    url = request.get_full_path()
    if request.method == "POST":
        check = request.POST.get('name', None)
        try:
            new_client_name=request.POST['user_clients']
        except:
            new_client_name=client_name
        if new_client_name != client_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('article-preview',None,kwargs={'client_name':new_client_name,'seller_name':'all-sellers', 'article_id':article_id}))
        try:
            new_seller_name=request.POST['user_sellers']
        except:
            new_seller_name="All Sellers"
        if new_seller_name!=seller_name:
            if check == "change":
                return HttpResponsePermanentRedirect(reverse('article-preview',None,kwargs={'client_name':client_name,'seller_name':new_seller_name, 'article_id':article_id}))    
    profile = request.user.get_profile()
    accounts = profile.managed_accounts.filter(client__slug = client_name)
        
    #getting ids from client_name and seller_name
    client = Client.objects.filter(slug=client_name)
    if client:
        client_id = client[0].id
    else:
        return HttpResponsePermanentRedirect(reverse('article-preview',None,kwargs={'client_name':profile.managed_clients[0].slug,'seller_name':'all-sellers', 'article_id':article_id}))

    if seller_name=='all-sellers':
        return HttpResponsePermanentRedirect(reverse('article-preview',None,kwargs={'client_name':client_name,'seller_name':slugify(accounts[0].name), 'article_id':article_id}))
    else:
        seller = Account.objects.select_related('id').filter(slug=seller_name, client__slug=client_name)   
        if seller:
            seller = seller[0]
            current_seller_id = seller.id
        else:
            return HttpResponsePermanentRedirect(reverse('article-preview',None,kwargs={'client_name':client_name,'seller_name':'all-sellers', 'article_id':article_id}))
    clients = profile.managed_clients()
#    parsed_excel_json = kwargs['updates']
#    to_update = simplejson.loads(parsed_excel_json)
    version_entry = ContentVersionTable.objects.get(job=job_id, article=src_id)
    errors, parsed_data = get_parsed_XML_content(version_entry.xml_content)
    print "%%%%%%%%%%%    ", errors, "  %%%%%%%%%%%%%%   ", parsed_data
    if errors:
        final_dict = {
            'clients':clients,
            'loggedin':True,
            'accounts':accounts,
            'url':request.get_full_path(),
            'client_name':client_name,
            'job_id':job_id,
            'seller_name':seller_name,
            }
        return render_to_response('content/article_preview.html', final_dict, context_instance=RequestContext(request))

    article_dict = preview_content_for_article(parsed_data)
    final_dict = {
        'clients':clients,
        'loggedin':True,
        'accounts':accounts,
        'url':request.get_full_path(),
        'client_name':client_name,
        'job_id':job_id,
        'seller_name':seller_name,
        }
    final_dict.update(article_dict) 
    return render_to_response('content/article_preview.html', final_dict, context_instance=RequestContext(request))

def write_content_updates(client_name, parsed_excel_json):
    errors = []
    to_update = simplejson.loads(parsed_excel_json)
    #Writing content updates to DB
    for entry in to_update:
        if selected_article == entry['article_id']:
            article_dict = entry
    prod_type = ProductType.objects.filter(type=article_dict['product_type'])[0]
    feature_grp = FeatureGroup.objects.filter(product_type = prod_type).order_by('sort_order')
#    for feature in entry['features']

    return errors

def select_article():
    #to render article select page for preview
    pass

#def preview_content_for_article(request, selected_article, to_update):
def preview_content_for_article(to_update):
#    for entry in to_update:
#        if selected_article == entry['article_id']:
#            article_dict = entry
    article_dict = to_update[0]        
    prod_type = ProductType.objects.filter(type=article_dict['product_type'])[0]
    feature_grp = FeatureGroup.objects.filter(product_type = prod_type).order_by('sort_order')
    #Fetching all set of features for product type
    features_set = prod_type.feature_set.all()
    datas = []
    features_dict = article_dict['features']
    keys = []
    for k in features_dict.keys():
        keys.append(k)
    #Get feature objects from feature_dict
#    features = product.productfeatures_set.select_related(
#        'feature',
#        'feature__group').all().order_by(
#        'feature__group__sort_order', 
#        'feature__sort_order')
    for grp in feature_grp:
        data = []
        for feature in features_set:
            key = slugify(feature.name)
            if key in keys:
                pass
            else:
                continue
            if not feature.group:
            # No feature group is assigned, so do not display the feature
                continue
            if feature.group.id != grp.id:
            # The feature does not belong to this current feature group    
                continue
            feature_content = {}
            content = ''
            if feature.type == 'number':
                try:
                    content = ("%.1f" % features_dict[key]).replace('.0','')  + ' ' + feature.unit.name
                except:
                    content = ("%.1f" % features_dict[key]).replace('.0','')
            elif feature.type == 'text':
                try:
                    content = features_dict[key]
                except:
                    pass
            elif feature.type == 'boolean':
            #Handle boolean features here, leavig for now
                if features_dict[key]=='TRUE' or features_dict[key]==1 or features_dict[key]=="Yes":
                    content = 'Yes'
                else:
                    content = 'No'
            try:
                feature_content = dict(name=feature.name,value=content)
            except:
                pass
            data.append(feature_content)
        group = {}
        group['name'] = grp.name
        group['features'] = data
        if features_set and data:
            datas.append(group)
        else:
        #If feature in not specified on content upload
            pass
            
    final_dict = {
        #'clients':clients,
        'loggedin':True,
       # 'accounts':accounts,
       # 'url':request.get_full_path(),
       # 'client_name':client_name,
       # 'seller_name':seller_name,
        'datas':datas,
       # 'product_name':article_dict['producttitle'],
       # 'show_title':show_title,
        'article_id':article_dict['article_id'],
        }       
    #Also pass the to_update as hidden parameter for persistence    
#    return render_to_response('content/article_preview.html', final_dict, context_instance=RequestContext(request))
    return final_dict

def get_parsed_XML_content(xml_str):
    # Only 1 article
#    xmldoc = etree.parse(xml_str)
    xmldoc = etree.parse(StringIO(xml_str))
    errors, to_update = [], []
    article_dict = {}
    for article in xmldoc.xpath('/products/article'): 
        article_id = article.xpath('_article-id')[0].text
        artilce_id = article_id.split('.')[0]
        article_dict['article_id'] = article_id
        #Check if article exists for the client else create it 
        #item = SellerRateChart.objects.filter(article_id=article_id)
        #getting product type of each article
        prod_type_name = article.xpath('_product-type')[0].text
            
        #Populate feature list for product type to be checked in XML
        prod_type = ProductType.objects.filter(type=prod_type_name)
        if prod_type:
            article_dict['product_type'] = prod_type_name
        else:
            errors.append(["Product type for article %s entered does not exist." % article_id])
            return errors, to_update
        prod_type=prod_type[0]    
        features_set = prod_type.feature_set.all()

        feature_list = []
        for feature in features_set:
            #Getting expected feature list for XML by slugifying feature names
            feature_list.append(slugify(feature.name))
#        feature_list.remove('3g')
#        feature_list.append('in3g')
        features_dict = {}
        for feat in feature_list:
            feat = "_" + feat
            try:
                #Insert features only if they are not empty
                feat_val = article.xpath(feat)[0].text
                if feat_val and feat_val != "":
                    feat = feat[1:len(feat)]
                    features_dict[feat] = feat_val
            except:
                errors.append(["Inappropriate excel headers/Missing Fields corresponding to Product Type %s for Article ID %s and field %s" % (prod_type_name, article_id, feat)])
                return errors, to_update
        article_dict['features'] = features_dict
        #Populate to update dict
        to_update.append(article_dict)
    return errors, to_update

def validate_and_split_xml(request, path_to_save):
    errors = []
    to_update = []
    # To do XML validation by XSD here
    #xsd_path = 
    xsd_path = "/home/ravi/Desktop/Content/mobile.xsd"

    schema_root = etree.parse(xsd_path)
    schema = etree.XMLSchema(schema_root)

    parser = etree.XMLParser(schema = schema)
    try: 
        try:
            xmldoc = etree.parse(path_to_save, parser)
        except etree.XMLSyntaxError, e:    
            errors.append([str(e)])
            errors.append(["XML failed validation against XSD. Please recheck your XML."])
            return errors, None
        
       #Checking basic sanity and required fields of uploaded xml 
        article_list = []
        for article in xmldoc.xpath('/products/article'): 
            try:
                article_id = article.xpath('_article-id')[0].text
                artilce_id = article_id.split('.')[0]
            except Exception,e:
                errors.append([str(e)])
                errors.append(["Article ID not entered for one of the products"])
                return errors, None
            #Check if article exists for the client else create it 
            item = SellerRateChart.objects.filter(article_id=article_id)
            if not item:
                errors.append(["Article ID %s is not present in Database, Please request entry for the article ID first " % article_id])
                return errors, None
            item = item[0]
            #getting product type of each article
            try:
                prod_type_name = article.xpath('_product-type')[0].text
                prod_type = ProductType.objects.filter(type=prod_type_name)
                if not prod_type:
                    errors.append(["Product type for article %s entered does not exist." % article_id])
                    return errors, None
                prod_type = prod_type[0]
                prod = item.product
                
                if not prod.product_type:
                    errors.append(["Product type has not been assigned for article %s. Kindly ask Futurebazaar team to rectify this." % article_id])
                    return errors, None

                if prod.product_type != prod_type:
                    errors.append(["Mismatch in Product type %s for article ID %s. There is a different product type (%s)  assigned to this article in database" % (prod_type_name, article_id, prod.product_type.name)])
                    return errors, None

            except Exception, e:
                errors.append([str(e)])
                errors.append(["Product type not assigned to article %s" % article_id])
                return errors, None
                
            #Checking for duplicate entries
            if article_id in article_list:
                errors.append(['Duplicate content entry for Articleid: %s !!! Please correct the error and and try to upload again!!!' % article_id])
                return errors, None
            else:
                article_list.append(article_id)
        f = open(path_to_save)
        xml_str = f.read()
        job = ContentJob() 
        job.user = request.user
        job.xml_content = xml_str
        job.save()
        start = 1
        i = 0

        while "<article>" in xml_str:
#            article_xml = "<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<products>\n" 
            article_xml = "<products>\n"

            article_xml = article_xml + xml_str[xml_str.find("<article>"):xml_str.find("</article>")+len("</article>")]
            article_xml = article_xml + "\n</products>"
            article_id = xmldoc.xpath('/products/article')[i].xpath('_article-id')[0].text
            article_id = article_id.split(".")[0]
            # XML uploaded, changed state to new
            version_entry = ContentVersionTable()
            product = SellerRateChart.objects.filter(article_id=article_id)

            if product:
                product = product[0]
            else:
                errors.append(['Article ID entered was not found in database, please recheck for article id: %s !' % article_id])
                raise Exception

            version_entry.article = product
            version_entry.job = job
            version_entry.status = "new"
            version_entry.xml_content = article_xml
            version_entry.save()
            user_log = ContentUserLog()
            user_log.reference_job = version_entry
            user_log.user = request.user
            user_log.old_state = None
            user_log.new_state = "new"
            user_log.comments = None
            user_log.save()
            i = i+1
            xml_str = xml_str.replace('<article>','<done>',1)
            xml_str = xml_str.replace("</article>","</done>", 1)
        return errors, job
    except Exception, e:
        log.info('Failed XML upload, Error is --------------- %s' % str(e))
        job.delete()
        errors.append(['XML upload has failed. Please try again'])
        return errors, None 

