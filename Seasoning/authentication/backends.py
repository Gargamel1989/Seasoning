"""
Copyright 2012, 2013 Driesen Joep

This file is part of Seasoning.

Seasoning is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Seasoning is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Seasoning.  If not, see <http://www.gnu.org/licenses/>.
    
"""
from django.contrib.auth import login, load_backend, get_user_model
from django.conf import settings
from django.contrib.sites.models import RequestSite, get_current_site

from authentication import signals
from authentication.forms import EmailUserCreationForm
from authentication.models import RegistrationProfile, User
from django.contrib.auth.backends import ModelBackend
import urllib2
from django.utils import simplejson
from urllib2 import HTTPError
import re


class RegistrationBackend(object):
    """
    A registration backend which follows a simple workflow:

    1. User signs up, inactive account is created.

    2. Email is sent to user with activation link.

    3. User clicks activation link, account is now active.

    Using this backend requires that

    * ``registration`` be listed in the ``INSTALLED_APPS`` setting
      (since this backend makes use of models defined in this
      application).

    * The setting ``ACCOUNT_ACTIVATION_DAYS`` be supplied, specifying
      (as an integer) the number of days from registration during
      which a user may activate their account (after that period
      expires, activation will be disallowed).

    * The creation of the templates
      ``authentication/activation_email_subject.txt`` and
      ``authentication/activation_email.txt``, which will be used for
      the activation email. See the notes for this backends
      ``register`` method for details regarding these templates.

    Additionally, registration can be temporarily closed by adding the
    setting ``REGISTRATION_OPEN`` and setting it to
    ``False``. Omitting this setting, or setting it to ``True``, will
    be interpreted as meaning that registration is currently open and
    permitted.

    Internally, this is accomplished via storing an activation key in
    an instance of ``registration.models.RegistrationProfile``. See
    that model and its custom manager for full documentation of its
    fields and supported operations.
    
    """
    def register(self, request, **kwargs):
        """
        Given a givenname, surname, email address, password, gender and date of
        birth, register a new user account, which will initially be inactive.

        Along with the new ``User`` object, a new
        ``registration.models.RegistrationProfile`` will be created,
        tied to that ``User``, containing the activation key which
        will be used for this account.

        An email will be sent to the supplied email address; this
        email should contain an activation link. The email will be
        rendered using two templates. See the documentation for
        ``RegistrationProfile.send_activation_email()`` for
        information about these templates and the contexts provided to
        them.

        After the ``User`` and ``RegistrationProfile`` are created and
        the activation email is sent, the signal
        ``registration.signals.user_registered`` will be sent, with
        the new ``User`` as the keyword argument ``user`` and the
        class of this backend as the sender.

        """
        givenname, surname, email, password, date_of_birth = kwargs['givenname'], kwargs['surname'], kwargs['email'], kwargs['password'],  kwargs['date_of_birth']
        
        site = RequestSite(request)
        new_user = RegistrationProfile.objects.create_inactive_user(givenname, surname, email,
                                                                    password, date_of_birth, 
                                                                    site)
        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)
        return new_user
    
    def social_register(self, request, social_id, social_network, givenname, surname, email, password, date_of_birth):
        """
        Users registering from a social network already have a validated e-mail address,
        and thus should not be sent an activatoin email
        
        The social_network parameter should be one of SocialUserBackend.{FACEBOOK, ...}
        
        """
        new_user = User.objects.create_user(givenname, surname, email, date_of_birth)
        new_user.save()
        
        signals.user_registered.send(sender=self.__class__,
                                     user=new_user,
                                     request=request)
        
        return new_user


    def activate(self, request, activation_key):
        """
        Given an an activation key, look up and activate the user
        account corresponding to that key (if possible).

        After successful activation, the signal
        ``registration.signals.user_activated`` will be sent, with the
        newly activated ``User`` as the keyword argument ``user`` and
        the class of this backend as the sender.
        
        """
        activated = RegistrationProfile.objects.activate_user(activation_key)
        if activated:
            signals.user_activated.send(sender=self.__class__,
                                        user=activated,
                                        request=request)
            # Bit of an ugly hack to get around authentication
            backend = load_backend(settings.AUTHENTICATION_BACKENDS[0])
            activated.backend = "%s.%s" % (backend.__module__, backend.__class__.__name__)
            login(request, activated)
        return activated

    def registration_allowed(self, request):
        """
        Indicate whether account registration is currently permitted,
        based on the value of the setting ``REGISTRATION_OPEN``. This
        is determined as follows:

        * If ``REGISTRATION_OPEN`` is not specified in settings, or is
          set to ``True``, registration is permitted.

        * If ``REGISTRATION_OPEN`` is both specified and set to
          ``False``, registration is not permitted.
        
        """
        return getattr(settings, 'REGISTRATION_OPEN', True)

    def get_form_class(self, request):
        """
        Return the default form class used for user registration.
        
        """
        return EmailUserCreationForm

    def post_registration_redirect(self, request, user):
        """
        Return the name of the URL to redirect to after successful
        user registration.
        
        """
        return ('registration_complete', (), {})

    def post_activation_redirect(self, request, user):
        """
        Return the name of the URL to redirect to after successful
        account activation.

        """
        return ('activation_complete', (), {})

class SocialUserBackend(ModelBackend):
    """
    This backend provides the ability to log in a user with a social network
    account.
    
    By default, the ``authenticate`` method creates ``User`` objects for
    emails that don't already exist in the database.  Subclasses can disable
    this behavior by setting the ``create_unknown_user`` attribute to
    ``False``.
    """
    
    FACEBOOK, TWITTER, GOOGLE, OPENID = 'facebook_id', 'twitter_id', 'google_id', 'openid_id'

    def authenticate(self, network_id, network):
        """
        The id should be the social id of the user that is being authentication. It
        is considered trusted.
        The network parameter specifies from which social network the user is
        authenticating. It should be one of backends.{FACEBOOK, TWIITER, GOOGLE, OPENID}
        
        """
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(**{network: network_id})
        except UserModel.DoesNotExist:
            return None
    
    def get_facebook_access_token(self, request, code):
        try:
            fb_token_request_url = 'https://graph.facebook.com/oauth/access_token?client_id=' + settings.FACEBOOK_APP_ID + \
                                   '&redirect_uri=http://' + get_current_site(request).domain + '/auth/fb/' + \
                                   '&client_secret=' + settings.FACEBOOK_SECRET + '&code=' + code
            fb_token_response = urllib2.urlopen(fb_token_request_url).read()
            if re.match('^access_token\=.*', fb_token_response):
                return fb_token_response.replace('access_token=', '')
        except HTTPError:
            return False
        
    def check_facebook_access_token(self, access_token):
        try:
            user_info_fb = urllib2.urlopen('https://graph.facebook.com/me?access_token=' + access_token)
            return simplejson.loads(user_info_fb.read())
        except HTTPError:
            return False