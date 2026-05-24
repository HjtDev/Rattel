from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.core.exceptions import ValidationError
from django_resized import ResizedImageField
from django.utils.translation import gettext_lazy as _
from sortedm2m.fields import SortedManyToManyField
from tinymce.models import HTMLField
from RattelBackend.cache import invalidate_cache
from users.models import User
from users.serializers import QuickUserSerializer
from utilities.image import generate_random_image
import mimetypes


class Link(models.Model):
    """Reusable link that can be referenced across the site"""
    class Meta:
        verbose_name = _('Link')
        verbose_name_plural = _('Links')
        ordering = ['name']
    
    name = models.CharField(max_length=255, verbose_name=_('Internal Name'),
                            help_text=_('Internal reference (e.g., "Contact Page")'))
    logo = models.FileField(upload_to='Links/', blank=True, null=True, verbose_name=_('Link Logo'), help_text=_('Recommended: Maintain square aspect-ratio'))
    url = models.URLField(verbose_name=_('URL'))
    
    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        if self.logo and self.logo.name:
            self.logo.delete(save=False)
        return super().delete(*args, **kwargs)


class FooterLinkColumn(models.Model):
    """A column of links in the footer"""
    class Meta:
        verbose_name = _('Footer Link Column')
        verbose_name_plural = _('Footer Link Columns')
        ordering = ['order', 'title']
    
    footer = models.ForeignKey('Footer', on_delete=models.CASCADE,
                               related_name='columns', verbose_name=_('Footer'))
    title = models.CharField(max_length=100, verbose_name=_('Column Title'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'),
                                        help_text=_('Lower numbers appear first'))
    
    def __str__(self):
        return f'{self.title} (Order: {self.order})'


class FooterColumnLink(models.Model):
    """Individual link within a footer column with custom label and ordering"""
    class Meta:
        verbose_name = _('Column Link')
        verbose_name_plural = _('Column Links')
        ordering = ['order', 'label']
        unique_together = [['column', 'link', 'order']]
    
    column = models.ForeignKey(FooterLinkColumn, on_delete=models.CASCADE,
                               related_name='column_links', verbose_name=_('Column'))
    link = models.ForeignKey(Link, on_delete=models.CASCADE, verbose_name=_('Link'))
    label = models.CharField(max_length=100, verbose_name=_('Display Label'), blank=True, null=True,
                             help_text=_('How this link appears in this column. Leave blank if you want to use link.name instead.'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'),
                                        help_text=_('Lower numbers appear first'))
    
    def __str__(self):
        return f'{self.label} ({self.column.title})'


class SocialMediaLink(models.Model):
    """Reusable social media link"""
    class Meta:
        verbose_name = _('Social Media Link')
        verbose_name_plural = _('Social Media Links')
        ordering = ['platform']
    
    class PlatformChoices(models.TextChoices):
        EITAA = 'eitaa', _('ایتا')
        BALE = 'bale', _('بله')
        APARAT = 'aparat', _('آپارات')
        TELEGRAM = 'telegram', _('Telegram')
        INSTAGRAM = 'instagram', _('Instagram')
        WHATSAPP = 'whatsapp', _('WhatsApp')
        YOUTUBE = 'youtube', _('Youtube')
        FACEBOOK = 'facebook', _('Facebook')
        X = 'x', _('X')
        LINKEDIN = 'linkedin', _('LinkedIn')
        TIKTOK = 'tiktok', _('TikTok')
        PINTEREST = 'pinterest', _('Pinterest')
    
    platform = models.CharField(max_length=50, choices=PlatformChoices.choices,
                                verbose_name=_('Platform'))
    url = models.URLField(verbose_name=_('Platform URL/Link/ID'))
    
    def __str__(self):
        return f'{self.get_platform_display()}: {self.url}'


class FooterSocialMedia(models.Model):
    """Social media link in footer with ordering"""
    class Meta:
        verbose_name = _('Footer Social Media')
        verbose_name_plural = _('Footer Social Media')
        ordering = ['order', 'social_link__platform']
        unique_together = [['footer', 'social_link']]
    
    footer = models.ForeignKey('Footer', on_delete=models.CASCADE,
                               related_name='social_media_items', verbose_name=_('Footer'))
    social_link = models.ForeignKey(SocialMediaLink, on_delete=models.CASCADE,
                                    verbose_name=_('Social Media Link'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'),
                                        help_text=_('Lower numbers appear first'))
    
    def __str__(self):
        return f'{self.social_link.get_platform_display()} (Order: {self.order})'


class Footer(models.Model):
    """Singleton footer configuration"""
    class Meta:
        verbose_name = _('Footer')
        verbose_name_plural = _('Footer')
    
    logo = ResizedImageField(upload_to='footer/', size=[506, 106], quality=100,
                             verbose_name=_('Footer Logo'), help_text=_('Recommended: 506×106 pixels'))
    description = models.TextField(max_length=600, verbose_name=_('Short Description'))
    rights = models.CharField(max_length=300, verbose_name=_('Copyright Text'),
                              help_text=_('e.g., "All rights reserved. © 2026"'))
    
    contact_address = models.CharField(max_length=500, blank=True, verbose_name=_('Contact Address'))
    contact_phone = models.CharField(max_length=50, blank=True, verbose_name=_('Contact Phone'))
    contact_email = models.EmailField(max_length=100, blank=True, verbose_name=_('Contact Email'))
    contact_hours = models.CharField(max_length=200, blank=True, verbose_name=_('Contact Hours'))
    
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
    
    navbar = models.ForeignKey('siteconfig.SiteNavbar', on_delete=models.CASCADE, related_name='+', verbose_name=_('Navbar'))
    
    link = models.ForeignKey(Link, related_name='+', on_delete=models.CASCADE, verbose_name=_('Link'))
    label = models.CharField(max_length=100, verbose_name=_('Display Label'), blank=True, null=True,
                             help_text=_('How this link appears in this column. Leave blank if you want to use link.name instead.'))
    
    order = models.PositiveSmallIntegerField(default=0, verbose_name=_('Order'),
                                        help_text=_('Lower numbers appear first'))
    
    
class SiteNavbarTitleOnlyItems(BaseNavbarItem):
    """Site navbar mega-menu col-1"""
    class Meta:
        verbose_name = _('Site Navbar Items')
        verbose_name_plural = _('Site Navbar Items')
        ordering = ('order',)
    
    def __str__(self):
        return f'Title Only: {self.label or self.link.name}'
    
class SiteNavbarDescribedItems(BaseNavbarItem):
    """Site navbar mega-menu col-2"""
    class Meta:
        verbose_name = _('Site Navbar Described')
        verbose_name_plural = _('Site Navbar Described')
        ordering = ('order',)
        
    description = models.CharField(max_length=150, verbose_name=_('Description'))
    
    def __str__(self):
        return f'Described: {self.label or self.link.name} - {self.description}'
    
    
class SiteNavbarImageItems(BaseNavbarItem):
    """Site navbar mega-menu col-3"""
    class Meta:
        verbose_name = _('Site Navbar Image Items')
        verbose_name_plural = _('Site Navbar Image Items')
        ordering = ('order',)
        
    description = models.CharField(max_length=150, verbose_name=_('Description'))
    icon = ResizedImageField(upload_to='navbar_images/Col3/', size=[40, 40], crop=['middle', 'center'], quality=100, verbose_name=_('Icon'), help_text=_('40 * 40 pixels'))
    
    def __str__(self):
        return f"Image Items: {self.label or self.link.name} - {self.icon.name or 'no-icon'}"

    def delete(self, *args, **kwargs):
        if self.icon and self.icon.name:
            self.icon.delete(save=False)
        return super().delete(*args, **kwargs)
    
    
class SiteNavbar(models.Model):
    """Singleton site navbar configuration"""
    class Meta:
        verbose_name = _('Site Navbar')
        verbose_name_plural = _('Site Navbar')

    navbar_logo = models.FileField(upload_to='navbar_images/logo/', verbose_name=_('Navbar Logo'), help_text=_('Suggested Format: .svg'))
    navbar_links = SortedManyToManyField(Link, related_name='navbar_links', blank=True, verbose_name=_('Navbar Links'))
        
    col1_title = models.CharField(max_length=100, verbose_name=_('Col 1 Title'))
    col2_title = models.CharField(max_length=100, verbose_name=_('Col 2 Title'))
    col3_title = models.CharField(max_length=100, verbose_name=_('Col 3 Title'))
    
    banner_title = models.CharField(max_length=100, verbose_name=_('Banner Col Title'))
    banner_link = models.URLField(verbose_name=_('Banner URL'))
    banner_img = ResizedImageField(upload_to='navbar_images/Col4/', size=[367, 320], crop=['middle', 'center'], quality=100, verbose_name=_('Banner Image'), help_text=_('367 * 320 pixels'))
    
    notification = models.CharField(max_length=255, blank=True, null=True, verbose_name=_('Notification message'), help_text=_('Shown under the mega-menu'))
    
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
        raise ValidationError('Site Navbar cannot be deleted. You can only edit it.')
    
    @classmethod
    def get_instance(cls):
        """Get or create the singleton Site Navbar instance"""
        navbar, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'navbar_logo': generate_random_image(150, 36, 'navbar_images/logo'),
                'col1_title': 'Col 1 Title',
                'col2_title': 'Col 2 Title',
                'col3_title': 'Col 3 Title',
            }
        )
        return navbar


class AboutUs(models.Model):
    class Meta:
        verbose_name = _('About Us')
        verbose_name_plural = _('About Us')

    image_section_title = models.CharField(max_length=255, verbose_name=_('Image Section Title'))
    image_section_top_right_image = models.FileField(
        upload_to='aboutus/images/',
        blank=True,
        null=True,
        verbose_name=_('Image Section Top Right Image')
    )
    image_section_bottom_right_image = models.FileField(
        upload_to='aboutus/images/',
        blank=True,
        null=True,
        verbose_name=_('Image Section Bottom Right Image')
    )
    image_section_middle_image = models.FileField(
        upload_to='aboutus/images/',
        blank=True,
        null=True,
        verbose_name=_('Image Section Middle Image')
    )
    image_section_bottom_left_image = models.FileField(
        upload_to='aboutus/images/',
        blank=True,
        null=True,
        verbose_name=_('Image Section Bottom Left Image')
    )
    image_section_box_title = models.CharField(max_length=100, verbose_name=_('Image Section Box Title'))
    image_section_box_description = models.TextField(max_length=300, verbose_name=_('Image Section Box Description'))

    info_section_title = models.CharField(max_length=255, verbose_name=_('Info Section Title'))
    info_section_description = HTMLField(verbose_name=_('Info Section Description'))
    info_section_information_boxes = SortedManyToManyField(
        'siteconfig.Information',
        related_name='aboutus_information_boxes',
        blank=True,
        verbose_name=_('Info Section Information Boxes')
    )

    trust_logo_section_title = models.CharField(
        max_length=255,
        default='',
        blank=True,
        verbose_name=_('Trust Logo Section Title')
    )
    trust_logo_section_links = SortedManyToManyField(
        Link,
        related_name='aboutus_trust_links',
        blank=True,
        verbose_name=_('Trust Logo Section Links')
    )

    def __str__(self):
        return 'About Us'

    def save(self, *args, **kwargs):
        if not self.pk and AboutUs.objects.exists():
            raise ValidationError(_('Only one About Us instance can exist. Edit the existing one.'))
        invalidate_cache('aboutus')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(_('About Us cannot be deleted. You can only edit it.'))

    @classmethod
    def get_instance(cls):
        about_us, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'image_section_title': _('About Us'),
                'image_section_box_title': _('Our Goal'),
                'image_section_box_description': _('Add your short goal statement here.'),
                'info_section_title': _('About Academy'),
                'info_section_description': _('<p>Add your about-us HTML description here.</p>'),
                'trust_logo_section_title': _('Trusted By'),
            }
        )
        return about_us


