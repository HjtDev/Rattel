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

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_cache('in_person_class_list')

    def delete(self, *args, **kwargs):
        if self.thumbnail and self.thumbnail.name:
            self.thumbnail.delete(save=False)
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

    def is_owned_by(self, user) -> bool:
        return self.bought_by.filter(pk=user.pk).exists()

    def __str__(self):
        return f'{self.in_person_class.title} — {self.time_range.label}'

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_cache('my_in_person_class_registrations')
