
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import json
import re
import datetime

from django.contrib.auth.models import User
from django.contrib.sites.models import get_current_site
from django.conf import settings

from tastypie import http
from tastypie import fields as tastypie_fields
from tastypie_mongoengine import fields as mongo_fields
from tastypie_mongoengine import resources

# Auth + auth
from tastypie.authorization import Authorization
from ideasapp.authentication import CustomApiKeyAuthentication
from ideasapp.authorization import StatusAuthorization

# Project-level objects
from ideaworks.generic_resources import BaseCorsResource

# Access the serializer for these objects
from ideasapp.serializers import CustomSerializer
import ideasapp.documents as documents

from api_functions import get_all_pms, get_max_pm, filter_by_data_level,tag_based_filtering, filter_by_data_level, calculate_informal_time
from api_functions import derive_snippet, get_contributors_info, count_builder, vote_score
from api_functions import get_user_vote_status, get_top_level_pm_elements
from api_functions import cleanup_tags

#-----------------------------------------------------------------------------

class CommentResource(BaseCorsResource, resources.MongoEngineResource):
    
    protective_marking = mongo_fields.EmbeddedDocumentField(embedded='ideasapp.api.ProtectiveMarkingResource', attribute='protective_marking', help_text='protective marking of this comment', null=True)
    
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
        """ Updates the comment modified timestamp field if the comment
            is edited."""

        # Also change the parent if there is one for this call
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/.*')
        m = re.match(regExp, bundle.request.path).groupdict()
        if m:
            documents.Idea.objects.get(id=m['doc_id']).update(**{'set__modified': datetime.datetime.utcnow()})
        
        # Change the modified date for all calls
        if bundle.request.method != 'GET':
            bundle.data['modified'] = datetime.datetime.utcnow()

        return bundle

    #-----------------------------------------------------------------------------

    def post_list(self, request, **kwargs):
        """ Upon creation of a new idea comment, change the total count too"""
        
        # Get the document
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/comments/')
        m = re.match(regExp, request.path).groupdict()
        if m:
            doc_id = m['doc_id']
        else:
            return super(CommentResource, self).post_list(request)

        doc = documents.Idea.objects.get(id=doc_id)
        
        if doc.status == 'published':
            #Assumes we already have a user otherwise they wouldn't have authenticated
            documents.Idea.objects(id=doc_id).update(**{'inc__comment_count': 1})
            return super(CommentResource, self).post_list(request)
        else:
            bundle = {"error": "User can only comment on ideas with status=published."}
            return self.create_response(request, bundle, response_class = http.HttpBadRequest)

# ------------------------------------------------------------------------------------------------------------        

    def obj_create(self, bundle, **kwargs):
        """ Add in the user information to the comment. """
        
        # Add the user to the data payload
        bundle.data['user'] = bundle.request.user.username
        
        return super(CommentResource, self).obj_create(bundle)

# ------------------------------------------------------------------------------------------------------------        
    
    def obj_delete(self, bundle, **kwargs):
        """ Determines how existing objects get deleted via the API  """
        
        # Get the document ID
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/comments/(?P<comment_id>\d+)/')
        m = re.match(regExp, bundle.request.path).groupdict()
        
        # Decrement the comment count of the host document
        documents.Idea.objects.get(id=m['doc_id']).update(**{'inc__comment_count': -1})
        
        return super(CommentResource, self).obj_delete(bundle, **{'pk':m['comment_id']})
        

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
    
            # Filter out the meta and objects content based on the data_level
            response_data = filter_by_data_level(request, response_data)

        else:
            response_data = data

        return response_data
# ------------------------------------------------------------------------------------------------------------        

    def alter_list_data_to_serialize(self, request, data):
        
        """ Modify content just before serialized to output """             
        
        # Tag-based filtering
        if request.method == 'GET' and request.GET.get('tags__in'):
            data = tag_based_filtering(request, data)
        
        # Assign the meta-level modified datetime to the most recent comment/idea modified datetime
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

#-----------------------------------------------------------------------------

