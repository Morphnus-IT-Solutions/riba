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
import xlrd
from notifications.notification import Notification
from notifications.email import Email as EmailAddress
from django.template import Context, Template
from django.template.loader import get_template
from django.core.mail import send_mail
from django.template.loader import render_to_string

wb = xlrd.open_workbook('report.xls')
s= wb.sheet_by_index(0)
coupon = Coupon.objects.get(code = 'dclm1010a6d')

for k in range(1,s.nrows):
    row = s.row(k)
    email = row[0].value
    print email
    coupon.uses += 1
    user_email = Email.objects.get(email=email)
    #coupon_email_map = CouponEmailMapping(coupon=coupon,email=user_email)
    #coupon_email_map.save()
    mail_obj = EmailAddress()
    mail_obj.isHtml = True
    mail_obj._from = "noreply@futurebazaar.com"
    mail_obj.body = render_to_string('notifications/subscriptions/apologize.html',None)
    mail_obj.subject = "Avail your revised futurebazaar.com discount coupon codes"
    mail_obj.to = email
    mail_obj.send()
