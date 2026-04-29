import uuid
import os
from django.conf import settings
from django.db import models
from django_resized import ResizedImageField
from django.core.exceptions import ValidationError


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
        verbose_name = 'Ticket'
        verbose_name_plural = 'Tickets'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['priority']),
        ]

    class StatusChoices(models.TextChoices):
        OPEN = 'open', 'Open'
        IN_PROGRESS = 'in_progress', 'In Progress'
        WAITING_USER = 'waiting_user', 'Waiting for User'
        CLOSED = 'closed', 'Closed'

    class PriorityChoices(models.TextChoices):
        LOW = 'low', 'Low'
        MEDIUM = 'medium', 'Medium'
        HIGH = 'high', 'High'
        URGENT = 'urgent', 'Urgent'

    class CategoryChoices(models.TextChoices):
        TECHNICAL = 'technical', 'Technical'
        BILLING = 'billing', 'Billing'
        CONTENT = 'content', 'Content'
        ACCOUNT = 'account', 'Account'
        OTHER = 'other', 'Other'

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name='Ticket ID',
    )

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets',
        verbose_name='User',
    )

    subject = models.CharField(max_length=255, verbose_name='Subject')

    status = models.CharField(
        max_length=20,
        choices=StatusChoices.choices,
        default=StatusChoices.OPEN,
        verbose_name='Status',
    )

    priority = models.CharField(
        max_length=10,
        choices=PriorityChoices.choices,
        default=PriorityChoices.MEDIUM,
        verbose_name='Priority',
    )

    category = models.CharField(
        max_length=20,
        choices=CategoryChoices.choices,
        default=CategoryChoices.OTHER,
        verbose_name='Category',
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created At')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated At')

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
        verbose_name = 'Message'
        verbose_name_plural = 'Messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['ticket', 'created_at']),
            models.Index(fields=['sender']),
        ]

    ticket = models.ForeignKey(
        Ticket,
        on_delete=models.CASCADE,
        related_name='messages',
        verbose_name='Ticket',
    )

    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='ticket_messages',
        verbose_name='Sender',
    )

    body = models.TextField(verbose_name='Message Body')

    attachment = ResizedImageField(
        upload_to=attachment_upload_path,
        blank=True,
        null=True,
        size=[1920, 1080],
        quality=90,
        verbose_name='Attachment',
        validators=[validate_attachment],
    )

    is_staff_reply = models.BooleanField(
        default=False,
        verbose_name='Staff Reply',
        help_text='True if this message was sent by an admin or staff member.',
    )

    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Sent At')

    def __str__(self):
        sender_label = 'Staff' if self.is_staff_reply else str(self.sender)
        return f'Message by {sender_label} on ticket #{self.ticket_id}'
