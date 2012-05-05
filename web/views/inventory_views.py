from django.contrib.auth.decorators import login_required, permission_required
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
from utils.utils import getPaginationContext, check_dates, create_context_for_search_results, get_excel_status, save_excel_file, get_user_profile
from web.forms import *
from web.views.order_view import operator
from web.views.user_views import is_new_user, set_logged_in_user, set_eligible_user, user_order_details, show_agent_order_history
from web.views.pricing_views import all_prices, upload_price_xls
from decimal import Decimal, ROUND_UP
import operator
import gviz_api
import calendar
import re
import ast
import operator
from django.core.urlresolvers import reverse
from django.template.defaultfilters import slugify
from sellers.decorators import check_role
import simplejson
import xlrd
from xlrd import XLRDError

def get_temporary_file_path():
    import tempfile
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

def validate_number(number):
    try:
        if number.strip():
            number_float = float(number)
            return True
        else:
            return False
    except:
        return False

def validate_date(date):
    try:
        converted_date = datetime.datetime.strptime(date,'%d-%m-%Y %H:%M')
        return True
    except:
        return False

def get_date_in_string_format(date,hours,minutes):
    date_string = date + ' '

    if hours.strip():
        date_string += hours + ':'
    else:
        date_string += '00:'

    if minutes.strip():
        date_string += minutes
    else:
        date_string += '00'

    return date_string

