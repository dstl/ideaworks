
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

"""    settings for running on RB's home machine.    """
import os
import sys
# We register the connection to mongo in here and only here. If you do it anywhere else, you
# risk loosing your data.
from mongoengine import register_connection

APPLICATION_NAME = 'ideaworks'
APPLICATION_TAG_LINE = ''
DB_ALIAS = 'default'


TESTING = 'test' in sys.argv
if TESTING == True:
    APPLICATION_NAME += '_testserver'
    
DEBUG = True
TEMPLATE_DEBUG = DEBUG
ALLOWED_HOSTS = ['localhost',]

# You can specify a directory for your log files if you do not wish to use
# the default folder within this projects structure. For example:
#LOG_PATH = '/var/log/'

# These appear on this page: http://localhost:8000/accounts/password/reset/
# Please provide 1 of these for your users otherwise they have no way of resetting passwords
ADMINS   = ((None,    # String, representing the admin's name
             None,    # String, representing the admin's email address
             None,    # String, representing the admin's phone number
             None),)  # String, representing a helpdesk URL
MANAGERS = ADMINS

CONFIG_PATH = os.path.dirname(os.path.abspath(__file__))
DJANGO_PROJ_PATH = os.path.dirname(CONFIG_PATH)

#////////////////////////////////////////////////////////////////////////
# DATABASE CONFIG
#////////////////////////////////////////////////////////////////////////

# The User/API key stuff is managed in a relational database
# Storing user and site content in different dbs is a bit klunky, 
# but I've left it that way because of how easy auth is tied to relational dbs
SQLDB_FOLDER = os.path.join(DJANGO_PROJ_PATH, 'user_db')

# Check the folder exists
if os.path.exists(SQLDB_FOLDER) == True:
    # Catch permissions issue
    try:
        DB_LOCATION = os.path.join(SQLDB_FOLDER, '%s.sql3.db'%(APPLICATION_NAME))
    except:
        DB_LOCATION = os.path.join(DJANGO_PROJ_PATH, '%s.sql3.db'%(APPLICATION_NAME))
        
else:
    DB_LOCATION = os.path.join(DJANGO_PROJ_PATH, '%s.sql3.db'%(APPLICATION_NAME))


DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',   # Add 'postgresql_psycopg2', 'mysql', 'sqlite3' or 'oracle'.
        'NAME': DB_LOCATION,                      # Or path to database file if using sqlite3.
        'USER': '',                               # Not used with sqlite3.
        'PASSWORD': '',                           # Not used with sqlite3.
        'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
        'PORT': '',                               # Set to empty string for default. Not used with sqlite3.
    }
}

# Mongo for site content.
MONGO_DATABASE_NAME = APPLICATION_NAME
register_connection(alias=DB_ALIAS, name=MONGO_DATABASE_NAME)

# ALTERNATIVELY - PROVIDE MORE INFORMATION
#MONGO_DB_PORT = < non local host db port >
#MONGO_DB_HOST = < non local host >
#MONGO_DB_USER = < non local host db user >
#MONGO_DB_PASS = < non local host db password >
#register_connection(alias='default',name=MONGO_DATABASE_NAME, host=MONGO_DB_HOST, port=MONGO_DB_PORT, username=MONGO_DB_USER, password=MONGO_DB_PASS)

# For the email-activation-based workflow
# You don't need this if you've gone for the simple registration backend.
ACCOUNT_ACTIVATION_DAYS = 7 # One-week activation window; you may, of course, use a different value.

# Whether new users are permitted to register
REGISTRATION_OPEN = True

# Anonymous viewing?
ANONYMOUS_VIEWING = True

# Make this unique, and don't share it with anybody.
SECRET_KEY = 'ytqsffdhs2v*4y)+t$p*2g_#+)rgh*si1eq0qnt1wr%afx$r^z'

LOGIN_URL = '%s/accounts/login'%(APPLICATION_NAME)

# This is only ever needed in the event that the url passed as 'next' is not safe.
LOGIN_REDIRECT_URL = '/%s'%(APPLICATION_NAME)

# urls that we can safely redirect to. The match is a startswith...
SAFE_REDIRECTS = ['http://%s/accounts'%(APPLICATION_NAME),
                  'http://%s'%(APPLICATION_NAME),

                  # This to ensure tests don't fail because of lack of test server in redirect list
                  'http://testserver/%s'%(APPLICATION_NAME),
                  ]

# Settings that allow auto population of required template tags
# In this case a url that can be provided as a next to url tag calls so that the front end site gets called.
FRONT_END_URL = '/%s'%(APPLICATION_NAME)

# These settings are for the RSS Feed. They provide a pretty name 
# for the feed titles.
END_POINT_DESCRIPTIONS = {'idea'    : '%s Ideas'%(APPLICATION_NAME),
                          'project' : '%s Projects'%(APPLICATION_NAME),
                          'feedback': '%s Feedback'%(APPLICATION_NAME)}

SHOW_LATEST_IDEAS_COUNT = 5
SHOW_LATEST_PROJECTS_COUNT = 5

# Explicitly set the settings that get rendered via the API

API_SETTINGS = {'application_name'            : APPLICATION_NAME,
                'application_tag_line'        : APPLICATION_TAG_LINE,
                'front_end_url'               : FRONT_END_URL,
                'login_url'                   : LOGIN_URL,
                'login_redirect_url'          : LOGIN_REDIRECT_URL,
                'show_latest_idea_count'      : SHOW_LATEST_IDEAS_COUNT,
                'show_latest_project_count'   : SHOW_LATEST_PROJECTS_COUNT,
                'admin_name'                  : ADMINS[0][0],
                'admin_email'                 : ADMINS[0][1],
                'admin_phone'                 : ADMINS[0][2],
                'admin_url'                   : ADMINS[0][3]}

''' IF YOU MODIFY THIS DICT, YOU WILL ALSO NEED TO MODIFY THE FIELDS IN config_app.api.ConfigResource
    FOR THE CONTENT TO BE AVAILABLE IN THE API '''
    


