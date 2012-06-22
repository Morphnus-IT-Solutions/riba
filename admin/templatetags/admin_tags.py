from django import template
from django.core.cache import cache
from django.db.models import Q
from django.template.loader import render_to_string

import re, time
from datetime import datetime, timedelta
from users.models import NewsLetter
from decimal import Decimal
from web import search_form_default
from django.core.cache import cache

register = template.Library()

import logging
from django.conf import settings


def render_header(request):
    return dict(request = request)
register.inclusion_tag('riba-admin/header.html')(render_header)
