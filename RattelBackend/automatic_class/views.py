import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView

from RattelBackend.mixins import ResponseBuilderMixin
from .models import AutomaticPlan, ClassRequest, PlanStep, AdminCallLog
from .permissions import HasAutomaticClassAccess
from .serializers import (
    AdminCallLogSerializer,
    AdminClassRequestSerializer,
    AdminPlanCreateSerializer,
    AdminPlanDetailSerializer,
    AdminPlanUpdateSerializer,
    AutomaticPlanSerializer,
    ClassRequestSerializer,
    PlanStepSerializer,
    StepCompleteSerializer,
    StepReportDelaySerializer,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# User-facing views
# ---------------------------------------------------------------------------

class ClassRequestView(APIView, ResponseBuilderMixin):
    """
    GET  — Returns the authenticated user's latest class request.
    POST — Submits a new class request (one active request per user).

    Permissions: IsAuthenticated
    """

    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'

    def get(self, request):
        try:
            req = ClassRequest.objects.filter(user=request.user).order_by('-created_at').first()
            if not req:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    success=False, error=-1, message='No class request found.',
                )
            return self.build_response(
                status.HTTP_200_OK,
                success=True, message='Successful',
                request=ClassRequestSerializer(req).data,
            )
        except Exception as e:
            logger.error(f'ClassRequestView.get failed: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False, error=-2, message='Something went wrong.',
            )

    def post(self, request):
        try:
            pending = ClassRequest.objects.filter(
                user=request.user,
                status__in=[ClassRequest.Status.PENDING, ClassRequest.Status.CONTACTED],
            ).exists()
            if pending:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    success=False, error=-1,
                    message='You already have a pending class request.',
                )

            serializer = ClassRequestSerializer(data=request.data)
            if not serializer.is_valid():
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    success=False, error=-2,
                    message='Invalid data.', errors=serializer.errors,
                )

            class_request = serializer.save(user=request.user)
            return self.build_response(
                status.HTTP_201_CREATED,
                success=True,
                message='Class request submitted. Our team will contact you shortly.',
                request=ClassRequestSerializer(class_request).data,
            )
        except Exception as e:
            logger.error(f'ClassRequestView.post failed: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False, error=-3, message='Something went wrong.',
            )


class MyPlanView(APIView, ResponseBuilderMixin):
    """
    Returns the authenticated user's active automatic plan (without step list).

    Permissions: IsAuthenticated + HasAutomaticClassAccess
    """

    permission_classes = (IsAuthenticated, HasAutomaticClassAccess)
    throttle_scope = 'main-throttle'

    def get(self, request):
        try:
            plan = AutomaticPlan.objects.filter(
                user=request.user, status=AutomaticPlan.Status.ACTIVE
            ).first()
            if not plan:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    success=False, error=-1,
                    message='No active automatic plan found.',
                )
            return self.build_response(
                status.HTTP_200_OK,
                success=True, message='Successful',
                plan=AutomaticPlanSerializer(plan).data,
            )
        except Exception as e:
            logger.error(f'MyPlanView.get failed: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False, error=-2, message='Something went wrong.',
            )


class TodayStepsView(APIView, ResponseBuilderMixin):
    """
    Returns the user's tasks for today along with any delayed tasks from previous days.

    Response:
        delayed_steps   — past-due steps not yet completed
        today_steps     — steps scheduled for today
        upcoming_steps  — next 3 upcoming steps (preview)
        has_delayed     — convenience boolean

    Permissions: IsAuthenticated + HasAutomaticClassAccess
    """

    permission_classes = (IsAuthenticated, HasAutomaticClassAccess)
    throttle_scope = 'main-throttle'

    def get(self, request):
        try:
            plan = AutomaticPlan.objects.filter(
                user=request.user, status=AutomaticPlan.Status.ACTIVE
            ).first()
            if not plan:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    success=False, error=-1,
                    message='No active automatic plan found.',
                )

            today = timezone.now().date()

            delayed = PlanStep.objects.filter(
                plan=plan,
                status__in=[PlanStep.Status.DELAYED, PlanStep.Status.PENDING],
                scheduled_date__lt=today,
            ).order_by('scheduled_date', 'step_number')

            today_steps = PlanStep.objects.filter(
                plan=plan, scheduled_date=today,
            ).exclude(
                status__in=[PlanStep.Status.COMPLETED, PlanStep.Status.SKIPPED]
            ).order_by('step_number')

            upcoming = PlanStep.objects.filter(
                plan=plan,
                status=PlanStep.Status.PENDING,
                scheduled_date__gt=today,
            ).order_by('scheduled_date', 'step_number')[:3]

            return self.build_response(
                status.HTTP_200_OK,
                success=True, message='Successful',
                has_delayed=delayed.exists(),
                delayed_steps=PlanStepSerializer(delayed, many=True).data,
                today_steps=PlanStepSerializer(today_steps, many=True).data,
                upcoming_steps=PlanStepSerializer(upcoming, many=True).data,
            )
        except Exception as e:
            logger.error(f'TodayStepsView.get failed: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False, error=-2, message='Something went wrong.',
            )


