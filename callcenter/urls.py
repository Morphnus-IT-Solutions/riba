from django.conf.urls.defaults import *

handler500 = 'web.views.errors.handle505'
handler404 = 'web.views.errors.handle404'

urlpatterns = patterns('', 
    (r'^[0-9.-]+/', include('callcenter.cc_urls')),
    (r'', include('callcenter.cc_urls')),
)
