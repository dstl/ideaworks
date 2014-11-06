
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import copy
import time
import json
import urlparse
import datetime
from xml.dom.minidom import parseString
from xml.parsers.expat import ExpatError

from django.test import TestCase
from django.core import urlresolvers
from django.test import client
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from registration.models import RegistrationProfile
from tastypie_mongoengine import test_runner

import ideasapp.documents as documents
from ideasapp import api
from ideasapp import api_functions

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
        
        # Get the profile of our new user to access the ACTIVATION key
        profile = RegistrationProfile.objects.get(user__email=email)
        
        # And now activate the profile using the activation key
        resp = self.client.get(reverse('registration_activate',
                                       args=(),
                                       kwargs={'activation_key': profile.activation_key}))

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
class Test_Basic_Authentication_Functions(Test_Authentication_Base):
    """
    Tests that clients can authenticate properly.
    """

    def setUp(self):
        
        # Add a user and build API key header
        self.user_id, self.api_key = self.add_user()
        self.headers = self.build_headers(self.user_id, self.api_key)
        
        
    def test_no_auth_required_on_GET(self):
        """ Authentication block on a post request """
        
        # Don't actually use the headers in the call
        response = self.c.get(self.resourceListURI('idea'))
        if settings.ANONYMOUS_VIEWING == True:
            self.assertEquals(response.status_code, 200)
        else:
            self.assertEquals(response.status_code, 401)
    
    def test_auth_block_a_POST(self):
        """ Authentication block on a post request """
    
        # Don't actually use the headers in the call
        data = {"title": "This idea will never stick...",
                 "description": "First idea description in here.",
                 "status":"published",
                 "protective_marking" : {"classification"   : "public",
                                         "descriptor"      : "private"
                                         }}
        
        response = self.c.post(self.resourceListURI('idea'), data=json.dumps(data), content_type='application/json')
        self.assertEquals(response.status_code, 401)
            

#------------------------------------------------------------------------------------------------------------

#@utils.override_settings(DEBUG=True)
class Test_Simple_GET_Idea_API(Test_Authentication_Base):

    def setUp(self):
        """ Insert documents to start with"""
        
        # Add a user and gain access to the API key and user
        user_id, api_key = self.add_user()
        self.headers = self.build_headers(user_id, api_key)
        response = self.c.get(self.resourceListURI('idea'), **self.headers)
        self.assertEquals(response.status_code, 200)
        
        self.pm =   {"classification"                : "PUBLIC",
                     "classification_short"          : "PU",
                     "classification_rank"           : 0,
                     "national_caveats_primary_name" : "MY EYES ONLY",
                     "descriptor"                    : "private",
                     "codewords"                     : ["banana1","banana2"],
                     "codewords_short"               : ["b1","b2"],
                     "national_caveats_members"      : ["ME"],
                     "national_caveats_rank"         : 3}
            
        docs = [{"title": "The first idea.",
                 "description": "First idea description in here.",
                 "status":"published",
                 "protective_marking" : self.pm },
                {"title": "The second idea.",
                 "description": "Second idea description in here.",
                 "status":"published",
                 "protective_marking" : self.pm }
                ]
        
        # Store the responses
        self.doc_locations = []
        for doc in docs:
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)

    def test_get_to_check_failure_anon(self):
        """ Test to check that new status code isn't backwards breaking"""
        
        url = '/api/v1/idea/?data_level=more&limit=3&offset=0&order_by=-created&status=published'
        response = self.c.get(url)
        self.assertEquals(response.status_code, 200)

    def test_get_to_check_failure_authenticated(self):
        """ Test to check that new status code isn't backwards breaking for authenticated user"""
        
        url = '/api/v1/idea/?data_level=more&limit=3&offset=0&order_by=-created&status=published'
        response = self.c.get(url, **self.headers)
        self.assertEquals(response.status_code, 200)
        
    def test_get_to_check_failure_authenticated_admin(self):
        """ Test to check that new status code isn't backwards breaking for authenticated ADMIN user"""
        
        user_id, api_key = self.add_user()
        user = self.give_privileges(user_id, priv='staff')
        headers = self.build_headers(user_id, api_key)
        
        url = '/api/v1/idea/?data_level=more&limit=3&offset=0&order_by=-created&status=published'
        response = self.c.get(url, **headers)
        self.assertEquals(response.status_code, 200)
        
    def test_get_all_ideas(self):
        """ Retrieve all ideas """
        
        response = self.c.get(self.resourceListURI('idea'), **self.headers)
        self.assertEquals(response.status_code, 200)
        meta, content = self.get_meta_and_objects(response)
        self.assertEquals(meta['total_count'], 2)
        self.assertEquals(len(content), 2)
        
    #TODO: Sort out xml tests
    
    def test_get_xml_list(self):
        """ Get an xml representation
            This will ERROR rather than FAIL if it doesn't succeed."""
        
        response = self.c.get('/api/%s/idea/?format=xml'%(self.api_name), **self.headers)
        self.assertEquals(response.status_code, 200)
        xml = parseString(response.content)
        
    def test_get_xml_list_fail(self):
        """ Get an xml representation - fails on content """
        
        response = self.c.get('/api/%s/idea/?format=xml'%(self.api_name), **self.headers)
        self.assertEquals(response.status_code, 200)
        self.assertRaises(ExpatError, parseString, response.content+'<hello world')

    def test_get_csv_list(self):
        """ Get an xml representation - fails on content """
        
        response = self.c.get('/api/%s/idea/?format=csv'%(self.api_name), **self.headers)
        self.assertEquals(response.status_code, 200)
        lines = response.content.split('\n')
        self.assertEquals(len(lines), 4)
        
        # Split up each line
        line_items = []
        for line in lines:
            line = line.split(',')
            line_items.append(line)
        
        # Check that each of the lines is the same length
        for i in range(len(line_items)-2):
            self.assertEquals(len(line_items[i]), len(line_items[i+1]))   

    def test_get_wrong_resource(self):
        """ Fail to retrieve resource because of incorrect name """
        
        response = self.c.get('/api/%s/ideax'%(self.api_name), **self.headers)
        self.assertEquals(response.status_code, 404)
        
    def test_get_1_idea(self):
        """ Retrieve 1 idea """
        
        pk = self.doc_locations[1].rstrip('/').split('/')[-1]
        response = self.c.get(self.resourceDetailURI('idea', pk), **self.headers)
        self.assertEquals(response.status_code, 200)
        
    def test_get_no_idea(self):
        """ Fail to retrieve an idea """
        
        pk = self.doc_locations[1].rstrip('/').split('/')[-1] + '_fake'
        response = self.c.get(self.resourceDetailURI('idea', pk), **self.headers)
        self.assertEquals(response.status_code, 404)

#------------------------------------------------------------------------------------------------------------

