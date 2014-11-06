(c) Crown Copyright 2011 Defence Science and Technology Laboratory UK

# Ideaworks

Ideaworks is a free and open source web application that allows a group of people to collate, comment on and rate ideas. The application also has
allows staff users to create projects, small packages of work that have developed from the ideas. 

It was initially designed and built by the UK Defence Science & Technology Laboratory (dstl) and released under AGPL as a prototype tool. Ideaworks is the first piece of software to be released onto Github because of its simplicity, low risk and potential benefit to the Free and Open Source software community - particularly those organising hackathons. 

We don’t pretend that the code is the best ever written (see NOTICE.md and LICENSE.md for the disclaimers), but please use it as you see fit, file bugs and enhancement issues (of which we’ll be adding a few outstanding). We very much welcome pull requests. 

The application is split into 2 parts:

1. A django project which provides the data API back-end and user authentication.
2. A responsive design html/js/css front-end. 

## Installation

The rest of this document outlines how to get it up and running. We’ve attempted to document it as best as possible, but it can be a bit of a pain, so we’re in the process of writing Ansible scripts to automate deployment on Ubuntu and CentOS. That will likely be published under a separate repo that links back to this as a submodule.



## Authentication

Two forks to the original code handle the different authentication setups. The primary ideaworks repo is setup to work with an SMTP server and requires
an email-based account activation step. The ideaworks-no-email fork does not require any SMTP connections; account activation is done automatically.

Calls to the API are authenticated using a username and API key. The content is read-only for anonymous users. All other http request types/verbs require 
an active API key and username. 

If you want to use the API only, you'll need to register and then ask your administrator for your key. We'll tidy this process up so that API keys are
available on a profile page once logged in.

## API Documentation

API auto-documentation is provided using django-tastytools. Visit: /docs/api_docs/.


# Dependencies

## Operating System:

We've tested and deployed ideaworks on RHEL, CentOS and Scientific Linux - generally 6.4, but it's likely to work on > 6.4.

You'll need to:

	$> sudo yum -y install httpd, libxml2, libxslt, gcc and python-devel

You'll also need:

    $> yum install -y mod_wsgi
    
and possibly:

    $> yum install -y mod_proxy


## Python:

It has been tested and works under Python 2.6 and 2.7.


## Python packages

We use [virtualenv](http://virtualenv.readthedocs.org/en/latest/ "virtualenv") and pip to manage python project dependencies. 

A requirements.txt file provided which lists the required packages. If you are connected to the Internet and have pip
(and/or virtualenv) installed, you can just run:

    $> pip install -r <path>/requirements.txt
    
If your deployment environment is not connected to the Internet, then follow these instructions to cache the dependencies before transfer
 to your deployment network:

When connected to the Internet, run:

    $> pip install --download <DIR> -r <PATH_TO>requirements.txt

Then, on your deployment network, you can run:

    $> pip install --no-index --find-links=<DIR> -r <PATH_TO>requirements.txt

where <DIR> is a directory you'll use to store each of the .gz/.zip/.tar dependency packages.
I've added a directory called /dependencies_cache which I use for this dependency caching.
<PATH_TO> is the path to the requirements.txt file in this proejct. 

Probably worth checking that all of the dependencies have downloaded before transferring over.


Django tastytools proved a bit more problematic to install, so check before you move on that it defintely installed:

    $> pip freeze

If not, then navigate to the source you've downloaded and run:
    
    $> pip install django-tastytools-master/ #Note the slash so that it's definitely pointing at the directory


## Front-end HTML, JavaScript, CSS, images and fonts

The front-end is self contained and will ship with all of the html, css and js libraries the application requires. 

The url scheme, domain and paths need to be set in the first config section of js/services.js within the istarter-web repo.

Example to be included.

## Web Server

We use Apache/httpd running with mod_wsgi to bridge to the Python web app.



## Apache Server conf files

Example apache conf files are provided in the setup folder. These need to be placed in your webservers conf.d/ directory.

An httpd restart/reload will be needed to pick up the new files. Below is a list of the files and what they control:

1. **ideaworks_api.conf**: Links the web app to the wsgi python daemon and provides a mapping between a url path and the static files required for the authentication pages.
2. **ideaworks_web.conf**: Provides a series of proxies that ensure seemless links between the front-end and the API.


## Databases

**Mongodb** is used for the site content (ideas, projects, comments, etc). We've used Mongodb 2.4, but it should work with 2.6+ too - we're not doing anything crazy.
You obviously don't have to use a local instance of mongo - there are commented example settings for using a remote db server in the project settings.

**Sqlite3** or **postgres** is used for the authentication backend because of the ease of integrating SQL dbs with Django.
This setup has some benefits (content and auth are stored separately) and some draw-backs (content and auth are stored separately!). :)



