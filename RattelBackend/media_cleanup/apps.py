from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MediaCleanupConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'media_cleanup'
    verbose_name = _('Media Cleanup')
