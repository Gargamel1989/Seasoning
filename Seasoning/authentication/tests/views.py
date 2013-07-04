from django.test import TestCase
from django.conf import settings
from authentication.forms import EmailUserCreationForm, ResendActivationEmailForm,\
    AccountSettingsForm
from authentication.models import User, RegistrationProfile, NewEmail
import datetime
import os
from django.core import mail
from django.contrib.sites.models import Site
from django.contrib.auth.forms import PasswordChangeForm

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
    
    def test_resend_activation_email_test(self):
        RegistrationProfile.objects.create_inactive_user(**{'username': 'testuser',
                                                            'password': 'haha',
                                                            'email': 'testuser@test.be',
                                                            'gender': User.MALE,
                                                            'date_of_birth': datetime.date.today(),
                                                            'site': Site.objects.get_current()})
        
        resp = self.client.get('/activate/resend/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('form' in resp.context)
        self.assertEqual(resp.context['form'].__class__, ResendActivationEmailForm)
        
        # Unknown email
        resp = self.client.post('/activate/resend/', {'email': 'testuser2@test.be'})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(mail.outbox), 1)
        
        resp = self.client.post('/activate/resend/', {'email': 'testuser@test.be'})
        self.assertRedirects(resp, '/', 302, 200)
        self.assertEqual(len(mail.outbox), 2)
    
    def test_activate_view(self):
        user = RegistrationProfile.objects.create_inactive_user(**{'username': 'testuser',
                                                                   'password': 'haha',
                                                                   'email': 'testuser@test.be',
                                                                   'gender': User.MALE,
                                                                   'date_of_birth': datetime.date.today(),
                                                                   'site': Site.objects.get_current()})
        registration_profile = RegistrationProfile.objects.get(user=user)
        
        # Bad activation key
        resp = self.client.get('/activate/wrongactivationcode/')
        self.assertEqual(resp.status_code, 404)
        self.failIf(User.objects.get(email='testuser@test.be').is_active)
        
        # Correct activation key
        resp = self.client.get('/activate/' + registration_profile.activation_key + '/')
        self.assertRedirects(resp, '/', 302, 200)
        self.assertTrue(User.objects.get(email='testuser@test.be').is_active)
    
    def test_account_settings_view(self):
        user = RegistrationProfile.objects.create_inactive_user(**{'username': 'testuser',
                                                                   'password': 'haha',
                                                                   'email': 'testuser@test.be',
                                                                   'gender': User.MALE,
                                                                   'date_of_birth': datetime.date.today(),
                                                                   'site': Site.objects.get_current()})
        RegistrationProfile.objects.activate_user(RegistrationProfile.objects.get(user=user).activation_key)
        
        resp = self.client.get('/account/settings/')
        self.assertRedirects(resp, '/login/?next=/account/settings/', 302, 200)
        
        self.client.login(username='testuser@test.be', password='haha')
        resp = self.client.get('/account/settings/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('form' in resp.context)
        self.failIf('new_email' in resp.context)
        self.assertEqual(resp.context['form'].__class__, AccountSettingsForm)
        
        resp = self.client.post('/account/settings/', {'email': 'othertestuser@test.be'})
        self.assertEqual(resp.status_code, 200)
        NewEmail.objects.get(user=user)
        self.assertTrue('new_email' in resp.context)
        
    def test_change_email_view(self):
        user = RegistrationProfile.objects.create_inactive_user(**{'username': 'testuser',
                                                                   'password': 'haha',
                                                                   'email': 'testuser@test.be',
                                                                   'gender': User.MALE,
                                                                   'date_of_birth': datetime.date.today(),
                                                                   'site': Site.objects.get_current()})
        RegistrationProfile.objects.activate_user(RegistrationProfile.objects.get(user=user).activation_key)
        
        self.client.login(username='testuser@test.be', password='haha')
        self.client.post('/account/settings/', {'email': 'othertestuser@test.be'})
        resp = self.client.get('/email/change/wrongactivationcode/')
        self.assertEqual(resp.status_code, 404)
        new_email = NewEmail.objects.get(user=user)
        resp = self.client.get('/email/change/' + new_email.activation_key + '/')
        self.assertRedirects(resp, '/account/settings/', 302, 200)
        
    def test_change_password_view(self):
        user = RegistrationProfile.objects.create_inactive_user(**{'username': 'testuser',
                                                                   'password': 'haha',
                                                                   'email': 'testuser@test.be',
                                                                   'gender': User.MALE,
                                                                   'date_of_birth': datetime.date.today(),
                                                                   'site': Site.objects.get_current()})
        RegistrationProfile.objects.activate_user(RegistrationProfile.objects.get(user=user).activation_key)
        
        self.client.login(username='testuser@test.be', password='haha')
        resp = self.client.get('/password/change/')
        self.assertEqual(resp.status_code, 200)
        self.assertTrue('form' in resp.context)
        self.assertEqual(resp.context['form'].__class__, PasswordChangeForm)
        
        resp = self.client.post('/password/change/', {'old_password': 'haha',
                                                      'new_password1': 'haha1',
                                                      'new_password2': 'haha1'})
        self.assertRedirects(resp, '/account/settings/', 302, 200)
        self.assertTrue(User.objects.get(email='testuser@test.be').check_password('haha1'))
        