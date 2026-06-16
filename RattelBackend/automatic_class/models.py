import uuid
from datetime import timedelta
from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


def _get_study_dates(start_date, time_freq, count):
    """
    Return a list of `count` calendar dates for study steps.

    per_day      → consecutive days: start, start+1, start+2, …
    per_two_days → every other day:  start, start+2, start+4, …

    user_day_availability and user_time_availability are admin-call metadata
    only and have no effect on when steps are scheduled.
    """
    gap = 1 if time_freq == AutomaticPlan.TimeFrequency.PER_DAY else 2
    return [start_date + timedelta(days=i * gap) for i in range(count)]


class ClassRequest(models.Model):
    """
    A user's initial request to be enrolled in the automatic class system.
    The admin will contact the user by phone and then create an AutomaticPlan.
    """

    class Meta:
        verbose_name = _('Class Request')
        verbose_name_plural = _('Class Requests')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
        ]

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending Admin')
        CONTACTED = 'contacted', _('Contacted')
        PLAN_CREATED = 'plan_created', _('Plan Created')
        REJECTED = 'rejected', _('Rejected')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='class_requests',
        verbose_name=_('User'),
    )

    notes = models.TextField(blank=True, verbose_name=_('User Notes'))
    admin_notes = models.TextField(blank=True, verbose_name=_('Admin Notes'))

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('Status'),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    def __str__(self):
        return f'Request by {self.user} [{self.get_status_display()}]'


