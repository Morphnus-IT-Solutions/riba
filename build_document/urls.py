from django.conf.urls.defaults import *

urlpatterns = patterns('build_document.views',
    (r'^$', 'view_documents'),
    (r'^upload-template/(?P<id>[0-9]+)/', 'upload_template'),
    (r'^upload-template/', 'upload_template'),
    (r'^template-details/(?P<id>[0-9]+)/', 'template_details'),
    (r'^template-details/', 'template_details'),
    (r'^create-questionnaire/(?P<id>[0-9]+)/', 'create_questionnaire'),
    (r'^create-questionnaire/', 'create_questionnaire'),
    (r'^question-details/(?P<id>[0-9]+)/', 'get_question_details'),
    (r'^finalize-template/', 'finalize_template'),
)
