from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def assert_lf(path: str) -> None:
    data = (ROOT / path).read_bytes()
    assert bytes([13, 10]) not in data, f"CRLF line endings found in {path}"


def test_p3_05_live_backup_restore_scripts_exist_and_are_lf_safe():
    scripts = [
        "infra/backup/run-backup-restore-proof.sh",
        "infra/backup/validate-backup-artifacts.sh",
        "infra/backup/redact-backup-restore-report.sh",
    ]
    for script in scripts:
        content = read(script)
        assert content.startswith("#!/usr/bin/env bash")
        assert "set -euo pipefail" in content
        assert "/opt/vatranscribe/backups" in content or "backup restore" in content.lower()
        assert "Do not" in content or "DO NOT" in content
        assert_lf(script)


def test_run_backup_restore_proof_orchestrates_encrypted_backup_and_disposable_restore():
    content = read("infra/backup/run-backup-restore-proof.sh")
    assert "/opt/vatranscribe/secrets/.env.runtime" in content
    assert "/opt/vatranscribe/backups" in content
    assert "BACKUP_REQUIRE_ENCRYPTION" in content
    assert "AGE_IDENTITY_FILE" in content
    assert "backup-postgres.sh" in content
    assert "validate-backup-artifacts.sh" in content
    assert "restore-drill.sh" in content
    assert "redact-backup-restore-report.sh" in content
    assert "vatranscribe_restore_drill" in content
    assert "latest_backup_artifact" in content


def test_validate_backup_artifacts_requires_checksum_manifest_age_and_pg_restore():
    content = read("infra/backup/validate-backup-artifacts.sh")
    assert "sha256sum -c" in content
    assert '"format": "pg_dump_custom"' in content
    assert '"encrypted_with_age": true' in content
    assert "age -d" in content
    assert "pg_restore --list" in content
    assert "BACKUP_REQUIRE_ENCRYPTION" in content
    assert "BACKUP_VALIDATION_RESULT=passed" in content
    assert "BACKUP_SHA256_PREFIX" in content


def test_redact_backup_restore_report_sanitizes_generated_evidence():
    content = read("infra/backup/redact-backup-restore-report.sh")
    assert "backup-restore-proof-evidence" in content
    assert "basename" in content
    assert "<redacted>" in content
    assert "Raw backup path: <redacted>" in content
    assert "age identity file: <redacted>" in content
    assert "rclone credentials: <redacted>" in content
    assert "database password: <redacted>" in content
    assert "DO NOT commit" in content


def test_p3_05_docs_and_evidence_templates_exist():
    docs = [
        "infra/backup/backup-restore-proof-checklist.md",
        "infra/backup/backup-restore-proof-evidence-template.md",
        "docs/deployment/backup-restore-proof.md",
        "docs/architecture/stage-4-p3-05-backup-restore-proof.md",
    ]
    corpus = ""
    for doc in docs:
        content = read(doc)
        lower = content.lower()
        assert "/opt/vatranscribe/backups" in content
        assert "/opt/vatranscribe/secrets/.env.runtime" in content
        assert "do not" in lower
        corpus += "\n" + lower
    for marker in [
        "pg_dump",
        "age",
        "sha-256",
        "manifest",
        "disposable",
        "alembic_version",
        "rpo",
        "rto",
    ]:
        assert marker in corpus, f"{marker} missing from P3-05 backup restore docs"


def test_release_checklist_includes_p3_05_gate():
    content = read("docs/release/p3-production-activation-checklist.md")
    assert "## P3-05 Backup restore proof" in content
    assert "run-backup-restore-proof.sh" in content
    assert "validate-backup-artifacts.sh" in content
    assert "redact-backup-restore-report.sh" in content
    assert "backup-restore-proof-evidence" in content
    assert "P3-05 Backup restore proof." not in content


def test_gitignore_blocks_backup_restore_proof_artifacts():
    content = read(".gitignore")
    assert "backup-restore-proof-evidence*.md" in content
    assert "*.backup-proof.txt" in content
    assert "*.restore-proof.txt" in content
    assert "restore-drill-redacted*.md" in content
