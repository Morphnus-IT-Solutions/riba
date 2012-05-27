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


from orders.models import Order, CodOrderVerification 
from rms.models import Campaign, Response, Interaction
from rms.views import get_or_create_response, move_response
import datetime, time
from payments.models import PaymentAttempt
from users.models import Profile, Phone, Email
from django.db.models import Q
import re
import logging

log = logging.getLogger('fborder')

def main():
    time_now = datetime.datetime.now()
    end_time = time_now - datetime.timedelta(minutes=15)
    start_time = time_now -  datetime.timedelta(minutes=30)

    # Orders that are only in cart state or buy later and not booked by an agent (if booked by agent a response already exists)
    cod_verifications = CodOrderVerification.objects.select_related('order').filter(
            created_on__range = (start_time,
            end_time),is_verified=False)

    for x in cod_verifications:
        order = x.order
        if order.support_state == 'booked':     # still its a pending order
            try:
                phones = Phone.objects.filter(phone=x.mobile_no)
                if phones:      # Phone number entered by user for COD verification
                    phone = phones[0]
                    
                campaign = None
                response = None
                ''' FB COD verification Campaign id is xx '''
                campaign = Campaign.objects.get(id=38)

                if campaign and phone:
                    response = get_or_create_response(campaign=campaign, phone=phone, type='outbound', medium=order.medium)
                    if response:
                        response.orders.add(order)
                        response.save()
                        # add interaction for detail information
                        notes = "order id: %s." %(order.reference_order_id)
                        if order.user != phone.user:
                            notes = notes + " Call using eyebeam directly. Response phone number does not belong to the user placing this order."
                        interaction = Interaction(response = response, communication_mode = 'call', notes = notes)
                        interaction.save()
                    else:
                        log.info("===COD Verification===  Cannot create response: %s" % phone)
            except Exception as e:
                log.info("===COD verification=== %s" %e)
                # TODO Send an email


# called every half an hour and look for the last 15 an hour enteries 

if __name__ == "__main__":
    main()

