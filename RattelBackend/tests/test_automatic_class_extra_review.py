from datetime import date, timedelta

import pytest
from django.contrib.auth import get_user_model

from automatic_class.models import AutomaticPlan, ExtraReviewRange, PlanStep

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(
        username='extrareviewuser',
        name='Extra Review User',
        phone='09100000050',
        password='testpass123',
    )


def _make_plan(user, **overrides):
    """
    Builds a plan with `status=draft` and saves it, then flips it to `active`
    on a second save — this is the real activation transition (`draft ->
    active`), so `_generate_steps()` runs for real against whatever
    ExtraReviewRange rows the test has already attached.
    """
    defaults = {
        'user': user,
        'start_page': 1,
        'end_page': 10,
        'start_date': date.today(),
        'time_freq': AutomaticPlan.TimeFrequency.PER_DAY,
        'reading_freq': AutomaticPlan.ReadingFrequency.FULL_PAGE,
        'review_freq': 1,
        'user_day_availability': AutomaticPlan.DayAvailability.ODD_DAYS,
        'user_time_availability': AutomaticPlan.TimeAvailability.MORNING,
    }
    defaults.update(overrides)
    status = defaults.pop('status', AutomaticPlan.Status.ACTIVE)
    plan = AutomaticPlan(status=AutomaticPlan.Status.DRAFT, **defaults)
    plan.save()
    if status == AutomaticPlan.Status.ACTIVE:
        plan.status = AutomaticPlan.Status.ACTIVE
        plan.save()
    return plan


def _add_range(plan, start_page, end_page, pages_per_session, order=0):
    return ExtraReviewRange.objects.create(
        plan=plan, start_page=start_page, end_page=end_page,
        pages_per_session=pages_per_session, order=order,
    )


def _steps_on(plan, day_offset):
    """All steps scheduled `day_offset` days after the plan's start_date, in step order."""
    target = plan.start_date + timedelta(days=day_offset)
    return list(plan.steps.filter(scheduled_date=target).order_by('step_number'))


def _extra_review_pages(steps):
    return [(s.page_start, s.page_end) for s in steps if s.step_type == PlanStep.StepType.EXTRA_REVIEW]


