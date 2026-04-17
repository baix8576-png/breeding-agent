#!/usr/bin/env bash
set -euo pipefail

WORKDIR=""
RESULTS_ROOT=""
OUTPUT_PATH=""
MANIFEST_PATH=""
PIPELINE_NAME=""
TASK_ID=""
RUN_ID=""
SESSION_ID=""
JOB_ID=""
JOB_STATE=""
SUBMIT_COMMAND=""
SCHEDULER_SCRIPT_PATH=""
WRAPPER_PATH=""
STDOUT_PATH=""
STDERR_PATH=""
AUDIT_PATH=""
FORCE="false"
LOG_PATHS=()

usage() {
  cat <<'EOF'
Usage: build_result_index.sh [options]

Options:
  --workdir PATH         Working directory for relative defaults (default: current directory)
  --results-root PATH    Root directory to scan for result artifacts (default: workdir/results)
  --manifest PATH        Optional manifest or traceability file to record as the primary source
  --pipeline NAME        Blueprint name (qc_pipeline/pca_pipeline/grm_builder/genomic_prediction)
  --task-id ID           Task id for run context
  --run-id ID            Run id for run context
  --session-id ID        Session id for run context
  --job-id ID            Scheduler job id for diagnostics context
  --job-state STATE      Scheduler job state for diagnostics context
  --submit-command TEXT  Scheduler submit command used for this run
  --scheduler-script PATH Scheduler script path for traceability links
  --wrapper PATH         Wrapper script path for traceability links
  --stdout-path PATH     Stdout log path for traceability links
  --stderr-path PATH     Stderr log path for traceability links
  --audit-path PATH      Audit record path for traceability links
  --log-path PATH        Log path for diagnostics (repeatable)
  --output PATH          Output JSON index path (default: workdir/results/report_index.json)
  --force                Allow overwriting the output file
  -h, --help             Show this help message
EOF
}

log() {
  printf '[report_generator:index] %s\n' "$*"
}

fail() {
  printf '[report_generator:index][error] %s\n' "$*" >&2
  exit 1
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --workdir) WORKDIR="${2:-}"; shift 2 ;;
    --results-root) RESULTS_ROOT="${2:-}"; shift 2 ;;
    --manifest) MANIFEST_PATH="${2:-}"; shift 2 ;;
    --pipeline) PIPELINE_NAME="${2:-}"; shift 2 ;;
    --task-id) TASK_ID="${2:-}"; shift 2 ;;
    --run-id) RUN_ID="${2:-}"; shift 2 ;;
    --session-id) SESSION_ID="${2:-}"; shift 2 ;;
    --job-id) JOB_ID="${2:-}"; shift 2 ;;
    --job-state) JOB_STATE="${2:-}"; shift 2 ;;
    --submit-command) SUBMIT_COMMAND="${2:-}"; shift 2 ;;
    --scheduler-script) SCHEDULER_SCRIPT_PATH="${2:-}"; shift 2 ;;
    --wrapper) WRAPPER_PATH="${2:-}"; shift 2 ;;
    --stdout-path) STDOUT_PATH="${2:-}"; shift 2 ;;
    --stderr-path) STDERR_PATH="${2:-}"; shift 2 ;;
    --audit-path) AUDIT_PATH="${2:-}"; shift 2 ;;
    --log-path) LOG_PATHS+=("${2:-}"); shift 2 ;;
    --output) OUTPUT_PATH="${2:-}"; shift 2 ;;
    --force) FORCE="true"; shift ;;
    -h|--help) usage; exit 0 ;;
    *) fail "Unknown option: $1" ;;
  esac
done

if [[ -z "$WORKDIR" ]]; then
  WORKDIR="$(pwd)"
fi
if [[ -z "$RESULTS_ROOT" ]]; then
  RESULTS_ROOT="$WORKDIR/results"
fi
if [[ -z "$OUTPUT_PATH" ]]; then
  OUTPUT_PATH="$RESULTS_ROOT/report_index.json"
fi

mkdir -p "$(dirname "$OUTPUT_PATH")"

if [[ -e "$OUTPUT_PATH" && "$FORCE" != "true" ]]; then
  fail "Output already exists: $OUTPUT_PATH. Use --force to overwrite."
fi
if [[ ! -d "$RESULTS_ROOT" ]]; then
  fail "Results root does not exist or is not a directory: $RESULTS_ROOT"
