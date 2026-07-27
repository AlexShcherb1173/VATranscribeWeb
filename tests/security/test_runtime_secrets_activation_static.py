from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_bytes(path: str) -> bytes:
    return (ROOT / path).read_bytes()


def test_runtime_secret_activation_scripts_exist_and_are_lf_safe():
    scripts = [
        "infra/deploy/create-runtime-env-template.sh",
        "infra/deploy/validate-runtime-env-live.sh",
        "infra/deploy/redact-runtime-env.sh",
    ]
    for script in scripts:
        content = read(script)
        data = read_bytes(script)
        assert content.startswith("#!/usr/bin/env bash")
        assert "set -euo pipefail" in content
        assert b"\r\n" not in data


def test_live_validator_wraps_production_validator_and_blocks_repo_env_file():
    content = read("infra/deploy/validate-runtime-env-live.sh")
    assert "validate-production-secrets.sh" in content
    assert "RUNTIME_ENV_FILE" in content
    assert "Runtime env file must not be inside the Git repository" in content
    assert "redact-runtime-env.sh" in content
    assert "EVIDENCE_FILE" in content


def test_redactor_never_prints_sensitive_values_raw():
    content = read("infra/deploy/redact-runtime-env.sh")
    assert "<redacted:set>" in content
    assert "SECRET" in content
    assert "DATABASE_URL" in content
    assert "SENTRY_DSN" in content
    assert "PLACEHOLDER_COUNT" in content


def test_runtime_template_generator_marks_manual_secret_filling():
    content = read("infra/deploy/create-runtime-env-template.sh")
    assert "DO NOT COMMIT" in content
    assert "<REQUIRED_SECRET>" in content
    assert "<REQUIRED_PRODUCTION_VALUE>" in content
    assert "SECRET_MANAGER_STRATEGY" in content
    assert "/opt/vatranscribe/secrets/.env.runtime" in content


def test_runtime_secret_activation_docs_and_evidence_exist():
    docs = [
        "infra/deploy/check-github-environment-secrets.md",
        "infra/security/runtime-secrets-activation-checklist.md",
        "infra/security/runtime-secrets-evidence-template.md",
        "docs/deployment/runtime-secrets-vault-activation.md",
        "docs/architecture/stage-4-p3-02-runtime-secrets-vault-activation.md",
        "docs/release/p3-production-activation-checklist.md",
    ]
    for doc in docs:
        content = read(doc)
        assert "/opt/vatranscribe/secrets/.env.runtime" in content
        assert "Do not" in content or "DO NOT" in content


def test_github_environment_secret_checklist_has_required_deploy_secrets():
    content = read("infra/deploy/check-github-environment-secrets.md")
    required = [
        "PRODUCTION_SSH_HOST",
        "PRODUCTION_SSH_USER",
        "PRODUCTION_SSH_KEY",
        "PRODUCTION_SSH_PORT",
        "PRODUCTION_PROJECT_ROOT",
        "PRODUCTION_RUNTIME_ENV_FILE",
        "PRODUCTION_SMOKE_BASE_URL",
    ]
    for name in required:
        assert name in content
    assert "production" in content


def test_gitignore_blocks_runtime_secret_outputs():
    content = read(".gitignore")
    assert ".env.runtime" in content
    assert "runtime-env*.template" in content
    assert "runtime-secrets-evidence*.md" in content
