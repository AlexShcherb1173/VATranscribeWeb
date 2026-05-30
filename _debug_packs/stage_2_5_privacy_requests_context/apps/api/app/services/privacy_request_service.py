from __future__ import annotations


class PrivacyRequestService:
    allowed_request_types = {'export', 'delete_account', 'delete_files', 'revoke_consent'}

    def validate_request_type(self, request_type: str) -> None:
        if request_type not in self.allowed_request_types:
            raise ValueError('Unsupported privacy request type')


privacy_request_service = PrivacyRequestService()