def show_all_inventory_levels(request,client_name, seller_name,  seller, client_id, count, profile):
    #Show all the articles maintained for this client with increasing order of inventory levels.
    accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = account.client.id)
        cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)

    rate_chart = None
    skuid = ""
    article_id = ""
    searched_by = ""
    flag = ""
    inventory = None
    product_image = None
    update_dict = None
    is_clearance_item = False
    delivery_time = None
    errors = []
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = account.client.id)
        cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
    is_clearance_item = False
    all_inventory = None
    is_global_dc_supported = utils.is_global_dc_maintained(seller.client)
    
    article_id = request.GET.get("articleid")
    if not article_id and request.method == 'POST':
        article_id = request.POST.get("articleid")

    dc_id = request.GET.get("dc_id")
    if not dc_id and request.method == 'POST':
        dc_id = request.POST.get("dc_id")

    if article_id and dc_id:
        no_article_id_matching_entry = False
        no_sku_matching_entry = False
        try:
            rate_chart = SellerRateChart.objects.get(article_id=article_id.strip(), seller=seller)
            searched_by = 'article_id'
        except SellerRateChart.DoesNotExist:
            no_article_id_matching_entry = True
        except SellerRateChart.MultipleObjectsReturned:
            errors.append('Multiple articles maintained for Articleid - %s' % article_id)      

        try:
            rate_chart = SellerRateChart.objects.get(sku=article_id.strip(), seller=seller)
            searched_by = 'article_id'
        except SellerRateChart.DoesNotExist:
            no_sku_matching_entry = True
        except SellerRateChart.MultipleObjectsReturned:
            errors.append('Multiple articles maintained for Articleid - %s' % article_id)      

        if no_article_id_matching_entry and no_sku_matching_entry:
            errors.append('No active article maintained for Articleid or SKU : %s' % article_id)
        
        if rate_chart:
            flag = "searched"
            #First, handling catalog specific prices               
            try:
                inventory = Inventory.objects.get(rate_chart=rate_chart, dc__id=dc_id)
            except Inventory.DoesNotExist:
                dc = Dc.objects.get(id=dc_id)
                inventory = Inventory(rate_chart=rate_chart, dc=dc, stock=0)
                inventory.save()

            product_image = ProductImage.objects.filter(product=rate_chart.product)
            if product_image:
                product_image = product_image[0]

            clearance_list = None
            is_clearance_item = False
            
            if utils.get_future_ecom_prod() == seller.client:
                pass
            else:
                try:
                    clearance_list = List.objects.get(type='clearance', client=seller.client)
                except List.DoesNotExist:
                    log.info('Clearance list does not exist!!')

            if clearance_list:
                try:
                    listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
                    is_clearance_item = True
                except ListItem.DoesNotExist:
                    pass 

            if request.method == 'POST':
                check = request.POST.get('name',None)
                if check != 'change':
                    if rate_chart:
                        if request.POST.get("update") and request.POST.get("update") == "Update":
                            flag = "updated"
                            updated_stock = request.POST.get("stock","")
                            if validate_number(updated_stock):
                                updated_stock = Decimal(str(updated_stock).strip())
                            else:
                                errors.append('Wrong value entered for Physical Stock!!! Please go back and correct the value.')

                            if is_global_dc_supported:
                                updated_deliverytime = request.POST.get("delivery_time")

                                if int(str(updated_deliverytime)) == 0:
                                    errors.append('You cannot set delivery time to 0!!! Please go back and select appropriate value!!!')
                            else:
                                updated_virtual_stock = request.POST.get('virtual_stock','')
                                if updated_virtual_stock: 
                                    if validate_number(updated_virtual_stock):
                                        updated_virtual_stock = Decimal(str(updated_virtual_stock).strip())
                                    else:
                                        errors.append('Wrong value entered for Virtual Stock!!! Please go back and correct the value.')

                                updated_expected_on = request.POST.get('expected_on','')
                                if updated_expected_on:
                                    updated_expected_on = get_date_in_string_format(request.POST.get('expected_on'),request.POST.get('expected_on#hr'),request.POST.get('expected_on#min'))
                                    if validate_date(updated_expected_on):
                                        updated_expected_on = datetime.datetime.strptime(updated_expected_on,'%d-%m-%Y %H:%M')
                                    else:
                                        errors.append('Wrong value entered for Expected On!!! Please go back and correct the value.')

                                updated_expires_on = request.POST.get('expires_on','')
                                if updated_expires_on:
                                    updated_expires_on = get_date_in_string_format(request.POST.get('expires_on'),request.POST.get('expires_on#hr'),request.POST.get('expires_on#min'))
                                    if validate_date(updated_expires_on):
                                        updated_expires_on = datetime.datetime.strptime(updated_expires_on,'%d-%m-%Y %H:%M')
                                    else:
                                        errors.append('Wrong value entered for Expires On!!! Please go back and correct the value.')

                                if not ((updated_virtual_stock and updated_expected_on and updated_expires_on) or (not updated_virtual_stock and not updated_expected_on and not updated_expires_on)):
                                    errors.append('Please maintain values for all the three fields: "Virtual Stock", "Expected On" and "Expires On". [Note: If you do not want to maintain virtual stock, simply keep all the three fields blank!!!]')
                                else:
                                    if updated_expected_on and (updated_expected_on <= datetime.datetime.now()):
                                        errors.append('Please maintain "Expected On" as some future time!!!')
                                    if updated_expires_on and (updated_expires_on <= datetime.datetime.now()):
                                        errors.append('Please maintain "Expires On" as some future time!!!')

                                updated_threshold_stock = request.POST.get('threshold_stock','')
                                if updated_threshold_stock:
                                    if validate_number(updated_threshold_stock):
                                        updated_threshold_stock = Decimal(str(updated_threshold_stock).strip())
                                    else:
                                        errors.append('Wrong value entered for Threshold Stock!!! Please go back and correct the value.')

                            updated_so = False
                            if request.POST.get("so") == 'selected':
                                updated_so = True

                            updated_cod = False
                            if request.POST.get("cod") == 'selected':
                                updated_cod = True

                            updated_clearance = False
                            if request.POST.get("clearance") == 'selected':
                                updated_clearance = True

                            update_dict = {
                                'stock':Decimal(str(updated_stock).strip()),
                                'so':updated_so,
                                'cod':updated_cod,
                                'clearance':updated_clearance,
                                }

                            if is_global_dc_supported:
                                update_dict.update({'delivery_time':int(str(updated_deliverytime).strip())})
                            else:
                                extra_params = {
                                    'virtual_stock':updated_virtual_stock if updated_virtual_stock else None,
                                    'expires_on':updated_expires_on if updated_expires_on else None,
                                    'expected_on':updated_expected_on if updated_expected_on else None,
                                    'threshold_stock':updated_threshold_stock if updated_threshold_stock else None,
                                    }
                                update_dict.update(extra_params)

                        if request.POST.get("confirm") and request.POST.get("confirm") == "Confirm":
                            inventory_log = InventoryLog()
                            flag = "confirmed"
                            updated_stock = request.POST.get("stock")
                            inventory_log.was_physical_stock = inventory.stock
                            inventory_log.new_physical_stock = updated_stock
                            if is_global_dc_supported:
                                updated_deliverytime = request.POST.get("delivery_time")
                            else:
                                updated_virtual_stock = request.POST.get('virtual_stock','')
                                if updated_virtual_stock and updated_virtual_stock.strip() != 'None':
                                    updated_virtual_stock = Decimal(str(updated_virtual_stock.strip()))
                                else:
                                    updated_virtual_stock = None
                                inventory_log.was_virtual_stock = inventory.virtual_stock
                                inventory_log.new_virtual_stock = updated_virtual_stock

                                updated_expected_on = request.POST.get('expected_on','').strip()
                                if updated_expected_on and updated_expected_on != 'None':
                                    updated_expected_on = datetime.datetime.strptime(request.POST.get('expected_on'),'%Y-%m-%d %H:%M:%S')
                                inventory_log.was_expected_on = inventory.expected_on
                                inventory_log.new_expected_on = updated_expected_on if updated_expected_on else None

                                updated_expires_on = request.POST.get('expires_on','').strip()
                                if updated_expires_on and updated_expires_on != 'None':
                                    updated_expires_on = datetime.datetime.strptime(request.POST.get('expires_on'),'%Y-%m-%d %H:%M:%S')
                                inventory_log.was_expires_on = inventory.expires_on
                                inventory_log.new_expires_on = updated_expires_on if updated_expires_on else None

                                updated_threshold_stock = request.POST.get('threshold_stock','')
                                if updated_threshold_stock and updated_threshold_stock.strip() != 'None':
                                    updated_threshold_stock = Decimal(str(request.POST.get('threshold_stock')))
                                else:
                                    updated_threshold_stock = None
                                inventory_log.was_threshold_stock = inventory.threshold_stock
                                inventory_log.new_threshold_stock = updated_threshold_stock

                                inventory_log.rate_chart = inventory.rate_chart
                                inventory_log.dc = inventory.dc
                                inventory_log.was_overbooked = inventory.overbooked
                                inventory_log.new_overbooked = inventory.overbooked
                                inventory_log.user = request.user
                                inventory_log.modified_by = 'admin'

        #                    updated_otc = False
        #                    if request.POST.get("otc") == 'selected':
        #                        updated_otc = True

                            updated_so = False
                            if request.POST.get("so") == 'selected':
                                updated_so = True
                             
                            updated_cod = False
                            if request.POST.get("cod") == 'selected':
                                updated_cod = True               

                            inventory.stock = Decimal(str(updated_stock))
                            if not is_global_dc_supported:
                                inventory.virtual_stock = updated_virtual_stock
                                inventory.expected_on = updated_expected_on if updated_expected_on else None
                                inventory.expires_on = updated_expires_on if updated_expires_on else None
                                inventory.threshold_stock = updated_threshold_stock
                            inventory_log.save()
                            inventory.save()

        #                    delivery_time_obj.delivery_time = int(str(updated_deliverytime))
        #                    delivery_time_obj.save()

                            #rate_chart.otc = updated_otc
                            rate_chart.ship_local_only = updated_so
                            rate_chart.is_cod_available = updated_cod
                            if is_global_dc_supported:
                                rate_chart.shipping_duration = Decimal(str(updated_deliverytime))
                            if inventory.stock:
                                rate_chart.stock_status = 'instock'
                            else:
                                rate_chart.stock_status = 'outofstock'
                            
                            rate_chart.save()

                            #Update solr index.
                            product = rate_chart.product
                            product.update_solr_index()

                            if request.POST.get("clearance") == 'selected':
                                #Check whether product belongs to clearance sale or not
                                if clearance_list:
                                    try:
                                        listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
                                    except ListItem.DoesNotExist:
                                        #Listitem does not exist, so add new one
                                        max_seq = clearance_list.listitem_set.all().aggregate(max=Max('sequence'))
                                        listitem = ListItem(list=clearance_list, sku=rate_chart, sequence=max_seq.get('max',0)+1)
                                        listitem.save()
                            else:
                                try:
                                    listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
                                    listitem.delete()
                                except ListItem.DoesNotExist:
                                    log.info('listitem object does not exist in clarance list')
                            return HttpResponseRedirect('/inventory/%s/%s/all_inventory' % (client_name, seller_name))
                            #all_inventory = Inventory.objects.select_related('rate_chart','rate_chart__article_id').filter(rate_chart__seller=seller).order_by('stock','rate_chart__article_id')
        else:
            log.info('Rate chart does not exist either for sku=%s or article_id=%s' % (skuid, article_id))
            if not errors:
                errors.append('No inventory levels maintained for this article!!!')
    else:
        all_inventory = Inventory.objects.select_related('rate_chart','rate_chart__article_id').filter(rate_chart__seller=seller).order_by('stock','rate_chart__article_id')

    inventory_dict = {
        'accounts' : accounts,
        'url' : request.get_full_path(),
        'article_id':article_id,
        'dc_id':dc_id,
        'sku':skuid,
        'inventory':inventory,
        'rate_chart':rate_chart,
        'is_clearance_item':is_clearance_item,
        'all_inventory':all_inventory,
        'product_image':product_image,
        'updates':update_dict,
        'searched_by':searched_by,
        'flag':flag,
        'errors':errors,
        'client_name':client_name,
        'seller_name':seller_name,
        'loggedin':True,
        'clients':clients,
        'client_display_name':Client.objects.filter(slug=client_name)[0].name,
        'is_global_dc_supported' : is_global_dc_supported,
    }
    return render_to_response('inventory/all_inventory1.html', inventory_dict, context_instance=RequestContext(request))  
      
