from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
import uuid


class Transaction(models.Model):
    class Meta:
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['transaction_status']),
            models.Index(fields=['tracking_id']),
        ]
        
    class CurrencyChoices(models.TextChoices):
        IRR = 'IRR', 'Rial'
        IRT = 'IRT', 'Toman'
        
    class TransactionTypes(models.TextChoices):
        GATEWAY = 'gateway', 'Gateway'
        TRANSFER = 'transfer', 'Transfer'
        CASH = 'cash', 'Cash'
        
    class TransactionReason(models.TextChoices):
        PAYMENT = 'payment', 'Payment'
        REFUND = 'refund', 'Refund'
        WITHDRAWAL = 'withdrawal', 'Withdrawal'
        DEPOSIT = 'deposit', 'Deposit'
        FEE = 'fee', 'Fee'
        ADJUSTMENT = 'adjustment', 'Adjustment'
        
    class TransactionStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        SUCCESS = 'success', 'Success'
        FAILED = 'failed', 'Failed'
        REFUNDED = 'refunded', 'Refunded'
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, blank=False, null=False, unique=True, verbose_name='Transaction ID')
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="transactions", verbose_name='User')
    
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(1_000_000_000)], verbose_name='Paid Amount')
    currency = models.CharField(choices=CurrencyChoices.choices, max_length=10, verbose_name='Currency')
    
    transaction_type = models.CharField(max_length=10, choices=TransactionTypes.choices, verbose_name='Transaction Type')
    transaction_reason = models.CharField(max_length=20, choices=TransactionReason.choices, verbose_name='Transaction Reason')
    transaction_status = models.CharField(max_length=20, choices=TransactionStatus.choices, verbose_name='Transaction Status')
    
    provider = models.CharField(max_length=100, verbose_name='Provider')
    tracking_id = models.CharField(max_length=200, unique=True, verbose_name='Tracking ID')
    provider_payload = models.JSONField(blank=True, null=True, verbose_name='Provider Payload')
    
    metadata = models.JSONField(default=dict, blank=True, verbose_name='Transaction metadata', help_text='IP Address, Device Info')
    
    description = models.TextField(max_length=300, blank=True, null=True, verbose_name='Description', help_text='Any thing about the transaction like failure reason.')
    
    locked_in = models.BooleanField(default=False, verbose_name='Locked in')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Created at')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Updated at')
    
    def __str__(self):
        return f'Transaction {self.id} - {self.tracking_id}'
