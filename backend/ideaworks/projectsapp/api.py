
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import re
import datetime
import json

from django.conf import settings
from django.contrib.sites.models import get_current_site

from tastypie import http
from tastypie import fields as tastypie_fields
from django.contrib.auth.models import User
from tastypie.authorization import Authorization
from tastypie_mongoengine import resources
from tastypie_mongoengine import fields as mongo_fields

from ideaworks.generic_resources import BaseCorsResource

import projectsapp.documents as documents
import ideasapp.documents as idea_documents # This used in tags aggregation

from projectsapp.authentication import CustomApiKeyAuthentication
from projectsapp.authorization import PrivAndStatusAuthorization
from projectsapp.serializers import CustomSerializer
from api_functions import cleanup_tags, get_all_pms, get_max_pm, filter_by_data_level, tag_based_filtering
from api_functions import calculate_informal_time, derive_snippet, get_contributors_info, count_builder
from api_functions import get_user_vote_status, get_top_level_pm_elements, merge_tag_results


#-----------------------------------------------------------------------------

class CommentResource(BaseCorsResource, resources.MongoEngineResource):
    
    protective_marking = mongo_fields.EmbeddedDocumentField(embedded='projectsapp.api.ProtectiveMarkingResource', attribute='protective_marking', help_text='protective marking of this comment', null=True)
    
    class Meta:
        resource_name = 'comment'
        #queryset = documents.Comment.objects.all()
        object_class = documents.Comment
        serializer = CustomSerializer()
        allowed_methods = ('get', 'post', 'put', 'patch', 'delete')
        
        authentication = CustomApiKeyAuthentication()
        authorization = Authorization()    

    #-----------------------------------------------------------------------------

    def hydrate_modified(self, bundle):
        ''' Updates the comment modified timestamp field if the comment
            is edited.'''

        # Also change the parent if there is one for this call
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/.*')
        m = re.match(regExp, bundle.request.path).groupdict()
        if m:
            documents.Project.objects.get(id=m['doc_id']).update(**{'set__modified': datetime.datetime.utcnow()})
        
        # Change the modified date for all calls
        if bundle.request.method != 'GET':
            bundle.data['modified'] = datetime.datetime.utcnow()

        return bundle

    #-----------------------------------------------------------------------------

    def post_list(self, request, **kwargs):
        ''' Upon creation of a new project comment, change the total count too'''
        
        # Get the document
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/comments/')
        m = re.match(regExp, request.path).groupdict()
        if m:
            doc_id = m['doc_id']
        else:
            return super(CommentResource, self).post_list(request)

        doc = documents.Project.objects.get(id=doc_id)
        
        if doc.status == 'published':
            #Assumes we already have a user otherwise they wouldn't have authenticated
            documents.Project.objects(id=doc_id).update(**{'inc__comment_count': 1})
            return super(CommentResource, self).post_list(request)
        else:
            bundle = {"error": "User can only comment on projects with status=published."}
            return self.create_response(request, bundle, response_class = http.HttpBadRequest)

# ------------------------------------------------------------------------------------------------------------        

    def obj_create(self, bundle, **kwargs):
        ''' Add in the user information to the comment. '''
        
        # Add the user to the data payload
        bundle.data['user'] = bundle.request.user.username
        
        return super(CommentResource, self).obj_create(bundle)

# ------------------------------------------------------------------------------------------------------------        
    
    def obj_delete(self, bundle, **kwargs):
        ''' Determines how existing objects get deleted via the API  '''
        
        # Get the document ID
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/comments/(?P<comment_id>\d+)/')
        m = re.match(regExp, bundle.request.path).groupdict()
        
        # Decrement the comment count of the host document
        documents.Project.objects.get(id=m['doc_id']).update(**{'inc__comment_count': -1})
        
        return super(CommentResource, self).obj_delete(bundle, **{'pk':m['comment_id']})
        