class IdeaResource(BaseCorsResource, resources.MongoEngineResource):
    
    protective_marking  = mongo_fields.EmbeddedDocumentField(embedded='ideasapp.api.ProtectiveMarkingResource', attribute='protective_marking', help_text='protective marking of this idea, comprising classification, descriptor, codewords and national caveats.', null=True)
    comments            = mongo_fields.EmbeddedListField(of='ideasapp.api.CommentResource', attribute='comments', full=True, null=True)
    likes               = mongo_fields.EmbeddedListField(of='ideasapp.api.LikeResource', attribute='likes', help_text='The user likes recorded for this idea', full=True, null=True)
    dislikes            = mongo_fields.EmbeddedListField(of='ideasapp.api.DislikeResource', attribute='dislikes', help_text='The user dislikes recorded for this idea', full=True, null=True)

    class Meta:
        queryset = documents.Idea.objects.all()
        resource_name = 'idea'
        # What is permitted at the list level and at the single instance level
        list_allowed_methods = ['get', 'post', 'delete', 'put']
        detailed_allowed_methods = ['get', 'post', 'put', 'delete', 'patch']
        
        # Setup to default print pretty - mainly for debuggin
        serializer = CustomSerializer()
        
        authentication = CustomApiKeyAuthentication()
        authorization = StatusAuthorization()
        
        max_limit = None

        filtering = {'created'        : ['gt', 'gte', 'lt', 'lte'],
                     'modified'       : ['gt', 'gte', 'lt', 'lte'],
                     'like_count'     : ['gt', 'gte', 'lt', 'lte'],
                     'dislike_count'  : ['gt', 'gte', 'lt', 'lte'],
                     'comment_count'  : ['gt', 'gte', 'lt', 'lte'],
                     'vote_score'     : ['gt', 'gte', 'lt', 'lte'],
                     'tag_count'      : ['gt', 'gte', 'lt', 'lte'],
                     
                     'verified'     : ['exact'],
                     'verified_by'  : ['exact'],
                     'tags'         : ['exact', 'in', 'contains'],
                     'status'       : ['exact', 'in'],
                     'user'         : ['exact'],
                     'public'       : ['exact']}

        ordering = ['title', 'created', 'modified', 'like_count', 'dislike_count', 'comment_count', 'verified', 'status', 'vote_score']        

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
            
        return super(IdeaResource, self).serialize(request, data, format, options)

# ------------------------------------------------------------------------------------------------------------        

    def obj_create(self, bundle, **kwargs):
        """ Modifies the content before submission """
        
        # Add in the user
        bundle.data['user'] = bundle.request.user.username
        # These ensure that counts are present if ideas are created with tags/likes/dislikes and comments
        bundle = count_builder(bundle, 'comments',  'comment_count')
        bundle = count_builder(bundle, 'likes',     'like_count')
        bundle = count_builder(bundle, 'dislikes',  'dislike_count')
        bundle = count_builder(bundle, 'tags',      'tag_count')
        
        # Sanitize tags before they get submitted
        try: bundle.data['tags'] = cleanup_tags(bundle.data['tags'])
        except: pass
                
        # Finally build the score
        bundle.data['vote_score'] = vote_score(bundle.data['like_count'], bundle.data['dislike_count'])
         
        return super(IdeaResource, self).obj_create(bundle)

    # No obj_update here because updates to lists of embedded docs don't trigger that function.
    # See individual embedded doc lists for update calls

# ------------------------------------------------------------------------------------------------------------        

    def obj_update(self, bundle, **kwargs):
        """ Updates content when resource is PUT or PATCHed """
        
        # These ensure that counts are present if ideas are created with tags/likes/dislikes and comments
        bundle = count_builder(bundle, 'tags', 'tag_count')
                 
        return super(IdeaResource, self).obj_create(bundle)

    # No obj_update here because updates to lists of embedded docs don't trigger that function.
    # See individual embedded doc lists for update calls

