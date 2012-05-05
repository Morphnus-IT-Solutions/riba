from django.shortcuts import render_to_response
from django.template import RequestContext

def check_role(roles):
    def decorator(view_func):
        def check(request, *args, **kwargs):
            if (request.session['role'] == 'Sellers Admin') or (roles in request.session['tabs']):
                return view_func(request, *args, **kwargs)
            else:
                resp = render_to_response('ppd/403.html', context_instance=RequestContext(request))
                resp.status_code = 403
                return resp
        return check
    return decorator

