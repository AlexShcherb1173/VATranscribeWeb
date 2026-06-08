from __future__ import annotations

import html
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urljoin, urlparse

from yt_dlp import YoutubeDL

from apps.api.app.config import get_settings


MEDIA_URL_RE = re.compile(
    r"""(?P<url>https?://[^"'<>\\\s]+?\.(?:mp4|m3u8|webm|mov|m4v|mp3|m4a|aac)(?:\?[^"'<>\\\s]*)?)""",
    re.IGNORECASE,
)

SRC_RE = re.compile(
    r"""(?:src|href|content)=["'](?P<url>[^"']+\.(?:mp4|m3u8|webm|mov|m4v|mp3|m4a|aac)(?:\?[^"']*)?)["']""",
    re.IGNORECASE,
)

OG_VIDEO_RE = re.compile(
    r"""<meta[^>]+(?:property|name)=["'](?:og:video|og:video:url|og:video:secure_url|twitter:player:stream)["'][^>]+content=["'](?P<url>[^"']+)["'][^>]*>""",
    re.IGNORECASE,
)


BAD_MEDIA_EXTENSIONS = {
    "mhtml",
    "html",
    "htm",
    "json",
    "xml",
    "storyboard",
    "srv1",
    "srv2",
    "srv3",
    "ttml",
    "vtt",
    "srt",
}

AUDIO_EXTENSIONS = {"mp3", "m4a", "aac", "wav", "flac", "ogg", "opus", "webm"}
VIDEO_EXTENSIONS = {"mp4", "webm", "mov", "m4v", "mkv", "avi"}


def _normalize_codec(value: Any) -> str:
    return str(value or "none").lower().strip()


def _format_ext(item: dict[str, Any]) -> str:
    return str(item.get("ext") or "").lower().strip().lstrip(".")


def _format_id(item: dict[str, Any]) -> str:
    return str(item.get("format_id") or "").lower().strip()


def _is_media_format(item: dict[str, Any]) -> bool:
    ext = _format_ext(item)
    format_id = _format_id(item)
    protocol = str(item.get("protocol") or "").lower()
    note = str(item.get("format_note") or "").lower()

    if not ext or ext in BAD_MEDIA_EXTENSIONS:
        return False

    if "storyboard" in format_id or "storyboard" in note or protocol == "mhtml":
        return False

    return True


def _is_audio_format(item: dict[str, Any]) -> bool:
    if not _is_media_format(item):
        return False

    ext = _format_ext(item)
    acodec = _normalize_codec(item.get("acodec"))
    vcodec = _normalize_codec(item.get("vcodec"))

    if acodec in {"none", ""}:
        return False

    return ext in AUDIO_EXTENSIONS or vcodec == "none"


def _is_video_format(item: dict[str, Any]) -> bool:
    if not _is_media_format(item):
        return False

    ext = _format_ext(item)
    vcodec = _normalize_codec(item.get("vcodec"))

    if vcodec in {"none", ""}:
        return False

    return ext in VIDEO_EXTENSIONS


def _is_combined_format(item: dict[str, Any]) -> bool:
    if not _is_media_format(item):
        return False

    acodec = _normalize_codec(item.get("acodec"))
    vcodec = _normalize_codec(item.get("vcodec"))

    return acodec not in {"none", ""} and vcodec not in {"none", ""}


def _is_youtube_auth_error(message: str) -> bool:
    normalized = message.lower()

    markers = [
        "sign in to confirm",
        "not a bot",
        "cookies",
        "use --cookies",
        "use --cookies-from-browser",
        "confirm you're not a bot",
        "confirm you’re not a bot",
    ]

    return any(marker in normalized for marker in markers)


def _is_youtube_not_bot_error(message: str) -> bool:
    normalized = message.lower()

    markers = [
        "sign in to confirm",
        "confirm you're not a bot",
        "confirm you’re not a bot",
        "not a bot",
    ]

    return any(marker in normalized for marker in markers)


