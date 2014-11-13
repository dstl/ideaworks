
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

