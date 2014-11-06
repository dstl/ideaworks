
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

from django import forms
from django.utils.translation import ugettext_lazy as _
from registration_email.forms import EmailRegistrationForm

class RegistrationEmailAndFormTermsOfService(EmailRegistrationForm):
    """
    Subclass of ``EmailRegistrationForm`` which adds:-
    1. A required checkbox for agreeing to a site's Terms of Service.
    2. First name
    3. Last name
    4. Organisation
    5. Team
    
    """
    tos = forms.BooleanField(widget=forms.CheckboxInput,
                             label=_(u'I have read and agree to the Terms of Service'),
                             help_text="In order to use this service you are required to read and agree to the terms of service.",
                             error_messages={'required': _("You must agree to the terms to register")})
    
    first_name = forms.CharField(widget=forms.TextInput(),
                             label=_(u'First name'),
                             help_text="Please enter your first name.",
                             required=False)
    
    last_name = forms.CharField(widget=forms.TextInput(),
                             label=_('Last name'),
                             help_text="Please enter your last name.",
                             required=False)
    
    organisation = forms.CharField(widget=forms.TextInput(),
                             label=_('Organisation'),
                             help_text="Please enter the name of your organisation.",
                             required=False)

    team = forms.CharField(widget=forms.TextInput(),
                             label=_('Team'),
                             help_text="Please enter the name of your team.",
                             required=False)
