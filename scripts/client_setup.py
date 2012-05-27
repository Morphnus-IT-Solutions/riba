#!/usr/bin/python

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


from accounts.models import *

# Client Details
while True:
	client_name = raw_input("1. Client Name : ").strip()
	if client_name:
		break


# Client Domain Details
while True:
	client_domain = raw_input("2. Client Domain : ").strip()
	if client_domain:
		break
while True:
	client_code = raw_input("3. Client Code : ").strip()
	if client_code:
		break


# Account Details
while True:
	account = raw_input("4. Account : ").strip()
	if account:
		break
website = raw_input("5. Website : ").strip()
print "Processing ..."


# Add Client
try:
    c = Client.objects.get(name = client_name)
except Client.DoesNotExist:
    c = Client(name = client_name)
    c.save()
c_id = c.id

# Add Client Domain
cd = ClientDomain(domain = client_domain, code = client_code, client = c)
cd.save()

# Add Account
acc = Account(name = account, client = c, code = client_code, website = website)
acc.save()

# Copy Payment Modes of Chaupaati Marketplace (id = 1)
import copy_payment_modes
copy_payment_modes.copy(1, c_id)

# Default Notification Settings
event_list = ['General', 'Pending Order', 'Confirmed Order']
for d in event_list:
	ns = NotificationSettings(account = acc, event = d)
	ns.save()