class StepCompleteView(APIView, ResponseBuilderMixin):
    """
    POST — Mark a step as completed. Accepts an optional delay_reason if completing late.

    Permissions: IsAuthenticated + HasAutomaticClassAccess
    """

    permission_classes = (IsAuthenticated, HasAutomaticClassAccess)
    throttle_scope = 'main-throttle'

    def post(self, request, step_id):
        try:
            step = PlanStep.objects.select_related('plan').get(
                id=step_id, plan__user=request.user
            )
        except PlanStep.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False, error=-1, message='Step not found.',
            )

        if step.status == PlanStep.Status.COMPLETED:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False, error=-2, message='This step is already completed.',
            )
        if step.status == PlanStep.Status.SKIPPED:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False, error=-3, message='This step has been skipped.',
            )
        if step.plan.status != AutomaticPlan.Status.ACTIVE:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False, error=-4, message='The associated plan is not active.',
            )

        serializer = StepCompleteSerializer(data=request.data)
        if not serializer.is_valid():
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False, error=-5,
                message='Invalid data.', errors=serializer.errors,
            )

        step.complete(delay_reason=serializer.validated_data.get('delay_reason', ''))

        # Auto-complete the plan when no steps remain open
        plan = step.plan
        remaining = plan.steps.exclude(
            status__in=[PlanStep.Status.COMPLETED, PlanStep.Status.SKIPPED]
        ).count()
        if remaining == 0:
            plan.status = AutomaticPlan.Status.COMPLETED
            plan.save(update_fields=['status', 'updated_at'])

        return self.build_response(
            status.HTTP_200_OK,
            success=True, message='Step marked as completed.',
            step=PlanStepSerializer(step).data,
        )


class StepReportDelayView(APIView, ResponseBuilderMixin):
    """
    POST — Report why a step was not completed without marking it complete.

    Permissions: IsAuthenticated + HasAutomaticClassAccess
    """

    permission_classes = (IsAuthenticated, HasAutomaticClassAccess)
    throttle_scope = 'main-throttle'

    def post(self, request, step_id):
        try:
            step = PlanStep.objects.select_related('plan').get(
                id=step_id, plan__user=request.user
            )
        except PlanStep.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False, error=-1, message='Step not found.',
            )

        if step.status not in (PlanStep.Status.PENDING, PlanStep.Status.DELAYED):
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False, error=-2,
                message='Only pending or delayed steps can have a reason reported.',
            )

        serializer = StepReportDelaySerializer(data=request.data)
        if not serializer.is_valid():
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False, error=-3,
                message='Invalid data.', errors=serializer.errors,
            )

        step.delay_reason = serializer.validated_data['delay_reason']
        step.status = PlanStep.Status.DELAYED
        step.is_delayed = True
        if not step.original_scheduled_date and step.scheduled_date:
            step.original_scheduled_date = step.scheduled_date
        step.save(update_fields=['delay_reason', 'status', 'is_delayed', 'original_scheduled_date'])

        return self.build_response(
            status.HTTP_200_OK,
            success=True, message='Delay reason recorded.',
            step=PlanStepSerializer(step).data,
        )