#@utils.override_settings(DEBUG=True)
class Test_Simple_GET_Idea_specifics(Test_Authentication_Base):

    def setUp(self):
        """ Insert documents to start with"""
        
        # Add a user and gain access to the API key and user
        user_id, api_key = self.add_user()
        self.headers = self.build_headers(user_id, api_key)
        response = self.c.get(self.resourceListURI('idea'), **self.headers)
        
        self.assertEquals(response.status_code, 200)

        self.pm =   {"classification"                : "PUBLIC",
                     "classification_short"          : "PU",
                     "classification_rank"           : 0,
                     "national_caveats_primary_name" : "MY EYES ONLY",
                     "descriptor"                    : "private",
                     "codewords"                     : ["banana1","banana2"],
                     "codewords_short"               : ["b1","b2"],
                     "national_caveats_members"      : ["ME"],
                     "national_caveats_rank"         : 3}
            
        docs = [{"title": "The first idea.",
                 "description": "First idea description in here.",
                 "protective_marking" : self.pm,
                 "status":"published",
                  "tags" : ["idea", "physics"]
                },
                {"title": "The second idea.",
                 "description": "Second idea description in here.",
                 "protective_marking" : self.pm,
                 "status":"published",
                 "tags" : ["idea", "another_tag"]
                 }
                ]
        
        # Store the responses
        self.doc_locations = []
        for doc in docs:
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)
        
    def test_get_idea_tag_list(self):
        """ Check that the tag list works OK """
        
        pk = self.doc_locations[1].rstrip('/').split('/')[-1]
        response = self.c.get(self.resourceDetailURI('idea', pk), **self.headers)
        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content)['objects'][0]
        self.assertEquals(data['tags'], ['idea','another_tag'])


    def test_get_idea_detail_check_meta_mx_pm(self):
        """ Checks that the detail levell has a meta.max_pm object """
        
        pk = self.doc_locations[1].rstrip('/').split('/')[-1]
        response = self.c.get(self.resourceDetailURI('idea', pk), **self.headers)
        self.assertEquals(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertTrue(meta.has_key('max_pm'))
        
    def test_get_idea_detail_check_meta_modified(self):
        """ Checks that the detail levell has a meta.modified object """
        
        pk = self.doc_locations[1].rstrip('/').split('/')[-1]
        response = self.c.get(self.resourceDetailURI('idea', pk), **self.headers)
        self.assertEquals(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertTrue(meta.has_key('modified'))
                

#@utils.override_settings(DEBUG=True)
class Test_Filtered_GET_Idea_API(Test_Authentication_Base):

    def setUp(self):

        # Add a user and gain access to the API key and user
        user_id, api_key = self.add_user()
        self.headers = self.build_headers(user_id, api_key)
        user_id2, api_key2 = self.add_user(email='dave@dave.com', first_name='dave', last_name='david')
        self.headers2 = self.build_headers(user_id2, api_key2)
                
        self.pm =   {"classification"                : "PUBLIC",
                     "classification_short"          : "PU",
                     "classification_rank"           : 0,
                     "national_caveats_primary_name" : "MY EYES ONLY",
                     "descriptor"                    : "private",
                     "codewords"                     : ["banana1","banana2"],
                     "codewords_short"               : ["b1","b2"],
                     "national_caveats_members"      : ["ME"],
                     "national_caveats_rank"         : 3}
        
        """ Insert documents to start with"""
        
        docs = [{"title": "The first idea.",
                 "description": "First idea description in here.",
                 "tags" : ["physics","maths","geography","sports","english"],
                 "protective_marking":self.pm, 
                 "status" : "published"},
                
                {"title": "The second idea.",
                 "description": "second idea description in here.",
                 "tags" : ["physics","maths","geography","sports"],
                 "protective_marking":self.pm,
                 "status" : "published"},
                
                {"title": "The third idea.",
                 "description": "third idea description in here.",
                 "tags" : ["physics","maths","geography"],
                 "protective_marking":self.pm,
                 "status" : "published"},
                
                {"title": "The Forth idea.",
                 "description": "forth idea description in here.",
                 "tags" : ["physics","maths"],
                 "protective_marking":self.pm,
                 "status" : "published"},

                {"title": "The Fifth idea.",
                 "description": "fifth idea description in here.",
                 "tags" : ["physics", "history"],
                 "protective_marking":self.pm,
                 "status" : "published"},
                
                {"title": "The Sixth idea.",
                 "description": "fifth idea description in here.",
                 "tags" : ["history", "design"],
                 "protective_marking":self.pm,
                 "status" : "published"},
                 ]
        
        # Store the responses
        self.doc_locations = []
        x = 0
        for doc in docs:
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)

            idea_url = response['location']

            dislike_uri = idea_url + 'dislikes/'
            new_dislikes = [{"comment" : {"title":"very good idea. I support."}},
                            {"comment" : {"title":"ditto - great idea."}}]
            for dislike in new_dislikes:
                dislike_resp = self.c.post(dislike_uri, json.dumps(dislike), content_type='application/json', **self.headers) 
                
            like_uri = idea_url + 'likes/'
            likes = [{"comment" : {"title":"very good idea. I support."}},
                            {"comment" : {"title":"ditto - great idea."}}]
            for like in likes:
                like_resp = self.c.post(like_uri, json.dumps(like), content_type='application/json', **self.headers2) 
                
            comments_uri = idea_url + 'comments/'
            new_comment = {"body"   : "perhaps we could extend that idea by...",
                            "title"  : "and what about adding to that idea with...",
                            "protective_marking" : self.pm}
            for i in range(x):
                comment_resp = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
                
            x += 1
            
            time.sleep(1)
            
        response = self.c.get(self.resourceListURI('idea')+'?data_level=less', **self.headers)

    def test_filter_by_comment_count_GTE(self):
        """ GTE filter on comment count """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('idea')+'?comment_count__gte=3', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 5)
        self.assertEqual(meta['total_count'], 5)

    def test_filter_by_comment_count_LTE(self):
        """ less than or eq filter on comment_count """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('idea')+'?comment_count__lte=2', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)
        self.assertEqual(meta['total_count'], 1)

    def test_filter_by_1tag_all_doc(self):
        """ Tag Filter - catch all documents with 1 tag """
        
        # Retrieve all results
        tags = ['physics', 'maths', 'geography', 'sports', 'english']
                
        response = self.c.get(self.resourceListURI('idea')+'?data_level=less&tags=physics', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 5)
        self.assertEqual(meta['total_count'], 5)
                
    def test_filter_by_1tag_1_doc(self):
        """ Range filter on comment count """
        
        # Retrieve all results
        tags = ['physics', 'maths', 'geography', 'sports', 'english']
        
        response = self.c.get(self.resourceListURI('idea')+'?data_level=more&tags=english', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)
        self.assertEqual(meta['total_count'], 1)

    def test_filter_by_1tag_1_doc_exact(self):
        """ Range filter on comment count """
        
        # Retrieve all results
        tags = ['physics', 'maths', 'geography', 'sports', 'english']
        
        response = self.c.get(self.resourceListURI('idea')+'?data_level=more&tags=english', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)
        self.assertEqual(meta['total_count'], 1)


    def test_filter_by_multiple_tags_OR(self):
        """ There is 1 doc with an english tag and 1 with a history tag. This should get those 2. """
        
        # Retrieve all results
        tags = ['physics', 'maths', 'geography', 'sports', 'english', 'history']
        
        response = self.c.get(self.resourceListURI('idea')+'?data_level=less&tags__in=english,history', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 3)
        self.assertEqual(meta['total_count'], 3)

    def test_filter_by_multiple_tags_check_post_sorting(self):
        """ A list of tags in the q parameter matches exactly
            the code for this is a modification that sorts the results of an __in query"""
        
        # Retrieve all results
        tags = ['physics', 'maths', 'geography', 'sports', 'english', 'history']
        
        response = self.c.get(self.resourceListURI('idea')+'?data_level=less&tags__in=physics,history,design', **self.headers)

        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 6)
        self.assertEqual(meta['total_count'], 6)
        self.assertEquals(objects[0]['tags'], ["physics","history"])
        self.assertEquals(objects[1]['tags'], ["history","design"])

#@utils.override_settings(DEBUG=True)
class Test_Filtered_GET_Idea_API_modified_status(Test_Authentication_Base):

    def setUp(self):

        # Add a user and gain access to the API key and user
        user_id, api_key = self.add_user()
        self.headers = self.build_headers(user_id, api_key)
        user_id2, api_key2 = self.add_user(email='dave@dave.com', first_name='dave', last_name='david')
        self.headers2 = self.build_headers(user_id2, api_key2)
                
        self.pm =   {"classification"                : "PUBLIC",
                     "classification_short"          : "PU",
                     "classification_rank"           : 0,
                     "national_caveats_primary_name" : "MY EYES ONLY",
                     "descriptor"                    : "private",
                     "codewords"                     : ["banana1","banana2"],
                     "codewords_short"               : ["b1","b2"],
                     "national_caveats_members"      : ["ME"],
                     "national_caveats_rank"         : 3}
        
        ''' Insert documents to start with'''
        
        docs = [{"title": "The first idea.",
                 "description": "First idea description in here.",
                 "tags" : ["physics","maths","geography","sports","english"],
                 "protective_marking":self.pm, 
                 "status" : "published"},
                
                {"title": "The second idea.",
                 "description": "second idea description in here.",
                 "tags" : ["physics","maths","geography","sports"],
                 "protective_marking":self.pm,
                 "status" : "published"},
                
                {"title": "The third idea.",
                 "description": "third idea description in here.",
                 "tags" : ["physics","maths","geography"],
                 "protective_marking":self.pm,
                 "status" : "draft"},
                
                {"title": "The Forth idea.",
                 "description": "forth idea description in here.",
                 "tags" : ["physics","maths"],
                 "protective_marking":self.pm,
                 "status" : "draft"},

                {"title": "The Fifth idea.",
                 "description": "fifth idea description in here.",
                 "tags" : ["physics", "history"],
                 "protective_marking":self.pm,
                 "status" : "hidden"},
                
                {"title": "The Sixth idea.",
                 "description": "fifth idea description in here.",
                 "tags" : ["history", "design"],
                 "protective_marking":self.pm,
                 "status" : "deleted"},
                 ]

        # Store the responses
        self.doc_locations = []
        x = 0
        for doc in docs:
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)

    def test_filter_by_status_published(self):
        """ Get ideas which have been published """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('idea')+'?status=published', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 2)
        self.assertEqual(meta['total_count'], 2)

    def test_filter_by_status_draft(self):
        """ Get ideas which have been draft """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('idea')+'?status=draft', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 2)
        self.assertEqual(meta['total_count'], 2)

    def test_filter_by_status_deleted(self):
        """ Get ideas which have been deleted """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('idea')+'?status=deleted', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)
        self.assertEqual(meta['total_count'], 1)

    def test_filter_by_status_hidden(self):
        """ Get ideas which have been hidden """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('idea')+'?status=hidden', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)
        self.assertEqual(meta['total_count'], 1)

    def test_filter_by_status_multiple(self):
        """ Get ideas by status using status__in syntax """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('idea')+'?status__in=published,draft', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 4)
        self.assertEqual(meta['total_count'], 4)

    def test_filter_by_status_multiple_2(self):
        """ Get ideas by status using status__in syntax """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('idea')+'?status__in=hidden,deleted', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 2)
        self.assertEqual(meta['total_count'], 2)

    def test_filter_by_status_published_not_own(self):
        """ Non-authoring user can only see objects with a published status """
        
        diff_user, diff_user_api_key = self.add_user(email='dave@dave.com', first_name='dave', last_name='david')
        diff_headers = self.build_headers(diff_user, diff_user_api_key)
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('idea')+'?status=draft', **diff_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 0)
        self.assertEqual(meta['total_count'], 0)
        
    def test_filter_by_status__in_published_not_own(self):
        """ Non-authoring user can only see objects with a published status """
        
        diff_user, diff_user_api_key = self.add_user(email='dave@dave.com', first_name='dave', last_name='david')
        diff_headers = self.build_headers(diff_user, diff_user_api_key)
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('idea')+'?status__in=draft,hidden', **diff_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 0)
        self.assertEqual(meta['total_count'], 0)

    def test_no_status_provided(self):
        """ Non-authoring user can only see objects with a published status """
        
        diff_user, diff_user_api_key = self.add_user(email='dave@dave.com', first_name='dave', last_name='david')
        diff_headers = self.build_headers(diff_user, diff_user_api_key)
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('idea'), **diff_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 2)
        self.assertEqual(meta['total_count'], 2)

    def test_new_user_new_idea_no_status_provided(self):
        """ New user drafts an object, but doesn't provide a status param so only has access to published """
        
        # New user
        diff_user, diff_user_api_key = self.add_user(email='dave@dave.com', first_name='dave', last_name='david')
        diff_headers = self.build_headers(diff_user, diff_user_api_key)
        
        # New user drafts a new document
        new_doc = {"title": "The Sixth idea.", "description": "fifth idea description in here.",
                 "tags" : ["history", "design"], "protective_marking":self.pm, "status" : "draft"}
        response = self.c.post(self.resourceListURI('idea'), json.dumps(new_doc), content_type='application/json', **diff_headers)
        self.assertEquals(response.status_code, 201)
        
        response = self.c.get(self.resourceListURI('idea'), **diff_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 2)
        self.assertEqual(meta['total_count'], 2)

    def test_new_user_new_idea_status_provided(self):
        """ New user drafts an object, and provides a status param so has access to his draft + all published """
        
        # New user
        diff_user, diff_user_api_key = self.add_user(email='dave@dave.com', first_name='dave', last_name='david')
        diff_headers = self.build_headers(diff_user, diff_user_api_key)
        
        # New user drafts a new document
        new_doc = {"title": "The Sixth idea.", "description": "fifth idea description in here.",
                 "tags" : ["history", "design"], "protective_marking":self.pm, "status" : "draft"}
        response = self.c.post(self.resourceListURI('idea'), json.dumps(new_doc), content_type='application/json', **diff_headers)
        self.assertEquals(response.status_code, 201)
        
        response = self.c.get(self.resourceListURI('idea')+'?status__in=published,draft', **diff_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 3)
        self.assertEqual(meta['total_count'], 3)


