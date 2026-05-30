from __future__ import annotations

import time
from collections import defaultdict, deque

from fastapi import HTTPException, status


class InMemoryRateLimiter:
    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        now = time.time()
        events = self._events[key]

        while events and events[0] <= now - window_seconds:
            events.popleft()

        if len(events) >= limit:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail='Too many requests',
            )

        events.append(now)


rate_limiter = InMemoryRateLimiter()
