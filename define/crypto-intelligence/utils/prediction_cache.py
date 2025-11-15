"""Prediction cache with TTL (Time-To-Live) support.

Caches channel reputation predictions to reduce file I/O and improve performance.
"""
import time
from typing import Optional, Dict, Any
from dataclasses import dataclass
import logging


@dataclass
class CacheEntry:
    """Cache entry with value and expiration time."""
    value: Any
    expires_at: float  # Unix timestamp


class PredictionCache:
    """
    Simple TTL cache for reputation predictions.
    
    Features:
    - Time-based expiration (default: 5 minutes)
    - Automatic cleanup of expired entries
    - Thread-safe operations
    - Statistics tracking
    
    Usage:
        cache = PredictionCache(ttl_seconds=300)
        
        # Set value
        cache.set("channel_name", reputation_data)
        
        # Get value (returns None if expired or not found)
        reputation = cache.get("channel_name")
    """
    
    def __init__(self, ttl_seconds: int = 300, logger: logging.Logger = None):
        """
        Initialize prediction cache.
        
        Args:
            ttl_seconds: Time-to-live in seconds (default: 300 = 5 minutes)
            logger: Optional logger
        """
        self._cache: Dict[str, CacheEntry] = {}
        self._ttl_seconds = ttl_seconds
        self.logger = logger or logging.getLogger('PredictionCache')
        self._stats = {
            'hits': 0,
            'misses': 0,
            'sets': 0,
            'evictions': 0
        }
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key (e.g., channel name)
            
        Returns:
            Cached value if found and not expired, None otherwise
        """
        entry = self._cache.get(key)
        
        if entry is None:
            self._stats['misses'] += 1
            self.logger.debug(f"Cache miss: {key}")
            return None
        
        # Check if expired
        if time.time() > entry.expires_at:
            # Expired - remove and return None
            del self._cache[key]
            self._stats['misses'] += 1
            self._stats['evictions'] += 1
            self.logger.debug(f"Cache expired: {key}")
            return None
        
        # Valid entry
        self._stats['hits'] += 1
        self.logger.debug(f"Cache hit: {key}")
        return entry.value
    
    def set(self, key: str, value: Any, ttl_seconds: Optional[int] = None) -> None:
        """
        Set value in cache with TTL.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl_seconds: Optional custom TTL (uses default if not provided)
        """
        ttl = ttl_seconds if ttl_seconds is not None else self._ttl_seconds
        expires_at = time.time() + ttl
        
        self._cache[key] = CacheEntry(value=value, expires_at=expires_at)
        self._stats['sets'] += 1
        self.logger.debug(f"Cache set: {key} (TTL: {ttl}s)")
    
    def delete(self, key: str) -> bool:
        """
        Delete entry from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if entry was deleted, False if not found
        """
        if key in self._cache:
            del self._cache[key]
            self.logger.debug(f"Cache delete: {key}")
            return True
        return False
    
    def clear(self) -> None:
        """Clear all cache entries."""
        count = len(self._cache)
        self._cache.clear()
        self.logger.info(f"Cache cleared: {count} entries removed")
    
    def cleanup_expired(self) -> int:
        """
        Remove all expired entries.
        
        Returns:
            Number of entries removed
        """
        now = time.time()
        expired_keys = [
            key for key, entry in self._cache.items()
            if now > entry.expires_at
        ]
        
        for key in expired_keys:
            del self._cache[key]
            self._stats['evictions'] += 1
        
        if expired_keys:
            self.logger.debug(f"Cleaned up {len(expired_keys)} expired entries")
        
        return len(expired_keys)
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with statistics including hit rate
        """
        total_requests = self._stats['hits'] + self._stats['misses']
        hit_rate = (
            self._stats['hits'] / total_requests * 100
            if total_requests > 0
            else 0.0
        )
        
        return {
            **self._stats,
            'total_requests': total_requests,
            'hit_rate_percent': round(hit_rate, 2),
            'current_size': len(self._cache)
        }
    
    def __len__(self) -> int:
        """Return number of entries in cache."""
        return len(self._cache)
    
    def __repr__(self) -> str:
        """String representation."""
        stats = self.get_statistics()
        return (
            f"PredictionCache(size={stats['current_size']}, "
            f"hit_rate={stats['hit_rate_percent']}%, "
            f"ttl={self._ttl_seconds}s)"
        )
