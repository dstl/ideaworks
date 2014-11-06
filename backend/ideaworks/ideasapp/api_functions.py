
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import json
import datetime
import math
from HTMLParser import HTMLParser

# Django objects/libs
from django.contrib.auth.models import User
from django.conf import settings
from django.utils.html import strip_tags, escape

# Project level object
from ideaworks.generic_resources import BaseCorsResource

# This django app
import ideasapp.documents as documents
from ideasapp.authentication import CustomApiKeyAuthentication
from ideasapp.serializers import CustomSerializer



def count_builder(bundle, field, count_field):
    """ Generates count values based on the length of another list/embedded field"""
    
    # Patch in the count values
    if bundle.data.has_key(field):
        bundle.data[count_field] = len(bundle.data[field])
    else:
        bundle.data[count_field] = 0
        bundle.data[field] = []
    
    return bundle

#--------------------------------------------------------------------------------

def cleanup_tags(tags):
    """ Sanitizes content submitted from the frontend."""
    
    clean_tags = [escape(strip_tags(tag)) for tag in tags]
    return clean_tags

#--------------------------------------------------------------------------------

def get_top_level_pm_elements(bundle):
    """ Extracts the useful PM elements out to the top level """
    
    # Ensure PM field exists
    try:
        pm = bundle.data['protective_marking']
    except:
        bundle.data['pretty_pm'] = 'NO PROTECTIVE MARKING FOUND'
        bundle.data['classification_short'] = 'NO PROTECTIVE MARKING FOUND'
    
    # Try to access the pretty pm
    try:    bundle.data['pretty_pm'] = pm.data['pretty_pm']
    except: bundle.data['pretty_pm'] = 'NO PROTECTIVE MARKING FOUND'
    
    # Try to access the short classification
    try:    bundle.data['classification_short'] = pm.data['classification_short']
    except: bundle.data['classification_short'] = 'NO PROTECTIVE MARKING FOUND'
        
    return bundle

#--------------------------------------------------------------------------------

def get_contributors_info(bundle, contributor=None):
    """ Get the user info for a specific contributor"""
    
    
    # Get the id of the user
    if not contributor:
        contributor = bundle.data['user']
    
    # Get the user object
    user_obj = None
    
    try:
        user_obj = User.objects.get(username=contributor)
    except:
        user_obj = User.objects.get(email=contributor)
    
    if user_obj:
        bundle.data['contributor_name'] = user_obj.first_name.title() + ' ' + user_obj.last_name.title()
    
    return bundle

#--------------------------------------------------------------------------------

def get_all_pms(documents, subdocs_to_check=[], pm_name='protective_marking', keep_field=None):
    """ Access all the PM elements from documents and lists of sub-documents
        keep_field specifies the field to keep - removing all the rest from the PM response."""
    
    pm_docs = []
    # Loop the objects
    for doc in documents:
        
        # Loop the fields and check if any of them are lists
        # If they are, then check for a PM subdocument to work on too
        for fld in doc.data.keys():
            if fld.lower() in subdocs_to_check:
                for sub_object in doc.data[fld]:
                    # Grab the pm object from any subdocuments
                    try:
                        pm_docs.append(sub_object.data[pm_name])
                    except KeyError:
                        print 'failed to append pm of listed subdoc'

        # Grab the protective marking object from the top level object
        try:
            pm_docs.append(doc.data[pm_name])
        except AttributeError:
            pm_docs.append(doc[pm_name])
        except KeyError:
            print 'Failed to get pm subdocument'
        
    return pm_docs
            
#--------------------------------------------------------------------------------

def get_sub_field(object, field_name):
    """ This is basically (realised after the fact) to catch the fact that
        in some cases the object being passed in is a bundle and in others (namely my tests)
        it is a list, which doesn't have the .data attribute """
    
    if object == None:
        content = None
    else:
        try:
            content = object.data[field_name]
        except AttributeError:
            content = object[field_name]
        
    return content
            
#--------------------------------------------------------------------------------

