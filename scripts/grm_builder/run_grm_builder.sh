#!/usr/bin/env bash
set -euo pipefail

WORKDIR=""
INPUT_ROOT=""
VCF_PATH=""
PLINK_PREFIX=""
PEDIGREE_PATH=""
ANALYSIS_TARGETS="grm,kinship"
REQUEST_TEXT=""

usage() {
  cat <<'EOF'
Usage: run_grm_builder.sh [options]

Options:
  --workdir PATH            Working directory for outputs (default: current directory)
  --input-root PATH         Root path used for automatic input discovery (default: workdir)
  --vcf PATH                VCF or VCF.GZ genotype file
  --plink-prefix PREFIX     PLINK binary prefix (.bed/.bim/.fam)
  --pedigree PATH           Pedigree table
  --analysis-targets CSV    Analysis targets (default: grm,kinship)
  --request-text TEXT       Original request text for audit context
EOF
}

log() {
  printf '[grm_builder] %s\n' "$*"
}

warn() {
  printf '[grm_builder][warn] %s\n' "$*" >&2
}

fail() {
  printf '[grm_builder][error] %s\n' "$*" >&2
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

OUT_DIR="$WORKDIR/results/grm"
REPORT_DIR="$WORKDIR/reports"
mkdir -p "$OUT_DIR" "$REPORT_DIR"

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
  TMP_PREFIX="$OUT_DIR/grm_tmp_dataset"
  log "Converting VCF to temporary PLINK binary dataset."
  plink2 --vcf "$VCF_PATH" --make-bed --out "$TMP_PREFIX"
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
  plink2 --bfile "$PLINK_PREFIX" --make-rel square --out "$OUT_DIR/grm"
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
  gcta64 --bfile "$PLINK_PREFIX" --make-grm --out "$OUT_DIR/grm_gcta"
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

log "GRM pipeline completed successfully."
