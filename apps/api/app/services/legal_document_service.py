from __future__ import annotations

from datetime import datetime, timezone
from textwrap import dedent

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.orm import Session

from apps.api.app.config import Settings, get_settings
from apps.api.app.models import LegalDocument

REQUIRED_LEGAL_DOCUMENT_TYPES: tuple[str, ...] = (
    "terms",
    "privacy",
    "personal_data",
)

OPTIONAL_LEGAL_DOCUMENT_TYPES: tuple[str, ...] = (
    "cookies",
    "refund",
)

ALL_LEGAL_DOCUMENT_TYPES: tuple[str, ...] = (
    *REQUIRED_LEGAL_DOCUMENT_TYPES,
    *OPTIONAL_LEGAL_DOCUMENT_TYPES,
)


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def normalize_document_type(document_type: str) -> str:
    return document_type.strip().lower().replace(" ", "_").replace("-", "_")


def _as_yes_no(value: bool) -> str:
    return "yes" if value else "no"


def _operator_block(settings: Settings) -> str:
    return dedent(
        f"""
        Operator:
        - Type: {settings.legal_operator_type}
        - Name: {settings.legal_operator_name}
        - INN: {settings.legal_operator_inn or "not specified for pre-release"}
        - OGRN/OGRNIP: {settings.legal_operator_ogrn or "not specified for pre-release"}
        - Address: {settings.legal_operator_address or "not specified for pre-release"}
        - Legal contact: {settings.legal_contact_email}
        - Privacy contact: {settings.privacy_contact_email}
        - Support contact: {settings.support_email}
        - Production domains: {settings.legal_production_domains}
        """
    ).strip()


def _processors_block(settings: Settings) -> str:
    return dedent(
        f"""
        Processors and third-party services:
        - Hosting provider: {settings.legal_hosting_provider}
        - CDN provider: {settings.legal_cdn_provider}
        - Analytics provider: {settings.legal_analytics_provider}
        - APM/monitoring provider: {settings.legal_apm_provider}
        - Payment provider: {settings.legal_payment_provider}
        - Email provider: {settings.legal_email_provider}
        - Main database country: {settings.legal_main_db_country}
        - Backup country: {settings.legal_backup_country}
        """
    ).strip()


def _retention_block(settings: Settings) -> str:
    return dedent(
        f"""
        Retention:
        - Uploaded/downloaded media: {settings.media_asset_retention_days} days by default or until user deletion.
        - Export artifacts: {settings.export_artifact_retention_days} days by default or until user deletion.
        - Transcripts: {settings.transcript_retention_days} days by default or until user deletion.
        - Temporary files: {settings.temp_file_retention_hours} hours.
        - Failed job files: {settings.failed_job_file_retention_days} days.
        - Audit/security logs: {settings.legal_audit_logs_retention_days} days.
        - Account deletion: {settings.legal_account_deletion_grace_days} days processing window where technically and legally applicable.
        - Backups: {settings.legal_backup_retention_policy}.
        - Billing records: {settings.legal_billing_records_retention}.
        - YouTube cookies: until user deletion or replacement of the uploaded cookies file.
        """
    ).strip()