#@utils.override_settings(DEBUG=True)
class Test_POST_Idea_API(Test_Authentication_Base):

    def setUp(self):
        
        # Add a user and gain access to the API key and user
        self.user, self.api_key = self.add_user()
        self.headers = self.build_headers(self.user, self.api_key)

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
                
    def test_POST_simple(self):

        doc = {"title": "The first idea.",
               "description": "First idea description in here.",
               "created" : "2013-01-01T00:00:00",
               "protective_marking" : self.pm,
               "status":"published",
               }
        
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 201)

        response = self.c.get(self.resourceListURI('idea'), **self.headers)
        meta = json.loads(response.content)['meta']
        objects = json.loads(response.content)['objects']
        
        # Top level checks
        self.assertEquals(meta['total_count'], 1)
        self.assertEquals(len(objects), 1)
        
    def test_POST_simple_usercheck(self):
        """ Test that created and user get automatically added"""
        
        doc = {"title": "The idea.",
               "description": "Idea description in here.",
               "status":"published",
               "protective_marking" : self.pm}
        
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 201)

        response = self.c.get(self.resourceListURI('idea'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        
        # Field checks
        self.assertTrue(datetime.datetime.strptime(objects[0]['created'], '%Y-%m-%dT%H:%M:%S.%f') < datetime.datetime.utcnow())
        self.assertEquals(objects[0]['user'], self.user.username)

        
    def test_PUT_simple(self):

        # POST a document
        doc = {"title": "The first idea.",
               "description": "First idea description in here.",
               "status":"published",
               "protective_marking" : self.pm
               }
        
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 201)
        idea1_url = response['location']
        
        # PUT another document using the 
        new_title = {"title":"the first idea, much improved.",
                     "status":"published",
                     "protective_marking" : self.pm
                     }
        response = self.c.put(idea1_url, json.dumps(new_title), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 204)

    def test_POST_add_comments(self):

        # POST a document
        doc = {"title": "The first idea.",
               "description": "First idea description in here.",
               "created" : "2013-01-01T00:00:00",
               "protective_marking" : self.pm,
               "status" : "published"}
        
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 201)
        
        # Check it's there and there is 1 comment 
        main_idea = response['location']
        
        # Now check its there via URL
        # Without the trailing slash results in 301 status_code
        comments_uri = self.fullURItoAbsoluteURI(main_idea) + 'comments/'
        comment_1 = comments_uri + '100/'
        response = self.c.get(comment_1, **self.headers)
        self.assertEquals(response.status_code, 404)
        
        # Try adding a new comment
        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "and what about adding to that idea with...",
                       "protective_marking" : self.pm}
        
        resp = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
        new_comment_uri = resp['location']
        
        # Now make sure there are 3 comments
        response = self.c.get(comments_uri, **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['total_count'], 1)
        self.assertEquals(objects[0]['user'], self.user.username)


    def test_POST_add_comment_to_unpublished_idea(self):
        """ Comments are only permitted against ideas with status=published
            This checks that a comment will fail where status=draft"""

        # POST a document
        doc = {"title": "The first idea.",
               "description": "First idea description in here.",
               "created" : "2013-01-01T00:00:00",
               "protective_marking" : self.pm,
               "status" : "draft"}
        
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 201)
        
        # Check it's there and there is 1 comment 
        main_idea = response['location']
        
        # Now check its there via URL
        # Without the trailing slash results in 301 status_code
        comments_uri = self.fullURItoAbsoluteURI(main_idea) + 'comments/'
        comment_1 = comments_uri + '100/'
        response = self.c.get(comment_1, **self.headers)
        self.assertEquals(response.status_code, 404)
        
        # Try adding a new comment
        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "and what about adding to that idea with...",
                       "protective_marking" : self.pm}
        
        resp = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(json.loads(resp.content)['error'], 'User can only comment on ideas with status=published.')
        
        
    ## Add some more tags
    """
    In shifting from an embeddedfieldlist to a simple list(string()) field
    for tags, I've dropped the ability to POST/PUT/PATCH the tags array.
    To edit the tags, the client has to extract the entire document (or the editable parts)
    and then PUT the new document back (which includes the tags). 
    """

#@utils.override_settings(DEBUG=True)
class Test_GET_tags(Test_Authentication_Base):

    def setUp(self):
        
        # Add a user and gain access to the API key and user
        user_id, api_key = self.add_user()
        self.headers = self.build_headers(user_id, api_key)
    
    def test_get_tag_list(self):
        """ Tests retrieval of tags"""
        
        # Insert a bunch of docs with different tag combinations
        docs = [{"title": "First idea.", "status":"published", "tags" : ["idea", "ideaworks", "physics", "rugby"]},
               {"title": "Second idea.", "status":"published", "tags" : ["idea", "ideaworks", "physics"]},
               {"title": "Second idea.", "status":"published", "tags" : ["idea", "ideaworks"]},
               {"title": "Third idea.", "status":"published", "tags" :  ["idea"]}]

        for doc in docs:
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            self.assertEqual(response.status_code, 201)
        
        # Check there are 4 tags total
        response = self.c.get(self.resourceListURI('tag'), **self.headers)
        tags = json.loads(response.content)['objects']
        self.assertEquals(len(tags), 4)
        
    def test_get_tag_list_order_by_default(self):
        """ Tests retrieval of tags with an extra aggregate term for sorting."""
        
        # Insert a bunch of docs with different tag combinations
        docs = [{"title": "First idea.","status":"published", "tags" : ["idea", "ideaworks", "physics", "rugby"]},
               {"title": "Second idea.","status":"published", "tags" : ["idea", "ideaworks", "physics"]},
               {"title": "Second idea.","status":"published", "tags" : ["idea", "ideaworks"]},
               {"title": "Third idea.","status":"published", "tags" :  ["idea"]}]

               
        for doc in docs:
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            self.assertEqual(response.status_code, 201)
        
        # Check the specific ordering of the tags
        response = self.c.get(self.resourceListURI('tag'), **self.headers)
        tags = json.loads(response.content)['objects']
        self.assertEquals(tags[0]['text'], 'idea')
        self.assertEquals(tags[1]['text'], 'ideaworks')
        self.assertEquals(tags[2]['text'], 'physics')
        self.assertEquals(tags[3]['text'], 'rugby')

    def test_get_tag_list_status_single_filter(self):
        """ Filter which documents get read for tags based on status."""
        
        # Insert a bunch of docs with different tag combinations
        docs = [{"title": "First idea.",  "status" : "draft",     "tags" : ["idea", "ideaworks", "physics", "rugby"]},
                {"title": "Second idea.", "status" : "published", "tags" : ["idea", "ideaworks", "physics"]},
                {"title": "Second idea.", "status" : "hidden",    "tags" : ["idea", "ideaworks"]},
                {"title": "Third idea.",  "status" : "deleted",    "tags" :  ["idea"]}]

               
        for doc in docs:
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            self.assertEqual(response.status_code, 201)
        
        # Check the specific ordering of the tags
        params = '?status=hidden'
        response = self.c.get(self.resourceListURI('tag')+params, **self.headers)
        tags = json.loads(response.content)['objects']
        self.assertEquals(len(tags), 2)
        
        
    def test_get_tag_list_status_multiple_statuses(self):
        """ Filter which documents get read for tags based on status."""
        
        # Insert a bunch of docs with different tag combinations
        docs = [{"title": "First idea.",  "status" : "draft",     "tags" : ["idea", "ideaworks", "physics", "rugby"]},
                {"title": "Second idea.", "status" : "published", "tags" : ["idea", "ideaworks", "physics"]},
                {"title": "Second idea.", "status" : "hidden",    "tags" : ["idea", "ideaworks"]},
                {"title": "Third idea.",  "status" : "deleted",    "tags" :  ["new_idea_tag"]}]
                
               
        for doc in docs:
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            self.assertEqual(response.status_code, 201)
        
        resp = self.c.get(self.resourceListURI('idea'))

        # Check the specific ordering of the tags
        params = '?status=hidden,deleted'
        response = self.c.get(self.resourceListURI('tag')+params, **self.headers)
        tags = json.loads(response.content)['objects']
        self.assertEquals(len(tags), 3)
        
