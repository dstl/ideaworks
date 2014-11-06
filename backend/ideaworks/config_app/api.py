
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

from tastypie import fields
from tastypie.resources import Resource

# Grab django project settings
from django.conf import settings

# Grab the serializer we're going to use to provide content to the front end.
from config_app.serializers import CustomSerializer

# Basic auth + auth as it's only a readonly API
from tastypie.authorization import Authorization
from tastypie.authentication import Authentication
from tastypie.exceptions import NotFound
from tastypie.bundle import Bundle

import logging
logging.getLogger(__name__)

class ConfigObject(object):
    """
    The base object for the config API. Sets the very minimum an object requires to be used as a resource.
    """
    
    def __init__(self, initial=None):
        self.__dict__['_data'] = {}

        self.__dict__['_data'] = initial
        
    def __getattr__(self, name):
        return self._data.get(name, None)

    def __setattr__(self, name, value):
        self.__dict__['_data'][name] = value

    def to_dict(self):
        return self._data


class ConfigResource(Resource):
    """
    The resource for configuration data to be sent to the front end
    so that site config only need be set in 1 location (the django app).
    """
    
    uuid                        = fields.CharField(attribute='uuid')
    application_name            = fields.CharField(attribute='application_name')
    application_tag_line        = fields.CharField(attribute='application_tag_line')
    front_end_url               = fields.CharField(attribute='front_end_url')
    login_url                   = fields.CharField(attribute='login_url')
    login_redirect_url          = fields.CharField(attribute='login_redirect_url')
    show_latest_idea_count      = fields.CharField(attribute='show_latest_idea_count')
    show_latest_project_count   = fields.CharField(attribute='show_latest_project_count')
    admin_name                  = fields.CharField(attribute='admin_name')
    admin_email                 = fields.CharField(attribute='admin_email')
    admin_phone                 = fields.CharField(attribute='admin_phone')

    class Meta:
        """
        The basics for a tastypie resource
        """
        resource_name = 'config'
        object_class = ConfigObject
        serializer = CustomSerializer()
        allowed_methods = ('get')
        
        authentication = Authentication()
        authorization = Authorization()
        
        #filtering
        #ordering
    # ------------------------------------------------------------------------------------------------------------        

    def determine_format(self, request):
        """ Override the default format, so that format=json is not required """
    
        content_types = {'json': 'application/json',
                         'jsonp': 'text/javascript',
                         'xml': 'application/xml',
                         'yaml': 'text/yaml'}
    
        format = request.GET.get('format', None)
        if format == None:
            return 'application/json'    
        else:
            return content_types[format]

    # ------------------------------------------------------------------------------------------------------------        
    
    def detail_uri_kwargs(self, bundle_or_obj):
        """ Grab the id of the specific resource """
        kwargs = {}

        if isinstance(bundle_or_obj, Bundle):
            kwargs['pk'] = bundle_or_obj.obj.uuid
        else:
            kwargs['pk'] = bundle_or_obj.uuid

        return kwargs

    # ------------------------------------------------------------------------------------------------------------        
    
    def get_object_list(self, request):
        """ Returns a list of results"""
        
        # This setting should be globally available from the settings import
        try:
            api_settings = settings.API_SETTINGS
        except:
            
            error_text = 'Failed to access settings to be used in config API. \n'
            error_text+= 'Local config file needs a setting named CONFIG_API_INCLUDE which contains a list '
            error_text+= 'of the settings to be shared via the API.'
            logging.error(error_text)
            raise NotFound("Settings for config API not available. Administrator required to check settings.")
        
        new_obj = ConfigObject(initial=api_settings)
        new_obj.uuid = 'api_settings'
        results = [new_obj]
        
        return results

    # ------------------------------------------------------------------------------------------------------------        

    def obj_get_list(self, bundle, **kwargs):
        """ Get the list """
        # Filtering disabled for brevity...
        return self.get_object_list(bundle.request)

