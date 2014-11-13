
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import os
import sys

#////////////////////////////////////////////////////////////////////////////////////
#
# This settings file adds in other settings files that are based on the 
# local running environment - the mac, dev server and deployments.
#
# Then each app has a number of settings, which are unique to them. They 
# import this settings file (and hence the local bits) and then extend
# with the app-based settings.
#
# Some of the settings in this file are only used by 2 or so apps, so they
# will need to be transferred with the app if it gets used elsewhere.
#
#
#////////////////////////////////////////////////////////////////////////////////////

# SETTINGS FROM LOCAL CONFIG

# You can key the configurations off of anything - I use project path.
configs = {
    '/Users/robrant/eclipseCode/ideaworks/backend/ideaworks'  : 'dev_rb',
    }

# Ensure all keys are lower case to ensure mis-match isn't due to case sensitivity
lowered_configs = {}
for key, val in configs.items():
    lowered_configs[key.lower()] = val
configs = lowered_configs
print '---',configs

#////////////////////////////////////////////////////////////////////////////////////
#
#    METHOD USED FOR ACCESSING MACHINE SPECIFIC SETTINGS (SEE config FOLDER AT PROJECT ROOT)
#
#////////////////////////////////////////////////////////////////////////////////////

ROOT_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
#print ROOT_PATH

# *** Have moved the local config stuff to the bottom so that it acts as an override
#     of the main settings. This seems to be a better setup for PaaS deployments
#     and makes sense for normal test servers too I think ***

#////////////////////////////////////////////////////////////////////////////////////
#
# Access tastypie API settings   
#
#////////////////////////////////////////////////////////////////////////////////////

# Import the configuration settings file - REPLACE projectname with your project
api_settings = __import__('tastypie_settings', globals(), locals(), 'ideaworks')

# Load the config settings properties into the local scope.
for setting in dir(api_settings):
    if setting == setting.upper():
        locals()[setting] = getattr(api_settings, setting)


#////////////////////////////////////////////////////////////////////////////////////
#
#    INFREQUENTLY CHANGED DEFAULT SETTINGS PROJECT WIDE
#
#////////////////////////////////////////////////////////////////////////////////////

TEMPLATE_DIRS = (os.path.join(ROOT_PATH, 'templates'),)

INSTALLED_APPS = (
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.sites',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Custom apps have to be above tastypie for some reason.
    'ideasapp',
    'auth_addin_app',
    'protective_marking_app',
    'contentapp',
    'config_app',
    'projectsapp',
    
    'tastypie',
    'tastypie_mongoengine',
    'tastytools',
    'registration',
    'registration_email',
    
    # Using the django admin interface for easy registration
    'django.contrib.admin',
    'django.contrib.admindocs',
    )

USE_TZ = True # Stops the breaking issue on 2.6 ('ValueError: as timezone() cannot be applied to naive datetime')

TIME_ZONE = 'Europe/London'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-uk'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = ''

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = ''

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = os.path.join(ROOT_PATH, 'static')

# See BOTTOM for STATIC_URL

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
#     'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
)

ROOT_URLCONF = 'ideaworks.urls'

#////////////////////////////////////////////////////////////////////////////////////

# Import the configuration settings file - REPLACE projectname with your project
try:
    config_module = __import__('config.%s' % configs[ROOT_PATH.lower()], globals(), locals(), 'ideaworks')    
    # Load the config settings properties into the local scope.
    for setting in dir(config_module):
        if setting == setting.upper():
            locals()[setting] = getattr(config_module, setting)

except Exception, e:
    print e
    print 'Not using pre-configured local settings file. Config file not found.'

#////////////////////////////////////////////////////////////////////////////////////
#
# Access Authentication settings   
#
#////////////////////////////////////////////////////////////////////////////////////

# Import the configuration settings file - REPLACE projectname with your project
auth_settings = __import__('auth_settings', globals(), locals(), 'ideaworks')

# Load the config settings properties into the local scope.
for setting in dir(auth_settings):
    if setting == setting.upper():
        locals()[setting] = getattr(auth_settings, setting)


# Set the sites information
# !! Domain must not include the scheme (http)
from django.contrib.sites.models import Site
try:
    one = Site.objects.all()[0]
    one.domain = 'localhost:8000'
    # This comes from the local setting file
    one.name = APPLICATION_NAME
    one.save()
except:
    pass


# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/%s/static/'%(APPLICATION_NAME)

#////////////////////////////////////////////////////////////////////////////////////
#
#    PROJECT WIDE LOGGING
#
#////////////////////////////////////////////////////////////////////////////////////

# Additional locations of static files
logFile        = "%s_error.log"%(APPLICATION_NAME)
requestLogFile = "%s_requests.log"%(APPLICATION_NAME)

# If LOG_PATH got set in the local settings, then this will pick up that directory - allowing for direct log writing to an external directory
try:
    LOG_PATH = LOG_PATH
except:
    LOG_PATH = os.path.join(ROOT_PATH, 'logs')

# LOG_PATH is pulled from the local settings files
LOG_FILE_PATH    = os.path.join(LOG_PATH, logFile)
REQUEST_LOG_PATH = os.path.join(LOG_PATH, requestLogFile)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        },
    },
    'handlers': {
        'default': {
            'level':'DEBUG',
            'class':'logging.handlers.RotatingFileHandler',
            'filename': LOG_FILE_PATH,
            'maxBytes': 1024*1024*5, # 5 MB
            'backupCount': 5,
            'formatter':'standard',
        },  
        'request_handler': {
                'level':'DEBUG',
                'class':'logging.handlers.RotatingFileHandler',
                'filename': REQUEST_LOG_PATH,
                'maxBytes': 1024*1024*5, # 5 MB
                'backupCount': 5,
                'formatter':'standard',
        },
    },
    'loggers': {

        '': {
            'handlers': ['default'],
            'level': 'DEBUG',
            'propagate': True
        },
        'django.request': {
            'handlers': ['request_handler'],
            'level': 'DEBUG',
            'propagate': False
        },
    }
}


