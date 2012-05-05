# Create your views here.

from django.http import HttpResponse, HttpResponseRedirect, HttpResponsePermanentRedirect, Http404
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.forms.models import formset_factory, inlineformset_factory
from question.models import *
from question.forms import *

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

def add_question(request):
    form = QuestionForm()
    question_formset = formset_factory(QuestionForm, extra=1)
    field_inline_formset = inlineformset_factory(Question, Field, form = FieldForm, extra=1)
    field_formset = field_inline_formset(instance = None)
    if request.method == "POST":
        if 'addfield' in request.POST:
            cp = request.POST.copy()
            cp['field_set-TOTAL_FORMS'] = int(cp['field_set-TOTAL_FORMS'])+1
            field_formset = field_inline_formset(cp,  instance=None)
            cp['question-TOTAL_FORMS'] = int(cp['question-TOTAL_FORMS'])
            question_formset = question_formset(cp,  instance=None)
        if 'addoption' in request.POST:
            cp = request.POST.copy()
            cp['question-TOTAL_FORMS'] = int(cp['question-TOTAL_FORMS'])+1
            question_formset = question_formset(cp,  instance=None)
            cp['field_set-TOTAL_FORMS'] = int(cp['field_set-TOTAL_FORMS'])
            field_formset = field_inline_formset(cp,  instance=None)
    ctxt = {
        'form': form,
        'question_formset': question_formset,
        'field_formset': field_formset,
    }
    return render_to_response('question/add_question.html', ctxt, context_instance=RequestContext(request))   
