from django.test import TestCase
from authentication.models import User, RegistrationProfile
import authentication.forms
import datetime
import os
from authentication.backends import RegistrationBackend
from django.contrib.sites.models import Site

class AuthenticationFormsTestCase(TestCase):
    
    def test_registration_form(self):
        User.objects.create_user(**{'givenname': 'test',
                                    'surname': 'user',
                                    'password': 'haha',
                                    'email': 'testuser@test.be',
                                    'date_of_birth': datetime.date.today()})
        os.environ['RECAPTCHA_TESTING'] = 'True'

        form = authentication.forms.EmailUserCreationForm(data={'givenname': 'test',
                                                                'surname': 'user',
                                                                'password': 'haha',
                                                                'password2': 'hahaa',
                                                                'email': 'testuser@test.be',
                                                                'date_of_birth': datetime.date.today(),
                                                                'tos': False,
                                                                'captcha': ''})
        self.failIf(form.is_valid())        
        self.assertFalse('givenname' in form.errors)
        self.assertFalse('surname' in form.errors)
        self.assertEqual(form.errors['__all__'], [u'The two password fields didn\'t match.'])
        self.assertEqual(form.errors['email'], [u'User with this Email address already exists.'])
        self.assertEqual(form.errors['tos'], [u'You must agree to the terms to register'])
        self.assertEqual(form.errors['captcha'], [u'You must enter the correct ReCaptcha characters'])
        
        form = authentication.forms.EmailUserCreationForm(data={'givenname': 'test',
                                                                'surname': 'user',
                                                                'password': 'haha',
                                                                'password2': 'haha',
                                                                'email': 'testuser2@test.be',
                                                                'date_of_birth': datetime.date.today(),
                                                                'tos': True,
                                                                'captcha': 'something'})
        self.failIf(form.is_valid())
        self.assertEqual(form.errors['givenname'], [u'Enter a valid username.'])
        self.assertEqual(form.errors['surname'], [u'Enter a valid username.'])
        self.assertEqual(form.errors['captcha'], [u'You must enter the correct ReCaptcha characters'])
        
        form = authentication.forms.EmailUserCreationForm(data={'givenname': 'test2',
                                                                'surname': 'user2',
                                                                'password': 'haha',
                                                                'password2': 'haha',
                                                                'email': 'testuser2@test.be',
                                                                'date_of_birth': datetime.date.today(),
                                                                'tos': True,
                                                                'recaptcha_response_field': 'PASSED'})
        self.assertTrue(form.is_valid())
        
    def test_resend_activation_email_form(self):
        form = authentication.forms.ResendActivationEmailForm(data={'email': ''})
        # Check invalid input
        self.failIf(form.is_valid())
        self.assertEqual(form.errors['email'], [u'Please enter a valid email address'])
        
        user = RegistrationProfile.objects.create_inactive_user(**{'givenname': 'test',
                                                                   'surname': 'user',
                                                                   'password': 'haha',
                                                                   'email': 'testuser@test.be',
                                                                   'date_of_birth': datetime.date.today(),
                                                                   'site': Site.objects.get_current()})
        # Check for inactive user
        form = authentication.forms.ResendActivationEmailForm(data={'email': user.email})
        
        self.assertTrue(form.is_valid())
        
        # Check for active user
        RegistrationProfile.objects.activate_user(RegistrationProfile.objects.get(user=user).activation_key)
        form = authentication.forms.ResendActivationEmailForm(data={'email': user.email})
        
        self.failIf(form.is_valid())
        self.assertEqual(form.errors['email'], [u'The account corresponding to this email address has already been activated'])
        
        # Check for unknown user
        form = authentication.forms.ResendActivationEmailForm(data={'email': 'unknown@example.com'})
        
        self.failIf(form.is_valid())
        self.assertEqual(form.errors['email'], [u'The given email address was not found'])
    
    def test_check_activate_account_form(self):
        RegistrationProfile.objects.create_inactive_user(**{'givenname': 'test',
                                                            'surname': 'user',
                                                            'password': 'haha',
                                                            'email': 'testuser@test.be',
                                                            'date_of_birth': datetime.date.today(),
                                                            'site': Site.objects.get_current()})
        
        form = authentication.forms.CheckActiveAuthenticationForm(data={'username': 'testuser@test.be',
                                                                        'password': 'haha'})
        
        self.failIf(form.is_valid())
        self.assertEqual(form.errors['__all__'], [u'This account has not been activated yet, so you may not log '
                                                   'in at this time. If you haven\'t received an activation email for '
                                                   '15 minutes after registering, you can use <a href="/activate/resend/">'
                                                   'this form</a> to resend an activation email.'])
    
    def test_account_settings_form(self):
        user = RegistrationProfile.objects.create_inactive_user(**{'givenname': 'test',
                                                                   'surname': 'user',
                                                                   'password': 'haha',
                                                                   'email': 'testuser@test.be',
                                                                   'date_of_birth': datetime.date.today(),
                                                                   'site': Site.objects.get_current()})
        RegistrationProfile.objects.activate_user(RegistrationProfile.objects.get(user=user).activation_key)
        
        # email doesn't change, empty avatar is possible
        form = authentication.forms.AccountSettingsForm(instance=user,
                                                        data={'email': 'testuser@test.be',
                                                              'avatar': ''})
        self.assertTrue(form.is_valid())
        self.assertRaises(AttributeError, form.new_email)
        
        # New Email
        form = authentication.forms.AccountSettingsForm(instance=user,
                                                        data={'email': 'othertestuser@test.be',
                                                              'avatar': 'test.png'})
        self.assertTrue(form.is_valid())
        self.assertEqual(form.new_email, 'othertestuser@test.be')
        