from __future__ import annotations

import socket

import pytest

from packages.core.vatranscribe_core.url_guard import UnsafeUrlError, validate_external_url


@pytest.mark.parametrize(
    "url",
    [
        "",
        "file:///etc/passwd",
        "ftp://example.com/file.mp4",
        "gopher://example.com/_x",
        "http://localhost/video.mp4",
        "http://localhost.localdomain/video.mp4",
        "http://metadata.google.internal/computeMetadata/v1/",
        "http://127.0.0.1/video.mp4",
        "http://127.1/video.mp4",
        "http://0.0.0.0/video.mp4",
        "http://10.0.0.1/video.mp4",
        "http://172.16.0.1/video.mp4",
        "http://192.168.1.10/video.mp4",
        "http://169.254.169.254/latest/meta-data/",
        "http://[::1]/video.mp4",
        "http://[fe80::1]/video.mp4",
        "http://[fc00::1]/video.mp4",
        "http://2130706433/video.mp4",
        "https://user:password@example.com/video.mp4",
    ],
)
def test_validate_external_url_blocks_internal_or_unsafe_urls_without_dns(url: str) -> None:
    with pytest.raises(UnsafeUrlError):
        validate_external_url(url, resolve_dns=False)


def test_validate_external_url_allows_external_http_https_without_dns() -> None:
    assert validate_external_url("https://example.com/video.mp4", resolve_dns=False) == "https://example.com/video.mp4"
    assert validate_external_url("http://example.com/video.mp4", resolve_dns=False) == "http://example.com/video.mp4"


def test_validate_external_url_blocks_dns_rebinding_to_private_ip() -> None:
    def resolver(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.5", 443))]

    with pytest.raises(UnsafeUrlError):
        validate_external_url("https://attacker.example/video.mp4", resolver=resolver)


def test_validate_external_url_allows_dns_to_public_ip() -> None:
    def resolver(*args, **kwargs):
        return [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443))]

    assert validate_external_url("https://cdn.example/video.mp4", resolver=resolver) == "https://cdn.example/video.mp4"


def test_validate_external_url_blocks_if_any_dns_answer_is_private() -> None:
    def resolver(*args, **kwargs):
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("8.8.8.8", 443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", ("127.0.0.1", 443)),
        ]

    with pytest.raises(UnsafeUrlError):
        validate_external_url("https://mixed.example/video.mp4", resolver=resolver)
