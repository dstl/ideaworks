
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK
# Author: Rich Brantingham

import re
import datetime
# OSS lib
from tastypie_mongoengine import fields as mongo_fields
from tastypie_mongoengine import resources

from django.contrib.sites.models import get_current_site
from django.conf import settings

# The objects and data output serializer classes used
import contentapp.documents as documents
from contentapp.serializers import CustomSerializer

# The various authentication and authorization classes used in here
from contentapp.authentication import CustomApiKeyAuthentication
from contentapp.authorization import StaffSuperAuthorization
from contentapp.authorization import PrivilegedAndSubmitterOnly
from contentapp.authorization import PrivilegedAndSubmitterOnlyComments

# Called from the project-level
from ideaworks.generic_resources import BaseCorsResource

# Functions worth storing in a different file.
from api_functions import calculate_informal_time, get_contributors_info,get_top_level_pm_elements
from api_functions import get_all_pms, get_max_pm
from api_functions import count_builder, derive_snippet

# -----------------------------------------------------------------------------

class ProtectiveMarkingResource(resources.MongoEngineResource):
    class Meta:
        object_class = documents.ProtectiveMarking
        resource_name = 'protective_marking'
        allowed_methods = ['get', 'post', 'put']
        serializer = CustomSerializer()

        authentication = CustomApiKeyAuthentication()
        #authorization = Authorization()

    def dehydrate(self, bundle):
        """ Add fields to each object on the way out """

        # Prettify the codewords
        if bundle.data.has_key('codewords') and bundle.data['codewords'] != None and bundle.data['codewords'] != '':
            pretty_codewords = '/'.join(bundle.data['codewords'])
            bundle.data['codewords_pretty'] = pretty_codewords
        else:
            pretty_codewords = ''

        # Prettify the lot
        if bundle.data.has_key('classification') == True and bundle.data['classification']:
            pretty_cls = bundle.data['classification'].upper()
        else:
            pretty_cls = 'CLASSIFICATION NOT KNOWN'

        if bundle.data.has_key('descriptor') == True and bundle.data['descriptor'] and len(bundle.data['descriptor']) > 0:
            pretty_descriptor = ' [%s]'%(bundle.data['descriptor'].upper())
        else:
            pretty_descriptor = ''

        if bundle.data.has_key('national_caveats_primary_name') == True and bundle.data['national_caveats_primary_name']:
            pretty_caveats = bundle.data['national_caveats_primary_name'].upper()
        else:
            pretty_caveats = ''
        
        pretty_pm = ' '.join([pretty_cls, pretty_descriptor, pretty_codewords, pretty_caveats]).rstrip(' ')
        while pretty_pm.find('  ') != -1:
            pretty_pm = pretty_pm.replace('  ',' ')
        
        #Clean up space before the descriptor 
        bundle.data['pretty_pm'] = pretty_pm
        
        return bundle

class SiteContentResource(BaseCorsResource, resources.MongoEngineResource):

    protective_marking = mongo_fields.EmbeddedDocumentField(embedded='contentapp.api.ProtectiveMarkingResource', attribute='protective_marking', help_text='protective marking of this content', null=True)

    class Meta:
        resource_name = 'site_content'
        queryset = documents.Content.objects.all()
        serializer = CustomSerializer()
        allowed_methods = ('get', 'post', 'put', 'delete')

        authentication = CustomApiKeyAuthentication()
        #authorization = PrivilegedUsersOnlyAuthorization()
        authorization = StaffSuperAuthorization()

        filtering = {'created'  : ['gt', 'gte', 'lt', 'lte'],
                     'modified' : ['gt', 'gte', 'lt', 'lte'],
                     'status'   : ['exact'],
                     'type'     : ['exact'],
                     'index'    : ['exact'],    # Is this page the index for this 'type' - e.g. index page for faq type?
                     'user'     : ['exact']}

        ordering = ['index', 'type', 'title', 'created',
                    'modified', 'status', 'user', 'summary', 'body']

    # ------------------------------------------------------------------------------------------------------------        

    def determine_format(self, request):
        """ Override the default format, so that format=json is not required """
    
        content_types = {
                        'json': 'application/json',
                        'jsonp': 'text/javascript',
                        'xml': 'application/xml',
                        'yaml': 'text/yaml',
                        'html': 'text/html',
                        'plist': 'application/x-plist',
                        'csv': 'text/csv',
                        'rss': 'application/rss+xml',
                    }
    
        format = request.GET.get('format', None)
        if format == None:
            return 'application/json'    
        else:
            return content_types[format]

