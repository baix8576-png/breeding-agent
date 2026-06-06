#!/usr/bin/env bash
set -euo pipefail

WORKDIR=""
INPUT_ROOT=""
VCF_PATH=""
PLINK_PREFIX=""
PHENOTYPE_PATH=""
COVARIATE_PATH=""
PEDIGREE_PATH=""
TRAIT_COLUMN=""
ANALYSIS_TARGETS="heritability,genomic_prediction"
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
PIPELINE_NAME="breeding_value_prediction"

usage() {
  cat <<'EOF'
Usage: run_breeding_value_prediction.sh [options]

Options:
  --workdir PATH            Working directory for outputs (default: current directory)
  --input-root PATH         Root path used for automatic input discovery (default: workdir)
  --vcf PATH                VCF or VCF.GZ genotype file
  --plink-prefix PREFIX     PLINK binary prefix (.bed/.bim/.fam)
  --phenotype PATH          Phenotype table (required)
  --covariate PATH          Covariate table
  --pedigree PATH           Pedigree table
  --trait-column NAME       Trait column name (optional hint)
  --analysis-targets CSV    Analysis targets (default: heritability,genomic_prediction)
  --request-text TEXT       Original request text for audit context
  --task-id ID              Task id for run context
  --run-id ID               Run id for run context
  --session-id ID           Session id for run context
  --threads INT             Tool thread count (default: remote CPU cap env, SLURM_CPUS_PER_TASK, or 1)
  --memory-mb INT           Tool memory cap in MB (default: remote cap env or 4096)
  --tmp-dir PATH            Temporary directory for tool spill files (default: workdir/tmp/breeding_value_prediction)
  --log-dir PATH            Log directory (default: workdir/logs)
  --dry-run                 Write manifests and planned outputs without running tools
  --force                   Allow overwriting template manifest/audit files
EOF
}

log() {
  printf '[breeding_value_prediction] %s\n' "$*"
}

warn() {
  printf '[breeding_value_prediction][warn] %s\n' "$*" >&2
}

fail() {
  printf '[breeding_value_prediction][error] %s\n' "$*" >&2
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
    "phenotype_path": "$(json_escape "$PHENOTYPE_PATH")",
    "covariate_path": "$(json_escape "$COVARIATE_PATH")",
    "pedigree_path": "$(json_escape "$PEDIGREE_PATH")",
    "trait_column": "$(json_escape "$TRAIT_COLUMN")"
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
    "Raw genotype, phenotype, covariate, and pedigree inputs are read-only from this wrapper.",
    "Prediction metrics require validation before breeding decisions."
  ]
}
EOF
}

has_target() {
  local target="$1"
  [[ ",${ANALYSIS_TARGETS}," == *",${target},"* ]]
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

find_first_phenotype() {
  find "$1" -type f \( -name "*pheno*.tsv" -o -name "*pheno*.csv" -o -name "*trait*.tsv" -o -name "*trait*.csv" \) -print | head -n 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workdir) WORKDIR="${2:-}"; shift 2 ;;
    --input-root) INPUT_ROOT="${2:-}"; shift 2 ;;
    --vcf) VCF_PATH="${2:-}"; shift 2 ;;
    --plink-prefix) PLINK_PREFIX="${2:-}"; shift 2 ;;
    --phenotype) PHENOTYPE_PATH="${2:-}"; shift 2 ;;
    --covariate) COVARIATE_PATH="${2:-}"; shift 2 ;;
    --pedigree) PEDIGREE_PATH="${2:-}"; shift 2 ;;
    --trait-column) TRAIT_COLUMN="${2:-}"; shift 2 ;;
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
for path_value in "$WORKDIR" "$INPUT_ROOT" "$VCF_PATH" "$PLINK_PREFIX" "$PHENOTYPE_PATH" "$COVARIATE_PATH" "$PEDIGREE_PATH" "$TMP_DIR" "$LOG_DIR"; do
  if [[ -n "$path_value" ]]; then
    validate_posix_path "path" "$path_value"
  fi
done

OUT_DIR="$WORKDIR/results/prediction"
H2_DIR="$OUT_DIR/heritability"
REPORT_DIR="$WORKDIR/reports"

mkdir -p "$OUT_DIR" "$H2_DIR" "$REPORT_DIR" "$LOG_DIR"
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
if [[ -z "$PHENOTYPE_PATH" ]]; then
  PHENOTYPE_PATH="$(find_first_phenotype "$INPUT_ROOT" || true)"
  if [[ -n "$PHENOTYPE_PATH" ]]; then
    log "Auto-detected phenotype table: $PHENOTYPE_PATH"
  fi
fi

write_run_manifest "$([[ "$DRY_RUN" == "true" ]] && printf 'dry_run' || printf 'execute')"
write_audit_sidecar "$([[ "$DRY_RUN" == "true" ]] && printf 'dry_run' || printf 'execute')"
if [[ "$DRY_RUN" == "true" ]]; then
  log "Dry-run complete; manifest and audit sidecar written without running tools."
  exit 0
fi

if [[ -z "$PLINK_PREFIX" && -n "$VCF_PATH" ]] && command_exists plink2; then
  TMP_PREFIX="$OUT_DIR/pred_tmp_dataset"
  log "Converting VCF to temporary PLINK binary dataset."
  plink2 --vcf "$VCF_PATH" --threads "$THREADS" --memory "$MEMORY_MB" --make-bed --out "$TMP_PREFIX"
  PLINK_PREFIX="$TMP_PREFIX"
fi

