from django.db.models.signals import m2m_changed
from django.dispatch import receiver

from RattelBackend.cache import invalidate_cache

from .models import InPersonClass


@receiver(m2m_changed, sender=InPersonClass.available_times.through)
@receiver(m2m_changed, sender=InPersonClass.categories.through)
def invalidate_list_cache_on_m2m_change(sender, action, **kwargs):
    if action in ('post_add', 'post_remove', 'post_clear'):
        invalidate_cache('in_person_class_list')
