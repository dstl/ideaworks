
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

"""
Linking the models into the django admin.
"""

from django.contrib.auth.admin import UserAdmin
from django.contrib.auth.models import User
from django.contrib import admin

from tastypie.admin import ApiKeyInline
from tastypie.models import ApiAccess, ApiKey

try:
    admin.site.register(ApiKey)
    admin.site.register(ApiAccess)
except:
    pass

class UserModelAdmin(UserAdmin):
    inlines = UserAdmin.inlines + [ApiKeyInline]

admin.site.unregister(User)
try:
    admin.site.register(User,UserModelAdmin)
except:
    pass