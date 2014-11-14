
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.utils.translation import ugettext as _

from django.shortcuts import resolve_url
from django.views.decorators.debug import sensitive_post_parameters
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_protect
from django.contrib.auth import REDIRECT_FIELD_NAME, login as auth_login, logout as auth_logout

from django.contrib.sites.models import get_current_site
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse

# Access the django project settings
from django.conf import settings

try:
    from urllib import parse as urllib_parse
except ImportError:     # Python 2
    import urllib as urllib_parse
    import urlparse
    urllib_parse.urlparse = urlparse.urlparse

def get_auth_roles(current_user):
    """ Gets the roles associated with the current user
        for the front-end to use. """

    roles = []
    if current_user.is_superuser == True:
        roles.append('super')
    if current_user.is_staff == True:
        roles.append('staff')
    return ','.join(roles)

#------------------------------------------------------------------------------------  

def is_safe_url(url, host=None):
    """
    Return ``True`` if the url is a safe redirection (i.e. it doesn't point to
    a different host).

    Always returns ``False`` on an empty url.
    
    **** This is an override of the django.utils.http is_safe_url ****
    
    """
    
    for safe_url in settings.SAFE_REDIRECTS:
        if url.startswith(safe_url):
            return True
    
    if not url or url == '':
        return False
    
    netloc = urllib_parse.urlparse(url)[1]
    return not netloc or netloc == host

#------------------------------------------------------------------------------------

def terms_of_service(request):
    """
    Renders the terms of service.
    """
    
    c = {"classification"  : "PERSONAL" }
    return render(request, "registration/description_snippet.html", c)

#------------------------------------------------------------------------------------

def activation_success(request):
    """
    What happens after registration/activation
    """
    
    c = {}
    return render(request, "registration/activate.html", c)

#----------------------------------------------------------------------
@login_required(login_url=settings.LOGIN_URL)
def checkLoginRequired(request):
    """
    Just checks that login was successful
    """
    
    return HttpResponse('Only access this if you are logged in. User authenticated: %s' %request.user.is_authenticated())

#----------------------------------------------------------------------
def checkLoginNotRequired(request):
    """
    Just checks that login was successful
    """
    
    return HttpResponse('Anyone can access this page. User authenticated: %s' %request.user.is_authenticated())

#----------------------------------------------------------------------
@sensitive_post_parameters()
@csrf_protect
@never_cache
def login_remember_me_apikey_response(request, template_name='registration/login.html',
                                      redirect_field_name=REDIRECT_FIELD_NAME,
                                      authentication_form=None, current_app=None,
                                      extra_context=None):

    """ Extending login to return the user id and the API key.
        This allows the FE to pick these up for all future requests (needed for API calls)."""
    
    redirect_to = request.REQUEST.get(redirect_field_name, settings.LOGIN_REDIRECT_URL)
    
    if request.method == "POST":
        # Incorporated remember me element of the login
        if not request.POST.get('remember_me', None):
            request.session.set_expiry(0)
        
        form = authentication_form(data=request.POST)
        
        if form.is_valid():
            if not is_safe_url(url=redirect_to, host=request.get_host()):
                redirect_to = resolve_url(settings.LOGIN_REDIRECT_URL)

            # Okay, security check complete. Log the user in.
            auth_login(request, form.get_user())

            if request.session.test_cookie_worked():
                request.session.delete_test_cookie()

            response = HttpResponseRedirect(redirect_to)

            # Access the user information to respond with
            current_user = form.get_user()
            if current_user and current_user.api_key:
                api_key = current_user.api_key.key
            else:
                api_key = 'no api key set for current user.'
                        
            response.set_cookie('user_id', current_user)
            response.set_cookie('api_key', api_key)
            response.set_cookie('user_name', '%s %s'%(current_user.first_name.title(), current_user.last_name.title()))
            response.set_cookie('user_email', current_user.email)
            response.set_cookie('user_roles', get_auth_roles(current_user))
            response.set_cookie('user_active', str(current_user.is_active).lower())
            return response
    
    else:
        form = authentication_form(request)

    request.session.set_test_cookie()

    current_site = get_current_site(request)

    context = {
        'form': form,
        redirect_field_name: redirect_to,
        'site': current_site,
        'site_name': current_site.name,
    }
    
    if extra_context is not None:
        context.update(extra_context)
    
    # Get the response object (although it is a template response - not rendered until after middleware
    return TemplateResponse(request, template_name, context, current_app=current_app)


#----------------------------------------------------------------------
def logout(request, next_page=None,
           template_name='registration/logged_out.html',
           redirect_field_name=REDIRECT_FIELD_NAME,
           current_app=None, extra_context=None):
    """
    Logs out the user and displays 'You are logged out' message.
    """
    auth_logout(request)

    if redirect_field_name in request.REQUEST:
        next_page = request.REQUEST[redirect_field_name]
        # Security check -- don't allow redirection to a different host.
        if not is_safe_url(url=next_page, host=request.get_host()):
            next_page = resolve_url(settings.LOGIN_REDIRECT_URL)

    if next_page:
        # Redirect to this page until the session has been cleared.
        return HttpResponseRedirect(next_page)

    current_site = get_current_site(request)
    context = {
        'site': current_site,
        'site_name': current_site.name,
        'title': _('Logged out')
    }
    if extra_context is not None:
        context.update(extra_context)
    return TemplateResponse(request, template_name, context,
        current_app=current_app)

#----------------------------------------------------------------------
def password_reset(request, template_name='registration/password_reset_info.html', extra_context=None):
    """
    Provides user with information about how to get their password reset.
    """
    
    # Retrieve the admin details from settings
    try: admin_name = settings.ADMINS[0][0]
    except: admin_name = None
    try: admin_email = settings.ADMINS[0][1]
    except: admin_email = None
    try: admin_phone = settings.ADMINS[0][2]
    except: admin_phone = None
    try: admin_url = settings.ADMINS[0][3]
    except: admin_url = None
        
    
    current_site = get_current_site(request)
    context = {
        'site': current_site,
        'site_name': current_site.name,
        'admin_name':  admin_name,
        'admin_email': admin_email,
        'admin_phone': admin_phone,
        'admin_url' :  admin_url,
        
        'title': _('Password Reset Information')
    }
    
    if extra_context is not None:
        context.update(extra_context)
    
    return TemplateResponse(request, template_name, context)
