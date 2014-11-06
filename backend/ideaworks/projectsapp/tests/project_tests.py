
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

import projectsapp.documents as documents
from projectsapp import api
from projectsapp import api_functions

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
        response = self.c.get(self.resourceListURI('project'))
        if settings.ANONYMOUS_VIEWING == True:
            self.assertEquals(response.status_code, 200)
        else:
            self.assertEquals(response.status_code, 401)
    
    def test_auth_block_a_POST(self):
        """ Authentication block on a post request """
    
        # Don't actually use the headers in the call
        data = {"title": "This project will never stick...",
                 "description": "First project description in here.",
                 "status":"published",
                 "protective_marking" : {"classification"   : "public",
                                         "descriptor"      : "private"
                                         }}
        
        response = self.c.post(self.resourceListURI('project'), data=json.dumps(data), content_type='application/json')
        self.assertEquals(response.status_code, 401)

    def test_auth_block_a_non_staff_POST(self):
        """ Authorization blocks a POST request by a non-staff user """
    
        # Don't actually use the headers in the call
        data = {"title": "This project will never stick...",
                 "description": "First project description in here.",
                 "status":"published",
                 "protective_marking" : {"classification"   : "public",
                                         "descriptor"      : "private"
                                         }}
        
        response = self.c.post(self.resourceListURI('project'), data=json.dumps(data), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 401)

    def test_auth_allow_staff_POST(self):
        """ Authorization allows POST by staff user """
    
        user_id, api_key = self.add_user("staff_user1@projects.com")
        user = self.give_privileges(user_id, priv='staff')
        headers = self.build_headers(user_id, api_key)
        
        # Don't actually use the headers in the call
        data = {"title": "This project will never stick...",
                 "description": "First project description in here.",
                 "status":"published",
                 "related_ideas":["xcxcxcxcxcxcxcxcxcxcxcxcxcxcx", "xcxcxcxcxcxcxcxcxcxcxcxcxcxcx"],
                 "protective_marking" : {"classification"   : "public",
                                         "descriptor"      : "private"
                                         }}
        
        response = self.c.post(self.resourceListURI('project'), data=json.dumps(data), content_type='application/json', **headers)
        self.assertEquals(response.status_code, 201)

#------------------------------------------------------------------------------------------------------------

#@utils.override_settings(DEBUG=True)
class Test_Simple_GET_Project_API(Test_Authentication_Base):

    def setUp(self):
        """ Insert documents to start with"""
        
        # Add a user and gain access to the API key and user
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)
        
        response = self.c.get(self.resourceListURI('project'), **self.headers)
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
            
        docs = [{"title": "The first project.",
                 "description": "First project description in here.",
                 "status":"published",
                 "protective_marking" : self.pm },
                {"title": "The second project.",
                 "description": "Second project description in here.",
                 "status":"published",
                 "protective_marking" : self.pm }
                ]
        
        # Store the responses
        self.doc_locations = []
        for doc in docs:
            response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)

    def test_get_to_check_failure_anon(self):
        """ Test to check that new status code isn't backwards breaking"""
        
        url = '/api/v1/project/?data_level=more&limit=3&offset=0&order_by=-created&status=published'
        response = self.c.get(url)
        self.assertEquals(response.status_code, 200)

    def test_get_to_check_failure_authenticated(self):
        """ Test to check that new status code isn't backwards breaking for authenticated user"""
        
        url = '/api/v1/project/?data_level=more&limit=3&offset=0&order_by=-created&status=published'
        response = self.c.get(url, **self.headers)
        self.assertEquals(response.status_code, 200)
        
    def test_get_to_check_failure_authenticated_admin(self):
        """ Test to check that new status code isn't backwards breaking for authenticated ADMIN user"""
        
        user_id, api_key = self.add_user()
        user = self.give_privileges(user_id, priv='staff')
        headers = self.build_headers(user_id, api_key)
        
        url = '/api/v1/project/?data_level=more&limit=3&offset=0&order_by=-created&status=published'
        response = self.c.get(url, **headers)
        self.assertEquals(response.status_code, 200)
        
    def test_get_all_projects(self):
        """ Retrieve all projects """
        
        response = self.c.get(self.resourceListURI('project'), **self.headers)
        self.assertEquals(response.status_code, 200)
        meta, content = self.get_meta_and_objects(response)
        self.assertEquals(meta['total_count'], 2)
        self.assertEquals(len(content), 2)
        
    #TODO: Sort out xml tests
    
    def test_get_xml_list(self):
        """ Get an xml representation
            This will ERROR rather than FAIL if it doesn't succeed."""
        
        response = self.c.get('/api/%s/project/?format=xml'%(self.api_name), **self.headers)
        self.assertEquals(response.status_code, 200)
        xml = parseString(response.content)
        
    def test_get_xml_list_fail(self):
        """ Get an xml representation - fails on content """
        
        response = self.c.get('/api/%s/project/?format=xml'%(self.api_name), **self.headers)
        self.assertEquals(response.status_code, 200)
        self.assertRaises(ExpatError, parseString, response.content+'<hello world')

    def test_get_csv_list(self):
        """ Get an xml representation - fails on content """
        
        response = self.c.get('/api/%s/project/?format=csv'%(self.api_name), **self.headers)
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
        
        response = self.c.get('/api/%s/projectx'%(self.api_name), **self.headers)
        self.assertEquals(response.status_code, 404)
        
    def test_get_1_project(self):
        """ Retrieve 1 project """
        
        pk = self.doc_locations[1].rstrip('/').split('/')[-1]
        response = self.c.get(self.resourceDetailURI('project', pk), **self.headers)
        self.assertEquals(response.status_code, 200)
        
    def test_get_no_project(self):
        """ Fail to retrieve an project """
        
        pk = self.doc_locations[1].rstrip('/').split('/')[-1] + '_fake'
        response = self.c.get(self.resourceDetailURI('project', pk), **self.headers)
        self.assertEquals(response.status_code, 404)

#------------------------------------------------------------------------------------------------------------

