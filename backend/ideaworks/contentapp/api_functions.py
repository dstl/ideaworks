
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import json
import datetime
from HTMLParser import HTMLParser   #Used to create a non-marked up snippet
from django.contrib.auth.models import User

from ideaworks.generic_resources import BaseCorsResource

# Contentapp objects, authentication class and data output serializer
import contentapp.documents as documents
from contentapp.authentication import CustomApiKeyAuthentication
from contentapp.serializers import CustomSerializer


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
    
# ----------------------------------------------------------------------------------

class MLStripper(HTMLParser):
    """ Used to strip out the tags from html content
    Primarily for summary content text. """
    
    def __init__(self):
        self.reset()
        self.fed = []
    def handle_data(self, d):
        self.fed.append(d)
    def get_data(self):
        return ''.join(self.fed)

# ----------------------------------------------------------------------------------

def strip_tags(html):
    """ Remove the tags"""
    s = MLStripper()
    s.feed(html)
    return s.get_data()
    
# ----------------------------------------------------------------------------------

def smart_truncate(content, length=100, suffix='...'):
    """ Truncate a string based on words """
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

    
