from users.models import Profile,Email,Phone
from django.contrib.auth.models import User
from utils import utils
import hashlib
import logging
import hashlib
from django.utils import simplejson as json

log = logging.getLogger('fborder')

class ChaupaatiBackend:
    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def get_user(self, user_id):
        return User.objects.get(pk=user_id)

    def authenticate(self, username=None, password=None, **kwargs):
        try:
            profile = None
            if utils.is_valid_email(username):
                input_type = "email"
            elif utils.is_valid_mobile(username):
                input_type = "mobile"
            else:
                input_type = "id"
            if input_type == 'email':
                try:
                    email = Email.objects.get(email=username)
                    profile = email.user              
                except Email.DoesNotExist:
                    return None
            if input_type == 'mobile':
                try:
                    phone = Phone.objects.get(phone=username)
                    profile = phone.user
                except Phone.DoesNotExist:
                    return None
            if profile:
            #profile = Profile.objects.get(primary_phone=username)
                salt = profile.salt
                passcode = profile.passcode

                generated_passcode = hashlib.md5(salt).hexdigest()
                generated_passcode += hashlib.md5(password.encode(
                    'ascii', 'ignore')).hexdigest()
                generated_passcode = hashlib.md5(generated_passcode).hexdigest()
                if passcode == generated_passcode:
                    return profile.user
            return None
        except Profile.DoesNotExist:
            return None
        return None

class PhoneEmailBackend():
    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def get_user(self, user_id):
        return User.objects.get(pk=user_id)

    def authenticate(self, username=None, password=None, **kwargs):
       # get user by email or phone
       from utils import utils
       profile = utils.get_profile_by_email_or_phone(username)
       if not profile:
           return None
       if profile.user.check_password(password):
           return profile.user
       return None

'''
Not used - prady
class FutureBazaarATGBackend():

    def get_user(self, user_id):
        return User.objects.get(pk=user_id)

    def authenticate(self, username=None, password=None, **kwargs):
        try:
            if not password:
                return None
            hexdigest = hashlib.md5(password.encode('ascii',
                'ignore')).hexdigest()
            dps_user = DpsUser.objects.get(login = username,
                password = hexdigest)
            profile = users.sync_atg_user(dps_user.login)
            return profile.user
        except DpsUser.DoesNotExist:
            return None
        except TypeError, te:
            # Throws a type error when password is None
            return None
        except Exception, e:
            log.exception('Error authenticating user using atg db %s' % repr(e))
            return None
'''

class FutureBazaarBackend():
    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def get_user(self, user_id):
        return User.objects.get(pk=user_id)

    def authenticate(self, username=None, password=None, **kwargs):
        try:
            request = kwargs.get('request', None)
            if utils.is_cc(request) and not hasattr(request,'call'):
                return None
            u = users.authenticate_user(username, password, '','', request)
            if u['responseCode'] == 'UM_USER_LOGGED_IN':
                log.debug('Matching username and password from atg: %s' % u)
                # sync atg user with ours
                profile = users.sync_user(u['items'][0])
                return profile.user
        except Exception, e:
            log.exception('Error authenticating user with atg %s' % repr(e))
            return None
        return None

class ATGPasswordBackend():
    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def get_user(self, user_id):
        return User.objects.get(pk=user_id)

    def authenticate(self, username=None, password=None, **kwargs):
       # get user by email or phone
       from utils import utils
       profile = utils.get_profile_by_email_or_phone(username)
       if not profile:
           return None
       if profile.check_atg_password(password):
           return profile.user
       return None

class FacebookAutoBackend():
    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def get_user(self, user_id):
        return User.objects.get(pk=user_id)

    def authenticate(self, request=None):
        facebook_info = utils.get_facebook_info(request)
        if not facebook_info:
            return None
        if facebook_info.linking_done and (not facebook_info.linking_denied):
            user = facebook_info.email.user.user
            user.atg_username = facebook_info.linked_to
            return user

        return None
