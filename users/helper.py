from utils import utils

def get_eligible_user(request):
    type = None
    if utils.is_cc(request):
        source = 'cc'
        callId = request.call['id']
        if callId in request.session:
            user = request.session[callId]['user']
        else:
            user = None
    else:
        source = 'web'
        user = None
        type = None
        if request.user.is_authenticated():
            user = request.user
            type = 'loggedin'
        else:
            if 'guest_user' in request.session:
                user = request.session['guest_user'].user
                type = 'guest_user'
    return source,user, type

def set_eligible_user(request,profile,type):
    if type == 'guest':
        if 'user' in request.session:
            del request.session['user']
        request.session['guest_user'] = profile
    else:
        if 'guest_user' in request.session:
            del request.session['guest_user']
        request.session['user'] = profile

def get_orderid_by_user(request,source,user):
    if source == 'cc':
        callId = request.call['id']
        ccSession = request.session.get(callId,None)
        if ccSession:
            return ccSession.get('orderId',None)
        else:
            return None
    elif source == 'web':
        if user:
            return request.session.get('orderId',None)
        else:
            return request.COOKIES.get('orderId',None)
    

def set_orderid_by_user(request,response,source,user,orderId):
    if source == 'cc':
        callId = request.call['id']
        if callId in request.session:
            ccSession = request.session[callId]
            if orderId:
                ccSession['orderId'] = orderId
            request.session[callId] = ccSession
    elif source == 'web':
        if user:
            if 'orderId' in request.COOKIES:
                response.delete_cookie('orderId')
            request.session['orderId'] = orderId
        else:
            response.set_cookie('orderId', orderId)
    return response

def get_call_user_or_signed_in_user(request):
    if utils.is_cc(request):
        return request.call['id']
    if request.user.is_authenticated():
        return request.user
    return None


def cc_login_required(default_handler, redirect_to=None):
    def wrap(f):
        redirect_to_page = redirect_to
        def wrapped_f(request, *args, **kwargs):
            if request.is_auth:
                return f(request, *args, **kwargs)
            if utils.is_cc(request):
                if hasattr(request,'call'):
                    if request.call.get('id', None):
                        return f(request, *args, **kwargs)
            else:
                return f(request, *args, **kwargs)
            return default_handler(request, redirect_to_page, *args, **kwargs)
        return wrapped_f
    return wrap
