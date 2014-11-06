
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

'''
From this
http://stackoverflow.com/questions/12485053/tastypie-apikey-authentication
and this
http://stackoverflow.com/questions/17508912/django-tastypie-why-are-api-keys-useful-and-how-to-support-multiple-auth-scheme

Alternatively - and hence why the bit is commented, have used this:
http://django-tastypie.readthedocs.org/en/latest/cookbook.html#adding-to-the-django-admin
'''

from django.contrib.auth.models import User    
from django.db import models  
from tastypie.models import create_api_key 

models.signals.post_save.connect(create_api_key, sender=User)
