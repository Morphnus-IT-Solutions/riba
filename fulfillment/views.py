from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader
from django.http import Http404, HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect
from django.contrib.auth.decorators import *
from django.contrib.auth.models import *
from django.contrib.auth import login as auth_login
from django.contrib  import auth
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.conf import settings
from django import forms
from users.models import *
from orders.models import *
from accounts.models import *
from catalog.models import *
from categories.models import *
from fulfillment.models import *
from users.forms import *
from accounts.forms import *
#from accounts.forms importseller_namefrom locations.forms import *
from utils import utils
from utils.utils import getPaginationContext, check_dates, create_context_for_search_results, get_excel_status, save_excel_file
from web.forms import *
from web.models import *
from web.views.pricing_views import all_prices, upload_price_xls, save_uploaded_file, get_temporary_file_path
import re
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from ppd.decorators import check_role
import xlrd
from xlrd import XLRDError
from lists.models import List, ListItem
from restapi import APIManager
from django.utils import simplejson

def lsp_view(action, content):
    action = action.lower()
    errors = []
    updates = []
    try:
        lsps = Lsp.objects.all()
        if action == 'view':
            header_list = ['Lsp name','Lsp Code'] 
            lsp_list = []
            for lsp in lsps:
                lsp_list.append([lsp.name, lsp.code])
            return lsp_list, header_list
		
        elif action == 'insert':
            for item in content:
                err = []
                try:
                    lsp = Lsp.objects.get(code=item['lsp_code'])
                    err = 'Lsp with code %s already exists in database' % lsp.code
                    errors.append(err)
                except:
                    p = Lsp()
                    p.code = item['lsp_code']
                    p.name = item['lsp_name']
                    p.save()
            return errors, updates 
                  
        else:
            errors.append('This action is not supported!!')
            return errors 
    except Exception, e:
       s = str(e) + "Something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 
        
def dc_view(action, content):
    action = action.lower()
    errors = []
    updates = []
    try:
        dcs = Dc.objects.select_related('client')
        if action == 'view':
            header_list = ['Dc name','Dc Code','Client','Cod flag','Dc Address'] 
            dc_list = []
            for dc in dcs:
                dc_list.append([dc.name, dc.code, dc.client.name, dc.cod_flag, dc.address])
            return dc_list, header_list
        
        elif action == 'insert':
            for item in content:
                err = []
                try:
                    dcs = Dc.objects.get(code=item['code'], client=item['client'])
                    err = 'DC with code %s and client %s already exists in database' % (dc.code, dc.client.name)
                    errors.append(str(err))
                except Exception, e:
                    p = Dc()
                    p.code = item['code']
                    p.name = item['name']
                    p.address = item['address']
                    if item['cod'] == "1":
                        p.cod_flag = True
                    else:
                        p.cod_flag = False
                    p.client = item['client']
                    p.save()
            return errors, updates 
        
        else:
            errors.append('This action is not supported!!')
            return errors
    except Exception,e:
       s = str(e) + "Something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 

def dc_local(action, content):
    action = action.lower()
    errors = []
    updates = []
    try:
        dc_locals = DcZipgroup.objects.select_related('zipgroup__lsp','dc')
        if action == 'view':
            header_list = ['DC Code','Zipgroup Code','LSP Code'] 
            dc_local_list = []
            for dc_local in dc_locals:
                dc_local_list.append([dc_local.dc.code, dc_local.zipgroup.zipgroup_code, dc_local.zipgroup.lsp.code])
            return dc_local_list, header_list
        
        elif action == 'insert':
            for item in content:
                err = ""
                try:
                    dc_local = DcZipgroup.objects.get(dc__code=item['dc'], zipgroup__zipgroup_code=item['zipgroup'])
                    err = 'DC with code %s  already has entry for zipgroup %s' % (dc_local.dc.code, dc_local.zipgroup.zipgroup_code)
                    errors.append(str(err))
                except:
                    try:
                        ls = Lsp.objects.get(code=item['lsp'])                            
                        dco = Dc.objects.get(code=item['dc'], client=item['client'])
                        zips = LspZipgroup.objects.get(zipgroup_code=item['zipgroup'])
                        p = DcZipgroup()
                        p.lsp = ls 
                        p.dc = dco
                        p.zipgroup = zips
                        p.save()
                    except Exception,e:
                        err = 'Dc %s Zipgroup %s or Lsp %s does not exist!' % (item['dc'], item['zipgroup'], item['lsp'])
                        errors.append(str(err))
            return errors, updates 
        else:
            errors.append('This action is not supported!!')
    except Exception,e:
       s = str(e) + "Something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 

