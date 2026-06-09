from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_url_guard_module_exists_and_blocks_ssrf_ranges() -> None:
    text = read("packages/core/vatranscribe_core/url_guard.py")

    assert "class UnsafeUrlError" in text
    assert "def validate_external_url" in text
    assert "SafeRedirectHandler" in text
    assert "build_safe_urllib_opener" in text
    assert "Only http and https URLs are allowed" in text
    assert "169.254.169.254" in text or "link-local" in text
    assert "is_global" in text
    assert "metadata.google.internal" in text
    assert "BLOCKED_HOST_SUFFIXES" in text


def test_downloads_router_validates_user_urls_before_analyze_and_job_create() -> None:
    text = read("apps/api/app/routers/downloads.py")

    assert "validate_external_url" in text
    assert "UnsafeUrlError" in text
    assert "def _validate_user_url_or_422" in text
    assert "clean_url = _validate_user_url_or_422(payload.url)" in text
    assert "analyze_url(clean_url" in text
    assert "input_url=clean_url" in text


def test_generic_jobs_router_validates_input_url() -> None:
    text = read("apps/api/app/routers/jobs.py")

    assert "validate_external_url" in text
    assert "def _validate_user_url_or_422" in text
    assert "input_url = _validate_user_url_or_422(payload.input_url)" in text
    assert "input_url=input_url" in text


def test_download_engine_guards_yt_dlp_and_http_page_fallback() -> None:
    text = read("packages/core/vatranscribe_core/download_engine.py")

    assert "validate_external_url" in text
    assert "build_safe_urllib_opener" in text
    assert "clean_url = validate_external_url(url)" in text
    assert "safe_media_url = validate_external_url(media_url)" in text
    assert "opener = build_safe_urllib_opener(max_redirects=5)" in text
    assert "opener.open(request, timeout=20)" in text
    assert "urllib.request.urlopen" not in text


def test_ssrf_tests_exist() -> None:
    assert (ROOT / "tests/security/test_ssrf_url_guard.py").exists()
    assert (ROOT / "tests/security/test_ssrf_url_guard_static.py").exists()


def test_ssrf_documentation_exists() -> None:
    text = read("docs/architecture/stage-4-p1-02-ssrf-url-guard.md")

    assert "P1-02" in text
    assert "SSRF" in text
    assert "localhost" in text
    assert "metadata" in text.lower()
    assert "redirect" in text.lower()
