#!/usr/bin/env bash
set -euo pipefail

WORKDIR=""
INPUT_ROOT=""
VCF_PATH=""
PLINK_PREFIX=""
PHENOTYPE_PATH=""
COVARIATE_PATH=""
PEDIGREE_PATH=""
ANALYSIS_TARGETS="qc,sample_qc,variant_qc"
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
PIPELINE_NAME="genotype_qc"

usage() {
  cat <<'EOF'
Usage: run_genotype_qc.sh [options]

Options:
  --workdir PATH            Working directory for outputs (default: current directory)
  --input-root PATH         Root path used for automatic input discovery (default: workdir)
  --vcf PATH                VCF or VCF.GZ genotype file
  --plink-prefix PREFIX     PLINK binary prefix (.bed/.bim/.fam)
  --phenotype PATH          Phenotype table
  --covariate PATH          Covariate table
  --pedigree PATH           Pedigree table
  --analysis-targets CSV    Analysis targets (default: qc,sample_qc,variant_qc)
  --request-text TEXT       Original request text for audit context
  --task-id ID              Task id for run context
  --run-id ID               Run id for run context
  --session-id ID           Session id for run context
  --threads INT             Tool thread count (default: remote CPU cap env, SLURM_CPUS_PER_TASK, or 1)
  --memory-mb INT           Tool memory cap in MB (default: remote cap env or 4096)
  --tmp-dir PATH            Temporary directory for tool spill files (default: workdir/tmp/genotype_qc)
  --log-dir PATH            Log directory (default: workdir/logs)
  --dry-run                 Write manifests and planned outputs without running tools
  --force                   Allow overwriting template manifest/audit files
EOF
}

log() {
  printf '[genotype_qc] %s\n' "$*"
}

warn() {
  printf '[genotype_qc][warn] %s\n' "$*" >&2
}

fail() {
  printf '[genotype_qc][error] %s\n' "$*" >&2
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
    "pedigree_path": "$(json_escape "$PEDIGREE_PATH")"
  },
  "tools": {
    "plink2": "$(json_escape "$(tool_path_or_missing plink2)")",
    "bcftools": "$(json_escape "$(tool_path_or_missing bcftools)")"
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
    "Raw genotype and phenotype inputs are read-only from this wrapper.",
    "Review QC thresholds before applying sample or variant exclusions."
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
    --phenotype) PHENOTYPE_PATH="${2:-}"; shift 2 ;;
    --covariate) COVARIATE_PATH="${2:-}"; shift 2 ;;
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
for path_value in "$WORKDIR" "$INPUT_ROOT" "$VCF_PATH" "$PLINK_PREFIX" "$PHENOTYPE_PATH" "$COVARIATE_PATH" "$PEDIGREE_PATH" "$TMP_DIR" "$LOG_DIR"; do
  if [[ -n "$path_value" ]]; then
    validate_posix_path "path" "$path_value"
  fi
done

OUT_DIR="$WORKDIR/results/qc"
REPORT_DIR="$WORKDIR/reports"
mkdir -p "$OUT_DIR" "$OUT_DIR/retained_dataset" "$REPORT_DIR" "$LOG_DIR"
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
  log "Converting VCF to temporary PLINK binary dataset for QC."
  TMP_PREFIX="$OUT_DIR/qc_tmp_dataset"
  plink2 --vcf "$VCF_PATH" --threads "$THREADS" --memory "$MEMORY_MB" --make-bed --out "$TMP_PREFIX"
  PLINK_PREFIX="$TMP_PREFIX"
fi

if [[ -z "$PLINK_PREFIX" && -z "$VCF_PATH" ]]; then
  fail "No genotype input found. Provide --vcf or --plink-prefix, or place files under --input-root."
fi

escaped_request="$(printf '%s' "$REQUEST_TEXT" | sed 's/\\/\\\\/g; s/"/\\"/g')"
escaped_targets="$(printf '%s' "$ANALYSIS_TARGETS" | sed 's/\\/\\\\/g; s/"/\\"/g')"
cat > "$OUT_DIR/input_manifest.json" <<EOF
{
  "pipeline": "genotype_qc",
  "analysis_targets": "$escaped_targets",
  "request_text": "$escaped_request",
  "vcf_path": "${VCF_PATH}",
  "plink_prefix": "${PLINK_PREFIX}",
  "phenotype_path": "${PHENOTYPE_PATH}",
  "covariate_path": "${COVARIATE_PATH}",
  "pedigree_path": "${PEDIGREE_PATH}"
}
EOF

