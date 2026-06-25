import uuid

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField

from RattelBackend.cache import invalidate_cache


class Category(models.Model):
    class Meta:
        verbose_name = _('Quiz Category')
        verbose_name_plural = _('Quiz Categories')
        ordering = ('name',)

    name = models.CharField(max_length=120, unique=True, verbose_name=_('Name'))
    slug = models.SlugField(max_length=140, unique=True, allow_unicode=True, verbose_name=_('Slug'))

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_cache('quiz_list')
        invalidate_cache('quiz_categories')

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        invalidate_cache('quiz_list')
        invalidate_cache('quiz_categories')
        return result


class Quiz(models.Model):
    class Difficulty(models.TextChoices):
        EASY = 'easy', _('Easy')
        MEDIUM = 'medium', _('Medium')
        HARD = 'hard', _('Hard')

    class Meta:
        verbose_name = _('Quiz')
        verbose_name_plural = _('Quizzes')
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['is_active', 'created_at']),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    description = HTMLField(verbose_name=_('Description'))
    thumbnail = models.FileField(
        upload_to='quiz/thumbnails/',
        blank=True,
        null=True,
        verbose_name=_('Thumbnail'),
    )
    categories = models.ManyToManyField(
        Category,
        related_name='quizzes',
        blank=True,
        verbose_name=_('Categories'),
    )
    difficulty = models.CharField(
        max_length=10,
        choices=Difficulty.choices,
        default=Difficulty.MEDIUM,
        verbose_name=_('Difficulty'),
    )
    is_active = models.BooleanField(default=True, verbose_name=_('Is Active'))
    randomize_question_order = models.BooleanField(
        default=False,
        verbose_name=_('Randomize Question Order'),
    )
    max_attempts_per_user = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Max Attempts Per User'),
        help_text=_('0 means unlimited'),
    )
    reveal_answers_during_quiz = models.BooleanField(
        default=False,
        verbose_name=_('Reveal Answers During Quiz'),
    )
    allow_retry_on_expiry = models.BooleanField(
        default=True,
        verbose_name=_('Allow Retry on Expiry'),
        help_text=_('If enabled, expired (timed-out) attempts do not count against the attempt limit.'),
    )
    start_date = models.DateTimeField(null=True, blank=True, verbose_name=_('Start Date'))
    end_date = models.DateTimeField(null=True, blank=True, verbose_name=_('End Date'))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_cache('quiz_list')

    def delete(self, *args, **kwargs):
        if self.thumbnail:
            self.thumbnail.delete(save=False)
        result = super().delete(*args, **kwargs)
        invalidate_cache('quiz_list')
        return result


class Question(models.Model):
    class Type(models.TextChoices):
        MULTIPLE_CHOICE = 'multiple_choice', _('Multiple Choice')
        FILL_BLANK = 'fill_blank', _('Fill in the Blank')
        TRUE_FALSE = 'true_false', _('True / False')
        MATCHING = 'matching', _('Matching')

    class Meta:
        verbose_name = _('Question')
        verbose_name_plural = _('Questions')
        ordering = ('order',)
        indexes = [
            models.Index(fields=['quiz', 'order']),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name=_('Quiz'),
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.MULTIPLE_CHOICE,
        verbose_name=_('Question Type'),
    )
    text = models.TextField(verbose_name=_('Question Text'))
    image = models.FileField(
        upload_to='quiz/questions/',
        blank=True,
        null=True,
        verbose_name=_('Question Image'),
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    score = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('Score'),
    )
    time_to_answer = models.PositiveIntegerField(
        default=30,
        verbose_name=_('Time to Answer (seconds)'),
        help_text=_('Contributes to the quiz global timer; not enforced per-question.'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    def __str__(self):
        return f'{self.quiz.title} — Q{self.order}: {self.text[:60]}'

    def delete(self, *args, **kwargs):
        if self.image:
            self.image.delete(save=False)
        return super().delete(*args, **kwargs)


class QuestionOption(models.Model):
    class Meta:
        verbose_name = _('Question Option')
        verbose_name_plural = _('Question Options')
        ordering = ('order',)

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='options',
        verbose_name=_('Question'),
    )
    text = models.CharField(max_length=500, verbose_name=_('Option Text'))
    is_correct = models.BooleanField(default=False, verbose_name=_('Is Correct'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))

    def __str__(self):
        return f'{self.text[:60]} {"✓" if self.is_correct else ""}'


class MatchingPair(models.Model):
    class Meta:
        verbose_name = _('Matching Pair')
        verbose_name_plural = _('Matching Pairs')
        ordering = ('order',)
        indexes = [models.Index(fields=['question', 'order'])]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='pairs',
        verbose_name=_('Question'),
    )
    left_text = models.CharField(max_length=500, verbose_name=_('Left Text'))
    right_text = models.CharField(max_length=500, verbose_name=_('Right Text'))
    left_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    right_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))

    def __str__(self):
        return f'{self.left_text[:40]} ↔ {self.right_text[:40]}'