## Email

Depending which fork you use, you might need access to an SMTP server. You'll need to know your credentials during the installation/configuration
process too so that they're available to Django's mail sending libraries. These settings will need to be provided in a file called email_settings.py
which gets stored alongside the main django project settings file (it gets pulled in by auth_settings - see that file for more info).


# Installation

* Clone down this repo and unpack it. You'll see 2 directories: *backend* and *frontend*, which contain the code for the API and the web frontend, respectively.


## Front-end Installation

* Find your apache root directory. On RHEL-based operating systems, you can find it using:

        $> grep -i 'DocumentRoot' /etc/httpd/conf/httpd.conf
        DocumentRoot /var/www/

* Copy the istarter-web directory into your apache root and rename it if you need to (note: you will probably have to deviate from the apache conf.d template if you rename this too).

* Ensure that other users (namely the apache/httpd user) can read this directory and its files.

* Modify the following content in frontend/istarter-web/js/service.js. Make sure you have leading slashes on appPath and frontEndPath otherwise some of the routing will struggle.

        // Change to suit host server
        Config.appProtocol = "http://";
        Config.appHost = "<my_host>";
        Config.appPath = "/istarter";
        Config.frontEndPath = "/istarter";
        Config.apiPath = "/api/v1/";
        
* Modify the frontend/istarter-web/index.html, line 15 so that the tab page title is appropriately named:

        <title><make this your APPLICATION_NAME></title>

* Modify frontend/istarter-web/templates/top-menu.html, line 12 so that the logo at the top of the page is correct for your application. You'll see the i and deaworks are separated for styling through CSS.

        <a class="brand" href="#"><i class="icon-large icon-lightbulb"></i><div><span class="logo1">i</span><span class="logo2">deaWorks</span><span class="logo1">!</span></div></a>


* If you wish to leave it where it is and assuming that location is outside the Apache document root, you will need to tweak your apache config (ideaworks_web.conf) so that Apache can read that directory. 
This approach has the advantage that git pulls directly from an upstream repo will not then need to be moved out to the apache front end location. Here's an example:

        <Directory "/home/PTN/brantinr/webapps/ideaworks_test/ideaworks/frontend/istarter-web">
            Order allow,deny
            Allow from all
            Options FollowSymLinks
            AllowOverride None
        </Directory>
        


## Backend (API & Auth) Installation

*Identify a suitable location to host the django project (the code in /backend). You can run it out of your home directory if you want 
or /opt is sometimes a good bet depending on how your environment is setup. This will assume you're running it out of /opt.

* Copy the `ideaworks` directory to that location.

        $> tar -cf ideaworks.tar ideaworks && sudo cp ideaworks.tar /opt    
        $> cd /opt
        $> sudo tar -xf ideaworks.tar && sudo rm ideaworks.tar

* Ensure that apache can read and execute files in this directory.

* Ensure that apache can write to the /logs directory. 

        $> chmod 777 /ideaworks/logs

## Configuration

With the exception of the apache settings, all of the ideaworks settings are configured via the python django project.
When the API is up and running, it exposes a small read-only web API which the front-end reads for its settings. We've done
this to reduce the number of files that need editing during installation and configuration.

This section will walk you through configuring the web & api parts of ideaworks and then Apache.


### API Configuration

#### Django project settings

