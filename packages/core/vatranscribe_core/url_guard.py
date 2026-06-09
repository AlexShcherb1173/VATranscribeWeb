from __future__ import annotations

import ipaddress
import re
import socket
import urllib.request
from collections.abc import Callable, Iterable
from urllib.parse import urlparse

ALLOWED_EXTERNAL_URL_SCHEMES = {"http", "https"}

BLOCKED_HOSTNAMES = {
    "localhost",
    "localhost.localdomain",
    "metadata",
    "metadata.google.internal",
}

BLOCKED_HOST_SUFFIXES = (
    ".localhost",
    ".local",
    ".internal",
    ".lan",
    ".home.arpa",
)

OBFUSCATED_NUMERIC_HOST_RE = re.compile(r"^(?:0x[0-9a-f]+|0[0-7]+|[0-9]+)$", re.IGNORECASE)
CONTROL_OR_WHITESPACE_RE = re.compile(r"[\x00-\x20\x7f]")


class UnsafeUrlError(ValueError):
    """Raised when a user-supplied URL is unsafe for outbound fetching."""


def _normalize_hostname(hostname: str | None) -> str:
    if not hostname:
        raise UnsafeUrlError("URL host is required")

    host = hostname.strip().strip("[]").rstrip(".").lower()

    if not host:
        raise UnsafeUrlError("URL host is required")

    if CONTROL_OR_WHITESPACE_RE.search(host):
        raise UnsafeUrlError("URL host contains control or whitespace characters")

    if "%" in host:
        raise UnsafeUrlError("URL host must not contain IPv6 zone identifiers")

    try:
        host = host.encode("idna").decode("ascii")
    except UnicodeError as exc:
        raise UnsafeUrlError("URL host is not a valid IDNA hostname") from exc

    return host


def _parse_ip_address(host: str) -> ipaddress.IPv4Address | ipaddress.IPv6Address | None:
    try:
        return ipaddress.ip_address(host)
    except ValueError:
        return None


def _is_blocked_ip_address(ip: ipaddress.IPv4Address | ipaddress.IPv6Address) -> bool:
    # Normalize IPv4-mapped IPv6 such as ::ffff:127.0.0.1.
    if isinstance(ip, ipaddress.IPv6Address) and ip.ipv4_mapped is not None:
        ip = ip.ipv4_mapped

    # is_global=False covers private, loopback, link-local, unspecified,
    # reserved, documentation networks, and shared address space.
    if not ip.is_global:
        return True

    if ip.is_loopback or ip.is_private or ip.is_link_local or ip.is_multicast:
        return True

    return False


def _assert_safe_host_name(host: str) -> None:
    if host in BLOCKED_HOSTNAMES:
        raise UnsafeUrlError(f"Blocked internal hostname: {host}")

    if any(host.endswith(suffix) for suffix in BLOCKED_HOST_SUFFIXES):
        raise UnsafeUrlError(f"Blocked internal hostname suffix: {host}")

    labels = host.split(".")

    if any(OBFUSCATED_NUMERIC_HOST_RE.fullmatch(label) for label in labels):
        # Reject unusual numeric host notation before DNS resolution because
        # some stacks interpret it as an IP literal, e.g. 2130706433 -> 127.0.0.1.
        if len(labels) != 4 or any(not label.isdigit() for label in labels):
            raise UnsafeUrlError(f"Blocked obfuscated numeric hostname: {host}")


def _resolved_ips_from_getaddrinfo(
    host: str,
    port: int | None,
    *,
    resolver: Callable[..., Iterable[tuple]] | None = None,
) -> set[ipaddress.IPv4Address | ipaddress.IPv6Address]:
    resolver = resolver or socket.getaddrinfo

    try:
        records = resolver(host, port or 443, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise UnsafeUrlError(f"URL host could not be resolved: {host}") from exc

    resolved: set[ipaddress.IPv4Address | ipaddress.IPv6Address] = set()

    for record in records:
        sockaddr = record[4]
        if not sockaddr:
            continue

        raw_ip = sockaddr[0]
        try:
            resolved.add(ipaddress.ip_address(raw_ip))
        except ValueError:
            raise UnsafeUrlError(f"Resolver returned invalid IP address: {raw_ip}")

    if not resolved:
        raise UnsafeUrlError(f"URL host resolved to no IP addresses: {host}")

    return resolved


def validate_external_url(
    url: str,
    *,
    resolve_dns: bool = True,
    resolver: Callable[..., Iterable[tuple]] | None = None,
) -> str:
    """Validate and normalize a user-supplied URL before outbound requests.

    The guard allows only http/https URLs whose host resolves exclusively to
    globally routable IP addresses. It rejects localhost, private networks,
    link-local networks, cloud metadata endpoints, internal schemes, userinfo,
    and ambiguous numeric host notation.
    """

    clean_url = (url or "").strip()

    if not clean_url:
        raise UnsafeUrlError("URL is required")

    if CONTROL_OR_WHITESPACE_RE.search(clean_url):
        raise UnsafeUrlError("URL contains control or whitespace characters")

    parsed = urlparse(clean_url)
    scheme = parsed.scheme.lower()

    if scheme not in ALLOWED_EXTERNAL_URL_SCHEMES:
        raise UnsafeUrlError("Only http and https URLs are allowed")

    if parsed.username or parsed.password:
        raise UnsafeUrlError("URL userinfo is not allowed")

    try:
        port = parsed.port
    except ValueError as exc:
        raise UnsafeUrlError("URL port is invalid") from exc

    host = _normalize_hostname(parsed.hostname)
    _assert_safe_host_name(host)

    ip_literal = _parse_ip_address(host)
    if ip_literal is not None:
        if _is_blocked_ip_address(ip_literal):
            raise UnsafeUrlError(f"Blocked non-public IP address: {ip_literal}")
        return clean_url

    if resolve_dns:
        resolved_ips = _resolved_ips_from_getaddrinfo(host, port, resolver=resolver)
        blocked = [str(ip) for ip in resolved_ips if _is_blocked_ip_address(ip)]
        if blocked:
            raise UnsafeUrlError(f"URL host resolves to blocked IP address(es): {', '.join(sorted(blocked))}")

    return clean_url


class SafeRedirectHandler(urllib.request.HTTPRedirectHandler):
    """Redirect handler that validates every redirect hop."""

    def __init__(self, *, max_redirects: int = 5) -> None:
        super().__init__()
        self.max_redirects = max_redirects
        self._redirect_count = 0

    def redirect_request(self, req, fp, code, msg, headers, newurl):  # type: ignore[override]
        self._redirect_count += 1

        if self._redirect_count > self.max_redirects:
            raise UnsafeUrlError(f"Too many redirects: max {self.max_redirects}")

        validate_external_url(newurl, resolve_dns=True)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


def build_safe_urllib_opener(*, max_redirects: int = 5) -> urllib.request.OpenerDirector:
    return urllib.request.build_opener(SafeRedirectHandler(max_redirects=max_redirects))
