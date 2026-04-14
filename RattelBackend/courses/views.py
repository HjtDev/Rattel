import logging
from typing import Any, Dict, Optional, Tuple
from django.contrib.auth import get_user_model
from django.core.paginator import Paginator, EmptyPage
from django.db.models import QuerySet, Count, Avg
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from RattelBackend.cache import drf_cached_response
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin
from users.serializers import QuickUserSerializer
from .models import Course
from .serializers import CourseListSerializer, CourseDetailSerializer

logger = logging.getLogger(__name__)
User = get_user_model()

SORT_MAP = {
    'rating': '-rating',
    'total_sell': None,          # handled manually — it's a property
    'has_discount': None,        # handler manually
    'most_videos': '-chapters__number_of_videos',
    'longest': '-total_time',
    'shortest': 'total_time',
}

DEFAULT_PAGE_SIZE = 12


class CourseListView(APIView, GetDataMixin, ResponseBuilderMixin):
    """
    Public API endpoint for listing courses with filtering, sorting, and pagination.

    Permissions:
        - AllowAny: No authentication required

    Throttling:
        - Uses the `main-throttle` scope -> 500/min

    Caching:
        - TTL: 15 minutes (900 seconds)
        - Cache prefix: 'course_list'
        - User-agnostic caching

    Query Params:
        - page (int):          Page number (default: 1)
        - count (int):         Number of results per page, 0 for unlimited (default: 12)
        - sort (str):          Sort order — rating | total_sell | most_videos | longest | shortest
        - age_group (str):     Filter by age group
        - difficulty (str):    Filter by difficulty
        - category (str):      Filter by category
        - teacher_name (str):  Filter by teacher name (partial match)
    """

    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    VALID_SORT_OPTIONS = ('rating', 'total_sell', 'has_discount', 'most_videos', 'longest', 'shortest')

    def _validate_sort(self, value: str) -> bool:
        return value in self.VALID_SORT_OPTIONS

    def _validate_page(self, value: str) -> bool:
        return value.isdigit() and int(value) >= 1

    def _validate_count(self, value: str) -> bool:
        return value.isdigit() and int(value) >= 1

    def _apply_filters(self, qs, params: Dict[str, Any]):
        """Apply query filters to the course queryset.

        Args:
            qs: Base Course queryset.
            params: Dict of validated query params.

        Returns:
            Filtered queryset.
        """
        if age_group := params.get('age_group'):
            qs = qs.filter(age_group=age_group)
        if difficulty := params.get('difficulty'):
            qs = qs.filter(difficulty=difficulty)
        if category := params.get('category'):
            qs = qs.filter(category=category)
        if teacher_name := params.get('teacher_name'):
            qs = qs.filter(teacher__name__icontains=teacher_name)
        return qs

    def _apply_sort(self, qs, sort: Optional[str]) -> Tuple[QuerySet, bool]:
        """Apply sorting to the queryset.

        Args:
            qs: Filtered queryset.
            sort: Sort key string or None.

        Returns:
            Tuple of (queryset, needs_python_sort bool).
            Python sort is needed for property-based sorts like total_sell.
        """
        if not sort:
            return qs.order_by('-created_at'), False
        if sort == 'total_sell':
            return qs, True
        if sort == 'has_discount':
            return qs.filter(new_price__gt=0).order_by('new_price'), False
        return qs.order_by(SORT_MAP[sort]), False

    def _paginate(self, items, page: int, count: int):
        """Paginate items using Django's built-in Paginator.

        Args:
            items: Queryset or list to paginate.
            page: 1-indexed page number.
            count: Items per page. 0 means return all without pagination.

        Returns:
            Tuple of (page_object_or_items, paginator_or_None).
        """
        if count == 0:
            return items, None
        paginator = Paginator(items, count)
        page_obj = paginator.page(page)   # raises EmptyPage if page is out of range
        return page_obj, paginator

    @method_decorator(
        drf_cached_response(
            ttl=900,
            cache_prefix='course_list',
            user_aware=False,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        """
        Return a paginated, filtered, sorted list of courses.

        Query Params:
            page (int):         Page number, >= 1
            count (int):        Results per page, 0
            sort (str):         One of rating | total_sell | most_videos | longest | shortest
            age_group (str):    Filter by AgeGroupChoices value
            difficulty (str):   Filter by DifficultyChoices value
            category (str):     Filter by CategoryChoices value
            teacher_name (str): Partial match on teacher name

        Returns:
            200 OK:
                - success=True
                - message: 'Successful'
                - courses: Serialized course list
                - total: Total matching course count
                - page: Current page number
                - page_size: Requested count per page
                - total_pages: Total number of pages (null when count=0)
                - has_next: Whether a next page exists (null when count=0)
                - has_previous: Whether a previous page exists (null when count=0)

            400 BAD REQUEST:
                - success=False
                - error: -1
                - message: Validation error detail

            404 NOT FOUND:
                - success=False
                - error: -3
                - message: Empty page

            500 INTERNAL SERVER ERROR:
                - success=False
                - error: -2
                - message: Generic failure message
        """
        success, result = self.get_data(
            request,
            ('page', self._validate_page),
            ('count', self._validate_count),
        )
        sort = request.query_params.get('sort', None)

        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result
            )

        if sort is not None and not self._validate_sort(sort):
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message={'sort': 'Invalid parameter.'}
            )

        page = int(result['page'])
        count = int(result['count'])

        try:
            qs = Course.objects.select_related('teacher').prefetch_related('chapters', 'bought_by').filter(is_visible=True)
            qs = self._apply_filters(qs, request.query_params)
            qs, needs_python_sort = self._apply_sort(qs, sort)

            if needs_python_sort:
                qs = sorted(qs, key=lambda c: c.total_sell, reverse=True)

            page_obj, paginator = self._paginate(qs, page, count)

        except EmptyPage:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-3,
                message='Empty Page.'
            )
        except Exception as e:
            logger.error(f'CourseListView failed: {e.__class__.__name__}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-2,
                message='Something went wrong while fetching courses.'
            )

        if paginator:
            courses_data = list(page_obj.object_list)
            total = paginator.count
            total_pages = paginator.num_pages
            has_next = page_obj.has_next()
            has_previous = page_obj.has_previous()
        else:
            courses_data = list(qs) if isinstance(qs, QuerySet) else list(page_obj)
            total = len(courses_data)
            total_pages = None
            has_next = None
            has_previous = None

        if not courses_data:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-3,
                message='Empty Page.'
            )

        serializer = CourseListSerializer(courses_data, many=True)

        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            courses=serializer.data,
            total=total,
            page=page,
            page_size=count,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
        )