fi
if [[ -n "$MANIFEST_PATH" && ! -f "$MANIFEST_PATH" ]]; then
  fail "Manifest file not found: $MANIFEST_PATH"
fi

python - "$WORKDIR" "$RESULTS_ROOT" "$OUTPUT_PATH" "$MANIFEST_PATH" "$PIPELINE_NAME" "$TASK_ID" "$RUN_ID" "$SESSION_ID" "$JOB_ID" "$JOB_STATE" "$SUBMIT_COMMAND" "$SCHEDULER_SCRIPT_PATH" "$WRAPPER_PATH" "$STDOUT_PATH" "$STDERR_PATH" "$AUDIT_PATH" "${LOG_PATHS[@]}" <<'PY'
from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path
import re
import sys


def canonical_pipeline(name: str) -> str:
    if not name:
        return ""
    normalized = name.strip().lower()
    aliases = {
        "qc": "qc_pipeline",
        "qc_pipeline": "qc_pipeline",
        "pca": "pca_pipeline",
        "pca_pipeline": "pca_pipeline",
        "population_structure": "pca_pipeline",
        "grm": "grm_builder",
        "grm_builder": "grm_builder",
        "genomic_prediction": "genomic_prediction",
        "genomic_selection": "genomic_prediction",
    }
    return aliases.get(normalized, normalized)


BLUEPRINT_PROFILES: dict[str, dict[str, object]] = {
    "qc_pipeline": {
        "title": "QC Blueprint",
        "summary": "Input inventory, sample QC, variant QC, and QC report packaging.",
        "sections": [
            "Input inventory",
            "Sample QC metrics",
            "Variant QC metrics",
            "Retained dataset note",
            "Known risks and unresolved checks",
        ],
        "required_markers": [
            "results/qc/sample_qc.tsv",
            "results/qc/variant_qc.tsv",
            "reports/qc_summary.md",
        ],
    },
    "pca_pipeline": {
        "title": "PCA/Structure Blueprint",
        "summary": "LD pruning, PCA computation, structure summary, and stratification warning.",
        "sections": [
            "Dataset basis",
            "Pruning strategy note",
            "PCA artifact inventory",
            "Population structure summary",
            "Stratification caveats",
        ],
        "required_markers": [
            "results/structure/pca/eigenvec.tsv",
            "results/structure/pca/eigenval.tsv",
            "reports/structure_summary.md",
            "reports/stratification_risk.md",
        ],
    },
    "grm_builder": {
        "title": "GRM Blueprint",
        "summary": "Marker standardization, relationship matrix build, and matrix QC packaging.",
        "sections": [
            "Marker standardization assumptions",
            "GRM matrix inventory",
            "Matrix QC summary",
            "Downstream consumer notes",
        ],
        "required_markers": [
            "results/grm/grm_matrix.tsv",
            "results/grm/grm_ids.tsv",
            "reports/grm_qc.md",
        ],
    },
    "genomic_prediction": {
        "title": "Genomic Prediction Blueprint",
        "summary": "Cohort alignment, model blueprint, validation metrics, and prediction report.",
        "sections": [
            "Trait and cohort scope",
            "Model family choice",
            "Training and validation design",
            "Prediction output inventory",
            "Interpretation caveats",
        ],
        "required_markers": [
            "results/prediction/model_spec.json",
            "results/prediction/predictions.tsv",
            "results/prediction/metrics.tsv",
            "reports/genomic_prediction_summary.md",
        ],
    },
}


def infer_pipeline(paths: list[str]) -> str:
    joined = "\n".join(path.lower() for path in paths)
    if "results/prediction/" in joined:
        return "genomic_prediction"
    if "results/grm/" in joined:
        return "grm_builder"
    if "results/structure/" in joined:
        return "pca_pipeline"
    if "results/qc/" in joined:
        return "qc_pipeline"
    return "unknown"


def classify_kind(path: str, suffix: str) -> str:
    lowered = path.lower()
    if "/traceability/" in lowered:
        return "traceability"
    if lowered.startswith("reports/") or "/reports/" in lowered:
        return "report"
    if "/figures/" in lowered or suffix in {".png", ".svg", ".jpg", ".jpeg", ".pdf"}:
        return "figure"
    if lowered.endswith(".log") or "/logs/" in lowered:
        return "log"
    return "result"


def infer_format(path: Path) -> str:
    suffixes = [segment.lower() for segment in path.suffixes]
    if not suffixes:
        return "binary"
    if len(suffixes) >= 2 and suffixes[-1] == ".gz":
        return f"{suffixes[-2].lstrip('.')}.gz"
    return suffixes[-1].lstrip(".")


