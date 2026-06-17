import uuid
from datetime import timedelta
from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.functional import classproperty
from django.utils.translation import gettext_lazy as _
from tinymce.models import HTMLField
from RattelBackend.cache import invalidate_cache


class Plan(models.Model):
    class Meta:
        verbose_name = _('Subscription Plan')
        verbose_name_plural = _('Subscription Plans')
        ordering = ['price']

    class OnlineClassLimit(models.IntegerChoices):
        NONE = 0, _('No Access')
        BASIC = 4, _('Up to 4 meetings/month')
        STANDARD = 8, _('Up to 8 meetings/month')
        PREMIUM = 12, _('Up to 12 meetings/month')

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, verbose_name=_('Plan ID'))

    name = models.CharField(max_length=255, verbose_name=_('Name'))
    description = HTMLField(verbose_name=_('Description'))
    picture = models.FileField(upload_to='subscriptions/pictures/', blank=True, null=True, verbose_name=_('Picture'))

    price = models.PositiveIntegerField(validators=[MinValueValidator(0)], verbose_name=_('Price (Toman)'))
    new_price = models.PositiveIntegerField(default=0, validators=[MinValueValidator(0)], verbose_name=_('Discounted Price (0 = no discount)'))

    # How many days the subscription lasts after purchase
    duration_days = models.PositiveIntegerField(
        default=30,
        validators=[MinValueValidator(1)],
        verbose_name=_('Duration (days)'),
    )

    # Features
    has_early_news_access = models.BooleanField(default=False, verbose_name=_('Early News Access'))
    has_quiz_access = models.BooleanField(default=False, verbose_name=_('Quiz Access'))
    has_free_course_access = models.BooleanField(default=False, verbose_name=_('Free Course Access'))
    online_class_limit = models.IntegerField(
        choices=OnlineClassLimit.choices,
        default=OnlineClassLimit.NONE,
        verbose_name=_('Online Class Meetings/Month'),
    )

    bought_by = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='purchased_plans',
        blank=True,
        verbose_name=_('Bought By'),
    )

    is_visible = models.BooleanField(default=True, verbose_name=_('Visible'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    @classproperty
    def CART_SERIALIZER(cls):
        from subscriptions.serializers import PlanCartSerializer
        return PlanCartSerializer

    @property
    def discount(self):
        if self.new_price and self.new_price < self.price and self.price > 0:
            return round((1 - self.new_price / self.price) * 100)
        return 0

    @property
    def has_online_class_access(self):
        return self.online_class_limit > self.OnlineClassLimit.NONE

    def is_owned_by(self, user):
        """Returns True only if the user has an active (non-expired) subscription for this exact plan."""
        today = timezone.now().date()
        try:
            sub = user.subscription
            return sub.plan_id == self.pk and sub.ends_in >= today
        except UserSubscription.DoesNotExist:
            return False

    def add_user(self, user):
        """Called by payment system on successful purchase. Creates or extends the user's subscription."""
        self.bought_by.add(user)

        today = timezone.now().date()
        subscription, created = UserSubscription.objects.get_or_create(
            user=user,
            defaults={
                'plan': self,
                'ends_in': today + timedelta(days=self.duration_days),
            },
        )
        if not created:
            # Extend from expiry or today, whichever is later, so partial time is never lost
            base = max(subscription.ends_in, today)
            subscription.plan = self
            subscription.ends_in = base + timedelta(days=self.duration_days)
            subscription.save()

        return subscription

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        invalidate_cache('subscription_plans')

    def delete(self, *args, **kwargs):
        if self.picture and self.picture.name:
            self.picture.delete(save=False)
        return super().delete(*args, **kwargs)

    def __str__(self):
        return self.name


class UserSubscription(models.Model):
    class Meta:
        verbose_name = _('User Subscription')
        verbose_name_plural = _('User Subscriptions')

    # OneToOne: each user can only have one active plan at a time
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='subscription',
        verbose_name=_('User'),
    )
    plan = models.ForeignKey(
        Plan,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_('Subscription Plan'),
    )
    started_at = models.DateField(auto_now_add=True, verbose_name=_('Started At'))
    ends_in = models.DateField(verbose_name=_('Ends In'))

    @property
    def is_active(self):
        if self.started_at is None:
            return _('Plan not started.')
        today = timezone.now().date()
        return self.started_at <= today <= self.ends_in

    def has_feature_early_news(self):
        return self.is_active and self.plan.has_early_news_access

    def has_feature_quiz(self):
        return self.is_active and self.plan.has_quiz_access

    def has_feature_online_class(self, min_meetings: int = 1):
        return self.is_active and self.plan.online_class_limit >= min_meetings

    def has_feature_free_courses(self):
        return self.is_active and self.plan.has_free_course_access

    def __str__(self):
        status = 'active' if self.is_active else 'expired'
        return f'{self.user} — {self.plan.name} ({status})'
