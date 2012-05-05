import logging
import re
from django.conf import settings
from django.contrib import auth
from accounts.models import Account, ClientDomain
from django.http import HttpResponse, HttpResponseRedirect,HttpResponsePermanentRedirect, Http404

log = logging.getLogger('request')
# Logger to log unhandled exceptions
uhrlog = logging.getLogger('uhrerror')

class FilterMiddleware:
    
    def process_request(self, request):
        filters = {}
        if request.COOKIES:
            if 'currency' in request.COOKIES:
                currency = request.COOKIES.get('currency','inr')
                if currency == 'usd':
                    filters['currency'] = 'usd'
                if currency == 'inr':
                    filters['currency'] = 'inr'
        request.filters = filters
        return None


class ClientMiddleWare:
    def convert_stg_dev_domains(self, domain):
        # Strip dev, stg things from domain to avoid people
        # polluting domains table
        if domain.startswith('div.'):
            domain = domain.replace('dev.', 'www.')
        if domain.startswith('stg.'):
            domain = domain.replace('stg.', 'www.')
        if domain.startswith('dev'):
            domain = domain.replace('dev','')
        if domain.startswith('stg'):
            domain = domain.replace('stg','')
        if domain.startswith('beta.'):
            domain = domain.replace('beta.', 'www.')
        if domain.startswith('beta'):
            domain = domain.replace('beta','')
        return domain

    def process_request(self, request):
        domain = request.META['HTTP_HOST']
        domain = domain.split(':')[0] # Skip port number
        #domain = self.convert_stg_dev_domains(domain)
        client = None
        if domain:
            try:
                client = ClientDomain.objects.select_related('client').get(
                domain=domain)
                request.client = client
            except ClientDomain.DoesNotExist:
                pass
        if not client and not request.path.startswith('/admin/'):
            # We are not able to find a client. Cannot serve request.
            # We send a HTTP GONE response.
            return HttpResponse("Cannot find requested page", 410)
        if client:
            # If we find a client, lets pre fetch price lists to optimize
            client.pre_fetch_price_lists()
            client.client.pre_fetch_price_lists()
        return None
                

class URLRestrictMiddleWare:

    def process_response(self, request, response):
        referer = request.META.get('HTTP_REFERER', None)
        path = request.path
        https_urls = ['/orders/payment', '/orders/RMSID_sendData/', '/media/', '/orders/get_payment_page',
        '/orders/validate_billing_info_form', '/orders/cod', '/orders/get_emi_options', '/orders/process']
        required_https = False
        for url in https_urls:
            if path.startswith(url):
                required_https = True
                break
        if referer and not required_https:
            if referer.startswith('https'):
                if 'orders/payment' in referer and 'orders/mycart' in path:
                    pass
                else:
                    log.info("Redirecting non-https url to http - Referer - %s - %s" % (referer, path))
                    return HttpResponseRedirect(request.build_absolute_uri())
        return response

class ExceptionMiddleWare:

    def is_real_exception(self, request, exception):
        # Real errors are non bot errors for now
        if request.method == 'POST':
            # Any post is real error
            return True
        ua = request.META.get('HTTP_USER_AGENT','').lower()
        if 'bot' in ua:
            return False
        if 'baidu' in ua:
            return False
        if 'majestic' in ua:
            return False
        return True

    def process_exception(self,request,exception):
        if self.is_real_exception(request, exception):
            try:
                if not isinstance(exception, Http404):
                    uhrlog.exception('Unhandled error at %s: %s: %s' % (request.get_full_path(),
                        request.POST,
                        request.META))
            except:
                pass
            # Dump order related errors into RMS
            if request.path.startswith('/orders'):
                try:
                    if request.user.is_authenticated:
                        from users.models import Phone, Profile
                        from rms.models import Response, Campaign
                        from rms import views as rms_views
                        from utils.utils import get_user_profile
                        profile = None
                        if request.user.is_authenticated():
                            profile = get_user_profile(request.user)
                        phones = Phone.objects.filter(user=profile)[:1]
                        if phones:
                            campaigns = Campaign.objects.filter(name='Web Errors',
                                client = request.client.client)[:1]
                            if campaigns:
                                response = rms_views.get_or_create_response(
                                    campaigns[0],
                                    phone = phones[0],
                                    dni = None,
                                    phone_number = None,
                                    type = 'outbound')
                except:
                    pass
        else:
            return HttpResponse("")

class FacebookAutoMiddleware:

    def process_request(self, request):
        check_facebook_auth = False
        if request.user.is_authenticated():
            check_facebook_auth = False
        else:
            check_facebook_auth = True
        if check_facebook_auth:
            try:
                # Not logged through facebook. Let us check if he should be
                user = auth.authenticate(request=request)
                if user:
                    username = user.atg_username
                    # Complete the login
                    from web.views import user_views 
                    user_views.login_from_facebook(request, user, username)
            except Exception, e:
                log.exception(
                    'Error auto login of facebook user %s' % repr(e))
        return None
