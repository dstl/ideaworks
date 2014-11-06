
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

from tastypie.authentication import Authentication
from tastypie.authorization import Authorization

from ideaworks.generic_resources import BaseCorsResource
from ideaworks.settings import *

from tastypie_mongoengine import resources
from protective_marking_app import documents as documents

from protective_marking_app.serializers import PrettyJSONSerializer

from tastypie_mongoengine import fields as mongo_fields

class GenericPMResource(BaseCorsResource, resources.MongoEngineResource):
        
    class Meta:
        allowed_methods = ['get']
        serializer = PrettyJSONSerializer()
        authentication = Authentication()
        authorization = Authorization()
    
    def determine_format(self, request):
        """ Override the default format, so that format=json is not required """
        content_types = {'json': 'application/json',
                         'jsonp': 'text/javascript',
                         'xml': 'application/xml',
                         'yaml': 'text/yaml',
                         'html': 'text/html',
                         'plist': 'application/x-plist',
                         'csv': 'text/csv'}

        format = request.GET.get('format', None)
        if format == None:
            return 'application/json'    
        else:
            return content_types[format]

#-----------------------------------------------------------------------------
        
class CssStyleResource(GenericPMResource):
    
    class Meta(GenericPMResource.Meta):
        object_class = documents.CssStyle
        resource_name = 'css_style'

#-----------------------------------------------------------------------------
        
class ClassificationResource(GenericPMResource):
    
    css_style  = mongo_fields.EmbeddedDocumentField(embedded='protective_marking_app.api.CssStyleResource', attribute='css_style', help_text='CSS Style associated with this protective marking element', null=True)
    
    class Meta(GenericPMResource.Meta):
        queryset = documents.Classification.objects.all()
        resource_name = 'classification'
        
#-----------------------------------------------------------------------------
        
class DescriptorResource(GenericPMResource):
    class Meta(GenericPMResource.Meta):
        queryset = documents.Descriptor.objects.all()
        resource_name = 'descriptor'
        
#-----------------------------------------------------------------------------
        
class CodewordResource(GenericPMResource):
    class Meta(GenericPMResource.Meta):
        queryset = documents.Codeword.objects.all()
        resource_name = 'codeword'
        
#-----------------------------------------------------------------------------
        
class NationalCaveatResource(GenericPMResource):
    class Meta(GenericPMResource.Meta):
        queryset = documents.NationalCaveat.objects.all()
        resource_name = 'national_caveat'
        