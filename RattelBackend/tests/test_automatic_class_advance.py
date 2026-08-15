from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from automatic_class.models import AutomaticPlan, PlanStep

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='acuser',
        name='AC User',
        phone='09100000020',
        password='testpass123',
    )


@pytest.fixture
def subscription(db, user):
    from subscriptions.models import Plan, UserSubscription

    plan = Plan.objects.create(
        name='Premium',
        description='desc',
        price=100000,
        online_class_limit=Plan.OnlineClassLimit.PREMIUM,
    )
    return UserSubscription.objects.create(
        user=user,
        plan=plan,
        ends_in=date.today() + timedelta(days=30),
    )


def _make_plan(user, advance_completion_days=None, **overrides):
    defaults = {
        'user': user,
        'start_page': 1,
        'end_page': 30,
        'start_date': date.today() - timedelta(days=5),
        'time_to_finish': date.today() + timedelta(days=30),
        'time_freq': AutomaticPlan.TimeFrequency.PER_DAY,
        'reading_freq': AutomaticPlan.ReadingFrequency.FULL_PAGE,
        'user_day_availability': AutomaticPlan.DayAvailability.ODD_DAYS,
        'user_time_availability': AutomaticPlan.TimeAvailability.MORNING,
        'status': AutomaticPlan.Status.ACTIVE,
        'advance_completion_days': advance_completion_days,
    }
    defaults.update(overrides)
    plan = AutomaticPlan(**defaults)
    # Bypass the auto step-generation side effect on save(); tests build steps explicitly.
    plan._steps_generated = True
    plan.save()
    return plan


def _make_step(plan, step_number, scheduled_date, status=PlanStep.Status.PENDING, **overrides):
    defaults = {
        'plan': plan,
        'step_number': step_number,
        'scheduled_date': scheduled_date,
        'step_type': PlanStep.StepType.MEMORIZE,
        'page_start': step_number,
        'page_end': step_number,
        'status': status,
    }
    defaults.update(overrides)
    return PlanStep.objects.create(**defaults)


@pytest.fixture
def api_client(user, subscription):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def complete_url(step_id):
    return reverse('automatic:step-complete', args=[step_id])


def today_url():
    return reverse('automatic:today-steps')


@pytest.mark.django_db
class TestUnlockedAheadSteps:
    def test_no_limit_blocks_future_step(self, user):
        plan = _make_plan(user, advance_completion_days=None)
        today_step = _make_step(plan, 1, date.today())
        future_step = _make_step(plan, 2, date.today() + timedelta(days=1))

        assert list(plan.get_unlocked_ahead_steps()) == []

    def test_open_overdue_step_blocks_unlock(self, user):
        plan = _make_plan(user, advance_completion_days=1)
        _make_step(plan, 1, date.today() - timedelta(days=1))  # still pending
        _make_step(plan, 2, date.today() + timedelta(days=1))

        assert list(plan.get_unlocked_ahead_steps()) == []

    def test_unlocks_next_day_once_current_is_closed(self, user):
        plan = _make_plan(user, advance_completion_days=1)
        _make_step(plan, 1, date.today(), status=PlanStep.Status.COMPLETED)
        next_day_1 = _make_step(plan, 2, date.today() + timedelta(days=1))
        next_day_2 = _make_step(plan, 3, date.today() + timedelta(days=1))
        far_step = _make_step(plan, 4, date.today() + timedelta(days=2))

        ahead = list(plan.get_unlocked_ahead_steps())
        assert set(ahead) == {next_day_1, next_day_2}
        assert far_step not in ahead

    def test_completing_unlocked_day_does_not_open_next_window(self, user):
        plan = _make_plan(user, advance_completion_days=1)
        _make_step(plan, 1, date.today(), status=PlanStep.Status.COMPLETED)
        _make_step(plan, 2, date.today() + timedelta(days=1), status=PlanStep.Status.COMPLETED)
        _make_step(plan, 3, date.today() + timedelta(days=2))

        assert list(plan.get_unlocked_ahead_steps()) == []

    def test_unlimited_window_keeps_unlocking_successive_days(self, user):
        plan = _make_plan(user, advance_completion_days=0)
        _make_step(plan, 1, date.today(), status=PlanStep.Status.COMPLETED)
        day2 = _make_step(plan, 2, date.today() + timedelta(days=1))
        _make_step(plan, 3, date.today() + timedelta(days=5))

        ahead = list(plan.get_unlocked_ahead_steps())
        assert ahead == [day2]


@pytest.mark.django_db
class TestStepCompleteView:
    def test_future_step_rejected_when_no_limit(self, api_client, user):
        plan = _make_plan(user, advance_completion_days=None)
        step = _make_step(plan, 1, date.today() + timedelta(days=1))

        resp = api_client.post(complete_url(step.id))
        assert resp.status_code == 400
        assert resp.data['error'] == -6
        step.refresh_from_db()
        assert step.status == PlanStep.Status.PENDING

    def test_future_step_rejected_while_earlier_step_open(self, api_client, user):
        plan = _make_plan(user, advance_completion_days=1)
        _make_step(plan, 1, date.today())  # still pending
        future = _make_step(plan, 2, date.today() + timedelta(days=1))

        resp = api_client.post(complete_url(future.id))
        assert resp.status_code == 400
        assert resp.data['error'] == -6

    def test_unlocked_future_step_completes_and_is_not_marked_delayed(self, api_client, user):
        plan = _make_plan(user, advance_completion_days=1)
        _make_step(plan, 1, date.today(), status=PlanStep.Status.COMPLETED)
        future = _make_step(plan, 2, date.today() + timedelta(days=1))

        resp = api_client.post(complete_url(future.id))
        assert resp.status_code == 200
        future.refresh_from_db()
        assert future.status == PlanStep.Status.COMPLETED
        assert future.is_delayed is False

    def test_today_and_overdue_steps_still_completable_out_of_order(self, api_client, user):
        plan = _make_plan(user, advance_completion_days=None)
        overdue = _make_step(plan, 1, date.today() - timedelta(days=2))
        today_step = _make_step(plan, 2, date.today())

        resp = api_client.post(complete_url(today_step.id))
        assert resp.status_code == 200
        resp = api_client.post(complete_url(overdue.id))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestTodayStepsView:
    def test_ahead_steps_excluded_from_upcoming_preview(self, api_client, user):
        plan = _make_plan(user, advance_completion_days=1)
        _make_step(plan, 1, date.today(), status=PlanStep.Status.COMPLETED)
        next_day = _make_step(plan, 2, date.today() + timedelta(days=1))
        far_step = _make_step(plan, 3, date.today() + timedelta(days=5))

        resp = api_client.get(today_url())
        assert resp.status_code == 200
        ahead_ids = {s['id'] for s in resp.data['ahead_steps']}
        upcoming_ids = {s['id'] for s in resp.data['upcoming_steps']}
        assert str(next_day.id) in ahead_ids
        assert str(next_day.id) not in upcoming_ids
        assert str(far_step.id) in upcoming_ids
        assert resp.data['advance_completion_days'] == 1
