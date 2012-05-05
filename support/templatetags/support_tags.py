from django import template
from django import forms
from datetime import datetime, timedelta
import logging

fb_log = logging.getLogger('fborder')
register = template.Library()

@register.inclusion_tag('support/top_nav.html')
def top_nav(request):
    menu_items = []
    #if (request.session['role'] == 'CallCenter') or (request.session['role'] == 'CC Manager'):
    #    menu_items.append({'name':'Home Stream', 'url':'/agent/',})
    #menu_items.append({'name':'Teams', 'url':'/team/',})
    order_dict = {'name':'Orders', 'url':'order/',}
    order_sub_menu = [
	    {'name':'Upload Orders', 'url':'order/upload/',},]
    order_dict['sub_menu'] = order_sub_menu
    menu_items.append(order_dict)
    menu_items.append({'name':'Payments', 'url':'payment/', 'sub_menu':[]})
    menu_items.append({'name':'Shipments', 'url':'shipment/', 'sub_menu':[]})
    menu_items.append({'name':'Refunds', 'url':'refund/', 'sub_menu':[]})
    menu_items.append({'name':'Fulfillment', 'url':'fulfillment/dashboard/', 'sub_menu':[]})
    menu_items.append({'name':'Complaints', 'url':'complaint/', 'sub_menu':[]})
    #if request.session['role'] == 'RMS Admin':
    #    if request.session['agent']:
    #        menu_items.append({'name':'Home Stream', 'url':'/agent/',})
    #    menu_items.append({'name':'Users', 'url':'/user/',})
    for item in menu_items:
        if hasattr(request, 'call') and request.call.get('cli'):
            t = request.path.split('/',2)
            path = t[2]
        else:
            t = request.path.split('/',1)
            path = t[1]
        item['selected'] = path.startswith(item['url'])
    return dict(menu_items=menu_items, request=request)

@register.simple_tag
def choicefield(type, entity, action_flows, name):
    if not (entity and action_flows):
        return ''
    id, choices = None, None
    choices = action_flows.get(entity.status, [])
    id = '%s_%s' % (type, entity.id)
    filtered_choices = []
    if type == 'payment':
        group = entity.get_payment_group()
        for choice in choices:
            if choice[2] == group:
                filtered_choices.append((choice[0], choice[1]))
    else:
        filtered_choices = [(c[0],c[1]) for c in choices]
    if filtered_choices:
        field = forms.ChoiceField(required=False, choices=filtered_choices)
        field.choices.insert(0, ('','----'))
        html = field.widget.render(name,None,{'id':''})
        html += ("<input type='submit' class='apply_action' id='"+id+"' value='Apply' />")
        return html
    else:
        return ''

def support_daterange(request, limit_from, limit_to):
    return dict(start_date=request.GET.get('start_date'), end_date=request.GET.get('end_date'),
        limit_from=limit_from, limit_to=limit_to)
register.inclusion_tag('support/daterange.html')(support_daterange)


@register.simple_tag
def rag(d):
    if not d:
        return ''
    d = d.replace(tzinfo=None)
    n = datetime.now()
    if d <= n:
        return 'rag_red'
    days_left = (d - n).days
    if days_left <= 2:
        return 'rag_amber'
    return ''
