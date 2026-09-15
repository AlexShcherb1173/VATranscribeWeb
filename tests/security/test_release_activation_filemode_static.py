import os
from pathlib import Path
import shutil
import stat
import subprocess

import pytest


ROOT = Path(__file__).resolve().parents[2]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def release_extraction_command() -> str:
    activator = read("infra/deploy/activate-release.sh")
    start = activator.index("tar \\\n  --extract")
    end = activator.index("\n\n", start)
    return activator[start:end]


def test_release_extraction_preserves_validated_git_file_modes():
    activator = read("infra/deploy/activate-release.sh")
    extraction = release_extraction_command()

    assert "umask 027" in activator
    assert "--no-same-owner" in extraction
    assert "--same-permissions" in extraction
    assert "--no-same-permissions" not in extraction
    assert "--delay-directory-restore" in extraction


def test_release_payload_accepts_only_regular_git_file_modes():
    workflow = read(".github/workflows/production-deploy.yml")

    assert '$1 != "100644" && $1 != "100755"' in workflow
    assert "Unsupported Git entry modes" in workflow
    assert "git archive --format=tar.gz" in workflow


@pytest.mark.skipif(
    os.name == "nt",
    reason="POSIX file modes are not authoritative on Windows/MSYS filesystems",
)
def test_gnu_tar_preserves_release_file_modes_despite_umask(tmp_path: Path):
    tar = shutil.which("tar")
    bash = shutil.which("bash")

    assert tar is not None, "GNU tar is required on Linux CI"
    assert bash is not None, "bash is required on Linux CI"

    version = subprocess.run(
        [tar, "--version"],
        check=True,
        capture_output=True,
        text=True,
    )
    assert "GNU tar" in version.stdout, "Linux CI must exercise GNU tar semantics"

    source = tmp_path / "source"
    extracted = tmp_path / "extracted"
    archive = tmp_path / "release.tar"
    source.mkdir()
    extracted.mkdir()

    regular = source / "regular.txt"
    executable = source / "executable.sh"
    regular.write_text("regular\n", encoding="utf-8")
    executable.write_text("#!/usr/bin/env bash\n", encoding="utf-8")
    regular.chmod(0o644)
    executable.chmod(0o755)

    subprocess.run(
        [
            tar,
            "--create",
            "--file",
            str(archive),
            "--directory",
            str(source),
            regular.name,
            executable.name,
        ],
        check=True,
    )

    subprocess.run(
        [
            bash,
            "-c",
            """set -euo pipefail
umask 027
"$1" --extract --file "$2" --directory "$3" \\
  --no-same-owner \\
  --same-permissions \\
  --delay-directory-restore
""",
            "release-filemode-test",
            tar,
            str(archive),
            str(extracted),
        ],
        check=True,
    )

    assert stat.S_IMODE((extracted / regular.name).stat().st_mode) == 0o644
    assert stat.S_IMODE((extracted / executable.name).stat().st_mode) == 0o755
