
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

from django import forms

# This set of imports and the class allows us to use the registration terms of service class
from registration.backends.default.views import RegistrationView

# For the signal
from django.dispatch import receiver
from registration.signals import user_registered

# This added in so that API key is created on account registration. Issue #IDEA-39.
from django.contrib.auth.models import User    
from django.db import models  
from tastypie.models import create_api_key 

models.signals.post_save.connect(create_api_key, sender=User)


class AuthCustomisedRegistrationView(RegistrationView):
    """
    Custom model that includes terms of service, first and last name and organisation info
    """
    
    tos = forms.BooleanField()
    first_name = forms.CharField(required=False)
    last_name = forms.CharField(required=False)
    organisation = forms.CharField(required=False)
    team = forms.CharField(required=False)
    
@receiver(user_registered)
def user_registered_handler(sender, user, request, **kwargs):
    """
    A signal handler that receives all the parameters from the validated form.
    """
    user.first_name = request.POST.get('first_name')
    user.last_name = request.POST.get('last_name')
    user.organisation = request.POST.get('organisation')
    user.team = request.POST.get('team')
    user.save()
