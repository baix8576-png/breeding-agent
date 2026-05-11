"""Observability helpers built from persisted audit records."""

from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from typing import Any

from audit.store import FileAuditStore


class ObservabilityService:
    """Aggregate task/scheduler/failure signals for lightweight dashboards."""

    def __init__(self, audit_store: FileAuditStore) -> None:
        self._audit_store = audit_store

    def build_metrics(
        self,
        *,
        working_directory: str | None = None,
        limit: int = 200,
    ) -> dict[str, Any]:
        rows = self._audit_store.list_recent_runs(
            working_directory=working_directory,
            limit=max(1, limit),
        )
        runtime_counter: Counter[str] = Counter()
        mode_counter: Counter[str] = Counter()
        scheduler_counter: Counter[str] = Counter()
        failure_counter: Counter[str] = Counter()
        gate_counter: Counter[str] = Counter()
        timeline: list[dict[str, Any]] = []

        for row in rows:
            runtime_path = str(row.get("runtime_path", "unknown"))
            runtime_counter[runtime_path] += 1

            summary = str(row.get("summary", "")).strip().lower()
            if summary.startswith("dry-run"):
                mode_counter["dry-run"] += 1
            elif summary.startswith("submit-preview"):
                mode_counter["submit-preview"] += 1
            elif summary.startswith("submit"):
                mode_counter["submit"] += 1
            else:
                mode_counter["unknown"] += 1

            job_id = str(row.get("job_id", "")).upper()
            if "-SLURM-" in job_id:
                scheduler_counter["slurm"] += 1
            elif "-PBS-" in job_id:
                scheduler_counter["pbs"] += 1
            elif job_id.startswith("SKIPPED-NONBIO-"):
                scheduler_counter["non_bio_skip"] += 1
            else:
                scheduler_counter["unknown"] += 1

            report_summary = str(row.get("report_summary", "")).lower()
            if "diagnostics=failed" in report_summary or "report_generator_status=failed" in report_summary:
                failure_counter["execution_failed"] += 1
            elif "diagnostics=warning" in report_summary:
                failure_counter["artifact_warning"] += 1
            elif "report_generator_status=skipped" in report_summary:
                failure_counter["report_generator_skipped"] += 1
            else:
                failure_counter["healthy_or_unknown"] += 1

            events, _path = self._audit_store.read_run_events(
                run_id=str(row.get("run_id", "")),
                task_id=str(row.get("task_id", "")),
                working_directory=working_directory,
            )
            if events:
                latest = events[-1]
                manual_records = latest.metadata.get("manual_confirmation_records", [])
                if isinstance(manual_records, list) and manual_records:
                    gate_counter["manual_confirmation_required"] += 1
                else:
                    gate_counter["auto_or_passive"] += 1
            else:
                gate_counter["unknown"] += 1

            timeline.append(
                {
                    "task_id": row.get("task_id"),
                    "run_id": row.get("run_id"),
                    "created_at": row.get("created_at"),
                    "runtime_path": runtime_path,
                    "failure_class": self._top_classification_for_row(report_summary),
                }
            )

        return {
            "schema_version": "observability_metrics.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "coverage": {
                "rows_scanned": len(rows),
                "limit": max(1, limit),
            },
            "task_metrics": {
                "total_runs": len(rows),
                "runtime_paths": dict(runtime_counter),
                "execution_modes": dict(mode_counter),
            },
            "scheduler_metrics": {
                "scheduler_distribution": dict(scheduler_counter),
                "gate_distribution": dict(gate_counter),
            },
            "failure_taxonomy": {
                "classes": dict(failure_counter),
            },
            "timeline": timeline[:50],
        }

    def build_dashboard(
        self,
        *,
        working_directory: str | None = None,
        limit: int = 100,
    ) -> dict[str, Any]:
        metrics = self.build_metrics(working_directory=working_directory, limit=limit)
        board_rows = self._audit_store.list_recent_runs(
            working_directory=working_directory,
            limit=max(1, min(limit, 50)),
        )
        top_failures = sorted(
            metrics["failure_taxonomy"]["classes"].items(),
            key=lambda item: (-int(item[1]), item[0]),
        )
        return {
            "schema_version": "observability_dashboard.v1",
            "metrics": metrics,
            "board": board_rows,
            "top_failure_classes": [
                {"class": name, "count": count}
                for name, count in top_failures
            ],
        }

    def _top_classification_for_row(self, report_summary: str) -> str:
        text = report_summary.lower()
        if "diagnostics=failed" in text:
            return "execution_failed"
        if "diagnostics=warning" in text:
            return "artifact_warning"
        if "report_generator_status=failed" in text:
            return "report_generator_failed"
        return "healthy_or_unknown"
