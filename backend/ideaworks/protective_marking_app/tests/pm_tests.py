
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import json
import urlparse

from django.core import urlresolvers
from django.test import client
from tastypie_mongoengine import test_runner

import protective_marking_app.documents as documents


class TestPmBaseClass(test_runner.MongoEngineTestCase):

    api_name = 'v1'
    c = client.Client()

    def get_meta_and_objects(self, response):
        content = json.loads(response.content)
        return content['meta'], content['objects']

    ''' User Handling Functions '''
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

    def tearDown(self):
        """ All sub classes will have Ideas collection destroyed """
        documents.Idea.objects.all().delete()

#------------------------------------------------------------------------------------------------
'''

Insert pms into the db.

Get all classifications
Get all descriptors
Get all national caveats
Get all codewords

Implement a data_level=less for just lists each of these.

Classifications
---------------
 - get sorted by rank
 - Get back just abbreviations
 - Lookup a full classification, get back an abbreviation
 - Lookup an abbreviation, get back a full classification
 - get back just the colour?
 
Codewords
---------
- Get a list of all codewords
- get a list of all abbreviated codewords
- Lookup a codeword and get back an abbreviation


Descriptors
-----------
- Get back all descriptors
- Return a plain list of descriptors


National Caveats:
-----------------
- Get back full detail
- Get back a less list of national caveat abbreviations
- Look up functionality - give an abbreviation and get back the country list
- Look up functionality - give a list of nationalities and get back abbreviation?

'''



    
    
    
    
    