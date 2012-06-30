# Create your views here.
from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from utils import utils
from document.models import *
from document.forms import *
from django.conf import settings
from django.forms.models import formset_factory, inlineformset_factory
from random import randint
from django.utils import simplejson

def view_documents(request):
    q = request.GET.get('q')
    if q:
        templates = Template.objects.select_related("category").filter(state="submitted").filter(Q(title__icontains=q) | Q(category__name__icontains=q))
    else:
        templates = Template.objects.select_related("category").filter(state="submitted")
    ctxt = {
        'q': q,
        'templates': templates,
        'count': templates.count(),
    }
    return render_to_response('riba-admin/document/view_documents.html', ctxt, context_instance=RequestContext(request))

def get_template_from_session(request, id=None):
    session = utils.get_session_obj(request)
    template_id = session.get('template_id', None)

    if id:
        session['template_id'] = id
        template_id = id

    template = ''
    if template_id:
        try:
            template = Template.objects.get(pk=template_id)
        except:
            pass
    return template



def add_keywords(request, template):
    kt = Keyword.objects.filter(template=template)
    kt.delete()
    total_words, keywords = [], []
    if template.upload_document:
        url = template.upload_document.url.replace('/media/', '/media/riba/')
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
        Keyword.objects.create(keyword=k, template=template)


def upload_template(request, id=None):
    template = get_template_from_session(request, id)
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
            if id:
                return HttpResponseRedirect('/admin/document/template-details/%s/' % id)
            else:
                return HttpResponseRedirect('/admin/document/template-details/')
        else:
            for er in form.errors:
                errors.append(form.errors[er])
    ctxt = {
        'form': form,
        'errors': errors,
        'id': id,
    }
    return render_to_response('riba-admin/document/upload_template.html', ctxt, context_instance=RequestContext(request))


def template_details(request, id=None):
    template = get_template_from_session(request, id)
    if not template:
        return HttpResponseRedirect(request.path.replace('template-details', 'upload-template'))
    form = TemplateForm(instance=template)
    errors = []
    if request.method == "POST":
        form = TemplateForm(request.POST, request.FILES, instance=template)
        if form.is_valid():
            form.save()
            if id:
                return HttpResponseRedirect('/admin/document/create-questionnaire/%s/' % id)
            else:
                return HttpResponseRedirect('/admin/document/create-questionnaire/')

        else:
            for er in form.errors:
                errors.append(form.errors[er])
    ctxt = {
        'form': form,
        'errors': errors,
        'id': id,
    }
    return  render_to_response('riba-admin/document/template_details.html', ctxt, context_instance=RequestContext(request))