class WorkWithUs(models.Model):
    class Meta:
        verbose_name = _('Work With Us')
        verbose_name_plural = _('Work With Us')

    hero_title = models.CharField(max_length=255, verbose_name=_('Hero Title'))
    hero_description = models.TextField(verbose_name=_('Hero Description'))
    hero_link = models.ForeignKey(
        Link,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='workwithus_hero_links',
        verbose_name=_('Hero Link')
    )
    hero_image = models.FileField(upload_to='workwithus/hero/', blank=True, null=True, verbose_name=_('Hero Image'))

    collaboration_section_title = models.CharField(max_length=255, verbose_name=_('Collaboration Section Title'))
    collaboration_section_description = models.TextField(verbose_name=_('Collaboration Section Description'))
    collaboration_section_step1_title = models.CharField(max_length=255, verbose_name=_('Collaboration Section Step 1 Title'))
    collaboration_section_step1_description = models.TextField(verbose_name=_('Collaboration Section Step 1 Description'))
    collaboration_section_step1_image = models.FileField(
        upload_to='workwithus/collaboration_steps/',
        blank=True,
        null=True,
        verbose_name=_('Collaboration Section Step 1 Image')
    )
    collaboration_section_step2_title = models.CharField(max_length=255, verbose_name=_('Collaboration Section Step 2 Title'))
    collaboration_section_step2_description = models.TextField(verbose_name=_('Collaboration Section Step 2 Description'))
    collaboration_section_step2_image = models.FileField(
        upload_to='workwithus/collaboration_steps/',
        blank=True,
        null=True,
        verbose_name=_('Collaboration Section Step 2 Image')
    )
    collaboration_section_step3_title = models.CharField(max_length=255, verbose_name=_('Collaboration Section Step 3 Title'))
    collaboration_section_step3_description = models.TextField(verbose_name=_('Collaboration Section Step 3 Description'))
    collaboration_section_step3_image = models.FileField(
        upload_to='workwithus/collaboration_steps/',
        blank=True,
        null=True,
        verbose_name=_('Collaboration Section Step 3 Image')
    )

    counter_section_item1_label = models.CharField(max_length=100, verbose_name=_('Counter Section Item 1 Label'))
    counter_section_item1_value = models.PositiveIntegerField(default=0, verbose_name=_('Counter Section Item 1 Value'))
    counter_section_item2_label = models.CharField(max_length=100, verbose_name=_('Counter Section Item 2 Label'))
    counter_section_item2_value = models.PositiveIntegerField(default=0, verbose_name=_('Counter Section Item 2 Value'))
    counter_section_item3_label = models.CharField(max_length=100, verbose_name=_('Counter Section Item 3 Label'))
    counter_section_item3_value = models.PositiveIntegerField(default=0, verbose_name=_('Counter Section Item 3 Value'))
    counter_section_item4_label = models.CharField(max_length=100, verbose_name=_('Counter Section Item 4 Label'))
    counter_section_item4_value = models.PositiveIntegerField(default=0, verbose_name=_('Counter Section Item 4 Value'))

    main_content_section_title = models.CharField(max_length=255, verbose_name=_('Main Content Section Title'))
    main_content_section_tab1_title = models.CharField(max_length=255, verbose_name=_('Main Content Section Tab 1 Title'))
    main_content_section_tab1_description = HTMLField(verbose_name=_('Main Content Section Tab 1 Description'))
    main_content_section_tab2_title = models.CharField(max_length=255, verbose_name=_('Main Content Section Tab 2 Title'))
    main_content_section_tab2_description = HTMLField(verbose_name=_('Main Content Section Tab 2 Description'))
    main_content_section_tab3_title = models.CharField(max_length=255, verbose_name=_('Main Content Section Tab 3 Title'))
    main_content_section_tab3_description = HTMLField(verbose_name=_('Main Content Section Tab 3 Description'))

    advertisement_section_title = models.CharField(max_length=255, verbose_name=_('Advertisement Section Title'))
    advertisement_section_description = models.TextField(verbose_name=_('Advertisement Section Description'))
    advertisement_section_link = models.ForeignKey(
        Link,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='workwithus_advertisement_links',
        verbose_name=_('Advertisement Section Link')
    )

    def __str__(self):
        return 'Work With Us'

    def save(self, *args, **kwargs):
        if not self.pk and WorkWithUs.objects.exists():
            raise ValidationError(_('Only one Work With Us instance can exist. Edit the existing one.'))
        invalidate_cache('workwithus')
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValidationError(_('Work With Us cannot be deleted. You can only edit it.'))

    @classmethod
    def get_instance(cls):
        work_with_us, created = cls.objects.get_or_create(
            pk=1,
            defaults={
                'hero_title': _('Become an Instructor!'),
                'hero_description': _('Add hero section description here.'),
                'collaboration_section_title': _('Collaboration Steps'),
                'collaboration_section_description': _('Add collaboration section description here.'),
                'collaboration_section_step1_title': _('Register'),
                'collaboration_section_step1_description': _('Add step 1 description.'),
                'collaboration_section_step2_title': _('Add Course'),
                'collaboration_section_step2_description': _('Add step 2 description.'),
                'collaboration_section_step3_title': _('Earn Income'),
                'collaboration_section_step3_description': _('Add step 3 description.'),
                'counter_section_item1_label': _('Total Students'),
                'counter_section_item2_label': _('Total Instructors'),
                'counter_section_item3_label': _('Total Courses'),
                'counter_section_item4_label': _('Languages'),
                'main_content_section_title': _('Instructor Recruitment Stages'),
                'main_content_section_tab1_title': _('Registration'),
                'main_content_section_tab1_description': _('<p>Add tab 1 content.</p>'),
                'main_content_section_tab2_title': _('Add Course'),
                'main_content_section_tab2_description': _('<p>Add tab 2 content.</p>'),
                'main_content_section_tab3_title': _('Monetization'),
                'main_content_section_tab3_description': _('<p>Add tab 3 content.</p>'),
                'advertisement_section_title': _('Become an Instructor!'),
                'advertisement_section_description': _('Add advertisement section description here.'),
            }
        )
        return work_with_us


