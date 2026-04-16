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
ANALYSIS_TARGETS="gwas,heritability,genomic_prediction"
REQUEST_TEXT=""

usage() {
  cat <<'EOF'
Usage: run_genomic_prediction.sh [options]

Options:
  --workdir PATH            Working directory for outputs (default: current directory)
  --input-root PATH         Root path used for automatic input discovery (default: workdir)
  --vcf PATH                VCF or VCF.GZ genotype file
  --plink-prefix PREFIX     PLINK binary prefix (.bed/.bim/.fam)
  --phenotype PATH          Phenotype table (required)
  --covariate PATH          Covariate table
  --pedigree PATH           Pedigree table
  --trait-column NAME       Trait column name (optional hint)
  --analysis-targets CSV    Analysis targets (default: gwas,heritability,genomic_prediction)
  --request-text TEXT       Original request text for audit context
EOF
}

log() {
  printf '[genomic_prediction] %s\n' "$*"
}

warn() {
  printf '[genomic_prediction][warn] %s\n' "$*" >&2
}

fail() {
  printf '[genomic_prediction][error] %s\n' "$*" >&2
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

OUT_DIR="$WORKDIR/results/prediction"
GWAS_DIR="$OUT_DIR/gwas"
H2_DIR="$OUT_DIR/heritability"
REPORT_DIR="$WORKDIR/reports"

mkdir -p "$OUT_DIR" "$GWAS_DIR" "$H2_DIR" "$REPORT_DIR"

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

if [[ -z "$PLINK_PREFIX" && -n "$VCF_PATH" ]] && command_exists plink2; then
  TMP_PREFIX="$OUT_DIR/pred_tmp_dataset"
  log "Converting VCF to temporary PLINK binary dataset."
  plink2 --vcf "$VCF_PATH" --make-bed --out "$TMP_PREFIX"
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
  "pipeline": "genomic_prediction",
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
  echo "- GWAS backend: PLINK2 --glm."
  echo "- Trait hint: ${TRAIT_COLUMN:-auto}"
} > "$OUT_DIR/model_family.md"

cat > "$OUT_DIR/model_spec.json" <<EOF
{
  "pipeline": "genomic_prediction",
  "genotype_prefix": "${PLINK_PREFIX}",
  "phenotype_path": "${PHENOTYPE_PATH}",
  "covariate_path": "${COVARIATE_PATH}",
  "analysis_targets": "$escaped_targets",
  "trait_column": "${TRAIT_COLUMN}"
}
EOF

executed_steps=()
gwas_result_file=""

if has_target "gwas"; then
  if ! command_exists plink2; then
    warn "Skipping GWAS because plink2 is unavailable."
  else
    log "Running PLINK2 GWAS."
    gwas_cmd=(plink2 --bfile "$PLINK_PREFIX" --pheno "$PHENOTYPE_PATH" --glm hide-covar --allow-no-sex --out "$GWAS_DIR/gwas")
    if [[ -n "$COVARIATE_PATH" && -f "$COVARIATE_PATH" ]]; then
      gwas_cmd+=(--covar "$COVARIATE_PATH")
    fi
    "${gwas_cmd[@]}"
    gwas_result_file="$(find "$GWAS_DIR" -maxdepth 1 -type f -name "gwas*.glm.*" -print | head -n 1)"
    executed_steps+=("plink2_glm")
  fi
fi

if has_target "heritability" || has_target "genomic_prediction"; then
  if ! command_exists gcta64; then
    warn "Skipping GCTA heritability/prediction because gcta64 is unavailable."
  else
    log "Running GCTA GRM build + REML heritability + random-effect prediction."
    gcta64 --bfile "$PLINK_PREFIX" --make-grm --out "$H2_DIR/grm"
    gcta64 --grm "$H2_DIR/grm" --pheno "$PHENOTYPE_PATH" --reml --reml-pred-rand --out "$H2_DIR/heritability"
    executed_steps+=("gcta_make_grm")
    executed_steps+=("gcta_reml")
    executed_steps+=("gcta_reml_pred_rand")
  fi
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
  if [[ -n "$gwas_result_file" && -f "$gwas_result_file" ]]; then
    gwas_rows="$(awk 'NR>1 {count++} END {print count+0}' "$gwas_result_file")"
    echo "gwas_variant_rows\t${gwas_rows}"
  fi
  pred_rows="$(awk 'NR>1 {count++} END {print count+0}' "$OUT_DIR/predictions.tsv")"
  echo "prediction_rows\t${pred_rows}"
} > "$OUT_DIR/metrics.tsv"

{
  echo "# GWAS Results Index"
  echo
  if [[ -n "$gwas_result_file" && -f "$gwas_result_file" ]]; then
    for gwas_file in "$GWAS_DIR"/gwas*.glm.*; do
      if [[ -f "$gwas_file" ]]; then
        echo "- $gwas_file"
      fi
    done
  else
    echo "- no_gwas_result_file"
  fi
} > "$GWAS_DIR/README.md"

{
  echo "# Genomic Prediction Summary"
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
  echo "- results/prediction/gwas/README.md"
  echo "- results/prediction/predictions.tsv"
  echo "- results/prediction/validation_plan.md"
  echo "- results/prediction/metrics.tsv"
  if [[ -f "$H2_DIR/heritability.hsq" ]]; then
    echo "- results/prediction/heritability/heritability.hsq"
  fi
} > "$REPORT_DIR/genomic_prediction_summary.md"

log "Genomic prediction pipeline completed successfully."