def generate_inventory_report(request, client_name, seller_name, seller, client_id, count,profile):
    from web.sbf_forms import FileUploadForm
    import os
    errors, message = [], None
    current_inventory = None
    form = None
    to_update = None
    path_to_save = None
    flag = None
    accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = account.client.id)
        cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    
    if request.method == 'POST':
        flag = "report"
        if request.POST.get("upload") == 'Generate Report':
            import xlrd
            form = FileUploadForm(request.POST, request.FILES)
            if form.is_valid():
                path_to_save = save_uploaded_file(request.FILES['status_file'])
                errors, current_inventory = get_current_inventory(path_to_save, seller)
            else:
                errors.append('Please select the excel file and then click upload!!!')
                form = FileUploadForm()
                flag = 'new'            
            #Delete the uploaded excel file
            if path_to_save:
                os.remove(path_to_save)
    else:
        flag = "new"
        form = FileUploadForm()
    
    inventory_dict = {
	    'accounts':accounts,
        'clients':clients,
        'client_name':client_name,
        'seller_name':seller_name,
        'flag':flag,
        'forms':form,
        'errors':errors,
        'current_inventory':current_inventory,
        'url':request.get_full_path(),
        'loggedin':True,
        }
    return render_to_response('inventory/report.html', inventory_dict, context_instance=RequestContext(request)) 

def get_current_inventory(path_to_save, seller):
    import xlrd
    from django.db.models import Q
    book = xlrd.open_workbook(path_to_save)
    sh = book.sheet_by_index(0)
    header = sh.row(0)
    map = {}
    idx = 0
    for idx in range(sh.ncols):
        map[header[idx].value.strip().lower()] = idx
    errors = []
    to_update = []
    consolidated_updates = []
    action_dict = {True:'YES', False:'NO'}

    for row_count in range(1, sh.nrows):
        row = sh.row(row_count)
        try:
            article_id = row[map['articleid']].value

            to_update.append({
                'article_id': str(article_id).split('.')[0],
            })
        except KeyError:
            errors.append('Unsupported excel file.')
            break
            
    if to_update:
        consolidated_updates = []
        for item in to_update:
            try:
                rate_chart = SellerRateChart.objects.get(article_id=item['article_id'], seller=seller)

                inventory = None
                stock = 0
                try:
                    inventory = Inventory.objects.get(rate_chart=rate_chart)
                    stock = inventory.stock
                except Inventory.DoesNotExist:
                    log.info('Inventory not maintained for article-id=%s' % item['article_id'])

                inventory_dict = {
                    'product_name' : rate_chart.product.title,
                    'article_id' : item['article_id'],
                    'current_stock' : stock,
                    'current_otc' : action_dict.get(rate_chart.otc,'--'),
                    'current_cod' : action_dict.get(rate_chart.is_cod_available,'--'),
                    'current_so' : action_dict.get(rate_chart.ship_local_only,'--'),
                    }

                consolidated_updates.append(inventory_dict)

            except SellerRateChart.DoesNotExist:
                errors.append('No active article maintained for Articleid - %s' % item['article_id'])
            except SellerRateChart.MultipleObjectsReturned:
                errors.append('Multiple articles maintained for Articleid - %s' % item['article_id'])
    else:
        log.info('no prices to upload in the sheet!!!')
        errors.append('no prices to upload in the sheet!!!')

    return errors, consolidated_updates

