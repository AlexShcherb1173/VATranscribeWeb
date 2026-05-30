import pytest

from apps.api.app.services.privacy_request_service import privacy_request_service


def test_validate_privacy_request_type_accepts_export():
    privacy_request_service.validate_request_type('export')


def test_validate_privacy_request_type_rejects_unknown():
    with pytest.raises(ValueError):
        privacy_request_service.validate_request_type('unknown')
