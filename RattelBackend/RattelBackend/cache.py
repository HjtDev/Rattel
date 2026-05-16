from collections.abc import Iterable
from functools import wraps
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from .mixins import GetDataMixin
from json import dumps as convert_payload_to_string
from django.core.cache import cache
from copy import deepcopy
import hashlib
import logging

logger = logging.getLogger(__name__)


def _validate_cache_options(
        ttl: int,
        cache_prefix: str = None,
        user_aware: bool = True,
        response_codes: Iterable[int] = None,
        cache_headers: bool = False
):
    """
    Validates cache decorator parameters.
    
    Args:
        ttl: Time to live in seconds
        cache_prefix: Redis key prefix for cache namespace
        user_aware: Include user/IP in cache key
        response_codes: HTTP status codes to cache
        cache_headers: Include request headers in cache key
        
    Raises:
        TypeError: Invalid parameter types
        ValidationError: Invalid cache_prefix format
    """
    if not isinstance(ttl, int):
        raise TypeError('TTL must be an integer')
    
    if ttl <= 0:
        raise ValueError('TTL must be a positive integer')
    
    # Allow None for auto-generation
    if cache_prefix is not None and not GetDataMixin.validate_string_secure(
            cache_prefix, max_length=200, redis=True
    ):
        raise ValidationError('cache_prefix cannot be used as a Redis key prefix')
    
    if not isinstance(user_aware, bool):
        raise TypeError('user_aware must be a boolean')
    
    if not isinstance(cache_headers, bool):
        raise TypeError('cache_headers must be a boolean')
    
    if response_codes is not None and (
            not isinstance(response_codes, Iterable)
            or not all(isinstance(code, int) for code in response_codes)
    ):
        raise TypeError('response_codes must be an iterable of integers')


def _extract_user_metadata(request):
    """
    Extracts user identification metadata from request.
    
    Args:
        request: DRF request object
        
    Returns:
        dict: {ip_address: str, client: str}
    """
    ip_address = GetDataMixin.get_client_ip(request)
    client = GetDataMixin.get_client_user_agent(request)
    
    return {'ip_address': ip_address, 'client': client}


def _generate_cache_prefix(view):
    """
    Auto-generates cache prefix from view class and method name.
    
    Args:
        view: View function/method
        
    Returns:
        str: Generated prefix like "MyViewSet_list"
    """
    # Extract class name and method name
    qualname_parts = view.__qualname__.split('.')
    if len(qualname_parts) >= 2:
        return f"{qualname_parts[0]}_{qualname_parts[1]}"
    return view.__name__


def _get_user_identifier(request):
    """
    Gets consistent user identifier for cache key tracking.
    
    Args:
        request: DRF request object
        
    Returns:
        User ID (int) or metadata dict for anonymous users
    """
    return (
        request.user.id if request.user.is_authenticated
        else _extract_user_metadata(request)
    )


def _get_user_cache_tracking_key(user_identifier, cache_prefix):
    """
    Generates Redis key for tracking user's cache keys.
    
    Args:
        user_identifier: User ID or metadata dict
        cache_prefix: Cache prefix for the view
        
    Returns:
        str: Redis key for tracking (e.g., "user_cache_tracking:123:prefix")
    """
    user_hash = hashlib.sha256(
        convert_payload_to_string(user_identifier, sort_keys=True, default=str).encode()
    ).hexdigest()
    return f'user_cache_tracking:{user_hash}:{cache_prefix}'