#@utils.override_settings(DEBUG=True)
class Test_Simple_GET_Project_specifics(Test_Authentication_Base):

    def setUp(self):
        """ Insert documents to start with"""
        
        # Add a user and gain access to the API key and user
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)
        response = self.c.get(self.resourceListURI('project'), **self.headers)
        
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
            
        docs = [{"title": "The first project.",
                 "description": "First project description in here.",
                 "protective_marking" : self.pm,
                 "status":"published",
                  "tags" : ["project", "physics"]
                },
                {"title": "The second project.",
                 "description": "Second project description in here.",
                 "protective_marking" : self.pm,
                 "status":"published",
                 "tags" : ["project", "another_tag"]
                 }
                ]
        
        # Store the responses
        self.doc_locations = []
        for doc in docs:
            response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)
        
    def test_get_project_tag_list(self):
        """ Check that the tag list works OK """
        
        pk = self.doc_locations[1].rstrip('/').split('/')[-1]
        response = self.c.get(self.resourceDetailURI('project', pk), **self.headers)
        self.assertEquals(response.status_code, 200)
        data = json.loads(response.content)['objects'][0]
        self.assertEquals(data['tags'], ['project','another_tag'])


    def test_get_project_detail_check_meta_mx_pm(self):
        """ Checks that the detail levell has a meta.max_pm object """
        
        pk = self.doc_locations[1].rstrip('/').split('/')[-1]
        response = self.c.get(self.resourceDetailURI('project', pk), **self.headers)
        self.assertEquals(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertTrue(meta.has_key('max_pm'))
        
    def test_get_project_detail_check_meta_modified(self):
        """ Checks that the detail levell has a meta.modified object """
        
        pk = self.doc_locations[1].rstrip('/').split('/')[-1]
        response = self.c.get(self.resourceDetailURI('project', pk), **self.headers)
        self.assertEquals(response.status_code, 200)
        meta, objects = self.get_meta_and_objects(response)
        self.assertTrue(meta.has_key('modified'))
                

#@utils.override_settings(DEBUG=True)
class Test_Filtered_GET_Project_API(Test_Authentication_Base):

    def setUp(self):

        # Add a user and gain access to the API key and user
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)

        # 2 more users        
        user_id2, api_key2 = self.add_user(email='dave@dave.com', first_name='dave', last_name='david')
        self.headers2 = self.build_headers(user_id2, api_key2)
        user_id3, api_key3 = self.add_user(email='sue@sue.com', first_name='sue', last_name='mcgrew')
        self.headers3 = self.build_headers(user_id3, api_key3)

                
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
        docs = [{"title": "The first project.",
                 "description": "First project description in here.",
                 "tags" : ["physics","maths","geography","sports","english"],
                 "protective_marking":self.pm, 
                 "status" : "published",
                 "related_ideas": ["xsft64kxj312n47jodam47o","xsft64kxj312n47jodam47o"]},
                
                {"title": "The second project.",
                 "description": "second project description in here.",
                 "tags" : ["physics","maths","geography","sports"],
                 "protective_marking":self.pm,
                 "status" : "published",
                 "related_ideas": ["xsft64kxj312n47jodam47o","xsft64kxj312n47jodam47o"]},
                
                {"title": "The third project.",
                 "description": "third project description in here.",
                 "tags" : ["physics","maths","geography"],
                 "protective_marking":self.pm,
                 "status" : "published",
                 "related_ideas": ["xsft64kxj312n47jodam47o","xsft64kxj312n47jodam47o"]},
                
                {"title": "The Forth project.",
                 "description": "forth project description in here.",
                 "tags" : ["physics","maths"],
                 "protective_marking":self.pm,
                 "status" : "published",
                 "related_ideas": ["xsft64kxj312n47jodam47o","xsft64kxj312n47jodam47o"]},

                {"title": "The Fifth project.",
                 "description": "fifth project description in here.",
                 "tags" : ["physics", "history"],
                 "protective_marking":self.pm,
                 "status" : "published",
                 "related_ideas": []},
                
                {"title": "The Sixth project.",
                 "description": "fifth project description in here.",
                 "tags" : ["history", "design"],
                 "protective_marking":self.pm,
                 "status" : "published",
                 "related_ideas": []}
                ]
        
        # Store the responses
        self.doc_locations = []
        x = 0
        for doc in docs:
            response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)

            project_url = response['location']
                
            backs_uri = project_url + 'backs/'
            backs = [{"comment" : {"title":"very good project. I support."}}]
            for back in backs:
                back_resp = self.c.post(backs_uri, json.dumps(back), content_type='application/json', **self.headers2) 
                self.assertEquals(back_resp.status_code, 201)
                
            comments_uri = project_url + 'comments/'
            new_comment = {"body"   : "perhaps we could extend that project by...",
                            "title"  : "and what about adding to that project with...",
                            "protective_marking" : self.pm}
            for i in range(x):
                comment_resp = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers3) 
                self.assertEquals(comment_resp.status_code, 201)
                
            x += 1
            
            time.sleep(1)
            
        response = self.c.get(self.resourceListURI('project')+'?data_level=less', **self.headers)
        
    def test_filter_by_comment_count_GTE(self):
        """ GTE filter on comment count """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('project')+'?comment_count__gte=3', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        
        self.assertEquals(len(objects), 4)
        self.assertEqual(meta['total_count'], 4)

    def test_filter_by_comment_count_LTE(self):
        """ less than or eq filter on comment_count """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('project')+'?comment_count__lte=2', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 2)
        self.assertEqual(meta['total_count'], 2)

    def test_filter_by_1tag_all_doc(self):
        """ Tag Filter - catch all documents with 1 tag """
        
        # Retrieve all results
        tags = ['physics', 'maths', 'geography', 'sports', 'english']
                
        response = self.c.get(self.resourceListURI('project')+'?data_level=less&tags=physics', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 5)
        self.assertEqual(meta['total_count'], 5)
                
    def test_filter_by_1tag_1_doc(self):
        """ Range filter on comment count """
        
        # Retrieve all results
        tags = ['physics', 'maths', 'geography', 'sports', 'english']
        
        response = self.c.get(self.resourceListURI('project')+'?data_level=more&tags=english', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)
        self.assertEqual(meta['total_count'], 1)

    def test_filter_by_1tag_1_doc_exact(self):
        """ Range filter on comment count """
        
        # Retrieve all results
        tags = ['physics', 'maths', 'geography', 'sports', 'english']
        
        response = self.c.get(self.resourceListURI('project')+'?data_level=more&tags=english', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)
        self.assertEqual(meta['total_count'], 1)


    def test_filter_by_multiple_tags_OR(self):
        """ There is 1 doc with an english tag and 1 with a history tag. This should get those 2. """
        
        # Retrieve all results
        tags = ['physics', 'maths', 'geography', 'sports', 'english', 'history']
        
        response = self.c.get(self.resourceListURI('project')+'?data_level=less&tags__in=english,history', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 3)
        self.assertEqual(meta['total_count'], 3)

    def test_filter_by_multiple_tags_check_post_sorting(self):
        """ A list of tags in the q parameter matches exactly
            the code for this is a modification that sorts the results of an __in query"""
        
        # Retrieve all results
        tags = ['physics', 'maths', 'geography', 'sports', 'english', 'history']
        
        response = self.c.get(self.resourceListURI('project')+'?data_level=less&tags__in=physics,history,design', **self.headers)

        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 6)
        self.assertEqual(meta['total_count'], 6)
        self.assertEquals(objects[0]['tags'], ["physics","history"])
        self.assertEquals(objects[1]['tags'], ["history","design"])

#@utils.override_settings(DEBUG=True)
class Test_Filtered_GET_Project_API_modified_status(Test_Authentication_Base):

    def setUp(self):

        # Add a user and gain access to the API key and user
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)
        
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
        docs = [{"title": "The first project.",
                 "description": "First project description in here.",
                 "tags" : ["physics","maths","geography","sports","english"],
                 "protective_marking":self.pm, 
                 "status" : "published",
                 "related_ideas": ["xsft64kxj312n47jodam47o","xsft64kxj312n47jodam47o"]},
                
                {"title": "The second project.",
                 "description": "second project description in here.",
                 "tags" : ["physics","maths","geography","sports"],
                 "protective_marking":self.pm,
                 "status" : "published",
                 "related_ideas": ["xsft64kxj312n47jodam47o","xsft64kxj312n47jodam47o"]},
                
                {"title": "The third project.",
                 "description": "third project description in here.",
                 "tags" : ["physics","maths","geography"],
                 "protective_marking":self.pm,
                 "status" : "draft",
                 "related_ideas": ["xsft64kxj312n47jodam47o","xsft64kxj312n47jodam47o"]},
                
                {"title": "The Forth project.",
                 "description": "forth project description in here.",
                 "tags" : ["physics","maths"],
                 "protective_marking":self.pm,
                 "status" : "draft",
                 "related_ideas": ["xsft64kxj312n47jodam47o","xsft64kxj312n47jodam47o"]},

                {"title": "The Fifth project.",
                 "description": "fifth project description in here.",
                 "tags" : ["physics", "history"],
                 "protective_marking":self.pm,
                 "status" : "hidden",
                 "related_ideas": ["xsft64kxj312n47jodam47o","xsft64kxj312n47jodam47o"]},
                
                {"title": "The Sixth project.",
                 "description": "fifth project description in here.",
                 "tags" : ["history", "design"],
                 "protective_marking":self.pm,
                 "status" : "deleted",
                 "related_ideas": ["xsft64kxj312n47jodam47o","xsft64kxj312n47jodam47o"]},
                 ]

        # Store the responses
        self.doc_locations = []
        x = 0
        for doc in docs:
            response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)

    def test_staff_filter_by_status_published(self):
        """ Get projects which have been published -accessed by staff user """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('project')+'?status=published', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 2)
        self.assertEqual(meta['total_count'], 2)

    
    def test_filter_by_status_published(self):
        """ Get projects which have been published - accessed by non-staff user"""
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('project')+'?status=published', **self.headers2)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 2)
        self.assertEqual(meta['total_count'], 2)

    def test_staff_filter_by_status_draft(self):
        """ Get projects which have been draft """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('project')+'?status=draft', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 2)
        self.assertEqual(meta['total_count'], 2)

    def test_staff_filter_by_status_deleted(self):
        """ Get projects which have been deleted """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('project')+'?status=deleted', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)
        self.assertEqual(meta['total_count'], 1)

    def test_staff_filter_by_status_hidden(self):
        """ Get projects which have been hidden """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('project')+'?status=hidden', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 1)
        self.assertEqual(meta['total_count'], 1)

    def test_staff_filter_by_status_multiple(self):
        """ Get projects by status using status__in syntax """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('project')+'?status__in=published,draft', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 4)
        self.assertEqual(meta['total_count'], 4)

    def test_staff_filter_by_status_multiple_2(self):
        """ Get projects by status using status__in syntax """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('project')+'?status__in=hidden,deleted', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 2)
        self.assertEqual(meta['total_count'], 2)

    def test_non_staff_filter_by_status_multiple_2(self):
        """ Get projects by status using status__in syntax """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('project')+'?status__in=hidden,deleted', **self.headers2)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 0)
        self.assertEqual(meta['total_count'], 0)
        

    def test_no_status_provided(self):
        """ Non-authoring user can only see objects with a published status """
        
        diff_user, diff_user_api_key = self.add_user(email='dave@dave.com', first_name='dave', last_name='david')
        diff_headers = self.build_headers(diff_user, diff_user_api_key)
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('project'), **diff_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(len(objects), 2)
        self.assertEqual(meta['total_count'], 2)

