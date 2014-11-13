
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham


import unittest


# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 

'''
Test files are based on the data type they are supporting.

feedback_tests.py - feedback functions
-----------------

    GETTING
    - try to access feedback
        - anon / public user - NOT AUTHORIZED.
        - submitter - can access only their feedback
        - staff - AUTHORIZED
        - admin - AUTHORIZED

    - as authorized, GET all (json/xml/rss)
    - filter by type
    - sort by created/modified
    
    POSTING
    - try to add feedback as all types of users:
        - anon - No
        - user - OK
        - staff - OK
    
    PUT/PATCH
    - try to edit as staff
    - try to edit as publisher
    
    COMMENTS - POST.
    - Try to add comment as staff
    - Try to add comment as reg user
    - Try to add comment as anon - fail.
    

'''

import copy
import time
import json
import urlparse
from xml.dom.minidom import parseString

from django.core import urlresolvers
from django.test import client
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from registration.models import RegistrationProfile

# Access the API classes, functions that support it and the documents that define the objects
from contentapp import api
from contentapp import api_functions
from contentapp import documents

#from tastypie_mongoengine import resources as tastypie_mongoengine_resources, test_runner
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
        
        # Now logout the user, so everything else is done on API key
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
class Test_POST_Feedback(Test_Authentication_Base):

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

    def test_POST_feedback_as_anon(self):
        """POST Feedback as AnonymousUser - Fail. Only reg users or staff or super can leave feedback. """
        
        doc = {"status"             : "published",
               "title"              : "Create an idea.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json')
        self.assertEqual(response.status_code, 401)

    def test_POST_content_as_regular_user(self):
        """POST site content as regular user and succeed. """
        
        # Add a user and gain access to the API key and user
        user, api_key = self.add_user()
        headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "published",
               "title"              : "Why don't you allow....",
               "summary"            : "Here's how...",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **headers)
        #print response.content
        self.assertEqual(response.status_code, 201)

    
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
               "public"             : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **headers)
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
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **headers)
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
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **headers)
        self.assertEqual(response.status_code, 400)