class MyProgressView(APIView, ResponseBuilderMixin):
    """
    Returns the user's full plan progress with all steps and stats.

    Permissions: IsAuthenticated + HasAutomaticClassAccess
    """

    permission_classes = (IsAuthenticated, HasAutomaticClassAccess)
    throttle_scope = 'main-throttle'

    def get(self, request):
        try:
            plan = AutomaticPlan.objects.filter(
                user=request.user,
                status__in=[AutomaticPlan.Status.ACTIVE, AutomaticPlan.Status.COMPLETED],
            ).prefetch_related('steps').first()

            if not plan:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    success=False, error=-1, message='No plan found.',
                )

            steps = plan.steps.all().order_by('step_number')
            today = timezone.now().date()

            stats = {
                'total': steps.count(),
                'completed': steps.filter(status=PlanStep.Status.COMPLETED).count(),
                'delayed': steps.filter(status=PlanStep.Status.DELAYED).count(),
                'pending': steps.filter(status=PlanStep.Status.PENDING).count(),
                'skipped': steps.filter(status=PlanStep.Status.SKIPPED).count(),
                'progress_percent': plan.progress_percent,
                'delayed_completions': steps.filter(
                    status=PlanStep.Status.COMPLETED, is_delayed=True
                ).count(),
            }

            return self.build_response(
                status.HTTP_200_OK,
                success=True, message='Successful',
                plan=AutomaticPlanSerializer(plan).data,
                steps=PlanStepSerializer(steps, many=True).data,
                stats=stats,
                today=str(today),
            )
        except Exception as e:
            logger.error(f'MyProgressView.get failed: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False, error=-2, message='Something went wrong.',
            )


# ---------------------------------------------------------------------------
# Admin views
# ---------------------------------------------------------------------------

class AdminClassRequestListView(APIView, ResponseBuilderMixin):
    """
    GET — List all class requests. Filter by ?status=pending|contacted|plan_created|rejected.

    Permissions: IsAdminUser
    """

    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    def get(self, request):
        try:
            qs = ClassRequest.objects.select_related('user').order_by('-created_at')
            filter_status = request.query_params.get('status')
            if filter_status:
                qs = qs.filter(status=filter_status)

            serializer = AdminClassRequestSerializer(qs, many=True)
            return self.build_response(
                status.HTTP_200_OK,
                success=True, message='Successful',
                requests=serializer.data,
                total=qs.count(),
            )
        except Exception as e:
            logger.error(f'AdminClassRequestListView.get failed: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False, error=-1, message='Something went wrong.',
            )


class AdminClassRequestDetailView(APIView, ResponseBuilderMixin):
    """
    GET   — Retrieve a single class request.
    PATCH — Update status / admin_notes.

    Permissions: IsAdminUser
    """

    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    def _get_object(self, request_id):
        try:
            return ClassRequest.objects.select_related('user').get(id=request_id)
        except ClassRequest.DoesNotExist:
            return None

    def get(self, request, request_id):
        obj = self._get_object(request_id)
        if not obj:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False, error=-1, message='Request not found.',
            )
        return self.build_response(
            status.HTTP_200_OK,
            success=True, message='Successful',
            request=AdminClassRequestSerializer(obj).data,
        )

    def patch(self, request, request_id):
        obj = self._get_object(request_id)
        if not obj:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False, error=-1, message='Request not found.',
            )

        serializer = AdminClassRequestSerializer(obj, data=request.data, partial=True)
        if not serializer.is_valid():
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False, error=-2,
                message='Invalid data.', errors=serializer.errors,
            )
        serializer.save()
        return self.build_response(
            status.HTTP_200_OK,
            success=True, message='Request updated.',
            request=serializer.data,
        )


