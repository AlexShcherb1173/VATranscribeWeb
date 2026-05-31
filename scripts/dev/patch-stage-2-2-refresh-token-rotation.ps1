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

Write-Host "Stage 2.2: Refresh Token Rotation patch..."

# ============================================================
# 1. Patch config.py
# Robustly add refresh_token_expire_days after access_token_expire_minutes.
# ============================================================

$ConfigPath = "apps\api\app\config.py"

if (-not (Test-Path $ConfigPath)) {
    throw "File not found: $ConfigPath"
}

$ConfigLines = Get-Content -Encoding UTF8 $ConfigPath

if (($ConfigLines -join "`n") -notmatch "refresh_token_expire_days") {
    $AccessTokenLineIndex = -1

    for ($i = 0; $i -lt $ConfigLines.Count; $i++) {
        if ($ConfigLines[$i] -match "access_token_expire_minutes") {
            $AccessTokenLineIndex = $i
            break
        }
    }

    if ($AccessTokenLineIndex -lt 0) {
        throw "Could not find access_token_expire_minutes in config.py"
    }

    $Indent = ""
    if ($ConfigLines[$AccessTokenLineIndex] -match "^(\s*)") {
        $Indent = $Matches[1]
    }

    $InsertLines = @(
        "$Indent" + "refresh_token_expire_days: int = Field(",
        "$Indent" + "    30, alias=""REFRESH_TOKEN_EXPIRE_DAYS""",
        "$Indent" + ")"
    )

    $NewLines = @()

    for ($i = 0; $i -lt $ConfigLines.Count; $i++) {
        $NewLines += $ConfigLines[$i]

        if ($i -eq $AccessTokenLineIndex) {
            # If access_token_expire_minutes is a multiline Field(...), insert after its closing ")".
            $ParenBalance = 0
            $StartFound = $false

            for ($j = $AccessTokenLineIndex; $j -lt $ConfigLines.Count; $j++) {
                $line = $ConfigLines[$j]

                foreach ($ch in $line.ToCharArray()) {
                    if ($ch -eq "(") {
                        $ParenBalance++
                        $StartFound = $true
                    } elseif ($ch -eq ")") {
                        $ParenBalance--
                    }
                }

                if ($StartFound -and $ParenBalance -le 0) {
                    # Copy missing multiline lines between i+1 and j.
                    for ($k = $i + 1; $k -le $j; $k++) {
                        $NewLines += $ConfigLines[$k]
                    }

                    $NewLines += $InsertLines

                    # Skip already copied lines.
                    $i = $j
                    break
                }

                # If this is not a Field(...) multiline and there are no parentheses.
                if (-not $StartFound) {
                    $NewLines += $InsertLines
                    break
                }
            }
        }
    }

    Set-Content -Encoding UTF8 -Path $ConfigPath -Value $NewLines
}

# ============================================================
# 2. Patch models.py
# Add RefreshToken ORM model and User.refresh_tokens relationship.
# ============================================================

$ModelsPath = "apps\api\app\models.py"

if (-not (Test-Path $ModelsPath)) {
    throw "File not found: $ModelsPath"
}

$ModelsText = Get-Content -Raw -Encoding UTF8 $ModelsPath
$ModelsText = $ModelsText -replace "`r`n", "`n"

