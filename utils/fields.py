import re, datetime
from django import forms
from django.core.validators import validate_email,EMPTY_VALUES
from django.db import models
from django.db.models.fields import CharField,TextField
from django.core.exceptions import ValidationError
#from south.modelsinspector import add_introspection_rules
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

email_separator_re = re.compile(r'[^\w\.\-\+@_]+')
phone_regex = re.compile(r'^\d{10}$')
email_regex = re.compile(r'^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,4}$')
pincode_regex = re.compile(r'^\d{6}$')

class MultiEmailFeild(CharField):
    widget = forms.Textarea

    def to_python(self, value):
        "Normalize data to list of strings"
        if not value:
            return []
        return email_separator_re.split(value)

    def validate(self, value):
        "Check if the value consists only of valid emails"

        # Use parent's handling of required fields, etc
        super(MultiEmailFeild, self).validate(value)

        for email in value:
            validate_email(email)

class PhoneNumberField(CharField):

    def to_python(self, value):
        if not value:
            return ''

    def validate(self, value):
        # Use parent's handling of required fields, etc
        super(PhoneNumberField, self).validate(value)
        if not phone_regex.match(value):
            raise ValidationError('Invalid phone number', code='invalid')

class CommaSeparatedCharField(CharField):

    def to_python(self,value):
        if value in EMPTY_VALUES:
            return u''
        csv = smart_unicode(','.join(value))
        return csv

class NewLineSeperatedTextField(TextField):

    def to_python(self, value):
        if not value:
            return []
        return value.split('\n')

def validate_phone(value):
    if not phone_regex.match(value):
        raise ValidationError(u'Enter a valid 10-digit phone number.', code='invalid')

def validate_pincode(value):
    if not pincode_regex.match(value):
        raise ValidationError(u'Enter a valid pincode number.', code='invalid')

def validate_password(value):
    if len(value) < 4:
        raise ValidationError(message='Enter a valid Password of Minimum 4 characters.', code='invalid')

SECS_PER_DAY=3600*24
class TimeDeltaField(models.Field):
    u'''
    Store Python's datetime.timedelta in an integer column.
    Most databasesystems only support 32 Bit integers by default.
    '''
    __metaclass__=models.SubfieldBase
    def __init__(self, *args, **kwargs):
        super(TimeDeltaField, self).__init__(*args, **kwargs)

    def to_python(self, value):
        if (value is None) or isinstance(value, datetime.timedelta):
            return value
        assert isinstance(value, long), (value, type(value))
        return datetime.timedelta(seconds=value)

    def get_internal_type(self):
        return 'IntegerField'

    def get_db_prep_lookup(self, lookup_type, value, connection=None, prepared=False):
        raise NotImplementedError()  # SQL WHERE

    def get_db_prep_save(self, value, connection=None, prepared=False):
        if (value is None) or isinstance(value, long):
            return value
        return SECS_PER_DAY*value.days+value.seconds

    def formfield(self, *args, **kwargs):
        defaults={'form_class': TimeDeltaFormField}
        defaults.update(kwargs)
        return super(TimeDeltaField, self).formfield(*args, **defaults)

    def value_to_string(self, obj):
        value = self._get_val_from_obj(obj)
        return self.get_db_prep_value(value)

class TimeDeltaFormField(forms.Field):
    default_error_messages = {
        'invalid':  _(u'Enter a whole number.'),
        }

    def __init__(self, *args, **kwargs):
        defaults={'widget': TimeDeltaWidget}
        defaults.update(kwargs)
        super(TimeDeltaFormField, self).__init__(*args, **defaults)

    def clean(self, value):
        # value comes from Timedelta.Widget.value_from_datadict(): tuple of strings
        super(TimeDeltaFormField, self).clean(value)
        assert len(value)==len(self.widget.inputs), (value, self.widget.inputs)
        i=0
        for value, multiply in zip(value, self.widget.multiply):
            try:
                i+=long(value)*multiply
            except ValueError, TypeError:
                raise forms.ValidationError(self.error_messages['invalid'])
        return i

class TimeDeltaWidget(forms.Widget):
    INPUTS=['days', 'hours', 'minutes', 'seconds']
    MULTIPLY=[60*60*24, 60*60, 60, 1]
    def __init__(self, attrs=None):
        self.widgets=[]
        if not attrs:
            attrs={}
        inputs=attrs.get('inputs', self.INPUTS)
        multiply=[]
        for input in inputs:
            assert input in self.INPUTS, (input, self.INPUT)
            self.widgets.append(forms.TextInput(attrs=attrs))
            multiply.append(self.MULTIPLY[self.INPUTS.index(input)])
        self.inputs=inputs
        self.multiply=multiply
        super(TimeDeltaWidget, self).__init__(attrs)

    def render(self, name, value, attrs):
        if value is None:
            values=[0 for i in self.inputs]
        elif isinstance(value, datetime.timedelta):
            values=split_seconds(value.days*SECS_PER_DAY+value.seconds, self.inputs, self.multiply)
        elif isinstance(value, long):
            # initial data from model
            values=split_seconds(value, self.inputs, self.multiply)
        else:
            assert isinstance(value, tuple), (value, type(value))
            assert len(value)==len(self.inputs), (value, self.inputs)
            values=value
        id=attrs.pop('id')
        assert not attrs, attrs
        rendered=[]
        for input, widget, val in zip(self.inputs, self.widgets, values):
            rendered.append(u'%s %s' % (_(input), widget.render('%s_%s' % (name, input), val)))
        return mark_safe('<div id="%s">%s</div>' % (id, ' '.join(rendered)))

    def value_from_datadict(self, data, files, name):
        # Don't throw ValidationError here, just return a tuple of strings.
        ret=[]
        for input, multi in zip(self.inputs, self.multiply):
            ret.append(data.get('%s_%s' % (name, input), 0))
        return tuple(ret)

    def _has_changed(self, initial_value, data_value):
        # data_value comes from value_from_datadict(): A tuple of strings.
        if initial_value is None:
            return bool(set(data_value)!=set([u'0']))
        assert isinstance(initial_value, datetime.timedelta), initial_value
        initial=tuple([unicode(i) for i in split_seconds(initial_value.days*SECS_PER_DAY+initial_value.seconds, self.inputs, self.multiply)])
        assert len(initial)==len(data_value), (initial, data_value)
        return bool(initial!=data_value)

def split_seconds(secs, inputs=TimeDeltaWidget.INPUTS, multiply=TimeDeltaWidget.MULTIPLY,
                  with_unit=False, remove_leading_zeros=False):
    ret=[]
    assert len(inputs)<=len(multiply), (inputs, multiply)
    for input, multi in zip(inputs, multiply):
        count, secs = divmod(secs, multi)
        if remove_leading_zeros and not ret and not count:
            continue
        if with_unit:
            ret.append('%s%s' % (count, input))
        else:
            ret.append(count)
    return ret

#add_introspection_rules([], ["^utils\.fields\.TimeDeltaField"])

