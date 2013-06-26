from django.test import TestCase
from django.conf import settings
from authentication.forms import EmailUserCreationForm
from authentication.models import User
import datetime
import os
from django.core import mail

class AuthenticationViewsTestCase(TestCase):
    
    def test_registration_view(self):
        old_allowed = getattr(settings, 'REGISTRATION_OPEN', True)
        
        # Test registration disallowed
        settings.REGISTRATION_OPEN = False

        resp = self.client.get('/register/')
        self.assertRedirects(resp, 'register/closed/', 302, 200)
        
        # From now on, only test with registration allowed
        settings.REGISTRATION_OPEN = True
        
        resp = self.client.get('/register/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('form' in resp.context)
        self.assertEqual(resp.context['form'].__class__, EmailUserCreationForm)
        
        resp = self.client.post('/register/', {'username': 'testuser',
                                               'password': 'haha',
                                               'password2': 'hahaa',
                                               'email': 'testuser@test.be',
                                               'gender': User.MALE,
                                               'date_of_birth': datetime.date.today(),
                                               'tos': False,
                                               'captcha': ''})
        # Invalid information in the form should just display the same page
        self.assertEqual(resp.status_code, 200)
        
        os.environ['RECAPTCHA_TESTING'] = 'True'
        resp = self.client.post('/register/', {'username': 'testuser',
                                               'password': 'haha',
                                               'password2': 'haha',
                                               'email': 'testuser@test.be',
                                               'gender': User.MALE,
                                               'date_of_birth': datetime.date.today(),
                                               'tos': True,
                                               'recaptcha_response_field': 'PASSED'})
        # Valid information in the form should redirect to registration complete
        self.assertRedirects(resp, 'register/complete/', 302, 200)
        self.assertEqual(len(mail.outbox), 1)
        User.objects.get(email='testuser@test.be')
        
        # Reset registration open
        settings.REGISTRATION_OPEN = old_allowed