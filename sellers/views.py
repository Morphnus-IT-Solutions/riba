from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import render_to_response
from django.template import RequestContext, Context, loader
from django.http import Http404, HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect
from django.views.decorators.cache import never_cache
from django.contrib.auth.models import *
from django.contrib.auth import login as auth_login
from django.contrib  import auth
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django import forms
from accounts.models import Account, Client, NotificationSettings
from sellers.decorators import check_role
from utils.utils import getPaginationContext, check_dates, get_excel_status, save_excel_file, create_context_for_search_results, ternary
from utils import utils
from orders.models import Order, OrderItem
from reviews.models import Review
from django.forms.models import modelformset_factory
from users.models import Tab, UserTab
from datetime import date, datetime, timedelta
from django.db.models import Q
from catalog.models import SellerRateChart
from inventory.views import * 
from web.views.pricing_views import * 
from decimal import Decimal
from payouts.forms import  PayoutHomeForm
from sellers.forms import AddUserForm, ListsForm, ListItemForm, CoordinatesForm
from accounts.forms import SellerProfileForm, SellerLoginForm, SellerNotificationForm
from restapi import APIManager
import math, re, calendar
from web.models import Coordinates

def landing_page(request):
    if request.user.is_authenticated():
        url = '/home/'
    else:
        url='/login/'
    return HttpResponseRedirect(url)

#called after login is successful.
@login_required   
def home(request):
    return render_to_response('ppd/landing_page.html',{}, context_instance=RequestContext(request))

#called on clicking category tab
@login_required
def category_tab(request):
    return render_to_response('ppd/category_tab.html',{}, context_instance=RequestContext(request))

#called on clicking fulfillment tab
@login_required
def fulfillment_tab(request):
    return render_to_response('ppd/fulfillment_tab.html',{}, context_instance=RequestContext(request))

#called on clicking category management tab inside category tab
@login_required
def category_management_tab(request):
    return render_to_response('ppd/category_management_tab.html',{}, context_instance=RequestContext(request))

#called on clicking sales tab
@login_required
def sales_tab(request):
    return render_to_response('ppd/sales_tab.html',{}, context_instance=RequestContext(request))

#called on clicking orders tab inside sales tab
@login_required
def orders_tab(request):
    return render_to_response('ppd/orders_tab.html',{}, context_instance=RequestContext(request))

#called on clicking management tab
@login_required
def management_tab(request):
    return render_to_response('ppd/management_tab.html',{}, context_instance=RequestContext(request))

#called on clicking payments tab
@login_required
def payments_tab(request):
    return render_to_response('ppd/payments_tab.html',{}, context_instance=RequestContext(request))

#called on clicking User Experience tab
@login_required
def user_experience_tab(request):
    return render_to_response('ppd/user_experience_tab.html',{}, context_instance=RequestContext(request))

#called on clicking lists in User Experience tab
@login_required
def lists_tab(request):
    return render_to_response('ppd/lists_tab.html',{}, context_instance=RequestContext(request))

#called on clicking inventory tab under category tab
@login_required
def inventory_tab(request):
    return render_to_response('ppd/inventory_tab.html',{}, context_instance=RequestContext(request))

#called on clicking pricing tab under category tab
@login_required
def pricing_tab(request):
    return render_to_response('ppd/pricing_tab.html',{}, context_instance=RequestContext(request))

#called on clicking marketing tab
@login_required
def marketing_tab(request):
    return render_to_response('ppd/marketing_tab.html',{}, context_instance=RequestContext(request))

#called on clicking site_properties under user_experience tab
@login_required
def site_properties_tab(request):
    return render_to_response('ppd/site_properties_tab.html',{}, context_instance=RequestContext(request))

#called for signout
@login_required
def logout(request):
    auth.logout(request)
    request.session.flush()
    params = request.GET
    return HttpResponseRedirect("/")

#called for getting orders report
@login_required
@check_role('Sales-Orders')
def orders(request,order_state):
    url = request.get_full_path()
    if 'search_trend' not in url and "from" not in url:
        if "?" in url:
            return HttpResponseRedirect(url+ '&search_trend=day')
        else:
            return HttpResponseRedirect(url+ '?search_trend=day')
    
    client = request.client.client
    seller = request.session['seller']
    #try:
    #    check = seller.id
    #except:
    #    seller = 'all-sellers'
    orders, order_id = [], 0
    dates = check_dates(request)
    search_trend, from_date, to_date = dates['search_trend'], dates['start_date'], dates['end_date']
    save_excel = get_excel_status(request, "excel")
    sort_by, order_by = get_sort_by_in_orders(request, order_state)
    url = updated_url(request)
    orders = get_orders(request, from_date, to_date, order_id, client, order_state, seller, order_by)
# export this report as excel        
    if save_excel == True:
        excel_header = ['Customer Name', 'Customer Phone', 'Order ID.', 'Transaction No.', 'Payment Notes','Order Date','Seller', 'Item Title','Item Qty', 'MRP','Offer Price','Discount', 'Order Amount','Booking Agent', 'Confirming Agent', 'Delivery Notes', 'Gift Notes', 'Payment Mode', 'Delivery Address','City', 'Full Address']
        excel_data = []
        for item in orders:
            excel_data.append([item.order.name(), item.order.phone(), item.order, item.transaction_no(), item.payment_notes(), item.order.timestamp, item.seller_rate_chart.seller.name, item.item_title ,item.qty, int(item.list_price), int(item.sale_price), int(item.list_price)-int(item.sale_price), int(item.order.payable_amount), item.order.booking_agent, item.order.confirming_agent, item.delivery_notes(), item.gift_notes(), item.order.payment_mode, item.order.get_delivery_address(), item.order.city(), item.order.get_delivery_address()])
        return save_excel_file(excel_header, excel_data)

    orders_dict = {
        'search_trend':search_trend, 
        'from_date':from_date, 
        'to_date':to_date, 
        'client':client, 
        'seller':seller, 
        'order_state':order_state, 
        'orders':orders, 
        'url':url,
        'sortby':sort_by, 
        }
    return render_to_response('ppd/orders.html',orders_dict, context_instance=RequestContext(request))   

#sub-function of function orders
def get_orders(request, from_date, to_date, order_id, client, order_state, seller, order_by):
    #if searching by order_id
    order_id = request.GET.get('order_id', None)
    if order_id:
        from_date = datetime.datetime.now()
        to_date = from_date
        query = Q(Q(order__id=order_id) | Q(order__reference_order_id=order_id), seller_rate_chart__seller__in = seller, order__support_state = order_state)
    else:
        if order_state == 'confirmed':
            query = Q(seller_rate_chart__seller__in = seller, order__support_state = order_state, order__confirming_timestamp__gte=from_date, order__confirming_timestamp__lte=to_date+timedelta(days=1))
        else:
            query = Q(seller_rate_chart__seller__in = seller, order__support_state = order_state, order__timestamp__gte=from_date, order__timestamp__lte=to_date+timedelta(days=1))

    orders = OrderItem.objects.select_related('order','seller_rate_chart','seller_rate_chart__seller').filter(query).order_by(order_by)
    return orders

#sub-function of function orders
def get_sort_by_in_orders(request, order_state):
    sort_by = request.GET.get('sortby','date_asc')
    if sort_by == 'date_asc':
        if order_state == 'confirmed':
            order_by = 'order__payment_realized_on'
        else:
            order_by = 'order__timestamp'
    elif sort_by == 'date_dsc':
        if order_state == 'confirmed':
            order_by = '-order__payment_realized_on'
        else:
            order_by = '-order__timestamp'
    elif sort_by == 'id_asc':
        order_by = 'order__id'
    elif sort_by == 'id_dsc':
        order_by = '-order__id'
    elif sort_by == 'amt_asc':
        order_by = 'total_amount'
    elif sort_by == 'amt_dsc':
        order_by = '-total_amount'
    else:
        order_by = 'order__payment_realized_on'
        sort_by = 'date_asc'
    return sort_by, order_by