def drf_cached_response(
        ttl: int,
        cache_prefix: str = None,
        user_aware: bool = True,
        response_codes: Iterable[int] = None,
        cache_headers: bool = False
):
    """
    Caches DRF view responses with flexible configuration.
    
    Args:
        ttl: Cache timeout in seconds
        cache_prefix: Redis key prefix (auto-generated if None)
        user_aware: Include user ID or IP/UA in cache key
        response_codes: Status codes to cache (default: [200])
        cache_headers: Include request headers in cache key
        
    Returns:
        Decorated view function
        
    Usage:
        @drf_cached_response(ttl=3600, cache_prefix='prefix')
        def list(self, request):
            return Response(data)
            
    Cache Invalidation:
        # Invalidate all users
        invalidate_cache('prefix')
        
        # Invalidate specific user only
        invalidate_cache('prefix', request=request)
    """
    # Auto-generate prefix if not provided
    def decorator(view):
        nonlocal cache_prefix
        if cache_prefix is None:
            cache_prefix = _generate_cache_prefix(view)
            logger.info(f'Auto-generated cache prefix: {cache_prefix}')
        
        # Validate after auto-generation
        _validate_cache_options(ttl, cache_prefix, user_aware, response_codes, cache_headers)
        
        @wraps(view)
        def wrapper(request, *args, **kwargs):
            
            # Skip caching if files are uploaded
            if hasattr(request, 'FILES') and request.FILES:
                logger.warning(
                    f'Skipped caching for {view.__qualname__}: request contains files'
                )
                return view(request, *args, **kwargs)
            
            # Default to caching only 200 OK responses
            res_codes = response_codes or [200]
            
            # Build cache key payload
            payload = {
                'view': view.__qualname__,
                'path': request.path,
                'method': request.method,
                'data': request.query_params if request.method == 'GET' else request.data
            }
            
            # Include user identification in cache key
            user_identifier = None
            if user_aware:
                user_identifier = _get_user_identifier(request)
                payload['user'] = user_identifier
            
            # Optionally include specific headers in cache key
            if cache_headers:
                # Cache common headers that affect response content
                relevant_headers = {
                    'Accept-Language': request.META.get('HTTP_ACCEPT_LANGUAGE'),
                    'Accept': request.META.get('HTTP_ACCEPT'),
                }
                payload['headers'] = relevant_headers
            
            # Generate deterministic cache key using SHA256
            raw_key = convert_payload_to_string(payload, sort_keys=True, default=str)
            key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
            cache_key = f'{cache_prefix}_drf_cache_{key_hash}'
            
            # Try to retrieve from cache
            cached_response = cache.get(cache_key)
            
            if cached_response is not None:
                # Cache hit - log and return cached data
                logger.info(
                    f'Cache HIT: {cache_key[:50]}... for {view.__qualname__}',
                    extra={'cache_key': cache_key, 'view': view.__qualname__}
                )
                
                cached_data = deepcopy(cached_response['data'])
                
                # Add cache flag to response if it's a dict
                if isinstance(cached_data, dict):
                    cached_data['restored_from_cache'] = True
                
                return Response(data=cached_data, status=cached_response['status'])
            
            # Cache miss - execute view
            logger.info(
                f'Cache MISS: {cache_key[:50]}... for {view.__qualname__}',
                extra={'cache_key': cache_key, 'view': view.__qualname__}
            )
            
            response = view(request, *args, **kwargs)
            
            # Only cache if response status code is in allowed list
            if response.status_code not in res_codes:
                logger.info(
                    f'Skipped caching: status {response.status_code} not in {res_codes}'
                )
                return response
            
            # Prepare data for caching
            data = deepcopy(response.data)
            if isinstance(data, dict):
                data['restored_from_cache'] = False
            else:
                logger.warning(
                    'Response data is not a dict; cache flag could not be appended',
                    extra={'data_type': type(response.data).__name__}
                )
            
            response_data = {
                'data': data,
                'status': response.status_code,
            }
            
            # Store in cache
            cache.set(cache_key, response_data, timeout=ttl)
            logger.info(f'Cached response for {cache_key[:50]}... (TTL: {ttl}s)')
            
            # Track cache key for user-specific invalidation
            if user_aware and user_identifier is not None:
                tracking_key = _get_user_cache_tracking_key(user_identifier, cache_prefix)
                
                # Get existing tracked keys for this user+prefix
                tracked_keys = cache.get(tracking_key, set())
                if not isinstance(tracked_keys, set):
                    tracked_keys = set()
                
                # Add new cache key to tracking
                tracked_keys.add(cache_key)
                
                # Store with same TTL as actual cache
                cache.set(tracking_key, tracked_keys, timeout=ttl)
                
                logger.info(
                    f'Tracking cache key for user invalidation: {tracking_key}'
                )
            
            return Response(data=data, status=response.status_code)
        return wrapper
    return decorator


def invalidate_cache(cache_prefix: str, request=None) -> int:
    """
    Invalidates cache entries for a given prefix.
    
    Args:
        cache_prefix: The prefix used in @drf_cached_response
        request: Optional DRF request object for user-specific invalidation
        
    Returns:
        int: Number of keys deleted
        
    Usage:
        # Invalidate all users' cache for this prefix
        invalidate_cache('prefix')
        
        # Invalidate only specific user's cache
        invalidate_cache('prefix', request=request)
        
    Note:
        - Global invalidation requires Redis backend with delete_pattern support
        - User-specific invalidation works with any cache backend
    """
    
    try:
        if request is None:
            # Global invalidation - all users
            pattern = f'{cache_prefix}_drf_cache_*'
            deleted = cache.delete_pattern(pattern)
            
            # Also clean up tracking keys
            tracking_pattern = f'user_cache_tracking:*:{cache_prefix}'
            cache.delete_pattern(tracking_pattern)
            
            logger.info(
                f'Invalidated {deleted} cache keys globally for prefix: {cache_prefix}'
            )
        else:
            # User-specific invalidation
            user_identifier = _get_user_identifier(request)
            tracking_key = _get_user_cache_tracking_key(user_identifier, cache_prefix)
            
            # Get tracked cache keys for this user
            tracked_keys = cache.get(tracking_key, set())
            
            if not tracked_keys:
                logger.info(
                    f'No cached keys found for user in prefix: {cache_prefix}'
                )
                return 0
            
            # Delete all cache keys for this user+prefix
            deleted = 0
            for cache_key in tracked_keys:
                if cache.delete(cache_key):
                    deleted += 1
            
            # Clean up tracking key itself
            cache.delete(tracking_key)
            
            logger.info(
                f'Invalidated {deleted} cache keys for user in prefix: {cache_prefix}'
            )
        
        return deleted
    
    except AttributeError:
        # Fallback for non-Redis backends (only for global invalidation)
        logger.warning(
            'Cache backend does not support delete_pattern. '
            'Use django-redis for global invalidation or provide request for user-specific.'
        )
        return 0