if ($ModelsText -notmatch "class RefreshToken\(Base\):") {
    $Insert = @(
        '    refresh_tokens: Mapped[list["RefreshToken"]] = relationship(',
        '        "RefreshToken",',
        '        back_populates="user",',
        '        cascade="all, delete-orphan",',
        '        foreign_keys="RefreshToken.user_id",',
        '    )',
        '',
        '',
        'class RefreshToken(Base):',
        '    __tablename__ = "refresh_tokens"',
        '',
        '    id: Mapped[str] = mapped_column(',
        '        String(36),',
        '        primary_key=True,',
        '        default=lambda: str(uuid.uuid4()),',
        '    )',
        '    user_id: Mapped[str] = mapped_column(',
        '        String(36),',
        '        ForeignKey("users.id", ondelete="CASCADE"),',
        '        nullable=False,',
        '        index=True,',
        '    )',
        '    token_hash: Mapped[str] = mapped_column(',
        '        String(128),',
        '        unique=True,',
        '        nullable=False,',
        '    )',
        '    is_revoked: Mapped[bool] = mapped_column(',
        '        Boolean,',
        '        nullable=False,',
        '        default=False,',
        '    )',
        '    created_at: Mapped[datetime] = mapped_column(',
        '        DateTime(timezone=True),',
        '        server_default=func.now(),',
        '        nullable=False,',
        '    )',
        '    expires_at: Mapped[datetime] = mapped_column(',
        '        DateTime(timezone=True),',
        '        nullable=False,',
        '    )',
        '    revoked_at: Mapped[datetime | None] = mapped_column(',
        '        DateTime(timezone=True),',
        '        nullable=True,',
        '    )',
        '',
        '    user: Mapped["User"] = relationship(',
        '        "User",',
        '        back_populates="refresh_tokens",',
        '    )',
        ''
    ) -join "`n"

    $Marker = "`n`nclass Plan(Base):"

    if ($ModelsText.Contains($Marker)) {
        $ModelsText = $ModelsText.Replace($Marker, "`n$Insert`nclass Plan(Base):")
    } else {
        throw "Could not find insertion point before class Plan(Base) in models.py"
    }

    Set-Content -Encoding UTF8 -Path $ModelsPath -Value $ModelsText
}

# ============================================================
# 3. Patch schemas.py
# TokenResponse gets refresh_token. Add request/response schemas.
# ============================================================

$SchemasPath = "apps\api\app\schemas.py"

if (-not (Test-Path $SchemasPath)) {
    throw "File not found: $SchemasPath"
}

$SchemasText = Get-Content -Raw -Encoding UTF8 $SchemasPath
$SchemasText = $SchemasText -replace "`r`n", "`n"

$OldTokenResponse = @(
    "class TokenResponse(BaseModel):",
    "    access_token: str",
    "    token_type: str = ""bearer"""
) -join "`n"

$NewTokenResponse = @(
    "class TokenResponse(BaseModel):",
    "    access_token: str",
    "    refresh_token: str | None = None",
    "    token_type: str = ""bearer""",
    "",
    "",
    "class RefreshTokenRequest(BaseModel):",
    "    refresh_token: str = Field(min_length=32, max_length=2048)",
    "",
    "",
    "class LogoutRequest(BaseModel):",
    "    refresh_token: str | None = Field(default=None, min_length=32, max_length=2048)",
    "",
    "",
    "class LogoutResponse(BaseModel):",
    "    ok: bool",
    "    detail: str"
) -join "`n"

if ($SchemasText -notmatch "class RefreshTokenRequest\(BaseModel\):") {
    if ($SchemasText.Contains($OldTokenResponse)) {
        $SchemasText = $SchemasText.Replace($OldTokenResponse, $NewTokenResponse)
    } else {
        throw "Could not find TokenResponse block in schemas.py"
    }

    Set-Content -Encoding UTF8 -Path $SchemasPath -Value $SchemasText
}

# ============================================================
# 4. Add refresh token service.
# ============================================================

