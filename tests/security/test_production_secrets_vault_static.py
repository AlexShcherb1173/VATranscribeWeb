from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_secret_manager_settings_exist_in_config():
    text = read("apps/api/app/config.py")
    assert "SECRET_MANAGER_STRATEGY" in text
    assert "RUNTIME_ENV_FILE" in text
    assert "PRODUCTION_SECRETS_VALIDATION_REQUIRED" in text
    assert "PRODUCTION_SECRET_MANAGER_STRATEGIES" in text
    assert "local-env" in text
    assert "runtime-env-file" in text
    assert "DATABASE_URL must not contain placeholder" in text


def test_runtime_env_validation_script_blocks_placeholders():
    text = read("infra/deploy/validate-production-secrets.sh")
    assert "APP_ENV must be production" in text
    assert "SECRET_MANAGER_STRATEGY" in text
    assert "RUNTIME_ENV_FILE" in text
    assert "SECRET_KEY" in text
    assert "DATABASE_URL" in text
    assert "POSTGRES_PASSWORD" in text
    assert "YOUTUBE_COOKIES_ENCRYPTION_KEY" in text
    assert "CHANGE_ME" in text
    assert "postgres:postgres" in text
    assert "RATE_LIMIT_REDIS_FAIL_OPEN" in text
    assert "ADMIN_2FA_REQUIRED" in text


def test_runtime_env_render_script_has_inventory_and_secure_permissions():
    text = read("infra/deploy/render-runtime-env.sh")
    assert "umask 077" in text
    assert "install -m 600" in text
    assert "Yandex Lockbox" in text
    assert "Doppler" in text
    assert "HashiCorp Vault" in text
    assert "PAYMENT_WEBHOOK_SECRET" in text
    assert "BACKUP_ENCRYPTION_RECIPIENT" in text


def test_deploy_and_rollback_validate_secrets_before_compose():
    for path in ("infra/deploy/deploy.sh", "infra/deploy/rollback.sh"):
        text = read(path)
        assert "validate-production-secrets.sh" in text
        assert "RUNTIME_ENV_FILE" in text
        assert "--env-file" in text
        assert "ln -sfn" in text


def test_github_actions_uses_production_runtime_env_file_secret():
    text = read(".github/workflows/production-deploy.yml")
    assert "PRODUCTION_RUNTIME_ENV_FILE" in text
    assert "Git ref/tag/branch to deploy" in text
    assert "run_deploy" in text


def test_env_templates_document_secret_strategy():
    for path in (".env.example", ".env.production.example"):
        text = read(path)
        assert "SECRET_MANAGER_STRATEGY" in text
        assert "RUNTIME_ENV_FILE" in text
        assert "PRODUCTION_SECRETS_VALIDATION_REQUIRED" in text
        assert "SECRET_ROTATION_POLICY_VERSION" in text
    prod = read(".env.production.example")
    assert "POSTGRES_PASSWORD" in prod
    assert "BACKUP_ENCRYPTION_RECIPIENT" in prod
    assert "PAYMENT_WEBHOOK_SECRET" in prod


def test_secret_docs_exist():
    for path in (
        "infra/security/secrets-inventory.md",
        "infra/security/secrets.vault-policy.md",
        "infra/security/secrets.rotation.md",
        "docs/security/production-secrets-vault.md",
        "docs/architecture/stage-4-p2-03-production-secrets-vault.md",
    ):
        text = read(path)
        assert "production" in text.lower()
        assert "secret" in text.lower()
