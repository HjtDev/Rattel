from django.apps import AppConfig
from django.utils.text import gettext_lazy as _


class AutomaticClassConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'automatic_class'
    verbose_name = _('Automatic Class System')

    def ready(self):
        import automatic_class.signals  # noqa: F401
