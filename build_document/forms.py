from django import forms
from categories.models import Category
from build_document.models import Template
from tinymce.widgets import TinyMCE

class UploadTemplateForm(forms.Form):
    category = forms.ModelChoiceField(queryset=Category.objects.all(), error_messages={'required':"Please select category"} , required=True)
    upload_document = forms.FileField(required=False, label="Upload Document")
    upload_text = forms.CharField(widget=TinyMCE(attrs={'cols': 80, 'rows': 15}), required=False, label="Paste Document Here")

    def __init__(self, *args, **kwargs):
        template = kwargs.pop('template', None)
        super(UploadTemplateForm, self).__init__(*args, **kwargs)
        if template:
            self.fields['category'].initial = template.category
            self.fields['upload_document'].initial = template.upload_document
            self.fields['upload_text'].initial = template.upload_text
        return

    def clean(self):
        if not ('upload_document' in self.cleaned_data and 'upload_text' in self.cleaned_data):
            raise forms.ValidationError(u"Please upload a document or paste the document")
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
