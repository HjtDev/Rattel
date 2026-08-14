import uuid
from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


class MediaSweepRun(models.Model):
    """
    Audit trail for admin-triggered orphaned-media sweeps (see media_cleanup.services).
    Rows are written only after a sweep actually deletes files — this model is never
    written to or read from outside the admin scan view.
    """

    class Meta:
        verbose_name = _('Media Sweep Run')
        verbose_name_plural = _('Media Sweep Runs')
        ordering = ['-created_at']

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, unique=True, verbose_name=_('ID'))

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Run At'))
    run_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='media_sweep_runs',
        verbose_name=_('Run By'),
    )

    files_deleted = models.PositiveIntegerField(default=0, verbose_name=_('Files Deleted'))
    bytes_freed = models.PositiveBigIntegerField(default=0, verbose_name=_('Bytes Freed'))
    errors = models.JSONField(default=list, blank=True, verbose_name=_('Errors'))

    def __str__(self):
        return f'{self.created_at:%Y-%m-%d %H:%M} — {self.files_deleted} files'
