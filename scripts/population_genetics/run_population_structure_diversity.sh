#!/usr/bin/env bash
set -euo pipefail

WORKDIR=""
INPUT_ROOT=""
VCF_PATH=""
PLINK_PREFIX=""
COVARIATE_PATH=""
POP_A_PATH=""
POP_B_PATH=""
WINDOW_SIZE="50000"
ANALYSIS_TARGETS="pca,population_structure,ld,roh,fst,pi,tajima_d"
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
PIPELINE_NAME="population_structure_diversity"

usage() {
  cat <<'EOF'
Usage: run_population_structure_diversity.sh [options]

Options:
  --workdir PATH            Working directory for outputs (default: current directory)
  --input-root PATH         Root path used for automatic input discovery (default: workdir)
  --vcf PATH                VCF or VCF.GZ genotype file
  --plink-prefix PREFIX     PLINK binary prefix (.bed/.bim/.fam)
  --covariate PATH          Covariate table for downstream model notes
  --population-a PATH       Sample list for population A (required for Fst)
  --population-b PATH       Sample list for population B (required for Fst)
  --window-size INT         Window size for pi and Tajima's D (default: 50000)
  --analysis-targets CSV    Analysis targets
  --request-text TEXT       Original request text for audit context
  --task-id ID              Task id for run context
  --run-id ID               Run id for run context
  --session-id ID           Session id for run context
  --threads INT             Tool thread count (default: remote CPU cap env, SLURM_CPUS_PER_TASK, or 1)
  --memory-mb INT           Tool memory cap in MB (default: remote cap env or 4096)
  --tmp-dir PATH            Temporary directory for tool spill files (default: workdir/tmp/population_structure_diversity)
  --log-dir PATH            Log directory (default: workdir/logs)
  --dry-run                 Write manifests and planned outputs without running tools
  --force                   Allow overwriting template manifest/audit files
EOF
}

log() {
  printf '[population_structure_diversity] %s\n' "$*"
}

warn() {
  printf '[population_structure_diversity][warn] %s\n' "$*" >&2
}

fail() {
  printf '[population_structure_diversity][error] %s\n' "$*" >&2
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
    "covariate_path": "$(json_escape "$COVARIATE_PATH")",
    "population_a": "$(json_escape "$POP_A_PATH")",
    "population_b": "$(json_escape "$POP_B_PATH")",
    "window_size": "$(json_escape "$WINDOW_SIZE")"
  },
  "tools": {
    "plink2": "$(json_escape "$(tool_path_or_missing plink2)")",
    "vcftools": "$(json_escape "$(tool_path_or_missing vcftools)")"
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
    "Raw genotype inputs and population lists are read-only from this wrapper.",
    "Population labels and structure interpretation require expert review."
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

run_vcftools() {
  local out_prefix="$1"
  shift
  if [[ "$VCF_PATH" == *.vcf.gz ]]; then
    vcftools --gzvcf "$VCF_PATH" "$@" --out "$out_prefix"
  else
    vcftools --vcf "$VCF_PATH" "$@" --out "$out_prefix"
  fi
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workdir) WORKDIR="${2:-}"; shift 2 ;;
    --input-root) INPUT_ROOT="${2:-}"; shift 2 ;;
    --vcf) VCF_PATH="${2:-}"; shift 2 ;;
    --plink-prefix) PLINK_PREFIX="${2:-}"; shift 2 ;;
    --covariate) COVARIATE_PATH="${2:-}"; shift 2 ;;
    --population-a) POP_A_PATH="${2:-}"; shift 2 ;;
    --population-b) POP_B_PATH="${2:-}"; shift 2 ;;
    --window-size) WINDOW_SIZE="${2:-}"; shift 2 ;;
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
for path_value in "$WORKDIR" "$INPUT_ROOT" "$VCF_PATH" "$PLINK_PREFIX" "$COVARIATE_PATH" "$POP_A_PATH" "$POP_B_PATH" "$TMP_DIR" "$LOG_DIR"; do
  if [[ -n "$path_value" ]]; then
    validate_posix_path "path" "$path_value"
  fi
done

OUT_DIR="$WORKDIR/results/structure"
PCA_DIR="$OUT_DIR/pca"
LD_DIR="$OUT_DIR/ld"
ROH_DIR="$OUT_DIR/roh"
POP_DIR="$OUT_DIR/popstats"
FIG_DIR="$OUT_DIR/figures"
REPORT_DIR="$WORKDIR/reports"

mkdir -p "$PCA_DIR" "$LD_DIR" "$ROH_DIR" "$POP_DIR" "$FIG_DIR" "$REPORT_DIR" "$LOG_DIR"
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

if ! command_exists plink2; then
  fail "plink2 is required for PCA, LD, and ROH analyses."
fi

if [[ -z "$PLINK_PREFIX" && -n "$VCF_PATH" ]]; then
  TMP_PREFIX="$OUT_DIR/pca_tmp_dataset"
  log "Converting VCF to temporary PLINK binary dataset."
  plink2 --vcf "$VCF_PATH" --threads "$THREADS" --memory "$MEMORY_MB" --make-bed --out "$TMP_PREFIX"
  PLINK_PREFIX="$TMP_PREFIX"