#sub-function of function orders
def updated_url(request):
    url = request.get_full_path()
    if "sortby=date_asc" in url:
        url = url.replace("&sortby=date_asc", "")
    elif "sortby=date_dsc" in url:
        url = url.replace("&sortby=date_dsc", "")
    elif "sortby=id_asc" in url:
        url = url.replace("&sortby=id_asc", "")
    elif "sortby=id_dsc" in url:
        url = url.replace("&sortby=id_dsc", "")
    elif "sortby=amt_asc" in url:
        url = url.replace("&sortby=amt_asc", "")
    elif "sortby=amt_dsc" in url:
        url = url.replace("&sortby=amt_dsc", "")
    return url


@login_required
@check_role('Sales-Orders')
def order_detail(request, order_id):
    client = request.client.client
    seller = request.session['seller']
    try:
        order = Order.objects.get(id=order_id, client = client)
    except Order.DoesNotExist:
        raise Http404
    order_items = order.get_order_items(request, select_related=('order','seller_rate_chart',
              'seller_rate_chart__product'), filter={'seller_rate_chart__seller__in':seller})
    if not order_items:
        raise Http404
    list_price_total, sale_price_total = 0, 0
    for od in order_items:
        list_price_total += od.list_price
        sale_price_total += od.sale_price
    discount_total = list_price_total - sale_price_total
    ctxt = { 'order': order,
            'order_items': order_items,
            'sale_price_total': sale_price_total,
            'list_price_total': list_price_total,
            'discount_total': discount_total
          }
    return render_to_response('ppd/order_detail.html', ctxt, context_instance=RequestContext(request))

@login_required
@check_role('Category-Products')
def products(request):
    from utils.solrutils import solr_search
    client = request.client.client
    seller = request.session['seller']
    q = 'client_id:%s' % client.id
    page_no = int(request.GET.get('page', 1))
    params = {}
    items_per_page = 20
    params['start'] = (page_no -1) * items_per_page
    params['rows'] = items_per_page
    solr_result = solr_search(q, fields='id', **params)
    product_ids = [res['id'] for res in solr_result.results]
    product_context = create_context_for_search_results(product_ids, request)
    total_results = solr_result.numFound
    total_pages = int(math.ceil(Decimal(solr_result.numFound)/Decimal(items_per_page)))
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

    products_dict = {
        'products': product_context,
        'client_display_name':client.name,
        'pagination':pagination,
        }
    return render_to_response('ppd/products.html', products_dict, context_instance=RequestContext(request))   

# called after click on products link under category tab
@login_required
@check_role('Category-Product Reviews')
def product_reviews(request, status):
    url = request.get_full_path()
    if 'search_trend' not in url and "from" not in url and not "sku" in url:
        if "?" in url:
            return HttpResponseRedirect(url+ '&search_trend=day')
        else:
            return HttpResponseRedirect(url+ '?search_trend=day')
    dates = check_dates(request)
    from_date, to_date, search_trend = dates['start_date'], dates['end_date'], dates['search_trend']
    client = request.client.client
    seller = request.session['seller'][0]
    sku = request.GET.get('sku',None)
    if sku:
        srcs = SellerRateChart.objects.filter(sku=sku)
        rcs_prods = srcs.values_list('product', flat=True).distinct()
        rcs_prods = list(rcs_prods)
        product_reviews = Review.objects.filter(product__in = rcs_prods, rate_chart__seller=seller).order_by('-reviewed_on')
        from_date = to_date
    else:
        if status=='pending' or status=='new':
            product_reviews = Review.objects.filter(
                rate_chart__seller__id=seller.id,
                rate_chart__seller__client=client.id,
                reviewed_on__gte=from_date, reviewed_on__lte=to_date+timedelta(days=1)).order_by('-reviewed_on')
        else:
            product_reviews = Review.objects.filter(
                rate_chart__seller__id=seller.id,
                rate_chart__seller__client=client.id,
                reviewed_on__gte=from_date, reviewed_on__lte=to_date+timedelta(days=1)).order_by('-modified_on')
    if "&status=approved" in url:
        url=url.replace("&status=approved", "")
    if "&status=pending" in url:
        url=url.replace("&status=pending", "")
    if "&status=flagged" in url:
        url=url.replace("&status=flagged", "")
    new, approved, rejected, flagged = None, None, None, None
    if product_reviews:
        new = product_reviews.filter(status='new')
        approved = product_reviews.filter(status='approved')
        rejected = product_reviews.filter(status='removed')
        flagged =  product_reviews.filter(status='flagged')
        product_reviews = product_reviews.filter(status=status)
    product_reviews_dict = {
                            'url':url,
                            'sku':sku,
                            'status':status, 
                            "product_reviews":product_reviews,
                            "total_reviews":len(product_reviews),
                            'search_trend':search_trend,
                            'from_date':from_date,
                            'to_date':to_date,
                            'new':new,
                            'approved':approved,
                            'rejected':rejected,
                            'flagged':flagged,    
                            'client_display_name':client.name,
                            'page':(int(request.GET.get('page',1))-1),
                            }
    return render_to_response('reviews/approval.html', product_reviews_dict, context_instance=RequestContext(request))

@login_required
def approve_or_disapprove_review(request):
    from datetime import datetime
    review_id = request.POST['on_id']
    on_or_off = request.POST['on_or_off']
    url = request.POST['url']
    review = Review.objects.get(id=review_id)
    if on_or_off == 'on':
        review.status='approved'
    if on_or_off == 'off':
        review.status = 'removed'
    if on_or_off == 'flag':
        review.status = 'flagged'
    review.modified_on = datetime.now()
    review.reviewed_by = utils.get_user_profile(request.user).full_name
    review.save()
    return HttpResponseRedirect(url)

#called after click on user rights in management tab
@login_required
@check_role('Management-User Rights')
def users(request):
    group, account= {}, {}
    group_in_url = request.GET.get('group',None)
    if group_in_url:
        group_in_url.replace('%20',' ')
        usrs = User.objects.distinct().filter(groups__name=group_in_url).order_by('-last_login')
        for user in usrs:
            acc = []
            group[user] = group_in_url
            acnts = utils.get_user_profile(user).managed_accounts.filter(client = request.client.client)
            for ele in acnts:
                acc.append(ele.name)
            account[user] = acc
    
    else:
        group_list = ['Sellers Admin','Sellers Manager','Sellers User','Sellers Client','Sellers Agent','IFS']
        usrs = User.objects.distinct().filter(groups__name__in=group_list).order_by('-last_login')
        for user in usrs:
            acc = []
            grps = Group.objects.filter(user=user)
            acnts = utils.get_user_profile(user).managed_accounts.filter(client = request.client.client)
            for ele in grps:
                if ele.name in group_list:
                    group[user] = ele
            for ele in acnts:
                acc.append(ele.name)
            account[user] = acc
    passing_dict = {
                    'users':usrs,
                    'group':group,
                    'account':account,
                    'url':request.get_full_path(),
                    'page':(int(request.GET.get('page',1))-1),
                    }
    return render_to_response('ppd/users.html', passing_dict,context_instance=RequestContext(request))

