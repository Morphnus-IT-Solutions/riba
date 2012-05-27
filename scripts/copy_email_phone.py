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

users = Profile.objects.all()

for user in users:
    if user.primary_email:
        try:
            email = Email.objects.get(email=user.primary_email)
        except Email.DoesNotExist:
            try:
                email = Email()
                email.email = user.primary_email
                email.user = user
                email.type='primary'
                email.save()
            except:
                pass
    if user.secondary_email:
        try:
            email = Email.objects.get(email=user.primary_email)
        except Email.DoesNotExist:
            try:
                email = Email()
                email.email = user.secondary_email
                email.user = user
                email.type='secondary'
                email.save()
            except:
                pass
    if user.user.username:
        try:
            phone = Phone.objects.get(phone=user.user.username)
        except Phone.DoesNotExist:
            try:
                phone = Phone()
                phone.phone = user.user.username
                phone.user = user
                phone.type = 'primary'
                phone.save()
            except:
                pass
