from django.test import TestCase
from authentication.backends import RegistrationBackend
from django.test.client import RequestFactory
from authentication.models import User, RegistrationProfile
import datetime
from django.contrib.sessions.backends.db import SessionStore

class AuthenticationBackendsTestCase(TestCase):
    
    def test_registration_and_activation(self):
        backend = RegistrationBackend()
        request = RequestFactory().get('/')
        
        backend.register(request, **{'username': 'testuser',
                                     'password': 'haha',
                                     'email': 'testuser@test.be',
                                     'gender': User.MALE,
                                     'date_of_birth': datetime.date.today()})
        user = User.objects.get(email='testuser@test.be')
        registration_profile = RegistrationProfile.objects.get(user=user)
        
        request.session = SessionStore()
        backend.activate(request, registration_profile.activation_key)
        
        user = User.objects.get(email='testuser@test.be')
        self.assertTrue(user.is_active)
        self.assertTrue(user.is_authenticated())