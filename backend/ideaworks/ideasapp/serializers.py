
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import datetime
import json
import csv

from django.core.serializers.json import DjangoJSONEncoder
from django.http import HttpResponse
from django.utils import feedgenerator
from django.conf import settings

from tastypie.serializers import Serializer

class PrettyJSONSerializer(Serializer):
    json_indent = 2

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return json.dumps(data, cls=DjangoJSONEncoder,
                sort_keys=True, ensure_ascii=False, indent=self.json_indent)

class CustomSerializer(Serializer):
    
    formats = ['json', 'jsonp', 'xml', 'yaml', 'html', 'plist', 'rss', 'csv']
    content_types = {
        'json': 'application/json',
        'jsonp': 'text/javascript',
        'xml': 'application/xml',
        'yaml': 'text/yaml',
        'html': 'text/html',
        'plist': 'application/x-plist',
        'rss': 'application/rss+xml',
        'csv': 'text/csv',
    }
    json_indent = 2

    def get_front_end_url(self, resource_id):
        """ Retrieves the front-end url for a specific idea/project/comment"""
        
        #TODO: Work out how to lookup a page's url for a specific idea/comment/project 
        return '/api/v1/idea/%s'%(resource_id)

    def format_text(self, pm, text):
        """ Formats the summary text to include a classification """
        
        return "(%s) %s"%(pm, text)

    def get_iso_dtg(self, datetime_string):
        """ Converts string into datetime and back again into ISO """
        
        try:
            dt = datetime.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S.%f')
        except:
            dt = datetime.datetime.strptime(datetime_string, '%Y-%m-%dT%H:%M:%S')
        
        return dt
        

    def to_rss(self, data, options=None):
        
        if not options or options == {}:
            options['title']       = 'default feed title'
            options['link']        = 'default feed link'
            options['description'] = 'default feed description'
            
        data = self.to_simple(data, options)
        
        #*****************************************************
        # Subclass the serialize function in your api
        # to build options which get passed into here.
        #*****************************************************
                
        # Feed level info
        feed = feedgenerator.Atom1Feed(
            title       = unicode(options['title']),
            link        = unicode(options['link']),
            description = unicode(options['description'])
        )
        
        #TODO: Add in classification abbreviation into the feed
        for item in data['objects']:
            feed.add_item(unique_id     = item['id'],
                          title         = self.format_text(item['classification_short'], item['title']),
                          description   = self.format_text(item['classification_short'], item['description']),
                          link          = self.get_front_end_url(item['id']),
                          pubdate       = self.get_iso_dtg(item['modified']),
                          author_name   = item['contributor_name'])
                        
        return feed.writeString('utf-8')

    def to_json(self, data, options=None):
        options = options or {}
        data = self.to_simple(data, options)
        return json.dumps(data, cls=DjangoJSONEncoder,
                sort_keys=True, ensure_ascii=False, indent=self.json_indent)

    def to_csv(self, data, options=None):
        """ Renders to csv"""
        
        response = HttpResponse(mimetype='text/csv')
        response['Content-Disposition'] = 'attachment; filename=%s.csv'%(settings.APPLICATION_NAME)
        writer = csv.writer(response)
        # Write headers to CSV file
        
        # Access the objects and a simplified version to get the fields
        objects = data['objects']
        simplified_data = self.to_simple(objects, options)
        
        headers = []
        # Remove subdocs - bit of a short-term fix
        for fld in simplified_data[0].keys():
            if not isinstance(simplified_data[0][fld], dict):
                headers.append(fld)
        # Write out the headers
        writer.writerow(headers)            
        
        # Write data to CSV file
        for obj in objects:
            row = []
            for field in headers:
                if field in headers:
                    val = obj.data[field]
                    if isinstance(val, list):
                        val = ';'.join(val)
                    if callable(val):
                        val = val()
                    row.append(val)
            writer.writerow(row)
            
        # Return CSV file to browser as download
        return response