def upload_pincodes(request,client_name, seller_name,  seller, cid, c, profile):
    from web.sbf_forms import FileUploadForm
    from django.utils import simplejson
    errors, message = [], None
    consolidated_updates = None
    form = None
    flag = None
    to_update, to_update_json = None, None
    path_to_save = None
    accounts = cache.get('accounts-'+str(cid)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = cid)
        cache.set('accounts-'+str(cid)+str(request.user.id),accounts,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    consolidated_so_updates, consolidated_otc_updates = [],[]

    if request.method == 'POST':
        if request.POST.get("upload") == 'Upload':
            import xlrd
            form = FileUploadForm(request.POST, request.FILES)
            if form.is_valid():
                path_to_save = save_uploaded_file(request.FILES['status_file'])
                error, to_update = get_parsed_upload_pins_excel(path_to_save)
                to_update_json = simplejson.dumps(to_update)
                if not error:
                    error, consolidated_so_updates, consolidated_otc_updates = get_pincodes(to_update, seller, False)
            
                if error:
                    errors.append(error)
                flag = 'show_details'
            else:
                errors.append('Please select the excel file and then click upload!!!')
                form = FileUploadForm()
                flag = 'new'

        elif request.POST.get("update") == 'Update':
            #path_to_save = request.POST.get("path_to_save")
            to_update_json = request.POST.get("to_update_json")
            to_update = simplejson.loads(to_update_json)
            error, consolidated_so_updates, consolidated_otc_updates = get_pincodes(to_update, seller, True)
            
            if error:
                errors.append(error)
            flag = 'updated'
            form = FileUploadForm()
    else:
        form = FileUploadForm()
        flag = 'new'
    
    so_dict = {
	    'accounts' : accounts,
        'clients':clients,
        'forms' : form,
        'client_name':client_name,
        'seller_name':seller_name,
        'errors' : errors,
        'to_update_json':to_update_json,
        'consolidated_so_updates' : consolidated_so_updates,
        'consolidated_otc_updates' : consolidated_otc_updates,
        'flag' : flag,
        'path_to_save' : path_to_save,
        'url' : request.get_full_path(),
        'loggedin':True,
        'client_display_name':Client.objects.filter(slug=client_name)[0].name,
        }
    return render_to_response('inventory/so_upload.html', so_dict, context_instance=RequestContext(request))

def get_parsed_upload_pins_excel(path_to_save):
    import xlrd
    try:
        book = xlrd.open_workbook(path_to_save)
    except XLRDError:
        return 'Inalid File Format','Inalid File Format'
    sh = book.sheet_by_index(0)
    header = sh.row(0)
    map = {}
    idx = 0
    for idx in range(sh.ncols):
        map[header[idx].value.strip().lower()] = idx
    errors = []
    to_update = []

    for row_count in range(1, sh.nrows):
        row = sh.row(row_count)
        try:
            pincode = row[map['pincode']].value
            type = row[map['type']].value
            action = row[map['action']].value
            to_update.append({
                'pincode': str(pincode).split('.')[0],
                'type': str(type).split('.')[0].upper(),
                'action': action.strip().upper(),
            })
        except KeyError:
            errors.append('Unsupported excel file.')
            break

    return errors, to_update

def get_pincodes(to_update, seller, save_changes):
#    import xlrd
    from django.db.models import Q
    from catalog.models import Pincode
#
#    book = xlrd.open_workbook(path_to_save)
#    sh = book.sheet_by_index(0)
#    header = sh.row(0)
#    map = {}
#    idx = 0
#    for idx in range(sh.ncols):
#        map[header[idx].value.strip().lower()] = idx
    errors = []
#    to_update = []
    consolidated_so_updates = []
    consolidated_otc_updates = []
#
#    for row_count in range(1, sh.nrows):
#        row = sh.row(row_count)
#        try:
#            pincode = row[map['pincode']].value
#            type = row[map['type']].value
#            action = row[map['action']].value
#            to_update.append({
#                'pincode': str(pincode).split('.')[0],
#                'type': str(type).split('.')[0].upper(),
#                'action': action.strip().upper(),
#            })
#        except KeyError:
#            errors.append('Unsupported excel file.')
#            break
            
    if to_update:
        consolidated_updates = []
        for item in to_update:
            servicable_pincode,current_status = None, None
            try:
                servicable_pincode = ServicablePincodes.objects.get(pincode__pin=item['pincode'], client=seller.client, service_type=item['type'])
                current_status = 'Yes'
            except ServicablePincodes.DoesNotExist:
                current_status = 'No'

            if save_changes:
                if item['action'] == 'ADD':
                    if servicable_pincode:
                        pass #As it is already under list of servicable pincodes, do nothing
                    else:
                        pincode = None
                        try:
                            pincode = Pincode.objects.get(pin=item['pincode'])
                        except Pincode.DoesNotExist:
                            pincode = Pincode(pin=item['pincode'])
                            pincode.save()

                        servicable_pincode = ServicablePincodes(pincode=pincode, client=seller.client, service_type=item['type'])
                        servicable_pincode.save()
                elif item['action'] == 'DELETE':
                    if servicable_pincode:
                        servicable_pincode.delete()
                    else:
                        pass #Do nothing as pincode is not listed in servicable pincodes

            
            if item['type'] == 'SO':
                so_dict = {
                    'pincode': item['pincode'],
                    'action':item['action'],
                    'current_status':current_status,
                    }

                consolidated_so_updates.append(so_dict)
            elif item['type'] == 'OTC':
                otc_dict = {
                    'pincode': item['pincode'],
                    'action':item['action'],
                    'current_status':current_status,
                    }

                consolidated_otc_updates.append(otc_dict)
    else:
        log.info('no prices to upload in the sheet!!!')

    return errors, consolidated_so_updates, consolidated_otc_updates

def update_articlelevel_inventory(request, seller, client_id, client_name, seller_name, c, profile):
    rate_chart = None
    skuid = ""
    article_id = ""
    searched_by = ""
    flag = ""
    inventory = None
    product_image = None
    update_dict = None
    is_clearance_item = False
    delivery_time = None
    errors = []
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = account.client.id)
        cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
    is_clearance_item = False
    is_global_dc_supported = utils.is_global_dc_maintained(seller.client)
    if request.method == 'POST':
        check = request.POST.get('name',None)
        if check != 'change':
            from pricing.models import Price

            skuid = request.POST.get("sku")
            article_id = request.POST.get("articleid")

            if not (skuid or article_id):
                errors.append('Please enter either SKU or Article id and then click search!!!')

            if skuid:
                try:
                    rate_chart = SellerRateChart.objects.get(sku=skuid.strip(), seller=seller)
                    searched_by = 'skuid'
                    article_id = rate_chart.article_id
                except SellerRateChart.DoesNotExist:
                    errors.append('No active article maintained for SKU - %s' % skuid)
                except SellerRateChart.MultipleObjectsReturned:
                    errors.append('Multiple active articles maintained for SKU - %s' % skuid)
            elif article_id:
                try:
                    rate_chart = SellerRateChart.objects.get(article_id=article_id.strip(), seller=seller)
                    searched_by = 'article_id'
                    skuid = rate_chart.sku
                except SellerRateChart.DoesNotExist:
                    errors.append('No active article maintained for Articleid - %s' % article_id)
                except SellerRateChart.MultipleObjectsReturned:
                    errors.append('Multiple active articles maintained for Articleid - %s' % article_id)
               
            if rate_chart:
                flag = "searched"
                #First, handling catalog specific prices               
                try:
                    inventory = Inventory.objects.get(rate_chart=rate_chart)
                except Inventory.DoesNotExist:
                    inventory = Inventory(rate_chart=rate_chart, stock=0)
                    inventory.save()

