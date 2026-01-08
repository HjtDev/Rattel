from django.db import models
from django.core.exceptions import ValidationError
from django_resized import ResizedImageField


class Link(models.Model):
    """Reusable link that can be referenced across the site"""
    class Meta:
        verbose_name = 'Link'
        verbose_name_plural = 'Links'
        ordering = ['name']
    
    name = models.CharField(max_length=255, verbose_name='Internal Name',
                            help_text='Internal reference (e.g., "Contact Page")')
    url = models.URLField(verbose_name='URL')
    
    def __str__(self):
        return self.name


class FooterLinkColumn(models.Model):
    """A column of links in the footer"""
    class Meta:
        verbose_name = 'Footer Link Column'
        verbose_name_plural = 'Footer Link Columns'
        ordering = ['order', 'title']
    
    footer = models.ForeignKey('Footer', on_delete=models.CASCADE,
                               related_name='columns', verbose_name='Footer')
    title = models.CharField(max_length=100, verbose_name='Column Title')
    order = models.PositiveIntegerField(default=0, verbose_name='Order',
                                        help_text='Lower numbers appear first')
    
    def __str__(self):
        return f'{self.title} (Order: {self.order})'


class FooterColumnLink(models.Model):
    """Individual link within a footer column with custom label and ordering"""
    class Meta:
        verbose_name = 'Column Link'
        verbose_name_plural = 'Column Links'
        ordering = ['order', 'label']
        unique_together = [['column', 'link', 'order']]
    
    column = models.ForeignKey(FooterLinkColumn, on_delete=models.CASCADE,
                               related_name='column_links', verbose_name='Column')
    link = models.ForeignKey(Link, on_delete=models.CASCADE, verbose_name='Link')
    label = models.CharField(max_length=100, verbose_name='Display Label', blank=True, null=True,
                             help_text='How this link appears in this column. Leave blank if you want to use link.name instead.')
    order = models.PositiveIntegerField(default=0, verbose_name='Order',
                                        help_text='Lower numbers appear first')
    
    def __str__(self):
        return f'{self.label} ({self.column.title})'


class SocialMediaLink(models.Model):
    """Reusable social media link"""
    class Meta:
        verbose_name = 'Social Media Link'
        verbose_name_plural = 'Social Media Links'
        ordering = ['platform']
    
    class PlatformChoices(models.TextChoices):
        EITAA = 'eitaa', 'ایتا'
        BALE = 'bale', 'بله'
        APARAT = 'aparat', 'آپارات'
        TELEGRAM = 'telegram', 'Telegram'
        INSTAGRAM = 'instagram', 'Instagram'
        WHATSAPP = 'whatsapp', 'WhatsApp'
        YOUTUBE = 'youtube', 'Youtube'
        FACEBOOK = 'facebook', 'Facebook'
        X = 'x', 'X'
        LINKEDIN = 'linkedin', 'LinkedIn'
        TIKTOK = 'tiktok', 'TikTok'
        PINTEREST = 'pinterest', 'Pinterest'
    
    platform = models.CharField(max_length=50, choices=PlatformChoices.choices,
                                verbose_name='Platform')
    url = models.URLField(verbose_name='Platform URL/Link/ID')
    
    def __str__(self):
        return f'{self.get_platform_display()}: {self.url}'


class FooterSocialMedia(models.Model):
    """Social media link in footer with ordering"""
    class Meta:
        verbose_name = 'Footer Social Media'
        verbose_name_plural = 'Footer Social Media'
        ordering = ['order', 'social_link__platform']
        unique_together = [['footer', 'social_link']]
    
    footer = models.ForeignKey('Footer', on_delete=models.CASCADE,
                               related_name='social_media_items', verbose_name='Footer')
    social_link = models.ForeignKey(SocialMediaLink, on_delete=models.CASCADE,
                                    verbose_name='Social Media Link')
    order = models.PositiveIntegerField(default=0, verbose_name='Order',
                                        help_text='Lower numbers appear first')
    
    def __str__(self):
        return f'{self.social_link.get_platform_display()} (Order: {self.order})'