def create_questionnaire(request, id=None):
    template = get_template_from_session(request)
    if not template:
        return HttpResponseRedirect(request.path.replace('template-details', 'upload-template'))

    keyword_queryset = Keyword.objects.filter(template=template)

    questionnaire_inline_formset =  inlineformset_factory(Template, Questionnaire, form = QuestionnaireForm, extra=1, can_delete=True)
    questionnaire_formset = questionnaire_inline_formset(instance=template, queryset=Questionnaire.objects.filter(question__level=1, field=None))
    errors = []
    if request.method == "POST":
        questionnaire_formset = questionnaire_inline_formset(request.POST, request.FILES, instance=None)
        if questionnaire_formset.is_valid():
            # Delete old questionnaire
            old_questionnaire = Questionnaire.objects.filter(template = template)
            old_questionnaire.delete()
            for q in questionnaire_formset.forms:
                # validate mandatory fields
                question = q.cleaned_data.get("question")
                sort_order = q.cleaned_data.get("sort_order")

                if not question:
                    errors.append("Please select question")
                if not sort_order:
                    errors.append("Please add sort order for all questions")

                if errors:
                    continue
                else:
                    children = question.get_all_children()
                    fields = question.field_set.all()
                    if fields:
                        for f in fields:
                            keyword = request.POST.get("questionnaire-%s-keyword" % f.id)
                            mandatory = request.POST.get("questionnaire-%s-mandatory" % f.id, False)
                            add_question(template, question, sort_order, field=f, keyword=keyword, mandatory=mandatory)
                    elif children:
                        keyword = request.POST.get("questionnaire-%s-keyword" % question.id)
                        mandatory = request.POST.get("questionnaire-%s-mandatory" % question.id, False)
                        add_question(template, question, sort_order, keyword=keyword, mandatory=mandatory)
                        for ch in children:
                            if ch.question:
                                fields = ch.question.field_set.all()
                                if fields:
                                    for f in fields:
                                        keyword = request.POST.get("questionnaire-%s-keyword" % f.id)
                                        mandatory = request.POST.get("questionnaire-%s-mandatory" % f.id, False)
                                        add_question(template, ch.question, sort_order, field=f, keyword=keyword, mandatory=mandatory)
                                else:
                                    keyword = request.POST.get("questionnaire-%s-keyword" % ch.question.id)
                                    mandatory = request.POST.get("questionnaire-%s-mandatory" % ch.question.id, False)
                                    add_question(template, ch.question, sort_order, keyword=keyword, mandatory=mandatory)
                    else:
                        keyword = request.POST.get("questionnaire-%s-keyword" % question.id)
                        mandatory = request.POST.get("questionnaire-%s-mandatory" % question.id, False)
                        add_question(template, question, sort_order, keyword=keyword, mandatory=mandatory)

                    return HttpResponseRedirect('/admin/document/finalize-template/')
        else:
            errors.append(questionnaire_formset.errors)
    ctxt = {
        'errors': errors,
        'questionnaire_formset': questionnaire_formset,
        'random_count': randint(1,999), # included for multiple popups of dependent question
        'id': id,
    }
    return render_to_response('riba-admin/document/questionnaire.html', ctxt, context_instance=RequestContext(request))


def add_question(template, question, sort_order, field=None, keyword=None, mandatory=None):
    if mandatory and mandatory == "on":
        mandatory = True
    qn = Questionnaire()
    qn.template = template
    qn.question = question
    qn.field = field
    qn.sort_order = sort_order
    qn.keyword_id = keyword
    qn.mandatory = mandatory
    qn.save()


def get_question_details(request, id):
    try:
        question = Question.objects.get(pk=id)
    except Question.DoesNotExist:
        raise Http404

    template = get_template_from_session(request)
    if not template:
        raise Http404

    keyword_queryset = Keyword.objects.filter(template=template)
    count = request.GET.get('count')
    if count:
        count = int(count)

    child_details = {}
    fields = ''

    children = question.get_all_children()
    for ch in children:
        if ch.question and ch.question not in child_details:
            fields = ch.question.field_set.all()
            child_details[ch.question] = fields

    fields = question.field_set.all()


    keywords = Keyword.objects.filter(template=template)

    ctxt = {
            "count": count,
            "question": question,
            "fields": fields,
            "child_details": child_details,
            "keywords": keyword_queryset,
           }
    return render_to_response('riba-admin/document/question_details.html', ctxt, context_instance=RequestContext(request))


def finalize_template(request):
    template = get_template_from_session(request)
    if not template:
        raise Http404

    form = FinalTemplateForm(instance=template)
    inline_formset = inlineformset_factory(Template, Questionnaire, form = FinalQuestionnaireForm, extra=0)

    formset = inline_formset(instance = template)

    if request.method == "POST":
        form = FinalTemplateForm(request.POST, request.FILES, instance = template)
        formset = inline_formset(request.POST, request.FILES, instance = template)
        if form.is_valid():
            qn = form.save()
            for f in formset:
                if f.is_valid() and f.cleaned_data.get('question'):
                    f.save()
        template.state = 'submitted'
        template.save()
        session = utils.get_session_obj(request)
        template_id = session.get('template_id', None)
        if template_id:
            session['template_id'] = None
        return HttpResponseRedirect('/document/')
    ctxt = {
        'template': template,
        'form': form,
        'formset': formset,
    }
    return render_to_response('riba-admin/document/finalize_template.html', ctxt, context_instance=RequestContext(request))
