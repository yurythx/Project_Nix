"""
Caching System
Provides comprehensive caching utilities with multiple backends
"""
import json
import logging
import hashlib
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime, timedelta
from functools import wraps
import pickle

from django.core.cache import cache as django_cache
from django.conf import settings

logger = logging.getLogger(__name__)


class ICacheBackend(ABC):
    """Cache backend interface"""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in cache"""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete value from cache"""
        pass
    
    @abstractmethod
    def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache"""
        pass


class DjangoCacheBackend(ICacheBackend):
    """Django cache backend"""
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from Django cache"""
        try:
            return django_cache.get(key)
        except Exception as e:
            logger.error(f"Error getting cache key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in Django cache"""
        try:
            django_cache.set(key, value, timeout=timeout)
            return True
        except Exception as e:
            logger.error(f"Error setting cache key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete value from Django cache"""
        try:
            django_cache.delete(key)
            return True
        except Exception as e:
            logger.error(f"Error deleting cache key {key}: {e}")
            return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in Django cache"""
        try:
            return django_cache.get(key) is not None
        except Exception as e:
            logger.error(f"Error checking cache key {key}: {e}")
            return False
    
    def clear(self) -> bool:
        """Clear all Django cache"""
        try:
            django_cache.clear()
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False


class MemoryCacheBackend(ICacheBackend):
    """In-memory cache backend"""
    
    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from memory cache"""
        if key in self._cache:
            item = self._cache[key]
            if item['expires_at'] is None or datetime.now() < item['expires_at']:
                return item['value']
            else:
                del self._cache[key]
        return None
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None) -> bool:
        """Set value in memory cache"""
        expires_at = None
        if timeout:
            expires_at = datetime.now() + timedelta(seconds=timeout)
        
        self._cache[key] = {
            'value': value,
            'expires_at': expires_at,
            'created_at': datetime.now()
        }
        return True
    
    def delete(self, key: str) -> bool:
        """Delete value from memory cache"""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def exists(self, key: str) -> bool:
        """Check if key exists in memory cache"""
        return self.get(key) is not None
    
    def clear(self) -> bool:
        """Clear all memory cache"""
        self._cache.clear()
        return True
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return {
            'total_keys': len(self._cache),
            'expired_keys': len([k for k, v in self._cache.items() 
                               if v['expires_at'] and datetime.now() > v['expires_at']])
        }


class CacheManager:
    """Cache manager with multiple backends"""
    
    def __init__(self):
        self.backends: Dict[str, ICacheBackend] = {}
        self.default_backend = "django"
        self._setup_default_backends()
    
    def _setup_default_backends(self):
        """Setup default cache backends"""
        self.register_backend("django", DjangoCacheBackend())
        self.register_backend("memory", MemoryCacheBackend())
    
    def register_backend(self, name: str, backend: ICacheBackend) -> None:
        """Register a cache backend"""
        self.backends[name] = backend
        logger.info(f"Registered cache backend: {name}")
    
    def get_backend(self, name: Optional[str] = None) -> ICacheBackend:
        """Get cache backend by name"""
        backend_name = name or self.default_backend
        if backend_name not in self.backends:
            raise ValueError(f"Unknown cache backend: {backend_name}")
        return self.backends[backend_name]
    
    def get(self, key: str, backend_name: Optional[str] = None) -> Optional[Any]:
        """Get value from cache"""
        backend = self.get_backend(backend_name)
        return backend.get(key)
    
    def set(self, key: str, value: Any, timeout: Optional[int] = None, 
            backend_name: Optional[str] = None) -> bool:
        """Set value in cache"""
        backend = self.get_backend(backend_name)
        return backend.set(key, value, timeout)
    
    def delete(self, key: str, backend_name: Optional[str] = None) -> bool:
        """Delete value from cache"""
        backend = self.get_backend(backend_name)
        return backend.delete(key)
    
    def exists(self, key: str, backend_name: Optional[str] = None) -> bool:
        """Check if key exists in cache"""
        backend = self.get_backend(backend_name)
        return backend.exists(key)
    
    def clear(self, backend_name: Optional[str] = None) -> bool:
        """Clear cache"""
        backend = self.get_backend(backend_name)
        return backend.clear()
    
    def get_or_set(self, key: str, default_func: Callable[[], Any], 
                   timeout: Optional[int] = None, backend_name: Optional[str] = None) -> Any:
        """Get value from cache or set default if not exists"""
        backend = self.get_backend(backend_name)
        value = backend.get(key)
        if value is None:
            value = default_func()
            backend.set(key, value, timeout)
        return value
    
    def invalidate_pattern(self, pattern: str, backend_name: Optional[str] = None) -> int:
        """Invalidate all keys matching pattern (memory backend only)"""
        backend = self.get_backend(backend_name)
        if isinstance(backend, MemoryCacheBackend):
            count = 0
            keys_to_delete = [k for k in backend._cache.keys() if pattern in k]
            for key in keys_to_delete:
                if backend.delete(key):
                    count += 1
            return count
        return 0


# Global cache manager instance
cache_manager = CacheManager()


def cache_result(timeout: Optional[int] = None, key_prefix: str = "", 
                backend_name: Optional[str] = None):
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            if args:
                key_parts.append(str(hash(args)))
            if kwargs:
                key_parts.append(str(hash(frozenset(kwargs.items()))))
            
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            result = cache_manager.get(cache_key, backend_name)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, timeout, backend_name)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        return wrapper
    return decorator


