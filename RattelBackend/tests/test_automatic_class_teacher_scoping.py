from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.urls import reverse
from rest_framework.test import APIClient

from automatic_class.models import AutomaticPlan, ClassRequest, OnlineCallSession, PlanStep
from automatic_class.signals import sms_on_new_class_request

User = get_user_model()


@pytest.fixture(autouse=True)
def disable_class_request_sms_alert():
    """ClassRequest.save() fires a real SMS via the post_save signal (see
    automatic_class/signals.py); settings.py always points at the live
    Melipayamak provider with no test override, so leaving this connected
    sends a real, billed SMS every time this file's tests run."""
    post_save.disconnect(sms_on_new_class_request, sender=ClassRequest)
    yield
    post_save.connect(sms_on_new_class_request, sender=ClassRequest)


@pytest.fixture
def teacher_a(db):
    return User.objects.create_user(
        username='teachera',
        name='Teacher A',
        phone='09100000040',
        password='testpass123',
        is_staff=True,
    )


@pytest.fixture
def teacher_b(db):
    return User.objects.create_user(
        username='teacherb',
        name='Teacher B',
        phone='09100000041',
        password='testpass123',
        is_staff=True,
    )


@pytest.fixture
def superuser(db):
    return User.objects.create_user(
        username='scopingsuperuser',
        name='Superuser',
        phone='09100000042',
        password='testpass123',
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def role_teacher(db):
    """A user with profile.role == 'teacher' but is_staff=False."""
    from users.models import Profile

    user = User.objects.create_user(
        username='roleteacher',
        name='Role Teacher',
        phone='09100000043',
        password='testpass123',
    )
    # A Profile is auto-created via a post_save signal on User — update it
    # rather than creating a second one.
    user.profile.role = Profile.RoleChoices.TEACHER
    user.profile.save(update_fields=['role'])
    return user


@pytest.fixture
def student(db):
    return User.objects.create_user(
        username='scopingstudent',
        name='Scoping Student',
        phone='09100000044',
        password='testpass123',
    )


def client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def _make_plan(user, teacher, bypass_step_gen=True, **overrides):
    defaults = {
        'user': user,
        'teacher': teacher,
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


def _plan_payload(user, teacher_id_unused=None, **overrides):
    payload = {
        'user': user.id,
        'start_page': 1,
        'end_page': 10,
        'start_date': str(date.today() + timedelta(days=1)),
        'time_freq': 'per_day',
        'reading_freq': 'full_page',
        'review_freq': 3,
        'user_day_availability': 'odd_days',
        'user_time_availability': 'morning',
        'status': 'draft',
    }
    payload.update(overrides)
    return payload


@pytest.mark.django_db
class TestPlanListScoping:
    def test_teacher_only_sees_own_plans(self, teacher_a, teacher_b, student):
        mine = _make_plan(student, teacher_a)
        _make_plan(student, teacher_b)

        resp = client_for(teacher_a).get(reverse('automatic:admin-plans'))
        assert resp.status_code == 200
        ids = {p['id'] for p in resp.data['plans']}
        assert str(mine.id) in ids
        assert len(ids) == 1

    def test_superuser_sees_all_plans(self, teacher_a, teacher_b, superuser, student):
        _make_plan(student, teacher_a)
        _make_plan(student, teacher_b)

        resp = client_for(superuser).get(reverse('automatic:admin-plans'))
        assert resp.status_code == 200
        assert len(resp.data['plans']) == 2

    def test_role_teacher_without_is_staff_gets_scoped_access(self, role_teacher, teacher_b, student):
        mine = _make_plan(student, role_teacher)
        _make_plan(student, teacher_b)

        resp = client_for(role_teacher).get(reverse('automatic:admin-plans'))
        assert resp.status_code == 200
        ids = {p['id'] for p in resp.data['plans']}
        assert ids == {str(mine.id)}

    def test_plain_student_denied(self, student):
        resp = client_for(student).get(reverse('automatic:admin-plans'))
        assert resp.status_code == 403


@pytest.mark.django_db
class TestPlanDetailScoping:
    def test_other_teachers_plan_detail_is_404(self, teacher_a, teacher_b, student):
        plan = _make_plan(student, teacher_b)

        resp = client_for(teacher_a).get(reverse('automatic:admin-plan-detail', args=[plan.id]))
        assert resp.status_code == 404

    def test_owning_teacher_sees_detail(self, teacher_a, student):
        plan = _make_plan(student, teacher_a)

        resp = client_for(teacher_a).get(reverse('automatic:admin-plan-detail', args=[plan.id]))
        assert resp.status_code == 200

    def test_other_teacher_cannot_patch(self, teacher_a, teacher_b, student):
        plan = _make_plan(student, teacher_b)

        resp = client_for(teacher_a).patch(
            reverse('automatic:admin-plan-detail', args=[plan.id]),
            {'admin_notes': 'hijacked'}, format='json',
        )
        assert resp.status_code == 404
        plan.refresh_from_db()
        assert plan.admin_notes != 'hijacked'

    def test_other_teacher_cannot_delete(self, teacher_a, teacher_b, student):
        plan = _make_plan(student, teacher_b, status=AutomaticPlan.Status.QUEUED, bypass_step_gen=False)

        resp = client_for(teacher_a).delete(reverse('automatic:admin-plan-detail', args=[plan.id]))
        assert resp.status_code == 404
        assert AutomaticPlan.objects.filter(id=plan.id).exists()

    def test_superuser_can_patch_and_delete_any_plan(self, teacher_a, superuser, student):
        plan = _make_plan(student, teacher_a, status=AutomaticPlan.Status.QUEUED, bypass_step_gen=False)

        resp = client_for(superuser).patch(
            reverse('automatic:admin-plan-detail', args=[plan.id]),
            {'admin_notes': 'ok'}, format='json',
        )
        assert resp.status_code == 200

        resp = client_for(superuser).delete(reverse('automatic:admin-plan-detail', args=[plan.id]))
        assert resp.status_code == 200


@pytest.mark.django_db
class TestPlanCreationScoping:
    def test_creator_is_always_pinned_as_teacher(self, teacher_a, student):
        payload = _plan_payload(student)
        resp = client_for(teacher_a).post(reverse('automatic:admin-plans'), payload, format='json')
        assert resp.status_code == 201
        plan = AutomaticPlan.objects.get(id=resp.data['plan']['id'])
        assert plan.teacher_id == teacher_a.id

    def test_teacher_field_in_payload_is_ignored(self, teacher_a, teacher_b, student):
        payload = _plan_payload(student, teacher=teacher_b.id)
        resp = client_for(teacher_a).post(reverse('automatic:admin-plans'), payload, format='json')
        assert resp.status_code == 201
        plan = AutomaticPlan.objects.get(id=resp.data['plan']['id'])
        assert plan.teacher_id == teacher_a.id

    def test_chaining_onto_another_teachers_plan_is_rejected(self, teacher_a, teacher_b, student):
        parent = _make_plan(student, teacher_b)
        payload = _plan_payload(
            student, parent_plan=str(parent.id), status='queued',
            start_page=31, end_page=40,
        )
        resp = client_for(teacher_a).post(reverse('automatic:admin-plans'), payload, format='json')
        assert resp.status_code == 400

    def test_superuser_can_chain_across_teachers(self, teacher_b, superuser, student):
        parent = _make_plan(student, teacher_b)
        payload = _plan_payload(
            student, parent_plan=str(parent.id), status='queued',
            start_page=31, end_page=40,
        )
        resp = client_for(superuser).post(reverse('automatic:admin-plans'), payload, format='json')
        assert resp.status_code == 201

    def test_cannot_repoint_parent_plan_via_patch_to_another_teacher(self, teacher_a, teacher_b, student):
        own_parent = _make_plan(student, teacher_a, status=AutomaticPlan.Status.COMPLETED)
        other_parent = _make_plan(student, teacher_b, start_page=50, end_page=60)
        child = _make_plan(
            student, teacher_a, bypass_step_gen=False,
            status=AutomaticPlan.Status.QUEUED, parent_plan=own_parent,
            start_page=31, end_page=40, start_date=date.today() + timedelta(days=10),
        )

        resp = client_for(teacher_a).patch(
            reverse('automatic:admin-plan-detail', args=[child.id]),
            {'parent_plan': str(other_parent.id)}, format='json',
        )
        assert resp.status_code == 400


@pytest.mark.django_db
class TestStepCallLogCallSessionScoping:
    def test_step_update_404s_for_non_owning_teacher(self, teacher_a, teacher_b, student):
        plan = _make_plan(student, teacher_b)
        step = _make_step(plan, 1, date.today())

        resp = client_for(teacher_a).patch(
            reverse('automatic:admin-step-update', args=[step.id]),
            {'admin_note': 'nope'}, format='json',
        )
        assert resp.status_code == 404

    def test_step_update_succeeds_for_owning_teacher(self, teacher_a, student):
        plan = _make_plan(student, teacher_a)
        step = _make_step(plan, 1, date.today())

        resp = client_for(teacher_a).patch(
            reverse('automatic:admin-step-update', args=[step.id]),
            {'admin_note': 'ok'}, format='json',
        )
        assert resp.status_code == 200

    def test_call_log_rejected_for_non_owning_teacher(self, teacher_a, teacher_b, student):
        plan = _make_plan(student, teacher_b)

        resp = client_for(teacher_a).post(
            reverse('automatic:admin-call-log'),
            {'plan': str(plan.id), 'notes': 'sneaky'}, format='json',
        )
        assert resp.status_code == 404
        assert plan.call_logs.count() == 0

    def test_call_log_succeeds_for_owning_teacher(self, teacher_a, student):
        plan = _make_plan(student, teacher_a)

        resp = client_for(teacher_a).post(
            reverse('automatic:admin-call-log'),
            {'plan': str(plan.id), 'notes': 'good call'}, format='json',
        )
        assert resp.status_code == 201
        assert plan.call_logs.count() == 1

    def test_call_session_update_404s_for_non_owning_teacher(self, teacher_a, teacher_b, student):
        plan = _make_plan(student, teacher_b)
        session = OnlineCallSession.objects.create(plan=plan, session_number=1)

        resp = client_for(teacher_a).patch(
            reverse('automatic:admin-call-session-update', args=[session.id]),
            {'status': 'completed'}, format='json',
        )
        assert resp.status_code == 404

    def test_call_session_update_succeeds_for_owning_teacher(self, teacher_a, student):
        plan = _make_plan(student, teacher_a)
        session = OnlineCallSession.objects.create(plan=plan, session_number=1)

        resp = client_for(teacher_a).patch(
            reverse('automatic:admin-call-session-update', args=[session.id]),
            {'status': 'completed'}, format='json',
        )
        assert resp.status_code == 200


@pytest.mark.django_db
class TestRequestsStayShared:
    def test_both_teachers_see_the_same_requests(self, teacher_a, teacher_b, student):
        req = ClassRequest.objects.create(user=student, notes='hi')

        resp_a = client_for(teacher_a).get(reverse('automatic:admin-requests'))
        resp_b = client_for(teacher_b).get(reverse('automatic:admin-requests'))
        assert resp_a.status_code == 200
        assert resp_b.status_code == 200
        ids_a = {r['id'] for r in resp_a.data['requests']}
        ids_b = {r['id'] for r in resp_b.data['requests']}
        assert ids_a == ids_b == {str(req.id)}

    def test_either_teacher_can_update_a_request(self, teacher_a, teacher_b, student):
        req = ClassRequest.objects.create(user=student, notes='hi')

        resp = client_for(teacher_b).patch(
            reverse('automatic:admin-request-detail', args=[req.id]),
            {'status': 'contacted'}, format='json',
        )
        assert resp.status_code == 200


@pytest.mark.django_db
class TestPlanHistory:
    def test_admin_user_filter_returns_all_statuses_for_scoped_teacher(self, teacher_a, teacher_b, student):
        _make_plan(student, teacher_a, status=AutomaticPlan.Status.COMPLETED)
        _make_plan(student, teacher_a, status=AutomaticPlan.Status.CANCELLED, start_page=31, end_page=40)
        _make_plan(student, teacher_b, status=AutomaticPlan.Status.ACTIVE, start_page=61, end_page=70)

        resp = client_for(teacher_a).get(reverse('automatic:admin-plans'), {'user': student.id})
        assert resp.status_code == 200
        assert len(resp.data['plans']) == 2
        statuses = {p['status'] for p in resp.data['plans']}
        assert statuses == {'completed', 'cancelled'}

    def test_my_plan_history_returns_every_status_chronologically(self, student):
        from subscriptions.models import Plan, UserSubscription

        sub_plan = Plan.objects.create(name='Premium', description='d', price=1, online_class_limit=Plan.OnlineClassLimit.PREMIUM)
        UserSubscription.objects.create(user=student, plan=sub_plan, ends_in=date.today() + timedelta(days=30))

        first = _make_plan(student, None, status=AutomaticPlan.Status.COMPLETED)
        second = _make_plan(student, None, status=AutomaticPlan.Status.QUEUED, parent_plan=first, start_page=31, end_page=40, start_date=date.today() + timedelta(days=10))

        resp = client_for(student).get(reverse('automatic:my-plan-history'))
        assert resp.status_code == 200
        ids = [p['id'] for p in resp.data['plans']]
        assert ids == [str(first.id), str(second.id)]
        assert resp.data['plans'][1]['parent_plan'] == first.id
