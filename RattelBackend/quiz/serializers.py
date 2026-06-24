import random

from rest_framework import serializers

from .models import (
    AttemptAnswer,
    Category,
    MatchingPair,
    Question,
    QuestionOption,
    Quiz,
    QuizAccessRequirement,
    QuizAttempt,
)


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name', 'slug')
        read_only_fields = fields


class QuestionOptionSerializer(serializers.ModelSerializer):
    """Public serializer — never exposes is_correct."""

    class Meta:
        model = QuestionOption
        fields = ('id', 'text', 'order')
        read_only_fields = fields


class QuestionOptionAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuestionOption
        fields = ('id', 'text', 'is_correct', 'order')


class MatchingPairAdminSerializer(serializers.ModelSerializer):
    class Meta:
        model = MatchingPair
        fields = ('id', 'left_text', 'right_text', 'left_id', 'right_id', 'order')
        read_only_fields = fields


class QuestionSerializer(serializers.ModelSerializer):
    options = QuestionOptionSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()
    left_items = serializers.SerializerMethodField()
    right_items = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = (
            'id', 'type', 'text', 'image', 'order', 'score', 'time_to_answer',
            'options', 'left_items', 'right_items',
        )
        read_only_fields = fields

    def get_image(self, obj: Question):
        request = self.context.get('request', None)
        if obj.image and obj.image.name:
            url = obj.image.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_left_items(self, obj: Question):
        if obj.type != Question.Type.MATCHING:
            return []
        return [{'id': str(p.left_id), 'text': p.left_text} for p in obj.pairs.all()]

    def get_right_items(self, obj: Question):
        if obj.type != Question.Type.MATCHING:
            return []
        pairs = list(obj.pairs.all())
        random.shuffle(pairs)
        return [{'id': str(p.right_id), 'text': p.right_text} for p in pairs]


class QuestionAdminSerializer(serializers.ModelSerializer):
    options = QuestionOptionAdminSerializer(many=True, read_only=True)
    pairs = MatchingPairAdminSerializer(many=True, read_only=True)
    image = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = (
            'id', 'type', 'text', 'image', 'order', 'score', 'time_to_answer',
            'created_at', 'updated_at', 'options', 'pairs',
        )
        read_only_fields = fields

    def get_image(self, obj: Question):
        request = self.context.get('request', None)
        if obj.image and obj.image.name:
            url = obj.image.url
            return request.build_absolute_uri(url) if request else url
        return None


class AccessRequirementSerializer(serializers.ModelSerializer):
    required_quiz = serializers.SerializerMethodField()

    class Meta:
        model = QuizAccessRequirement
        fields = ('id', 'type', 'required_quiz', 'required_score')
        read_only_fields = fields

    def get_required_quiz(self, obj: QuizAccessRequirement):
        if obj.required_quiz:
            return {'id': str(obj.required_quiz.id), 'title': obj.required_quiz.title}
        return None


class QuizListSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    thumbnail = serializers.SerializerMethodField()
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    attempts_remaining = serializers.SerializerMethodField()
    access_met = serializers.SerializerMethodField()
    access_reason = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = (
            'id', 'title', 'thumbnail', 'categories', 'difficulty', 'difficulty_display',
            'is_active', 'start_date', 'end_date', 'created_at',
            'attempts_remaining', 'access_met', 'access_reason',
        )
        read_only_fields = fields

    def get_thumbnail(self, obj: Quiz):
        request = self.context.get('request', None)
        if obj.thumbnail and obj.thumbnail.name:
            url = obj.thumbnail.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_attempts_remaining(self, obj: Quiz):
        if obj.max_attempts_per_user == 0:
            return None
        user = self.context.get('user', None)
        if not user or not user.is_authenticated:
            return obj.max_attempts_per_user
        statuses = [QuizAttempt.Status.COMPLETED]
        if not obj.allow_retry_on_expiry:
            statuses.append(QuizAttempt.Status.EXPIRED)
        used = QuizAttempt.objects.filter(
            user=user, quiz=obj, status__in=statuses
        ).count()
        return max(0, obj.max_attempts_per_user - used)

    def get_access_met(self, obj: Quiz):
        user = self.context.get('user', None)
        from .utils import _check_access
        if not user or not user.is_authenticated:
            has_non_free = obj.access_requirements.exclude(
                type=QuizAccessRequirement.Type.FREE
            ).exists()
            return not has_non_free
        access_met, _ = _check_access(obj, user)
        return access_met

    def get_access_reason(self, obj: Quiz):
        user = self.context.get('user', None)
        from .utils import _check_access
        if not user or not user.is_authenticated:
            return ''
        _, reason = _check_access(obj, user)
        return reason