Write-TextFile "apps/api/app/services/refresh_token_service.py" @(
    "from __future__ import annotations",
    "",
    "from datetime import datetime, timedelta, timezone",
    "",
    "from fastapi import HTTPException, status",
    "from sqlalchemy import select",
    "from sqlalchemy.orm import Session",
    "",
    "from apps.api.app.config import settings",
    "from apps.api.app.models import RefreshToken, User",
    "from apps.api.app.security_foundation.token_rotation import (",
    "    generate_refresh_token,",
    "    hash_refresh_token,",
    ")",
    "",
    "",
    "def utcnow() -> datetime:",
    "    return datetime.now(timezone.utc)",
    "",
    "",
    "def create_refresh_token_for_user(",
    "    db: Session,",
    "    user: User,",
    ") -> tuple[str, RefreshToken]:",
    "    raw_token = generate_refresh_token()",
    "    token_hash = hash_refresh_token(raw_token)",
    "",
    "    token_row = RefreshToken(",
    "        user_id=user.id,",
    "        token_hash=token_hash,",
    "        is_revoked=False,",
    "        expires_at=utcnow() + timedelta(days=settings.refresh_token_expire_days),",
    "    )",
    "",
    "    db.add(token_row)",
    "    db.flush()",
    "",
    "    return raw_token, token_row",
    "",
    "",
    "def get_active_refresh_token_or_401(",
    "    db: Session,",
    "    raw_token: str,",
    ") -> RefreshToken:",
    "    token_hash = hash_refresh_token(raw_token)",
    "",
    "    token_row = db.scalar(",
    "        select(RefreshToken).where(RefreshToken.token_hash == token_hash)",
    "    )",
    "",
    "    if token_row is None:",
    "        raise HTTPException(",
    "            status_code=status.HTTP_401_UNAUTHORIZED,",
    "            detail='Invalid refresh token',",
    "        )",
    "",
    "    if token_row.is_revoked:",
    "        raise HTTPException(",
    "            status_code=status.HTTP_401_UNAUTHORIZED,",
    "            detail='Refresh token has been revoked',",
    "        )",
    "",
    "    if token_row.expires_at <= utcnow():",
    "        raise HTTPException(",
    "            status_code=status.HTTP_401_UNAUTHORIZED,",
    "            detail='Refresh token has expired',",
    "        )",
    "",
    "    return token_row",
    "",
    "",
    "def rotate_refresh_token(",
    "    db: Session,",
    "    raw_token: str,",
    ") -> tuple[User, str, RefreshToken]:",
    "    old_token = get_active_refresh_token_or_401(db, raw_token)",
    "",
    "    user = db.get(User, old_token.user_id)",
    "    if user is None or not user.is_active:",
    "        raise HTTPException(",
    "            status_code=status.HTTP_401_UNAUTHORIZED,",
    "            detail='User not found or inactive',",
    "        )",
    "",
    "    old_token.is_revoked = True",
    "    old_token.revoked_at = utcnow()",
    "",
    "    new_raw_token, new_token_row = create_refresh_token_for_user(db, user)",
    "",
    "    return user, new_raw_token, new_token_row",
    "",
    "",
    "def revoke_refresh_token(",
    "    db: Session,",
    "    raw_token: str,",
    ") -> bool:",
    "    try:",
    "        token_row = get_active_refresh_token_or_401(db, raw_token)",
    "    except HTTPException:",
    "        return False",
    "",
    "    token_row.is_revoked = True",
    "    token_row.revoked_at = utcnow()",
    "    db.flush()",
    "",
    "    return True",
    "",
    "",
    "def revoke_all_user_refresh_tokens(",
    "    db: Session,",
    "    user: User,",
    ") -> int:",
    "    token_rows = list(",
    "        db.scalars(",
    "            select(RefreshToken).where(",
    "                RefreshToken.user_id == user.id,",
    "                RefreshToken.is_revoked.is_(False),",
    "            )",
    "        )",
    "    )",
    "",
    "    now = utcnow()",
    "    for token_row in token_rows:",
    "        token_row.is_revoked = True",
    "        token_row.revoked_at = now",
    "",
    "    db.flush()",
    "",
    "    return len(token_rows)"
)

# ============================================================
# 5. Replace auth.py with real refresh flow.
# ============================================================

