from django import template
from question.models import *
from question.forms import *
from question.views import add_question
from django.forms.models import formset_factory, inlineformset_factory

register = template.Library()

def add_nested_question(request):
    form = QuestionForm()
    field_inline_formset = inlineformset_factory(Question, Field, form = FieldForm, extra=1)
    field_formset = field_inline_formset(instance=None)
    option_inline_formset = inlineformset_factory(Question, Option, form = OptionForm, extra=1)
    option_formset = option_inline_formset(instance=None)
    return dict(form = form, \
                option_formset = option_formset,\
                field_formset = field_formset, request=request)
register.inclusion_tag('question/nested_question.html')(add_nested_question)

@register.filter
def split_newline(value):
    return value.split('\n')

@register.filter
def get_range(value):
    return range(1, value)

@register.filter
def row_class(count):
    if count % 2 == 0:
        return 1
    else:
        return 2

def document_tabs(request, tab):
    tabs = [dict(name="upload-template", text="Upload Template"), dict(name="template-details", text="Template Details"), 
            dict(name="create-questionnaire", text="Create Questionnaire"), dict(name="finalize-template", text="Finalize Template")]
    tab_click = True
    for t in tabs:
        if t["name"] == tab:
            tab_click = False
        t["tab_click"] = tab_click
    return dict(request=request, tab=tab, tabs=tabs)
register.inclusion_tag("riba-admin/document/tabs.html")(document_tabs)
