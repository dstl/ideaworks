# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import unittest
import time
import json
import urlparse

from django.core import urlresolvers
from django.test import client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from registration.models import RegistrationProfile
from tastypie_mongoengine import test_runner

# Access the API classes, functions that support it and the documents that define the objects
from contentapp import api
from contentapp import api_functions
import contentapp.documents as documents

class Test_Authentication_Base(test_runner.MongoEngineTestCase):
    """
    Base class to handle functions common throughout tests
    """

    api_name = 'v1'
    c = client.Client()

    def get_meta_and_objects(self, response):
        content = json.loads(response.content)
        return content['meta'], content['objects']

    """ User Handling Functions """
    def resourceListURI(self, resource_name):
        return urlresolvers.reverse('api_dispatch_list', kwargs={'api_name': self.api_name, 'resource_name': resource_name})

    def resourcePK(self, resource_uri):
        match = urlresolvers.resolve(resource_uri)
        return match.kwargs['pk']

    def resourceDetailURI(self, resource_name, resource_pk):
        return urlresolvers.reverse('api_dispatch_detail', kwargs={'api_name': self.api_name, 'resource_name': resource_name, 'pk': resource_pk})

    def fullURItoAbsoluteURI(self, uri):
        scheme, netloc, path, query, fragment = urlparse.urlsplit(uri)
        return urlparse.urlunsplit((None, None, path, query, fragment))

    def add_user(self, email=None, first_name=None, last_name=None):
        """ Add users
            Need all 3 optionals.s """
        
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
        
        # Now logout so that the rest of the tests are done on API key only
        resp = self.c.post(reverse('auth_logout'))
        
        # Give all other tests access to the user and API key
        user = User.objects.get(email=email)
        api_key = user.api_key.key

        return user, api_key
    
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

    
    def build_headers(self, user, api_key):
        """ Build request headers for calls requiring authentication """
        
        headers={"HTTP_AUTHORIZATION":"ApiKey %s:%s"%(user.username, api_key)}
        return headers


#@utils.override_settings(DEBUG=True)
class Test_POST_Site_Content(Test_Authentication_Base):

    def setUp(self):
        
        self.pm =   {"classification"                : "PUBLIC",
                     "classification_short"          : "PU",
                     "classification_rank"           : 0,
                     "national_caveats_primary_name" : "MY EYES ONLY",
                     "national_caveats_members"      : ["ME"],
                     "national_caveats_rank"         : 3,
                     "descriptor"                    : "private",
                     "codewords"                     : ["banana1","banana2"],
                     "codewords_short"               : ["b1","b2"]
                     }

    def test_POST_content_as_anon(self):
        """POST site content as AnonymousUser and FAIL. Staff status should be set through the admin interface. """
        
        doc = {"status"             : "published",
               "title"              : "Create an idea.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "user_guide",
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('site_content'), json.dumps(doc), content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_POST_content_as_regular_user(self):
        """POST site content as regular user and fail. Only staff or superuser should be able to POST. """
        
        # Add a user and gain access to the API key and user
        user, api_key = self.add_user()
        headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "published",
               "title"              : "Create an idea.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "user_guide",
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('site_content'), json.dumps(doc), content_type='application/json', **headers)
        self.assertEqual(response.status_code, 401)

    
    def test_POST_content_as_staff(self):
        """POST site content as staff member. Staff status should be set through the admin interface. """
        
        # Upgrade the user privs
        user, api_key = self.add_user()
        user = self.give_privileges(user, priv='staff')
        headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "published",
               "title"              : "Create an idea.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "user_guide",
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('site_content'), json.dumps(doc), content_type='application/json', **headers)
        self.assertEqual(response.status_code, 201)
        
    def test_POST_content_as_superuser(self):
        """POST site content as superuser. Staff status should be set through the admin interface. """
        
        # Upgrade the user privs
        user, api_key = self.add_user()
        user = self.give_privileges(user, priv='superuser')
        headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "published",
               "title"              : "Create an idea.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "user_guide",
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('site_content'), json.dumps(doc), content_type='application/json', **headers)
        self.assertEqual(response.status_code, 201)
   
    def test_POST_content_no_pm(self):
        """Cannot post content without a pm. """
        
        # Upgrade the user privs
        user, api_key = self.add_user()
        user = self.give_privileges(user, priv='superuser')
        headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "published",
               "title"              : "Create an idea.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "user_guide"}
        
        response = self.c.post(self.resourceListURI('site_content'), json.dumps(doc), content_type='application/json', **headers)
        self.assertEqual(response.status_code, 400)
         

