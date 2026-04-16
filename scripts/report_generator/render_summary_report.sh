#!/usr/bin/env bash
set -euo pipefail

WORKDIR=""
INDEX_PATH=""
OUTPUT_PATH=""
TITLE="geneagent V1 Summary Report"
FORCE="false"

usage() {
  cat <<'EOF'
Usage: render_summary_report.sh [options]

Options:
  --workdir PATH        Working directory for relative defaults (default: current directory)
  --index PATH          Report index JSON (default: workdir/results/report_index.json)
  --output PATH         Output markdown report path (default: workdir/reports/summary_report.md)
  --title TEXT          Report title
  --force               Allow overwriting the output file
  -h, --help            Show this help message
EOF
}

log() {
  printf '[report_generator:render] %s\n' "$*"
}

fail() {
  printf '[report_generator:render][error] %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workdir) WORKDIR="${2:-}"; shift 2 ;;
    --index) INDEX_PATH="${2:-}"; shift 2 ;;
    --output) OUTPUT_PATH="${2:-}"; shift 2 ;;
    --title) TITLE="${2:-}"; shift 2 ;;
    --force) FORCE="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) fail "Unknown option: $1" ;;
  esac
done

if [[ -z "$WORKDIR" ]]; then
  WORKDIR="$(pwd)"
fi
if [[ -z "$INDEX_PATH" ]]; then
  INDEX_PATH="$WORKDIR/results/report_index.json"
fi
if [[ -z "$OUTPUT_PATH" ]]; then
  OUTPUT_PATH="$WORKDIR/reports/summary_report.md"
fi

mkdir -p "$(dirname "$OUTPUT_PATH")"

if [[ -e "$OUTPUT_PATH" && "$FORCE" != "true" ]]; then
  fail "Output already exists: $OUTPUT_PATH. Use --force to overwrite."
fi
if [[ ! -f "$INDEX_PATH" ]]; then
  fail "Index file not found: $INDEX_PATH"
fi

artifact_count="$(grep -c '"path":' "$INDEX_PATH" || true)"

{
  printf '# %s\n\n' "$TITLE"
  printf '## Inputs\n\n'
  printf '- Index file: `%s`\n' "$INDEX_PATH"
  printf '- Workdir: `%s`\n' "$WORKDIR"
  printf '\n## Artifact Count\n\n'
  printf '- Declared artifacts: `%s`\n' "${artifact_count:-0}"
  printf '\n## Render Notes\n\n'
  printf '- This report only packages declared outputs.\n'
  printf '- It does not overwrite existing results unless `--force` is used.\n'
  printf '- Review the index and traceability files before treating this as a release report.\n'
} > "$OUTPUT_PATH"

log "Wrote summary report to $OUTPUT_PATH"
