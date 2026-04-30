from django.contrib import admin
from django.utils.html import format_html
from .models import Ticket, Message


class MessageInline(admin.StackedInline):
    model = Message
    extra = 0
    show_change_link = True
    fields = ('sender', 'body', 'attachment', 'is_staff_reply', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('created_at',)


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'subject',
        'user',
        'status_badge',
        'priority_badge',
        'category',
        'message_count',
        'updated_at',
    )

    list_filter = (
        'status',
        'priority',
        'category',
        'created_at',
    )

    search_fields = (
        'subject',
        'user__username',
        'user__email',
        'user__name',
    )

    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_select_related = ('user',)
    list_per_page = 50
    show_full_result_count = True

    readonly_fields = ('id', 'created_at', 'updated_at')

    inlines = [MessageInline]

    fieldsets = (
        (
            'Ticket Information',
            {
                'classes': ('tab-general',),
                'fields': (
                    'id',
                    'user',
                    'subject',
                    'category',
                ),
            },
        ),
        (
            'Status & Priority',
            {
                'classes': ('tab-status',),
                'fields': (
                    'status',
                    'priority',
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

    @admin.display(description='Status')
    def status_badge(self, obj):
        """Render a colored badge for ticket status.

        Args:
            obj: Ticket instance.

        Returns:
            SafeData: HTML badge.
        """
        color_map = {
            Ticket.StatusChoices.OPEN: '#28a745',
            Ticket.StatusChoices.IN_PROGRESS: '#007bff',
            Ticket.StatusChoices.WAITING_USER: '#ffc107',
            Ticket.StatusChoices.CLOSED: '#6c757d',
        }
        color = color_map.get(obj.status, '#343a40')
        return format_html(
            '<span style="padding:3px 8px; border-radius:10px; '
            'background:{}; color:#fff; font-weight:600;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description='Priority')
    def priority_badge(self, obj):
        """Render a colored badge for ticket priority.

        Args:
            obj: Ticket instance.

        Returns:
            SafeData: HTML badge.
        """
        color_map = {
            Ticket.PriorityChoices.LOW: '#6c757d',
            Ticket.PriorityChoices.MEDIUM: '#17a2b8',
            Ticket.PriorityChoices.HIGH: '#fd7e14',
            Ticket.PriorityChoices.URGENT: '#dc3545',
        }
        color = color_map.get(obj.priority, '#343a40')
        return format_html(
            '<span style="padding:3px 8px; border-radius:10px; '
            'background:{}; color:#fff; font-weight:600;">{}</span>',
            color,
            obj.get_priority_display(),
        )

    @admin.display(description='Messages')
    def message_count(self, obj):
        """Return the total message count for this ticket.

        Args:
            obj: Ticket instance.

        Returns:
            int: Message count.
        """
        return obj.message_count

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user').prefetch_related('messages')


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = (
        'id',
        'ticket',
        'sender',
        'is_staff_reply',
        'has_attachment',
        'created_at',
    )

    list_filter = (
        'is_staff_reply',
        'created_at',
        'ticket__status',
    )

    search_fields = (
        'body',
        'sender__username',
        'sender__email',
        'ticket__subject',
    )

    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_select_related = ('ticket', 'sender')
    list_per_page = 50
    readonly_fields = ('created_at',)

    fieldsets = (
        (
            'Message',
            {
                'classes': ('tab-general',),
                'fields': (
                    'ticket',
                    'sender',
                    'body',
                    'attachment',
                    'is_staff_reply',
                ),
            },
        ),
        (
            'Timestamps',
            {
                'classes': ('tab-timestamps',),
                'fields': ('created_at',),
            },
        ),
    )

    @admin.display(description='Attachment', boolean=True)
    def has_attachment(self, obj):
        """Return True if this message has an attachment.

        Args:
            obj: Message instance.

        Returns:
            bool: Whether an attachment exists.
        """
        return bool(obj.attachment)

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('ticket', 'sender')
