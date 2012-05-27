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

from orders.models import *
from integrations.fbapi import users as f_users, orders as f_orders, fbapiutils
from decimal import Decimal
import simplejson

if __name__ == '__main__':
    cookie_file = fbapiutils.init()
    sock = open('/tmp/fix_data.csv', 'r')
    data_set = []
    lines = sock.readlines()
    keys = ['order_note',
		'payment_mode',
		'received_by',
		'emi_details',
		'sub_pay_type',
		'current_price_list',
		'order_amount',
		'pincode',
		'pg_response',
		'shipping_postal_code']
    for line in lines:
        data = line.split("#")
	d = {}
	for i in range(0,len(keys)):
	    d.update({keys[i]: data[i].strip()})
        """
	d['emi_details'] = {}
        d['order_amount'] = int(d['order_amount'])
	"""
	js = simplejson.loads(d['pg_response'])
	for key in js.keys():
	    if key in ['cvv', 'exp_year', 'exp_month', 'card_no']:
		js[key] = int(js[key])

	d['pg_response'] = {'cardNo': js['card_no'],
			'cardCvv': js['cvv'],
			'cardHoldersName': js['name_on_card'],
			'cardExpMon': js['exp_month'],
			'cardExpYear': js['exp_year'],
			'amountReceivedFromPG': d['order_amount'],
			'currentPriceList': d['current_price_list'],
			'orderAmount': d['order_amount'],
			'paymentMode': d['payment_mode']}
	    
        data_set.append(d)

    sock.close()
    from pprint import pprint
    i = 0
    for data in data_set:
    	f_users.get_user_by_mobile('salimasm@yahoo.com', 'hemant.fb', cookie_file)
    	f_users.submit_cart(data, 'hemant.fb', cookie_file)
        i = i+1
	print i
