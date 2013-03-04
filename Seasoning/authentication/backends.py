from django.contrib.auth.models import User
from django.contrib.auth.backends import ModelBackend

class EmailAuthBackend(ModelBackend):
    """
    Email Authentication Backend
    
    Allows a user to sign in using an email/password pair rather than
    a username/password pair.
    
    If the user has just been activated, you may pass this user in the
    activated_user argument. The method will then just return this user
    again, effectively authenticating it.
    """
    
    def authenticate(self, email=None, password=None, activated_user=None):
        """ Authenticate a user based on email address as the user name. """
        if activated_user:
            return activated_user
        try:
            user = User.objects.get(email=email)
            if user.check_password(password):
                return user
        except User.DoesNotExist:
            return None