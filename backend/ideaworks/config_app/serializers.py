
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import json
from django.core.serializers.json import DjangoJSONEncoder
from tastypie.serializers import Serializer

class PrettyJSONSerializer(Serializer):
    """ Prettifies json output. Only really used before I moved onto custom serializer. Left in because
        it can be useful for debugging """
        
    json_indent = 2

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return json.dumps(data, cls=DjangoJSONEncoder,
                sort_keys=True, ensure_ascii=False, indent=self.json_indent)

class CustomSerializer(Serializer):
    """
    Custom serializer that adds extra data export types
    """
    formats = ['json', 'jsonp', 'xml', 'yaml']
    content_types = {
        'json': 'application/json',
        'jsonp': 'text/javascript',
        'xml': 'application/xml',
        'yaml': 'text/yaml'}
    
    json_indent = 2

    def get_front_end_url(self, resource_id):
        """
        Retrieves the front-end url for a specific idea/project/comment
        """
        
        #TODO: Work out how to lookup a page's url for a specific idea/comment/project 
        return '/api/v1/idea/%s'%(resource_id)

    def format_summary(self, pm, text):
        """
        Formats the summary text to include a classification
        """
        
        return text
        #summary = '<b style="color:%s">%s</b> ' %(pm['pm_colour'], pm['short_class'])
        #summary += text
        #return summary

    def to_json(self, data, options=None):
        """
        Dumps out the config content as json. Overriding existing function.
        """
        options = options or {}
        data = self.to_simple(data, options)
        return json.dumps(data, cls=DjangoJSONEncoder,
                sort_keys=True, ensure_ascii=False, indent=self.json_indent)