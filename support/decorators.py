from django.shortcuts import render_to_response
from django.template import RequestContext

def check_role(roles):
    def decorator(view_func):
        def check(request, *args, **kwargs):
            if ('role' in request.session) and \
                ((request.session['role'] == 'Support Admin') or (request.session['role'] in roles)):
                return view_func(request, *args, **kwargs)
            resp = render_to_response('support/403.html', context_instance=RequestContext(request))
            resp.status_code = 403
            return resp
        return check
    return decorator