# ------------------------------------------------------------------------------------------------------------        

    def obj_create(self, bundle, **kwargs):
        """ Add in the user information to the comment. """
        
        # Add the user to the data payload
        bundle.data['user'] = bundle.request.user.username
        return super(SiteContentResource, self).obj_create(bundle)

# ------------------------------------------------------------------------------------------------------------        

    def obj_update(self, bundle, **kwargs):
        """ Apply the authorization limits when put/patch-ing"""
        
        # We must get the primary key because the mongoengine obj_update function is
        # expecting one to access the object we want to modify.
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/')
        m = re.match(regExp, bundle.request.path).groupdict()
        if not getattr(bundle.obj, 'pk', None):
            bundle.obj.pk = m['doc_id']
        
        return super(SiteContentResource, self).obj_update(bundle)

# ------------------------------------------------------------------------------------------------------------        

    def hydrate_modified(self, bundle):
        """ Updates the top-level modified timestamp field if the idea
            is edited. It doesn't handle updates to comments because they are
            an embedded resource"""
        
        if bundle.request.method != 'GET':
            bundle.data['modified'] = datetime.datetime.utcnow()
        return bundle
    
    # ------------------------------------------------------------------------------------------------------------        

    def dehydrate(self, bundle):
        """ Dehydrate - data on its way back to requester """
        
        # Class will always have a time_stamp due to default.
        bundle.data['informal_created'] = calculate_informal_time(bundle.data['created'])
        bundle.data['informal_modified'] = calculate_informal_time(bundle.data['modified'])
        
        # Get the useful protective marking elements
        bundle = get_top_level_pm_elements(bundle)
               
        # Lookup the user's info
        bundle = get_contributors_info(bundle)
        
        return bundle

# ------------------------------------------------------------------------------------------------------------        

    def alter_detail_data_to_serialize(self, request, data):
        """ Modify the content just before serializing data for a specific item """
        
        # Don't apply the meta object if it's anything but GET
        if request.method == 'GET':
            # Add a meta element for the single item response
            response_data = {'meta':{},'objects':[data]}
    
            # Add max PM into a newly created meta object
            pms = get_all_pms(response_data['objects'], subdocs_to_check=[], pm_name='protective_marking')
            response_data['meta']['max_pm'] = get_max_pm(pms)    
    
            # Get the modified time for this 1 object
            response_data['meta']['modified'] = data.data['modified'] 

        else:
            response_data = data

        return response_data

# ------------------------------------------------------------------------------------------------------------        
    
    def alter_list_data_to_serialize(self, request, data):
        """ Modify content just before serialized to output """             

        # Try to get the modified timestamp. Except catches instance where no data
        try:
            idea_mod = documents.Content.objects.order_by('-modified')[0]['modified']
            data['meta']['modified'] = idea_mod
        except:
            return data
            
        # Find the highest protective marking in the dataset
        if request.method == 'GET':
            pms = get_all_pms(data['objects'], pm_name='protective_marking')
            data['meta']['max_pm'] = get_max_pm(pms)    
        
        return data
#-----------------------------------------------------------------------------