We use a main settings file (ideaworks/settings.py) which pulls additional settings from a local config file based
on a file-path key/value dictionary. This dictionary is in the ideaworks/settings.py file and it should point to a file in the config directory.

Let's setup a new local config file for your environment:

Open the django project settings file:

    $> vim ideaworks/settings.py

Add a new key:value to this dictionary:
    
    configs = {'/Users/bob/ideaworks/src/ideaworks'         : 'dev_bob',
               '/Users/bob/eclipseCode/istarter/ideaworks'  : 'dev_rich'}

For example:

    configs = {'/Users/bob/ideaworks/src/ideaworks'         : 'dev_bob',
               '/Users/rich/eclipseCode/istarter/ideaworks' : 'dev_rich',
            ***'/opt/ideaworks/ideaworks'            	    : 'ops_deployment'***}
               

When we fire up the server, the ideaworks/settings.py file will use the fact it knows it's own project path (`ROOT_PATH` in settings.py)
to identify which local config file to use. When it identifies that it needs to use ops_deployment.py (.py is assumed), it'll try to find that file in config/.

Next up then, create a file in config/ called ops_deployment.py and copy/paste the content from one of the other dev_* files into your new file.

Change the parameters in this file as you require. 
The `APPLICATION_NAME` is probably the most important one - if you don't want your instance to be called ideaworks, then you'll need to change the `APPLICATION_NAME`.
Note that changing `APPLICATION_NAME` will also change database names and other references to ideaworks, but changes will be consistent across the code/application.

Also - there is a hard-coded pointer to your domain, which you should change too. This only gets used in some of the auth pages, but its worth changing. In `settings.py` on line 202, change this:

    one.domain = 'localhost:8000'

to 

    one.domain = '<your host>'

If when you fire up the server, in the server logs you see *Not using pre-configured local settings file. Config file not found.*, django isn't finding your local config file.
Check your paths. When it does the lookup, it is not case sensitive.

#### Database file location and read/write permissions

* If using sqlite3, the project will attempt to write the database file to a dedicated folder for your user db(e.g. `/opt/ideaworks/user_db`). Your local config file determines 
 the name of this file, inheriting part of the file name from the `APPLICATION_NAME` parameter. If you want it to write to a different directory, 
 edit these lines in your config file (e.g. `/opt/ideaworks/config/ops_deployment.py`):
 
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
    
    
#### Logs


* You can set the directory into which this app will write log files using the `LOG_PATH` parameter in your local config file.
* Alternatively, don't set LOG_PATH and it'll default to the `logs` directory within the project structure. If you go down this route, consider setting a symlink from the local logs directory to your centralised server log directory (often `/var/log/ideaworks/`):

        $> cd /var/log
        $> sudo ln -s /opt/ideaworks/logs/ ideaworks
        # Check it...
        $> ll ideaworks
        lrwxrwxrwx. 1 root   root         20 Jun 12 05:09 ideaworks -> /opt/ideaworks/logs/

### Email

If you're **NOT** using the *ideaworks-no-email* branch, then this application will expect to be able to connect to an SMTP server. You'll need to provide a file in src/ideaworks/ideaworks/ called email_settings.py
in which you should drop your SMTP settings. Examples of the SMTP settings required are provided in the src/ideaworks/ideaworks/auth_settings.py file.

### Setup the Auth DB (Sqlite or pg)

* Navigate to the django manage.py file

