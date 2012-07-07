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
        'template': template,
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
        'template': template,
    }
    return  render_to_response('riba-admin/document/template_details.html', ctxt, context_instance=RequestContext(request))


def create_questionnaire(request, id=None):
    template = get_template_from_session(request)
    if not template:
        return HttpResponseRedirect(request.path.replace('template-details', 'upload-template'))

    if request.method == "GET":
        keyword_queryset = Keyword.objects.filter(template=template)
        question_queryset = Question.objects.filter(level=1)

        errors = []

        qdict = {}
        questionnaire = Questionnaire.objects.select_related('question').filter(template=template).order_by('sort_order')

        '''
         dict format
         ------------
         qdict = {sort_order: {'question': level_1_question,
                               'fields': [list of all questionnaires having fields belonging to parent question]
                               'children': {question: [list of all questionnaires having fields belonging to child question]},
                              }
                 }
        '''
        for q in questionnaire:
            if q.sort_order not in qdict:
                qdict[q.sort_order] = {}
            print q.question, q.question.level
            if q.question.level == 1:
                if not qdict[q.sort_order].get('question'):
                    qdict[q.sort_order]['question'] = {}
                    qdict[q.sort_order]['children'] = {}
                    qdict[q.sort_order]['fields'] = []
                qdict[q.sort_order]['question'] = q
                

                if q.field:
                    if not qdict[q.sort_order].get('fields'):
                        qdict[q.sort_order]['fields'] = [q]
                    else:
                        qdict[q.sort_order]['fields'].append(q)

            else:
                if not qdict[q.sort_order].get('children'):
                    qdict[q.sort_order]['children'] = {}

                if q.field:
                    if not qdict[q.sort_order]['children'].get(q.question):
                        qdict[q.sort_order]['children'][q.question] = [q]
                    else:
                        qdict[q.sort_order]['children'][q.question].append(q)
                else:
                    if not qdict[q.sort_order]['children'].get(q.question):
                        qdict[q.sort_order]['children'][q.question] = []
        print qdict
        ctxt = {
                'errors': errors,
                #'questionnaire_formset': questionnaire_formset,
                'random_count': randint(1,999), # included for multiple popups of dependent question
                'id': id,
                'template': template,
                'qdict': qdict,
                'questions': question_queryset,
                'keywords': keyword_queryset,
                'total_forms': len(qdict)
            }
        return render_to_response('riba-admin/document/questionnaire.html', ctxt, context_instance=RequestContext(request))

    elif request.method == "POST":
        valid_questions, errors = validate_questions(request)
        if not errors:
            # Delete old questionnaire
            old_questionnaire = Questionnaire.objects.filter(template = template)
            old_questionnaire.delete()
            
        for question in valid_questions:
            children = question.get_all_children()
            sort_order = question.sort_order
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
    

def validate_questions(request):
    valid_questions, errors = [], []
    total_forms = request.POST.get('questionnaire_set-TOTAL_FORMS')
    if total_forms:
        for q in range(int(total_forms)):
            question_id = request.POST.get('questionnaire_set-%s-question' % str(q))
            sort_order = request.POST.get('questionnaire_set-%s-sort_order' % str(q))
            delete = request.POST.get('questionnaire_set-%s-DELETE' % str(q))

            if not delete:
                if not question_id:
                    errors.append("Please select question in row %s" % str(q+1))
                if not sort_order:
                    errors.append("Please add sort order in row %s" % str(q+1))

                # We are adding questions to database even if there are errors
                # coz we want to display questions to edit after displaying error
                try:
                    question = Question.objects.get(pk=int(question_id))
                    question.sort_order = sort_order
                    question.save()
                    valid_questions.append(question)
                except Exception, e:
                    print e
                    errors.append("Please select appropriate question in row %s" % str(q+1))
    else:
        errors.append("Questions not updated properly. Please refresh and try again.")

    return valid_questions, errors


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
                else:
                    print formset.errors[f]
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
