from django import forms
from categories.models import Category
from build_document.models import *
from tinymce.widgets import TinyMCE

class UploadTemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ('category', 'upload_document', 'upload_text',)

    def __init__(self, *args, **kwargs):
        super(UploadTemplateForm, self).__init__(*args, **kwargs)
        self.fields['category'].error_messages['required'] = 'Please enter category'
        self.fields['upload_text'].widget = TinyMCE(attrs={'cols': 50, 'rows': 15})

    def clean(self):
        if not ('upload_document' in self.cleaned_data and 'upload_text' in self.cleaned_data) or \
                (self.cleaned_data['upload_document'] == "" and self.cleaned_data['upload_text'] == ""):
            raise forms.ValidationError(u"Please upload or paste the document")
        return self.cleaned_data


class TemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ('title', 'offer_price', 'time_to_build', 'information', 'about')

    def __init__(self, *args, **kwargs):
        super(TemplateForm, self).__init__(*args, **kwargs)
        self.fields['information'].widget = TinyMCE(attrs={'cols': 40, 'rows': 10})
        self.fields['about'].widget = TinyMCE(attrs={'cols': 40, 'rows': 10})
        self.fields['title'].error_messages['required'] = 'Please enter title'
        self.fields['offer_price'].error_messages['required'] = 'Please enter price'


class QuestionnaireForm(forms.ModelForm):
    class Meta:
        model = Questionnaire
        fields = ('question', 'sort_order',)

    def __init__(self, *args, **kwargs):
        template = kwargs.pop('template', None)
        super(QuestionnaireForm, self).__init__(*args, **kwargs)
        self.fields["question"].widget.attrs['class'] = 'question'
        self.fields["question"].queryset = Question.objects.filter(level=1).order_by("question")
        self.fields['question'].error_messages['required'] = 'Please enter question'
        self.fields['sort_order'].error_messages['required'] = 'Please enter sort order for all questions'


class FinalTemplateForm(forms.ModelForm):
    class Meta:
        model = Template
        fields = ('title', 'category', 'upload_document', 'upload_text', 'offer_price', 'time_to_build', 'information', 'about')




class FinalQuestionnaireForm(forms.ModelForm):
    class Meta:
        model = Questionnaire
        fields = ('question', 'field', 'keyword', 'sort_order', 'mandatory',)
