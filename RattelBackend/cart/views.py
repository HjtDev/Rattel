import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from RattelBackend.cache import invalidate_cache
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin
from .models import CartItem

logger = logging.getLogger(__name__)


class CartView(APIView, GetDataMixin, ResponseBuilderMixin):
    """
    Main cart endpoint.

    Permissions:
        - IsAuthenticated: Must be logged in.

    Throttling:
        - Uses the `main-throttle` scope.

    GET:
        Returns all cart items serialized via each item's CART_SERIALIZER,
        along with the total cart price.

    POST:
        Adds or decreases an item in the cart.
        Requires: app_label, model, object_id (int).
        Optional: quantity (int, default=1). Pass a negative value to decrease.

    DELETE:
        - If app_label, model, and object_id are provided: removes that specific item.
        - If none are provided: clears the entire cart.
    """

    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'

    def get(self, request):
        """
        Return all cart items serialized with their model's CART_SERIALIZER
        and the total price of the cart.

        Returns:
            200 OK:
                - success=True
                - message: 'Successful'
                - items: List of serialized cart items
                - total_price: Total price of all items in the cart
        """
        cart = CartItem.for_user(request.user)

        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            items=cart.get_serialized_items(),
            total_price=cart.total_price(),
        )

    def post(self, request):
        """
        Add or decrease an item in the cart.

        Body Params:
            app_label (str):  App label of the item's model.
            model (str):      Model name (lowercase).
            object_id (int):  Primary key of the item.
            quantity (int):   Units to add (positive) or decrease (negative). Default: 1.

        Returns:
            200 OK:
                - success=True
                - message: 'added' | 'updated' | 'removed'

            400 BAD REQUEST:
                - success=False
                - error: -1
                - message: Validation/failure reason

            403 FORBIDDEN:
                - success=False
                - error: -10
                - message: 'Insecure parameter'
        """
        success, data = self.get_data(request, 'app_label', 'model', 'object_id')
        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=data,
            )

        app_label = data['app_label']
        model = data['model']
        object_id = data['object_id']

        for field_name, value in (('app_label', app_label), ('model', model)):
            if not self.validate_string_secure(value, sql=True, lookup=True, injection=True):
                logger.warning(
                    f'Insecure cart POST param {field_name}={value!r} '
                    f'from user {request.user.pk}'
                )
                return self.build_response(
                    status.HTTP_403_FORBIDDEN,
                    success=False,
                    error=-10,
                    message='Insecure parameter',
                )

        if not self.validate_string_secure(object_id, sql=True, lookup=True, injection=True):
            logger.warning(
                f'Insecure cart POST param object_id={object_id!r} '
                f'from user {request.user.pk}'
            )
            return self.build_response(
                status.HTTP_403_FORBIDDEN,
                success=False,
                error=-10,
                message='Insecure parameter',
            )

        quantity = request.data.get('quantity', 1)
        try:
            quantity = int(quantity)
        except (ValueError, TypeError):
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message='quantity must be an integer.',
            )

        cart = CartItem.for_user(request.user)
        ok, result = cart.add(app_label, model, object_id, quantity)

        if not ok:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result,
            )

        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message=result,
        )

    def delete(self, request):
        """
        Remove a specific item or clear the entire cart.

        Body Params (all optional — omit all to clear the cart):
            app_label (str):  App label of the item's model.
            model (str):      Model name (lowercase).
            object_id (int):  Primary key of the item.

        Returns:
            200 OK:
                - success=True
                - message: 'removed' | 'cleared'
                - count (only on clear): Number of items deleted

            400 BAD REQUEST:
                - success=False
                - error: -1
                - message: Failure reason

            403 FORBIDDEN:
                - success=False
                - error: -10
                - message: 'Insecure parameter'
        """
        app_label = request.data.get('app_label')
        model = request.data.get('model')
        object_id = request.data.get('object_id')

        cart = CartItem.for_user(request.user)

        if app_label is None and model is None and object_id is None:
            deleted_count = cart.clear()
            return self.build_response(
                status.HTTP_200_OK,
                success=True,
                message='cleared',
                count=deleted_count,
            )

        for field_name, value in (('app_label', app_label), ('model', model)):
            if not isinstance(value, str) or not self.validate_string_secure(
                value, sql=True, lookup=True, injection=True
            ):
                logger.warning(
                    f'Insecure cart DELETE param {field_name}={value!r} '
                    f'from user {request.user.pk}'
                )
                return self.build_response(
                    status.HTTP_403_FORBIDDEN,
                    success=False,
                    error=-10,
                    message='Insecure parameter',
                )

        if not isinstance(object_id, str) or not self.validate_string_secure(
            object_id, sql=True, lookup=True, injection=True
        ):
            logger.warning(
                f'Insecure cart DELETE param object_id={object_id!r} '
                f'from user {request.user.pk}'
            )
            return self.build_response(
                status.HTTP_403_FORBIDDEN,
                success=False,
                error=-10,
                message='Insecure parameter',
            )

        ok, result = cart.remove(app_label, model, object_id)

        if not ok:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result,
            )

        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message=result,
        )


