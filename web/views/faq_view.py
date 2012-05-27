from datetime import datetime
import hashlib
import logging

from django.conf import settings
from django.contrib.auth.models import User
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect, Http404
from django.template import RequestContext

from django.utils.safestring import mark_safe
from django.shortcuts import render_to_response, get_object_or_404
from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.contrib.auth.decorators import user_passes_test
from django.core.mail import send_mail
from django.core import serializers
from django.forms.models import modelformset_factory
from django.forms.formsets import formset_factory
from django.contrib.auth import authenticate, login
from django.utils import simplejson
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.core.urlresolvers import reverse
from accounts.models import Account
from web.sbf_forms import SearchForm, FilterForm, SortForm
from catalog.models import *
from categories.models import *
from django.views.generic.list_detail import object_list
from utils.solrutils import *
from utils.utils import *
from lists.models import *
import solr
import re
import math

log = logging.getLogger('request')
search_log = logging.getLogger('search')


def faq_page(request):
    html_page = 'pages/faq'+request.path+'.html'
    return render_to_response(html_page, None, context_instance = RequestContext(request))
