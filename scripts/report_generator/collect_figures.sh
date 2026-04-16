#!/usr/bin/env bash
set -euo pipefail

WORKDIR=""
FIGURE_ROOTS=()
OUTPUT_DIR=""
FORCE="false"

usage() {
  cat <<'EOF'
Usage: collect_figures.sh [options]

Options:
  --workdir PATH          Working directory for relative defaults (default: current directory)
  --figure-root PATH      Figure directory to collect from (repeatable)
  --output-dir PATH       Destination directory for collected figures (default: workdir/results/figures)
  --force                 Allow overwriting files with the same destination name
  -h, --help              Show this help message
EOF
}

log() {
  printf '[report_generator:figures] %s\n' "$*"
}

fail() {
  printf '[report_generator:figures][error] %s\n' "$*" >&2
  exit 1
}

copy_figure() {
  local source="$1"
  local dest="$2"
  if [[ -e "$dest" && "$FORCE" != "true" ]]; then
    fail "Figure already exists: $dest. Use --force to overwrite."
  fi
  cp "$source" "$dest"
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workdir) WORKDIR="${2:-}"; shift 2 ;;
    --figure-root) FIGURE_ROOTS+=("${2:-}"); shift 2 ;;
    --output-dir) OUTPUT_DIR="${2:-}"; shift 2 ;;
    --force) FORCE="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) fail "Unknown option: $1" ;;
  esac
done

if [[ -z "$WORKDIR" ]]; then
  WORKDIR="$(pwd)"
fi
if [[ -z "$OUTPUT_DIR" ]]; then
  OUTPUT_DIR="$WORKDIR/results/figures"
fi

mkdir -p "$OUTPUT_DIR"

if [[ ${#FIGURE_ROOTS[@]} -eq 0 ]]; then
  if [[ -d "$WORKDIR/results" ]]; then
    while IFS= read -r -d '' dir; do
      FIGURE_ROOTS+=("$dir")
    done < <(find "$WORKDIR/results" -type d \( -name figures -o -name figure -o -name figs \) -print0)
  fi
fi

if [[ ${#FIGURE_ROOTS[@]} -eq 0 ]]; then
  fail "No figure roots provided or discovered."
fi

manifest_tsv="$OUTPUT_DIR/figure_index.tsv"
printf "source_root\tfigure_path\tcopied_to\n" > "$manifest_tsv"

copied=0
for root in "${FIGURE_ROOTS[@]}"; do
  [[ -d "$root" ]] || fail "Figure root does not exist: $root"
  while IFS= read -r -d '' figure; do
    dest="$OUTPUT_DIR/$(basename "$figure")"
    copy_figure "$figure" "$dest"
    printf "%s\t%s\t%s\n" "$root" "$figure" "$dest" >> "$manifest_tsv"
    copied=$((copied + 1))
  done < <(find "$root" -type f \( -name "*.png" -o -name "*.jpg" -o -name "*.jpeg" -o -name "*.svg" -o -name "*.pdf" \) -print0)
done

if [[ "$copied" -eq 0 ]]; then
  fail "No figures were found in the provided roots."
fi

log "Collected $copied figure(s) into $OUTPUT_DIR"
