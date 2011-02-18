from django.contrib.auth.models import User as DjangoUser, check_password
from csc.pseudo_auth.models import LegacyUser

class LegacyBackend:
    def authenticate(self, username=None, password=None):
        try:
            # Load user object
            u = LegacyUser.objects.get(username=username)

            # Abort if Django should handle this
            if u.password.startswith('sha1$'): return None
            salt = u.salt

            # Build Django-compatible password string
            enc_password = 'sha1$--' + u.salt + '--$' + u.password

            # Check password
            if check_password(password+'--',enc_password):
                # Migrate them to new passwords.
                u.salt = None
                u.save()
                user = self.get_user(u.id)
                user.set_password(password)
                user.save()
                return user
        except LegacyUser.DoesNotExist:
            return None

        # Operation Complete!
        return None

    def get_user(self, user_id):
        try:
            return DjangoUser.objects.get(pk=user_id)
        except DjangoUser.DoesNotExist:
            return None
