import logging
from django.core.paginator import EmptyPage, Paginator
from django.db.models import F, Q
from django.utils.decorators import method_decorator
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from RattelBackend.cache import drf_cached_response, invalidate_cache
from RattelBackend.mixins import GetDataMixin, ResponseBuilderMixin
from .models import BlogPost, BlogComment, BlogCategory, BlogTag
from .serializers import BlogPostListSerializer, BlogPostDetailSerializer, BlogCommentSerializer

logger = logging.getLogger(__name__)

DEFAULT_PAGE_SIZE = 12
VALID_SORT_OPTIONS = ('newest', 'oldest', 'most_views', 'least_views', 'most_read')


class BlogListView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    def _parse_page(self, value):
        return int(value) if value and str(value).isdigit() and int(value) > 0 else 1

    def _parse_count(self, value):
        if value is None:
            return DEFAULT_PAGE_SIZE
        if str(value).isdigit() and int(value) >= 0:
            return int(value)
        return DEFAULT_PAGE_SIZE

    def _apply_filters(self, qs, request):
        category = request.query_params.get('category')
        tag = request.query_params.get('tag')
        author = request.query_params.get('author')
        search = request.query_params.get('search')

        if category and self.validate_string_secure(category, lookup=True, sql=True, injection=True):
            qs = qs.filter(Q(category__slug=category) | Q(category__name__iexact=category))

        if tag and self.validate_string_secure(tag, lookup=True, sql=True, injection=True):
            qs = qs.filter(Q(tags__slug=tag) | Q(tags__name__iexact=tag))

        if author and self.validate_string_secure(author, lookup=True, sql=True, injection=True):
            qs = qs.filter(author__name__icontains=author)

        if search and self.validate_string_secure(search, lookup=True, sql=True, injection=True):
            qs = qs.filter(
                Q(title__icontains=search)
                | Q(short_description__icontains=search)
                | Q(description__icontains=search)
                | Q(tags__name__icontains=search)
            )

        return qs.distinct()

    def _apply_sort(self, qs, sort):
        sort = sort if sort in VALID_SORT_OPTIONS else 'newest'
        if sort == 'newest':
            return qs.order_by('-published_at', '-created_at')
        if sort == 'oldest':
            return qs.order_by('published_at', 'created_at')
        if sort == 'most_views':
            return qs.order_by('-view_count', '-published_at')
        if sort == 'least_views':
            return qs.order_by('view_count', '-published_at')
        if sort == 'most_read':
            return qs.order_by('-ttr', '-published_at')
        return qs

    @method_decorator(
        drf_cached_response(
            ttl=600,
            cache_prefix='blog_list',
            user_aware=True,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        page = self._parse_page(request.query_params.get('page'))
        count = self._parse_count(request.query_params.get('count'))
        sort = request.query_params.get('sort', 'newest')

        try:
            qs = BlogPost.objects.select_related('author', 'category').prefetch_related('tags').filter(is_visible=True)
            qs = self._apply_filters(qs, request)
            qs = self._apply_sort(qs, sort)

            if count == 0:
                posts = list(qs)
                paginator = None
                page_obj = None
            else:
                paginator = Paginator(qs, count)
                page_obj = paginator.page(page)
                posts = list(page_obj.object_list)

        except EmptyPage:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-3,
                message='Empty Page.'
            )
        except Exception as e:
            logger.error(f'BlogListView failed: {e.__class__.__name__}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-2,
                message='Something went wrong while fetching blog posts.'
            )

        if not posts:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-3,
                message='Empty Page.'
            )

        serializer = BlogPostListSerializer(posts, many=True, context={'request': request})

        if paginator:
            total = paginator.count
            total_pages = paginator.num_pages
            has_next = page_obj.has_next()
            has_previous = page_obj.has_previous()
        else:
            total = len(posts)
            total_pages = None
            has_next = None
            has_previous = None

        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            posts=serializer.data,
            total=total,
            page=page,
            page_size=count,
            total_pages=total_pages,
            has_next=has_next,
            has_previous=has_previous,
        )


class BlogDetailView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    @method_decorator(
        drf_cached_response(
            ttl=600,
            cache_prefix='blog_detail',
            user_aware=True,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request, post_id):
        try:
            post = (
                BlogPost.objects
                .select_related('author', 'category')
                .prefetch_related('tags', 'comments__user', 'comments__replies__user')
                .get(pk=post_id, is_visible=True)
            )
        except BlogPost.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-1,
                message='Blog post not found.'
            )
        except Exception as e:
            logger.error(f'BlogDetailView failed for id={post_id}: {e.__class__.__name__}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-2,
                message='Something went wrong while fetching the blog post.'
            )

        serializer = BlogPostDetailSerializer(post, context={'request': request})
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            post=serializer.data,
        )


class BlogViewCountView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    @method_decorator(
        drf_cached_response(
            ttl=1800,
            cache_prefix='blog_view_count',
            user_aware=True,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request, post_id):
        try:
            updated = BlogPost.objects.filter(pk=post_id, is_visible=True).update(view_count=F('view_count') + 1)
            if not updated:
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    success=False,
                    error=-1,
                    message='Blog post not found.'
                )

            post = BlogPost.objects.only('id', 'view_count').get(pk=post_id)
            invalidate_cache('blog_list')
            invalidate_cache('blog_detail')
            return self.build_response(
                status.HTTP_200_OK,
                success=True,
                message='View recorded',
                view_count=post.view_count,
            )
        except Exception as e:
            logger.error(f'BlogViewCountView failed: {e.__class__.__name__}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-2,
                message='Something went wrong while updating views.'
            )


