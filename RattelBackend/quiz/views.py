import json
import logging
import random

from django.core.cache import cache
from django.core.paginator import EmptyPage, Paginator
from django.shortcuts import get_object_or_404
from django.db import models, transaction
from django.db.models import Q, Sum
from django.utils import timezone
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.views import APIView

from RattelBackend.cache import drf_cached_response
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin

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
from .serializers import (
    AccessRequirementSerializer,
    AttemptAnswerResultSerializer,
    CategorySerializer,
    QuestionAdminSerializer,
    QuizAdminListSerializer,
    QuizAdminSerializer,
    QuizAttemptSerializer,
    QuizDetailSerializer,
    QuizListSerializer,
)
from .utils import _check_access

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 9
ATTEMPT_CACHE_KEY = 'quiz_attempt_{attempt_id}'
MAX_THUMBNAIL_SIZE = 5 * 1024 * 1024  # 5 MB
MAX_IMAGE_SIZE = 5 * 1024 * 1024  # 5 MB
ALLOWED_THUMBNAIL_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}
ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/webp', 'image/gif'}


def _parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    return str(value).lower() in ('true', '1', 'yes')


# ---------------------------------------------------------------------------
# Admin views
# ---------------------------------------------------------------------------

class AdminCategoryListView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            categories=serializer.data,
        )

    def post(self, request):
        success, result = self.get_data(request, 'name', 'slug')
        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1, message=result
            )
        name = result['name']
        slug = result['slug']
        if not self.validate_string_secure(name, sql=True, lookup=True, injection=True):
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message={'name': 'Invalid parameter.'},
            )
        if Category.objects.filter(slug=slug).exists():
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message={'slug': 'این اسلاگ قبلاً استفاده شده است.'},
            )
        category = Category.objects.create(name=name, slug=slug)
        serializer = CategorySerializer(category)
        return self.build_response(
            status.HTTP_201_CREATED, success=True, message='Successful',
            category=serializer.data,
        )


class AdminQuizListCreateView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    def _validate_page(self, value: str) -> bool:
        return value.isdigit() and int(value) >= 1

    def get(self, request):
        page = int(request.query_params.get('page', 1))
        count = int(request.query_params.get('count', DEFAULT_PAGE_SIZE))
        try:
            qs = Quiz.objects.prefetch_related('categories').order_by('-created_at')
            paginator = Paginator(qs, count)
            page_obj = paginator.page(page)
        except EmptyPage:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='Empty Page.'
            )
        except Exception as e:
            logger.error(f'AdminQuizListCreateView.get failed: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR, success=False, error=-2,
                message='Something went wrong.',
            )
        serializer = QuizAdminListSerializer(
            list(page_obj.object_list), many=True, context={'request': request}
        )
        return self.build_response(
            status.HTTP_200_OK, success=True, message='Successful',
            quizzes=serializer.data,
            total=paginator.count,
            page=page,
            total_pages=paginator.num_pages,
        )

    def post(self, request):
        success, result = self.get_data(request, 'title')
        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1, message=result
            )

        title = result['title']
        if not self.validate_string_secure(title, sql=True, lookup=True, injection=True):
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message={'title': 'Invalid parameter.'},
            )

        difficulty = request.data.get('difficulty', Quiz.Difficulty.MEDIUM)
        if difficulty not in [c[0] for c in Quiz.Difficulty.choices]:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message={'difficulty': 'مقدار سختی نامعتبر است.'},
            )

        thumbnail = request.FILES.get('thumbnail')
        if thumbnail:
            if thumbnail.size > MAX_THUMBNAIL_SIZE:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'thumbnail': 'حجم تصویر نباید بیشتر از ۵ مگابایت باشد.'},
                )
            if thumbnail.content_type not in ALLOWED_THUMBNAIL_TYPES:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'thumbnail': 'فرمت تصویر معتبر نیست.'},
                )

        quiz = Quiz(
            title=title,
            description=request.data.get('description', ''),
            difficulty=difficulty,
            is_active=_parse_bool(request.data.get('is_active', True)),
            randomize_question_order=_parse_bool(request.data.get('randomize_question_order', False)),
            max_attempts_per_user=int(request.data.get('max_attempts_per_user', 0)),
            reveal_answers_during_quiz=_parse_bool(request.data.get('reveal_answers_during_quiz', False)),
            allow_retry_on_expiry=_parse_bool(request.data.get('allow_retry_on_expiry', True)),
            start_date=request.data.get('start_date') or None,
            end_date=request.data.get('end_date') or None,
        )
        if thumbnail:
            quiz.thumbnail = thumbnail
        quiz.save()

        raw_cats = request.data.get('categories', [])
        category_ids = raw_cats if isinstance(raw_cats, list) else request.data.getlist('categories', [])
        if category_ids:
            quiz.categories.set(Category.objects.filter(pk__in=category_ids))

        serializer = QuizAdminSerializer(quiz, context={'request': request})
        return self.build_response(
            status.HTTP_201_CREATED, success=True, message='Successful', quiz=serializer.data
        )


