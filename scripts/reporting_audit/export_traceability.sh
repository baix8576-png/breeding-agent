#!/usr/bin/env bash
set -euo pipefail

WORKDIR=""
INPUT_MANIFEST=""
INDEX_PATH=""
OUTPUT_DIR=""
JOB_ID=""
SUBMIT_COMMAND=""
SCHEDULER_SCRIPT_PATH=""
WRAPPER_PATH=""
STDOUT_PATH=""
STDERR_PATH=""
AUDIT_PATH=""
FORCE="false"

usage() {
  cat <<'EOF'
Usage: export_traceability.sh [options]

Options:
  --workdir PATH            Working directory for relative defaults (default: current directory)
  --manifest PATH           Input manifest or pipeline manifest to capture
  --index PATH              Artifact index JSON (default: workdir/results/report_index.json)
  --output-dir PATH         Destination directory for traceability files (default: workdir/results/traceability)
  --job-id ID               Scheduler job id for traceability context
  --submit-command TEXT     Scheduler submit command
  --scheduler-script PATH   Scheduler script path
  --wrapper PATH            Wrapper script path
  --stdout-path PATH        Stdout log path
  --stderr-path PATH        Stderr log path
  --audit-path PATH         Audit record path
  --force                   Allow overwriting existing traceability files
  -h, --help                Show this help message
EOF
}

log() {
  printf '[report_generator:traceability] %s\n' "$*"
}

fail() {
  printf '[report_generator:traceability][error] %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workdir) WORKDIR="${2:-}"; shift 2 ;;
    --manifest) INPUT_MANIFEST="${2:-}"; shift 2 ;;
    --index) INDEX_PATH="${2:-}"; shift 2 ;;
    --output-dir) OUTPUT_DIR="${2:-}"; shift 2 ;;
    --job-id) JOB_ID="${2:-}"; shift 2 ;;
    --submit-command) SUBMIT_COMMAND="${2:-}"; shift 2 ;;
    --scheduler-script) SCHEDULER_SCRIPT_PATH="${2:-}"; shift 2 ;;
    --wrapper) WRAPPER_PATH="${2:-}"; shift 2 ;;
    --stdout-path) STDOUT_PATH="${2:-}"; shift 2 ;;
    --stderr-path) STDERR_PATH="${2:-}"; shift 2 ;;
    --audit-path) AUDIT_PATH="${2:-}"; shift 2 ;;
    --force) FORCE="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) fail "Unknown option: $1" ;;
  esac
done

if [[ -z "$WORKDIR" ]]; then
  WORKDIR="$(pwd)"
fi
if [[ -z "$INDEX_PATH" ]]; then
  INDEX_PATH="$WORKDIR/results/report_index.json"
fi
if [[ -z "$OUTPUT_DIR" ]]; then
  OUTPUT_DIR="$WORKDIR/results/traceability"
fi

mkdir -p "$OUTPUT_DIR"

trace_json="$OUTPUT_DIR/traceability.json"
trace_md="$OUTPUT_DIR/traceability.md"

if [[ -e "$trace_json" && "$FORCE" != "true" ]]; then
  fail "Traceability output already exists: $trace_json. Use --force to overwrite."
fi
if [[ ! -f "$INDEX_PATH" ]]; then
  fail "Index file not found: $INDEX_PATH"
fi
if [[ -n "$INPUT_MANIFEST" && ! -f "$INPUT_MANIFEST" ]]; then
  fail "Manifest file not found: $INPUT_MANIFEST"
fi

python - "$WORKDIR" "$INDEX_PATH" "$trace_json" "$trace_md" "$INPUT_MANIFEST" "$JOB_ID" "$SUBMIT_COMMAND" "$SCHEDULER_SCRIPT_PATH" "$WRAPPER_PATH" "$STDOUT_PATH" "$STDERR_PATH" "$AUDIT_PATH" <<'PY'
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import sys

workdir = Path(sys.argv[1]).resolve()
index_path = Path(sys.argv[2]).resolve()
trace_json_path = Path(sys.argv[3]).resolve()
trace_md_path = Path(sys.argv[4]).resolve()
manifest = sys.argv[5].strip()
job_id = sys.argv[6].strip()
submit_command = sys.argv[7].strip()
scheduler_script = sys.argv[8].strip()
wrapper_path = sys.argv[9].strip()
stdout_path = sys.argv[10].strip()
stderr_path = sys.argv[11].strip()
audit_path = sys.argv[12].strip()

def normalize(path: str) -> str:
    return str(path).replace("\\", "/")

def resolve_exists(raw_path: str) -> tuple[str, bool]:
    if not raw_path:
        return "", False
    candidate = Path(raw_path)
    return raw_path, candidate.is_file()

generated_at = datetime.now(timezone.utc).isoformat()
index_payload = json.loads(index_path.read_text(encoding="utf-8"))
traceability_from_index = index_payload.get("traceability", {})
index_links = traceability_from_index.get("links", []) if isinstance(traceability_from_index, dict) else []

explicit_links = []
for rel, raw in [
    ("scheduler_script", scheduler_script),
    ("wrapper_script", wrapper_path),
    ("stdout_log", stdout_path),
    ("stderr_log", stderr_path),
    ("audit_record", audit_path),
]:
    path, exists = resolve_exists(raw)
    if not path:
        continue
    explicit_links.append({"rel": rel, "path": path, "exists": exists})

link_map: dict[str, dict[str, object]] = {}
for link in index_links:
    if not isinstance(link, dict):
        continue
    rel = str(link.get("rel", "")).strip()
    path = str(link.get("path", "")).strip()
    if not rel or not path:
        continue
    link_map[rel] = {
        "rel": rel,
        "path": path,
        "exists": bool(link.get("exists", False)),
    }
for link in explicit_links:
    link_map[str(link["rel"])] = link

traceability_payload = {
    "generated_at": generated_at,
    "workdir": normalize(workdir),
    "index_path": normalize(index_path),
    "input_manifest": manifest if manifest else None,
    "job_id": job_id or (traceability_from_index.get("job_id") if isinstance(traceability_from_index, dict) else None),
    "submit_command": submit_command or (traceability_from_index.get("submit_command") if isinstance(traceability_from_index, dict) else None),
    "links": list(link_map.values()),
}

trace_json_path.write_text(json.dumps(traceability_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

lines = [
    "# Traceability Export",
    "",
    "## Inputs",
    "",
    f"- generated_at: `{generated_at}`",
    f"- workdir: `{normalize(workdir)}`",
    f"- index_path: `{normalize(index_path)}`",
    f"- input_manifest: `{manifest if manifest else 'none'}`",
    f"- job_id: `{traceability_payload['job_id'] if traceability_payload['job_id'] else 'none'}`",
    "",
    "## Traceability Links",
    "",
]
for link in traceability_payload["links"]:
    lines.append(
        f"- {link['rel']}: `{link['path']}` (exists={link['exists']})"
    )
lines.extend(
    [
        "",
        "## Intended Use",
        "",
        "- Preserve run context, artifact indexing, and release notes.",
        "- Feed this export into audit or release packaging workflows.",
    ]
)
trace_md_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

log "Wrote traceability files to $OUTPUT_DIR"