class CourseDetailView(APIView, GetDataMixin, ResponseBuilderMixin):
    """
    Public API endpoint for retrieving full details of a single course.

    Permissions:
        - AllowAny: No authentication required

    Throttling:
        - Uses the `main-throttle` scope -> 500/min

    Caching:
        - TTL: 15 minutes (900 seconds)
        - Cache prefix: 'course_detail'
        - User-agnostic caching
    """

    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    @method_decorator(
        drf_cached_response(
            ttl=900,
            cache_prefix='course_detail',
            user_aware=True,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request, course_id):
        """
        Return full details for a single course by its UUID.

        Path Params:
            course_id (UUID): The primary key of the course.

        Returns:
            200 OK:
                - success=True
                - message: 'Successful'
                - course: Fully serialized course data including chapters and episodes

            404 NOT FOUND:
                - success=False
                - error: -1
                - message: Course not found

            500 INTERNAL SERVER ERROR:
                - success=False
                - error: -2
                - message: Generic failure message
        """
        if not self.validate_string_secure(course_id, sql=True, lookup=True, injection=True):
            metadata = {
                'user': request.user,
                'ip': self.get_client_ip(request),
                'user_agent': self.get_client_user_agent(request)
            }
            logger.warning(f'Dangerous request has been denied.\n{metadata}')
            return self.build_response(
                status.HTTP_403_FORBIDDEN,
                success=False,
                error=-10,
                message='Insecure parameter'
            )

        try:
            course = (
                Course.objects
                .select_related('teacher')
                .prefetch_related('chapters__episodes', 'bought_by')
                .get(pk=course_id, is_visible=True)
            )
        except Course.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-1,
                message='Course not found.'
            )
        except Exception as e:
            logger.error(f'CourseDetailView failed for id={course_id}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-2,
                message='Something went wrong while fetching the course.'
            )

        serializer = CourseDetailSerializer(course, context={'request': request})
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            course=serializer.data,
        )


class TeacherListView(APIView, GetDataMixin, ResponseBuilderMixin):
    """
    Public API endpoint for listing teachers with their course stats.

    Permissions:
        - AllowAny: No authentication required

    Throttling:
        - Uses the `main-throttle` scope -> 500/min

    Caching:
        - TTL: 15 minutes (900 seconds)
        - Cache prefix: 'teacher_list'
        - User-agnostic caching
    """

    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    @method_decorator(
        drf_cached_response(
            ttl=900,
            cache_prefix='teacher_list',
            user_aware=False,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        """
        Return a list of teachers with their name, profile picture, course count,
        and average course rating.

        Returns:
            200 OK:
                - success=True
                - message: 'Successful'
                - teachers: List of teacher objects, each containing:
                    - name
                    - profile_picture
                    - number_of_courses
                    - average_rating

            500 INTERNAL SERVER ERROR:
                - success=False
                - error: -1
                - message: Generic failure message
        """
        try:
            teachers = (
                User.objects
                .filter(courses_taught__isnull=False)
                .annotate(
                    number_of_courses=Count('courses_taught', distinct=True),
                    average_rating=Avg('courses_taught__rating'),
                )
                .distinct()
            )

            data = [
                {
                    **QuickUserSerializer(teacher, context={'request': request}).data,
                    'number_of_courses': teacher.number_of_courses,
                    'average_rating': round(teacher.average_rating, 2) if teacher.average_rating else 0.0,
                }
                for teacher in teachers
            ]
        except Exception as e:
            logger.error(f'TeacherListView failed: {e.__class__.__name__}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-1,
                message='Something went wrong while fetching teachers.'
            )

        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            teachers=data,
        )
