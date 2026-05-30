from __future__ import annotations

import hashlib
import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


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
                detail="Too many requests",
            )

        events.append(now)

    def reset(self) -> None:
        self._events.clear()


def get_client_ip(request: Request) -> str:
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    if request.client:
        return request.client.host

    return "unknown"


def stable_hash(value: str | None) -> str:
    raw = (value or "unknown").strip().lower()
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def build_rate_limit_key(
    scope: str,
    request: Request,
    subject: str | None = None,
) -> str:
    client_ip = get_client_ip(request)
    ip_hash = stable_hash(client_ip)
    subject_hash = stable_hash(subject) if subject else "none"

    return f"{scope}:ip:{ip_hash}:subject:{subject_hash}"


rate_limiter = InMemoryRateLimiter()
