
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

import re
from tastypie.authorization import Authorization
from tastypie.exceptions import Unauthorized
import contentapp.documents as documents

def all_read_check_list(object_list, bundle):
    
    if bundle.request.method == 'GET':
        return object_list

def all_read_check_detail(object_list, bundle):
    
    if bundle.request.method == 'GET':
        return True
    
def staff_superuser_check_list(object_list, bundle):
    
    if bundle.request.user.is_staff == True:
        return object_list
    elif bundle.request.user.is_superuser == True:
        return object_list
    else:
        raise Unauthorized("You are not authorized to conduct this action.") 

def staff_superuser_check_detail(object_list, bundle):
    
    if bundle.request.user.is_staff == True:
        return True
    elif bundle.request.user.is_superuser == True:
        return True
    else:
        raise Unauthorized("You are not authorized to conduct this action.") 

class StaffSuperAuthorization(Authorization):

    def staff_superuser_check_list(self, object_list, bundle):
    
        if bundle.request.user.is_staff == True:
            return object_list
        elif bundle.request.user.is_superuser == True:
            return object_list
        else:
            raise Unauthorized("You are not authorized to conduct this action.") 

    def staff_superuser_check_detail(self, object_list, bundle):
        
        if bundle.request.user.is_staff == True:
            return True
        elif bundle.request.user.is_superuser == True:
            return True
        else:
            raise Unauthorized("You are not authorized to conduct this action.")

    def create_list(self, object_list, bundle):
        return self.staff_superuser_check_list(object_list, bundle)
        
    def create_detail(self, object_list, bundle):
        return self.staff_superuser_check_detail(object_list, bundle)

    def delete_list(self, object_list, bundle):
        return self.staff_superuser_check_list(object_list, bundle)
        
    def delete_detail(self, object_list, bundle):
        return self.staff_superuser_check_detail(object_list, bundle)

    def update_list(self, object_list, bundle):
        return self.staff_superuser_check_list(object_list, bundle)
        
    def update_detail(self, object_list, bundle):
        return self.staff_superuser_check_detail(object_list, bundle)


class PrivilegedAndSubmitterOnly(Authorization):
    """
    Private Feedback:
    -----------------
    the user associated with the object can create, update, delete and read
    staff/super can CRUD
    User can comment on it
    Staff/super can comment on it.
    
    Public Feedback:
    ----------------
    User can CRUD
    Staff/super can CRUD
    All can read
    All can comment
    
    Note - when overriding update_ you'll need to also override the 
    obj_update function and derive the bundle.obj.pk which the intermediate
    functions require. Specifically, tastypie_mongoengine.resources.obj_update
    uses bundle.obj.pk to find the object to update.
    
    
    """
    
    def read_list(self, object_list, bundle):
        """ Public - all read, otherwise just creator and staff """

        allowed = []

        for obj in object_list:
            
            if obj['public'] == True:
                allowed.append(obj)
            else:
                if str(obj.user) == str(bundle.request.user):
                    allowed.append(obj)
                elif bundle.request.user.is_staff == True or bundle.request.user.is_superuser == True:
                    allowed.append(obj)
        return allowed

    def read_detail(self, object_list, bundle):

        allowed = False
        
        # If there's no objects, the let it be read
        if len(object_list) == 0:
            return True
        else:
            obj = object_list[0]

        if obj['public'] == True:
            allowed = True
        else:
            if str(obj.user) == str(bundle.request.user):
                allowed = True
            elif bundle.request.user.is_staff == True or bundle.request.user.is_superuser == True:
                allowed = True
        
        return allowed
        
    def update_detail(self, object_list, bundle):

        if str(object_list[0].user) == str(bundle.request.user):
            return True
        else:
            return staff_superuser_check_detail(object_list, bundle)
        
    def delete_list(self, object_list, bundle):
        
        if str(object_list[0].user) == str(bundle.request.user):
            return object_list
        else:
            return staff_superuser_check_list(object_list, bundle)
        
    def delete_detail(self, object_list, bundle):
        
        if str(object_list[0].user) == str(bundle.request.user):
            return True
        else:
            return staff_superuser_check_detail(object_list, bundle)

    def create_detail(self, object_list, bundle):
        
        allowed = False
        
        # Regular expression to match feedback id with comments
        # Look for a 24 length alph numeric string preceding 'comments' in a path structure and call the output variable 'feedback_id'
        regExp = re.compile('.*/(?P<feedback_id>[a-zA-Z0-9]{24})/comments/.*')
        m = re.match(regExp, bundle.request.path)
        # It's a call to comments
        if m:
            ids = m.groupdict()
            feedback_obj = documents.Feedback.objects.get(id=ids['feedback_id'])

        # It's just a straight call to the feedback/ end point
        else:
            allowed = True
                
        return allowed
        