class AdminQuizDetailView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    def _get_quiz(self, quiz_id):
        try:
            return Quiz.objects.prefetch_related(
                'categories', 'questions__options', 'access_requirements'
            ).get(pk=quiz_id)
        except Quiz.DoesNotExist:
            return None

    def get(self, request, quiz_id):
        quiz = self._get_quiz(quiz_id)
        if not quiz:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='آزمون یافت نشد.'
            )
        serializer = QuizAdminSerializer(quiz, context={'request': request})
        return self.build_response(
            status.HTTP_200_OK, success=True, message='Successful', quiz=serializer.data
        )

    def put(self, request, quiz_id):
        quiz = self._get_quiz(quiz_id)
        if not quiz:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='آزمون یافت نشد.'
            )

        if 'title' in request.data:
            title = request.data['title']
            if not self.validate_string_secure(title, sql=True, lookup=True, injection=True):
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'title': 'Invalid parameter.'},
                )
            quiz.title = title

        if 'description' in request.data:
            quiz.description = request.data['description']
        if 'difficulty' in request.data:
            difficulty = request.data['difficulty']
            if difficulty not in [c[0] for c in Quiz.Difficulty.choices]:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'difficulty': 'مقدار سختی نامعتبر است.'},
                )
            quiz.difficulty = difficulty
        if 'is_active' in request.data:
            quiz.is_active = _parse_bool(request.data['is_active'])
        if 'randomize_question_order' in request.data:
            quiz.randomize_question_order = _parse_bool(request.data['randomize_question_order'])
        if 'max_attempts_per_user' in request.data:
            quiz.max_attempts_per_user = int(request.data['max_attempts_per_user'])
        if 'reveal_answers_during_quiz' in request.data:
            quiz.reveal_answers_during_quiz = _parse_bool(request.data['reveal_answers_during_quiz'])
        if 'allow_retry_on_expiry' in request.data:
            quiz.allow_retry_on_expiry = _parse_bool(request.data['allow_retry_on_expiry'])
        if 'start_date' in request.data:
            quiz.start_date = request.data['start_date'] or None
        if 'end_date' in request.data:
            quiz.end_date = request.data['end_date'] or None

        thumbnail = request.FILES.get('thumbnail')
        if thumbnail:
            if thumbnail.size > MAX_THUMBNAIL_SIZE:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'thumbnail': 'حجم تصویر نباید بیشتر از ۵ مگابایت باشد.'},
                )
            if thumbnail.content_type not in ALLOWED_THUMBNAIL_TYPES:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'thumbnail': 'فرمت تصویر معتبر نیست.'},
                )
            if quiz.thumbnail:
                quiz.thumbnail.delete(save=False)
            quiz.thumbnail = thumbnail

        quiz.save()

        if 'categories' in request.data:
            raw_cats = request.data.get('categories', [])
            category_ids = raw_cats if isinstance(raw_cats, list) else request.data.getlist('categories', [])
            quiz.categories.set(Category.objects.filter(pk__in=category_ids))

        serializer = QuizAdminSerializer(quiz, context={'request': request})
        return self.build_response(
            status.HTTP_200_OK, success=True, message='Successful', quiz=serializer.data
        )

    def delete(self, request, quiz_id):
        quiz = self._get_quiz(quiz_id)
        if not quiz:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='آزمون یافت نشد.'
            )
        quiz.delete()
        return self.build_response(status.HTTP_204_NO_CONTENT)