def build_default_legal_documents(settings: Settings | None = None) -> tuple[dict[str, str], ...]:
    settings = settings or get_settings()
    operator = _operator_block(settings)
    processors = _processors_block(settings)
    retention = _retention_block(settings)
    version = settings.legal_document_version

    return (
        {
            "document_type": "terms",
            "version": version,
            "title": "User Agreement / Terms of Service",
            "content": dedent(
                f"""
                VATranscribe User Agreement / Terms of Service
                Version: {version}

                1. Scope
                These Terms govern access to VATranscribe, including the public website, authenticated dashboard, API-backed upload, download, transcription, export, quota and account functionality.

                2. Operator
                {operator}

                3. Account and access
                A user account may be required to use protected functionality. The user is responsible for keeping credentials secure and for activity performed through the account. VATranscribe may enforce password policy, refresh token rotation, CSRF protection, rate limits and other security controls.

                4. Media processing
                The user is responsible for having the legal right to upload, download, process, transcribe, store and export submitted media. The service must not be used for unlawful content, abusive automation, unauthorized access attempts, rights infringement or circumvention of third-party restrictions.

                5. YouTube cookies
                If enabled, the user may upload a Netscape cookies.txt file for their own jobs. The file is stored encrypted per user, used only to prepare the user's download jobs and may be deleted or replaced by the user. The user is responsible for complying with third-party platform rules.

                6. Quotas and service limits
                VATranscribe may enforce storage, upload, download, export, transcription, job and rate limits. Jobs can be rejected or stopped when limits are exceeded.

                7. Billing status
                Billing and paid subscriptions are disabled until a production payment provider and verified payment workflow are enabled. Paid-plan activation must not rely on manual or fake upgrade flows in production.

                8. Availability and changes
                The service may change during pre-release operation. Production service levels require a separate published service-level commitment or written agreement.

                9. Termination
                VATranscribe may suspend or terminate access if the account creates security, legal, infrastructure or abuse risk. The user may submit privacy requests for export or deletion where supported.

                10. Contact
                Legal notices: {settings.legal_contact_email}
                Support: {settings.support_email}
                """
            ).strip(),
        },
        {
            "document_type": "privacy",
            "version": version,
            "title": "Privacy Policy",
            "content": dedent(
                f"""
                VATranscribe Privacy Policy
                Version: {version}

                1. Controller / operator
                {operator}

                2. Categories of personal data
                VATranscribe may process:
                - Account data: email, password hash, account status, profile or display name where provided.
                - Security data: IP address, user-agent, audit logs, refresh token hashes, CSRF cookie metadata and security events.
                - File and workflow data: uploaded audio/video, downloaded media, generated transcripts, export artifacts in txt/srt/vtt/json formats, job metadata, checksums, sizes and timestamps.
                - YouTube cookies data: encrypted per-user Netscape cookies.txt file if uploaded by the user.
                - Billing data: plan, subscription status, payment status, provider transaction id, invoices or receipts where enabled.
                - Monitoring data: Sentry events, error traces and technical logs where monitoring is enabled.

                3. Purposes of processing
                Personal data is processed to register and authenticate users, provide upload/download/transcription/export functionality, store results in the user account, secure accounts, maintain audit logs, account for quota and usage, provide support, comply with legal obligations and improve reliability. Analytics is used only after consent where analytics is enabled.

                4. Cookies and browser storage
                Essential cookies and storage may be used for authentication, CSRF protection, language, session and security purposes. Analytics cookies are disabled unless explicitly enabled and consented where required.

                5. Processors and third parties
                {processors}

                6. Retention
                {retention}

                7. Rights and requests
                Users may request access, export, deletion, correction or consent revocation where legally and technically applicable. Requests are processed through the privacy request workflow or by contacting {settings.privacy_contact_email}.

                8. Security
                VATranscribe uses authentication controls, encrypted per-user YouTube cookie storage, owner-scoped file access, rate limits, audit logs, private storage endpoints, backup controls and container hardening. No security measure is absolute; users should avoid uploading unnecessary personal data.

                9. Cross-border and localization status
                Target users: {settings.legal_target_users}
                Russian citizens personal data processing: {_as_yes_no(settings.legal_152fz_russian_pd)}
                RKN notification status: {settings.legal_152fz_rkn_notification_status}
                Personal data localization status: {settings.legal_152fz_pd_localization_status}

                10. Contact
                Privacy requests: {settings.privacy_contact_email}
                Legal notices: {settings.legal_contact_email}
                """
            ).strip(),
        },
        {
            "document_type": "personal_data",
            "version": version,
            "title": "Consent to Personal Data Processing",
            "content": dedent(
                f"""
                VATranscribe Consent to Personal Data Processing
                Version: {version}

                1. Operator
                {operator}

                2. Consent
                By accepting this document, the user gives consent to processing of personal data required for account registration, authentication, media workflows, security, audit logging, quota accounting, support, privacy request handling and legally required records.

                3. Data covered by consent
                The consent covers account data, security data, workflow metadata, uploaded and downloaded files, transcripts, export artifacts, privacy request comments, encrypted YouTube cookies if uploaded by the user, and billing-related data where payment functionality is enabled.

                4. Processing operations
                Processing may include collection, recording, organization, storage, adaptation, retrieval, use, transfer to configured processors where applicable, blocking, deletion and destruction.

                5. Retention and withdrawal
                {retention}
                The user may withdraw consent where processing is based on consent. Withdrawal may limit access to the service. Some records may continue to be processed where necessary for security, legal obligations, billing, dispute resolution or audit evidence.

                6. Analytics and marketing
                Analytics cookies enabled: {_as_yes_no(settings.legal_analytics_cookies_enabled)}
                Marketing pixels enabled: {_as_yes_no(settings.legal_marketing_pixels_enabled)}
                CRM/ad pixels enabled: {_as_yes_no(settings.legal_crm_ad_pixels_enabled)}
                Non-essential tracking must not be enabled without the required consent.

                7. Contact
                Privacy contact: {settings.privacy_contact_email}
                """
            ).strip(),
        },
        {
            "document_type": "cookies",
            "version": version,
            "title": "Cookie Policy",
            "content": dedent(
                f"""
                VATranscribe Cookie Policy
                Version: {version}

                Essential cookies and browser storage are used for authentication, CSRF protection, session security, language and interface preferences. These technologies are necessary for secure operation of the service.

                Analytics cookies enabled: {_as_yes_no(settings.legal_analytics_cookies_enabled)}
                Marketing pixels enabled: {_as_yes_no(settings.legal_marketing_pixels_enabled)}
                CRM/ad pixels enabled: {_as_yes_no(settings.legal_crm_ad_pixels_enabled)}

                If analytics or marketing technologies are enabled, the service must present a consent choice before non-essential tracking is activated where required.
                """
            ).strip(),
        },
        {
            "document_type": "refund",
            "version": version,
            "title": "Refund Policy",
            "content": dedent(
                f"""
                VATranscribe Refund Policy
                Version: {version}

                Paid billing is disabled until a production payment provider is enabled. Before paid subscriptions are launched, the service must publish exact price, billing period, renewal, cancellation, refund, invoice and fiscal receipt rules.

                Refund handling contact: {settings.support_email}
                Payment provider: {settings.legal_payment_provider}
                """
            ).strip(),
        },
    )


