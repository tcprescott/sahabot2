"""In-memory per-user API rate limiter (sliding window).

NOTE: This implementation is per-process. For multi-worker deployments,
use a shared backend (e.g., Redis) and replace the storage accordingly.
"""

from __future__ import annotations

import asyncio
import time
import logging
from collections import defaultdict, deque
from typing import Deque, Dict, Tuple

logger = logging.getLogger(__name__)


class _InMemoryLimiter:
    def __init__(self) -> None:
        self._buckets: Dict[int, Deque[float]] = defaultdict(deque)
        self._locks: Dict[int, asyncio.Lock] = defaultdict(asyncio.Lock)

    async def check_and_consume(self, user_id: int, limit: int, window_seconds: int) -> Tuple[bool, float]:
        """
        Attempt to consume one request for user_id.

        Returns (allowed, retry_after_seconds).
        """
        now = time.monotonic()
        lock = self._locks[user_id]
        async with lock:
            bucket = self._buckets[user_id]
            # Evict entries outside window
            cutoff = now - window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()

            if len(bucket) < limit:
                bucket.append(now)
                return True, 0.0

            # Compute retry-after based on oldest timestamp
            oldest = bucket[0]
            retry_after = max(0.0, window_seconds - (now - oldest))
            return False, retry_after


class RateLimitService:
    """Service wrapper around the in-memory limiter."""

    def __init__(self) -> None:
        self._limiter = _InMemoryLimiter()

    async def enforce(self, user_id: int, per_minute: int, window_seconds: int) -> Tuple[bool, float]:
        return await self._limiter.check_and_consume(user_id, per_minute, window_seconds)