# ------------------------------------------------------------------------------------------------------------        

    def alter_detail_data_to_serialize(self, request, data):
        ''' Modify the content just before serializing data for a specific item '''
        
        # Don't apply the meta object if it's anything but GET
        if request.method == 'GET':
            
            # Add a meta element for the single item response
            response_data = {'meta':{},'objects':[data]}
    
            # Add max PM into a newly created meta object
            pms = get_all_pms(response_data['objects'], subdocs_to_check=[], pm_name='protective_marking')
            response_data['meta']['max_pm'] = get_max_pm(pms)    
    
            # Get the modified time for this 1 object
            response_data['meta']['modified'] = data.data['modified'] 
    
            # Filter out the meta and objects content based on the data_level
            response_data = filter_by_data_level(request, response_data)

        else:
            response_data = data

        return response_data
# ------------------------------------------------------------------------------------------------------------        

    def alter_list_data_to_serialize(self, request, data):
        
        ''' Modify content just before serialized to output '''             
        
        # Tag-based filtering
        if request.method == 'GET' and request.GET.get('tags__in'):
            data = tag_based_filtering(request, data)
        
        # Assign the meta-level modified datetime to the most recent comment/project modified datetime
        object_modified_dts = [obj.data['modified'] for obj in data['objects']]
        if len(object_modified_dts) > 0:
            data['meta']['modified'] = max(object_modified_dts)
        
        # Find the highest protective marking in the dataset
        pms = get_all_pms(data['objects'],subdocs_to_check=[], pm_name='protective_marking')
        data['meta']['max_pm'] = get_max_pm(pms)    

        # Filter out the meta and objects content based on the data_level
        if request.method == 'GET':
            data = filter_by_data_level(request, data)
        
        return data

# ------------------------------------------------------------------------------------------------------------        

    def determine_format(self, request):
        ''' Override the default format, so that format=json is not required '''
    
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
        ''' Dehydrate to calc stuff on its way out '''
        
        # Class will always have a created/modified due to default.
        bundle.data['informal_created'] = calculate_informal_time(bundle.data['created'])
        bundle.data['informal_modified'] = calculate_informal_time(bundle.data['modified'])
        
        if bundle.data.has_key('body'):
            bundle.data['body_snippet'] = derive_snippet(bundle.data['body'])
        
        # Lookup the user's info
        bundle = get_contributors_info(bundle)
        
        return bundle

#-----------------------------------------------------------------------------

class ProjectResource(BaseCorsResource, resources.MongoEngineResource):
    
    protective_marking  = mongo_fields.EmbeddedDocumentField(embedded='projectsapp.api.ProtectiveMarkingResource', attribute='protective_marking', help_text='protective marking of this object, comprising classification, descriptor, codewords and national caveats.', null=True)
    comments            = mongo_fields.EmbeddedListField(of='projectsapp.api.CommentResource', attribute='comments', full=True, null=True)
    backs               = mongo_fields.EmbeddedListField(of='projectsapp.api.BackResource', attribute='backs', help_text='The user backing recorded for this object', full=True, null=True)
    
    class Meta:
        queryset = documents.Project.objects.all()
        resource_name = 'project'
        # What is permitted at the list level and at the single instance level
        list_allowed_methods = ['get', 'post', 'delete', 'put']
        detailed_allowed_methods = ['get', 'post', 'put', 'delete', 'patch']
        
        # Setup to default print pretty - mainly for debuggin
        serializer = CustomSerializer()
        
        authentication = CustomApiKeyAuthentication()
        authorization = PrivAndStatusAuthorization()
        
        max_limit = None

        filtering = {'created'        : ['gt', 'gte', 'lt', 'lte'],
                     'modified'       : ['gt', 'gte', 'lt', 'lte'],
                     'back_count'     : ['gt', 'gte', 'lt', 'lte'],
                     'comment_count'  : ['gt', 'gte', 'lt', 'lte'],
                     'tag_count'      : ['gt', 'gte', 'lt', 'lte'],
                     
                     'tags'         : ['exact', 'in', 'contains'],
                     'status'       : ['exact', 'in'],
                     'user'         : ['exact']}

        ordering = ['title', 'created', 'modified', 'back_count', 'comment_count', 'status']        

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
                options['title'] = settings.END_POINT_DESCRIPTIONS[api_end_point] + filtered
                
                current_site = get_current_site(request)
                options['link'] = current_site.domain + settings.FRONT_END_URL
                options['description'] = settings.END_POINT_DESCRIPTIONS[api_end_point]
            
        return super(ProjectResource, self).serialize(request, data, format, options)

