#!/usr/bin/env bash
set -euo pipefail

WORKDIR=""
RESULTS_ROOT=""
INDEX_PATH=""
FIGURE_OUTPUT_DIR=""
SUMMARY_OUTPUT_PATH=""
TRACEABILITY_OUTPUT_DIR=""
MANIFEST_PATH=""
PIPELINE_NAME=""
TASK_ID=""
RUN_ID=""
SESSION_ID=""
JOB_ID=""
JOB_STATE=""
SUBMIT_COMMAND=""
SCHEDULER_SCRIPT_PATH=""
WRAPPER_PATH=""
STDOUT_PATH=""
STDERR_PATH=""
AUDIT_PATH=""
TITLE="geneagent V1.5 Summary Report"
FORCE="false"
FIGURE_ROOTS=()
LOG_PATHS=()

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
  --pipeline NAME         Blueprint name (qc_pipeline/pca_pipeline/grm_builder/genomic_prediction)
  --task-id ID            Task id for run context
  --run-id ID             Run id for run context
  --session-id ID         Session id for run context
  --job-id ID             Scheduler job id for diagnostics context
  --job-state STATE       Scheduler job state for diagnostics context
  --submit-command TEXT   Scheduler submit command
  --scheduler-script PATH Scheduler script path for traceability links
  --wrapper PATH          Wrapper script path for traceability links
  --stdout-path PATH      Stdout log path for traceability links
  --stderr-path PATH      Stderr log path for traceability links
  --audit-path PATH       Audit path for traceability links
  --log-path PATH         Log path for diagnostics (repeatable)
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
    --pipeline) PIPELINE_NAME="${2:-}"; shift 2 ;;
    --task-id) TASK_ID="${2:-}"; shift 2 ;;
    --run-id) RUN_ID="${2:-}"; shift 2 ;;
    --session-id) SESSION_ID="${2:-}"; shift 2 ;;
    --job-id) JOB_ID="${2:-}"; shift 2 ;;
    --job-state) JOB_STATE="${2:-}"; shift 2 ;;
    --submit-command) SUBMIT_COMMAND="${2:-}"; shift 2 ;;
    --scheduler-script) SCHEDULER_SCRIPT_PATH="${2:-}"; shift 2 ;;
    --wrapper) WRAPPER_PATH="${2:-}"; shift 2 ;;
    --stdout-path) STDOUT_PATH="${2:-}"; shift 2 ;;
    --stderr-path) STDERR_PATH="${2:-}"; shift 2 ;;
    --audit-path) AUDIT_PATH="${2:-}"; shift 2 ;;
    --log-path) LOG_PATHS+=("${2:-}"); shift 2 ;;
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

collect_args=(
  --workdir "$WORKDIR"
  --output-dir "$FIGURE_OUTPUT_DIR"
)
build_args=(
  --workdir "$WORKDIR"
  --results-root "$RESULTS_ROOT"
  --output "$INDEX_PATH"
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
if [[ -n "$PIPELINE_NAME" ]]; then
  build_args+=(--pipeline "$PIPELINE_NAME")
fi
if [[ -n "$TASK_ID" ]]; then
  build_args+=(--task-id "$TASK_ID")
fi
if [[ -n "$RUN_ID" ]]; then
  build_args+=(--run-id "$RUN_ID")
fi
if [[ -n "$SESSION_ID" ]]; then
  build_args+=(--session-id "$SESSION_ID")
fi
if [[ -n "$JOB_ID" ]]; then
  build_args+=(--job-id "$JOB_ID")
  trace_args+=(--job-id "$JOB_ID")
fi
if [[ -n "$JOB_STATE" ]]; then
  build_args+=(--job-state "$JOB_STATE")
fi
if [[ -n "$SUBMIT_COMMAND" ]]; then
  build_args+=(--submit-command "$SUBMIT_COMMAND")
  trace_args+=(--submit-command "$SUBMIT_COMMAND")
fi
if [[ -n "$SCHEDULER_SCRIPT_PATH" ]]; then
  build_args+=(--scheduler-script "$SCHEDULER_SCRIPT_PATH")
  trace_args+=(--scheduler-script "$SCHEDULER_SCRIPT_PATH")
fi
if [[ -n "$WRAPPER_PATH" ]]; then
  build_args+=(--wrapper "$WRAPPER_PATH")
  trace_args+=(--wrapper "$WRAPPER_PATH")
fi
if [[ -n "$STDOUT_PATH" ]]; then
  build_args+=(--stdout-path "$STDOUT_PATH")
  trace_args+=(--stdout-path "$STDOUT_PATH")
fi
if [[ -n "$STDERR_PATH" ]]; then
  build_args+=(--stderr-path "$STDERR_PATH")
  trace_args+=(--stderr-path "$STDERR_PATH")
fi
if [[ -n "$AUDIT_PATH" ]]; then
  build_args+=(--audit-path "$AUDIT_PATH")
  trace_args+=(--audit-path "$AUDIT_PATH")
fi
for log_path in "${LOG_PATHS[@]}"; do
  build_args+=(--log-path "$log_path")
done
if [[ "$FORCE" == "true" ]]; then
  build_args+=(--force)
  collect_args+=(--force)
  render_args+=(--force)
  trace_args+=(--force)
fi
for figure_root in "${FIGURE_ROOTS[@]}"; do
  collect_args+=(--figure-root "$figure_root")
done

build_args_force=("${build_args[@]}" --force)
render_args_force=("${render_args[@]}" --force)

log "Collecting figures."
bash "$SCRIPT_DIR/collect_figures.sh" "${collect_args[@]}"

log "Building result index (pass 1)."
bash "$SCRIPT_DIR/build_result_index.sh" "${build_args[@]}"

log "Rendering summary report."
bash "$SCRIPT_DIR/render_summary_report.sh" "${render_args[@]}"

log "Exporting traceability."
bash "$SCRIPT_DIR/export_traceability.sh" "${trace_args[@]}"

log "Refreshing result index (pass 2, include traceability outputs)."
bash "$SCRIPT_DIR/build_result_index.sh" "${build_args_force[@]}"

log "Rendering summary report (pass 2, synced with v2 index)."
bash "$SCRIPT_DIR/render_summary_report.sh" "${render_args_force[@]}"

log "Report generator completed successfully."
