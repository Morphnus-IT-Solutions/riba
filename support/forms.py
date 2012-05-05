from django import forms
from support.models import Team, User, State, SubState, ActionFlow, InformationFlow
from payments.models import PaymentAttempt
from utils import fields
import re

CSV_RE = re.compile(r'^(\s*\d+\s*,)*(\s*\d+\s*){,1}\s*$')

class TeamForm(forms.ModelForm):
    class Meta:
        model = Team


class UserForm(forms.Form):
    username = forms.CharField()
    team = forms.ModelChoiceField(queryset=Team.objects.all(), empty_label=None)
    role = forms.ChoiceField(choices=(('member','Member'),('lead','Lead')))


class StateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StateForm, self).__init__(*args, **kwargs)
        self.fields['responsible_team'].empty_label = None
    
    class Meta:
        model = State


class SubStateForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(SubStateForm, self).__init__(*args, **kwargs)
        self.fields['state'].empty_label = None
        self.fields['acting_team'].empty_label = None
        self.fields['tat'].widget = fields.TimeDeltaWidget({'inputs':['days','hours']})
    
    class Meta:
        model = SubState
        exclude = ('entity',)


class ActionFlowForm(forms.ModelForm):
    class Meta:
        model = ActionFlow
        exclude = ('group',)


class InformationFlowForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(InformationFlowForm, self).__init__(*args, **kwargs)
        self.fields['acting_team'].empty_label = None
        self.fields['receipients'].widget = forms.CheckboxSelectMultiple()
        self.fields['receipients'].queryset = Team.objects.all()

    class Meta:
        model = InformationFlow


class OrderAckForm(forms.Form):
    orderId = forms.CharField()
    orderState = forms.CharField()
    orderDesc = forms.CharField(required=False)
    header = forms.CharField()
    id = forms.IntegerField()


class ItemAckForm(forms.Form):
    orderId = forms.CharField()
    #orderDate = forms.DateField(input_formats=['%Y%m%d'], required=False)
    header = forms.CharField()
    atgDocumentId = forms.IntegerField()
    quantity = forms.IntegerField()
    plantId = forms.IntegerField()
    itemState = forms.CharField(required=False)
    deliveryNumber = forms.CharField(required=False)
    deliveryDate = forms.DateField(required=False, input_formats=['%d-%m-%Y'])
    invoiceNumber = forms.CharField(required=False)
    invoiceDate = forms.DateField(required=False, input_formats=['%d-%m-%Y'])
    invoiceNetValue = forms.DecimalField(required=False)
    pgiCreationDate = forms.DateField(required=False, input_formats=['%Y%m%d'])
    retID = forms.IntegerField(required=False)  #Return item id
    retCreatedDate = forms.DateField(required=False)
    retInvoiceDate = forms.DateField(required=False)
    retInvoiceNetValue = forms.DecimalField(required=False)
    pgrCreationDate = forms.DateField(required=False, input_formats=['%Y%m%d'])
    awbNumber = forms.CharField(required=False)
    lspName = forms.CharField(required=False)


class DelAckForm(forms.Form):
    orderId = forms.CharField()
    header = forms.CharField()
    #atgDocumentId = forms.IntegerField(required=False)
    deliveryNumber = forms.CharField()
    deliveryDateTime = forms.DateTimeField(required=False, input_formats=['%Y%m%d %H%M%S'])


class InvoiceCancelForm(forms.Form):
    invoiceNumber = forms.CharField()
    deliveryNumber = forms.CharField()


class LSPAckForm(forms.Form):
    header = forms.CharField()
    deliveryNumber = forms.CharField()
    trackingNumber = forms.CharField()
    itemState = forms.CharField()
    lspCode = forms.CharField()
    pickupDate = forms.DateField(required=False, input_formats=['%d/%m/%Y'])
    deliveryDate = forms.DateField(required=False, input_formats=['%d/%m/%Y'])
    processingType = forms.CharField(required=False)


