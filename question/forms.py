from django import forms
from question.widgets import SelectWithPop
from question.models import *

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('question', 'category', 'description', 'type', 'answer_type', 'rows', 'columns', )

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['question'].error_messages['required'] = 'Please enter question'
        self.fields['category'].error_messages['required'] = 'Please select category'


class OptionForm(forms.ModelForm):
    #dependent_question = forms.ModelChoiceField(Department.objects, required=False, widget=SelectWithPop)
    class Meta:
        model = Option
        fields = ('option_value', 'dependent_question',)


class FieldForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ('field_label', 'field_type', 'field_option', 'sort_order')

    def __init__(self, *args, **kwargs):
        super(FieldForm, self).__init__(*args, **kwargs)
        self.fields['field_option'].widget.attrs['cols'] = 15
        self.fields['field_option'].widget.attrs['rows'] = 5
