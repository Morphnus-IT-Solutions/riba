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

from atg.models import FtbDealsLogin
from utils import utils
from users.models import Email, Phone, DailySubscription, NewsLetter
from feeds.models import SubscriptionSync
from datetime import datetime

def migrate_subscriptions():
    start = datetime(day=1, month=4, year=2011)
    subscripions_qs = FtbDealsLogin.objects.filter(registration_time__gte=start)
    newsletter = NewsLetter.objects.get(pk=2)
    for subscription in subscripions_qs:
        if SubscriptionSync.objects.filter(ext_id=subscription.id):
            #print 'Skipping %s: Already synced' % subscription.id
            continue
        email = subscription.email_address or ''
        mobile = subscription.mobile_number or ''
        name = subscription.register_name or ''
        if len(email) > 50 or len(name) > 100:
            #print 'Skipping %s: Long data' % subscription.id
            continue

        source = 'atg'
        if subscription.facebook_user == 1:
            source = 'facebook-atg'

        profile = None

        is_valid_email = False
        e = None
      	if utils.is_valid_email(email):
            is_valid_email = True
            try:
                e = Email.objects.get(email=email)
                profile = e.user
            except Email.DoesNotExist:
                pass

        is_valid_mobile = False
        m = None                 
        if utils.is_valid_mobile(mobile):
            is_valid_mobile = True
            try:
                m = Phone.objects.get(phone=mobile)
                profile = m.user
            except Phone.DoesNotExist:
                pass

        if not is_valid_mobile and is_valid_email:
            #print 'Skipping %s, %s, %s: Invalid data' % (email, mobile, name)
            continue

        if not profile:
            # Create a new profile in our system
            if is_valid_email:
                usr, profile = utils.get_or_create_user(email, email,
                                   password=None, first_name=name)
            if not is_valid_email:
                usr, profile = utils.get_or_create_user(mobile, '',
                                   password=None, first_name=name)

        if not profile:
            # Still not able to create profile
            #print 'Skipping %s, %s, %s: No profile' % (email, mobile, name)
            continue

	if not e:
            try:
                e = Email.objects.get(email=email)
            except Email.DoesNotExist:
                # Create a new email
                e = Email()
                e.user = profile
                e.email = email
                e.save()

        if not m:
            try:
                m = Phone.objects.get(phone=mobile)
            except Phone.DoesNotExist:
                m = Phone()
                m.user = profile
                m.phone = mobile
                m.save()

        # Create an entry into the subscription table 
        subscr = DailySubscription()
        subscr.email_alert_on = e
        subscr.sms_alert_on = m
        subscr.source = source
        subscr.timestamp = subscription.registration_time
        subscr.newsletter = newsletter
        subscr.save()

        link = SubscriptionSync()
        link.ext_id = subscription.id
        link.account = 'futurebazaar'
        link.save() 

if __name__ == '__main__':
    migrate_subscriptions()
