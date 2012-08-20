from django.conf.urls.defaults import *
from django.contrib.auth.views import password_change, password_change_done 
import socket

# XXX this is a lot of time. we should build more aggressive timeouts
# and retries rather than blocking calls
socket.setdefaulttimeout(5*60)

urlpatterns = patterns('web.views',
    # home page. no url params
    url(r'^$', 'home.index'),
)

urlpatterns += patterns('',(r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/media/images/favicon.ico'}))

from django.conf import settings
if settings.DEBUG:
    urlpatterns += patterns('',(r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}) )
    urlpatterns += patterns('',(r'^adminmedia/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.ADMIN_MEDIA_PREFIX}) )
