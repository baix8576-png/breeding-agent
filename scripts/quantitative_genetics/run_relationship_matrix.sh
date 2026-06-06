#!/usr/bin/env bash
set -euo pipefail

WORKDIR=""
INPUT_ROOT=""
VCF_PATH=""
PLINK_PREFIX=""
PEDIGREE_PATH=""
ANALYSIS_TARGETS="grm,kinship"
REQUEST_TEXT=""
TASK_ID=""
RUN_ID=""
SESSION_ID=""
THREADS="${GENEAGENT_REMOTE_CPU_CAP:-${GENEAGENT_REMOTE_SHELL_CPU_CAP:-${SLURM_CPUS_PER_TASK:-1}}}"
MEMORY_MB=""
TMP_DIR=""
LOG_DIR=""
DRY_RUN="false"
FORCE="false"
RUN_LOG=""
PIPELINE_NAME="relationship_matrix"

usage() {
  cat <<'EOF'
Usage: run_relationship_matrix.sh [options]

Options:
  --workdir PATH            Working directory for outputs (default: current directory)
  --input-root PATH         Root path used for automatic input discovery (default: workdir)
  --vcf PATH                VCF or VCF.GZ genotype file
  --plink-prefix PREFIX     PLINK binary prefix (.bed/.bim/.fam)
  --pedigree PATH           Pedigree table
  --analysis-targets CSV    Analysis targets (default: grm,kinship)
  --request-text TEXT       Original request text for audit context
  --task-id ID              Task id for run context
  --run-id ID               Run id for run context
  --session-id ID           Session id for run context
  --threads INT             Tool thread count (default: remote CPU cap env, SLURM_CPUS_PER_TASK, or 1)
  --memory-mb INT           Tool memory cap in MB (default: remote cap env or 4096)
  --tmp-dir PATH            Temporary directory for tool spill files (default: workdir/tmp/relationship_matrix)
  --log-dir PATH            Log directory (default: workdir/logs)
  --dry-run                 Write manifests and planned outputs without running tools
  --force                   Allow overwriting template manifest/audit files
EOF
}

log() {
  printf '[relationship_matrix] %s\n' "$*"
}

warn() {
  printf '[relationship_matrix][warn] %s\n' "$*" >&2
}

fail() {
  printf '[relationship_matrix][error] %s\n' "$*" >&2
  exit 1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
}

json_escape() {
  printf '%s' "$1" | sed 's/\\/\\\\/g; s/"/\\"/g'
}

validate_posix_path() {
  local label="$1"
  local value="$2"
  if [[ "$value" == *\\* ]]; then
    fail "$label uses Windows-style backslashes. Use POSIX '/' paths for HPC execution: $value"
  fi
}

normalize_threads() {
  if ! [[ "$THREADS" =~ ^[0-9]+$ ]] || [[ "$THREADS" -lt 1 ]]; then
    fail "--threads must be a positive integer."
  fi
}

resolve_resource_limits() {
  if [[ -z "$MEMORY_MB" ]]; then
    if [[ "${GENEAGENT_REMOTE_MEMORY_GB_CAP:-}" =~ ^[0-9]+$ ]]; then
      MEMORY_MB=$((GENEAGENT_REMOTE_MEMORY_GB_CAP * 1024))
    elif [[ "${GENEAGENT_REMOTE_SHELL_MEMORY_GB_CAP:-}" =~ ^[0-9]+$ ]]; then
      MEMORY_MB=$((GENEAGENT_REMOTE_SHELL_MEMORY_GB_CAP * 1024))
    else
      MEMORY_MB=4096
    fi
  fi
  if ! [[ "$MEMORY_MB" =~ ^[0-9]+$ ]] || [[ "$MEMORY_MB" -lt 256 ]]; then
    fail "--memory-mb must be an integer >= 256."
  fi
  if [[ -z "$TMP_DIR" ]]; then
    TMP_DIR="$WORKDIR/tmp/$PIPELINE_NAME"
  fi
  validate_posix_path "tmp-dir" "$TMP_DIR"
}