# called on click on user_rights under management tab
@login_required
@check_role('Management-User Rights')
def create_or_edit_users(request):
    action = request.GET.get('action','add')
    from users.models import Tab, UserTab
    tabs = Tab.objects.filter(system='platform')
    group_list = ['Sellers Admin','Sellers Manager','Sellers User','Sellers Client','Sellers Agent','IFS']
    groups = Group.objects.filter(name__in=group_list)
    selected_tabs, selected_accounts = [], []
    errors = ''
    user = None
    username = request.GET.get('username',None)
    if username:
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            errors = 'User Does Not Exist'
    if action == 'delete' and user:
        for group in groups:
            if user.groups.filter(name__in=group_list):
                user.groups.remove(group)
        errors = 'Access Removed. '+username+' now donot have acess to Sellers Hub'
    elif action == 'edit' and user:
        if request.method == 'POST':
            #getting checked tabs and populating in database
            for i in range(tabs.count()):
                selected_tabs.append(request.POST.get(str(i),''))
            user_tabs = UserTab.objects.filter(user=utils.get_user_profile(user), tab__in=tabs)
            for user_tab in user_tabs:
                user_tab.delete()
            for tab in selected_tabs:
                new_tab = Tab.objects.filter(tab_name=tab, system='platform')
                if new_tab:
                    user_tab = UserTab()
                    user_tab.tab = new_tab[0]
                    user_tab.user= utils.get_user_profile(user)
                    user_tab.save()
            
            #getting checked accounts
            for i in range(request.session['all_sellers'].count()):
                selected_accounts.append(request.POST.get('account'+str(i),None))
            managed_accounts = utils.get_user_profile(user).managed_accounts.filter(client = request.client.client)
            for account in managed_accounts:
                utils.get_user_profile(user).managed_accounts.remove(account)
            for account in selected_accounts:
                if account:
                    acc = Account.objects.get(name=account)
                    utils.get_user_profile(user).managed_accounts.add(acc)
                    utils.get_user_profile(user).save()
            
            #getting selected_group
            selected_group = request.POST.get('selected_group',None)
            user_groups = user.groups.filter(name__in=group_list)
            for group in user_groups:
                user.groups.remove(group)
            selected_group = Group.objects.filter(name=selected_group)[0]
            user.groups.add(selected_group)
            errors = 'User with username ' +username+' Edited'

    elif action == 'add':
        if request.method == 'POST':
            username = request.POST.get('username_to_search', None)
            check = request.POST.get('check',None)
            if not user and username:
                try:
                    user = User.objects.get(username=username)
                except:
                    errors = 'User with username '+username+' does not exist'
            for i in range(tabs.count()):
                selected_tabs.append(request.POST.get(str(i),''))
            
            for i in range(request.session['all_sellers'].count()):
                selected_accounts.append(request.POST.get('account'+str(i),None))
            
            selected_group = request.POST.get('selected_group',None)
            
            if not check: 
                user_groups = Group.objects.filter(name__in=group_list)
                for group in user_groups:
                    if group in user.groups.filter(name__in=group_list):
                        errors = 'User wih username '+username+' already exists'
                    else:
                        selected_group = Group.objects.get(name=selected_group)
                        user.groups.add(selected_group)

                managed_accounts = utils.get_user_profile(user).managed_accounts.filter(client = request.client.client)
                for account in managed_accounts:
                    utils.get_user_profile(user).managed_accounts.remove(account)
                for account in selected_accounts:
                    if account:
                        acc = Account.objects.get(name=account)
                        utils.get_user_profile(user).managed_accounts.add(acc)
                        utils.get_user_profile(user).save()
             
                user_tabs = UserTab.objects.filter(user=utils.get_user_profile(user), tab__in=tabs)
                for user_tab in user_tabs:
                    user_tab.delete()
                for tab in selected_tabs:
                    new_tab = Tab.objects.filter(tab_name=tab, system='platform')
                    if new_tab:
                        user_tab = UserTab()
                        user_tab.tab = new_tab[0]
                        user_tab.user= utils.get_user_profile(user)
                        user_tab.save()
                errors = 'User - '+username+' now has access to Sellers Hub'
    passing_dict = {
                    'user':user,
                    'errors':errors,
                    'tabs':tabs,
                    'groups':groups,
                    'action':action,
                    }
    return render_to_response('ppd/create_or_edit_user.html',passing_dict,context_instance=RequestContext(request))

#Called on click on profile under management tab
@login_required
@check_role('Management-Profile')
def profile(request):
    account = request.session['seller'][0]
    profile_exists, profile = profile_exists_or_not(account.id)
    if request.method == "POST":
        login_form = SellerLoginForm(request.POST, prefix = "login")
        login_form_error, user, profile = login_result(login_form, account)
        form = SellerProfileForm(request.POST, instance=account, prefix="profile")
        if form.is_valid():
            form.save()
        profile_dict = {
            'form': form,
            'form_errors': form.errors,
            'login_form': login_form,
            'login_form_error': login_form_error,
            'profile_exists': profile_exists,
            'client_display_name':request.client.client.name
        }
        return render_to_response('ppd/profile.html', profile_dict, context_instance=RequestContext(request))
    
    else: #If the form has not been submitted 
        form = SellerProfileForm(instance = account, prefix="profile")
        login_form = SellerLoginForm(prefix="login")
        profile_dict = {
            'form': form,
            'account':account,
            'login_form': login_form,
            'profile_exists': profile_exists,
            'client_display_name':request.client.client.name
        }
        return render_to_response('ppd/profile.html', profile_dict, context_instance=RequestContext(request))

#sub-function of profile
def profile_exists_or_not(account):
    try:
        profile = Profile.objects.get(acquired_through_account = account)
        return True, profile
    except:
        return False, ''

#sub-function of profile
def login_result(login_form, account):
    if login_form.is_valid():
        username = login_form.cleaned_data.get('username', '')
        password = login_form.cleaned_data.get('password','')
        new_password = login_form.cleaned_data.get('new_password', '')
        confirm_password = login_form.cleaned_data.get('confirm_password', '')
        error = ''
        user = ''
        profile_exists, profile = profile_exists_or_not(account)
        if profile_exists:
            if new_password:
                if not username:
                    error = 'Please enter username'
                elif not password:
                    error = 'Please enter password'
                elif not confirm_password:
                    error = 'Please confirm password'
                elif new_password != confirm_password:
                    error = 'New password and confirm password entries do not match'
                elif profile.user.username != username:
                    error = 'Entered username does not belong to this account'
                elif not profile.user.check_password(password):
                    error = 'Please enter the correct password for this entry'
                else:
                    profile.user.set_password(new_password)
                    profile.user.save()

        else:
            if password:
                if not username:
                    error = 'Please enter username'
                elif not password:
                    error = 'Please enter password'
                elif not confirm_password:
                    error = 'Please confirm password'
                elif password != confirm_password:
                    error = 'Password and confirm password entries do not match'
                else:
                    is_new, u, has_password = is_new_user(username)
                    if not is_new:
                        error = 'This username already exists for another user. Please enter a different username'
                    else:
                        input_type = False
                        if utils.is_valid_email(username):
                            input_type = "email"
                        elif utils.is_valid_mobile(username):
                            input_type = "mobile"
                        else:
                            input_type = "id"
                        if input_type == 'id':
                            error = 'Please enter a valid Email / Mobile'
                        else:
                            user, profile = utils.get_or_create_user(username, '', password)
                            profile.full_name = account.name
                            profile.acquired_through_account = account
                            profile.save()
        return error,user,profile


@login_required
@check_role('Management-Notifications')
def notifications(request):
    from django.forms.formsets import formset_factory
    client = request.client.client
    account = request.session['seller'][0]
    try:
        notification_queryset = NotificationSettings.objects.filter(account = account)
    except:
        notification_queryset = None
    new_fields = False
    if notification_queryset:
        SellerNotificationFormSet = modelformset_factory(NotificationSettings,
        extra = 0,
        fields = ("event", "on_primary_email", "on_secondary_email", "on_primary_phone", "on_secondary_phone")
        )
    else:
        SellerNotificationFormSet = modelformset_factory(NotificationSettings,
        extra = 3,
        fields = ("event", "on_primary_email", "on_secondary_email", "on_primary_phone", "on_secondary_phone")
        )

    if request.method == "POST":#If the form has been submittedi
        formset = SellerNotificationFormSet(request.POST)
        for form in formset.forms:
            if form.is_valid():
                formtemp=form.save(commit=False)
                formtemp.account= account
                formtemp.save()
        notification_dict = {
            'formset': formset,
            'new_fields':new_fields,
            'client_display_name':client.name
        }
        return render_to_response('ppd/notification.html', notification_dict, context_instance=RequestContext(request))
        
    else: #If the form has not been submitted 
        if notification_queryset:
            formset = SellerNotificationFormSet(queryset=notification_queryset)
        else:
            formset = SellerNotificationFormSet(queryset=NotificationSettings.objects.none(), initial = [{"event":'general'},{"event":'pending_order_event'},{"event":'order_confirmed_event'}])
        new_fields = True
        notification_dict = {
            'formset': formset,
            'new_fields':new_fields,
            'client_display_name':client.name
        }
        return render_to_response('ppd/notification.html', notification_dict, context_instance=RequestContext(request))


