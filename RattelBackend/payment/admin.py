from django.contrib import admin
from django.utils.html import format_html
from .models import Transaction


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
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
        'created_at',
    )
    
    list_filter = (
        'transaction_status',
        'transaction_type',
        'transaction_reason',
        'currency',
        'provider',
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
        'tracking_id'
    )
    
    fieldsets = (
        (
            'Core Information',
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
                ),
            },
        ),
        (
            'Provider & Tracking',
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
            'Metadata & Description',
            {
                'classes': ('tab-metadata',),
                'fields': (
                    'metadata',
                    'description',
                ),
            },
        ),
        (
            'Timestamps',
            {
                'classes': ('tab-timestamps',),
                'fields': (
                    'created_at',
                    'updated_at',
                ),
            },
        ),
    )
    
    @admin.display(description='Amount')
    def amount_display(self, obj):
        return f'{obj.amount:,} {obj.currency}'
    
    @admin.display(description='Status')
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

