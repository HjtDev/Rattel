from django.dispatch import receiver
from django.db.models.signals import post_save, pre_delete
from .models import Course, Chapter, Episode
from RattelBackend.cache import invalidate_cache


@receiver([post_save, pre_delete], sender=Course)
@receiver([post_save, pre_delete], sender=Chapter)
@receiver([post_save, pre_delete], sender=Episode)
def invalidate_course_cache(sender, instance, **kwargs):
    if not instance.pk:
        return

    # Invalidate all course caches
    invalidate_cache('course_list')
    invalidate_cache('course_detail')
