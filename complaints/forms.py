from django import forms
from complaints.models import *
from utils import fields

class ComplaintAddForm(forms.Form):
    products = forms.MultipleChoiceField(error_messages={'required':'Please select atleast one product'}, widget=forms.CheckboxSelectMultiple())
    category = forms.ChoiceField(choices=Complaint.CATEGORY_CHOICES)
    status = forms.ChoiceField(widget=forms.HiddenInput, choices=Complaint.STATUS_CHOICES)
    source = forms.ChoiceField(choices=Complaint.SOURCE_CHOICES)
    notes = forms.CharField(widget=forms.Textarea)
    order = forms.IntegerField(widget=forms.HiddenInput, required=False)
    
    def __init__(self, choices=None, *args, **kwargs):
        super(ComplaintAddForm, self).__init__(*args, **kwargs)
        if choices:
            self.fields['products'].choices = choices


class ComplaintUpdateForm(forms.Form):
    category = forms.ChoiceField(choices=Complaint.CATEGORY_CHOICES)
    status = forms.ChoiceField(choices=Complaint.STATUS_CHOICES)
    notes = forms.CharField(widget=forms.Textarea)
    complaint = forms.IntegerField(widget=forms.HiddenInput)

class ComplaintFilterForm(forms.Form):
    complaint_id = forms.CharField(required=False, label='Complaint ID')
    phone = forms.CharField(required=False, validators=[fields.validate_phone])
    email = forms.CharField(required=False, validators=[fields.validate_email])
    order_id = forms.CharField(required=False, label='Order ID')
    category = forms.ChoiceField(required=False, choices= [('','-------')] + [x for x in Complaint.CATEGORY_CHOICES],initial=Complaint.CATEGORY_CHOICES[0][0])
    status = forms.ChoiceField(required=False, choices= [('','-------')] + [x for x in Complaint.STATUS_CHOICES], initial=Complaint.STATUS_CHOICES[0][0])
    level = forms.ChoiceField(required=False, choices= [('','-------')] + [x for x in Complaint.LEVEL_CHOICES])

