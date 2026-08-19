from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_supply_chain_evidence_scripts_exist_and_cover_required_tools():
    ps1 = read("scripts/security/run-supply-chain-evidence.ps1")
    sh = read("scripts/security/run-supply-chain-evidence.sh")

    for content in [ps1, sh]:
        assert "pip-audit" in content
        assert "npm audit" in content
        assert "trivy" in content.lower()
        assert "gitleaks" in content.lower()
        assert "syft" in content.lower()
        assert "SBOM" in content
        assert "HIGH,CRITICAL" in content or "High/Critical" in content
        assert "BLOCKED_OR_REQUIRES_TRIAGE" in content
        assert "supply-chain-evidence" in content


def test_supply_chain_redaction_scripts_exist_and_warn_against_committing_raw_reports():
    ps1 = read("scripts/security/redact-supply-chain-evidence.ps1")
    sh = read("scripts/security/redact-supply-chain-evidence.sh")

    for content in [ps1, sh]:
        assert "<redacted>" in content
        assert "DO NOT commit raw scanner outputs" in content
        assert "GITHUB_TOKEN" in content
        assert "NPM_TOKEN" in content
        assert "DATABASE_URL" in content
        assert "SENTRY_DSN" in content


def test_supply_chain_evidence_docs_exist_and_document_release_gate():
    docs = [
        "infra/security/supply-chain-evidence-checklist.md",
        "infra/security/supply-chain-evidence-template.md",
        "infra/security/vulnerability-triage-high-critical.md",
        "docs/security/supply-chain-evidence.md",
        "docs/architecture/stage-4-p3-07-supply-chain-evidence.md",
    ]

    for doc in docs:
        content = read(doc)
        assert "pip-audit" in content
        assert "npm audit" in content
        assert "Trivy" in content
        assert "Gitleaks" in content
        assert "Syft" in content
        assert "High" in content or "HIGH" in content
        assert "Critical" in content or "CRITICAL" in content
        assert "DO NOT" in content


def test_release_checklist_contains_p3_07_supply_chain_evidence():
    checklist = read("docs/release/p3-production-activation-checklist.md")

    assert "P3-07 Supply-chain evidence" in checklist
    assert "pip-audit" in checklist
    assert "npm audit --workspaces --audit-level=high" in checklist
    assert "Trivy" in checklist
    assert "Gitleaks" in checklist
    assert "Syft SBOM" in checklist
    assert "High/Critical findings" in checklist
    assert "Raw reports" in checklist


def test_gitignore_blocks_supply_chain_evidence_artifacts():
    gitignore = read(".gitignore")

    assert "/reports/security/supply-chain-evidence/" in gitignore
    assert "supply-chain-evidence*.md" in gitignore
    assert "*.pip-audit.json" in gitignore
    assert "*.npm-audit.json" in gitignore
    assert "*.trivy.json" in gitignore
    assert "*.gitleaks.json" in gitignore
    assert "*.sbom.spdx.json" in gitignore

def test_powershell_runner_propagates_native_exit_codes():
    ps1 = read("scripts/security/run-supply-chain-evidence.ps1")

    assert "$ExitCode = $LASTEXITCODE" in ps1
    assert "$NpmExit = $LASTEXITCODE" in ps1
    assert '--skip-dirs "**/node_modules"' in ps1
    assert '--skip-dirs "**/node_modules"' in read("scripts/security/run-supply-chain-evidence.sh")
    assert "--timeout 30m" in ps1
    assert "--scanners vuln,misconfig,secret" in ps1
    assert "--timeout 30m" in read("scripts/security/run-supply-chain-evidence.sh")
    assert "--scanners vuln,misconfig,secret" in read("scripts/security/run-supply-chain-evidence.sh")
    assert "| Expiry date |" in ps1
    assert "| Expiry date |" in read("scripts/security/run-supply-chain-evidence.sh")

def test_all_supply_chain_runners_use_project_mode_pip_audit():
    runners = [
        read("scripts/security/run-supply-chain-evidence.ps1"),
        read("scripts/security/run-supply-chain-evidence.sh"),
        read("scripts/security/run-supply-chain-scan.ps1"),
        read("scripts/security/run-supply-chain-scan.sh"),
    ]

    expected = "pip-audit . --strict --progress-spinner off --timeout 60"

    for content in runners:
        assert expected in content
        assert "pip-audit --local" not in content
