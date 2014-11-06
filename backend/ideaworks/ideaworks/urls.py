
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

from django.conf.urls import patterns, include, url
from django.conf.urls.defaults import *
from tastypie.api import Api

# These 2 lines enable the django admin interface and objects 
from django.contrib import admin
admin.autodiscover()

# Api() is now instantiated in api/tools.py
from api.tools import v1_api
    
urlpatterns = patterns('',

    # API
    (r'^api/', include(v1_api.urls)),
    
    # Admin interface
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),

    # API Documentation
    # Navigate to docs/doc
    #TODO: Make this clearer and more coherent across ideas and projects
    (r'^api_docs/', include('tastytools.urls'), {'api_name': v1_api.api_name}),
    
    # Authentication, registration, etc.
    url(r'^',   include('auth_addin_app.urls')),


)


#from django.contrib.staticfiles.urls import staticfiles_urlpatterns
#urlpatterns += staticfiles_urlpatterns()
