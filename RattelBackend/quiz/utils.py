from django.db.models import Sum

from .models import Quiz, QuizAccessRequirement, QuizAttempt


def _check_access(quiz: Quiz, user) -> tuple[bool, str]:
    """Return (access_met, denial_reason). Checks all requirements with AND semantics."""
    for req in quiz.access_requirements.all():
        if req.type == QuizAccessRequirement.Type.FREE:
            continue
        if req.type == QuizAccessRequirement.Type.SUBSCRIPTION:
            sub = getattr(user, 'subscription', None)
            if not sub or not sub.has_feature_quiz():
                return False, 'اشتراک فعال با دسترسی به آزمون نیاز است.'
        elif req.type == QuizAccessRequirement.Type.COMPLETED_QUIZ:
            if not req.required_quiz:
                continue
            if not QuizAttempt.objects.filter(
                user=user, quiz=req.required_quiz, status=QuizAttempt.Status.COMPLETED
            ).exists():
                return False, 'باید آزمون پیش‌نیاز را تکمیل کنید.'
        elif req.type == QuizAccessRequirement.Type.MIN_SCORE:
            total = (
                QuizAttempt.objects
                .filter(user=user, status=QuizAttempt.Status.COMPLETED)
                .aggregate(total=Sum('score'))['total'] or 0
            )
            if total < (req.required_score or 0):
                return False, f'حداقل {req.required_score} امتیاز کل نیاز است.'
    return True, ''
