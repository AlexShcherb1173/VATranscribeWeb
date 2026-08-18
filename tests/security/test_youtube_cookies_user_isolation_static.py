from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel: str) -> str:
    return (ROOT / rel).read_text(encoding="utf-8")


def test_config_requires_youtube_cookie_encryption_key_in_production():
    text = read("apps/api/app/config.py")
    assert "youtube_cookies_encryption_key" in text
    assert "YOUTUBE_COOKIES_ENCRYPTION_KEY is required in production" in text
    assert "YT_DLP_COOKIES_FILE must not be set in production" in text


def test_model_stores_youtube_cookies_per_user_encrypted_without_path():
    text = read("apps/api/app/models.py")
    assert "class UserYoutubeCookies" in text
    assert "__tablename__ = \"user_youtube_cookies\"" in text
    assert "user_id" in text
    assert "encrypted_cookie_blob" in text
    assert "source_filename" in text
    model_block = text[text.index("class UserYoutubeCookies"): text.index("class PrivacyRequest")]
    assert "cookies_file" not in model_block
    assert "path" not in model_block


def test_youtube_cookies_router_has_upload_status_delete_and_no_path_response():
    text = read("apps/api/app/routers/youtube_cookies.py")
    assert "APIRouter(prefix=\"/youtube-cookies\"" in text
    assert "@router.post" in text
    assert "@router.get" in text
    assert "@router.delete" in text
    assert "UploadFile" in text
    assert "YouTubeCookiesStatusResponse" in text
    assert "file_path" not in text
    assert "storage_path" not in text


def test_youtube_cookie_service_encrypts_and_creates_temporary_per_job_file():
    text = read("apps/api/app/services/youtube_cookies_service.py")
    assert "from cryptography.fernet import Fernet" in text
    assert "_encrypt_cookie_text" in text
    assert "_decrypt_cookie_text" in text
    assert "create_temp_youtube_cookies_file_for_user" in text
    assert "delete_temp_youtube_cookies_file" in text
    assert "youtube_cookies_temp_dir" in text
    assert "chmod(0o600)" in text


def test_download_engine_no_longer_uses_global_resolved_cookies_file():
    text = read("packages/core/vatranscribe_core/download_engine.py")
    assert "settings.resolved_cookies_file" not in text
    assert "cookies_file: str | Path | None = None" in text
    assert "selected_cookies_file" in text
    assert "options[\"cookiefile\"] = str(selected_cookies_file)" in text


def test_worker_uses_only_user_scoped_cookies_and_deletes_temp_file():
    worker_paths = [
        path
        for path in (ROOT / "apps/worker").rglob("jobs.py")
        if "download_media" in path.read_text(encoding="utf-8")
    ]
    assert worker_paths
    for path in worker_paths:
        text = path.read_text(encoding="utf-8")
        assert "create_temp_youtube_cookies_file_for_user" in text
        assert "user_id=job.user_id" in text
        assert "cookies_file=youtube_cookies_file" in text
        assert "finally:" in text
        assert "delete_temp_youtube_cookies_file(youtube_cookies_file)" in text


def test_env_examples_do_not_point_to_global_youtube_cookie_file():
    dev_env = read(".env.example")
    prod_env = read(".env.production.example")
    assert "YOUTUBE_COOKIES_ENCRYPTION_KEY" in dev_env
    assert "YOUTUBE_COOKIES_ENCRYPTION_KEY" in prod_env
    assert "YT_DLP_COOKIES_FILE=./storage/cookies/youtube.txt" not in dev_env
    assert "YT_DLP_COOKIES_FILE=./storage/cookies/youtube.txt" not in prod_env

def test_legacy_global_youtube_cookie_settings_router_is_removed():
    legacy_router = ROOT / "apps/api/app/routers/settings.py"
    router_index = read("apps/api/app/routers/__init__.py")

    assert not legacy_router.exists()
    assert "routers.settings" not in router_index
    assert "settings_router" not in router_index


def test_frontend_uses_only_per_user_youtube_cookie_endpoints():
    active_wrapper = read("apps/web/src/shared/api/settings.ts")
    settings_page = read("apps/web/src/pages/settings/SettingsPage.tsx")
    duplicate_wrapper = ROOT / "apps/web/src/pages/shared/api/settings.ts"

    assert '"/youtube-cookies/status"' in active_wrapper
    assert active_wrapper.count('"/youtube-cookies"') == 2
    assert "/settings/youtube-cookies" not in active_wrapper

    assert "source_filename: string | null" in active_wrapper
    assert "cookie_format: string | null" in active_wrapper
    assert "updated_at: string | null" in active_wrapper
    assert "exists:" not in active_wrapper
    assert "path:" not in active_wrapper

    assert "status?.configured" in settings_page
    assert "status?.source_filename" in settings_page
    assert "status?.exists" not in settings_page
    assert "status?.path" not in settings_page

    assert not duplicate_wrapper.exists()

    frontend_root = ROOT / "apps/web/src"

    for path in [
        *frontend_root.rglob("*.ts"),
        *frontend_root.rglob("*.tsx"),
    ]:
        text = path.read_text(encoding="utf-8")
        assert "/settings/youtube-cookies" not in text, path


def test_compose_explicitly_injects_cookie_key_into_api_and_worker():
    compose = read("docker-compose.yml")
    expected = (
        "YOUTUBE_COOKIES_ENCRYPTION_KEY: "
        "${YOUTUBE_COOKIES_ENCRYPTION_KEY:-}"
    )

    assert compose.count(expected) == 2