#@utils.override_settings(DEBUG=True)
class Test_Like_and_Dislike_actions(Test_Authentication_Base):
    
    def setUp(self):

        # Add a user and gain access to the API key and user
        self.user, self.api_key = self.add_user()
        self.headers = self.build_headers(self.user, self.api_key)
        
        # Add a doc
        doc = {"title": "First idea.",
               "description" : "This is the first idea in a series of good ideas.",
               "status" : "published"}
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.resource_uri = response['location']
        self.assertEqual(response.status_code, 201)

    def test_attempt_to_dislike_a_draft_idea(self):
        """ Code should stop the user attempting to dislike a draft idea - only allowed on published."""
        
        # Change that idea status to be draft via the db directly
        id = self.resource_uri.strip('/').split('/')[-1]
        doc = documents.Idea.objects.get(id=id).update(**{'set__status':'draft'})
        
        # Without the trailing slash results in 301 status_code
        dislikes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'dislikes/'
        
        # Try adding a new comment
        response = self.c.post(dislikes_uri, json.dumps({"comment" : {"title":"very good idea. I support."}}), content_type='application/json', **self.headers) 
        
        # Now make sure there are 3 comments
        self.assertEquals(response.status_code, 400)
    
    def test_dislike_an_idea_catch_single_user(self):
        """ As the same user, attempt to dislike an idea twice
            and fail to do so. Resultant dislike array remains 1 long."""
        
        # Without the trailing slash results in 301 status_code
        dislikes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'dislikes/'
        
        # Try adding a new comment
        # No user provided - picked up automatically
        new_dislikes = [{"comment" : {"title":"very good idea. I support."}},
                        {"comment" : {"title": "ditto - great idea."}}]
        for dislike in new_dislikes:
            self.c.post(dislikes_uri, json.dumps(dislike), content_type='application/json', **self.headers) 
        
        # Now make sure there are 3 comments
        response = self.c.get(dislikes_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(len(content), 1)
        self.assertEquals(content[0]['user'], self.user.username)
        
        # Make sure the like count is correct
        response = self.c.get(self.resource_uri, **self.headers)
        self.assertEquals(json.loads(response.content)['objects'][0]['dislike_count'], 1)

    def test_dislike_an_idea_2_users(self):
        """ userA likes an idea. UserA tries to like it again - it should fail.
            userB likes an idea and it registers. """
        
        user_2, api_key_2 = self.add_user('dude@ideaworks.com')
        self.headers_2 = self.build_headers(user_2, api_key_2)
        
        # Without the trailing slash results in 301 status_code
        dislikes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'dislikes/'
        
        # Try adding a new comment
        # No user provided - picked up automatically
        # Only 2 of these should go in because user 1 can't like something twice
        self.c.post(dislikes_uri, json.dumps({"comment":{"title":"cool"}}), content_type='application/json', **self.headers) 
        self.c.post(dislikes_uri, json.dumps({"comment":{"title":"fun"}}), content_type='application/json', **self.headers) 
        self.c.post(dislikes_uri, json.dumps({"comment":{"title":"nice"}}), content_type='application/json', **self.headers_2) 
        
        # Now make sure there are 2 likes with different users
        response = self.c.get(dislikes_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(len(content), 2)
        
        self.assertEquals(content[0]['user'], self.user.username)
        self.assertEquals(content[1]['user'], user_2.username)
        
        # Make sure the like count is correct
        response = self.c.get(self.resource_uri, **self.headers)
        self.assertEquals(json.loads(response.content)['objects'][0]['dislike_count'], 2)

    def test_attempt_to_like_a_draft_idea(self):
        """ Code should stop the user attempting to like a draft idea - only allowed on published."""
        
        # Change that idea status to be draft via the db directly
        id = self.resource_uri.strip('/').split('/')[-1]
        doc = documents.Idea.objects.get(id=id).update(**{'set__status':'draft'})
        
        # Without the trailing slash results in 301 status_code
        dislikes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'likes/'
        
        # Try adding a new comment
        response = self.c.post(dislikes_uri, json.dumps({"comment" : {"title":"very good idea. I support."}}), content_type='application/json', **self.headers) 
        
        # Now make sure there are 3 comments
        self.assertEquals(response.status_code, 400)

    def test_like_an_idea_catch_single_user(self):
        """ A user attempts to like something twice and fails. Like array still only 1 long."""
        
        # Without the trailing slash results in 301 status_code
        likes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'likes/'
        
        # Try adding a new comment
        # No user provided - picked up automatically
        new_likes = [{"comment" : {"title":"very good idea. I support."}},
                     {"comment" : {"title": "ditto - great idea."}}]
        for like in new_likes:
            self.c.post(likes_uri, json.dumps(like), content_type='application/json', **self.headers) 
        
        # Now make sure there are 3 comments
        response = self.c.get(likes_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(len(content), 1)
        self.assertEquals(content[0]['user'], self.user.username)
        
    def test_like_an_idea_check_like_count(self):
        """ Like an idea - check the count keeps track"""
        
        # Without the trailing slash results in 301 status_code
        likes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'likes/'
        
        # Try adding a new comment
        # No user provided - picked up automatically
        new_likes = [{"comment" : {"title":"very good idea. I support."}},
                     {"comment" : {"title": "ditto - great idea."}}]
        for like in new_likes:
            self.c.post(likes_uri, json.dumps(like), content_type='application/json', **self.headers) 

        # Make sure the like count is correct
        response = self.c.get(self.resource_uri, **self.headers)
        self.assertEquals(json.loads(response.content)['objects'][0]['like_count'], 1)
        

    def test_like_an_idea_2_users(self):
        """ userA likes an idea. UserA tries to like it again - it should fail.
            userB likes an idea and it registers. """
        
        user_2, api_key_2 = self.add_user('dude@ideaworks.com')
        self.headers_2 = self.build_headers(user_2, api_key_2)
        
        # Without the trailing slash results in 301 status_code
        likes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'likes/'
        
        # Try adding a new comment
        # No user provided - picked up automatically
        # Only 2 of these should go in because user 1 can't like something twice
        self.c.post(likes_uri, json.dumps({"comment":{"title":"cool"}}), content_type='application/json', **self.headers) 
        self.c.post(likes_uri, json.dumps({"comment":{"title":"fun"}}), content_type='application/json', **self.headers) 
        self.c.post(likes_uri, json.dumps({"comment":{"title":"nice"}}), content_type='application/json', **self.headers_2) 
        
        # Now make sure there are 2 likes with different users
        response = self.c.get(likes_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(len(content), 2)
        
        self.assertEquals(content[0]['user'], self.user.username)
        self.assertEquals(content[1]['user'], user_2.username)


    def test_like_an_idea_2_users_check_count2(self):
        """ userA likes an idea. UserA tries to like it again - it should fail.
            userB likes an idea and it registers. """
        
        user_2, api_key_2 = self.add_user('dude@ideaworks.com')
        self.headers_2 = self.build_headers(user_2, api_key_2)
        
        # Without the trailing slash results in 301 status_code
        likes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'likes/'
        
        # Try adding a new comment
        # No user provided - picked up automatically
        # Only 2 of these should go in because user 1 can't like something twice
        self.c.post(likes_uri, json.dumps({"comment":{"title":"cool"}}), content_type='application/json', **self.headers) 
        self.c.post(likes_uri, json.dumps({"comment":{"title":"fun"}}), content_type='application/json', **self.headers) 
        self.c.post(likes_uri, json.dumps({"comment":{"title":"nice"}}), content_type='application/json', **self.headers_2) 
                
        # Make sure the like count is correct
        response = self.c.get(self.resource_uri, **self.headers)
        self.assertEquals(json.loads(response.content)['objects'][0]['like_count'], 2)
    
    def test_user_likes_idea_and_changes_to_dislike(self):
        """ userA LIKES an idea. UserA tries to DISLIKE it instead - it should SUCCEED. """
        
        # Like, then dislike
        likes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'likes/'
        self.c.post(likes_uri, json.dumps({"comment":{"title":"cool"}}), content_type='application/json', **self.headers) 
        
        # Check it registered
        response = self.c.get(likes_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(len(content), 1)
        
        dislikes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'dislikes/'
        self.c.post(dislikes_uri, json.dumps({"comment":{"title":"fun"}}), content_type='application/json', **self.headers) 
        
        # Check that the change to dislike registered
        response = self.c.get(dislikes_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(len(content), 1)
        
        # Make sure the original one got dropped
        response = self.c.get(likes_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(len(content), 0)
        

    def test_user_dislikes_idea_and_changes_to_like(self):
        """ userA dislikes an idea. UserA tries to like it instead - it should SUCCEED. """
        
        # Dislike, then like
        dislikes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'dislikes/'
        self.c.post(dislikes_uri, json.dumps({"comment":{"title":"fun"}}), content_type='application/json', **self.headers) 
        
        # Make sure the vote has transferred
        response = self.c.get(dislikes_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(len(content), 1)
        
        likes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'likes/'
        self.c.post(likes_uri, json.dumps({"comment":{"title":"cool"}}), content_type='application/json', **self.headers) 
        
        # Make sure the vote has transferred
        response = self.c.get(likes_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(len(content), 1)
        
        # Double check that its gone from the original
        response = self.c.get(dislikes_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(len(content), 0)

    def test_like_an_idea_check_count_2(self):
        """ userA likes an idea. UserA tries to like it again - it should fail.
            userB likes an idea and it registers. """
        
        user_2, api_key_2 = self.add_user('dude@ideaworks.com')
        self.headers_2 = self.build_headers(user_2, api_key_2)
        
        # Without the trailing slash results in 301 status_code
        likes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'likes/'
        
        # Try adding a new comment
        # No user provided - picked up automatically
        # Only 2 of these should go in because user 1 can't like something twice
        self.c.post(likes_uri, json.dumps({"comment":{"title":"cool"}}), content_type='application/json', **self.headers) 
        self.c.post(likes_uri, json.dumps({"comment":{"title":"fun"}}), content_type='application/json', **self.headers) 
        self.c.post(likes_uri, json.dumps({"comment":{"title":"nice"}}), content_type='application/json', **self.headers_2) 
        
        # Now make sure there are 2 likes with different users
        response = self.c.get(likes_uri, **self.headers)
        content = json.loads(response.content)['objects']
        
        self.assertEquals(content[0]['user'], self.user.username)
        self.assertEquals(content[1]['user'], user_2.username)

    def test_like_comment_stored_in_comments_model(self):
        """ Check that a Like comment gets stored in the comments model, not as a vote subdoc """
                
        # Without the trailing slash results in 301 status_code
        likes_uri    = self.fullURItoAbsoluteURI(self.resource_uri) + 'likes/'
        comments_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'comments/'
        
        new_comment = {"comment" : {"title"              : "heres a new comment",
                                    "body"               : "heres the body of a new comment",
                                    "protective_marking" : {"classification" : "PUBLIC",
                                                            "classification_short" : "PU",
                                                            "classification_rank" : 0,
                                                            "national_caveats_primary_name" : '',
                                                            "national_caveats_members" : [],
                                                            "codewords" : ['BANANA 1', 'BANANA 2'],
                                                            "codewords_short" : ['B1', 'B2'],
                                                            "descriptor" : 'PRIVATE'}
                                    }
                       }
        
        # Try adding a new like with comment
        self.c.post(likes_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
        
        # Now make sure there are 2 likes with different users
        response = self.c.get(comments_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(content[0]['user'], self.user.username)
        
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **self.headers)

        # ['objects'][0] - because detail level has a meta object
        doc = json.loads(response.content)['objects'][0]
        self.assertEquals(len(doc['comments']), 1)
        self.assertEquals(doc['comment_count'], 1)
        self.assertEquals(doc['comments'][0]['type'], 'like')
        
        self.assertEquals(len(doc['likes']), 1)
        self.assertEquals(doc['like_count'], 1)

    def test_dislike_comment_stored_in_comments_model(self):
        """ Check that a dislike comment gets stored in the comments model, not as a vote subdoc """
                
        # Without the trailing slash results in 301 status_code
        dislikes_uri    = self.fullURItoAbsoluteURI(self.resource_uri) + 'dislikes/'
        comments_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'comments/'
        
        new_comment = {"comment" : {"title"              : "heres a new comment",
                                    "body"               : "heres the body of a new comment",
                                    "protective_marking" : {"classification" : "PUBLIC",
                                                            "classification_short" : "PU",
                                                            "classification_rank" : 0,
                                                            "national_caveats_primary_name" : '',
                                                            "national_caveats_members" : [],
                                                            "codewords" : ['BANANA 1', 'BANANA 2'],
                                                            "codewords_short" : ['B1', 'B2'],
                                                            "descriptor" : 'PRIVATE'}
                                    }
                       }
        
        # Try adding a new like with comment
        self.c.post(dislikes_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
        
        # Now make sure there are 2 likes with different users
        response = self.c.get(comments_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(content[0]['user'], self.user.username)
        
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **self.headers)
        doc = json.loads(response.content)['objects'][0]
        self.assertEquals(len(doc['comments']), 1)
        self.assertEquals(doc['comment_count'], 1)
        
        self.assertEquals(len(doc['dislikes']), 1)
        self.assertEquals(doc['dislike_count'], 1)
        
        self.assertEquals(doc['comments'][0]['type'], 'dislike')

    def test_attempted_like_spoof_fake_user(self):
        """ Mimics someone attemtpting to increment like by submitting a fake user """
        
        # The user that is recorded in the db isn't fake_like@xyz.com
        
        likes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'likes/'
        fake_data = {'user':'fake_like@xyz.com'}
        self.c.post(likes_uri, json.dumps(fake_data), content_type='application/json', **self.headers) 
        
        # Now make sure there are 2 likes with different users
        response = self.c.get(likes_uri, **self.headers)
        self.assertEquals(json.loads(response.content)['objects'][0]['user'], self.user.username)

    def test_get_user_vote_status_like(self):
        """ Check that the API returns the user_vote field """
        
        uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'likes/'
        self.c.post(uri, json.dumps({}), content_type='application/json', **self.headers) 
        
        # Check the user vote is the correct value
        response = self.c.get(self.resource_uri, **self.headers)
        self.assertEquals(json.loads(response.content)['objects'][0]['user_voted'], 1)

    def test_get_user_vote_status_dislike(self):
        """ Check that the API returns the user_vote field """
        
        uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'dislikes/'
        self.c.post(uri, json.dumps({}), content_type='application/json', **self.headers) 
        
        # Check the user vote is the correct value
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **self.headers)
        self.assertEquals(json.loads(response.content)['objects'][0]['user_voted'], -1)
        
    def test_get_user_vote_status_neither(self):
        """ Check that the API returns the user_vote field """
        
        # Check the user vote is the correct value
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **self.headers)
        self.assertEquals(json.loads(response.content)['objects'][0]['user_voted'], 0)
    
    def test_user_vote_issue45_case1(self):
        """ 
            Re-creating this action on the front-end
            -----------------------------------------
            UserA logs in - not actually required in the tests (API auth)
            UserA votes on (likes) idea_001
            Check user_voted for idea_001 - should be +1
            UserA logs out
            
            UserB logs in - not actually required in the tests (API auth)
            UserB opens idea_001
            Check user_voted for idea_001 - should be 0
            UserB votes on (dislikes) idea_001
            Check user_voted for idea_001 - should be -1
        """
        
        # Create UserA
        userA, userA_api_key = self.add_user(email="a@a.com", first_name="a", last_name="user_a")
        userA_headers = self.build_headers(userA, userA_api_key)
        
        # UserA like an idea
        uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'likes/'
        x = self.c.post(uri, json.dumps({}), content_type='application/json', **userA_headers) 
        
        # Check the user vote is correct
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **userA_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['user_voted'], 1)
        
        # Create UserB
        userB, userB_api_key = self.add_user(email="b@b.com", first_name="b", last_name="user_b")
        userB_headers = self.build_headers(userB, userB_api_key)

        # UserB shouldn't have a user_vote yet
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **userB_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['user_voted'], 0)
        
        # UserB dislikes something
        uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'dislikes/'
        x = self.c.post(uri, json.dumps({}), content_type='application/json', **userB_headers) 

        # UserB now has a user_vote of -1
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **userB_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['user_voted'], -1)
        
        
        
    def test_user_vote_issue45_case2(self):
        """ UserA logs in
            UserA votes on (likes) idea_001
            Check user_voted for idea_001 - should be +1
            UserA logs out
            
            Anonymous opens idea_001
            Check user_voted for idea_001 - should be 0
            
            UserB logs in - not actually required in the tests (API auth)
            UserB opens idea_001
            Check user_voted for idea_001 - should be 0
            UserB votes on (dislikes) idea_001
            Check user_voted for idea_001 - should be -1

        """
        
        # Create UserA
        userA, userA_api_key = self.add_user(email="a@a.com", first_name="a", last_name="user_a")
        userA_headers = self.build_headers(userA, userA_api_key)
        
        # UserA like an idea
        uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'likes/'
        x = self.c.post(uri, json.dumps({}), content_type='application/json', **userA_headers) 
        
        # Check the user vote is correct
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **userA_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['user_voted'], 1)
        
        # AnonymousUser shouldn't have a user_vote yet
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['user_voted'], 0)
        
        # And now UserB just to be sure...
        userB, userB_api_key = self.add_user(email="b@b.com", first_name="b", last_name="user_b")
        userB_headers = self.build_headers(userB, userB_api_key)

        # UserB shouldn't have a user_vote yet
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **userB_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['user_voted'], 0)
        
        # UserB dislikes something
        uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'dislikes/'
        x = self.c.post(uri, json.dumps({}), content_type='application/json', **userB_headers) 

        # UserB now has a user_vote of -1
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **userB_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['user_voted'], -1)
        
    #===============================================================================
    # DIFFERENT WAYS OF QUERYING THE COMMENTS API - by user? by title?
    #===============================================================================

    #===============================================================================
    #TODO: Check that a null classification can be posted- for when we drop that.
    #===============================================================================

#@utils.override_settings(DEBUG=True)
class Test_Scoring(Test_Authentication_Base):
    
    def setUp(self):

        # Add a user and gain access to the API key and user
        self.user, self.api_key = self.add_user()
        self.headers = self.build_headers(self.user, self.api_key)
        
        # Add a doc
        doc = {"title": "First idea.", "status":"published", "description" : "This is the first idea in a series of good ideas."}
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.resource_uri = response['location']
        self.assertEqual(response.status_code, 201)

    def test_get_score_single_dislike(self):
        """ Check that the API returns the vote_score field """
        
        dislikes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'dislikes/'
        resp = self.c.post(dislikes_uri, json.dumps({}), content_type='application/json', **self.headers) 
        
        # Check the user vote is the correct value
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        score = objects[0]['vote_score']
        self.assertLess(score, 0.1)

    def test_get_score_multiple_likes(self):
        """ Check that the API returns the vote_score field
            and that it updates after a load of likes are added """
        
        # Do 1 via the Rest interface
        likes_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'likes/'
        resp = self.c.post(likes_uri, json.dumps({}), content_type='application/json', **self.headers) 

        # Here - check that the score is initially low
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        score = objects[0]['vote_score']
        self.assertLess(score, 0.3)

        # Build a load more users and get them all to like it
        for i in range(100):
            user_id, api_key = self.add_user(email="user_%s@ideaworks.com"%(i), first_name="user_%s"%(i), last_name="last_name_user_%s"%(i))
            user_specific_headers = self.build_headers(user_id, api_key)
            resp = self.c.post(likes_uri, json.dumps({}), content_type='application/json', **user_specific_headers) 
        
        # Check the user vote is the correct value
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        score = objects[0]['vote_score']
        self.assertGreater(score, 0.9)

#@utils.override_settings(DEBUG=True)
class Test_Idea_Sorting(Test_Authentication_Base):

    def setUp(self):
        """ Add in some documents"""

        # Add a user and gain access to the API key and user
        user_id, api_key = self.add_user()
        self.headers = self.build_headers(user_id, api_key)

        self.doc_ids = []

        # Insert 10 docs 
        for i in range(10):
            doc = {"title": "Idea #%s"%(i), "status":"published", "description": "First idea description in here."}
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            if response.status_code == 201:
                self.doc_ids.append(response['location'])
            time.sleep(0.5)
            
        # Check they went in OK
        content = json.loads(self.c.get(self.resourceListURI('idea'), **self.headers).content)
        self.assertEquals(len(content['objects']), 10)
    
    
    def test_doc_asc_created_sort(self):
        """Sort results by date in asc order """
        
        response = self.c.get('/api/v1/idea/?order_by=created', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        for i in range(1, len(objects)):
            this = datetime.datetime.strptime(objects[i]['created'], '%Y-%m-%dT%H:%M:%S.%f')
            prev = datetime.datetime.strptime(objects[i-1]['created'], '%Y-%m-%dT%H:%M:%S.%f')
            self.assertTrue(prev < this)

    def test_doc_desc_created_sort(self):
        """ Sort results by date in descending order. """

        response = self.c.get('/api/v1/idea/?order_by=-created', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        for i in range(1, len(objects)):
            this = datetime.datetime.strptime(objects[i]['created'], '%Y-%m-%dT%H:%M:%S.%f')
            prev = datetime.datetime.strptime(objects[i-1]['created'], '%Y-%m-%dT%H:%M:%S.%f')
            self.assertTrue(prev > this)
    
    def test_doc_like_count_sort_desc(self):
        """ Sort results by like count in descending order. """

        # Add some likes
        for i in range(len(self.doc_ids)-1):
            likes_uri = self.fullURItoAbsoluteURI(self.doc_ids[i]) + 'likes/'
            
            # Add a different number of likes for each idea
            x = i + 1
            
            for j in range(1, x+2):
                # Add a different user each time
                user_id, api_key = self.add_user(email='%s@blah.com'%(j))
                headers = self.build_headers(user_id, api_key)
                
                try:
                    resp = self.c.get(likes_uri, **headers)
                    resp = self.c.post(likes_uri, json.dumps({'comment':{"title":'cool %s'%(j)}}), content_type='application/json', **headers) 
                except Exception, e:
                    print e
                                
        response = self.c.get('/api/v1/idea/?order_by=like_count', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        
        for x in range(len(objects)-1):
            this_like_count = objects[x]['like_count']
            next_like_count = objects[x+1]['like_count']
            if this_like_count and next_like_count:
                self.assertGreater(next_like_count, this_like_count)
                
    ## MORE TESTS FOR DIFFERENT SORT FIELDS ##    

#@utils.override_settings(DEBUG=True)
class Test_Check_Modified(Test_Authentication_Base):

    def setUp(self):
        """ Add in some documents"""

        # Add a user and gain access to the API key and user
        user_id, api_key = self.add_user()
        self.headers = self.build_headers(user_id, api_key)
        number_ideas = 3
        
        # Insert 10 docs with different months
        for i in range(number_ideas):
            doc = {"title": "Idea #%s"%(i), "description": "First idea description in here.", "status": "published"}
            #resp = self.c.get(self.resourceListURI('idea'), **self.headers)
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            main_idea = response['location']
            self.assertEquals(response.status_code, 201)
            
            comments_uri = self.fullURItoAbsoluteURI(main_idea) + 'comments/'
            
            # Try adding new comments
            for j in range (3):
                new_comment = {"user"   : "rich@rich.com",
                               "body"   : "#%s perhaps we could extend that idea by..."%(j),
                               "title"  : "and what about adding to that idea with %s..."%(j),
                               "protective_marking" : {"classification":"unclassified","descriptor":""}}
                resp = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
                self.assertEquals(resp.status_code, 201)
                
        # Wait to ensure we have a different time
        time.sleep(0.5)

        # Check they went in OK
        content = json.loads(self.c.get(self.resourceListURI('idea'), **self.headers).content)
        self.assertEquals(len(content['objects']), number_ideas)
        
    def retrieve_most_recent_timestamp(self, objects):
        """Gets the most recent timestamp"""
        
        dates = []
        for obj in objects:
            dates += [datetime.datetime.strptime(obj['created'], '%Y-%m-%dT%H:%M:%S.%f'), datetime.datetime.strptime(obj['modified'], '%Y-%m-%dT%H:%M:%S.%f')]
        return max(dates)
    
    def test_update_idea_modified_ts_field_on_POST(self):
        """ Checks that the Idea API updates the modified timestamp field when part of the idea is changed"""
        
        # Get all data
        content = json.loads(self.c.get(self.resourceListURI('idea'), **self.headers).content)
        idea_0 = content['objects'][0]
        old_title = idea_0['title']
        old_ts = idea_0['modified']
        
        # Patch a new title - partial addition which leaves the rest in place correctly.
        new_title = {"title":"this is a major change to the title because it was offensive..."}
        response = self.c.patch(self.fullURItoAbsoluteURI(idea_0['resource_uri']), json.dumps(new_title), content_type='application/json', **self.headers)
        content = json.loads(self.c.get(self.resourceListURI('idea'), **self.headers).content)
        
        # Retrieve the last idea in the set now because it's been moved
        idea_0 = content['objects'][0]
        new_stored_title = idea_0['title']

        # Check its not the same as the previous one and is the intended new one        
        self.assertNotEqual(old_title, new_stored_title)
        self.assertEqual(new_title['title'], new_stored_title)
        
        # Check the timestamps
        new_ts = idea_0['modified']
        self.assertGreater(new_ts, old_ts)

    def test_update_idea_modified_ts_field_on_POST_to_comment(self):
        """ Checks that the Idea API updates the modified timestamp field when part of the idea is changed.
            Mods to the comments/likes/dislikes will change the overall objects modified date."""
        
        # Get all data
        content = json.loads(self.c.get(self.resourceListURI('idea'), **self.headers).content)
        idea_x = content['objects'][-1]
        idea_old_ts = idea_x['modified']
        first_comment = idea_x['comments'][0]
        
        # Patch a new title - partial addition which leaves the rest in place correctly.
        new_comment_title = {"title":"this is a major change to the title because it was offensive..."}
        response = self.c.patch(first_comment['resource_uri'], json.dumps(new_comment_title), content_type='application/json', **self.headers)
        time.sleep(1)
        
        # After a short sleep, get the ideas again
        content = json.loads(self.c.get(self.resourceListURI('idea'), **self.headers).content)
        idea_x = content['objects'][-1]
        
        # Get the modified time for the IDEA
        idea_new_ts = idea_x['modified']
        
        # Get the first comment again
        new_first_comment = idea_x['comments'][0]
        
        # Check that the new first comment title is what we tried to change it to
        self.assertEqual(new_first_comment['title'], new_comment_title['title'])
        
        # Check that the idea modified ts has changes.
        self.assertGreater(idea_new_ts, idea_old_ts)


    def test_check_idea_modified_is_correct(self):
        """Checks that the idea level modified is correct """

        response = self.c.get('/api/v1/idea/', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        for idea in objects:
            most_recent_comment = self.retrieve_most_recent_timestamp(idea['comments'])
            self.assertEquals(most_recent_comment.strftime('%Y-%m-%dT%H:%M:%S'),
                              datetime.datetime.strptime(idea['modified'], '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%dT%H:%M:%S'))

    def test_check_meta_modified_is_correct(self):
        """Checks that the meta-level modified is correct """
        
        response = self.c.get('/api/v1/idea/', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        most_recent_idea = self.retrieve_most_recent_timestamp(objects)
        most_recent_comment = datetime.datetime.utcnow() - datetime.timedelta(days=1000)
        for idea in objects:
            most_recent_comment = max([self.retrieve_most_recent_timestamp(idea['comments']), most_recent_comment])
        most_recent = max([most_recent_idea, most_recent_comment])
        
        self.assertEquals(most_recent, datetime.datetime.strptime(meta['modified'], '%Y-%m-%dT%H:%M:%S.%f'))

    def test_update_idea_tag_count(self):
        """ Check that the tag count changes if its edited."""
        
        # Get all data
        content = json.loads(self.c.get(self.resourceListURI('idea'), **self.headers).content)
        idea_0 = content['objects'][0]
        old_tags = idea_0['tags']
        old_tag_count = idea_0['tag_count']
        self.assertEquals(old_tag_count, 0)
        
        # Patch some tags in, having forgotten them first time round
        add_tags = {"tags" : ["physics","maths","geography","sports","english"]}
        response = self.c.patch(self.fullURItoAbsoluteURI(idea_0['resource_uri']), json.dumps(add_tags), content_type='application/json', **self.headers)
        content = json.loads(self.c.get(self.resourceListURI('idea'), **self.headers).content)
        
        # Retrieve the idea
        idea_0 = content['objects'][0]
        new_tags = idea_0['tags']
        new_tag_count = idea_0['tag_count']

        # Check its not the same as the previous one and is the intended new one        
        self.assertNotEqual(old_tags, new_tags)
        self.assertEqual(new_tag_count, 5)
        
#@utils.override_settings(DEBUG=True)
class Test_Data_Level_Responses(Test_Authentication_Base):

    def setUp(self):
        """ Add in some documents"""

        # Add a user and gain access to the API key and user
        user_id, api_key = self.add_user()
        self.headers = self.build_headers(user_id, api_key)

        # Insert 10 docs with different months
        for i in range(3):
            doc = {"title": "Idea #%s"%(i),"status":"published", "description": "First idea description in here."}
            # Just to check its there?
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            main_idea = response['location']
            
            comments_uri = self.fullURItoAbsoluteURI(main_idea) + 'comments/'
            # Try adding new comments
            for j in range (5):
                new_comment = {"user"   : "rich@rich.com",
                               "body"   : "#%s perhaps we could extend that idea by..."%(j),
                               "title"  : "and what about adding to that idea with %s..."%(j),
                               "protective_marking" : {"classification":"unclassified","descriptor":""}}
                # Just to check its there?
                self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
            
            dislikes_uri = self.fullURItoAbsoluteURI(main_idea) + 'dislikes/'
            new_dislike = {"user" : "dave@dave.com",
                           "comment" : {"title":"this is one of the worst ideas ever - someone else tried this and it failed."}}
            response = self.c.post(dislikes_uri, json.dumps(new_dislike), content_type='application/json', **self.headers) 
        
            likes_uri = self.fullURItoAbsoluteURI(main_idea) + 'likes/'
            response = self.c.post(likes_uri, json.dumps({"user" : "dave@dave.com"}), content_type='application/json', **self.headers) 
        
            
        # Check they went in OK
        content = json.loads(self.c.get(self.resourceListURI('idea'), **self.headers).content)
    
    def test_response_data_test_set_list(self):
        """Check that we get back the expected set of fields"""
        
        response = self.c.get('/api/v1/idea/?data_level=test', **self.headers)
        meta, data = self.get_meta_and_objects(response)
        data_response_keys = data[0].keys()
        for fld in settings.RESPONSE_FIELDS['test']:
            self.assertTrue(fld in data_response_keys)
        
    def test_response_data_test_set_meta(self):
        """Check that we get back the expected set of fields"""
        
        response = self.c.get('/api/v1/idea/?data_level=meta', **self.headers)
        content = json.loads(response.content)
        self.assertFalse(content.has_key('data'))
        self.assertTrue(content.has_key('meta'))

    def test_response_data_check_comments_modified(self):
        """Is there a meta.modified for a /idea/<id>/comments/ call?"""
        
        response = self.c.get('/api/v1/idea/?data_level=meta', **self.headers)
        content = json.loads(response.content)
        self.assertTrue(content.has_key('meta'))
        self.assertTrue(content['meta']['modified'])

#@utils.override_settings(DEBUG=True)
class Test_Contributor_Naming(Test_Authentication_Base):

    def setUp(self):
        """ Add in some documents"""

        # Add a user and gain access to the API key and user
        user_id, api_key = self.add_user()
        self.headers = self.build_headers(user_id, api_key)
        
        # We need another user for comments
        user_id2, api_key2 = self.add_user(email='dave@davison.com', first_name='dave', last_name='davidson')
        self.headers2 = self.build_headers(user_id2, api_key2)
        
        # We also need a 3rd user because of the unique constraint (applied in code logic) on like/dislike fields
        user_id3, api_key3 = self.add_user(email='john@cleese.com', first_name='john', last_name='cleese')
        self.headers3 = self.build_headers(user_id3, api_key3)


        # Insert 10 docs with different months
        for i in range(3):
            doc = {"title": "Idea #%s"%(i), "description": "First idea description in here.", "status": "published"}
            # Just to check its there?
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            main_idea = response['location']
            
            comments_uri = self.fullURItoAbsoluteURI(main_idea) + 'comments/'
            # Try adding new comments
            for j in range (5):
                new_comment = {"body"   : "#%s perhaps we could extend that idea by..."%(j),
                               "title"  : "and what about adding to that idea with %s..."%(j),
                               "protective_marking" : {"classification":"unclassified","descriptor":""}}
                # Just to check its there?
                self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers2) 
            
            dislikes_uri = self.fullURItoAbsoluteURI(main_idea) + 'dislikes/'
            new_dislike = {"comment" : {"title":"this is one of the worst ideas ever - someone else tried this and it failed."}}
            response = self.c.post(dislikes_uri, json.dumps(new_dislike), content_type='application/json', **self.headers2) 
        
            likes_uri = self.fullURItoAbsoluteURI(main_idea) + 'likes/'
            response = self.c.post(likes_uri, json.dumps({}), content_type='application/json', **self.headers3) 
        
    def test_idea_contributor_name(self):
        """ Check the idea has a contribtor name """
        
        response = self.c.get(self.resourceListURI('idea'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['contributor_name'], 'Bob Roberts')

    def test_comment_contributor_name(self):
        """ Check the comment has a contribtor name """
        
        response = self.c.get(self.resourceListURI('idea'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['comments'][0]['contributor_name'], 'Dave Davidson')
        
    def test_likes_contributor_name(self):
        """ Check the likes has a contribtor name """
        
        response = self.c.get(self.resourceListURI('idea'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['likes'][0]['contributor_name'], 'John Cleese')
                
    def test_dislikes_contributor_name(self):
        """ Check the dislikes has a contribtor name """
        
        response = self.c.get(self.resourceListURI('idea'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['dislikes'][0]['contributor_name'], 'Dave Davidson')
        


#@utils.override_settings(DEBUG=True)
class Test_Idea_With_Protective_Markings(Test_Authentication_Base):

    def setUp(self):
        """ Add in some documents"""

        # Add a user and gain access to the API key and user
        user_id, api_key = self.add_user()
        self.headers = self.build_headers(user_id, api_key)
        
    def test_submit_full_pm(self):
        """ Submit a complete protective marking """
        
        doc = {"title": "Idea #1",
               "description": "First idea description in here.",
               "status" : "published",
               "protective_marking" : {"classification" : "PUBLIC",
                                       "classification_short" : "PU",
                                       "classification_rank" : 0,
                                       
                                       "national_caveats_primary_name" : 'ME ONLY',
                                       "national_caveats_members" : [],
                                       
                                       "codewords" : ['BANANA 1', 'BANANA 2'],
                                       "codewords_short" : ['B1', 'B2'],
                                       
                                       "descriptor" : 'PRIVATE'}
               }
               
        # Just to check its there?
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        response = self.c.get(self.resourceListURI('idea'))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['protective_marking']['classification'], 'PUBLIC')        
        self.assertEquals(objects[0]['protective_marking']['pretty_pm'], 'PUBLIC [PRIVATE] BANANA 1/BANANA 2 ME ONLY')
        
        # Check that it also comes out in the idea-level content
        self.assertEquals(objects[0]['pretty_pm'], 'PUBLIC [PRIVATE] BANANA 1/BANANA 2 ME ONLY')
        
        
    def test_submit_classification(self):
        """ Submit a classification """
        
        doc = {"title": "Idea #1",
               "description": "First idea description in here.",
               "status": "published",
               "protective_marking" : {"classification" : "PUBLIC",
                                       "classification_short" : "PU",
                                       "classification_rank" : 0,
                                       }
               }
        
        # Just to check its there?
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        response = self.c.get(self.resourceListURI('idea'))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['protective_marking']['classification'], 'PUBLIC')
        self.assertEquals(objects[0]['protective_marking']['pretty_pm'], 'PUBLIC')
        
        
    def test_submit_national_caveats(self):
        """ Submit a national caveat """

        doc = {"title": "Idea #1",
               "description": "First idea description in here.",
               "status":"published",
               "protective_marking" : {"national_caveats_primary_name" : 'ME ONLY',
                                       "national_caveats_members" : ['1', '2', '3'],
                                       }
               }

        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        response = self.c.get(self.resourceListURI('idea'))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['protective_marking']['national_caveats_primary_name'], 'ME ONLY')
        self.assertEquals(objects[0]['protective_marking']['national_caveats_members'], ['1','2','3'])
        self.assertEquals(objects[0]['protective_marking']['pretty_pm'], 'CLASSIFICATION NOT KNOWN ME ONLY')
        

    def test_submit_codewords(self):
        """ Submit a codeword """

        doc = {"title": "Idea #1",
               "description": "First idea description in here.",
               "status":"published",
               "protective_marking" : {"codewords" : ['BANANA 1', 'BANANA 2'],
                                       "codewords_short" : ['B1', 'B2']}
               }

        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        response = self.c.get(self.resourceListURI('idea'))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['protective_marking']['codewords'], ['BANANA 1', 'BANANA 2'])
        self.assertEquals(objects[0]['protective_marking']['codewords_short'], ['B1', 'B2'])
        self.assertEquals(objects[0]['protective_marking']['pretty_pm'], 'CLASSIFICATION NOT KNOWN BANANA 1/BANANA 2')

    def test_submit_descriptors(self):
        """ Submit descriptors """

        doc = {"title": "Idea #1",
               "description": "First idea description in here.",
               "status":"published",
               "protective_marking" : {"descriptor" : 'PRIVATE'}
               }

        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        response = self.c.get(self.resourceListURI('idea'))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['protective_marking']['descriptor'], 'PRIVATE')
        self.assertEquals(objects[0]['protective_marking']['pretty_pm'], 'CLASSIFICATION NOT KNOWN [PRIVATE]')
        

#@utils.override_settings(DEBUG=True)
class Test_Get_All_PMs(TestCase):
        
    def setUp(self):
        
        self.sample_pms = [{'classification':'public','classification_short':'PU'},
                           {'classification':'group','classification_short':'GR'},
                           {'classification':'private','classification_short':'PR'},
                           {'classification':'personal','classification_short':'PE'}]

        # Build up a PM
        self.pm  = documents.ProtectiveMarking(classification='PUBLIC',
                                               classification_short='PU',
                                               classification_rank=0,
                                               descriptor='BUSINESS',
                                               codewords=['THIS','THAT'],
                                               codewords_short=['T1','T2'],
                                               national_caveats_primary_name='ME ONLY',
                                               national_caveats_members=['1','2','3'],
                                               national_caveats_rank=2)

    #===============================================================================
    #        
    # COMMENTED BECAUSE I CAN'T WORK OUT HOW TO BUILD A BUNDLE INSIDE A TEST
    # 
    #     def test_get_pm_from_top_level_only(self):
    #         """Retrieves pms from a set of objects."""
    # 
    #         docs = []
    #         for i in range(4):
    # 
    #             new_pm = copy.deepcopy(self.pm)
    #             new_pm['classification']        = self.sample_pms[i]['classification']
    #             new_pm['classification_short']  = self.sample_pms[i]['classification_short']
    # 
    #             doc = documents.Idea(title ='new idea', protective_marking = new_pm)
    #             #print doc.to_json()
    # 
    #             docs.append(doc)
    # 
    #         pm_list = api.get_all_pms(docs)
    #         
    #         self.assertEquals(len(pm_list), 4)
    # 
    # 
    #     def test_get_pm_from_top_level_and_nested(self):
    #         """Retrieves pms from a set of objects and sub objects."""
    # 
    #         docs = []
    # 
    #         for i in range(4):
    # 
    #             new_pm = copy.deepcopy(self.pm)
    #             new_pm['classification']        = self.sample_pms[i]['classification']
    #             new_pm['classification_short']  = self.sample_pms[i]['classification_short']
    # 
    #             # Loop and create some comments
    #             comments = [documents.Comment(title='new comment', body='great idea', protective_marking=new_pm) for i in range(3)]
    #             
    #             # Create the document
    #             doc = documents.Idea(title ='new idea',
    #                                  comments=comments,
    #                                  protective_marking=new_pm)
    #             docs.append(doc)
    # 
    #         pm_list = api.get_all_pms(docs)
    #         
    #         self.assertEquals(len(pm_list), 16)
    #         
    #===============================================================================

    def test_get_max_pm_inject_PU(self):
        """Retrieves the max pm"""

        pm_list = []
        for i in range(3):
            pm = copy.deepcopy(self.pm)
            pm_list.append(pm)
            
        max_pm = api.get_max_pm(pm_list)
        self.assertEquals(max_pm['classification'], 'PUBLIC')


    def test_get_max_pm_inject_PR(self):
        """Retrieves the max pm"""

        pm_list = []
        for i in range(3):
            pm = copy.deepcopy(self.pm)
            pm_list.append(pm)
        
        pm_list[0]['classification']='PRIVATE'
        pm_list[0]['classification_short']='PR'
        pm_list[0]['classification_rank']=2
        
        max_pm = api.get_max_pm(pm_list)
        self.assertEquals(max_pm['classification'], 'PRIVATE')

    def test_get_max_pm_inject_PE(self):
        """Retrieves the max pm"""

        pm_list = []
        for i in range(3):
            pm = copy.deepcopy(self.pm)
            pm_list.append(pm)
       
        pm_list[0]['classification']='PERSONAL'
        pm_list[0]['classification_short']='PE'
        pm_list[0]['classification_rank']=3
        
        max_pm = api.get_max_pm(pm_list)
        self.assertEquals(max_pm['classification'], 'PERSONAL')

    def test_get_max_pm_nat_cavs(self):
        """Retrieves the max pm - check national cavs"""

        pm_list = []
        for i in range(3):
            pm = copy.deepcopy(self.pm)
            pm_list.append(pm)

        pm_list[0]['national_caveats_primary_name']='HIM ONLY'
        pm_list[0]['national_caveats_members']= ['1','2']
        pm_list[0]['national_caveats_rank']=3
        
        max_pm = api.get_max_pm(pm_list)
        self.assertEquals(max_pm['national_caveats_primary_name'], 'HIM ONLY')
        self.assertEquals(max_pm['national_caveats_members'], ['1','2'])
        self.assertEquals(max_pm['national_caveats_rank'], 3)

    def test_get_max_pm_multiple_descriptors(self):
        """Retrieves the max pm"""
        
        descriptors=['LOCSEN','PRIVATE','PERSONAL']

        pm_list = []
        for i in range(3):
            pm = copy.deepcopy(self.pm)
            pm['descriptor']=descriptors[i]
            pm_list.append(pm)
        
        max_pm = api.get_max_pm(pm_list)
        self.assertEquals(max_pm['descriptor'], 'LOCSEN,PRIVATE,PERSONAL')

    def test_get_max_pm_multiple_codewords(self):
        """Retrieves the max pm"""
        
        codewords=['BANANA1','BANANA2','BANANA3']

        pm_list = []
        for i in range(3):
            pm = copy.deepcopy(self.pm)
            pm['codewords']=[codewords[i]]
            pm_list.append(pm)
        
        max_pm = api.get_max_pm(pm_list)
        self.assertEquals(sorted(max_pm['codewords']), sorted(codewords))
        
#@utils.override_settings(DEBUG=True)
class Test_Max_PM_in_Meta(Test_Authentication_Base):

    def setUp(self):
        """ Add in some documents"""

        # Add a user and gain access to the API key and user
        user_id, api_key = self.add_user()
        self.headers = self.build_headers(user_id, api_key)
        
        # We need another user for comments
        user_id2, api_key2 = self.add_user(email='dave@davison.com', first_name='dave', last_name='davidson')
        self.headers2 = self.build_headers(user_id2, api_key2)
        
        # We also need a 3rd user because of the unique constraint (applied in code logic) on like/dislike fields
        user_id3, api_key3 = self.add_user(email='john@cleese.com', first_name='john', last_name='cleese')
        self.headers3 = self.build_headers(user_id3, api_key3)

        self.pm  = {'classification':'PUBLIC',
                    'classification_short':'O',
                    'classification_rank':0,
                    'descriptor':'PRIVATE',
                    'codewords':['THIS','THAT'],
                    'codewords_short':['T1','T2'],
                    'national_caveats_primary_name':'ME ONLY',
                    'national_caveats_members':['1','2','3'],
                    'national_caveats_rank':2
                    }


    def test_just_idea_level_O(self):
        """ just pms in the ideas - all at O to overcome a bug where PUBLIC wasn't rendering a max pm."""

        doc = {"title": "Idea #1",
               "description": "First idea description in here.",
               "status":"published",
               'protective_marking' : self.pm}
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        response = self.c.get(self.resourceListURI('idea'))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['max_pm']['classification'], 'PUBLIC')


    def test_just_idea_level(self):
        """ just pms in the ideas """

        # Insert a couple of documents
        doc = {"title": "Idea #1", "description": "First idea description in here.", 'protective_marking' : self.pm, "status":"published"}
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        doc = {"title": "Idea #2", "description": "First idea description in here.", 'protective_marking' : self.pm, "status":"published"}
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        
        # Bump the classification on the final one
        doc['protective_marking']['classification'] = 'PRIVATE'
        doc['protective_marking']['classification_short'] = 'PR'
        doc['protective_marking']['classification_rank'] = 2
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)

        response = self.c.get(self.resourceListURI('idea'))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['max_pm']['classification'], 'PRIVATE')

    def test_include_embedded_level(self):
        """ PMs inside the embedded level too """

        # Insert a couple of documents
        doc = {"title": "Idea #1", "description": "First idea description in here.", 'protective_marking' : self.pm, "status": "published"}
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        doc = {"title": "Idea #2", "description": "First idea description in here.", 'protective_marking' : self.pm, "status": "published"}
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        
        # Bump the classification on the final one
        doc['protective_marking']['classification'] = 'PRIVATE'
        doc['protective_marking']['classification_short'] = 'PR'
        doc['protective_marking']['classification_rank'] = 2
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)

        response = self.c.get(self.resourceListURI('idea'))
        meta, objects = self.get_meta_and_objects(response)
        comments_uri = objects[0]['resource_uri'] + 'comments/'
        
        pm = copy.deepcopy(self.pm)
        pm['classification'] = 'PERSONAL'
        pm['classification_short'] = 'PE'
        pm['classification_rank'] = 3
        
        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "and what about adding to that idea with...",
                       "protective_marking" : pm}
        
        # Just to check its there?
        response = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers2) 
        check = response['location']
        response = self.c.get(check)
        
        response = self.c.get(self.resourceListURI('idea'))
        
        meta, objects = self.get_meta_and_objects(response)
        
        self.assertEquals(meta['max_pm']['classification'], 'PERSONAL')