class FeedbackResource(BaseCorsResource, resources.MongoEngineResource):
    
    protective_marking = mongo_fields.EmbeddedDocumentField(embedded='contentapp.api.ProtectiveMarkingResource', attribute='protective_marking', help_text='protective marking of this content', null=True)
    comments           = mongo_fields.EmbeddedListField(of='contentapp.api.FeedbackCommentResource', attribute='comments', full=True, null=True)
    
    class Meta:
        resource_name = 'feedback'
        queryset = documents.Feedback.objects.all()
        serializer = CustomSerializer()
        allowed_methods = ('get', 'post', 'put', 'delete')
        
        authentication = CustomApiKeyAuthentication()
        authorization = PrivilegedAndSubmitterOnly()
        
        filtering = {'created'  : ['gt', 'gte', 'lt', 'lte'],
                     'modified' : ['gt', 'gte', 'lt', 'lte'],
                     'status'   : ['exact'],
                     'type'     : ['exact'],
                     'user'     : ['exact']}

        ordering = ['title', 'created', 'modified', 'status', 'user', 'summary', 'body']

    # ------------------------------------------------------------------------------------------------------------        

    def determine_format(self, request):
        """ Override the default format, so that format=json is not required """
    
        content_types = {
                        'json': 'application/json',
                        'jsonp': 'text/javascript',
                        'xml': 'application/xml',
                        'yaml': 'text/yaml',
                        'html': 'text/html',
                        'plist': 'application/x-plist',
                        'csv': 'text/csv',
                        'rss': 'application/rss+xml',
                    }
    
        format = request.GET.get('format', None)
        if format == None:
            return 'application/json'    
        else:
            return content_types[format]

    # ------------------------------------------------------------------------------------------------------------        

    def obj_create(self, bundle, **kwargs):
        """ How to create a feedback object  """
        
        # Add the user to the data payload
        bundle.data['user'] = bundle.request.user.username
        bundle = count_builder(bundle, 'comments',  'comment_count')
        
        return super(FeedbackResource, self).obj_create(bundle)
    
    # ------------------------------------------------------------------------------------------------------------        

    def obj_update(self, bundle, **kwargs):
        """ Apply the authorization limits when putting"""
        
        # We must get the primary key because the mongoengine obj_update function is
        # expecting one to access the object we want to modify.
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/')
        m = re.match(regExp, bundle.request.path).groupdict()
        if not getattr(bundle.obj, 'pk', None):
            bundle.obj.pk = m['doc_id']
        
        return super(FeedbackResource, self).obj_update(bundle)
    
    # ------------------------------------------------------------------------------------------------------------        

    def hydrate_modified(self, bundle):
        """ Updates the idea-level modified timestamp field if the idea
            is edited. It doesn't handle updates to comments because they are
            an embedded resource"""
        
        if bundle.request.method != 'GET':
            bundle.data['modified'] = datetime.datetime.utcnow()
        return bundle
    
    # ------------------------------------------------------------------------------------------------------------        

    def dehydrate(self, bundle):
        """ Dehydrate - data on its way back to requester """
        
        # Class will always have a time_stamp due to default.
        bundle.data['informal_created'] = calculate_informal_time(bundle.data['created'])
        bundle.data['informal_modified'] = calculate_informal_time(bundle.data['modified'])
        
        # Get the useful protective marking elements
        bundle = get_top_level_pm_elements(bundle)
               
        # Lookup the user's info
        bundle = get_contributors_info(bundle)
        
        return bundle

# ------------------------------------------------------------------------------------------------------------        

    def alter_detail_data_to_serialize(self, request, data):
        """ Modify the content just before serializing data for a specific item """
        
        # Don't apply the meta object if it's anything but GET
        if request.method == 'GET':
            # Add a meta element for the single item response
            response_data = {'meta':{},'objects':[data]}
    
            # Add max PM into a newly created meta object
            pms = get_all_pms(response_data['objects'], subdocs_to_check=['comments'], pm_name='protective_marking')
            response_data['meta']['max_pm'] = get_max_pm(pms)    
    
            # Get the modified time for this 1 object
            response_data['meta']['modified'] = data.data['modified'] 

        else:
            response_data = data

        return response_data

# ------------------------------------------------------------------------------------------------------------        
    
    def alter_list_data_to_serialize(self, request, data):
        """ Modify content just before serialized to output """             

        # Try to get the modified timestamp. Except catches instance where no data
        try:
            idea_mod = documents.Feedback.objects.order_by('-modified')[0]['modified']
            data['meta']['modified'] = idea_mod
        except:
            return data
            
        # Find the highest protective marking in the dataset
        if request.method == 'GET':
            pms = get_all_pms(data['objects'], subdocs_to_check=['comments'], pm_name='protective_marking')
            data['meta']['max_pm'] = get_max_pm(pms)    
        
        return data
    
    #-----------------------------------------------------------------------------
    
    def serialize(self, request, data, format, options=None):
        """
        Override of resource.serialize so that custom options
        can be built for the rss serializer
        """
        
        # Is it an rss feed
        if 'application/rss+xml' in format:
            
            options = {}
            
            # Has the feed been filtered?
            params = request.GET.keys()
            params.pop(params.index('format'))
            if params and len(params) > 0:
                filtered = ' (filtered)'
            else:
                filtered = ''
            
            # Build a title based on the end point
            path = request.path.strip('/').split('/')
            # If it's not a detail view
            if len(path[-1]) != 24:

                # If there are tags, then make them available for the title
                tags = request.GET.get('tags', None)
                if not tags:
                    tags = request.GET.get('tags__in', None)
                if tags:
                    filtered = ' (Tags:%s)'%(tags)

                # Build the title                
                api_end_point = path[-1].lower()
                options['title'] = settings.END_POINT_DESCRIPTIONS[api_end_point]
                
                current_site = get_current_site(request)
                options['link'] = current_site.domain + settings.FRONT_END_URL
                options['description'] = settings.END_POINT_DESCRIPTIONS[api_end_point]
            
        return super(FeedbackResource, self).serialize(request, data, format, options)
    
#-----------------------------------------------------------------------------

