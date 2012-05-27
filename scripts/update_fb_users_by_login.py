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

from users.models import Profile
from integrations.fbapi import users, orders, fbapiutils
from orders.models import *

import logging

log = logging.getLogger('request')


if __name__ == '__main__':

    ls = []
    f = open('/tmp/map2')
    for line in f.readlines():
        line = line.strip()
        orderid, login = line.split('\t')
      	ls.append({'orderid':orderid, 'login':login}) 
        profile = None
        try:
            e = Email.objects.get(email=login)
            profile = e.user
        except Email.DoesNotExist:
            try:
                p = Phone.objects.get(phone=login)
                profile = p.user
            except Phone.DoesNotExist:
                log.info( "No matching user for %s" % login)
        if profile:
            profile.atg_username = login
            profile.save()
            if profile.user.username != login:
                log.info( "username %s does not match with login %s" % (profile.user.username, login))
                


    #orders = Order.objects.filter(reference_order_id__in=ls, state="confirmed")
    
    for info in ls:
        l = info["orderid"]
        log.info( "DEBUG: processing....%s" % info)

        order = Order.objects.filter(reference_order_id = l, state="confirmed").order_by("-payment_realized_on")
        if order:
            order = order[0]
        else:
            order = Order.objects.filter(reference_order_id = l, state="pending_order").order_by("-timestamp")
            if order:
                order = order[0]
            else:
                order = Order.objects.filter(reference_order_id = l).order_by("-timestamp")
                if order:
                    order = order[0]

        if not order:
            log.info( "DEBUG: No order found %s" % l)
        else:
            if order.user.user.username != info["login"]:
                log.info( "DEBUG: %s by %s. Attached to %s" % (l, order.user.user.username, info["login"]))

                    
        try:
	    delivery_info = order.get_delivery_info()
	    shipping_address = delivery_info.address
	     
	    billing_info = BillingInfo.objects.filter(user=order.user)
	    if billing_info:
		billing_info = billing_info[len(billing_info) - 1]
		billing_address = billing_info.address
            else:
                log.info( "DEBUG: No billing info found.Using shipping as billing")

            cookie_file = fbapiutils.init()
    	    ress = users.get_user_by_login(order.user.atg_username, "hemant.fb", cookie_file)

            log.info( "USERINFO %s" % ress)
            if ress["responseCode"] != "UM_FOUND_USER":
                log.info( "DEBUG: Did not find user %s" % order.user.atg_username)
                users.create_user(order.user.atg_username, '', "hemant.fb", cookie_file)
            else:
                continue

	    first_name = ""
	    last_name = ""
            billingaddress = ""
            billingcity = ""
            billingstate = ""
	    if order.user.user.first_name:
		first_name = order.user.user.first_name
	    elif billing_info:
		first_name = billing_info.first_name
	    if order.user.user.last_name:
		last_name = order.user.user.last_name
	    elif billing_info:
		last_name = billing_info.last_name
	    delivery_first_name = ""
	    delivery_last_name = ""
	    delivery_first_name = delivery_info.address.name
	    if delivery_info.address.name:
		ls = delivery_info.address.name.split()
		if ls:
		    if len(ls) >1:
			delivery_first_name = ls[0]
			delivery_last_name = ls[1]
            if billing_info:
                billingaddress = billing_info.address.address
                billingcity = billing_info.address.city.name
                billingpin = billing_info.address.pincode
                billingphone = billing_info.phone
                billingstate = billing_info.address.state.name
            else:
                billingaddress = delivery_info.address.address
                billingcity = delivery_info.address.city.name
                billingpin = delivery_info.address.pincode
                billingphone = delivery_info.address.phone
                billingstate = delivery_info.address.state.name

	    resp = users.update_user({
		    "first_name": delivery_first_name,
		    "last_name": delivery_last_name,
		    "address": delivery_info.address.address,
		    "city": delivery_info.address.city.name,
		    "state": fbapiutils.STATES_MAP[delivery_info.address.state.name],
		    "country": "IN",
		    "postal_code": delivery_info.address.pincode,
		    "phone_number": delivery_info.address.phone
		},
		{
		    "first_name": first_name,
		    "last_name": last_name,
		    "address": billingaddress,
		    "city": billingcity,
		    "state": fbapiutils.STATES_MAP[billingstate],
		    "country": "IN",
		    "postal_code": billingpin,
		    "phone_number": billingphone
		},
		"",
		cookie_file)
	    log.info( "UPDATE_RESPONSE %s" % resp)
        except Exception, e:
            log.info( "DEBUG: %s" % repr(e))
            continue
