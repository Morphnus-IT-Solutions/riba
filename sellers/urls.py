from django.conf.urls.defaults import *
from django.http import HttpResponseRedirect
from django.contrib import admin
from django.conf.urls.defaults import url
from django.conf import settings
from web.views.ppd_views import *  #import only those functions which are required
from web.views.user_views import * #import only those functions which are required
admin.autodiscover()
handler500 = 'web.views.errors.handle505'
handler404 = 'web.views.errors.handle404'

#fulfillment views
urlpatterns = patterns('fulfillment.views',
    (r'^fulfillment/ifs_database/$', 'ifs_select'),
    url(r'^fulfillment/ifs_database/(?P<selected_table>[a-zA-Z_\-]+)/(?P<selected_action>[a-zA-Z_\-]+)/$', 'ifs_actions', name='upload-ifs'),
    (r'^fulfillment/check_fulfillment/$', 'fulfillment_check'),
    #(r'^ifs/upload/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/','web.views.ppd_views.ifs_select',name='ifs-select'), 
    #(r'^ifs/fulfillment/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/','web.views.ppd_views.fulfillment_check',name='fulfillment'),
    )

urlpatterns += patterns('web.views',
    (r'^login/$', 'home.login',{'template_name':'systems/login.html'}),
    (r'^sales/orders/update_shipping_info/(?P<order_id>[0-9]+)$', 'user_views.update_shipping_info'),
    )

urlpatterns += patterns('sellers.views',
    (r'^$', 'landing_page'),
# tabs urls
    (r'^home/$', 'home'),
    (r'^sales/$', 'sales_tab'),
    (r'^category/$', 'category_tab'),
    (r'^payments/$', 'payments_tab'),
    (r'^marketing/$', 'marketing_tab'),
    (r'^management/$', 'management_tab'),
    (r'^user_experience/$', 'user_experience_tab'),
    (r'^fulfillment/$', 'fulfillment_tab'),

#sub tabs of sales
    (r'^sales/orders/$', 'orders_tab'),
    (r'^sales/orders/(?P<order_state>[a-zA-Z]+)/$', 'orders'),
    (r'^sales/orders/(?P<order_id>[0-9]+)/$', 'order_detail'),

#sub tabs of category
    (r'^category/category_management/$', 'category_management_tab'),
    (r'^category/products/$', 'products'),
    (r'^category/product_reviews/(?P<status>[a-zA-Z]+)/$', 'product_reviews'),
    (r'^category/product_reviews/approve_or_disapprove_review/$', 'approve_or_disapprove_review'),
    (r'^reviews/approve_or_disapprove_review','approve_or_disapprove_review'),
    #inventory urls
    (r'^category/category_management/inventory/$', 'inventory_tab'),
    (r'^category/category_management/inventory/(?P<update_type>[a-zA-Z-_/]+)/$', 'inventory_module'),
    #pricing urls
    (r'^category/category_management/pricing/$', 'pricing_tab'),
    (r'^category/category_management/pricing/(?P<update_type>[a-zA-Z-_/]+)/$', 'client_pricing'),

#sub tabs of management
    (r'^management/user_rights/$', 'users'),
    (r'^management/user_rights/add/$', 'create_or_edit_users'),
    (r'^management/profile/$', 'profile'),
    (r'^management/notifications/$', 'notifications'),

#sub tabs of payments
    (r'^payments/option_settings/$', 'option_settings'),
    (r'^payments/channel_settings/$', 'channel_settings'),
    (r'^payments/payouts/$', 'payouts'),
    (r'^payments/payment_form_fields/', 'payment_form_fields'),
    (r'^payments/activate_payment_option', 'activate_payment_option'),
    (r'^payments/channel_payment_option_on_or_off/', 'channel_payment_option_on_or_off'),
    #(r'^payments/second_factor_auth', 'second_factor_auth'),
    #(r'^payments/order_taking_option', 'order_taking_option'),

#sub tabs of marketing
    (r'^marketing/manage_promotions/(?P<fromindex>[0-9]+)/$', 'promotions_list'),

#sub tabs of user_experience
    (r'^user_experience/site_properties/$', 'site_properties_tab'),
    (r'^user_experience/site_properties/lists/$', 'lists_tab'),
    (r'^user_experience/site_properties/lists/view_all_lists/$', 'view_all_lists'),
    (r'^user_experience/site_properties/lists/add_new_list/$', 'add_new_list'),
    (r'^user_experience/site_properties/lists/searchitem/(?P<pg>[0-9]+)/$', 'search_item'),
    (r'^user_experience/site_properties/lists/display_list/(?P<ID>[0-9]+)/$', 'list_display'),
    (r'^user_experience/site_properties/lists/edit/(?P<ID>[0-9]+)/$', 'edit_list'),
	(r'^user_experience/site_properties/lists/delete_item/$','delete_item'),
	(r'^user_experience/site_properties/lists/coordinates/(?P<ID>[0-9]+)/$', 'coordinates'),
	(r'^user_experience/site_properties/lists/view_coordinates/(?P<ID>[0-9]+)/$', 'view_coordinates'),
	(r'^mdel/$', 'mdel'),


#logout
    (r'^auth/signout/$', 'logout'),
    (r'^seller_change/$', 'seller_change'),
#admin site urls
    (r'^admin/', include(admin.site.urls)),
    )

if settings.DEBUG:
    urlpatterns += patterns('',(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}) )