Write-TextFile "apps/api/app/routers/auth.py" @(
    "from __future__ import annotations",
    "",
    "from fastapi import APIRouter, Depends, HTTPException, status",
    "from sqlalchemy import select",
    "from sqlalchemy.exc import IntegrityError",
    "from sqlalchemy.orm import Session",
    "",
    "from apps.api.app.database import get_db",
    "from apps.api.app.dependencies import get_current_user",
    "from apps.api.app.models import User",
    "from apps.api.app.schemas import (",
    "    LoginRequest,",
    "    LogoutRequest,",
    "    LogoutResponse,",
    "    RefreshTokenRequest,",
    "    RegisterRequest,",
    "    TokenResponse,",
    "    UserRead,",
    ")",
    "from apps.api.app.security import create_access_token",
    "from apps.api.app.services.account_bootstrap import ensure_user_profile, ensure_user_quota",
    "from apps.api.app.services.auth_service import get_password_hash, verify_password",
    "from apps.api.app.services.refresh_token_service import (",
    "    create_refresh_token_for_user,",
    "    revoke_all_user_refresh_tokens,",
    "    revoke_refresh_token,",
    "    rotate_refresh_token,",
    ")",
    "",
    "router = APIRouter(prefix='/auth', tags=['Auth'])",
    "",
    "",
    "def normalize_email(email: str) -> str:",
    "    return email.strip().lower()",
    "",
    "",
    "def ensure_account_defaults(db: Session, user: User) -> None:",
    "    try:",
    "        ensure_user_profile(db, user)",
    "        ensure_user_quota(db, user)",
    "        db.commit()",
    "    except IntegrityError:",
    "        db.rollback()",
    "        ensure_user_profile(db, user)",
    "        ensure_user_quota(db, user)",
    "        db.commit()",
    "",
    "",
    "@router.post('/register', response_model=UserRead, status_code=status.HTTP_201_CREATED)",
    "def register_user(payload: RegisterRequest, db: Session = Depends(get_db)) -> User:",
    "    email = normalize_email(payload.email)",
    "",
    "    existing_user = db.scalar(select(User).where(User.email == email))",
    "    if existing_user is not None:",
    "        raise HTTPException(",
    "            status_code=status.HTTP_409_CONFLICT,",
    "            detail='User with this email already exists.',",
    "        )",
    "",
    "    user = User(",
    "        email=email,",
    "        password_hash=get_password_hash(payload.password),",
    "        is_active=True,",
    "    )",
    "",
    "    db.add(user)",
    "",
    "    try:",
    "        db.commit()",
    "    except IntegrityError as exc:",
    "        db.rollback()",
    "        raise HTTPException(",
    "            status_code=status.HTTP_409_CONFLICT,",
    "            detail='User with this email already exists.',",
    "        ) from exc",
    "",
    "    db.refresh(user)",
    "    ensure_account_defaults(db, user)",
    "    db.refresh(user)",
    "",
    "    return user",
    "",
    "",
    "@router.post('/login', response_model=TokenResponse)",
    "def login_user(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:",
    "    email = normalize_email(payload.email)",
    "",
    "    user = db.scalar(select(User).where(User.email == email))",
    "",
    "    if user is None or not verify_password(payload.password, user.password_hash):",
    "        raise HTTPException(",
    "            status_code=status.HTTP_401_UNAUTHORIZED,",
    "            detail='Invalid email or password.',",
    "        )",
    "",
    "    if not user.is_active:",
    "        raise HTTPException(",
    "            status_code=status.HTTP_403_FORBIDDEN,",
    "            detail='User is inactive.',",
    "        )",
    "",
    "    ensure_account_defaults(db, user)",
    "    db.refresh(user)",
    "",
    "    refresh_token, _ = create_refresh_token_for_user(db, user)",
    "    db.commit()",
    "",
    "    return TokenResponse(",
    "        access_token=create_access_token(subject=str(user.id)),",
    "        refresh_token=refresh_token,",
    "        token_type='bearer',",
    "    )",
    "",
    "",
    "@router.post('/refresh', response_model=TokenResponse)",
    "def refresh_tokens(",
    "    payload: RefreshTokenRequest,",
    "    db: Session = Depends(get_db),",
    ") -> TokenResponse:",
    "    user, new_refresh_token, _ = rotate_refresh_token(db, payload.refresh_token)",
    "    db.commit()",
    "",
    "    return TokenResponse(",
    "        access_token=create_access_token(subject=str(user.id)),",
    "        refresh_token=new_refresh_token,",
    "        token_type='bearer',",
    "    )",
    "",
    "",
    "@router.post('/logout', response_model=LogoutResponse)",
    "def logout_user(",
    "    payload: LogoutRequest,",
    "    db: Session = Depends(get_db),",
    ") -> LogoutResponse:",
    "    if payload.refresh_token:",
    "        revoke_refresh_token(db, payload.refresh_token)",
    "        db.commit()",
    "",
    "    return LogoutResponse(ok=True, detail='Logged out')",
    "",
    "",
    "@router.post('/logout-all', response_model=LogoutResponse)",
    "def logout_all_user_sessions(",
    "    current_user: User = Depends(get_current_user),",
    "    db: Session = Depends(get_db),",
    ") -> LogoutResponse:",
    "    revoked_count = revoke_all_user_refresh_tokens(db, current_user)",
    "    db.commit()",
    "",
    "    return LogoutResponse(",
    "        ok=True,",
    "        detail=f'Revoked refresh tokens: {revoked_count}',",
    "    )",
    "",
    "",
    "@router.get('/me', response_model=UserRead)",
    "def read_me(current_user: User = Depends(get_current_user)) -> User:",
    "    return current_user"
)

