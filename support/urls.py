from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('', 
    (r'^[0-9.-]+/', include('support.support_urls')),
    (r'', include('support.support_urls')),
)
