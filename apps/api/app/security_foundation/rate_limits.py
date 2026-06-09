from __future__ import annotations

import hashlib
import ipaddress
import time
from collections import defaultdict, deque
from collections.abc import Iterable
from typing import Any

from fastapi import HTTPException, Request, status
from redis import Redis
from redis.exceptions import RedisError


class InMemoryRateLimiter:
    """Development/test fallback limiter.

    Production must use RedisBackedRateLimiter so limits are shared between API
    instances and survive process-level concurrency.
    """

    def __init__(self) -> None:
        self._events: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        if limit <= 0:
            return

        now = time.time()
        events = self._events[key]

        while events and events[0] <= now - window_seconds:
            events.popleft()

        if len(events) >= limit:
            raise_rate_limited()

        events.append(now)

    def reset(self) -> None:
        self._events.clear()


class RedisBackedRateLimiter:
    """Fixed-window Redis limiter.

    Uses atomic INCR plus EXPIRE. This is intentionally simple and predictable:
    the Nginx layer already absorbs bursts, while this API layer provides a
    distributed backstop across multiple API workers/containers.
    """

    def __init__(
        self,
        redis_url: str,
        *,
        prefix: str = "vatranscribe:rate-limit",
        fail_open: bool = False,
        redis_client: Redis | None = None,
    ) -> None:
        self.redis_url = redis_url
        self.prefix = prefix.strip(":")
        self.fail_open = fail_open
        self._redis_client = redis_client

    @property
    def redis_client(self) -> Redis:
        if self._redis_client is None:
            self._redis_client = Redis.from_url(self.redis_url, decode_responses=True)
        return self._redis_client

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        if limit <= 0:
            return

        now = int(time.time())
        window_id = now // max(window_seconds, 1)
        redis_key = f"{self.prefix}:{key}:{window_id}"

        try:
            pipe = self.redis_client.pipeline()
            pipe.incr(redis_key)
            pipe.expire(redis_key, window_seconds + 5)
            current, _ = pipe.execute()
        except RedisError as exc:
            if self.fail_open:
                return
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Rate limit backend unavailable",
            ) from exc

        if int(current) > limit:
            raise_rate_limited()


class ConfiguredRateLimiter:
    def __init__(self) -> None:
        self._memory = InMemoryRateLimiter()
        self._redis_limiters: dict[tuple[str, bool], RedisBackedRateLimiter] = {}

    def check(self, key: str, limit: int, window_seconds: int) -> None:
        settings = _get_settings()
        backend = settings.rate_limit_backend

        if backend == "redis":
            redis_url = settings.rate_limit_redis_url_resolved
            limiter_key = (redis_url, settings.rate_limit_fail_open)
            limiter = self._redis_limiters.get(limiter_key)
            if limiter is None:
                limiter = RedisBackedRateLimiter(
                    redis_url=redis_url,
                    fail_open=settings.rate_limit_fail_open,
                )
                self._redis_limiters[limiter_key] = limiter
            limiter.check(key=key, limit=limit, window_seconds=window_seconds)
            return

        self._memory.check(key=key, limit=limit, window_seconds=window_seconds)

    def reset(self) -> None:
        self._memory.reset()
        self._redis_limiters.clear()


def _get_settings() -> Any:
    from apps.api.app.config import get_settings

    return get_settings()


def raise_rate_limited() -> None:
    raise HTTPException(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        detail="Too many requests",
    )


def _split_csv(value: str | Iterable[str] | None) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [item.strip() for item in value.split(",") if item.strip()]
    return [str(item).strip() for item in value if str(item).strip()]


def _parse_ip(value: str | None) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    if not value:
        return None

    raw = value.strip().strip('"').strip("'")
    if not raw:
        return None

    if raw.startswith("[") and "]" in raw:
        raw = raw[1 : raw.index("]")]
    elif raw.count(":") == 1 and raw.rsplit(":", 1)[1].isdigit():
        raw = raw.rsplit(":", 1)[0]

    try:
        return ipaddress.ip_address(raw)
    except ValueError:
        return None


def _parse_networks(cidrs: str | Iterable[str] | None) -> list[ipaddress._BaseNetwork]:
    networks: list[ipaddress._BaseNetwork] = []
    for item in _split_csv(cidrs):
        try:
            networks.append(ipaddress.ip_network(item, strict=False))
        except ValueError:
            continue
    return networks


def is_trusted_proxy_ip(ip_value: str | None, trusted_proxy_cidrs: str | Iterable[str] | None) -> bool:
    ip = _parse_ip(ip_value)
    if ip is None:
        return False
    return any(ip in network for network in _parse_networks(trusted_proxy_cidrs))


def _is_public_forwarded_client_ip(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    return not (
        ip.is_private
        or ip.is_loopback
        or ip.is_link_local
        or ip.is_multicast
        or ip.is_reserved
        or ip.is_unspecified
    )


def _forwarded_header_candidates(value: str | None) -> list[str]:
    if not value:
        return []

    candidates: list[str] = []
    for forwarded_item in value.split(","):
        for part in forwarded_item.split(";"):
            key, sep, raw_value = part.strip().partition("=")
            if sep and key.strip().lower() == "for":
                candidates.append(raw_value.strip())
    return candidates


def _forwarded_candidates(request: Request) -> list[str]:
    candidates: list[str] = []

    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        candidates.extend(item.strip() for item in forwarded_for.split(",") if item.strip())

    real_ip = request.headers.get("x-real-ip")
    if real_ip:
        candidates.append(real_ip.strip())

    candidates.extend(_forwarded_header_candidates(request.headers.get("forwarded")))

    return candidates


def get_client_ip(
    request: Request,
    *,
    trusted_proxy_cidrs: str | Iterable[str] | None = None,
) -> str:
    direct_client_ip = request.client.host if request.client else "unknown"

    if trusted_proxy_cidrs is None:
        trusted_proxy_cidrs = _get_settings().trusted_proxy_cidrs

    if not is_trusted_proxy_ip(direct_client_ip, trusted_proxy_cidrs):
        return direct_client_ip

    for candidate in _forwarded_candidates(request):
        parsed = _parse_ip(candidate)
        if parsed is not None and _is_public_forwarded_client_ip(parsed):
            return str(parsed)

    return direct_client_ip


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


rate_limiter = ConfiguredRateLimiter()