class WorkWithUsResumeSubmission(models.Model):
    class Meta:
        verbose_name = _('Work With Us Resume Submission')
        verbose_name_plural = _('Work With Us Resume Submissions')
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['-created_at']),
            models.Index(fields=['email']),
        ]

    work_with_us = models.ForeignKey(
        WorkWithUs,
        on_delete=models.CASCADE,
        related_name='resume_submissions',
        verbose_name=_('Work With Us')
    )
    full_name = models.CharField(max_length=150, verbose_name=_('Full Name'))
    email = models.EmailField(verbose_name=_('Email'))
    phone_number = models.CharField(max_length=50, verbose_name=_('Phone Number'))
    message = models.TextField(verbose_name=_('Message'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    def __str__(self):
        return f'{self.full_name} ({self.email})'


class Information(models.Model):
    """Information sections model"""
    class Meta:
        verbose_name = _('Information Section')
        verbose_name_plural = _('Information Sections')
        ordering = ('order',)

    title = models.CharField(max_length=130, verbose_name=_('Title'))
    description = HTMLField(verbose_name=_('Description'))
    image = models.FileField(upload_to='information/images', verbose_name=_('Image'), help_text=_('Recommended: 615 * 435'))

    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'), help_text=_('Lower number appear first'))

    mainpage = models.ForeignKey('siteconfig.MainPage', on_delete=models.SET_NULL, blank=True, null=True, related_name='info_boxes', verbose_name=_('Main Page'))

    def __str__(self):
        return f'Information Section: {self.title}'

    def delete(self, *args, **kwargs):
        if self.image and self.image.name:
            self.image.delete(save=False)
        return super().delete(*args, **kwargs)


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
        verbose_name = _('Main Page')
        verbose_name_plural = _('Main Page')

    # Landing
    landing_title = models.CharField(max_length=100, verbose_name=_('Main Title'))
    landing_brushed_title = models.CharField(max_length=100, verbose_name=_('Brushed Title'))
    landing_description = models.TextField(max_length=600, verbose_name=_('Description'))

    landing_link = models.ForeignKey(Link, on_delete=models.SET_NULL, related_name='is_landing_link', blank=True, null=True, verbose_name=_('Quick Start Link'))
    landing_video = models.FileField(upload_to='landing_contents/video', blank=True, null=True, validators=[video_validator], verbose_name=_('Video Intro'))

    landing_image = models.FileField(upload_to='landing_contents/image', verbose_name=_('Landing Image'), help_text=_('Recommended: 386 * 603'))
    icon1 = models.FileField(upload_to='landing_contents/icons', blank=True, null=True, verbose_name=_('Feature Icon #1'))
    icon2 = models.FileField(upload_to='landing_contents/icons', blank=True, null=True, verbose_name=_('Feature Icon #2'))
    icon3 = models.FileField(upload_to='landing_contents/icons', blank=True, null=True, verbose_name=_('Feature Icon #3'))
    feature1 = models.CharField(max_length=50, blank=True, default='', verbose_name=_('Feature #1'))
    feature2 = models.CharField(max_length=50, blank=True, default='', verbose_name=_('Feature #2'))
    feature3 = models.CharField(max_length=50, blank=True, default='', verbose_name=_('Feature #3'))
    landing_message_title = models.CharField(max_length=60, verbose_name=_('Message Title'))
    landing_message_description = models.CharField(max_length=80, verbose_name=_('Message Description'))

    @property
    def landing(self):  # Get all landing data with one property
        from siteconfig.serializers import LinkSerializer
        return {
            'title': self.landing_title,
            'brushed_title': self.landing_brushed_title,
            'description': self.landing_description,
            'link': LinkSerializer(self.landing_link).data if self.landing_link else None,  # Serialize link if a link is added
            'video': self.landing_video.name and self.landing_video.url,  # Grab URL if available
            'image': self.landing_image.url,
            'icon1': self.icon1.name and self.icon1.url if self.icon1 else None,
            'icon2': self.icon2.name and self.icon2.url if self.icon2 else None,
            'icon3': self.icon3.name and self.icon3.url if self.icon3 else None,
            'feature1': self.feature1,
            'feature2': self.feature2,
            'feature3': self.feature3,
            'message_title': self.landing_message_title,
            'message_description': self.landing_message_description,
        }

    # Stats
    stat1_title = models.CharField(max_length=80, verbose_name=_('Stat #1 Title'))
    stat1_description = models.CharField(max_length=80, verbose_name=_('Stat #1 Description'))
    stat1_link = models.ForeignKey(Link, on_delete=models.SET_NULL, blank=True, null=True, related_name='is_stat1_link', verbose_name=_('Stat #1 Link'))

    stat2_title = models.CharField(max_length=80, verbose_name=_('Stat #2 Title'))
    stat2_description = models.CharField(max_length=80, verbose_name=_('Stat #2 Description'))
    stat2_link = models.ForeignKey(Link, on_delete=models.SET_NULL, blank=True, null=True, related_name='is_stat2_link', verbose_name=_('Stat #2 Link'))

    stat3_title = models.CharField(max_length=80, verbose_name=_('Stat #3 Title'))
    stat3_description = models.CharField(max_length=80, verbose_name=_('Stat #3 Description'))
    stat3_link = models.ForeignKey(Link, on_delete=models.SET_NULL, blank=True, null=True, related_name='is_stat3_link', verbose_name=_('Stat #3 Link'))

    stat4_title = models.CharField(max_length=80, verbose_name=_('Stat #4 Title'))
    stat4_description = models.CharField(max_length=80, verbose_name=_('Stat #4 Description'))
    stat4_link = models.ForeignKey(Link, on_delete=models.SET_NULL, blank=True, null=True, related_name='is_stat4_link', verbose_name=_('Stat #4 Link'))

    @property
    def stats(self):  # Access all the statistics of the site with one property
        return {
            'stat1_title': self.stat1_title,
            'stat1_description': self.stat1_description,
            'stat1_link': {
                'name': self.stat1_link.name,
                'url': self.stat1_link.url,
            } if self.stat1_link else None,

            'stat2_title': self.stat2_title,
            'stat2_description': self.stat2_description,
            'stat2_link': {
                'name': self.stat2_link.name,
                'url': self.stat2_link.url,
            } if self.stat2_link else None,

            'stat3_title': self.stat3_title,
            'stat3_description': self.stat3_description,
            'stat3_link': {
                'name': self.stat3_link.name,
                'url': self.stat3_link.url,
            } if self.stat3_link else None,

            'stat4_title': self.stat4_title,
            'stat4_description': self.stat4_description,
            'stat4_link': {
                'name': self.stat4_link.name,
                'url': self.stat4_link.url,
            } if self.stat4_link else None,
        }

    # Advertisement
    ad_title = models.CharField(max_length=100, verbose_name=_('Advertisement Title'))
    ad_description = models.TextField(max_length=300, verbose_name=_('Advertisement Description'))
    ad_link = models.ForeignKey(Link, on_delete=models.SET_NULL, related_name='is_ad_link', blank=True, null=True, verbose_name=_('Advertisement Link'))

    @property
    def advertisement(self):  # Access Advertisement content with one property
        from siteconfig.serializers import LinkSerializer
        return {
            'title': self.ad_title,
            'description': self.ad_description,
            'link': LinkSerializer(self.ad_link).data if self.ad_link else None,
        }

    # Dual Choice
    choice1_title = models.CharField(max_length=100, verbose_name=_('Choice #1 Title'))
    choice1_description = models.TextField(max_length=300, verbose_name=_('Choice #1 Description'))
    choice1_image = ResizedImageField(upload_to='DualChoice/images', quality=100,
                             verbose_name=_('Choice #1 Image'), help_text=_('Recommended: 235 * 200 pixel'))
    choice1_link = models.ForeignKey(Link, on_delete=models.SET_NULL, blank=True, null=True, related_name='is_choice1_link', verbose_name=_('Choice #1 Link'))

    choice2_title = models.CharField(max_length=100, verbose_name=_('Choice #2 Title'))
    choice2_description = models.TextField(max_length=300, verbose_name=_('Choice #2 Description'))
    choice2_image = ResizedImageField(upload_to='DualChoice/images', quality=100,
                                      verbose_name=_('Choice #2 Image'), help_text=_('Recommended: 235 * 200 pixel'))
    choice2_link = models.ForeignKey(Link, on_delete=models.SET_NULL, blank=True, null=True, related_name='is_choice2_link', verbose_name=_('Choice #2 Link'))

    @property
    def dual_choices(self):
        from siteconfig.serializers import LinkSerializer
        return {
            'choice1_title': self.choice1_title,
            'choice1_description': self.choice1_description,
            'choice1_image': self.choice1_image.name and self.choice1_image.url,
            'choice1_link': LinkSerializer(self.choice1_link).data,

            'choice2_title': self.choice2_title,
            'choice2_description': self.choice2_description,
            'choice2_image': self.choice2_image.name and self.choice2_image.url,
            'choice2_link': LinkSerializer(self.choice2_link).data,
        }

    # User Experience
    ux_title = models.CharField(max_length=100, verbose_name=_('User Experience Title'))
    ux_description = models.TextField(max_length=300, verbose_name=_('User Experience Description'))

    ux_top_users_enable = models.BooleanField(default=False, verbose_name=_('Show Selected Top Users'))
    ux_top_users = models.ManyToManyField(User, related_name='ux_top_users', blank=True, verbose_name=_('Top Users List'))
    ux_top_users_title = models.CharField(max_length=60, verbose_name=_('Top Users Title'))

    ux_comment1_text = models.TextField(max_length=400, verbose_name=_('User Comment #1 Text'))
    ux_comment1_user = models.ForeignKey(User, related_name='main_page_comment1', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_('User Comment #1 User'))
    ux_comment1_rate = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name=_('User Comment #1 Rate'))

    ux_comment2_text = models.TextField(max_length=400, verbose_name=_('User Comment #2 Text'))
    ux_comment2_user = models.ForeignKey(User, related_name='main_page_comment2', on_delete=models.SET_NULL, blank=True, null=True, verbose_name=_('User Comment #2 User'))
    ux_comment2_rate = models.PositiveIntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name=_('User Comment #2 Rate'))

    @property
    def user_experience(self):
        return {
            'title': self.ux_title,
            'description': self.ux_description,

            'top_users': self.ux_top_users_enable and {  # Returns top users list if ux_top_users_enable == True
                'title': self.ux_top_users_title,
                'list': QuickUserSerializer(self.ux_top_users.all(), many=True).data,
            },
            'comment1_text': self.ux_comment1_text,
            'comment1_user': QuickUserSerializer(self.ux_comment1_user).data if self.ux_comment1_user else None,
            'comment1_rate': self.ux_comment1_rate,

            'comment2_text': self.ux_comment2_text,
            'comment2_user': QuickUserSerializer(self.ux_comment2_user).data if self.ux_comment2_user else None,
            'comment2_rate': self.ux_comment2_rate,
        }

    # Top teachers
    logo_link_title = models.CharField(max_length=100, verbose_name=_('Logo Link List Title'))
    logo_link_description = models.TextField(max_length=200, verbose_name=_('Logo Link List Description'))
    logo_link_list = models.ManyToManyField(Link, related_name='logo_links', blank=True, verbose_name=_('Logo Link List'))

    @property
    def logo_links(self):
        from siteconfig.serializers import LinkSerializer
        return {
            'title': self.logo_link_title,
            'description': self.logo_link_description,
            'list': LinkSerializer(self.logo_link_list.all(), many=True).data,
        }

    # Imaged Links
    imaged_links_list = models.ManyToManyField(Link, related_name='custom_imaged_links', blank=True, verbose_name=_('Custom Imaged Links List'))

    @property
    def imaged_links(self):
        from siteconfig.serializers import LinkSerializer
        return {
            'links': LinkSerializer(self.imaged_links_list.all(), many=True).data,
        }

    # Top Courses Video
    top_courses_video = models.FileField(upload_to='top_course_video/', blank=True, validators=[video_validator], verbose_name=_('Top Course Video File'))

    @property
    def courses_demo(self):
        return {
            'video': self.top_courses_video.name and self.top_courses_video.url,
        }


    @property
    def information_boxes(self):
        from .serializers import InformationSerializer
        return {
            'boxes': InformationSerializer(self.info_boxes.all().order_by('order'), many=True).data,
        }


    def __str__(self):
        return 'Main Page Content'

    def clean(self):
        super().clean()
        if not self.pk:
            return

        if self.imaged_links_list.exists():
            for link in self.imaged_links_list.all():
                if not link.logo.name:
                    raise ValidationError({'imaged_links_list': f'Imaged Links List must have logo. {link} does not have a logo.'})

    def save(self, *args, **kwargs):
        """Enforce singleton pattern"""
        if not self.pk and MainPage.objects.exists():
            raise ValidationError('Only one MainPage instance can exist. Edit the existing one.')

        # Invalidate MainPage cache for everyone
        invalidate_cache('mainpage')

        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
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
                'icon1': generate_random_image(64, 64, 'landing_contents/icons'),
                'icon2': generate_random_image(64, 64, 'landing_contents/icons'),
                'icon3': generate_random_image(64, 64, 'landing_contents/icons'),
                'feature1': 'Feature 1',
                'feature2': 'Feature 2',
                'feature3': 'Feature 3',
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
                'choice1_title': 'Choice1 Title',
                'choice1_description': 'Choice1 Description',
                'choice1_image': generate_random_image(235, 200, 'DualChoice/images'),
                'choice2_title': 'Choice2 Title',
                'choice2_description': 'Choice2 Description',
                'choice2_image': generate_random_image(235, 200, 'DualChoice/images'),
                'course_suggestions_title': 'Course Suggestions Title',
                'course_suggestions_description': 'Course Suggestions Description',
                'ux_title': 'UX Title',
                'ux_description': 'UX Description',
                'ux_top_users_title': 'UX Top Users Title',
                'ux_comment1_text': 'UX Comment #1 Text',
                'ux_comment2_text': 'UX Comment #2 Text',
                'logo_link_title': 'Logo Link Title',
                'logo_link_description': 'Logo Link Description',
            }
        )
        return mainpage


class FAQ(models.Model):
    class Meta:
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQs')
        ordering = ('order',)

    question = models.CharField(max_length=255, verbose_name=_('Question'))
    answer = models.TextField(verbose_name=_('Answer'))

    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'), help_text=_('Order of the FAQ. Lower number appears first.'))

    is_visible = models.BooleanField(default=True, verbose_name=_('Visible'))

    def __str__(self):
        return f"FAQ: {self.question[:19] + '...' if len(self.question) > 20 else self.question}"
    
    def save(self, *args, **kwargs):
        invalidate_cache('faq')

        return super().save(*args, **kwargs)
        
