from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse
from utils import utils
def handle505(request, *args, **kwargs):
    return render_to_response("500.html", None, context_instance=RequestContext(request))

def handle404(request, *args, **kwargs):
    if utils.is_platform(request):
        return render_to_response("ppd/404.html", None, context_instance=RequestContext(request))
    return render_to_response("404.html", None, context_instance=RequestContext(request))
