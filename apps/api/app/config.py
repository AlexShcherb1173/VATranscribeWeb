from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from ipaddress import ip_network
from urllib.parse import urlparse

from pydantic import Field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

ALLOWED_APP_ENVS = {"development", "test", "production"}
ALLOWED_JWT_ALGORITHMS = {"HS256", "RS256"}
ALLOWED_COOKIE_SAMESITE = {"lax", "strict"}
DEFAULT_SECRET_KEY_VALUES = {
    "super-secret-key-change-me",
    "change-me",
    "changeme",
    "secret",
    "secret-key",
    "development-secret-key",
}

SECRET_PLACEHOLDER_FRAGMENTS = (
    "change_me",
    "change-me",
    "changeme",
    "replace_me",
    "replace-me",
    "todo",
    "example.com",
    "super-secret",
    "local-dev",
    "placeholder",
)

ALLOWED_SECRET_MANAGER_STRATEGIES = {
    "local-env",
    "runtime-env-file",
    "github-environments",
    "yandex-lockbox",
    "doppler",
    "hashicorp-vault",
    "onepassword-cli",
    "docker-secrets",
}

PRODUCTION_SECRET_MANAGER_STRATEGIES = ALLOWED_SECRET_MANAGER_STRATEGIES - {"local-env"}

ALLOWED_PAYMENT_PROVIDERS = {
    "disabled",
    "yookassa",
    "cloudpayments",
    "stripe",
    "robokassa",
}
LOCALHOST_VALUES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
}

LEGAL_PLACEHOLDER_VALUES = {
    "",
    "change_me",
    "change-me",
    "changeme",
    "change me",
    "vatrascribe operator",
    "vatranscribe operator",
    "legal@example.com",
    "privacy@example.com",
    "support@example.com",
    "example.com",
    "localhost",
    "not specified",
    "not configured",
}

LEGAL_UNDECIDED_VALUES = {
    "",
    "not_decided",
    "not decided",
    "not-decided",
    "unknown",
    "todo",
    "tbd",
}

def _is_legal_placeholder(value: str | None) -> bool:
    if value is None:
        return True

    normalized = value.strip().lower()
    return (
        normalized in LEGAL_PLACEHOLDER_VALUES
        or "change_me" in normalized
        or "change-me" in normalized
        or "changeme" in normalized
    )


def _is_unmonitored_example_email(value: str | None) -> bool:
    if _is_legal_placeholder(value):
        return True

    normalized = value.strip().lower()
    return (
        "@" not in normalized
        or normalized.endswith("@example.com")
        or normalized.endswith("@example.org")
        or normalized.endswith("@localhost")
    )


def _looks_like_secret_placeholder(value: str | None) -> bool:
    if value is None:
        return True

    normalized = value.strip().lower()
    if not normalized:
        return True

    return any(fragment in normalized for fragment in SECRET_PLACEHOLDER_FRAGMENTS)


def _split_domains(value: str) -> list[str]:
    return [item.strip().lower() for item in value.split(",") if item.strip()]


def _is_undecided_legal_value(value: str | None) -> bool:
    if value is None:
        return True
    return value.strip().lower() in LEGAL_UNDECIDED_VALUES


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]



def _validate_cidr_list(value: str, field_name: str) -> list[str]:
    errors: list[str] = []
    for item in _split_csv(value):
        try:
            network = ip_network(item, strict=False)
        except ValueError:
            errors.append(f"{field_name} contains invalid CIDR: {item}")
            continue

        if network.prefixlen == 0:
            errors.append(f"{field_name} must not contain a catch-all CIDR: {item}")

    return errors

def _origin_host(origin: str) -> str:
    parsed = urlparse(origin)
    return (parsed.hostname or "").strip().lower()


def _is_local_origin(origin: str) -> bool:
    host = _origin_host(origin)
    return host in LOCALHOST_VALUES or host.endswith(".localhost")


def _validate_https_origin(origin: str, field_name: str) -> list[str]:
    errors: list[str] = []
    parsed = urlparse(origin)

    if origin == "*":
        errors.append(f"{field_name} must not contain '*'")
        return errors

    if parsed.scheme != "https":
        errors.append(f"{field_name} origin must use https: {origin}")

    if _is_local_origin(origin):
        errors.append(f"{field_name} origin must not use localhost/private dev host: {origin}")

    if not parsed.netloc:
        errors.append(f"{field_name} origin must be a full origin URL: {origin}")

    return errors


