from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin
from .models import Footer
from .serializers import FooterSerializer
from rest_framework import status
import logging


logger = logging.getLogger(__name__)

class FooterView(APIView, ResponseBuilderMixin):
    """
    Public API endpoint for retrieving footer configuration data.
    
    Provides a read-only GET endpoint that returns the current footer instance,
    typically used for rendering global site footer content such as links,
    copyright text, and branding elements.
    
    Permissions:
        - AllowAny: No authentication required
    
    Throttling:
        - Uses the `main-throttle` -> 300/min
    """
    
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'
    
    def get(self, request):
        """
        Retrieve the active footer configuration.
        
        Fetches the singleton Footer instance, serializes it, and returns the
        structured footer data for client-side consumption.
        
        Returns:
            200 OK:
                - success=True
                - footer: Serialized footer data
                - message: 'Successful'
            
            500 BAD REQUEST:
                - success=False
                - message: Generic failure message when footer retrieval or
                  serialization fails
        """
        try:
            # Retrieve the singleton footer instance
            footer = Footer.get_instance()
            
            # Serialize footer data with request context
            serializer = FooterSerializer(footer, context={'request': request})
            
            # Return successful response
            return self.build_response(
                status=status.HTTP_200_OK,
                success=True,
                footer=serializer.data,
                message='Successful'
            )
        
        except Exception as e:
            # Log unexpected errors during retrieval or serialization
            logger.error(f'Something went wrong while trying to get/serializer footer: {e}')
            
            # Return generic error response
            return self.build_response(
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message='Something went wrong while trying to get footer.'
            )
