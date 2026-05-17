from django.db import models
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MinValueValidator
from django.utils.translation import gettext_lazy as _
from .manager import CartManager


class CartItem(models.Model):
    class Meta:
        verbose_name = 'Cart Item'
        verbose_name_plural = 'Cart Items'
        indexes = [
            models.Index(fields=['user', 'content_type', 'object_id']),
        ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cart_items',
        verbose_name=_('User'),
    )

    content_type = models.ForeignKey(
        ContentType,
        on_delete=models.CASCADE,
        verbose_name=_('Item Type'),
    )
    object_id = models.CharField(max_length=255, verbose_name=_('Item ID'))
    content_object = GenericForeignKey('content_type', 'object_id')

    quantity = models.PositiveIntegerField(
        default=1,
        validators=[MinValueValidator(1)],
        verbose_name=_('Quantity'),
    )

    added_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Added At'))

    def __str__(self):
        return f"{self.user.username}'s cart — {self.content_type} id={self.object_id} (qty={self.quantity})"

    @staticmethod
    def for_user(user) -> CartManager:
        """
        Returns a CartManager instance scoped to the given user.

        Args:
            user: An authenticated User instance.

        Returns:
            CartManager bound to that user.
        """
        return CartManager(user)
