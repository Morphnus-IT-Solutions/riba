from django import forms
from question.widgets import SelectWithPop
from question.models import *

class QuestionForm(forms.ModelForm):
    class Meta:
        model = Question
        fields = ('question', 'category', 'description', 'answer_type', 'is_recurring', 'recurring_times', 'recurring_label', 'rows', 'columns', )

    def __init__(self, *args, **kwargs):
        super(QuestionForm, self).__init__(*args, **kwargs)
        self.fields['question'].error_messages['required'] = 'Please enter question'
        self.fields['category'].error_messages['required'] = 'Please select category'


class OptionForm(forms.ModelForm):
    class Meta:
        model = Option
        fields = ('option_value', 'dependent_question',)


    def __init__(self, *args, **kwargs):
        super(OptionForm, self).__init__(*args, **kwargs)
        self.fields['option_value'].error_messages['required'] = 'Please enter option value'


    def clean(self):
        if self.cleaned_data.get('dependent_question') and not self.cleaned_data.get('option_value'):
            raise forms.ValidationError(u"Please enter Option Value in Options")
        return self.cleaned_data


class FieldForm(forms.ModelForm):
    class Meta:
        model = Field
        fields = ('field_label', 'field_type', 'field_option', 'sort_order')

    def __init__(self, *args, **kwargs):
        super(FieldForm, self).__init__(*args, **kwargs)
        self.fields['field_option'].widget.attrs['cols'] = 15
        self.fields['field_option'].widget.attrs['rows'] = 5
        self.fields['field_type'].choices.insert(0,('','----'))
        self.fields['field_label'].required = False
        self.fields['field_type'].required = False
        self.fields['sort_order'].required = False

    def clean(self):
        if (self.cleaned_data.get('field_type') or self.cleaned_data.get('field_options')) and not self.cleaned_data.get('field_label'):
            raise forms.ValidationError(u"Please enter Field Label in Fields")
        if self.cleaned_data.get('field_label') and not self.cleaned_data.get('field_type'):
            raise forms.ValidationError(u"Please select Field Type in Fields")
        return self.cleaned_data