# ------------------------------------------------------------------------------------------------------------        

    def obj_create(self, bundle, **kwargs):
        ''' Modifies the content before submission '''
        
        # Add in the user
        bundle.data['user'] = bundle.request.user.username
        
        # Sanitize tags before they get submitted
        try: bundle.data['tags'] = cleanup_tags(bundle.data['tags'])
        except: pass
        
        # These ensure that counts are present if projects are created with tags and backs and comments
        bundle = count_builder(bundle, 'comments',  'comment_count')
        bundle = count_builder(bundle, 'backs',     'back_count')
        bundle = count_builder(bundle, 'tags',      'tag_count')
         
        return super(ProjectResource, self).obj_create(bundle)

# ------------------------------------------------------------------------------------------------------------        

    def obj_update(self, bundle, **kwargs):
        ''' Updates content when resource is PUT or PATCHed '''
        
        # These ensure that counts are present if ideas are created with extra content
        bundle = count_builder(bundle, 'tags', 'tag_count')
                 
        return super(ProjectResource, self).obj_create(bundle)

    # No obj_update here because updates to lists of embedded docs don't trigger that function.
    # See individual embedded doc lists for update calls

# ------------------------------------------------------------------------------------------------------------        

    def alter_detail_data_to_serialize(self, request, data):
        ''' Modify the content just before serializing data for a specific item '''
        
        # Don't apply the meta object if it's anything but GET
        if request.method == 'GET':
            
            # Add a meta element for the single item response
            response_data = {'meta':{},'objects':[data]}
    
            # Add max PM into a newly created meta object
            pms = get_all_pms(response_data['objects'],subdocs_to_check=['comments'],pm_name='protective_marking')
            response_data['meta']['max_pm'] = get_max_pm(pms)    
    
            # Get the modified time for this 1 object
            response_data['meta']['modified'] = data.data['modified'] 
    
            # Filter out the meta and objects content based on the data_level
            response_data = filter_by_data_level(request, response_data)
    
        else:
            response_data = data

        return response_data