def normalize_path(path: Path) -> str:
    return str(path).replace("\\", "/")


def to_rel(path: Path, workdir: Path) -> str:
    try:
        return normalize_path(path.relative_to(workdir))
    except ValueError:
        return normalize_path(path)


def add_artifact(
    *,
    artifact_path: Path,
    workdir: Path,
    source: str,
    container: list[dict[str, object]],
    dedup: set[str],
) -> None:
    if not artifact_path.is_file():
        return
    rel_path = to_rel(artifact_path, workdir)
    if rel_path in dedup:
        return
    dedup.add(rel_path)
    suffix = artifact_path.suffix.lower()
    container.append(
        {
            "path": rel_path,
            "name": artifact_path.name,
            "kind": classify_kind(rel_path, suffix),
            "format": infer_format(artifact_path),
            "size_bytes": artifact_path.stat().st_size,
            "source": source,
        }
    )


def scan_failure_signals(log_path: Path, rel_path: str) -> list[dict[str, str]]:
    signals: list[dict[str, str]] = []
    text = log_path.read_text(encoding="utf-8", errors="ignore")
    if len(text) > 400_000:
        text = text[-400_000:]
    patterns = [
        ("out_of_memory", re.compile(r"out of memory|oom|killed process", re.IGNORECASE), "error"),
        ("timeout", re.compile(r"time limit|timeout", re.IGNORECASE), "error"),
        ("missing_input", re.compile(r"no such file|file not found|missing file", re.IGNORECASE), "error"),
        ("python_exception", re.compile(r"traceback|exception", re.IGNORECASE), "error"),
        ("scheduler_error", re.compile(r"sbatch: error|qsub:|slurmstepd: error|job failed|error:", re.IGNORECASE), "error"),
        ("warning", re.compile(r"\bwarning\b", re.IGNORECASE), "warning"),
    ]
    for code, pattern, severity in patterns:
        match = pattern.search(text)
        if not match:
            continue
        start = max(0, match.start() - 90)
        end = min(len(text), match.end() + 90)
        excerpt = " ".join(text[start:end].split())
        signals.append(
            {
                "code": code,
                "severity": severity,
                "source": rel_path,
                "message": excerpt[:240],
            }
        )
    return signals


def to_status(
    *,
    job_state: str,
    has_error_signals: bool,
    missing_required_count: int,
) -> str:
    normalized = job_state.strip().lower()
    if normalized in {"failed", "cancelled", "timeout", "error"}:
        return "failed"
    if has_error_signals:
        return "failed"
    if normalized in {"running", "queued"}:
        return "in_progress"
    if missing_required_count > 0:
        return "warning"
    return "ok"


workdir = Path(sys.argv[1]).resolve()
results_root = Path(sys.argv[2]).resolve()
output_path = Path(sys.argv[3]).resolve()
manifest_path_raw = sys.argv[4].strip()
pipeline_raw = sys.argv[5].strip()
task_id = sys.argv[6].strip()
run_id = sys.argv[7].strip()
session_id = sys.argv[8].strip()
job_id = sys.argv[9].strip()
job_state = sys.argv[10].strip()
submit_command = sys.argv[11].strip()
scheduler_script_path = sys.argv[12].strip()
wrapper_path = sys.argv[13].strip()
stdout_path = sys.argv[14].strip()
stderr_path = sys.argv[15].strip()
audit_path = sys.argv[16].strip()
log_paths_raw = [entry for entry in sys.argv[17:] if entry.strip()]

artifacts: list[dict[str, object]] = []
seen_paths: set[str] = set()

scan_roots = [results_root, (workdir / "reports")]
for root in scan_roots:
    if not root.exists() or not root.is_dir():
        continue
    for artifact_path in sorted(root.rglob("*")):
        if not artifact_path.is_file():
            continue
        if artifact_path.resolve() == output_path:
            continue
        add_artifact(
            artifact_path=artifact_path,
            workdir=workdir,
            source="filesystem_scan",
            container=artifacts,
            dedup=seen_paths,
        )

provided_logs: list[str] = []
for raw in log_paths_raw:
    path = Path(raw).expanduser()
    if not path.is_absolute():
        path = (workdir / path).resolve()
    if path.is_file():
        add_artifact(
            artifact_path=path,
            workdir=workdir,
            source="scheduler_log",
            container=artifacts,
            dedup=seen_paths,
        )
        provided_logs.append(to_rel(path, workdir))
    else:
        provided_logs.append(normalize_path(path))

