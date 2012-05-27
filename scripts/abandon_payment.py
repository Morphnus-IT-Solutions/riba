#!/usr/bin/env python
import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.fbsettings'
ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)

from rms.models import Campaign, Interaction, Response
from rms.views import get_or_create_response, move_response
import datetime, time
from payments.models import PaymentAttempt
from users.models import Profile, Phone, Email
from utils import utils
import logging
import re


log = logging.getLogger('fborder')

def main():
    time_now = datetime.datetime.now()
    end_time = time_now - datetime.timedelta(minutes=15)
    start_time = time_now -  datetime.timedelta(minutes=30)

    ''' Payment Attempts that are in pending '''
    pa = PaymentAttempt.objects.select_related('order,order__user,order__user__user').filter(status__in=('pending realization','rejected'), created_on__range = (start_time, end_time), order__support_state='booked', order__booking_agent__isnull=True,order__confirming_agent__isnull=True,order__agent__isnull=True).exclude(payment_mode__in=utils.DEFERRED_PAYMENT_MODES)
    for attempt in pa:
        try:
            ''' Getting the 1st phone number if exists '''
            phones = Phone.objects.filter(user = attempt.order.user_id)[:1]
            if phones:
                phone = phones[0]
                
                campaign = None
                response = None
                
                ''' Select campaign as per client '''
                if(attempt.order.client.id==5):
                    ''' Abandon Payment Campaign id is 22 '''
                    campaign = Campaign.objects.get(id=22)

                elif(attempt.order.client.id==6):
                    ''' Holii Abandoned Payment campaign id is 29 '''
                    campaign = Campaign.objects.get(id=29)
                
                elif(attempt.order.client.id==1):
                    ''' Chaupaati Abandoned Payment campaign id is 28 '''
                    campaign = Campaign.objects.get(id=28)
                
                if campaign and phone:
                    response = get_or_create_response(campaign=campaign, phone=phone, type='outbound', medium=attempt.order.medium)
                    if response:
                        response.orders.add(attempt.order)
                        response.save()
                        notes = "order id: %s Order Amount: %s Login: %s Payment_mode: %s" %(attempt.order.reference_order_id, attempt.order.total, attempt.order.user.user.username, attempt.payment_mode)
                        interaction = Interaction(response = response, communication_mode = 'call', notes = notes)
                        interaction.save()
                        # TODO add interaction for providing details to agent
                    else:
                        log.info("===ABANDONED PAYMENT=== Unable to create response : %s " % phone)
                        # TODO Send an email
            else:
                log.info("===ABANDONED PAYMENT=== Unable to create response as no phone attached to user ")
                # TODO Send an email

        except Exception, e:
            log.info("===ABANDONED PAYMENT=== Exception %s" % repr(e))
            # TODO Send an email

# move new responses to Calling Delayed state if they are not assignedd to any agents even after 150 minutes of their creation time.                
    expiry_time = time_now - datetime.timedelta(minutes=150)
    responses = Response.objects.filter(campaign__in=(22,28,29),assigned_to__isnull=True, last_interacted_by__isnull=True, created_on__lt=expiry_time, funnel_state=None, funnel_sub_state=None)
    if responses:
        for response in responses:
            try:
                funnel_state = response.campaign.funnel.funnel_states.get(name='Dialled')
                funnel_sub_state = response.campaign.campaign_sub_states.get(name='Calling Delayed', funnel_state=funnel_state)
                move_response(response=response, state=funnel_state, substate=funnel_sub_state)
            except Exception, e:
                log.info("===ABANDONED PAYMENT=== Moving to stale state Exception: %s" % repr(e))
                # TODO Send an email


if __name__ == "__main__":
    main()

