import uuid
from django.conf import settings
from django.db import models
from django_resized import ResizedImageField
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
import os


def validate_attachment(file):
    """
    Validates that the uploaded attachment is a JPG or PNG and does not exceed 3 MB.

    Args:
        file: The uploaded file instance.

    Raises:
        ValidationError: If the file type or size is not allowed.
    """
    allowed_extensions = ('jpg', 'jpeg', 'png')
    max_size = 3 * 1024 * 1024  # 3 MB

    ext = os.path.splitext(file.name)[1].lower().lstrip('.')
    if ext not in allowed_extensions:
        raise ValidationError(
            f'Only JPG and PNG attachments are allowed. Got: .{ext}'
        )

    if file.size > max_size:
        raise ValidationError(
            f'Attachment must be 3 MB or smaller. Got: {file.size / 1024 / 1024:.2f} MB'
        )


def attachment_upload_path(instance, filename):
    """Build a per-ticket upload path for message attachments.

    Args:
        instance: The Message instance.
        filename: Original filename.

    Returns:
        str: Path relative to MEDIA_ROOT.
    """
    return os.path.join(
        'tickets',
        f'ticket_{instance.ticket_id}',
        'attachments',
        filename,
    )


class Ticket(models.Model):
    """
    Represents a support ticket opened by a user.

    This model is designed to be reusable across projects with minimal
    dependencies — the only external dependency is the AUTH_USER_MODEL setting.
    """

    class Meta:
        verbose_name = _('Ticket')
        verbose_name_plural = _('Tickets')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['priority']),
        ]

    class StatusChoices(models.TextChoices):
        OPEN = 'open', _('Open')
        IN_PROGRESS = 'in_progress', _('In Progress')
        WAITING_USER = 'waiting_user', _('Waiting for User')
        CLOSED = 'closed', _('Closed')

    class PriorityChoices(models.TextChoices):
        LOW = 'low', _('Low')
        MEDIUM = 'medium', _('Medium')
        HIGH = 'high', _('High')
        URGENT = 'urgent', _('Urgent')

    class CategoryChoices(models.TextChoices):
        TECHNICAL = 'technical', _('Technical')
        BILLING = 'billing', _('Billing')
        CONTENT = 'content', _('Content')
        ACCOUNT = 'account', _('Account')
        OTHER = 'other', _('Other')

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=_('Ticket ID'),
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name=_('User'),
    )

    subject = models.CharField(max_length=255, verbose_name=_('Subject'))

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.OPEN,
        verbose_name=_('Status'),
    )

    priority = models.CharField(
        max_length=10,
        choices=PriorityChoices.choices,
        default=PriorityChoices.MEDIUM,
        verbose_name=_('Priority'),
    )

    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        default=CategoryChoices.OTHER,
        verbose_name=_('Category'),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created At'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated At'))

    def __str__(self):
        return f'[{self.get_status_display()}] {self.subject} — {self.user}'

    @property
    def message_count(self):
        """Return the total number of messages in this ticket.

        Returns:
            int: Message count.
        """
        return self.messages.count()

    def close(self):
        """Mark the ticket as closed.

        Returns:
            bool: True if status changed, False if already closed.
        """
        if self.status == self.StatusChoices.CLOSED:
            return False
        self.status = self.StatusChoices.CLOSED
        self.save(update_fields=['status', 'updated_at'])
        return True

    def reopen(self):
        """Reopen a closed ticket back to OPEN.

        Returns:
            bool: True if reopened, False if not closed.
        """
        if self.status != self.StatusChoices.CLOSED:
            return False
        self.status = self.StatusChoices.OPEN
        self.save(update_fields=['status', 'updated_at'])
        return True


class Message(models.Model):
    """
    A single message within a support ticket.

    Messages can be sent by either the ticket owner or an admin/staff member.
    Supports optional image attachments (JPG/PNG, up to 3 MB).
    """

    class Meta:
        verbose_name = _('Message')
        verbose_name_plural = _('Messages')
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
            models.Index(fields=['sender']),
        ]

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name=_('Ticket'),
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ticket_messages',
        verbose_name=_('Sender'),
    )

    body = models.TextField(verbose_name=_('Message Body'))

    attachment = ResizedImageField(
        upload_to=attachment_upload_path,
        blank=True,
        null=True,
        size=[1920, 1080],
        quality=90,
        verbose_name=_('Attachment'),
        validators=[validate_attachment],
    )

    is_staff_reply = models.BooleanField(
        default=False,
        verbose_name=_('Staff Reply'),
        help_text=_('True if this message was sent by an admin or staff member.'),
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Sent At'))

    def __str__(self):
        sender_label = 'Staff' if self.is_staff_reply else str(self.sender)
        return f'Message by {sender_label} on ticket #{self.ticket_id}'

    def delete(self, *args, **kwargs):
        if self.attachment and self.attachment.name:
            self.attachment.delete(save=False)
        return super().delete(*args, **kwargs)
