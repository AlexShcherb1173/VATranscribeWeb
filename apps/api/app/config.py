from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


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
    app_name: str = "VATranscribe API"
    app_env: str = "development"
    debug: bool = True

    api_prefix: str = Field("/api/v1", alias="API_PREFIX")

    # --- DATABASE / REDIS ---
    database_url: str = Field(..., alias="DATABASE_URL")
    redis_url: str = Field("redis://redis:6379/0", alias="REDIS_URL")

    # --- AUTH ---
    secret_key: str = Field(..., alias="SECRET_KEY")
    access_token_expire_minutes: int = Field(
        1440, alias="ACCESS_TOKEN_EXPIRE_MINUTES"
    )

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

    # ============================================================
    # HELPERS
    # ============================================================

    @property
    def cors_origins_list(self) -> list[str]:
        if self.cors_origins.strip() == "*":
            return ["*"]

        return [
            origin.strip()
            for origin in self.cors_origins.split(",")
            if origin.strip()
        ]

    @property
    def storage_dirs(self) -> list[Path]:
        return [
            self.storage_root,
            self.uploads_dir,
            self.downloads_dir,
            self.temp_dir,
            self.cookies_dir,  # 🔥 добавлено
            self.transcripts_txt_dir,
            self.transcripts_srt_dir,
            self.transcripts_vtt_dir,
            self.transcripts_json_dir,
        ]

    @property
    def resolved_cookies_file(self) -> Path:
        """
        Возвращает фактический путь cookies файла:
        либо из .env, либо дефолт storage/cookies/youtube.txt
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