#----------------------------------------------------------------------------------------

#@utils.override_settings(DEBUG=True)
class Test_Deletes(Test_Authentication_Base):

    def setUp(self):

        # Add a user and gain access to the API key and user
        user_id, api_key = self.add_user()
        self.headers = self.build_headers(user_id, api_key)
        user_id2, api_key2 = self.add_user(email='dave@dave.com', first_name='dave', last_name='david')
        self.headers2 = self.build_headers(user_id2, api_key2)
                
        self.pm =   {"classification"                : "PUBLIC",
                     "classification_short"          : "PU",
                     "classification_rank"           : 0,
                     "national_caveats_primary_name" : "MY EYES ONLY",
                     "descriptor"                    : "private",
                     "codewords"                     : ["banana1","banana2"],
                     "codewords_short"               : ["b1","b2"],
                     "national_caveats_members"      : ["ME"],
                     "national_caveats_rank"         : 3}
        
        """ Insert documents to start with"""
        docs = [{"title": "The first idea.",
                 "description": "First idea description in here.",
                 "tags" : ["physics","maths","geography","sports","english"],
                 "protective_marking":self.pm, 
                 "status" : "published"},
                
                {"title": "The second idea.",
                 "description": "second idea description in here.",
                 "tags" : ["physics","maths","geography","sports"],
                 "protective_marking":self.pm,
                 "status" : "published"}]
        
        # Store the responses
        self.doc_locations = []
        x = 0
        for doc in docs:
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)

            idea_url = response['location']
            comments_uri = idea_url + 'comments/'
            new_comment = {"body"   : "perhaps we could extend that idea by...",
                            "title"  : "and what about adding to that idea with...",
                            "protective_marking" : self.pm}
            for i in range(x):
                comment_resp = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
                
            x += 1
            
            time.sleep(1)
            
        response = self.c.get(self.resourceListURI('idea')+'?data_level=less', **self.headers)

    def test_delete_comment_decrement_count(self):
        """ Delete a comment from an idea and check the comment_count reduces """                 
        
        # Get the id for the idea
        response = self.c.get(self.resourceListURI('idea'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        idea1_id = objects[1]['id']
        
        # Count the comments
        resp = self.c.get(self.resourceDetailURI('idea', idea1_id), **self.headers)
        meta, objects = self.get_meta_and_objects(resp)
        self.assertEquals(objects[0]['comment_count'], 1)
        
        # Delete the comment
        path = self.resourceListURI('idea')+'%s/comments/0/'%(idea1_id)
        resp = self.c.delete(path, content_type='application/json', **self.headers)
        
        response = self.c.get(self.resourceDetailURI('idea', idea1_id), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['comment_count'], 0)

    def test_delete_when_multiple_comments(self):
        """ Create a comment - done in setup
            Create another comment - done here
            Attempt to delete a comment by specific URI
        """
        
        # Get the idea id
        response = self.c.get(self.resourceListURI('idea'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        idea1_id = objects[1]['id']
        
        # Build the comments URI
        comments_uri = self.resourceDetailURI('idea', idea1_id)+'comments/'

        # Post a new comment
        new_comment = {"body"   : "perhaps we could extend that idea by...",
                       "title"  : "and what about adding to that idea with...",
                       "protective_marking" : self.pm}
        
        comment_resp = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 

        # Check there are now 2 comments
        response = self.c.get(self.resourceDetailURI('idea', idea1_id), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['comment_count'], 2)
        self.assertEquals(len(objects[0]['comments']), 2)

        # Delete the first comment
        delete_uri = comments_uri + '0/'
        resp = self.c.delete(delete_uri, content_type='application/json', **self.headers)
        self.assertEquals(resp.status_code, 204)
        
        # Now check that it definitely got deleted
        response = self.c.get(self.resourceDetailURI('idea', idea1_id), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['comment_count'], 1)
        self.assertEquals(len(objects[0]['comments']), 1)


#@utils.override_settings(DEBUG=True)
class Test_Get_Non_Standard_Fields(Test_Authentication_Base):

    def setUp(self):

        # Add a user and gain access to the API key and user
        user_id, api_key = self.add_user()
        self.headers = self.build_headers(user_id, api_key)
        user_id2, api_key2 = self.add_user(email='dave@dave.com', first_name='dave', last_name='david')
        self.headers2 = self.build_headers(user_id2, api_key2)
                
        self.pm =   {"classification"                : "PUBLIC",
                     "classification_short"          : "PU",
                     "classification_rank"           : 0,
                     "national_caveats_primary_name" : "MY EYES ONLY",
                     "descriptor"                    : "private",
                     "codewords"                     : ["banana1","banana2"],
                     "codewords_short"               : ["b1","b2"],
                     "national_caveats_members"      : ["ME"],
                     "national_caveats_rank"         : 3}
        
        """ Insert documents to start with"""
        docs = [{"title": "The first idea.",
                 "description": '<a href="http://www.example.com">First</a> idea <b>description</b> in here.',
                 "tags" : ["physics","maths","geography","sports","english"],
                 "protective_marking":self.pm, 
                 "status" : "published"},
                
                {"title": "The second idea.",
                 "description": "<h2>second</h2> idea <b>description</b> in here." + " The quick brown fox jumped over the lazy dog."*10,
                 "tags" : ["physics","maths","geography","sports"],
                 "protective_marking":self.pm,
                 "status" : "published"}
                 ]
        
        # Store the responses
        self.doc_locations = []
        x = 0
        for doc in docs:
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)

            idea_url = response['location']

            comments_uri = idea_url + 'comments/'
            new_comment = {"body"   : "perhaps we could <b> extend </b> that idea by...",
                            "title"  : "and what about adding to that idea with...",
                            "protective_marking" : self.pm}
            for i in range(x):
                comment_resp = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
                
            x += 1
            
            time.sleep(1)
            
    def test_check_description_snippet(self):
        """ Checks we get back a snippet of the description from html """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('idea'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        
        #First doc - short
        self.assertEquals(objects[0]['description_snippet'], 'First idea description in here.')
        self.assertEquals(objects[1]['description_snippet'], 'second idea description in here. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox...')
        

class Test_Basic_API_Functions(TestCase):
    
    def test_strip_tags(self):
        """ Tests stripping html tags"""
        
        text = """<b><a href="http://www.helloworld.com">this is the text</a></b>"""
        text = api_functions.strip_tags(text)
        self.assertEquals(text, "this is the text")
        
    def test_smart_truncate_short_string(self):
        """ Tests truncating on full words"""
        
        text = "the quick brown fox jumped over the lazy dog."
        text = api_functions.smart_truncate(content=text, length=180, suffix='...')
        self.assertEquals(text, 'the quick brown fox jumped over the lazy dog.')
        
    def test_smart_truncate(self):
        """ Tests truncating on full words"""
        
        text = "the quick brown fox jumped over the lazy dog."
        text = api_functions.smart_truncate(content=text, length=18, suffix='...')
        self.assertEquals(text, 'the quick brown...')
        
    
    def test_derive_snippet(self):
        """ Tests complete snippet derivation """
        
        text = """<b><a href="http://www.helloworld.com">the quick brown fox jumped over the lazy dog.</a></b>"""
        text = api_functions.derive_snippet(text_html=text, chrs=18)
        self.assertEquals(text, 'the quick brown...')

    def test_vote_score_low_number_of_obs(self):
        """ Like / dislike score """
        
        likes = 1
        dislikes = 1
        
        score = api_functions.vote_score(likes, dislikes)
        self.assertLess(score, 0.1)

    def test_vote_score_high_number_of_obs(self):
        """ Like / dislike score """
        
        likes = 400
        dislikes = 400
        
        score = api_functions.vote_score(likes, dislikes)
        self.assertAlmostEqual(score, 0.465, 3)

    def test_cleanup_tags(self):
        """ Cleanup the tags submitted from the front-end to avoid XSS risks """
        
        tags = ['<a href="http://badplace.com/script.js">puppies</a>',
                '<SCRIPT SRC=http://ha.ckers.org/xss.js></SCRIPT>',
                """<IMG SRC="javascript:alert('XSS');">""",
                "<IMG SRC=javascript:alert('XSS');>",
                "<IMG SRC=JaVaScrIpT:alert('XSS');>",
                """<IMG SRC=`javascript:alert("puppies, 'puppies'");>`""",
                '<a onmouseover="alert(document.cookie)">puppies</a>',
                '<a onmouseover=alert(document.cookie)>puppies</a>',
                '<a onmouseover=alert(document.cookie)>puppies</a>',
                '<b>kittens</b>']
        
        clean_tags = api_functions.cleanup_tags(tags)
        self.assertEquals(clean_tags, [u'puppies', u'', u'', u'', u'', u'`', u'puppies', u'puppies', u'puppies', u'kittens'])
        
        