from django import forms
from orders.models import Order
from accounts.models import *
from users.models import Profile
from django.core.validators import validate_email
from utils import fields, utils
from django.forms.models import BaseModelFormSet
from datetime import datetime
from django.conf import settings

class ShippingInfoForm(forms.Form):
    delivery_first_name = forms.CharField(max_length=200, 
        error_messages={'required':"Please enter first name"})
    delivery_last_name = forms.CharField(max_length=200,
        error_messages={'required':"Please enter last name"})
    delivery_address = forms.CharField(widget=forms.Textarea, 
        error_messages={'required':"Please enter address"})
    delivery_city = forms.CharField(max_length=200, 
        error_messages={'required':"Please enter city"})
    delivery_country = forms.CharField(max_length=200, 
        error_messages={'required':"Please enter country"})
    delivery_pincode = forms.CharField(max_length='6',  
        error_messages={'required':"Please enter pincode",
            'invalid':"Please enter a valid pincode."}, 
        validators=[fields.validate_pincode])
    delivery_phone = forms.CharField(max_length=10,
        validators=[fields.validate_phone], 
        error_messages={'required':"Please enter phone number",
        'invalid':"Please enter a valid phone number"})
    delivery_email = forms.CharField(max_length=200,required=False,
        validators=[validate_email],
        error_messages={'invalid': 'Please enter a valid email address'})
    
    def __init__(self, *args, **kwargs):
        info = kwargs.pop('info', None)
        addressbook = kwargs.pop('addressbook', None)
        client = kwargs.pop('client', None)
        super(ShippingInfoForm, self).__init__(*args, **kwargs)
        self.fields['delivery_country'].initial = 'India'
        
        if utils.is_future_ecom(client) or utils.is_indiaholii_client(client):
            self.fields['delivery_state'] = forms.ChoiceField(
                choices = utils.get_unique_fb_states(),
                error_messages={'required':"Please select state"})
            self.fields['delivery_state'].choices.insert(0,('','-- Select State --'))
            self.fields['delivery_country'].widget.attrs['readonly'] = True
        else:
            self.fields['delivery_state'] = forms.CharField(max_length=200, 
                error_messages={'required':"Please enter state"})

        if utils.is_wholii_client(client):
            self.fields['delivery_pincode'] = forms.CharField(max_length='10',  
                error_messages={'required':"Please enter Zipcode",
                    'invalid':"Please enter a valid Zipcode."})
            self.fields['delivery_country'].initial = ''
        elif utils.is_usholii_client(client):
            self.fields['delivery_pincode'] = forms.CharField(max_length='10',  
                error_messages={'required':"Please enter Zipcode",
                    'invalid':"Please enter a valid Zipcode."})
            self.fields['delivery_state'] = forms.ChoiceField(
                choices = utils.get_us_states(),
                error_messages={'required':"Please select state"})
            self.fields['delivery_state'].choices.insert(0,('','-- Select State --'))
            self.fields['delivery_country'].initial = 'USA'
        else:
            self.fields['delivery_state'] = forms.ChoiceField(
                choices = utils.get_unique_fb_states(),
                error_messages={'required':"Please select state"})
            self.fields['delivery_state'].choices.insert(0,('','-- Select State --'))
            self.fields['delivery_country'].widget.attrs['readonly'] = True
        
        try:
            if info:
                self.fields['delivery_first_name'].initial = info.address.first_name
                self.fields['delivery_last_name'].initial = info.address.last_name
                self.fields['delivery_address'].initial = info.address.address
                self.fields['delivery_city'].initial = info.address.city.name
                self.fields['delivery_pincode'].initial = info.address.pincode
                self.fields['delivery_state'].initial = info.address.state.name
                self.fields['delivery_country'].initial = info.address.country.name
                self.fields['delivery_phone'].initial = info.address.phone
                self.fields['delivery_email'].initial = info.address.email

            elif addressbook:
                self.fields['delivery_first_name'].initial = addressbook.first_name
                self.fields['delivery_last_name'].initial = addressbook.last_name
                self.fields['delivery_address'].initial = addressbook.address
                self.fields['delivery_city'].initial = addressbook.city.name
                self.fields['delivery_pincode'].initial = addressbook.pincode
                self.fields['delivery_state'].initial = addressbook.state.name
                self.fields['delivery_country'].initial = addressbook.country.name
                self.fields['delivery_phone'].initial = addressbook.phone
                self.fields['delivery_email'].initial = addressbook.email
        except AttributeError:
            # exception for old orders booked through call center interface
            # where only pincode was mandatory
            pass
        return
    
    
