from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('rms.views',
    url(r'^campaign/$', 'campaign_list', name='rms_campaign_list'),
    url(r'^campaign/(?P<campaign_id>\d+)/$', 'campaign', name='rms_campaign_detail'),
    url(r'^campaign/add/$', 'campaign_add', name='rms_campaign_add_1'),
    url(r'^campaign/add/(?P<demo_id>\d+)/(?P<campaign_id>\d+)/$', 'campaign_add', name='rms_campaign_add_2'),
    url(r'^campaign/(?P<campaign_id>\d+)/edit/$', 'campaign_edit', name='rms_campaign_edit'),
    url(r'^campaign/(?P<campaign_id>\d+)/agents/$', 'campaign_agents', name='rms_campaign_agents'),
    url(r'^campaign/(?P<campaign_id>\d+)/responses/upload/$', 'upload_responses', name='campaign_response_upload'),
    url(r'^campaign/(?P<campaign_id>\d+)/responses/untagged/$', 'get_untagged_responses', name='untagged_response_list'),
    url(r'^campaign/(?P<campaign_id>\d+)/responses/$', 'campaign_response_list', name='campaign_response_list'),
    url(r'^response/(?P<response_id>\d+)/$', 'get_interactions', name='interaction_list'),
    url(r'^response/(?P<response_id>\d+)/call$', 'call_response', name='call_response'),
    url(r'^response/(?P<response_id>\d+)/callclose$', 'add_interaction', name='interaction_list'),
    url(r'^agent/JSlist/$', 'get_response_list_forJS', name='agent_response_list_forJS'),
    url(r'^agent/$', 'get_agent_responses', name='agent_response_list'),
    url(r'^user/add/$', 'user_add', name='user_add'),
    url(r'^user/(?P<user_id>\d+)/edit/$', 'user_edit', name='user_edit'),
    url(r'^user/(?P<user_id>\d+)/$', 'users', name='user'),
    url(r'^user/group/(?P<group_id>\d+)/$', 'user_group', name='user_group'),
    url(r'^user/$', 'users', name='user_list'),
    url(r'^backlog/$', 'backlog', name='agent_backlog'),
    url(r'^$', 'homepage_redirect', name='homepage')
)

urlpatterns += patterns('',
    (r'^accounts/login/$','web.views.home.login',{'template_name':'systems/login.html'}),
    (r'^auth/signout','web.views.user_views.logout'),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT})
)

