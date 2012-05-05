from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('support.views',
    #Search
    url(r'^search/suggest/', 'suggest'),
    url(r'^search/', 'search'),
    #Orders
    url(r'^order/(?P<order_id>\d+)/$', 'order_detail'),
    #url(r'^order/(?P<order_id>\d+)/shipping/$', 'order_shipping'),
    #url(r'^order/(?P<order_id>\d+)/payment/$', 'order_payment'),
    url(r'^order/(?P<order_id>\d+)/modify/$', 'order_modify'),
    url(r'^order/(?P<order_id>\d+)/cancel/$', 'order_cancel'),
    url(r'^order/(?P<order_id>\d+)/change_payment/$', 'order_change_payment'),
    url(r'^order/upload/$', 'order_upload'),
    url(r'^order/$', 'order_list'),
    
    url(r'^fulfillment/procurement/$', 'procurement_list'),
    url(r'^fulfillment/procurement/(?P<item_id>\d+)/form/$', 'procurement_form'),
    url(r'^fulfillment/dispatch/$', 'dispatch_list'),
    url(r'^fulfillment/dashboard/', 'fulfillment_dashboard'),
    url(r'^fulfillment/$', 'fulfillment_home'),
   
    #OrderItems
    url(r'^orderitem/(?P<item_id>\d+)/form/$', 'order_item_form'),

    #Shipments
    url(r'^shipment/$', 'shipment_list'),

    #Payments
    url(r'^payment/(?P<payment_id>\d+)/form/$', 'payment_form'),
    url(r'^payment/$', 'payment_list'),
    
    #Refunds
    url(r'^refund/(?P<refund_id>\d+)/form/$', 'refund_form'),
    url(r'^refund/$', 'refund_list'),

    #complaints
    url(r'^complaint/add_complaint/$','add_complaint'),
    url(r'^complaint/update_complaint/$','update_complaint'),
    url(r'^complaint/$','complaint_list'),

    #Teams
    url(r'^team/(?P<team_id>\d+)/edit/$', 'team_edit', name='support_edit_team'),
    url(r'^team/(?P<team_id>\d+)/$', 'team', name='support_team'),
    url(r'^team/add/$', 'team_add', name='support_add_team'),
    url(r'^team/$', 'team', name='support_team_list'),

    #Users
    url(r'^user/(?P<user_id>\d+)/edit/$', 'user_edit', name='support_edit_user'),
    url(r'^user/(?P<user_id>\d+)/$', 'user', name='support_user'),
    url(r'^user/add/$', 'user_add', name='support_add_user'),
    url(r'^user/$', 'user', name='support_user_list'),

    #States
    url(r'^state/(?P<state_id>\d+)/edit/$', 'state_edit', name='support_edit_state'),
    url(r'^state/(?P<state_id>\d+)/$', 'state', name='support_state'),
    url(r'^state/add/$', 'state_add', name='support_add_state'),
    url(r'^state/$', 'state', name='support_state_list'),

    #Substates
    url(r'^substate/(?P<substate_id>\d+)/edit/$', 'substate_edit', name='support_edit_substate'),
    url(r'^substate/(?P<substate_id>\d+)/$', 'substate', name='support_substate'),
    url(r'^substate/add/$', 'substate_add', name='support_add_substate'),
    url(r'^substate/$', 'substate', name='support_substate_list'),

    #Actions
    url(r'^actionflow/(?P<flow_id>\d+)/edit/$', 'actionflow_edit', name='support_edit_actionflow'),
    url(r'^actionflow/(?P<flow_id>\d+)/$', 'actionflow', name='support_actionflow'),
    url(r'^actionflow/add/$', 'actionflow_add', name='support_add_actionflow'),
    url(r'^actionflow/$', 'actionflow', name='support_actionflow_list'),

    #Information
    url(r'^informationflow/(?P<flow_id>\d+)/edit/$', 'informationflow_edit', name='support_edit_informationflow'),
    url(r'^informationflow/(?P<flow_id>\d+)/$', 'informationflow', name='support_informationflow'),
    url(r'^informationflow/add/$', 'informationflow_add', name='support_add_informationflow'),
    url(r'^informationflow/$', 'informationflow', name='support_informationflow_list'),
    url(r'^$', 'homepage_redirect', name='homepage'),

    #URLs to receive post data from JAPS (to process SAP acks)
    url(r'^order_ack', 'order_ack', name='support_order_ack'),
    url(r'^can_ack/$', 'order_ack', name='support_order_cancel_ack'),
    url(r'^mod_ack/$', 'order_ack', name='support_order_modify_ack'),
    url(r'^ret_ack/$', 'return_order_ack', name='support_return_order_ack'),
    url(r'^item_ack/$', 'item_ack', name='support_item_ack'),
    url(r'^del_ack/$', 'del_ack', name='support_delivery_ack'),
    url(r'^inv_ack/$', 'invoice_ack', name='support_invoice_ack'),
    url(r'^lsp_ack/$', 'lsp_ack', name='support_lsp_ack'),
    url(r'^inv_print_ack/$', 'inv_print_ack', name='support_inv_print_ack'),
)

urlpatterns += patterns('',
    (r'^accounts/login/$','web.views.home.login',{'template_name':'systems/login.html'}),
    (r'^auth/signout','web.views.user_views.logout'),
    (r'^media/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^sap/update_inventory/', 'sap.views.sap_updates'),
    (r'^user/callclose','rms.views.add_interaction')
)

