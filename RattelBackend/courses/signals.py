from django.conf import settings
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
    invalidate_cache('my_courses')


# Teachers List is disabled
# @receiver([post_save, pre_delete], sender=settings.AUTH_USER_MODEL)
# def invalidate_teacher_cache(sender, instance: settings.AUTH_USER_MODEL, **kwargs):
#     if not instance.pk:
#         return
#
#     if instance. and instance.profile.role == 'teacher':
#         invalidate_cache('teacher_list')
