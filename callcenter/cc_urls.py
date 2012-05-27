from django.conf.urls.defaults import *

from web.views import *
from rms import signal_listeners

urlpatterns = patterns('',
    (r'^home$', 'web.views.home.index'),
    (r'^accounts/login/$','web.views.home.login'),
    (r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'popups/signin.html'}),    
    (r'^share/(?P<id>\d+)', 'web.views.product_views.share_product'),
    #(r'^collections','web.views.product_views.get_parent_products'),

    (r'^user/get_user_context','web.views.user_views.get_or_create_user_context'),
    (r'^user/update_user_profile','web.views.user_views.update_user_profile'),
    #(r'^user/callclose','web.views.user_views.close_call'),
    (r'^user/callclose','rms.views.add_interaction'),
    (r'^user/change_user','web.views.user_views.change_user'),
    (r'^user/cc_signup','web.views.user_views.cc_signup'),
    (r'^user/cc_verify','web.views.user_views.cc_verify'),
    (r'^user/signout','web.views.user_views.signout'),
    (r'^order/agentperformance','web.views.user_views.show_agent_order_history'),

)

from django.conf import settings
if settings.DEBUG:
    urlpatterns += patterns('',(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}) )
    urlpatterns += patterns('',(r'^adminmedia/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.ADMIN_MEDIA_PREFIX}) )

if settings.CLIENT == 'Holii':
    urlpatterns += patterns('', (r'^collections','web.views.product_views.get_parent_products'))

urlpatterns += patterns('',(r'^/', 'callcenter.views.dump_call_info'))
urlpatterns += patterns('',(r'', include('urls')))
