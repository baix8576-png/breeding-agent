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

usage() {
  cat <<'EOF'
Usage: run_pca_pipeline.sh [options]

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
EOF
}

log() {
  printf '[pca_pipeline] %s\n' "$*"
}

warn() {
  printf '[pca_pipeline][warn] %s\n' "$*" >&2
}

fail() {
  printf '[pca_pipeline][error] %s\n' "$*" >&2
  exit 1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
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

OUT_DIR="$WORKDIR/results/structure"
PCA_DIR="$OUT_DIR/pca"
LD_DIR="$OUT_DIR/ld"
ROH_DIR="$OUT_DIR/roh"
POP_DIR="$OUT_DIR/popstats"
FIG_DIR="$OUT_DIR/figures"
REPORT_DIR="$WORKDIR/reports"

mkdir -p "$PCA_DIR" "$LD_DIR" "$ROH_DIR" "$POP_DIR" "$FIG_DIR" "$REPORT_DIR"

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

if ! command_exists plink2; then
  fail "plink2 is required for PCA, LD, and ROH analyses."
fi

if [[ -z "$PLINK_PREFIX" && -n "$VCF_PATH" ]]; then
  TMP_PREFIX="$OUT_DIR/pca_tmp_dataset"
  log "Converting VCF to temporary PLINK binary dataset."
  plink2 --vcf "$VCF_PATH" --make-bed --out "$TMP_PREFIX"
  PLINK_PREFIX="$TMP_PREFIX"
fi

if [[ -z "$PLINK_PREFIX" ]]; then
  fail "No PLINK dataset available. Provide --plink-prefix or VCF for conversion."
fi

executed_steps=()

log "Running LD pruning."
plink2 --bfile "$PLINK_PREFIX" --indep-pairwise 50 5 0.2 --out "$OUT_DIR/prune"
executed_steps+=("plink2_indep_pairwise")

cat > "$OUT_DIR/pruning_manifest.json" <<EOF
{
  "pipeline": "pca_pipeline",
  "analysis_targets": "${ANALYSIS_TARGETS}",
  "plink_prefix": "${PLINK_PREFIX}",
  "window": 50,
  "step": 5,
  "r2_threshold": 0.2
}
EOF

if has_target "pca" || has_target "population_structure"; then
  log "Running PCA."
  plink2 --bfile "$PLINK_PREFIX" --extract "$OUT_DIR/prune.prune.in" --pca 20 --out "$PCA_DIR/pca"
  cp "$PCA_DIR/pca.eigenvec" "$PCA_DIR/eigenvec.tsv"
  cp "$PCA_DIR/pca.eigenval" "$PCA_DIR/eigenval.tsv"
  executed_steps+=("plink2_pca")
fi

if has_target "ld"; then
  log "Running LD pairwise statistics."
  plink2 --bfile "$PLINK_PREFIX" --extract "$OUT_DIR/prune.prune.in" --r2 gz --ld-window-kb 500 --ld-window 99999 --ld-window-r2 0.0 --out "$LD_DIR/ld_decay"
  executed_steps+=("plink2_r2")
fi

if has_target "roh"; then
  log "Running ROH detection."
  plink2 --bfile "$PLINK_PREFIX" --extract "$OUT_DIR/prune.prune.in" --homozyg --out "$ROH_DIR/roh"
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

log "PCA and population-statistics pipeline completed successfully."