#@utils.override_settings(DEBUG=True)
class Test_POST_Project_API(Test_Authentication_Base):

    def setUp(self):
        
        # Add a user and gain access to the API key and user
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        self.user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)
        
        user_id2, api_key2 = self.add_user(email='dave@dave.com', first_name='dave', last_name='david')
        self.headers2 = self.build_headers(user_id2, api_key2)
        
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

        doc = {"title": "The first project.",
               "description": "First project description in here.",
               "created" : "2013-01-01T00:00:00",
               "protective_marking" : self.pm,
               "status":"published",
               "related_ideas": []
               }
        
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 201)

        response = self.c.get(self.resourceListURI('project'), **self.headers)
        meta = json.loads(response.content)['meta']
        objects = json.loads(response.content)['objects']
        
        # Top level checks
        self.assertEquals(meta['total_count'], 1)
        self.assertEquals(len(objects), 1)
        
    def test_POST_simple_usercheck(self):
        """ Test that created and user get automatically added"""
        
        doc = {"title": "The project.",
               "description": "Project description in here.",
               "status":"published",
               "protective_marking" : self.pm,
               "related_ideas":[]}
        
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 201)

        response = self.c.get(self.resourceListURI('project'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        
        # Field checks
        self.assertTrue(datetime.datetime.strptime(objects[0]['created'], '%Y-%m-%dT%H:%M:%S.%f') < datetime.datetime.utcnow())
        self.assertEquals(objects[0]['user'], self.user.username)

        
    def test_PUT_simple(self):

        # POST a document
        doc = {"title": "The first project.",
               "description": "First project description in here.",
               "status":"published",
               "protective_marking" : self.pm,
               "related_ideas":[]
               }
        
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 201)
        project1_url = response['location']
        
        # PUT another document using the 
        new_title = {"title":"the first project, much improved.",
                     "status":"published",
                     "protective_marking" : self.pm
                     }
        response = self.c.put(project1_url, json.dumps(new_title), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 204)

    def test_POST_add_comments(self):

        # POST a document
        doc = {"title": "The first project.",
               "description": "First project description in here.",
               "created" : "2013-01-01T00:00:00",
               "protective_marking" : self.pm,
               "status" : "published",
               "related_ideas":[]}
        
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 201)
        
        # Check it's there and there is 1 comment 
        main_project = response['location']
        
        # Now check its there via URL
        # Without the trailing slash results in 301 status_code
        comments_uri = self.fullURItoAbsoluteURI(main_project) + 'comments/'
        comment_1 = comments_uri + '100/'
        response = self.c.get(comment_1, **self.headers)
        self.assertEquals(response.status_code, 404)
        
        # Try adding a new comment
        new_comment = {"body"   : "perhaps we could extend that project by...",
                       "title"  : "and what about adding to that project with...",
                       "protective_marking" : self.pm}
        
        resp = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
        new_comment_uri = resp['location']
        
        # Now make sure there are 3 comments
        response = self.c.get(comments_uri, **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['total_count'], 1)
        self.assertEquals(objects[0]['user'], self.user.username)


    def test_POST_add_comment_to_unpublished_project(self):
        """ Comments are only permitted against projects with status=published
            This checks that a comment will fail where status=draft"""

        # POST a document
        doc = {"title": "The first project.",
               "description": "First project description in here.",
               "created" : "2013-01-01T00:00:00",
               "protective_marking" : self.pm,
               "status" : "draft",
               "related_ideas":[]}
        
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEqual(response.status_code, 201)
        
        # Check it's there and there is 1 comment 
        main_project = response['location']
        
        # Now check its there via URL
        # Without the trailing slash results in 301 status_code
        comments_uri = self.fullURItoAbsoluteURI(main_project) + 'comments/'
        comment_1 = comments_uri + '100/'
        response = self.c.get(comment_1, **self.headers)
        self.assertEquals(response.status_code, 404)
        
        # Try adding a new comment
        new_comment = {"body"   : "perhaps we could extend that project by...",
                       "title"  : "and what about adding to that project with...",
                       "protective_marking" : self.pm}
        
        resp = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers2) 
        self.assertEquals(resp.status_code, 400)
        self.assertEquals(json.loads(resp.content)['error'], 'User can only comment on projects with status=published.')
        
        
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
        
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)

    def test_get_tag_list(self):
        """ Tests retrieval of tags"""
        
        # Insert a bunch of docs with different tag combinations
        docs = [{"title": "First project.", "status":"published", "tags" : ["project", "projectworks", "physics", "rugby"]},
               {"title": "Second project.", "status":"published", "tags" : ["project", "projectworks", "physics"]},
               {"title": "Second project.", "status":"published", "tags" : ["project", "projectworks"]},
               {"title": "Third project.", "status":"published", "tags" :  ["project"]}]

        for doc in docs:
            response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
            self.assertEqual(response.status_code, 201)
        
        # Check there are 4 tags total
        response = self.c.get(self.resourceListURI('tag'), **self.headers)
        tags = json.loads(response.content)['objects']
        self.assertEquals(len(tags), 4)
        
    def test_get_tag_list_order_by_default(self):
        """ Tests retrieval of tags with an extra aggregate term for sorting."""
        
        # Insert a bunch of docs with different tag combinations
        docs = [{"title": "First project.","status":"published", "tags" : ["project", "projectworks", "physics", "rugby"]},
               {"title": "Second project.","status":"published", "tags" : ["project", "projectworks", "physics"]},
               {"title": "Second project.","status":"published", "tags" : ["project", "projectworks"]},
               {"title": "Third project.","status":"published", "tags" :  ["project"]}]

               
        for doc in docs:
            response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
            self.assertEqual(response.status_code, 201)
        
        # Check the specific ordering of the tags
        response = self.c.get(self.resourceListURI('tag'), **self.headers)
        tags = json.loads(response.content)['objects']
        self.assertEquals(tags[0]['text'], 'project')
        self.assertEquals(tags[1]['text'], 'projectworks')
        self.assertEquals(tags[2]['text'], 'physics')
        self.assertEquals(tags[3]['text'], 'rugby')

    def test_get_tag_list_status_single_filter(self):
        """ Filter which documents get read for tags based on status."""
        
        # Insert a bunch of docs with different tag combinations
        docs = [{"title": "First project.",  "status" : "draft",     "tags" : ["project", "projectworks", "physics", "rugby"]},
                {"title": "Second project.", "status" : "published", "tags" : ["project", "projectworks", "physics"]},
                {"title": "Second project.", "status" : "hidden",    "tags" : ["project", "projectworks"]},
                {"title": "Third project.",  "status" : "deleted",    "tags" :  ["project"]}]

               
        for doc in docs:
            response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
            self.assertEqual(response.status_code, 201)
        
        # Check the specific ordering of the tags
        params = '?status=hidden'
        response = self.c.get(self.resourceListURI('tag')+params, **self.headers)
        tags = json.loads(response.content)['objects']
        self.assertEquals(len(tags), 2)
        
        
    def test_get_tag_list_status_multiple_statuses(self):
        """ Filter which documents get read for tags based on status."""
        
        # Insert a bunch of docs with different tag combinations
        docs = [{"title": "First project.",  "status" : "draft",     "tags" : ["project", "projectworks", "physics", "rugby"]},
                {"title": "Second project.", "status" : "published", "tags" : ["project", "projectworks", "physics"]},
                {"title": "Second project.", "status" : "hidden",    "tags" : ["project", "projectworks"]},
                {"title": "Third project.",  "status" : "deleted",    "tags" :  ["new_project_tag"]}]
                
               
        for doc in docs:
            response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
            self.assertEqual(response.status_code, 201)
        
        resp = self.c.get(self.resourceListURI('project'))

        # Check the specific ordering of the tags
        params = '?status=hidden,deleted'
        response = self.c.get(self.resourceListURI('tag')+params, **self.headers)
        tags = json.loads(response.content)['objects']
        self.assertEquals(len(tags), 3)
        
