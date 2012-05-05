from django.conf.urls.defaults import *
from django.http import HttpResponseRedirect
from django.contrib import admin
from django.conf.urls.defaults import url
from django.conf import settings

admin.autodiscover()
handler500 = 'web.views.errors.handle505'
handler404 = 'web.views.errors.handle404'

urlpatterns = patterns('question.views',
    (r'^view/$', 'view_all_questions'),
    #(r'^view/(?P<question_id>[0-9]+)/$', 'view_question'),
    (r'^add/$', 'add_question'),
    (r'^delete/(?P<question_id>[0-9]+)/$', 'delete_question'),
)