#                delivery_time_obj = None
#                try:
#                    delivery_time_obj = DeliveryTime.objects.get(inventory=inventory)
#                except DeliveryTime.DoesNotExist:
#                    delivery_time_obj = DeliveryTime(inventory=inventory, delivery_time=0)
#                    delivery_time_obj.save()
#
#                delivery_time = delivery_time_obj.delivery_time

                product_image = ProductImage.objects.filter(product=rate_chart.product)
                if product_image:
                    product_image = product_image[0]

                clearance_list = None
                is_clearance_item = False
                
                if utils.get_future_ecom_prod() == seller.client:
                    pass
                else:
                    try:
                        clearance_list = List.objects.get(type='clearance', client=seller.client)
                    except List.DoesNotExist:
                        log.info('Clearance list does not exist!!')

                if clearance_list:
                    try:
                        listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
                        is_clearance_item = True
                    except ListItem.DoesNotExist:
                        pass 

                if request.POST.get("update") and request.POST.get("update") == "Update":
                    flag = "updated"
                    updated_stock = request.POST.get("stock")
                    updated_deliverytime = request.POST.get("delivery_time")

                    if int(str(updated_deliverytime)) == 0:
                        errors.append('You cannot set delivery time to 0!!! Please go back and select appropriate value!!!')
#                    updated_otc = False
#                    if request.POST.get("otc") == 'selected':
#                        updated_otc = True

                    updated_so = False
                    if request.POST.get("so") == 'selected':
                        updated_so = True

                    updated_cod = False
                    if request.POST.get("cod") == 'selected':
                        updated_cod = True

                    updated_clearance = False
                    if request.POST.get("clearance") == 'selected':
                        updated_clearance = True

                    update_dict = {
                        'stock':Decimal(str(updated_stock).strip()),
                        'delivery_time':int(str(updated_deliverytime).strip()),
                        #'otc':updated_otc,
                        'so':updated_so,
                        'cod':updated_cod,
                        'clearance':updated_clearance,
                        }


                if request.POST.get("confirm") and request.POST.get("confirm") == "Confirm":
                    flag = "confirmed"
                    updated_stock = request.POST.get("stock")
                    updated_deliverytime = request.POST.get("delivery_time")
#                    updated_otc = False
#                    if request.POST.get("otc") == 'selected':
#                        updated_otc = True

                    updated_so = False
                    if request.POST.get("so") == 'selected':
                        updated_so = True
                     
                    updated_cod = False
                    if request.POST.get("cod") == 'selected':
                        updated_cod = True               

                    inventory.stock = Decimal(str(updated_stock))
                    inventory.save()

#                    delivery_time_obj.delivery_time = int(str(updated_deliverytime))
#                    delivery_time_obj.save()

                    #rate_chart.otc = updated_otc
                    rate_chart.ship_local_only = updated_so
                    rate_chart.is_cod_available = updated_cod
                    rate_chart.shipping_duration = Decimal(str(updated_deliverytime))
                    if inventory.stock:
                        rate_chart.stock_status = 'instock'
                    else:
                        rate_chart.stock_status = 'outofstock'
                    
                    rate_chart.save()

                    #Update solr index.
                    product = rate_chart.product
                    product.update_solr_index()

                    if request.POST.get("clearance") == 'selected':
                        #Check whether product belongs to clearance sale or not
                        if clearance_list:
                            try:
                                listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
                            except ListItem.DoesNotExist:
                                #Listitem does not exist, so add new one
                                max_seq = clearance_list.listitem_set.all().aggregate(max=Max('sequence'))
                                listitem = ListItem(list=clearance_list, sku=rate_chart, sequence=max_seq.get('max',0)+1)
                                listitem.save()
                    else:
                        try:
                            listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
                            listitem.delete()
                        except ListItem.DoesNotExist:
                            log.info('listitem object does not exist in clarance list')

                    #flag = 'new'
                    #show_all_inventory_levels(request,client_name, seller_name,  seller, client_id, c, profile, flag)

            else:
                log.info('Rate chart does not exist either for sku=%s or article_id=%s' % (skuid, article_id))
                if not errors:
                    errors.append('No inventory levels maintained for this article!!!')
           
    inventory_dict = {
        'accounts' : accounts,
        'url' : request.get_full_path(),
        'article_id':article_id,
        'sku':skuid,
        'inventory':inventory,
        'rate_chart':rate_chart,
        'is_clearance_item':is_clearance_item,
        #'delivery_time':delivery_time,
        'product_image':product_image,
        'updates':update_dict,
        'searched_by':searched_by,
        'flag':flag,
        'errors':errors,
        'client_name':client_name,
        'seller_name':seller_name,
        'loggedin':True,
        'clients':clients,
        'client_display_name':Client.objects.filter(slug=client_name)[0].name
    }
    return render_to_response('inventory/search_by_sku.html', inventory_dict, context_instance=RequestContext(request))