def zip_lsp(action, content):
    action = action.lower()
    errors = []
    updates = []
    try:
        ziplsps = LspZipgroup.objects.select_related('lsp')
        if action == 'view':
            header_list = ['LSP Code','Zipgroup Code','Zipgroup Name',] 
            ziplsp_list = []
            for ziplsp in ziplsps:
                ziplsp_list.append([ziplsp.lsp.code, ziplsp.zipgroup_code, ziplsp.zipgroup_name])
            return ziplsp_list, header_list
        elif action == 'insert':
            for item in content:
                err = []
                try:
                    ziplsp = LspZipgroup.objects.get(lsp__code=item['lsp'], zipgroup_code=item['zipcode'])
                    err = 'Zipgroup with code %s  already has entry for Lsp %s' % (item['zipcode'], item['lsp'])
                    errors.append(str(err))
                except:
                    p = LspZipgroup()
                    p.zipgroup_name = item['zipname']
                    p.zipgroup_code = item['zipcode']
                    
                    try:
                        ls = Lsp.objects.get(code=item['lsp'])
                        p.lsp = ls
                        p.save()
                    except Exception,e:
                        err = 'Lsp %s does not exist!, error with Zipgroup %s Zipcode %s' % (item['lsp'], item['zipname'], item['zipcode'])
                        errors.append(str(err))
            return errors, updates 
        else:
            errors.append('This action is not supported!!')    
    except Exception,e:
       s = str(e) + "Something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 

def pin_zip(action, content, params_dict):
    action = action.lower()
    errors = []
    updates = []
    try:
        if action == 'view':
            page = params_dict['page'] 
            pin = params_dict['pincode'] 
            lsp_code = params_dict['lsp_code'] 
            zip_code = params_dict['zipgroup_code'] 
            pinzips = PincodeZipgroupMap.objects.all().select_related('zipgroup__lsp')
            if pin or lsp_code or zip_code:
                if pin:
                    pinzips = pinzips.filter(pincode=pin)
                if lsp_code:
                    pinzips = pinzips.filter(zipgroup__lsp__code=lsp_code)
                if zip_code:
                    pinzips = pinzips.filter(zipgroup__zipgroup_code=zip_code)
            else:
                pinzips = PincodeZipgroupMap.objects.select_related('zipgroup__lsp')[(page-1)*100:page*100]
            header_list = ['Pincode','Zipgroup Code','LSP_Code','LSP Priority','COD Flag','HighValue Flag','Supported ProductGroup'] 
            pinzip_list = []
            for pinzip in pinzips:
                pinzip_list.append([pinzip.pincode, pinzip.zipgroup.zipgroup_code, pinzip.zipgroup.lsp.code, pinzip.lsp_priority, pinzip.cod_flag, pinzip.high_value, pinzip.supported_product_groups,])
            return pinzip_list, header_list
        elif action == 'update' or action == 'delete' or action == 'insert':
            for item in content:
                err = []
                pinzip = None
                try:
                    pinzip = PincodeZipgroupMap.objects.get(pincode=item['pincode'], zipgroup__zipgroup_code=item['zipgroup'], zipgroup__lsp__code=item['lsp'])
                except:
                    pass
                if action == 'insert':
                    if pinzip:
                        err = 'Entry already exists for Pincode %s Zipgroup code %s Lsp %s' % (item['pincode'], item['zipgroup'], item['lsp']) 
                        errors.append(str(err))
                    else:
                        p = PincodeZipgroupMap()
                        p.pincode = item['pincode']
                        if item['cod'] == "1":
                            p.cod_flag = True
                        else:
                            p.cod_flag = False
                        if item['high_val'] == "1":
                            p.high_value = True
                        else:
                            p.high_value = False
                        p.lsp_priority = item['lsp_priority'] 
                        p.supported_product_groups = item['prod_grps']
                        try:
                            zipgrp = LspZipgroup.objects.get(lsp__code=item['lsp'], zipgroup_code=item['zipgroup'])
                            p.zipgroup = zipgrp
                            p.save()
                        except:
                            err = 'Zipgroup code %s and LSP % combination does not exist!' % (item['zipgroup'], item['lsp'])
                            errors.append(str(err))
                elif action == 'update':
                    #Note that only Product groups, Lsp priority COD flag and High value can be updated
                    if not pinzip:
                        err = 'Entry does not exist for Pincode %s Zipgroup code %s Lsp %s, hence update is not possible. Note that Product Groups, High value flag, LSP priority and COD flag fields can be updated.' % (item['pincode'], item['zipgroup'], item['lsp']) 
                        errors.append(str(err))
                    else:
                        p = pinzip
                        p.lsp_priority = item['lsp_priority'] 
                        p.supported_product_groups = item['prod_grps']
                        if item['cod'] == "1":
                            p.cod_flag = True
                        else:
                            p.cod_flag = False
                        if item['high_val'] == "1":
                            p.high_value = True
                        else:
                            p.high_value = False
                        p.save()
                elif action == 'delete':
                    # Deletion based on Pincode, Lsp, Zipgroup 
                    if not pinzip:
                        err = 'Entry does not exist for Pincode %s Zipgroup code %s Lsp %s, hence delete is not possible.' % (item['pincode'], item['zipgroup'], item['lsp']) 
                        errors.append(str(err))
                    else:
                        pinzip.delete()
        return errors, updates 
    except Exception,e:
       s = str(e) + "Something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 

