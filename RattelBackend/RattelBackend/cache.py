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
        @drf_cached_response(ttl=3600, cache_prefix='footer')
        def list(self, request):
            return Response(data)
            
    Cache Invalidation:
        cache.delete_pattern('footer_drf_cache_*')
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
            if user_aware:
                payload['user'] = (
                    request.user.id if request.user.is_authenticated
                    else _extract_user_metadata(request)
                )
            
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
                logger.debug(
                    f'Cache HIT: {cache_key[:50]}... for {view.__qualname__}',
                    extra={'cache_key': cache_key, 'view': view.__qualname__}
                )
                
                cached_data = deepcopy(cached_response['data'])
                
                # Add cache flag to response if it's a dict
                if isinstance(cached_data, dict):
                    cached_data['restored_from_cache'] = True
                
                return Response(data=cached_data, status=cached_response['status'])
            
            # Cache miss - execute view
            logger.debug(
                f'Cache MISS: {cache_key[:50]}... for {view.__qualname__}',
                extra={'cache_key': cache_key, 'view': view.__qualname__}
            )
            
            response = view(request, *args, **kwargs)
            
            # Only cache if response status code is in allowed list
            if response.status_code not in res_codes:
                logger.debug(
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
            logger.debug(f'Cached response for {cache_key[:50]}... (TTL: {ttl}s)')
            
            return response
        return wrapper
    return decorator


# Convenience function for manual cache invalidation
def invalidate_cache(cache_prefix: str) -> int:
    """
    Invalidates all cache entries for a given prefix.
    
    Args:
        cache_prefix: The prefix used in @drf_cached_response
        
    Returns:
        int: Number of keys deleted
        
    Usage:
        invalidate_cache('footer')
        
    Note: Requires Redis backend with delete_pattern support
    """
    pattern = f'{cache_prefix}_drf_cache_*'
    
    try:
        # Redis-specific pattern deletion
        deleted = cache.delete_pattern(pattern)
        logger.info(f'Invalidated {deleted} cache keys with pattern: {pattern}')
        return deleted
    except AttributeError:
        # Fallback for non-Redis backends
        logger.warning(
            'Cache backend does not support delete_pattern. '
            'Manual invalidation required or use djagno-redis.'
        )
        return 0
