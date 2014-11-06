
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

from django import template
from django.conf import settings

register = template.Library()

# Settings values
@register.simple_tag
def admin_email():
    """ Called by the template to access specific settings """
    
    admins = getattr(settings, 'ADMINS', None)
    if admins:
        admin_email = admins[0][1]
        return admin_email