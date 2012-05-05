from users.models import Profile
from django.contrib.auth.models import User
import hashlib
import logging
from orders.models import Order
from utils import utils
from users.models import Email,Phone

log = logging.getLogger('request')

class OrderBackend:
    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False

    def get_user(self, user_id):
        return User.objects.get(pk=user_id)

    def authenticate(self, request, username=None, orderid=None):
        try:
            if orderid:
                try:
                    if utils.is_future_ecom(request.client.client):
                        order = Order.objects.filter(reference_order_id=orderid,state='pending_order')
                        if order:
                            order = order[0]
                        else:
                            return None
                    else:
                        order = Order.objects.get(id=orderid)
                except Order.DoesNotExist:
                    return None
                profile = None
                if utils.is_valid_email(username):
                    input_type = "email"
                elif utils.is_valid_mobile(username):
                    input_type = "mobile"
                else:
                    input_type = "id"
                if input_type == "email":
                    try:
                        email = Email.objects.get(email=username)
                        profile = email.user              
                    except Email.DoesNotExist:
                        return None
                if input_type == "mobile":
                    try:
                        phone = Phone.objects.get(phone=username)
                        profile = phone.user
                    except Phone.DoesNotExist:
                        return None
                if profile:
                    if order.user == profile:
                        return profile.user
            return None
        except Profile.DoesNotExist:
            return None
        return None
