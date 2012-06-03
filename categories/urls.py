from django.conf.urls.defaults import *
from django.http import HttpResponseRedirect
from django.contrib import admin
from django.conf.urls.defaults import url
from django.conf import settings

admin.autodiscover()
handler500 = 'web.views.errors.handle505'
handler404 = 'web.views.errors.handle404'

urlpatterns = patterns('categories.views',
    (r'^(?P<id>[0-9]+)/$', 'view_category'),
    (r'^view/$', 'view_all_categories'),
    (r'^add/', 'add_category'),
    (r'^edit/(?P<id>[0-9]+)/$', 'edit_category'),
    (r'^delete/(?P<id>[0-9]+)/$', 'delete_category'),
)
