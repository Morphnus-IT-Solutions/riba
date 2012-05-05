from locations.models import AddressBook, City
import re
import logging
from django.forms.models import inlineformset_factory,modelformset_factory
import utils
from django.forms.extras import widgets
from django import forms
from utils import fields,utils 

log = logging.getLogger('request')

      
class MyAddressForm(forms.ModelForm):
    def __init__(self, request, *args, **kwargs):
        super(MyAddressForm, self).__init__(*args, **kwargs)
        if 'instance' in kwargs:
            self.address = kwargs['instance']
            self.fields['cityname'] = forms.CharField(max_length=100, error_messages={'required':'Please enter city.'},label='City', widget=forms.TextInput(attrs={'class':'input_m tgd','maxlength':'40'}),initial = self.address.city.name )
            if utils.is_future_ecom(request.client.client) or utils.is_ezoneonline(request.client.client) or utils.is_holii_client(request.client.client):
                from integrations.fbapi import fbapiutils
                if utils.is_usholii_client(request.client.client):
                    unique_states = utils.get_us_states()
                else:
                    unique_states = utils.get_unique_fb_states()
                if utils.is_ezoneonline(request.client.client) or utils.is_holii_client(request.client.client):
                    unique_states.insert(0, ('', '-- Select State --'))
                if utils.is_usholii_client(request.client.client):
                    if not fbapiutils.US_STATES_MAP.get(self.address.state.name,''): 
                        self.fields['statename'] = forms.ChoiceField(choices = unique_states,
                            error_messages={'required':'Please select state'},
                            label='State')
                    else:
                        self.fields['statename'] = forms.ChoiceField(choices = unique_states,
                            error_messages={'required':'Please select state'},
                            label='State',initial=fbapiutils.US_STATES_MAP[self.address.state.name])
                else:
                    if not fbapiutils.STATES_MAP.get(self.address.state.name,''): 
                        self.fields['statename'] = forms.ChoiceField(choices = unique_states,
                            error_messages={'required':'Please select state'},
                            label='State')
                    else:
                        self.fields['statename'] = forms.ChoiceField(choices = unique_states,
                            error_messages={'required':'Please select state'},
                            label='State',initial=fbapiutils.STATES_MAP[self.address.state.name])
            self.fields['statename'] = forms.CharField(max_length=100, error_messages={'required':'Please enter state.'},
            label='State', widget=forms.TextInput(attrs={'class':'input_m tgd','maxlength':'40'}),initial=self.address.state.name )
            self.fields['countryname'] = forms.CharField(max_length=100, error_messages={'required':'Please enter country.'}, label='Country', widget=forms.TextInput(attrs={'class':'input_m tgd','maxlength':'40'}),initial=self.address.country.name )
            self.fields['address'] = forms.CharField(error_messages={'required':'Please enter address.'},widget = forms.Textarea(attrs={'class':'input_l tgd','rows':'3'}), initial = self.address.address)
            self.fields['phone'] = forms.CharField(max_length=10,error_messages={'required':'Please enter Phone No.','invalid':'Please enter 10-digit Phone No.'},widget = forms.TextInput(attrs={'class':'input_m tgd','maxlength':'10'}), initial = self.address.phone)
            if utils.is_usholii_client(request.client.client) or utils.is_wholii_client(request.client.client):
                self.fields['pincode'] = forms.CharField(error_messages={'required':'Please enter Zipcode.','invalid':"Please enter valid Zipcode."},widget = forms.TextInput(attrs={'class':'input_m tgd','maxlength':'10'}), initial = self.address.pincode)
            else:
                self.fields['pincode'] = forms.CharField(error_messages={'required':'Please enter Pincode.','invalid':"Please enter valid Pincode."},validators=[fields.validate_pincode],widget = forms.TextInput(attrs={'class':'input_m tgd','maxlength':'6'}), initial = self.address.pincode)

            
        else:
            self.fields['cityname'] = forms.CharField(max_length=100, error_messages={'required':'Please enter city.'},label='City', widget=forms.TextInput(attrs={'class':'input_m tgd','maxlength':'40'}) )
            if utils.is_usholii_client(request.client.client):
                unique_states = utils.get_us_states()
            else:
                unique_states = utils.get_unique_fb_states()
            if utils.is_future_ecom(request.client.client) or utils.is_ezoneonline(request.client.client) or utils.is_usholii_client(request.client.client) or utils.is_indiaholii_client(request.client.client):
                if utils.is_ezoneonline(request.client.client) or utils.is_usholii_client(request.client.client) or utils.is_indiaholii_client(request.client.client):
                    unique_states.insert(0, ('', '-- Select State --'))
                self.fields['statename'] = forms.ChoiceField(choices = unique_states,
                    error_messages={'required':'Please select state'}, label='State')
            else:
                self.fields['statename'] = forms.CharField(max_length=100,error_messages={'required':'Please enter state.'}, label='State', widget=forms.TextInput(attrs={'class':'input_m tgd','maxlength':'40'}))
            self.fields['countryname'] = forms.CharField(max_length=100, label='Country', error_messages={'required':'Please enter country.'},widget=forms.TextInput(attrs={'class':'input_m tgd','maxlength':'40'}))
            self.fields['address'] = forms.CharField(error_messages={'required':'Please enter address.'},widget = forms.Textarea(attrs={'class':'input_l tgd','rows':'3'}))
            self.fields['phone'] = forms.CharField(error_messages={'required':'Please enter Phone No.','invalid':"Please enter 10-digit Phone No."},validators=[fields.validate_phone],widget = forms.TextInput(attrs={'class':'input_m tgd','maxlength':'10'}))
            if utils.is_usholii_client(request.client.client) or utils.is_wholii_client(request.client.client):
                self.fields['pincode'] = forms.CharField(error_messages={'required':'Please enter Zipcode.','invalid':"Please enter valid Zipcode."},widget = forms.TextInput(attrs={'class':'input_m tgd','maxlength':'10'}))
            else:
                self.fields['pincode'] = forms.CharField(error_messages={'required':'Please enter Pincode.','invalid':"Please enter valid Pincode."},widget = forms.TextInput(attrs={'class':'input_m tgd','maxlength':'6'}))
        if utils.is_future_ecom(request.client.client) or utils.is_ezoneonline(request.client.client) or utils.is_usholii_client(request.client.client) or utils.is_indiaholii_client(request.client.client):
            self.fields['countryname'].widget.attrs['readonly'] = 'readonly'
            self.fields['statename'].widget.attrs['class'] = 'input_m tgd'
            if utils.is_usholii_client(request.client.client):
                self.fields['countryname'].initial = 'USA'
            else:
                self.fields['countryname'].initial = 'India'
        
    class Meta:
        model = AddressBook
        fields = ("first_name", "last_name", "pincode","email", "defaddress")
        widgets = {
            "first_name": forms.TextInput(attrs={'class':'input_l tgd','maxlength':'50'}),
            "last_name": forms.TextInput(attrs={'class':'input_l tgd','maxlength':'50'}),
            "email": forms.TextInput(attrs={'class':'input_m tgd','maxlength':'50'}),
        }
