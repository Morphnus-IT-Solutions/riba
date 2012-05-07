from django import forms
from question.widgets import SelectWithPop
from question.models import *

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('question', 'type', 'answer_type',)

class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ('option_value', 'dependent_question',)

class FieldForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ('field_label', 'field_type',)