# ------------------------------------------------------------------------------------------------------------        
    
    def alter_list_data_to_serialize(self, request, data):
        
        ''' Modify content just before serialized to output '''             

        # Try to get the modified timestamp. Except catches instance where no data
        try:
            proj_mod = documents.Project.objects.order_by('-modified')[0]['modified']
        except:
            return data
        
        # Retrieve all comment modified timestamps (idea, comments)
        res = documents.Project._get_collection().aggregate([
            { "$project" : {"_id" : 0, "comments" : 1}},
            { "$unwind" : "$comments" },
            { "$project" : {"modified" : "$comments.modified"}},
            { "$sort" : {"modified" : -1}},
            { "$limit" : 1}
        ])['result']
        
        # In the event that there are no comments, chuck in an old date to guarantee the Project mod date wins
        if res:
            comments_mod = res[0]['modified']
        else:
            comments_mod = datetime.datetime(1970,1,1)
            
        # Assign the meta-level modified datetime to the most recent comment/Project modified datetime
        data['meta']['modified'] = max([proj_mod, comments_mod])
        
        # Tag-based filtering
        if request.method == 'GET' and request.GET.get('tags__in'):
            data = tag_based_filtering(request, data)
        
        # Find the highest protective marking in the dataset
        pms = get_all_pms(data['objects'], subdocs_to_check=['comments'], pm_name='protective_marking')
        data['meta']['max_pm'] = get_max_pm(pms)    

        # Filter out the meta and objects content based on the data_level
        if request.method == 'GET':
            data = filter_by_data_level(request, data)
        
        return data

    # ------------------------------------------------------------------------------------------------------------        

    def determine_format(self, request):
        ''' Override the default format, so that format=json is not required '''
    
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

    def hydrate_modified(self, bundle):
        ''' Updates the Project-level modified timestamp field if the Project
            is edited. It doesn't handle updates to comments because they are
            an embedded resource'''
        
        if bundle.request.method != 'GET':
            bundle.data['modified'] = datetime.datetime.utcnow()
        return bundle

    # ------------------------------------------------------------------------------------------------------------        

    def dehydrate(self, bundle):
        ''' Dehydrate - data on its way back to requester '''
        
        # User gets passed through because CustomAuth now passes it even for GET requests
        bundle.data['user_backed'] = get_user_vote_status(bundle)
        
        # Class will always have a time_stamp due to default.
        bundle.data['informal_created'] = calculate_informal_time(bundle.data['created'])
        bundle.data['informal_modified'] = calculate_informal_time(bundle.data['modified'])
        
        # Get the useful protective marking elements
        bundle = get_top_level_pm_elements(bundle)
               
        # Lookup the user's info
        bundle = get_contributors_info(bundle)

        # Produce a truncated (by word), html-tag cleaned version
        if bundle.data.has_key('description'):
            bundle.data['description_snippet'] = derive_snippet(bundle.data['description'])
        
        return bundle

#-----------------------------------------------------------------------------
        
class BackResource(resources.MongoEngineResource):
    '''The Backs against this Project.''' 

    # Placeholder field that is only handled at the API level, 
    # Not stored in the db, but used to populate the Comments API end point.
    #comment = tastypie_fields.CharField(attribute='comment', help_text="A comment associated with the Backs, but stored in comments.")
    
    class Meta:
        resource_name = 'back'
        object_class = documents.Vote
        allowed_methods = ['get', 'post', 'patch', 'put', 'delete']
        serializer = CustomSerializer()

        authentication = CustomApiKeyAuthentication()
        authorization = Authorization()

    #-----------------------------------------------------------------------------

    def post_list(self, request, **kwargs):
        ''' Upon creation of a new Project tag, change the total count too'''
        
        # Get the document
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/.*')
        m = re.match(regExp, request.path).groupdict()
        if m:
            doc_id = m['doc_id']
        else:
            return super(BackResource, self).post_list(request)

        doc = documents.Project.objects.get(id=doc_id)
        
        # Backs are only allowed on published content
        if doc.status != 'published':
            bundle = {"error": "User can only back published Projects."}
            return self.create_response(request, bundle, response_class = http.HttpBadRequest)
        
        else:
            # Get a list of who has backed
            users_already_backed = [vote['user'] for vote in doc['backs']]
            
            # Check this user actually exists in the db
            check_user = User.objects.get_by_natural_key(request.user.username)
            if not check_user:
                return
                #TODO: Return an error - Back not incremented
            
            # Check whether the user has voted
            user_id = request.user.username
                            
            # USER HAS ALREADY BACKED THE PROJECT - BLOCK ATTEMPTED DUPLICATE
            if user_id not in users_already_backed:
                documents.Project.objects(id=doc_id).update(**{'inc__back_count': 1})

            # USER HASN'T DONE ANYTHING - LET HIM VOTE        
            return super(BackResource, self).post_list(request)        
    
    #-----------------------------------------------------------------------------

    def obj_create(self, bundle, **kwargs):
        ''' Determines how new objects will get created  '''
        
        # Get the current document ID and those who have already Backed it
        doc_id = bundle.request.path.replace('/backs/', '').split('/')[-1]
        doc = documents.Project.objects.get(id=doc_id)
        
        # Get a list of who has backed it
        users_already_backed = [back['user'] for back in doc['backs']]
        
        # Get the current user
        user_id = bundle.request.user.username
        
        # Assumes we already have a user otherwise they wouldn't have authenticated
        if user_id not in users_already_backed:
            bundle.data['user'] = user_id

            # Decided to merge vote comments with standard comments,
            # so this takes care of that in the backend.
            if bundle.data.has_key('comment') == True:
                
                vote_comment = bundle.data['comment']
                
                new_comment = {'type'               : 'back',
                               'title'              : vote_comment['title'],
                               'user'               : user_id,
                               'modified'           : datetime.datetime.utcnow(),
                               'created'            : datetime.datetime.utcnow(),
                               }
                
                # Effectively optional fields
                try:
                    new_comment['body'] = vote_comment['body']
                except:
                    new_comment['body'] = None

                try:
                    new_comment['protective_marking'] = vote_comment['protective_marking']
                except:
                    new_comment['protective_marking'] = None

                # Add in the new comment
                try:
                    documents.Project.objects(id=doc_id).update(**{'push__comments' : new_comment})
                    
                except:
                    print 'Failed to push comment to project'
                    #TODO: Add in proper logging.

                # Increment the comment count at the same time
                documents.Project.objects(id=doc_id).update(**{'inc__comment_count': 1})
            
            return super(BackResource, self).obj_create(bundle)

