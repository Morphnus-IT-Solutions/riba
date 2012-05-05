from activitystream.models import *
from catalog.models import SellerRateChart
from django.shortcuts import render_to_response, get_object_or_404
from django.http import HttpResponse
from django.template import RequestContext
import time

# write_to_as # {{{
def write_to_as(user, aclientdomain, atype, asrc):
    user_str = 'Anonymous'
    if user:
        if hasattr(user, 'full_name'):
            user_str = user.full_name
        else:
            user_str = 'Private user'

    user_str = user_str.strip()
    if not user_str:
        user_str = 'Anonymous'

    if not aclientdomain:
        raise AssertionError("Trying to write activity without domain")
    domain_str = 'on <a href="http://%s">%s</a>' % (aclientdomain, aclientdomain)

    if not atype:
        raise AssertionError("Trying to write activity without type")
    if atype not in ACHOICELIST:
        raise AssertionError("Trying to write activity with invalid type")

    if not asrc and (str(atype) != 'Feedback'):
        raise AssertionError("Trying to write activity without src")
    asrc_str = '<a href="/%s">%s</a>' % (asrc.product.url(), asrc.product.title)

    astream = ''
    if atype == 'Buy':
        astream = '%s bought %s' % (user_str, asrc_str)
    elif atype == 'Like':
        astream = '%s likes %s' % (user_str, asrc_str)
    elif atype == 'Review':
        astream = '%s wrote a review of %s' % (user_str, asrc_str)
    elif atype == 'Rating':
        astream = '%s has rated %s' % (user_str, asrc_str)
    else:
        astream = '%s wrote a feedback' % (user_str)

    act_obj = Activity()
    act_obj.user = user
    act_obj.aclientdomain = aclientdomain
    act_obj.atype = atype
    act_obj.asrc = asrc
    act_obj.astream = astream
    act_obj.atime = int(time.time())
    act_obj.save()
    return astream
# }}}

# write_stream # {{{
def write_stream(request, atype, src_id):
    user = None
    if request.user.is_authenticated():
        user = request.user.get_profile()

    aclientdomain = request.client
    
    asrc = None
    if src_id != 0:
        try:
            asrc = SellerRateChart.objects.get(id=int(src_id))
        except Exception:
            pass
    astream = write_to_as(user, aclientdomain, atype, asrc=asrc)
    return HttpResponse(astream)
# }}}

# read stream # {{{
def read_stream(request):
    act_objs = Activity.objects.filter(aclientdomain=request.client).order_by('-atime')[:10]
    return render_to_response(
        'activitystream/homestream.html', { 'act_objs' : act_objs,'request':request },
        RequestContext(request)
    )
# }}}

#Reads recently bought products
def read_recently_stolen(request):
    act_objs = Activity.objects.filter(aclientdomain=request.client,atype="Buy").order_by('-atime')[:6]
    return render_to_response(
        'web/home/recently_stolen.html', { 'act_objs' : act_objs,'request':request },
        RequestContext(request)
    )
