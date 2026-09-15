from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOCKERFILES = (
    ROOT / "infra/docker/api.Dockerfile",
    ROOT / "infra/docker/worker.Dockerfile",
)
DENO_VERSION = "2.9.4"
DENO_SHA256 = "c24f955d9fbfe0ea5ae2b501c8e71ae76e31e4c9782390a54a284b3364fda725"


def test_deno_release_is_pinned_and_verified() -> None:
    for dockerfile in DOCKERFILES:
        text = dockerfile.read_text(encoding="utf-8")

        assert f"ARG DENO_VERSION={DENO_VERSION}" in text
        assert f"ARG DENO_SHA256={DENO_SHA256}" in text
        assert "https://deno.land/install.sh" not in text
        assert "DENO_INSTALL=/usr/local" not in text
        assert "--http1.1" in text
        assert "--retry 5 --retry-delay 2 --retry-all-errors" in text
        assert (
            "https://github.com/denoland/deno/releases/download/"
            "v${DENO_VERSION}/deno-x86_64-unknown-linux-gnu.zip"
        ) in text
        assert (
            'echo "${DENO_SHA256}  /tmp/deno.zip" | sha256sum -c -'
        ) in text
        assert "unzip -q /tmp/deno.zip -d /usr/local/bin" in text
        assert "chmod 0755 /usr/local/bin/deno" in text
        assert "rm -f /tmp/deno.zip" in text
        assert "deno --version" in text
        assert "head -n 1 | cut -d ' ' -f 2" in text
        assert "sed -n '1s/^deno //p'" not in text
