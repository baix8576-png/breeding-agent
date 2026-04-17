#!/usr/bin/env bash
set -euo pipefail

WORKDIR=""
INDEX_PATH=""
OUTPUT_PATH=""
TITLE="geneagent V1.5 Summary Report"
FORCE="false"

usage() {
  cat <<'EOF'
Usage: render_summary_report.sh [options]

Options:
  --workdir PATH        Working directory for relative defaults (default: current directory)
  --index PATH          Report index JSON (default: workdir/results/report_index.json)
  --output PATH         Output markdown report path (default: workdir/reports/summary_report.md)
  --title TEXT          Report title
  --force               Allow overwriting the output file
  -h, --help            Show this help message
EOF
}

log() {
  printf '[report_generator:render] %s\n' "$*"
}

fail() {
  printf '[report_generator:render][error] %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workdir) WORKDIR="${2:-}"; shift 2 ;;
    --index) INDEX_PATH="${2:-}"; shift 2 ;;
    --output) OUTPUT_PATH="${2:-}"; shift 2 ;;
    --title) TITLE="${2:-}"; shift 2 ;;
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
if [[ -z "$OUTPUT_PATH" ]]; then
  OUTPUT_PATH="$WORKDIR/reports/summary_report.md"
fi

mkdir -p "$(dirname "$OUTPUT_PATH")"

if [[ -e "$OUTPUT_PATH" && "$FORCE" != "true" ]]; then
  fail "Output already exists: $OUTPUT_PATH. Use --force to overwrite."
fi
if [[ ! -f "$INDEX_PATH" ]]; then
  fail "Index file not found: $INDEX_PATH"
fi

python - "$WORKDIR" "$INDEX_PATH" "$OUTPUT_PATH" "$TITLE" <<'PY'
from __future__ import annotations

import json
from pathlib import Path
import sys

workdir = Path(sys.argv[1])
index_path = Path(sys.argv[2])
output_path = Path(sys.argv[3])
title = sys.argv[4]

payload = json.loads(index_path.read_text(encoding="utf-8"))
schema_version = str(payload.get("schema_version", "report_index.v1"))
run_context = payload.get("run_context", {}) if isinstance(payload.get("run_context"), dict) else {}

lines: list[str] = [f"# {title}", ""]
lines.extend(
    [
        "## Inputs",
        "",
        f"- Index file: `{index_path}`",
        f"- Workdir: `{workdir}`",
        f"- Schema version: `{schema_version}`",
        f"- task_id: `{run_context.get('task_id', 'unknown')}`",
        f"- run_id: `{run_context.get('run_id', 'unknown')}`",
        f"- pipeline: `{run_context.get('pipeline_name', payload.get('pipeline_blueprint', 'unknown'))}`",
        "",
    ]
)

summary_block = payload.get("summary")
if isinstance(summary_block, dict):
    lines.append("## Execution Summary")
    lines.append("")
    lines.append(f"- {summary_block.get('one_line', 'No summary available.')}")
    lines.append("")

artifact_counts = payload.get("artifact_counts")
if isinstance(artifact_counts, dict):
    lines.append("## Artifact Counts")
    lines.append("")
    lines.append(f"- Total: `{artifact_counts.get('total', 0)}`")
    lines.append(f"- Results: `{artifact_counts.get('results', 0)}`")
    lines.append(f"- Figures: `{artifact_counts.get('figures', 0)}`")
    lines.append(f"- Reports: `{artifact_counts.get('reports', 0)}`")
    lines.append(f"- Logs: `{artifact_counts.get('logs', 0)}`")
    lines.append(f"- Traceability: `{artifact_counts.get('traceability', 0)}`")
    lines.append("")
else:
    declared = payload.get("artifacts")
    artifact_count = len(declared) if isinstance(declared, list) else 0
    lines.append("## Artifact Count")
    lines.append("")
    lines.append(f"- Declared artifacts: `{artifact_count}`")
    lines.append("")

