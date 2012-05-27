import logging
import re
from accounts.models import Account
from django.core.cache import cache
from django.conf import settings
from django.utils.cache import patch_vary_headers

request_log = logging.getLogger('request')
call_token_re = re.compile('[0-9.-]+')

class CallMiddleware:
    
    def process_request(self, request):
        # call token
        # cli-dni-type-uniqueid-response_id
        request.is_auth = False
        from utils.utils import is_cc, is_cs, is_support
        starts_with = request.path.split("/")[1]

        if (is_cc(request) or is_cs(request) or is_support(request)) and not starts_with in ['media', 'admin']:
            # decorate request with call info
            path_tokens = request.path.split('/')
            length = len(path_tokens)
            cli = None
            dni = None
            type = None
            uniqueid = None
            response_id = None
            agent = None
            url_token = None
            #exclusive_seller = None
            if path_tokens and length > 1:
                call_token = path_tokens[1]
                if call_token_re.match(call_token):
                    # cli-dni-type-uniqueid-response_id
                    url_token = path_tokens[1]
                    call_tokens = call_token.split('-')
                    call_tokens_length = len(call_tokens)
                    if call_tokens_length >= 5:
                        response_id = call_tokens[4]
                    if call_tokens_length >= 4:
                        uniqueid = call_tokens[3]
                    if call_tokens_length >= 3:
                        type = call_tokens[2]
                    if call_tokens_length >= 2:
                        dni = call_tokens[1]
                    if call_tokens_length >= 1:
                        cli = call_tokens[0][-10:]

            if request.user and request.user.is_authenticated():
                agent = request.user.username
            call = {'id':uniqueid, 'agent':agent, 'dni':dni, 'type':type, 'attempt_id':None,
                    'response_id':response_id, 'cli': cli, 'url_token': url_token}
            if not call.get('incoming_call',''):
                call['incoming_call'] = cli
            request.call = call
			# is_auth flag bifurcates between admin and normal interface in callcenter and store for holii and chaupaati
            if request.path.startswith('/orders/auth/') or request.path.startswith('/orders/cancel/'):
                request.is_auth = True
        return None
