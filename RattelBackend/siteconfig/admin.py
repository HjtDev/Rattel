from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.shortcuts import redirect
from django.urls import reverse
from .models import (
    Link,
    FooterLinkColumn,
    FooterColumnLink,
    SocialMediaLink,
    FooterSocialMedia,
    Footer,
    SiteNavbarTitleOnlyItems,
    SiteNavbarDescribedItems,
    SiteNavbarImageItems,
    SiteNavbar,
    MainPage, Information, FAQ, AboutUs
)


class FooterColumnLinkInline(admin.TabularInline):
    """Inline for managing links within a column"""
    model = FooterColumnLink
    extra = 1
    fields = ['link', 'label', 'order']
    ordering = ['order']
    autocomplete_fields = ['link']
    verbose_name = _('Link')
    verbose_name_plural = _('Links in this Column')


class FooterLinkColumnInline(admin.StackedInline):
    """Inline for managing columns within footer"""
    model = FooterLinkColumn
    extra = 0
    fields = ['title', 'order']
    ordering = ['order']
    show_change_link = True
    verbose_name = _('Link Column')
    verbose_name_plural = _('Footer Link Columns')


class FooterSocialMediaInline(admin.TabularInline):
    """Inline for managing social media links in footer"""
    model = FooterSocialMedia
    extra = 1
    fields = ['social_link', 'order']
    ordering = ['order']
    autocomplete_fields = ['social_link']
    verbose_name = _('Social Media Link')
    verbose_name_plural = _('Social Media Links')


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ['name', 'url']
    search_fields = ['name', 'url']
    list_per_page = 25
    
    fieldsets = [
        (_('Link Information'), {
            'fields': ['name', 'url', 'logo'],
            'description': _('Create reusable links that can be used throughout the site')
        })
    ]


@admin.register(SocialMediaLink)
class SocialMediaLinkAdmin(admin.ModelAdmin):
    list_display = ['platform', 'url', 'usage_count']
    list_filter = ['platform']
    search_fields = ['url', 'platform']
    list_per_page = 25
    
    fieldsets = [
        (_('Social Media Information'), {
            'fields': ['platform', 'url'],
            'description': _('Create reusable social media links for your footer')
        })
    ]
    
    def usage_count(self, obj):
        return obj.footersocialmedia_set.count()
    usage_count.short_description = _('Used in Footer')


@admin.register(FooterLinkColumn)
class FooterLinkColumnAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'links_count']
    list_filter = ['footer']
    search_fields = ['title']
    ordering = ['order', 'title']
    list_per_page = 25
    
    inlines = [FooterColumnLinkInline]
    
    fieldsets = [
        (_('Column Configuration'), {
            'fields': ['title', 'order'],
            'description': _('Configure this link column. Add links using the tabular inline below.')
        })
    ]
    
    def links_count(self, obj):
        return obj.column_links.count()
    links_count.short_description = _('Number of Links')


