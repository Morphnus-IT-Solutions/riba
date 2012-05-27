from django.conf.urls.defaults import *

urlpatterns = patterns('ccm.views',
    # dashboard. the home screen
    url(r'^$','dashboard'),
)
