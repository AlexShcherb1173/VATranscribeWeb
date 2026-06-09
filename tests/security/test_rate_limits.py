import pytest
from fastapi import HTTPException

from apps.api.app.security_foundation.rate_limits import (
    InMemoryRateLimiter,
    RedisBackedRateLimiter,
    get_client_ip,
    is_trusted_proxy_ip,
)


class FakePipeline:
    def __init__(self, store: dict[str, int]) -> None:
        self.store = store
        self.key: str | None = None

    def incr(self, key: str):
        self.key = key
        return self

    def expire(self, key: str, seconds: int):
        return self

    def execute(self):
        assert self.key is not None
        self.store[self.key] = self.store.get(self.key, 0) + 1
        return [self.store[self.key], True]


class FakeRedis:
    def __init__(self) -> None:
        self.store: dict[str, int] = {}

    def pipeline(self) -> FakePipeline:
        return FakePipeline(self.store)


class Client:
    def __init__(self, host: str) -> None:
        self.host = host


class RequestLike:
    def __init__(self, host: str, headers: dict[str, str] | None = None) -> None:
        self.client = Client(host)
        self.headers = headers or {}


def test_rate_limiter_blocks_after_limit():
    limiter = InMemoryRateLimiter()
    limiter.check("k", limit=1, window_seconds=60)
    with pytest.raises(HTTPException):
        limiter.check("k", limit=1, window_seconds=60)


def test_redis_rate_limiter_blocks_after_limit():
    limiter = RedisBackedRateLimiter(
        "redis://redis:6379/2",
        redis_client=FakeRedis(),
    )

    limiter.check("k", limit=1, window_seconds=60)

    with pytest.raises(HTTPException) as exc_info:
        limiter.check("k", limit=1, window_seconds=60)

    assert exc_info.value.status_code == 429


def test_untrusted_proxy_headers_are_ignored():
    request = RequestLike(
        "93.184.216.34",
        {"x-forwarded-for": "8.8.8.8"},
    )

    assert get_client_ip(request, trusted_proxy_cidrs="127.0.0.1/32") == "93.184.216.34"


def test_trusted_proxy_forwarded_for_public_ip_is_used():
    request = RequestLike(
        "172.18.0.2",
        {"x-forwarded-for": "8.8.8.8, 172.18.0.2"},
    )

    assert get_client_ip(request, trusted_proxy_cidrs="172.16.0.0/12") == "8.8.8.8"


def test_trusted_proxy_private_spoofed_forwarded_for_is_rejected():
    request = RequestLike(
        "172.18.0.2",
        {"x-forwarded-for": "127.0.0.1, 10.0.0.1"},
    )

    assert get_client_ip(request, trusted_proxy_cidrs="172.16.0.0/12") == "172.18.0.2"


def test_forwarded_header_is_used_only_from_trusted_proxy():
    request = RequestLike(
        "172.18.0.2",
        {"forwarded": 'for="8.8.4.4";proto=https;host=api.example.com'},
    )

    assert get_client_ip(request, trusted_proxy_cidrs="172.16.0.0/12") == "8.8.4.4"


def test_trusted_proxy_cidr_matching():
    assert is_trusted_proxy_ip("172.18.0.2", "172.16.0.0/12") is True
    assert is_trusted_proxy_ip("8.8.8.8", "172.16.0.0/12") is False