def get_max_pm(pm_docs):
    """ Get the maximum protective marking elements """

    max_class_rank = -1
    max_class_full = 'PUBLIC'
    max_class_short = 'PU'
    
    max_nat_cavs_rank = 0
    max_nat_cavs = ''
    max_nat_cavs_members = []

    codewords = []
    codewords_short = []
    descriptors = []
    
    # Derive maximums (classifications and national caveats)
    for doc in pm_docs:
        doc_class_rank = get_sub_field(doc, 'classification_rank')
        if doc_class_rank == None:
            continue
        
        doc_cavs_rank = get_sub_field(doc, 'national_caveats_rank')
        if doc_class_rank == None:
            continue        
        
        # CLASSIFICATION
        # Is it higher than the current max rank value?
        if not doc:
            continue
        
        if int(doc_class_rank) > max_class_rank:
            max_class_full  = get_sub_field(doc, 'classification')
            max_class_short = get_sub_field(doc, 'classification_short')
            max_class_rank  = get_sub_field(doc, 'classification_rank')
        
        if int(doc_cavs_rank) > max_nat_cavs_rank:
            max_nat_cavs           = get_sub_field(doc, 'national_caveats_primary_name')
            max_nat_cavs_members   = get_sub_field(doc, 'national_caveats_members')
            max_nat_cavs_rank      = get_sub_field(doc, 'national_caveats_rank')
    
        # Concatenate the codewords - assumed not mutually exclusive
        codewords += get_sub_field(doc, 'codewords')
        
        codewords_short += get_sub_field(doc, 'codewords_short')
        
        # Concatenate the descriptors - assumed not mutually exclusive
        if get_sub_field(doc, 'descriptor') and get_sub_field(doc, 'descriptor').upper() not in descriptors:
            descriptors.append(get_sub_field(doc, 'descriptor'))
    
    #TODO: Just joining the descriptors together rather than handling them properly as a list
    descriptors_out = ','.join(descriptors)
    
    max_pm = documents.ProtectiveMarking(classification                = max_class_full,
                                         classification_short          = max_class_short,
                                         classification_rank           = max_class_rank,
                                         national_caveats_primary_name = max_nat_cavs,
                                         national_caveats_members      = max_nat_cavs_members,
                                         national_caveats_rank         = max_nat_cavs_rank,
                                         codewords                     = list(set(codewords)),          # Get a unique list
                                         codewords_short               = list(set(codewords_short)),
                                         descriptor                    = descriptors_out)
    
    return json.loads(max_pm.to_json())

#--------------------------------------------------------------------------------

def calculate_informal_time(time_stamp):
    """ Calculates an informal time and presents it as a string
        Outside the classes as it may get used in several places."""

    now = datetime.datetime.utcnow()
    delta = now - time_stamp

    if delta.days < 1 and delta.seconds <= 60:
        informal_format = "just now"    
        
    elif delta.days < 1 and delta.seconds > 60 and delta.seconds <= 120:
        informal_format = "1 minute ago"
    
    elif delta.days < 1 and delta.seconds < 3600:
        informal_format = "%s minutes ago" %(int(delta.seconds/60))

    elif delta.days < 1 and delta.seconds/3600 <= 2:
        informal_format = "%s hour ago" %(int(delta.seconds/3600))
    
    elif delta.days < 1 and delta.seconds/3600 <= 24:
        informal_format = "%s hours ago" %(int(delta.seconds/3600))
    
    # If it was within the last week
    elif delta.days <= 7:
        informal_format = time_stamp.strftime("%A at %H:%M z")

    # If it was last 6 months
    elif delta.days <= 182:
        informal_format = time_stamp.strftime("%a, %d %b at %H:%M z")
    
    # If it was within the last year
    elif delta.days <= 365:
        informal_format = time_stamp.strftime("%d %B")
     
    # If it was last year
    else:
        informal_format = time_stamp.strftime("%d %b '%y")
     
    return informal_format

#-----------------------------------------------------------------------------