def prod_grp_view( action, content):
    action = action.lower()
    errors = []
    updates = []
    try:
        prodgrps = ProductGroup.objects.select_related('client')
        if action == 'view':
            header_list = ['ProductGroup', 'ProductGroup Name', 'ShipLocal Flag', 'Transport Mode', 'HighValue Flag', 'Threshold Value','Client'] 
            prodgrp_list = []
            for prodgrp in prodgrps:
                prodgrp_list.append([prodgrp.name, prodgrp.description, prodgrp.local_tag, prodgrp.ship_mode, prodgrp.high_value_flag, prodgrp.threshold_amount, prodgrp.client.name])
            
            return prodgrp_list, header_list
        elif action == 'insert':
            for item in content:
                err = []
                try:
                    prodgrp = ProductGroup.objects.get(name=item['prod_grp_id'])
                    err = 'Product Group %s already exists' % prodgrp.name
                    errors.append(str(err))
                except: 
                    p = ProductGroup()
                    p.name = item['prod_grp_id']
                    p.description = item['prod_grp_name']
                    p.client = item['client']
                    if item['ship_local'] == "1":
                        p.local_tag = True
                    else:
                        p.local_tag = False
                    if item['high_val'] == "1":
                        p.high_value_flag = True
                    else:
                        p.high_value_flag = False
                    p.ship_mode = item['transport_mode']
                    p.threshold_amount = item['threshold_amt']
                    p.save()
            return errors, updates 
        else:
            errors.append('This action is not supported!!')
    except Exception,e:
       s = str(e) + "Something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 

def article_prod_grp(action, content, params_dict):
    action = action.lower()
    errors = []
    updates = []
    try:
        if action == 'view':
            page = params_dict['page'] 
            articleid = params_dict['article_id'] 
            prod_grp = params_dict['prod_grp'] 
            art_prods = ArticleProductgroup.objects.all().select_related('product_group')
            if articleid or prod_grp:
                if articleid:
                    art_prods = art_prods.filter(article_id=articleid)
                if prod_grp:
                    art_prods = art_prods.filter(product_group__name=prod_grp)
            else:
                art_prods = ArticleProductgroup.objects.select_related('product_group')[(page-1)*100:page*100]
            header_list = ['SAP Article','ProductGroup'] 
            art_prod_list = []
            for art_prod in art_prods:
               art_prod_list.append([art_prod.article_id, art_prod.product_group,])
            return art_prod_list, header_list
        elif action == 'update' or action == 'delete' or action == 'insert':
            for item in content:
                err = ""
                art_prod = None
                try:
                    art_prod  = ArticleProductgroup.objects.get(article_id=item['articleid'])
                except:
                    pass
                if action == 'insert':
                    if art_prod:
                        err = 'Article %s is already mapped to Product Group  %s' % (art_prod.article_id, art_prod.product_group)
                        errors.append(str(err))
                    else:
                        p = ArticleProductgroup()
                        p.article_id = item['articleid']
                        try:
                            prod = ProductGroup.objects.get(name=item['prod_grp'], client=item['client'])
                            p.product_group = prod
                            p.save()
                        except:
                            err = 'Product Group  %s does not exist!' % item['prod_grp']
                            errors.append(str(err))
                elif action == 'update':
                    #Note that only change of Product Group for article is allowed
                    if not art_prod:
                        err = 'Article %s cannot be found in database!' % item['articleid']
                        errors.append(str(err))
                    else:
                        try:
                            prod = ProductGroup.objects.get(name=item['prod_grp'], client=item['client'])
                            p = art_prod
                            p.product_group = prod
                            p.save()
                        except:
                            err = 'Product Group  %s does not exist!' % item['prod_grp']
                            errors.append(err)
                elif action == 'delete':
                    # Only article based deletion allowed
                    if not art_prod:
                        err = 'Article %s cannot be found in database!' % item['articleid']
                        errors.append(err)
                    else:
                        art_prod.delete()
            return errors, updates 
    except Exception,e:
       s = str(e) + " -- something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 