selected_blueprint_summary = payload.get("selected_blueprint_summary")
if isinstance(selected_blueprint_summary, dict):
    coverage = selected_blueprint_summary.get("coverage", {})
    lines.append("## Blueprint Summary")
    lines.append("")
    lines.append(f"- Blueprint: `{selected_blueprint_summary.get('name', 'unknown')}`")
    lines.append(f"- Title: {selected_blueprint_summary.get('title', 'N/A')}")
    lines.append(f"- Summary: {selected_blueprint_summary.get('summary', 'N/A')}")
    lines.append(
        "- Required markers coverage: "
        f"`{coverage.get('present_markers', 0)}/{coverage.get('required_markers', 0)}`"
    )
    missing_markers = coverage.get("missing_markers", [])
    if isinstance(missing_markers, list) and missing_markers:
        lines.append("- Missing required markers:")
        for marker in missing_markers:
            lines.append(f"  - `{marker}`")
    sections = selected_blueprint_summary.get("sections", [])
    if isinstance(sections, list) and sections:
        lines.append("- Suggested report sections:")
        for section in sections:
            lines.append(f"  - {section}")
    lines.append("")

blueprint_summary = payload.get("blueprint_summary")
if isinstance(blueprint_summary, dict):
    lines.append("## Blueprint Matrix")
    lines.append("")
    for key in ["qc", "pca", "grm", "genomic_prediction"]:
        item = blueprint_summary.get(key)
        if not isinstance(item, dict):
            continue
        lines.append(
            f"- {key}: status=`{item.get('status', 'unknown')}`, "
            f"artifacts=`{item.get('artifact_count', 0)}`"
        )
    lines.append("")

diagnostics = payload.get("diagnostics")
if isinstance(diagnostics, dict):
    lines.append("## Failure Diagnostics")
    lines.append("")
    lines.append(f"- Status: `{diagnostics.get('status', 'unknown')}`")
    lines.append(f"- Summary: {diagnostics.get('summary', 'N/A')}")
    signals = diagnostics.get("signals", [])
    if isinstance(signals, list) and signals:
        lines.append("- Signals:")
        for signal in signals[:10]:
            if not isinstance(signal, dict):
                continue
            lines.append(
                "  - "
                f"[{signal.get('severity', 'info')}] `{signal.get('code', 'signal')}` "
                f"@ `{signal.get('source', 'unknown')}`: {signal.get('message', '')}"
            )
    failure_tasks = diagnostics.get("failure_tasks", [])
    if isinstance(failure_tasks, list) and failure_tasks:
        lines.append("- Failure tasks:")
        for task in failure_tasks:
            lines.append(f"  - `{task}`")
    lines.append("")

traceability = payload.get("traceability")
if isinstance(traceability, dict):
    lines.append("## Traceability Links")
    lines.append("")
    links = traceability.get("links", [])
    if isinstance(links, list):
        for link in links:
            if not isinstance(link, dict):
                continue
            lines.append(
                f"- {link.get('rel', 'link')}: `{link.get('path', '')}` "
                f"(exists={link.get('exists', False)})"
            )
    lines.append("")
else:
    traceability_links = payload.get("traceability_links")
    if isinstance(traceability_links, dict):
        lines.append("## Traceability Links")
        lines.append("")
        for key, value in traceability_links.items():
            if not isinstance(value, dict):
                continue
            path = value.get("path", "")
            exists = value.get("exists", False)
            lines.append(f"- {key}: `{path}` (exists={exists})")
        lines.append("")

lines.extend(
    [
        "## Render Notes",
        "",
        "- This report packages generated artifacts and diagnostics for runtime/audit handoff.",
        "- Confirm safety gate decisions and scheduler state before treating outputs as final release material.",
    ]
)

output_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
PY

log "Wrote summary report to $OUTPUT_PATH"