def channel_payment_option_on_or_off(request):
    option_code = request.POST['option']
    on_or_off = request.POST['on_or_off']
    domain_payment_option = DomainPaymentOptions.objects.get(id=option_code)
    # domain_payment_option = DomainPaymentOptions.objects.get(id=option_code)
    if on_or_off == 'on':
        domain_payment_option.is_active = True
        domain_payment_option.save()
    if on_or_off == 'off':
        domain_payment_option.is_active = False
        domain_payment_option.save()
    return HttpResponse('ok')


def activate_payment_option(request):
    option_id = request.POST['option']
    is_active = request.POST['activate']
    is_active = True if is_active == 'True' else False
    po = PaymentOption.objects.get(id=option_id)
    po.is_active = is_active
    po.save()
    if not is_active:
        dpo = DomainPaymentOptions.objects.filter(payment_option__id=option_id)
        for d in dpo:
            d.is_active = False
            d.save()
    return HttpResponse('ok')


def get_payment_options_form_obj(request, option):#option contains payment mode instance
    if option.payment_mode.code in ("deposit-transfer"):
        if request.method == "POST":
            if option.is_active == True:
                form = DepositForm(request.POST, instance = option, prefix = option.payment_mode.code)  
            else:
                form = DepositForm(instance=option, prefix = option.payment_mode.code)
        else:
            form =  DepositForm(instance=option, prefix = option.payment_mode.code)
        return {'form':form, 'type':'filled', 'payment_mode': option.payment_mode, 'client':option.client}

    if option.payment_mode.code == "cash":
        if request.method == "POST":
            if option.is_active == True:
                form = CashCollectionForm(request.POST, instance = option, prefix = option.payment_mode.code)  
            else:
                form = CashCollectionForm(instance=option, prefix = option.payment_mode.code)
        else:
            form = CashCollectionForm(instance=option, prefix = option.payment_mode.code)
        return {'form':form, 'type':'filled', 'payment_mode': option.payment_mode, 'client':option.client}
   
    if option.payment_mode.code == "cheque":
        if request.method == "POST":
            if option.is_active == True:
                form = ChequeForm(request.POST, instance = option, prefix = option.payment_mode.code)  
            else:
                form = ChequeForm(instance=option, prefix = option.payment_mode.code)
        else:
            form = ChequeForm(instance=option, prefix = option.payment_mode.code)
        return {'form':form, 'type':'filled', 'payment_mode': option.payment_mode, 'client':option.client}

    if option.payment_mode.code in ['store', 'card-at-store', 'cash-at-store',
            'cash-at-office']:
        if request.method == "POST":
            if option.is_active == True:
                form = StoreForm(request.POST, instance = option, prefix = option.payment_mode.code)  
            else:
                form = StoreForm(instance=option, prefix = option.payment_mode.code)
        else:
            form = StoreForm(instance=option, prefix = option.payment_mode.code)
        return {'form':form, 'type':'filled', 'payment_mode': option.payment_mode, 'client':option.client}
        
    if option.payment_mode.code in ["credit-card", "payback", "netbanking", "card-ivr", 
            "credit-card-emi-web","credit-card-emi-ivr", "debit-card", "cod", "cash-collection"]:
        return { 'type':'empty', 'payment_mode':option.payment_mode}
    else:
        if request.method == "POST":
            form = PaymentOptionForm(request.POST, instance = option, prefix = option.payment_mode.code)
        else:
            form = PaymentOptionForm(instance=option, prefix = option.payment_mode.code)
        return {'form':form, 'type':'filled', 'payment_mode': option.payment_mode, 'client':option.client}


def payment_form_fields(request, *args, **kwargs):
    if request.method == "POST":
        form_id = request.POST['form_pm']
        pm = form_id.split('_')[0]
        client_id = int(form_id.split('_')[1])
        client = Client.objects.get(id=client_id)
        deposit_options = None
        payment_mode = PaymentMode.objects.filter(code=pm)
        payment_mode = payment_mode[0]
        if payment_mode.code in ('deposit-transfer'):
            option = DepositPaymentOptions(client=client,
                    payment_mode=payment_mode)
            po_form = get_payment_options_form_obj(request, option)
            form = po_form['form']
            errors=None
            if form.errors:
                errors = form.errors
            else:
                form.save()
                try:
                    po = PaymentOption.objects.get(payment_mode=payment_mode,
                            client=client)
                except:
                    PaymentOption(payment_mode=payment_mode,
                            client=client).save()
            deposit_options = DepositPaymentOptions.objects.filter(client=client,
                    payment_mode=payment_mode)
            return render_to_response('ppd/deposit_form.html',
                {'po_form':po_form,
                 'deposit_options':deposit_options,
                 'errors':errors,
                },
                context_instance=RequestContext(request))
        else:
            try:
                option = PaymentOption.objects.get(client=client,
                    payment_mode=payment_mode)
            except:
                option = PaymentOption(client=client, payment_mode=payment_mode)
        form_obj = get_payment_options_form_obj(request, option)
        if form_obj['type']!= 'empty':
            form = form_obj['form']
            if form.errors:
                return HttpResponse(simplejson.dumps(dict(status="error",
                    errors=form.errors)))
            else:
                form.save()
        else:
            form.save()
        return HttpResponse(simplejson.dumps(dict(status='ok')))
    else:
        code = request.GET['pm_id']
        pm = PaymentMode.objects.filter(code=code)
        pm = pm[0]
        client = request.client.client
        html = 'ppd/settings_mode_display.html'
        if code in ('deposit-transfer'):
            html='ppd/deposit_form.html'
            po_form = None
            option_dt = DepositPaymentOptions.objects.filter(client=client,
                        payment_mode=pm)
            option = DepositPaymentOptions(client=client, payment_mode=pm)
            po_form = get_payment_options_form_obj(request, option)
            return render_to_response(html,
                {'po_form':po_form,
                 'deposit_options':option_dt,
                },
                context_instance=RequestContext(request))
        try:
            option = PaymentOption.objects.get(client=client, payment_mode = pm) 
        except PaymentOption.DoesNotExist:
            option = PaymentOption(client=client, payment_mode = pm)
        form_obj = get_payment_options_form_obj(request, option)
        return render_to_response(html,
                {'po_form':form_obj,
                }, 
                context_instance=RequestContext(request))


def get_payment_dict(request, get_options = False):
    _client = request.client.client
    payment_options = PaymentOption.objects.select_related('payment_mode').filter(client=_client).order_by('-is_active')
    domain_payment_options_list = []
    client_domains = None
    if get_options:
        payment_options = payment_options.filter(is_active=True)
        client_domains = ClientDomain.objects.filter(client=_client,is_channel=1)
        domain_payment_options = DomainPaymentOptions.objects.select_related('client_domain', 'payment_option').filter(client_domain__in=client_domains, payment_option__in=payment_options, payment_option__is_active=True)

        for po in payment_options:
            for cd in client_domains:
                for dpo in domain_payment_options:
                    if dpo.payment_option == po and dpo.client_domain == cd:
                        domain_payment_options_list.append(dpo)
    payment_dict = {
                'payment_options':payment_options,
                'client_domains':client_domains, #client_domains,
                'domain_payment_options_list':domain_payment_options_list,
    }   
    return payment_dict

@login_required
@check_role('Payments-Option Settings')
def option_settings(request):
    option_dict = {}
    option_dict = get_payment_dict(request)
    option_dict['client'] = request.client.client
    return render_to_response('ppd/settings.html', option_dict, context_instance=RequestContext(request))

@login_required
@check_role('Payments-Channel Settings')
def channel_settings(request):
    channel_dict = {}
    channel_dict = get_payment_dict(request, get_options = True)
    channel_dict['client'] = request.client.client
    return render_to_response('ppd/settings_on_off_display.html', channel_dict, context_instance=RequestContext(request))


