
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

"""
Add the api part to the django user interface. This bit doesn't actually populate when
working under Python 2.6,but does under python 2.7.

"""

'''
From this
http://stackoverflow.com/questions/12485053/tastypie-apikey-authentication
and this
http://stackoverflow.com/questions/17508912/django-tastypie-why-are-api-keys-useful-and-how-to-support-multiple-auth-scheme

Alternatively:
http://django-tastypie.readthedocs.org/en/latest/cookbook.html#adding-to-the-django-admin
'''

from django.contrib.auth.models import User    
from django.db import models  
from tastypie.models import create_api_key 

models.signals.post_save.connect(create_api_key, sender=User)