class AdminQuizQuestionListView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    def get(self, request, quiz_id):
        try:
            quiz = Quiz.objects.get(pk=quiz_id)
        except Quiz.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='آزمون یافت نشد.'
            )
        questions = Question.objects.prefetch_related('options', 'pairs').filter(quiz=quiz).order_by('order')
        serializer = QuestionAdminSerializer(questions, many=True)
        return self.build_response(
            status.HTTP_200_OK, success=True, message='Successful',
            questions=serializer.data,
        )

    def post(self, request, quiz_id):
        try:
            quiz = Quiz.objects.get(pk=quiz_id)
        except Quiz.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='آزمون یافت نشد.'
            )

        success, result = self.get_data(request, 'text')
        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1, message=result
            )

        q_type = request.data.get('type', Question.Type.MULTIPLE_CHOICE)
        if q_type not in [c[0] for c in Question.Type.choices]:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message={'type': 'نوع سوال نامعتبر است.'},
            )

        image = request.FILES.get('image', None)
        if image:
            if image.content_type not in ALLOWED_IMAGE_TYPES:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'image': 'فرمت تصویر نامعتبر است.'},
                )
            if image.size > MAX_IMAGE_SIZE:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'image': 'حجم تصویر نباید بیشتر از ۵ مگابایت باشد.'},
                )

        if q_type == Question.Type.MATCHING:
            pairs_raw = request.data.get('pairs', '[]')
            if isinstance(pairs_raw, str):
                try:
                    pairs_data = json.loads(pairs_raw)
                except (json.JSONDecodeError, TypeError):
                    pairs_data = []
            else:
                pairs_data = pairs_raw if isinstance(pairs_raw, list) else []
            if len(pairs_data) < 2:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'pairs': 'حداقل ۲ جفت لازم است.'},
                )
            if any(not str(p.get('left_text', '')).strip() or not str(p.get('right_text', '')).strip() for p in pairs_data):
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'pairs': 'متن همه جفت‌ها الزامی است.'},
                )
            try:
                with transaction.atomic():
                    question = Question.objects.create(
                        quiz=quiz,
                        type=q_type,
                        text=result['text'],
                        order=int(request.data.get('order', 0)),
                        score=int(request.data.get('score', 1)),
                        time_to_answer=int(request.data.get('time_to_answer', 30)),
                    )
                    if image:
                        question.image = image
                        question.save(update_fields=['image'])
                    MatchingPair.objects.bulk_create([
                        MatchingPair(
                            question=question,
                            left_text=p.get('left_text', ''),
                            right_text=p.get('right_text', ''),
                            order=i,
                        )
                        for i, p in enumerate(pairs_data)
                    ])
            except Exception as e:
                logger.error(f'AdminQuizQuestionListView.post (matching) failed: {e}')
                return self.build_response(
                    status.HTTP_500_INTERNAL_SERVER_ERROR, success=False, error=-2,
                    message='خطا در ایجاد سوال.',
                )
        else:
            options_raw = request.data.get('options', '[]')
            if isinstance(options_raw, str):
                try:
                    options_data = json.loads(options_raw)
                except (json.JSONDecodeError, TypeError):
                    options_data = []
            else:
                options_data = options_raw if isinstance(options_raw, list) else []
            if not isinstance(options_data, list):
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'options': 'لیست گزینه‌ها نامعتبر است.'},
                )
            expected_count = 2 if q_type == Question.Type.TRUE_FALSE else 4
            if len(options_data) != expected_count:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'options': f'سوال {q_type} باید دقیقاً {expected_count} گزینه داشته باشد.'},
                )
            correct_count = sum(1 for o in options_data if _parse_bool(o.get('is_correct', False)))
            if correct_count != 1:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'options': 'دقیقاً یک گزینه باید صحیح باشد.'},
                )
            try:
                with transaction.atomic():
                    question = Question.objects.create(
                        quiz=quiz,
                        type=q_type,
                        text=result['text'],
                        order=int(request.data.get('order', 0)),
                        score=int(request.data.get('score', 1)),
                        time_to_answer=int(request.data.get('time_to_answer', 30)),
                    )
                    if image:
                        question.image = image
                        question.save(update_fields=['image'])
                    QuestionOption.objects.bulk_create([
                        QuestionOption(
                            question=question,
                            text=opt.get('text', ''),
                            is_correct=_parse_bool(opt.get('is_correct', False)),
                            order=int(opt.get('order', i)),
                        )
                        for i, opt in enumerate(options_data)
                    ])
            except Exception as e:
                logger.error(f'AdminQuizQuestionListView.post failed: {e}')
                return self.build_response(
                    status.HTTP_500_INTERNAL_SERVER_ERROR, success=False, error=-2,
                    message='خطا در ایجاد سوال.',
                )

        question.refresh_from_db()
        serializer = QuestionAdminSerializer(
            Question.objects.prefetch_related('options', 'pairs').get(pk=question.pk)
        )
        return self.build_response(
            status.HTTP_201_CREATED, success=True, message='Successful',
            question=serializer.data,
        )


