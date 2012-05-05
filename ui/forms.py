from django import forms
from dialer.models import Attempt
import logging

log = logging.getLogger('ccc')

class CloseAttemptForm(forms.Form):
    def __init__(self, opts, *args, **kwargs):
        self.opts = opts
        super(CloseAttemptForm, self).__init__(*args, **kwargs)
        self.fields['response_status'].choices = opts['response_statuses']

    call_status = forms.ChoiceField(choices=(
            ('Busy','Busy'),
            ('Congestion','Congestion'),
            ('Invalid Number', 'Invalid Number'),
            ('No reply', 'No reply'),
            ('Unreachable','Unreachable'),
            ('Answered', 'Answered')))
    response_status = forms.ChoiceField(choices=(('---','---'),))
    comments = forms.CharField(widget=forms.Textarea(),required=False)
    next_call = forms.CharField(required=False)
    next_call_hour = forms.ChoiceField(required=False, choices=
            tuple([('','')] + [('%02d'%x,'%02d'%x) for x in range(1,13)]))
    next_call_min = forms.ChoiceField(required=False, choices=
            tuple([('','')] + [('%02d'%x,'%02d'%x) for x in range(0,59,15)]))
    next_call_am_pm = forms.ChoiceField(required=False, choices=(
        ('AM','AM'),
        ('PM','PM')))
