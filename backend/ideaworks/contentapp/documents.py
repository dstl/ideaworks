
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import datetime
from mongoengine import Document, BooleanField, IntField, EmbeddedDocument, DateTimeField, ListField, StringField, EmbeddedDocumentField
#TODO: How to implement a sort by protective marking?

class InheritableDocument(Document):
    meta = {'abstract'          : True,
            'allow_inheritance' : True,
            'db_alias'          : 'default'}

class InheritableEmbeddedDocument(EmbeddedDocument):
    meta = {'abstract'          : True,
            'allow_inheritance' : True,
            'db_alias'          : 'default'}

#------------------------------------------------------------------------

class ProtectiveMarking(InheritableEmbeddedDocument):
    """ Represents the document protective marking information.
        Help text is provided as a setting due to change in the PM scheme in 2014."""

    # Classsification Info
    classification       = StringField(max_length=200, required=False, help_text='Full classification name protecting this object')
    classification_short = StringField(max_length=200, required=False, help_text='Abbreviated classification protecting this object')
    classification_rank  = IntField(default=0, required=False, help_text='A numeric representation of the classification to allow sorting.')
    
    # Descriptor
    descriptor         = StringField(max_length=200, required=False, help_text='escriptors protecting this object.')
    
    # Codeword info
    codewords          = ListField(StringField(), required=False, help_text='Codewords that protect this object.')
    codewords_short    = ListField(StringField(), required=False, help_text='Codewords that protect this object abbreviations as a list/array')
    
    # National caveat info
    national_caveats_primary_name   = StringField(required=False, help_text='Abbreviated national caveat')
    national_caveats_members        = ListField(StringField(), required=False, help_text='Constituent countries.')
    national_caveats_rank           = IntField(default=0, required=False, help_text='A numeric representation of the national caveats to help sorting')

#------------------------------------------------------------------------

class FeedbackComment(InheritableEmbeddedDocument):
    """ A comment object, typically housed in a ListField holding ReferenceField """
    
    type                       = StringField(help_text='The type of comment to allow for filtering.', required=False)
    user                       = StringField(help_text="ID of the user submitting the comment")
    title                      = StringField(max_length=200, help_text="The title of the comment, limited to 100 chrs.")
    created                    = DateTimeField(help_text="The date and time of when the object was created.", default=datetime.datetime.utcnow)
    modified                   = DateTimeField(help_text="When the comment or dependent data was last modified.", default=datetime.datetime.utcnow)
    body                       = StringField(max_length=5000, help_text="Main body of the text, limited to 1000 chrs.")
    protective_marking         = EmbeddedDocumentField(ProtectiveMarking)
    
#------------------------------------------------------------------------

class Content(InheritableDocument):
    """ A Content object which stores different types of staff-defined static content """
    
    status              = StringField(help_text='The status of this content.')
    type                = StringField(help_text='The type of content', required=True)
    user                = StringField(help_text="ID of the user submitting the content")
    title               = StringField(max_length=100, help_text="The title of the content, limited to 100 chrs.")
    summary             = StringField(max_length=140, help_text="A summary snippet of the content.")
    created             = DateTimeField(help_text="The date and time of when the object was created.", default=datetime.datetime.utcnow)
    modified            = DateTimeField(help_text="When the comment or dependent data was last modified.", default=datetime.datetime.utcnow)
    body                = StringField(help_text="Main body of the text. No character limit.")
    protective_marking  = EmbeddedDocumentField(ProtectiveMarking, required=True)
    index               = BooleanField(help_text='Whether this is the index page for this type of site content.')
    
#------------------------------------------------------------------------

class Feedback(InheritableDocument):
    """ A Content object extended to include feedback-specific things """
    
    status              = StringField(help_text='The status of this content.')
    type                = StringField(help_text='The type of content', required=True)
    user                = StringField(help_text="ID of the user submitting the content")
    title               = StringField(max_length=100, help_text="The title of the content, limited to 100 chrs.")
    summary             = StringField(max_length=140, help_text="A summary snippet of the content.")
    created             = DateTimeField(help_text="The date and time of when the object was created.", default=datetime.datetime.utcnow)
    modified            = DateTimeField(help_text="When the comment or dependent data was last modified.", default=datetime.datetime.utcnow)
    body                = StringField(help_text="Main body of the text. No character limit.")
    protective_marking  = EmbeddedDocumentField(ProtectiveMarking, required=True)
    # Public is currenty true because not supporting private feedback.
    public              = BooleanField(default=True, help_text='Whether the feedback can be made public or not.')
    
    comments            = ListField(EmbeddedDocumentField(FeedbackComment))
    comment_count       = IntField(help_text='number of comments associated with this item.')


