from django.db import models
from django.conf import settings
from .models import Course, Episode


class EpisodeProgress(models.Model):
    """
    Tracks user progress for individual episodes.
    
    This model stores which episodes a user has watched, when they last watched,
    and whether they completed the episode. Used for calculating course progress
    and implementing "continue watching" features.
    """
    
    class Meta:
        verbose_name = 'Episode Progress'
        verbose_name_plural = 'Episode Progress'
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
        verbose_name='User'
    )
    
    episode = models.ForeignKey(
        Episode,
        on_delete=models.CASCADE,
        related_name='user_progress',
        verbose_name='Episode'
    )
    
    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='episode_progress',
        verbose_name='Course',
        help_text='Denormalized for faster queries'
    )
    
    is_completed = models.BooleanField(
        default=False,
        verbose_name='Completed',
        help_text='Whether user has completed this episode'
    )
    
    watch_count = models.PositiveIntegerField(
        default=1,
        verbose_name='Watch Count',
        help_text='Number of times user has watched this episode'
    )
    
    watch_duration = models.PositiveIntegerField(
        default=0,
        verbose_name='Watch Duration (seconds)',
        help_text='Total seconds watched (for video progress tracking)'
    )
    
    last_watched_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Last Watched At'
    )
    
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Created At'
    )
    
    def __str__(self):
        status = "✓" if self.is_completed else "○"
        return f'{status} {self.user.username} - {self.episode.title}'
