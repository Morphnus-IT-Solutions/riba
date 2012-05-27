from rms.models import Campaign, Response, Interaction
from operator import itemgetter
from django import template
import re
from django.db.models import Count
from django.utils.html import conditional_escape
from django.utils.encoding import force_unicode
from django.utils.safestring import mark_safe
import django.forms
import datetime
from ccm.models import Agent
from django.db.models import Q 

register = template.Library()

@register.inclusion_tag('rms/top_nav.html')
def top_nav(request):
    menu_items = []
    if (request.session['role'] == 'CallCenter') or (request.session['role'] == 'CC Manager'):
        menu_items.append({'name':'Home Stream', 'url':'/agent/',})
    menu_items.append({'name':'Campaigns', 'url':'/campaign/',})
    if (request.session['role'] == 'RMS Admin') or (request.session['role'] == 'CC Manager'):
        menu_items.append({'name':'Backlogs', 'url':'/backlog/',})
    if request.session['role'] == 'RMS Admin':
        if request.session['agent']:
            menu_items.append({'name':'Home Stream', 'url':'/agent/',})
        menu_items.append({'name':'Users', 'url':'/user/',})
    for item in menu_items:
        item['selected'] = request.path.startswith(item['url'])
    return dict(menu_items=menu_items)

def rms_daterange(search_trend, start_date, end_date, request,args=None):
    url = request.path
    url += '?'
    return dict(search_trend=search_trend, start_date=start_date, end_date=end_date, request=request, url=url, args=args)
register.inclusion_tag('rms/daterange.html')(rms_daterange)

class _PseudoCheckboxBoundField(object):
    """An object from which to render one checkbox.

    Helper class.

    Because the checkbox iterator needs to be able return something
    that acts, closely enough, like a checkbox bound field.
    """
    def __init__(self, name, option_label, option_value, attrs, checked):
        self.parent_name = name
        self.name = option_label
        self.value = option_value
        self.attrs = attrs
        self.checked = checked
        self.id = attrs.get('id', '')
        self.errors = u'' # We don't have individual cb errors

    def tag(self):
        cb = django.forms.CheckboxInput(self.attrs,
                                        check_test=lambda v: self.checked)
        return cb.render(self.parent_name, self.value)

    def label_head(self):
        id = self.id
        if not id:
            return u'<label>'
        return mark_safe(u'<label for="%s">' % id)

    def labeled(self):
        return mark_safe(u'%s%s %s</label>' % (
            self.label_head(),
            self.tag(),
            self.name
            ))

    def lone_label(self):
        return mark_safe(u'%s%s</label>' % (
            self.label_head(),
            self.name
            ))

    def __unicode__(self):
        return self.labeled()

class _ValueGrabber(object):
    """A pseudo widget to capture information from the MultiSelect object.

    This is a helper class.

    There's no clean way to reach into the MultiSelect bound field to
    get this information, but it does call its widget with all the
    necessary info.  This probably has legs because changing the
    render interface would have far reaching consequences.
    """
    def __init__(self):
        self.attrs = {}

    def render(self, name, data, attrs):
        self.name = name
        self.data = data
        self.attrs = attrs

@register.filter
def checkboxiterator(bound_field):
    """Filter the bound field of a multi-select into an iterator of checkboxes.

    Passing the multiselect into the filter gives us access to the bound
    field here.

    We then actually behave as a generator of _PseudoCheckboxBoundField
    objects, which is iterable.
    """
    widget = bound_field.field.widget
    # Snag the bound field details.  Let it's as_widget method do the work.
    bfd = _ValueGrabber()
    bound_field.as_widget(bfd)
    name = bfd.name
    values = bfd.data
    attrs = bfd.attrs

    # Fix up data and attrs
    if values is None:
        values = set()
    else:
        values = set([force_unicode(v) for v in values])
    id = attrs and attrs.get('id', False)
    partial_attrs = widget.build_attrs(attrs, name=name)

    for i, (option_value, option_label) in enumerate(widget.choices):
        option_value = force_unicode(option_value)
        final_attrs = partial_attrs
        if id is not False:
            final_attrs = dict(partial_attrs,
                               id=u'%s_%s' % (id, i))
        yield _PseudoCheckboxBoundField(
            name,
            conditional_escape(force_unicode(option_label)),
            option_value,
            final_attrs,
            option_value in values)

@register.inclusion_tag('rms/agents.html')
def agent_list(agents, grouping, type):
    agents = checkboxiterator(agents)
    agent_groups, group, count = [], [], []
    i, j = 0, 0
    for checkbox in agents:
        group.append(checkbox)
        i += 1
        if i == grouping[j]['number']:
            agent_groups.append((grouping[j]['report_to__name'],group))
            i = 0
            j += 1
            group = []
    return dict(groups=agent_groups,type=type)

@register.simple_tag
def pending_followups(request, agent=None, campaign=None):
    if not agent:
        return None
    else:
        timenow = datetime.datetime.now()
        followup_time = timenow - datetime.timedelta(minutes=-30)
        if campaign:
            followups = Response.objects.filter(campaign=campaign, is_closed=False, assigned_to=agent, followup_on__lt=followup_time).count()
        else:
            followups = Response.objects.filter(is_closed=False, assigned_to=agent, followup_on__lt=followup_time).count()
        return followups
