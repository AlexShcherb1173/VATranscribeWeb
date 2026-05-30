from apps.api.app.services.consent_service import consent_service


def test_build_consent_record():
    record = consent_service.build_consent_record(
        user_id=1,
        document_type='privacy',
        document_version='1.0',
    )
    assert record['user_id'] == 1
    assert record['accepted'] is True