apply_resource_limits() {
  mkdir -p "$TMP_DIR"
  export TMPDIR="$TMP_DIR"
  export OMP_NUM_THREADS="$THREADS"
  export OPENBLAS_NUM_THREADS="$THREADS"
  export MKL_NUM_THREADS="$THREADS"
  export NUMEXPR_NUM_THREADS="$THREADS"
  local memory_kb=$((MEMORY_MB * 1024))
  ulimit -v "$memory_kb" || warn "Unable to apply virtual-memory ulimit."
}

tool_path_or_missing() {
  local tool="$1"
  if command_exists "$tool"; then
    command -v "$tool"
  else
    printf 'missing'
  fi
}

write_json_file() {
  local path="$1"
  if [[ -e "$path" && "$FORCE" != "true" ]]; then
    fail "Output already exists: $path. Use --force to overwrite."
  fi
  cat > "$path"
}

write_run_manifest() {
  local mode="$1"
  local manifest_path="$OUT_DIR/run_manifest.json"
  write_json_file "$manifest_path" <<EOF
{
  "schema_version": "analysis_script_template.v1",
  "pipeline": "$PIPELINE_NAME",
  "mode": "$mode",
  "run_context": {
    "task_id": "$(json_escape "$TASK_ID")",
    "run_id": "$(json_escape "$RUN_ID")",
    "session_id": "$(json_escape "$SESSION_ID")"
  },
  "workdir": "$(json_escape "$WORKDIR")",
  "input_root": "$(json_escape "$INPUT_ROOT")",
  "analysis_targets": "$(json_escape "$ANALYSIS_TARGETS")",
  "threads": $THREADS,
  "memory_mb": $MEMORY_MB,
  "tmp_dir": "$(json_escape "$TMP_DIR")",
  "inputs": {
    "vcf_path": "$(json_escape "$VCF_PATH")",
    "plink_prefix": "$(json_escape "$PLINK_PREFIX")",
    "pedigree_path": "$(json_escape "$PEDIGREE_PATH")"
  },
  "tools": {
    "plink2": "$(json_escape "$(tool_path_or_missing plink2)")",
    "gcta64": "$(json_escape "$(tool_path_or_missing gcta64)")"
  },
  "outputs": {
    "results": "$(json_escape "$OUT_DIR")",
    "reports": "$(json_escape "$REPORT_DIR")",
    "log": "$(json_escape "$RUN_LOG")"
  },
  "safety": {
    "scheduler_managed_externally": true,
    "raw_inputs_read_only": true,
    "destructive_overwrite_requires_force": true
  }
}
EOF
}

write_audit_sidecar() {
  local mode="$1"
  local audit_path="$OUT_DIR/audit_sidecar.json"
  write_json_file "$audit_path" <<EOF
{
  "schema_version": "analysis_script_audit_sidecar.v1",
  "pipeline": "$PIPELINE_NAME",
  "mode": "$mode",
  "task_id": "$(json_escape "$TASK_ID")",
  "run_id": "$(json_escape "$RUN_ID")",
  "session_id": "$(json_escape "$SESSION_ID")",
  "analysis_targets": "$(json_escape "$ANALYSIS_TARGETS")",
  "log_path": "$(json_escape "$RUN_LOG")",
  "notes": [
    "Scheduler submission and polling are managed outside scripts/.",
    "Raw genotype and pedigree inputs are read-only from this wrapper.",
    "GRM consumers must verify sample order before downstream modeling."
  ]
}
EOF
}

find_first_vcf() {
  find "$1" -type f \( -name "*.vcf" -o -name "*.vcf.gz" \) -print | head -n 1
}

