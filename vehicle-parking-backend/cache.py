import time
from functools import wraps
from flask import request, jsonify, make_response

class SimpleCache:
    """Thread-safe in-memory cache with TTL expiry and key/prefix invalidation"""
    def __init__(self, default_timeout=60):
        self.default_timeout = default_timeout
        self._cache = {}
        self.stats = {'hits': 0, 'misses': 0}

    def get(self, key):
        if key in self._cache:
            value, expiry = self._cache[key]
            if expiry is None or time.time() < expiry:
                self.stats['hits'] += 1
                return value
            else:
                del self._cache[key]
        self.stats['misses'] += 1
        return None

    def set(self, key, value, timeout=None):
        if timeout is None:
            timeout = self.default_timeout
        expiry = time.time() + timeout if timeout > 0 else None
        self._cache[key] = (value, expiry)

    def delete(self, key):
        self._cache.pop(key, None)

    def invalidate_prefix(self, prefix):
        keys_to_delete = [k for k in self._cache if k.startswith(prefix)]
        for k in keys_to_delete:
            self._cache.pop(k, None)

    def clear(self):
        self._cache.clear()

cache = SimpleCache(default_timeout=60)

def cached(timeout=60, key_prefix="view"):
    """Decorator to cache Flask view response with TTL and custom headers"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Include query params in cache key
            query_str = request.query_string.decode('utf-8')
            cache_key = f"{key_prefix}:{request.path}?{query_str}"
            
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                response = make_response(jsonify(cached_data))
                response.headers['X-Cache'] = 'HIT'
                response.headers['X-Cache-TTL'] = str(timeout)
                return response
            
            # Execute endpoint
            result = f(*args, **kwargs)
            
            # Handle tuple response (response_data, status_code)
            if isinstance(result, tuple):
                data, status_code = result[0], result[1]
            else:
                data, status_code = result, 200
                
            if status_code == 200 and hasattr(data, 'get_json'):
                json_data = data.get_json()
                cache.set(cache_key, json_data, timeout=timeout)
                response = make_response(jsonify(json_data), status_code)
                response.headers['X-Cache'] = 'MISS'
                response.headers['X-Cache-TTL'] = str(timeout)
                return response
                
            return result
        return decorated_function
    return decorator

