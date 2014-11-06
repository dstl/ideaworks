
# (c) Crown Copyright 2014 Defence Science and Technology Laboratory UK 
# Author: Rich Brantingham

from tastypie.authorization import Authorization

class StatusAuthorization(Authorization):

    def read_list(self, object_list, bundle):
        """ Public - all read, otherwise just creator and staff """

        allowed = []
        
        # No type of status provided
        if not bundle.request.GET.get('status', None) and not bundle.request.GET.get('status__in', None):
            # Just return the published results
            for obj in object_list:
                if obj.status == 'published': 
                    allowed.append(obj.id)

        # Status is provided so make sure that the objects are either 'published' or 'draft' and belong
        else:
            if bundle.request.user.is_superuser == True or bundle.request.user.is_staff == True:
                allowed = [obj.id for obj in object_list]
            else:
                for obj in object_list:
                    # The object is published so add it
                    if obj.status == 'published':
                        allowed.append(obj.id)
                    # The object is authored by this user so add it
                    elif str(obj.user) == str(bundle.request.user):
                        allowed.append(obj.id)

        return object_list.filter(id__in=allowed)

        
    def read_detail(self, object_list, bundle):

        allowed = True
        obj = object_list[0]
        
        # No type of status provided
        if not bundle.request.GET.get('status', None) and not bundle.request.GET.get('status__in', None):
            if obj.status == 'published': 
                allowed = True

        # Status is provided so make sure the object is either 'published' or 'draft' and belong
        else:
            if bundle.request.user.is_superuser == True or bundle.request.user.is_staff == True:
                allowed = True
            else:
                # The object is published so add it
                if obj.status == 'published':
                    allowed = True
                # The object is authored by this user so add it
                elif str(obj.user) == str(bundle.request.user):
                    allowed = True

        return allowed