def delv_chart(action, content, params_dict):
    errors = []
    updates = []
    action = action.lower()
    try:
        if action == 'view':
            page = params_dict['page'] 
            dc_code = params_dict['dc_code'] 
            lsp_code = params_dict['lsp_code'] 
            zip_code = params_dict['zipgroup_code'] 
            delv_charts = LspDeliveryChart.objects.all().select_related('zipgroup__lsp','dc')
            if dc_code or lsp_code or zip_code:
                if dc_code:
                    delv_charts = delv_charts.filter(dc__code=dc_code)
                if lsp_code:
                    delv_charts = delv_charts.filter(zipgroup__lsp__code=lsp_code)
                if zip_code:
                    delv_charts = delv_charts.filter(zipgroup__zipgroup_code=zip_code)
            else:
                delv_charts = LspDeliveryChart.objects.select_related('zipgroup__lsp','dc')[(page-1)*100:page*100]
            header_list = ['Dc Code','Zipgroup Code','LSP Code','Mode of Transport','Transit Time'] 
            delv_charts_list = []
            for delv_chart in delv_charts:
                delv_charts_list.append([delv_chart.dc.code, delv_chart.zipgroup.zipgroup_code, delv_chart.zipgroup.lsp.code, delv_chart.ship_mode, delv_chart.transit_time])
            return delv_charts_list, header_list
        
        elif action == 'update' or action == 'delete' or action == 'insert':
            for item in content:
                err = []
                delv_chart = None
                try:
                    delv_chart = LspDeliveryChart.objects.get(dc__code=item['dc'], zipgroup__zipgroup_code=item['zipgroup'], zipgroup__lsp__code=item['lsp'], ship_mode=item['transport_mode'])
                except:
                    pass
                if action == 'insert':
                    if delv_chart:
                        err = 'Entry already exists for Dc %s Zipgroup code %s Lsp %s Transportation mode %s' % (item['dc'], item['zipgroup'], item['lsp'], item['transport_mode']) 
                        errors.append(str(err))
                    else:
                        p = LspDeliveryChart()
                        p.ship_mode = item['transport_mode']
                        p.transit_time = item['delivery_time']
                        try:
                            dc = Dc.objects.get(code=item['dc'], client=item['client'])
                            zipgrp = LspZipgroup.objects.get(lsp__code=item['lsp'], zipgroup_code=item['zipgroup'])
                            p.dc = dc
                            p.zipgroup = zipgrp
                            p.save()
                        except:
                            err = 'Dc %s does not exist!' % item['dc']
                            errors.append(str(err))
                            err = 'Zipgroup code %s and LSP %s combination does not exist!' % (item['zipgroup'], item['lsp'])
                            errors.append(str(err))
                elif action == 'update':
                    #Note that only delivery time can be updated
                    if not delv_chart:
                        err = 'Entry does not exist for Dc %s Zipgroup code %s Lsp %s Transportation mode %s, hence update is not possible. Note that only Transit/Delivery time can be updated.' % (item['dc'], item['zipgroup'], item['lsp'], item['transport_mode']) 
                        errors.append(str(err))
                    else:
                        p = delv_chart 
                        p.transit_time = item['delivery_time']
                        p.save()
                elif action == 'delete':
                    # Deletion based on Dc, Lsp, Zipgroup and Transport mode combinations
                    if not delv_chart:
                        err = 'Entry does not exist for Dc %s Zipgroup code %s Lsp %s Transportation mode %s, hence delete is not possible.' % (item['dc'], item['zipgroup'], item['lsp'], item['transport_mode']) 
                        errors.append(str(err))
                    else:
                        delv_chart.delete()
            return errors, updates 
    except Exception,e:
       s = str(e) + "something unexpected has happened, please contact the developer to fix this or check your inputs carefully!"
       errors.append(s)
       return 
def ifs_table_action_map():
    action_list = ['View', 'Insert', 'Update', 'Delete']
    action_list_view = ['View','Insert']
    table_dict = {
        'Lsp_Master':action_list_view,
        'DC_Master':action_list_view,
        'DC_Zipgroup_LSP_Local_Ship':action_list_view,
        'Zipgroup_LSP_Map':action_list_view, 
        'Pincode_Zipgroup_Map':action_list,
        'ProductGroup_Master':action_list_view,
        'Article_ProductGroup_Map':action_list,
        'DC_Zipgroup_LSP_Map':action_list,
    }
    return table_dict

def ifs_select(request):
    table_dict = ifs_table_action_map() 
    selected_table = ''
    selected_action = ''
    if request.method == "POST":
        try:
            selected_table = request.POST['table']
        except:
            selected_table='Lsp_Master'
        try:
            selected_action = request.POST['action']
        except:
            selected_action = ['View']
        return HttpResponsePermanentRedirect(reverse('upload-ifs',None,kwargs={'selected_table':selected_table,'selected_action':selected_action}))

    return render_to_response('ifs/ifs_select.html',
            {
            'selected_table':selected_table,
            'table_dict':table_dict,
            },
            context_instance=RequestContext(request))            