# ------------------------------------------------------------------------------------------------------------        
    
    def obj_delete(self, bundle, **kwargs):
        ''' Determines how existing objects get deleted via the API  '''
        
        # Get the document ID
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/backs/(?P<back_id>\d+)/')
        m = re.match(regExp, bundle.request.path).groupdict()
        
        # Decrement the comment count of the host document
        documents.Project.objects.get(id=m['doc_id']).update(**{'inc__back_count': -1})
        
        return super(BackResource, self).obj_delete(bundle, **{'pk':m['back_id']})
        
        
# ------------------------------------------------------------------------------------------------------------        

    def hydrate(self, bundle):
        ''' Changes the modified date of the parent object '''
        
        # Also change the parent if there is one for this call
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/.*')
        m = re.match(regExp, bundle.request.path).groupdict()
        if m:
            documents.Project.objects.get(id=m['doc_id']).update(**{'set__modified': datetime.datetime.utcnow()})
        
        bundle = super(BackResource, self).hydrate(bundle) 
        return bundle

# ------------------------------------------------------------------------------------------------------------        

    def alter_detail_data_to_serialize(self, request, data):
        ''' Modify the content just before serializing data for a specific item '''
        
        # Don't apply the meta object if it's anything but GET
        if request.method == 'GET':
            
            # Add a meta element for the single item response
            response_data = {'meta':{},'objects':[data]}
    
            # Nothing classified about backs - they have no content other than user
            max_pm = documents.ProtectiveMarking(classification                = 'NOT CLASSIFIED',
                                                 classification_short          = 'NC',
                                                 classification_rank           = -1,
                                                 national_caveats_primary_name = '',
                                                 national_caveats_members      = [],
                                                 national_caveats_rank         = -1,
                                                 codewords                     = [],
                                                 codewords_short               = [],
                                                 descriptor                    = '')
            
            response_data['meta']['max_pm'] = json.loads(max_pm.to_json())
    
            # Get the modified time for this 1 object
            response_data['meta']['modified'] = [vote.data['created'] for vote in response_data['objects']]
    
            # Metadata only requests - minimum response allows client to check for updates
            if request.GET.get('data_level') == 'meta':
                del response_data['objects']

        else:
            response_data = data

        return response_data
