from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class InPersonClassConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'in_person_class'
    verbose_name = _('In-Person Class System')

    def ready(self):
        import in_person_class.signals  # noqa: F401
