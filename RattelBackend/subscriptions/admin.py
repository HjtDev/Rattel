from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from jalali_date import date2jalali, datetime2jalali
from jalali_date.fields import JalaliDateField, SplitJalaliDateTimeField
from jalali_date.widgets import AdminJalaliDateWidget, AdminSplitJalaliDateTime

from .models import Plan, UserSubscription

_JALALI_FORMFIELD_OVERRIDES = {
    models.DateField: {'form_class': JalaliDateField, 'widget': AdminJalaliDateWidget},
    models.DateTimeField: {'form_class': SplitJalaliDateTimeField, 'widget': AdminSplitJalaliDateTime},
}


class UserSubscriptionInline(admin.TabularInline):
    model = UserSubscription
    extra = 0
    fields = ('user', 'started_at', 'ends_in', 'is_active_display')
    readonly_fields = ('is_active_display', 'started_at')
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES

    @admin.display(description=_('Active Subscription'))
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;font-weight:bold;">✓</span>')
        return format_html('<span style="color:red;font-weight:bold;">✗</span>')


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = (
        'name',
        'price_display',
        'discount_display',
        'duration_days',
        'has_early_news_access',
        'has_quiz_access',
        'online_class_limit',
        'subscriber_count',
        'is_visible',
        'created_at_jalali',
    )
    list_filter = ('is_visible', 'has_early_news_access', 'has_quiz_access', 'online_class_limit')
    search_fields = ('name',)
    ordering = ('price',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    filter_horizontal = ('bought_by',)
    inlines = [UserSubscriptionInline]

    fieldsets = (
        (_('Core Information'), {
            'fields': ('id', 'name', 'picture', 'is_visible'),
        }),
        (_('Pricing'), {
            'fields': ('price', 'new_price', 'duration_days'),
        }),
        (_('Features'), {
            'fields': ('has_early_news_access', 'has_quiz_access', 'has_free_course_access', 'online_class_limit'),
        }),
        (_('Subscribers'), {
            'fields': ('bought_by',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description=_('Created At'))
    def created_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.created_at)).strftime('%Y/%m/%d %H:%M')

    @admin.display(description=_('Price'))
    def price_display(self, obj):
        effective = obj.new_price if obj.new_price else obj.price
        return f'{effective:,} تومان'

    @admin.display(description=_('Discount'))
    def discount_display(self, obj):
        d = obj.discount
        if d:
            return format_html(
                '<span style="padding:3px 8px;border-radius:10px;'
                'background:#dc3545;color:#fff;font-weight:600;">{}%</span>',
                d,
            )
        return '—'

    @admin.display(description=_('Subscribers'))
    def subscriber_count(self, obj):
        return obj.subscriptions.count()

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('subscriptions')


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = ('user', 'plan', 'started_at_jalali', 'ends_in_jalali', 'is_active_display')
    list_filter = ('plan',)
    search_fields = ('user__username', 'user__phone', 'plan__name')
    ordering = ('-ends_in',)
    list_select_related = ('user', 'plan')
    readonly_fields = ('is_active_display', 'started_at')

    @admin.display(description=_('Started At'))
    def started_at_jalali(self, obj):
        return date2jalali(obj.started_at).strftime('%Y/%m/%d')

    @admin.display(description=_('Ends In'))
    def ends_in_jalali(self, obj):
        return date2jalali(obj.ends_in).strftime('%Y/%m/%d')

    @admin.display(description=_('Active Subscription'))
    def is_active_display(self, obj):
        if obj.is_active:
            return format_html('<span style="color:green;font-weight:bold;">Active</span>')
        return format_html('<span style="color:red;font-weight:bold;">Expired</span>')