# ------------------------------------------------------------------------------------------------------------        

    def alter_detail_data_to_serialize(self, request, data):
        """ Modify the content just before serializing data for a specific item """
        
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
        
        """ Modify content just before serialized to output """             

        # Try to get the modified timestamp. Except catches instance where no data
        try:
            idea_mod = documents.Idea.objects.order_by('-modified')[0]['modified']
        except:
            return data
        
        # Retrieve all comment modified timestamps (idea, comments)
        res = documents.Idea._get_collection().aggregate([
            { "$project" : {"_id" : 0, "comments" : 1}},
            { "$unwind" : "$comments" },
            { "$project" : {"modified" : "$comments.modified"}},
            { "$sort" : {"modified" : -1}},
            { "$limit" : 1}
        ])['result']
        
        # In the event that there are no comments, chuck in an old date to guarantee the idea mod date wins
        if res:
            comments_mod = res[0]['modified']
        else:
            comments_mod = datetime.datetime(1970,1,1)
            
        # Assign the meta-level modified datetime to the most recent comment/idea modified datetime
        data['meta']['modified'] = max([idea_mod, comments_mod])
        
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
    '''    
    def hydrate(self, bundle):
        """ Need to pass through user all the way through to dehydrate,
            so enabling that here"""
        print 'in hydrate', bundle.request.user
        bundle = super(IdeaResource, self).hydrate(bundle) 
        
        return bundle
    '''
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
        
        # User gets passed through because CustomAuth now passes it even for GET requests
        bundle.data['user_voted'] = get_user_vote_status(bundle)
        
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
        
class IdeaTagResource(resources.MongoEngineResource):
    """ the listed embedded subdocument tag as opposed to the result of the aggregate function""" 

    tag_protective_marking = mongo_fields.EmbeddedDocumentField(embedded='ideasapp.api.ProtectiveMarkingResource', attribute='tag_protective_marking', help_text='protective marking of this comment', null=True)
    
    class Meta:
        resource_name = 'ideatag'
        object_class = documents.IdeaTag
        allowed_methods = ['get', 'post']
        serializer = CustomSerializer()

        authentication = CustomApiKeyAuthentication()
        authorization = Authorization()    

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
    
    def post_list(self, request, **kwargs):
        """ Upon creation of a new idea tag, change the total count too"""
                
        # Update the current tag count + count of new tags
        doc_id = request.path.replace('/tags/', '').split('/')[-1]
        documents.Idea.objects(id=doc_id).update(**{'inc__tag_count': 1})
        return super(IdeaTagResource, self).post_list(request)        


#-----------------------------------------------------------------------------
        
