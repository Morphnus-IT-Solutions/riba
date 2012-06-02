# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from utils import utils
from build_document.models import Template
from build_document.forms import *


def create_new_template(request):
    #template = Template.objects.create()
    return ''

def get_template_from_session(request):
    session = utils.get_session_obj(request)
    template_id = session.get('template_id')
    template = ''
    if template_id:
        template = Template.objects.get(pk=template_id)
    return template


def upload_template(request):
    template = get_template_from_session(request)
    form = UploadTemplateForm(template=template)
    if request.method == "POST":
        category_id = request.POST.get('category')
        upload_document = request.POST.get('upload_document')
        upload_text = request.POST.get('upload_text')
        if template:
            template.category_id = category_id
            template.upload_document = upload_document
            template.upload_text = upload_text
            template.save()
        else:
            template = Template.objects.create(category_id = category_id, upload_document = upload_document, upload_text = upload_text)
            session['template_id'] = template.id
        return HttpResponseRedirect('/build-document/template-details/')
    ctxt = {
        'form': form,
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
