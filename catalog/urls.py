from django.conf.urls.defaults import *

urlpatterns = patterns('',
    (r'^dashboard$','catalog.views.show_dashboard'),
    (r'^add$','catalog.views.add_product'),
    (r'^addproduct$','catalog.views.add'),
    (r'^featureinfo$','catalog.views.get_feature_info'),
)
