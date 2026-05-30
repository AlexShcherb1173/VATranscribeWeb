from apps.api.app.services.legal_document_service import legal_document_service


def test_normalize_document_type():
    assert legal_document_service.normalize_document_type('Privacy Policy') == 'privacy_policy'
