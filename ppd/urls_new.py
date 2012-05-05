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
    # handle find requests
    (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/assets/images/favicon.ico'}),
    (r'^robots.txt$','web.views.ppd_views.robots'),
    (r'^sitemap$','web.views.ppd_views.sitemap'),
    (r'^(?P<page>[a-zA-Z0-9\-]+).html$', 'web.views.ppd_views.serve_static'),

    # PPD seller pages
    (r'^accounts/login', 'web.views.home.login',{'template_name':'systems/login.html'}),
    #(r'^home/',user_dashboard),
    url(r'^home/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', user_login_page, name='ppd-user-login-page'), 
    url(r'^products/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', user_products, name='ppd-user-products'), 
    #(r'^products/(?P<current_seller_id>\d+)', user_products),
    #(r'^orders/$', user_orders),
    url(r'^orders/(?P<order_state>[a-zA-Z0-9_\-]+)/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', user_orders, name="ppd-user-orders"),
    #(r'^orders/(?P<acc_section_type>[a-zA-Z0-9_\-]+)/(?P<current_seller_id>\d+)', user_orders),
    #(r'^profile/$', 'web.views.ppd_views.user_profile'),
    url(r'^profile/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', 'web.views.ppd_views.user_profile', name='ppd-user-profile'),
    url(r'^notification/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', 'web.views.ppd_views.user_notification', name='ppd-user-notifications'),
    url(r'^payment/settings/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', 'web.views.ppd_views.payment_settings', name='ppd-user-payment-settings'),
    url(r'^payment/options/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', payment_options, name='ppd-user-payment-options'),
    url(r'^payouts/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$',user_payouts, name='ppd-user-payouts'),
    url(r'^reports/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<report_type>[a-zA-Z0-9_\-]+)/$', 'web.views.ppd_views.user_reports', name='ppd-user-reports'),
    (r'^reviews/approve_or_disapprove_review',approve_or_disapprove_review),
    url(r'^reviews/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$',user_reviews, name='ppd-user-reviews'),
    (r'^prices/price_version_details',price_version_details),
    url(r'^prices/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<update_type>[a-zA-Z0-9_\-]+)/$',client_pricing, name='ppd-user-pricing'),
    #(r'^prices/price_version_details',price_version_details),
    url(r'^inventory/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/(?P<update_type>[a-zA-Z0-9_\-]+)/$', 'web.views.ppd_views.inventory_module', name="ppd-user-inventory"),
    #analyze and edit the url for the below view
    url(r'^user/(?P<profile_id>\d+)/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', user_dashboard, name='ppd-user-dashboard'), 
    url(r'^subscribers/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$', subscribers, name='ppd-user-subscribers'), 
    url(r'^seller/orders/(?P<order_id>[0-9]+)/(?P<client_name>[a-zA-Z0-9_\-]+)/(?P<seller_name>[a-zA-Z0-9_\-]+)/$','web.views.user_views.seller_order_details', name='ppd-order-details'),
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
    (r'^manage_seller_payouts', 'web.views.ppd_views.manage_seller_payouts'),
    (r'^auth/signin/','web.views.ppd_views.login'),
    (r'^auth/signup/','web.views.ppd_views.login'),
    (r'^auth/signout','web.views.ppd_views.logout'),
    (r'^seller/signup/','web.views.ppd_views.seller_signup'),
    (r'^admin/', include(admin.site.urls)),
    #For IFS
    (r'^ifs/upload/','web.views.ppd_views.ifs_upload'), 
    (r'^ifs/fulfillment/','web.views.ppd_views.fulfillment_check'),
    (r'^seller/update_shipping_info/(?P<order_id>[a-zA-Z0-9_\-]+)/(?P<client_name>[a-zA-Z0-9_\-]+)/$','web.views.user_views.update_shipping_info'),
    (r'^seller/update_shipping_info/(?P<order_id>[a-zA-Z0-9_\-]+)/$','web.views.user_views.update_shipping_info'),

    )

urlpatterns += patterns('',
    #url(r'^accounts/login/$','web.views.ppd_views.login', name=''),
    url(r'^auth/signout','web.views.user_views.logout', name=''),
    url(r'^$','web.views.ppd_views.homepage_redirect'),
)

from django.conf import settings
if settings.DEBUG:
    urlpatterns += patterns('',(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}) )
