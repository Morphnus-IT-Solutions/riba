from locations.models import Address, City
from feedback.models import Feedback
import re
import logging
from django.forms.models import inlineformset_factory,modelformset_factory
import utils
from django.forms.extras import widgets
from django import forms

log = logging.getLogger('request')

      
class FeedbackForm(forms.ModelForm):
    class Meta:
        model = Feedback
        fields = ("name", "email", "phone", "feedback", "client")
        widgets = {
            "name": forms.TextInput(attrs={'class':'input_l tgd','maxlength':'50'}),
            "email": forms.TextInput(attrs={'class':'input_m tgd','maxlength':'50'}),
            "phone": forms.TextInput(attrs={'class':'input_m tgd','maxlength':'20'}),
        }