def ifs_actions(request, selected_table, selected_action):
    title_table = selected_table.replace('_',' ')
    table_dict = ifs_table_action_map()
    content_list = []
    url = request.get_full_path()
    header_list = []
    display_list = []
    #When it enters the view for first time, flag is new
    flag = 'new' 
    content = {}    
    entries = 100
    pincode = ""
    zipgroup_code = ""
    lsp_code = ""
    article_id = ""
    prod_grp = "" 
    dc_code = ""
    pagination = {}
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    if selected_action.lower() == 'view':
        
        if selected_table.lower() == 'lsp_master':
             content_list, header_list = lsp_view(selected_action, content)
        elif selected_table == 'DC_Master':
             content_list, header_list = dc_view(selected_action, content)
        elif selected_table == 'DC_Zipgroup_LSP_Local_Ship':
             content_list, header_list = dc_local(selected_action, content)
        elif selected_table == 'Zipgroup_LSP_Map':
             content_list, header_list = zip_lsp(selected_action, content)
        elif selected_table == 'Pincode_Zipgroup_Map':
            count = PincodeZipgroupMap.objects.count()
            pincode = request.POST.get("pincode", "")
            lsp_code = request.POST.get("lsp_code", "")
            zipgroup_code = request.POST.get("zipgroup_code", "")
            params_dict = {'page':page, 'pincode':pincode, 'lsp_code':lsp_code, 'zipgroup_code':zipgroup_code }
            content_list, header_list = pin_zip(selected_action, content, params_dict)
            if not pincode and not lsp_code and not zipgroup_code:    
                paginator = Paginator(content_list, 1) # Show 30 items per page
                base_url = request.get_full_path()
                page_pattern = re.compile('[&?]page=\d+')
                base_url = page_pattern.sub('',base_url)
                page_pattern = re.compile('[&?]per_page=\d+')
                base_url = page_pattern.sub('',base_url)
                if base_url.find('?') == -1:
                    base_url = base_url + '?'
                else:
                    base_url = base_url + '&'
                pagination = getPaginationContext(page, (count/entries + 1), base_url) 
                try:
                   display_list = paginator.page(page)
                except (EmptyPage, InvalidPage):
                   display_list = paginator.page(paginator.num_pages)
        elif selected_table == 'ProductGroup_Master':
             content_list, header_list = prod_grp_view( selected_action, content)
        elif selected_table == 'Article_ProductGroup_Map':
             count = ArticleProductgroup.objects.count()
             article_id = request.POST.get("article_id", "")
             prod_grp = request.POST.get("prod_grp", "")
             params_dict = {'page':page, 'prod_grp':prod_grp, 'article_id':article_id, }
             content_list, header_list = article_prod_grp( selected_action, content, params_dict)
             if not article_id and not prod_grp:
                 paginator = Paginator(content_list, 1) # Show 30 items per page
                 base_url = request.get_full_path()
                 page_pattern = re.compile('[&?]page=\d+')
                 base_url = page_pattern.sub('',base_url)
                 page_pattern = re.compile('[&?]per_page=\d+')
                 base_url = page_pattern.sub('',base_url)
                 if base_url.find('?') == -1:
                     base_url = base_url + '?'
                 else:
                     base_url = base_url + '&'
                
                 pagination = getPaginationContext(page, (count/entries + 1), base_url) 
                 try:
                    display_list = paginator.page(page)
                 except (EmptyPage, InvalidPage):
                    display_list = paginator.page(paginator.num_pages)
        elif selected_table == 'DC_Zipgroup_LSP_Map':
             count = LspDeliveryChart.objects.count()
             dc_code = request.POST.get("dc_code", "")
             lsp_code = request.POST.get("lsp_code", "")
             zipgroup_code = request.POST.get("zipgroup_code", "")
             params_dict = {'page':page, 'dc_code':dc_code, 'lsp_code':lsp_code, 'zipgroup_code':zipgroup_code }
             content_list, header_list = delv_chart(selected_action, content, params_dict)
             if not dc_code and not lsp_code and not zipgroup_code:    
                 paginator = Paginator(content_list, 1) # Show 30 items per page
                 base_url = request.get_full_path()
                 page_pattern = re.compile('[&?]page=\d+')
                 base_url = page_pattern.sub('',base_url)
                 page_pattern = re.compile('[&?]per_page=\d+')
                 base_url = page_pattern.sub('',base_url)
                 if base_url.find('?') == -1:
                     base_url = base_url + '?'
                 else:
                     base_url = base_url + '&'
                
                 pagination = getPaginationContext(page, (count/entries + 1), base_url) 
                 try:
                    display_list = paginator.page(page)
                 except (EmptyPage, InvalidPage):
                    display_list = paginator.page(paginator.num_pages)
        
        return render_to_response('ifs/ifs_view.html',
            {
             'title_table':title_table,
             'lsp_code':lsp_code,
             'zipgroup_code':zipgroup_code,
             'pincode':pincode,
             'article_id':article_id,
             'prod_grp':prod_grp,
             'dc_code':dc_code,  
             'pagination':pagination,        
             'selected_action':selected_action,
             'display_list':display_list,
             'header_list':header_list,
             'content_list':content_list,
            },
            context_instance=RequestContext(request))   
    
    elif selected_action.lower() == 'update' or selected_action.lower() == 'insert' or selected_action.lower() == 'delete':
        from web.sbf_forms import FileUploadForm
        errors, message = [], None
        consolidated_updates = None
        form = None
        flag = None
        to_update = None
        path_to_save = None

        if request.method == 'POST':
            if request.POST.get("upload") == 'Upload':
                import xlrd
                form = FileUploadForm(request.POST, request.FILES)
                if form.is_valid():
                    path_to_save = save_uploaded_file(request.FILES['status_file'])
                    errors, consolidated_updates = get_ifs_updates(request, path_to_save, selected_table, selected_action, False)
                    if not errors:
                        flag = 'updated'
                    else:
                        flag='upload_errors'
                else:
                    errors.append(['Please select the excel file and then click upload!!!'])
                    form = FileUploadForm()
                    flag = 'new'

        else:
            form = FileUploadForm()
            flag = 'new'
            
        ifs_dict = {
            'forms' : form,
            'errors' : errors,
            'consolidated_updates' : consolidated_updates,
            'flag' : flag,
            'path_to_save' : path_to_save,
            'title_table':title_table,
            'selected_action':selected_action,
            #'header_list':header_list,
            #'content_list':content_list,
            }
        return render_to_response('ifs/ifs_upload.html', ifs_dict, context_instance=RequestContext(request))  

