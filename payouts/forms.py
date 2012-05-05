from django import forms
from payouts.models import *
from accounts.models import Account
from datetime import date


class PayoutHomeForm(forms.Form):
    def __init__(self,*args, **kwargs):
        super(PayoutHomeForm,self).__init__(*args,**kwargs)
        self.fields['seller'] = forms.ModelChoiceField(queryset=Account.objects.get_query_set(), required=False)
#                error_messages = {'required': 'Please select seller'})
        self.fields['month'] = forms.ChoiceField(
                initial = date.today().month,
                choices = (('','---------'),) +SellerPayout.MONTHS,
                label = 'Select Payout Month',
                error_messages = {'required': 'Please select payout month'})
        self.fields['year'] = forms.ChoiceField(
                initial = date.today().year,
                choices = (
                    ('','---------'),
                    (2007,2007),
                    (2008,2008),
                    (2009,2009),
                    (2010,2010),
                    (2011,2011),
                    (2012,2012),
                    (2013,2013)),
                label = 'Select Payout Year',
                error_messages = {'required': 'Please select payout year'})
