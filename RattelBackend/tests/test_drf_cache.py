import pytest
from django.core.cache import cache
from rest_framework.response import Response
from RattelBackend.cache import drf_cached_response, invalidate_cache


class DummyUser:
    """Minimal user stub for authenticated / anonymous testing."""
    def __init__(self, user_id=None):
        self.id = user_id
        self.is_authenticated = user_id is not None


class DummyRequest:
    """Minimal DRF-like request object for cache tests."""
    def __init__(
            self,
            method='GET',
            path='/test/',
            data=None,
            query_params=None,
            user=None,
            meta=None,
            files=None,
    ):
        self.method = method
        self.path = path
        self.data = data or {}
        self.query_params = query_params or {}
        self.user = user or DummyUser()
        self.META = meta or {}
        self.FILES = files or {}


@pytest.fixture(autouse=True)
def clear_cache():
    """Ensure cache isolation between tests."""
    cache.clear()
    yield
    cache.clear()


class TestBasicCaching:
    """Core cache hit/miss behavior."""
    
    def test_cache_miss_then_hit(self):
        """Second identical request should hit cache and not re-execute view."""
        calls = {'count': 0}
        
        @drf_cached_response(ttl=60, cache_prefix="basic")
        def view(request):
            calls['count'] += 1
            return Response({'value': calls['count']}, status=200)
        
        request = DummyRequest()
        
        r1 = view(request)
        r2 = view(request)
        
        assert r1.data['value'] == 1
        assert r2.data['value'] == 1
        assert r2.data['restored_from_cache'] is True
        assert calls['count'] == 1
    
    def test_cache_different_query_params(self):
        """Different query params must generate different cache keys."""
        calls = {'count': 0}
        
        @drf_cached_response(ttl=60, cache_prefix='query')
        def view(request):
            calls['count'] += 1
            return Response({'value': calls['count']}, status=200)
        
        r1 = DummyRequest(query_params={'a': 1})
        r2 = DummyRequest(query_params={'a': 2})
        
        view(r1)
        view(r2)
        
        assert calls['count'] == 2


class TestUserAwareCaching:
    """User-aware cache behavior and isolation."""
    
    def test_cache_isolated_per_authenticated_user(self):
        """Each authenticated user must have an isolated cache."""
        calls = {'count': 0}
        
        @drf_cached_response(ttl=60, cache_prefix="user", user_aware=True)
        def view(request):
            calls['count'] += 1
            return Response({'value': calls['count']}, status=200)
        
        u1 = DummyRequest(user=DummyUser(1))
        u2 = DummyRequest(user=DummyUser(2))
        
        view(u1)
        view(u2)
        view(u1)
        
        assert calls['count'] == 2
    
    def test_user_aware_can_be_disabled(self):
        """Disabling user_aware should share cache between users."""
        calls = {"count": 0}
        
        @drf_cached_response(ttl=60, cache_prefix='shared', user_aware=False)
        def view(request):
            calls['count'] += 1
            return Response({'value': calls['count']}, status=200)
        
        u1 = DummyRequest(user=DummyUser(1))
        u2 = DummyRequest(user=DummyUser(2))
        
        view(u1)
        view(u2)
        
        assert calls['count'] == 1


class TestAnonymousCaching:
    """Anonymous user cache identification via IP + User-Agent."""
    
    def test_anonymous_users_cached_by_ip_and_ua(self, monkeypatch):
        """Anonymous requests with same IP/UA must share cache."""
        from RattelBackend.cache import GetDataMixin
        
        monkeypatch.setattr(
            GetDataMixin, 'get_client_ip', lambda request: '127.0.0.1'
        )
        monkeypatch.setattr(
            GetDataMixin, 'get_client_user_agent', lambda request: 'pytest-agent'
        )
        
        calls = {"count": 0}
        
        @drf_cached_response(ttl=60, cache_prefix="anon")
        def view(request):
            calls['count'] += 1
            return Response({'value': calls['count']}, status=200)
        
        r1 = DummyRequest(user=DummyUser())
        r2 = DummyRequest(user=DummyUser())
        
        view(r1)
        view(r2)
        
        assert calls['count'] == 1


class TestResponseCodes:
    """Response code filtering logic."""
    
    def test_non_cacheable_status_is_not_cached(self):
        """Responses with disallowed status codes must never be cached."""
        calls = {'count': 0}
        
        @drf_cached_response(ttl=60, cache_prefix='status', response_codes=[200])
        def view(request):
            calls['count'] += 1
            return Response({'value': calls['count']}, status=201)
        
        request = DummyRequest()
        
        view(request)
        view(request)
        
        assert calls['count'] == 2


class TestHeaderAwareCaching:
    """Cache behavior when request headers are included in key."""
    
    def test_accept_language_affects_cache_key(self):
        """Different Accept-Language headers must produce separate cache entries."""
        calls = {'count': 0}
        
        @drf_cached_response(ttl=60, cache_prefix='headers', cache_headers=True)
        def view(request):
            calls['count'] += 1
            return Response(
                {
                    'value': calls['count'],
                    'lang': request.META.get('HTTP_ACCEPT_LANGUAGE'),
                },
                status=200,
            )
        
        en = DummyRequest(meta={'HTTP_ACCEPT_LANGUAGE': 'en'})
        fa = DummyRequest(meta={'HTTP_ACCEPT_LANGUAGE': 'fa'})
        
        view(en)
        view(fa)
        view(en)
        
        assert calls['count'] == 2


class TestFileUploadBypass:
    """Ensure requests with FILES are never cached."""
    
    def test_request_with_files_skips_cache(self):
        """Requests containing FILES must bypass cache."""
        calls = {'count': 0}
        
        @drf_cached_response(ttl=60, cache_prefix='files')
        def view(request):
            calls['count'] += 1
            return Response({'value': calls['count']}, status=200)
        
        request = DummyRequest(files={'file': b'dummy'})
        
        view(request)
        view(request)
        
        assert calls['count'] == 2


class TestCacheInvalidation:
    """Global and user-specific cache invalidation."""
    
    def test_user_specific_invalidation(self):
        """Only the requesting user's cache entries should be invalidated."""
        calls = {'count': 0}
        
        @drf_cached_response(ttl=60, cache_prefix="invalidate_user")
        def view(request):
            calls['count'] += 1
            return Response({'value': calls['count']}, status=200)
        
        u1 = DummyRequest(user=DummyUser(1))
        u2 = DummyRequest(user=DummyUser(2))
        
        view(u1)
        view(u2)
        
        deleted = invalidate_cache('invalidate_user', request=u1)
        assert deleted == 1
        
        view(u1)
        view(u2)
        
        assert calls['count'] == 3
    
    def test_global_invalidation(self):
        """Global invalidation should remove all cache entries for prefix."""
        calls = {'count': 0}
        
        @drf_cached_response(ttl=60, cache_prefix='global')
        def view(request):
            calls['count'] += 1
            return Response({'value': calls['count']}, status=200)
        
        r1 = DummyRequest(user=DummyUser(1))
        r2 = DummyRequest(user=DummyUser(2))
        
        view(r1)
        view(r2)
        
        deleted = invalidate_cache('global')
        assert deleted >= 2
        
        view(r1)
        view(r2)
        
        assert calls['count'] == 4