class AdminPlanListView(APIView, ResponseBuilderMixin):
    """
    GET  — List all plans. Filter by ?status= or ?user=<user_id>.
    POST — Create a new plan for a user.

    Permissions: IsAdminUser
    """

    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    def get(self, request):
        try:
            qs = (
                AutomaticPlan.objects
                .select_related('user', 'teacher')
                .order_by('-created_at')
            )
            if request.query_params.get('status'):
                qs = qs.filter(status=request.query_params['status'])
            if request.query_params.get('user'):
                qs = qs.filter(user_id=request.query_params['user'])

            return self.build_response(
                status.HTTP_200_OK,
                success=True, message='Successful',
                plans=AutomaticPlanSerializer(qs, many=True).data,
                total=qs.count(),
            )
        except Exception as e:
            logger.error(f'AdminPlanListView.get failed: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False, error=-1, message='Something went wrong.',
            )

    def post(self, request):
        try:
            serializer = AdminPlanCreateSerializer(data=request.data)
            if not serializer.is_valid():
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    success=False, error=-2,
                    message='Invalid data.', errors=serializer.errors,
                )
            plan = serializer.save()

            # Sync the linked request status
            if plan.request:
                plan.request.status = ClassRequest.Status.PLAN_CREATED
                plan.request.save(update_fields=['status', 'updated_at'])

            return self.build_response(
                status.HTTP_201_CREATED,
                success=True, message='Plan created.',
                plan=AdminPlanDetailSerializer(plan).data,
            )
        except Exception as e:
            logger.error(f'AdminPlanListView.post failed: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False, error=-3, message='Something went wrong.',
            )


class AdminPlanDetailView(APIView, ResponseBuilderMixin):
    """
    GET   — Full plan detail with all steps and call logs.
    PATCH — Update plan fields. Changing schedule fields does NOT regenerate steps automatically
            (delete the plan and recreate it if a full regeneration is needed).

    Permissions: IsAdminUser
    """

    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    def _get_plan(self, plan_id):
        try:
            return (
                AutomaticPlan.objects
                .prefetch_related('steps', 'call_logs__called_by')
                .select_related('user', 'teacher', 'request')
                .get(id=plan_id)
            )
        except AutomaticPlan.DoesNotExist:
            return None

    def get(self, request, plan_id):
        plan = self._get_plan(plan_id)
        if not plan:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False, error=-1, message='Plan not found.',
            )
        return self.build_response(
            status.HTTP_200_OK,
            success=True, message='Successful',
            plan=AdminPlanDetailSerializer(plan).data,
            call_logs=AdminCallLogSerializer(plan.call_logs.all(), many=True).data,
        )

    def patch(self, request, plan_id):
        plan = self._get_plan(plan_id)
        if not plan:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False, error=-1, message='Plan not found.',
            )

        serializer = AdminPlanUpdateSerializer(plan, data=request.data, partial=True)
        if not serializer.is_valid():
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False, error=-2,
                message='Invalid data.', errors=serializer.errors,
            )
        updated = serializer.save()
        return self.build_response(
            status.HTTP_200_OK,
            success=True, message='Plan updated.',
            plan=AdminPlanDetailSerializer(updated).data,
        )


class AdminStepUpdateView(APIView, ResponseBuilderMixin):
    """
    PATCH — Admin override for a single step: update status, admin_note, or scheduled_date.

    Permissions: IsAdminUser
    """

    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    ALLOWED_FIELDS = {'status', 'admin_note', 'scheduled_date'}

    def patch(self, request, step_id):
        try:
            step = PlanStep.objects.select_related('plan').get(id=step_id)
        except PlanStep.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False, error=-1, message='Step not found.',
            )

        payload = {k: v for k, v in request.data.items() if k in self.ALLOWED_FIELDS}
        if not payload:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False, error=-2,
                message=f'Provide at least one of: {", ".join(self.ALLOWED_FIELDS)}.',
            )

        for field, value in payload.items():
            setattr(step, field, value)
        step.save(update_fields=list(payload.keys()))

        return self.build_response(
            status.HTTP_200_OK,
            success=True, message='Step updated.',
            step=PlanStepSerializer(step).data,
        )


class AdminCallLogCreateView(APIView, ResponseBuilderMixin):
    """
    POST — Log an admin/teacher call against a plan.

    Permissions: IsAdminUser
    """

    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    def post(self, request):
        try:
            serializer = AdminCallLogSerializer(data=request.data)
            if not serializer.is_valid():
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    success=False, error=-1,
                    message='Invalid data.', errors=serializer.errors,
                )
            log = serializer.save(called_by=request.user)
            return self.build_response(
                status.HTTP_201_CREATED,
                success=True, message='Call logged.',
                log=AdminCallLogSerializer(log).data,
            )
        except Exception as e:
            logger.error(f'AdminCallLogCreateView.post failed: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False, error=-2, message='Something went wrong.',
            )