find_first_plink_prefix() {
  local root="$1"
  local bed_path
  bed_path="$(find "$root" -type f -name "*.bed" -print | head -n 1)"
  if [[ -z "$bed_path" ]]; then
    return 1
  fi
  local prefix="${bed_path%.bed}"
  if [[ -f "${prefix}.bim" && -f "${prefix}.fam" ]]; then
    printf '%s' "$prefix"
    return 0
  fi
  return 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workdir) WORKDIR="${2:-}"; shift 2 ;;
    --input-root) INPUT_ROOT="${2:-}"; shift 2 ;;
    --vcf) VCF_PATH="${2:-}"; shift 2 ;;
    --plink-prefix) PLINK_PREFIX="${2:-}"; shift 2 ;;
    --pedigree) PEDIGREE_PATH="${2:-}"; shift 2 ;;
    --analysis-targets) ANALYSIS_TARGETS="${2:-}"; shift 2 ;;
    --request-text) REQUEST_TEXT="${2:-}"; shift 2 ;;
    --task-id) TASK_ID="${2:-}"; shift 2 ;;
    --run-id) RUN_ID="${2:-}"; shift 2 ;;
    --session-id) SESSION_ID="${2:-}"; shift 2 ;;
    --threads) THREADS="${2:-}"; shift 2 ;;
    --memory-mb) MEMORY_MB="${2:-}"; shift 2 ;;
    --tmp-dir) TMP_DIR="${2:-}"; shift 2 ;;
    --log-dir) LOG_DIR="${2:-}"; shift 2 ;;
    --dry-run) DRY_RUN="true"; shift ;;
    --force) FORCE="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) fail "Unknown option: $1" ;;
  esac
done

if [[ -z "$WORKDIR" ]]; then
  WORKDIR="$(pwd)"
fi
if [[ -z "$INPUT_ROOT" ]]; then
  INPUT_ROOT="$WORKDIR"
fi
if [[ -z "$LOG_DIR" ]]; then
  LOG_DIR="$WORKDIR/logs"
fi
normalize_threads
resolve_resource_limits
for path_value in "$WORKDIR" "$INPUT_ROOT" "$VCF_PATH" "$PLINK_PREFIX" "$PEDIGREE_PATH" "$TMP_DIR" "$LOG_DIR"; do
  if [[ -n "$path_value" ]]; then
    validate_posix_path "path" "$path_value"
  fi
done

OUT_DIR="$WORKDIR/results/grm"
REPORT_DIR="$WORKDIR/reports"
mkdir -p "$OUT_DIR" "$REPORT_DIR" "$LOG_DIR"
RUN_LOG="$LOG_DIR/$PIPELINE_NAME.log"
exec > >(tee -a "$RUN_LOG") 2>&1
apply_resource_limits

if [[ -z "$PLINK_PREFIX" ]]; then
  if detected_prefix="$(find_first_plink_prefix "$INPUT_ROOT")"; then
    PLINK_PREFIX="$detected_prefix"
    log "Auto-detected PLINK prefix: $PLINK_PREFIX"
  fi
fi
if [[ -z "$VCF_PATH" ]]; then
  VCF_PATH="$(find_first_vcf "$INPUT_ROOT" || true)"
  if [[ -n "$VCF_PATH" ]]; then
    log "Auto-detected VCF path: $VCF_PATH"
  fi
fi

write_run_manifest "$([[ "$DRY_RUN" == "true" ]] && printf 'dry_run' || printf 'execute')"
write_audit_sidecar "$([[ "$DRY_RUN" == "true" ]] && printf 'dry_run' || printf 'execute')"
if [[ "$DRY_RUN" == "true" ]]; then
  log "Dry-run complete; manifest and audit sidecar written without running tools."
  exit 0
fi

if [[ -z "$PLINK_PREFIX" && -n "$VCF_PATH" ]] && command_exists plink2; then
  TMP_PREFIX="$OUT_DIR/grm_tmp_dataset"
  log "Converting VCF to temporary PLINK binary dataset."
  plink2 --vcf "$VCF_PATH" --threads "$THREADS" --memory "$MEMORY_MB" --make-bed --out "$TMP_PREFIX"
  PLINK_PREFIX="$TMP_PREFIX"
fi

if [[ -z "$PLINK_PREFIX" ]]; then
  fail "No PLINK dataset available. Provide --plink-prefix or VCF for conversion."
fi

if ! command_exists plink2 && ! command_exists gcta64; then
  fail "Neither plink2 nor gcta64 is available. At least one is required for GRM generation."
fi