@login_required
@check_role('Payments-Payouts')
def payouts(request):
    client = request.client.client
    seller = request.session['seller']
    if request.method == "GET":
        payout_home_form = PayoutHomeForm() 
        month = date.today().month
        year = date.today().year
        seller_payout = get_seller_payout_and_process(seller, month, year)
        payouts_dict = {
            'payout_home_form':payout_home_form,
            'seller_payout': seller_payout,
            'month': month,
            'year': year,
            'seller': seller,
            'url':request.get_full_path()
        }
        payouts_dict['client_display_name']=client.name
        return render_to_response('ppd/payouts.html', payouts_dict, context_instance=RequestContext(request))
    
    if request.method == 'POST':
        check = request.POST.get('name', None)
        if check != 'change':
            payout_home_form = PayoutHomeForm(request.POST)
            if payout_home_form.is_valid():
                month = payout_home_form.cleaned_data['month']
                year = payout_home_form.cleaned_data['year']
                seller_payout = get_seller_payout_and_process(seller, month, year)
                payouts_dict = {
                    'payout_home_form':payout_home_form,
                    'seller_payout': seller_payout,
                    'month': month,
                    'year': year,
                    'seller': seller,
                    'url':request.get_full_path(),
                }
                payouts_dict['client_display_name']=client.name
                response = render_to_response('ppd/payouts.html', payouts_dict, context_instance = RequestContext(request))
                return response
            else:
                payouts_dict = {
                    'payout_home_form':payout_home_form,
                }
                payouts_dict.update(user_dict)
                payouts_dict['cid']=client_id
                payouts_dict['sid']=current_seller_id
                payouts_dict['url']=url
                return render_to_response('ppd/payouts.html', payouts_dict, context_instance=RequestContext(request))

def get_seller_payout_and_process(seller, month, year):
    c = calendar.monthrange(int(year),int(str(month)))
    last_day = c[1]
    gte_date = '%s-%s-01' % (str(year),str(month))
    lte_date = '%s-%s-%s' % (str(year),str(month),last_day)
    order_items = OrderItem.objects.filter(seller_rate_chart__seller=seller,order__payment_realized_on__gte=gte_date,order__payment_realized_on__lte=lte_date,state__in=['confirmed','shipped','delivered',None])
    
    try:
        seller_configurations = SellerConfigurations.objects.get(seller=seller)
        percentage_commission = seller_configurations.percentage_commission
        collected_by = seller_configurations.amount_collected_by
        if collected_by == 'chaupaati':
            pass
        else:
            pass
        #calculate transfer price based on percentage commission
        configurations = Configurations.objects.all()
        service_tax = configurations[0].service_tax / Decimal("100")
    except:
        return None
    #payout components
    total_sale_price = Decimal(0)
    total_shipping_charges = Decimal(0)
    total_payment_gateway_charges = Decimal(0)
    chaupaati_discount = Decimal(0)
    seller_discount = Decimal(0)
    total_collected_amount = Decimal(0)
    total_applicable_amount = Decimal(0)
    commission_in_amount = Decimal(0)
    gross_payout = Decimal(0)
    chaupaati_commision_invoice = Decimal(0)
    net_payout = Decimal(0)

    seller_payout_details = SellerPayoutDetails.objects.using('default').filter(month=month,year=year,seller=seller)
    seller_payout_details.delete()

    for order_item in order_items:
        #item wise payout details
        total_sale_price += order_item.sale_price
        total_shipping_charges += order_item.shipping_charges
        discount = Decimal("%.15g" % order_item.spl_discount())
        chaupaati_discount += discount
        #seller_discount +=
        #total_payment_gateway_charges += order_item.
        payable_amount = Decimal("%.15g" % order_item.payable_amount())
        total_collected_amount += payable_amount
        total_applicable_amount += ( payable_amount + discount)
        commission_in_amount += (order_item.seller_rate_chart.transfer_price)

        #save payout details for each item
        seller_payout_details = SellerPayoutDetails()
        seller_payout_details.year = year
        seller_payout_details.month = month
        seller_payout_details.order_item = order_item
        seller_payout_details.seller = seller
        seller_payout_details.sale_price = order_item.sale_price
        seller_payout_details.shipping_charges = order_item.shipping_charges
        #seller_payout_details.gateway_charges
        seller_payout_details.chaupaati_discount = Decimal("%.15g" % order_item.spl_discount())
        #seller_payout_details.seller_discount =
        seller_payout_details.collected_amount = Decimal("%.15g" % order_item.payable_amount())
        seller_payout_details.applicable_amount = seller_payout_details.collected_amount + seller_payout_details.chaupaati_discount
        seller_payout_details.commision_amount = order_item.seller_rate_chart.transfer_price
        seller_payout_details.gross_payout = seller_payout_details.collected_amount - seller_payout_details.commission_amount
        seller_payout_details.commission_invoice_amount = seller_payout_details.commission_amount + (seller_payout_details.commission_amount * service_tax)
        seller_payout_details.net_payout = seller_payout_details.applicable_amount - seller_payout_details.commission_invoice_amount
        seller_payout_details.save()


    gross_payout = total_applicable_amount - commission_in_amount
    chaupaati_commision_invoice = commission_in_amount + (commission_in_amount * service_tax)
    net_payout = total_applicable_amount - chaupaati_commision_invoice

    #payout totals
    try:
        seller_payout = SellerPayout.objects.get(month=month,year=year,seller=seller)
        seller_payout.delete(using='default')
        seller_payout = SellerPayout()
    except:
        seller_payout = SellerPayout()
    seller_payout.seller = seller
    seller_payout.month = month
    seller_payout.year = year
    seller_payout.sale_price = total_sale_price
    seller_payout.shipping_charges = total_shipping_charges
    seller_payout.gateway_charges = total_payment_gateway_charges
    seller_payout.chaupaati_discount = chaupaati_discount
    seller_payout.seller_discount = seller_discount
    seller_payout.collected_amount = total_collected_amount
    seller_payout.applicable_amount = total_collected_amount + chaupaati_discount
    seller_payout.commission_amount = commission_in_amount
    seller_payout.gross_payout = gross_payout
    seller_payout.commission_invoice_amount = chaupaati_commision_invoice
    seller_payout.net_payout = net_payout
    seller_payout.save()
    return seller_payout

#promotions list
@login_required
@check_role('Orders')
def promotions_list(request, fromindex):
    promotionsJsonStr = APIManager.getAllPromotions(fromindex, 10)
    promotionsJson = simplejson.loads(promotionsJsonStr)
    i=1
    for promo in promotionsJson['promotions'] :
        promo['url'] = '/show_promotion/'+client_name+'/'+seller_name+'/'+str(promo['promotionId'])+'/'  
        promo['onbutton'] = str(promo['promotionId']) + 'on' 
        promo['onnotbutton'] =  str(promo['promotionId']) + 'onnot' 
        promo['buttonname'] = str(promo['promotionId'])
        promo['index'] = 'promo' + str(i)
        promo['len'] = len(promo['coupons'])
        if(len(promo['coupons'])>0):
            promo['firstcoupon'] = promo['coupons'][0]
        else:
            promo['firstcoupon'] = ''
        i=i+1
        

    i=1
    for promo in promotionsJson['promotions'] :
        promo['url'] = '/show_promotion/'+client_name+'/'+seller_name+'/'+str(promo['promotionId'])+'/'  
        promo['onbutton'] = str(promo['promotionId']) + 'on' 
        promo['onnotbutton'] =  str(promo['promotionId']) + 'onnot' 
        promo['buttonname'] = str(promo['promotionId'])
        promo['index'] = 'promo' + str(i)
        i=i+1
    
    fromindex_next = int(fromindex) + 10
    fromindex_prev = int(fromindex) - 10
    if fromindex_prev < 0:
        fromindex_prev = 0    

    promotions_list_dict = {
        'loggedin':True,
        'clients':clients,
        'accounts':accounts,
        'client_name':client_name,
        'seller_name':seller_name,
        'promotions':promotionsJson,
        'fromindex_next':fromindex_next,
        'fromindex_prev':fromindex_prev,
        'fromindex':fromindex,
        'client_display_name':Client.objects.filter(slug=client_name)[0].name
    }

    return render_to_response('ppd/promotions_list.html',promotions_list_dict, context_instance=RequestContext(request))

