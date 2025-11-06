import pytest

from application.services.core.rate_limit_service import RateLimitService


@pytest.mark.asyncio
async def test_rate_limiter_allows_within_limit_then_blocks():
    limiter = RateLimitService()
    user_id = 1
    per_minute = 5
    window = 60

    # Allow exactly 'per_minute' requests
    for _ in range(per_minute):
        allowed, retry_after = await limiter.enforce(user_id, per_minute, window)
        assert allowed is True
        assert retry_after == 0

    # Next request should be blocked
    allowed, retry_after = await limiter.enforce(user_id, per_minute, window)
    assert allowed is False
    assert retry_after > 0