class AdminQuestionDetailView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    def put(self, request, question_id):
        try:
            question = Question.objects.prefetch_related('options').get(pk=question_id)
        except Question.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='سوال یافت نشد.'
            )

        if 'text' in request.data:
            question.text = request.data['text']
        if 'type' in request.data:
            q_type = request.data['type']
            if q_type not in [c[0] for c in Question.Type.choices]:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'type': 'نوع سوال نامعتبر است.'},
                )
            question.type = q_type
        if 'order' in request.data:
            question.order = int(request.data['order'])
        if 'score' in request.data:
            question.score = int(request.data['score'])
        if 'time_to_answer' in request.data:
            question.time_to_answer = int(request.data['time_to_answer'])

        image = request.FILES.get('image', None)
        if image:
            if image.content_type not in ALLOWED_IMAGE_TYPES:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'image': 'فرمت تصویر نامعتبر است.'},
                )
            if image.size > MAX_IMAGE_SIZE:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'image': 'حجم تصویر نباید بیشتر از ۵ مگابایت باشد.'},
                )

        if question.type == Question.Type.MATCHING:
            pairs_raw = request.data.get('pairs')
            if isinstance(pairs_raw, str):
                try:
                    pairs_data = json.loads(pairs_raw)
                except (json.JSONDecodeError, TypeError):
                    pairs_data = None
            elif isinstance(pairs_raw, list):
                pairs_data = pairs_raw
            else:
                pairs_data = None
            if pairs_data is not None:
                if len(pairs_data) < 2:
                    return self.build_response(
                        status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                        message={'pairs': 'حداقل ۲ جفت لازم است.'},
                    )
                if any(not str(p.get('left_text', '')).strip() or not str(p.get('right_text', '')).strip() for p in pairs_data):
                    return self.build_response(
                        status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                        message={'pairs': 'متن همه جفت‌ها الزامی است.'},
                    )
                try:
                    with transaction.atomic():
                        question.save()
                        question.pairs.all().delete()
                        MatchingPair.objects.bulk_create([
                            MatchingPair(
                                question=question,
                                left_text=p.get('left_text', ''),
                                right_text=p.get('right_text', ''),
                                order=i,
                            )
                            for i, p in enumerate(pairs_data)
                        ])
                except Exception as e:
                    logger.error(f'AdminQuestionDetailView.put (matching) failed: {e}')
                    return self.build_response(
                        status.HTTP_500_INTERNAL_SERVER_ERROR, success=False, error=-2,
                        message='خطا در ویرایش سوال.',
                    )
            else:
                question.save()
        else:
            options_data = request.data.get('options')
            if isinstance(options_data, str):
                try:
                    options_data = json.loads(options_data)
                except (json.JSONDecodeError, TypeError):
                    options_data = None
            if options_data is not None:
                expected_count = 2 if question.type == Question.Type.TRUE_FALSE else 4
                if not isinstance(options_data, list) or len(options_data) != expected_count:
                    return self.build_response(
                        status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                        message={'options': f'سوال {question.type} باید دقیقاً {expected_count} گزینه داشته باشد.'},
                    )
                correct_count = sum(1 for o in options_data if _parse_bool(o.get('is_correct', False)))
                if correct_count != 1:
                    return self.build_response(
                        status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                        message={'options': 'دقیقاً یک گزینه باید صحیح باشد.'},
                    )
                try:
                    with transaction.atomic():
                        question.save()
                        question.options.all().delete()
                        QuestionOption.objects.bulk_create([
                            QuestionOption(
                                question=question,
                                text=opt.get('text', ''),
                                is_correct=_parse_bool(opt.get('is_correct', False)),
                                order=int(opt.get('order', i)),
                            )
                            for i, opt in enumerate(options_data)
                        ])
                except Exception as e:
                    logger.error(f'AdminQuestionDetailView.put failed: {e}')
                    return self.build_response(
                        status.HTTP_500_INTERNAL_SERVER_ERROR, success=False, error=-2,
                        message='خطا در ویرایش سوال.',
                    )
            else:
                question.save()

        if image:
            if question.image:
                question.image.delete(save=False)
            question.image = image
            question.save(update_fields=['image'])

        serializer = QuestionAdminSerializer(
            Question.objects.prefetch_related('options', 'pairs').get(pk=question.pk),
            context={'request': request},
        )
        return self.build_response(
            status.HTTP_200_OK, success=True, message='Successful', question=serializer.data
        )

    def delete(self, request, question_id):
        try:
            question = Question.objects.get(pk=question_id)
        except Question.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='سوال یافت نشد.'
            )
        question.delete()
        return self.build_response(status.HTTP_204_NO_CONTENT)


