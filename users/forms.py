from django import forms
from users.models import Profile
import re
import logging
from django.forms.models import inlineformset_factory,modelformset_factory
import utils
from django.forms.extras import widgets

log = logging.getLogger('request')

class UserForm(forms.ModelForm):
    class Meta:
        model = Profile
    passcode = forms.CharField(widget=forms.PasswordInput(render_value=False))

class MyProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("full_name", "primary_phone", "secondary_phone", "primary_email", "webpage", "twitter", "facebook", "date_of_birth", "gender")
        widgets = {
            'gender':forms.widgets.RadioSelect(),
            'date_of_birth':widgets.SelectDateWidget(years = range(1900,2010) ),
            'primary_phone': forms.TextInput(attrs={'maxlength':'10'}),
        }

class PpdAdminUserSignupForm(forms.Form):
    product_choices = (('children_products', 'Children Products'), ('magazines','Magazines'), ('appliances', 'Appliances'), ('other', 'Other'))
    sale_price_choices = (('under_1000', 'Under Rs. 1,000'), ('1000-3000', 'Rs. 1,000 - 3,000'), ('3000-10000', 'Rs. 3,000 - 10,000'), ('Above-10000', 'Above Rs. 10,000'))
    daily_responses_choices = (('10-100', '10-100'),('100-300', '100-300'), ('300-1000','300-1000'), ('above-1000','Above 1000'))
    time_to_ship_choices = (('1-3', '1-3 working days'), ('4-7', '4-7 working days'), ('7-10', '7-10 working days'))
    stocking_choices = (('central','Central'), ('state', 'State'), ('local', 'Local'))
    average_retail_margins_choices = (('under-10', 'Under 10%'), ('10-20', '10% - 20%'), ('20-30', '20% - 30%'), ('above-30', 'Above 30%'))
    name = forms.CharField(max_length=200, error_messages={'required':"Please enter name"})
    mobile = forms.CharField(max_length=200, error_messages={'required':"Please enter mobile"})
    email = forms.EmailField(max_length=200, error_messages={'required':"Please enter email"})
    company = forms.CharField(max_length=200, error_messages={'required':"Please enter company"})
    website = forms.CharField(max_length=200, error_messages={'required':"Please enter website"})
    products = forms.ChoiceField(label="Products You Sell", choices = product_choices, widget=forms.CheckboxSelectMultiple)
    average_sale_price = forms.ChoiceField(choices = sale_price_choices)
    average_retail_margins = forms.ChoiceField(choices = average_retail_margins_choices)
    daily_responses = forms.ChoiceField(choices = daily_responses_choices)
    time_to_ship = forms.ChoiceField(choices = time_to_ship_choices)
    stocking = forms.ChoiceField(choices = stocking_choices)
    remarks = forms.CharField(widget=forms.widgets.Textarea())

