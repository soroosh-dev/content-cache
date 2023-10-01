'''
API endpoints for account app are defined here.
'''
from django.contrib.auth import get_user_model
from rest_framework import status, authentication
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import UserSerializer
from .permissions import UnauthenticatedForPostAuthenticatedForOther

@api_view(['POST'])
@throttle_classes([AnonRateThrottle])
def register(request):
    '''
    API endpoint responsible for registering new users via username, password
    and email (optional).
    '''
    if request.user.is_authenticated:
        return Response(
            {
                'errors': ['You can not access this endpoint as an authenticated user.',],
            },
            status=status.HTTP_403_FORBIDDEN
        )
    serializer = UserSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class AccountManager(APIView):
    '''
    Implements API endpoints for managing customer accounts.
    '''
    authentication_classes = [
        authentication.TokenAuthentication,
        authentication.SessionAuthentication]
    permission_classes = [UnauthenticatedForPostAuthenticatedForOther,]
    throttle_classes = [UserRateThrottle, AnonRateThrottle]

    def get(self, request):
        '''
        Show user data with GET method.
        '''
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def post(self, request):
        '''
        Responsible for login operation.
        '''
        if 'username' not in request.data.keys() or 'password' not in request.data.keys():
            return Response(
                {'errors': ['Credentials are not provided.',]},
                status=status.HTTP_400_BAD_REQUEST
                )
        user_model = get_user_model()
        try:
            user = user_model.objects.get(username=request.data['username'])
        except user_model.DoesNotExist:
            return Response(
                {"errors": ["Provided credentials are invalid",]},
                status=status.HTTP_401_UNAUTHORIZED
                )

        if user.check_password(request.data['password']):
            serializer = UserSerializer(user)
            return Response(serializer.data)
        return Response(
                    {"errors": ["Provided credentials are invalid.",]},
                    status=status.HTTP_401_UNAUTHORIZED
                    )

    def put(self, request):
        '''
        API endpoint for updating user info (email or password).
        '''
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        '''
        API endpoint for deleting a user.
        '''
        # TODO first remove user files then remove user itself.
        return Response({"message": "A DELETE request", "user": str(request.user), "data": request.data})