class PaymentFilterForm(forms.Form):
    name = forms.CharField(required=False)
    phone = forms.CharField(required=False, validators=[fields.validate_phone])
    email = forms.CharField(required=False, validators=[fields.validate_email])
    order_id = forms.CharField(required=False, label='Order ID')
    transaction_id = forms.CharField(required=False, label='Transaction ID')
    method = forms.ChoiceField(required=False,
        choices=PaymentAttempt.PAYMENT_MODES)
    state = forms.CharField(required=False)
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)

    def __init__(self, *args, **kwargs):
        super(PaymentFilterForm, self).__init__(*args, **kwargs)
        if self.fields['method'].choices[0][0] != '':
            self.fields['method'].choices.insert(0, ('','----'))

    def clean(self):
        if self.cleaned_data.get('order_id') and not CSV_RE.match(self.cleaned_data['order_id']):
            raise forms.ValidationError(u"Please enter valid order ids in CSV format")
        return self.cleaned_data

class RefundFilterForm(forms.Form):
    name = forms.CharField(required=False)
    phone = forms.CharField(required=False, validators=[fields.validate_phone])
    email = forms.CharField(required=False, validators=[fields.validate_email])
    order_id = forms.CharField(required=False, label='Order ID')
    state = forms.ChoiceField(required=False, choices=(
        ('','----'),
        ('open','Open'),
        ('failed','Failed'),
        ('closed','Closed')))
    payment_mode = forms.ChoiceField(required=False,
        choices=PaymentAttempt.PAYMENT_MODES, label='Payment Mode')
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)

    def __init__(self, *args, **kwargs):
        super(RefundFilterForm, self).__init__(*args, **kwargs)
        if self.fields['payment_mode'].choices[0][0] != '':
            self.fields['payment_mode'].choices.insert(0, ('','----'))

    def clean(self):
        if self.cleaned_data.get('order_id') and not CSV_RE.match(self.cleaned_data['order_id']):
            raise forms.ValidationError(u"Please enter valid order ids in CSV format")
        return self.cleaned_data

class ShipmentFilterForm(forms.Form):
    order_id = forms.CharField(required=False, label='Order ID')
    delivery_number = forms.CharField(required=False, label='Delivery Number')
    tracking_number = forms.CharField(required=False, label='AWB Number')
    lsp = forms.ModelChoiceField(required=False, empty_label='----',
        queryset=None, label='LSP')
    invoice_number = forms.CharField(required=False, label='Invoice Number')
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    status = forms.CharField(required=False)

    def __init__(self, *args, **kwargs):
        from fulfillment.models import Lsp
        super(ShipmentFilterForm, self).__init__(*args, **kwargs)
        self.fields['lsp'].queryset = Lsp.objects.all().order_by('name')

    def clean(self):
        if self.cleaned_data.get('order_id') and not CSV_RE.match(self.cleaned_data['order_id']):
            raise forms.ValidationError(u"Please enter valid order ids in CSV format")
        if self.cleaned_data.get('delivery_number') and not CSV_RE.match(self.cleaned_data['delivery_number']):
            raise forms.ValidationError(u"Please enter valid delivery numbers in CSV format")
        if self.cleaned_data.get('invoice_number') and not CSV_RE.match(self.cleaned_data['invoice_number']):
            raise forms.ValidationError(u"Please enter valid invoice numbers in CSV format")
        return self.cleaned_data

class OrderFilterForm(forms.Form):
    name = forms.CharField(required=False)
    phone = forms.CharField(required=False, validators=[fields.validate_phone])
    email = forms.CharField(required=False, validators=[fields.validate_email])
    order_id = forms.CharField(required=False, label='Order ID')
    state = forms.CharField(required=False)
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)

    def clean(self):
        if self.cleaned_data.get('order_id') and not CSV_RE.match(self.cleaned_data['order_id']):
            raise forms.ValidationError(u"Please enter valid order ids in CSV format")
        return self.cleaned_data

