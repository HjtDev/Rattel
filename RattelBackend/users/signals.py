from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Profile, UserSettings

@receiver(post_save, sender=User)
def create_user_profile_and_settings(sender, instance, created, **kwargs):
    """Auto-create Profile and Settings when User is created."""
    if created:
        Profile.objects.create(user=instance)
        UserSettings.objects.create(user=instance)