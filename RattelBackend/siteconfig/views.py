from typing import Optional, Any, Dict
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin
from RattelBackend.cache import drf_cached_response, invalidate_cache
from .models import Footer, SiteNavbar, MainPage
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
        - Uses the `main-throttle` -> 500/min
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
        - Uses the `main-throttle` -> 500/min
    
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

class MainPageView(APIView, GetDataMixin, ResponseBuilderMixin):
    """
    Public API endpoint for retrieving main page section data.

    Supports partial or full page loads by accepting a `section` query parameter.
    Each section maps directly to a property on the MainPage singleton, allowing
    the frontend to fetch only what it needs.

    Permissions:
        - AllowAny: No authentication required

    Throttling:
        - Uses the `main-throttle` scope -> 500/min

    Caching:
        - TTL: 30 minutes (1800 seconds)
        - Cache prefix: 'mainpage'
        - User-agnostic caching

    Valid Sections:
        - full_page:          All sections combined
        - landing:            Hero area (title, video, image, CTA)
        - stats:              Four statistics blocks
        - advertisement:      Ad banner content and link
        - dual_choices:            Dual choice section titles, descriptions and images
        - user_experience:    Testimonials and top users
        - top_teachers: Top selected teachers
        - imaged_links: Imaged button links with icon
        - courses_demo: Courses Demo video
        - information_boxes: Information boxes with HTML content
    """

    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'
    VALID_SECTIONS = (
        'full_page', 'landing', 'stats',
        'advertisement', 'dual_choices', 'user_experience',
        'top_teachers', 'imaged_links', 'courses_demo',
        'information_boxes'
    )

    def validate_target_section(self, section: str) -> bool:
        """
        Validate that the requested section is a recognized page section.

        Args:
            section: The section name to validate.

        Returns:
            True if the section is in VALID_SECTIONS, False otherwise.
        """
        return section in self.VALID_SECTIONS

    def get_section(self, section: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve data for a specific section or the full page from the MainPage singleton.

        For a specific section, fetches the corresponding property directly via getattr.
        For 'full_page', iterates over all valid sections and assembles a combined dict.

        Args:
            section: The section name to fetch. Use 'full_page' to retrieve all sections.

        Returns:
            A dict containing the section data, or None if retrieval fails.

        Example:
            >>> self.get_section('landing')
            {'landing': {'landing_title': '...', ...}}

            >>> self.get_section('full_page')
            {'landing': {...}, 'stats': {...}, ...}
        """
        try:
            mainpage = MainPage.get_instance()
            if section != 'full_page':
                logger.info(f'Fetching {section}')
                return {section: getattr(mainpage, section)}
            logger.info('Starting a full page load.')
            structure = {section: dict()}
            data = structure[section]
            for sec in self.VALID_SECTIONS:
                if sec == 'full_page':
                    continue
                data[sec] = getattr(mainpage, sec)
            return data
        except AttributeError as e:
            logger.error(f'Failed to load main page data: {e}')
            return None

    @method_decorator(
        drf_cached_response(
            ttl=1800,
            cache_prefix='mainpage',
            user_aware=False,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        """
        Retrieve main page data for a given section.

        Accepts a `section` query parameter to determine which part of the main page
        to return. Validates the section name before fetching, and returns the
        corresponding data from the MainPage singleton.

        Query Params:
            section (str): The page section to retrieve. Must be one of VALID_SECTIONS.

        Returns:
            200 OK:
                - success=True
                - message: 'Successful'
                - mainpage: Dict containing the requested section data

            400 BAD REQUEST:
                - success=False
                - error: -1
                - message: Validation error detail (missing or invalid section)

            500 INTERNAL SERVER ERROR:
                - success=False
                - error: -2
                - message: Generic failure message when section data cannot be fetched
        """
        # Validate the `section` query param against VALID_SECTIONS
        success, result = self.get_data(request, ('section', self.validate_target_section))
        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result
            )

        # Fetch the requested section from the singleton
        data = self.get_section(result['section'])
        if not data:
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-2,
                message='Something went wrong while trying to fetch the section.'
            )

        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            mainpage=data
        )
