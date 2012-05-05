from django import forms
from accounts.models import *
import re
import logging
from django.forms.models import inlineformset_factory,modelformset_factory
from django.forms.formsets import formset_factory
import utils
from django.forms.extras import widgets

log = logging.getLogger('request')

class SellerForm(forms.ModelForm):
    class Meta:
        model = Account
    passcode = forms.CharField(widget=forms.PasswordInput(render_value=False))

class SellerProfileForm(forms.ModelForm):
    class Meta:
        model = Account
        fields = ("name", "code", "website", "confirmed_order_email", "pending_order_email", "share_product_email", "signature", "pending_order_helpline", "confirmed_order_helpline", "sms_mask", "type", "customer_support_no", "primary_email", "secondary_email", "primary_phone", "secondary_phone", "shipping_policy", "returns_policy", "tos", "dni", "greeting_title", "greeting_text")
        widgets = {
#            'gender':forms.widgets.RadioSelect(),
        }

class SellerLoginForm(forms.Form):
    username = forms.CharField(max_length = 200, required=False)
    password = forms.CharField(widget=forms.PasswordInput(render_value=False), required=False)
    new_password = forms.CharField(widget=forms.PasswordInput(render_value=False), required=False)
    confirm_password = forms.CharField(widget=forms.PasswordInput(render_value=False), required=False)

class SellerNotificationForm(forms.ModelForm):
    class Meta:
        model = NotificationSettings
        fields = ("event", "on_primary_email", "on_secondary_email", "on_primary_phone", "on_secondary_phone")

class PaymentOptionForm(forms.ModelForm):
    class Meta:
        model = PaymentOption
        fields = ("payment_delivery_address", "bank_branch", "bank_ac_name", "bank_ac_type", "bank_name", "bank_ac_no", "bank_address", "bank_ifsc")

class CashCollectionForm(forms.ModelForm):
    class Meta:
        model = DepositPaymentOptions
        fields = ("bank_ac_no", "bank_ifsc")

class DepositForm(forms.ModelForm):
    class Meta:
        model = DepositPaymentOptions
        fields = ("bank_ac_name", "bank_ac_type", "bank_name", "bank_ac_no", "bank_ifsc")

class TransferForm(forms.ModelForm):
    class Meta:
        model = PaymentOption
        fields = ("bank_ac_name", "bank_ac_type", "bank_name", "bank_ac_no", "bank_ifsc")

class ChequeForm(forms.ModelForm):
    class Meta:
        model = PaymentOption
        fields = ("in_favor_of", "payment_delivery_address")

class StoreForm(forms.ModelForm):
    class Meta:
        model = PaymentOption
        fields = ("location_url",)
