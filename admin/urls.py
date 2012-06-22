from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template

handler500 = 'web.views.errors.handle505'
handler404 = 'web.views.errors.handle404'

urlpatterns = patterns('',
    (r'^categories/', include('categories.urls')),
    (r'^question/', include('question.urls')),
    (r'^build-document/', include('build_document.urls')),
    (r'^logout/', 'django.contrib.auth.views.logout_then_login', {'login_url': '/admin/'}),
    (r'^$', 'admin.views.home'),
)
