from django.contrib import admin
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from jalali_date import datetime2jalali
from jalali_date.fields import JalaliDateField, SplitJalaliDateTimeField
from jalali_date.widgets import AdminJalaliDateWidget, AdminSplitJalaliDateTime

from .models import (
    AttemptAnswer,
    Category,
    Question,
    QuestionOption,
    Quiz,
    QuizAccessRequirement,
    QuizAttempt,
)

_JALALI_FORMFIELD_OVERRIDES = {
    models.DateField: {'form_class': JalaliDateField, 'widget': AdminJalaliDateWidget},
    models.DateTimeField: {'form_class': SplitJalaliDateTimeField, 'widget': AdminSplitJalaliDateTime},
}


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ('name',)


class QuizAccessRequirementInline(admin.TabularInline):
    model = QuizAccessRequirement
    fk_name = 'quiz'
    extra = 0
    fields = ('type', 'required_quiz', 'required_score')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = ('title', 'difficulty', 'is_active', 'start_date_jalali', 'end_date_jalali', 'created_at_jalali')
    list_filter = ('is_active', 'difficulty', 'categories')
    search_fields = ('title',)
    ordering = ('-created_at',)
    readonly_fields = ('id', 'created_at', 'updated_at')
    filter_horizontal = ('categories',)
    inlines = [QuizAccessRequirementInline]

    fieldsets = (
        (_('Core Information'), {
            'fields': ('id', 'title', 'thumbnail', 'categories', 'difficulty', 'is_active'),
        }),
        (_('Description'), {
            'fields': ('description',),
        }),
        (_('Settings'), {
            'fields': (
                'randomize_question_order', 'max_attempts_per_user', 'reveal_answers_during_quiz',
            ),
        }),
        (_('Schedule'), {
            'fields': ('start_date', 'end_date'),
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )

    @admin.display(description=_('Start Date'))
    def start_date_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.start_date)).strftime('%Y/%m/%d %H:%M') if obj.start_date else '—'

    @admin.display(description=_('End Date'))
    def end_date_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.end_date)).strftime('%Y/%m/%d %H:%M') if obj.end_date else '—'

    @admin.display(description=_('Created At'))
    def created_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.created_at)).strftime('%Y/%m/%d %H:%M')


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4
    max_num = 4
    fields = ('text', 'is_correct', 'order')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = ('text_short', 'quiz', 'type', 'order', 'score', 'time_to_answer')
    list_filter = ('quiz', 'type')
    search_fields = ('text',)
    ordering = ('quiz', 'order')
    readonly_fields = ('id', 'created_at', 'updated_at')
    inlines = [QuestionOptionInline]

    @admin.display(description=_('Question'))
    def text_short(self, obj: Question):
        return obj.text[:80]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = ('user', 'quiz', 'score', 'correct_count', 'incorrect_count', 'status', 'started_at_jalali', 'finished_at_jalali')
    list_filter = ('status', 'quiz')
    search_fields = ('user__username',)
    ordering = ('-started_at',)
    readonly_fields = (
        'id', 'quiz', 'user', 'started_at', 'finished_at',
        'score', 'correct_count', 'incorrect_count', 'time_spent', 'status',
        'created_at', 'updated_at',
    )

    @admin.display(description=_('Started At'))
    def started_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.started_at)).strftime('%Y/%m/%d %H:%M')

    @admin.display(description=_('Finished At'))
    def finished_at_jalali(self, obj):
        return datetime2jalali(timezone.localtime(obj.finished_at)).strftime('%Y/%m/%d %H:%M') if obj.finished_at else '—'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AttemptAnswer)
class AttemptAnswerAdmin(admin.ModelAdmin):
    formfield_overrides = _JALALI_FORMFIELD_OVERRIDES
    list_display = ('attempt', 'question', 'selected_option', 'is_correct', 'time_taken')
    list_filter = ('is_correct',)
    readonly_fields = ('attempt', 'question', 'selected_option', 'is_correct', 'time_taken')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
