from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_user_admin_flag_and_2fa_models_exist():
    models = read("apps/api/app/models.py")
    assert "is_admin: Mapped[bool]" in models
    assert "class AdminTwoFactor" in models
    assert "class AdminRecoveryCode" in models
    assert "encrypted_totp_secret" in models
    assert "encrypted_pending_totp_secret" in models
    assert "code_hash" in models


def test_admin_2fa_router_is_registered():
    init = read("apps/api/app/routers/__init__.py")
    router = read("apps/api/app/routers/admin_security.py")
    assert "admin_security_router" in init
    assert "router.include_router(admin_security_router)" in init
    assert "APIRouter(prefix=\"/admin/security\"" in router
    assert "/2fa/setup" in router
    assert "/2fa/confirm" in router
    assert "/2fa/disable" in router
    assert "/2fa/recovery-codes/rotate" in router
    assert "Depends(require_admin_user)" in router
    assert "Depends(require_admin_2fa)" in router


def test_admin_dependencies_enforce_role_and_2fa():
    deps = read("apps/api/app/dependencies.py")
    assert "def require_admin_user" in deps
    assert "is_admin" in deps
    assert "Admin access required" in deps
    assert "def require_admin_2fa" in deps
    assert "is_admin_2fa_enabled" in deps
    assert "Admin two-factor authentication is required" in deps


def test_totp_service_uses_standard_hmac_and_hashed_recovery_codes():
    service = read("apps/api/app/services/admin_2fa_service.py")
    assert "hmac.new" in service
    assert "hashlib.sha1" in service
    assert "otpauth://totp/" in service
    assert "pbkdf2_hmac" in service
    assert "consume_recovery_code" in service
    assert "cryptography.fernet" in service


def test_admin_2fa_production_settings_are_guarded():
    config = read("apps/api/app/config.py")
    env_prod = read(".env.production.example")
    assert "ADMIN_2FA_REQUIRED" in config
    assert "ADMIN_2FA_ISSUER" in config
    assert "ADMIN_2FA_REQUIRED must be true in production" in config
    assert "ADMIN_2FA_ISSUER must be a real production value" in config
    assert "ADMIN_2FA_REQUIRED=true" in env_prod


def test_admin_2fa_migration_exists():
    migration = read("alembic/versions/20260610_0002_admin_2fa.py")
    assert "down_revision" in migration and "20260609_0001" in migration
    assert "op.add_column" in migration and "is_admin" in migration
    assert "admin_two_factor" in migration
    assert "admin_recovery_codes" in migration


def test_admin_2fa_docs_exist():
    doc = read("docs/security/admin-2fa.md")
    arch = read("docs/architecture/stage-4-p2-02-admin-2fa.md")
    assert "TOTP" in doc
    assert "recovery codes" in doc.lower()
    assert "require_admin_2fa" in arch
    assert "P2-02" in arch
