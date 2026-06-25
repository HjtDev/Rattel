from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone
from jalali_date import datetime2jalali
from jalali_date.fields import JalaliDateField, SplitJalaliDateTimeField
from jalali_date.widgets import AdminJalaliDateWidget, AdminSplitJalaliDateTime

from .progress_models import EpisodeProgress

_JALALI_FORMFIELD_OVERRIDES = {
    models.DateField: {'form_class': JalaliDateField, 'widget': AdminJalaliDateWidget},
    models.DateTimeField: {'form_class': SplitJalaliDateTimeField, 'widget': AdminSplitJalaliDateTime},
}


@admin.register(EpisodeProgress)
class EpisodeProgressAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = (
        'user_link',
        'course_link',
        'episode_title',
        'completion_status',
        'watch_count',
        'last_watched_at_jalali',
    )

    list_filter = (
        'is_completed',
        'course',
        'last_watched_at',
    )

    search_fields = (
        'user__username',
        'user__email',
        'course__name',
        'episode__title',
    )

    readonly_fields = (
        'user',
        'episode',
        'course',
        'created_at',
        'last_watched_at',
    )

    fieldsets = (
        (_('User & Content'), {
            'fields': ('user', 'course', 'episode')
        }),
        (_('Progress'), {
            'fields': ('is_completed', 'watch_count', 'watch_duration')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'last_watched_at')
        }),
    )

    @admin.display(description=_('Last Watched'))
    def last_watched_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.last_watched_at)).strftime('%Y/%m/%d %H:%M') if obj.last_watched_at else '—'

    def user_link(self, obj):
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username
        )
    user_link.short_description = _('User')
    user_link.admin_order_field = 'user__username'

    def course_link(self, obj):
        return format_html(
            '<a href="/admin/courses/course/{}/change/">{}</a>',
            obj.course.id,
            obj.course.name
        )
    course_link.short_description = _('Course')
    course_link.admin_order_field = 'course__name'

    def episode_title(self, obj):
        return obj.episode.title
    episode_title.short_description = _('Episode')
    episode_title.admin_order_field = 'episode__title'

    def completion_status(self, obj):
        if obj.is_completed:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ {}</span>',
                _('Completed'),
            )
        return format_html(
            '<span style="color: orange;">○ {}</span>',
            _('In Progress'),
        )
    completion_status.short_description = _('Status')
    completion_status.admin_order_field = 'is_completed'

    def has_add_permission(self, request):
        return False
