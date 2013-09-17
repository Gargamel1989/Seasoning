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
from django.test import TestCase
from authentication.models import User, RegistrationProfile, NewEmail
import datetime
import re
from django.contrib.sites.models import Site
from django.core import mail, management
from django.utils.hashcompat import sha_constructor
from django.conf import settings
from recipes.models import Recipe, Cuisine


class AuthenticationModelsTestCase(TestCase):
    
    user_info = {'givenname': 'test',
                 'surname': 'user',
                 'password': 'haha',
                 'email': 'testuser@test.be',
                 'date_of_birth': datetime.date.today()}
    
    def test_user_creation(self):
        User.objects.create_user(**self.user_info)
        new_user = User.objects.get(email="testuser@test.be")
        self.assertEqual(new_user.givenname, 'test')
        self.assertEqual(new_user.surname, 'user')
        self.assertEqual(new_user.date_of_birth, datetime.date.today())
        self.assertEqual(new_user.avatar.url, 'https://www.seasoning.be/media/images/users/no_image.png')
        self.assertEqual(new_user.is_active, True)
        self.assertEqual(new_user.is_staff, False)
        self.assertEqual(new_user.is_superuser, False)
        User.objects.create_superuser("test", "superuser", "testsuperuser@test.be", datetime.date.today(), "haha")
        new_superuser = User.objects.get(email="testsuperuser@test.be")
        self.assertEqual(new_superuser.is_superuser, True)
    
    def test_profile_creation(self):
        """
        Creating a registration profile for a user populates the
        profile with the correct user and a SHA1 hash to use as
        activation key.
        
        """
        new_user = User.objects.create_user(**self.user_info)
        profile = RegistrationProfile.objects.create_profile(new_user)

        self.assertEqual(RegistrationProfile.objects.count(), 1)
        self.assertEqual(profile.user.id, new_user.id)
        self.failUnless(re.match('^[a-f0-9]{40}$', profile.activation_key))
        self.assertEqual(unicode(profile),
                         "Registration information for testuser@test.be")

    def test_activation_email(self):
        """
        ``RegistrationProfile.send_activation_email`` sends an
        email.
        
        """
        new_user = User.objects.create_user(**self.user_info)
        profile = RegistrationProfile.objects.create_profile(new_user)
        profile.send_activation_email(Site.objects.get_current())
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user_info['email']])

    def test_user_creation_with_registration_profile(self):
        """
        Creating a new user populates the correct data, and sets the
        user's account inactive.
        
        """
        new_user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                                    **self.user_info)
        self.assertEqual(new_user.givenname, 'test')
        self.assertEqual(new_user.surname, 'user')
        self.assertEqual(new_user.email, 'testuser@test.be')
        self.failUnless(new_user.check_password('haha'))
        self.failIf(new_user.is_active)

    def test_user_creation_email(self):
        """
        By default, creating a new user sends an activation email.
        
        """
        RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                         **self.user_info)
        self.assertEqual(len(mail.outbox), 1)

    def test_user_creation_no_email(self):
        """
        Passing ``send_email=False`` when creating a new user will not
        send an activation email.
        
        """
        RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                         send_email=False,
                                                         **self.user_info)
        self.assertEqual(len(mail.outbox), 0)

    def test_unexpired_account(self):
        """
        ``RegistrationProfile.activation_key_expired()`` is ``False``
        within the activation window.
        
        """
        new_user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                                    **self.user_info)
        profile = RegistrationProfile.objects.get(user=new_user)
        self.failIf(profile.activation_key_expired())

    def test_expired_account(self):
        """
        ``RegistrationProfile.activation_key_expired()`` is ``True``
        outside the activation window.
        
        """
        new_user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                                    **self.user_info)
        new_user.date_joined -= datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS + 1)
        new_user.save()
        profile = RegistrationProfile.objects.get(user=new_user)
        self.failUnless(profile.activation_key_expired())

    def test_valid_activation(self):
        """
        Activating a user within the permitted window makes the
        account active, and resets the activation key.
        
        """
        new_user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                                    **self.user_info)
        profile = RegistrationProfile.objects.get(user=new_user)
        activated = RegistrationProfile.objects.activate_user(profile.activation_key)

        self.failUnless(isinstance(activated, User))
        self.assertEqual(activated.id, new_user.id)
        self.failUnless(activated.is_active)

        profile = RegistrationProfile.objects.get(user=new_user)
        self.assertEqual(profile.activation_key, RegistrationProfile.ACTIVATED)

    def test_expired_activation(self):
        """
        Attempting to activate outside the permitted window does not
        activate the account.
        
        """
        new_user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                                    **self.user_info)
        new_user.date_joined -= datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS + 1)
        new_user.save()

        profile = RegistrationProfile.objects.get(user=new_user)
        activated = RegistrationProfile.objects.activate_user(profile.activation_key)

        self.failIf(isinstance(activated, User))
        self.failIf(activated)

        new_user = User.objects.get(email='testuser@test.be')
        self.failIf(new_user.is_active)

        profile = RegistrationProfile.objects.get(user=new_user)
        self.assertNotEqual(profile.activation_key, RegistrationProfile.ACTIVATED)

    def test_activation_invalid_key(self):
        """
        Attempting to activate with a key which is not a SHA1 hash
        fails.
        
        """
        self.failIf(RegistrationProfile.objects.activate_user('foo'))

    def test_activation_already_activated(self):
        """
        Attempting to re-activate an already-activated account fails.
        
        """
        new_user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                                    **self.user_info)
        profile = RegistrationProfile.objects.get(user=new_user)
        RegistrationProfile.objects.activate_user(profile.activation_key)

        profile = RegistrationProfile.objects.get(user=new_user)
        self.failIf(RegistrationProfile.objects.activate_user(profile.activation_key))

    def test_activation_nonexistent_key(self):
        """
        Attempting to activate with a non-existent key (i.e., one not
        associated with any account) fails.
        
        """
        # Due to the way activation keys are constructed during
        # registration, this will never be a valid key.
        invalid_key = sha_constructor('foo').hexdigest()
        self.failIf(RegistrationProfile.objects.activate_user(invalid_key))

    def test_expired_user_deletion(self):
        """
        ``RegistrationProfile.objects.delete_expired_users()`` only
        deletes inactive users whose activation window has expired.
        
        """
        RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                         **self.user_info)
        expired_user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                                        givenname='bob',
                                                                        surname='smith',
                                                                        password='secret',
                                                                        email='bob@example.com',
                                                                        date_of_birth=datetime.date.today())
        expired_user.date_joined -= datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS + 1)
        expired_user.save()

        RegistrationProfile.objects.delete_expired_users()
        self.assertEqual(RegistrationProfile.objects.count(), 1)
        self.assertRaises(User.DoesNotExist, User.objects.get, email='bob@example.com')

    def test_management_command(self):
        """
        The ``cleanupregistration`` management command properly
        deletes expired accounts.
        
        """
        RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                         **self.user_info)
        expired_user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                                        givenname='bob',
                                                                        surname='smith',
                                                                        password='secret',
                                                                        email='bob@example.com',
                                                                        date_of_birth=datetime.date.today())
        expired_user.date_joined -= datetime.timedelta(days=settings.ACCOUNT_ACTIVATION_DAYS + 1)
        expired_user.save()

        management.call_command('cleanupregistration')
        self.assertEqual(RegistrationProfile.objects.count(), 1)
        self.assertRaises(User.DoesNotExist, User.objects.get, email='bob@example.com')
    
    def test_new_email(self):
        new_user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                                    **self.user_info)
        
        profile = RegistrationProfile.objects.get(user=new_user)
        RegistrationProfile.objects.activate_user(profile.activation_key)
        
        new_email = NewEmail.objects.create_inactive_email(user=new_user, 
                                                           new_email='bob@example.com', 
                                                           site=Site.objects.get_current(), 
                                                           send_email=False)
        self.assertEqual(new_email.user, new_user)
        self.assertEqual(new_email.email, 'bob@example.com')
        self.failUnless(re.match('^[a-f0-9]{40}$', new_email.activation_key))
        
        new_email.send_new_email_email(Site.objects.get_current())
        
        # One for registration, one for new email
        self.assertEqual(len(mail.outbox), 2)
    
    def test_new_email_activation(self):
        new_user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                                    **self.user_info)
        
        profile = RegistrationProfile.objects.get(user=new_user)
        RegistrationProfile.objects.activate_user(profile.activation_key)
        
        new_email = NewEmail.objects.create_inactive_email(user=new_user, 
                                                           new_email='bob@example.com', 
                                                           site=Site.objects.get_current())
        
        
        # One for registration, one for new email
        self.assertEqual(len(mail.outbox), 2)
        
        updated_user = NewEmail.objects.activate_email(new_user, new_email.activation_key)
        self.assertEqual(updated_user.email, new_email.email)
        self.assertEqual(User.objects.get(pk=new_user.pk).email, new_email.email)
        self.assertRaises(NewEmail.DoesNotExist, NewEmail.objects.get, user=new_user)
    
    def test_rank(self):
        user = RegistrationProfile.objects.create_inactive_user(site=Site.objects.get_current(),
                                                                    **self.user_info)
        
        profile = RegistrationProfile.objects.get(user=user)
        RegistrationProfile.objects.activate_user(profile.activation_key)
        
        self.assertEqual(user.rank(), User.RANKS[0])
        self.assertEqual(user.recipes_until_next_rank(), 2)
        
        Cuisine(name="Andere").save()
        for i in xrange(256):
            if i == 100:
                # 100 Recipes added
                self.assertEqual(user.rank(), User.RANKS[6])
                self.assertEqual(user.recipes_until_next_rank(), 28)
            Recipe(name=str(i), author=user, course=0, 
                   description='test', portions=1, active_time=1,
                   passive_time=1, instructions='test').save()
            
        self.assertEqual(user.rank(), User.RANKS[8])
        self.assertEqual(user.recipes_until_next_rank(), 0)