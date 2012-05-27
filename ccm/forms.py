from ccm.models import CallSlot
from django import forms
from django.forms import widgets

class CallSlotForm(forms.ModelForm):
    """CallSlot Form with modified behavior

    The form shows pretty checkboxes for selecting days, which are serialized
    to string before being saved and deserialized to pre-populate the form with
    initial values in accordance with the values of call_slot.days_of_week
    """

    DAYS_OF_WEEK = (
        ('0', 'Sunday'),
        ('1', 'Monday'),
        ('2', 'Tuesday'),
        ('3', 'Wednesday'),
        ('4', 'Thursday'),
        ('5', 'Friday'),
        ('6', 'Saturday'),
    )

    dow = forms.MultipleChoiceField(
            widget=widgets.CheckboxSelectMultiple(),
            choices=DAYS_OF_WEEK)
    
    def __init__(self, *args, **kwargs):
        super(CallSlotForm, self).__init__(*args, **kwargs)
        instance = kwargs.get('instance', None)
        if instance:
            dow = instance.days_of_week
            dow_initial = [i for i in range(len(dow)) if int(dow[i])]
        else:
            dow_this = []
        self.fields['dow'].initial = dow_initial


    class Meta:
        model = CallSlot

    def clean_dow(self):
        dow = self.cleaned_data['dow']
        dow_str_list = list('0'*7)
        for e in dow:
            dow_str_list[int(e)] = '1'
        dow_str = ''.join(dow_str_list)
        print dow_str
        return dow_str

    def save(self, *args, **kwargs):
        kwargs.update({'commit': False})
        call_slot = super(CallSlotForm, self).save(*args, **kwargs)
        call_slot.days_of_week = self.cleaned_data['dow']
        call_slot.save()
        return call_slot