def _is_youtube_unavailable_error(message: str) -> bool:
    normalized = message.lower()

    markers = [
        "video unavailable",
        "this video is unavailable",
        "private video",
        "has been removed",
        "removed by the uploader",
        "not available in your country",
        "not available in this country",
        "members-only content",
    ]

    return any(marker in normalized for marker in markers)


def _is_requested_format_error(message: str) -> bool:
    normalized = message.lower()

    markers = [
        "requested format is not available",
        "format is not available",
        "requested formats are incompatible",
        "no video formats found",
        "no audio formats found",
    ]

    return any(marker in normalized for marker in markers)


def _raise_readable_youtube_auth_error(message: str) -> None:
    raise ValueError(
        "YouTube требует авторизацию или cookies. "
        "Загрузи актуальный youtube.txt в Настройки → YouTube cookies. "
        f"Оригинальная ошибка yt-dlp: {message}"
    )


def _raise_readable_youtube_not_bot_error(
    *,
    cookies_error: Exception,
    without_cookies_error: Exception,
) -> None:
    raise ValueError(
        "YouTube требует подтверждение, что запрос выполняет не бот. "
        "Приложение сначала попробовало анализ с youtube.txt, затем повторило без cookies, "
        "но YouTube всё равно заблокировал extraction. "
        "Экспортируй свежий youtube.txt из браузера, где это видео реально воспроизводится, "
        "через Get cookies.txt LOCALLY и загрузи его в Настройки → YouTube cookies. "
        f"Ошибка с cookies: {cookies_error}. "
        f"Ошибка без cookies: {without_cookies_error}"
    ) from without_cookies_error


def _raise_readable_youtube_unavailable_error(message: str) -> None:
    raise ValueError(
        "Видео недоступно. Возможные причины: ролик удалён, приватный, "
        "ограничен регионом/возрастом или недоступен для текущего аккаунта. "
        f"Оригинальная ошибка yt-dlp: {message}"
    )


def _raise_readable_format_error(message: str) -> None:
    raise ValueError(
        "Выбранный формат недоступен для этого видео. "
        "Приложение попробовало fallback-форматы, но скачать медиа не удалось. "
        f"Оригинальная ошибка yt-dlp: {message}"
    )


def _handle_known_yt_dlp_error(exc: Exception) -> None:
    message = str(exc)

    if _is_youtube_unavailable_error(message):
        _raise_readable_youtube_unavailable_error(message)

    if _is_youtube_auth_error(message):
        _raise_readable_youtube_auth_error(message)


def _unique_formats(formats: list[str | None]) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()

    for item in formats:
        value = str(item or "").strip()

        if not value or value in seen:
            continue

        seen.add(value)
        result.append(value)

    return result


def _ffmpeg_path() -> str:
    settings = get_settings()
    raw_path = str(getattr(settings, "ffmpeg_path", "") or "").strip()

    if not raw_path:
        return "/usr/bin"

    path = Path(raw_path)

    if path.name in {"ffmpeg", "ffmpeg.exe"}:
        return str(path.parent)

    return raw_path


def _split_csv_env_value(value: str | None) -> list[str]:
    if not value:
        return []

    return [
        item.strip()
        for item in value.split(",")
        if item.strip()
    ]


def _youtube_extractor_args() -> dict[str, dict[str, list[str]]] | None:
    """
    Builds yt-dlp extractor args for YouTube.

    Runtime modes:
    - YT_DLP_YOUTUBE_PLAYER_CLIENT empty + PO token empty:
      use yt-dlp default clients.
    - YT_DLP_YOUTUBE_PLAYER_CLIENT=mweb + PO token empty:
      intentionally ignore mweb and use yt-dlp default clients, because mweb
      without GVS PO token can return only mhtml/storyboard formats.
    - YT_DLP_YOUTUBE_PLAYER_CLIENT=mweb + PO token present:
      use mweb with the provided PO token.
    """
    settings = get_settings()

    player_client = str(
        getattr(settings, "yt_dlp_youtube_player_client", "") or ""
    ).strip()

    po_token = str(
        getattr(settings, "yt_dlp_youtube_po_token", "") or ""
    ).strip()

    player_clients = _split_csv_env_value(player_client)
    po_tokens = _split_csv_env_value(po_token)

    has_mweb_client = any(
        client.lower() == "mweb"
        for client in player_clients
    )

    # Critical guard:
    # mweb without GVS PO Token often skips real mp4/webm/m4a formats and leaves
    # only mhtml storyboard entries. In that case, do not pass player_client=mweb
    # to yt-dlp; let yt-dlp choose its default clients.
    if has_mweb_client and not po_tokens:
        return None

    youtube_args: dict[str, list[str]] = {}

    if player_clients:
        youtube_args["player_client"] = player_clients

    if po_tokens:
        youtube_args["po_token"] = po_tokens

    if not youtube_args:
        return None

    return {"youtube": youtube_args}