class AdminQuestionReorderView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    def post(self, request):
        items = request.data.get('items')
        if not isinstance(items, list) or not items:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message={'items': 'لیست ترتیب‌بندی نامعتبر است.'},
            )

        ids = [str(item.get('id', '')) for item in items]
        questions = Question.objects.filter(pk__in=ids)
        if questions.count() != len(ids):
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message='برخی سوالات یافت نشدند.',
            )

        quiz_ids = set(questions.values_list('quiz_id', flat=True))
        if len(quiz_ids) != 1:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message='همه سوالات باید متعلق به یک آزمون باشند.',
            )

        order_map = {str(item['id']): int(item.get('order', 0)) for item in items}
        for question in questions:
            question.order = order_map[str(question.pk)]
        Question.objects.bulk_update(questions, ['order'])

        return self.build_response(
            status.HTTP_200_OK, success=True, message='ترتیب سوالات به‌روز شد.'
        )


# ---------------------------------------------------------------------------
# User views
# ---------------------------------------------------------------------------

class CategoryListView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    @method_decorator(
        drf_cached_response(
            ttl=1800,
            cache_prefix='quiz_categories',
            user_aware=False,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return self.build_response(
            status.HTTP_200_OK, success=True, message='Successful',
            categories=serializer.data,
        )


class QuizListView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    def _validate_page(self, value: str) -> bool:
        return value.isdigit() and int(value) >= 1

    def _validate_count(self, value: str) -> bool:
        return value.isdigit() and int(value) >= 1

    def get(self, request):
        success, result = self.get_data(
            request,
            ('page', self._validate_page),
            ('count', self._validate_count),
        )
        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1, message=result
            )

        page = int(result.get('page', 1))
        count = int(result.get('count', DEFAULT_PAGE_SIZE))
        category_slug = request.query_params.get('category', None)

        try:
            qs = (
                Quiz.objects
                .prefetch_related('categories', 'access_requirements')
                .filter(is_active=True)
            )
            now = timezone.now()
            # Exclude quizzes that haven't started yet or have ended
            qs = qs.filter(
                Q(start_date__isnull=True) | Q(start_date__lte=now)
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gte=now)
            )

            if category_slug:
                if not self.validate_string_secure(category_slug, sql=True, lookup=True, injection=True):
                    return self.build_response(
                        status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                        message={'category': 'Invalid parameter.'},
                    )
                qs = qs.filter(categories__slug=category_slug).distinct()

            paginator = Paginator(qs, count)
            page_obj = paginator.page(page)

        except EmptyPage:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='Empty Page.'
            )
        except Exception as e:
            logger.error(f'QuizListView failed: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR, success=False, error=-2,
                message='Something went wrong.',
            )

        serializer = QuizListSerializer(
            list(page_obj.object_list),
            many=True,
            context={'request': request, 'user': request.user},
        )
        return self.build_response(
            status.HTTP_200_OK, success=True, message='Successful',
            quizzes=serializer.data,
            total=paginator.count,
            page=page,
            page_size=count,
            total_pages=paginator.num_pages,
            has_next=page_obj.has_next(),
            has_previous=page_obj.has_previous(),
        )


class QuizDetailView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    def get(self, request, quiz_id):
        try:
            quiz = (
                Quiz.objects
                .prefetch_related('categories', 'access_requirements')
                .get(pk=quiz_id, is_active=True)
            )
        except Quiz.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='آزمون یافت نشد.'
            )
        serializer = QuizDetailSerializer(
            quiz, context={'request': request, 'user': request.user}
        )
        return self.build_response(
            status.HTTP_200_OK, success=True, message='Successful', quiz=serializer.data
        )


