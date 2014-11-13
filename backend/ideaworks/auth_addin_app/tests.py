
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

"""
Most of the auth stuff is out of the box inherited from registration_email, registration and django.auth.
I've overridden the login view to pass back a user id and the user's API key for the front-end to use in all API calls.
"""

from django.test import TestCase
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User
from django.conf import settings

from registration.models import RegistrationProfile # model to hold a registration profile - precursor to user account
 
class CustomCookieTests(TestCase):
    """
    The auth is responding to a login attempt with custom cookies that
    the front-end then uses for user display and permissions (in combination with sessions).
    These tests ensure that setup works OK.
    """
    def setUp(self):
        """
        Basic setup for each test: creates a user with an API key
        """

        # Register a user
        resp = self.client.post(reverse('registration_register'),
                                data={'username': 'bob',
                                      'email': 'bob@example.com',
                                      'first_name' : 'bob',
                                      'last_name' : 'roberts',
                                      'organisation' : 'org',
                                      'team' : 'team',
                                      'password1': 'test_password',
                                      'password2': 'test_password',
                                      'tos': True})
                
        self.user = User.objects.get(email='bob@example.com')
        self.api_key = self.user.api_key.key
        
    def tearDown(self):
        """
        Drop the profiles that got created for each test.
        """
        RegistrationProfile.objects.all().delete()
        
    def test_login(self):
        """
        Tests that successful login returns a user id and API key.
        """
        
        # Now login
        resp = self.client.post(reverse('auth_login'),
                               data={'username' : 'bob@example.com',
                                     'password' : 'test_password'})
        self.assertEquals(self.api_key, resp.cookies.get('api_key').value)
        self.assertEquals(self.user.username, resp.cookies.get('user_id').value)

    def test_login_user_info(self):
        """
        Tests that login successfully responds with a friendly user name and email addresss.
        """
        
        # Now login
        resp = self.client.post(reverse('auth_login'),
                               data={'username' : 'bob@example.com',
                                     'password' : 'test_password'})
        
        # Build up friendly user name
        user_name = self.user.first_name.title() + ' ' + self.user.last_name.title()
        
        self.assertEquals(user_name, resp.cookies.get('user_name').value)
        self.assertEquals(self.user.email, resp.cookies.get('user_email').value)

    def test_login_user_roles_info_active(self):
        """
        Tests that login successfully responds with user active level.
        """
        resp = self.client.post(reverse('auth_login'),
                               data={'username' : 'bob@example.com',
                                     'password' : 'test_password'})
        self.assertEquals('true', resp.cookies.get('user_active').value)
    
    def test_login_user_roles_info_basic_user(self):
        """
        Tests that login successfully responds with role info.
        """
        resp = self.client.post(reverse('auth_login'),
                               data={'username' : 'bob@example.com',
                                     'password' : 'test_password'})
        self.assertEquals('', resp.cookies.get('user_roles').value)

    def test_login_user_roles_info_superuser(self):
        """
        Tests that login successfully responds with role info.
        """
        # Make the user a superuser
        self.user.is_superuser = True
        self.user.save()
        self.assertTrue(self.user.is_superuser)
        
        resp = self.client.post(reverse('auth_login'),
                               data={'username' : 'bob@example.com',
                                     'password' : 'test_password'})
        self.assertEquals('super', resp.cookies.get('user_roles').value)

    def test_login_user_roles_info_staff(self):
        """
        Tests that login successfully responds with role info.
        """
        # Make the user a superuser
        self.user.is_staff = True
        self.user.save()
        self.assertTrue(self.user.is_staff)
        
        resp = self.client.post(reverse('auth_login'),
                               data={'username' : 'bob@example.com',
                                     'password' : 'test_password'})
        self.assertEquals('staff', resp.cookies.get('user_roles').value)

    def test_login_user_roles_info_staff_and_super(self):
        """
        Tests that login successfully responds with role info.
        """
        # Make the user a superuser
        self.user.is_staff     = True
        self.user.is_superuser = True
        self.user.save()
        self.assertTrue(self.user.is_staff)
        self.assertTrue(self.user.is_superuser)
        
        resp = self.client.post(reverse('auth_login'),
                               data={'username' : 'bob@example.com',
                                     'password' : 'test_password'})
        self.assertEquals('super,staff', resp.cookies.get('user_roles').value)


    def test_login_redirect_safe(self):
        """
        Tests for redirecting successfully based on the modifications to is_safe_url
        """
        
        # Now login
        resp = self.client.post(reverse('auth_login'),
                               data={'username' : 'bob@example.com',
                                     'password' : 'test_password',
                                     'next'     : 'http://ideaworks/#'})
        self.assertEquals(resp['location'], 'http://testserver/ideaworks_testserver')
        self.assertEquals(resp.status_code, 302)
        
        
    def test_login_redirect_not_safe(self):
        """
        Tests for redirecting successfully based on the modifications to is_safe_url
        """
        
        # Now login
        resp = self.client.post(reverse('auth_login'),
                               data={'username' : 'bob@example.com',
                                     'password' : 'test_password',
                                     'next'     : 'http://unsafe_domain/#'})
        self.assertEquals(resp['location'], 'http://testserver'+settings.LOGIN_REDIRECT_URL)
        self.assertEquals(resp.status_code, 302)

    def test_logout_redirect_safe(self):
        """
        Tests for redirecting successfully based on the modifications to is_safe_url
        """
        
        # Now login
        resp = self.client.post(reverse('auth_logout'),
                               data={'next'     : 'http://ideaworks/#'})
        self.assertEquals(resp['location'], 'http://testserver/ideaworks_testserver')
        self.assertEquals(resp.status_code, 302)
    
    def test_logout_redirect_not_safe(self):
        """
        Tests for redirecting successfully based on the modifications to is_safe_url
        """
        
        # Now login
        resp = self.client.post(reverse('auth_logout'),
                               data={'next'     : 'http://unsafe_domain/#'})
        self.assertEquals(resp['location'], 'http://testserver'+settings.LOGIN_REDIRECT_URL)
        self.assertEquals(resp.status_code, 302)