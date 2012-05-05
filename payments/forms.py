from django import forms
import re
from accounts.models import DomainPaymentOptions

class PaymentAttemptForm(forms.Form):
    instrument_no = forms.CharField(label='Cheque Number')
    instrument_issue_bank = forms.CharField(label='Bank')
    instrument_recv_date = forms.DateField(label='Received On',
        input_formats=['%d %b %Y'], widget=forms.TextInput(attrs={
        'readonly':'readonly', 'autocomplete':'off'}))
    amount = forms.DecimalField(max_digits=12, decimal_places=2)
    pg_transaction_id = forms.CharField(label='Transaction ID')
    payment_realized_on = forms.DateTimeField(label='Payment On',
        input_formats=['%d %b %Y'], widget=forms.TextInput(attrs={
        'readonly':'readonly', 'autocomplete':'off'}))
    gateway = forms.CharField(label='Deposit Bank')
    notes = forms.CharField(required=False)

    def clean(self):
        if ('amount' in self.cleaned_data) and not self.cleaned_data['amount']:
            raise forms.ValidationError(u"Please enter amount")
        if ('instrument_no' in self.cleaned_data) and not self.cleaned_data['instrument_no'].isdigit():
            raise forms.ValidationError(u"Please enter a valid cheque number")
        return self.cleaned_data

class InstantPaymentFormCC(forms.Form):
    bank = forms.CharField(max_length=5, label='Bank', error_messages={'required': 'Please enter Bank Code'})
    transaction_no = forms.CharField(label='Transaction No.', error_messages={'required': 'Please enter Transaction No.'})
    transaction_notes = forms.CharField(label='Transaction Notes', error_messages={'required': 'Please enter Notes'})

class RefundForm(forms.Form):
    amount = forms.DecimalField(max_digits=12, decimal_places=2)
    notes = forms.CharField(required=False)
    
    def clean(self):
        if ('amount' in self.cleaned_data) and not self.cleaned_data['amount']:
            raise forms.ValidationError(u"Please enter amount")
        return self.cleaned_data

class ConfirmPaymentForm(forms.Form):
    def __init__(self, request, order, *args, **kwargs):
        self.request = request
        self.order = order
        super(ConfirmPaymentForm, self).__init__(*args, **kwargs)
        pm_choices = (('','Select'),)
        pm_choices += order.client.get_payment_options()

        self.fields['payment_mode'] = forms.ChoiceField(
                choices = pm_choices,
                label='Select payment option',
                error_messages = {'required': 'Please select payment option'}
                )   
        self.fields['transaction_no'] = forms.CharField(required=False)
        self.fields['transaction_notes'] = forms.CharField(widget=forms.Textarea,required=False)
        self.fields['transaction_password'] = forms.CharField(widget=forms.PasswordInput, required=False)
        if order.payment_mode:
            self.fields['payment_mode'].initial = order.payment_mode
        if not self.request.client.is_second_factor_auth_reqd:
            self.fields['transaction_password'].widget.attrs['class'] = 'hidden'
       
    def clean(self):
        if self.request.client.is_second_factor_auth_reqd:
            if 'transaction_password' in self.cleaned_data:
                try:
                    user_profile = utils.get_user_info(self.request)
                    user_profile = user_profile['profile']
                    if self.cleaned_data['transaction_password'].strip() == "" or user_profile.transaction_password != self.cleaned_data['transaction_password'].strip():
                        raise forms.ValidationError(
                            u"Please enter the correct transaction password")
                except:
                    raise forms.ValidationError(
                        u"Please enter the correct transaction password.")
        return self.cleaned_data	