#@utils.override_settings(DEBUG=True)
class Test_Back_Actions(Test_Authentication_Base):
    
    def setUp(self):

        # Add a user and gain access to the API key and user
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        self.user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)

        self.user_id2, self.api_key2 = self.add_user(email='dave@dave.com', first_name='dave', last_name='david')
        self.headers2 = self.build_headers(self.user_id2, self.api_key2)

        # Add a doc
        doc = {"title"          : "First project.",
               "description"    : "This is the first project in a series of good projects.",
               "status"         : "published",
               "related_ideas"  : []}
        
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.resource_uri = response['location']
        self.assertEqual(response.status_code, 201)

    def test_attempt_to_back_a_draft_project(self):
        """ Code should stop the user attempting to backing a draft project - only allowed on published."""
        
        # Change that project status to be draft via the db directly
        id = self.resource_uri.strip('/').split('/')[-1]
        doc = documents.Project.objects.get(id=id).update(**{'set__status':'draft'})
        
        # Without the trailing slash results in 301 status_code
        backs_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'backs/'
        
        # Try adding a new comment
        response = self.c.post(backs_uri, json.dumps({"comment" : {"title":"very good project. I support."}}), content_type='application/json', **self.headers2) 
        
        # Now make sure there are 3 comments
        self.assertEquals(response.status_code, 400)
    
    def test_back_a_project_catch_single_user(self):
        """ As the same user, attempt to back a project twice
            and fail to do so. Resultant back array remains 1 long."""
        
        # Without the trailing slash results in 301 status_code
        backing_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'backs/'
        
        # Try adding a new comment
        # No user provided - picked up automatically
        new_backings = [{"comment" : {"title":"very good project. I support."}},
                        {"comment" : {"title": "ditto - great project."}}]
        for back in new_backings:
            self.c.post(backing_uri, json.dumps(back), content_type='application/json', **self.headers2) 
        
        # Now make sure there are 3 comments
        response = self.c.get(backing_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(len(content), 1)
        self.assertEquals(content[0]['user'], self.user_id2.username)
        
        # Make sure the back count is correct
        response = self.c.get(self.resource_uri, **self.headers)
        self.assertEquals(json.loads(response.content)['objects'][0]['back_count'], 1)

    def test_back_a_project_2_users(self):
        """ userA backs an project. UserA tries to back it again - it should fail.
            userB backs an project and it registers. """

        # Add a 3rd user (now 1 staff, 2 users)        
        user_id3, api_key3 = self.add_user(email='sue@dave.com', first_name='sue', last_name='mcgrew')
        self.headers3 = self.build_headers(user_id3, api_key3)
        
        # Without the trailing slash results in 301 status_code
        back_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'backs/'
        
        # Try adding a new comment
        # No user provided - picked up automatically
        # Only 2 of these should go in because user 1 can't back something twice
        self.c.post(back_uri, json.dumps({"comment":{"title":"cool"}}), content_type='application/json', **self.headers2) 
        self.c.post(back_uri, json.dumps({"comment":{"title":"fun"}}), content_type='application/json', **self.headers2) 
        self.c.post(back_uri, json.dumps({"comment":{"title":"nice"}}), content_type='application/json', **self.headers3) 
        
        # Now make sure there are 2 backs with different users
        response = self.c.get(back_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(len(content), 2)
        
        self.assertEquals(content[0]['user'], self.user_id2.username)
        self.assertEquals(content[1]['user'], user_id3.username)
        
        # Make sure the back count is correct
        response = self.c.get(self.resource_uri, **self.headers)
        self.assertEquals(json.loads(response.content)['objects'][0]['back_count'], 2)
    
    def test_user_backs_project_and_then_revokes_by_delete(self):
        """ userA backS an project. UserA tries to back it instead - it should SUCCEED. """
        
        # back
        back_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'backs/'
        self.c.post(back_uri, json.dumps({"comment":{"title":"cool"}}), content_type='application/json', **self.headers) 
        
        # Check it registered
        response = self.c.get(back_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(len(content), 1)
        back_exact_uri = content[0]['resource_uri']
        
        # Delete the backing
        response = self.c.delete(back_exact_uri, **self.headers)
        self.assertEquals(response.status_code, 204)
        
        # Make sure it got dropped
        response = self.c.get(back_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(len(content), 0)

    def test_back_comment_stored_in_comments_model(self):
        """ Check that a Back comment gets stored in the comments model, not as a vote subdoc """
                
        # Without the trailing slash results in 301 status_code
        backs_uri    = self.fullURItoAbsoluteURI(self.resource_uri) + 'backs/'
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
        
        # Try adding a new backing with comment
        self.c.post(backs_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
        
        # Now make sure there are 2 backs with different users
        response = self.c.get(comments_uri, **self.headers)
        content = json.loads(response.content)['objects']
        self.assertEquals(content[0]['user'], self.user.username)
        
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **self.headers)

        # ['objects'][0] - because detail level has a meta object
        doc = json.loads(response.content)['objects'][0]
        self.assertEquals(len(doc['comments']), 1)
        self.assertEquals(doc['comment_count'], 1)
        self.assertEquals(doc['comments'][0]['type'], 'back')
        
        self.assertEquals(len(doc['backs']), 1)
        self.assertEquals(doc['back_count'], 1)

    def test_attempted_back_spoof_fake_user(self):
        """ Mimics someone attemtpting to increment back by submitting a fake user """
        
        # The user that is recorded in the db isn't fake_back@xyz.com
        
        backs_uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'backs/'
        fake_data = {'user':'fake_back@xyz.com'}
        self.c.post(backs_uri, json.dumps(fake_data), content_type='application/json', **self.headers) 
        
        # Now make sure there are 2 backs with different users
        response = self.c.get(backs_uri, **self.headers)
        self.assertEquals(json.loads(response.content)['objects'][0]['user'], self.user.username)

    def test_get_user_vote_status_back(self):
        """ Check that the API returns the user_backed field """
        
        uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'backs/'
        self.c.post(uri, json.dumps({}), content_type='application/json', **self.headers) 
        
        # Check the user vote is the correct value
        response = self.c.get(self.resource_uri, **self.headers)
        self.assertEquals(json.loads(response.content)['objects'][0]['user_backed'], 1)
        
    def test_get_user_vote_status_not_backed(self):
        """ Check that the API returns the user_backed field """
        
        # Check the user vote is the correct value
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **self.headers)
        self.assertEquals(json.loads(response.content)['objects'][0]['user_backed'], 0)
    
    def test_user_vote_issue45_case1(self):
        """ 
            Re-creating this action on the front-end
            -----------------------------------------
            UserA logs in - not actually required in the tests (API auth)
            UserA votes on (backs) project_001
            Check user_voted for project_001 - should be +1
            UserA logs out
            
            UserB logs in - not actually required in the tests (API auth)
            UserB opens project_001
            Check user_voted for project_001 - should be 0
            UserB votes on (backs) project_001
            Check user_voted for project_001 - should be -1
        """
        
        # Create UserA
        userA, userA_api_key = self.add_user(email="a@a.com", first_name="a", last_name="user_a")
        userA_headers = self.build_headers(userA, userA_api_key)
        
        # UserA backs an project
        uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'backs/'
        x = self.c.post(uri, json.dumps({}), content_type='application/json', **userA_headers) 
        
        # Check the user_backed is correct
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **userA_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['user_backed'], 1)
        
        # Create UserB
        userB, userB_api_key = self.add_user(email="b@b.com", first_name="b", last_name="user_b")
        userB_headers = self.build_headers(userB, userB_api_key)

        # UserB shouldn't have a user_vote yet
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **userB_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['user_backed'], 0)
        
        # UserB backs something
        uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'backs/'
        x = self.c.post(uri, json.dumps({}), content_type='application/json', **userB_headers) 

        # UserB now has a user_vote of -1
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **userB_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['user_backed'], 1)
        
        
        
    def test_user_vote_issue45_case2(self):
        """ UserA logs in
            UserA votes on (backs) project_001
            Check user_voted for project_001 - should be +1
            UserA logs out
            
            Anonymous opens project_001
            Check user_voted for project_001 - should be 0
            
            UserB logs in - not actually required in the tests (API auth)
            UserB opens project_001
            Check user_voted for project_001 - should be 0
            UserB votes on (backs) project_001
            Check user_voted for project_001 - should be -1

        """
        
        # Create UserA
        userA, userA_api_key = self.add_user(email="a@a.com", first_name="a", last_name="user_a")
        userA_headers = self.build_headers(userA, userA_api_key)
        
        # UserA backs an project
        uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'backs/'
        x = self.c.post(uri, json.dumps({}), content_type='application/json', **userA_headers) 
        
        # Check the user_backed is correct
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **userA_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['user_backed'], 1)
        
        # AnonymousUser shouldn't have a user_backed yet
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['user_backed'], 0)
        
        # And now UserB just to be sure...
        userB, userB_api_key = self.add_user(email="b@b.com", first_name="b", last_name="user_b")
        userB_headers = self.build_headers(userB, userB_api_key)

        # UserB shouldn't have a user_vote yet
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **userB_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['user_backed'], 0)
        
        # UserB backs something
        uri = self.fullURItoAbsoluteURI(self.resource_uri) + 'backs/'
        x = self.c.post(uri, json.dumps({}), content_type='application/json', **userB_headers) 

        # UserB now has a user_vote of 0
        response = self.c.get(self.fullURItoAbsoluteURI(self.resource_uri), **userB_headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['user_backed'], 1)

        
    #===============================================================================
    # DIFFERENT WAYS OF QUERYING THE COMMENTS API - by user? by title?
    #===============================================================================

    #===============================================================================
    #TODO: Check that a null classification can be posted- for when we drop that.
    #===============================================================================