def _base_ydl_options(
    *,
    use_cookies: bool = True,
    cookies_file: str | Path | None = None,
) -> dict[str, Any]:
    settings = get_settings()

    selected_cookies_file = cookies_file
    proxy_url = getattr(settings, "yt_dlp_proxy_url", None)
    extractor_args = _youtube_extractor_args()

    options: dict[str, Any] = {
        "quiet": True,
        "no_warnings": True,
        "noplaylist": True,
        "ffmpeg_location": _ffmpeg_path(),
        "retries": 10,
        "fragment_retries": 10,
        "file_access_retries": 3,
        "extractor_retries": 3,
        "skip_unavailable_fragments": True,
        "continuedl": False,
        "socket_timeout": 30,
        "http_chunk_size": 10 * 1024 * 1024,
        "concurrent_fragment_downloads": 1,
        "overwrites": True,

        # Mild throttling to reduce YouTube anti-bot pressure.
        "sleep_interval_requests": 5,
        "sleep_interval": 5,
        "max_sleep_interval": 10,
    }

    if extractor_args:
        options["extractor_args"] = extractor_args

    if use_cookies and selected_cookies_file and Path(selected_cookies_file).exists():
        options["cookiefile"] = str(selected_cookies_file)

    if proxy_url:
        options["proxy"] = proxy_url

    return options


