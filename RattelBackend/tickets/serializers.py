from rest_framework import serializers
from users.serializers import QuickUserSerializer
from .models import Ticket, Message


class MessageSerializer(serializers.ModelSerializer):
    """Serializes a single ticket message for read operations."""

    sender = QuickUserSerializer(read_only=True)
    attachment = serializers.SerializerMethodField()

    class Meta:
        model = Message
        fields = (
            'id',
            'sender',
            'body',
            'attachment',
            'is_staff_reply',
            'created_at',
        )
        read_only_fields = fields

    def get_attachment(self, obj: Message):
        """Return absolute URL for attachment if it exists.

        Args:
            obj: Message instance.

        Returns:
            str | None: Absolute URL or None.
        """
        if not obj.attachment:
            return None
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(obj.attachment.url)
        return obj.attachment.url


class TicketListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for listing tickets (no messages)."""

    class Meta:
        model = Ticket
        fields = (
            'id',
            'subject',
            'status',
            'priority',
            'category',
            'message_count',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields


class TicketDetailSerializer(serializers.ModelSerializer):
    """Full ticket serializer including all messages."""

    messages = serializers.SerializerMethodField()

    class Meta:
        model = Ticket
        fields = (
            'id',
            'subject',
            'status',
            'priority',
            'category',
            'message_count',
            'messages',
            'created_at',
            'updated_at',
        )
        read_only_fields = fields

    def get_messages(self, obj: Ticket):
        """Return serialized messages ordered oldest-first.

        Args:
            obj: Ticket instance.

        Returns:
            list: Serialized message data.
        """
        return MessageSerializer(
            obj.messages.select_related('sender').order_by('created_at'),
            many=True,
            context=self.context,
        ).data
