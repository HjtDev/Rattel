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
        username='chainuser',
        name='Chain User',
        phone='09100000030',
        password='testpass123',
    )


@pytest.fixture
def other_user(db):
    return User.objects.create_user(
        username='chainother',
        name='Chain Other',
        phone='09100000031',
        password='testpass123',
    )


@pytest.fixture
def admin_user(db):
    # Superuser: bypasses per-teacher scoping, matching "admin can do everything".
    return User.objects.create_user(
        username='chainadmin',
        name='Chain Admin',
        phone='09100000032',
        password='testpass123',
        is_staff=True,
        is_superuser=True,
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


def _make_plan(user, bypass_step_gen=True, **overrides):
    defaults = {
        'user': user,
        'start_page': 1,
        'end_page': 30,
        'start_date': date.today() - timedelta(days=5),
        'time_freq': AutomaticPlan.TimeFrequency.PER_DAY,
        'reading_freq': AutomaticPlan.ReadingFrequency.FULL_PAGE,
        'user_day_availability': AutomaticPlan.DayAvailability.ODD_DAYS,
        'user_time_availability': AutomaticPlan.TimeAvailability.MORNING,
        'status': AutomaticPlan.Status.ACTIVE,
    }
    defaults.update(overrides)
    plan = AutomaticPlan(**defaults)
    if bypass_step_gen:
        # Bypass the auto step-generation side effect on save(); the test builds
        # steps explicitly. Chained (queued) plans must NOT bypass this, since the
        # tests need real step generation to fire on activation.
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


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


def complete_url(step_id):
    return reverse('automatic:step-complete', args=[step_id])


def _chain_payload(parent, user, **overrides):
    payload = {
        'user': user.id,
        'parent_plan': str(parent.id),
        'start_page': 31,
        'end_page': 40,
        'start_date': str(date.today() + timedelta(days=10)),
        'time_freq': 'per_day',
        'reading_freq': 'full_page',
        'review_freq': 3,
        'user_day_availability': 'odd_days',
        'user_time_availability': 'morning',
        'status': 'queued',
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
class TestChainActivation:
    def test_completing_parent_activates_queued_child_and_generates_steps(self, api_client, user):
        parent = _make_plan(user, start_date=date.today() - timedelta(days=2))
        step = _make_step(parent, 1, date.today())
        child = _make_plan(
            user, bypass_step_gen=False,
            status=AutomaticPlan.Status.QUEUED, parent_plan=parent,
            start_page=31, end_page=40, start_date=date.today() + timedelta(days=10),
        )

        resp = api_client.post(complete_url(step.id))
        assert resp.status_code == 200

        parent.refresh_from_db()
        child.refresh_from_db()
        assert parent.status == AutomaticPlan.Status.COMPLETED
        assert child.status == AutomaticPlan.Status.ACTIVE
        assert child.steps.exists()

    def test_child_start_date_rebased_to_today_when_overdue(self, api_client, user):
        parent = _make_plan(user)
        step = _make_step(parent, 1, date.today())
        child = _make_plan(
            user, bypass_step_gen=False,
            status=AutomaticPlan.Status.QUEUED, parent_plan=parent,
            start_page=31, end_page=40, start_date=date.today() - timedelta(days=3),
        )

        api_client.post(complete_url(step.id))
        child.refresh_from_db()
        assert child.start_date == date.today()

    def test_child_future_start_date_preserved(self, api_client, user):
        parent = _make_plan(user)
        step = _make_step(parent, 1, date.today())
        future = date.today() + timedelta(days=5)
        child = _make_plan(
            user, bypass_step_gen=False,
            status=AutomaticPlan.Status.QUEUED, parent_plan=parent,
            start_page=31, end_page=40, start_date=future,
        )

        api_client.post(complete_url(step.id))
        child.refresh_from_db()
        assert child.start_date == future

    def test_generate_call_sessions_false_skips_call_sessions(self, api_client, user, subscription):
        parent = _make_plan(user)
        step = _make_step(parent, 1, date.today())
        child = _make_plan(
            user, bypass_step_gen=False,
            status=AutomaticPlan.Status.QUEUED, parent_plan=parent,
            start_page=31, end_page=40, start_date=date.today() + timedelta(days=10),
            generate_call_sessions=False,
        )

        api_client.post(complete_url(step.id))
        child.refresh_from_db()
        assert child.call_sessions.count() == 0

    def test_generate_call_sessions_true_creates_sessions(self, api_client, user, subscription):
        parent = _make_plan(user)
        step = _make_step(parent, 1, date.today())
        child = _make_plan(
            user, bypass_step_gen=False,
            status=AutomaticPlan.Status.QUEUED, parent_plan=parent,
            start_page=31, end_page=40, start_date=date.today() + timedelta(days=10),
            generate_call_sessions=True,
        )

        api_client.post(complete_url(step.id))
        child.refresh_from_db()
        assert child.call_sessions.count() > 0


@pytest.mark.django_db
class TestChainCascade:
    def test_cancelling_parent_cascades_to_queued_child(self, user):
        parent = _make_plan(user)
        child = _make_plan(
            user, bypass_step_gen=False,
            status=AutomaticPlan.Status.QUEUED, parent_plan=parent,
            start_page=31, end_page=40, start_date=date.today() + timedelta(days=10),
        )

        parent.status = AutomaticPlan.Status.CANCELLED
        parent.save()

        child.refresh_from_db()
        assert child.status == AutomaticPlan.Status.CANCELLED

    def test_deleting_parent_deletes_queued_child(self, user):
        parent = _make_plan(user)
        child = _make_plan(
            user, bypass_step_gen=False,
            status=AutomaticPlan.Status.QUEUED, parent_plan=parent,
            start_page=31, end_page=40, start_date=date.today() + timedelta(days=10),
        )
        child_id = child.id

        parent.delete()

        assert not AutomaticPlan.objects.filter(id=child_id).exists()


@pytest.mark.django_db
class TestChainValidation:
    def test_cannot_chain_to_another_users_plan(self, admin_client, user, other_user):
        parent = _make_plan(user)
        payload = _chain_payload(parent, other_user)

        resp = admin_client.post(reverse('automatic:admin-plans'), payload, format='json')
        assert resp.status_code == 400

    def test_cannot_chain_second_plan_while_one_queued(self, admin_client, user):
        parent = _make_plan(user)
        _make_plan(
            user, bypass_step_gen=False,
            status=AutomaticPlan.Status.QUEUED, parent_plan=parent,
            start_page=31, end_page=40, start_date=date.today() + timedelta(days=10),
        )
        payload = _chain_payload(parent, user, start_page=41, end_page=50)

        resp = admin_client.post(reverse('automatic:admin-plans'), payload, format='json')
        assert resp.status_code == 400

    def test_cannot_set_start_date_on_or_before_parent_last_step(self, admin_client, user):
        parent = _make_plan(user)
        last_step_date = date.today() + timedelta(days=3)
        _make_step(parent, 1, last_step_date)
        payload = _chain_payload(parent, user, start_date=str(last_step_date))

        resp = admin_client.post(reverse('automatic:admin-plans'), payload, format='json')
        assert resp.status_code == 400


@pytest.mark.django_db
class TestChainVisibility:
    def test_queued_plan_invisible_to_user_but_flagged_on_parent(self, api_client, user):
        parent = _make_plan(user)
        _make_step(parent, 1, date.today())
        _make_plan(
            user, bypass_step_gen=False,
            status=AutomaticPlan.Status.QUEUED, parent_plan=parent,
            start_page=31, end_page=40, start_date=date.today() + timedelta(days=10),
        )

        resp = api_client.get(reverse('automatic:my-plan'))
        assert resp.status_code == 200
        assert resp.data['plan']['id'] == str(parent.id)
        assert resp.data['plan']['has_chained_plan'] is True


@pytest.mark.django_db
class TestAdminPlanDelete:
    def test_delete_queued_plan_succeeds(self, admin_client, user):
        parent = _make_plan(user)
        child = _make_plan(
            user, bypass_step_gen=False,
            status=AutomaticPlan.Status.QUEUED, parent_plan=parent,
            start_page=31, end_page=40, start_date=date.today() + timedelta(days=10),
        )

        resp = admin_client.delete(reverse('automatic:admin-plan-detail', args=[child.id]))
        assert resp.status_code == 200
        assert not AutomaticPlan.objects.filter(id=child.id).exists()

    def test_delete_active_plan_refused(self, admin_client, user):
        parent = _make_plan(user)

        resp = admin_client.delete(reverse('automatic:admin-plan-detail', args=[parent.id]))
        assert resp.status_code == 400
        assert AutomaticPlan.objects.filter(id=parent.id).exists()


@pytest.mark.django_db
class TestClassRequestGuard:
    def test_refused_with_active_plan(self, api_client, user):
        _make_plan(user)

        resp = api_client.post(reverse('automatic:class-request'), {'notes': 'test'}, format='json')
        assert resp.status_code == 400

    def test_refused_with_queued_plan(self, api_client, user):
        _make_plan(user, bypass_step_gen=False, status=AutomaticPlan.Status.QUEUED)

        resp = api_client.post(reverse('automatic:class-request'), {'notes': 'test'}, format='json')
        assert resp.status_code == 400
