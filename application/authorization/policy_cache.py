"""
Policy evaluation result caching.

Caches the results of policy evaluations to improve performance.
Cache is invalidated when:
- User roles change
- Role policies change
- Direct user policies change
- Organization membership changes
"""

import logging
from typing import Optional
from datetime import datetime, timedelta, timezone

logger = logging.getLogger(__name__)


class PolicyCache:
    """
    In-memory cache for policy evaluation results.
    
    Cache key format: "user:{user_id}:org:{org_id}:action:{action}:resource:{resource}"
    
    Future: Replace with Redis for production use.
    """
    
    def __init__(self, ttl_seconds: int = 300):
        """
        Initialize the PolicyCache.
        
        Args:
            ttl_seconds: Time-to-live for cache entries in seconds (default 5 minutes)
        """
        self._cache = {}  # dict[str, tuple[bool, datetime]]
        self._ttl_seconds = ttl_seconds
        logger.info("PolicyCache initialized with TTL=%s seconds", ttl_seconds)
    
    def get(
        self,
        user_id: int,
        organization_id: int,
        action: str,
        resource: str
    ) -> Optional[bool]:
        """
        Get cached evaluation result.
        
        Args:
            user_id: User ID
            organization_id: Organization ID
            action: Action being performed
            resource: Resource being accessed
        
        Returns:
            Cached result (True/False) if found and not expired, None otherwise
        """
        key = self._make_key(user_id, organization_id, action, resource)
        
        if key not in self._cache:
            return None
        
        result, expires_at = self._cache[key]
        
        # Check if expired
        if datetime.now(timezone.utc) > expires_at:
            del self._cache[key]
            logger.debug("Cache miss (expired): %s", key)
            return None
        
        logger.debug("Cache hit: %s -> %s", key, result)
        return result
    
    def set(
        self,
        user_id: int,
        organization_id: int,
        action: str,
        resource: str,
        result: bool
    ) -> None:
        """
        Store evaluation result in cache.
        
        Args:
            user_id: User ID
            organization_id: Organization ID
            action: Action being performed
            resource: Resource being accessed
            result: Evaluation result (True/False)
        """
        key = self._make_key(user_id, organization_id, action, resource)
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=self._ttl_seconds)
        
        self._cache[key] = (result, expires_at)
        logger.debug("Cache set: %s -> %s (expires at %s)", key, result, expires_at)
    
    def invalidate_user(self, user_id: int) -> None:
        """
        Invalidate all cache entries for a user.
        
        Call this when:
        - User's roles change
        - User's direct policies change
        - User joins/leaves an organization
        
        Args:
            user_id: User ID to invalidate
        """
        user_prefix = f"user:{user_id}:"
        keys_to_delete = [k for k in self._cache.keys() if k.startswith(user_prefix)]
        
        for key in keys_to_delete:
            del self._cache[key]
        
        logger.info("Invalidated %s cache entries for user %s", len(keys_to_delete), user_id)
    
    def invalidate_organization(self, organization_id: int) -> None:
        """
        Invalidate all cache entries for an organization.
        
        Call this when:
        - Organization roles change
        - Organization role policies change
        
        Args:
            organization_id: Organization ID to invalidate
        """
        org_prefix = f"org:{organization_id}:"
        keys_to_delete = [k for k in self._cache.keys() if org_prefix in k]
        
        for key in keys_to_delete:
            del self._cache[key]
        
        logger.info(
            "Invalidated %s cache entries for organization %s",
            len(keys_to_delete),
            organization_id
        )
    
    def invalidate_role(self, organization_id: int, role_name: str) -> None:
        """
        Invalidate cache entries affected by a role change.
        
        Call this when:
        - Role policies are modified
        - Role is deleted
        
        Args:
            organization_id: Organization ID
            role_name: Name of role that changed
        """
        # For simplicity, invalidate entire organization
        # Future: Track which users have which roles for more granular invalidation
        self.invalidate_organization(organization_id)
        logger.info(
            "Invalidated cache for organization %s due to role '%s' change",
            organization_id,
            role_name
        )
    
    def clear(self) -> None:
        """Clear entire cache."""
        count = len(self._cache)
        self._cache.clear()
        logger.info("Cleared entire cache (%s entries)", count)
    
    def get_stats(self) -> dict:
        """
        Get cache statistics.
        
        Returns:
            Dict with cache stats (entry count, expired count, etc.)
        """
        total_entries = len(self._cache)
        now = datetime.now(timezone.utc)
        expired_entries = sum(
            1 for _, expires_at in self._cache.values()
            if now > expires_at
        )
        
        return {
            "total_entries": total_entries,
            "active_entries": total_entries - expired_entries,
            "expired_entries": expired_entries,
            "ttl_seconds": self._ttl_seconds,
        }
    
    def _make_key(
        self,
        user_id: int,
        organization_id: int,
        action: str,
        resource: str
    ) -> str:
        """
        Generate cache key.
        
        Args:
            user_id: User ID
            organization_id: Organization ID
            action: Action
            resource: Resource
        
        Returns:
            Cache key string
        """
        return f"user:{user_id}:org:{organization_id}:action:{action}:resource:{resource}"


# Global cache instance
# Future: Replace with Redis for production multi-process support
_global_cache: Optional[PolicyCache] = None


def get_cache() -> PolicyCache:
    """
    Get or create global PolicyCache instance.
    
    Returns:
        PolicyCache instance
    """
    global _global_cache
    if _global_cache is None:
        _global_cache = PolicyCache()
    return _global_cache


def invalidate_user_cache(user_id: int) -> None:
    """
    Convenience function to invalidate user cache.
    
    Args:
        user_id: User ID
    """
    cache = get_cache()
    cache.invalidate_user(user_id)


def invalidate_organization_cache(organization_id: int) -> None:
    """
    Convenience function to invalidate organization cache.
    
    Args:
        organization_id: Organization ID
    """
    cache = get_cache()
    cache.invalidate_organization(organization_id)


def invalidate_role_cache(organization_id: int, role_name: str) -> None:
    """
    Convenience function to invalidate role cache.
    
    Args:
        organization_id: Organization ID
        role_name: Role name
    """
    cache = get_cache()
    cache.invalidate_role(organization_id, role_name)