def cache_method_result(timeout: Optional[int] = None, key_prefix: str = "", 
                       backend_name: Optional[str] = None):
    """Decorator to cache method results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Generate cache key including instance
            key_parts = [key_prefix, func.__name__, str(id(self))]
            if args:
                key_parts.append(str(hash(args)))
            if kwargs:
                key_parts.append(str(hash(frozenset(kwargs.items()))))
            
            cache_key = hashlib.md5(":".join(key_parts).encode()).hexdigest()
            
            # Try to get from cache
            result = cache_manager.get(cache_key, backend_name)
            if result is not None:
                logger.debug(f"Cache hit for {func.__name__}")
                return result
            
            # Execute method and cache result
            result = func(self, *args, **kwargs)
            cache_manager.set(cache_key, result, timeout, backend_name)
            logger.debug(f"Cached result for {func.__name__}")
            
            return result
        return wrapper
    return decorator


class CacheKeyGenerator:
    """Utility for generating cache keys"""
    
    @staticmethod
    def generate_key(*parts: Any, separator: str = ":") -> str:
        """Generate cache key from parts"""
        key_parts = [str(part) for part in parts if part is not None]
        return separator.join(key_parts)
    
    @staticmethod
    def generate_hash_key(*parts: Any) -> str:
        """Generate hashed cache key from parts"""
        key_string = ":".join(str(part) for part in parts if part is not None)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    @staticmethod
    def generate_model_key(model_name: str, instance_id: Any, field: str = "") -> str:
        """Generate cache key for model instance"""
        parts = ["model", model_name, str(instance_id)]
        if field:
            parts.append(field)
        return CacheKeyGenerator.generate_key(*parts)
    
    @staticmethod
    def generate_list_key(model_name: str, filters: Dict[str, Any] = None) -> str:
        """Generate cache key for model list"""
        parts = ["list", model_name]
        if filters:
            for key, value in sorted(filters.items()):
                parts.extend([key, str(value)])
        return CacheKeyGenerator.generate_key(*parts)


# Convenience functions
def get_cache(key: str, backend_name: Optional[str] = None) -> Optional[Any]:
    """Get value from cache"""
    return cache_manager.get(key, backend_name)


def set_cache(key: str, value: Any, timeout: Optional[int] = None, 
              backend_name: Optional[str] = None) -> bool:
    """Set value in cache"""
    return cache_manager.set(key, value, timeout, backend_name)


def delete_cache(key: str, backend_name: Optional[str] = None) -> bool:
    """Delete value from cache"""
    return cache_manager.delete(key, backend_name)


def cache_exists(key: str, backend_name: Optional[str] = None) -> bool:
    """Check if key exists in cache"""
    return cache_manager.exists(key, backend_name) 