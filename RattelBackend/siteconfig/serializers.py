from rest_framework.serializers import ModelSerializer
from .models import Footer, FooterLinkColumn, FooterColumnLink, FooterSocialMedia, SocialMediaLink, Link
import logging


logger = logging.getLogger(__name__)


class LinkSerializer(ModelSerializer):
    """
    Serializes reusable Link objects.
    
    Input: Link model instance
    Output: {name: str, url: str}
    """
    class Meta:
        model = Link
        fields = ('name', 'url')


class SocialMediaLinkSerializer(ModelSerializer):
    """
    Serializes social media platform links.
    
    Input: SocialMediaLink model instance
    Output: {platform: str, url: str}
    """
    class Meta:
        model = SocialMediaLink
        fields = ('platform', 'url')


class FooterSocialMediaSerializer(ModelSerializer):
    """
    Serializes social media links with ordering for footer display.
    
    Input: FooterSocialMedia model instance
    Output: {social_link: {...}, order: int}
    
    Note: Nested social_link contains platform and url
    """
    # Nested serializer to include full social media details
    social_link = SocialMediaLinkSerializer()
    
    class Meta:
        model = FooterSocialMedia
        fields = ('social_link', 'order')


class FooterColumnLinkSerializer(ModelSerializer):
    """
    Serializes individual links within a footer column.
    
    Input: FooterColumnLink model instance
    Output: {label: str, order: int, link: {...}}
    
    Note: Nested link contains name and url
    """
    # Nested serializer to include full link details
    link = LinkSerializer()
    
    class Meta:
        model = FooterColumnLink
        fields = ('label', 'order', 'link')


class FooterLinkColumnSerializer(ModelSerializer):
    """
    Serializes footer columns with their contained links.
    
    Input: FooterLinkColumn model instance
    Output: {title: str, order: int, column_links: [...]}
    
    Note: column_links is an array of FooterColumnLink objects
    """
    # Many links can belong to one column
    column_links = FooterColumnLinkSerializer(many=True)
    
    class Meta:
        model = FooterLinkColumn
        fields = ('title', 'order', 'column_links')


class FooterSerializer(ModelSerializer):
    """
    Main footer serializer with all nested relationships.
    
    Input: Footer model instance (singleton)
    Output: {
        logo: str (image url),
        description: str,
        rights: str,
        columns: [...],
        social_media_items: [...]
    }
    
    Note: This provides the complete footer structure for frontend rendering
    """
    # Nested columns with their links
    columns = FooterLinkColumnSerializer(many=True)
    
    # Nested social media links
    social_media_items = FooterSocialMediaSerializer(many=True)
    
    class Meta:
        model = Footer
        fields = ('logo', 'description', 'rights', 'columns', 'social_media_items')
        
    def get_logo(self, obj: Footer):
        """
        Build full URL for logo if request context was passed.
        
        Args:
            obj: Footer model instance
            
        Returns:
            Full URL for logo if request context exists, static URL of logo otherwise.
        """
        
        # Retrieve request from context
        request = self.context.get('request', None)
        
        # request was not passed
        if request is None:
            logger.warning(f'Falling back to static URL. request context was not passed. {self.__class__.__name__}.logo')
            return obj.logo.url
        
        return request.get_absolute_uri(obj.logo.url)
