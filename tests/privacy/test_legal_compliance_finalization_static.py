from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_backend_legal_documents_are_not_default_placeholders():
    text = read("apps/api/app/services/legal_document_service.py")

    assert "Default Terms of Service placeholder" not in text
    assert "Replace with final legal text before production" not in text
    assert "build_default_legal_documents" in text
    assert "LEGAL_DOCUMENT_VERSION" in read("apps/api/app/config.py")
    assert "YouTube cookies" in text
    assert "Billing and paid subscriptions are disabled" in text


def test_production_config_has_legal_guardrails():
    text = read("apps/api/app/config.py")

    assert "LEGAL_PLACEHOLDER_VALUES" in text
    assert 'legal_operator_name: str = Field("VATranscribe Operator", alias="LEGAL_OPERATOR_NAME")' in text
    assert 'legal_contact_email: str = Field("legal@example.com", alias="LEGAL_CONTACT_EMAIL")' in text
    assert 'privacy_contact_email: str = Field("privacy@example.com", alias="PRIVACY_CONTACT_EMAIL")' in text
    assert "LEGAL_OPERATOR_NAME must be a real production value" in text
    assert "must be a real monitored email" in text
    assert "LEGAL_PRODUCTION_DOMAINS must be configured in production" in text
    assert "LEGAL_152FZ_PD_LOCALIZATION_STATUS must be decided" in text


def test_env_examples_document_legal_settings():
    dev_env = read(".env.example")
    prod_env = read(".env.production.example")

    for key in [
        "LEGAL_DOCUMENT_VERSION",
        "LEGAL_OPERATOR_TYPE",
        "LEGAL_OPERATOR_NAME",
        "LEGAL_CONTACT_EMAIL",
        "PRIVACY_CONTACT_EMAIL",
        "LEGAL_TARGET_USERS",
        "LEGAL_152FZ_RUSSIAN_PD",
        "LEGAL_152FZ_RKN_NOTIFICATION_STATUS",
        "LEGAL_152FZ_PD_LOCALIZATION_STATUS",
    ]:
        assert key in dev_env
        assert key in prod_env

    assert "LEGAL_OPERATOR_NAME=VATranscribe Operator" in dev_env
    assert "LEGAL_OPERATOR_NAME=CHANGE_ME_REAL_OPERATOR_NAME" in prod_env


def test_marketing_legal_texts_are_not_labeled_as_drafts():
    for path in [
        "apps/marketing/src/config/legal.ts",
        "apps/marketing/src/config/legal.ru.ts",
        "apps/marketing/src/components/LegalDocumentLayout.astro",
    ]:
        text = read(path).lower()
        assert "draft notice" not in text
        assert "черновик" not in text
        assert "lorem" not in text
        assert "ipsum" not in text
        assert "todo" not in text
        assert "fixme" not in text
        assert "replace with final legal text before production" not in text


def test_required_registration_documents_remain_terms_privacy_personal_data():
    service = read("apps/api/app/services/legal_document_service.py")
    marketing = read("apps/marketing/src/config/legal.ts")

    assert '"terms"' in service
    assert '"privacy"' in service
    assert '"personal_data"' in service
    assert "requiredRegistrationDocumentTypes" in marketing
    assert '"terms"' in marketing
    assert '"privacy"' in marketing
    assert '"personal_data"' in marketing


def test_legal_compliance_docs_exist():
    for path in [
        "docs/legal/compliance-matrix.md",
        "docs/legal/personal-data-map.md",
        "docs/legal/152-fz-readiness.md",
        "docs/legal/legal-release-checklist.md",
    ]:
        text = read(path)
        assert "P2-01" in text
        assert "VATranscribe" in text