#inventory landing function
@never_cache
@check_role('Category-Inventory')
def inventory_module(request, update_type):
    client = request.client.client
    seller = request.session['seller'][0]
    #Populating the required fields for rendering Seller's Hub Pages
    count = 0
    if update_type == 'inventory_bulk_upload':
        return inventory_bulk_upload(request, seller=seller)
    if update_type == 'inventory_upload_success':
        return inventory_upload_success(request, seller=seller)
    #if update_type == 'inventory_articlelevel_update':
    #    return update_articlelevel_inventory(request)
    #if update_type == 'otc_upload':
    #    return upload_otc_pincodes(request, seller, client_id, count, user_dict, profile)
    #if update_type == 'slo_upload':
    #    return upload_pincodes(request, client_name, seller_name,seller, client_id, count, profile)
    #if update_type == 'gen_reprt':
    #    return generate_inventory_report(request,client_name, seller_name,  seller, client_id, count, profile)
    if update_type == 'all_inventory':
        return show_all_inventory_levels(request, seller=seller)
    if update_type == 'edit_virtual_inventory':
        return edit_virtual_inventory(request, seller=seller)
    if update_type == 'add_vi':
        return add_virtual_inventory(request, seller=seller)
    if update_type == 'delete_vi':
        return delete_virtual_inventory(request, seller=seller)
    if update_type == 'edit_physical_inventory':
        return edit_physical_inventory(request, seller=seller)
    if update_type == 'edit_backorder':
        return edit_backorderable_entry(request, seller=seller)
    if update_type == 'sto':
        return sto_report(request, seller=seller)


@login_required
@never_cache
@check_role('Category-Pricing')
def client_pricing(request, update_type):
    client = request.client.client
    seller = request.session['seller']
    if update_type == 'search_by_sku':
        return search_by_sku(request, seller=seller)
    if update_type == 'upload_xls':
        return upload_price_xls(request, seller=seller)
    if update_type == 'approve_pricing_job':
        return approve_pricing_job(request, seller=seller)
    if update_type == 'gen_reprt':
        return generate_pricing_report(request, seller=seller)
    if update_type == 'all_prices':
        return all_prices(request, seller=seller)

@login_required
def seller_change(request):
    client = request.client.client
    if request.method == 'POST':
        seller_id = request.POST['user_sellers']
        url = request.POST['url']
        if not seller_id == 'all-sellers':
            request.session['seller'] = Account.objects.filter(id=seller_id)
        else:
            request.session['seller'] = request.session['all_sellers']
        return HttpResponseRedirect(url)

@login_required
@check_role('User Experience-Lists')
def view_all_lists(request):
    client = request.client.client
    seller = request.session['seller']
    list_obj = List.objects.filter(client=client.id).order_by('-id')
	#passing dictionary
    lists_intro_dict = {	
		'list_objects':list_obj,
		'len': len(list_obj),
        }
    return render_to_response('lists/lists_intro.html', lists_intro_dict, context_instance=RequestContext(request))

@login_required
@check_role('User Experience-Lists')
def add_new_list(request):
	flag, dflag, errorflag = 0, 0, 0
	#coordflag=0
	ID=0
	if request.method == "POST":#If the form has been submitted
		#print "post----"
		form = ListsForm(request.POST, request.FILES, prefix="lists")
		iteminlineformset = inlineformset_factory(List, ListItem, form = ListItemForm, extra  = 2)
		#formset = iteminlineformset(request.POST, request.FILES, instance = None)
		#coordformset = CoordinatesForm(request.POST,prefix="coordinates")
		#coordinlineformset = inlineformset_factory(List, Coordinates, form =CoordinatesForm, extra=1) 
		#coordformset = coordinlineformset(request.POST, instance=None, prefix="coordinates")

		if 'additem' in request.POST:
			dflag=1
			flag=1
			errorflag=1
			cp=request.POST.copy()
			cp['listitem_set-TOTAL_FORMS']=int(cp['listitem_set-TOTAL_FORMS'])+1
			formset=iteminlineformset(cp,  instance=None)
		elif 'save' in request.POST:
			flag=1
			errorflag=0
			objflag=0
			#print "save--------------"
			formset = iteminlineformset(request.POST,request.FILES, instance = None)
			if form.is_valid():
				#print "formset-----------", formset
				flag=1
				clientobj = request.client.client
				obj=List()
				objlist = List()
				title = form.cleaned_data['title']
				objlist.title = form.cleaned_data['title']
				objlist.slug=slugify(title)
				objlist.client = clientobj
				form.client = clientobj
				objlist.starts_on = request.POST.get('lists-starts_on', None)
				objlist.ends_on = request.POST.get('lists-ends_on',None)
				if objlist.starts_on:
					if objlist.ends_on:
						pass
					else:
						objlist.ends_on=None
				else:
					objlist.starts_on=None
					objlist.ends_on=None
				type = form.cleaned_data['type'] 
				client_obj = request.client.client
				objlist.type = form.cleaned_data['type']
				objlist.template_type = form.cleaned_data['template_type']
				objlist.description = form.cleaned_data['description']
				#objlist.visibility = form.cleaned_data['visibility']
				objlist.banner_image=form.cleaned_data['banner_image']
				#print "objlist.banner/_image in add------------------------", objlist.banner_image
				#objlist.tagline=form.cleaned_data['tagline']
				#objlist.sort_order=form.cleaned_data['sort_order']
				objlist.redirect_to=form.cleaned_data['redirect_to']
				objlist.banner_type=form.cleaned_data['banner_type']
				#print "objlist.banner_type---------", objlist.banner_type
				#if objlist.banner_type=='image_mapping':
			#		coordflag=1
		#			print "suceess------"
				for i in formset.forms:
					if i.is_valid():
						seq = i.cleaned_data['sequence']
						if seq<>None:
							print "sequence not none"
							if seq<=0:
								print "my sequence is", seq
								errorflag=1
								print "my error is------------", errorflag
					else:
						objflag=1
				#print "objflag before saving-----------", objflag
				#print "errorflag before saving-----------", errorflag
				if objflag==0 and errorflag==0:
					#print "objflag==", objflag
					#if errorflag==0:
					objlist.save()
					objlist=List.objects.get(title=title, type=type, client = client_obj.id)
					ID = objlist.id
					list_obj = List.objects.filter(client=client_obj.id)
					
				for i in formset.forms:
					#print "in for"
					if i.is_valid():
						#print "i valid"
						try:
							#print "in try---------"
							listitemobj = ListItem()
							listobj = List.objects.filter(type=type, client = client_obj, title=title)
							#print "listobj is----------------", listobj
							#print "error after this"
							id1 = listobj[0].id
							#print "error before this"
							i.list_id = id1
							listitemobj.list = listobj[0]
							sku = i.cleaned_data['sku']
							#sku= 6056
							#print "sku--------", sku
							listitemobj.sku_id = sku.id
							#listitemobj.sku_id=6056
							listitemobj.sequence = i.cleaned_data['sequence']
							if listitemobj.sequence==None:
								listitemobj.sequence=999
							if listitemobj.sequence <=0:
								#print "sequence error"
								errorflag=1
							listitemobj.user_description = i.cleaned_data['user_description']
							listitemobj.user_title = i.cleaned_data['user_title']
							user_features = i.cleaned_data['user_features']
							listitemobj.starts_on = objlist.starts_on
							listitemobj.ends_on = objlist.ends_on
							listitemobj.status = i.cleaned_data['status']
							listitemobj.user_image=i.cleaned_data['user_image']
							#print "listitemobj.banner/_image in add------------------------", listitemobj.user_image
							listitemobj.redirect_to=form.cleaned_data['redirect_to']
							#print "listitemobj-------------", listitemobj
							listitemobj.save()
						except Exception,e:
							#print "2222222222222except, ", e
							pass
					else:
						errorflag=1
						#print "i invalid, i errors %s" % repr(i.errors)
				if errorflag==0:
					pass
					#objlist.save()
			else:
				errorflag=1
		lists_dict = {
			'form': form,
			#'coordformset':coordformset,
			'formset':formset,
			'ID':ID,
			'flag':flag,
			'errorflag':errorflag,
			'dflag':dflag,
			#'coordflag':coordflag,
			'pg':1,
			}
		return render_to_response('lists/lists.html', lists_dict, context_instance=RequestContext(request))
	else:
		flag=1
		errorflag=1
		form = ListsForm(prefix="lists")
		iteminlineformset = inlineformset_factory(List, ListItem, form = ListItemForm, extra=2)
		formset = iteminlineformset(instance = None)
		lists_dict = {
			'form': form,
			#'coordformset':coordformset,
			'formset': formset,
			'flag':flag,
			#'dflag':dflag,
			'errorflag':errorflag,
			#'coordflag':coordflag,
			'pg':1,
		}
	return render_to_response('lists/lists.html', lists_dict, context_instance=RequestContext(request))

