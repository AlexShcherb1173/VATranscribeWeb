$ErrorActionPreference = "Stop"

$Root = "D:\DevProject\PythonProject\VATranscribeWeb"

if (-not (Test-Path $Root)) {
    throw "Project root not found: $Root"
}

Set-Location $Root

function Write-TextFile {
    param(
        [string]$Path,
        [string[]]$Lines
    )

    $Parent = Split-Path $Path -Parent

    if ($Parent -and -not (Test-Path $Parent)) {
        New-Item -ItemType Directory -Force -Path $Parent | Out-Null
    }

    Set-Content -Encoding UTF8 -Path $Path -Value $Lines
}

Write-Host "Fixing Stage 2 security package conflict..."

# New package name. Do not use apps/api/app/security because security.py already exists.
New-Item -ItemType Directory -Force -Path "apps/api/app/security_foundation" | Out-Null

Write-TextFile "apps/api/app/security_foundation/__init__.py" @(
    '"""Security foundation helpers for Stage 2."""'
)

Write-TextFile "apps/api/app/security_foundation/password_policy.py" @(
    "from __future__ import annotations",
    "",
    "",
    "class PasswordPolicyError(ValueError):",
    "    pass",
    "",
    "",
    "def validate_password_strength(password: str) -> None:",
    "    if len(password) < 8:",
    "        raise PasswordPolicyError('Password must contain at least 8 characters')",
    "",
    "    if password.lower() == password:",
    "        raise PasswordPolicyError('Password must contain at least one uppercase letter')",
    "",
    "    if password.upper() == password:",
    "        raise PasswordPolicyError('Password must contain at least one lowercase letter')",
    "",
    "    if not any(ch.isdigit() for ch in password):",
    "        raise PasswordPolicyError('Password must contain at least one digit')",
    "",
    "",
    "def is_password_acceptable(password: str) -> bool:",
    "    try:",
    "        validate_password_strength(password)",
    "    except PasswordPolicyError:",
    "        return False",
    "    return True"
)

Write-TextFile "apps/api/app/security_foundation/ownership.py" @(
    "from __future__ import annotations",
    "",
    "from fastapi import HTTPException, status",
    "",
    "",
    "def assert_owner(resource_user_id: int | str, current_user_id: int | str) -> None:",
    "    if str(resource_user_id) != str(current_user_id):",
    "        raise HTTPException(",
    "            status_code=status.HTTP_404_NOT_FOUND,",
    "            detail='Resource not found',",
    "        )",
    "",
    "",
    "def is_owner(resource_user_id: int | str, current_user_id: int | str) -> bool:",
    "    return str(resource_user_id) == str(current_user_id)"
)

Write-TextFile "apps/api/app/security_foundation/rate_limits.py" @(
    "from __future__ import annotations",
    "",
    "import time",
    "from collections import defaultdict, deque",
    "",
    "from fastapi import HTTPException, status",
    "",
    "",
    "class InMemoryRateLimiter:",
    "    def __init__(self) -> None:",
    "        self._events: dict[str, deque[float]] = defaultdict(deque)",
    "",
    "    def check(self, key: str, limit: int, window_seconds: int) -> None:",
    "        now = time.time()",
    "        events = self._events[key]",
    "",
    "        while events and events[0] <= now - window_seconds:",
    "            events.popleft()",
    "",
    "        if len(events) >= limit:",
    "            raise HTTPException(",
    "                status_code=status.HTTP_429_TOO_MANY_REQUESTS,",
    "                detail='Too many requests',",
    "            )",
    "",
    "        events.append(now)",
    "",
    "",
    "rate_limiter = InMemoryRateLimiter()"
)

