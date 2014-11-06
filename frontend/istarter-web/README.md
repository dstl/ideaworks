IdeaWorks Web Front End
======================

Installation
-------------
Clone repository to a local drive, these instructions assume

c:/www/ideaworks-web/



Setting up Apache to use mod proxy for Cross-Domain XMLHttpRequest Calls
========================================================================
As the API and the Web UI run on different servers (or ports) they fall foul of the same-origin policy, so a reverse proxy must be setup to allow the application to use relative paths for the Ajax requests.


Local Development Setup
-----------------------
**This is for local testing on a Windows PC. Change paths for Mac/Linux installations**

Un-comment proxy LoadModule lines in C:\[your Apache installation path]\Apache2.2\conf\http.conf

    LoadModule proxy_module modules/mod_proxy.so
    LoadModule proxy_connect_module modules/mod_proxy_connect.so
    LoadModule proxy_http_module modules/mod_proxy_http.so


Un-comment `Include conf/extra/httpd-vhosts.conf` line in http.conf

Edit C:\[your Apache installation path]\Apache2.2\conf\extra\httpd-vhosts.conf

    <VirtualHost *:80>
    AllowEncodedSlashes On
    ServerAdmin test@localhost
    ServerName ideaworks
    ServerAlias 127.0.0.1
    DocumentRoot "c:/www/ideaworks-web/"

    ProxyPass /api/ http://localhost:8000/api/
    ProxyPassReverse /api/ http://localhost:8000/api/
    </VirtualHost>


In your hosts file (Windows - C:\Windows\System32\drivers\etc\hosts , Mac - /private/etc/hosts) add the following DNS mapping

    127.0.0.1	ideaworks

Restart your Apache server

Start up the ideaworks API on port 8000 - $python manage.py runserver:0.0.0.0:8000

You should now be able to navigate to 

http://ideaworks 

to open the web interface and 

http://ideaworks/api

to access the API 
