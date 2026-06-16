import logging
from celery import shared_task
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
