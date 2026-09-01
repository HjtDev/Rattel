from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APIClient

from automatic_class.models import AutomaticPlan, ExtraReviewRange, PlanStep

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='planedituser',
        name='Plan Edit User',
        phone='09100000060',
        password='testpass123',
    )


@pytest.fixture
def admin_user(db):
    # Superuser: bypasses per-teacher scoping, matching "admin can do everything".
    return User.objects.create_user(
        username='planeditadmin',
        name='Plan Edit Admin',
        phone='09100000061',
        password='testpass123',
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def admin_client(admin_user):
    client = APIClient()
    client.force_authenticate(user=admin_user)
    return client


def _make_plan(user, bypass_step_gen=True, **overrides):
    defaults = {
        'user': user,
        'start_page': 1,
        'end_page': 30,
        'start_date': date.today() + timedelta(days=1),
        'time_freq': AutomaticPlan.TimeFrequency.PER_DAY,
        'reading_freq': AutomaticPlan.ReadingFrequency.FULL_PAGE,
        'review_freq': 3,
        'user_day_availability': AutomaticPlan.DayAvailability.ODD_DAYS,
        'user_time_availability': AutomaticPlan.TimeAvailability.MORNING,
        'status': AutomaticPlan.Status.DRAFT,
    }
    defaults.update(overrides)
    plan = AutomaticPlan(**defaults)
    if bypass_step_gen:
        # Simulates an already-activated plan whose steps exist, without
        # actually running generation — mirrors the pattern used across the
        # automatic_class test suite.
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


def plan_detail_url(plan_id):
    return reverse('automatic:admin-plan-detail', args=[plan_id])


@pytest.mark.django_db
class TestPreStartPlanEditing:
    def test_draft_plan_is_editable(self, admin_client, user):
        plan = _make_plan(user, bypass_step_gen=False, status=AutomaticPlan.Status.DRAFT)

        resp = admin_client.patch(plan_detail_url(plan.id), {
            'start_page': 5, 'end_page': 50, 'review_freq': 2,
        }, format='json')

        assert resp.status_code == 200
        plan.refresh_from_db()
        assert plan.start_page == 5
        assert plan.end_page == 50
        assert plan.review_freq == 2

    def test_queued_plan_schedule_fields_are_editable(self, admin_client, user):
        parent = _make_plan(user, status=AutomaticPlan.Status.ACTIVE)
        _make_step(parent, 1, date.today())
        child = _make_plan(
            user, bypass_step_gen=False,
            status=AutomaticPlan.Status.QUEUED, parent_plan=parent,
            start_page=31, end_page=40, start_date=date.today() + timedelta(days=10),
        )

        new_start = date.today() + timedelta(days=15)
        resp = admin_client.patch(plan_detail_url(child.id), {
            'start_page': 100, 'end_page': 120, 'start_date': str(new_start),
            'review_freq': 5,
            'extra_review_ranges': [{'start_page': 1, 'end_page': 10, 'pages_per_session': 2}],
        }, format='json')

        assert resp.status_code == 200
        child.refresh_from_db()
        assert child.start_page == 100
        assert child.end_page == 120
        assert child.start_date == new_start
        assert child.review_freq == 5
        ranges = list(child.extra_review_ranges.all())
        assert len(ranges) == 1
        assert (ranges[0].start_page, ranges[0].end_page, ranges[0].pages_per_session) == (1, 10, 2)

    def test_edited_queued_plan_generates_steps_from_the_new_parameters(self, admin_client, user):
        """End-to-end proof that editing before activation is safe: the child's
        generated steps reflect the edited parameters, not the original ones."""
        parent = _make_plan(user, status=AutomaticPlan.Status.ACTIVE, start_date=date.today() - timedelta(days=1))
        step = _make_step(parent, 1, date.today())
        child = _make_plan(
            user, bypass_step_gen=False,
            status=AutomaticPlan.Status.QUEUED, parent_plan=parent,
            start_page=31, end_page=40, start_date=date.today() + timedelta(days=10),
        )

        edit_resp = admin_client.patch(plan_detail_url(child.id), {
            'start_page': 200, 'end_page': 202, 'review_freq': 1,
            'extra_review_ranges': [{'start_page': 500, 'end_page': 502, 'pages_per_session': 1}],
        }, format='json')
        assert edit_resp.status_code == 200

        # Replicate StepCompleteView's completion + auto-complete-parent logic
        # directly (it requires a student-side subscription we don't need to
        # set up here) so the chain-activation side effect fires for real.
        step.complete()
        if not parent.steps.exclude(
            status__in=[PlanStep.Status.COMPLETED, PlanStep.Status.SKIPPED]
        ).exists():
            parent.status = AutomaticPlan.Status.COMPLETED
            parent.save()

        child.refresh_from_db()
        assert child.status == AutomaticPlan.Status.ACTIVE
        memorize_pages = sorted(
            child.steps.filter(step_type=PlanStep.StepType.MEMORIZE).values_list('page_start', flat=True)
        )
        assert memorize_pages == [200, 201, 202]
        extra_pages = sorted(
            child.steps.filter(step_type=PlanStep.StepType.EXTRA_REVIEW).values_list('page_start', flat=True)
        )
        assert extra_pages and min(extra_pages) >= 500

    def test_draft_activation_patch_still_works(self, admin_client, user):
        plan = _make_plan(user, bypass_step_gen=False, status=AutomaticPlan.Status.DRAFT)

        resp = admin_client.patch(plan_detail_url(plan.id), {'status': 'active'}, format='json')

        assert resp.status_code == 200
        plan.refresh_from_db()
        assert plan.status == AutomaticPlan.Status.ACTIVE
        assert plan.steps.exists()

    def test_resending_unchanged_locked_field_is_accepted(self, admin_client, user):
        parent = _make_plan(user, status=AutomaticPlan.Status.ACTIVE)
        _make_step(parent, 1, date.today())
        child = _make_plan(
            user, bypass_step_gen=False,
            status=AutomaticPlan.Status.QUEUED, parent_plan=parent,
            start_page=31, end_page=40, start_date=date.today() + timedelta(days=10),
        )
        resp = admin_client.patch(plan_detail_url(child.id), {
            'start_page': child.start_page, 'end_page': child.end_page,
            'admin_notes': 'unchanged fields resubmitted',
        }, format='json')

        assert resp.status_code == 200
        child.refresh_from_db()
        assert child.admin_notes == 'unchanged fields resubmitted'


@pytest.mark.django_db
class TestPostGenerationPlanLocking:
    def test_active_plan_schedule_edit_is_refused(self, admin_client, user):
        plan = _make_plan(user, bypass_step_gen=True, status=AutomaticPlan.Status.ACTIVE)

        # start_page=5 stays well under the plan's end_page=30, so this only
        # exercises the post-generation lock — not the start<end ordering check.
        resp = admin_client.patch(plan_detail_url(plan.id), {'start_page': 5}, format='json')

        assert resp.status_code == 400
        assert 'start_page' in resp.data.get('errors', {})
        plan.refresh_from_db()
        assert plan.start_page != 5

    def test_active_plan_extra_review_ranges_edit_is_refused(self, admin_client, user):
        plan = _make_plan(user, bypass_step_gen=True, status=AutomaticPlan.Status.ACTIVE)
        ExtraReviewRange.objects.create(plan=plan, start_page=1, end_page=5, pages_per_session=1, order=0)

        resp = admin_client.patch(plan_detail_url(plan.id), {
            'extra_review_ranges': [{'start_page': 1, 'end_page': 5, 'pages_per_session': 2}],
        }, format='json')

        assert resp.status_code == 400
        assert 'extra_review_ranges' in resp.data.get('errors', {})

    def test_active_plan_non_schedule_fields_still_editable(self, admin_client, user):
        plan = _make_plan(user, bypass_step_gen=True, status=AutomaticPlan.Status.ACTIVE)

        resp = admin_client.patch(plan_detail_url(plan.id), {
            'admin_notes': 'called the student', 'advance_completion_days': 3,
        }, format='json')

        assert resp.status_code == 200
        plan.refresh_from_db()
        assert plan.admin_notes == 'called the student'
        assert plan.advance_completion_days == 3

    def test_active_plan_status_change_still_works(self, admin_client, user):
        plan = _make_plan(user, bypass_step_gen=True, status=AutomaticPlan.Status.ACTIVE)

        resp = admin_client.patch(plan_detail_url(plan.id), {'status': 'cancelled'}, format='json')

        assert resp.status_code == 200
        plan.refresh_from_db()
        assert plan.status == AutomaticPlan.Status.CANCELLED