@admin.register(Footer)
class FooterAdmin(admin.ModelAdmin):
    """
    Main footer configuration - Singleton pattern
    Manage everything from here or use dedicated pages
    """
    
    inlines = [FooterLinkColumnInline, FooterSocialMediaInline]
    
    fieldsets = [
        (_('Branding & Identity'), {
            'fields': ['logo', 'description'],
            'description': _('Configure your footer branding and main description'),
            'classes': ['wide']
        }),
        (_('Legal & Copyright'), {
            'fields': ['rights'],
            'description': _('Footer copyright and rights information'),
            'classes': ['wide']
        }),
        (_('Contact Us'), {
            'fields': ['contact_phone', 'contact_email', 'contact_address', 'contact_hours'],
            'description': _('Footer Contact Us column information'),
            'classes': ['wide']
        })
    ]
    
    def has_add_permission(self, request):
        """Only allow one Footer instance"""
        return not Footer.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of singleton footer"""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Auto-redirect to edit page if footer exists"""
        if Footer.objects.exists():
            footer = Footer.objects.first()
            return redirect(reverse('admin:siteconfig_footer_change', args=[footer.pk]))
        return super().changelist_view(request, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Add helpful context to the change view"""
        extra_context = extra_context or {}
        extra_context['title'] = 'Configure Footer'
        extra_context['subtitle'] = 'Manage footer branding, columns, and social media'
        return super().change_view(request, object_id, form_url, extra_context)


class SiteNavbarTitleOnlyItemsInline(admin.StackedInline):
    """Inline for managing title only items within navbar"""
    model = SiteNavbarTitleOnlyItems
    extra = 1
    fields = ['label', 'link', 'order']
    ordering = ['order']
    autocomplete_fields = ['link']
    verbose_name = _('Title Only Item')
    verbose_name_plural = _('Title Only Items')

class SiteNavbarDescribedItemsInline(admin.StackedInline):
    """Inline for managing title only items within navbar"""
    model = SiteNavbarDescribedItems
    extra = 1
    fields = ['label', 'link', 'description', 'order']
    ordering = ['order']
    autocomplete_fields = ['link']
    verbose_name = _('Described Item')
    verbose_name_plural = _('Described Items')

class SiteNavbarImageItemsInline(admin.StackedInline):
    """Inline for managing title only items within navbar"""
    model = SiteNavbarImageItems
    extra = 1
    fields = ['label', 'link', 'description', 'icon', 'order']
    ordering = ['order']
    autocomplete_fields = ['link']
    verbose_name = _('Image Item')
    verbose_name_plural = _('Image Items')


class InformationInline(admin.StackedInline):
    """Inline for managing site information boxes"""
    model = Information
    extra = 0
    fields = ('title', 'description', 'image', 'order')
    ordering = ('order',)
    verbose_name = _('Information Box')
    verbose_name_plural = _('Information Boxes')


@admin.register(SiteNavbar)
class SiteNavbarAdmin(admin.ModelAdmin):
    """
    Site Navbar configuration - Singleton pattern
    Manage everything from here or use dedicated pages
    """
    
    inlines = [SiteNavbarTitleOnlyItemsInline, SiteNavbarDescribedItemsInline, SiteNavbarImageItemsInline]
    
    fieldsets = [
        (_('Navbar'), {
            'fields': ['navbar_logo', 'navbar_links'],
            'description': _('Navbar Items + Logo'),
            'classes': ['wide']
        }),
        (_('Mega-Menu Titles'), {
            'fields': ['col1_title', 'col2_title', 'col3_title'],
            'description': _('Title of each column in mega-menu'),
            'classes': ['wide']
        }),
        (_('Mega-Menu Banner'), {
            'fields': ['banner_title', 'banner_link', 'banner_img'],
            'description': _('Banner info/image in mega-menu'),
            'classes': ['wide']
        }),
        (_('Mega-Menu Notification'), {
            'fields': ['notification'],
            'description': _('Notification message in mega-menu'),
            'classes': ['wide']
        })
    ]
    
    def has_add_permission(self, request):
        """Only allow one SiteNavbar instance"""
        return not SiteNavbar.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of singleton site navbar"""
        return False
    
    def changelist_view(self, request, extra_context=None):
        """Auto-redirect to edit page if footer exists"""
        if SiteNavbar.objects.exists():
            navbar = SiteNavbar.objects.first()
            return redirect(reverse('admin:siteconfig_sitenavbar_change', args=[navbar.pk]))
        return super().changelist_view(request, extra_context)
    
    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Add helpful context to the change view"""
        extra_context = extra_context or {}
        extra_context['title'] = 'Configure SiteNavbar'
        extra_context['subtitle'] = 'Manage Navbar items, banner and notification'
        return super().change_view(request, object_id, form_url, extra_context)

@admin.register(MainPage)
class MainPageAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        """Only allow one MainPage instance"""
        return not MainPage.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """Prevent deletion of singleton site navbar"""
        return False

    def changelist_view(self, request, extra_context=None):
        """Auto-redirect to edit page if MainPage exists"""
        if MainPage.objects.exists():
            navbar = MainPage.objects.first()
            return redirect(reverse('admin:siteconfig_mainpage_change', args=[navbar.pk]))
        return super().changelist_view(request, extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        """Add helpful context to the change view"""
        extra_context = extra_context or {}
        extra_context['title'] = 'Configure MainPage'
        extra_context['subtitle'] = 'Manage MainPage items'
        return super().change_view(request, object_id, form_url, extra_context)

    inlines = [InformationInline]

    # ── Fieldset layout ────────────────────────────────────────────────────────
    fieldsets = (
        (_('Landing Section'), {
            'description': _('Hero area at the top of the page.'),
            'fields': (
                ('landing_title', 'landing_brushed_title'),
                'landing_description',
                ('landing_link', 'landing_video'),
                'landing_image',
                ('icon1', 'feature1'),
                ('icon2', 'feature2'),
                ('icon3', 'feature3'),
                ('landing_message_title', 'landing_message_description'),
            ),
        }),
        (_('Statistics'), {
            'description': _('Four stat blocks shown on the homepage.'),
            'classes': ('collapse',),
            'fields': (
                ('stat1_title', 'stat1_description'),
                ('stat1_link',),

                ('stat2_title', 'stat2_description'),
                ('stat2_link',),

                ('stat3_title', 'stat3_description'),
                ('stat3_link',),

                ('stat4_title', 'stat4_description'),
                ('stat4_link',),
            ),
        }),
        (_('Advertisement Banner'), {
            'classes': ('collapse',),
            'fields': (
                'ad_title',
                'ad_description',
                'ad_link',
            ),
        }),
        (_('Dual Choice'), {
            'classes': ('collapse',),
            'fields': (
                ('choice1_title', 'choice1_link'),
                ('choice1_description',),
                ('choice1_image',),
                ('choice2_title', 'choice2_link'),
                ('choice2_description',),
                ('choice2_image',),
            )
        }),
        (_('User Experience Section'), {
            'description': _('Testimonials and top-user showcase.'),
            'classes': ('collapse',),
            'fields': (
                'ux_title',
                'ux_description',
                # Top users
                'ux_top_users_enable',
                'ux_top_users_title',
                'ux_top_users',
                # Comment 1
                'ux_comment1_text',
                'ux_comment1_user',
                'ux_comment1_rate',
                # Comment 2
                'ux_comment2_text',
                'ux_comment2_user',
                'ux_comment2_rate',
            ),
        }),
        (_('Top Teachers'), {
            'classes': ('collapse',),
            'fields': (
                'top_teachers_title',
                'top_teachers_description',
                'top_teachers_list'
            )
        }),
        (_('Imaged Links'), {
            'classes': ('collapse',),
            'fields': ('imaged_links_list',)
        }),
        (_('Course Demo'), {
            'classes': ('collapse',),
            'fields': ('top_courses_video',)
        }),
    )

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'is_visible')
    list_filter = ('is_visible',)
    search_fields = ('question', 'answer', 'order')
    ordering = ('order',)


@admin.register(AboutUs)
class AboutUsAdmin(admin.ModelAdmin):
    list_display = ('image_section_title', 'info_boxes_count', 'trust_links_count', 'info_section_title', 'trust_logo_section_title')
    search_fields = ('image_section_title', 'info_section_title', 'trust_logo_section_title')
    readonly_fields = ()

    fieldsets = (
        (_('Image Section'), {
            'fields': (
                'image_section_title',
                'image_section_top_right_image',
                'image_section_bottom_right_image',
                'image_section_middle_image',
                'image_section_bottom_left_image',
                'image_section_box_title',
                'image_section_box_description',
            ),
            'classes': ('wide',),
        }),
        (_('Info Section'), {
            'fields': (
                'info_section_title',
                'info_section_description',
                'info_section_information_boxes'
            ),
            'description': _('Select info boxes from inline table below.'),
            'classes': ('wide',),
        }),
        (_('Trust Logo Section'), {
            'fields': ('trust_logo_section_title', 'trust_logo_section_links'),
            'description': _('Select trust logo links from inline table below.'),
            'classes': ('wide',),
        }),
    )

    def info_boxes_count(self, obj):
        return obj.info_section_information_boxes.count()

    def trust_links_count(self, obj):
        return obj.trust_logo_section_links.count()

    info_boxes_count.short_description = _('Info Boxes')
    trust_links_count.short_description = _('Trust Links')

    def has_add_permission(self, request):
        return not AboutUs.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False

    def changelist_view(self, request, extra_context=None):
        if AboutUs.objects.exists():
            instance = AboutUs.objects.first()
            return redirect(reverse('admin:siteconfig_aboutus_change', args=[instance.pk]))
        return super().changelist_view(request, extra_context)
