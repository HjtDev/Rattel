from django.apps import AppConfig
from django.utils.text import gettext_lazy as _


class SubscriptionsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'subscriptions'
    verbose_name = _('Subscriptions')
