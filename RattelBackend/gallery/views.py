import logging

from django.core.paginator import EmptyPage, Paginator
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from RattelBackend.cache import drf_cached_response
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin
from .models import Gallery
from .serializers import GalleryListSerializer, GalleryDetailSerializer

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 12


class GalleryListView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    def _parse_page(self, value):
        return int(value) if value and str(value).isdigit() and int(value) >= 1 else 1

    def _parse_count(self, value):
        if value is None:
            return DEFAULT_PAGE_SIZE
        if str(value).isdigit() and int(value) >= 0:
            return int(value)
        return DEFAULT_PAGE_SIZE

    @method_decorator(
        drf_cached_response(
            ttl=900,
            cache_prefix='gallery_list',
            user_aware=False,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        page = self._parse_page(request.query_params.get('page'))
        count = self._parse_count(request.query_params.get('count'))

        try:
            qs = Gallery.objects.prefetch_related('content').all()
            if count == 0:
                items = list(qs)
                paginator = None
                page_obj = None
            else:
                paginator = Paginator(qs, count)
                page_obj = paginator.page(page)
                items = list(page_obj.object_list)
        except EmptyPage:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-3,
                message='Empty Page.'
            )
        except Exception as e:
            logger.error(f'GalleryListView failed: {e.__class__.__name__}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-2,
                message='Something went wrong while fetching gallery items.'
            )

        if not items:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-3,
                message='Empty Page.'
            )

        serializer = GalleryListSerializer(items, many=True, context={'request': request})
        if paginator:
            total = paginator.count
            total_pages = paginator.num_pages
            has_next = page_obj.has_next()
            has_previous = page_obj.has_previous()
        else:
            total = len(items)
            total_pages = None
            has_next = None
            has_previous = None

        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            items=serializer.data,
            total=total,
            page=page,
            page_size=count,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
        )


class GalleryDetailView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    @method_decorator(
        drf_cached_response(
            ttl=900,
            cache_prefix='gallery_detail',
            user_aware=False,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request, gallery_id):
        try:
            gallery = Gallery.objects.prefetch_related('content').get(pk=gallery_id)
        except Gallery.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-1,
                message='Gallery item not found.'
            )
        except Exception as e:
            logger.error(f'GalleryDetailView failed for id={gallery_id}: {e.__class__.__name__}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-2,
                message='Something went wrong while fetching gallery item.'
            )

        serializer = GalleryDetailSerializer(gallery, context={'request': request})
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            item=serializer.data,
        )
