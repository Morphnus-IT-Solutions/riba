from django import forms
from accounts.models import *
import re
import logging
from django.forms.models import inlineformset_factory,modelformset_factory
from django.forms.formsets import formset_factory
import utils
from django.forms.extras import widgets

log = logging.getLogger('request')

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