def _cleanup_old_outputs(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    for candidate in output_path.parent.glob(f"{output_path.stem}.*"):
        if candidate.is_file():
            try:
                candidate.unlink()
            except OSError:
                pass

    part_file = output_path.with_suffix(output_path.suffix + ".part")
    if part_file.exists():
        try:
            part_file.unlink()
        except OSError:
            pass


def _is_probably_direct_media_url(url: str) -> bool:
    path = urlparse(url).path.lower()
    return path.endswith((".mp4", ".m3u8", ".webm", ".mov", ".m4v", ".mp3", ".m4a", ".aac"))


def _fetch_html_page(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/124.0 Safari/537.36"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        },
    )

    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            content_type = response.headers.get("content-type", "")
            raw = response.read(3 * 1024 * 1024)

        if "text/html" not in content_type and "application/xhtml" not in content_type:
            return raw.decode("utf-8", errors="ignore")

        return raw.decode("utf-8", errors="ignore")
    except urllib.error.URLError as exc:
        raise ValueError(f"Failed to fetch page HTML: {exc}") from exc


def _normalize_found_url(page_url: str, found_url: str) -> str:
    normalized = html.unescape(found_url.strip())

    if normalized.startswith("//"):
        parsed = urlparse(page_url)
        return f"{parsed.scheme}:{normalized}"

    return urljoin(page_url, normalized)


def _extract_media_candidates_from_html(page_url: str, page_html: str) -> list[str]:
    candidates: list[str] = []

    for match in OG_VIDEO_RE.finditer(page_html):
        candidates.append(_normalize_found_url(page_url, match.group("url")))

    for match in SRC_RE.finditer(page_html):
        candidates.append(_normalize_found_url(page_url, match.group("url")))

    for match in MEDIA_URL_RE.finditer(page_html):
        candidates.append(_normalize_found_url(page_url, match.group("url")))

    unique: list[str] = []
    seen: set[str] = set()

    for candidate in candidates:
        clean = candidate.strip()

        if not clean or clean in seen:
            continue

        seen.add(clean)
        unique.append(clean)

    return unique


def _choose_best_media_candidate(candidates: list[str]) -> str | None:
    if not candidates:
        return None

    priority = [".m3u8", ".mp4", ".webm", ".mov", ".m4v", ".mp3", ".m4a", ".aac"]

    for ext in priority:
        for candidate in candidates:
            if ext in urlparse(candidate).path.lower():
                return candidate

    return candidates[0]


def resolve_media_url_from_http_page(url: str) -> str:
    clean_url = url.strip()

    if _is_probably_direct_media_url(clean_url):
        return clean_url

    page_html = _fetch_html_page(clean_url)
    candidates = _extract_media_candidates_from_html(clean_url, page_html)
    media_url = _choose_best_media_candidate(candidates)

    if not media_url:
        raise ValueError(
            "На странице не найдена открытая ссылка на видео или аудио. "
            "Если это личный кабинет, нужна прямая .mp4/.m3u8 ссылка или загрузка файла вручную."
        )

    return media_url


def _extract_info_once(
    url: str,
    *,
    download: bool,
    use_cookies: bool,
    options: dict[str, Any] | None = None,
    cookies_file: str | Path | None = None,
) -> tuple[dict[str, Any], str]:
    clean_url = url.strip()
    ydl_options = {
        **_base_ydl_options(use_cookies=use_cookies, cookies_file=cookies_file),
        **(options or {}),
    }

    with YoutubeDL(ydl_options) as ydl:
        return ydl.extract_info(clean_url, download=download), clean_url


def _extract_info_with_http_page_fallback(
    url: str,
    *,
    download: bool,
    use_cookies: bool,
    options: dict[str, Any] | None = None,
    cookies_file: str | Path | None = None,
) -> tuple[dict[str, Any], str]:
    clean_url = url.strip()

    try:
        return _extract_info_once(
            clean_url,
            download=download,
            use_cookies=use_cookies,
            options=options,
            cookies_file=cookies_file,
        )
    except Exception as exc:
        message = str(exc)

        if "Unsupported URL" not in message:
            raise

        resolved_url = resolve_media_url_from_http_page(clean_url)

        return _extract_info_once(
            resolved_url,
            download=download,
            use_cookies=use_cookies,
            options=options,
            cookies_file=cookies_file,
        )


def _extract_info_with_fallback(
    url: str,
    *,
    download: bool = False,
    options: dict[str, Any] | None = None,
    cookies_file: str | Path | None = None,
) -> tuple[dict[str, Any], str]:
    clean_url = url.strip()

    try:
        return _extract_info_with_http_page_fallback(
            clean_url,
            download=download,
            use_cookies=True,
            options=options,
            cookies_file=cookies_file,
        )
    except Exception as cookies_exc:
        cookies_message = str(cookies_exc)

        if not _is_youtube_not_bot_error(cookies_message):
            _handle_known_yt_dlp_error(cookies_exc)
            raise

        try:
            return _extract_info_with_http_page_fallback(
                clean_url,
                download=download,
                use_cookies=False,
                options=options,
                cookies_file=cookies_file,
            )
        except Exception as without_cookies_exc:
            without_cookies_message = str(without_cookies_exc)

            if _is_youtube_not_bot_error(without_cookies_message):
                _raise_readable_youtube_not_bot_error(
                    cookies_error=cookies_exc,
                    without_cookies_error=without_cookies_exc,
                )

            _handle_known_yt_dlp_error(without_cookies_exc)
            raise


def analyze_url(
    url: str,
    *,
    cookies_file: str | Path | None = None,
) -> dict[str, Any]:
    clean_url = url.strip()
    info, resolved_url = _extract_info_with_fallback(
        clean_url,
        download=False,
        cookies_file=cookies_file,
    )

    formats = info.get("formats", []) or []
    analyzed_formats: list[dict[str, Any]] = []

    for item in formats:
        if not _is_media_format(item):
            continue

        acodec = _normalize_codec(item.get("acodec"))
        vcodec = _normalize_codec(item.get("vcodec"))

        analyzed_formats.append(
            {
                "format_id": item.get("format_id"),
                "ext": item.get("ext"),
                "format_note": item.get("format_note"),
                "resolution": item.get("resolution"),
                "height": item.get("height"),
                "width": item.get("width"),
                "fps": item.get("fps"),
                "vcodec": item.get("vcodec"),
                "acodec": item.get("acodec"),
                "filesize": item.get("filesize") or item.get("filesize_approx"),
                "tbr": item.get("tbr"),
                "audio_only": acodec not in {"none", ""} and vcodec == "none",
                "video_only": vcodec not in {"none", ""} and acodec == "none",
            }
        )

    if not analyzed_formats:
        raise ValueError(
            "Для этой ссылки не найдено доступных медиаформатов. "
            "Видео может быть недоступно, приватно, ограничено регионом/возрастом "
            "или YouTube требует актуальные cookies."
        )

    duration = info.get("duration")
    webpage_url = info.get("webpage_url") or resolved_url
    extractor = info.get("extractor")

    return {
        "url": webpage_url,
        "input_url": clean_url,
        "resolved_media_url": resolved_url if resolved_url != clean_url else None,
        "platform": extractor,
        "title": info.get("title") or Path(urlparse(resolved_url).path).name,
        "duration_seconds": duration,
        "thumbnail_url": info.get("thumbnail"),
        "available_formats": analyzed_formats,
        "extract_audio": False,
        "duration": duration,
        "webpage_url": webpage_url,
        "extractor": extractor,
        "formats": analyzed_formats,
    }


def _resolve_final_file(output_path: Path, requested_format: str) -> Path:
    requested_format = requested_format.lower().strip().lstrip(".")
    expected_path = output_path.with_suffix(f".{requested_format}")

    if expected_path.exists():
        return expected_path

    if output_path.exists() and output_path.is_file():
        return output_path

    candidates = sorted(
        candidate
        for candidate in output_path.parent.glob(f"{output_path.stem}.*")
        if candidate.is_file() and not candidate.name.endswith(".part")
    )

    if not candidates:
        raise FileNotFoundError(f"Downloaded file not found for base path: {output_path}")

    exact_candidates = [
        candidate
        for candidate in candidates
        if candidate.suffix.lower().lstrip(".") == requested_format
    ]

    return exact_candidates[0] if exact_candidates else candidates[0]


def _download_single_file(
    *,
    url: str,
    fmt: str,
    output_path: Path,
    requested_format: str,
    extra_options: dict[str, Any] | None = None,
    progress_hook: Callable[[dict[str, Any]], None] | None = None,
    fallback_formats: list[str] | None = None,
    cookies_file: str | Path | None = None,
) -> dict[str, Any]:
    formats_to_try = _unique_formats([fmt, *(fallback_formats or [])])
    last_exception: Exception | None = None

    for current_format in formats_to_try:
        _cleanup_old_outputs(output_path)

        options: dict[str, Any] = {
            "format": current_format,
            "outtmpl": str(output_path.with_suffix(".%(ext)s")),
            **(extra_options or {}),
        }

        if progress_hook is not None:
            options["progress_hooks"] = [progress_hook]

        try:
            info, final_url = _extract_info_with_fallback(
                url.strip(),
                download=True,
                options=options,
                cookies_file=cookies_file,
            )
            final_path = _resolve_final_file(output_path, requested_format)

            return {
                "title": info.get("title"),
                "extractor": info.get("extractor"),
                "webpage_url": info.get("webpage_url") or final_url,
                "final_path": final_path,
                "resolved_media_url": final_url if final_url != url.strip() else None,
                "used_format": current_format,
            }
        except Exception as exc:
            message = str(exc)
            last_exception = exc

            if _is_requested_format_error(message):
                continue

            _handle_known_yt_dlp_error(exc)
            raise

    if last_exception is not None:
        _raise_readable_format_error(str(last_exception))

    raise ValueError("Download failed: no formats to try")


def _safe_selected_format_id(
    *,
    url: str,
    selected_format_id: str | None,
    expected_kind: str,
    cookies_file: str | Path | None = None,
) -> str | None:
    if not selected_format_id:
        return None

    info, _ = _extract_info_with_fallback(
        url.strip(),
        download=False,
        cookies_file=cookies_file,
    )
    formats = info.get("formats", []) or []

    for item in formats:
        if str(item.get("format_id")) != str(selected_format_id):
            continue

        if expected_kind == "audio" and _is_audio_format(item):
            return str(selected_format_id)

        if expected_kind == "video" and _is_video_format(item):
            return str(selected_format_id)

        if expected_kind == "media" and _is_media_format(item):
            return str(selected_format_id)

        return None

    return None


def download_media(
    *,
    url: str,
    requested_format: str,
    output_path: Path,
    mp4_mode: str = "compatible",
    video_format_id: str | None = None,
    audio_format_id: str | None = None,
    progress_hook: Callable[[dict[str, Any]], None] | None = None,
    cookies_file: str | Path | None = None,
) -> dict[str, Any]:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    requested_format = requested_format.lower().strip().lstrip(".")
    mp4_mode = (mp4_mode or "compatible").lower().strip()
    clean_url = url.strip()

    allowed_modes = {
        "compatible",
        "fast",
        "audio_mp3",
        "video_mp4_compatible",
        "video_mp4_fast",
        "selected_original",
        "best_available",
    }

    if not requested_format:
        raise ValueError("requested_format is required")

    if mp4_mode not in allowed_modes:
        raise ValueError(f"Unsupported download mode: {mp4_mode}")

    if mp4_mode == "audio_mp3":
        requested_format = "mp3"
        mp4_mode = "compatible"

    if mp4_mode == "video_mp4_compatible":
        requested_format = "mp4"
        mp4_mode = "compatible"

    if mp4_mode == "video_mp4_fast":
        requested_format = "mp4"
        mp4_mode = "fast"

    _cleanup_old_outputs(output_path)

    if mp4_mode == "selected_original":
        selected_format_id = _safe_selected_format_id(
            url=clean_url,
            selected_format_id=video_format_id or audio_format_id,
            expected_kind="media",
            cookies_file=cookies_file,
        )

        if not selected_format_id:
            selected_format_id = video_format_id or audio_format_id

        result = _download_single_file(
            url=clean_url,
            fmt=selected_format_id or "bv*+ba/best",
            output_path=output_path,
            requested_format=requested_format,
            progress_hook=progress_hook,
            cookies_file=cookies_file,
            fallback_formats=[
                "bv*+ba/best",
                "best",
            ],
        )

        return {
            **result,
            "requested_format": requested_format,
            "mp4_mode": "selected_original",
        }

    if mp4_mode == "best_available":
        result = _download_single_file(
            url=clean_url,
            fmt="bv*+ba/best",
            output_path=output_path,
            requested_format=requested_format,
            progress_hook=progress_hook,
            cookies_file=cookies_file,
            extra_options={
                "merge_output_format": requested_format
                if requested_format in {"mp4", "webm", "mkv"}
                else "mp4",
            },
            fallback_formats=[
                "bestvideo+bestaudio/best",
                "best",
            ],
        )

        return {
            **result,
            "requested_format": requested_format,
            "mp4_mode": "best_available",
        }

    if requested_format == "mp3":
        selected_audio_format = _safe_selected_format_id(
            url=clean_url,
            selected_format_id=audio_format_id,
            expected_kind="audio",
            cookies_file=cookies_file,
        )

        result = _download_single_file(
            url=clean_url,
            fmt=selected_audio_format or "bestaudio[ext=m4a]/bestaudio/best",
            output_path=output_path,
            requested_format="mp3",
            progress_hook=progress_hook,
            cookies_file=cookies_file,
            extra_options={
                "postprocessors": [
                    {
                        "key": "FFmpegExtractAudio",
                        "preferredcodec": "mp3",
                        "preferredquality": "192",
                    }
                ],
            },
            fallback_formats=[
                "bestaudio/best",
                "best",
            ],
        )

        return {
            **result,
            "requested_format": "mp3",
            "mp4_mode": mp4_mode,
        }

    if requested_format == "mp4" and mp4_mode == "fast":
        safe_video_format_id = _safe_selected_format_id(
            url=clean_url,
            selected_format_id=video_format_id,
            expected_kind="video",
            cookies_file=cookies_file,
        )
        safe_audio_format_id = _safe_selected_format_id(
            url=clean_url,
            selected_format_id=audio_format_id,
            expected_kind="audio",
            cookies_file=cookies_file,
        )

        if safe_video_format_id and safe_audio_format_id:
            ydl_format = f"{safe_video_format_id}+{safe_audio_format_id}"
        elif safe_video_format_id:
            ydl_format = f"{safe_video_format_id}+ba[ext=m4a]/bestaudio[ext=m4a]/ba/best"
        else:
            ydl_format = "bv*[ext=mp4]+ba[ext=m4a]/bv*+ba/best[ext=mp4]/best"

        result = _download_single_file(
            url=clean_url,
            fmt=ydl_format,
            output_path=output_path,
            requested_format="mp4",
            progress_hook=progress_hook,
            cookies_file=cookies_file,
            extra_options={
                "merge_output_format": "mp4",
            },
            fallback_formats=[
                "bv*+ba/best",
                "bestvideo+bestaudio/best",
                "best",
            ],
        )

        return {
            **result,
            "requested_format": "mp4",
            "mp4_mode": mp4_mode,
        }

    if requested_format == "mp4" and mp4_mode == "compatible":
        video_base = output_path.with_name(f"{output_path.stem}__video.mp4")
        audio_base = output_path.with_name(f"{output_path.stem}__audio.m4a")

        _cleanup_old_outputs(video_base)
        _cleanup_old_outputs(audio_base)

        safe_video_format_id = _safe_selected_format_id(
            url=clean_url,
            selected_format_id=video_format_id,
            expected_kind="video",
            cookies_file=cookies_file,
        )
        safe_audio_format_id = _safe_selected_format_id(
            url=clean_url,
            selected_format_id=audio_format_id,
            expected_kind="audio",
            cookies_file=cookies_file,
        )

        video_result = _download_single_file(
            url=clean_url,
            fmt=safe_video_format_id or "bv*[ext=mp4]/bestvideo[ext=mp4]/best[ext=mp4]",
            output_path=video_base,
            requested_format="mp4",
            progress_hook=progress_hook,
            cookies_file=cookies_file,
            fallback_formats=[
                "bv*/bestvideo/best",
                "best[ext=mp4]/best",
            ],
        )

        audio_result = _download_single_file(
            url=clean_url,
            fmt=safe_audio_format_id or "ba[ext=m4a]/bestaudio[ext=m4a]/ba/bestaudio/best",
            output_path=audio_base,
            requested_format="m4a",
            progress_hook=progress_hook,
            cookies_file=cookies_file,
            fallback_formats=[
                "ba/bestaudio/best",
                "best",
            ],
        )

        return {
            "title": video_result.get("title"),
            "extractor": video_result.get("extractor"),
            "webpage_url": video_result.get("webpage_url") or clean_url,
            "resolved_media_url": video_result.get("resolved_media_url"),
            "requested_format": "mp4",
            "mp4_mode": mp4_mode,
            "video_path": Path(video_result["final_path"]),
            "audio_path": Path(audio_result["final_path"]),
            "final_path": output_path.with_suffix(".mp4"),
            "used_video_format": video_result.get("used_format"),
            "used_audio_format": audio_result.get("used_format"),
        }

    result = _download_single_file(
        url=clean_url,
        fmt=video_format_id or audio_format_id or "best",
        output_path=output_path,
        requested_format=requested_format,
        progress_hook=progress_hook,
            cookies_file=cookies_file,
        fallback_formats=[
            "bv*+ba/best",
            "best",
        ],
    )

    return {
        **result,
        "requested_format": requested_format,
        "mp4_mode": mp4_mode,
    }