artifacts.sort(key=lambda item: str(item.get("path", "")))

by_kind: dict[str, list[str]] = {
    "results": [],
    "figures": [],
    "reports": [],
    "logs": [],
    "traceability": [],
}
for artifact in artifacts:
    rel_path = str(artifact.get("path", ""))
    kind = str(artifact.get("kind", "result"))
    if kind == "figure":
        by_kind["figures"].append(rel_path)
    elif kind == "report":
        by_kind["reports"].append(rel_path)
    elif kind == "log":
        by_kind["logs"].append(rel_path)
    elif kind == "traceability":
        by_kind["traceability"].append(rel_path)
    else:
        by_kind["results"].append(rel_path)

path_pool = [str(item.get("path", "")) for item in artifacts]
pipeline_name = canonical_pipeline(pipeline_raw) or infer_pipeline(path_pool)
profile = BLUEPRINT_PROFILES.get(pipeline_name)
required_markers = list(profile.get("required_markers", [])) if profile else []
existing_paths = set(path_pool)
present_markers = [marker for marker in required_markers if marker in existing_paths]
missing_markers = [marker for marker in required_markers if marker not in existing_paths]

log_signals: list[dict[str, str]] = []
for log_path in by_kind["logs"]:
    absolute_log = (workdir / log_path).resolve()
    if absolute_log.is_file():
        log_signals.extend(scan_failure_signals(absolute_log, log_path))

for provided in provided_logs:
    if provided not in by_kind["logs"]:
        log_signals.append(
            {
                "code": "log_path_missing",
                "severity": "warning",
                "source": provided,
                "message": "Configured log path was not found at index-build time.",
            }
        )

has_error_signals = any(signal["severity"] == "error" for signal in log_signals)
diagnostic_status = to_status(
    job_state=job_state,
    has_error_signals=has_error_signals,
    missing_required_count=len(missing_markers),
)
if diagnostic_status == "failed":
    diagnostic_summary = "Failure signals were detected; inspect linked logs and rerun with recovery strategy."
elif diagnostic_status == "in_progress":
    diagnostic_summary = "Job is still running or queued; diagnostics are provisional until terminal state."
elif diagnostic_status == "warning":
    diagnostic_summary = "No hard failure signals, but required blueprint artifacts are still missing."
else:
    diagnostic_summary = "No obvious failure signals detected in current artifacts and log snapshots."

traceability_json = workdir / "results" / "traceability" / "traceability.json"
traceability_md = workdir / "results" / "traceability" / "traceability.md"
traceability_links = {
    "traceability_json": {
        "path": to_rel(traceability_json, workdir),
        "exists": traceability_json.is_file(),
    },
    "traceability_markdown": {
        "path": to_rel(traceability_md, workdir),
        "exists": traceability_md.is_file(),
    },
}

artifact_counts = {
    "total": len(artifacts),
    "results": len(by_kind["results"]),
    "figures": len(by_kind["figures"]),
    "reports": len(by_kind["reports"]),
    "logs": len(by_kind["logs"]),
    "traceability": len(by_kind["traceability"]),
}

BLUEPRINT_SUMMARY_KEYS = [
    ("qc", "qc_pipeline"),
    ("pca", "pca_pipeline"),
    ("grm", "grm_builder"),
    ("genomic_prediction", "genomic_prediction"),
]

blueprint_summary: dict[str, dict[str, object]] = {}
for short_key, profile_key in BLUEPRINT_SUMMARY_KEYS:
    current_profile = BLUEPRINT_PROFILES[profile_key]
    current_required = list(current_profile["required_markers"])
    current_present = [marker for marker in current_required if marker in existing_paths]
    current_missing = [marker for marker in current_required if marker not in existing_paths]
    status = "selected" if profile_key == pipeline_name else "not_selected"
    if profile_key == pipeline_name and missing_markers and diagnostic_status != "failed":
        status = "selected_with_gaps"
    highlight_pool = current_present or current_required
    blueprint_summary[short_key] = {
        "status": status,
        "artifact_count": len(current_present),
        "highlights": highlight_pool[:3],
        "summary": str(current_profile["summary"]),
        "sections": list(current_profile["sections"]),
        "coverage": {
            "required_markers": len(current_required),
            "present_markers": len(current_present),
            "missing_markers": current_missing,
        },
    }

