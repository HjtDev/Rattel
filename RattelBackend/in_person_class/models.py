import uuid
from datetime import date

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField

from RattelBackend.cache import invalidate_cache


class TimeRange(models.Model):
    class Meta:
        verbose_name = _('Time Range')
        verbose_name_plural = _('Time Ranges')
        ordering = ('label',)

    label = models.CharField(max_length=100, verbose_name=_('Label'))

    def __str__(self):
        return self.label

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_cache('in_person_class_list')

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        invalidate_cache('in_person_class_list')
        return result


class Category(models.Model):
    class Meta:
        verbose_name = _('Category')
        verbose_name_plural = _('Categories')
        ordering = ('name',)

    name = models.CharField(max_length=120, unique=True, verbose_name=_('Name'))
    slug = models.SlugField(max_length=140, unique=True, allow_unicode=True, verbose_name=_('Slug'))

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_cache('in_person_class_list')
        invalidate_cache('in_person_class_categories')

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        invalidate_cache('in_person_class_list')
        invalidate_cache('in_person_class_categories')
        return result


class InPersonClass(models.Model):
    class Meta:
        verbose_name = _('In-Person Class')
        verbose_name_plural = _('In-Person Classes')
        ordering = ('-start_date',)
        indexes = [
            models.Index(fields=['is_visible', 'start_date']),
        ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, verbose_name=_('ID'))

    thumbnail = models.FileField(upload_to='in_person_class/thumbnails/', blank=True, null=True, verbose_name=_('Thumbnail'))
    title = models.CharField(max_length=255, verbose_name=_('Title'))
    short_description = HTMLField(verbose_name=_('Short Description'))

    price = models.PositiveIntegerField(validators=[MinValueValidator(0)], verbose_name=_('Price (Toman)'))
    new_price = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name=_('Discounted Price (0 = no discount)'))

    available_times = models.ManyToManyField(TimeRange, related_name='classes', blank=True, verbose_name=_('Available Times'))
    categories = models.ManyToManyField(Category, related_name='classes', blank=True, verbose_name=_('Categories'))

    start_date = models.DateField(verbose_name=_('Start Date'))
    end_date = models.DateField(verbose_name=_('End Date'))

    capacity = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_('Capacity per Time Slot (empty = unlimited)'),
    )

    meeting_url = models.URLField(blank=True, null=True, verbose_name=_('Online Meeting URL'))

    is_visible = models.BooleanField(default=True, verbose_name=_('Visible'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    @property
    def discount(self):
        if self.new_price and self.new_price < self.price and self.price > 0:
            return round((1 - self.new_price / self.price) * 100)
        return 0

    @property
    def is_active(self):
        return self.end_date >= date.today()

    @property
    def has_started(self) -> bool:
        """start_date is a date (no time-of-day), so a class starting today is
        not yet considered started — it may still be scheduled later today.
        Only once the calendar date has passed is it definitively started.
        """
        return self.start_date < date.today()

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_cache('in_person_class_list')

    def delete(self, *args, **kwargs):
        result = super().delete(*args, **kwargs)
        invalidate_cache('in_person_class_list')
        return result


class InPersonClassRegistration(models.Model):
    class Meta:
        verbose_name = _('In-Person Class Registration')
        verbose_name_plural = _('In-Person Class Registrations')
        unique_together = [('in_person_class', 'time_range')]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, verbose_name=_('ID'))

    in_person_class = models.ForeignKey(
        InPersonClass,
        on_delete=models.CASCADE,
        related_name='registrations',
        verbose_name=_('In-Person Class'),
    )
    time_range = models.ForeignKey(
        TimeRange,
        on_delete=models.PROTECT,
        related_name='registrations',
        verbose_name=_('Time Range'),
    )

    # Snapshot fields — copied from InPersonClass at registration creation time
    start_date = models.DateField(verbose_name=_('Start Date'))
    end_date = models.DateField(verbose_name=_('End Date'))
    price = models.PositiveIntegerField(verbose_name=_('Price (Toman)'))
    new_price = models.PositiveIntegerField(default=0, verbose_name=_('Discounted Price'))

    bought_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='in_person_class_registrations',
        blank=True,
        verbose_name=_('Bought By'),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))

    # Cart system interface
    @classproperty
    def CART_SERIALIZER(cls):
        from in_person_class.serializers import InPersonClassRegistrationCartSerializer
        return InPersonClassRegistrationCartSerializer

    def add_user(self, user):
        self.bought_by.add(user)
        invalidate_cache('my_in_person_class_registrations')
        invalidate_cache('in_person_class_list')

    def is_owned_by(self, user) -> bool:
        return self.bought_by.filter(pk=user.pk).exists()

    @property
    def capacity(self):
        """Effective capacity, read live from the parent class (None = unlimited)."""
        return self.in_person_class.capacity

    @property
    def registered_count(self) -> int:
        return self.bought_by.count()

    @property
    def seats_remaining(self):
        cap = self.capacity
        return None if cap is None else max(cap - self.registered_count, 0)

    @property
    def is_full(self) -> bool:
        cap = self.capacity
        return False if cap is None else self.registered_count >= cap

    def _purchase_blocked_reason(self, user) -> str | None:
        """Shared validity check for both add-to-cart and finalize/payout time.

        Returns None if the user already owns this registration — an existing
        owner must never be blocked from a re-check they didn't ask for.
        """
        if self.is_owned_by(user):
            return None
        if self.in_person_class.has_started:
            return 'این کلاس قبلاً شروع شده است.'
        if self.is_full:
            return 'ظرفیت این کلاس تکمیل شده است.'
        return None

    def can_be_added_to_cart(self, user) -> tuple[bool, str]:
        """Cart-system hook (see CartManager.add) — blocks adding a full or already-started slot."""
        reason = self._purchase_blocked_reason(user)
        return (False, reason) if reason else (True, '')

    def can_be_finalized(self, user) -> tuple[bool, str]:
        """Payout-time hook (see PaymentStartView / CartFinalizerView) — re-checks
        the same conditions as can_be_added_to_cart, since a cart item can sit
        for an arbitrary amount of time before the user actually pays.
        """
        reason = self._purchase_blocked_reason(user)
        return (False, reason) if reason else (True, '')

    def __str__(self):
        return f'{self.in_person_class.title} — {self.time_range.label}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_cache('my_in_person_class_registrations')
