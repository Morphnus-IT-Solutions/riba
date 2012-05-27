from rms.models import *
from ccm.models import Agent
from rms.views import get_or_create_response, move_response
from orders.signals import pending_order_signal, confirmed_order_signal
import logging

log = logging.getLogger('fborder')

def on_pending_order_created(sender, **kwargs):
    call = kwargs.get('call', None)
    order = kwargs.get('order', None)
    user = kwargs.get('user', None)
    try:
        agent = Agent.objects.get(user=user)
    except Agent.DoesNotExist:
        log.info('RMS: Skipping po signal, no agent found for %s' % user.id)
        return

    if not call or ('.' not in call['id']) or not order:
        log.info('RMS: Skipping po signal, missing call/order call: %s, order: %s' %(call, order))
        return
    
    response_id = call.get('response_id', None)
    if not response_id:
        response = get_or_create_response(dni=call['dni'], phone_number=call['cli'])
        if not response:
            log.info('RMS: Cannot create response - dni: %s, phone: %s. Skipping po signal' % (call['dni'],call['cli']))
            return
        else:
            response_id = response.id
    else:
        try:
            response = Response.objects.select_related('orders').get(pk=int(response_id))
        except Response.DoesNotExist:
            log.info('RMS: No such response %s. Skipping po signal' % response_id)
            return
    
    if order not in response.orders.all():
        response.orders.add(order)
        try:
            funnel_state = response.campaign.funnel.funnel_states.get(name='Pending Order')
            funnel_sub_state = response.campaign.campaign_sub_states.get(name='Awaiting Payment', funnel_state=funnel_state)
            move_response(response=response, state=funnel_state, substate=funnel_sub_state, agent=agent, callid=call['id'])
        except FunnelSubState.DoesNotExist:
            log.info('RMS: No funnel sub state. Skipping po signal')
            return
        except FunnelState.DoesNotExist:
            log.info('RMS: No funnel state. Skipping po signal')
            return

def on_order_confirmed(sender, **kwargs):
    order = kwargs.get('order', None)
    if not order:
        log.info('RMS: Skipping order confirmed signal. No order sent')
        return
    response = order.response.all().order_by('-id')[:1]
    if not response:
        log.info('RMS: Skipping order conf signal. No response for %s' % order.id)
        return
    response = response[0]
    try:
        funnel_state = response.campaign.funnel.funnel_states.get(name='Order')
        if order.booking_agent or order.agent: 
            funnel_sub_state = response.campaign.campaign_sub_states.get(name='Paid - Assisted', funnel_state=funnel_state)
        else:
            funnel_sub_state = response.campaign.campaign_sub_states.get(name='Paid - Direct', funnel_state=funnel_state)
        move_response(response=response, state=funnel_state, substate=funnel_sub_state)
    except FunnelSubState.DoesNotExist:
        log.info('RMS: No funnel sub state. Skipping order confirmed signal')
        return
    except FunnelState.DoesNotExist:
        log.info('RMS: No funnel state. Skipping order confirmed signal')
        return


pending_order_signal.connect(on_pending_order_created, dispatch_uid='pending_order_rms')
confirmed_order_signal.connect(on_order_confirmed, dispatch_uid='confirmed_order_rms')
