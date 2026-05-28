from __future__ import annotations

from pathlib import Path


def safe_unlink(path: str | Path) -> bool:
    target = Path(path)
    if target.exists() and target.is_file():
        target.unlink(missing_ok=True)
        return True
    return False