@pytest.mark.django_db
class TestParallelExtraReviewRanges:
    def test_multiple_ranges_advance_in_parallel_on_the_same_session(self, user):
        """
        The scenario from the feature request: a 1–10 page plan, 1 page/day,
        1 review page, with three independent extra-review ranges (100–110,
        200–210, 450–460) each at 1 page/session. On day 2 (the second
        memorize session) every range must contribute exactly one step, all
        sharing that session's date — not staggered across different days.
        """
        plan = AutomaticPlan(
            user=user, start_page=1, end_page=10,
            start_date=date.today(), time_freq=AutomaticPlan.TimeFrequency.PER_DAY,
            reading_freq=AutomaticPlan.ReadingFrequency.FULL_PAGE,
            review_freq=1,
            user_day_availability=AutomaticPlan.DayAvailability.ODD_DAYS,
            user_time_availability=AutomaticPlan.TimeAvailability.MORNING,
            status=AutomaticPlan.Status.DRAFT,
        )
        plan.save()
        _add_range(plan, 100, 110, 1, order=0)
        _add_range(plan, 200, 210, 1, order=1)
        _add_range(plan, 450, 460, 1, order=2)
        plan.status = AutomaticPlan.Status.ACTIVE
        plan.save()

        # Day 0 = page 1 (no review yet, extra ranges start at their first page)
        day0 = _steps_on(plan, 0)
        assert _extra_review_pages(day0) == [(100, 100), (200, 200), (450, 450)]

        # Day 1 = page 2: memorize 2, review 1, extra 101 / 201 / 451 — same session.
        day1 = _steps_on(plan, 1)
        types_and_pages = [(s.step_type, s.page_start, s.page_end) for s in day1]
        assert types_and_pages == [
            (PlanStep.StepType.MEMORIZE, 2, 2),
            (PlanStep.StepType.REVIEW, 1, 1),
            (PlanStep.StepType.EXTRA_REVIEW, 101, 101),
            (PlanStep.StepType.EXTRA_REVIEW, 201, 201),
            (PlanStep.StepType.EXTRA_REVIEW, 451, 451),
        ]
        # All five steps belong to the same scheduled session.
        assert len({s.scheduled_date for s in day1}) == 1
        # step_number is sequential within the session.
        numbers = [s.step_number for s in day1]
        assert numbers == sorted(numbers)
        assert numbers == list(range(numbers[0], numbers[0] + 5))

    def test_each_range_wraps_independently(self, user):
        """A short range wraps back to its own start while a longer range next
        to it keeps advancing — cursors must not be shared or reset together."""
        plan = _make_plan(user, start_page=1, end_page=12, review_freq=1, status=AutomaticPlan.Status.DRAFT)
        _add_range(plan, 100, 102, 1, order=0)   # 3-page range, wraps every 3 days
        _add_range(plan, 200, 210, 1, order=1)   # 11-page range, keeps advancing
        plan.status = AutomaticPlan.Status.ACTIVE
        plan.save()

        short_seen = [_extra_review_pages(_steps_on(plan, i))[0] for i in range(6)]
        long_seen = [_extra_review_pages(_steps_on(plan, i))[1] for i in range(6)]

        assert short_seen == [(100, 100), (101, 101), (102, 102), (100, 100), (101, 101), (102, 102)]
        assert long_seen == [(200, 200), (201, 201), (202, 202), (203, 203), (204, 204), (205, 205)]

    def test_pages_per_session_clamps_at_range_end_then_wraps(self, user):
        """A 6-page range at 4 pages/session yields a full 4-page chunk, then a
        clamped 2-page remainder, then wraps back to a full 4-page chunk."""
        plan = _make_plan(user, start_page=1, end_page=3, review_freq=1, status=AutomaticPlan.Status.DRAFT)
        _add_range(plan, 100, 105, 4, order=0)
        plan.status = AutomaticPlan.Status.ACTIVE
        plan.save()

        seen = [_extra_review_pages(_steps_on(plan, i))[0] for i in range(3)]
        assert seen == [(100, 103), (104, 105), (100, 103)]

    def test_no_ranges_generates_no_extra_review_steps(self, user):
        plan = _make_plan(user)
        assert plan.steps.filter(step_type=PlanStep.StepType.EXTRA_REVIEW).exists() is False

    def test_zero_pages_per_session_range_is_skipped(self, user):
        """A range with pages_per_session=0 (shouldn't normally be creatable via
        the serializer, but the model layer must not divide-by-zero or hang)."""
        plan = _make_plan(user, status=AutomaticPlan.Status.DRAFT)
        _add_range(plan, 100, 110, 0, order=0)
        plan.status = AutomaticPlan.Status.ACTIVE
        plan.save()
        assert plan.steps.filter(step_type=PlanStep.StepType.EXTRA_REVIEW).exists() is False

    def test_half_page_reading_advances_cursors_once_per_half(self, user):
        """Pins existing (intentional) behaviour: half-page mode creates two
        sessions per page, so an extra-review cursor advances twice per page."""
        plan = _make_plan(
            user, start_page=1, end_page=2, review_freq=1,
            reading_freq=AutomaticPlan.ReadingFrequency.HALF_PAGE,
            status=AutomaticPlan.Status.DRAFT,
        )
        _add_range(plan, 100, 110, 1, order=0)
        plan.status = AutomaticPlan.Status.ACTIVE
        plan.save()

        # 2 pages * 2 halves = 4 memorize sessions before the final review.
        memorize_sessions = plan.steps.filter(step_type=PlanStep.StepType.MEMORIZE).order_by('step_number')
        assert memorize_sessions.count() == 4

        extra_pages = [
            _extra_review_pages(_steps_on(plan, i))[0]
            for i in range(4)
        ]
        assert extra_pages == [(100, 100), (101, 101), (102, 102), (103, 103)]