# ============================================================
# 6. Add static tests.
# ============================================================

Write-TextFile "tests/security/test_refresh_token_rotation_static.py" @(
    "from pathlib import Path",
    "",
    "",
    "ROOT = Path(__file__).resolve().parents[2]",
    "",
    "",
    "def read(path: str) -> str:",
    "    return (ROOT / path).read_text(encoding='utf-8')",
    "",
    "",
    "def test_auth_router_has_refresh_logout_endpoints():",
    "    text = read('apps/api/app/routers/auth.py')",
    "    assert ""@router.post('/refresh'"" in text",
    "    assert ""@router.post('/logout'"" in text",
    "    assert ""@router.post('/logout-all'"" in text",
    "",
    "",
    "def test_login_returns_refresh_token():",
    "    text = read('apps/api/app/routers/auth.py')",
    "    assert 'create_refresh_token_for_user' in text",
    "    assert 'refresh_token=refresh_token' in text",
    "",
    "",
    "def test_refresh_rotates_refresh_token():",
    "    text = read('apps/api/app/services/refresh_token_service.py')",
    "    assert 'old_token.is_revoked = True' in text",
    "    assert 'create_refresh_token_for_user' in text",
    "",
    "",
    "def test_refresh_tokens_model_exists():",
    "    text = read('apps/api/app/models.py')",
    "    assert 'class RefreshToken(Base):' in text",
    "    assert '__tablename__ = ""refresh_tokens""' in text"
)

# ============================================================
# 7. Update docs.
# ============================================================

Write-TextFile "docs/security/refresh-token-rotation.md" @(
    "# Refresh Token Rotation",
    "",
    "Stage 2.2 implements refresh token rotation in the real auth flow.",
    "",
    "## Endpoints",
    "",
    "- POST /api/v1/auth/login",
    "- POST /api/v1/auth/refresh",
    "- POST /api/v1/auth/logout",
    "- POST /api/v1/auth/logout-all",
    "",
    "## Login",
    "",
    "Login returns:",
    "- access_token",
    "- refresh_token",
    "- token_type",
    "",
    "## Refresh",
    "",
    "Refresh token flow:",
    "1. Client sends refresh_token.",
    "2. API hashes token and finds active DB record.",
    "3. API rejects missing, revoked or expired tokens.",
    "4. API revokes old token.",
    "5. API creates a new refresh token.",
    "6. API returns a new access_token and refresh_token.",
    "",
    "## Logout",
    "",
    "Logout revokes the provided refresh token.",
    "",
    "## Logout all",
    "",
    "Logout all requires current access token and revokes all active refresh tokens for current user.",
    "",
    "## Storage rule",
    "",
    "Only refresh token hashes are stored in DB. Raw refresh tokens are returned only once to the client."
)

Write-Host "Stage 2.2 refresh token rotation patch completed."
Write-Host ""
Write-Host "Next:"
Write-Host "docker compose build api"
Write-Host "docker compose up -d api"
Write-Host "docker compose exec api python -m pytest tests/security tests/privacy"
Write-Host "docker compose exec api alembic upgrade head"