class AutomaticPlan(models.Model):
    """
    A personalised memorisation plan created by an admin (teacher) for a user.
    Steps are auto-generated on first activation.
    """

    class Meta:
        verbose_name = _('Automatic Plan')
        verbose_name_plural = _('Automatic Plans')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
        ]

    class TimeFrequency(models.TextChoices):
        PER_DAY = 'per_day', _('Per Day')
        PER_TWO_DAYS = 'per_two_days', _('Per Two Days')

    class ReadingFrequency(models.TextChoices):
        HALF_PAGE = 'half_page', _('Half Page')
        FULL_PAGE = 'full_page', _('Full Page')

    class DayAvailability(models.TextChoices):
        ODD_DAYS = 'odd_days', _('Odd Days (Sun, Tue, Thu)')
        EVEN_DAYS = 'even_days', _('Even Days (Sat, Mon, Wed)')

    class TimeAvailability(models.TextChoices):
        MORNING = 'morning', _('9 AM – 11 AM')
        AFTERNOON = 'afternoon', _('3 PM – 5 PM')
        EVENING = 'evening', _('7 PM – 9 PM')

    class Status(models.TextChoices):
        DRAFT = 'draft', _('Draft')
        ACTIVE = 'active', _('Active')
        COMPLETED = 'completed', _('Completed')
        CANCELLED = 'cancelled', _('Cancelled')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    request = models.OneToOneField(
        ClassRequest,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='plan',
        verbose_name=_('Class Request'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='automatic_plans',
        verbose_name=_('Student'),
    )

    teacher = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='taught_plans',
        verbose_name=_('Teacher'),
    )

    start_page = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('Start Page'),
    )
    end_page = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('End Page'),
    )

    start_date = models.DateField(verbose_name=_('Start Date'))
    time_to_finish = models.DateField(verbose_name=_('Target Finish Date'))

    time_freq = models.CharField(
        max_length=20,
        choices=TimeFrequency.choices,
        default=TimeFrequency.PER_DAY,
        verbose_name=_('Study Frequency'),
    )

    reading_freq = models.CharField(
        max_length=20,
        choices=ReadingFrequency.choices,
        default=ReadingFrequency.FULL_PAGE,
        verbose_name=_('Reading Amount per Session'),
    )

    review_freq = models.PositiveIntegerField(
        default=3,
        validators=[MinValueValidator(1)],
        verbose_name=_('Review Every N Pages'),
    )

    user_day_availability = models.CharField(
        max_length=20,
        choices=DayAvailability.choices,
        verbose_name=_('Available Days'),
    )

    user_time_availability = models.CharField(
        max_length=20,
        choices=TimeAvailability.choices,
        verbose_name=_('Preferred Time Slot'),
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        verbose_name=_('Plan Status'),
    )

    admin_notes = models.TextField(blank=True, verbose_name=_('Admin Notes'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    # Track whether steps have been generated so we don't regenerate on re-save
    _steps_generated = models.BooleanField(
        default=False,
        editable=False,
        verbose_name=_('Steps Generated'),
    )

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_page and self.end_page and self.start_page >= self.end_page:
            raise ValidationError({'end_page': _('End page must be greater than start page.')})
        if self.start_date and self.time_to_finish and self.start_date >= self.time_to_finish:
            raise ValidationError({'time_to_finish': _('Finish date must be after start date.')})

    def save(self, *args, **kwargs):
        is_new = self._state.adding
        old_status = None
        if not is_new:
            try:
                old_status = AutomaticPlan.objects.values_list('status', flat=True).get(pk=self.pk)
            except AutomaticPlan.DoesNotExist:
                pass

        super().save(*args, **kwargs)

        # Generate steps when plan first becomes active and steps haven't been created yet
        activating = (
            self.status == self.Status.ACTIVE
            and not self._steps_generated
            and (is_new or old_status != self.Status.ACTIVE)
        )
        if activating:
            self._generate_steps()
            AutomaticPlan.objects.filter(pk=self.pk).update(_steps_generated=True)

    def _generate_steps(self):
        steps_data = []  # (step_type, page_start, page_end, sub_part)
        current_page = self.start_page
        pages_since_review = 0

        while current_page <= self.end_page:
            if self.reading_freq == self.ReadingFrequency.FULL_PAGE:
                steps_data.append((
                    PlanStep.StepType.MEMORIZE,
                    current_page, current_page,
                    PlanStep.SubPart.FULL,
                ))
                pages_since_review += 1
            else:  # HALF_PAGE — two sessions per page
                steps_data.append((
                    PlanStep.StepType.MEMORIZE,
                    current_page, current_page,
                    PlanStep.SubPart.FIRST_HALF,
                ))
                steps_data.append((
                    PlanStep.StepType.MEMORIZE,
                    current_page, current_page,
                    PlanStep.SubPart.SECOND_HALF,
                ))
                pages_since_review += 1

            current_page += 1

            if pages_since_review >= self.review_freq:
                review_start = current_page - pages_since_review
                steps_data.append((
                    PlanStep.StepType.REVIEW,
                    review_start, current_page - 1,
                    PlanStep.SubPart.FULL,
                ))
                pages_since_review = 0

        # Final comprehensive review
        steps_data.append((
            PlanStep.StepType.FINAL_REVIEW,
            self.start_page, self.end_page,
            PlanStep.SubPart.FULL,
        ))

        study_dates = _get_study_dates(self.start_date, self.time_freq, len(steps_data))

        plan_steps = []
        for i, (step_type, page_start, page_end, sub_part) in enumerate(steps_data):
            scheduled_date = study_dates[i] if i < len(study_dates) else None
            plan_steps.append(PlanStep(
                plan=self,
                step_number=i + 1,
                scheduled_date=scheduled_date,
                step_type=step_type,
                page_start=page_start,
                page_end=page_end,
                sub_part=sub_part,
            ))

        PlanStep.objects.bulk_create(plan_steps)

    @property
    def total_steps(self):
        return self.steps.count()

    @property
    def completed_steps(self):
        return self.steps.filter(status=PlanStep.Status.COMPLETED).count()

    @property
    def progress_percent(self):
        total = self.total_steps
        if total == 0:
            return 0
        return round(self.completed_steps / total * 100)

    def __str__(self):
        return f'Plan for {self.user} [{self.get_status_display()}] pages {self.start_page}–{self.end_page}'


class PlanStep(models.Model):
    """
    A single daily task within an AutomaticPlan.
    Steps are auto-generated when the plan is first activated.
    """

    class Meta:
        verbose_name = _('Plan Step')
        verbose_name_plural = _('Plan Steps')
        ordering = ['step_number']
        indexes = [
            models.Index(fields=['plan', 'scheduled_date']),
            models.Index(fields=['plan', 'status']),
            models.Index(fields=['scheduled_date', 'status']),
        ]

    class StepType(models.TextChoices):
        MEMORIZE = 'memorize', _('Memorize')
        REVIEW = 'review', _('Review')
        FINAL_REVIEW = 'final_review', _('Final Review')

    class SubPart(models.TextChoices):
        FULL = 'full', _('Full Page')
        FIRST_HALF = 'first_half', _('First Half')
        SECOND_HALF = 'second_half', _('Second Half')

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        DELAYED = 'delayed', _('Delayed')
        COMPLETED = 'completed', _('Completed')
        SKIPPED = 'skipped', _('Skipped')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    plan = models.ForeignKey(
        AutomaticPlan,
        on_delete=models.CASCADE,
        related_name='steps',
        verbose_name=_('Plan'),
    )

    step_number = models.PositiveIntegerField(verbose_name=_('Step Number'))

    scheduled_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Scheduled Date'),
    )

    step_type = models.CharField(
        max_length=20,
        choices=StepType.choices,
        verbose_name=_('Step Type'),
    )

    page_start = models.PositiveIntegerField(verbose_name=_('Page Start'))
    page_end = models.PositiveIntegerField(verbose_name=_('Page End'))

    sub_part = models.CharField(
        max_length=20,
        choices=SubPart.choices,
        default=SubPart.FULL,
        verbose_name=_('Sub Part'),
    )

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('Status'),
    )

    is_delayed = models.BooleanField(
        default=False,
        verbose_name=_('Was Delayed'),
        help_text=_('True if this step was completed or carried over past its scheduled date.'),
    )

    original_scheduled_date = models.DateField(
        null=True,
        blank=True,
        verbose_name=_('Original Scheduled Date'),
        help_text=_('Set when a pending step is pushed past its scheduled date.'),
    )

    completed_at = models.DateTimeField(null=True, blank=True, verbose_name=_('Completed At'))
    delay_reason = models.TextField(blank=True, verbose_name=_('Delay Reason'))
    admin_note = models.TextField(blank=True, verbose_name=_('Admin Note'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    def mark_delayed(self):
        """Called by the nightly task when a pending step passes its scheduled date."""
        if self.status == self.Status.PENDING and self.scheduled_date:
            self.status = self.Status.DELAYED
            self.is_delayed = True
            self.original_scheduled_date = self.scheduled_date
            self.save(update_fields=['status', 'is_delayed', 'original_scheduled_date'])

    def complete(self, delay_reason: str = ''):
        today = timezone.now().date()
        was_delayed = self.scheduled_date and today > self.scheduled_date
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.is_delayed = was_delayed
        if was_delayed and delay_reason:
            self.delay_reason = delay_reason
        if was_delayed and not self.original_scheduled_date:
            self.original_scheduled_date = self.scheduled_date
        self.save(update_fields=[
            'status', 'completed_at', 'is_delayed', 'delay_reason', 'original_scheduled_date',
        ])

    def __str__(self):
        part = f' ({self.get_sub_part_display()})' if self.sub_part != self.SubPart.FULL else ''
        return (
            f'Step {self.step_number}: {self.get_step_type_display()} '
            f'pp.{self.page_start}–{self.page_end}{part} [{self.get_status_display()}]'
        )


class AdminCallLog(models.Model):
    """Records every time an admin calls a student to check on their progress."""

    class Meta:
        verbose_name = _('Admin Call Log')
        verbose_name_plural = _('Admin Call Logs')
        ordering = ['-call_date']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    plan = models.ForeignKey(
        AutomaticPlan,
        on_delete=models.CASCADE,
        related_name='call_logs',
        verbose_name=_('Plan'),
    )

    called_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='class_call_logs',
        verbose_name=_('Called By'),
    )

    notes = models.TextField(verbose_name=_('Call Notes'))
    call_date = models.DateTimeField(default=timezone.now, verbose_name=_('Call Date'))
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'Call by {self.called_by} on plan {self.plan_id} at {self.call_date:%Y-%m-%d %H:%M}'
