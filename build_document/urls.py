from django.conf.urls.defaults import *

urlpatterns = patterns('build_document.views',
    (r'^$', 'view_documents'),
    (r'^upload-template/', 'upload_template'),
    (r'^template-details/', 'template_details'),
    (r'^create-questionnaire/', 'create_questionnaire'),
    (r'^question-details/(?P<id>[0-9]+)/', 'get_question_details'),
    (r'^finalize-template/', 'finalize_template'),
)
