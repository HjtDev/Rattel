from django.contrib import admin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import AdminCallLog, AutomaticPlan, ClassRequest, PlanStep


class PlanStepInline(admin.TabularInline):
    model = PlanStep
    extra = 0
    fields = (
        'step_number', 'scheduled_date', 'step_type', 'page_start', 'page_end',
        'sub_part', 'status', 'is_delayed', 'completed_at', 'admin_note',
    )
    readonly_fields = ('step_number', 'is_delayed', 'completed_at', 'created_at')
    ordering = ('step_number',)
    show_change_link = True


class AdminCallLogInline(admin.TabularInline):
    model = AdminCallLog
    extra = 0
    fields = ('called_by', 'call_date', 'notes')
    readonly_fields = ('called_by', 'call_date')
    ordering = ('-call_date',)


@admin.register(ClassRequest)
class ClassRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'status_badge', 'created_at', 'updated_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username', 'user__phone', 'notes')
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    list_select_related = ('user',)

    fieldsets = (
        (_('Request'), {
            'fields': ('id', 'user', 'notes', 'status'),
        }),
        (_('Admin'), {
            'fields': ('admin_notes',),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        colors = {
            ClassRequest.Status.PENDING: '#f0ad4e',
            ClassRequest.Status.CONTACTED: '#5bc0de',
            ClassRequest.Status.PLAN_CREATED: '#5cb85c',
            ClassRequest.Status.REJECTED: '#d9534f',
        }
        color = colors.get(obj.status, '#aaa')
        return format_html(
            '<span style="padding:3px 10px;border-radius:10px;background:{};'
            'color:#fff;font-weight:600;">{}</span>',
            color, obj.get_status_display(),
        )


@admin.register(AutomaticPlan)
class AutomaticPlanAdmin(admin.ModelAdmin):
    list_display = (
        'user', 'teacher', 'page_range', 'status_badge',
        'progress_display', 'start_date', 'time_to_finish', 'created_at',
    )
    list_filter = ('status', 'time_freq', 'reading_freq', 'user_day_availability')
    search_fields = ('user__username', 'user__phone', 'teacher__username')
    ordering = ('-created_at',)
    readonly_fields = (
        'id', '_steps_generated', 'progress_display',
        'total_steps_display', 'created_at', 'updated_at',
    )
    list_select_related = ('user', 'teacher')
    inlines = [PlanStepInline, AdminCallLogInline]

    fieldsets = (
        (_('Participants'), {
            'fields': ('id', 'request', 'user', 'teacher'),
        }),
        (_('Plan Parameters'), {
            'fields': (
                'start_page', 'end_page', 'start_date', 'time_to_finish',
                'time_freq', 'reading_freq', 'review_freq',
            ),
        }),
        (_('User Availability'), {
            'fields': ('user_day_availability', 'user_time_availability'),
        }),
        (_('Status & Notes'), {
            'fields': ('status', 'admin_notes'),
        }),
        (_('Progress'), {
            'fields': ('_steps_generated', 'total_steps_display', 'progress_display'),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
        }),
    )

    @admin.display(description=_('Pages'))
    def page_range(self, obj):
        return f'{obj.start_page} – {obj.end_page}'

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        colors = {
            AutomaticPlan.Status.DRAFT: '#aaa',
            AutomaticPlan.Status.ACTIVE: '#5cb85c',
            AutomaticPlan.Status.COMPLETED: '#337ab7',
            AutomaticPlan.Status.CANCELLED: '#d9534f',
        }
        color = colors.get(obj.status, '#aaa')
        return format_html(
            '<span style="padding:3px 10px;border-radius:10px;background:{};'
            'color:#fff;font-weight:600;">{}</span>',
            color, obj.get_status_display(),
        )

    @admin.display(description=_('Progress'))
    def progress_display(self, obj):
        pct = obj.progress_percent
        color = '#5cb85c' if pct >= 80 else '#f0ad4e' if pct >= 40 else '#d9534f'
        return format_html(
            '<span style="color:{};">{}/{} ({}%)</span>',
            color, obj.completed_steps, obj.total_steps, pct,
        )

    @admin.display(description=_('Total Steps'))
    def total_steps_display(self, obj):
        return obj.total_steps


@admin.register(PlanStep)
class PlanStepAdmin(admin.ModelAdmin):
    list_display = (
        'plan', 'step_number', 'step_type', 'page_range',
        'scheduled_date', 'status_badge', 'is_delayed',
    )
    list_filter = ('status', 'step_type', 'is_delayed', 'scheduled_date')
    search_fields = ('plan__user__username', 'delay_reason', 'admin_note')
    ordering = ('plan', 'step_number')
    readonly_fields = ('id', 'is_delayed', 'original_scheduled_date', 'completed_at', 'created_at')
    list_select_related = ('plan__user',)

    fieldsets = (
        (_('Step'), {
            'fields': ('id', 'plan', 'step_number', 'step_type', 'sub_part'),
        }),
        (_('Content'), {
            'fields': ('page_start', 'page_end'),
        }),
        (_('Schedule & Status'), {
            'fields': ('scheduled_date', 'status', 'is_delayed', 'original_scheduled_date', 'completed_at'),
        }),
        (_('Notes'), {
            'fields': ('delay_reason', 'admin_note'),
        }),
        (_('Timestamps'), {
            'fields': ('created_at',),
        }),
    )

    @admin.display(description=_('Pages'))
    def page_range(self, obj):
        if obj.page_start == obj.page_end:
            return f'p.{obj.page_start}'
        return f'pp.{obj.page_start}–{obj.page_end}'

    @admin.display(description=_('Status'))
    def status_badge(self, obj):
        colors = {
            PlanStep.Status.PENDING: '#f0ad4e',
            PlanStep.Status.DELAYED: '#d9534f',
            PlanStep.Status.COMPLETED: '#5cb85c',
            PlanStep.Status.SKIPPED: '#aaa',
        }
        color = colors.get(obj.status, '#aaa')
        return format_html(
            '<span style="padding:2px 8px;border-radius:8px;background:{};'
            'color:#fff;font-weight:600;">{}</span>',
            color, obj.get_status_display(),
        )


@admin.register(AdminCallLog)
class AdminCallLogAdmin(admin.ModelAdmin):
    list_display = ('called_by', 'plan', 'call_date', 'notes_preview')
    list_filter = ('call_date',)
    search_fields = ('plan__user__username', 'called_by__username', 'notes')
    ordering = ('-call_date',)
    readonly_fields = ('id', 'created_at')
    list_select_related = ('called_by', 'plan__user')

    @admin.display(description=_('Notes'))
    def notes_preview(self, obj):
        return obj.notes[:80] + '…' if len(obj.notes) > 80 else obj.notes