class CartLengthView(APIView, ResponseBuilderMixin):
    """
    Returns the number of distinct items in the user's cart.

    Permissions:
        - IsAuthenticated: Must be logged in.

    Throttling:
        - Uses the `main-throttle` scope.
    """

    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'

    def get(self, request):
        """
        Return the count of distinct cart item rows.

        Returns:
            200 OK:
                - success=True
                - message: 'Successful'
                - length: Number of distinct items in the cart
        """
        cart = CartItem.for_user(request.user)
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            length=cart.length(),
        )


class CartTotalPriceView(APIView, ResponseBuilderMixin):
    """
    Returns the total price of all items in the user's cart.

    Permissions:
        - IsAuthenticated: Must be logged in.

    Throttling:
        - Uses the `main-throttle` scope.
    """

    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'

    def get(self, request):
        """
        Return the total price of the cart, respecting discounts.

        Returns:
            200 OK:
                - success=True
                - message: 'Successful'
                - total_price: Sum of effective prices across all cart items
        """
        cart = CartItem.for_user(request.user)
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            total_price=cart.total_price(),
        )


class CartFinalizerView(APIView, GetDataMixin, ResponseBuilderMixin):
    """
    Finalizes a purchase by verifying the transaction and granting the user
    access to each item in their cart.

    Permissions:
        - IsAuthenticated: Must be logged in.

    Throttling:
        - Uses the `main-throttle` scope.

    POST:
        Verifies the transaction_id against the cart total and marks all items
        as purchased by adding the user to each item's bought_by, then clears
        the cart.
    """

    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'
    cache_invalidation = ('course_detail',)

    def post(self, request):
        """
        Finalize the purchase for the authenticated user's cart.

        Body Params:
            transaction_id (str): UUID of the Transaction created by the payment gateway.

        Returns:
            200 OK:
                - success=True
                - message: 'Purchase finalized.'

            400 BAD REQUEST:
                - success=False
                - error: -1
                - message: Missing/invalid field

            402 PAYMENT REQUIRED:
                - success=False
                - error: -3
                - message: Transaction amount does not cover cart total

            403 FORBIDDEN:
                - success=False
                - error: -10
                - message: 'Insecure parameter' | Transaction belongs to a different user

            404 NOT FOUND:
                - success=False
                - error: -2
                - message: Transaction not found

            409 CONFLICT:
                - success=False
                - error: -4
                - message: Transaction already used (locked_in)
        """
        from payment.models import Transaction

        success, data = self.get_data(request, 'transaction_id')
        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=data,
            )

        transaction_id = data['transaction_id']

        if not self.validate_string_secure(transaction_id, sql=True, lookup=True, injection=True):
            logger.warning(
                f'Insecure transaction_id={transaction_id!r} '
                f'from user {request.user.pk} in CartFinalizerView.'
            )
            return self.build_response(
                status.HTTP_403_FORBIDDEN,
                success=False,
                error=-10,
                message='Insecure parameter',
            )

        try:
            transaction = Transaction.objects.get(pk=transaction_id)
        except Transaction.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-2,
                message='Transaction not found.',
            )

        if transaction.user != request.user:
            logger.warning(
                f'User {request.user.pk} attempted to finalize transaction '
                f'{transaction_id} that belongs to user {transaction.user_id}.'
            )
            return self.build_response(
                status.HTTP_403_FORBIDDEN,
                success=False,
                error=-10,
                message='This transaction does not belong to you.',
            )

        if transaction.locked_in:
            return self.build_response(
                status.HTTP_409_CONFLICT,
                success=False,
                error=-4,
                message='This transaction has already been used.',
            )

        if transaction.transaction_status != Transaction.TransactionStatus.SUCCESS:
            return self.build_response(
                status.HTTP_402_PAYMENT_REQUIRED,
                success=False,
                error=-5,
                message='Transaction has not been completed successfully.',
            )

        cart = CartItem.for_user(request.user)

        cart_total_in_rial = cart.total_price() * 10

        if transaction.amount < cart_total_in_rial:
            return self.build_response(
                status.HTTP_402_PAYMENT_REQUIRED,
                success=False,
                error=-3,
                message='Transaction amount does not cover the cart total.',
            )

        for cart_item in cart:
            cart_item.item.bought_by.add(request.user)

        for cache_key in self.cache_invalidation:
            invalidate_cache(cache_key, request)

        transaction.locked_in = True
        transaction.save(update_fields=['locked_in'])

        cart.clear()

        logger.info(
            f'Cart finalized for user {request.user.pk} '
            f'via transaction {transaction_id}.'
        )

        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Purchase finalized.',
        )
