import logging
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from RattelBackend.cache import drf_cached_response
from RattelBackend.mixins import ResponseBuilderMixin
from .models import Plan, UserSubscription
from .serializers import PlanSerializer, UserSubscriptionSerializer

logger = logging.getLogger(__name__)


class PlanListView(APIView, ResponseBuilderMixin):
    """
    Public endpoint listing all visible subscription plans.

    Permissions:
        - AllowAny

    Caching:
        - TTL: 15 minutes (900 seconds)
        - Cache prefix: 'subscription_plans'

    Returns:
        200 OK:
            - success=True
            - message: 'Successful'
            - plans: Serialized plan list ordered by price
            - total: Count of plans

        500 INTERNAL SERVER ERROR:
            - success=False
            - error: -1
            - message: Generic failure message
    """

    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    @method_decorator(
        drf_cached_response(
            ttl=900,
            cache_prefix='subscription_plans',
            user_aware=False,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        try:
            plans = Plan.objects.filter(is_visible=True)
            serializer = PlanSerializer(plans, many=True, context={'request': request})
            return self.build_response(
                status.HTTP_200_OK,
                success=True,
                message='Successful',
                plans=serializer.data,
                total=plans.count(),
            )
        except Exception as e:
            logger.error(f'PlanListView failed: {e.__class__.__name__}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-1,
                message='Something went wrong while fetching subscription plans.',
            )


class MySubscriptionView(APIView, ResponseBuilderMixin):
    """
    Returns the authenticated user's current subscription.

    Permissions:
        - IsAuthenticated

    Returns:
        200 OK:
            - success=True
            - subscription: { plan, started_at, ends_in, is_active }

        404 NOT FOUND:
            - success=False
            - error: -1  (no subscription)

        500 INTERNAL SERVER ERROR:
            - success=False
            - error: -2
    """

    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'

    def get(self, request):
        try:
            subscription = UserSubscription.objects.select_related('plan').get(user=request.user)
        except UserSubscription.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-1,
                message='No active subscription found.',
            )
        except Exception as e:
            logger.error(f'MySubscriptionView failed: {e.__class__.__name__}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-2,
                message='Something went wrong.',
            )

        serializer = UserSubscriptionSerializer(subscription, context={'request': request})
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            subscription=serializer.data,
        )