fi

if [[ -z "$PLINK_PREFIX" ]]; then
  fail "No PLINK dataset available. Provide --plink-prefix or VCF for conversion."
fi

executed_steps=()

log "Running LD pruning."
plink2 --bfile "$PLINK_PREFIX" --threads "$THREADS" --memory "$MEMORY_MB" --indep-pairwise 50 5 0.2 --out "$OUT_DIR/prune"
executed_steps+=("plink2_indep_pairwise")

cat > "$OUT_DIR/pruning_manifest.json" <<EOF
{
  "pipeline": "population_structure_diversity",
  "analysis_targets": "${ANALYSIS_TARGETS}",
  "plink_prefix": "${PLINK_PREFIX}",
  "window": 50,
  "step": 5,
  "r2_threshold": 0.2
}
EOF

if has_target "pca" || has_target "population_structure"; then
  log "Running PCA."
  plink2 --bfile "$PLINK_PREFIX" --threads "$THREADS" --memory "$MEMORY_MB" --extract "$OUT_DIR/prune.prune.in" --pca 20 --out "$PCA_DIR/pca"
  cp "$PCA_DIR/pca.eigenvec" "$PCA_DIR/eigenvec.tsv"
  cp "$PCA_DIR/pca.eigenval" "$PCA_DIR/eigenval.tsv"
  executed_steps+=("plink2_pca")
fi

if has_target "ld"; then
  log "Running LD pairwise statistics."
  plink2 --bfile "$PLINK_PREFIX" --threads "$THREADS" --memory "$MEMORY_MB" --extract "$OUT_DIR/prune.prune.in" --r2 gz --ld-window-kb 500 --ld-window 99999 --ld-window-r2 0.0 --out "$LD_DIR/ld_decay"
  executed_steps+=("plink2_r2")
fi

if has_target "roh"; then
  log "Running ROH detection."
  plink2 --bfile "$PLINK_PREFIX" --threads "$THREADS" --memory "$MEMORY_MB" --homozyg --extract "$OUT_DIR/prune.prune.in" --out "$ROH_DIR/roh"
  executed_steps+=("plink2_homozyg")
fi

if has_target "fst" || has_target "pi" || has_target "tajima_d"; then
  if [[ -z "$VCF_PATH" ]]; then
    warn "Skipping vcftools population statistics because no VCF input is available."
  elif ! command_exists vcftools; then
    warn "Skipping vcftools population statistics because vcftools is unavailable."
  else
    if has_target "fst"; then
      if [[ -n "$POP_A_PATH" && -n "$POP_B_PATH" ]]; then
        log "Running windowed Fst."
        run_vcftools "$POP_DIR/fst" --weir-fst-pop "$POP_A_PATH" --weir-fst-pop "$POP_B_PATH"
        executed_steps+=("vcftools_weir_fst")
      else
        warn "Skipping Fst because --population-a and --population-b were not provided."
      fi
    fi
    if has_target "pi"; then
      log "Running nucleotide diversity (pi)."
      run_vcftools "$POP_DIR/pi" --window-pi "$WINDOW_SIZE"
      executed_steps+=("vcftools_window_pi")
    fi
    if has_target "tajima_d"; then
      log "Running Tajima's D."
      run_vcftools "$POP_DIR/tajima" --TajimaD "$WINDOW_SIZE"
      executed_steps+=("vcftools_tajima_d")
    fi
  fi
fi

if [[ ${#executed_steps[@]} -eq 0 ]]; then
  fail "No analysis step executed."
fi

{
  echo "# Figure Index"
  echo
  echo "Generated visualization-ready outputs:"
  echo "- results/structure/pca/eigenvec.tsv"
  echo "- results/structure/pca/eigenval.tsv"
  if [[ -f "$LD_DIR/ld_decay.ld.gz" ]]; then
    echo "- results/structure/ld/ld_decay.ld.gz"
  fi
  if [[ -f "$ROH_DIR/roh.hom" ]]; then
    echo "- results/structure/roh/roh.hom"
  fi
} > "$FIG_DIR/README.md"

{
  echo "# Population Structure Summary"
  echo
  echo "## Executed Steps"
  for step in "${executed_steps[@]}"; do
    echo "- $step"
  done
  echo
  echo "## Inputs"
  echo "- plink_prefix: ${PLINK_PREFIX}"
  echo "- vcf_path: ${VCF_PATH:-none}"
  echo "- covariate: ${COVARIATE_PATH:-none}"
  echo "- request: ${REQUEST_TEXT:-none}"
} > "$REPORT_DIR/structure_summary.md"

{
  echo "# Stratification Risk Note"
  echo
  echo "- PCA should be reviewed for outlier clusters before GWAS or genomic prediction."
  echo "- If pronounced structure is observed, include principal components as covariates."
  echo "- Population-statistics outputs (Fst/pi/Tajima's D) depend on population files and should be interpreted with species-specific context."
} > "$REPORT_DIR/stratification_risk.md"

log "Population structure and diversity analysis completed successfully."
