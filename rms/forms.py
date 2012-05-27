from django import forms
from django.contrib.auth.models import Group
from ccm.models import Agent
from rms.models import Campaign, Response
IMPORT_FILE_TYPES = ['.xls']

class CampaignForm(forms.ModelForm): 
    campaign_type = forms.ModelChoiceField(label = 'Campaign Type', queryset = Campaign.objects.filter(demo=True))

    def __init__(self, *args, **kwargs):
        super(CampaignForm, self).__init__(*args, **kwargs)
        self.fields['starts_on'].input_formats = ['%Y-%m-%d %H:%M:%S']
        self.fields['ends_on'].input_formats = ['%Y-%m-%d %H:%M:%S']

    class Meta:
        model = Campaign
        exclude = ('funnel', 'demo', 'draft', 'inbound_agents', 'outbound_agents')

class CampaignAgentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(CampaignAgentForm, self).__init__(*args, **kwargs)
        self.fields['inbound_agents'].widget = forms.CheckboxSelectMultiple()
        self.fields['inbound_agents'].queryset = Agent.objects.exclude(report_to=None).order_by('report_to__name','name')
        self.fields['outbound_agents'].widget = forms.CheckboxSelectMultiple()
        self.fields['outbound_agents'].queryset = Agent.objects.exclude(report_to=None).order_by('report_to__name','name')
    
    class Meta:
        model = Campaign
        fields = ('inbound_agents', 'outbound_agents')

class XlsInputForm(forms.Form):
    input_excel = forms.FileField(label = "File")

    def clean_input_excel(self):
        import os
        input_excel = self.cleaned_data['input_excel']
        extension = os.path.splitext(input_excel.name)[1]
        if not (extension in IMPORT_FILE_TYPES):
            raise forms.ValidationError("%s is not a valid excel file. Please make sure your uploaded file is an Excel File (.xls)" %extension)
        else:
            return input_excel


class DateRangeForm(forms.Form):	
	start_date = forms.DateField(required = False, input_formats=['%Y-%m-%d'])
	end_date = forms.DateField(required = False, input_formats=['%Y-%m-%d'])


class CallCloseForm(forms.Form):
    communication = forms.ChoiceField(label='Communication Mode', required=False, choices = (('call','Call'),
                                                                                             ('sms','SMS'),
                                                                                             ('email','Email'),
                                                                                             ('chat','Chat')))
    state = forms.CharField(label = 'State', required=False)
    substate = forms.CharField(label = 'Substate', required=False)
    notes = forms.CharField(widget = forms.Textarea, required=False)
    followup_on = forms.DateTimeField(label='Followup On', required=False)


class AddUserForm(forms.Form):
    username = forms.CharField(label='User Name')
    role = forms.ModelChoiceField(queryset=Group.objects.filter(name__in=['CallCenter','CC Manager','Client','RMS Admin']), empty_label=None)


class EditUserForm(forms.Form):
    role = forms.ModelChoiceField(queryset=Group.objects.filter(name__in=['CallCenter','CC Manager','Client','RMS Admin']), required=False)
    campaigns = forms.ModelMultipleChoiceField(queryset=[], required=False)

    def __init__(self, *args, **kwargs):
        super(EditUserForm, self).__init__(*args, **kwargs)
        self.fields['campaigns'].widget = forms.CheckboxSelectMultiple()
        self.fields['campaigns'].queryset = Campaign.objects.filter(demo=False)
