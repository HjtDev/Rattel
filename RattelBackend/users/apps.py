from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    verbose_name = _('Users System')
    name = 'users'
    
    def ready(self):
        import users.signals
