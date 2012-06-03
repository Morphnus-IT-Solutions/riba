# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from utils import utils
from build_document.models import *
from build_document.forms import *
from django.conf import settings


def get_template_from_session(request):
    session = utils.get_session_obj(request)
    template_id = session.get('template_id', None)
    template = ''
    if template_id:
        template = Template.objects.get(pk=template_id)
    return template

def add_keywords(request, template):
    qn = Questionnaire.objects.filter(template=template)
    qn.delete()
    total_words, keywords = [], []
    if template.upload_document:
        url = template.upload_document.url.replace('/media/', '/media/tinla/')
        f = open(settings.DOCUMENT_ROOT+url, 'r')
        fr = f.read()
        total_words = fr.split('$$$')
        f.close()
    elif template.upload_text:
        total_words = template.upload_text.split('$$$')
    for k in range(len(total_words)):
        if k % 2 == 1:
            keywords.append(total_words[k])
    for k in keywords:
        q = Questionnaire.objects.create(keyword=k, template=template)


def upload_template(request):
    template = get_template_from_session(request)
    if template:
        form = UploadTemplateForm(instance=template)
    else:
        form = UploadTemplateForm(instance=None) 
    errors = []
    if request.method == "POST":
        if template:
            form = UploadTemplateForm(request.POST, request.FILES, instance=template)
        else:
            form = UploadTemplateForm(request.POST, request.FILES)
        session = utils.get_session_obj(request)
        if form.is_valid():
            form.save()
            session['template_id'] = form.instance.id
            # add keywords
            add_keywords(request, form.instance)
            return HttpResponseRedirect('/build-document/template-details/')
        else:
            for er in form.errors:
                errors.append(form.errors[er])
    ctxt = {
        'form': form,
        'errors': errors
    }
    return render_to_response('build_document/upload_template.html', ctxt, context_instance=RequestContext(request))


def template_details(request):
    template = get_template_from_session(request)
    if not template:
        return HttpResponseRedirect(request.path.replace('template-details', 'upload-template'))
    form = TemplateForm(instance=template)
    errors = []
    if request.method == "POST":
        form = TemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/build_document/create-questionnaire/')
        else:
            for er in form.errors:
                errors.append(form.errors[er])
    ctxt = {
        'form': form,
        'errors': errors,
    }
    return  render_to_response('build_document/template_details.html', ctxt, context_instance=RequestContext(request))
