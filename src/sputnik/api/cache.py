"""Simple in-memory caching layer for API responses."""

import time
from typing import Any, Dict, Optional, Callable
from threading import Lock


class SimpleCache:
    """Thread-safe in-memory cache with TTL support."""
    
    def __init__(self, default_ttl: int = 300):
        """
        Initialize cache.
        
        Args:
            default_ttl: Default time-to-live in seconds (default: 5 minutes)
        """
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._lock = Lock()
        self.default_ttl = default_ttl
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None if not found/expired
        """
        with self._lock:
            if key not in self._cache:
                return None
            
            entry = self._cache[key]
            if time.time() > entry["expires_at"]:
                # Expired, remove it
                del self._cache[key]
                return None
            
            return entry["value"]
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time-to-live in seconds (uses default if None)
        """
        with self._lock:
            ttl = ttl or self.default_ttl
            self._cache[key] = {
                "value": value,
                "expires_at": time.time() + ttl,
            }
    
    def delete(self, key: str) -> None:
        """Delete key from cache."""
        with self._lock:
            self._cache.pop(key, None)
    
    def clear(self) -> None:
        """Clear all cache entries."""
        with self._lock:
            self._cache.clear()
    
    def get_or_set(
        self,
        key: str,
        factory: Callable[[], Any],
        ttl: Optional[int] = None,
    ) -> Any:
        """
        Get value from cache, or set it using factory function if not found.
        
        Args:
            key: Cache key
            factory: Function to generate value if not cached
            ttl: Time-to-live in seconds
            
        Returns:
            Cached or newly generated value
        """
        value = self.get(key)
        if value is not None:
            return value
        
        value = factory()
        self.set(key, value, ttl)
        return value
    
    def size(self) -> int:
        """Get number of cache entries."""
        with self._lock:
            return len(self._cache)
    
    def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        with self._lock:
            now = time.time()
            expired_keys = [
                key for key, entry in self._cache.items()
                if now > entry["expires_at"]
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)


# Global cache instances
_schema_cache: Optional[SimpleCache] = None
_metrics_cache: Optional[SimpleCache] = None
_general_cache: Optional[SimpleCache] = None


def get_schema_cache() -> SimpleCache:
    """Get schema cache (5 minute TTL)."""
    global _schema_cache
    if _schema_cache is None:
        _schema_cache = SimpleCache(default_ttl=300)  # 5 minutes
    return _schema_cache


def get_metrics_cache() -> SimpleCache:
    """Get metrics cache (1 minute TTL)."""
    global _metrics_cache
    if _metrics_cache is None:
        _metrics_cache = SimpleCache(default_ttl=60)  # 1 minute
    return _metrics_cache


def get_general_cache() -> SimpleCache:
    """Get general cache (2 minute TTL)."""
    global _general_cache
    if _general_cache is None:
        _general_cache = SimpleCache(default_ttl=120)  # 2 minutes
    return _general_cache