* Get into your virtualenvironment (assuming you've install virtualenvwrapper too. if not, use activate)

        $> workon ideaworks

* Setup the database and db users

        $> python manage.py syncdb
    
* You should see the following. Then just follow the prompts. 

        Creating tables ...
        Creating table auth_permission
        Creating table auth_group_permissions
        Creating table auth_group
        Creating table auth_user_groups
        Creating table auth_user_user_permissions
        Creating table auth_user
        Creating table django_content_type
        Creating table django_session
        Creating table django_site
        Creating table tastypie_apiaccess
        Creating table tastypie_apikey
        Creating table tastytools_test
        Creating table django_admin_log
        Creating table registration_registrationprofile

        You just installed Django's auth system, which means you don't have any superusers defined.
        Would you like to create one now? (yes/no): 

* You might see the following error. I did, but it didn't cause any issues:

        ValueError: astimezone() cannot be applied to a naive datetime
        
* When you run syncdb from anything other than apache user the logs and db directories inherit the permissions of the user who ran that command. That can cause problems for apache accessing them, so
check the permissions of files that have just been created in logs/ and user_db/ and make sure apache can write to them.



### Setup the protective marking

* You may wish to set up a protective marking structure for your application instance. The protective marking structure allows the site owners to associate different levels of security with different
bits of information. We've done this to be in accordance with the Uk government security classification guide, but it may be overkill for many use cases. 

The front-end does not currently get its protective
marking data from the API (it gets it from data files stored within the front-end. You'll need to modify the files in /frontend/istarter-web/data/protective_marking for it to take effect in your instance of the app.

* When the front-end uses content served by the API, you'll need to run some data into the database. Here's what to do:-
** Modify the files in /backend/protective_marking_app/data accordingly (the existing examples should give you a feel for whats needed).
** In /backend/protective_marking_app/documents.py, uncomment the lines that point to your mongodb instance. They should be the same as in your local config file.
** Run /backend/protective_marking_app/data/_insert_data.py which will dump your PM data into the database.
** You can then hit it from /api/v1/classification, etc.  
 

### Setup the Site Content DB (mongo) 

* If your mongo database is running with authentication, then you'll need to create the relevant database and create a user on that database.

* The database name will need to be the same as the `APPLICATION_NAME` setting which you set in your local config file within the django app. Or modify the code in that local config file so that the dependency is dropped.

* Make a note of the Mongo username and password you've created and edit your local config file:

* **Comment these lines**

        MONGO_DATABASE_NAME = APPLICATION_NAME
        register_connection(alias='default',name=MONGO_DATABASE_NAME)

* **Uncomment these lines and set the parameters correctly**

        #MONGO_DB_PORT = < non local host db port >
        #MONGO_DB_HOST = < non local host >
        #MONGO_DB_USER = < non local host db user >
        #MONGO_DB_PASS = < non local host db password >
        register_connection(alias='default',name=MONGO_DATABASE_NAME, host=MONGO_DB_HOST, port=MONGO_DB_PORT, username=MONGO_DB_USER, password=MONGO_DB_PASS)

### Front-end Configuration

* The front-end is configured by setting parameters in your local config file (in config/). These are shared with the front end by a light-weight web API.

* Examples of front-end settings that can be changed in your local config file include `APPLICATION_NAME` and `SHOW_LATEST_IDEAS_COUNT` (the number of ideas to show in the latest ideas list).

TODO: This needs more work and needs more work on the front-end to pull in from the API.

### Apache Configuration

* Ensure Apache has access to the libraries needed for proxying.

        $> sudo vim /etc/httpd/conf/httpd.conf
    
* Uncomment the following lines if they're not already uncommented:
    
        LoadModule proxy_module modules/mod_proxy.so
	    LoadModule proxy_connect_module modules/mod_proxy_connect.so
	    LoadModule proxy_http_module modules/mod_proxy_http.so

* From `apache_conf` folder in the deployment tarball, copy the example apache conf files into your httpd/conf.d/ directory.

        $> sudo cp apache_conf/*.conf /etc/httpd/conf.d/

* Open the ideaworks-*api*.conf file for editing:

        $> vim /etc/httpd/conf.d/ideaworks-api.conf

* You will need to change the following lines to reflect your deployment environment:

        Alias /ideaworks_api/static/ <<full-path-to-the-static-directory-specified-in-django-settings-with-trailing-slash>>
        to...
        Alias /ideaworks_api/static/ /opt/ideaworks/static/
.
        <Directory <<full-path-to-the-static-directory-specified-in-django-settings-with-NO-trailing-slash>> >
        to...
        <Directory /opt/ideaworks/static>
.
        WSGIDaemonProcess <server-host>/ideaworks_api python-path=<full-path-to-django-project-level-directory>:<full-path-to-virtualenv-python-site-packages>
        to...
        WSGIDaemonProcess istarter.com/ideaworks_api python-path=/opt/ideaworks/:/home/ec2-user/venvs/ideaworks/lib/python2.6/site-packages>
        # Incidentally, I think this <server-host> is just a unique name within the apache setup, so it can probably be anything provided you're consistent.        
.
        WSGIScriptAlias /ideaworks_api <full-path-to-wsgi.py-file-within-your-project>
        to...
        WSGIScriptAlias /ideaworks_api /opt/ideaworks/ideaworks/wsgi.py
.
       <Directory <full-path-to-django-project-sub-directory>>
        to...
        <Directory /opt/ideaworks/ideaworks>
.
        WSGIProcessGroup <server-host>/ideaworks_api
        to...
        WSGIProcessGroup istarter.com/ideaworks_api


* Open the ideaworks-*web*.conf file for editing:

        $> vim /etc/httpd/conf.d/ideaworks-web.conf
    
* You will need to change all the proxy lines in this file to reflect the server host info. Here's one example:

        ProxyPass /ideaworks/api_docs/ <<server-host>>/ideaworks/api_docs/
        ProxyPassReverse /ideaworks/api_docs/ <<server-host>>/ideaworks/api_docs/
        to...
        ProxyPass /ideaworks/api_docs/ http://my_host.com/ideaworks/api_docs/
        ProxyPassReverse /ideaworks/api_docs/ http://my_host.com/ideaworks/api_docs/
        #TODO: There is probably a better way of referencing the server host than this. 
.
        Alias /<<instance_name>> /var/www/istarter-web/istarter
        to...
        Alias /istarter /var/www/istarter-web/istarter
        # TODO: The absolute path to istarter above will change at some point to ideaworks for consistency.
.
        <Directory <<full-path-to-apache-readable-location-containing-ideaworks-front-end-code>> >
        to...
        <Directory /var/www/istarter-web>
        
        
* In order for apache to pick up the changes to httpd.conf and your new files, you will need to restart (or possibly just reload you apache server):

        $> sudo service httpd restart (| reload)

   
## Did it all Work?

* To test the API, navigate to the directory containing the manage.py file and run:

        $> python manage.py test ideasapp auth_addin_app contentapp protective_marking_app
        
* To test the front-end and the whole platform, navigate to the URL you have specified in your apache config files.

## Known Issues

* If you get a ValueError: astimezone() cannot be applied to a naive datetime, add the following to your settings.py (or local config file):

        USE_TZ = True

* If you get a 500 response and your apache logs contain this error:

        ImportError: No moduled named django.core.wsgi

... then check your selinux settings and check that your selinux settings will remain after system reboot.

        $> getenforce
        
The short-term fix is to change selinux to permissive (rather than enforcing) as follows:

        $> setenforce 0
        
* If trying from outside the box and getting errors, check your firewall (iptables) settings.



## What to do on update

When it comes to updating the software, version control on your deployment server should help you ensure your deployment settings don't get over-written.
That said, this problem only exists where changes are made within a file (as opposed to a new file). A small amount of effort is needed to remove any config from
within files that would otherwise not change between deployments.

In the meantime, when you upgrade your deployment, do the following:

* Take a copy of your mongo database (site content):

        $> mongodump -d <name_of_your_db> -o /tmp/ideaworks_upgrade/my_db_dump
    
* Take a copy of your sqlite database (users):

        $> cp user_db/<APPLICATION_NAME>.sql.db /tmp/ideaworks_upgrade/my_sql_dump
    
* Copy your local config file

        $> cp config/dev_config.py /tmp/ideaworks_upgrade/
    
* Copy Apache config files

        $> cp /etc/httpd/conf.d/istarter* /tmp/ideaworks_upgrade
    
* Copy the main settings file (because I've left a configurable parameter in there)

        $> cp ideaworks/settings.py /tmp/ideaworks_upgrade/
    
   

    





     

(c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 

Author: Rich Brantingham