def check_dc_validity(to_update, seller):
    from fulfillment.models import Dc
    #Get list of dc
    dc_in_excel = []
    dc_not_present = []

    for item in to_update:
        if not item['dc'] in dc_in_excel:
            dc_in_excel.append(item['dc'])

    if dc_in_excel:
        available_dc = Dc.objects.filter(code__in=dc_in_excel, client=seller.client).values('code')

    if available_dc:
        if len(available_dc) == len(dc_in_excel):
            pass
        else:
            for dc_in_excel_item in dc_in_excel:
                found = False
                for available_dc_item in available_dc:
                    if dc_in_excel_item == available_dc_item:
                        found = True
                        break

                if not found:
                    dc_not_present.append(dc_in_excel_item)

    return dc_not_present

def upload_bulk_inventory(request, seller, client_id,client_name, seller_name, c, profile):
    from django.utils import simplejson
    from web.sbf_forms import FileUploadForm
    profile = cache.get('profile-'+str(request.user.id))
    if not profile:
        profile = utils.get_user_profile(request.user)
        cache.set('profile-'+str(request.user.id),profile,1800)
    clients = cache.get('clients-'+str(request.user.id))
    if not clients:
        clients = profile.managed_clients()
        cache.set('clients-'+str(request.user.id),clients,1800)
    errors, message = [], None
    consolidated_updates = None
    parsed_excel_json = None
    form = None
    flag = None
    to_update = None
    path_to_save = None
    dc_not_present = []
    accounts = cache.get('accounts-'+str(client_id)+str(request.user.id))
    if not accounts:
        accounts = profile.managed_accounts.filter(client__id = account.client.id)
        cache.set('accounts-'+str(client_id)+str(request.user.id),accounts,1800)
    if request.method == 'POST':
        if request.POST.get("upload") == 'Upload':
            import xlrd
            form = FileUploadForm(request.POST, request.FILES)
            if form.is_valid():
                path_to_save = save_uploaded_file(request.FILES['status_file'])
                errors, to_update = get_parsed_inventory_excel(path_to_save)
                if not errors:
                    dc_not_present = check_dc_validity(to_update, seller)
                    if dc_not_present:
                        dc_not_present_string = ''
                        for item in dc_not_present:
                            dc_not_present_string += item + ','
                        dc_not_present_string = dc_not_present_string[:len(dc_not_present_string-1)]
                        errors.append('Entries not found for DC Codes - %s. Please correct the DC Entries and then try to upload again!!!' % dc_not_present_string)
                        form = FileUploadForm()
                        flag = 'new'
                    else:
                        errors, consolidated_updates = get_inventory_updates(to_update, seller, False)
                        parsed_excel_json = simplejson.dumps(to_update)
                        flag = 'show_details'
                else:
                    form = FileUploadForm()
                    flag = 'new'

                #Delete the uploaded excel file
                if path_to_save:
                    os.remove(path_to_save)
            else:
                errors.append('Please select the excel file and then click upload!!!')
                form = FileUploadForm()
                flag = 'new'
        elif request.POST.get("update") == 'Update':
            #path_to_save = request.POST.get("path_to_save")
            parsed_excel_json = request.POST.get("parsed_excel_json")
            to_update = simplejson.loads(parsed_excel_json)
            errors, consolidated_updates = get_inventory_updates(to_update, seller, True, request.user)
            flag = 'updated'
            form = FileUploadForm()
    else:
        form = FileUploadForm()
        flag = 'new'

    is_global_dc_supported = utils.is_global_dc_maintained(seller.client)

    inventory_dict = {
	    'accounts' : accounts,
        'is_global_dc_supported':is_global_dc_supported,
        'forms' : form,
        'errors' : errors,
        'consolidated_updates' : consolidated_updates,
        'parsed_excel_json' : parsed_excel_json,
        'flag' : flag,
        'path_to_save' : path_to_save,
        'url' : request.get_full_path(),
        'client_name':client_name,
        'seller_name':seller_name,
        'loggedin':True,
        'clients':clients,
        'client_display_name':Client.objects.filter(slug=client_name)[0].name,
        }
    return render_to_response('inventory/inventory_upload.html', inventory_dict, context_instance=RequestContext(request))

def get_parsed_inventory_excel(path_to_save):
    import xlrd
    try:
        book = xlrd.open_workbook(path_to_save)
    except XLRDError:
        return ['invalid file format'],['invalid file format']
    sh = book.sheet_by_index(0)
    header = sh.row(0)
    map = {}
    idx = 0
    for idx in range(sh.ncols):
        map[header[idx].value.strip().lower()] = idx
    errors = []
    to_update = []
    consolidated_updates = []
    article_id_list = []

    for row_count in range(1, sh.nrows):
        row = sh.row(row_count)
        try:
            article_id = str(int(row[map['articleid']].value))
            action = row[map['action']].value
            dc = row[map['dc']].value
            stock = str(row[map['physical_stock']].value)

            virtual_stock = ''
            try:
                virtual_stock = row[map['virtual_stock']].value
            except KeyError:
                pass

            expires_on = ''
            try:
                expires_on = row[map['expires_on']].value
            except KeyError:
                pass
            
            expected_on = ''
            try:
                expected_on = row[map['expected_on']].value
            except KeyError:
                pass
           
            threshold_stock = ''
            try:
                threshold_stock = row[map['threshold_stock']].value
            except KeyError:
                pass

            otc = 'no'
            try:
                otc = row[map['otc']].value
                if not otc:
                    otc = 'no'
            except KeyError:
                pass
            
            cod = 'no'
            try:
                cod = row[map['cod']].value
                if not cod:
                    cod = 'no'
            except KeyError:
                pass

            so = 'no'
            try:
                so = row[map['so']].value
                if not so:
                    so = 'no'
            except KeyError:
                pass

            clearance = 'no'
            try:
                clearance = row[map['clearance']].value
                if not clearance:
                    clearance = 'no'
            except KeyError:
                pass

            delivery_time = ''
            try:
                delivery_time = int(row[map['delivery time']].value)
            except KeyError:
                pass
            
            add_dict = {
                'article_id': str(article_id).strip().split('.')[0],
                'action': action.strip().lower(),
                'stock' : str(stock).strip().split('.')[0],
                'virtual_stock' : str(virtual_stock).strip().split('.')[0],
                'expires_on' : expires_on,
                'expected_on' : expected_on,
                'threshold_stock' : str(threshold_stock).strip().split('.')[0],
                'dc' : str(dc).strip().split('.')[0],
                'otc' : otc.strip().lower(),
                'cod': cod.strip().lower(),
                'so': so.strip().lower(),
                'clearance': clearance.strip().lower(),
                'delivery_time' : delivery_time,
                }

            repeated = False
            for item in to_update:
                if (item['article_id'] == add_dict['article_id']) and (item['dc'] == add_dict['dc']):
                    repeated = True
                    break

            if not repeated:
                to_update.append(add_dict)
                if not add_dict['article_id'] in article_id_list:
                    article_id_list.append(add_dict['article_id'])
            else:
                errors.append('Duplicate entry for Articleid: %s and DC: %s combination!!! Please correct the error and and try to upload again!!!' % (item['article_id'],item['dc']))
        except KeyError:
            errors.append('Unsupported excel file.')
            break

    return errors, to_update

