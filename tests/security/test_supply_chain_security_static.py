from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_security_scan_workflow_contains_required_scanners():
    workflow = read(".github/workflows/security-scan.yml")

    assert "name: Security Scan" in workflow
    assert "pull_request" in workflow
    assert "schedule" in workflow
    assert "pip-audit" in workflow
    assert "npm audit --workspaces --audit-level=high" in workflow
    assert "aquasecurity/trivy-action" in workflow
    assert "gitleaks/gitleaks-action" in workflow
    assert "anchore/sbom-action" in workflow
    assert "HIGH,CRITICAL" in workflow


def test_dependabot_covers_core_ecosystems():
    config = read(".github/dependabot.yml")

    assert "package-ecosystem: \"github-actions\"" in config
    assert "package-ecosystem: \"pip\"" in config
    assert "package-ecosystem: \"npm\"" in config
    assert "package-ecosystem: \"docker\"" in config
    assert "directory: \"/apps/web\"" in config
    assert "directory: \"/apps/marketing\"" in config
    assert "interval: \"weekly\"" in config


def test_local_supply_chain_scan_scripts_exist():
    ps1 = read("scripts/security/run-supply-chain-scan.ps1")
    sh = read("scripts/security/run-supply-chain-scan.sh")
    lock_ps1 = read("scripts/security/check-lockfiles.ps1")
    lock_sh = read("scripts/security/check-lockfiles.sh")

    for content in [ps1, sh]:
        assert "pip-audit" in content
        assert "npm audit" in content
        assert "trivy" in content.lower()
        assert "gitleaks" in content.lower()
        assert "syft" in content.lower()

    assert "package-lock.json" in lock_ps1
    assert "package-lock.json" in lock_sh
    assert "pyproject.toml" in lock_ps1
    assert "pyproject.toml" in lock_sh


def test_supply_chain_policy_documents_release_gate():
    policy = read("infra/security/supply-chain-policy.md")
    triage = read("infra/security/vulnerability-triage.md")
    release_gate = read("docs/release/security-release-gate.md")
    sbom = read("infra/security/sbom.md")
    secret = read("infra/security/secret-scanning.md")

    assert "Critical" in policy
    assert "High" in policy
    assert "block" in policy.lower()
    assert "Medium" in triage
    assert "manual review" in triage.lower()
    assert "SBOM" in sbom
    assert "Gitleaks" in secret
    assert "Production release is blocked" in release_gate


def test_gitleaks_config_exists_with_safe_allowlist_scope():
    config = read(".gitleaks.toml")

    assert "useDefault = true" in config
    assert ".env.example" in config
    assert ".env.production.example" in config
    assert "not-a-real-secret" in config