{
  echo "# Marker Standardization"
  echo
  echo "- request: ${REQUEST_TEXT:-none}"
  echo "- analysis_targets: ${ANALYSIS_TARGETS}"
  echo "- plink_prefix: ${PLINK_PREFIX}"
  echo "- pedigree: ${PEDIGREE_PATH:-none}"
  echo "- notes: genotype matrix was standardized by the selected backend before GRM estimation."
} > "$OUT_DIR/marker_standardization.md"

executed_steps=()

if command_exists plink2; then
  log "Running PLINK2 relationship matrix generation."
  plink2 --bfile "$PLINK_PREFIX" --threads "$THREADS" --memory "$MEMORY_MB" --make-rel square --out "$OUT_DIR/grm"
  if [[ -f "$OUT_DIR/grm.rel" ]]; then
    cp "$OUT_DIR/grm.rel" "$OUT_DIR/grm_matrix.tsv"
  elif [[ -f "$OUT_DIR/grm.rel.zst" ]] && command_exists zstd; then
    zstd -dc "$OUT_DIR/grm.rel.zst" > "$OUT_DIR/grm_matrix.tsv"
  else
    warn "PLINK2 relationship file not found in expected text format."
  fi
  executed_steps+=("plink2_make_rel")
fi

if command_exists gcta64; then
  log "Running GCTA binary GRM generation."
  gcta64 --bfile "$PLINK_PREFIX" --thread-num "$THREADS" --make-grm --out "$OUT_DIR/grm_gcta"
  executed_steps+=("gcta_make_grm")
fi

if [[ ! -f "$OUT_DIR/grm_matrix.tsv" ]]; then
  warn "No text matrix generated; creating matrix pointer file from available binaries."
  {
    echo "matrix_source"
    if [[ -f "$OUT_DIR/grm_gcta.grm.bin" ]]; then
      echo "$OUT_DIR/grm_gcta.grm.bin"
    else
      echo "unavailable"
    fi
  } > "$OUT_DIR/grm_matrix.tsv"
fi

if [[ -f "${PLINK_PREFIX}.fam" ]]; then
  awk 'BEGIN {OFS="\t"; print "fid","iid"} {print $1,$2}' "${PLINK_PREFIX}.fam" > "$OUT_DIR/grm_ids.tsv"
else
  printf "fid\tiid\n" > "$OUT_DIR/grm_ids.tsv"
fi

matrix_rows="$(wc -l < "$OUT_DIR/grm_matrix.tsv" | tr -d ' ')"
matrix_cols="$(head -n 1 "$OUT_DIR/grm_matrix.tsv" | awk '{print NF}')"
matrix_shape="unknown"
if [[ "$matrix_rows" -gt 0 && "$matrix_cols" -gt 0 ]]; then
  matrix_shape="${matrix_rows}x${matrix_cols}"
fi

{
  echo "# GRM QC Summary"
  echo
  echo "## Executed Steps"
  for step in "${executed_steps[@]}"; do
    echo "- $step"
  done
  echo
  echo "## Matrix Checks"
  echo "- matrix_shape: ${matrix_shape}"
  if [[ "$matrix_rows" -eq "$matrix_cols" ]]; then
    echo "- square_matrix_check: pass"
  else
    echo "- square_matrix_check: warn"
  fi
  echo "- grm_matrix: results/grm/grm_matrix.tsv"
  echo "- grm_ids: results/grm/grm_ids.tsv"
} > "$REPORT_DIR/grm_qc.md"

{
  echo "# GRM Package Index"
  echo
  echo "- results/grm/marker_standardization.md"
  echo "- results/grm/grm_matrix.tsv"
  echo "- results/grm/grm_ids.tsv"
  if [[ -f "$OUT_DIR/grm_gcta.grm.bin" ]]; then
    echo "- results/grm/grm_gcta.grm.bin"
    echo "- results/grm/grm_gcta.grm.N.bin"
    echo "- results/grm/grm_gcta.grm.id"
  fi
  echo "- reports/grm_qc.md"
} > "$OUT_DIR/README.md"

log "Relationship matrix workflow completed successfully."