class LikeResource(resources.MongoEngineResource):
    """The Likes against this idea.""" 

    # Placeholder field that is only handled at the API level, 
    # Not stored in the db, but used to populate the Comments API end point.
    #comment = tastypie_fields.CharField(attribute='comment', help_text="A comment associated with the like/dislike, but stored in comments.")
    
    class Meta:
        resource_name = 'like'
        object_class = documents.Vote
        allowed_methods = ['get', 'post', 'patch', 'put']
        serializer = CustomSerializer()

        authentication = CustomApiKeyAuthentication()
        authorization = Authorization()

    def post_list(self, request, **kwargs):
        """ Upon creation of a new idea tag, change the total count too"""
        
        # Get the document
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/.*')
        m = re.match(regExp, request.path).groupdict()
        if m:
            doc_id = m['doc_id']
        else:
            return super(LikeResource, self).post_list(request)

        doc = documents.Idea.objects.get(id=doc_id)
        
        # Likes are only allowed on published content
        if doc.status != 'published':
            bundle = {"error": "User can only like published ideas."}
            return self.create_response(request, bundle, response_class = http.HttpBadRequest)
        
        else:
            # Get a list of who has liked or disliked
            users_already_liked     = [vote['user'] for vote in doc['likes']]
            users_already_disliked  = [vote['user'] for vote in doc['dislikes']]
            
            # Check this user actually exists in the db
            check_user = User.objects.get_by_natural_key(request.user.username)
            if not check_user:
                return
                #TODO: Return an error - like not incremented
            
            # Check whether the user has voted
            user_id = request.user.username
    
            # User has already disliked the idea - flip the vote
            if user_id in users_already_disliked:
                # Single transaction - decrement dislike, increment like, pull the previous vote
                documents.Idea.objects(id=doc_id).update(**{'inc__dislike_count': -1,
                                                            'pull__dislikes__user':user_id,
                                                            'inc__like_count': 1})
                        
            # User has already liked the idea - block the duplicate attempt
            elif user_id not in users_already_liked:
                documents.Idea.objects(id=doc_id).update(**{'inc__like_count': 1})
    
            # Having made any mods, now re-compute the score value
            current_idea = documents.Idea.objects.get(id=doc_id)
            score = vote_score(current_idea['like_count'], current_idea['dislike_count'])
            documents.Idea.objects(id=doc_id).update(**{'set__vote_score':score})

            # User hasn't done anything up to now, so let him/her vote        
            return super(LikeResource, self).post_list(request)        
            

    def obj_create(self, bundle, **kwargs):
        """ Determines how new objects will get created  """
        
        # Get the current document ID and those who have already liked it
        doc_id = bundle.request.path.replace('/likes/', '').split('/')[-1]
        doc = documents.Idea.objects.get(id=doc_id)
        
        # Get a list of who has liked or disliked
        users_already_voted = [like['user'] for like in doc['likes']]
        users_already_voted += [like['user'] for like in doc['dislikes']]
        
        # Get the current user
        user_id = bundle.request.user.username
        
        # Assumes we already have a user otherwise they wouldn't have authenticated
        if user_id not in users_already_voted:
            bundle.data['user'] = user_id

            # Decided to merge vote comments with standard comments,
            # so this takes care of that in the backend.
            if bundle.data.has_key('comment') == True:
                
                vote_comment = bundle.data['comment']
                
                new_comment = {'type'               : 'like',
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
                    documents.Idea.objects(id=doc_id).update(**{'push__comments' : new_comment})
                    
                except:
                    print 'Failed to push comment'
                    #TODO: Add in proper logging.

                # Increment the comment count at the same time
                documents.Idea.objects(id=doc_id).update(**{'inc__comment_count': 1})
            
            return super(LikeResource, self).obj_create(bundle)

        
# ------------------------------------------------------------------------------------------------------------        

    def hydrate(self, bundle):
        """ Changes the modified date of the parent object """
        
        # Also change the parent if there is one for this call
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/.*')
        m = re.match(regExp, bundle.request.path).groupdict()
        if m:
            documents.Idea.objects.get(id=m['doc_id']).update(**{'set__modified': datetime.datetime.utcnow()})
        
        bundle = super(LikeResource, self).hydrate(bundle) 
        return bundle

# ------------------------------------------------------------------------------------------------------------        

    def alter_detail_data_to_serialize(self, request, data):
        """ Modify the content just before serializing data for a specific item """
        
        # Don't apply the meta object if it's anything but GET
        if request.method == 'GET':
            # Add a meta element for the single item response
            response_data = {'meta':{},'objects':[data]}
    
            # Nothing classified about likes/dislikes - they have no content other than user
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
        
        """ Modify content just before serialized to output """             
        
        
        # Tag-based filtering
        if request.method == 'GET':
            if request.GET.get('tags__in'):
                data = tag_based_filtering(request, data)
        
            # Assign the meta-level modified datetime to the most recent comment/idea modified datetime
            object_modified_dts = [obj.data['created'] for obj in data['objects']]
            
            # In the case where a call returns no likes
            if len(object_modified_dts) > 0:
                data['meta']['modified'] = max(object_modified_dts)
            else:
                data['meta']['modified'] = datetime.datetime(1970,1,1)
                
            # Nothing classified about likes/dislikes - they have no content other than user
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
    
    def dehydrate(self, bundle):
        
        # Lookup the user's info
        bundle = get_contributors_info(bundle)
        return bundle        
    
  
#-----------------------------------------------------------------------------
        
class DislikeResource(resources.MongoEngineResource):
    """The dislikes against this idea.""" 

    class Meta:
        resource_name = 'dislike'
        object_class = documents.Vote
        allowed_methods = ['get', 'post']
        serializer = CustomSerializer()

        authentication = CustomApiKeyAuthentication()
        authorization = Authorization()

    def post_list(self, request, **kwargs):
        """ Upon creation of a new idea tag, change the total count too"""
        
        # Get the document
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/.*')
        m = re.match(regExp, request.path).groupdict()
        if m:
            doc_id = m['doc_id']
        else:
            return super(DislikeResource, self).post_list(request)

        doc = documents.Idea.objects.get(id=doc_id)
        
        # Likes are only allowed on published content
        if doc.status != 'published':
            bundle = {"error": "User can only dislike published ideas."}
            return self.create_response(request, bundle, response_class = http.HttpBadRequest)
        
        else:
        
            # Get a list of who has liked or disliked
            users_already_liked     = [vote['user'] for vote in doc['likes']]
            users_already_disliked  = [vote['user'] for vote in doc['dislikes']]
            
            # Check whether the user has voted
            user_id = request.user.username
    
            # FOR A DISLIKE ACTION...
            
            # User has already liked, so just let them switch their like to dislike
            # and keep track of the counters.
            if user_id in users_already_liked:
                # Single transaction - decrement like, increment dislike, pull the previous vote
                documents.Idea.objects(id=doc_id).update(**{'inc__like_count': -1,
                                                            'pull__likes__user':user_id,
                                                            'inc__dislike_count': 1})
            
            # User has already disliked, so block this attempted to dislike again
            elif user_id not in users_already_disliked:
                documents.Idea.objects(id=doc_id).update(**{'inc__dislike_count': 1})
            
            # Having made any mods, now re-compute the score value
            current_idea = documents.Idea.objects.get(id=doc_id)
            score = vote_score(current_idea['like_count'], current_idea['dislike_count'])
            documents.Idea.objects(id=doc_id).update(**{'set__vote_score':score})
            
            # User hasn't done anything up to now, so let them dislike.
            return super(DislikeResource, self).post_list(request)        
        

    def obj_create(self, bundle, **kwargs):
        """ Determines how new objects will get created  """
        
        # Get the current document ID and those who have already liked it
        doc_id = bundle.request.path.replace('/dislikes/', '').split('/')[-1]
        doc = documents.Idea.objects.get(id=doc_id)
        
        # Get a list of who has liked or disliked
        users_already_voted = [vote['user'] for vote in doc['likes']]
        users_already_voted += [vote['user'] for vote in doc['dislikes']]
        
        # Get the current user
        user_id = bundle.request.user.username
        
        # Assumes we already have a user otherwise they wouldn't have authenticated
        #TODO: If it is a dupe, then send back something specific that says it's a duplicate.
        if user_id not in users_already_voted:
            bundle.data['user'] = user_id
            
            # Decided to merge vote comments with standard comments,
            # so this takes care of that in the backend.
            if bundle.data.has_key('comment') == True:
                vote_comment = bundle.data['comment']
                new_comment = {'type'               : 'dislike',
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
                    documents.Idea.objects(id=doc_id).update(**{'push__comments' : new_comment})
                except:
                    print 'Failed to push comment'
                    #TODO: Add in proper logging.
                    
                # Increment the comment count at the same time
                documents.Idea.objects(id=doc_id).update(**{'inc__comment_count': 1})
                
            return super(DislikeResource, self).obj_create(bundle)

# ------------------------------------------------------------------------------------------------------------        

    def alter_detail_data_to_serialize(self, request, data):
        """ Modify the content just before serializing data for a specific item """
        
        # Don't apply the meta object if it's anything but GET
        if request.method == 'GET':
            # Add a meta element for the single item response
            response_data = {'meta':{},'objects':[data]}
    
            # Nothing classified about likes/dislikes - they have no content other than user
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
        
        """ Modify content just before serialized to output """             
        
        
        # Tag-based filtering
        if request.method == 'GET':
            if request.GET.get('tags__in'):
                data = tag_based_filtering(request, data)
        
            
            # Assign the meta-level modified datetime to the most recent comment/idea modified datetime
            object_modified_dts = [obj.data['created'] for obj in data['objects']]
            # In the case where a call returns no likes
            if len(object_modified_dts) > 0:
                data['meta']['modified'] = max(object_modified_dts)
            else:
                data['meta']['modified'] = datetime.datetime(1970,1,1)
            
            # Nothing classified about likes/dislikes - they have no content other than user
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

# ----------------------------------------------------------------------------------------------------
  
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
        
        # Lookup the user's info
        bundle = get_contributors_info(bundle)
        return bundle

# ------------------------------------------------------------------------------------------------------------        

    def hydrate(self, bundle):
        """ Changes the modified date of the parent object """
        
        # Also change the parent if there is one for this call
        regExp = re.compile('.*/(?P<doc_id>[a-zA-Z0-9]{24})/.*')
        m = re.match(regExp, bundle.request.path).groupdict()
        if m:
            documents.Idea.objects.get(id=m['doc_id']).update(**{'set__modified': datetime.datetime.utcnow()})
        
        
        return bundle


#-----------------------------------------------------------------------------
        
class TagResource(BaseCorsResource, resources.MongoEngineResource):
    
    text = tastypie_fields.CharField(attribute='text',readonly=True,unique=True,help_text="Tag text.")
    count = tastypie_fields.IntegerField(attribute='count',readonly=True,help_text="Number of (concept) instances of the tag.")

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
        res = documents.Idea._get_collection().aggregate(aggregation)['result']
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
        
        