class BillingInfoForm(forms.Form):
    billing_first_name = forms.CharField(max_length=200, 
        error_messages={'required':"Please enter first name"})
    billing_last_name = forms.CharField(max_length=200,
        error_messages={'required':"Please enter last name"})
    billing_address = forms.CharField(widget=forms.Textarea,
        error_messages={'required':"Please enter address"})
    billing_city = forms.CharField(max_length=200,
        error_messages={'required':"Please enter city"})
    billing_pincode = forms.CharField(max_length=6,
        error_messages={'required':"Please enter pincode",
        'invalid':"Please enter a valid pincode."},
        validators=[fields.validate_pincode])
    billing_state = forms.CharField(max_length=200, 
        error_messages={'required':"Please enter state"})
    billing_country = forms.CharField(max_length=200, 
        error_messages={'required':"Please enter country"})
    billing_phone = forms.CharField(max_length=10, 
        error_messages={'required':"Please enter phone number",
        'invalid':"Please enter a valid phone number"},
        validators=[fields.validate_phone])
    billing_email = forms.CharField(max_length=100,required=False,
        validators=[validate_email],
        error_messages={'invalid': 'Please enter a valid email address'})
    
    def __init__(self, *args, **kwargs):
        info = kwargs.pop('info', None)
        super(BillingInfoForm, self).__init__(*args, **kwargs)
        # XXX State should be a text field for non futurebazaar clients
        self.fields['billing_state'] = forms.ChoiceField(
            choices = utils.get_unique_fb_states())
        if info:
            self.fields['billing_first_name'].initial = info.address.first_name
            self.fields['billing_last_name'].initial = info.address.last_name
            self.fields['billing_address'].initial = info.address.address
            self.fields['billing_city'].initial = info.address.city.name
            self.fields['billing_pincode'].initial = info.address.pincode
            self.fields['billing_state'].initial = info.address.state.name
            self.fields['billing_country'].initial = info.address.country.name
            self.fields['billing_phone'].initial = info.address.phone
            self.fields['billing_email'].initial = info.address.email
        return
    
    def clean(self):
        if 'billing_pincode' in self.cleaned_data:
            if not self.cleaned_data['billing_pincode']:
                raise forms.ValidationError(u"Please enter billing pincode")
            elif not self.cleaned_data['billing_pincode'].isdigit():
                raise forms.ValidationError(u"Please enter digits only")
        return self.cleaned_data

class DeliveryNotesForm(forms.Form):
    delivery_notes = forms.CharField(widget=forms.Textarea, required=False)
    delivery_gift_notes = forms.CharField(widget=forms.Textarea, required=False)
    def __init__(self,*args, **kwargs):
        super(DeliveryNotesForm,self).__init__(*args,**kwargs)
        self.fields['delivery_notes'].widget.attrs['class'] = 'tgd texta_m'
        self.fields['delivery_notes'].widget.attrs[
            'default_value'] = 'Delivery Instructions'
        self.fields['delivery_gift_notes'].widget.attrs[
            'class'] = 'tgd texta_m'
        self.fields['delivery_gift_notes'].widget.attrs[
            'default_value'] = 'Gift Message'
    
class OrderCancellationForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(OrderCancellationForm, self).__init__(*args, **kwargs)
        self.fields['cancellation_notes'] = forms.CharField(widget=forms.Textarea,
                error_messages = {'required': 'Please fill the cancellation notes.'},
                )
        self.fields['next_action'] = forms.TypedChoiceField(widget=forms.RadioSelect,
                choices = (('action_1', 'Refund after cancellation'), ('action_2', 'No Refund Required'), ('action_3', 'Amount already Refunded')),
                initial = 'action_2', required=False
                )

class FMEMIForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(FMEMIForm, self).__init__(*args, **kwargs)
        MONTHS = (
                ('','Month'),
                ('01','Jan'),
                ('02','Feb'),
                ('03','Mar'),
                ('04','Apr'),
                ('05','May'),
                ('06','Jun'),
                ('07','Jul'),
                ('08','Aug'),
                ('09','Sep'),
                ('10','Oct'),
                ('11','Nov'),
                ('12','Dec'))
        self.fields['issuing_bank'] = forms.CharField(max_length=50)
        self.fields['last_4_digits'] = forms.CharField(max_length=4,
            error_messages = {'required':"Please enter last 4 digits of your credit card."})
        self.fields['issue_month'] = forms.ChoiceField(
            choices = MONTHS,
            error_messages = {'required':'Please enter issuing month'})
        current_year = datetime.now().year
        issue_year_choices = (('','Year'),)
        for i in range(2000, current_year):
            issue_year_choices += ((str(i),str(i)),)
        self.fields['issue_year'] = forms.ChoiceField(
            choices = issue_year_choices,
            error_messages = {'required':'Please enter issuing year'})
        self.fields['exp_month'] = forms.ChoiceField(
            choices = MONTHS,
            error_messages = {'required':'Please enter expiration month'})
        exp_year_choices = (('','Year'),)
        for i in range(current_year,2025):
            exp_year_choices += ((str(i),str(i)),)
        self.fields['exp_year'] = forms.ChoiceField(
            choices = exp_year_choices, 
            error_messages = {'required':'Please enter expiration year'})
        self.fields['name_on_card'] = forms.CharField(max_length=100,
            error_messages={'required':"Please enter Name"})
        self.fields['last_4_digits'].widget.attrs['style'] = 'width:150px;'
        self.fields['last_4_digits'].widget.attrs['autocomplete'] = 'off'
        self.fields['issue_month'].widget.attrs['style'] = 'width:77px;'
        self.fields['issue_year'].widget.attrs['style'] = 'width:77px;'
        self.fields['exp_month'].widget.attrs['style'] = 'width:77px;'
        self.fields['exp_year'].widget.attrs['style'] = 'width:77px;'
        self.fields['name_on_card'].widget.attrs['style'] = 'width:150px;'
        self.fields['name_on_card'].widget.attrs['autocomplete'] = 'off'

class CreditCardForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super(CreditCardForm, self).__init__(*args, **kwargs)
        self.fields['card_no'] = forms.CharField(max_length=16,error_messages={'required':"Please enter card number"})
        self.fields['exp_month'] = forms.ChoiceField(
            choices = (
                ('','Month'),
                ('01','Jan'),
                ('02','Feb'),
                ('03','Mar'),
                ('04','Apr'),
                ('05','May'),
                ('06','Jun'),
                ('07','Jul'),
                ('08','Aug'),
                ('09','Sep'),
                ('10','Oct'),
                ('11','Nov'),
                ('12','Dec')),
                error_messages = {'required':'Please enter expiration month'})
        self.fields['exp_year'] = forms.ChoiceField(
            choices = (
                ('','Year'),
                ('2012','2012'),
                ('2013','2013'),
                ('2014','2014'),
                ('2015','2015'),
                ('2016','2016'),
                ('2017','2017'),
                ('2018','2018'),
                ('2019','2019'),
                ('2020','2020'),
                ('2021','2021'),
                ('2022','2022'),
                ('2023','2023'),
                ('2024','2024'),
                ('2025','2025')),
                error_messages = {'required':'Please enter expiration year'})
        self.fields['cvv'] = forms.CharField(max_length=3, widget=forms.PasswordInput,error_messages={'required':"Please enter cvv number"})
        self.fields['name_on_card'] = forms.CharField(max_length=100,error_messages={'required':"Please enter name on card"})
        self.fields['card_no'].widget.attrs['style'] = 'width:150px;'
        self.fields['card_no'].widget.attrs['autocomplete'] = 'off'
        self.fields['exp_month'].widget.attrs['style'] = 'width:77px;'
        self.fields['exp_year'].widget.attrs['style'] = 'width:77px;'
        self.fields['cvv'].widget.attrs['style'] = 'width:150px;'
        self.fields['cvv'].widget.attrs['autocomplete'] = 'off'
        self.fields['name_on_card'].widget.attrs['style'] = 'width:150px;'
        self.fields['name_on_card'].widget.attrs['autocomplete'] = 'off'

class BasePaymentOptionFormSet(BaseModelFormSet):
    def __init__(self, *args,**kwargs):
        super(BasePaymentOptionFormSet, self).__init__(*args,**kwargs)
        #self.queryset = PaymentOption.objects.filter(payment_mode__client__id='1')


def flf_msg(status_code):
    errorCode = status_code.lower()
    if errorCode == "err_inv":
        errDesc = "Sorry, we cannot ship this product. This product is currently out of stock."
    else:
        errDesc = "Sorry, we cannot ship this product at your pincode. "
    return errDesc


#For support state movement
class OrderItemForm(forms.Form):
    expected_stock_arrival = forms.DateField(label='Stock Arrival Date',
        input_formats=['%d %b %Y'], widget=forms.TextInput(attrs={
        'readonly':'readonly', 'autocomplete':'off'}))
    delivery_no = forms.CharField(label='Delivery Number')
    po_number = forms.CharField(label='PO Number', required=False)
    po_date = forms.DateField(label='PO Creation Date',
        input_formats=['%d %b %Y'], widget=forms.TextInput(attrs={
        'readonly':'readonly', 'autocomplete':'off'}), required=False)
    notes = forms.CharField(required=False)

    def clean(self):
        if ('delivery_no' in self.cleaned_data) and not self.cleaned_data['delivery_no'].isdigit():
            raise forms.ValidationError(u"Please enter a valid delivery number")
        if self.cleaned_data.get('po_number') and not self.cleaned_data['po_number'].isdigit():
            raise forms.ValidationError(u"Please enter a valid PO number")
        return self.cleaned_data

