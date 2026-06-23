from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Category, InPersonClass, InPersonClassRegistration, TimeRange


@admin.register(TimeRange)
class TimeRangeAdmin(admin.ModelAdmin):
    list_display = ('label',)
    search_fields = ('label',)
    ordering = ('label',)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name', 'slug')
    ordering = ('name',)


@admin.register(InPersonClass)
class InPersonClassAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'start_date',
        'end_date',
        'price_display',
        'discount_display',
        'is_visible',
        'created_at',
    )

    list_filter = ('is_visible', 'start_date', 'categories')
    search_fields = ('title',)
    ordering = ('-start_date',)
    date_hierarchy = 'start_date'
    list_per_page = 50

    readonly_fields = ('id', 'created_at', 'updated_at')
    filter_horizontal = ('available_times', 'categories')

    fieldsets = (
        (
            _('Core Information'),
            {
                'fields': ('id', 'title', 'thumbnail', 'is_visible'),
            },
        ),
        (
            _('Description'),
            {
                'fields': ('short_description',),
            },
        ),
        (
            _('Pricing'),
            {
                'fields': ('price', 'new_price'),
            },
        ),
        (
            _('Schedule'),
            {
                'fields': ('start_date', 'end_date', 'available_times'),
            },
        ),
        (
            _('Categories'),
            {
                'fields': ('categories',),
            },
        ),
        (
            _('Timestamps'),
            {
                'fields': ('created_at', 'updated_at'),
            },
        ),
    )

    @admin.display(description=_('Price'))
    def price_display(self, obj):
        effective = obj.new_price if obj.new_price else obj.price
        return f'{effective:,} تومان'

    @admin.display(description=_('Discount'))
    def discount_display(self, obj):
        d = obj.discount
        if d:
            return format_html(
                '<span style="padding:3px 8px; border-radius:10px; '
                'background:#dc3545; color:#fff; font-weight:600;">{}%</span>',
                d,
            )
        return '—'


@admin.register(InPersonClassRegistration)
class InPersonClassRegistrationAdmin(admin.ModelAdmin):
    list_display = (
        'in_person_class',
        'time_range',
        'start_date',
        'end_date',
        'price',
        'registered_count',
        'created_at',
    )

    list_filter = ('in_person_class',)
    search_fields = ('in_person_class__title', 'time_range__label')
    list_select_related = ('in_person_class', 'time_range')
    ordering = ('-created_at',)
    list_per_page = 50

    readonly_fields = ('id', 'start_date', 'end_date', 'price', 'new_price', 'created_at')
    filter_horizontal = ('bought_by',)

    @admin.display(description=_('Registered'))
    def registered_count(self, obj):
        return obj.bought_by.count()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('bought_by')

    fieldsets = (
        (
            _('Registration'),
            {
                'fields': ('id', 'in_person_class', 'time_range'),
            },
        ),
        (
            _('Snapshot at Registration'),
            {
                'fields': ('start_date', 'end_date', 'price', 'new_price'),
            },
        ),
        (
            _('Students'),
            {
                'fields': ('bought_by',),
            },
        ),
        (
            _('Timestamps'),
            {
                'fields': ('created_at',),
            },
        ),
    )
