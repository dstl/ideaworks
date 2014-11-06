
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

from django.http import HttpResponse

from tastypie_mongoengine import resources
from tastypie.exceptions import ImmediateHttpResponse
from tastypie import http

class BaseCorsResource(resources.MongoEngineResource):
    """
    Class implementing CORS, @danigosa author and taken from this blog:
    http://codeispoetry.me/index.php/make-your-django-tastypie-api-cross-domain/
    Inheriting this in our models allows requests to the API from any domain, which is useful for the front-end.
    """
    
    def create_response(self, *args, **kwargs):
        response = super(BaseCorsResource, self).create_response(*args, **kwargs)
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Headers'] = 'Content-Type'
        return response

    def method_check(self, request, allowed=None):
        """
        For this base resource, check that the HTTP request method is permitted.
        """
        if allowed is None:
            allowed = []

        # Get the method (GET/POST/PUT, etc) from the django request object
        request_method = request.method.lower()
        allows = ','.join([str(i).upper() for i in allowed])
        
        if request_method == 'options':
            response = HttpResponse(allows)
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Allow-Headers'] = 'Content-Type'
            response['Allow'] = allows
            raise ImmediateHttpResponse(response=response)

        if not request_method in allowed:
            response = http.HttpMethodNotAllowed(allows)
            response['Allow'] = allows
            raise ImmediateHttpResponse(response=response)

        return request_method