#@utils.override_settings(DEBUG=True)
class Test_GET_Site_Content(Test_Authentication_Base):

    def setUp(self):
        
        self.pm =   {"classification"                : "PUBLIC",
                     "classification_short"          : "PU",
                     "classification_rank"           : 0,
                     "national_caveats_primary_name" : "MY EYES ONLY",
                     "national_caveats_members"      : ["ME"],
                     "national_caveats_rank"         : 3,
                     "descriptor"                    : "private",
                     "codewords"                     : ["banana1","banana2"],
                     "codewords_short"               : ["b1","b2"]
                     }

        # Upgrade the user privs
        user, api_key = self.add_user()
        user = self.give_privileges(user, priv='staff')
        headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "published",
               "title"              : "Create an idea.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "user_guide",
               "index"              : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('site_content'), json.dumps(doc), content_type='application/json', **headers)
        self.resource_uri = response['location']
        self.assertEqual(response.status_code, 201)
        
        
    def test_GET_content_anon(self):
        """GET site content as AnonymousUser. """
                        
        params = '?type=user_guide'
        response = self.c.get(self.resourceListURI('site_content')+params)
        self.assertEqual(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['total_count'], 1)
        self.assertEquals(len(objects), 1)
        
        
    def test_GET_content_regular_user(self):
        """GET site content as regular user. """
        
        # Add a user and gain access to the API key and user
        user, api_key = self.add_user()
        headers = self.build_headers(user, api_key)
                        
        params = '?type=user_guide'
        response = self.c.get(self.resourceListURI('site_content')+params, **headers)
        self.assertEqual(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['total_count'], 1)
        self.assertEquals(len(objects), 1)

    def test_GET_content_staff(self):
        """GET site content as staff user. """
        
        # Add a user and gain access to the API key and user
        user, api_key = self.add_user()
        user = self.give_privileges(user, priv='staff')
        headers = self.build_headers(user, api_key)
                        
        params = '?type=user_guide'
        response = self.c.get(self.resourceListURI('site_content')+params, **headers)
        self.assertEqual(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['total_count'], 1)
        self.assertEquals(len(objects), 1)

    def test_GET_regular_user_status(self):
        """GET site content by content status. """
        
        params = '?type=user_guide&status=draft'
        response = self.c.get(self.resourceListURI('site_content')+params)
        self.assertEqual(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['total_count'], 0)
        self.assertEquals(len(objects), 0)

    def test_GET_by_type_and_index_no_docs(self):
        """Try and fail to get the document based on index.
           Proves that the following test doesn't just work by accident.
        """
                
        # Add a user and gain access to the API key and user
        user, api_key = self.add_user(email="dave@dave.com", first_name='dave', last_name='dave')
        headers = self.build_headers(user, api_key)
        
        params = '?type=user_guide&index=true'
        response = self.c.get(self.resourceListURI('site_content')+params, **headers)
        self.assertEqual(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['total_count'], 0)
        self.assertEquals(len(objects), 0)
        
    def test_GET_by_type_and_index(self):
        """GET site content by the type and whether or not its an index page """
        
        # Via the db, change the index of this doc to True
        id = self.resource_uri.strip('/').split('/')[-1]
        documents.Content.objects.get(id=id).update(**{"set__index":True})
        
        # Add a user and gain access to the API key and user
        user, api_key = self.add_user(email="dave@dave.com", first_name='dave', last_name='dave')
        headers = self.build_headers(user, api_key)
        
        params = '?type=user_guide&index=true'
        response = self.c.get(self.resourceListURI('site_content')+params, **headers)
        self.assertEqual(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['total_count'], 1)
        self.assertEquals(len(objects), 1)


