import pytest
from fastapi import HTTPException

from apps.api.app.security_foundation.rate_limits import InMemoryRateLimiter


def test_rate_limiter_blocks_after_limit():
    limiter = InMemoryRateLimiter()
    limiter.check('k', limit=1, window_seconds=60)
    with pytest.raises(HTTPException):
        limiter.check('k', limit=1, window_seconds=60)
