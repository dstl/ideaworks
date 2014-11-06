
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

"""
Tests relating to RSS fed idea content
"""
import time
import json
import urlparse
import datetime
from xml.dom.minidom import parseString

from django.core import urlresolvers
from django.test import client
from django.conf import settings
from django.core.urlresolvers import reverse
from django.contrib.auth.models import User

from registration.models import RegistrationProfile
from tastypie_mongoengine import test_runner

from ideasapp import documents
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
    
#@utils.override_settings(DEBUG=True)
class Test_Idea_RSS_Format(Test_Authentication_Base):

    """ Basic checks against formats and counts"""


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
                 "protective_marking" : self.pm },
                
                {"title": "The third idea.",
                 "description": "Third idea description in here.",
                 "status":"published",
                 "protective_marking" : self.pm },
                
                {"title": "The forth idea.",
                 "description": "Forth idea description in here.",
                 "status":"published",
                 "protective_marking" : self.pm }
                ]
        
        # Store the responses
        self.doc_locations = []
        for doc in docs:
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)
            

    def test_get_all_ideas(self):
        """ Retrieve all ideas """
        
        response = self.c.get(self.resourceListURI('idea') + "?format=rss", **self.headers)
        self.assertEquals(response.status_code, 200)

    def test_check_feed_title(self):
        """ Check that the title is correct """
        
        response = self.c.get(self.resourceListURI('idea') + "?format=rss", **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(feed['title'], settings.END_POINT_DESCRIPTIONS['idea'])
    
    def test_check_feed_title_filtered(self):
        """ Check that the title is correct - with (filtered) """
        
        response = self.c.get(self.resourceListURI('idea') + "?format=rss&test=blah", **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(feed['title'], settings.END_POINT_DESCRIPTIONS['idea']+' (filtered)')

    def test_check_feed_title_filtered_by_single_tag(self):
        """ Filter by single tag"""

        params =  "?format=rss" + "&tags=one"
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(feed['title'], settings.END_POINT_DESCRIPTIONS['idea']+' (Tags:one)')
        
    
    def test_check_feed_title_filtered_by_tags(self):
        """ Filter by multiple tags"""

        params =  "?format=rss" + "&tags__in=one,two"
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(feed['title'], settings.END_POINT_DESCRIPTIONS['idea']+' (Tags:one,two)')
        
  
    def test_check_feed_updated(self):
        """ Check that the updated is correct """
        
        # Get all the documents from the db directly
        docs = documents.Idea.objects.all()
        latest = datetime.datetime(year=1970, month=1, day=1)
        for doc in docs:
            if doc.created > latest:
                latest = doc.created
            if doc.modified > latest:
                latest = doc.modified
        
        # Adjust latest for difference in system clock
        #FIXME: Why is the feed pulling in system time and not zulu?
        #latest += datetime.timedelta(seconds=3600)
        
        response = self.c.get(self.resourceListURI('idea') + "?format=rss", **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(feed['updated'], latest.strftime('%Y-%m-%dT%H:%M:%SZ'))
    
    def test_feed_count_entries(self):
        """ Check the number of entries is correct """
        
        # Get all the documents from the db directly
        docs = documents.Idea.objects.all()
        response = self.c.get(self.resourceListURI('idea') + "?format=rss", **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(len(feed['entries']), len(docs))

    def test_feed_check_published_only(self):
        """ Check the number of entries is correct """

        # Add a draft object and a published doc (to ensure this bit works)
        doc = {"title": "The FIRST DRAFT idea.", "description": "First idea in draft.",
                 "status":"draft", "protective_marking" : self.pm }
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)

        doc = {"title": "The fifth published idea.", "description": "First idea description in here.",
                 "status":"published", "protective_marking" : self.pm }
        response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        
        # Now call the feed and ensure only the 3 published ones are present
        response = self.c.get(self.resourceListURI('idea') + "?format=rss", **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(len(feed['entries']), 5)
        

#@utils.override_settings(DEBUG=True)
class Test_Idea_RSS_Modifications(Test_Authentication_Base):
    
    """ Checks that the feed generator updates correctly when different
        aspects of the objects are modified"""

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
                 "protective_marking" : self.pm,
                 "tags":["one"]},
                
                {"title": "The third idea.",
                 "description": "Third idea description in here.",
                 "status":"published",
                 "protective_marking" : self.pm,
                 "tags":["two"]},
                
                {"title": "The forth idea.",
                 "description": "Forth idea description in here.",
                 "status":"published",
                 "protective_marking" : self.pm,
                 "tags":["one","two"]}
                ]
        
        # Store the responses
        self.doc_locations = []
        for doc in docs:
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)
            
        
            
    def test_feed_object_is_commented_on(self):
        """ A comment gets added to the feed, <updated> should change """

        # Hit the feed & get the published dtg    
        params =  "?format=rss"
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        published_1 = datetime.datetime.strptime(feed['updated'], '%Y-%m-%dT%H:%M:%SZ')
        
        # Wait a sec... (so that they aren't forced to have same time by inprecision)
        time.sleep(1)
        
        # Hit the feed for a second time
        # This is anal: it demonstrates that the difference in <updated> time is not just
        # due the fact that it's being called later, but because there has been a genuine
        # modification to the content.
        params =  "?format=rss"
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        published_check = datetime.datetime.strptime(feed['updated'], '%Y-%m-%dT%H:%M:%SZ')
        self.assertEquals(published_1, published_check)
                
        # Now comment on an idea
        uri = self.doc_locations[0] + 'comments/'
        new_data = {'title':'heres a new comment', 'body':'Here is the body of a new comment', 'protective_marking':self.pm}
        response = self.c.post(uri, json.dumps(new_data), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        
        # Hit the feed again
        params =  "?format=rss"
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        published_2 = datetime.datetime.strptime(feed['updated'], '%Y-%m-%dT%H:%M:%SZ')
        
        # Check the commented one has effected the <updated> time
        self.assertGreater(published_2, published_1)
        
     
    def test_feed_object_is_liked(self):
        """ One of the objects gets liked, the <updated> field should change """
         
        # Hit the feed & get the published dtg    
        response = self.c.get(self.resourceListURI('idea')+"?format=rss", **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        published_1 = datetime.datetime.strptime(feed['updated'], '%Y-%m-%dT%H:%M:%SZ')
        
        # Wait a sec... (so that they aren't forced to have same time by inprecision)
        time.sleep(1)
        
        # Now like an idea
        uri = self.doc_locations[0] + 'likes/'
        response = self.c.post(uri, content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        
        # Hit the feed again and get the published date
        response = self.c.get(self.resourceListURI('idea')+"?format=rss", **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        published_2 = datetime.datetime.strptime(feed['updated'], '%Y-%m-%dT%H:%M:%SZ')
        
        # Check the commented one has effected the <updated> time
        self.assertGreater(published_2, published_1)


    def test_feed_object_is_disliked(self):
        """ One of the objects gets liked, the <updated> field should change """
         
        # Hit the feed & get the published dtg    
        response = self.c.get(self.resourceListURI('idea')+"?format=rss", **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        published_1 = datetime.datetime.strptime(feed['updated'], '%Y-%m-%dT%H:%M:%SZ')
        
        # Wait a sec... (so that they aren't forced to have same time by inprecision)
        time.sleep(1)
        
        # Now dislike an object
        uri = self.doc_locations[0] + 'dislikes/'
        response = self.c.post(uri, content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        
        # Hit the feed again and get the published date
        response = self.c.get(self.resourceListURI('idea')+"?format=rss", **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        published_2 = datetime.datetime.strptime(feed['updated'], '%Y-%m-%dT%H:%M:%SZ')
        
        # Check the commented one has effected the <updated> time
        self.assertGreater(published_2, published_1)

 
#@utils.override_settings(DEBUG=True)
class Test_Idea_RSS_Filtering(Test_Authentication_Base):
    
    """ Checks that the entries are filtered correctly. """

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
                 "protective_marking" : self.pm,
                 "tags" : ["zero"]},
                
                {"title": "The second idea.",
                 "description": "Second idea description in here.",
                 "status":"published",
                 "protective_marking" : self.pm,
                 "tags":["one"]},
                
                {"title": "The third idea.",
                 "description": "Third idea description in here.",
                 "status":"published",
                 "protective_marking" : self.pm,
                 "tags":["two"]},
                
                {"title": "The forth idea.",
                 "description": "Forth idea description in here.",
                 "status":"published",
                 "protective_marking" : self.pm,
                 "tags":["one","two"]}
                ]
        
        # Store the responses
        self.doc_locations = []
        for doc in docs:
            response = self.c.post(self.resourceListURI('idea'), json.dumps(doc), content_type='application/json', **self.headers)
            self.doc_locations.append(response['location'])
            self.assertEqual(response.status_code, 201)

    def test_feed_filtered_by_single_tag(self):
        """ Filter by a single tag"""

        params =  "?format=rss" + "&tags=zero"
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(len(feed['entries']), 1)
        
         
    def test_feed_filtered_by_tags(self):
        """ Filter by multiple tags"""

        params =  "?format=rss" + "&tags__in=one,"
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(len(feed['entries']), 2)

        
    def test_feed_filtered_by_user(self):
        """ Filter the feed by user"""

        # Create a new user and use them to add a new doc
        user_id, api_key = self.add_user(email="new_user@ideaworks.com", first_name="new", last_name="user")
        headers = self.build_headers(user_id, api_key)
        
        new_doc = {"title": "The forth idea.",
                 "description": "Forth idea description in here.",
                 "status":"published",
                 "protective_marking" : self.pm,
                 "tags":["one","two"]}
        response = self.c.post(self.resourceListURI('idea'), json.dumps(new_doc), content_type='application/json', **headers)
            
        params =  "?format=rss" + "&user=%s"%(user_id)
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(len(feed['entries']), 1)

        
    def test_feed_filtered_by_like_count(self):
        """ Filter the feed by number of LIKES"""
        
        idea_url = self.doc_locations[0]
        uri = idea_url + 'likes/'
        
        response = self.c.post(uri, content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
                
        params =  "?format=rss" + "&like_count__gte=1"
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(len(feed['entries']), 1)

    def test_feed_filtered_by_like_count_high_filter(self):
        """ Filter the feed by number of LIKES
            Set a high filter to show it doesn't return everything."""
        
        idea_url = self.doc_locations[0]
        uri = idea_url + 'likes/'
        
        response = self.c.post(uri, content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
                
        params =  "?format=rss" + "&like_count__gte=2"
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(len(feed['entries']), 0)

    def test_feed_filtered_by_dislike_count(self):
        """ Filter the feed by number of DISLIKES"""
        
        idea_url = self.doc_locations[0]
        uri = idea_url + 'dislikes/'
        
        response = self.c.post(uri, content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
                
        params =  "?format=rss" + "&dislike_count__gte=1"
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(len(feed['entries']), 1)

    def test_feed_filtered_by_dislike_count_high_filter(self):
        """ Filter the feed by number of DISLIKES
            Set a high filter to show it doesn't return everything."""
        
        idea_url = self.doc_locations[0]
        uri = idea_url + 'dislikes/'
        
        response = self.c.post(uri, content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
                
        params =  "?format=rss" + "&dislike_count__gte=2"
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(len(feed['entries']), 0)

               
    def test_feed_filtered_by_score(self):
        """ Filter the feed by the vote_score"""
        
        idea_url = self.doc_locations[0]
        uri = idea_url + 'likes/'
        
        response = self.c.post(uri, content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        
        # Call the json to get back the score - just for dev/testing
        #params =  "?vote_score__gt=0"
        #response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        #print response.content
        
        # Call the rss to get back the rss for checking
        params =  "?format=rss" + "&vote_score__gt=0"
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(len(feed['entries']), 1)

         
    def test_feed_filtered_by_comment_count(self):
        """ Filter the feed by number of comments"""

        idea_url = self.doc_locations[0]
        uri = idea_url + 'comments/'
        new_data = {'title':'heres a new comment',
                    'body':'Here is the body of a new comment',
                    'protective_marking':self.pm}
        
        response = self.c.post(uri, json.dumps(new_data), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        
        params =  "?format=rss" + "&comment_count__gte=1"
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(len(feed['entries']), 1)
        
    def test_feed_filtered_by_comment_count_opposite(self):
        """ Filter the feed by number of comments
            High comment_count filter to make sure its not just accepting everything."""

        # Get the uri for the first idea
        idea_url = self.doc_locations[0]
        uri = idea_url + 'comments/'
        
        # Post a comment to the idea
        new_data = {'title':'heres a new comment',
                    'body':'Here is the body of a new comment',
                    'protective_marking':self.pm}
        response = self.c.post(uri, json.dumps(new_data), content_type='application/json', **self.headers)
        self.assertEquals(response.status_code, 201)
        
        # Get the feed filtered by comment count
        params =  "?format=rss" + "&comment_count__gte=2"
        response = self.c.get(self.resourceListURI('idea')+params, **self.headers)
        
        self.assertEquals(response.status_code, 200)
        feed = self.extract_feed_from_response(response)
        self.assertEquals(len(feed['entries']), 0)
