import logging
from datetime import date

from django.core.paginator import EmptyPage, Paginator
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from RattelBackend.cache import drf_cached_response
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin

from .models import InPersonClass, InPersonClassRegistration
from .serializers import (
    CategorySerializer,
    InPersonClassListSerializer,
    InPersonClassRegistrationSerializer,
)

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 9


class InPersonClassListView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    def _validate_page(self, value: str) -> bool:
        return value.isdigit() and int(value) >= 1

    def _validate_count(self, value: str) -> bool:
        return value.isdigit() and int(value) >= 1

    @method_decorator(
        drf_cached_response(
            ttl=900,
            cache_prefix='in_person_class_list',
            user_aware=False,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        success, result = self.get_data(
            request,
            ('page', self._validate_page),
            ('count', self._validate_count),
        )

        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result,
            )

        page = int(result.get('page', 1))
        count = int(result.get('count', DEFAULT_PAGE_SIZE))
        category_slug = request.query_params.get('category', None)

        try:
            qs = (
                InPersonClass.objects
                .prefetch_related('available_times', 'categories')
                .filter(is_visible=True)
                .order_by('-start_date')
            )

            if category_slug:
                if not self.validate_string_secure(category_slug, sql=True, lookup=True, injection=True):
                    return self.build_response(
                        status.HTTP_400_BAD_REQUEST,
                        success=False,
                        error=-1,
                        message={'category': 'Invalid parameter.'},
                    )
                qs = qs.filter(categories__slug=category_slug).distinct()

            paginator = Paginator(qs, count)
            page_obj = paginator.page(page)

        except EmptyPage:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-3,
                message='Empty Page.',
            )
        except Exception as e:
            logger.error(f'InPersonClassListView failed: {e.__class__.__name__}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-2,
                message='Something went wrong while fetching classes.',
            )

        serializer = InPersonClassListSerializer(
            list(page_obj.object_list),
            many=True,
            context={'request': request},
        )

        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            classes=serializer.data,
            total=paginator.count,
            page=page,
            page_size=count,
            total_pages=paginator.num_pages,
            has_next=page_obj.has_next(),
            has_previous=page_obj.has_previous(),
        )


class CategoryListView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    @method_decorator(
        drf_cached_response(
            ttl=1800,
            cache_prefix='in_person_class_categories',
            user_aware=False,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        from .models import Category
        categories = Category.objects.all()
        serializer = CategorySerializer(categories, many=True)
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            categories=serializer.data,
        )


class RegisterView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'

    def post(self, request):
        success, result = self.get_data(request, 'class_id', 'time_range_id')

        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result,
            )

        class_id = result['class_id']
        time_range_id = result['time_range_id']

        if not self.validate_string_secure(str(class_id), sql=True, lookup=True, injection=True):
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message={'class_id': 'Invalid parameter.'},
            )

        try:
            ipc = InPersonClass.objects.prefetch_related('available_times').get(
                pk=class_id, is_visible=True
            )
        except InPersonClass.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-3,
                message='کلاس مورد نظر یافت نشد.',
            )

        if not ipc.available_times.filter(pk=time_range_id).exists():
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message={'time_range_id': 'زمان انتخابی برای این کلاس معتبر نیست.'},
            )

        if ipc.end_date < date.today():
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message='این کلاس دیگر پذیرش ندارد.',
            )

        registration, _ = InPersonClassRegistration.objects.get_or_create(
            in_person_class=ipc,
            time_range_id=time_range_id,
            defaults={
                'start_date': ipc.start_date,
                'end_date': ipc.end_date,
                'price': ipc.price,
                'new_price': ipc.new_price,
            },
        )

        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            id=str(registration.pk),
        )


class MyRegistrationsView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'

    @method_decorator(
        drf_cached_response(
            ttl=300,
            cache_prefix='my_in_person_class_registrations',
            user_aware=True,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        registrations = (
            InPersonClassRegistration.objects
            .select_related('in_person_class', 'time_range')
            .prefetch_related('in_person_class__categories', 'in_person_class__available_times')
            .filter(bought_by=request.user)
            .order_by('-created_at')
        )

        serializer = InPersonClassRegistrationSerializer(
            registrations,
            many=True,
            context={'request': request},
        )

        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            registrations=serializer.data,
            total=registrations.count(),
        )
