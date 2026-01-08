from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin
from RattelBackend.cache import drf_cached_response, invalidate_cache
from .models import Footer, SiteNavbar
from .serializers import FooterSerializer, SiteNavbarSerializer
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
    
    @method_decorator(
        drf_cached_response(
            ttl=1800,
            cache_prefix='footer',
            user_aware=False,
            response_codes=[200],
            cache_headers=False,
        )
    )
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
                status.HTTP_200_OK,
                success=True,
                footer=serializer.data,
                message='Successful'
            )
        
        except Exception as e:
            # Log unexpected errors during retrieval or serialization
            logger.error(f'Something went wrong while trying to get/serializer footer: {e}')
            
            # Return generic error response
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message='Something went wrong while trying to get footer.'
            )


class NavbarView(APIView, ResponseBuilderMixin):
    """
    Public API endpoint for retrieving navbar configuration data.
    
    Provides a read-only GET endpoint that returns the current navbar instance,
    typically used for rendering global site navigation including menu items,
    links, and navigation structure.
    
    Permissions:
        - AllowAny: No authentication required
    
    Throttling:
        - Uses the `main-throttle` -> 300/min
    
    Caching:
        - TTL: 30 minutes (1800 seconds)
        - Cache prefix: 'navbar'
        - User-agnostic caching
    """
    
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'  # 300/min
    
    @method_decorator(
        drf_cached_response(
            ttl=1800,
            cache_prefix='navbar',
            user_aware=False,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        """
        Retrieve the active navbar configuration.
        
        Fetches the singleton SiteNavbar instance, serializes it, and returns the
        structured navbar data for client-side consumption.
        
        Returns:
            200 OK:
                - success=True
                - navbar: Serialized navbar data
                - message: 'Successful'
            
            500 INTERNAL SERVER ERROR:
                - success=False
                - message: Generic failure message when navbar retrieval or
                  serialization fails
        """
        try:
            # Retrieve the singleton navbar instance
            navbar = SiteNavbar.get_instance()
            
            # Serialize navbar data with request context
            serializer = SiteNavbarSerializer(navbar, context={'request': request})
            
            # Return successful response
            return self.build_response(
                status.HTTP_200_OK,
                success=True,
                message='Successful',
                navbar=serializer.data,
            )
        except Exception as e:
            # Log unexpected errors during retrieval or serialization
            logger.error(f'Something went wrong while trying to get navbar: {e}')
            
            # Return generic error response
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                message='Something went wrong while trying to fetch/serialize navbar.'
            )
