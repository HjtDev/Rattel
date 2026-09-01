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
        QUEUED = 'queued', _('Queued')
        ACTIVE = 'active', _('Active Plan')
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

    parent_plan = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.CASCADE,
        related_name='chained_plans',
        verbose_name=_('Chained From Plan'),
        help_text=_('When set, this plan activates automatically once the parent plan completes.'),
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
    time_to_finish = models.DateField(
        null=True, blank=True, verbose_name=_('Target Finish Date'),
    )

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

    advance_completion_days = models.PositiveIntegerField(
        null=True,
        blank=True,
        default=None,
        verbose_name=_('Advance Completion Days'),
        help_text=_(
            'How many days ahead the user may complete steps. '
            'Empty disables pre-completion; 0 means unlimited.'
        ),
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

    generate_call_sessions = models.BooleanField(
        default=True,
        verbose_name=_('Generate Call Sessions on Activation'),
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

        if self.parent_plan_id:
            if self.parent_plan_id == self.pk:
                raise ValidationError({'parent_plan': _('A plan cannot be chained to itself.')})
            if self.parent_plan.user_id != self.user_id:
                raise ValidationError({'parent_plan': _('The chained plan must belong to the same user as the parent plan.')})
            if self.parent_plan.status != self.Status.ACTIVE:
                raise ValidationError({'parent_plan': _('You can only chain a plan onto an active plan.')})
            existing = self.parent_plan.chained_plans.filter(status=self.Status.QUEUED)
            if self.pk:
                existing = existing.exclude(pk=self.pk)
            if existing.exists():
                raise ValidationError({'parent_plan': _('This plan already has a queued chained plan.')})
            last_step_date = self.parent_plan.last_step_date
            if last_step_date and self.start_date and self.start_date <= last_step_date:
                raise ValidationError({'start_date': _('The chained plan must start after the parent plan\'s last step.')})

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
            self._create_call_sessions()

        completing = (
            self.status == self.Status.COMPLETED
            and not is_new
            and old_status != self.Status.COMPLETED
        )
        if completing:
            self._activate_chained_plan()

        cancelling = (
            self.status == self.Status.CANCELLED
            and not is_new
            and old_status != self.Status.CANCELLED
        )
        if cancelling:
            self.chained_plans.filter(status=self.Status.QUEUED).update(status=self.Status.CANCELLED)

    def _generate_steps(self):
        # Each extra-review range keeps its own independent cursor so all ranges
        # advance in parallel on the same schedule, rather than one after another.
        ranges = [r for r in self.extra_review_ranges.all() if r.pages_per_session > 0]
        cursors = [r.start_page for r in ranges]

        # Build sessions: each session is a list of (step_type, page_start, page_end, sub_part)
        # Steps within a session share the same scheduled_date.
        all_sessions = []

        for p in range(self.start_page, self.end_page + 1):
            pages_fully_before = p - self.start_page

            if self.reading_freq == self.ReadingFrequency.FULL_PAGE:
                sub_parts = [PlanStep.SubPart.FULL]
            else:
                sub_parts = [PlanStep.SubPart.FIRST_HALF, PlanStep.SubPart.SECOND_HALF]

            for sub_part in sub_parts:
                session = [(PlanStep.StepType.MEMORIZE, p, p, sub_part)]

                # Rolling-window review: cover the previous review_freq pages
                if pages_fully_before > 0:
                    review_count = min(pages_fully_before, self.review_freq)
                    session.append((
                        PlanStep.StepType.REVIEW,
                        p - review_count, p - 1,
                        PlanStep.SubPart.FULL,
                    ))

                # Cycling extra-review ranges — one step per range, all sharing
                # this session (and therefore this scheduled_date).
                for idx, r in enumerate(ranges):
                    cur = cursors[idx]
                    end = min(cur + r.pages_per_session - 1, r.end_page)
                    session.append((
                        PlanStep.StepType.EXTRA_REVIEW,
                        cur, end,
                        PlanStep.SubPart.FULL,
                    ))
                    nxt = end + 1
                    cursors[idx] = r.start_page if nxt > r.end_page else nxt

                all_sessions.append(session)

        # Final comprehensive review gets its own session
        all_sessions.append([(
            PlanStep.StepType.FINAL_REVIEW,
            self.start_page, self.end_page,
            PlanStep.SubPart.FULL,
        )])

        study_dates = _get_study_dates(self.start_date, self.time_freq, len(all_sessions))

        plan_steps = []
        step_number = 1
        for i, session in enumerate(all_sessions):
            scheduled_date = study_dates[i] if i < len(study_dates) else None
            for (step_type, page_start, page_end, sub_part) in session:
                plan_steps.append(PlanStep(
                    plan=self,
                    step_number=step_number,
                    scheduled_date=scheduled_date,
                    step_type=step_type,
                    page_start=page_start,
                    page_end=page_end,
                    sub_part=sub_part,
                ))
                step_number += 1

        PlanStep.objects.bulk_create(plan_steps)

    def _activate_chained_plan(self):
        """Promote the queued follow-up plan when this plan completes."""
        nxt = self.chained_plans.filter(status=self.Status.QUEUED).order_by('created_at').first()
        if not nxt:
            return
        today = timezone.now().date()
        nxt.start_date = max(nxt.start_date, today)
        nxt.status = self.Status.ACTIVE
        nxt.save()

    def _create_call_sessions(self):
        if not self.generate_call_sessions:
            return
        from subscriptions.models import UserSubscription
        from django.utils import timezone
        try:
            today = timezone.now().date()
            sub = (
                UserSubscription.objects
                .select_related('plan')
                .filter(user=self.user, started_at__lte=today, ends_in__gte=today)
                .order_by('-ends_in')
                .first()
            )
            limit = sub.plan.online_class_limit if sub else 0
        except Exception:
            limit = 0

        if limit <= 0:
            return

        OnlineCallSession.objects.bulk_create([
            OnlineCallSession(plan=self, session_number=n)
            for n in range(1, limit + 1)
        ])

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

    @property
    def last_step_date(self):
        return self.steps.aggregate(models.Max('scheduled_date'))['scheduled_date__max']

    def get_unlocked_ahead_steps(self):
        """Future-dated steps this user is currently allowed to complete early."""
        limit = self.advance_completion_days
        if limit is None:
            return PlanStep.objects.none()

        today = timezone.now().date()
        closed = [PlanStep.Status.COMPLETED, PlanStep.Status.SKIPPED]

        # Nothing unlocks while anything due today or earlier is still open.
        if self.steps.filter(
            scheduled_date__isnull=False, scheduled_date__lte=today,
        ).exclude(status__in=closed).exists():
            return PlanStep.objects.none()

        future = self.steps.filter(
            scheduled_date__gt=today,
        ).exclude(status__in=closed)
        if limit > 0:
            future = future.filter(scheduled_date__lte=today + timedelta(days=limit))

        # `future` holds only OPEN steps, so its earliest date IS the next
        # unlocked day — a fully completed day drops out and the next one
        # takes its place.
        next_date = future.order_by('scheduled_date').values_list(
            'scheduled_date', flat=True
        ).first()
        if next_date is None:
            return PlanStep.objects.none()
        return future.filter(scheduled_date=next_date).order_by('step_number')

    def __str__(self):
        return f'Plan for {self.user} [{self.get_status_display()}] pages {self.start_page}–{self.end_page}'


class ExtraReviewRange(models.Model):
    """
    An additional page range an admin wants reviewed alongside the main plan.
    A plan may have any number of these; each keeps its own cycling cursor in
    `AutomaticPlan._generate_steps()` so all ranges advance in parallel on the
    same schedule rather than one after another.
    """

    class Meta:
        verbose_name = _('Extra Review Range')
        verbose_name_plural = _('Extra Review Ranges')
        ordering = ['order', 'created_at']
        indexes = [
            models.Index(fields=['plan', 'order']),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    plan = models.ForeignKey(
        AutomaticPlan,
        on_delete=models.CASCADE,
        related_name='extra_review_ranges',
        verbose_name=_('Plan'),
    )

    start_page = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('Start Page'),
    )
    end_page = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        verbose_name=_('End Page'),
    )
    pages_per_session = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('Pages per Session'),
    )
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    def clean(self):
        from django.core.exceptions import ValidationError
        if self.start_page and self.end_page and self.end_page < self.start_page:
            raise ValidationError({'end_page': _('End page must be greater than or equal to start page.')})

    def __str__(self):
        return f'Extra review pp.{self.start_page}–{self.end_page} ({self.pages_per_session}/session) for plan {self.plan_id}'


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
        EXTRA_REVIEW = 'extra_review', _('Extra Review')
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


class OnlineCallSession(models.Model):
    """
    Tracks individual structured online call sessions allocated by a student's subscription.
    Created automatically when a plan is first activated.
    """

    class Meta:
        verbose_name = _('Online Call Session')
        verbose_name_plural = _('Online Call Sessions')
        ordering = ['session_number']
        unique_together = [('plan', 'session_number')]

    class Status(models.TextChoices):
        PENDING = 'pending', _('Pending')
        COMPLETED = 'completed', _('Completed')
        NO_ANSWER = 'no_answer', _('No Answer')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    plan = models.ForeignKey(
        AutomaticPlan,
        on_delete=models.CASCADE,
        related_name='call_sessions',
        verbose_name=_('Plan'),
    )

    session_number = models.PositiveIntegerField(verbose_name=_('Session Number'))

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
        verbose_name=_('Status'),
    )

    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Completed At'),
    )

    notes = models.TextField(blank=True, verbose_name=_('Notes'))

    marked_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='marked_call_sessions',
        verbose_name=_('Marked By'),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    def __str__(self):
        return f'Call session {self.session_number} for plan {self.plan_id} [{self.get_status_display()}]'
