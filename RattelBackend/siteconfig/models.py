from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.core.exceptions import ValidationError
from django_resized import ResizedImageField
from RattelBackend.cache import invalidate_cache
from users.models import User
import mimetypes

from utilities.image import generate_random_image


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
        
        # Invalidate footer cache for everyone
        invalidate_cache('footer')
        
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
        
        # Invalidate footer cache for everyone
        invalidate_cache('navbar')
        
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


def video_validator(file):
    """Video file validator"""
    if file is None:
        return

    mime_type, _ = mimetypes.guess_type(file.name)

    # Unknow file format
    if not mime_type:
        raise ValidationError('Could not guess the file type')

    # Not a video
    if not mime_type.startswith('video'):
        raise ValidationError('Only video files are allowed.')

class MainPage(models.Model):
    """Main Page Content"""
    class Meta:
        verbose_name = 'Main Page'
        verbose_name_plural = 'Main Page'

    # Landing
    landing_title = models.CharField(max_length=100, verbose_name='Main Title')
    landing_brushed_title = models.CharField(max_length=100, verbose_name='Brushed Title')
    landing_description = models.TextField(max_length=600, verbose_name='Description')

    landing_link = models.ForeignKey(Link, on_delete=models.SET_NULL, related_name='is_landing_link', blank=True, null=True, verbose_name='Quick Start Link')
    landing_video = models.FileField(upload_to='landing_contents/video', blank=True, null=True, validators=[video_validator], verbose_name='Video Intro')

    landing_image = ResizedImageField(upload_to='landing_contents/image', size=[386, 603], quality=100, crop=['middle', 'center'], verbose_name='Landing Image')
    landing_message_title = models.CharField(max_length=60, verbose_name='Message Title')
    landing_message_description = models.CharField(max_length=80, verbose_name='Message Description')

    @property
    def landing(self):  # Get all landing data with one property
        return {
            'landing_title': self.landing_title,
            'landing_brushed_title': self.landing_brushed_title,
            'landing_description': self.landing_description,
            'landing_link': {
                'name': self.landing_link.name,
                'url': self.landing_link.url,
            } if self.landing_link else None,  # Serialize link if a link is added
            'landing_video': self.landing_video.name and self.landing_video.url,  # Grab URL if available
            'landing_image': self.landing_image.url,
            'landing_message_title': self.landing_message_title,
            'landing_message_description': self.landing_message_description,
        }

    # Stats
    stat1_title = models.CharField(max_length=80, verbose_name='Stat #1 Title')
    stat1_description = models.CharField(max_length=80, verbose_name='Stat #1 Description')

    stat2_title = models.CharField(max_length=80, verbose_name='Stat #2 Title')
    stat2_description = models.CharField(max_length=80, verbose_name='Stat #2 Description')

    stat3_title = models.CharField(max_length=80, verbose_name='Stat #3 Title')
    stat3_description = models.CharField(max_length=80, verbose_name='Stat #3 Description')

    stat4_title = models.CharField(max_length=80, verbose_name='Stat #4 Title')
    stat4_description = models.CharField(max_length=80, verbose_name='Stat #4 Description')

    @property
    def stats(self):  # Access all the statistics of the site with one property
        return {
            'stat1_title': self.stat1_title,
            'stat1_description': self.stat1_description,
            'stat2_title': self.stat2_title,
            'stat2_description': self.stat2_description,
            'stat3_title': self.stat3_title,
            'stat3_description': self.stat3_description,
            'stat4_title': self.stat4_title,
            'stat4_description': self.stat4_description,
        }

    # Courses
    courses_title = models.CharField(max_length=100, verbose_name='Courses Section Title')
    courses_description = models.TextField(max_length=200, verbose_name='Courses Section Description')

    @property
    def courses(self):  # Access Courses section content with one property
        return {
            'courses_title': self.courses_title,
            'courses_description': self.courses_description,
        }

    # Advertisement
    ad_title = models.CharField(max_length=100, verbose_name='Advertisement Title')
    ad_description = models.TextField(max_length=300, verbose_name='Advertisement Description')
    ad_link = models.ForeignKey(Link, on_delete=models.SET_NULL, related_name='is_ad_link', blank=True, null=True, verbose_name='Advertisement Link')

    @property
    def advertisement(self):  # Access Advertisement content with one property
        return {
            'ad_title': self.ad_title,
            'ad_description': self.ad_description,
            'ad_link': {
                'name': self.ad_link.name,
                'url': self.ad_link.url,
            } if self.ad_link else None,
        }

    # Course Suggestions
    course_suggestions_title = models.CharField(max_length=100, verbose_name='Course Suggestion Title')
    course_suggestions_description = models.TextField(max_length=200, verbose_name='Course Suggestion Description')

    @property
    def course_suggestions(self):  # Access Courses section content with one property
        return {
            'course_suggestions_title': self.course_suggestions_title,
            'course_suggestions_description': self.course_suggestions_description,
        }

    # User Experience
    ux_title = models.CharField(max_length=100, verbose_name='User Experience Title')
    ux_description = models.TextField(max_length=300, verbose_name='User Experience Description')

    ux_top_users_enable = models.BooleanField(default=False, verbose_name='Show Selected Top Users')
    ux_top_users = models.ManyToManyField(User, related_name='ux_top_users', blank=True, verbose_name='Top Users List')
    ux_top_users_title = models.CharField(max_length=60, verbose_name='Top Users Title')

    ux_comment1_text = models.TextField(max_length=400, verbose_name='User Comment #1 Text')
    ux_comment1_user = models.ForeignKey(User, related_name='main_page_comment1', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='User Comment #1 User')
    ux_comment1_rate = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name='User Comment #1 Rate')

    ux_comment2_text = models.TextField(max_length=400, verbose_name='User Comment #2 Text')
    ux_comment2_user = models.ForeignKey(User, related_name='main_page_comment2', on_delete=models.SET_NULL, blank=True, null=True, verbose_name='User Comment #2 User')
    ux_comment2_rate = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name='User Comment #2 Rate')

    @property
    def user_experience(self):
        return {
            'ux_title': self.ux_title,
            'ux_description': self.ux_description,
            'top_users': self.ux_top_users_enable and {  # Returns top users list if ux_top_users_enable == True
                'ux_top_users_title': self.ux_top_users_title,
                'ux_top_users': [{'name': user.name, 'profile_picture': user.profile_picture.name and user.profile_picture.url} for user in self.ux_top_users.all()]
            },
            'ux_comment1_text': self.ux_comment1_text,
            'ux_comment1_user': {
                'name': self.ux_comment1_user.name,
                'profile_picture': self.ux_comment1_user.profile_picture.name and self.ux_comment1_user.profile_picture.url,  # Checks if the profile exists
            } if self.ux_comment1_user else None,
            'ux_comment1_rate': self.ux_comment1_rate,
            'ux_comment2_text': self.ux_comment2_text,
            'ux_comment2_user': {
                'name': self.ux_comment2_user.name,
                'profile_picture': self.ux_comment2_user.profile_picture.name and self.ux_comment2_user.profile_picture.url,  # Checks if the profile exists
            } if self.ux_comment2_user else None,
            'ux_comment2_rate': self.ux_comment2_rate,
        }


    def __str__(self):
        return 'Main Page Content'

    def save(self, *args, **kwargs):
        """Enforce singleton pattern"""
        if not self.pk and MainPage.objects.exists():
            raise ValidationError('Only one MainPage instance can exist. Edit the existing one.')

        # Invalidate MainPage cache for everyone
        invalidate_cache('mainpage')

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        """Prevent deletion of singleton"""
        raise ValidationError('MainPage cannot be deleted. You can only edit it.')

    @classmethod
    def get_instance(cls) -> MainPage:
        """Get or create the singleton MainPage instance"""
        mainpage, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'landing_title': 'Landing Title',
                'landing_brushed_title': 'Landing Brushed Title',
                'landing_description': 'Landing Description',
                'landing_image': generate_random_image(386, 603, 'landing_contents/image'),
                'landing_message_title': 'Landing Message Title',
                'landing_message_description': 'Landing Message Description',
                'stat1_title': 'Stat1 Title',
                'stat1_description': 'Stat1 Description',
                'stat2_title': 'Stat2 Title',
                'stat2_description': 'Stat2 Description',
                'stat3_title': 'Stat3 Title',
                'stat3_description': 'Stat3 Description',
                'stat4_title': 'Stat4 Title',
                'stat4_description': 'Stat4 Description',
                'courses_title': 'Courses Title',
                'courses_description': 'Courses Description',
                'ad_title': 'Ads Title',
                'ad_description': 'Ads Description',
                'course_suggestions_title': 'Course Suggestions Title',
                'course_suggestions_description': 'Course Suggestions Description',
                'ux_title': 'UX Title',
                'ux_description': 'UX Description',
                'ux_top_users_title': 'UX Top Users Title',
                'ux_comment1_text': 'UX Comment #1 Text',
                'ux_comment2_text': 'UX Comment #2 Text'
            }
        )
        return mainpage
