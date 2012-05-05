from django.conf.urls.defaults import *
from django.http import HttpResponseRedirect
from django.contrib import admin

from django.conf.urls.defaults import url
from web.views.ppd_views import *
from web.views.user_views import *
admin.autodiscover()

handler500 = 'web.views.errors.handle505'
handler404 = 'web.views.errors.handle404'

urlpatterns = patterns('',
    # base menu pages:
    (r'^(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/category/$', 'web.views.ppd_views.category'),
    (r'^(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/sales/$', 'web.views.ppd_views.sales'),
    (r'^(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/marketing/$', 'web.views.ppd_views.marketing'),
    (r'^(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/payments/$', 'web.views.ppd_views.payments'),
    (r'^(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/management/$', 'web.views.ppd_views.management'),
    # handle find requests
    (r'^category', 'web.views.ppd_views.category'),
    (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/assets/images/favicon.ico'}),
    (r'^robots.txt$','web.views.ppd_views.robots'),
    (r'^sitemap$','web.views.ppd_views.sitemap'),
    (r'^(?P<page>[a-zA-Z0-9\-]+).html$', 'web.views.ppd_views.serve_static'),

    # PPD seller pages
    #(r'^$',user_dashboard),
    (r'^accounts/login', 'web.views.home.login',{'template_name':'systems/login.html'}),
    #(r'^home/',user_dashboard),
    url(r'^home/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', user_login_page, name='ppd-user-login-page'), 
    url(r'^(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/category/products/$', user_products, name='ppd-user-products'),
    url(r'^promotions_list/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<fromindex>[0-9]+)/$', promotions_list, name='promotions-list'),
    url(r'^show_promotion/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<promotionid>[0-9]+)/$', show_promotion, name='show-promotion'), 
    url(r'^show_coupons/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<promotionid>[0-9]+)/$', show_coupons, name='show-coupons'), 
 
    url(r'^save_promotion_list/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<fromindex>[0-9]+)/$', save_promotion_list, name='save-promotion-list'),

    url(r'^create_new_promotion/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', create_new_promotion, name='create-new-promotion'),
    url(r'^save_promotion/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', save_promotion, name='save-promotion'),
    url(r'^(?P<seller_name>[a-zA-Z0-9_\-]+)/sales/orders/(?P<order_state>[a-zA-Z0-9_\-]+)/$', user_orders, name="ppd-user-orders"),
    url(r'^profile/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', 'web.views.ppd_views.user_profile', name='ppd-user-profile'),
    #adding a new url for lists
#	url(r'^additems/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<ID>[0-9]+)/$', 'web.views.ppd_views.user_additems', name='ppd-user-additems'),
	url(r'^edit/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<ID>[0-9]+)/$', 'web.views.ppd_views.user_editlists', name='ppd-user-editlists'),
	url(r'^coordinates/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<ID>[0-9]+)/$', 'web.views.ppd_views.user_coordinates', name='ppd-user-coordinates'),
	url(r'^viewcoordinates/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<ID>[0-9]+)/$', 'web.views.ppd_views.user_view_coordinates', name='ppd-user-view-coordinates'),

	#url(r'^delete/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<ID>[0-9]+)/$', 'web.views.ppd_views.user_deletelists', name='ppd-user-deletelists'),
#	url(r'^delconfirm/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', 'web.views.ppd_views.user_delconfirm', name='ppd-user-delconfirm'),
	url(r'^itemdel/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$','web.views.ppd_views.user_itemdel', name='ppd-user-itemdel'),
	url(r'^mdel/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', 'web.views.ppd_views.user_mdel', name='ppd-user-mdel'),
	url(r'^listdisplay/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<ID>[0-9]+)/$', 'web.views.ppd_views.user_list_display', name='ppd-user-displayitems'),
	#/additems/ezoneonline/letsbuy/48/?page=1
	url(r'^itemsku/(?P<client_name>[a-zA-Z0-0_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<pg>[0-9]+)/$', 'web.views.ppd_views.skupagination', name='ppd-skupagination'),
	url(r'^addlists/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', 'web.views.ppd_views.user_addlists', name='ppd-user-addlists'),
    url(r'^lists/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', 'web.views.ppd_views.user_lists', name='ppd-user-lists'),
    url(r'^notification/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', 'web.views.ppd_views.user_notification', name='ppd-user-notifications'),
    url(r'^payment/settings/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', 'web.views.ppd_views.payment_settings', name='ppd-user-payment-settings'),
    url(r'^payment/options/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', payment_options, name='ppd-user-payment-options'),
    url(r'^payouts/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$',user_payouts, name='ppd-user-payouts'),
    url(r'^reports/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<report_type>[a-zA-Z0-9_\-]+)/$', 'web.views.ppd_views.user_reports', name='ppd-user-reports'),
    (r'^reviews/approve_or_disapprove_review',approve_or_disapprove_review),
    url(r'^catalog/reviews/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<status>[a-zA-Z0-9_\-]+)/$',user_reviews, name='ppd-user-reviews'),
    #(r'^prices/price_version_details',price_version_details),
    url(r'^prices/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<update_type>[a-zA-Z0-9_\-]+)/$',client_pricing, name='ppd-user-pricing'),
    #(r'^prices/price_version_details',price_version_details),
    url(r'^inventory/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<update_type>[a-zA-Z0-9_\-]+)/$', 'web.views.ppd_views.inventory_module', name="ppd-user-inventory"),
    #analyze and edit the url for the below view
    url(r'^user/(?P<profile_id>\d+)/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', user_dashboard, name='ppd-user-dashboard'), 
    #url(r'^seller/orders/(?P<order_id>[0-9]+)/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$','web.views.user_views.seller_order_details', name='ppd-order-details'),
    (r'^user/orders/(?P<order_id>[0-9]+)/','web.views.user_views.user_order_details'),
    #(r'^seller/profile', 'web.views.user_views.show_profile'),
    (r'^seller/address/','web.views.user_views.show_address'),
    #(r'^seller/orders/','web.views.user_views.seller_order_details'),
    (r'^seller/wishlist/','web.views.user_views.show_wishlist'),
    #(r'^acc_sections/(?P<profile_id>\d+)/(?P<acc_section>[a-zA-Z0-9_\-]+)/(?P<current_seller_id>\d+)', 'web.views.ppd_views.acc_sections'),
    (r'^mixed_modes_popup/(?P<option_id>\d+)/$','web.views.ppd_views.mixed_modes_popup'),
    (r'^grouped_modes_content/(?P<code>[a-zA-Z0-9_\-]+)/(?P<current_seller_id>\d+)/$','web.views.ppd_views.grouped_modes_content'),
    (r'^sellers_from_clients', 'web.views.ppd_views.sellers_from_clients'),
    (r'^client_account_display_action', 'web.views.ppd_views.client_account_display_action'),
    (r'^seller_account_display_action', 'web.views.ppd_views.seller_account_display_action'),
    url(r'^orders/seller/(?P<order_id>[0-9]+)/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$','web.views.user_views.seller_order_details',name="ppd-order-details"),
    #(r'^seller/orders/','web.views.user_views.show_seller_orders'),
    (r'^seller/update_shipping_info/(?P<order_id>[0-9]+)/','web.views.user_views.update_shipping_info'),
    (r'^seller/payment_form_fields/', payment_form_fields),
    (r'^seller/payment_option_on_or_off/',payment_option_on_or_off),
    (r'^seller/second_factor_auth', second_factor_auth),
    (r'^seller/order_taking_option', order_taking_option),
    (r'^seller/activate_payment_option', activate_payment_option),
    (r'^seller/edit_deposit_option', edit_deposit_option),
    (r'^manage_seller_payouts', 'web.views.ppd_views.manage_seller_payouts'),
    (r'^auth/signin/','web.views.ppd_views.login'),
    (r'^auth/signup/','web.views.ppd_views.login'),
    (r'^auth/signout','web.views.ppd_views.logout'),
    (r'^seller/signup/','web.views.ppd_views.seller_signup'),
    url(r'^users/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$','web.views.ppd_views.users',name='ppd-users'),
    url(r'^user/create/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$','web.views.ppd_views.create_user',name='ppd-create-user'),
    (r'^admin/', include(admin.site.urls)),
    #For IFS
    url(r'^home/ifs/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/','web.views.ppd_views.ifs_home',name='ifs-home'),
    url(r'^ifs/upload/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<selected_table>[a-zA-Z_\-]+)/(?P<selected_action>[a-zA-Z_\-]+)/','web.views.ppd_views.ifs_actions',name='upload-ifs'), 
    url(r'^ifs/upload/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/','web.views.ppd_views.ifs_select',name='ifs-select'), 
    url(r'^ifs/fulfillment/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/','web.views.ppd_views.fulfillment_check',name='fulfillment'),
   # url(r'^content/upload/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/','web.views.ppd_views.content_upload',name='content-upload'), 
   # url(r'^content/preview/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/','web.views.ppd_views.content_preview',name='content-preview'),
    )

urlpatterns += patterns('',
    #url(r'^accounts/login/$','web.views.ppd_views.login', name=''),
    url(r'^auth/signout','web.views.user_views.logout', name=''),
    url(r'^$','web.views.ppd_views.homepage_redirect'),
)

from django.conf import settings
if settings.DEBUG:
    urlpatterns += patterns('',(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}) )
