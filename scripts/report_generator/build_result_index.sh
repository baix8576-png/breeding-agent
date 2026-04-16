#!/usr/bin/env bash
set -euo pipefail

WORKDIR=""
RESULTS_ROOT=""
OUTPUT_PATH=""
MANIFEST_PATH=""
FORCE="false"

usage() {
  cat <<'EOF'
Usage: build_result_index.sh [options]

Options:
  --workdir PATH         Working directory for relative defaults (default: current directory)
  --results-root PATH    Root directory to scan for result artifacts (default: workdir/results)
  --manifest PATH        Optional manifest or traceability file to record as the primary source
  --output PATH          Output JSON index path (default: workdir/results/report_index.json)
  --force                Allow overwriting the output file
  -h, --help             Show this help message
EOF
}

log() {
  printf '[report_generator:index] %s\n' "$*"
}

fail() {
  printf '[report_generator:index][error] %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workdir) WORKDIR="${2:-}"; shift 2 ;;
    --results-root) RESULTS_ROOT="${2:-}"; shift 2 ;;
    --manifest) MANIFEST_PATH="${2:-}"; shift 2 ;;
    --output) OUTPUT_PATH="${2:-}"; shift 2 ;;
    --force) FORCE="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) fail "Unknown option: $1" ;;
  esac
done

if [[ -z "$WORKDIR" ]]; then
  WORKDIR="$(pwd)"
fi
if [[ -z "$RESULTS_ROOT" ]]; then
  RESULTS_ROOT="$WORKDIR/results"
fi
if [[ -z "$OUTPUT_PATH" ]]; then
  OUTPUT_PATH="$RESULTS_ROOT/report_index.json"
fi

mkdir -p "$(dirname "$OUTPUT_PATH")"

if [[ -e "$OUTPUT_PATH" && "$FORCE" != "true" ]]; then
  fail "Output already exists: $OUTPUT_PATH. Use --force to overwrite."
fi
if [[ ! -d "$RESULTS_ROOT" ]]; then
  fail "Results root does not exist or is not a directory: $RESULTS_ROOT"
fi

tmp_file="${OUTPUT_PATH}.tmp.$$"
{
  printf '{\n'
  printf '  "workdir": "%s",\n' "$WORKDIR"
  printf '  "results_root": "%s",\n' "$RESULTS_ROOT"
  if [[ -n "$MANIFEST_PATH" ]]; then
    printf '  "primary_manifest": "%s",\n' "$MANIFEST_PATH"
  else
    printf '  "primary_manifest": null,\n'
  fi
  printf '  "artifacts": [\n'
  first="true"
  while IFS= read -r -d '' artifact; do
    rel_path="${artifact#"$WORKDIR"/}"
    if [[ "$first" == "true" ]]; then
      first="false"
    else
      printf ',\n'
    fi
    printf '    {"path": "%s", "name": "%s"}' "$rel_path" "$(basename "$artifact")"
  done < <(find "$RESULTS_ROOT" -type f \( -name "*.md" -o -name "*.tsv" -o -name "*.csv" -o -name "*.json" -o -name "*.txt" -o -name "*.png" -o -name "*.svg" -o -name "*.pdf" \) -print0)
  printf '\n  ]\n'
  printf '}\n'
} > "$tmp_file"

mv "$tmp_file" "$OUTPUT_PATH"
log "Wrote result index to $OUTPUT_PATH"
