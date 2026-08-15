from django.utils import timezone
from rest_framework import serializers
from .models import AutomaticPlan, ClassRequest, PlanStep, AdminCallLog, OnlineCallSession


class ClassRequestSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    plan_is_cancelled = serializers.SerializerMethodField()
    plan_is_completed = serializers.SerializerMethodField()

    class Meta:
        model = ClassRequest
        fields = ('id', 'notes', 'status', 'status_display', 'plan_is_cancelled', 'plan_is_completed', 'created_at', 'updated_at')
        read_only_fields = ('id', 'status', 'status_display', 'plan_is_cancelled', 'plan_is_completed', 'created_at', 'updated_at')

    def get_plan_is_cancelled(self, obj):
        if obj.status != ClassRequest.Status.PLAN_CREATED:
            return False
        try:
            return obj.plan.status == AutomaticPlan.Status.CANCELLED
        except AutomaticPlan.DoesNotExist:
            return False

    def get_plan_is_completed(self, obj):
        if obj.status != ClassRequest.Status.PLAN_CREATED:
            return False
        try:
            return obj.plan.status == AutomaticPlan.Status.COMPLETED
        except AutomaticPlan.DoesNotExist:
            return False


class AdminClassRequestSerializer(serializers.ModelSerializer):
    """Full request serializer for admin use — includes admin_notes and user info."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    user_display = serializers.SerializerMethodField()

    class Meta:
        model = ClassRequest
        fields = (
            'id', 'user', 'user_display', 'notes', 'admin_notes',
            'status', 'status_display', 'created_at', 'updated_at',
        )
        read_only_fields = ('id', 'user', 'user_display', 'created_at', 'updated_at')

    def get_user_display(self, obj):
        u = obj.user
        return {
            'id': u.pk,
            'username': getattr(u, 'username', str(u)),
            'phone': getattr(u, 'phone', None),
        }


class PlanStepSerializer(serializers.ModelSerializer):
    step_type_display = serializers.CharField(source='get_step_type_display', read_only=True)
    sub_part_display = serializers.CharField(source='get_sub_part_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_overdue = serializers.SerializerMethodField()

    class Meta:
        model = PlanStep
        fields = (
            'id', 'step_number', 'scheduled_date',
            'step_type', 'step_type_display',
            'page_start', 'page_end',
            'sub_part', 'sub_part_display',
            'status', 'status_display',
            'is_delayed', 'original_scheduled_date',
            'completed_at', 'delay_reason', 'admin_note',
            'is_overdue',
        )
        read_only_fields = fields

    def get_is_overdue(self, obj):
        if obj.status in (PlanStep.Status.COMPLETED, PlanStep.Status.SKIPPED):
            return False
        if not obj.scheduled_date:
            return False
        return timezone.now().date() > obj.scheduled_date


class AutomaticPlanSerializer(serializers.ModelSerializer):
    """Read-only plan representation for the student dashboard."""
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    time_freq_display = serializers.CharField(source='get_time_freq_display', read_only=True)
    reading_freq_display = serializers.CharField(source='get_reading_freq_display', read_only=True)
    user_day_availability_display = serializers.CharField(
        source='get_user_day_availability_display', read_only=True
    )
    user_time_availability_display = serializers.CharField(
        source='get_user_time_availability_display', read_only=True
    )
    teacher_display = serializers.SerializerMethodField()
    total_steps = serializers.IntegerField(read_only=True)
    completed_steps = serializers.IntegerField(read_only=True)
    progress_percent = serializers.IntegerField(read_only=True)
    call_sessions = serializers.SerializerMethodField()
    has_chained_plan = serializers.SerializerMethodField()

    class Meta:
        model = AutomaticPlan
        fields = (
            'id', 'start_page', 'end_page', 'start_date', 'time_to_finish',
            'time_freq', 'time_freq_display',
            'reading_freq', 'reading_freq_display',
            'review_freq',
            'extra_review_start_page', 'extra_review_end_page', 'extra_review_pages_per_session',
            'advance_completion_days',
            'user_day_availability', 'user_day_availability_display',
            'user_time_availability', 'user_time_availability_display',
            'status', 'status_display',
            'teacher_display',
            'total_steps', 'completed_steps', 'progress_percent',
            'call_sessions', 'has_chained_plan',
            'created_at',
        )
        read_only_fields = fields

    def get_has_chained_plan(self, obj):
        return obj.chained_plans.filter(status=AutomaticPlan.Status.QUEUED).exists()

    def get_call_sessions(self, obj):
        sessions = obj.call_sessions.all()
        return [
            {
                'id': str(s.id),
                'session_number': s.session_number,
                'status': s.status,
                'status_display': s.get_status_display(),
                'completed_at': s.completed_at.isoformat() if s.completed_at else None,
                'notes': s.notes,
            }
            for s in sessions
        ]

    def get_teacher_display(self, obj):
        if not obj.teacher:
            return None
        u = obj.teacher
        return {
            'id': u.pk,
            'username': getattr(u, 'username', str(u)),
        }


class AdminPlanCreateSerializer(serializers.ModelSerializer):
    """Used by admins to create a plan for a user."""

    class Meta:
        model = AutomaticPlan
        fields = (
            'id', 'request', 'user', 'teacher', 'parent_plan', 'generate_call_sessions',
            'start_page', 'end_page', 'start_date', 'time_to_finish',
            'time_freq', 'reading_freq', 'review_freq',
            'extra_review_start_page', 'extra_review_end_page', 'extra_review_pages_per_session',
            'advance_completion_days',
            'user_day_availability', 'user_time_availability',
            'status', 'admin_notes',
        )
        read_only_fields = ('id',)

    def validate(self, attrs):
        start_page = attrs.get('start_page')
        end_page = attrs.get('end_page')

        if start_page and end_page and start_page >= end_page:
            raise serializers.ValidationError({'end_page': 'End page must be greater than start page.'})

        parent_plan = attrs.get('parent_plan')
        if parent_plan:
            user = attrs.get('user')
            start_date = attrs.get('start_date')
            if user and parent_plan.user_id != user.pk:
                raise serializers.ValidationError({'parent_plan': 'The chained plan must belong to the same user as the parent plan.'})
            if parent_plan.status != AutomaticPlan.Status.ACTIVE:
                raise serializers.ValidationError({'parent_plan': 'You can only chain a plan onto an active plan.'})
            if parent_plan.chained_plans.filter(status=AutomaticPlan.Status.QUEUED).exists():
                raise serializers.ValidationError({'parent_plan': 'This plan already has a queued chained plan.'})
            last_step_date = parent_plan.last_step_date
            if last_step_date and start_date and start_date <= last_step_date:
                raise serializers.ValidationError({'start_date': "The chained plan must start after the parent plan's last step."})
        return attrs


class AdminPlanUpdateSerializer(serializers.ModelSerializer):
    """Partial update serializer for admins — cannot change user once set."""

    class Meta:
        model = AutomaticPlan
        fields = (
            'teacher', 'parent_plan', 'generate_call_sessions',
            'start_page', 'end_page', 'start_date', 'time_to_finish',
            'time_freq', 'reading_freq', 'review_freq',
            'extra_review_start_page', 'extra_review_end_page', 'extra_review_pages_per_session',
            'advance_completion_days',
            'user_day_availability', 'user_time_availability',
            'status', 'admin_notes',
        )

    def validate(self, attrs):
        instance = self.instance
        start_page = attrs.get('start_page', instance.start_page if instance else None)
        end_page = attrs.get('end_page', instance.end_page if instance else None)
        start_date = attrs.get('start_date', instance.start_date if instance else None)

        if start_page and end_page and start_page >= end_page:
            raise serializers.ValidationError({'end_page': 'End page must be greater than start page.'})

        if instance and instance.status == AutomaticPlan.Status.QUEUED:
            new_status = attrs.get('status', instance.status)
            if new_status != instance.status and new_status != AutomaticPlan.Status.CANCELLED:
                raise serializers.ValidationError({'status': 'A queued plan can only be cancelled directly; it activates automatically when its parent plan completes.'})

        if instance and instance.parent_plan_id and 'start_date' in attrs:
            last_step_date = instance.parent_plan.last_step_date
            if last_step_date and start_date and start_date <= last_step_date:
                raise serializers.ValidationError({'start_date': "The chained plan must start after the parent plan's last step."})
        return attrs


class AdminPlanListSerializer(AutomaticPlanSerializer):
    """Lightweight plan serializer for the admin list view — adds user_display without nested steps."""
    user_display = serializers.SerializerMethodField()

    class Meta(AutomaticPlanSerializer.Meta):
        fields = AutomaticPlanSerializer.Meta.fields + ('user_display', 'admin_notes')
        read_only_fields = fields

    def get_user_display(self, obj):
        u = obj.user
        if not u:
            return None
        return {
            'id': u.pk,
            'username': getattr(u, 'username', str(u)),
            'phone': getattr(u, 'phone', None),
        }

    def get_call_sessions(self, obj):
        return []


class OnlineCallSessionSerializer(serializers.ModelSerializer):
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    marked_by_display = serializers.SerializerMethodField()

    class Meta:
        model = OnlineCallSession
        fields = (
            'id', 'session_number', 'status', 'status_display',
            'completed_at', 'notes', 'marked_by_display', 'created_at',
        )
        read_only_fields = fields

    def get_marked_by_display(self, obj):
        if not obj.marked_by:
            return None
        return getattr(obj.marked_by, 'username', str(obj.marked_by))


class AdminCallSessionUpdateSerializer(serializers.Serializer):
    status = serializers.ChoiceField(choices=OnlineCallSession.Status.choices)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=2000)


class AdminPlanDetailSerializer(AutomaticPlanSerializer):
    """Extended plan serializer for admin — includes all fields plus steps summary."""
    user_display = serializers.SerializerMethodField()
    steps = PlanStepSerializer(many=True, read_only=True)
    call_sessions = OnlineCallSessionSerializer(many=True, read_only=True)
    subscription_info = serializers.SerializerMethodField()
    last_step_date = serializers.ReadOnlyField()
    chained_plan = serializers.SerializerMethodField()

    class Meta(AutomaticPlanSerializer.Meta):
        fields = AutomaticPlanSerializer.Meta.fields + (
            'user_display', 'admin_notes', '_steps_generated', 'steps',
            'call_sessions', 'subscription_info', 'parent_plan',
            'generate_call_sessions', 'last_step_date', 'chained_plan',
        )
        read_only_fields = fields

    def get_user_display(self, obj):
        u = obj.user
        return {
            'id': u.pk,
            'username': getattr(u, 'username', str(u)),
            'phone': getattr(u, 'phone', None),
        }

    def get_chained_plan(self, obj):
        child = obj.chained_plans.filter(status=AutomaticPlan.Status.QUEUED).order_by('created_at').first()
        if not child:
            return None
        return {
            'id': str(child.id),
            'start_page': child.start_page,
            'end_page': child.end_page,
            'start_date': child.start_date,
            'status': child.status,
        }

    def get_subscription_info(self, obj):
        from subscriptions.models import UserSubscription
        from django.utils import timezone
        try:
            today = timezone.now().date()
            sub = (
                UserSubscription.objects
                .select_related('plan')
                .filter(user=obj.user)
                .order_by('-ends_in')
                .first()
            )
            if not sub:
                return None
            return {
                'plan_name': sub.plan.name,
                'online_class_limit': sub.plan.online_class_limit,
                'is_active': sub.is_active,
            }
        except Exception:
            return None


class StepCompleteSerializer(serializers.Serializer):
    delay_reason = serializers.CharField(required=False, allow_blank=True, max_length=1000)


class StepReportDelaySerializer(serializers.Serializer):
    delay_reason = serializers.CharField(max_length=1000)


class AdminCallLogSerializer(serializers.ModelSerializer):
    called_by_display = serializers.SerializerMethodField()

    class Meta:
        model = AdminCallLog
        fields = ('id', 'plan', 'called_by', 'called_by_display', 'notes', 'call_date', 'created_at')
        read_only_fields = ('id', 'called_by', 'called_by_display', 'created_at')

    def get_called_by_display(self, obj):
        if not obj.called_by:
            return None
        u = obj.called_by
        return getattr(u, 'username', str(u))