class QuizDetailSerializer(QuizListSerializer):
    access_requirements = AccessRequirementSerializer(many=True, read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta(QuizListSerializer.Meta):
        fields = QuizListSerializer.Meta.fields + (
            'description', 'randomize_question_order', 'max_attempts_per_user',
            'reveal_answers_during_quiz', 'allow_retry_on_expiry', 'access_requirements', 'question_count',
        )
        read_only_fields = fields

    def get_question_count(self, obj: Quiz):
        return obj.questions.count()


class QuizAdminSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    thumbnail = serializers.SerializerMethodField()
    questions = QuestionAdminSerializer(many=True, read_only=True)
    access_requirements = AccessRequirementSerializer(many=True, read_only=True)
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = (
            'id', 'title', 'description', 'thumbnail', 'categories', 'difficulty',
            'difficulty_display', 'is_active', 'randomize_question_order',
            'max_attempts_per_user', 'reveal_answers_during_quiz', 'allow_retry_on_expiry',
            'start_date', 'end_date', 'created_at', 'updated_at', 'questions',
            'access_requirements', 'question_count',
        )
        read_only_fields = fields

    def get_thumbnail(self, obj: Quiz):
        request = self.context.get('request', None)
        if obj.thumbnail and obj.thumbnail.name:
            url = obj.thumbnail.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_question_count(self, obj: Quiz):
        return obj.questions.count()


class QuizAdminListSerializer(serializers.ModelSerializer):
    categories = CategorySerializer(many=True, read_only=True)
    thumbnail = serializers.SerializerMethodField()
    difficulty_display = serializers.CharField(source='get_difficulty_display', read_only=True)
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = (
            'id', 'title', 'thumbnail', 'categories', 'difficulty', 'difficulty_display',
            'is_active', 'start_date', 'end_date', 'created_at', 'updated_at',
            'question_count',
        )
        read_only_fields = fields

    def get_thumbnail(self, obj: Quiz):
        request = self.context.get('request', None)
        if obj.thumbnail and obj.thumbnail.name:
            url = obj.thumbnail.url
            return request.build_absolute_uri(url) if request else url
        return None

    def get_question_count(self, obj: Quiz):
        return obj.questions.count()


class QuizAttemptSerializer(serializers.ModelSerializer):
    quiz = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = QuizAttempt
        fields = (
            'id', 'quiz', 'started_at', 'finished_at', 'score',
            'correct_count', 'incorrect_count', 'time_spent',
            'status', 'status_display', 'created_at',
        )
        read_only_fields = fields

    def get_quiz(self, obj: QuizAttempt):
        return {'id': str(obj.quiz.id), 'title': obj.quiz.title}


class AttemptAnswerResultSerializer(serializers.ModelSerializer):
    question_id = serializers.UUIDField(source='question.id', read_only=True)
    selected_option_id = serializers.SerializerMethodField()
    correct_option_id = serializers.SerializerMethodField()
    correct_pairs = serializers.SerializerMethodField()

    class Meta:
        model = AttemptAnswer
        fields = (
            'question_id', 'selected_option_id', 'correct_option_id',
            'is_correct', 'matching_answer', 'correct_pairs',
        )
        read_only_fields = fields

    def get_selected_option_id(self, obj: AttemptAnswer):
        return str(obj.selected_option.id) if obj.selected_option else None

    def get_correct_option_id(self, obj: AttemptAnswer):
        if obj.question.type == Question.Type.MATCHING:
            return None
        correct = obj.question.options.filter(is_correct=True).first()
        return str(correct.id) if correct else None

    def get_correct_pairs(self, obj: AttemptAnswer):
        if obj.question.type != Question.Type.MATCHING:
            return None
        return [
            {
                'left_id': str(p.left_id),
                'right_id': str(p.right_id),
                'left_text': p.left_text,
                'right_text': p.right_text,
            }
            for p in obj.question.pairs.all()
        ]
