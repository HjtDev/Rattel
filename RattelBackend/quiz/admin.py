from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from .models import (
    AttemptAnswer,
    Category,
    Question,
    QuestionOption,
    Quiz,
    QuizAccessRequirement,
    QuizAttempt,
)


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
    list_display = ('title', 'difficulty', 'is_active', 'start_date', 'end_date', 'created_at')
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


class QuestionOptionInline(admin.TabularInline):
    model = QuestionOption
    extra = 4
    max_num = 4
    fields = ('text', 'is_correct', 'order')


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
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
    list_display = ('user', 'quiz', 'score', 'correct_count', 'incorrect_count', 'status', 'started_at', 'finished_at')
    list_filter = ('status', 'quiz')
    search_fields = ('user__username',)
    ordering = ('-started_at',)
    readonly_fields = (
        'id', 'quiz', 'user', 'started_at', 'finished_at',
        'score', 'correct_count', 'incorrect_count', 'time_spent', 'status',
        'created_at', 'updated_at',
    )

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False


@admin.register(AttemptAnswer)
class AttemptAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_option', 'is_correct', 'time_taken')
    list_filter = ('is_correct',)
    readonly_fields = ('attempt', 'question', 'selected_option', 'is_correct', 'time_taken')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False
