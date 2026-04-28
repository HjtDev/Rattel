from rest_framework.fields import SerializerMethodField
from rest_framework.serializers import ModelSerializer
from .models import Footer, FooterLinkColumn, FooterColumnLink, FooterSocialMedia, SocialMediaLink, Link, SiteNavbar, \
    SiteNavbarTitleOnlyItems, BaseNavbarItem, SiteNavbarDescribedItems, SiteNavbarImageItems, Information, FAQ
import logging


logger = logging.getLogger(__name__)


class LinkSerializer(ModelSerializer):
    """
    Serializes reusable Link objects.
    
    Input: Link model instance
    Output: {name: str, url: str, logo: str<file-path>}
    """
    class Meta:
        model = Link
        fields = ('name', 'logo', 'url')

    def get_logo(self, obj: Footer):
        """
        Build full URL for logo if request context was passed and a logo was attached.

        Args:
            obj: Link model instance

        Returns:
            None if no logo is attached.
            Full URL for logo if request context exists, static URL of logo otherwise.
        """

        # Returns None if no logo is attached
        if not obj.logo.name:
            return None

        # Retrieve request from context
        request = self.context.get('request', None)

        # request was not passed
        if request is None:
            logger.warning(f'Falling back to static URL. request context was not passed. {self.__class__.__name__}.logo')
            return obj.logo.url

        return request.build_absolute_uri(obj.logo.url)


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
        fields = (
            'logo', 'description', 'rights', 'columns', 'social_media_items',
            'contact_address', 'contact_phone', 'contact_email', 'contact_hours'
        )
        
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
        
        return request.build_absolute_uri(obj.logo.url)


class BaseNavbarItemSerializer(ModelSerializer):
    """
    Base serializer for all navbar items.
    
    Serializes common fields for navbar items including:
        - `link`: Nested link details using `LinkSerializer`
        - `label`: Display text of the navbar item
        - `order`: Display order for sorting in the navbar
    
    Used as a base class for more specialized navbar item serializers.
    """
    link = LinkSerializer()
    
    class Meta:
        model = BaseNavbarItem
        fields = ['link', 'label', 'order']


class SiteNavbarTitleOnlyItemsSerializer(BaseNavbarItemSerializer):
    """
    Serializer for navbar items that only include a title.
    
    Inherits all fields from `BaseNavbarItemSerializer`.
    Maps to `SiteNavbarTitleOnlyItems` model.
    """
    class Meta:
        model = SiteNavbarTitleOnlyItems
        fields = BaseNavbarItemSerializer.Meta.fields


class SiteNavbarDescribedItemsSerializer(BaseNavbarItemSerializer):
    """
    Serializer for navbar items with a title and description.
    
    Inherits fields from `BaseNavbarItemSerializer` and adds:
        - `description`: Text description for the item
    
    Maps to `SiteNavbarDescribedItems` model.
    """
    class Meta:
        model = SiteNavbarDescribedItems
        fields = BaseNavbarItemSerializer.Meta.fields + ['description']


class SiteNavbarImageItemsSerializer(BaseNavbarItemSerializer):
    """
    Serializer for navbar items that include an image/icon.
    
    Inherits fields from `BaseNavbarItemSerializer` and adds:
        - `description`: Text description
        - `icon`: Image/icon URL for the navbar item, full URL built with request context if available
    """
    icon = SerializerMethodField()
    
    class Meta:
        model = SiteNavbarImageItems
        fields = BaseNavbarItemSerializer.Meta.fields + ['description', 'icon']
    
    def get_icon(self, obj: SiteNavbarImageItems):
        """
        Build the full URL for the item's icon.
        
        Args:
            obj: SiteNavbarImageItems model instance
            
        Returns:
            Full URL of the icon if request context exists; otherwise returns relative URL.
        """
        request = self.context.get('request', None)
        if request is None:
            return obj.icon.url
        return request.build_absolute_uri(obj.icon.url)


class SiteNavbarSerializer(ModelSerializer):
    """
    Serializer for the complete site navbar structure.
    
    Includes three columns of navbar items (col1, col2, col3) and an optional banner.
    Each column is populated using specialized item serializers:
        - col1: Title-only items
        - col2: Described items
        - col3: Image items
    """
    navbar_links = LinkSerializer(many=True, read_only=True)
    col1 = SerializerMethodField()
    col2 = SerializerMethodField()
    col3 = SerializerMethodField()
    banner = SerializerMethodField()
    
    class Meta:
        model = SiteNavbar
        fields = ('navbar_logo', 'navbar_links', 'col1', 'col2', 'col3', 'banner', 'notification')

    def get_navbar_logo(self, obj: SiteNavbar):
        """
        Build the full URL for the navbar logo if request context passed..

        Args:
            obj: SiteNavbar model instance

        Returns:
            Full URL of the logo if request context exists; otherwise returns relative URL.
        """
        request = self.context.get('request', None)

        if request is None:
            return obj.logo.url

        return request.build_absolute_uri(obj.logo.url)
    
    def get_col1(self, obj: SiteNavbar):
        """
        Retrieve title-only navbar items for column 1, ordered by `order`.
        """
        items = SiteNavbarTitleOnlyItems.objects.filter(navbar=obj).order_by('order')
        return {'title': obj.col1_title, 'items': SiteNavbarTitleOnlyItemsSerializer(items, many=True).data}
    
    def get_col2(self, obj: SiteNavbar):
        """
        Retrieve described navbar items for column 2, ordered by `order`.
        """
        items = SiteNavbarDescribedItems.objects.filter(navbar=obj).order_by('order')
        return {'title': obj.col2_title, 'items': SiteNavbarDescribedItemsSerializer(items, many=True).data}

    def get_col3(self, obj: SiteNavbar):
        """
        Retrieve image navbar items for column 3, ordered by `order`.
        """
        request = self.context.get('request', None)
        items = SiteNavbarImageItems.objects.filter(navbar=obj).order_by('order')

        if request:
            return {'title': obj.col3_title, 'items': SiteNavbarImageItemsSerializer(items, many=True, context={'request': request}).data}
        else:
            return {'title': obj.col3_title, 'items': SiteNavbarImageItemsSerializer(items, many=True).data}

    def get_banner(self, obj: SiteNavbar):
        """
        Build the banner object for the navbar.
        
        Returns:
            Dictionary containing:
                - image: Full URL of the banner image (or None if not set)
                - title: Banner title string
                - link: Banner link URL
        """
        banner_image = obj.banner_img.url if obj.banner_img else None
        banner_title = obj.banner_title
        banner_link = obj.banner_link
        
        request = self.context.get('request', None)
        if request is not None and banner_image:
            banner_image = request.build_absolute_uri(banner_image)
        
        return {
            'image': banner_image,
            'title': banner_title,
            'link': banner_link,
        }

class InformationSerializer(ModelSerializer):
    class Meta:
        model = Information
        fields = ('title', 'description', 'image', 'order')

    def get_image(self, obj: Information):
        """
        Build the full URL for the image if request context passed..

        Args:
            obj: Information model instance

        Returns:
            Full URL for the image if request context exists; otherwise returns relative URL.
        """
        request = self.context.get('request', None)

        if request is None:
            return obj.image.url

        return request.build_absolute_uri(obj.image.url)

class FAQSerializer(ModelSerializer):
    class Meta:
        model = FAQ
        fields = ('question', 'answer', 'order')
