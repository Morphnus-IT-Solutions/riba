# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.forms.models import formset_factory, inlineformset_factory
from question.models import *
from question.forms import *
from random import randint
from django.utils.html import escape

def view_all_questions(request):
    ques = Question.objects.filter(type='normal').order_by('-id')
    q = request.GET.get('q')
    if q:
        ques =  ques.filter(question__icontains=q)
    ques_dict = {    
        'ques':ques,
        'q':q,
        }    
    return render_to_response('question/view_questions.html', ques_dict, context_instance=RequestContext(request))


def delete_question(request, question_id):
    try:
        ques_obj = Question.objects.get(id = question_id)
    except Question.DoesNotExist:
        raise Http404        
    if request.method == "POST":
        ques_obj.delete()
    
    del_question_dict = {    
        'question':question,
        'question_id': question_id
        }    
    return render_to_response('question/question_delete_confirm.html', del_question_dict, context_instance=RequestContext(request))

def add_question(request, id=None):
    form = QuestionForm()
    field_inline_formset = inlineformset_factory(Question, Field, form = FieldForm, extra=1, can_delete=True)
    field_formset = field_inline_formset(instance=None)
    option_inline_formset = inlineformset_factory(Question, Option, form = OptionForm, extra=1, fk_name="question", can_delete=True)
    option_formset = option_inline_formset(instance=None)
    is_popup = 0
    if request.method == "POST":
        if 'save' in request.POST:
            is_popup = request.POST.get('is_popup', 0)
            form = QuestionForm(request.POST, request.FILES)
            field_formset = field_inline_formset(request.POST, request.FILES, instance=None)
            option_formset = option_inline_formset(request.POST, request.FILES, instance=None)
            if form.is_valid():
                q = form.save()
            for fld in field_formset:
                if fld.is_valid() and fld.cleaned_data.get('field_label'):
                    f = Field()
                    f.question = q
                    f.field_label = fld.cleaned_data.get('field_label')
                    f.field_type = fld.cleaned_data.get('field_type')
                    f.save()
            for op in option_formset:
                if op.is_valid() and op.cleaned_data.get('option_value'):
                    o = Option()
                    o.question = q
                    o.option_value = op.cleaned_data.get('option_value')
                    o.dependent_question = op.cleaned_data.get('dependent_question')
                    o.save()
                    try:
                        qt = QuestionTree.objects.get(question=o.dependent_question, parent_question=q, parent_value=o.option_value)
                    except QuestionTree.DoesNotExist:
                        qt = QuestionTree(question=o.dependent_question, parent_question=q, parent_value=o.option_value)
                        qt.save()
            if is_popup == '1':
                return HttpResponse('<script type="text/javascript">opener.dismissAddAnotherPopup(window, "%s", "%s");</script>' % (escape(q._get_pk_val()), escape(q)))
            else:
                return HttpResponseRedirect('/question/%s' %q.id)
    else:
        is_popup = request.GET.get('_popup', 0)
    ctxt = {
        'form': form,
        'option_formset': option_formset,
        'field_formset': field_formset,
        'random_count': randint(1,999), # included for multiple popups of dependent question 
        'is_popup': is_popup,
    }
    return render_to_response('question/add_question.html', ctxt, context_instance=RequestContext(request))


def view_question(request, id):
    q = Question.objects.get(pk=id)
    q_fields = q.field_set.all()
    q_options = q.option_set.all()
    ctxt = {
        'q': q,
        'fields': q_fields,
        'options': q_options,
    }
    return render_to_response('question/question.html', ctxt, context_instance=RequestContext(request))


def preview_question(request, id):
    if request.method == "POST":
        qid = request.POST.get('current_question_id', id)
        qval = request.POST.get('current_question_val')
        q_tree = QuestionTree.objects.select_related('question').get(parent_question__id=qid, parent_value=qval)
        q = q_tree.question or q_tree.parent_question 
    else:
        q = Question.objects.get(pk=id)
    q_fields = q.field_set.all()
    q_options = q.option_set.all()
    q_hierarchy = q.get_question_hierarchy()
    ctxt = {
        'q': q,
        'fields': q_fields,
        'options': q_options,
        'hierarchy': q_hierarchy,
    }
    return render_to_response('question/preview_question.html', ctxt, context_instance=RequestContext(request))    
