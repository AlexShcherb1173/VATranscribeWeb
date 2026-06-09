from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def test_legal_and_consent_models_exist():
    text = read("apps/api/app/models.py")

    assert "class LegalDocument(Base):" in text
    assert '__tablename__ = "legal_documents"' in text
    assert "class UserConsent(Base):" in text
    assert '__tablename__ = "user_consents"' in text


def test_register_request_requires_legal_acceptances():
    text = read("apps/api/app/schemas.py")

    assert "class LegalDocumentAcceptanceRequest(BaseModel):" in text
    assert "accepted_legal_documents" in text


def test_register_validates_required_consents():
    text = read("apps/api/app/routers/auth.py")

    assert "validate_required_consents" in text
    assert "record_user_consents" in text
    assert "legal.consents_accepted" in text


def test_legal_router_exposes_current_documents():
    text = read("apps/api/app/routers/legal.py")

    assert '@router.get("/documents"' in text
    assert '@router.get("/documents/current"' in text
    assert '@router.get("/documents/{document_type}/current"' in text


def test_consents_router_exposes_user_consents_and_accept_current():
    text = read("apps/api/app/routers/consents.py")

    assert '@router.get("/me"' in text
    assert '@router.post("/accept-current"' in text