@login_required    
@check_role('Fulfillment')
def fulfillment_check(request):
    errors = []
    input_fault = ""
    if request.method == 'POST':
        pincode = request.POST['pincode']
        paytype = request.POST['paytype']
        article_id = request.POST['article_id']
        skuId = request.POST['skuId']
        quantity = request.POST['quantity']
        flag = "submitted"
        if paytype == 'cod':
            isCod = 1
        else:
            isCod = 0
        input_fault = validate_fulfillment_input(pincode, article_id, skuId, quantity)
        client_id = request.client.client.id
        if skuId:
            prods = SellerRateChart.objects.filter(sku=skuId, seller__client=request.client.client)
            if prods:
                article_id = prods[0].article_id
            else:
                input_fault = input_fault + "Product with entered Sku/Article Id does not exist."
        elif article_id:
            prods = SellerRateChart.objects.filter(article_id=article_id, seller__client=request.client.client)
            if prods:
                skuId = prods[0].sku
            else:
                input_fault = input_fault + "Product with entered Sku/Article Id does not exist."
        else:    
            input_fault = input_fault + "Product with entered Sku/Article Id does not exist."
        if input_fault:
            errors.append(input_fault)
            ifserr_dict = {'loggedin':True, 
                'errors':errors, 
                'flag':flag,
                'skuId':skuId,
                'pincode':pincode,
                'url':request.get_full_path(),
                'article_id':article_id,
                'paytype':paytype,
                'quantity':quantity,
                }
            return render_to_response('ifs/fulfillment_check.html', ifserr_dict, context_instance=RequestContext(request))
        from orders.check_availability import check_availability_new
        json_response = check_availability_new(article_id, prods[0].id, pincode, quantity, request.client.client.id, isCod)
        log.info('Checking availability for %s: %s' % (article_id, json_response))
        try:
            if not json_response or not json_response['responseCode'].lower()=='success':
                if not json_response:
                    errors.append('Did not receive a response in API call! Could not connect via Restful Web service!')
                elif not json_response['responseCode'].lower()=='success':
                    errDisp = errorDesc(json_response['responseCode'])
                    errors.append(errDisp)
                    errors.append('Sorry. We cannot ship %s to %s' % (article_id, pincode))            
                ifserr_dict = {'loggedin':True, 
                    'errors':errors, 
                    'flag':flag, 
                    'skuId':skuId,
                    'pincode':pincode,
                    'article_id':article_id,
                    'paytype':paytype,
                    'quantity':quantity,
                    }
                return render_to_response('ifs/fulfillment_check.html/', ifserr_dict, context_instance=RequestContext(request))
            ifs_bo = json_response['items']
            ifs_bo = ifs_bo[0]
            pinzips = PincodeZipgroupMap.objects.filter(pincode=pincode).select_related('zipgroup')
            zipgroups = []
            for zipgrp in pinzips:    
                zipgroups.append(zipgrp.zipgroup.zipgroup_name + " - " + zipgrp.zipgroup.zipgroup_code)
            primaryDCLsp = ifs_bo['primaryDCLSP'].split("_")
            #dcLspList = split_sequence(ifs_bo['dcLspSequence'])
            dcLspList = simplejson.loads(ifs_bo['dcLspSequence'])
            dcStockString = stringtoList(ifs_bo['dcStockString'])
            dcPhysicalStockString = stringtoList(ifs_bo['dcPhysicalStockString'])
            dclsp = primaryDCLsp[0]+"-"+primaryDCLsp[1]
           # json_response['status_code'], 
           # json_response['status'], 
           # json_response['status_message'], 
           # json_response['num_returned'], 
           # json_response['num_found'], 
           # json_response['errors'], 
           # json_response['startIndex'],
           # print ifs_bo['skuID'], 
            fulfillment_dict = {
                'skuId':skuId,
                'productgroup':ifs_bo['productGroup'],
                'isHighValue':ifs_bo['isHighValue'],
                'primaryDCLsp':dclsp,
                'totalDeliveryTime':ifs_bo['totalDeliveryTime'], 
                'isBackorderable':ifs_bo['isBackorderable'], 
                'defaultDC':ifs_bo['defaultDC'], 
                'deliveryTime':ifs_bo['deliveryTime'], 
                'totalQuantityFound':ifs_bo['totalQuantityFound'], 
                'dcStockString':dcStockString,
                'dcPhysicalStockString':dcPhysicalStockString,
                'inventoryTime':ifs_bo['inventoryTime'],
                'flfMessages':ifs_bo['flfMessages'], 
                'isShipLocalOnly':ifs_bo['isShipLocalOnly'], 
                'isInvCheck':ifs_bo['isInvCheck'], 
                'dcLspSequence':dcLspList, 
                'modeOfTransport':ifs_bo['modeOfTransport'], 
                'isAllQuantityFulfilled':ifs_bo['isAllQuantityFulfilled'],
                'zipgroups':zipgroups,
                'flag':flag,
                'pincode':pincode,
                'article_id':article_id,
                'paytype':paytype,
                'quantity':quantity,
                'errors':errors,
            }
        except KeyError, e:
            errors.append('Unexpected response received from IFS API.')
            errors.append(repr(e))
            fulfillment_dict = {
                'skuId':skuId,
                'pincode':pincode,
                'article_id':article_id,
                'paytype':paytype,
                'quantity':quantity,
                'errors':errors,
            }
        except Exception,e:
            errors.append('An unexpected error has occured, please contact developer with the reference error below.')
            errors.append(repr(e))
            fulfillment_dict = {
                'errors':errors,
            }
        return render_to_response('ifs/fulfillment_check.html', fulfillment_dict, context_instance=RequestContext(request))
    else:
    # Not post method    
        return render_to_response('ifs/fulfillment_check.html',
                 {},               
                 context_instance=RequestContext(request))

