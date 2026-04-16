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

usage() {
  cat <<'EOF'
Usage: run_qc_pipeline.sh [options]

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
EOF
}

log() {
  printf '[qc_pipeline] %s\n' "$*"
}

warn() {
  printf '[qc_pipeline][warn] %s\n' "$*" >&2
}

fail() {
  printf '[qc_pipeline][error] %s\n' "$*" >&2
  exit 1
}

command_exists() {
  command -v "$1" >/dev/null 2>&1
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

OUT_DIR="$WORKDIR/results/qc"
REPORT_DIR="$WORKDIR/reports"
mkdir -p "$OUT_DIR" "$OUT_DIR/retained_dataset" "$REPORT_DIR"

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

if [[ -z "$PLINK_PREFIX" && -n "$VCF_PATH" ]] && command_exists plink2; then
  log "Converting VCF to temporary PLINK binary dataset for QC."
  TMP_PREFIX="$OUT_DIR/qc_tmp_dataset"
  plink2 --vcf "$VCF_PATH" --make-bed --out "$TMP_PREFIX"
  PLINK_PREFIX="$TMP_PREFIX"
fi

if [[ -z "$PLINK_PREFIX" && -z "$VCF_PATH" ]]; then
  fail "No genotype input found. Provide --vcf or --plink-prefix, or place files under --input-root."
fi

escaped_request="$(printf '%s' "$REQUEST_TEXT" | sed 's/\\/\\\\/g; s/"/\\"/g')"
escaped_targets="$(printf '%s' "$ANALYSIS_TARGETS" | sed 's/\\/\\\\/g; s/"/\\"/g')"
cat > "$OUT_DIR/input_manifest.json" <<EOF
{
  "pipeline": "qc_pipeline",
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
  plink2 --bfile "$PLINK_PREFIX" --missing --hardy --freq --out "$OUT_DIR/plink_qc"
  executed_steps+=("plink2_missing_hardy_freq")
else
  warn "Skipping PLINK2 QC because plink2 or PLINK prefix is unavailable."
fi

if command_exists bcftools && [[ -n "$VCF_PATH" ]]; then
  log "Running bcftools stats."
  bcftools stats "$VCF_PATH" > "$OUT_DIR/bcftools.stats.txt"
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

log "QC pipeline completed successfully."
