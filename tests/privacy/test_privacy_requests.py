from pathlib import Path

import pytest

from apps.api.app.services.privacy_request_service import privacy_request_service


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding='utf-8')


def test_validate_privacy_request_type_accepts_export():
    privacy_request_service.validate_request_type('export')


def test_validate_privacy_request_type_rejects_unknown():
    with pytest.raises(ValueError):
        privacy_request_service.validate_request_type('unknown')


def test_privacy_request_model_exists():
    text = read('apps/api/app/models.py')
    assert 'class PrivacyRequest(Base):' in text
    assert '__tablename__ = "privacy_requests"' in text
    assert 'request_type' in text
    assert 'processed_at' in text


def test_privacy_request_schemas_exist():
    text = read('apps/api/app/schemas.py')
    assert 'class PrivacyRequestCreate(BaseModel):' in text
    assert 'class PrivacyRequestRead(BaseModel):' in text
    assert 'class PrivacyOverviewResponse(BaseModel):' in text


def test_privacy_router_requires_current_user_and_writes_audit():
    text = read('apps/api/app/routers/privacy.py')
    assert 'Depends(get_current_user)' in text
    assert 'create_user_privacy_request' in text
    assert 'list_user_privacy_requests' in text
    assert 'privacy.request_created' in text
    assert 'record_audit_event' in text