def get_inventory_updates(to_update, seller, save_changes, user=None):
    from django.db.models import Q
    from catalog.models import InventoryLog
    errors = []
    consolidated_updates = []
    action_dict = {True:'YES', False:'NO'}
    if_any_updates = False
    is_global_dc_supported = utils.is_global_dc_maintained(seller.client)
    updated_virtual_stock, updated_expires_on, updated_expected_on = None, None, None
    updated_threshold_stock = None
    inventory_log = None

    if to_update:
        consolidated_updates = []
        for item in to_update:
            try:
                rate_chart = SellerRateChart.objects.get(article_id=item['article_id'], seller=seller)

                inventory = None
                try:
                    inventory = Inventory.objects.get(rate_chart=rate_chart, dc__client=seller.client, dc__code=item['dc'])
                except Inventory.DoesNotExist:
                    dc = None
                    try:
                        dc = Dc.objects.get(code=item['dc'], client=seller.client)
                    except Dc.DoesNotExist:
                        log.info('No DC found for client=%s and code=%s combination' % (seller.client, item['dc']))
                    if dc:
                        inventory = Inventory(rate_chart=rate_chart, stock=0, dc=dc)
                        inventory.save()

                #Check whether product belongs to clearance sale or not
                clearance_list = None
                current_clearance_status = 'NO'
                if utils.get_future_ecom_prod() == seller.client:
                    pass
                else:
                    clearance_list = None
                    try:
                        clearance_list = List.objects.get(type='clearance', client=seller.client)
                    except:
                        log.info('No clearance list maintained for %s' % seller.client)

                    clearance_list_items = None
                    if clearance_list:
                        clearance_list_items = clearance_list.listitem_set.all()

                        for listitem in clearance_list_items:
                            if rate_chart == listitem.sku:
                                current_clearance_status = 'YES'
                    
                inventory_dict = {
                    'product_name' : rate_chart.product.title,
                    'article_id' : item['article_id'],
                    'current_otc' : action_dict.get(rate_chart.otc,'--'),
                    'updated_otc': item['otc'].upper(),
                    'current_cod' : action_dict.get(rate_chart.is_cod_available,'--'),
                    'updated_cod': item['cod'].upper(),
                    'current_so' : action_dict.get(rate_chart.ship_local_only,'--'),
                    'updated_so': item['so'].upper(),
                    'current_clearance' : current_clearance_status,
                    'updated_clearance': item['clearance'].upper(),
                    }

                if is_global_dc_supported:
                    if rate_chart.shipping_duration:
                        delivery_time = str(rate_chart.shipping_duration)
                    else:
                        delivery_time = '--'

                    extra_params = {
                        'current_deliverytime':delivery_time,
                        'updated_deliverytime': Decimal(str(item['delivery_time'])),
                        }
                    inventory_dict.update(extra_params)

                if item['action'] == 'update':
                    #If action=update, overwrite the current inventory.
                    if save_changes:
                        inventory_log = InventoryLog()
                        inventory_log.was_physical_stock = inventory.stock

                        inventory.stock = Decimal(str(item['stock']))
                        if inventory.stock < Decimal('0'):
                            inventory.stock = Decimal('0')
                        inventory.save()

                        inventory_log.new_physical_stock = inventory.stock

                    extra_params = {
                        'current_stock' : inventory.stock,
                        'updated_stock' : Decimal(str(item['stock'])),
                        }
                    inventory_dict.update(extra_params)
                elif item['action'] == 'add':
                    # stock = current stock + additional stock
                    updated_stock = 0
                    if inventory.stock:
                        updated_stock = inventory.stock + Decimal(str(item['stock']))
                    else:
                        updated_stock = Decimal(str(item['stock']))

                    if save_changes:
                        inventory_log = InventoryLog()
                        inventory_log.was_physical_stock = inventory.stock
                        inventory.stock = updated_stock
                        inventory.save()
                        inventory_log.new_physical_stock = inventory.stock
                    
                    extra_params = {
                        'current_stock' : inventory.stock,
                        'updated_stock' : updated_stock,
                        }
                    inventory_dict.update(extra_params)

                if item['virtual_stock'] and item['expires_on'] and item['expected_on']:
                    current_virtual_stock, current_expires_on, current_expected_on = None, None, None 
                    if inventory.expires_on  and (inventory.expires_on < datetime.datetime.now()):
                        current_virtual_stock = '--'
                        current_expires_on = '--'
                        current_expected_on = '--'
                    else:
                        current_virtual_stock = '--'
                        if inventory.virtual_stock:
                            current_virtual_stock = inventory.virtual_stock
                        current_expires_on = '--'
                        if inventory.expires_on:
                            current_expires_on = inventory.expires_on
                        current_expected_on = '--'
                        if inventory.expected_on:
                            current_expected_on = inventory.expected_on

                    updated_virtual_stock = Decimal(str(item['virtual_stock']))
                    updated_expires_on = item['expires_on']
                    updated_expected_on = item['expected_on']

                    extra_params = {
                        'current_virtual_stock' : current_virtual_stock,
                        'updated_virtual_stock' : updated_virtual_stock,
                        'current_expected_on' : current_expected_on,
                        'updated_expected_on' : datetime.datetime.strptime(item['expected_on'],'%Y-%m-%d %H:%M:%S'),
                        'current_expires_on' : current_expires_on,
                        'updated_expires_on' : datetime.datetime.strptime(item['expires_on'],'%Y-%m-%d %H:%M:%S'),
                        }   
                    inventory_dict.update(extra_params)
                
                if item['threshold_stock']:
                    current_threshold_stock = '--'
                    if inventory.threshold_stock:
                        current_threshold_stock = inventory.threshold_stock
                    updated_threshold_stock = Decimal(str(item['threshold_stock']))
                    
                    extra_params = {
                        'current_threshold_stock' : current_threshold_stock,
                        'updated_threshold_stock' : updated_threshold_stock,
                        }
                    inventory_dict.update(extra_params)

                consolidated_updates.append(inventory_dict)

                if save_changes:
                    #Update inventory related stuff.
                    if item['virtual_stock'] and item['expires_on'] and item['expected_on']:
                        inventory_log.was_virtual_stock = inventory.virtual_stock
                        inventory_log.was_expires_on = inventory.expires_on
                        inventory_log.was_expected_on = invetory.expected_on

                        inventory.virtual_stock = Decimal(str(item['virtual_stock']))
                        inventory.expires_on = datetime.datetime.strptime(item['expires_on'],'%Y-%m-%d %H:%M:%S')
                        inventory.expected_on = datetime.datetime.strptime(item['expected_on'],'%Y-%m-%d %H:%M:%S')
                        inventory.save()

                        inventory_log.new_virtual_stock = inventory.virtual_stock
                        inventory_log.new_expires_on = inventory.expires_on
                        inventory_log.new_expected_on = inventory.expected_on

                    if item['threshold_stock']:
                        inventory_log.was_threshold_stock = inventory.threshold_stock

                        inventory.threshold_stock = Decimal(str(item['threshold_stock']))
                        inventory.save()

                        inventory_log.new_threshold_stock = inventory.threshold_stock

                    if inventory_log:
                        inventory_log.rate_chart = inventory.rate_chart
                        inventory_log.dc = inventory.dc
                        inventory_log.modified_by = 'admin'
                        inventory_log.user = user
                        inventory_log.save()

                    #Now, update the rate chart entires
                    if item['otc'] == 'yes':
                        rate_chart.otc = True
                    elif item['otc'] == 'no':
                        rate_chart.otc = False
                    
                    if item['cod'] == 'yes':
                        rate_chart.is_cod_available = True
                    elif item['cod'] == 'no':
                        rate_chart.is_cod_available = False

                    if item['so'] == 'yes':
                        rate_chart.ship_local_only = True
                    elif item['so'] == 'no':
                        rate_chart.ship_local_only = False

                    if item['clearance'] == 'yes':
                        if not clearance_list:
                            clearance_list = List(type='clearance', client=seller.client)
                            clearance_list.save()

                        try:
                            listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
                        except ListItem.DoesNotExist:
                            #Listitem does not exist, so add new one
                            max_seq = clearance_list.listitem_set.all().aggregate(max=Max('sequence'))
                            if max_seq['max'] == None: max_seq['max'] = 0
                            listitem = ListItem(list=clearance_list, sku=rate_chart, sequence=(max_seq['max']+1))
                            listitem.save()
                    elif item['clearance'] == 'no':
                        if clearance_list:
                            try:
                                listitem = ListItem.objects.get(list=clearance_list, sku=rate_chart)
                                listitem.delete()
                            except ListItem.DoesNotExist:
                                log.info('listitem object does not exist in clarance list')

                    if is_global_dc_supported:
                        rate_chart.shipping_duration = str(item['delivery_time'])
                        
                    rate_chart.save()
                    
                    #Update solr index.
                    #Make product available on site, if-
                    #1) Valid price is maintained.(--Already mainained above, so no need to check again)
                    #2) Pricelist priorities are maintained.
                    #3) Valid stock is maintained.
                    product = rate_chart.product
                    rate_chart.stock_status = 'outofstock'

                    if inventory.stock:
                        if not (utils.is_holii_client(seller.client) or utils.is_wholii_client(seller.client)): 
                            prices_maintained_for_src = Price.objects.filter(
                                rate_chart=rate_chart).exclude(
                                Q(price_type='timed',start_time__gte=datetime.datetime.now())| 
                                Q(price_type='timed', end_time__lte=datetime.datetime.now())
                                )

                            if prices_maintained_for_src:
                                domain_level_applicable_pricelists = DomainLevelPriceList.objects.filter(domain__client=rate_chart.seller.client)
                        
                                if domain_level_applicable_pricelists:
                                    rate_chart.stock_status = 'instock'
                                else:
                                    client_level_applicable_pricelists = ClientLevelPriceList.objects.filter(client=rate_chart.seller.client)
                                    if client_level_applicable_pricelists:
                                        rate_chart.stock_status = 'instock'
                        else:
                            rate_chart.stock_status = 'instock'

                    rate_chart.save()
                    product.update_solr_index()
            except SellerRateChart.DoesNotExist:
                errors.append('No active article maintained for Articleid - %s' % item['article_id'])
            except SellerRateChart.MultipleObjectsReturned:
                errors.append('Multiple articles maintained for Articleid - %s' % item['article_id'])
            except Exception,e:
                log.info("Exception = %s" % repr(e))
    else:
        log.info('no data to upload in the sheet!!!')

    return errors, consolidated_updates

