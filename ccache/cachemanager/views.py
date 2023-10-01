'''
These views implement API endpoints for cache manager
'''
import io
from django.http import FileResponse
from rest_framework import permissions
from rest_framework import status
from rest_framework import authentication
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.views import APIView
from rest_framework.decorators import \
    api_view, permission_classes, throttle_classes
from .cachelib import CacheFacade

class Storage(APIView):
    '''
    API endpionts for adding a file to cache(via POST) 
    and checking files cached by a user (via GET).
    '''
    authentication_classes = [authentication.TokenAuthentication, authentication.SessionAuthentication]
    permission_classes = [permissions.IsAuthenticated]
    throttle_classes = [UserRateThrottle]
    parser_classes = [FormParser, MultiPartParser]

    def post(self, request):
        '''
        Add uploaded file to cache.
        '''
        if 'file' in request.FILES.keys():
            uploaded_file = request.FILES['file']
        else:
            return Response(
                {"errors": ["file field is required"],},
                status=status.HTTP_400_BAD_REQUEST
                )
        minify = 'minify' in request.data.keys() and request.data['minify'] == "true"
        convert = 'convert' in request.data.keys() and request.data['convert'] == "true"
        cache = CacheFacade()
        store_result = cache.store_file(
            uploaded_file, owner=request.user, convert=convert, minify=minify
            )
        if store_result['success']:
            return Response(store_result['file_info'])
        return Response({"errors": store_result['errors']}, status=status.HTTP_400_BAD_REQUEST)

    def get(self, request):
        '''
        Return a list of all cached files by the user.
        '''
        cache = CacheFacade()
        return Response(cache.list_files(request.user))

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
@throttle_classes([UserRateThrottle,])
def get_saved_file(request, filename):
    '''
    Return cached file.
    '''
    cache = CacheFacade()
    file_content = cache.retrieve_file(filename, request.user)
    if file_content:
        return FileResponse(io.BytesIO(file_content), filename=filename)
    else:
        return Response({}, status=status.HTTP_404_NOT_FOUND)
