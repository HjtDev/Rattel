from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models
from django.conf import settings
from django.utils.translation import gettext_lazy as _
import uuid


class Transaction(models.Model):
    class Meta:
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['transaction_status']),
            models.Index(fields=['tracking_id']),
        ]
        
    class CurrencyChoices(models.TextChoices):
        IRR = 'IRR', _('Rial')
        IRT = 'IRT', _('Toman')
        
    class TransactionTypes(models.TextChoices):
        GATEWAY = 'gateway', _('Gateway')
        TRANSFER = 'transfer', _('Transfer')
        CASH = 'cash', _('Cash')
        
    class TransactionReason(models.TextChoices):
        PAYMENT = 'payment', _('Payment')
        REFUND = 'refund', _('Refund')
        WITHDRAWAL = 'withdrawal', _('Withdrawal')
        DEPOSIT = 'deposit', _('Deposit')
        FEE = 'fee', _('Fee')
        ADJUSTMENT = 'adjustment', _('Adjustment')
        
    class TransactionStatus(models.TextChoices):
        PENDING = 'pending', _('Pending')
        SUCCESS = 'success', _('Success')
        FAILED = 'failed', _('Failed')
        REFUNDED = 'refunded', _('Refunded')
        
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False, blank=False, null=False, unique=True, verbose_name=_('Transaction ID'))
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="transactions", verbose_name=_('User'))
    
    amount = models.PositiveIntegerField(validators=[MinValueValidator(1), MaxValueValidator(1_000_000_000)], verbose_name=_('Paid Amount'))
    currency = models.CharField(choices=CurrencyChoices.choices, max_length=10, verbose_name=_('Currency'))
    
    transaction_type = models.CharField(max_length=10, choices=TransactionTypes.choices, verbose_name=_('Transaction Type'))
    transaction_reason = models.CharField(max_length=20, choices=TransactionReason.choices, verbose_name=_('Transaction Reason'))
    transaction_status = models.CharField(max_length=20, choices=TransactionStatus.choices, verbose_name=_('Transaction Status'))
    
    provider = models.CharField(max_length=100, verbose_name=_('Provider'))
    tracking_id = models.CharField(max_length=200, unique=True, verbose_name=_('Tracking ID'))
    provider_payload = models.JSONField(blank=True, null=True, verbose_name=_('Provider Payload'))
    
    metadata = models.JSONField(default=dict, blank=True, verbose_name=_('Transaction metadata'), help_text=_('IP Address, Device Info'))
    
    description = models.TextField(max_length=300, blank=True, null=True, verbose_name=_('Description'), help_text=_('Any thing about the transaction like failure reason.'))
    
    locked_in = models.BooleanField(default=False, verbose_name=_('Locked in'))
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Created at'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Updated at'))
    
    def __str__(self):
        return f'Transaction {self.id} - {self.tracking_id}'
