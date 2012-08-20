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
        return None