class QuizStartView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'

    def post(self, request, quiz_id):
        try:
            quiz = (
                Quiz.objects
                .prefetch_related('access_requirements')
                .get(pk=quiz_id, is_active=True)
            )
        except Quiz.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='آزمون یافت نشد.'
            )

        now = timezone.now()
        if quiz.start_date and now < quiz.start_date:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message='این آزمون هنوز شروع نشده است.',
            )
        if quiz.end_date and now > quiz.end_date:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message='زمان این آزمون به پایان رسیده است.',
            )

        # Check for existing in-progress attempt
        existing = QuizAttempt.objects.filter(
            quiz=quiz, user=request.user, status=QuizAttempt.Status.IN_PROGRESS
        ).first()
        if existing:
            key = ATTEMPT_CACHE_KEY.format(attempt_id=existing.id)
            if cache.get(key) is not None:
                return self.build_response(
                    status.HTTP_409_CONFLICT, success=False, error=-4,
                    message='آزمون در حال اجرا دارید.',
                )
            # Redis key expired — mark attempt as expired and continue
            existing.status = QuizAttempt.Status.EXPIRED
            existing.save(update_fields=['status', 'updated_at'])

        # Check attempt limit
        if quiz.max_attempts_per_user > 0:
            statuses = [QuizAttempt.Status.COMPLETED]
            if not quiz.allow_retry_on_expiry:
                statuses.append(QuizAttempt.Status.EXPIRED)
            used_count = QuizAttempt.objects.filter(
                quiz=quiz, user=request.user, status__in=statuses
            ).count()
            if used_count >= quiz.max_attempts_per_user:
                return self.build_response(
                    status.HTTP_403_FORBIDDEN, success=False, error=-5,
                    message='به حداکثر تعداد مجاز شرکت در این آزمون رسیده‌اید.',
                )

        # Check access requirements
        access_met, reason = _check_access(quiz, request.user)
        if not access_met:
            return self.build_response(
                status.HTTP_403_FORBIDDEN, success=False, error=-6, message=reason
            )

        # Fetch questions
        questions_qs = Question.objects.prefetch_related('options', 'pairs').filter(quiz=quiz).order_by('order')
        questions = list(questions_qs)
        if not questions:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message='این آزمون هنوز سوالی ندارد.',
            )

        if quiz.randomize_question_order:
            random.shuffle(questions)

        # Create attempt
        attempt = QuizAttempt.objects.create(
            quiz=quiz,
            user=request.user,
            status=QuizAttempt.Status.IN_PROGRESS,
        )

        # Set Redis TTL
        total_ttl = sum(q.time_to_answer for q in questions)
        if total_ttl <= 0:
            total_ttl = 3600
        cache.set(ATTEMPT_CACHE_KEY.format(attempt_id=attempt.id), 1, timeout=total_ttl)

        from .serializers import QuestionSerializer
        serializer = QuestionSerializer(questions, many=True)
        return self.build_response(
            status.HTTP_200_OK, success=True, message='Successful',
            attempt_id=str(attempt.id),
            questions=serializer.data,
            total_time_seconds=total_ttl,
            reveal_answers_during_quiz=quiz.reveal_answers_during_quiz,
        )


