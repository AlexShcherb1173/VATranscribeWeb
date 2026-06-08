from __future__ import annotations

from functools import lru_cache
from pathlib import Path
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
LOCALHOST_VALUES = {
    "localhost",
    "127.0.0.1",
    "0.0.0.0",
    "::1",
}


def _split_csv(value: str) -> list[str]:
    return [item.strip() for item in value.split(",") if item.strip()]


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
    cookies_dir: Path = Field(Path("storage/cookies"), alias="COOKIES_DIR")

    yt_dlp_cookies_file: Path | None = Field(
        None, alias="YT_DLP_COOKIES_FILE"
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
        if self.cookie_domain == "":
            self.cookie_domain = None

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

        if len(self.secret_key) < 32:
            errors.append("SECRET_KEY must be at least 32 characters in production")

        secret_key_normalized = self.secret_key.strip().lower()
        if (
            secret_key_normalized in DEFAULT_SECRET_KEY_VALUES
            or "change-me" in secret_key_normalized
            or "changeme" in secret_key_normalized
        ):
            errors.append("SECRET_KEY must not use a default/change-me value")

        if self.access_token_expire_minutes > 15:
            errors.append(
                "ACCESS_TOKEN_EXPIRE_MINUTES must be <= 15 in production"
            )

        if self.refresh_token_expire_days > 30:
            errors.append(
                "REFRESH_TOKEN_EXPIRE_DAYS must be <= 30 in production"
            )

        if not self.cookie_secure:
            errors.append("COOKIE_SECURE must be true in production")

        if not self.cookie_httponly:
            errors.append("COOKIE_HTTPONLY must be true in production")

        errors.extend(_validate_cookie_domain(self.cookie_domain))

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
    def storage_dirs(self) -> list[Path]:
        return [
            self.storage_root,
            self.uploads_dir,
            self.downloads_dir,
            self.temp_dir,
            self.cookies_dir,
            self.transcripts_txt_dir,
            self.transcripts_srt_dir,
            self.transcripts_vtt_dir,
            self.transcripts_json_dir,
        ]

    @property
    def resolved_cookies_file(self) -> Path:
        """
        Возвращает фактический путь cookies файла:
        либо из .env, либо дефолт storage/cookies/youtube.txt.
        """
        if self.yt_dlp_cookies_file:
            return self.yt_dlp_cookies_file

        return self.cookies_dir / "youtube.txt"


# ============================================================
# SINGLETON
# ============================================================

@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