#@utils.override_settings(DEBUG=True)
class Test_Project_Sorting(Test_Authentication_Base):

    def setUp(self):
        """ Add in some documents"""

        # Add a user and gain access to the API key and user
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        self.user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)

        self.doc_ids = []

        # Insert 10 docs with different months
        for i in range(10):
            doc = {"title": "Project #%s"%(i), "status":"published", "description": "First project description in here."}
            response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
            if response.status_code == 201:
                self.doc_ids.append(response['location'])

        # Check they went in OK
        content = json.loads(self.c.get(self.resourceListURI('project'), **self.headers).content)
        self.assertEquals(len(content['objects']), 10)
    
    
    def test_doc_asc_created_sort(self):
        """Sort results by date in asc order """
        
        response = self.c.get('/api/v1/project/?order_by=created', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        for i in range(1, len(objects)):
            this = datetime.datetime.strptime(objects[i]['created'], '%Y-%m-%dT%H:%M:%S.%f')
            prev = datetime.datetime.strptime(objects[i-1]['created'], '%Y-%m-%dT%H:%M:%S.%f')
            self.assertTrue(prev < this)

    def test_doc_desc_created_sort(self):
        """ Sort results by date in descending order. """

        response = self.c.get('/api/v1/project/?order_by=-created', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        for i in range(1, len(objects)):
            this = datetime.datetime.strptime(objects[i]['created'], '%Y-%m-%dT%H:%M:%S.%f')
            prev = datetime.datetime.strptime(objects[i-1]['created'], '%Y-%m-%dT%H:%M:%S.%f')
            self.assertTrue(prev > this)
    
    def test_doc_back_count_sort_desc(self):
        """ Sort results by back count in descending order. """

        # Add some backs
        for i in range(len(self.doc_ids)-1):
            backs_uri = self.fullURItoAbsoluteURI(self.doc_ids[i]) + 'backs/'
            
            # Add a different number of backs for each project
            x = i + 1
            
            for j in range(1, x+2):
                # Add a different user each time
                user_id, api_key = self.add_user(email='%s@blah.com'%(j))
                headers = self.build_headers(user_id, api_key)
                
                try:
                    resp = self.c.post(backs_uri, json.dumps({'comment':{"title":'cool %s'%(j)}}), content_type='application/json', **headers) 
                except Exception, e:
                    print e
                                
        response = self.c.get('/api/v1/project/?order_by=back_count', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        
        for x in range(len(objects)-1):
            this_back_count = objects[x]['back_count']
            next_back_count = objects[x+1]['back_count']
            if this_back_count and next_back_count:
                self.assertGreater(next_back_count, this_back_count)
                
    ## MORE TESTS FOR DIFFERENT SORT FIELDS ##    

#@utils.override_settings(DEBUG=True)
class Test_Check_Modified(Test_Authentication_Base):

    def setUp(self):
        """ Add in some documents"""

        # Add a user and gain access to the API key and user
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)
        number_projects = 3
        
        # Insert 10 docs with different months
        for i in range(number_projects):
            doc = {"title": "Project #%s"%(i), "description": "First project description in here.", "status": "published"}
            #resp = self.c.get(self.resourceListURI('project'), **self.headers)
            response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
            main_project = response['location']
            self.assertEquals(response.status_code, 201)
            
            comments_uri = self.fullURItoAbsoluteURI(main_project) + 'comments/'
            
            # Try adding new comments
            for j in range (3):
                new_comment = {"user"   : "rich@rich.com",
                               "body"   : "#%s perhaps we could extend that project by..."%(j),
                               "title"  : "and what about adding to that project with %s..."%(j),
                               "protective_marking" : {"classification":"unclassified","descriptor":""}}
                resp = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
                self.assertEquals(resp.status_code, 201)
                
        # Wait to ensure we have a different time
        time.sleep(0.5)

        # Check they went in OK
        content = json.loads(self.c.get(self.resourceListURI('project'), **self.headers).content)
        self.assertEquals(len(content['objects']), number_projects)
        
    def retrieve_most_recent_timestamp(self, objects):
        """Gets the most recent timestamp"""
        
        dates = []
        for obj in objects:
            dates += [datetime.datetime.strptime(obj['created'], '%Y-%m-%dT%H:%M:%S.%f'), datetime.datetime.strptime(obj['modified'], '%Y-%m-%dT%H:%M:%S.%f')]
        return max(dates)
    
    def test_update_project_modified_ts_field_on_POST(self):
        """ Checks that the Project API updates the modified timestamp field when part of the project is changed"""
        
        # Get all data
        content = json.loads(self.c.get(self.resourceListURI('project'), **self.headers).content)
        project_0 = content['objects'][0]
        old_title = project_0['title']
        old_ts = project_0['modified']
        
        # Patch a new title - partial addition which leaves the rest in place correctly.
        new_title = {"title":"this is a major change to the title because it was offensive..."}
        response = self.c.patch(self.fullURItoAbsoluteURI(project_0['resource_uri']), json.dumps(new_title), content_type='application/json', **self.headers)
        content = json.loads(self.c.get(self.resourceListURI('project'), **self.headers).content)
        
        # Retrieve the last project in the set now because it's been moved
        project_0 = content['objects'][0]
        new_stored_title = project_0['title']

        # Check its not the same as the previous one and is the intended new one        
        self.assertNotEqual(old_title, new_stored_title)
        self.assertEqual(new_title['title'], new_stored_title)
        
        # Check the timestamps
        new_ts = project_0['modified']
        self.assertGreater(new_ts, old_ts)

    def test_update_project_modified_ts_field_on_POST_to_comment(self):
        """ Checks that the Project API updates the modified timestamp field when part of the project is changed.
            Mods to the comments/backs will change the overall objects modified date."""
        
        # Get all data
        content = json.loads(self.c.get(self.resourceListURI('project'), **self.headers).content)
        project_x = content['objects'][-1]
        project_old_ts = project_x['modified']
        first_comment = project_x['comments'][0]
        
        # Patch a new title - partial addition which leaves the rest in place correctly.
        new_comment_title = {"title":"this is a major change to the title because it was offensive..."}
        response = self.c.patch(first_comment['resource_uri'], json.dumps(new_comment_title), content_type='application/json', **self.headers)
        time.sleep(1)
        
        # After a short sleep, get the projects again
        content = json.loads(self.c.get(self.resourceListURI('project'), **self.headers).content)
        project_x = content['objects'][-1]
        
        # Get the modified time for the Project
        project_new_ts = project_x['modified']
        
        # Get the first comment again
        new_first_comment = project_x['comments'][0]
        
        # Check that the new first comment title is what we tried to change it to
        self.assertEqual(new_first_comment['title'], new_comment_title['title'])
        
        # Check that the project modified ts has changes.
        self.assertGreater(project_new_ts, project_old_ts)


    def test_check_project_modified_is_correct(self):
        """Checks that the project level modified is correct """

        response = self.c.get('/api/v1/project/', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        for project in objects:
            most_recent_comment = self.retrieve_most_recent_timestamp(project['comments'])
            self.assertEquals(most_recent_comment.strftime('%Y-%m-%dT%H:%M:%S'),
                              datetime.datetime.strptime(project['modified'], '%Y-%m-%dT%H:%M:%S.%f').strftime('%Y-%m-%dT%H:%M:%S'))

    def test_check_meta_modified_is_correct(self):
        """Checks that the meta-level modified is correct """
        
        response = self.c.get('/api/v1/project/', **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        most_recent_project = self.retrieve_most_recent_timestamp(objects)
        most_recent_comment = datetime.datetime.utcnow() - datetime.timedelta(days=1000)
        for project in objects:
            most_recent_comment = max([self.retrieve_most_recent_timestamp(project['comments']), most_recent_comment])
        most_recent = max([most_recent_project, most_recent_comment])
        
        self.assertEquals(most_recent, datetime.datetime.strptime(meta['modified'], '%Y-%m-%dT%H:%M:%S.%f'))

    def test_update_project_tag_count(self):
        """ Check that the tag count changes if its edited."""
        
        # Get all data
        content = json.loads(self.c.get(self.resourceListURI('project'), **self.headers).content)
        project_0 = content['objects'][0]
        old_tags = project_0['tags']
        old_tag_count = project_0['tag_count']
        self.assertEquals(old_tag_count, 0)
        
        # Patch some tags in, having forgotten them first time round
        add_tags = {"tags" : ["physics","maths","geography","sports","english"]}
        response = self.c.patch(self.fullURItoAbsoluteURI(project_0['resource_uri']), json.dumps(add_tags), content_type='application/json', **self.headers)
        content = json.loads(self.c.get(self.resourceListURI('project'), **self.headers).content)
        
        # Retrieve the project
        project_0 = content['objects'][0]
        new_tags = project_0['tags']
        new_tag_count = project_0['tag_count']

        # Check its not the same as the previous one and is the intended new one        
        self.assertNotEqual(old_tags, new_tags)
        self.assertEqual(new_tag_count, 5)
        
#@utils.override_settings(DEBUG=True)
class Test_Data_Level_Responses(Test_Authentication_Base):

    def setUp(self):
        """ Add in some documents"""

        # Add a user and gain access to the API key and user
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)
        
        # Insert 10 docs with different months
        for i in range(3):
            doc = {"title": "Project #%s"%(i),"status":"published", "description": "First project description in here."}
            # Just to check its there?
            response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
            main_project = response['location']
            
            comments_uri = self.fullURItoAbsoluteURI(main_project) + 'comments/'
            # Try adding new comments
            for j in range (5):
                new_comment = {"user"   : "rich@rich.com",
                               "body"   : "#%s perhaps we could extend that project by..."%(j),
                               "title"  : "and what about adding to that project with %s..."%(j),
                               "protective_marking" : {"classification":"unclassified","descriptor":""}}
                # Just to check its there?
                self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
            
            backs_uri = self.fullURItoAbsoluteURI(main_project) + 'backs/'
            new_backs = {"user" : "dave@dave.com",
                           "comment" : {"title":"this is one of the worst projects ever - someone else tried this and it failed."}}
            response = self.c.post(backs_uri, json.dumps(new_backs), content_type='application/json', **self.headers)         
            
        # Check they went in OK
        content = json.loads(self.c.get(self.resourceListURI('project'), **self.headers).content)
    
    def test_response_data_test_set_list(self):
        """Check that we get back the expected set of fields"""
        
        response = self.c.get('/api/v1/project/?data_level=proj_test', **self.headers)
        meta, data = self.get_meta_and_objects(response)
        data_response_keys = data[0].keys()
        for fld in settings.RESPONSE_FIELDS['proj_test']:
            self.assertTrue(fld in data_response_keys)
        
    def test_response_data_test_set_meta(self):
        """Check that we get back the expected set of fields"""
        
        response = self.c.get('/api/v1/project/?data_level=meta', **self.headers)
        content = json.loads(response.content)
        self.assertFalse(content.has_key('data'))
        self.assertTrue(content.has_key('meta'))

    def test_response_data_check_comments_modified(self):
        """Is there a meta.modified for a /project/<id>/comments/ call?"""
        
        response = self.c.get('/api/v1/project/?data_level=meta', **self.headers)
        content = json.loads(response.content)
        self.assertTrue(content.has_key('meta'))
        self.assertTrue(content['meta']['modified'])

#@utils.override_settings(DEBUG=True)
class Test_Contributor_Naming(Test_Authentication_Base):

    def setUp(self):
        """ Add in some documents"""

        # Add a user and gain access to the API key and user
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)
        
        # We need another user for comments
        user_id2, api_key2 = self.add_user(email='dave@davison.com', first_name='dave', last_name='davidson')
        self.headers2 = self.build_headers(user_id2, api_key2)
        
        # We also need a 3rd user because of the unique constraint (applied in code logic) on backs fields
        user_id3, api_key3 = self.add_user(email='john@cleese.com', first_name='john', last_name='cleese')
        self.headers3 = self.build_headers(user_id3, api_key3)


        # Insert 10 docs with different months
        for i in range(3):
            doc = {"title": "Project #%s"%(i), "description": "First project description in here.", "status": "published"}
            # Just to check its there?
            response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
            main_project = response['location']
            
            comments_uri = self.fullURItoAbsoluteURI(main_project) + 'comments/'
            # Try adding new comments
            for j in range (5):
                new_comment = {"body"   : "#%s perhaps we could extend that project by..."%(j),
                               "title"  : "and what about adding to that project with %s..."%(j),
                               "protective_marking" : {"classification":"unclassified","descriptor":""}}
                # Just to check its there?
                self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers2) 
                    
            backs_uri = self.fullURItoAbsoluteURI(main_project) + 'backs/'
            response = self.c.post(backs_uri, json.dumps({}), content_type='application/json', **self.headers3) 
        
    def test_project_contributor_name(self):
        """ Check the project has a contribtor name """
        
        response = self.c.get(self.resourceListURI('project'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['contributor_name'], 'Bob Roberts')

    def test_comment_contributor_name(self):
        """ Check the comment has a contribtor name """
        
        response = self.c.get(self.resourceListURI('project'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['comments'][0]['contributor_name'], 'Dave Davidson')
        
    def test_backs_contributor_name(self):
        """ Check the backs has a contribtor name """
        
        response = self.c.get(self.resourceListURI('project'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['backs'][0]['contributor_name'], 'John Cleese')
                


#@utils.override_settings(DEBUG=True)
class Test_Project_With_Protective_Markings(Test_Authentication_Base):

    def setUp(self):
        """ Add in some documents"""

        # Add a user and gain access to the API key and user
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)
        
    def test_submit_full_pm(self):
        """ Submit a complete protective marking """
        
        doc = {"title": "Project #1",
               "description": "First project description in here.",
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
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        response = self.c.get(self.resourceListURI('project'))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['protective_marking']['classification'], 'PUBLIC')        
        self.assertEquals(objects[0]['protective_marking']['pretty_pm'], 'PUBLIC [PRIVATE] BANANA 1/BANANA 2 ME ONLY')
        
        # Check that it also comes out in the project-level content
        self.assertEquals(objects[0]['pretty_pm'], 'PUBLIC [PRIVATE] BANANA 1/BANANA 2 ME ONLY')
        
        
    def test_submit_classification(self):
        """ Submit a classification """
        
        doc = {"title": "Project #1",
               "description": "First project description in here.",
               "status": "published",
               "protective_marking" : {"classification" : "PUBLIC",
                                       "classification_short" : "PU",
                                       "classification_rank" : 0,
                                       }
               }
        
        # Just to check its there?
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        response = self.c.get(self.resourceListURI('project'))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['protective_marking']['classification'], 'PUBLIC')
        self.assertEquals(objects[0]['protective_marking']['pretty_pm'], 'PUBLIC')
        
        
    def test_submit_national_caveats(self):
        """ Submit a national caveat """

        doc = {"title": "Project #1",
               "description": "First project description in here.",
               "status":"published",
               "protective_marking" : {"national_caveats_primary_name" : 'ME ONLY',
                                       "national_caveats_members" : ['1', '2', '3'],
                                       }
               }

        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        response = self.c.get(self.resourceListURI('project'))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['protective_marking']['national_caveats_primary_name'], 'ME ONLY')
        self.assertEquals(objects[0]['protective_marking']['national_caveats_members'], ['1','2','3'])
        self.assertEquals(objects[0]['protective_marking']['pretty_pm'], 'CLASSIFICATION NOT KNOWN ME ONLY')
        

    def test_submit_codewords(self):
        """ Submit a codeword """

        doc = {"title": "Project #1",
               "description": "First project description in here.",
               "status":"published",
               "protective_marking" : {"codewords" : ['BANANA 1', 'BANANA 2'],
                                       "codewords_short" : ['B1', 'B2']}
               }

        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        response = self.c.get(self.resourceListURI('project'))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['protective_marking']['codewords'], ['BANANA 1', 'BANANA 2'])
        self.assertEquals(objects[0]['protective_marking']['codewords_short'], ['B1', 'B2'])
        self.assertEquals(objects[0]['protective_marking']['pretty_pm'], 'CLASSIFICATION NOT KNOWN BANANA 1/BANANA 2')

    def test_submit_descriptors(self):
        """ Submit descriptors """

        doc = {"title": "Project #1",
               "description": "First project description in here.",
               "status":"published",
               "protective_marking" : {"descriptor" : 'PRIVATE'}
               }

        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        response = self.c.get(self.resourceListURI('project'))
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
    #             doc = documents.Project(title ='new project', protective_marking = new_pm)
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
    #             comments = [documents.Comment(title='new comment', body='great project', protective_marking=new_pm) for i in range(3)]
    #             
    #             # Create the document
    #             doc = documents.Project(title ='new project',
    #                                  comments=comments,
    #                                  protective_marking=new_pm)
    #             docs.append(doc)
    # 
    #         pm_list = api.get_all_pms(docs)
    #         
    #         self.assertEquals(len(pm_list), 16)
    #         
    #===============================================================================

    def test_get_max_pm_inject_O(self):
        """Retrieves the max pm"""

        pm_list = []
        for i in range(3):
            pm = copy.deepcopy(self.pm)
            pm_list.append(pm)
            
        max_pm = api.get_max_pm(pm_list)
        self.assertEquals(max_pm['classification'], 'PUBLIC')


    def test_get_max_pm_inject_S(self):
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

    def test_get_max_pm_inject_TS(self):
        """Retrieves the max pm"""

        pm_list = []
        for i in range(3):
            pm = copy.deepcopy(self.pm)
            pm_list.append(pm)

        pm_list[0]['classification']='PRIVATE'
        pm_list[0]['classification_short']='PR'
        pm_list[0]['classification_rank']=2
        
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
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)
        
        # We need another user for comments
        user_id2, api_key2 = self.add_user(email='dave@davison.com', first_name='dave', last_name='davidson')
        self.headers2 = self.build_headers(user_id2, api_key2)
        
        # We also need a 3rd user because of the unique constraint (applied in code logic) on backs fields
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


    def test_just_project_level_O(self):
        """ just pms in the projects - all at O to overcome a bug where PUBLIC wasn't rendering a max pm."""

        doc = {"title": "Project #1",
               "description": "First project description in here.",
               "status":"published",
               'protective_marking' : self.pm}
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        response = self.c.get(self.resourceListURI('project'))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['max_pm']['classification'], 'PUBLIC')


    def test_just_project_level(self):
        """ just pms in the projects """

        # Insert a couple of documents
        doc = {"title": "Project #1", "description": "First project description in here.", 'protective_marking' : self.pm, "status":"published"}
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        doc = {"title": "Project #2", "description": "First project description in here.", 'protective_marking' : self.pm, "status":"published"}
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        
        # Bump the classification on the final one
        doc['protective_marking']['classification'] = 'PRIVATE'
        doc['protective_marking']['classification_short'] = 'PR'
        doc['protective_marking']['classification_rank'] = 2
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)

        response = self.c.get(self.resourceListURI('project'))
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(meta['max_pm']['classification'], 'PRIVATE')

    def test_include_embedded_level(self):
        """ PMs inside the embedded level too """

        # Insert a couple of documents
        doc = {"title": "Project #1", "description": "First project description in here.", 'protective_marking' : self.pm, "status": "published"}
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        doc = {"title": "Project #2", "description": "First project description in here.", 'protective_marking' : self.pm, "status": "published"}
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        
        # Bump the classification on the final one
        doc['protective_marking']['classification'] = 'PRIVATE'
        doc['protective_marking']['classification_short'] = 'PR'
        doc['protective_marking']['classification_rank'] = 2
        response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)

        response = self.c.get(self.resourceListURI('project'))
        meta, objects = self.get_meta_and_objects(response)
        comments_uri = objects[0]['resource_uri'] + 'comments/'
        
        pm = copy.deepcopy(self.pm)
        pm['classification'] = 'PERSONAL'
        pm['classification_short'] = 'PE'
        pm['classification_rank'] = 3
        
        new_comment = {"body"   : "perhaps we could extend that project by...",
                       "title"  : "and what about adding to that project with...",
                       "protective_marking" : pm}
        
        # Just to check its there?
        response = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers2) 
        check = response['location']
        response = self.c.get(check)
        
        response = self.c.get(self.resourceListURI('project'))
        
        meta, objects = self.get_meta_and_objects(response)
        #print json.dumps(objects, indent=3)
        
        self.assertEquals(meta['max_pm']['classification'], 'PERSONAL')


