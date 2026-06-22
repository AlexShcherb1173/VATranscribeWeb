from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_lf(path: str) -> None:
    data = (ROOT / path).read_bytes()
    assert bytes([13, 10]) not in data, f"CRLF line endings found in {path}"


def test_p3_08_rehearsal_scripts_exist_and_are_lf_safe():
    scripts = [
        "infra/deploy/run-production-rehearsal.sh",
        "infra/deploy/validate-production-rehearsal.sh",
        "infra/deploy/redact-production-rehearsal-evidence.sh",
    ]
    for script in scripts:
        content = read(script)
        assert content.startswith("#!/usr/bin/env bash")
        assert "set -euo pipefail" in content
        assert "/opt/vatranscribe/secrets/.env.runtime" in content or "DO NOT" in content
        assert "DO NOT" in content
        assert_lf(script)


def test_run_production_rehearsal_orchestrates_release_gates():
    content = read("infra/deploy/run-production-rehearsal.sh")

    for marker in [
        "REHEARSAL_ALLOW_LIVE_ACTIONS",
        "deploy.sh",
        "python -m alembic upgrade head",
        "smoke-test.sh",
        "rollback.sh",
        "run-backup-restore-proof.sh",
        "AUTH_CHECK_RESULT",
        "FILES_CHECK_RESULT",
        "JOBS_CHECK_RESULT",
        "BILLING_CHECK_RESULT",
        "COOKIE_CHECK_RESULT",
        "ANALYTICS_CHECK_RESULT",
        "ROLLBACK_SECONDS",
        "GO_NO_GO",
    ]:
        assert marker in content

    assert "elapsed > 300" in content
    assert "PRODUCTION_REHEARSAL_RESULT" in content


def test_validate_production_rehearsal_checks_go_no_go_and_sensitive_markers():
    content = read("infra/deploy/validate-production-rehearsal.sh")

    for marker in [
        "P3_STAGE=P3-08 Production rehearsal",
        "RUNTIME_SECRETS_RESULT=PASS",
        "COMPOSE_CONFIG_RESULT=PASS",
        "SMOKE_RESULT=PASS",
        "ROLLBACK_TIMING",
        "BACKUP_RESTORE",
        "AUTH_FILES_JOBS_BILLING_COOKIE_ANALYTICS_RESULT=PASS",
        "GO_NO_GO",
    ]:
        assert marker in content

    for forbidden in [
        "super-secret-key-change-me",
        "postgres:postgres@",
        "DATABASE_URL=postgresql",
        "POSTGRES_PASSWORD=",
        "SECRET_KEY=",
        "SENTRY_DSN=http",
        "PAYMENT_API_KEY=",
    ]:
        assert forbidden in content


def test_redact_production_rehearsal_evidence_removes_common_secrets():
    content = read("infra/deploy/redact-production-rehearsal-evidence.sh")

    for marker in [
        "<redacted>",
        "DATABASE_URL=",
        "POSTGRES_PASSWORD=",
        "SECRET_KEY=",
        "SENTRY_DSN=",
        "PAYMENT_API_KEY=",
        "PAYMENT_WEBHOOK_SECRET=",
        "TELEGRAM_ALERT_BOT_TOKEN=",
        "SMTP_PASSWORD=",
        "YOUTUBE_COOKIES_ENCRYPTION_KEY=",
        "DO NOT commit",
    ]:
        assert marker in content


def test_p3_08_docs_and_final_go_no_go_checklist_exist():
    docs = [
        "infra/deploy/production-rehearsal-checklist.md",
        "infra/deploy/production-rehearsal-evidence-template.md",
        "docs/deployment/production-rehearsal.md",
        "docs/architecture/stage-4-p3-08-production-rehearsal.md",
        "docs/release/final-production-go-nogo-checklist.md",
    ]
    corpus = ""
    for doc in docs:
        content = read(doc)
        assert "DO NOT" in content
        assert "/opt/vatranscribe/secrets/.env.runtime" in content
        corpus += "\n" + content.lower()

    for marker in [
        "staging deploy",
        "migrations",
        "smoke",
        "rollback",
        "backup/restore",
        "auth",
        "files",
        "jobs",
        "billing",
        "cookie",
        "analytics",
        "go / no-go",
    ]:
        assert marker in corpus, f"{marker} missing from P3-08 docs"


def test_release_checklist_contains_p3_08_rehearsal_gate():
    content = read("docs/release/p3-production-activation-checklist.md")

    assert "## P3-08 Production rehearsal" in content
    assert "run-production-rehearsal.sh" in content
    assert "validate-production-rehearsal.sh" in content
    assert "rollback.sh" in content
    assert "300 seconds" in content
    assert "Auth checks" in content
    assert "Private files/storage checks" in content
    assert "Billing checks" in content
    assert "Analytics checks" in content
    assert "final-production-go-nogo-checklist.md" in content


def test_gitignore_blocks_production_rehearsal_evidence_artifacts():
    content = read(".gitignore")

    assert "/reports/release/production-rehearsal/" in content
    assert "production-rehearsal-evidence*.md" in content
    assert "production-rehearsal-*.raw.txt" in content
    assert "production-rehearsal-*.redacted.txt" in content
    assert "*.production-rehearsal.log" in content
