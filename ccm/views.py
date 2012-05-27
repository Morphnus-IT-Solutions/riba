# Create your views here.
from django.shortcuts import render_to_response
from django.template import RequestContext 

def dashboard(request, *args, **kwargs):
    return render_to_response('ccm/dashboard.html',
            {},
            context_instance=RequestContext(request))
