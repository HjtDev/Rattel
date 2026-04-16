import logging

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

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

        try:
            object_id = int(object_id)
        except (ValueError, TypeError):
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message='object_id must be an integer.',
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

        try:
            object_id = int(object_id)
        except (ValueError, TypeError):
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message='object_id must be an integer.',
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