def get_ifs_updates(request, path_to_save, selected_table, selected_action, save_changes):
    import xlrd
    from django.db.models import Q
    book = xlrd.open_workbook(path_to_save)
    sh = book.sheet_by_index(0)
    header = sh.row(0)
    map = {}
    params_dict = {}
    idx = 0
    for idx in range(sh.ncols):
        map[header[idx].value.strip()] = idx
    errors = []
    err =[]
    to_update = []
    consolidated_updates = []
    action_dict = {True:'YES', False:'NO'}
    if_any_updates = False
    client_obj = request.client.client
    try:
        if selected_table.lower() == 'lsp_master':
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                lsp_name = row[map['LSP_Name']].value
                lsp_code = int(row[map['LSP_Code']].value)
            
                to_update.append({
                    'lsp_code': str(lsp_code).strip().split('.')[0],
                    'lsp_name': lsp_name.strip().lower(),
                })
            err, updates = lsp_view( selected_action, to_update)    
            if err:
                errors.append(err)
            else:
                pass
        elif selected_table == 'DC_Master':
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                name = row[map['DC_Name']].value
                code = int(row[map['DC_Code']].value)
                address = row[map['DC_Address']].value
                client = row[map['Client']].value 
                cod = row[map['COD_Flag']].value
                 
                to_update.append({
                    'code': str(code).strip().split('.')[0],
                    'name': name.strip().lower(),
                    'address': address.strip().lower(),
                    'cod': str(cod).strip().lower(),
                    'client':client_obj
                })
            err, updates = dc_view(selected_action, to_update)
            if err:
                errors.append(err)
            else:
                pass
                
        elif selected_table == 'DC_Zipgroup_LSP_Local_Ship':
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                lsp = int(row[map['LSP_Code']].value)
                dc = int(row[map['DC_Code']].value)
                zipgroup = int(row[map['Zipgroup_Code']].value)
                to_update.append({
                    'lsp': str(lsp).strip().split('.')[0],
                    'dc': str(dc).strip().split('.')[0],
                    'zipgroup': str(zipgroup).strip().split('.')[0],
                    'client':client_obj
                })
            err, updates = dc_local(selected_action, to_update)
            if err:
                errors.append(err)
            else:
                pass
        elif selected_table == 'Zipgroup_LSP_Map':
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                lsp = int(row[map['LSP_Code']].value)
                zipname = row[map['Zipgroup_Name']].value
                zipcode = int(row[map['Zipgroup_Code']].value)
                to_update.append({
                    'lsp': str(lsp).strip().split('.')[0],
                    'zipname': zipname.strip().lower(),
                    'zipcode': str(zipcode).strip().split('.')[0],
                    'client':client_obj
                })
            err, updates = zip_lsp( selected_action, to_update)
            if err:
                errors.append(err)
            else:
                pass
        elif selected_table == 'Pincode_Zipgroup_Map':
            prods = ProductGroup.objects.all()
            prod_list = []
            for prod in prods:
                prod_list.append(prod.name)
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                lsp = int(row[map['LSP_Code']].value)
                zipgroup = int(row[map['Zipgroup_Code']].value)
                pincode = int(row[map['Pincode']].value)
                cod = row[map['COD_Flag']].value
                high_val = row[map['HighValue_Flag']].value 
                lsp_priority = int(row[map['LSP_Priority']].value)
                prod_grps = str(row[map['Supported_ProductGroup']].value).replace(" ","")
                err = validate_prodgrps(prod_grps, prod_list) 
                err1 = validate_pincode(str(pincode))
                if not err and not err1:
                    to_update.append({
                        'lsp': str(lsp).strip().split('.')[0],
                        'zipgroup': str(zipgroup).strip().split('.')[0],
                        'pincode': str(pincode).strip().split('.')[0],
                        'cod': str(cod).strip().lower(),
                        'high_val': str(high_val).strip().lower(),   
                        'lsp_priority': lsp_priority,           
                        'prod_grps':prod_grps,
                        'client':client_obj
                     })
                else:
                    if err:
                        errors.append(err)
                    if err1:
                        errors.append(err1)
            err, updates = pin_zip( selected_action, to_update, params_dict)
            if err:
                errors.append(err)
            else:
                pass
        elif selected_table == 'ProductGroup_Master':
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                prod_grp_id = row[map['ProductGroup_ID']].value 
                prod_grp_name = row[map['ProductGroup_Name']].value 
                transport_mode = row[map['Transport_Mode']].value
                high_val = row[map['HighValue_Flag']].value 
                ship_local = row[map['ShipLocal_Flag']].value
                threshold_amt =  Decimal(str(row[map['Threshold_Value']].value))
                to_update.append({
                    'high_val': str(high_val).strip().lower(),   
                    'ship_local': str(ship_local).strip().lower(),   
                    'transport_mode': transport_mode.strip().lower(),   
                    'prod_grp_id':prod_grp_id,
                    'threshold_amt': str(threshold_amt).strip().split('.')[0],
                    'prod_grp_name':prod_grp_name,
                    'client':client_obj,
                 })
            err, updates = prod_grp_view(selected_action, to_update)    
            if err:
                errors.append(err)
            else:
                pass
        elif selected_table == 'Article_ProductGroup_Map':
            prods = ProductGroup.objects.all()
            prod_list = []
            for prod in prods:
                prod_list.append(prod.name)
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                articleid = int(row[map['SAP_Article_ID']].value)
                prod_grp = row[map['ProductGroup_ID']].value
                err = validate_prodgrp(prod_grp, prod_list)
                if not err:
                    to_update.append({
                        'articleid': str(articleid).strip().split('.')[0],
                        'prod_grp': str(prod_grp).strip().split('.')[0],
                        'client':client_obj,
                    })
                else:
                    errors.append(err)
            err, updates = article_prod_grp( selected_action, to_update, params_dict)
            if err:
                errors.append(err)
            else:
                pass
        elif selected_table == 'DC_Zipgroup_LSP_Map':
            for row_count in range(1, sh.nrows):
                row = sh.row(row_count)
                lsp = int(row[map['LSP_Code']].value)
                dc = int(row[map['DC_Code']].value)
                zipgroup = int(row[map['Zipgroup_Code']].value)
                transport_mode = row[map['Transport_Mode']].value
                delivery_time = int(row[map['Transit_Time']].value)
                to_update.append({
                    'transport_mode': transport_mode.strip().lower(),   
                    'lsp': str(lsp).strip().split('.')[0],
                    'dc': str(dc).strip().split('.')[0],
                    'zipgroup': str(zipgroup).strip().split('.')[0],
                    'delivery_time':delivery_time,
                    'client':client_obj
                })  
            err, updates = delv_chart(selected_action, to_update, params_dict)
            if err:
                errors.append(err)
            else:
                pass
    except KeyError:
        errors.append(['Unsupported excel file. Please check if headers are in the prescribed format.'])

    if to_update:
        pass
    else:
        log.info('No details found to upload in the sheet!!!')

    return errors, consolidated_updates