class QuizSubmitAnswerView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'

    def post(self, request, quiz_id, attempt_id):
        try:
            attempt = QuizAttempt.objects.select_related('quiz').get(
                pk=attempt_id, user=request.user
            )
        except QuizAttempt.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='تلاش یافت نشد.'
            )

        if str(attempt.quiz.id) != str(quiz_id):
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message='آزمون با تلاش مطابقت ندارد.',
            )
        if attempt.status != QuizAttempt.Status.IN_PROGRESS:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message='این آزمون در وضعیت فعال نیست.',
            )

        success, result = self.get_data(request, 'question_id')
        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1, message=result
            )

        question_id = result['question_id']

        try:
            question = Question.objects.prefetch_related('pairs').get(pk=question_id, quiz_id=quiz_id)
        except Question.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='سوال یافت نشد.'
            )

        if AttemptAnswer.objects.filter(attempt=attempt, question=question).exists():
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message='این سوال قبلاً پاسخ داده شده است.',
            )

        time_taken = int(request.data.get('time_taken', 0))

        if question.type == Question.Type.MATCHING:
            matching_answer = request.data.get('matching_answer', {})
            if isinstance(matching_answer, str):
                try:
                    matching_answer = json.loads(matching_answer)
                except (json.JSONDecodeError, TypeError):
                    matching_answer = {}
            if not isinstance(matching_answer, dict):
                matching_answer = {}
            pairs = list(question.pairs.all())
            is_correct = bool(pairs) and all(
                str(p.right_id) == matching_answer.get(str(p.left_id))
                for p in pairs
            )
            AttemptAnswer.objects.create(
                attempt=attempt,
                question=question,
                is_correct=is_correct,
                time_taken=time_taken,
                matching_answer=matching_answer,
            )
            response_data = dict(success=True, message='پاسخ ثبت شد.')
            if attempt.quiz.reveal_answers_during_quiz:
                response_data['is_correct'] = is_correct
                response_data['correct_pairs'] = [
                    {'left_id': str(p.left_id), 'right_id': str(p.right_id)}
                    for p in pairs
                ]
            return self.build_response(status.HTTP_200_OK, **response_data)

        selected_option_id = request.data.get('selected_option_id')
        if not selected_option_id:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message={'selected_option_id': 'این فیلد الزامی است.'},
            )
        try:
            option = QuestionOption.objects.get(pk=selected_option_id, question=question)
        except QuestionOption.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='گزینه یافت نشد.'
            )

        AttemptAnswer.objects.create(
            attempt=attempt,
            question=question,
            selected_option=option,
            is_correct=option.is_correct,
            time_taken=time_taken,
        )

        response_data = dict(success=True, message='پاسخ ثبت شد.')
        if attempt.quiz.reveal_answers_during_quiz:
            correct_option = question.options.filter(is_correct=True).first()
            response_data['is_correct'] = option.is_correct
            response_data['correct_option_id'] = str(correct_option.id) if correct_option else None

        return self.build_response(status.HTTP_200_OK, **response_data)


class QuizFinishView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'

    def post(self, request, quiz_id, attempt_id):
        try:
            attempt = QuizAttempt.objects.select_related('quiz').get(
                pk=attempt_id, user=request.user
            )
        except QuizAttempt.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='تلاش یافت نشد.'
            )

        if str(attempt.quiz.id) != str(quiz_id):
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message='آزمون با تلاش مطابقت ندارد.',
            )
        if attempt.status != QuizAttempt.Status.IN_PROGRESS:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message='این آزمون قبلاً پایان یافته است.',
            )

        key = ATTEMPT_CACHE_KEY.format(attempt_id=attempt.id)
        key_exists = cache.get(key)

        answers = list(
            AttemptAnswer.objects.select_related('question', 'selected_option')
            .prefetch_related('question__options', 'question__pairs')
            .filter(attempt=attempt)
        )

        score = sum(a.question.score for a in answers if a.is_correct)
        correct_count = sum(1 for a in answers if a.is_correct)
        incorrect_count = sum(1 for a in answers if not a.is_correct)
        total_questions = attempt.quiz.questions.count()
        time_spent = int((timezone.now() - attempt.started_at).total_seconds())

        attempt.score = score
        attempt.correct_count = correct_count
        attempt.incorrect_count = incorrect_count
        attempt.time_spent = time_spent
        attempt.finished_at = timezone.now()
        attempt.status = (
            QuizAttempt.Status.EXPIRED if key_exists is None else QuizAttempt.Status.COMPLETED
        )
        attempt.save()

        if key_exists is not None:
            cache.delete(key)

        answers_data = AttemptAnswerResultSerializer(answers, many=True).data

        return self.build_response(
            status.HTTP_200_OK, success=True, message='Successful',
            score=score,
            correct_count=correct_count,
            incorrect_count=incorrect_count,
            total_questions=total_questions,
            time_spent=time_spent,
            status=attempt.status,
            answers=answers_data,
        )


class LeaderboardView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    def get(self, request):
        top10 = list(
            QuizAttempt.objects
            .filter(status=QuizAttempt.Status.COMPLETED)
            .values('user__id', 'user__username')
            .annotate(total_score=Sum('score'))
            .order_by('-total_score')[:10]
        )

        user_rank = None
        user_entry = None
        if request.user and request.user.is_authenticated:
            user_total = (
                QuizAttempt.objects
                .filter(user=request.user, status=QuizAttempt.Status.COMPLETED)
                .aggregate(total=Sum('score'))['total'] or 0
            )
            users_above = (
                QuizAttempt.objects
                .filter(status=QuizAttempt.Status.COMPLETED)
                .values('user')
                .annotate(total_score=Sum('score'))
                .filter(total_score__gt=user_total)
                .count()
            )
            user_rank = users_above + 1
            user_in_top10 = any(e['user__id'] == request.user.id for e in top10)
            if not user_in_top10:
                user_entry = {
                    'user__id': request.user.id,
                    'user__username': request.user.username,
                    'total_score': user_total,
                    'rank': user_rank,
                }

        return self.build_response(
            status.HTTP_200_OK, success=True, message='Successful',
            leaderboard=top10,
            user_rank=user_rank,
            user_entry=user_entry,
        )