#@utils.override_settings(DEBUG=True)
class Test_PUT_Feedback(Test_Authentication_Base):

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

        user, api_key = self.add_user()
        self.headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "draft",
               "title"              : "Create an idea.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "user_guide",
               "public"             : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **self.headers)
        self.resource_uri = response['location']
        self.assertEqual(response.status_code, 201)

        
    def test_PUT_content_anon(self):
        """PUT site content as AnonymousUser. """

        new_content = {"title":"Help: How to create an idea",
                       "status" : "published",
                       "protective_marking" : self.pm}
        
        response = self.c.put(self.resource_uri, json.dumps(new_content), content_type='application/json')
        self.assertEquals(response.status_code, 401)

        
    def test_PUT_content_publisher(self):
        """PUT site content as the publisher user. """

        # using the self.headers = the original autheor

        new_content = {"status"             : "published",
                       "title"              : "Feedback from me",
                       "summary"            : "A summary of my feedback",
                       "body"               : "Here's the content of the <b> site content </b> that includes html",
                       "type"               : "feedback",
                       "protective_marking" : self.pm}
        
        response = self.c.put(self.resource_uri, json.dumps(new_content), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 204)

    def test_PUT_content_regular_user(self):
        """PUT site content as regular user. """

        # Add vanilla user
        user, api_key = self.add_user(email="new_user@ideaworks.com")
        headers = self.build_headers(user, api_key)

        new_content = {"status"             : "published",
                       "title"              : "Feedback from me",
                       "summary"            : "A summary of my feedback",
                       "body"               : "Here's the content of the <b> site content </b> that includes html",
                       "type"               : "feedback",
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

        # Add and then upgrade a new user
        user, api_key = self.add_user(email="new_staff@ideaworks.com")
        user = self.give_privileges(user, priv='staff')
        headers = self.build_headers(user, api_key)

        # Get the original document
        response = self.c.get(self.resource_uri, **headers)
        meta, objects = self.get_meta_and_objects(response)
        orig_modified = objects[0]['modified']

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
        
        response = self.c.get(self.resource_uri, **headers)
        meta, objects = self.get_meta_and_objects(response)
        modified = objects[0]['modified']
        self.assertGreater(modified, orig_modified)

#TODO: Need tests to cover POST to feedback.

#@utils.override_settings(DEBUG=True)
class Test_GET_Feedback(Test_Authentication_Base):

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

        user, api_key = self.add_user()
        self.headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "draft",
               "title"              : "Heres some feedback.",
               "summary"            : "Here is how I would do this.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **self.headers)
        self.resource_uri = response['location']
        self.assertEqual(response.status_code, 201)

    def extract_entries(self, feed):
        """ Get the entries into a python structure and out of xml""" 
        
        entries = feed.getElementsByTagName('entry')
        entry_list = []
        for entry in entries:
            entry_dict = {}
            for node in entry.childNodes:
                try:
                    entry_dict[node.nodeName] = node.childNodes[0].nodeValue
                except:
                    pass
            entry_list.append(entry_dict)
        return entry_list

    def extract_top_level_node(self, feed, key):

        try:
            return feed.getElementsByTagName(key)[0].childNodes[0].nodeValue
        except:
            return None

    def extract_feed_level_content(self, feed):
        """ Extracts the feed (top) level content"""

        feed_dict = {}
        feed = feed.getElementsByTagName('feed')[0]
        feed_dict['title']       = self.extract_top_level_node(feed, 'title')
        feed_dict['description'] = self.extract_top_level_node(feed, 'description')
        feed_dict['link']        = self.extract_top_level_node(feed, 'link')
        feed_dict['updated']     = self.extract_top_level_node(feed, 'updated')
        return feed_dict

    def extract_feed_from_response(self, response):
        """ Gets the feed content out of the response object """
        
        feed     = parseString(response.content)
        feed_out = self.extract_feed_level_content(feed)
        feed_out['entries'] = self.extract_entries(feed)
        
        return feed_out

    def test_GET_public_as_anon(self):
        """ Get the public feedback items as anonymous"""
        
        doc = {"status"             : "draft",
               "title"              : "Here's some more feedback.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : True,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **self.headers)
        resource_uri = response['location']
        self.assertEqual(response.status_code, 201)
        
        # Get only the public ones
        response = self.c.get(self.resourceListURI('feedback'))
        self.assertEquals(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)

    def test_GET_public_as_reg_user(self):
        """ Get the public feedback items as registered user"""
        
        doc = {"status"             : "draft",
               "title"              : "Here's some more feedback.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : True,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **self.headers)
        resource_uri = response['location']
        self.assertEqual(response.status_code, 201)
        
        # Get only the public ones
        response = self.c.get(self.resourceListURI('feedback'))
        self.assertEquals(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)

    def test_GET_private_as_anon(self):
        """ Get the private feedback as anon user - fail"""
        
        doc = {"status"             : "draft",
               "title"              : "Here's some more feedback.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **self.headers)
        resource_uri = response['location']
        self.assertEqual(response.status_code, 201)
        
        # Get only the public ones
        response = self.c.get(self.resourceListURI('feedback'))
        self.assertEquals(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 0)

    def test_GET_private_as_reg_user(self):
        """ Get the private feedback as a reg user who didn't contribute the content - fail"""
        
        doc = {"status"             : "draft",
               "title"              : "Here's some more feedback.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **self.headers)
        resource_uri = response['location']
        self.assertEqual(response.status_code, 201)
        
        # Get only the public ones
        user, api_key = self.add_user(email="different_user@ideaworks.com")
        headers = self.build_headers(user, api_key)
        
        response = self.c.get(self.resourceListURI('feedback'), **headers)
        self.assertEquals(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 0)

    def test_GET_private_as_contributor(self):
        """ Get the private feedback as a reg user who contributed the content - succeed"""
        
        doc = {"status"             : "draft",
               "title"              : "Here's some more feedback.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **self.headers)
        resource_uri = response['location']
        self.assertEqual(response.status_code, 201)
                
        response = self.c.get(self.resourceListURI('feedback'), **self.headers)
        self.assertEquals(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 2)

    def test_GET_private_as_staff(self):
        """ Get all feedback as staff"""
        
        # New user no privs
        user, api_key = self.add_user(email="different_user@ideaworks.com")
        user_headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "draft",
               "title"              : "Here's some more feedback.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **user_headers)
        self.assertEqual(response.status_code, 201)
        
        user, api_key = self.add_user(email="different_user@ideaworks.com")
        user = self.give_privileges(user, priv='staff')
        staff_headers = self.build_headers(user, api_key)
                
        response = self.c.get(self.resourceListURI('feedback'), **staff_headers)
        self.assertEquals(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 2)

    def test_GET_private_as_staff_RSS(self):
        """ Get all feedback as staff via RSS feed"""
        
        # New user no privs
        user, api_key = self.add_user(email="different_user@ideaworks.com")
        user_headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "draft",
               "title"              : "Here's some more feedback.",
               "summary"            : "How to create an idea.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **user_headers)
        self.assertEqual(response.status_code, 201)
        
        user, api_key = self.add_user(email="different_user@ideaworks.com")
        user = self.give_privileges(user, priv='staff')
        staff_headers = self.build_headers(user, api_key)
                
        response = self.c.get(self.resourceListURI('feedback')+'?format=rss', **staff_headers)
        self.assertEquals(response.status_code, 200)
        
        # Now check the right amount of entries are present
        docs = documents.Feedback.objects.all()
        response = self.c.get(self.resourceListURI('feedback') + "?format=rss", **staff_headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(len(feed['entries']), len(docs))
        
#@utils.override_settings(DEBUG=True)
class Test_POST_Comment_On_Public_Feedback(Test_Authentication_Base):
    
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

        user, api_key = self.add_user()
        self.headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "draft",
               "title"              : "Heres some feedback.",
               "summary"            : "Here is how I would do this.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : True,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **self.headers)
        self.resource_uri = response['location']
        self.assertEqual(response.status_code, 201)


    def test_comment_on_public_feedback_anon(self):
        """ Anon user attempts to comment on public feedback - FAILS"""
        
        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "Thanks for your feedback...",
                       "protective_marking" : self.pm}
        
        response = self.c.post(self.resource_uri + 'comments/', json.dumps(new_comment), content_type='application/json')
        self.assertEquals(response.status_code, 401)

    def test_comment_on_public_feedback_reg_user(self):
        """ Regular user attempts to comment on public feedback - SUCCEEDS"""

        # Get a new user
        user, api_key = self.add_user('ok_to_comment@ideaworks.com')
        headers = self.build_headers(user, api_key)

        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "Thanks for your feedback...",
                       "protective_marking" : self.pm}
        
        response = self.c.post(self.resource_uri + 'comments/', json.dumps(new_comment), content_type='application/json', **headers)
        self.assertEquals(response.status_code, 201)

    def test_comment_on_public_feedback_author(self):
        """ Staff user attempts to comment on public feedback - SUCCEEDS"""

        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "Thanks for your feedback...",
                       "protective_marking" : self.pm}

        # Use the author
        response = self.c.post(self.resource_uri + 'comments/', json.dumps(new_comment), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)

    def test_comment_on_public_feedback_staff(self):
        """ Staff user attempts to comment on public feedback - SUCCEEDS"""

        # Get a new user, and upgrade them.
        user, api_key = self.add_user('ok_to_comment@ideaworks.com')
        user = self.give_privileges(user, priv='staff')
        headers = self.build_headers(user, api_key)

        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "Thanks for your feedback...",
                       "protective_marking" : self.pm}
        
        response = self.c.post(self.resource_uri + 'comments/', json.dumps(new_comment), content_type='application/json', **headers)
        self.assertEquals(response.status_code, 201)

'''
#@utils.override_settings(DEBUG=True)
class Test_POST_Comment_On_Private_Feedback(Test_Authentication_Base):
    
    """
    At time of writing (May 2014), the intended behaviour was:
    1. comments on private feedback only allowed by super/staff and the author of the feedback - generate discussion.
    2. comments on public feedback allowed by any authenticated user. 
    
    I can't get this work, i think because there is a bug in django-tastypie-mongoengine
    that means authorization isn't properly checked for embedded documents.
    
    Here's the main issue described and open:
    
    https://github.com/wlanslovenija/django-tastypie-mongoengine/issues/70
    
    As such, the behaviour at the moment (with tests that pass) is that all
    authenticated users (irrespective of staff/superuser/author) can make comments
    on private feedback.
    
    """
    
    
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

        user, api_key = self.add_user()
        self.headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "draft",
               "title"              : "Heres some feedback.",
               "summary"            : "Here is how I would do this.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **self.headers)
        self.resource_uri = response['location']
        self.assertEqual(response.status_code, 201)
        

    def test_comment_on_private_feedback_anon(self):
        """ Anon user attempts to comment on private feedback - FAILS"""
        
        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "Thanks for your feedback...",
                       "protective_marking" : self.pm}
        
        response = self.c.post(self.resource_uri + 'comments/', json.dumps(new_comment), content_type='application/json')
        self.assertEquals(response.status_code, 401)

    def test_comment_on_private_feedback_reg_user(self):
        """ Regular user attempts to comment on private feedback
            Succeeds, but actually shouldn't do - its a registered tastypie issue. """

        # Get a new user
        user, api_key = self.add_user('ok_to_comment@ideaworks.com')
        headers = self.build_headers(user, api_key)

        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "Thanks for your feedback...",
                       "protective_marking" : self.pm}
        
        response = self.c.post(self.resource_uri + 'comments/', json.dumps(new_comment), content_type='application/json', **headers)
        self.assertEquals(response.status_code, 201)

    def test_comment_on_private_feedback_author(self):
        """ Staff user attempts to comment on private feedback - SUCCEEDS"""

        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "Thanks for your feedback...",
                       "protective_marking" : self.pm}

        # Use the author
        response = self.c.post(self.resource_uri + 'comments/', json.dumps(new_comment), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)

    def test_comment_on_private_feedback_staff(self):
        """ Staff user attempts to comment on private feedback - SUCCEEDS"""

        # Get a new user, and upgrade them.
        user, api_key = self.add_user('ok_to_comment@ideaworks.com')
        user = self.give_privileges(user, priv='staff')
        headers = self.build_headers(user, api_key)

        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "Thanks for your feedback...",
                       "protective_marking" : self.pm}
        
        response = self.c.post(self.resource_uri + 'comments/', json.dumps(new_comment), content_type='application/json', **headers)
        self.assertEquals(response.status_code, 201)
'''

#@utils.override_settings(DEBUG=True)
class Test_GET_Comments_On_Public_Feedback(Test_Authentication_Base):
    
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

        user, api_key = self.add_user()
        self.headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "draft",
               "title"              : "Heres some feedback.",
               "summary"            : "Here is how I would do this.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : True,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **self.headers)
        
        self.resource_uri = response['location']
        self.assertEqual(response.status_code, 201)

        # Apply some comments
        # Get a new user, and upgrade them.
        user, api_key = self.add_user('ok_to_comment@ideaworks.com')
        #user = self.give_privileges(user, priv='staff')
        staff_headers = self.build_headers(user, api_key)

        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "Thanks for your feedback...",
                       "protective_marking" : self.pm}
        
        response = self.c.post(self.resource_uri + 'comments/', json.dumps(new_comment), content_type='application/json', **staff_headers)
        self.assertEquals(response.status_code, 201)
        
        """
        ************
        Diagnosis...
        1. Can create feedback with public = False
        2. Cannot add comment to feedback when public = False - it fails in the lines just above this
        3. Can add comments to feedback when public = True
        
        This means that there is something wrong in the create_detail within the authorization
        being applied to the comments API.
        
        It is likely to be a check against public/private
        The create_detail within the authorization class applied to the embedded doc (comments in this case)
        does not get called (tried that), but the parent document authorization create_detail() function
        does get called. Try putting a simple print statement in each and then attempt to POST a comment to /comments/.
        
        So the parent authorization needs to conduct the check for whether the current user has authorization to
        post a comment.
        
        On the comments, neither create_list or update_detail are getting called. 
        
        Is this the case for the GET/read too? 
        
        """
        
    
    def test_public_anon(self):
        """ Anon user attempts to comment on public feedback - FAILS"""

        response = self.c.get(self.resource_uri+'comments/')
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)

    def test_public_reg_user(self):
        """ Regular user attempts to comment on public feedback - SUCCEEDS"""

        # Get a new user, and upgrade them.
        user, api_key = self.add_user('not_ok_to_read_comments@ideaworks.com')
        headers = self.build_headers(user, api_key)

        response = self.c.get(self.resource_uri+'comments/', **headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)

    def test_public_author(self):
        """ Regular user attempts to comment on public feedback - SUCCEEDS"""

        # Get a new user, and upgrade them.
        user, api_key = self.add_user('not_ok_to_read_comments@ideaworks.com')
        headers = self.build_headers(user, api_key)

        response = self.c.get(self.resource_uri+'comments/', **headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)

    def test_public_staff(self):
        """ Staff user attempts to comment on public feedback - SUCCEEDS"""

        response = self.c.get(self.resource_uri+'comments/', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)

'''

# NOT SUPPORTING PRIVATE COMMENTS BECAUSE OF THE ISSUES WITH AUTHORIZATION 
# FOR NESTED SUB-DOCUMENTS. 

#@utils.override_settings(DEBUG=True)
class Test_GET_Comments_On_Private_Feedback(Test_Authentication_Base):
    
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

        user, api_key = self.add_user()
        self.headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "draft",
               "title"              : "Heres some feedback.",
               "summary"            : "Here is how I would do this.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : False,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **self.headers)
        self.resource_uri = response['location']
        self.assertEqual(response.status_code, 201)

        # Apply some comments
        # Get a new user, and upgrade them.
        user, api_key = self.add_user('ok_to_comment@ideaworks.com')
        #user = self.give_privileges(user, priv='staff')
        staff_headers = self.build_headers(user, api_key)

        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "Thanks for your feedback...",
                       "protective_marking" : self.pm}
        
        comments_uri = self.resource_uri + 'comments/'
        print '**'*20
        #print comments_uri
        response = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **staff_headers)
        print response.status_code
        
        self.assertEquals(response.status_code, 201)
        
    def test_private_anon(self):
        """ Anon user attempts to comment on public feedback - FAILS"""

        response = self.c.get(self.resource_uri+'comments/')
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 0)

    def test_private_reg_user(self):
        """ Regular user attempts to comment on public feedback - SUCCEEDS"""

        # Get a new user, and upgrade them.
        user, api_key = self.add_user('not_ok_to_read_comments@ideaworks.com')
        headers = self.build_headers(user, api_key)

        response = self.c.get(self.resource_uri+'comments/', **headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 0)

    def test_private_author(self):
        """ Staff user attempts to comment on public feedback - SUCCEEDS"""

        response = self.c.get(self.resource_uri+'comments/', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)

    def test_private_staff(self):
        """ Staff user attempts to comment on public feedback - SUCCEEDS"""

        response = self.c.get(self.resource_uri+'comments/', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)

'''

#@utils.override_settings(DEBUG=True)
class Test_GET_Feedback_Protective_Marking(Test_Authentication_Base):
    """ Make sure the max protective marking get pulled through"""
    
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

        user, api_key = self.add_user()
        self.headers = self.build_headers(user, api_key)
        
        doc = {"status"             : "draft",
               "title"              : "Heres some feedback.",
               "summary"            : "Here is how I would do this.",
               "body"               : "Here's the content of the <b> site content </b> that includes html",
               "type"               : "feedback",
               "public"             : True,
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('feedback'), json.dumps(doc), content_type='application/json', **self.headers)
        
        self.resource_uri = response['location']
        self.assertEqual(response.status_code, 201)

        # Apply some comments
        # Get a new user, and upgrade them.
        user, api_key = self.add_user('ok_to_comment@ideaworks.com')
        #user = self.give_privileges(user, priv='staff')
        staff_headers = self.build_headers(user, api_key)

        comment_pm = copy.copy(self.pm)
        comment_pm['classification'] = 'GROUP'

        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "Thanks for your feedback...",
                       "protective_marking" : comment_pm}
        
        response = self.c.post(self.resource_uri + 'comments/', json.dumps(new_comment), content_type='application/json', **staff_headers)
        self.assertEquals(response.status_code, 201)
    
    def test_meta_level_max_pm_list(self):
        """ Check that we get a max_pm"""

        response = self.c.get(self.resourceListURI('feedback'))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)
        self.assertTrue(meta.has_key('max_pm'))
        self.assertEquals(meta['max_pm']['classification'], 'GROUP')
    
    def test_meta_level_max_pm_detail(self):
        """ Check that we get a max_pm when accessing the detail view"""

        response = self.c.get(self.resource_uri)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)
        self.assertTrue(meta.has_key('max_pm'))
        self.assertEquals(meta['max_pm']['classification'], 'GROUP')


if __name__ == "__main__":
    #import sys;sys.argv = ['', 'Test.testName']

    unittest.main()