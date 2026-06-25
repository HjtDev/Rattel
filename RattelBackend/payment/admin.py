from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.utils import timezone
from jalali_date import datetime2jalali
from jalali_date.fields import JalaliDateField, SplitJalaliDateTimeField
from jalali_date.widgets import AdminJalaliDateWidget, AdminSplitJalaliDateTime

from .models import Transaction

_JALALI_FORMFIELD_OVERRIDES = {
    models.DateField: {'form_class': JalaliDateField, 'widget': AdminJalaliDateWidget},
    models.DateTimeField: {'form_class': SplitJalaliDateTimeField, 'widget': AdminSplitJalaliDateTime},
}


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = (
        'id',
        'user',
        'amount_display',
        'currency',
        'transaction_type',
        'transaction_reason',
        'transaction_status_badge',
        'provider',
        'tracking_id',
        'locked_in',
        'created_at_jalali',
    )

    list_filter = (
        'transaction_status',
        'transaction_type',
        'transaction_reason',
        'currency',
        'provider',
        'locked_in',
        'created_at',
    )

    search_fields = (
        'id',
        'tracking_id',
        'user__username',
        'user__email',
        'provider',
    )

    ordering = ('-created_at',)
    date_hierarchy = 'created_at'

    list_select_related = ('user',)

    list_per_page = 50
    show_full_result_count = True

    readonly_fields = (
        'id',
        'created_at',
        'updated_at',
        'provider',
        'tracking_id',
        'locked_in'
    )

    fieldsets = (
        (
            _('Core Information'),
            {
                'classes': ('tab-general',),
                'fields': (
                    'id',
                    'user',
                    'amount',
                    'currency',
                    'transaction_type',
                    'transaction_reason',
                    'transaction_status',
                    'locked_in'
                ),
            },
        ),
        (
            _('Provider & Tracking'),
            {
                'classes': ('tab-provider',),
                'fields': (
                    'provider',
                    'tracking_id',
                    'provider_payload',
                ),
            },
        ),
        (
            _('Metadata & Description'),
            {
                'classes': ('tab-metadata',),
                'fields': (
                    'metadata',
                    'description',
                ),
            },
        ),
        (
            _('Timestamps'),
            {
                'classes': ('tab-timestamps',),
                'fields': (
                    'created_at',
                    'updated_at',
                ),
            },
        ),
    )

    @admin.display(description=_('Created At'))
    def created_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.created_at)).strftime('%Y/%m/%d %H:%M')

    @admin.display(description=_('Amount'))
    def amount_display(self, obj):
        return f'{obj.amount:,} {obj.currency}'

    @admin.display(description=_('Status'))
    def transaction_status_badge(self, obj):
        color_map = {
            Transaction.TransactionStatus.SUCCESS: '#28a745',
            Transaction.TransactionStatus.PENDING: '#ffc107',
            Transaction.TransactionStatus.FAILED: '#dc3545',
            Transaction.TransactionStatus.REFUNDED: '#17a2b8',
        }
        color = color_map.get(obj.transaction_status, '#343a40')
        return format_html(
            '<span style="padding:3px 8px; border-radius:10px; '
            'background:{}; color:#fff; font-weight:600;">{}</span>',
            color,
            obj.get_transaction_status_display(),
        )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('user')
