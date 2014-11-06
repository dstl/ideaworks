
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import datetime
from mongoengine import Document, IntField, EmbeddedDocument, DateTimeField, ListField, StringField, EmbeddedDocumentField

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

class Comment(InheritableEmbeddedDocument):
    """ A comment object, typically housed in a ListField holding ReferenceField """
    
    type                       = StringField(help_text='The type of comment to allow for filtering.', required=False)
    user                       = StringField(help_text="ID of the user submitting the comment")
    title                      = StringField(max_length=200, help_text="The title of the comment, limited to 100 chrs.")
    created                    = DateTimeField(help_text="The date and time of when the object was created.", default=datetime.datetime.utcnow)
    modified                   = DateTimeField(help_text="When the comment or dependent data was last modified.", default=datetime.datetime.utcnow)
    body                       = StringField(max_length=5000, help_text="Main body of the text, limited to 1000 chrs.")
    protective_marking         = EmbeddedDocumentField(ProtectiveMarking)
    
#------------------------------------------------------------------------

class Tag(InheritableDocument):
    text = StringField(max_length=30)
    count = IntField(default=0)

#------------------------------------------------------------------------

class Vote(InheritableEmbeddedDocument):    
    """ A class to be used to store simple user sentiment. """
    
    user        = StringField()
    created     = DateTimeField(help_text="When the user backed the object.", default=datetime.datetime.utcnow)

#------------------------------------------------------------------------

class Project(InheritableDocument):
    """ The project object """
    
    user                = StringField(max_length=200, help_text="The project creator. User id as a string.")
    title               = StringField(max_length=200,  help_text="The title for this project. <br/>E.g. 'Quantum processing'")
    description         = StringField(max_length=5000, help_text="A description of the project.")
    protective_marking  = EmbeddedDocumentField(ProtectiveMarking, help_text='Protective marking of this project.<br/>Comprising classification, descriptor, codewords and national caveats.<br/>See protective marking end point for fields.')
    created             = DateTimeField(help_text="The date and time of when the object was created.", default=datetime.datetime.utcnow)
    modified            = DateTimeField(help_text="When any component of the project or dependent data was last modified.", default=datetime.datetime.utcnow)
    tags                = ListField(StringField(), help_text="Tags that describe or relate to this project.<br/>E.g. ['physics', 'photons', 'expensive']")

    # Easier not to treat these as actual object ids
    backs               = ListField(EmbeddedDocumentField(Vote), help_text="Users who have backed this project.")
    comments            = ListField(EmbeddedDocumentField(Comment))
    related_ideas       = ListField(StringField(), help_text="Ideas associated with this project")
    
    # These included so that they get populated to the docs
    back_count          = IntField(required=False)
    comment_count       = IntField(required=False)
    tag_count           = IntField(required=False)
    
    status              = StringField(help_text="The current status of the object: published | draft | deleted | hidden ")

#------------------------------------------------------------------------
    