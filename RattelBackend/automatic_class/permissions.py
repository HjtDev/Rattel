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


class IsAutomaticClassStaff(BasePermission):
    """
    Grants access to the automatic-class teacher/admin panel: staff,
    superusers, or a profile.role == 'teacher' user — matches the frontend's
    panel-visibility gate.

    This only controls whether the panel is reachable at all. Object-level
    scoping to the requester's own plans (unless they're a superuser) happens
    separately in each view's queryset.
    """
    message = 'Staff, superuser, or teacher role is required to access the automatic class panel.'

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_staff or user.is_superuser:
            return True
        profile = getattr(user, 'profile', None)
        return bool(profile and profile.role == 'teacher')