class Footer(models.Model):
    """Singleton footer configuration"""
    class Meta:
        verbose_name = 'Footer'
        verbose_name_plural = 'Footer'
    
    logo = ResizedImageField(upload_to='footer/', size=[506, 106], quality=100,
                             verbose_name='Footer Logo', help_text='Recommended: 506×106 pixels')
    description = models.TextField(max_length=600, verbose_name='Short Description')
    rights = models.CharField(max_length=300, verbose_name='Copyright Text',
                              help_text='e.g., "All rights reserved. © 2026"')
    
    def __str__(self):
        return 'Footer Configuration'
    
    def save(self, *args, **kwargs):
        """Enforce singleton pattern"""
        if not self.pk and Footer.objects.exists():
            raise ValidationError('Only one Footer instance can exist. Edit the existing one.')
        return super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of singleton"""
        raise ValidationError('Footer cannot be deleted. You can only edit it.')
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton Footer instance"""
        footer, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'description': 'Add your site description here',
                'rights': 'All rights reserved. © 2026'
            }
        )
        return footer
    
    
class BaseNavbarItem(models.Model):
    """Base Navbar item - Abstract"""
    class Meta:
        abstract = True
    
    navbar = models.ForeignKey('siteconfig.SiteNavbar', on_delete=models.CASCADE, related_name='+', verbose_name='Navbar')
    
    link = models.ForeignKey(Link, related_name='+', on_delete=models.CASCADE, verbose_name='Link')
    label = models.CharField(max_length=100, verbose_name='Display Label', blank=True, null=True,
                             help_text='How this link appears in this column. Leave blank if you want to use link.name instead.')
    
    order = models.PositiveSmallIntegerField(default=0, verbose_name='Order',
                                        help_text='Lower numbers appear first')
    
    
class SiteNavbarTitleOnlyItems(BaseNavbarItem):
    """Site navbar mega-menu col-1"""
    class Meta:
        verbose_name = 'Site Navbar Items'
        verbose_name_plural = 'Site Navbar Items'
        ordering = ('order',)
    
    def __str__(self):
        return f'Title Only: {self.label or self.link.name}'
    
class SiteNavbarDescribedItems(BaseNavbarItem):
    """Site navbar mega-menu col-2"""
    class Meta:
        verbose_name = 'Site Navbar Described'
        verbose_name_plural = 'Site Navbar Described'
        ordering = ('order',)
        
    description = models.CharField(max_length=150, verbose_name='Description')
    
    def __str__(self):
        return f'Described: {self.label or self.link.name} - {self.description}'
    
    
class SiteNavbarImageItems(BaseNavbarItem):
    """Site navbar mega-menu col-3"""
    class Meta:
        verbose_name = 'Site Navbar Image Items'
        verbose_name_plural = 'Site Navbar Image Items'
        ordering = ('order',)
        
    description = models.CharField(max_length=150, verbose_name='Description')
    icon = ResizedImageField(upload_to='navbar_images/Col3/', size=[40, 40], crop=['middle', 'center'], quality=100, verbose_name='Icon', help_text='40 * 40 pixels')
    
    def __str__(self):
        return f'Image Items: {self.label or self.link.name} - {self.icon.name or 'no-icon'}'
    
    
class SiteNavbar(models.Model):
    """Singleton site navbar configuration"""
    class Meta:
        verbose_name = 'Site Navbar'
        verbose_name_plural = 'Site Navbar'
        
    col1_title = models.CharField(max_length=100, verbose_name='Col 1 Title')
    col2_title = models.CharField(max_length=100, verbose_name='Col 2 Title')
    col3_title = models.CharField(max_length=100, verbose_name='Col 3 Title')
    
    banner_title = models.CharField(max_length=100, verbose_name='Banner Col Title')
    banner_link = models.URLField(verbose_name='Banner URL')
    banner_img = ResizedImageField(upload_to='navbar_images/Col4/', size=[367, 320], crop=['middle', 'center'], quality=100, verbose_name='Banner Image', help_text='367 * 320 pixels')
    
    notification = models.CharField(max_length=255, blank=True, null=True, verbose_name='Notification message', help_text='Shown under the mega-menu')
    
    def __str__(self):
        return 'Site Navbar'
    
    def save(self, *args, **kwargs):
        """Enforce singleton pattern"""
        if not self.pk and SiteNavbar.objects.exists():
            raise ValidationError('Only one Site Navbar instance can exist. Edit the existing one.')
        return super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of singleton"""
        raise ValidationError('Site Navbar cannot be deleted. You can only edit it.')
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton Site Navbar instance"""
        navbar, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'col1_title': 'Col 1 Title',
                'col2_title': 'Col 2 Title',
                'col3_title': 'Col 3 Title',
            }
        )
        return navbar
