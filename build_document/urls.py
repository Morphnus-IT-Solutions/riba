from django.conf.urls.defaults import *

urlpatterns = patterns('build_document.views',
    (r'^upload-template/', 'upload_template'),
    (r'^template-details/', 'template_details'),
    (r'^create-questionnaire/', 'create_questionnaire'),
)


