
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

#//////////////////////////////////////////////////////////////////////////////
#
# THESE TEMPLATE TAGS ARE NOT USED IN THE CODE ANY LONGER
# THEY HAVE BEEN REPLACED BY VARIABLES READING DIRECT FROM SETTINGS
# BECAUSE IT WAS SO MUCH EASIER TO IMPLEMENT LOGIC WITH VARIABLES THAN TAGS
#
#//////////////////////////////////////////////////////////////////////////////

from django import template
from django.conf import settings

register = template.Library()

@register.simple_tag
def admin_name():
    """ Called by the template to access admin name """
    
    admins = getattr(settings, 'ADMINS', None)
    if admins:
        try:
            admin_name = admins[0][0]
        except:
            admin_name = None
        return admin_name

@register.simple_tag
def admin_email():
    """ Called by the template to access admin email """
    
    admins = getattr(settings, 'ADMINS', None)
    if admins:
        try:
            admin_email = admins[0][1]
        except:
            admin_email = None
        return admin_email

@register.simple_tag
def admin_phone():
    """ Called by the template to access phone number """
    
    admins = getattr(settings, 'ADMINS', None)
    if admins:
        try:
            admin_phone = admins[0][2]
        except:
            admin_phone = None
        return admin_phone
    
@register.simple_tag
def admin_url():
    """ Called by the template to access Admin Url """
    
    admins = getattr(settings, 'ADMINS', None)
    if admins:
        try:
            admin_url = admins[0][3]
        except:
            admin_url = None
        return admin_url
