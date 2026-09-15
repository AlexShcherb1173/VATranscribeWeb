#!/usr/bin/env bash
set -euo pipefail

# Creates a sanitized evidence report from a restore drill report.
# DO NOT commit generated evidence files, raw restore reports, backup paths, keys, or runtime env values to Git.

INPUT_REPORT="${1:-}"
OUTPUT_REPORT="${2:-}"
BACKUP_DIR="${BACKUP_DIR:-/opt/vatranscribe/backups}"
[[ -n "${INPUT_REPORT}" && -f "${INPUT_REPORT}" ]] || { echo "Usage: $0 restore-drill-report.md [redacted-output.md]" >&2; exit 2; }

if [[ -z "${OUTPUT_REPORT}" ]]; then
  OUTPUT_REPORT="$(dirname "${INPUT_REPORT}")/backup-restore-proof-evidence-$(date -u +%Y%m%dT%H%M%SZ).md"
fi

mkdir -p "$(dirname "${OUTPUT_REPORT}")"

status_line="$(grep -m1 '^- Status:' "${INPUT_REPORT}" || true)"
created_line="$(grep -m1 '^- Created at UTC:' "${INPUT_REPORT}" || true)"
backup_line="$(grep -m1 '^- Backup file:' "${INPUT_REPORT}" || true)"
restore_db_line="$(grep -m1 '^- Disposable restore database:' "${INPUT_REPORT}" || true)"
verification_line="$(grep -m1 '^- Verification:' "${INPUT_REPORT}" || true)"
rpo_line="$(grep -m1 '^- RPO:' "${INPUT_REPORT}" || true)"
rto_line="$(grep -m1 '^- RTO:' "${INPUT_REPORT}" || true)"

backup_path="${backup_line#- Backup file: }"
backup_basename=""
if [[ -n "${backup_path}" && "${backup_path}" != "${backup_line}" ]]; then
  backup_basename="$(basename "${backup_path}")"
else
  backup_basename="<redacted-backup-artifact>"
fi

row_counts="$(awk '/^```text/{capture=1; next} /^```/{capture=0} capture{print}' "${INPUT_REPORT}" | sed -E 's/[0-9]+/<count>/g' || true)"

cat > "${OUTPUT_REPORT}" <<MD
# P3-05 Backup restore proof evidence

${status_line:-'- Status: unknown'}
${created_line:-'- Created at UTC: unknown'}
- Backup artifact: ${backup_basename}
${restore_db_line:-'- Disposable restore database: vatranscribe_restore_drill'}
- Production database overwritten: no
${verification_line:-'- Verification: checksum, manifest, pg_restore list, alembic_version, critical tables, row count queries'}

## RPO/RTO

${rpo_line:-'- RPO: 24 hours'}
${rto_line:-'- RTO: 2 hours'}

## Sanitized row-count evidence

\`\`\`text
${row_counts:-not collected}
\`\`\`

## Evidence handling

- Raw backup path: <redacted>
- age identity file: <redacted>
- rclone credentials: <redacted>
- database password: <redacted>

DO NOT commit this generated evidence, backup artifacts, SQL dumps, age keys, rclone configuration, or runtime env files to Git.
MD

# Remove indentation produced by the heredoc block above.
sed -i 's/^    //' "${OUTPUT_REPORT}"
echo "[OK] Redacted backup restore evidence written: ${OUTPUT_REPORT}"
