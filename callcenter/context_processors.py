from django.conf import settings

def call(request):
    call = getattr(request, 'call', None)
    return dict(request_call=call)

def conf(request):
    conf = {'DEBUG': settings.DEBUG, 'MEDIA_PREFIX': settings.MEDIA_PREFIX}
    return dict(conf=conf)
