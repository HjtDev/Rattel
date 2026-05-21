from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import Gallery, GalleryContent


class GalleryContentInline(admin.StackedInline):
    model = GalleryContent
    extra = 0
    show_change_link = True
    fields = (
        'content_type',
        'order',
        'image',
        'video',
        'audio',
        'embed_code',
        'created_at',
        'updated_at',
    )
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('order', 'id')


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    list_display = ('title', 'content_count', 'created_at', 'updated_at')
    list_display_links = ('title',)
    search_fields = ('title',)
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = (GalleryContentInline,)
    fieldsets = (
        (
            _('General'),
            {
                'classes': ('tab-general',),
                'fields': ('id', 'title', 'thumbnail'),
            },
        ),
        (
            _('Timestamps'),
            {
                'classes': ('tab-timestamps',),
                'fields': ('created_at', 'updated_at'),
            },
        ),
    )

    @admin.display(description=_('Content Count'))
    def content_count(self, obj):
        return obj.content.count()


@admin.register(GalleryContent)
class GalleryContentAdmin(admin.ModelAdmin):
    list_display = ('gallery', 'content_type', 'order', 'has_file', 'created_at')
    list_filter = ('content_type', 'gallery', 'created_at')
    search_fields = ('gallery__title', 'embed_code')
    ordering = ('gallery', 'order', 'id')
    readonly_fields = ('created_at', 'updated_at')
    autocomplete_fields = ('gallery',)
    fieldsets = (
        (
            _('Relations'),
            {
                'classes': ('tab-relations',),
                'fields': ('gallery', 'content_type', 'order'),
            },
        ),
        (
            _('Media'),
            {
                'classes': ('tab-media',),
                'fields': ('image', 'video', 'audio', 'embed_code'),
            },
        ),
        (
            _('Timestamps'),
            {
                'classes': ('tab-timestamps',),
                'fields': ('created_at', 'updated_at'),
            },
        ),
    )

    @admin.display(boolean=True, description=_('Has File'))
    def has_file(self, obj):
        return bool(obj.image or obj.video or obj.audio or obj.embed_code.strip())
