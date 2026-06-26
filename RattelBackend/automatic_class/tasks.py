import logging
from celery import shared_task
from django.conf import settings
from django.db.models import Exists, OuterRef
from django.utils import timezone

logger = logging.getLogger(__name__)


@shared_task(name='automatic_class.mark_delayed_steps')
def mark_delayed_steps():
    """
    Nightly task: marks every pending PlanStep whose scheduled_date has passed as DELAYED.
    Schedule this in the admin under Periodic Tasks (django-celery-beat):
        Task: automatic_class.mark_delayed_steps
        Crontab: 0 0 * * *  (midnight every day)
    """
    from .models import PlanStep, AutomaticPlan

    today = timezone.now().date()

    overdue = PlanStep.objects.filter(
        status=PlanStep.Status.PENDING,
        scheduled_date__lt=today,
        plan__status=AutomaticPlan.Status.ACTIVE,
    ).select_related('plan')

    count = overdue.count()
    if count == 0:
        logger.info('mark_delayed_steps: no overdue steps found.')
        return 'No overdue steps.'

    for step in overdue:
        step.mark_delayed()

    logger.info(f'mark_delayed_steps: marked {count} steps as delayed.')
    return f'Marked {count} steps as delayed.'


@shared_task(name='automatic_class.alert_inactive_plan_users')
def alert_inactive_plan_users():
    """
    Periodic task: sends SMS to users who have an ACTIVE plan with at least one
    overdue step (scheduled_date < today, status PENDING or DELAYED).
    Schedule in admin under Periodic Tasks (django-celery-beat):
        Task: automatic_class.alert_inactive_plan_users
        Crontab: 0 9 * * 1  (9 AM every Monday, for example)
    """
    from .models import AutomaticPlan, PlanStep

    required_settings = (
        'SMS_HANDLER',
        'SMS_PROVIDER',
        'SMS_SETTINGS',
        'SMS_API_AUTOMATIC_PLAN_DELAYED_ALERT_TEMPLATE',
    )
    for setting in required_settings:
        if not hasattr(settings, setting):
            logger.warning(f'{setting} not configured')
            return f'{setting} not configured.'

    try:
        sms = settings.SMS_HANDLER(settings.SMS_PROVIDER, **settings.SMS_SETTINGS)
    except Exception as e:
        logger.error(f'Failed to initialize SMS handler: {e}')
        return f'Failed to initialize SMS handler: {e}'

    today = timezone.now().date()

    inactive_plans = AutomaticPlan.objects.filter(
        status=AutomaticPlan.Status.ACTIVE,
    ).filter(
        Exists(
            PlanStep.objects.filter(
                plan=OuterRef('pk'),
                status__in=[PlanStep.Status.PENDING, PlanStep.Status.DELAYED],
                scheduled_date__lt=today,
            )
        )
    ).select_related('user')

    count = 0
    for plan in inactive_plans:
        user = plan.user
        if not user.phone:
            continue
        try:
            sent = sms.provider.send_with_template(
                settings.SMS_API_AUTOMATIC_PLAN_DELAYED_ALERT_TEMPLATE,
                user.phone,
                user.name or user.username,
            )
            if sent:
                count += 1
            else:
                logger.warning(f'SMS provider returned False for {user.phone}')
        except Exception as e:
            logger.error(
                f'Failed to send inactive plan SMS to {user.phone}. Exception: {e}',
                exc_info=True,
            )

    logger.info(f'alert_inactive_plan_users: sent {count} alerts.')
    return f'Sent {count} inactive plan alerts.'
