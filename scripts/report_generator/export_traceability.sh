#!/usr/bin/env bash
set -euo pipefail

WORKDIR=""
INPUT_MANIFEST=""
INDEX_PATH=""
OUTPUT_DIR=""
FORCE="false"

usage() {
  cat <<'EOF'
Usage: export_traceability.sh [options]

Options:
  --workdir PATH          Working directory for relative defaults (default: current directory)
  --manifest PATH         Input manifest or pipeline manifest to capture
  --index PATH            Artifact index JSON (default: workdir/results/report_index.json)
  --output-dir PATH       Destination directory for traceability files (default: workdir/results/traceability)
  --force                 Allow overwriting existing traceability files
  -h, --help              Show this help message
EOF
}

log() {
  printf '[report_generator:traceability] %s\n' "$*"
}

fail() {
  printf '[report_generator:traceability][error] %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workdir) WORKDIR="${2:-}"; shift 2 ;;
    --manifest) INPUT_MANIFEST="${2:-}"; shift 2 ;;
    --index) INDEX_PATH="${2:-}"; shift 2 ;;
    --output-dir) OUTPUT_DIR="${2:-}"; shift 2 ;;
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
if [[ -z "$OUTPUT_DIR" ]]; then
  OUTPUT_DIR="$WORKDIR/results/traceability"
fi

mkdir -p "$OUTPUT_DIR"

trace_json="$OUTPUT_DIR/traceability.json"
trace_md="$OUTPUT_DIR/traceability.md"

if [[ -e "$trace_json" && "$FORCE" != "true" ]]; then
  fail "Traceability output already exists: $trace_json. Use --force to overwrite."
fi

if [[ ! -f "$INDEX_PATH" ]]; then
  fail "Index file not found: $INDEX_PATH"
fi

if [[ -n "$INPUT_MANIFEST" && ! -f "$INPUT_MANIFEST" ]]; then
  fail "Manifest file not found: $INPUT_MANIFEST"
fi

generated_at="$(date -u +"%Y-%m-%dT%H:%M:%SZ")"

{
  printf '{\n'
  printf '  "generated_at": "%s",\n' "$generated_at"
  printf '  "workdir": "%s",\n' "$WORKDIR"
  printf '  "index_path": "%s",\n' "$INDEX_PATH"
  if [[ -n "$INPUT_MANIFEST" ]]; then
    printf '  "input_manifest": "%s"\n' "$INPUT_MANIFEST"
  else
    printf '  "input_manifest": null\n'
  fi
  printf '}\n'
} > "$trace_json"

{
  printf '# Traceability Export\n\n'
  printf '## Inputs\n\n'
  printf '- generated_at: `%s`\n' "$generated_at"
  printf '- workdir: `%s`\n' "$WORKDIR"
  printf '- index_path: `%s`\n' "$INDEX_PATH"
  if [[ -n "$INPUT_MANIFEST" ]]; then
    printf '- input_manifest: `%s`\n' "$INPUT_MANIFEST"
  else
    printf '- input_manifest: `none`\n'
  fi
  printf '\n## Intended Use\n\n'
  printf '- Preserve run context, artifact indexing, and release notes.\n'
  printf '- Feed this export into audit or release packaging workflows.\n'
} > "$trace_md"

log "Wrote traceability files to $OUTPUT_DIR"