#@utils.override_settings(DEBUG=True)
class Test_PUTPATCH_Site_Content(Test_Authentication_Base):

    def setUp(self):
        
        self.pm =   {"classification"                : "PUBLIC",
                     "classification_short"          : "PU",
                     "classification_rank"           : 0,
                     "national_caveats_primary_name" : "MY EYES ONLY",
                     "national_caveats_members"      : ["ME"],
                     "national_caveats_rank"         : 3,
                     "descriptor"                    : "private",
                     "codewords"                     : ["banana1","banana2"],
                     "codewords_short"               : ["b1","b2"]
                     }

        # Upgrade the user privs
        user, api_key = self.add_user()
        user = self.give_privileges(user, priv='staff')
        self.headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "draft",
               "title"              : "Create an idea.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "user_guide",
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('site_content'), json.dumps(doc), content_type='application/json', **self.headers)
        self.resource_uri = response['location']
        self.assertEqual(response.status_code, 201)

        
    def test_PUT_content_anon(self):
        """PUT site content as AnonymousUser. """

        new_content = {"title":"Help: How to create an idea",
                       "status" : "published",
                       "protective_marking" : self.pm}
        
        response = self.c.put(self.resource_uri, json.dumps(new_content), content_type='application/json')
        self.assertEquals(response.status_code, 401)

        
    def test_PUT_content_regular_user(self):
        """PUT site content as regular user. """

        # Add vanilla user
        user, api_key = self.add_user(email="new_user@ideaworks.com")
        headers = self.build_headers(user, api_key)

        new_content = {"status" : "published",
                       "protective_marking" : self.pm}
        
        response = self.c.put(self.resource_uri, json.dumps(new_content), content_type='application/json', **headers)
        self.assertEquals(response.status_code, 401)
        
    def test_PUT_content_staff(self):
        """PUT site content as staff user. """

        # Add and then upgrade a new user
        user, api_key = self.add_user(email="new_staff@ideaworks.com")
        user = self.give_privileges(user, priv='staff')
        headers = self.build_headers(user, api_key)

        new_content = {"status"             : "published",
                       "title"              : "Create an idea.",
                       "summary"            : "How to create an idea.",
                       "body"               : "Here's the content of the <b> site content </b> that includes html",
                       "type"               : "user_guide",
                       "protective_marking" : self.pm}
        
        response = self.c.put(self.resource_uri, json.dumps(new_content), content_type='application/json', **headers)
        self.assertEquals(response.status_code, 204)

    def test_PUT_content_staff_no_protective_marking(self):
        """PUT site content and fail because of lack of PM. """

        # Add and then upgrade a new user
        user, api_key = self.add_user(email="new_staff@ideaworks.com")
        user = self.give_privileges(user, priv='staff')
        headers = self.build_headers(user, api_key)

        new_content = {"status"             : "published",
                       "title"              : "Create an idea.",
                       "summary"            : "How to create an idea.",
                       "body"               : "Here's the content of the <b> site content </b> that includes html",
                       "type"               : "user_guide"
                       }
        
        response = self.c.put(self.resource_uri, json.dumps(new_content), content_type='application/json', **headers)
        self.assertEquals(response.status_code, 400)
        self.assertGreater(json.loads(response.content)['error'][0].find('protective_marking'), -1)

    def test_PUT_content_staff_check_modified(self):
        """PUT site content and check modified date changes. """

        # Get the original document
        response = self.c.get(self.resource_uri)
        meta, objects = self.get_meta_and_objects(response)
        orig_modified = objects[0]['modified']

        # Add and then upgrade a new user
        user, api_key = self.add_user(email="new_staff@ideaworks.com")
        user = self.give_privileges(user, priv='staff')
        headers = self.build_headers(user, api_key)

        # Wait a sec just to make the modified time clearly different
        time.sleep(1)

        new_content = {"status"             : "published",
                       "title"              : "Create an idea.",
                       "summary"            : "How to create an idea.",
                       "body"               : "Here's the content of the <b> site content </b> that includes html",
                       "type"               : "user_guide",
                       "protective_marking" : self.pm}
        
        response = self.c.put(self.resource_uri, json.dumps(new_content), content_type='application/json', **headers)
        self.assertEquals(response.status_code, 204)
        
        response = self.c.get(self.resource_uri)
        meta, objects = self.get_meta_and_objects(response)
        modified = objects[0]['modified']
        self.assertGreater(modified, orig_modified)
        

