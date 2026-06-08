# Stage 4 / P0-04 — YouTube cookies user isolation

## Status

`P0-04_youtube_cookies_user_isolation` closes the global YouTube cookies risk.

## Security model

- YouTube cookies are stored per user.
- Cookies are encrypted at rest with `YOUTUBE_COOKIES_ENCRYPTION_KEY`.
- API responses never expose filesystem paths to cookie files.
- `YT_DLP_COOKIES_FILE` is disabled for production.
- Worker creates a temporary cookies file only for the current job owner.
- Temporary cookies files are deleted in `finally` after the yt-dlp call.
- User can delete uploaded YouTube cookies through `DELETE /api/v1/youtube-cookies`.

## API

```text
POST   /api/v1/youtube-cookies
GET    /api/v1/youtube-cookies/status
DELETE /api/v1/youtube-cookies
```

Status response intentionally exposes only metadata:

```json
{
  "configured": true,
  "source_filename": "youtube-cookies.txt",
  "cookie_format": "netscape",
  "size_bytes": 12345,
  "updated_at": "2026-06-09T00:00:00Z"
}
```

No `path`, `file_path`, `storage_path`, `cookies_file` or absolute path is returned.

## Cookie format

Only Netscape `cookies.txt` is supported for this stage.

## Required production env

```env
YOUTUBE_COOKIES_ENCRYPTION_KEY=CHANGE_ME_GENERATE_WITH_FERNET
YOUTUBE_COOKIES_MAX_BYTES=1048576
YOUTUBE_COOKIES_TEMP_DIR=./storage/tmp/ytdlp-cookies
YT_DLP_COOKIES_FILE=
```

Generate a key:

```powershell
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## Verification

```powershell
alembic upgrade head
pytest tests/security/test_youtube_cookies_user_isolation_static.py -v
pytest -v
npm --prefix apps/web run build
```

Runtime smoke:

```powershell
http --form POST "$API/youtube-cookies" "Authorization:Bearer $AccessToken" file@youtube-cookies.txt
http GET "$API/youtube-cookies/status" "Authorization:Bearer $AccessToken"
http DELETE "$API/youtube-cookies" "Authorization:Bearer $AccessToken"
```
