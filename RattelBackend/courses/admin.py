from django.contrib import admin
from django.utils.html import format_html

from .models import Course, Chapter, Episode
from .progress_admin import *  # Import progress admin


class ChapterInline(admin.StackedInline):
    model = Chapter
    extra = 0
    show_change_link = True
    fields = ('title', 'order', 'description', 'number_of_files', 'number_of_videos', 'is_free', 'is_visible')
    ordering = ('order',)


class EpisodeInline(admin.StackedInline):
    model = Episode
    extra = 0
    fields = ('title', 'type', 'file')


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'teacher',
        'category',
        'difficulty',
        'age_group',
        'price_display',
        'discount_display',
        'total_sell',
        'is_visible',
        'created_at',
    )

    list_filter = (
        'category',
        'difficulty',
        'age_group',
        'created_at',
    )

    search_fields = (
        'name',
        'teacher__username',
        'teacher__email',
    )

    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_select_related = ('teacher',)
    list_per_page = 50

    readonly_fields = ('id', 'created_at', 'updated_at')

    filter_horizontal = ('bought_by',)

    inlines = [ChapterInline]

    fieldsets = (
        (
            'Core Information',
            {
                'classes': ('tab-general',),
                'fields': (
                    'id',
                    'name',
                    'teacher',
                    'category',
                    'difficulty',
                    'age_group',
                    'rating',
                    'image',
                    'intro_video',
                    'is_visible',
                ),
            },
        ),
        (
            'Description',
            {
                'classes': ('tab-description',),
                'fields': (
                    'short_description',
                    'long_description',
                ),
            },
        ),
        (
            'Pricing',
            {
                'classes': ('tab-pricing',),
                'fields': (
                    'price',
                    'new_price',
                    'extra_sells',
                ),
            },
        ),
        (
            'Students',
            {
                'classes': ('tab-students',),
                'fields': ('bought_by',),
            },
        ),
        (
            'Timestamps',
            {
                'classes': ('tab-timestamps',),
                'fields': ('total_time', 'created_at', 'updated_at'),
            },
        ),
    )

    @admin.display(description='Price')
    def price_display(self, obj):
        """Display effective price with Toman label.

        Args:
            obj: Course instance.

        Returns:
            str: Formatted price string.
        """
        effective = obj.new_price if obj.new_price else obj.price
        return f'{effective:,} تومان'

    @admin.display(description='Discount')
    def discount_display(self, obj):
        """Display discount badge if applicable.

        Args:
            obj: Course instance.

        Returns:
            str or SafeData: Discount badge HTML or dash.
        """
        d = obj.discount
        if d:
            return format_html(
                '<span style="padding:3px 8px; border-radius:10px; '
                'background:#dc3545; color:#fff; font-weight:600;">{}%</span>',
                d,
            )
        return '—'

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('teacher')


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'course',
        'order',
        'number_of_files',
        'number_of_videos',
        'is_free',
        'is_visible',
        'created_at',
    )

    list_filter = ('is_free', 'is_visible', 'course')
    search_fields = ('title', 'course__name')
    ordering = ('course', 'order')
    list_select_related = ('course',)

    readonly_fields = ('number_of_videos', 'number_of_files', 'created_at', 'updated_at')

    inlines = [EpisodeInline]

    fieldsets = (
        (
            'Chapter Info',
            {
                'fields': ('course', 'title', 'order', 'description', 'is_free', 'is_visible'),
            },
        ),
        (
            'Content Counts',
            {
                'fields': ('number_of_files', 'number_of_videos'),
            },
        ),
        (
            'Timestamps',
            {
                'fields': ('created_at', 'updated_at'),
            },
        ),
    )


@admin.register(Episode)
class EpisodeAdmin(admin.ModelAdmin):
    list_display = ('title', 'chapter', 'type', 'created_at')
    list_filter = ('type', 'chapter__course')
    search_fields = ('title', 'chapter__title', 'chapter__course__name')
    list_select_related = ('chapter', 'chapter__course')
    ordering = ('chapter', 'id')
    readonly_fields = ('created_at',)
