
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import datetime
from mongoengine import Document, IntField, ListField, StringField, EmbeddedDocument, EmbeddedDocumentField, BooleanField, DateTimeField

# ----------------------------------------------------------------------------------------------------------
# This is commented so that the django project does not try to establish 
# another connection to mongo. Uncomment this if you want to run the 
# projective marking content into the database, but re-comment if you're 
# running the application or just running the tests - otherwise you may 
# lose your mongo-stored content. 

#import settings as settings
#TODO: How to implement a sort by protective marking?
#from django.contrib.auth.models import User
#from mongoengine import register_connection

#MONGO_DATABASE_NAME = 'ideaworks'
#MONGO_DB_PORT = 27348
#MONGO_DB_HOST = 'ds027348.mongolab.com'
#MONGO_DB_USER = 'ideaworks'
#MONGO_DB_PASS = 'ideaworks'
#register_connection(alias='default',name=MONGO_DATABASE_NAME, host=MONGO_DB_HOST, port=MONGO_DB_PORT, username=MONGO_DB_USER, password=MONGO_DB_PASS)
#register_connection(alias='default',name=MONGO_DATABASE_NAME)

# ----------------------------------------------------------------------------------------------------------


class InheritableDocument(Document):
    meta = {'abstract'          : True,
            'allow_inheritance' : True,
            'db_alias'          : 'default'}

class InheritableEmbeddedDocument(EmbeddedDocument):
    meta = {'abstract'          : True,
            'allow_inheritance' : True,
            'db_alias'          : 'default'}

# Help text for the Protective Marking of the resource
# More found here: https://www.gov.uk/government/uploads/system/uploads/attachment_data/file/251480/Government-Security-Classifications-April-2014.pdf
CLASSIFICATION_HELP     = 'The classification of this content.'
DESCRIPTOR_HELP         = 'A classification descriptor applying to the content.'
CODEWORDS_HELP          = 'A list of codewords applying to the content.'
NATIONAL_CAVEATS_HELP   = 'National caveats applied to the content.'

class CssStyle(InheritableEmbeddedDocument):
    """ Class to store the colour information associated with front end presentation of a classification."""
    
    background_color = StringField(max_length=8)    # E.g. "#fff"
    color            = StringField(max_length=8)    # E.g. "#888"
    border           = StringField(max_length=20)   # E.g. "solid 1px #ddd;"
    
#------------------------------------------------------------------------

class Prefix(InheritableDocument):
    """ Class to store the protective marking prefix. """
    
    prefix = StringField(max_length=4)

#------------------------------------------------------------------------

class Classification(InheritableDocument):
    """ Different classifications of the content. """
    classification      = StringField(max_length=200, required=False, help_text=CLASSIFICATION_HELP)
    abbreviation        = StringField(max_length=2, required=True)
    source              = StringField(required=False)
    comment             = StringField(max_length=1000)
    css_style           = EmbeddedDocumentField(CssStyle)
    national_authority  = StringField(max_length=3, help_text='The country code of the country that recognises this classification.')
    rank                = IntField(required=True)
    active              = BooleanField()
    inserted            = DateTimeField(default=datetime.datetime.utcnow)
     
#------------------------------------------------------------------------

class Descriptor(InheritableDocument):
    """The different descriptors"""
    
    descriptor          = StringField(required=False, help_text=DESCRIPTOR_HELP)
    source              = StringField(required=False)
    comment             = StringField(required=False)
    national_authority  = StringField(max_length=3, help_text='The country code of the country that recognises this descriptor.')
    active              = BooleanField()
    inserted            = DateTimeField(default=datetime.datetime.utcnow)

#------------------------------------------------------------------------

class Codeword(InheritableDocument):
    """The different codewords"""
    
    codeword            = StringField(max_length=200, required=False, help_text=CODEWORDS_HELP)
    abbreviation        = StringField(required=True)
    comment             = StringField(required=False)
    source              = StringField(required=False)
    national_authority  = StringField(max_length=3, help_text='The country code of the country that recognises this codeword.')
    abbreviation        = StringField(max_length=20)
    active              = BooleanField()
    inserted            = DateTimeField(default=datetime.datetime.utcnow)

#------------------------------------------------------------------------

class NationalCaveat(InheritableDocument):
    """The different national caveats"""
    
    primary_name        = StringField(max_length=200, required=False, help_text=NATIONAL_CAVEATS_HELP)
    secondary_names     = ListField(StringField(), required=False)
    member_countries    = ListField(StringField(max_length=3), required=False)
    source              = StringField(required=False)
    comment             = StringField(required=False)
    active              = BooleanField()
    inserted            = DateTimeField(default=datetime.datetime.utcnow)
    rank                = IntField(required=True)
    