# ------------------------------------------------------------------------------------------------------------        

    def alter_list_data_to_serialize(self, request, data):
        
        ''' Modify content just before serialized to output '''             
        
        
        # Tag-based filtering
        if request.method == 'GET':
            if request.GET.get('tags__in'):
                data = tag_based_filtering(request, data)
        
            # Assign the meta-level modified datetime to the most recent comment/Project modified datetime
            object_modified_dts = [obj.data['created'] for obj in data['objects']]
            
            # In the case where a call returns no backs
            if len(object_modified_dts) > 0:
                data['meta']['modified'] = max(object_modified_dts)
            else:
                data['meta']['modified'] = datetime.datetime(1970,1,1)
                
            # Nothing classified about backs - they have no content other than user
            max_pm = documents.ProtectiveMarking(classification                = 'NOT CLASSIFIED',
                                                     classification_short          = 'NC',
                                                     classification_rank           = -1,
                                                     national_caveats_primary_name = '',
                                                     national_caveats_members      = [],
                                                     national_caveats_rank         = -1,
                                                     codewords                     = [],
                                                     codewords_short               = [],
                                                     descriptor                    = '')
            data['meta']['max_pm'] = json.loads(max_pm.to_json())
    
            # Metadata only requests
            if request.GET.get('data_level') == 'meta':
                del data['objects']
                return data
        
        return data
        
    #-----------------------------------------------------------------------------

    def determine_format(self, request):
        ''' Override the default format, so that format=json is not required '''
    
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

    #-----------------------------------------------------------------------------
    def dehydrate(self, bundle):
        
        # Lookup the user's info
        bundle = get_contributors_info(bundle)
        return bundle        
    
#-----------------------------------------------------------------------------
        
class TagResource(BaseCorsResource, resources.MongoEngineResource):
    
    text = tastypie_fields.CharField(attribute='text',readonly=True,unique=True,help_text="Tag text.")
    count = tastypie_fields.IntegerField(attribute='count',readonly=True,help_text="Number of object instances of the tag.")

    class Meta:
        object_class = documents.Tag
        resource_name = 'tag'
        # Don't bother returning a resource uri or id
        include_resource_uri = False
        excludes = ['id']
        allowed_methods = ['get']
        serializer = CustomSerializer()
        max_limit = None

        authentication = CustomApiKeyAuthentication()
        authorization = Authorization()    


    def determine_format(self, request):
        ''' Override the default format, so that format=json is not required '''
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
        
    def get_object_list(self, request):
        
        # Build a basic aggregation
        aggregation = [
                        { "$unwind" : "$tags" },
                        { "$group" : { 
                            "_id" : "$tags",
                            "count" : { "$sum" : 1 }
                            }
                         },
                         { "$sort" : {"count" : -1}
                        }
                       ]
        
        status = request.GET.get('status', None)  
        # So that status can be a list of comma separated statuses: ?status=hidden,published,draft
        if status:
            statuses = [s.strip() for s in status.split(',')]
            aggregation.insert(0, {"$match" : {"status" : { "$in" : statuses }}})
        
        # Get results from Projects and from Ideas
        proj_res = documents.Project._get_collection().aggregate(aggregation)['result']
        idea_res = idea_documents.Idea._get_collection().aggregate(aggregation)['result']
        
        # Merge them into 1 list
        res = merge_tag_results(proj_res, idea_res)
        return [documents.Tag(text=tag['_id'],count=tag['count']) for tag in res]

    def obj_get_list(self, bundle, **kwargs):
        # Filtering disabled for brevity...
        return self.get_object_list(bundle.request)

#-----------------------------------------------------------------------------
        
class ProtectiveMarkingResource(resources.MongoEngineResource):
    class Meta:
        object_class = documents.ProtectiveMarking
        resource_name = 'protective_marking'
        allowed_methods = ['get', 'post', 'put']
        serializer = CustomSerializer()
        max_limit = None

        authentication = CustomApiKeyAuthentication()
        authorization = Authorization()    

    def dehydrate(self, bundle):
        ''' Add fields to each object on the way out '''

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
        
        