if profile:
    selected_blueprint = {
        "name": pipeline_name,
        "title": str(profile["title"]),
        "summary": str(profile["summary"]),
        "sections": list(profile["sections"]),
        "coverage": {
            "required_markers": len(required_markers),
            "present_markers": len(present_markers),
            "missing_markers": missing_markers,
        },
    }
else:
    selected_blueprint = {
        "name": pipeline_name,
        "title": "Unknown Blueprint",
        "summary": "No blueprint profile matched this artifact bundle.",
        "sections": [],
        "coverage": {
            "required_markers": 0,
            "present_markers": 0,
            "missing_markers": [],
        },
    }

traceability_items = []
for rel_name, raw_path in [
    ("scheduler_script", scheduler_script_path),
    ("wrapper_script", wrapper_path),
    ("stdout_log", stdout_path),
    ("stderr_log", stderr_path),
    ("audit_record", audit_path),
]:
    if not raw_path:
        continue
    candidate = Path(raw_path)
    traceability_items.append(
        {
            "rel": rel_name,
            "path": raw_path,
            "exists": candidate.is_file(),
        }
    )
traceability_items.extend(
    [
        {
            "rel": "traceability_json",
            "path": traceability_links["traceability_json"]["path"],
            "exists": traceability_links["traceability_json"]["exists"],
        },
        {
            "rel": "traceability_markdown",
            "path": traceability_links["traceability_markdown"]["path"],
            "exists": traceability_links["traceability_markdown"]["exists"],
        },
    ]
)

payload = {
    "schema_version": "report_index.v2",
    "generated_at": datetime.now(timezone.utc).isoformat(),
    "generator": {
        "tool": "report_generator",
        "version": "v1.5",
        "command": "build_result_index.sh",
    },
    "run_context": {
        "task_id": task_id or None,
        "run_id": run_id or None,
        "session_id": session_id or None,
        "pipeline_name": pipeline_name if pipeline_name else None,
    },
    "roots": {
        "workdir": normalize_path(workdir),
        "results_root": normalize_path(results_root),
        "reports_root": normalize_path(workdir / "reports"),
    },
    "workdir": normalize_path(workdir),
    "results_root": normalize_path(results_root),
    "primary_manifest": manifest_path_raw if manifest_path_raw else None,
    "pipeline_blueprint": pipeline_name,
    "job_context": {
        "job_id": job_id if job_id else None,
        "job_state": job_state if job_state else None,
        "submit_command": submit_command if submit_command else None,
    },
    "artifact_counts": artifact_counts,
    "collections": {
        "results": [normalize_path((workdir / path).resolve()) for path in by_kind["results"]],
        "figures": [normalize_path((workdir / path).resolve()) for path in by_kind["figures"]],
        "logs": [normalize_path((workdir / path).resolve()) for path in by_kind["logs"]],
        "reports": [normalize_path((workdir / path).resolve()) for path in by_kind["reports"]],
    },
    "by_kind": by_kind,
    "artifacts": artifacts,
    "blueprint_summary": blueprint_summary,
    "selected_blueprint_summary": selected_blueprint,
    "diagnostics": {
        "status": diagnostic_status,
        "summary": diagnostic_summary,
        "signals": log_signals,
        "provided_log_paths": provided_logs,
        "failure_tasks": [job_id] if diagnostic_status == "failed" and job_id else [],
        "hints": [
            "Inspect stderr first for parser/runtime errors.",
            "For transient scheduler errors, retry with configured backoff after checking queue state.",
            "For resource failures, increase CPU/memory envelope before re-submit.",
        ] if diagnostic_status in {"failed", "warning"} else [],
    },
    "traceability_links": traceability_links,
    "traceability": {
        "job_id": job_id if job_id else None,
        "submit_command": submit_command if submit_command else None,
        "links": traceability_items,
    },
    "summary": {
        "one_line": (
            f"{pipeline_name or 'unknown'} selected; "
            f"{artifact_counts['results']} results, {artifact_counts['figures']} figures, "
            f"{artifact_counts['logs']} logs, {artifact_counts['reports']} reports; "
            f"diagnostics={diagnostic_status}"
        ),
        "counts": artifact_counts,
    },
}

output_path.parent.mkdir(parents=True, exist_ok=True)
output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
PY

log "Wrote report index v2 to $OUTPUT_PATH"