class PrivilegedAndSubmitterOnlyComments(Authorization):
    """ For private feedback, only author and staff/super can add comments
        For public feedback, any authenticated user can comment."""

    """
    At time of writing (May 2014), the intended behaviour was:
    1. comments on private feedback only allowed by super/staff and the author of the feedback - generate discussion.
    2. comments on public feedback allowed by any authenticated user. 
    
    I can't get this work, i think because there is a bug in django-tastypie-mongoengine
    that means authorization isn't properly checked for embedded documents.
    
    Here's the main issue described and open:
    
    https://github.com/wlanslovenija/django-tastypie-mongoengine/issues/70
    
    As such, the behaviour at the moment (with tests that pass) is that all
    authenticated users (irrespective of staff/superuser/author) can make comments
    on private feedback.
    
    """

    def read_list(self, object_list, bundle):
        """ Public - all read, otherwise just creator and staff """

        allowed = False

        # Regular expression to match feedback id with comments
        regExp = re.compile('.*/(?P<feedback_id>[a-zA-Z0-9]{24})/comments/.*')
        m = re.match(regExp, bundle.request.path).groupdict()
        
        # Get the feedback object
        feedback_obj = documents.Feedback.objects.get(id=m['feedback_id'])

        # If the parent feedback object is public, then return these results
        if feedback_obj.public == True:
            allowed = True
        else:
            if str(feedback_obj.user) == str(bundle.request.user):
                allowed = True
            
            # Is the request user staff or superuser?
            elif bundle.request.user.is_staff == True or bundle.request.user.is_superuser == True:
                allowed = True

        # If the parent feedback object is public, then return these results        
        if allowed == True:
            return object_list
        else:
            return []

    def read_detail(self, object_list, bundle):
        
        allowed = False
        
        # Regular expression to match feedback id with comments
        regExp = re.compile('.*/(?P<feedback_id>[a-zA-Z0-9]{24})/comments/.*')
        m = re.match(regExp, bundle.request.path).groupdict()
        
        # Get the feedback object
        feedback_obj = documents.Feedback.objects.get(id=m['feedback_id'])

        # If the parent feedback object is public, then return these results
        if feedback_obj.public == True:
            allowed = True
        else:
            if str(feedback_obj.user) == str(bundle.request.user):
                allowed = True
            
            # Is the request user staff or superuser?
            elif bundle.request.user.is_staff == True or bundle.request.user.is_superuser == True:
                allowed = True

        # If the parent feedback object is public, then return these results        
        return allowed
    
    """
    
    #TODO: This commented because of the bug with auth on nested documents.
    
    def create_detail(self, object_list, bundle):
        
        allowed = False
        
        # Regular expression to match feedback id with comments
        regExp = re.compile('.*/(?P<feedback_id>[a-zA-Z0-9]{24})/comments/.*')
        m = re.match(regExp, bundle.request.path).groupdict()
        
        # Get the feedback object
        feedback_obj = documents.Feedback.objects.get(id=m['feedback_id'])
        print 'PUblic ', feedback_obj.public
        
        # If the parent feedback object is public, then return these results
        if feedback_obj.public == True:
            print 'it is public'
            allowed = True
        else:
            print 'it is not public'
            if str(feedback_obj.user) == str(bundle.request.user):
                allowed = True
            
            # Is the request user staff or superuser?
            elif bundle.request.user.is_staff == True or bundle.request.user.is_superuser == True:
                allowed = True
            
            print 'from user check tests', allowed

        print 'final allowed', allowed
        # If the parent feedback object is public, then return these results        
        return allowed
    """