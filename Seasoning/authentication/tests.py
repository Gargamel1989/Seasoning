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
from authentication.models import User, RegistrationProfile
import datetime
import re


class UserModelTestCase(TestCase):
    
    def test_user_creation(self):
        User.objects.create_user("testuser", "testuser@test.be", 
                                 User.MALE, datetime.date.today(), "haha")
        new_user = User.objects.get(email="testuser@test.be")
        self.assertEqual(new_user.username, 'testuser')
        self.assertEqual(new_user.gender, User.MALE)
        self.assertEqual(new_user.date_of_birth, datetime.date.today())
        self.assertEqual(new_user.avatar.url, '/media/images/users/no_image.png')
        self.assertEqual(new_user.is_active, True)
        self.assertEqual(new_user.is_staff, False)
        self.assertEqual(new_user.is_superuser, False)
        self.assertEqual(new_user.date_joined, datetime.date.today())
        User.objects.create_superuser("testsuperuser", "testsuperuser@test.be", 
                                      User.MALE, datetime.date.today(), "haha")
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
                         "Registration information for alice")

        
    