class ToggleSaveBlogPostView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'

    def post(self, request, post_id):
        try:
            post = BlogPost.objects.get(pk=post_id, is_visible=True)
        except BlogPost.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-1,
                message='Blog post not found'
            )
        except Exception as e:
            logger.error(f'ToggleSaveBlogPostView fetch failed: {e.__class__.__name__}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-2,
                message='Something went wrong'
            )

        try:
            if post.saved_by.filter(pk=request.user.pk).exists():
                post.saved_by.remove(request.user)
                is_saved = False
                message = 'Post removed from saved list'
            else:
                post.saved_by.add(request.user)
                is_saved = True
                message = 'Post saved'

            invalidate_cache('blog_list', request)
            invalidate_cache('blog_detail', request)
            invalidate_cache('my_saved_blog_posts', request)

            return self.build_response(
                status.HTTP_200_OK,
                success=True,
                message=message,
                is_saved=is_saved,
            )
        except Exception as e:
            logger.error(f'ToggleSaveBlogPostView failed: {e.__class__.__name__}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-2,
                message='Something went wrong'
            )


class MySavedBlogPostsView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (IsAuthenticated,)
    throttle_scope = 'main-throttle'

    @method_decorator(
        drf_cached_response(
            ttl=300,
            cache_prefix='my_saved_blog_posts',
            user_aware=True,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        try:
            posts = request.user.saved_blog_posts.select_related('author', 'category').prefetch_related('tags').filter(is_visible=True)
            serializer = BlogPostListSerializer(posts, many=True, context={'request': request})
            return self.build_response(
                status.HTTP_200_OK,
                success=True,
                message='Successful',
                posts=serializer.data,
                total=posts.count(),
            )
        except Exception as e:
            logger.error(f'MySavedBlogPostsView failed: {e.__class__.__name__}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-1,
                message='Something went wrong while fetching your saved posts.'
            )


class BlogCommentListCreateView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    @method_decorator(
        drf_cached_response(
            ttl=120,
            cache_prefix='blog_comments',
            user_aware=False,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request, post_id):
        try:
            if not BlogPost.objects.filter(pk=post_id, is_visible=True).exists():
                return self.build_response(
                    status.HTTP_404_NOT_FOUND,
                    success=False,
                    error=-1,
                    message='Blog post not found.'
                )
            comments = BlogComment.objects.select_related('user').filter(post_id=post_id, reply_to__isnull=True)
            serializer = BlogCommentSerializer(comments, many=True, context={'request': request})
            return self.build_response(
                status.HTTP_200_OK,
                success=True,
                message='Successful',
                comments=serializer.data,
                total=comments.count(),
            )
        except Exception as e:
            logger.error(f'BlogCommentListCreateView GET failed: {e.__class__.__name__}: {e}')
            return self.build_response(
                status.HTTP_500_INTERNAL_SERVER_ERROR,
                success=False,
                error=-2,
                message='Something went wrong while fetching comments.'
            )

    def post(self, request, post_id):
        if not request.user.is_authenticated:
            return self.build_response(
                status.HTTP_401_UNAUTHORIZED,
                success=False,
                error=-4,
                message='Authentication required.'
            )

        success, result = self.get_data(request, 'content')
        if not success:
            return self.build_response(
                status.HTTP_400_BAD_REQUEST,
                success=False,
                error=-1,
                message=result
            )

        content = result['content']
        if not self.validate_string_secure(content, max_length=5000, sql=True, lookup=True, injection=True):
            return self.build_response(
                status.HTTP_403_FORBIDDEN,
                success=False,
                error=-10,
                message='Insecure parameter'
            )

        reply_to_id = request.data.get('reply_to')

        try:
            post = BlogPost.objects.get(pk=post_id, is_visible=True)
        except BlogPost.DoesNotExist:
            return self.build_response(
                status.HTTP_404_NOT_FOUND,
                success=False,
                error=-1,
                message='Blog post not found.'
            )

        reply_to = None
        if reply_to_id:
            try:
                reply_to = BlogComment.objects.get(pk=reply_to_id, post=post)
            except BlogComment.DoesNotExist:
                return self.build_response(
                    status.HTTP_400_BAD_REQUEST,
                    success=False,
                    error=-2,
                    message='Invalid reply target.'
                )

        comment = BlogComment.objects.create(
            post=post,
            user=request.user,
            content=content,
            reply_to=reply_to,
        )

        invalidate_cache('blog_comments')
        invalidate_cache('blog_detail')

        serializer = BlogCommentSerializer(comment, context={'request': request})
        return self.build_response(
            status.HTTP_201_CREATED,
            success=True,
            message='Comment submitted',
            comment=serializer.data,
        )


class BlogMetaView(APIView, GetDataMixin, ResponseBuilderMixin):
    permission_classes = (AllowAny,)
    throttle_scope = 'main-throttle'

    @method_decorator(
        drf_cached_response(
            ttl=1800,
            cache_prefix='blog_meta',
            user_aware=False,
            response_codes=[200],
            cache_headers=False,
        )
    )
    def get(self, request):
        categories = BlogCategory.objects.all()
        tags = BlogTag.objects.all()
        return self.build_response(
            status.HTTP_200_OK,
            success=True,
            message='Successful',
            categories=[{'name': c.name, 'slug': c.slug} for c in categories],
            tags=[{'name': t.name, 'slug': t.slug} for t in tags],
        )

