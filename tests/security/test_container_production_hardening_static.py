from pathlib import Path


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def test_api_and_worker_dockerfiles_create_non_root_runtime_user():
    api = read("infra/docker/api.Dockerfile")
    worker = read("infra/docker/worker.Dockerfile")

    for text in (api, worker):
        assert "groupadd --system --gid 10001 appuser" in text
        assert "useradd --system --uid 10001" in text
        assert "USER 10001:10001" in text

    assert "C_FORCE_ROOT=true" not in worker
    assert "C_FORCE_ROOT=true" not in api


def test_production_compose_removes_public_api_db_redis_ports():
    text = read("infra/compose/docker-compose.prod.yml")

    assert "api:" in text
    assert "db:" in text
    assert "redis:" in text
    assert "ports: !reset []" in text
    assert 'expose:\n      - "8000"' in text
    assert 'expose:\n      - "5432"' in text
    assert 'expose:\n      - "6379"' in text


def test_production_compose_removes_project_bind_mounts_for_api_and_worker():
    text = read("infra/compose/docker-compose.prod.yml")

    assert "volumes: !override" in text
    assert "./:/app" not in text
    assert "vatranscribe_storage:/app/storage" in text


def test_api_worker_have_runtime_hardening_controls():
    text = read("infra/compose/docker-compose.prod.yml")

    assert 'user: "10001:10001"' in text
    assert "read_only: true" in text
    assert "tmpfs:" in text
    assert "cap_drop:" in text
    assert "- ALL" in text
    assert "security_opt:" in text
    assert "no-new-privileges:true" in text


def test_worker_does_not_force_root_in_production():
    text = read("infra/compose/docker-compose.prod.yml")

    assert 'C_FORCE_ROOT: "false"' in text
    assert 'C_FORCE_ROOT: "true"' not in text


def test_production_hardening_document_exists():
    text = read("docs/architecture/stage-4-p1-05-container-production-hardening.md")

    assert "P1-05" in text
    assert "non-root" in text
    assert "DOCKER-USER" in text
    assert "yt-dlp" in text
