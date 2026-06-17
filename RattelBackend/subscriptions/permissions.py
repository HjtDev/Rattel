from rest_framework.permissions import BasePermission


def _get_subscription(user):
    return getattr(user, 'subscription', None)


class HasEarlyNewsAccess(BasePermission):
    message = 'An active subscription with early news access is required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        sub = _get_subscription(request.user)
        return sub is not None and sub.has_feature_early_news()


class HasQuizAccess(BasePermission):
    message = 'An active subscription with quiz access is required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        sub = _get_subscription(request.user)
        return sub is not None and sub.has_feature_quiz()


class HasFreeCourseAccess(BasePermission):
    message = 'An active subscription with free course access is required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        sub = _get_subscription(request.user)
        return sub is not None and sub.has_feature_free_courses()


class HasOnlineClassAccess(BasePermission):
    """Passes if the user has any level of online class access (≥ 1 meeting/month)."""
    message = 'An active subscription with online class access is required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        sub = _get_subscription(request.user)
        return sub is not None and sub.has_feature_online_class(min_meetings=1)


class HasOnlineClassAccess4(BasePermission):
    """Passes if the user has at least 4 online class meetings/month."""
    message = 'An active subscription with at least 4 online meetings per month is required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        sub = _get_subscription(request.user)
        return sub is not None and sub.has_feature_online_class(min_meetings=4)


class HasOnlineClassAccess8(BasePermission):
    """Passes if the user has at least 8 online class meetings/month."""
    message = 'An active subscription with at least 8 online meetings per month is required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        sub = _get_subscription(request.user)
        return sub is not None and sub.has_feature_online_class(min_meetings=8)


class HasOnlineClassAccess12(BasePermission):
    """Passes if the user has at least 12 online class meetings/month."""
    message = 'An active subscription with at least 12 online meetings per month is required.'

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        sub = _get_subscription(request.user)
        return sub is not None and sub.has_feature_online_class(min_meetings=12)