#@utils.override_settings(DEBUG=True)
class Test_DELETE_Site_Content(Test_Authentication_Base):

    def setUp(self):
        
        self.pm =   {"classification"                : "PUBLIC",
                     "classification_short"          : "PU",
                     "classification_rank"           : 0,
                     "national_caveats_primary_name" : "MY EYES ONLY",
                     "national_caveats_members"      : ["ME"],
                     "national_caveats_rank"         : 3,
                     "descriptor"                    : "private",
                     "codewords"                     : ["banana1","banana2"],
                     "codewords_short"               : ["b1","b2"]
                     }

        # Upgrade the user privs
        user, api_key = self.add_user()
        user = self.give_privileges(user, priv='staff')
        self.headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "draft",
               "title"              : "Create an idea.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "user_guide",
               "index"              : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('site_content'), json.dumps(doc), content_type='application/json', **self.headers)
        self.resource_uri = response['location']
        self.assertEqual(response.status_code, 201)

        
    def test_DELETE_content_anon(self):
        """Delete site content as AnonymousUser. """

        response = self.c.delete(self.resource_uri, content_type='application/json')
        self.assertEquals(response.status_code, 401)

        
    def test_DELETE_content_regular_user(self):
        """Delete site content as regular user. """

        # Add vanilla user
        user, api_key = self.add_user(email="new_user@ideaworks.com")
        headers = self.build_headers(user, api_key)
        
        response = self.c.delete(self.resource_uri, content_type='application/json', **headers)
        self.assertEquals(response.status_code, 401)
        
    def test_DELETE_content_staff(self):
        """Delete site content as staff user. """

        # Add and then upgrade a new user
        user, api_key = self.add_user(email="new_staff@ideaworks.com")
        user = self.give_privileges(user, priv='staff')
        headers = self.build_headers(user, api_key)

        response = self.c.delete(self.resource_uri, content_type='application/json', **headers)
        self.assertEquals(response.status_code, 204)
        self.assertEquals(self.c.get(self.resource_uri).status_code, 404)

        """******* Not supporting PATCH - TFD ******** """

#@utils.override_settings(DEBUG=True)
class Test_GET_Site_Content_ProtectiveMarking(Test_Authentication_Base):

    def setUp(self):
        
        self.pm =   {"classification"                : "PUBLIC",
                     "classification_short"          : "PU",
                     "classification_rank"           : 0,
                     "national_caveats_primary_name" : "MY EYES ONLY",
                     "national_caveats_members"      : ["ME"],
                     "national_caveats_rank"         : 3,
                     "descriptor"                    : "private",
                     "codewords"                     : ["banana1","banana2"],
                     "codewords_short"               : ["b1","b2"]
                     }

        # Upgrade the user privs
        user, api_key = self.add_user()
        user = self.give_privileges(user, priv='staff')
        headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "published",
               "title"              : "Create an idea.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "user_guide",
               "index"              : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('site_content'), json.dumps(doc), content_type='application/json', **headers)
        self.resource_uri = response['location']
        self.assertEqual(response.status_code, 201)
        
        
    def test_GET_content_document_level(self):
        """Check that there is protective maring at the document level. """
                        
        params = '?type=user_guide'
        response = self.c.get(self.resourceListURI('site_content')+params)
        self.assertEqual(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['protective_marking']['classification'], self.pm['classification'])

    def test_GET_content_meta(self):
        """Check that there is protective maring at meta level. """
                        
        params = '?type=user_guide'
        response = self.c.get(self.resourceListURI('site_content')+params)
        self.assertEqual(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertTrue(meta.has_key('max_pm'))
                

if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']
    unittest.main()