from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
from .models import Course, Episode


class EpisodeProgress(models.Model):
    """
    Tracks user progress for individual episodes.
    
    This model stores which episodes a user has watched, when they last watched,
    and whether they completed the episode. Used for calculating course progress
    and implementing "continue watching" features.
    """
    
    class Meta:
        verbose_name = _('Episode Progress')
        verbose_name_plural = _('Episode Progress')
        unique_together = ('user', 'episode')
        indexes = [
            models.Index(fields=['user', 'course']),
            models.Index(fields=['user', '-last_watched_at']),
            models.Index(fields=['course', 'is_completed']),
        ]
        ordering = ['-last_watched_at']
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='episode_progress',
        verbose_name=_('User')
    )
    
    episode = models.ForeignKey(
        Episode,
        on_delete=models.CASCADE,
        related_name='user_progress',
        verbose_name=_('Episode')
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='episode_progress',
        verbose_name=_('Course'),
        help_text=_('Denormalized for faster queries')
    )
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name=_('Completed'),
        help_text=_('Whether user has completed this episode')
    )
    
    watch_count = models.PositiveIntegerField(
        default=1,
        verbose_name=_('Watch Count'),
        help_text=_('Number of times user has watched this episode')
    )
    
    watch_duration = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Watch Duration (seconds)'),
        help_text=_('Total seconds watched (for video progress tracking)')
    )
    
    last_watched_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last Watched At')
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Created At')
    )
    
    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f'{status} {self.user.username} - {self.episode.title}'
