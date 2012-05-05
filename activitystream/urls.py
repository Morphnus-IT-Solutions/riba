from django.conf.urls.defaults import *

urlpatterns = patterns('web.views.as_views',
    (r'^write-stream/(?P<atype>\w+)/(?P<src_id>\w+)/$', 'write_stream'),
    (r'^read-stream/$', 'read_stream'),
    (r'^recently-stolen/$', 'read_recently_stolen'),
)
