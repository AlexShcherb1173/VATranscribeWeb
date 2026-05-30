from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(r"D:\DevProject\PythonProject\VATranscribeWeb")
JOBS_PATH = ROOT / "apps/api/app/routers/jobs.py"


def main() -> None:
    if not JOBS_PATH.exists():
        raise RuntimeError(f"File not found: {JOBS_PATH}")

    text = JOBS_PATH.read_text(encoding="utf-8-sig")
    text = text.replace("\r\n", "\n")

    # 1. Ensure access control import exists.
    if "from apps.api.app.services.access_control import get_user_media_asset_or_404" not in text:
        quota_import = (
            "from apps.api.app.services.quota_service import "
            "assert_can_create_job, increment_jobs_used"
        )

        if quota_import not in text:
            raise RuntimeError(
                "Could not find quota_service import. "
                "Open apps/api/app/routers/jobs.py and check imports."
            )

        text = text.replace(
            quota_import,
            quota_import
            + "\nfrom apps.api.app.services.access_control import get_user_media_asset_or_404",
            1,
        )

    # 2. Insert ownership validation before Job(...) creation.
    if "media_asset_id=payload.transcription_media_asset_id" not in text:
        pattern = re.compile(
            r"(?P<indent>[ \t]+)assert_can_create_job\(db, current_user, jobs_to_add=1\)\n"
            r"\n"
            r"(?P=indent)job = Job\(",
            re.MULTILINE,
        )

        match = pattern.search(text)

        if not match:
            raise RuntimeError(
                "Could not find insertion point near assert_can_create_job(...) and job = Job(...). "
                "Send output of: Select-String -Path .\\apps\\api\\app\\routers\\jobs.py "
                "-Pattern \"assert_can_create_job|job = Job|transcription_media_asset_id\" -Context 5,8"
            )

        indent = match.group("indent")

        replacement = (
            f"{indent}assert_can_create_job(db, current_user, jobs_to_add=1)\n"
            f"\n"
            f"{indent}if payload.transcription_media_asset_id:\n"
            f"{indent}    get_user_media_asset_or_404(\n"
            f"{indent}        db=db,\n"
            f"{indent}        current_user=current_user,\n"
            f"{indent}        media_asset_id=payload.transcription_media_asset_id,\n"
            f"{indent}    )\n"
            f"\n"
            f"{indent}job = Job("
        )

        text = pattern.sub(replacement, text, count=1)

    JOBS_PATH.write_text(text, encoding="utf-8")

    print("OK: POST /jobs ownership validation patched.")
    print("")
    print("Patched file:")
    print(JOBS_PATH)


if __name__ == "__main__":
    main()