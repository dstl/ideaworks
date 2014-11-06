
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

"""
Settings specific to the registration application.
"""

AUTHENTICATION_BACKENDS = (
        'registration_email.auth.EmailBackend',
    )

REGISTRATION_EMAIL_REGISTER_SUCCESS_URL = lambda request, user: 'registration_complete'
REGISTRATION_EMAIL_ACTIVATE_SUCCESS_URL = lambda request, user: 'activation_success'

# The module defining the profile for users
AUTH_PROFILE_MODULE = 'extra_registration_parts.models'

# Create a file called email_settings.py in the same directory
# as this file and add in the email-related settings below
from email_settings import *

"""
Required email settings

DEFAULT_FROM_EMAIL  = '<default from email address - where will the email address appear from?>'
EMAIL_HOST_USER     = '<your email address>'
EMAIL_HOST_PASSWORD = '<your email password>'
EMAIL_PORT          = 587
EMAIL_HOST          = '<your email host>' - eg. 'smtp.live.com'
EMAIL_USE_TLS       = True
FEEDBACK_RECIPIENTS = ['<another or the same email address>',]

"""