if [[ -z "$PLINK_PREFIX" ]]; then
  fail "No PLINK dataset available. Provide --plink-prefix or VCF for conversion."
fi
if [[ -z "$PHENOTYPE_PATH" || ! -f "$PHENOTYPE_PATH" ]]; then
  fail "Phenotype table is required for genomic prediction."
fi

escaped_request="$(printf '%s' "$REQUEST_TEXT" | sed 's/\\/\\\\/g; s/"/\\"/g')"
escaped_targets="$(printf '%s' "$ANALYSIS_TARGETS" | sed 's/\\/\\\\/g; s/"/\\"/g')"
cat > "$OUT_DIR/cohort_alignment.json" <<EOF
{
  "pipeline": "breeding_value_prediction",
  "analysis_targets": "$escaped_targets",
  "request_text": "$escaped_request",
  "plink_prefix": "${PLINK_PREFIX}",
  "phenotype_path": "${PHENOTYPE_PATH}",
  "covariate_path": "${COVARIATE_PATH}",
  "pedigree_path": "${PEDIGREE_PATH}",
  "trait_column": "${TRAIT_COLUMN}"
}
EOF

{
  echo "# Model Family Selection"
  echo
  echo "- Default backbone: GBLUP-compatible path (GCTA REML + random-effect prediction)."
  echo "- Association mapping is handled by scripts/association_mapping/run_gwas.sh."
  echo "- Trait hint: ${TRAIT_COLUMN:-auto}"
} > "$OUT_DIR/model_family.md"

cat > "$OUT_DIR/model_spec.json" <<EOF
{
  "pipeline": "breeding_value_prediction",
  "genotype_prefix": "${PLINK_PREFIX}",
  "phenotype_path": "${PHENOTYPE_PATH}",
  "covariate_path": "${COVARIATE_PATH}",
  "analysis_targets": "$escaped_targets",
  "trait_column": "${TRAIT_COLUMN}"
}
EOF

executed_steps=()

if has_target "heritability" || has_target "genomic_prediction"; then
  if ! command_exists gcta64; then
    warn "Skipping GCTA heritability/prediction because gcta64 is unavailable."
  else
    log "Running GCTA GRM build + REML heritability + random-effect prediction."
    gcta64 --bfile "$PLINK_PREFIX" --thread-num "$THREADS" --make-grm --out "$H2_DIR/grm"
    gcta64 --grm "$H2_DIR/grm" --thread-num "$THREADS" --pheno "$PHENOTYPE_PATH" --reml --reml-pred-rand --out "$H2_DIR/heritability"
    executed_steps+=("gcta_make_grm")
    executed_steps+=("gcta_reml")
    executed_steps+=("gcta_reml_pred_rand")
  fi
fi

if [[ "${#executed_steps[@]}" -eq 0 ]]; then
  fail "No breeding value prediction step executed. Ensure requested targets are valid and required tools (gcta64) are available."
fi

if [[ -f "$H2_DIR/heritability.indi.blp" ]]; then
  awk 'BEGIN {OFS="\t"; print "fid","iid","gebv"} NR>1 {print $1,$2,$3}' "$H2_DIR/heritability.indi.blp" > "$OUT_DIR/predictions.tsv"
elif [[ -f "${PLINK_PREFIX}.fam" ]]; then
  warn "Prediction file from GCTA is unavailable; generating fallback sample list with missing GEBV."
  awk 'BEGIN {OFS="\t"; print "fid","iid","gebv"} {print $1,$2,"NA"}' "${PLINK_PREFIX}.fam" > "$OUT_DIR/predictions.tsv"
else
  printf "fid\tiid\tgebv\n" > "$OUT_DIR/predictions.tsv"
fi

{
  echo "# Validation Plan"
  echo
  echo "- Use k-fold cross validation for production runs."
  echo "- Track predictive correlation and calibration bias by cohort."
  echo "- This run stores immediate diagnostics for downstream audit."
} > "$OUT_DIR/validation_plan.md"

{
  echo "metric\tvalue"
  if [[ -f "$H2_DIR/heritability.hsq" ]]; then
    h2_value="$(awk '$1=="V(G)/Vp" {print $2}' "$H2_DIR/heritability.hsq" | head -n 1)"
    if [[ -n "$h2_value" ]]; then
      echo "heritability_h2\t${h2_value}"
    fi
  fi
  pred_rows="$(awk 'NR>1 {count++} END {print count+0}' "$OUT_DIR/predictions.tsv")"
  echo "prediction_rows\t${pred_rows}"
} > "$OUT_DIR/metrics.tsv"

{
  echo "# Breeding Value Prediction Summary"
  echo
  echo "## Executed Steps"
  for step in "${executed_steps[@]}"; do
    echo "- $step"
  done
  echo
  echo "## Inputs"
  echo "- plink_prefix: ${PLINK_PREFIX}"
  echo "- phenotype: ${PHENOTYPE_PATH}"
  echo "- covariate: ${COVARIATE_PATH:-none}"
  echo "- pedigree: ${PEDIGREE_PATH:-none}"
  echo
  echo "## Outputs"
  echo "- results/prediction/cohort_alignment.json"
  echo "- results/prediction/model_family.md"
  echo "- results/prediction/model_spec.json"
  echo "- results/prediction/predictions.tsv"
  echo "- results/prediction/validation_plan.md"
  echo "- results/prediction/metrics.tsv"
  if [[ -f "$H2_DIR/heritability.hsq" ]]; then
    echo "- results/prediction/heritability/heritability.hsq"
  fi
} > "$REPORT_DIR/genomic_prediction_summary.md"

log "Breeding value prediction workflow completed successfully."
