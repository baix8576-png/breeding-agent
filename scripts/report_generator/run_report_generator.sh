#!/usr/bin/env bash
set -euo pipefail

WORKDIR=""
RESULTS_ROOT=""
INDEX_PATH=""
FIGURE_OUTPUT_DIR=""
SUMMARY_OUTPUT_PATH=""
TRACEABILITY_OUTPUT_DIR=""
MANIFEST_PATH=""
TITLE="geneagent V1 Summary Report"
FORCE="false"
FIGURE_ROOTS=()

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

usage() {
  cat <<'EOF'
Usage: run_report_generator.sh [options]

Options:
  --workdir PATH          Working directory for relative defaults (default: current directory)
  --results-root PATH     Results root scanned by build_result_index.sh (default: workdir/results)
  --index PATH            Artifact index path (default: workdir/results/report_index.json)
  --figure-root PATH      Figure root to collect from (repeatable)
  --figure-output-dir PATH Collected figure destination (default: workdir/results/figures)
  --summary-output PATH   Summary report markdown path (default: workdir/reports/summary_report.md)
  --traceability-dir PATH Traceability output directory (default: workdir/results/traceability)
  --manifest PATH         Optional manifest or traceability source path
  --title TEXT            Summary report title
  --force                 Allow overwriting existing outputs
  -h, --help              Show this help message
EOF
}

log() {
  printf '[report_generator:run] %s\n' "$*"
}

fail() {
  printf '[report_generator:run][error] %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workdir) WORKDIR="${2:-}"; shift 2 ;;
    --results-root) RESULTS_ROOT="${2:-}"; shift 2 ;;
    --index) INDEX_PATH="${2:-}"; shift 2 ;;
    --figure-root) FIGURE_ROOTS+=("${2:-}"); shift 2 ;;
    --figure-output-dir) FIGURE_OUTPUT_DIR="${2:-}"; shift 2 ;;
    --summary-output) SUMMARY_OUTPUT_PATH="${2:-}"; shift 2 ;;
    --traceability-dir) TRACEABILITY_OUTPUT_DIR="${2:-}"; shift 2 ;;
    --manifest) MANIFEST_PATH="${2:-}"; shift 2 ;;
    --title) TITLE="${2:-}"; shift 2 ;;
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
if [[ -z "$INDEX_PATH" ]]; then
  INDEX_PATH="$RESULTS_ROOT/report_index.json"
fi
if [[ -z "$FIGURE_OUTPUT_DIR" ]]; then
  FIGURE_OUTPUT_DIR="$WORKDIR/results/figures"
fi
if [[ -z "$SUMMARY_OUTPUT_PATH" ]]; then
  SUMMARY_OUTPUT_PATH="$WORKDIR/reports/summary_report.md"
fi
if [[ -z "$TRACEABILITY_OUTPUT_DIR" ]]; then
  TRACEABILITY_OUTPUT_DIR="$WORKDIR/results/traceability"
fi

build_args=(
  --workdir "$WORKDIR"
  --results-root "$RESULTS_ROOT"
  --output "$INDEX_PATH"
)
collect_args=(
  --workdir "$WORKDIR"
  --output-dir "$FIGURE_OUTPUT_DIR"
)
render_args=(
  --workdir "$WORKDIR"
  --index "$INDEX_PATH"
  --output "$SUMMARY_OUTPUT_PATH"
  --title "$TITLE"
)
trace_args=(
  --workdir "$WORKDIR"
  --index "$INDEX_PATH"
  --output-dir "$TRACEABILITY_OUTPUT_DIR"
)

if [[ -n "$MANIFEST_PATH" ]]; then
  build_args+=(--manifest "$MANIFEST_PATH")
  trace_args+=(--manifest "$MANIFEST_PATH")
fi
if [[ "$FORCE" == "true" ]]; then
  build_args+=(--force)
  collect_args+=(--force)
  render_args+=(--force)
  trace_args+=(--force)
fi
for figure_root in "${FIGURE_ROOTS[@]}"; do
  collect_args+=(--figure-root "$figure_root")
done

log "Building result index."
bash "$SCRIPT_DIR/build_result_index.sh" "${build_args[@]}"

log "Collecting figures."
bash "$SCRIPT_DIR/collect_figures.sh" "${collect_args[@]}"

log "Rendering summary report."
bash "$SCRIPT_DIR/render_summary_report.sh" "${render_args[@]}"

log "Exporting traceability."
bash "$SCRIPT_DIR/export_traceability.sh" "${trace_args[@]}"

log "Report generator completed successfully."
