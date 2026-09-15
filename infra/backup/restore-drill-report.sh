#!/usr/bin/env bash
set -euo pipefail

REPORT_PATH="${1:-}"
BACKUP_FILE="${2:-}"
RESTORE_DB="${3:-}"
STATUS="${4:-unknown}"
ROW_COUNTS="${5:-not collected}"
[[ -n "${REPORT_PATH}" ]] || { echo "Usage: $0 report.md backup_file restore_db status [row_counts]" >&2; exit 2; }
mkdir -p "$(dirname "${REPORT_PATH}")"

cat > "${REPORT_PATH}" <<MD
# VATranscribeWeb restore drill report

- Status: ${STATUS}
- Created at UTC: $(date -u +%Y-%m-%dT%H:%M:%SZ)
- Backup file: ${BACKUP_FILE}
- Disposable restore database: ${RESTORE_DB}
- Production database overwritten: no
- Verification: checksum, manifest, pg_restore list, alembic_version, critical tables, row count queries

## Row counts

\`\`\`text
${ROW_COUNTS}
\`\`\`

## RPO/RTO targets

- RPO: ${BACKUP_RPO_HOURS:-24} hours
- RTO: ${BACKUP_RTO_HOURS:-2} hours

## Operator notes

Attach this report to the monthly backup/restore evidence log.
MD

echo "[OK] Restore drill report written: ${REPORT_PATH}"