Write-TextFile "apps/api/app/security_foundation/token_rotation.py" @(
    "from __future__ import annotations",
    "",
    "import hashlib",
    "import secrets",
    "",
    "",
    "def generate_refresh_token() -> str:",
    "    return secrets.token_urlsafe(64)",
    "",
    "",
    "def hash_refresh_token(token: str) -> str:",
    "    return hashlib.sha256(token.encode('utf-8')).hexdigest()",
    "",
    "",
    "def verify_refresh_token_hash(token: str, token_hash: str) -> bool:",
    "    return hash_refresh_token(token) == token_hash"
)

Write-TextFile "apps/api/app/security_foundation/privacy.py" @(
    "from __future__ import annotations",
    "",
    "import hashlib",
    "",
    "",
    "def hash_ip_address(ip_address: str | None) -> str | None:",
    "    if not ip_address:",
    "        return None",
    "    return hashlib.sha256(ip_address.encode('utf-8')).hexdigest()",
    "",
    "",
    "def mask_email(email: str) -> str:",
    "    if '@' not in email:",
    "        return email",
    "    name, domain = email.split('@', 1)",
    "    if len(name) <= 2:",
    "        masked = '*' * len(name)",
    "    else:",
    "        masked = name[0] + '*' * (len(name) - 2) + name[-1]",
    "    return masked + '@' + domain"
)

# Patch router import.
Write-TextFile "apps/api/app/routers/security.py" @(
    "from __future__ import annotations",
    "",
    "from fastapi import APIRouter, Request",
    "",
    "from apps.api.app.security_foundation.rate_limits import rate_limiter",
    "",
    "",
    "router = APIRouter(prefix='/security', tags=['security'])",
    "",
    "",
    "@router.get('/ping-rate-limit')",
    "def ping_rate_limit(request: Request) -> dict[str, str]:",
    "    client = request.client.host if request.client else 'unknown'",
    "    rate_limiter.check(",
    "        key='security_ping:' + client,",
    "        limit=10,",
    "        window_seconds=60,",
    "    )",
    "    return {'status': 'ok'}"
)

# Patch tests imports.
Write-TextFile "tests/security/test_password_policy.py" @(
    "import pytest",
    "",
    "from apps.api.app.security_foundation.password_policy import PasswordPolicyError, validate_password_strength",
    "",
    "",
    "def test_password_policy_accepts_strong_password():",
    "    validate_password_strength('StrongPass123')",
    "",
    "",
    "def test_password_policy_rejects_short_password():",
    "    with pytest.raises(PasswordPolicyError):",
    "        validate_password_strength('A1b')"
)

Write-TextFile "tests/security/test_ownership.py" @(
    "import pytest",
    "from fastapi import HTTPException",
    "",
    "from apps.api.app.security_foundation.ownership import assert_owner, is_owner",
    "",
    "",
    "def test_is_owner_true():",
    "    assert is_owner(1, 1) is True",
    "",
    "",
    "def test_assert_owner_raises_for_non_owner():",
    "    with pytest.raises(HTTPException):",
    "        assert_owner(1, 2)"
)

Write-TextFile "tests/security/test_rate_limits.py" @(
    "import pytest",
    "from fastapi import HTTPException",
    "",
    "from apps.api.app.security_foundation.rate_limits import InMemoryRateLimiter",
    "",
    "",
    "def test_rate_limiter_blocks_after_limit():",
    "    limiter = InMemoryRateLimiter()",
    "    limiter.check('k', limit=1, window_seconds=60)",
    "    with pytest.raises(HTTPException):",
    "        limiter.check('k', limit=1, window_seconds=60)"
)

# Remove unused conflicting folder files if they exist.
# Do not remove apps/api/app/security.py.
$OldSecurityDir = "apps/api/app/security"
if (Test-Path $OldSecurityDir) {
    Write-Host "Removing unused directory: $OldSecurityDir"
    Remove-Item $OldSecurityDir -Recurse -Force
}

Write-Host "Security package conflict fixed."
Write-Host ""
Write-Host "Next:"
Write-Host "docker compose restart api"
Write-Host "docker compose logs api --tail=80"
Write-Host "curl http://localhost:8000/api/v1/security/ping-rate-limit"