def _validate_cookie_domain(domain: str | None) -> list[str]:
    if not domain:
        return ["COOKIE_DOMAIN is required in production"]

    if "://" in domain:
        return ["COOKIE_DOMAIN must be a domain, not a URL"]

    clean_domain = domain.lstrip(".").lower()
    if clean_domain in LOCALHOST_VALUES or clean_domain.endswith(".localhost"):
        return ["COOKIE_DOMAIN must not use localhost"]

    if "." not in clean_domain:
        return ["COOKIE_DOMAIN must be a fully qualified domain"]

    return []


class Settings(BaseSettings):
    """
    Глобальные настройки приложения, читаемые из .env.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # --- APP ---
    app_name: str = Field("VATranscribe API", alias="APP_NAME")
    app_env: str = Field("development", alias="APP_ENV")
    debug: bool = Field(True, alias="DEBUG")
    expose_api_docs: bool = Field(True, alias="EXPOSE_API_DOCS")

    api_prefix: str = Field("/api/v1", alias="API_PREFIX")

    # --- PUBLIC ORIGINS / DOMAINS ---
    public_marketing_origin: str | None = Field(None, alias="PUBLIC_MARKETING_ORIGIN")
    public_app_origin: str | None = Field(None, alias="PUBLIC_APP_ORIGIN")
    public_api_origin: str | None = Field(None, alias="PUBLIC_API_ORIGIN")
    public_admin_origin: str | None = Field(None, alias="PUBLIC_ADMIN_ORIGIN")

    # --- DATABASE / REDIS ---
    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field("redis://redis:6379/0", alias="REDIS_URL")

    # --- OBSERVABILITY / LOGGING ---
    sentry_dsn: str | None = Field(None, alias="SENTRY_DSN")
    sentry_traces_sample_rate: float = Field(0.0, alias="SENTRY_TRACES_SAMPLE_RATE")
    log_level: str = Field("INFO", alias="LOG_LEVEL")
    log_json: bool = Field(True, alias="LOG_JSON")
    release_version: str | None = Field(None, alias="RELEASE_VERSION")

    # --- PRODUCTION SECRETS / VAULT ---
    secret_manager_strategy: str = Field("local-env", alias="SECRET_MANAGER_STRATEGY")
    runtime_env_file: str | None = Field(None, alias="RUNTIME_ENV_FILE")
    production_secrets_validation_required: bool = Field(
        True, alias="PRODUCTION_SECRETS_VALIDATION_REQUIRED"
    )
    secret_rotation_policy_version: str = Field(
        "2026-06", alias="SECRET_ROTATION_POLICY_VERSION"
    )

    # --- LEGAL / COMPLIANCE ---
    legal_document_version: str = Field("2.0", alias="LEGAL_DOCUMENT_VERSION")
    legal_operator_type: str = Field("pre-release", alias="LEGAL_OPERATOR_TYPE")
    legal_operator_name: str = Field("VATranscribe Operator", alias="LEGAL_OPERATOR_NAME")
    legal_operator_inn: str | None = Field(None, alias="LEGAL_OPERATOR_INN")
    legal_operator_ogrn: str | None = Field(None, alias="LEGAL_OPERATOR_OGRN")
    legal_operator_address: str | None = Field(None, alias="LEGAL_OPERATOR_ADDRESS")
    legal_contact_email: str = Field("legal@example.com", alias="LEGAL_CONTACT_EMAIL")
    privacy_contact_email: str = Field("privacy@example.com", alias="PRIVACY_CONTACT_EMAIL")
    support_email: str = Field("legal@example.com", alias="SUPPORT_EMAIL")
    legal_production_domains: str = Field("vatranscribe.ru,app.vatranscribe.ru,api.vatranscribe.ru", alias="LEGAL_PRODUCTION_DOMAINS")
    legal_target_users: str = Field("pre-release", alias="LEGAL_TARGET_USERS")
    legal_main_db_country: str = Field("not_decided", alias="LEGAL_MAIN_DB_COUNTRY")
    legal_backup_country: str = Field("not_decided", alias="LEGAL_BACKUP_COUNTRY")
    legal_hosting_provider: str = Field("disabled", alias="LEGAL_HOSTING_PROVIDER")
    legal_cdn_provider: str = Field("disabled", alias="LEGAL_CDN_PROVIDER")
    legal_analytics_provider: str = Field("disabled", alias="LEGAL_ANALYTICS_PROVIDER")
    legal_apm_provider: str = Field("disabled", alias="LEGAL_APM_PROVIDER")
    legal_payment_provider: str = Field("disabled", alias="LEGAL_PAYMENT_PROVIDER")
    legal_email_provider: str = Field("disabled", alias="LEGAL_EMAIL_PROVIDER")
    legal_youtube_cookies_upload_enabled: bool = Field(True, alias="LEGAL_YOUTUBE_COOKIES_UPLOAD_ENABLED")
    legal_analytics_cookies_enabled: bool = Field(False, alias="LEGAL_ANALYTICS_COOKIES_ENABLED")
    legal_marketing_pixels_enabled: bool = Field(False, alias="LEGAL_MARKETING_PIXELS_ENABLED")
    legal_crm_ad_pixels_enabled: bool = Field(False, alias="LEGAL_CRM_AD_PIXELS_ENABLED")
    legal_audit_logs_retention_days: int = Field(180, alias="LEGAL_AUDIT_LOGS_RETENTION_DAYS")
    legal_account_deletion_grace_days: int = Field(30, alias="LEGAL_ACCOUNT_DELETION_GRACE_DAYS")
    legal_backup_retention_policy: str = Field("7 daily / 4 weekly / 6 monthly", alias="LEGAL_BACKUP_RETENTION_POLICY")
    legal_billing_records_retention: str = Field("not enabled", alias="LEGAL_BILLING_RECORDS_RETENTION")
    legal_152fz_russian_pd: bool = Field(False, alias="LEGAL_152FZ_RUSSIAN_PD")
    legal_152fz_rkn_notification_status: str = Field("not_decided", alias="LEGAL_152FZ_RKN_NOTIFICATION_STATUS")
    legal_152fz_pd_localization_status: str = Field("not_decided", alias="LEGAL_152FZ_PD_LOCALIZATION_STATUS")

    # --- ADMIN SECURITY / 2FA ---
    admin_2fa_required: bool = Field(True, alias="ADMIN_2FA_REQUIRED")
    admin_2fa_issuer: str = Field("VATranscribe", alias="ADMIN_2FA_ISSUER")
    admin_2fa_recovery_code_count: int = Field(10, alias="ADMIN_2FA_RECOVERY_CODE_COUNT")
    admin_2fa_recovery_code_bytes: int = Field(10, alias="ADMIN_2FA_RECOVERY_CODE_BYTES")
    admin_2fa_totp_window: int = Field(1, alias="ADMIN_2FA_TOTP_WINDOW")

    # --- BILLING / PAYMENT PRODUCTION GATE ---
    payment_provider: str = Field("disabled", alias="PAYMENT_PROVIDER")
    payment_webhook_secret: str | None = Field(None, alias="PAYMENT_WEBHOOK_SECRET")
    payment_api_key: str | None = Field(None, alias="PAYMENT_API_KEY")
    payment_webhook_signature_header: str = Field(
        "X-VATranscribe-Signature", alias="PAYMENT_WEBHOOK_SIGNATURE_HEADER"
    )
    billing_fake_upgrade_enabled: bool = Field(True, alias="BILLING_FAKE_UPGRADE_ENABLED")
    billing_paid_plans_enabled: bool = Field(False, alias="BILLING_PAID_PLANS_ENABLED")


    # --- RATE LIMITING / TRUSTED PROXY ---
    rate_limit_backend: str = Field("memory", alias="RATE_LIMIT_BACKEND")
    rate_limit_redis_url: str | None = Field(None, alias="RATE_LIMIT_REDIS_URL")
    rate_limit_fail_open: bool = Field(False, alias="RATE_LIMIT_FAIL_OPEN")
    trusted_proxy_cidrs: str = Field("127.0.0.1/32,::1/128", alias="TRUSTED_PROXY_CIDRS")
    rate_limit_general_api_per_minute: int = Field(120, alias="RATE_LIMIT_GENERAL_API_PER_MINUTE")
    rate_limit_auth_per_minute: int = Field(10, alias="RATE_LIMIT_AUTH_PER_MINUTE")
    rate_limit_auth_strict_per_minute: int = Field(5, alias="RATE_LIMIT_AUTH_STRICT_PER_MINUTE")
    rate_limit_upload_per_minute: int = Field(10, alias="RATE_LIMIT_UPLOAD_PER_MINUTE")
    rate_limit_download_per_minute: int = Field(30, alias="RATE_LIMIT_DOWNLOAD_PER_MINUTE")
    rate_limit_analyze_per_minute: int = Field(10, alias="RATE_LIMIT_ANALYZE_PER_MINUTE")

    # --- AUTH / JWT ---
    secret_key: str = Field(..., alias="SECRET_KEY")
    jwt_algorithm: str = Field("HS256", alias="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(
        1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )
    refresh_token_expire_days: int = Field(30, alias="REFRESH_TOKEN_EXPIRE_DAYS")

    # --- AUTH COOKIES ---
    cookie_secure: bool = Field(False, alias="COOKIE_SECURE")
    cookie_httponly: bool = Field(True, alias="COOKIE_HTTPONLY")
    cookie_samesite: str = Field("lax", alias="COOKIE_SAMESITE")
    cookie_domain: str | None = Field(None, alias="COOKIE_DOMAIN")
    refresh_cookie_name: str = Field("vatranscribe_refresh_token", alias="REFRESH_COOKIE_NAME")
    csrf_cookie_name: str = Field("vatranscribe_csrf_token", alias="CSRF_COOKIE_NAME")
    csrf_header_name: str = Field("X-CSRF-Token", alias="CSRF_HEADER_NAME")

    # --- CORS ---
    cors_origins: str = Field("*", alias="CORS_ORIGINS")

    # --- STORAGE ---
    storage_root: Path = Field(Path("storage"), alias="STORAGE_ROOT")
    uploads_dir: Path = Field(Path("storage/uploads"), alias="UPLOADS_DIR")
    downloads_dir: Path = Field(Path("storage/downloads"), alias="DOWNLOADS_DIR")
    temp_dir: Path = Field(Path("storage/tmp"), alias="TEMP_DIR")


    # --- UPLOAD / DOWNLOAD / RETENTION LIMITS ---
    max_upload_bytes: int = Field(1024 * 1024 * 1024, alias="MAX_UPLOAD_BYTES")
    upload_stream_chunk_bytes: int = Field(1024 * 1024, alias="UPLOAD_STREAM_CHUNK_BYTES")
    max_external_download_bytes: int = Field(2 * 1024 * 1024 * 1024, alias="MAX_EXTERNAL_DOWNLOAD_BYTES")
    max_export_artifact_bytes: int = Field(500 * 1024 * 1024, alias="MAX_EXPORT_ARTIFACT_BYTES")
    max_media_download_bytes: int = Field(2 * 1024 * 1024 * 1024, alias="MAX_MEDIA_DOWNLOAD_BYTES")
    temp_file_retention_hours: int = Field(24, alias="TEMP_FILE_RETENTION_HOURS")
    failed_job_file_retention_days: int = Field(7, alias="FAILED_JOB_FILE_RETENTION_DAYS")
    export_artifact_retention_days: int = Field(14, alias="EXPORT_ARTIFACT_RETENTION_DAYS")
    media_asset_retention_days: int = Field(30, alias="MEDIA_ASSET_RETENTION_DAYS")
    transcript_retention_days: int = Field(90, alias="TRANSCRIPT_RETENTION_DAYS")
    cleanup_batch_size: int = Field(500, alias="CLEANUP_BATCH_SIZE")

    # --- TRANSCRIPTS ---
    transcripts_txt_dir: Path = Field(
        Path("storage/transcripts/txt"), alias="TRANSCRIPTS_TXT_DIR"
    )
    transcripts_srt_dir: Path = Field(
        Path("storage/transcripts/srt"), alias="TRANSCRIPTS_SRT_DIR"
    )
    transcripts_vtt_dir: Path = Field(
        Path("storage/transcripts/vtt"), alias="TRANSCRIPTS_VTT_DIR"
    )
    transcripts_json_dir: Path = Field(
        Path("storage/transcripts/json"), alias="TRANSCRIPTS_JSON_DIR"
    )

    # --- COOKIES / YT-DLP ---
    # Deprecated global cookie path is kept only for backward-compatible parsing.
    # Production must use encrypted per-user YouTube cookies instead.
    cookies_dir: Path = Field(Path("storage/cookies"), alias="COOKIES_DIR")

    yt_dlp_cookies_file: Path | None = Field(
        None, alias="YT_DLP_COOKIES_FILE"
    )

    youtube_cookies_encryption_key: str | None = Field(
        None, alias="YOUTUBE_COOKIES_ENCRYPTION_KEY"
    )
    youtube_cookies_max_bytes: int = Field(
        1024 * 1024, alias="YOUTUBE_COOKIES_MAX_BYTES"
    )
    youtube_cookies_temp_dir: Path = Field(
        Path("storage/tmp/ytdlp-cookies"), alias="YOUTUBE_COOKIES_TEMP_DIR"
    )

    yt_dlp_proxy_url: str | None = Field(
        None, alias="YT_DLP_PROXY_URL"
    )

    yt_dlp_youtube_player_client: str | None = Field(
        None, alias="YT_DLP_YOUTUBE_PLAYER_CLIENT"
    )
    yt_dlp_youtube_po_token: str | None = Field(
        None, alias="YT_DLP_YOUTUBE_PO_TOKEN"
    )

    # --- TRANSCRIPTION ---
    default_transcription_model: str = Field(
        "medium", alias="DEFAULT_TRANSCRIPTION_MODEL"
    )
    default_language: str | None = Field(
        None, alias="DEFAULT_LANGUAGE"
    )

    @model_validator(mode="after")
    def validate_environment_guardrails(self) -> "Settings":
        errors: list[str] = []

        self.app_env = self.app_env.strip().lower()
        self.jwt_algorithm = self.jwt_algorithm.strip().upper()
        self.cookie_samesite = self.cookie_samesite.strip().lower()
        self.log_level = self.log_level.strip().upper()
        if self.release_version == "":
            self.release_version = None
        if self.sentry_dsn == "":
            self.sentry_dsn = None

        for attr_name in (
            "legal_document_version",
            "legal_operator_type",
            "legal_operator_name",
            "legal_operator_inn",
            "legal_operator_ogrn",
            "legal_operator_address",
            "legal_contact_email",
            "privacy_contact_email",
            "support_email",
            "legal_production_domains",
            "legal_target_users",
            "legal_main_db_country",
            "legal_backup_country",
            "legal_hosting_provider",
            "legal_cdn_provider",
            "legal_analytics_provider",
            "legal_apm_provider",
            "legal_payment_provider",
            "legal_email_provider",
            "legal_backup_retention_policy",
            "legal_billing_records_retention",
            "legal_152fz_rkn_notification_status",
            "legal_152fz_pd_localization_status",
            "admin_2fa_issuer",
            "payment_provider",
            "payment_webhook_secret",
            "payment_api_key",
            "payment_webhook_signature_header",
            "secret_manager_strategy",
            "runtime_env_file",
            "secret_rotation_policy_version",
        ):
            value = getattr(self, attr_name)
            if isinstance(value, str):
                value = value.strip()
                setattr(self, attr_name, value if value else None)

        if self.legal_operator_type:
            self.legal_operator_type = self.legal_operator_type.lower()
        self.legal_production_domains = ",".join(_split_domains(self.legal_production_domains or ""))
        self.legal_152fz_rkn_notification_status = (self.legal_152fz_rkn_notification_status or "not_decided").strip().lower()
        self.legal_152fz_pd_localization_status = (self.legal_152fz_pd_localization_status or "not_decided").strip().lower()

        self.secret_manager_strategy = (self.secret_manager_strategy or "local-env").strip().lower()
        if self.runtime_env_file == "":
            self.runtime_env_file = None
        if self.secret_rotation_policy_version == "":
            self.secret_rotation_policy_version = None

        self.rate_limit_backend = self.rate_limit_backend.strip().lower()
        self.trusted_proxy_cidrs = ",".join(_split_csv(self.trusted_proxy_cidrs))
        if self.rate_limit_redis_url == "":
            self.rate_limit_redis_url = None
        if self.cookie_domain == "":
            self.cookie_domain = None

        if self.youtube_cookies_encryption_key == "":
            self.youtube_cookies_encryption_key = None

        self.refresh_cookie_name = self.refresh_cookie_name.strip()
        self.csrf_cookie_name = self.csrf_cookie_name.strip()
        self.csrf_header_name = self.csrf_header_name.strip()
        if not self.refresh_cookie_name or not self.csrf_cookie_name or not self.csrf_header_name:
            errors.append("AUTH cookie names must not be empty")
        if self.refresh_cookie_name == self.csrf_cookie_name:
            errors.append("REFRESH_COOKIE_NAME and CSRF_COOKIE_NAME must be different")

        if self.app_env not in ALLOWED_APP_ENVS:
            errors.append(
                "APP_ENV must be one of: development, test, production"
            )

        if self.jwt_algorithm not in ALLOWED_JWT_ALGORITHMS:
            errors.append("JWT_ALGORITHM must be HS256 or RS256")

        if self.cookie_samesite not in ALLOWED_COOKIE_SAMESITE:
            errors.append("COOKIE_SAMESITE must be lax or strict")

        if self.log_level not in {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}:
            errors.append("LOG_LEVEL must be one of: DEBUG, INFO, WARNING, ERROR, CRITICAL")

        if not 0.0 <= self.sentry_traces_sample_rate <= 1.0:
            errors.append("SENTRY_TRACES_SAMPLE_RATE must be between 0.0 and 1.0")

        if self.secret_manager_strategy not in ALLOWED_SECRET_MANAGER_STRATEGIES:
            errors.append(
                "SECRET_MANAGER_STRATEGY must be one of: "
                + ", ".join(sorted(ALLOWED_SECRET_MANAGER_STRATEGIES))
            )

        if self.admin_2fa_recovery_code_count <= 0:
            errors.append("ADMIN_2FA_RECOVERY_CODE_COUNT must be positive")

        if self.admin_2fa_recovery_code_bytes < 8:
            errors.append("ADMIN_2FA_RECOVERY_CODE_BYTES must be >= 8")

        if self.admin_2fa_totp_window < 0 or self.admin_2fa_totp_window > 2:
            errors.append("ADMIN_2FA_TOTP_WINDOW must be between 0 and 2")

        self.payment_provider = (self.payment_provider or "disabled").strip().lower()
        if self.payment_provider not in ALLOWED_PAYMENT_PROVIDERS:
            errors.append(
                "PAYMENT_PROVIDER must be one of: "
                + ", ".join(sorted(ALLOWED_PAYMENT_PROVIDERS))
            )

        if self.payment_webhook_secret == "":
            self.payment_webhook_secret = None
        if self.payment_api_key == "":
            self.payment_api_key = None
        if not self.payment_webhook_signature_header:
            errors.append("PAYMENT_WEBHOOK_SIGNATURE_HEADER must not be empty")

        if self.payment_provider == "disabled" and self.billing_paid_plans_enabled:
            errors.append(
                "BILLING_PAID_PLANS_ENABLED cannot be true when PAYMENT_PROVIDER=disabled"
            )

        if self.youtube_cookies_max_bytes <= 0:
            errors.append("YOUTUBE_COOKIES_MAX_BYTES must be positive")

        if self.rate_limit_backend not in {"memory", "redis"}:
            errors.append("RATE_LIMIT_BACKEND must be memory or redis")

        if not self.trusted_proxy_cidrs_list:
            errors.append("TRUSTED_PROXY_CIDRS must not be empty")

        errors.extend(_validate_cidr_list(self.trusted_proxy_cidrs, "TRUSTED_PROXY_CIDRS"))

        for field_name, value in {
            "RATE_LIMIT_GENERAL_API_PER_MINUTE": self.rate_limit_general_api_per_minute,
            "RATE_LIMIT_AUTH_PER_MINUTE": self.rate_limit_auth_per_minute,
            "RATE_LIMIT_AUTH_STRICT_PER_MINUTE": self.rate_limit_auth_strict_per_minute,
            "RATE_LIMIT_UPLOAD_PER_MINUTE": self.rate_limit_upload_per_minute,
            "RATE_LIMIT_DOWNLOAD_PER_MINUTE": self.rate_limit_download_per_minute,
            "RATE_LIMIT_ANALYZE_PER_MINUTE": self.rate_limit_analyze_per_minute,
        }.items():
            if value <= 0:
                errors.append(f"{field_name} must be positive")



        for field_name, value in {
            "MAX_UPLOAD_BYTES": self.max_upload_bytes,
            "UPLOAD_STREAM_CHUNK_BYTES": self.upload_stream_chunk_bytes,
            "MAX_EXTERNAL_DOWNLOAD_BYTES": self.max_external_download_bytes,
            "MAX_EXPORT_ARTIFACT_BYTES": self.max_export_artifact_bytes,
            "MAX_MEDIA_DOWNLOAD_BYTES": self.max_media_download_bytes,
            "TEMP_FILE_RETENTION_HOURS": self.temp_file_retention_hours,
            "FAILED_JOB_FILE_RETENTION_DAYS": self.failed_job_file_retention_days,
            "EXPORT_ARTIFACT_RETENTION_DAYS": self.export_artifact_retention_days,
            "MEDIA_ASSET_RETENTION_DAYS": self.media_asset_retention_days,
            "TRANSCRIPT_RETENTION_DAYS": self.transcript_retention_days,
            "CLEANUP_BATCH_SIZE": self.cleanup_batch_size,
        }.items():
            if value <= 0:
                errors.append(f"{field_name} must be positive")

        if self.upload_stream_chunk_bytes > self.max_upload_bytes:
            errors.append("UPLOAD_STREAM_CHUNK_BYTES must be <= MAX_UPLOAD_BYTES")

        if self.is_production:
            errors.extend(self._validate_production_settings())

        if errors:
            raise ValueError("Invalid application settings: " + "; ".join(errors))

        return self

    def _validate_production_settings(self) -> list[str]:
        errors: list[str] = []

        if self.debug:
            errors.append("APP_ENV=production requires DEBUG=false")

        if self.expose_api_docs:
            errors.append("APP_ENV=production requires EXPOSE_API_DOCS=false")

        if self.production_secrets_validation_required is not True:
            errors.append("PRODUCTION_SECRETS_VALIDATION_REQUIRED must be true in production")

        if self.secret_manager_strategy not in PRODUCTION_SECRET_MANAGER_STRATEGIES:
            errors.append(
                "SECRET_MANAGER_STRATEGY must not be local-env in production; "
                "use runtime-env-file, GitHub Environments or a vault adapter"
            )

        if not self.runtime_env_file:
            errors.append("RUNTIME_ENV_FILE is required in production")

        if _looks_like_secret_placeholder(self.runtime_env_file):
            errors.append("RUNTIME_ENV_FILE must not be a placeholder value")

        if len(self.secret_key) < 32:
            errors.append("SECRET_KEY must be at least 32 characters in production")

        secret_key_normalized = self.secret_key.strip().lower()
        if (
            secret_key_normalized in DEFAULT_SECRET_KEY_VALUES
            or "change-me" in secret_key_normalized
            or "changeme" in secret_key_normalized
        ):
            errors.append("SECRET_KEY must not use a default/change-me value")

        if _looks_like_secret_placeholder(self.database_url):
            errors.append("DATABASE_URL must not contain placeholder values in production")

        database_url_normalized = self.database_url.strip().lower()
        if "postgres:postgres" in database_url_normalized:
            errors.append("DATABASE_URL must not use postgres:postgres in production")

        if _looks_like_secret_placeholder(self.redis_url):
            errors.append("REDIS_URL must not contain placeholder values in production")

        if self.sentry_dsn and _looks_like_secret_placeholder(self.sentry_dsn):
            errors.append("SENTRY_DSN must not contain placeholder values")

        if self.access_token_expire_minutes > 15:
            errors.append(
                "ACCESS_TOKEN_EXPIRE_MINUTES must be <= 15 in production"
            )

        if self.refresh_token_expire_days > 30:
            errors.append(
                "REFRESH_TOKEN_EXPIRE_DAYS must be <= 30 in production"
            )


        if self.rate_limit_backend != "redis":
            errors.append("RATE_LIMIT_BACKEND=redis is required in production")

        if not self.rate_limit_redis_url_resolved:
            errors.append("RATE_LIMIT_REDIS_URL or REDIS_URL is required for production rate limiting")

        if self.rate_limit_fail_open:
            errors.append("RATE_LIMIT_FAIL_OPEN must be false in production")

        if not self.cookie_secure:
            errors.append("COOKIE_SECURE must be true in production")

        if not self.cookie_httponly:
            errors.append("COOKIE_HTTPONLY must be true in production")

        errors.extend(_validate_cookie_domain(self.cookie_domain))

        if self.yt_dlp_cookies_file is not None:
            errors.append(
                "YT_DLP_COOKIES_FILE must not be set in production; "
                "use encrypted per-user YouTube cookies"
            )

        if not self.youtube_cookies_encryption_key:
            errors.append("YOUTUBE_COOKIES_ENCRYPTION_KEY is required in production")
        else:
            key_normalized = self.youtube_cookies_encryption_key.strip().lower()
            if (
                len(self.youtube_cookies_encryption_key.strip()) < 32
                or "change_me" in key_normalized
                or "change-me" in key_normalized
                or "changeme" in key_normalized
            ):
                errors.append(
                    "YOUTUBE_COOKIES_ENCRYPTION_KEY must be a real high-entropy key"
                )

        cors_origins = self.cors_origins_list
        if not cors_origins:
            errors.append("CORS_ORIGINS must not be empty in production")

        for origin in cors_origins:
            errors.extend(_validate_https_origin(origin, "CORS_ORIGINS"))

        required_public_origins = {
            "PUBLIC_MARKETING_ORIGIN": self.public_marketing_origin,
            "PUBLIC_APP_ORIGIN": self.public_app_origin,
            "PUBLIC_API_ORIGIN": self.public_api_origin,
            "PUBLIC_ADMIN_ORIGIN": self.public_admin_origin,
        }

        for field_name, origin in required_public_origins.items():
            if not origin:
                errors.append(f"{field_name} is required in production")
                continue
            errors.extend(_validate_https_origin(origin, field_name))

        if _is_legal_placeholder(self.legal_operator_name):
            errors.append("LEGAL_OPERATOR_NAME must be a real production value")

        if self.legal_operator_type in {"pre-release", "prerelease", "development", "dev", "test"}:
            errors.append("LEGAL_OPERATOR_TYPE must be final for production")

        for field_name, value in {
            "LEGAL_CONTACT_EMAIL": self.legal_contact_email,
            "PRIVACY_CONTACT_EMAIL": self.privacy_contact_email,
            "SUPPORT_EMAIL": self.support_email,
        }.items():
            if _is_unmonitored_example_email(value):
                errors.append(f"{field_name} must be a real monitored email")

        if not self.legal_production_domains_list:
            errors.append("LEGAL_PRODUCTION_DOMAINS must be configured in production")

        for domain in self.legal_production_domains_list:
            if domain in {"localhost", "127.0.0.1", "example.com"} or domain.endswith(".localhost"):
                errors.append(f"LEGAL_PRODUCTION_DOMAINS contains non-production domain: {domain}")

        if self.legal_document_version in {"", "1.0"}:
            errors.append("LEGAL_DOCUMENT_VERSION must identify the finalized legal document set")

        if self.legal_audit_logs_retention_days <= 0:
            errors.append("LEGAL_AUDIT_LOGS_RETENTION_DAYS must be positive")

        if self.legal_account_deletion_grace_days <= 0:
            errors.append("LEGAL_ACCOUNT_DELETION_GRACE_DAYS must be positive")

        if self.legal_152fz_russian_pd and _is_undecided_legal_value(self.legal_152fz_pd_localization_status):
            errors.append("LEGAL_152FZ_PD_LOCALIZATION_STATUS must be decided when Russian personal data is processed")

        if self.legal_152fz_russian_pd and self.legal_152fz_rkn_notification_status == "not_done":
            errors.append("LEGAL_152FZ_RKN_NOTIFICATION_STATUS must not be not_done in production")

        if not self.admin_2fa_required:
            errors.append("ADMIN_2FA_REQUIRED must be true in production")

        if _is_legal_placeholder(self.admin_2fa_issuer):
            errors.append("ADMIN_2FA_ISSUER must be a real production value")

        if self.billing_fake_upgrade_enabled:
            errors.append("BILLING_FAKE_UPGRADE_ENABLED must be false in production")

        if self.payment_provider == "disabled" and self.billing_paid_plans_enabled:
            errors.append(
                "BILLING_PAID_PLANS_ENABLED cannot be true when PAYMENT_PROVIDER=disabled"
            )

        if self.payment_provider != "disabled":
            if not self.billing_paid_plans_enabled:
                errors.append(
                    "BILLING_PAID_PLANS_ENABLED must be true when PAYMENT_PROVIDER is enabled"
                )
            if _looks_like_secret_placeholder(self.payment_webhook_secret):
                errors.append(
                    "PAYMENT_WEBHOOK_SECRET is required and must not be a placeholder "
                    "when PAYMENT_PROVIDER is enabled"
                )
            if _looks_like_secret_placeholder(self.payment_api_key):
                errors.append(
                    "PAYMENT_API_KEY is required and must not be a placeholder "
                    "when PAYMENT_PROVIDER is enabled"
                )
            if self.legal_payment_provider == "disabled":
                errors.append(
                    "LEGAL_PAYMENT_PROVIDER must identify the payment provider "
                    "when PAYMENT_PROVIDER is enabled"
                )

        return errors

    # ============================================================
    # HELPERS
    # ============================================================

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def api_docs_enabled(self) -> bool:
        return self.expose_api_docs and not self.is_production

    @property
    def docs_url(self) -> str | None:
        return "/docs" if self.api_docs_enabled else None

    @property
    def redoc_url(self) -> str | None:
        return "/redoc" if self.api_docs_enabled else None

    @property
    def openapi_url(self) -> str | None:
        return "/openapi.json" if self.api_docs_enabled else None

    @property
    def cors_origins_list(self) -> list[str]:
        return _split_csv(self.cors_origins)

    @property
    def log_level_upper(self) -> int:
        import logging

        return getattr(logging, self.log_level, logging.INFO)


    @property
    def rate_limit_redis_url_resolved(self) -> str:
        return self.rate_limit_redis_url or self.redis_url

    @property
    def trusted_proxy_cidrs_list(self) -> list[str]:
        return _split_csv(self.trusted_proxy_cidrs)

    @property
    def legal_production_domains_list(self) -> list[str]:
        return _split_domains(self.legal_production_domains or "")

    @property
    def payment_provider_enabled(self) -> bool:
        return self.payment_provider != "disabled"

    @property
    def fake_billing_upgrade_allowed(self) -> bool:
        return self.billing_fake_upgrade_enabled and not self.is_production

    @property
    def storage_dirs(self) -> list[Path]:
        return [
            self.storage_root,
            self.uploads_dir,
            self.downloads_dir,
            self.temp_dir,
            self.youtube_cookies_temp_dir,
            self.transcripts_txt_dir,
            self.transcripts_srt_dir,
            self.transcripts_vtt_dir,
            self.transcripts_json_dir,
        ]

    @property
    def resolved_cookies_file(self) -> Path | None:
        """
        Deprecated: global yt-dlp cookies are disabled.
        Use encrypted per-user YouTube cookies and temporary per-job files.
        """
        return None


# ============================================================
# SINGLETON
# ============================================================

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