executed_steps=()

if command_exists plink2 && [[ -n "$PLINK_PREFIX" ]]; then
  log "Running PLINK2 missingness, HWE, and allele-frequency QC."
  plink2 --bfile "$PLINK_PREFIX" --threads "$THREADS" --memory "$MEMORY_MB" --missing --hardy --freq --out "$OUT_DIR/plink_qc"
  executed_steps+=("plink2_missing_hardy_freq")
else
  warn "Skipping PLINK2 QC because plink2 or PLINK prefix is unavailable."
fi

if command_exists bcftools && [[ -n "$VCF_PATH" ]]; then
  log "Running bcftools stats."
  bcftools stats --threads "$THREADS" "$VCF_PATH" > "$OUT_DIR/bcftools.stats.txt"
  executed_steps+=("bcftools_stats")
else
  warn "Skipping bcftools stats because bcftools or VCF path is unavailable."
fi

if [[ ${#executed_steps[@]} -eq 0 ]]; then
  fail "No QC algorithm executed. Install plink2 and/or bcftools and provide compatible inputs."
fi

SAMPLE_QC_PATH="$OUT_DIR/sample_qc.tsv"
VARIANT_QC_PATH="$OUT_DIR/variant_qc.tsv"

printf "fid\tiid\tmissing_rate\n" > "$SAMPLE_QC_PATH"
if [[ -f "$OUT_DIR/plink_qc.smiss" ]]; then
  awk 'NR>1 {print $1 "\t" $2 "\t" $6}' "$OUT_DIR/plink_qc.smiss" >> "$SAMPLE_QC_PATH"
fi

printf "variant_id\tmissing_rate\talt_freq\n" > "$VARIANT_QC_PATH"
if [[ -f "$OUT_DIR/plink_qc.vmiss" && -f "$OUT_DIR/plink_qc.afreq" ]]; then
  awk '
    NR==FNR {if (FNR > 1) freq[$2]=$5; next}
    FNR>1 {
      alt="NA";
      if ($2 in freq) alt=freq[$2];
      print $2 "\t" $5 "\t" alt
    }
  ' "$OUT_DIR/plink_qc.afreq" "$OUT_DIR/plink_qc.vmiss" >> "$VARIANT_QC_PATH"
elif [[ -f "$OUT_DIR/plink_qc.vmiss" ]]; then
  awk 'NR>1 {print $2 "\t" $5 "\tNA"}' "$OUT_DIR/plink_qc.vmiss" >> "$VARIANT_QC_PATH"
fi

cat > "$OUT_DIR/retained_dataset/README.md" <<EOF
# Retained Dataset Index

This QC run generated metric tables for sample and variant filtering decisions.

- sample_qc: $(basename "$SAMPLE_QC_PATH")
- variant_qc: $(basename "$VARIANT_QC_PATH")
- plink_prefix: ${PLINK_PREFIX}
- vcf_path: ${VCF_PATH}
EOF

{
  echo "# QC Summary"
  echo
  echo "## Executed Steps"
  for step in "${executed_steps[@]}"; do
    echo "- $step"
  done
  echo
  echo "## Inputs"
  echo "- plink_prefix: ${PLINK_PREFIX:-none}"
  echo "- vcf_path: ${VCF_PATH:-none}"
  echo "- phenotype: ${PHENOTYPE_PATH:-none}"
  echo "- covariate: ${COVARIATE_PATH:-none}"
  echo "- pedigree: ${PEDIGREE_PATH:-none}"
  echo
  echo "## Output Files"
  echo "- results/qc/input_manifest.json"
  echo "- results/qc/sample_qc.tsv"
  echo "- results/qc/variant_qc.tsv"
  echo "- results/qc/retained_dataset/README.md"
  if [[ -f "$OUT_DIR/bcftools.stats.txt" ]]; then
    echo "- results/qc/bcftools.stats.txt"
  fi
} > "$REPORT_DIR/qc_summary.md"

log "Genotype QC completed successfully."
