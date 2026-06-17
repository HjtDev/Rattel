from rest_framework.permissions import BasePermission
from subscriptions.permissions import _get_subscription


class HasAutomaticClassAccess(BasePermission):
    """Requires an active subscription with online class access."""
    message = 'An active subscription with online class access is required to use the automatic class system.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        sub = _get_subscription(request.user)
        return sub is not None and sub.has_feature_online_class(min_meetings=1)
