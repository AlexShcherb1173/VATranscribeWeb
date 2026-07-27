#!/usr/bin/env bash
set -Eeuo pipefail

INPUT_FILE="${1:-}"
OUTPUT_FILE="${2:-}"

if [ -z "$INPUT_FILE" ] || [ -z "$OUTPUT_FILE" ]; then
  echo "Usage: $0 <input-file> <output-file>" >&2
  exit 2
fi

if [ ! -f "$INPUT_FILE" ]; then
  echo "[FAIL] Input file not found: $INPUT_FILE" >&2
  exit 1
fi

mkdir -p "$(dirname "$OUTPUT_FILE")"
cp "$INPUT_FILE" "$OUTPUT_FILE"

# Generic redaction for accidental secrets, private registry URLs, tokens, and local runtime paths.
sed -i -E 's#(token|secret|password|passwd|api[_-]?key|authorization|credential|private[_-]?key)([=: ]+)[^ ,;\"\047]+#\1\2<redacted>#Ig' "$OUTPUT_FILE"
sed -i -E 's#(https?://)[^/@[:space:]]+:[^/@[:space:]]+@#\1<redacted>:<redacted>@#g' "$OUTPUT_FILE"
sed -i -E 's#(registry\.npmjs\.org/)[^[:space:]]+#\1<redacted>#g' "$OUTPUT_FILE"
sed -i -E 's#(/opt/vatranscribe/secrets/)[^[:space:]]+#\1<redacted>#g' "$OUTPUT_FILE"
sed -i -E 's#(DATABASE_URL=).*#\1<redacted>#g' "$OUTPUT_FILE"
sed -i -E 's#(SENTRY_DSN=).*#\1<redacted>#g' "$OUTPUT_FILE"
sed -i -E 's#(NPM_TOKEN=).*#\1<redacted>#g' "$OUTPUT_FILE"
sed -i -E 's#(GITHUB_TOKEN=).*#\1<redacted>#g' "$OUTPUT_FILE"

cat >>"$OUTPUT_FILE" <<'EOF_NOTICE'

## Redaction notice

This is a sanitized evidence summary. DO NOT commit raw scanner outputs, SBOM files, private registry URLs, real credentials, runtime env files, or unreviewed secret findings to the repository.
EOF_NOTICE

chmod 600 "$OUTPUT_FILE" 2>/dev/null || true

echo "[OK] Redacted supply-chain evidence written: $OUTPUT_FILE"
