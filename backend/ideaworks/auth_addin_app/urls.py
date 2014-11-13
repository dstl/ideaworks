
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

from django.conf.urls import patterns, include, url
from django.views.generic.base import TemplateView

# Access the model that defines what our registration profile will look like in the db
from auth_addin_app.models import AuthCustomisedRegistrationView
# Access the form that will define what the form looks like online
from auth_addin_app.forms import RegistrationEmailAndFormTermsOfService
# Form for email-based authentication
from registration_email.forms import EmailAuthenticationForm
# Remember me login form also from registration email
from auth_addin_app.views import login_remember_me_apikey_response, logout, password_reset

# Access the django project settings for a default URL
from django.conf import settings

#from registration_email.forms import EmailRegistrationForm
urlpatterns = patterns('',
    
    # Overriding registration_email register url
    url(r'^accounts/register/$',
        AuthCustomisedRegistrationView.as_view(
            form_class=RegistrationEmailAndFormTermsOfService,
            get_success_url=getattr(
                settings, 'REGISTRATION_EMAIL_REGISTER_SUCCESS_URL',
                lambda request, user: '/'),
        ),
        name='registration_register'),

   url(r'^accounts/register/complete/$',
       TemplateView.as_view(template_name='registration/registration_complete.html'),
       name='registration_complete'),
    
    # Overriding Login so that we can put user id and API key into the response
    url(
        r'^accounts/login/$',
        login_remember_me_apikey_response,
        {'template_name': 'registration/login.html',
         'authentication_form': EmailAuthenticationForm, },
        name='auth_login',
    ),

    # Overriding Login so that we can put user id and API key into the response
    url(
        r'^accounts/logout/$',
        logout,
        {'template_name': 'registration/logout.html'},
        name='auth_logout',
    ),

    url(r'^accounts/password/reset/$',
        password_reset,
        name='auth_password_reset'),

    # Email-based auth
    url(r'^accounts/', include('registration_email.backends.simple.urls')),

    # Pointer to terms of service
    url(r'^tos/', 'auth_addin_app.views.terms_of_service', name='term_of_service'),

    # 2 simple views that allow you to check whether login/authentication has been successful
    url(r'^check_login_required/$',     'auth_addin_app.views.checkLoginRequired',    name='check_login_required'),
    url(r'^check_login_not_required/$', 'auth_addin_app.views.checkLoginNotRequired', name='check_login_not_required'),

)

from django.contrib.staticfiles.urls import staticfiles_urlpatterns
urlpatterns += staticfiles_urlpatterns()