@login_required
@check_role('User Experience-Lists')
def search_item(request, pg):
	pagination = {}
	srcitems =[]
	src_page=[]
	search_page=[]
	url = request.get_full_path()
	sku_id=0
	sku_items1=[]
	sku_items2=[]
	sku_items=[]
	sku_id = request.GET.get('sku_id')
	try:
		medium = request.GET.get('medium', 'cc')
		items_per_page =20
		if sku_id:
			try:
				sku_items1 = SellerRateChart.objects.select_related('id', 'product' ,'sku').filter(Q(id__icontains = sku_id)|Q(sku__icontains=sku_id))
				for i in sku_items1:
					sku_items.append(i)
			except:
				pass
			k = Product.objects.filter(title__icontains= sku_id)
			for i in k:
				sku_items2 = SellerRateChart.objects.select_related('id', 'product', 'sku').filter(Q(product=i))
				for j in sku_items2:
					sku_items.append(j)	
			paginator = Paginator(sku_items, items_per_page)
		else:
			srcitems = []
			#srcitems = SellerRateChart.objects.filter()
			paginator = Paginator(srcitems, items_per_page)
		try:
			page = int(request.GET.get('page',1))
		except ValueError:
			page=1
		base_url=request.get_full_path()
		page_pattern = re.compile('[&?]page=\d+')
		base_url = page_pattern.sub('', base_url)
		if base_url.find('?')==-1:
			base_url = base_url+'?'
		else:
			base_url = base_url+'&'
		pagination = getPaginationContext(page, paginator.num_pages, base_url)

		try:
			src_page = paginator.page(page)
		except(emptyPage, InvalidPage):
			src_page = paginator.page(paginator.num_pages)
	except Exception, e:
		log.exception('Exception while rendering items %s' % repr(e))
		
	skupage_dict ={
		'pagination':pagination,
		'srcitems': src_page,
	}
	return render_to_response('lists/skupage.html', skupage_dict, context_instance=RequestContext(request))

@login_required
@check_role('User Experience-Lists')
def list_display(request, ID):
	coordflag=0
	client_obj = request.client.client
	list_obj = List.objects.filter(client=client_obj.id)
	listobj = List.objects.get(id = ID)
	coordobj = Coordinates.objects.filter(list=listobj)
	if listobj.banner_type=='image_mapping':
		coordflag=1
	listitemobj = ListItem.objects.filter(list = listobj)
	srcobj=[]
	for i in listitemobj:
		src = SellerRateChart.objects.get(id=i.sku.id)
		srcobj.append(src)
	l = len(listitemobj)
	list_display_dict = {	
            'coordflag':coordflag,
			'len':l,
			'srcobj':srcobj,
			'ID': ID,
			'list_objects':listobj,
			'listitemobj':listitemobj,
			'coordobj': coordobj,
		}
	return render_to_response('lists/list_display.html', list_display_dict, context_instance=RequestContext(request))

@login_required
@check_role('User Experience-Lists')
def edit_list(request, ID):
	flag=0
	listitem12=[]
	listitemobj=[]
	dflag=0
	errorflag=0
	objflag=0
	if request.method == "POST":
		a = List.objects.get(id=ID)
		form=ListsForm(request.POST,request.FILES, instance=a)
		b=ListItem.objects.filter(list=a)
		l = len(b)
		iteminlineformset = inlineformset_factory(List, ListItem, form=ListItemForm, max_num=0)
		#if request.POST.get("id")=="Delete":
		if "dellist" in request.POST:

			formset = iteminlineformset(request.POST,request.FILES, instance=a)
			flag=2
			a = List.objects.get(id=ID)
			b = ListItem.objects.filter(list=a)
			a.delete()
			b.delete()
			client_obj = request.client.client
			list_obj = List.objects.filter(client=client_obj.id)

		elif "save" in request.POST:
			#print "a----------------", a
			#print "b----------------", b
			formset = iteminlineformset(request.POST,request.FILES, instance=a)
			flag=1
			errorflag=0
			#print "erorflag in save-------------", errorflag
			if form.is_valid():
				errorflag=0
				#print "errorlfag in form.isvalid------------", errorflag
				clientobj = request.client.client
				objlist= List.objects.get(id=ID)
				old_starts_on=objlist.starts_on
				old_ends_on=objlist.ends_on
				title = form.cleaned_data['title']
				type= form.cleaned_data['type']
				objlist.title = form.cleaned_data['title']
				objlist.slug = form.cleaned_data['slug']
				objlist.client = clientobj
				form.client = clientobj
				objlist.type = form.cleaned_data['type']
				objlist.template_type = form.cleaned_data['template_type']
				objlist.description = form.cleaned_data['description']
				objlist.starts_on = request.POST.get('starts_on',None)
				objlist.ends_on = request.POST.get('ends_on',None)
				#objlist.is_featured = form.cleaned_data['is_featured']
				#objlist.visibility = form.cleaned_data['visibility']
				objlist.banner_image=form.cleaned_data['banner_image']
				if objlist.banner_image==False:
					objlist.banner_image=None
				print "objlist.banner_image---------------", 	objlist.banner_image
				#objlist.tagline=form.cleaned_data['tagline']
				#objlist.sort_order=form.cleaned_data['sort_order']
				objlist.redirect_to=form.cleaned_data['redirect_to']
				objlist.banner_type=form.cleaned_data['banner_type']
				if objlist.starts_on:
					if objlist.ends_on:
						pass
					else:
						objlist.ends_on=old_ends_on
				else:
					objlist.starts_on=old_starts_on
					objlist.ends_on=old_ends_on

				for i in formset.forms:
					if i.is_valid():
						seq = i.cleaned_data['sequence']
						if seq<>None:
							print "sequence not none"
							if seq<=0:
								print "my sequence is", seq
								errorflag=1
								print "my error is------------", errorflag
					else:
						objflag=1
				#print "objflag before saving-----------", objflag
				#print "errorflag before saving-----------", errorflag
				if objflag==0 and errorflag==0:
					#print "objflag==", objflag
					#if errorflag==0:
					objlist.save()

				#objlist.save()
				client_obj = request.client.client
				list_obj = List.objects.filter(client=client_obj.id)
				listobj = List.objects.get(id=ID)
				listitem12=ListItem.objects.filter(list=listobj)
				listitemobj=[]
				count=0
				for i in formset.forms:
					#print "edit in for--------_", i
					if i.is_valid():
						errorflag=0
						#print "is valid"
						try:
							#print "edit in try----------"
							sku = i.cleaned_data['sku']
							#print "sku-----", sku.id
							listitem =ListItem()
							listitem.list = listobj
							listitem.sku_id = sku.id
							listitem.sequence = i.cleaned_data['sequence']
							if listitem.sequence==None:
								listitem.sequence=999
							if listitem.sequence <=0:
								errorflag=1
							listitem.user_description = i.cleaned_data['user_description']
							listitem.user_title = i.cleaned_data['user_title']
							listitem.user_features = i.cleaned_data['user_features']
							listitem.starts_on = objlist.starts_on
							listitem.ends_on = objlist.ends_on
							listitem.status = i.cleaned_data['status']
							listitem.user_image = i.cleaned_data['user_image']

							if listitem.user_image==False:
								listitem.user_image=None
							listitem.redirect_to = i.cleaned_data['redirect_to']
							#print "listiemffuawer image------", listitem.user_image
							listitemobj.append(listitem)
							count=count+1
							#listitemobj.save()
						except Exception ,e:
							#print "exception 1", e
							pass
					else:
						errorflag=1
						#print "errorflag-------------", errorflag
						#print "i invalid, i errors %s" % repr(i.errors)
			else:
				errorflag=1
				#print "errorflag==", errorflag
				#print "forminvlaid %s" % repr(form.errors)
			if errorflag==0 and objflag==0:
				for i in listitem12:
					#print "hahahaaa---", i
					i.delete()
				for i in listitemobj:
					#print i
					i.save()

		elif "additem" in request.POST:
			flag=1
			errorflag=1
			#print "flag in additem post edit----", flag
			#print "errorflag in additem post edit------------", errorflag
			dflag=1

			formset = iteminlineformset(request.POST,request.FILES, instance=a)
			#print "calling additem in request.post"
			a = List.objects.get(id=ID)
			form=ListsForm(request.POST,request.FILES, instance=a)
			b=ListItem.objects.filter(list=a)
			l = len(b)
			iteminlineformset = inlineformset_factory(List, ListItem, form=ListItemForm)
			cp=request.POST.copy()
			np = request.POST.copy()
			cp['listitem_set-TOTAL_FORMS']=int(cp['listitem_set-TOTAL_FORMS'])+1
			formset=iteminlineformset(cp,request.POST , instance=a)
		#print "flag just before edit_dict---------------", flag
		#print "erorflag just before edit_dict---------------", errorflag
		edit_dict = {
			'form': form,
			'formset':formset,
			'size': l,
			'ID':ID,
			'flag':flag,
			'dflag':dflag,
            'errorflag':errorflag,
			#'coordflag':coordflag,
			'obj':a,
			'pg':1,
			}
		return render_to_response('lists/edit_lists.html', edit_dict, context_instance=RequestContext(request))

	else:
		a = List.objects.get(id=ID)
		form =ListsForm(instance=a)
		b = ListItem.objects.filter(list=a)
		l =len(b)
		flag=1
		errorflag=1
		#print "flag in get========", flag
		#print "errorflag in get---------", errorflag
		iteminlineformset = inlineformset_factory(List, ListItem, form = ListItemForm, max_num=0)
		formset = iteminlineformset(instance =a)
		edit_dict = {	
			'ID':ID,
            'errorflag':errorflag,
			'flag':flag,
			'dflag':dflag,
			#'coordflag':coordflag,
			'form':form,
			'formset':formset,
			'size':l,
			'obj':a,
            'pg':1
		}
	return render_to_response('lists/edit_lists.html', edit_dict, context_instance=RequestContext(request))

