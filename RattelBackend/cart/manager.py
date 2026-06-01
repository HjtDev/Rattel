from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ImproperlyConfigured
import logging


logger = logging.getLogger(__name__)


class CartManager:
    """
    Manages cart operations for an authenticated user.

    Handles add, remove, clear, length, and iteration over cart items.
    All operations are scoped to a single user instance.

    Allowed item types are controlled via settings.CART_ALLOWED_CONTENT_TYPES,
    which must be a list of '<app_label>.<model>' strings.
    """

    def __init__(self, user):
        self.user = user

    def _get_allowed_content_types(self) -> list[ContentType]:
        """
        Resolves the allowed ContentType instances from settings.CART_ALLOWED_CONTENT_TYPES.

        Returns:
            List of allowed ContentType instances.

        Raises:
            ImproperlyConfigured: If the setting is missing or malformed.
        """
        allowed = getattr(settings, 'CART_ALLOWED_CONTENT_TYPES', None)

        if allowed is None:
            raise ImproperlyConfigured(
                'CART_ALLOWED_CONTENT_TYPES must be defined in settings as a list of '
                '"<app_label>.<model>" strings.'
            )

        content_types = []
        for entry in allowed:
            try:
                app_label, model = entry.split('.')
            except ValueError:
                raise ImproperlyConfigured(
                    f'Invalid CART_ALLOWED_CONTENT_TYPES entry "{entry}". '
                    f'Expected format: "<app_label>.<model>".'
                )
            try:
                content_types.append(ContentType.objects.get(app_label=app_label, model=model))
            except ContentType.DoesNotExist:
                raise ImproperlyConfigured(
                    f'ContentType for "{entry}" does not exist. '
                    f'Make sure the app and model are correctly registered.'
                )

        return content_types

    def _resolve_content_type(self, app_label: str, model: str) -> ContentType | None:
        """
        Validates and returns the ContentType if it is in the allowed list.

        Args:
            app_label: The app label of the model.
            model: The model name (lowercase).

        Returns:
            ContentType instance if allowed, None otherwise.
        """
        allowed = self._get_allowed_content_types()

        try:
            content_type = ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist:
            logger.warning(f'ContentType "{app_label}.{model}" does not exist.')
            return None

        if content_type not in allowed:
            logger.warning(
                f'ContentType "{app_label}.{model}" is not in CART_ALLOWED_CONTENT_TYPES.'
            )
            return None

        return content_type

    def add(self, app_label: str, model: str, object_id: str | int, quantity: int = 1) -> tuple[bool, str]:
        """
        Adds or decreases an item in the cart.
        Pass a positive quantity to add/stack, a negative quantity to decrease.
        If the resulting quantity drops to zero or below the item is removed from the cart.

        Args:
            app_label: The app label of the item's model.
            model: The model name (lowercase).
            object_id: The primary key of the item instance.
            quantity: Units to add (positive) or remove (negative). Must not be 0.

        Returns:
            (True, 'added') if a new cart item was created.
            (True, 'updated') if an existing cart item's quantity was increased.
            (True, 'removed') if the decrease brought the quantity to zero or below.
            (False, reason) on failure.
        """
        from .models import CartItem

        if not isinstance(quantity, int) or quantity == 0:
            logger.error(f'Invalid quantity "{quantity}" provided to CartManager.add.')
            return False, 'Quantity must be a non-zero integer.'

        content_type = self._resolve_content_type(app_label, model)
        if content_type is None:
            return False, f'"{app_label}.{model}" is not an allowed cart item type.'

        if quantity > 0:
            item_obj = content_type.model_class().objects.filter(pk=object_id).first()
            if item_obj is None:
                logger.error(f'Object with id={object_id} does not exist for "{app_label}.{model}".')
                return False, 'Item does not exist.'
            if hasattr(item_obj, 'bought_by') and item_obj.bought_by.filter(pk=self.user.pk).exists():
                logger.info(
                    f'User {self.user.pk} already owns "{app_label}.{model}" id={object_id}. '
                    f'Blocked cart add.'
                )
                return False, 'You already own this item.'

        object_id = str(object_id)

        cart_item = CartItem.objects.filter(
            user=self.user,
            content_type=content_type,
            object_id=object_id,
        ).first()

        if cart_item is not None:
            new_quantity = cart_item.quantity + quantity
            if new_quantity <= 0:
                cart_item.delete()
                logger.info(
                    f'Removed "{app_label}.{model}" id={object_id} from cart for user '
                    f'{self.user.pk} after quantity dropped to {new_quantity}.'
                )
                return True, 'removed'
            cart_item.quantity = new_quantity
            cart_item.save(update_fields=['quantity'])
            logger.info(
                f'Updated quantity for "{app_label}.{model}" id={object_id} '
                f'to {new_quantity} for user {self.user.pk}.'
            )
            return True, 'updated'

        if quantity < 0:
            logger.warning(
                f'Tried to decrease "{app_label}.{model}" id={object_id} '
                f'for user {self.user.pk} but it was not in the cart.'
            )
            return False, 'Item not found in cart.'

        CartItem.objects.create(
            user=self.user,
            content_type=content_type,
            object_id=object_id,
            quantity=quantity,
        )
        logger.info(
            f'Added "{app_label}.{model}" id={object_id} '
            f'(qty={quantity}) to cart for user {self.user.pk}.'
        )
        return True, 'added'

    def remove(self, app_label: str, model: str, object_id: str | int) -> tuple[bool, str]:
        """
        Removes an item from the cart entirely.

        Args:
            app_label: The app label of the item's model.
            model: The model name (lowercase).
            object_id: The primary key of the item instance.

        Returns:
            (True, 'removed') if the item was found and deleted.
            (False, reason) if the item was not in the cart.
        """
        from .models import CartItem

        content_type = self._resolve_content_type(app_label, model)
        if content_type is None:
            return False, f'"{app_label}.{model}" is not an allowed cart item type.'

        object_id = str(object_id)

        deleted_count, _ = CartItem.objects.filter(
            user=self.user,
            content_type=content_type,
            object_id=object_id,
        ).delete()

        if deleted_count == 0:
            logger.warning(
                f'Tried to remove "{app_label}.{model}" id={object_id} '
                f'from cart for user {self.user.pk} but it was not found.'
            )
            return False, 'Item not found in cart.'

        logger.info(
            f'Removed "{app_label}.{model}" id={object_id} '
            f'from cart for user {self.user.pk}.'
        )
        return True, 'removed'

    def clear(self) -> int:
        """
        Removes all items from the user's cart.

        Returns:
            Number of items deleted.
        """
        from .models import CartItem

        deleted_count, _ = CartItem.objects.filter(user=self.user).delete()
        logger.info(f'Cleared cart for user {self.user.pk}. {deleted_count} item(s) removed.')
        return deleted_count

    def length(self) -> int:
        """
        Returns the total number of cart item rows (not sum of quantities).

        Returns:
            Integer count of distinct cart items.
        """
        from .models import CartItem

        return CartItem.objects.filter(user=self.user).count()

    def __len__(self):
        return self.length()

    def __iter__(self):
        """
        Iterates over the user's cart items, each with its resolved content object.

        Yields:
            CartItem instances with .item populated (the actual model instance).
        """
        from .models import CartItem

        items = CartItem.objects.filter(user=self.user).select_related('content_type')
        for cart_item in items:
            cart_item.item = cart_item.content_object
            yield cart_item

    def total_price(self) -> float:
        """
        Returns the total price of all items in the cart.

        For each item, uses new_price if it is non-zero (discounted), otherwise uses price.
        The quantity of each cart item is taken into account.

        Returns:
            Total price as a float.
        """
        total = 0
        for cart_item in self:
            item = cart_item.item
            unit_price = item.new_price if item.new_price else item.price
            total += unit_price * cart_item.quantity
        return total

    def get_serialized_items(self) -> list:
        """
        Returns a serialized list of all items in the cart.

        For each cart item, retrieves the CART_SERIALIZER classproperty from the
        item's model class and uses it to serialize the item instance.

        Returns:
            List of serialized item data dicts.
        """
        serialized = []
        for cart_item in self:
            item = cart_item.item
            serializer_class = item.__class__.CART_SERIALIZER
            serialized_item = serializer_class(item).data
            serialized_item['quantity'] = cart_item.quantity
            serialized_item['app_label'] = cart_item.content_type.app_label
            serialized_item['model'] = cart_item.content_type.model
            serialized_item['object_id'] = cart_item.object_id
            if hasattr(item, 'price'):
                serialized_item['price'] = item.price
            if hasattr(item, 'new_price'):
                serialized_item['new_price'] = item.new_price
            serialized.append(serialized_item)
        return serialized
