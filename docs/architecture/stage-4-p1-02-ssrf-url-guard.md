# Stage 4 / P1-02 — SSRF URL Guard

## Status

`P1-02_ssrf_url_guard` adds a defensive URL validation layer for user-supplied external media URLs.

## Why this is required

VATranscribe accepts external video/download URLs. Without SSRF protection, a user could submit URLs that target internal services, Docker network services, local metadata endpoints, local files, or dangerous redirect chains.

## Controls implemented

- Only `http` and `https` schemes are allowed.
- `file://`, `ftp://`, `gopher://`, scheme-relative URLs, and empty URLs are rejected.
- URL userinfo is rejected.
- Local/internal hostnames are rejected, including `localhost`, `.localhost`, `.local`, `.internal`, `.lan`, `.home.arpa`, and `metadata.google.internal`.
- IP literals are checked before outbound requests.
- DNS answers are resolved and blocked if any answer is non-public.
- Private, loopback, link-local, shared, reserved, unspecified, multicast, and documentation ranges are blocked via `ipaddress.is_global` and explicit checks.
- Basic obfuscated numeric host notation is blocked.
- HTML-page fallback no longer uses direct `urllib.request.urlopen`; it uses a safe opener that validates every redirect hop.
- API entrypoints validate URL input before creating analyze/download jobs.
- Core download engine validates URL input before handing it to `yt-dlp` and before fallback `urllib` fetches.

## Protected flows

- `POST /api/v1/downloads/analyze`
- `POST /api/v1/downloads/jobs`
- Generic `POST /api/v1/jobs` when `input_url` is supplied
- Worker download execution through `download_media(...)`
- Core HTML fallback `resolve_media_url_from_http_page(...)`

## Known limitation

This guard validates the initial URL, DNS resolution, candidate media URLs extracted from HTML, and Python `urllib` redirects. `yt-dlp` has its own network stack and may still follow platform-specific redirects internally. For production, this application-level guard should be paired with network egress policy/firewall rules that block metadata IPs and private networks from the API/worker containers.

## Verification

Run:

```powershell
pytest tests/security/test_ssrf_url_guard.py -v
pytest tests/security/test_ssrf_url_guard_static.py -v
pytest -v
npm --prefix apps/web run build
```
