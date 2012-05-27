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

from users.models import *
from promotions.models import *
from django.db import models
from django.contrib.auth.models import User
from affiliates.models import *

f= open('coupon1.csv')
lines = f.readlines()
client = Client.objects.get(name = 'New Future Bazaar')
newsletter = NewsLetter.objects.get(client = client,newsletter='DailyDeals')
affiliate = Affiliate.objects.get(name = 'Idea')
for line in lines:
    coupon = Coupon()
    coupon.status='active'
    coupon.affiliate = affiliate
    coupon.discount_available_on='futurebazaar'
    coupon.discount_value=150
    coupon.newsletter =newsletter 
    coupon.code=line.strip()
    coupon.save()