def tag_based_filtering(request, data):
    """ Filters the results by multiple tags """
    
    # The tags in the query
    tags = request.GET.get('tags__in').split(',')
    object_holder_list = []
    
    # Loop the objects and the queried tags, count the number of matches per doc
    for obj in data['objects']:
        # Hold the bundle in a dict to keep bundle untouched
        object_holder = {'bundle_obj':obj, 'tags_matched':0}
        for tag in tags:
            if tag in obj.data['tags']:
                object_holder['tags_matched'] += 1 
        object_holder_list.append(object_holder)
    
    # Sort the ideas in reverse order based on the number of matching tags
    sorted_data = sorted(object_holder_list, key=lambda k: k['tags_matched'], reverse=True)
    
    # Return just the idea objects
    data['objects'] = [sorted_idea['bundle_obj'] for sorted_idea in sorted_data]

    return data

#-----------------------------------------------------------------------------

def get_user_vote_status(bundle):
    """ Reports back whether and how the user has previously voted """
    
    # Has the current user voted on this idea?
    pos_votes = [vote.data['user'] for vote in bundle.data['likes']]
    neg_votes = [vote.data['user'] for vote in bundle.data['dislikes']]
    
    if unicode(bundle.request.user) in neg_votes:
        user_vote = -1
    elif unicode(bundle.request.user) in pos_votes:
        user_vote = 1
    else:
        user_vote = 0
    return user_vote

#-----------------------------------------------------------------------------

def filter_by_data_level(request, response_data):
    """ Filters the response data based"""

    data_level = request.GET.get('data_level', None)
    
    # Metadata only requests - minimum response allows client to check for updates
    if data_level == 'meta':
        del response_data['objects']

    elif data_level != 'meta' and data_level:
        for record in response_data['objects']:
            for key in record.data.keys():
                # Only allow through the fields specified in  RESPONSE_FIELD list
                if key.lower() not in settings.RESPONSE_FIELDS[data_level]: 
                    del record.data[key]

    return response_data
    
# ----------------------------------------------------------------------------------

""" Used to strip out the tags from html content
    Primarily for summary content text. """

class MLStripper(HTMLParser):
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

# ----------------------------------------------------------------------------------

def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()
    
# ----------------------------------------------------------------------------------

def smart_truncate(content, length=100, suffix='...'):
    if len(content) <= length:
        return content
    else:
        return ' '.join(content[:length+1].split(' ')[0:-1]) + suffix
    
# ----------------------------------------------------------------------------------

def derive_snippet(text_html, chrs=240):
    """ Strips text of html tags and truncates on nearest full word """
    
    if not text_html or text_html == '':
        text = text_html
    else:
        stripped_text = strip_tags(text_html.replace('\n', ''))
        text = smart_truncate(stripped_text, length=chrs, suffix='...')
        
    return text

# ----------------------------------------------------------------------------------

def vote_score(pos_count, neg_count):
    """ Calculates a score, based on:
        http://www.evanmiller.org/how-not-to-sort-by-average-rating.html """
    """
    SELECT widget_id, ((positive + 1.9208) / (positive + negative) - 
                   1.96 * SQRT((positive * negative) / (positive + negative) + 0.9604) / 
                          (positive + negative)) / (1 + 3.8416 / (positive + negative)) 
       AS ci_lower_bound FROM widgets WHERE positive + negative > 0 
       ORDER BY ci_lower_bound DESC;
    If your boss doesn't believe that such a complicated SQL statement could possibly return a useful result, just compare the results to the other two method described above:
    SELECT widget_id, (positive - negative) 
       AS net_positive_ratings FROM widgets ORDER BY net_positive_ratings DESC;
    SELECT widget_id, positive / (positive + negative) 
       AS average_rating FROM widgets ORDER BY average_rating DESC;
    """
    
    pos_count = float(pos_count)
    neg_count = float(neg_count)
    
    if pos_count + neg_count > 0:
        term_a = (pos_count + 1.9208) / (pos_count + neg_count)
        term_b = 1.96 * math.sqrt((pos_count * neg_count) / (pos_count + neg_count) + 0.9604)
        numerator = term_a - term_b / (pos_count + neg_count)
        
        denominator = 1 + 3.8416 / (pos_count + neg_count) 
        
        score = numerator / denominator
    else:
        score = 0
        
    return score
    
    
    