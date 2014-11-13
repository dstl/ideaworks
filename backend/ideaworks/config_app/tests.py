
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import json
import urlparse

from django.core import urlresolvers
from django.test import client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from registration.models import RegistrationProfile
from tastypie_mongoengine import test_runner

class Test_Authentication_Base(test_runner.MongoEngineTestCase):
    """
    Base class to handle functions common throughout tests
    """

    api_name = 'v1'
    c = client.Client()

    def get_meta_and_objects(self, response):
        content = json.loads(response.content)
        return content['meta'], content['objects']

    def resourceListURI(self, resource_name):
        """ Get the resource list uri """
        return urlresolvers.reverse('api_dispatch_list', kwargs={'api_name': self.api_name, 'resource_name': resource_name})

    def resourcePK(self, resource_uri):
        """Get the resource primary key from a uri"""
        match = urlresolvers.resolve(resource_uri)
        return match.kwargs['pk']

    def resourceDetailURI(self, resource_name, resource_pk):
        """ Get the resource detail URI """
        return urlresolvers.reverse('api_dispatch_detail', kwargs={'api_name': self.api_name, 'resource_name': resource_name, 'pk': resource_pk})

    def fullURItoAbsoluteURI(self, uri):
        """ Get the full URI for a resource """
        scheme, netloc, path, query, fragment = urlparse.urlsplit(uri)
        return urlparse.urlunsplit((None, None, path, query, fragment))

    def add_user(self, email=None, first_name=None, last_name=None):
        """ Add users. Need all 3 optionals """
        
        # Allow ability to add an email from tests
        if email==None:
            email = 'bob@example.com'
        if first_name==None:
            first_name = 'bob'
        if last_name==None:
            last_name = 'roberts'
            
        # Register a new user
        resp = self.c.post(reverse('registration_register'),
                           data={'email': email,
                                 'first_name' : first_name,   'last_name' : last_name,
                                 'organisation' : 'org', 'team' : 'team',
                                 'password1': 'test_password',  'password2': 'test_password',
                                 'tos': True})
        
        resp = self.c.post(reverse('auth_logout'))
        
        # Give all other tests access to the user and API key
        user = User.objects.get(email=email)
        api_key = user.api_key.key

        return user, api_key
    
    def build_headers(self, user, api_key):
        """ Build request headers for calls requiring authentication """
        
        headers={"HTTP_AUTHORIZATION":"ApiKey %s:%s"%(user.username, api_key)}
        return headers

    def give_privileges(self, user, priv):
        """ makes the user superuser | staff """

        if priv.lower() == 'staff':
            user.is_staff = True
        elif priv.lower() == 'superuser':
            user.is_superuser = True
        else:
            print 'failed to set privileges (%s) for user %' %(priv, user)
        
        user.save()
        return user

#------------------------------------------------------------------------------------------------------------

#@utils.override_settings(DEBUG=True)
class Test_Config_API_Access(Test_Authentication_Base):
    """
    Tests that clients can access the Config API under different users.
    """
        
    def test_anon_access_to_config(self):
        """ Anonymous access to the api config """
        
        # Don't actually use the headers in the call
        response = self.c.get(self.resourceListURI('config'))
        self.assertEquals(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['total_count'], 1)
        self.assertTrue(objects[0].has_key('application_name'))
        
    def test_user_access_to_config(self):
        """ Authenticated user access to the api config """
        
        user, api_key = self.add_user(email='user1@app.com')
        headers = self.build_headers(user, api_key)
        
        # Don't actually use the headers in the call
        response = self.c.get(self.resourceListURI('config'), **headers)
        self.assertEquals(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['total_count'], 1)
        self.assertTrue(objects[0].has_key('application_name'))
        
    def test_staff_access_to_config(self):
        """ Authenticated user access to the api config """
        
        user, api_key = self.add_user(email='staff@app.com')
        user = self.give_privileges(user, 'staff')
        headers = self.build_headers(user, api_key)
        
        # Don't actually use the headers in the call
        response = self.c.get(self.resourceListURI('config'), **headers)
        self.assertEquals(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['total_count'], 1)
        self.assertTrue(objects[0].has_key('application_name'))
        

        
        
        
        
        