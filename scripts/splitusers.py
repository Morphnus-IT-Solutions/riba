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

from django.db import transaction
from orders.models import *
from fulfillment.models import *
import logging
log = logging.getLogger('fborder')

from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest
from users.models import *
from django.contrib.auth.models import User
from accounts.models import ClientDomain
from utils import utils
import re

phone_re = re.compile('\d{10}')

def splitusers(email_or_phone):
    email = None
    phone = None
    profile = None
    try:
        email = Email.objects.get(email=email_or_phone)
        profile = email.user
    except Email.DoesNotExist:
        phone = Phone.objects.get(phone=email_or_phone)
        profile = phone.user

    emails = profile.email_set.all()
    phones = profile.phone_set.all()

    for email in emails:
        if not email_re.match(email.email):
            print 'Invalid email %s' % email.email
            # XXX Delete this email
            continue

        with transaction.commit_on_success():
            try:
                au = User.objects.get(username=email.email)
                print 'Skipping splitting email %s' % email.email
            except User.DoesNotExist:
                au = User.objects.create_user(username=email.email, email.email)
                au.save()

                p = Profile(user=au)
                p.save()

                profile_remap = ProfileRemap(
                    old_profile = email.user,
                    new_profile = p,
                    email = email)

                email.user = p
                email.save()
                
                profile_remap.save()

                print 'Created new profile for %s' % email.email
            
    for phone in phones:
        if not phone_re.match(phone.phone):
            print 'Invalid phone %s' % phone.phone
            # XXX Delete this phone
            continue

        with transaction.commit_on_success():
            try:
                au = User.objects.get(username=phone.phone)
                print 'Skipping splitting phone  %s' % phone.phone
            except User.DoesNotExist:
                au = User(username=email.email, email='')
                au.set_unusable_password()
                au.save()

                p = Profile(user=au)
                p.save()

                profile_remap = ProfileRemap(
                    old_profile = phone.user,
                    new_profile = p,
                    phone = phone)

                phone.user = p
                phone.save()

                profile_remap.save()

                
                print 'Created new profile for %s' % email.email
                


if __name__ == '__main__':
    splitusers(sys.argv[1])

