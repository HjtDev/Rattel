from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from jalali_date import datetime2jalali
from jalali_date.fields import JalaliDateField, SplitJalaliDateTimeField
from jalali_date.widgets import AdminJalaliDateWidget, AdminSplitJalaliDateTime

from .models import Gallery, GalleryContent

_JALALI_FORMFIELD_OVERRIDES = {
    models.DateField: {'form_class': JalaliDateField, 'widget': AdminJalaliDateWidget},
    models.DateTimeField: {'form_class': SplitJalaliDateTimeField, 'widget': AdminSplitJalaliDateTime},
}


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
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES


@admin.register(Gallery)
class GalleryAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = ('title', 'content_count', 'created_at_jalali', 'updated_at_jalali')
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

    @admin.display(description=_('Created At'))
    def created_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.created_at)).strftime('%Y/%m/%d %H:%M')

    @admin.display(description=_('Updated At'))
    def updated_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.updated_at)).strftime('%Y/%m/%d %H:%M')

    @admin.display(description=_('Content Count'))
    def content_count(self, obj):
        return obj.content.count()


@admin.register(GalleryContent)
class GalleryContentAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = ('gallery', 'content_type', 'order', 'has_file', 'created_at_jalali')
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

    @admin.display(description=_('Created At'))
    def created_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.created_at)).strftime('%Y/%m/%d %H:%M')

    @admin.display(boolean=True, description=_('Has File'))
    def has_file(self, obj):
        return bool(obj.image or obj.video or obj.audio or obj.embed_code.strip())
