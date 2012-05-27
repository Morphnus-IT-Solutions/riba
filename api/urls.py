from django.conf.urls.defaults import *
import bl.api
urlpatterns = patterns('',
    (r'response/call/(?P<response_id>\d+)', 'api.views.call_response'),
    (r'call/close', 'api.views.close_inbound_call'),
    (r'attempt/(?P<attempt_id>\d+)/update', 'api.views.update_attempt'),
    (r'attempt/(?P<attempt_id>\d+)', 'api.views.attempt_detail'),
    (r'event/order_confirmed_get', 'api.views.order_confirmed_get'),
    (r'event/order_confirmed', 'api.views.order_confirmed'),
    (r'response/add_or_get', 'api.views.get_or_create_response'),
    (r'response/add', 'api.views.add_response'),
)