class ProcurementFilterForm(forms.Form):
    category = forms.ModelChoiceField(required=False, queryset=None,
        empty_label='----')
    dc = forms.ModelChoiceField(required=False, queryset=None,
        empty_label='----', label='DC')
    state = forms.ChoiceField(required=False, choices=())
    article_id = forms.CharField(required=False, label='Article ID')
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)
    exclude_sto = forms.BooleanField(required=False)

    def __init__(self, *args, **kwargs):
        from accounts.models import Client
        from categories.models import Category
        from fulfillment.models import Dc
        super(ProcurementFilterForm, self).__init__(*args, **kwargs)
        client = Client.objects.get(name='Future Bazaar')
        self.fields['category'].queryset = Category.objects.filter(
            client=client).order_by('name')
        self.fields['dc'].queryset = Dc.objects.filter(client=client
            ).order_by('code')
        self.fields['state'].choices = [
            ('','----'),
            ('no stock','No Stock'),
            ('stock expected','Stock Expected'),
            ('raised po','Raised PO')]

class DispatchFilterForm(forms.Form):
    order_id = forms.CharField(required=False, label='Order ID')
    delivery_number = forms.CharField(required=False, label='Delivery Number')
    invoice_number = forms.CharField(required=False, label='Invoice Number')
    dc = forms.ModelChoiceField(required=False, queryset=None,
        empty_label='----', label='DC')
    lsp = forms.ModelChoiceField(required=False, queryset=None,
        empty_label='----', label='LSP')
    state = forms.ChoiceField(required=False, choices=())
    start_date = forms.DateField(required=False)
    end_date = forms.DateField(required=False)

    def __init__(self, *args, **kwargs):
        from accounts.models import Client
        from fulfillment.models import Dc, Lsp
        super(DispatchFilterForm, self).__init__(*args, **kwargs)
        client = Client.objects.get(name='Future Bazaar')
        self.fields['dc'].queryset = Dc.objects.filter(client=client
            ).order_by('code')
        self.fields['lsp'].queryset = Lsp.objects.all().order_by('name')
        self.fields['state'].choices = [
            ('','----'),
            ('delivery created','Delivery Created'),
            ('invoiced','Invoiced')]

class BulkUploadForm(forms.Form):
    uploaded_file = forms.FileField(required=True)
    
    def clean(self):
        import os
        uploaded_file = self.cleaned_data['uploaded_file']
        extension = os.path.splitext(uploaded_file.name)[1].lower()
        if not (extension in ['.xls',]):
            raise forms.ValidationError(u'%s is not a valid excel file. Please \
                make sure your input file is an excel file (.xlsx format is NOT supported)' % extension)
        return self.cleaned_data

class BulkPaymentForm(forms.Form):
    order_id = forms.CharField()
    payment_mode = forms.CharField()
    txn_id = forms.CharField()
    txn_date = forms.DateField(input_formats=['%d-%m-%Y'])
    notes= forms.CharField(required=False)
    date = forms.DateField(input_formats=['%d-%m-%Y'])
    amount = forms.DecimalField()
    state = forms.CharField()
    bank = forms.CharField()

class PaymentChangeForm(forms.Form):
    payment_mode = forms.ChoiceField(label='Payment Mode',
        choices=PaymentAttempt.PAYMENT_MODES_FOR_SUPPORT)
    gateway = forms.ChoiceField(label='Partner', choices=(('SUVI','Suvidha'),
        ('ICCA','ICICI Cash'),('EBIL','EasyBill'),('ITZC','Itz Cash')))
    amount = forms.DecimalField(label='Payment Amount')
    bank = forms.ChoiceField(required=False, label='EMI Plan', choices=(
        ('HDFC','HDFC - No EMI'),
        ('HDF3','HDFC - 3 Months'),
        ('HDF6','HDFC - 6 Months'),
        ('HDF9','HDFC - 9 Months'),
        ('ICIC','ICICI - No EMI'),
        ('ICI3','ICICI - 3 Months'),
        ('ICI6','ICICI - 6 Months'),
        ('ICI9','ICICI - 9 Months')))
    reject = forms.BooleanField(required=False, label='Reject existing payments')

    def clean(self):
        if not self.cleaned_data.get('amount'):
            raise forms.ValidationError(u"Please enter amount")
        return self.cleaned_data

