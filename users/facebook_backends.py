from django.contrib.auth.models import User

class FacebookBackend:
    supports_object_permissions = False
    supports_anonymous_user = False
    supports_inactive_user = False


    def get_user(self, user_id):
        return User.objects.get(pk=user_id)

    def authenticate(self, facebook_user, **kwargs):
        return facebook_user
