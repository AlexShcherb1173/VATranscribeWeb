from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_p3_06_legal_activation_documents_exist_and_have_core_controls():
    docs = [
        "infra/legal/legal-operator-release-checklist.md",
        "infra/legal/152-fz-rkn-localization-decision.md",
        "infra/legal/processors-subprocessors-inventory.md",
        "infra/legal/legal-final-review-evidence-template.md",
        "infra/legal/privacy-terms-cookies-final-review.md",
        "docs/legal/production-legal-release-checklist.md",
        "docs/legal/152-fz-rkn-localization-decision.md",
        "docs/legal/processors-subprocessors-inventory.md",
        "docs/deployment/legal-152fz-activation.md",
        "docs/architecture/stage-4-p3-06-legal-152fz-activation.md",
    ]

    for doc in docs:
        content = read(doc)
        assert "VATranscribe" in content
        assert "DO NOT" in content
        assert "not legal advice" in content


def test_152fz_rkn_localization_decisions_are_explicit_release_blockers():
    content = read("docs/legal/152-fz-rkn-localization-decision.md")
    infra = read("infra/legal/152-fz-rkn-localization-decision.md")
    combined = content + "\n" + infra

    for marker in [
        "152-ФЗ",
        "RKN",
        "РКН",
        "Roskomnadzor",
        "Personal data localization",
        "LEGAL_152FZ_RUSSIAN_PD",
        "LEGAL_152FZ_RKN_NOTIFICATION_STATUS",
        "LEGAL_152FZ_PD_LOCALIZATION_STATUS",
        "LEGAL_CROSS_BORDER_TRANSFER_STATUS",
    ]:
        assert marker in combined

    assert "Production launch should stay blocked" in content


def test_processors_inventory_covers_core_production_providers():
    content = read("docs/legal/processors-subprocessors-inventory.md") + read(
        "infra/legal/processors-subprocessors-inventory.md"
    )

    for provider_category in [
        "Hosting",
        "Backup storage",
        "DNS/CDN",
        "Email",
        "Payment",
        "Sentry",
        "Analytics",
        "Logging",
        "Support",
    ]:
        assert provider_category in content

    assert "Cross-border transfer" in content
    assert "Privacy Policy" in content
    assert "Cookie Policy" in content


def test_privacy_terms_cookies_final_review_is_required():
    content = read("infra/legal/privacy-terms-cookies-final-review.md")

    for document in [
        "Privacy Policy",
        "User Agreement",
        "Cookie Policy",
        "Consent to personal data processing",
        "Consent to analytics/cookies",
        "Data deletion/export",
    ]:
        assert document in content

    assert "Cookie banner blocks non-essential analytics before consent" in content
    assert "Backend legal document versions match" in content


def test_p3_release_checklist_contains_legal_152fz_block():
    checklist = read("docs/release/p3-production-activation-checklist.md")

    assert "## P3-06 Legal / 152-ФЗ activation" in checklist
    assert "Real operator details are filled locally" in checklist
    assert "RKN operator notification decision is recorded" in checklist
    assert "Personal data localization decision is recorded" in checklist
    assert "Processors/subprocessors inventory is complete" in checklist
    assert "Completed legal evidence" in checklist


def test_p3_06_gitignore_blocks_legal_evidence_artifacts():
    gitignore = read(".gitignore")

    for pattern in [
        "legal-final-review-evidence*.md",
        "legal-152fz-evidence*.md",
        "operator-details*.md",
        "processors-subprocessors-inventory.completed*.md",
    ]:
        assert pattern in gitignore

def test_legal_document_versions_are_aligned_across_production_surfaces():
    config = read("apps/api/app/config.py")
    marketing = read("apps/marketing/src/config/legal.ts")
    assert 'legal_document_version: str = Field("2.0"' in config
    assert 'export const LEGAL_VERSION = "2.0";' in marketing
    for path in [
        "apps/web/src/features/auth/api/auth.ts",
        "apps/web/src/features/auth/ui/RegisterForm.tsx",
        "apps/web/src/pages/auth/api/auth.ts",
        "apps/web/src/pages/auth/ui/RegisterForm.tsx",
    ]:
        text = read(path)
        assert 'document_version: "1.0"' not in text
        assert text.count('document_version: "2.0"') >= 3
    versions_doc = read("docs/privacy/legal-document-versions.md")
    assert '`2.0`' in versions_doc
    assert '`1.0`' not in versions_doc
