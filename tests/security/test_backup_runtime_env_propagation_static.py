from pathlib import Path


BACKUP_SCRIPT = Path(
    "infra/backup/backup-postgres.sh"
)


def read_backup_script() -> str:
    return BACKUP_SCRIPT.read_text(
        encoding="utf-8"
    )


def test_runtime_env_is_loaded_before_backup_config_resolution():
    script = read_backup_script()

    runtime_decl = (
        'RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-}"'
    )
    runtime_guard = (
        'if [[ -n "${RUNTIME_ENV_FILE}" ]]; then'
    )
    runtime_exists = (
        '[[ -f "${RUNTIME_ENV_FILE}" ]]'
    )
    runtime_readable = (
        '[[ -r "${RUNTIME_ENV_FILE}" ]]'
    )
    runtime_source = (
        'source "${RUNTIME_ENV_FILE}"'
    )

    config_markers = [
        'PROJECT_NAME="${PROJECT_NAME:-vatranscribeweb}"',
        'POSTGRES_DB="${POSTGRES_DB:-vatranscribe}"',
        'POSTGRES_USER="${POSTGRES_USER:-postgres}"',
        'BACKUP_DIR="${BACKUP_DIR:-/backups/vatranscribe}"',
        (
            'BACKUP_REQUIRE_ENCRYPTION='
            '"${BACKUP_REQUIRE_ENCRYPTION:-false}"'
        ),
        (
            'BACKUP_ENCRYPTION_RECIPIENT='
            '"${BACKUP_ENCRYPTION_RECIPIENT:-'
            '${AGE_RECIPIENT:-}}"'
        ),
        (
            'BACKUP_REMOTE='
            '"${BACKUP_REMOTE:-${S3_REMOTE:-}}"'
        ),
    ]

    for marker in [
        runtime_decl,
        runtime_guard,
        runtime_exists,
        runtime_readable,
        runtime_source,
        *config_markers,
    ]:
        assert marker in script

    source_index = script.index(
        runtime_source
    )

    for marker in config_markers:
        assert source_index < script.index(
            marker
        )


def test_runtime_env_values_are_exported_to_child_processes():
    script = read_backup_script()

    source_marker = (
        'source "${RUNTIME_ENV_FILE}"'
    )

    source_index = script.index(
        source_marker
    )

    set_a_index = script.rfind(
        "set -a",
        0,
        source_index,
    )

    set_plus_a_index = script.index(
        "set +a",
        source_index,
    )

    assert set_a_index != -1
    assert set_a_index < source_index
    assert source_index < set_plus_a_index


def test_explicit_missing_or_unreadable_runtime_env_fails_closed():
    script = read_backup_script()

    assert (
        '[[ -f "${RUNTIME_ENV_FILE}" ]] || {'
        in script
    )

    assert (
        '[[ -r "${RUNTIME_ENV_FILE}" ]] || {'
        in script
    )

    assert (
        'Runtime env file not found: '
        '${RUNTIME_ENV_FILE}'
        in script
    )

    assert (
        'Runtime env file is not readable: '
        '${RUNTIME_ENV_FILE}'
        in script
    )


def test_runtime_env_remains_optional_for_prepopulated_callers():
    script = read_backup_script()

    assert (
        'RUNTIME_ENV_FILE="${RUNTIME_ENV_FILE:-}"'
        in script
    )

    assert (
        'if [[ -n "${RUNTIME_ENV_FILE}" ]]; then'
        in script
    )


def test_existing_compose_env_file_contract_is_preserved():
    script = read_backup_script()

    assert (
        'docker compose --env-file "${RUNTIME_ENV_FILE}"'
        in script
    )