class FeedbackCommentResource(BaseCorsResource, resources.MongoEngineResource):
    
    protective_marking = mongo_fields.EmbeddedDocumentField(embedded='contentapp.api.ProtectiveMarkingResource', attribute='protective_marking', help_text='protective marking of this comment', null=True)
    
    class Meta:
        #resource_name = 'comment'
        #queryset = documents.FeedbackComment.objects.all()
        object_class = documents.FeedbackComment
        serializer = CustomSerializer()
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        
        authentication = CustomApiKeyAuthentication()
        authorization = PrivilegedAndSubmitterOnlyComments()    
        
# ------------------------------------------------------------------------------------------------------------        
    
    def hydrate_modified(self, bundle):
        """ Updates the comment modified timestamp field if the comment
            is edited."""
        
        if bundle.request.method != 'GET':
            bundle.data['modified'] = datetime.datetime.utcnow()
        return bundle

# ------------------------------------------------------------------------------------------------------------        

    def post_list(self, request, **kwargs):
        """ Upon creation of a new comment (i.e. a post to the list end point), change the total count too """
               
        # Get the document
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/comments/.*')
        m = re.match(regExp, request.path).groupdict()
        #Assumes we already have a user otherwise they wouldn't have authenticated
        documents.Feedback.objects(id=m['doc_id']).update(**{'inc__comment_count': 1})
        return super(FeedbackCommentResource, self).post_list(request)

# ------------------------------------------------------------------------------------------------------------        

    def obj_create(self, bundle, **kwargs):
        """ Add in the user information to the comment. """
        
        # Add the user to the data payload
        bundle.data['user'] = bundle.request.user.username
        return super(FeedbackCommentResource, self).obj_create(bundle)

# ------------------------------------------------------------------------------------------------------------        
    
    def obj_delete(self, bundle, **kwargs):
        """ Determines how existing objects get deleted via the API  """
        
        # Get the document ID
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/comments/(?P<comment_id>\d+)/')
        m = re.match(regExp, bundle.request.path).groupdict()
        
        # Decrement the comment count of the host document
        documents.Feedback.objects.get(id=m['doc_id']).update(**{'inc__comment_count': -1})
        
        return super(FeedbackCommentResource, self).obj_delete(bundle, **{'pk':m['comment_id']})
        

# ------------------------------------------------------------------------------------------------------------        

    def alter_detail_data_to_serialize(self, request, data):
        """ Modify the content just before serializing data for a specific item """
        
        # Don't apply the meta object if it's anything but GET
        if request.method == 'GET':
            # Add a meta element for the single item response
            response_data = {'meta':{},'objects':[data]}
    
            # Add max PM into a newly created meta object
            pms = get_all_pms(response_data['objects'], subdocs_to_check=[], pm_name='protective_marking')
            response_data['meta']['max_pm'] = get_max_pm(pms)    
    
            # Get the modified time for this 1 object
            response_data['meta']['modified'] = data.data['modified'] 
    
        else:
            response_data = data

        return response_data
# ------------------------------------------------------------------------------------------------------------        

    def alter_list_data_to_serialize(self, request, data):
        
        """ Modify content just before serialized to output """             
                
        # Assign the meta-level modified datetime to the most recent comment modified datetime
        object_modified_dts = [obj.data['modified'] for obj in data['objects']]
        if len(object_modified_dts) > 0:
            data['meta']['modified'] = max(object_modified_dts)
        
        # Find the highest protective marking in the dataset
        pms = get_all_pms(data['objects'],subdocs_to_check=[], pm_name='protective_marking')
        data['meta']['max_pm'] = get_max_pm(pms)    
        
        return data

# ------------------------------------------------------------------------------------------------------------        

    def determine_format(self, request):
        """ Override the default format, so that format=json is not required """
    
        content_types = {
                        'json': 'application/json',
                        'jsonp': 'text/javascript',
                        'xml': 'application/xml',
                        'yaml': 'text/yaml',
                        'html': 'text/html',
                        'plist': 'application/x-plist',
                        'csv': 'text/csv',
                    }
    
        format = request.GET.get('format', None)
        if format == None:
            return 'application/json'    
        else:
            return content_types[format]
        
# ------------------------------------------------------------------------------------------------------------        
     
    def dehydrate(self, bundle):
        """ Dehydrate to calc stuff on its way out """

        # Class will always have a created/modified due to default.
        bundle.data['informal_created'] = calculate_informal_time(bundle.data['created'])
        bundle.data['informal_modified'] = calculate_informal_time(bundle.data['modified'])

        if bundle.data.has_key('body'):
            bundle.data['body_snippet'] = derive_snippet(bundle.data['body'])

        # Lookup the user's info
        bundle = get_contributors_info(bundle)
        return bundle
            