@login_required
@check_role('User Experience-Lists')
def delete_item(request):
    f = request.GET.get("sku")
    listid= request.GET.get("id")
    arr=[]
    k  = str(f)
    while True:
		a= k.partition(',')[0]
		b=k.partition(',')[1]
		c=k.partition(',')[2]
		arr.append(a)
		if(b):
			k=c
		else:
			break
    listobj= List.objects.get(id=listid)
    for i in arr:
		srcobj = SellerRateChart.objects.filter(sku=i)
		listitemobj=ListItem.objects.filter(list=listobj, sku=i)
		listitemobj.delete()
    client_obj = request.client.client
    list_obj = List.objects.filter(client=client_obj.id)
    lists_intro_dict = {	
		'list_objects':list_obj,
		}
    return render_to_response('ppd/lists_intro.html', lists_intro_dict, context_instance=RequestContext(request))

@login_required
@check_role('User Experience-Lists')
def coordinates(request, ID):
	nflag=0
	if request.method=="POST":
		errorflag=0
		coordformset = modelformset_factory(Coordinates, max_num=0, extra=4)
		data = {
			'coord-TOTAL_FORMS':u'4',
			'coord-INITIAL_FORMS':u'4',
			'coord-MAX_NUM_FORMS':u'4',
			}

		formset = coordformset(request.POST, prefix='coord')
		coordlist=[]
		for i in formset.forms:
			if i.is_valid():
				nflag=1
				try:
					coordobj= Coordinates()
					listobj = List.objects.get(id=ID)
					coordobj.list=listobj
					coordobj.sequence=i.cleaned_data['sequence']
					if coordobj.sequence<=0 and coordobj.sequence>=10:
						errorflag=1
					coordobj.co_ordinates=i.cleaned_data['co_ordinates']
					coordobj.link=i.cleaned_data['link']
					if coordobj.sequence:
						coordlist.append(coordobj)
				except Exception, e:
					pass
			else:
				k=i.errors
				for j in k:
					if j.find('sequence'):
						pass
				errorflag=1
		listobj = List.objects.get(id=ID)
		try:
			queryset = Coordinates.objects.filter(list=listobj)
			if errorflag==0:
				for i in queryset:
					i.delete()
		except Exception, e:
			pass
		if errorflag==0:
			for i in coordlist:
				i.save()
			nflag=1
		coordinates_dict = {
			'formset':formset,
			'ID':ID,
			'ID':listobj.id,
			'listobj':listobj,
			'nflag':nflag,
			'errorflag': errorflag,
			}
		return render_to_response('lists/coordinates.html', coordinates_dict, context_instance=RequestContext(request))
	else:
		nflag=1
		errorflag=1 
		coordformset = modelformset_factory(Coordinates, form=CoordinatesForm, extra=4)
		listobj=List.objects.get(id=ID)
		data = {
			'coord-TOTAL_FORMS':u'4',
			'coord-INITIAL_FORMS':u'4',
			'coord-MAX_NUM_FORMS':u'4',
		}
		try:
			queryset12 = Coordinates.objects.filter(list=listobj) 
			formset = coordformset(prefix='coord', queryset=queryset12)
		except Exception, e:
			formset = coordformset(prefix='coord')
		for i in formset:
			try:
				pass
			except Exception,e:
				pass
		coordinates_dict = {
			'formset':formset,
			'listobj':listobj,
			'ID':listobj.id,
			'nflag':nflag,
			'errorflag':errorflag,
        }
	return render_to_response('lists/coordinates.html', coordinates_dict, context_instance=RequestContext(request))


def view_coordinates(request, ID):
	listobj=List.objects.get(id=ID)
	coordobj=Coordinates.objects.filter(list=listobj)
	view_coordinates_dict = {
		'ID':ID,
		'listobj':listobj,
		'coordobj':coordobj,
		}
	return render_to_response('lists/view_coordinates.html', view_coordinates_dict, context_instance=RequestContext(request))


def mdel(request):
	f = request.GET.get("id")
	arrlist=[]
	arritem=[]
	k  = str(f)
	while True:
		a= k.partition(',')[0]
		b=k.partition(',')[1]
		c=k.partition(',')[2]
		arrlist.append(a)
		if(b):
			k=c
		else:
			break
	for i in arrlist:
		listobj = List.objects.get(id=i)
		listitemobj=ListItem.objects.filter(list=listobj)
		arritem.append(listitemobj)
		listobj.delete()
		listitemobj.delete()
	delete_confirm_dict ={
		'arrlist':arrlist,
		'arritem':arritem,
	}
	client_obj = request.client.client
	list_obj = List.objects.filter(client=client_obj.id)
	lists_intro_dict = {	
		'list_objects':list_obj,
		}	
	return render_to_response('ppd/lists_intro.html', lists_intro_dict, context_instance=RequestContext(request))