class MyAttemptsView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'

    @method_decorator(
        drf_cached_response(
            ttl=120,
            cache_prefix='quiz_my_attempts',
            user_aware=True,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        attempts = (
            QuizAttempt.objects
            .select_related('quiz')
            .filter(user=request.user)
            .order_by('-created_at')
        )
        serializer = QuizAttemptSerializer(attempts, many=True)
        return self.build_response(
            status.HTTP_200_OK, success=True, message='Successful',
            attempts=serializer.data,
            total=attempts.count(),
        )


class AdminQuizRequirementListView(APIView, GetDataMixin, ResponseBuilderMixin):
    """Create an access requirement for a quiz."""
    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    def post(self, request, quiz_id):
        try:
            quiz = Quiz.objects.get(pk=quiz_id)
        except Quiz.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='آزمون یافت نشد.'
            )

        req_type = request.data.get('type', QuizAccessRequirement.Type.FREE)
        if req_type not in [c[0] for c in QuizAccessRequirement.Type.choices]:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message={'type': 'نوع دسترسی نامعتبر است.'},
            )

        if quiz.access_requirements.filter(type=req_type).exists():
            return self.build_response(
                status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                message={'type': 'این نوع شرط دسترسی قبلاً تعریف شده است.'},
            )

        required_quiz = None
        if req_type == QuizAccessRequirement.Type.COMPLETED_QUIZ:
            required_quiz_id = request.data.get('required_quiz_id')
            if not required_quiz_id:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'required_quiz_id': 'آزمون پیش‌نیاز الزامی است.'},
                )
            try:
                required_quiz = Quiz.objects.get(pk=required_quiz_id)
            except Quiz.DoesNotExist:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND, success=False, error=-3,
                    message='آزمون پیش‌نیاز یافت نشد.',
                )

        required_score = None
        if req_type == QuizAccessRequirement.Type.MIN_SCORE:
            required_score = request.data.get('required_score')
            if required_score is None:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST, success=False, error=-1,
                    message={'required_score': 'حداقل امتیاز الزامی است.'},
                )
            required_score = int(required_score)

        req = QuizAccessRequirement.objects.create(
            quiz=quiz,
            type=req_type,
            required_quiz=required_quiz,
            required_score=required_score,
        )
        serializer = AccessRequirementSerializer(req)
        return self.build_response(
            status.HTTP_201_CREATED, success=True, message='Successful',
            requirement=serializer.data,
        )


class AdminQuizRequirementDetailView(APIView, GetDataMixin, ResponseBuilderMixin):
    """Delete a single access requirement."""
    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    def delete(self, request, req_id):
        try:
            req = QuizAccessRequirement.objects.get(pk=req_id)
        except QuizAccessRequirement.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND, success=False, error=-3, message='شرط دسترسی یافت نشد.'
            )
        req.delete()
        return self.build_response(status.HTTP_204_NO_CONTENT)


class AdminQuizParticipantsView(APIView, ResponseBuilderMixin):
    """Return all completed attempts for a quiz, ordered by score."""
    permission_classes = (IsAdminUser,)
    throttle_scope = 'main-throttle'

    def get(self, request, quiz_id):
        quiz = get_object_or_404(Quiz, id=quiz_id)
        attempts = (
            QuizAttempt.objects
            .filter(quiz=quiz, status=QuizAttempt.Status.COMPLETED)
            .select_related('user')
            .order_by('-score', 'time_spent')
        )
        data = [
            {
                'user_id': a.user.id,
                'username': a.user.username,
                'score': a.score,
                'correct_count': a.correct_count,
                'incorrect_count': a.incorrect_count,
                'time_spent': a.time_spent,
                'finished_at': a.finished_at,
            }
            for a in attempts
        ]
        return self.build_response(
            status.HTTP_200_OK, success=True,
            message='Successful', participants=data, total=len(data)
        )