def validate_pincode(pin):
    errors = ""
    import re
    ptrn = re.compile('^[1-9]{1}[0-9]{5}$') 
    if ptrn.match(pin):
        return errors
    else:    
        errors = 'Invalid pincode. '
    return errors    

def validate_prodgrp(prod_grp, prod_list):
    errors = []
    import re
    ptrn = re.compile('^C\d+') 
    if ptrn.match(prod_grp):
        return
    else:    
        errors.append('Invalid Productgroup. ')
    return errors    

def validate_prodgrps(prod_grps, prod_list):
    result = 0
    err = []
    errors = []
    import re
    ptrn = re.compile('C\d+,')
    ptrn1 = re.compile('[\w,]+,$')
    grps = ptrn.finditer(prod_grps)
    for grp in grps:
        grp_name = grp.group().replace(",","")
        if grp_name in prod_list:
            result = result + 1
        else:
            log.info('Product group in Pincode Product group maping does not exist in Product Group master. ')
    if (not ptrn1.match(prod_grps)) or (result+1) != len(prod_grps.split(",")):
        err = "Error in Product group entry %s . " % prod_grps
        errors.append(err)
    return errors

def errorDesc(errorCode):
    errorCode = errorCode.lower()
    if errorCode == "err_prodgrp":
        errDesc = "Product group was not found for the given article"
        return errDesc
    elif errorCode == "err_inv":
        errDesc = "Inventory not found for the article."
        return errDesc
    elif errorCode == "err_local":
        errDesc = "Product is Ship-Local type, but the pincode does not come under local coverage area of any of the DCs. "
        return errDesc
    elif errorCode == "err_delv":
        errDesc = "No entry of DC, LSP and Pincode in LSP-DC-Zipgroup Map table (Delivery chart), hence cannot be delivered. "
        return errDesc
    elif errorCode == "err_inv_local":
        errDesc = "Inventory not available for Ship-local only case."
        return errDesc
    elif errorCode == "failure":
        errDesc = "Cannot fulfill - Failed."
        return errDesc
    elif errorCode == "err_cvg_area":
        errDesc = "This pincode doesnt come under our coverage area."
        return errDesc
    elif errorCode == "err_inv_cod":
        errDesc = "No LSP found for COD at the pincode."
        return errDesc
    elif errorCode == "err_lsp_hv":
        errDesc = "Cannot fulfill due to High value of Product."
        return errDesc
    elif errorCode == "err_lsp_cod":
        errDesc = "No LSP supports COD at this pincode."
        return errDesc
    elif errorCode == "err_inv_cod_local":
        errDesc = "Inventory not available for both COD and Ship Local case."
        return errDesc

def validate_fulfillment_input(pincode, article_id, skuId, quantity):
    s1 = ""
    s2 = ""
    s3 = ""
    s1 = validate_pincode(pincode)
    if not article_id.isdigit() and not skuId.isdigit():
        s2 = "\n Please enter correct Article or SKU ID."
    if not quantity.isdigit() or quantity=="0":   
        s3 = "\nPlease enter correct quantity."
    return (s1 + s2 + s3)

def skuToArticleId(skuId, prods):
    if prods:
        article_id = prods[0].article_id
        return article_id
    return ""

def stringtoList(s):
    if s == "" or s == None:
        return None
    list1 = s.split(',')
    finalList = []
    for ele in list1:
        element = ele.split("_")
        key1 = element[0]
        key2 = element[1]
        finalList.append([key1, key2])
    return finalList

def split_sequence(dcLspSequence):
    result = []
    for dcLsp in dcLspSequence:
        temp_list = []
    return
