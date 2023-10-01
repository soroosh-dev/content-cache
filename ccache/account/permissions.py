'''
Permission classes for account app are defined here.
'''
from rest_framework import permissions

class UnauthenticatedForPostAuthenticatedForOther(permissions.BasePermission):
    '''
    A permission class to restrict access with POST method for authenticated users and 
    allow access via other methods only to authenticated users.
    '''

    def has_permission(self, request, view):
        '''
        This function enforces permission policy.
        '''
        #ALLOW_ANYWAY = ["HEAD", "OPTION"]
        allow_authenticated = ["GET", "PUT", "DELETE"]
        #ALLOW_UNAUTHENTICATED = ["POST"]

        if (request.user.is_authenticated and request.method == 'POST') or \
            (not request.user.is_authenticated and request.method in allow_authenticated):
            return False
        return True
