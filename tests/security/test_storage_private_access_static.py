from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def read(rel_path: str) -> str:
    return (ROOT / rel_path).read_text(encoding="utf-8")


def test_fastapi_does_not_mount_public_storage() -> None:
    content = read("apps/api/app/main.py")

    assert "StaticFiles" not in content
    assert "app.mount('/storage'" not in content
    assert "app.mount(\"/storage\"" not in content
    assert "storage_static" not in content


def test_nginx_does_not_proxy_public_storage() -> None:
    content = read("infra/docker/nginx.conf")

    assert "location /storage/" not in content
    assert "proxy_pass http://api:8000/storage" not in content


def test_vite_dev_server_does_not_proxy_public_storage() -> None:
    content = read("apps/web/vite.config.ts")

    assert '"/storage"' not in content
    assert "'/storage'" not in content


def test_public_api_schemas_do_not_expose_filesystem_paths() -> None:
    content = read("apps/api/app/schemas.py")

    media_asset_schema = re.search(
        r"class MediaAssetResponse\(BaseModel\):(?P<body>.*?)(?:\n\nclass |\Z)",
        content,
        flags=re.S,
    )
    export_schema = re.search(
        r"class ExportArtifactResponse\(BaseModel\):(?P<body>.*?)(?:\n\nclass |\Z)",
        content,
        flags=re.S,
    )

    assert media_asset_schema is not None
    assert export_schema is not None
    assert re.search(r"^\s*path\s*:", media_asset_schema.group("body"), flags=re.M) is None
    assert re.search(r"^\s*path\s*:", export_schema.group("body"), flags=re.M) is None


def test_response_builders_do_not_emit_internal_paths() -> None:
    files = [
        "apps/api/app/routers/media_assets.py",
        "apps/api/app/routers/jobs.py",
        "apps/api/app/routers/export_artifacts.py",
        "apps/api/app/routers/transcripts.py",
    ]

    for rel_path in files:
        content = read(rel_path)
        assert "path=item.path" not in content
        assert '"path": item.path' not in content
        assert '"path": media_asset.path' not in content