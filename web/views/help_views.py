# Create your views here.
import logging
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect
from django.template import RequestContext

from django.utils.safestring import mark_safe
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.core import serializers
from django.contrib.auth import authenticate, login
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from help.models import *

log = logging.getLogger('request')

def show_help(request, slug):
    try:
        help = Help.objects.get(slug=slug)
    except Help.DoesNotExist:
        help = None
    format = request.GET.get('f','')
    if format:
        format = '-%s' % format
    return render_to_response("help/help%s.html" % format,
            {"help":help},
            context_instance = RequestContext(request))
