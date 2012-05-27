from django.conf.urls.defaults import *
from django.views.generic.simple import direct_to_template
# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

handler500 = 'web.views.errors.handle505'
handler404 = 'web.views.errors.handle404'

urlpatterns = patterns('',
    # Example:
    # (r'^tinla/', include('tinla.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    #(r'^rms/', include('rms.urls')),
    url(r'^social/fbchannel', direct_to_template, {'template':'social/fbchannel.html'}),
    (r'^accounts/logout/$', 'django.contrib.auth.views.logout_then_login'),

    (r'^favicon\.ico$', 'django.views.generic.simple.redirect_to', {'url': '/media/images/favicon.ico'}),
    (r'^print-request$', 'web.views.webmaster.print_request'),
    (r'^LiveSearchSiteAuth.xml$','web.views.webmaster.verify_msn'),
    (r'^sitemap$','web.views.webmaster.sitemap'),
    (r'^admin/', include(admin.site.urls)),
    (r'^accounts/login/$','web.views.home.login'),
    (r'^tinymce/', include('tinymce.urls')),
    (r'^accounts/', include('accounts.urls')),
    (r'^promotions/', include('promotions.urls')),
    (r'^catalog/', include('catalog.urls')),
    (r'^categories/', include('categories.urls')),
    (r'^question/', include('question.urls')),
    (r'^facebookconnect/', include('facebookconnect.urls')),
    (r'^login/$', 'django.contrib.auth.views.login', {'template_name': 'popups/signin.html'}),

    ('', include('web.urls')),
)