#----------------------------------------------------------------------------------------

#@utils.override_settings(DEBUG=True)
class Test_Deletes(Test_Authentication_Base):

    def setUp(self):

        # Add a user and gain access to the API key and user
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)
        
        
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
        docs = [{"title": "The first project.",
                 "description": "First project description in here.",
                 "tags" : ["physics","maths","geography","sports","english"],
                 "protective_marking":self.pm, 
                 "status" : "published"},
                
                {"title": "The second project.",
                 "description": "second project description in here.",
                 "tags" : ["physics","maths","geography","sports"],
                 "protective_marking":self.pm,
                 "status" : "published"}]
        
        # Store the responses
        self.doc_locations = []
        x = 0
        for doc in docs:
            response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)

            project_url = response['location']
            comments_uri = project_url + 'comments/'
            new_comment = {"body"   : "perhaps we could extend that project by...",
                            "title"  : "and what about adding to that project with...",
                            "protective_marking" : self.pm}
            for i in range(x):
                comment_resp = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
                
            x += 1
            
            time.sleep(1)
            
        response = self.c.get(self.resourceListURI('project')+'?data_level=less', **self.headers)
        #for x in json.loads(response.content)['objects']:
        #    print json.dumps(x, indent=4)

    def test_delete_comment_decrement_count(self):
        """ Delete a comment from an project and check the comment_count reduces """                 
        
        # Get the id for the project
        response = self.c.get(self.resourceListURI('project'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        project1_id = objects[1]['id']
        
        # Count the comments
        resp = self.c.get(self.resourceDetailURI('project', project1_id), **self.headers)
        meta, objects = self.get_meta_and_objects(resp)
        self.assertEquals(objects[0]['comment_count'], 1)
        
        # Delete the comment
        path = self.resourceListURI('project')+'%s/comments/0/'%(project1_id)
        resp = self.c.delete(path, content_type='application/json', **self.headers)
        
        response = self.c.get(self.resourceDetailURI('project', project1_id), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['comment_count'], 0)

    def test_delete_when_multiple_comments(self):
        """ Create a comment - done in setup
            Create another comment - done here
            Attempt to delete a comment by specific URI
        """
        
        # Get the project id
        response = self.c.get(self.resourceListURI('project'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        project1_id = objects[1]['id']
        
        # Build the comments URI
        comments_uri = self.resourceDetailURI('project', project1_id)+'comments/'

        # Post a new comment
        new_comment = {"body"   : "perhaps we could extend that project by...",
                       "title"  : "and what about adding to that project with...",
                       "protective_marking" : self.pm}
        
        comment_resp = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 

        # Check there are now 2 comments
        response = self.c.get(self.resourceDetailURI('project', project1_id), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['comment_count'], 2)
        self.assertEquals(len(objects[0]['comments']), 2)

        # Delete the first comment
        delete_uri = comments_uri + '0/'
        resp = self.c.delete(delete_uri, content_type='application/json', **self.headers)
        self.assertEquals(resp.status_code, 204)
        
        # Now check that it definitely got deleted
        response = self.c.get(self.resourceDetailURI('project', project1_id), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        self.assertEquals(objects[0]['comment_count'], 1)
        self.assertEquals(len(objects[0]['comments']), 1)


#@utils.override_settings(DEBUG=True)
class Test_Get_Non_Standard_Fields(Test_Authentication_Base):

    def setUp(self):

        # Add a user and gain access to the API key and user
        self.user_id, self.api_key = self.add_user("staff_user1@projects.com")
        user = self.give_privileges(self.user_id, priv='staff')
        self.headers = self.build_headers(self.user_id, self.api_key)
        
        
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
        docs = [{"title": "The first project.",
                 "description": '<a href="http://www.example.com">First</a> project <b>description</b> in here.',
                 "tags" : ["physics","maths","geography","sports","english"],
                 "protective_marking":self.pm, 
                 "status" : "published"},
                
                {"title": "The second project.",
                 "description": "<h2>second</h2> project <b>description</b> in here." + " The quick brown fox jumped over the lazy dog."*10,
                 "tags" : ["physics","maths","geography","sports"],
                 "protective_marking":self.pm,
                 "status" : "published"}
                 ]
        
        # Store the responses
        self.doc_locations = []
        x = 0
        for doc in docs:
            response = self.c.post(self.resourceListURI('project'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)

            project_url = response['location']

            comments_uri = project_url + 'comments/'
            new_comment = {"body"   : "perhaps we could <b> extend </b> that project by...",
                            "title"  : "and what about adding to that project with...",
                            "protective_marking" : self.pm}
            for i in range(x):
                comment_resp = self.c.post(comments_uri, json.dumps(new_comment), content_type='application/json', **self.headers) 
                
            x += 1
            
            time.sleep(1)
            
    def test_check_description_snippet(self):
        """ Checks we get back a snippet of the description from html """
        
        # Retrieve all results
        response = self.c.get(self.resourceListURI('project'), **self.headers)
        meta, objects = self.get_meta_and_objects(response)
        
        #First doc - short
        self.assertEquals(objects[0]['description_snippet'], 'First project description in here.')
        self.assertEquals(objects[1]['description_snippet'], 'second project description in here. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox jumped over the lazy dog. The quick brown fox...')
        

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

    def test_merge_tag_results(self):
        """ Check that 2 lists of dicts get merged correctly - exact match """
        
        project_tags = [{"_id":"hello", "count":1},
                     {"_id":"world", "count":2},
                     {"_id":"again", "count":3}]
        
        proj_tags = [{"_id":"hello", "count":1},
                     {"_id":"world", "count":2},
                     {"_id":"again", "count":3}]
        
        truth = [{"_id":"hello", "count":2},
                 {"_id":"world", "count":4},
                 {"_id":"again", "count":6}]
        
        res = api_functions.merge_tag_results(proj_tags, project_tags)
        
        truth_dict = {}
        res_dict = {}

        # This works for 2.6 and 2.7, which trhe previous version of code didn't (only 2.7).        
        for tag in truth:
            truth_dict[tag['_id']] = tag['count']
            
        for tag in res:
            res_dict[tag['_id']] = tag['count']
        
        for key in truth_dict.keys():
            self.assertEquals(truth_dict[key], res_dict[key])
        
    def test_merge_tag_results_gaps(self):
        """ Check that 2 lists of dicts get merged correctly - gaps in 1 """

        project_tags = [{"_id":"hello", "count":1},
                     {"_id":"world", "count":2},
                     {"_id":"again", "count":3}]
        
        proj_tags = [{"_id":"hello", "count":1},
                     {"_id":"again", "count":3}]
        
        truth = [{"_id":"again", "count":6},
                 {"_id":"hello", "count":2},
                 {"_id":"world", "count":2}]
        
        res = api_functions.merge_tag_results(proj_tags, project_tags)
        self.assertEquals(truth, res)
        
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
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        