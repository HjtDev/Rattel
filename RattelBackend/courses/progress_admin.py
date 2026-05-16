from django.contrib import admin
from django.utils.html import format_html
from .progress_models import EpisodeProgress


@admin.register(EpisodeProgress)
class EpisodeProgressAdmin(admin.ModelAdmin):
    list_display = (
        'user_link',
        'course_link',
        'episode_title',
        'completion_status',
        'watch_count',
        'last_watched_at',
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
        ('User & Content', {
            'fields': ('user', 'course', 'episode')
        }),
        ('Progress', {
            'fields': ('is_completed', 'watch_count', 'watch_duration')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'last_watched_at')
        }),
    )
    
    def user_link(self, obj):
        """Display user as clickable link."""
        return format_html(
            '<a href="/admin/users/user/{}/change/">{}</a>',
            obj.user.id,
            obj.user.username
        )
    user_link.short_description = 'User'
    user_link.admin_order_field = 'user__username'
    
    def course_link(self, obj):
        """Display course as clickable link."""
        return format_html(
            '<a href="/admin/courses/course/{}/change/">{}</a>',
            obj.course.id,
            obj.course.name
        )
    course_link.short_description = 'Course'
    course_link.admin_order_field = 'course__name'
    
    def episode_title(self, obj):
        """Display episode title."""
        return obj.episode.title
    episode_title.short_description = 'Episode'
    episode_title.admin_order_field = 'episode__title'
    
    def completion_status(self, obj):
        """Display completion status with icon."""
        if obj.is_completed:
            return format_html(
                '<span style="color: green; font-weight: bold;">✓ Completed</span>'
            )
        return format_html(
            '<span style="color: orange;">○ In Progress</span>'
        )
    completion_status.short_description = 'Status'
    completion_status.admin_order_field = 'is_completed'
    
    def has_add_permission(self, request):
        """Disable manual creation of progress records."""
        return False
