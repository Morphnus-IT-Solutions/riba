from django.conf.urls.defaults import *

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.site.disable_action('delete_selected')

admin.autodiscover()

handler500 = 'analytics_orders.views.handle505'
handler404 = 'analytics_orders.views.handle404'

urlpatterns = patterns('',
    # Example:
    # (r'^oms/', include('oms.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$', 'django.contrib.auth.views.login',{'template_name':'systems/login.html'}),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login',{'login_url':'/accounts/login'}),
    (r'^report_dashboard/reports_access_count/','analytics_report_access.views.reports_access_count'),
    (r'^report_dashboard/report_access_details/','analytics_report_access.views.report_access_details'),
    (r'^report_dashboard/user_permissions_report/','analytics_report_access.views.user_permissions_report'),
    (r'^marketing/subscription_report/','analytics_subscriptions.views.subscription_report'),
    (r'^reports/subscription_report_source/','analytics_subscriptions.views.subscription_report_source'),
    (r'^category/deal_reports/(?P<catalog_ids>[0-9_]+)','analytics_deals.views.deal_reports'),
    (r'^category/deal_reports/','analytics_deals.views.deal_reports'),
    (r'^category/category_report/','analytics_deals.views.category_report'),
    (r'^category/brand_report/','analytics_deals.views.brand_report'),
    (r'^category/category_details/','analytics_deals.views.category_details'),
    (r'^reports/deal_extract/','analytics_deals.views.deal_extract'),
    (r'^marketing/payback_report/','analytics_deals.views.payback_report'),
    (r'^marketing/payback_details/','analytics_deals.views.payback_details'),
    (r'^marketing/payback_kpi_report/','analytics_deals.views.payback_kpi_report'),
    (r'^marketing/promotions_report/','analytics_deals.views.promotions_report'),
    (r'^marketing/shopping_cart_analysis/','analytics_deals.views.shopping_cart_analysis'),
    (r'^cs/payment_attempt_report/','analytics_payments.views.payment_attempt_report'),
    (r'^marketing/deal_summary_report/','analytics_deals.views.deal_summary_report'),
    (r'^http_error_page/','analytics_utils.utils.http_error_page'),

#SCM Dashboard links
    (r'^scm/scm_dashboard/','analytics_scm.views.scm_dashboard'),

#    (r'^api/', include('analytics_api.urls')),
    (r'^scm/', include('analytics_scm.urls')),
    (r'^qa_reports/', include('analytics_complaints.urls')),
    (r'^data/', include('analytics_pentaho.urls')),
    (r'^cs/', include('analytics_cs.urls')),
    (r'', include('analytics_orders.urls')),
)

from django.conf import settings
urlpatterns += patterns('',(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}) )