class QuizAccessRequirement(models.Model):
    class Type(models.TextChoices):
        FREE = 'free', _('Free')
        COMPLETED_QUIZ = 'completed_quiz', _('Completed Quiz')
        MIN_SCORE = 'min_score', _('Minimum Score')
        SUBSCRIPTION = 'subscription', _('Subscription Required')

    class Meta:
        verbose_name = _('Quiz Access Requirement')
        verbose_name_plural = _('Quiz Access Requirements')

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='access_requirements',
        verbose_name=_('Quiz'),
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.FREE,
        verbose_name=_('Requirement Type'),
    )
    required_quiz = models.ForeignKey(
        Quiz,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='required_by',
        verbose_name=_('Required Quiz'),
    )
    required_score = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Required Score'),
    )

    def __str__(self):
        return f'{self.quiz.title} — {self.get_type_display()}'


class QuizAttempt(models.Model):
    class Status(models.TextChoices):
        IN_PROGRESS = 'in_progress', _('In Progress')
        COMPLETED = 'completed', _('Completed')
        EXPIRED = 'expired', _('Expired')

    class Meta:
        verbose_name = _('Quiz Attempt')
        verbose_name_plural = _('Quiz Attempts')
        ordering = ('-created_at',)
        indexes = [
            models.Index(fields=['user', 'quiz']),
            models.Index(fields=['user', 'status']),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name='attempts',
        verbose_name=_('Quiz'),
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='quiz_attempts',
        verbose_name=_('User'),
    )
    started_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Started At'))
    finished_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Finished At'))
    score = models.PositiveIntegerField(default=0, verbose_name=_('Score'))
    correct_count = models.PositiveIntegerField(default=0, verbose_name=_('Correct Count'))
    incorrect_count = models.PositiveIntegerField(default=0, verbose_name=_('Incorrect Count'))
    time_spent = models.PositiveIntegerField(default=0, verbose_name=_('Time Spent (seconds)'))
    status = models.CharField(
        max_length=15,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
        verbose_name=_('Status'),
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    def __str__(self):
        return f'{self.user} — {self.quiz.title} ({self.status})'


class AttemptAnswer(models.Model):
    class Meta:
        verbose_name = _('Attempt Answer')
        verbose_name_plural = _('Attempt Answers')
        unique_together = [('attempt', 'question')]

    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name='answers',
        verbose_name=_('Attempt'),
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name='attempt_answers',
        verbose_name=_('Question'),
    )
    selected_option = models.ForeignKey(
        QuestionOption,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='selections',
        verbose_name=_('Selected Option'),
    )
    is_correct = models.BooleanField(default=False, verbose_name=_('Is Correct'))
    time_taken = models.PositiveIntegerField(default=0, verbose_name=_('Time Taken (seconds)'))
    matching_answer = models.JSONField(null=True, blank=True, default=None, verbose_name=_('Matching Answer'))

    def __str__(self):
        return f'{self.attempt} — Q:{self.question_id} {"✓" if self.is_correct else "✗"}'
