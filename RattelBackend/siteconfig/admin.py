from django.contrib import admin
from django.shortcuts import redirect
from django.urls import reverse
from .models import (
    Link,
    FooterLinkColumn,
    FooterColumnLink,
    SocialMediaLink,
    FooterSocialMedia,
    Footer
)


class FooterColumnLinkInline(admin.TabularInline):
    """Inline for managing links within a column"""
    model = FooterColumnLink
    extra = 1
    fields = ['link', 'label', 'order']
    ordering = ['order']
    autocomplete_fields = ['link']
    verbose_name = 'Link'
    verbose_name_plural = 'Links in this Column'


class FooterLinkColumnInline(admin.StackedInline):
    """Inline for managing columns within footer"""
    model = FooterLinkColumn
    extra = 0
    fields = ['title', 'order']
    ordering = ['order']
    show_change_link = True
    verbose_name = 'Link Column'
    verbose_name_plural = 'Footer Link Columns'


class FooterSocialMediaInline(admin.TabularInline):
    """Inline for managing social media links in footer"""
    model = FooterSocialMedia
    extra = 1
    fields = ['social_link', 'order']
    ordering = ['order']
    autocomplete_fields = ['social_link']
    verbose_name = 'Social Media Link'
    verbose_name_plural = 'Social Media Links'


@admin.register(Link)
class LinkAdmin(admin.ModelAdmin):
    list_display = ['name', 'url', 'usage_count']
    search_fields = ['name', 'url']
    list_per_page = 25
    
    fieldsets = [
        ('Link Information', {
            'fields': ['name', 'url'],
            'description': 'Create reusable links that can be used throughout the footer columns'
        })
    ]
    
    def usage_count(self, obj):
        return obj.footercolumnlink_set.count()
    usage_count.short_description = 'Used in Columns'


@admin.register(SocialMediaLink)
class SocialMediaLinkAdmin(admin.ModelAdmin):
    list_display = ['platform', 'url', 'usage_count']
    list_filter = ['platform']
    search_fields = ['url', 'platform']
    list_per_page = 25
    
    fieldsets = [
        ('Social Media Information', {
            'fields': ['platform', 'url'],
            'description': 'Create reusable social media links for your footer'
        })
    ]
    
    def usage_count(self, obj):
        return obj.footersocialmedia_set.count()
    usage_count.short_description = 'Used in Footer'


@admin.register(FooterLinkColumn)
class FooterLinkColumnAdmin(admin.ModelAdmin):
    list_display = ['title', 'order', 'links_count']
    list_filter = ['footer']
    search_fields = ['title']
    ordering = ['order', 'title']
    list_per_page = 25
    
    inlines = [FooterColumnLinkInline]
    
    fieldsets = [
        ('Column Configuration', {
            'fields': ['title', 'order'],
            'description': 'Configure this link column. Add links using the tabular inline below.'
        })
    ]
    
    def links_count(self, obj):
        return obj.column_links.count()
    links_count.short_description = 'Number of Links'


@admin.register(Footer)
class FooterAdmin(admin.ModelAdmin):
    """
    Main footer configuration - Singleton pattern
    Manage everything from here or use dedicated pages
    """
    
    inlines = [FooterLinkColumnInline, FooterSocialMediaInline]
    
    fieldsets = [
        ('Branding & Identity', {
            'fields': ['logo', 'description'],
            'description': 'Configure your footer branding and main description',
            'classes': ['wide']
        }),
        ('Legal & Copyright', {
            'fields': ['rights'],
            'description': 'Footer copyright and rights information',
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
