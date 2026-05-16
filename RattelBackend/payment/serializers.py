from rest_framework.serializers import ModelSerializer
from .models import Transaction


class TransactionSerializer(ModelSerializer):
    """
    Serializer for user transactions with essential information only.
    """
    
    class Meta:
        model = Transaction
        fields = (
            'tracking_id',
            'amount',
            'currency',
            'transaction_status',
            'transaction_reason',
            'description',
            'created_at',
        )
        read_only_fields = fields
