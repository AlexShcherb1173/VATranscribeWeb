from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import HTTPException

from apps.api.app.services.storage_limits import (
    FileSizeLimitExceeded,
    assert_path_size_within_limit,
    assert_size_within_limit,
    parse_content_length,
)


def test_parse_content_length_accepts_valid_value() -> None:
    assert parse_content_length({"content-length": "123"}) == 123


def test_parse_content_length_rejects_invalid_value() -> None:
    with pytest.raises(HTTPException):
        parse_content_length({"content-length": "abc"})


def test_size_limit_raises_413() -> None:
    with pytest.raises(FileSizeLimitExceeded) as exc:
        assert_size_within_limit(11, 10, "Upload")
    assert exc.value.status_code == 413


def test_path_size_limit_returns_size(tmp_path: Path) -> None:
    path = tmp_path / "item.bin"
    path.write_bytes(b"abc")
    assert assert_path_size_within_limit(path, 3, "File") == 3
