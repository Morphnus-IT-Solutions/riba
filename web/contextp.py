from django.conf import settings
from lists.models import List
from datetime import datetime

def user(request):
    if 'guest_user' in request.session:
        user = request.session['guest_user']
    elif 'user' in request.session:
        user = request.session['user']
    else:
        user = None
    return {'logged_user':user}

def facebookid(request):
    facebookid = ''
    if 'facebookid' in request.session:
        facebookid = request.session['facebookid']
    return {'facebookid':facebookid}

def app_settings(request):
   ctxt = {}
   #ctxt['facebook_app_id'] = settings.FACEBOOK_APPLICATION_ID
   ctxt['DONT_SHOW_GOOGLE_ANALYTICS'] = settings.DONT_SHOW_GOOGLE_ANALYTICS
   return {'app_settings' : ctxt}

def media(request):
    url = settings.MEDIA_URL
    is_https = 'HTTPS' in request.META['SERVER_PROTOCOL']
    if is_https:
        url = url.replace('http://','https://')
    return {'MEDIA_URL': url}

def is_friday_deals(request):
    return {'is_friday_deals': List.objects.filter(type="friday_deal", starts_on__lte=datetime.now,
            ends_on__gte=datetime.now).order_by('-id').exists()}
