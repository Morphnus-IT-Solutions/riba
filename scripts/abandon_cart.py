#!/usr/bin/env python
import os, sys

os.environ['DJANGO_SETTINGS_MODULE'] = 'tinla.settings'

ROOT_FOLDER = os.path.realpath(os.path.dirname(__file__))
ROOT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')]

if ROOT_FOLDER not in sys.path:
    sys.path.insert(1, ROOT_FOLDER + '/')

# also add the parent folder
PARENT_FOLDER = ROOT_FOLDER[:ROOT_FOLDER.rindex('/')+1]
if PARENT_FOLDER not in sys.path:
    sys.path.insert(1, PARENT_FOLDER)


from orders.models import Order
from rms.models import Campaign, Response
from rms.views import get_or_create_response, move_response
import datetime, time
from payments.models import PaymentAttempt
from users.models import Profile, Phone, Email
import re
import logging

log = logging.getLogger('fborder')

def main():
    time_now = datetime.datetime.now()
    end_time = time_now - datetime.timedelta(minutes=30)
    start_time = time_now -  datetime.timedelta(minutes=45)

    # Orders that are only in cart state or buy later and not booked by an agent (if booked by agent a response already exists)
    orders = Order.objects.filter(
            modified_on__range = (start_time,
            end_time),state__in=(
            'cart','guest_cart','temporary_cart','unassigned_cart'),
            booking_agent__isnull=True,
            confirming_agent__isnull=True,
            agent__isnull=True, total__gt=0)

    for order in orders:
        try:
            phones = Phone.objects.filter(
                user = order.user)[:1]
            if phones:
                phone = phones[0]

                campaign = None
                response = None
                ''' Select campaign as per client '''
                if(order.client.id==5):
                    ''' FB Abandon Cart Campaign id is 23 '''
                    campaign = Campaign.objects.get(id=23)
                
                elif(order.client.id==1):
                    ''' Chaupaati Abandoned Carts campaign id is 30 '''
                    campaign = Campaign.objects.get(id=30)
                
                elif(order.client.id==6):
                    ''' Holii Abandoned Carts Campaign id is 31 '''
                    campaign = Campaign.objects.get(id=31)
                
                if campaign:
                    response = get_or_create_response(campaign=campaign, phone=phone, type='outbound', medium=order.medium)
                    if response:
                        response.orders.add(order)
                        response.save()
                    else:
                        log.info("===ABANDONED CART===  Cannot create response: %s" % phone)
                        # TODO Send an email

            else:
                log.info("===ABANDONED CART===  Cannot create response: No phone attched to user")
                # TODO Send an email

        except Exception, e:
            log.info("===ABANDONED CART=== %s" % repr(e))
            # TODO Send an email

# move new responses to Calling Delayed state if they are not assignedd to any agents even after 150 minutes of their creation time.                
    expiry_time = time_now - datetime.timedelta(minutes=150)
    responses = Response.objects.filter(campaign__in=(23,30,31),assigned_to__isnull=True, last_interacted_by__isnull=True, created_on__lt=expiry_time, funnel_state=None, funnel_sub_state=None)
    if responses:
        for response in responses:
            try:
                funnel_state = response.campaign.funnel.funnel_states.get(name='Dialled')
                funnel_sub_state = response.campaign.campaign_sub_states.get(name='Calling Delayed', funnel_state=funnel_state)
                move_response(response=response, state=funnel_state, substate=funnel_sub_state)
            except Exception, e:
                log.info("===ABANDONED CART=== Moving to stale state Exception: %s" % repr(e))
                # TODO Send an email





# called every half an hour and look for the last 15 an hour enteries 

if __name__ == "__main__":
    main()