def ensure_default_legal_documents(db: Session) -> None:
    documents = build_default_legal_documents()
    now = utcnow()

    for item in documents:
        document_type = normalize_document_type(item["document_type"])

        existing = db.scalar(
            select(LegalDocument).where(
                LegalDocument.document_type == document_type,
                LegalDocument.version == item["version"],
            )
        )

        db.execute(
            update(LegalDocument)
            .where(
                LegalDocument.document_type == document_type,
                LegalDocument.version != item["version"],
                LegalDocument.is_active.is_(True),
            )
            .values(is_active=False)
        )

        if existing is not None:
            existing.title = item["title"]
            existing.content = item["content"]
            existing.is_active = True
            if existing.published_at is None:
                existing.published_at = now
            existing.updated_at = now
            continue

        db.add(
            LegalDocument(
                document_type=document_type,
                version=item["version"],
                title=item["title"],
                content=item["content"],
                is_active=True,
                published_at=now,
            )
        )

    db.flush()


def list_active_legal_documents(db: Session) -> list[LegalDocument]:
    ensure_default_legal_documents(db)

    return list(
        db.scalars(
            select(LegalDocument)
            .where(LegalDocument.is_active.is_(True))
            .order_by(LegalDocument.document_type.asc(), LegalDocument.published_at.desc())
        )
    )


def get_current_legal_document(db: Session, document_type: str) -> LegalDocument:
    ensure_default_legal_documents(db)

    normalized = normalize_document_type(document_type)

    document = db.scalar(
        select(LegalDocument)
        .where(
            LegalDocument.document_type == normalized,
            LegalDocument.is_active.is_(True),
        )
        .order_by(LegalDocument.published_at.desc(), LegalDocument.created_at.desc())
    )

    if document is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Active legal document '{normalized}' not found",
        )

    return document


def list_required_active_legal_documents(db: Session) -> list[LegalDocument]:
    ensure_default_legal_documents(db)

    return [
        get_current_legal_document(db, document_type)
        for document_type in REQUIRED_LEGAL_DOCUMENT_TYPES
    ]


class LegalDocumentService:
    def normalize_document_type(self, document_type: str) -> str:
        return normalize_document_type(document_type)


legal_document_service = LegalDocumentService()
