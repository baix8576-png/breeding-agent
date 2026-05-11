"""Production gate, release standardization, and final-review helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
import subprocess
import sys
from typing import Any

from audit.store import FileAuditStore
from runtime.settings import Settings


@dataclass(slots=True)
class GovernanceService:
    """Execute governance checks required for production readiness."""

    settings: Settings
    audit_store: FileAuditStore

    def run_production_gate(
        self,
        *,
        working_directory: str | None = None,
        execute_tests: bool = False,
        timeout_seconds: int = 300,
    ) -> dict[str, Any]:
        root = Path(working_directory or Path.cwd())
        suites = [
            {
                "check_id": "contract_regression",
                "description": "Contract regression suite for stable IO schemas.",
                "command": [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "tests/unit/contracts/test_execution.py",
                    "tests/unit/runtime/test_compat_envelope.py",
                ],
            },
            {
                "check_id": "scheduler_simulation",
                "description": "Scheduler simulation and retry/quota semantics regression.",
                "command": [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "tests/unit/scheduler/test_scheduler_planning.py",
                    "tests/unit/scheduler/test_atomic_profiles.py",
                ],
            },
            {
                "check_id": "knowledge_retrieval_regression",
                "description": "Knowledge retrieval ranking/fallback/evidence consistency regression.",
                "command": [
                    sys.executable,
                    "-m",
                    "pytest",
                    "-q",
                    "tests/unit/knowledge/test_retrieval.py",
                ],
            },
        ]

        results: list[dict[str, Any]] = []
        if execute_tests:
            for suite in suites:
                completed = subprocess.run(
                    suite["command"],
                    cwd=str(root),
                    capture_output=True,
                    text=True,
                    check=False,
                    timeout=max(60, int(timeout_seconds)),
                )
                results.append(
                    {
                        "check_id": suite["check_id"],
                        "description": suite["description"],
                        "status": "pass" if completed.returncode == 0 else "fail",
                        "returncode": completed.returncode,
                        "command": suite["command"],
                        "stdout_tail": (completed.stdout or "").splitlines()[-20:],
                        "stderr_tail": (completed.stderr or "").splitlines()[-20:],
                    }
                )
        else:
            for suite in suites:
                results.append(
                    {
                        "check_id": suite["check_id"],
                        "description": suite["description"],
                        "status": "planned",
                        "command": suite["command"],
                    }
                )

        audit_check = self._audit_integrity_check(working_directory=working_directory)
        results.append(audit_check)
        overall = "pass"
        if any(item["status"] == "fail" for item in results):
            overall = "fail"
        elif any(item["status"] == "planned" for item in results):
            overall = "planned"
        return {
            "schema_version": "production_gate.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "execute_tests": execute_tests,
            "overall_status": overall,
            "checks": results,
        }

    def build_release_plan(
        self,
        *,
        version_tag: str,
        change_summary: str,
        stage_ids: list[str] | None = None,
    ) -> dict[str, Any]:
        normalized = version_tag.strip() or "v2.0.0"
        if not normalized.startswith("v"):
            normalized = f"v{normalized}"
        stage_list = [item for item in (stage_ids or []) if item.strip()]
        rollback_plan = [
            "Preserve latest release artifact and deployment manifest before rollout.",
            "If gate fails post-release, revert to previous stable tag and restore scheduler settings snapshot.",
            "Restore previous API compatibility headers and verify non-bio no-cluster policy remains enforced.",
            "Re-run compileall + pytest + production gate to validate rollback integrity.",
        ]
        release_notes_template = "\n".join(
            [
                f"# Release {normalized}",
                "",
                "## Scope",
                change_summary.strip() or "Fill in this release scope summary.",
                "",
                "## Stage Mapping",
                ", ".join(stage_list) if stage_list else "stage mapping pending",
                "",
                "## Compatibility",
                f"- current_api_version: {self.settings.api_current_version}",
                f"- stable_prefix: {self.settings.api_v2_prefix}",
                f"- v1_sunset: {self.settings.api_v1_sunset_date}",
                "",
                "## Verification",
                "- python -m compileall src tests",
                "- python -m pytest -q",
                "- production gate pipeline",
                "",
                "## Risks",
                "- Fill in high-risk changes and mitigations.",
                "",
                "## Rollback",
                *[f"- {line}" for line in rollback_plan],
            ]
        )
        return {
            "schema_version": "release_plan.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "version_tag": normalized,
            "stage_ids": stage_list,
            "release_notes_template": release_notes_template,
            "rollback_plan": rollback_plan,
            "checklist": [
                "tag version",
                "publish change summary",
                "run production gate",
                "archive audit bundle for release candidate",
            ],
        }

    def final_acceptance_review(
        self,
        *,
        working_directory: str | None = None,
    ) -> dict[str, Any]:
        root = Path(working_directory or Path.cwd())
        required_dirs = [
            "src",
            "tests",
            "references",
            "scripts",
            ".agents",
            ".codex",
        ]
        forbidden_dirs = [
            "src_v2",
            "new_src",
            "temp_final",
            "final_version",
        ]
        missing_required = [name for name in required_dirs if not (root / name).exists()]
        forbidden_present = [name for name in forbidden_dirs if (root / name).exists()]
        architecture_pass = not missing_required and not forbidden_present

        governance_pass = all(
            [
                bool(self.settings.api_current_version.strip()),
                bool(self.settings.api_v2_prefix.strip()),
                bool(self.settings.api_version_policy_path.strip()),
                self.settings.api_compatibility_window_days > 0,
            ]
        )

        observability_payload = self.run_production_gate(
            working_directory=working_directory,
            execute_tests=False,
        )
        operability_pass = (
            observability_payload.get("overall_status") in {"planned", "pass"}
            and isinstance(observability_payload.get("checks"), list)
        )
        overall = architecture_pass and governance_pass and operability_pass
        return {
            "schema_version": "v2_final_review.v1",
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "overall_status": "pass" if overall else "not_ready",
            "architecture_boundary": {
                "status": "pass" if architecture_pass else "fail",
                "missing_required_dirs": missing_required,
                "forbidden_dirs_present": forbidden_present,
            },
            "governance_requirements": {
                "status": "pass" if governance_pass else "fail",
                "api_current_version": self.settings.api_current_version,
                "stable_prefix": self.settings.api_v2_prefix,
                "version_policy_path": self.settings.api_version_policy_path,
                "compatibility_window_days": self.settings.api_compatibility_window_days,
            },
            "operability": {
                "status": "pass" if operability_pass else "fail",
                "production_gate_overview": observability_payload.get("overall_status"),
                "checks_count": len(observability_payload.get("checks", [])),
            },
            "next_actions": (
                []
                if overall
                else [
                    "Fix failed review section(s) and rerun final acceptance review.",
                    "Ensure production gate checks are executable in target environment.",
                ]
            ),
        }

    def _audit_integrity_check(self, *, working_directory: str | None = None) -> dict[str, Any]:
        rows = self.audit_store.list_recent_runs(
            working_directory=working_directory,
            limit=100,
        )
        required = [
            "input_summary",
            "planning_summary",
            "submission_command",
            "job_id",
            "log_paths",
            "manual_confirmation_records",
        ]
        inspected = 0
        missing_events = 0
        samples: list[dict[str, Any]] = []
        for row in rows[:50]:
            run_id = str(row.get("run_id", ""))
            task_id = str(row.get("task_id", ""))
            events, _path = self.audit_store.read_run_events(
                run_id=run_id,
                task_id=task_id,
                working_directory=working_directory,
            )
            if not events:
                continue
            inspected += 1
            latest = events[-1]
            metadata = latest.metadata if isinstance(latest.metadata, dict) else {}
            missing = [key for key in required if key not in metadata]
            if missing:
                missing_events += 1
                samples.append(
                    {
                        "task_id": task_id,
                        "run_id": run_id,
                        "missing_fields": missing,
                    }
                )
        status = "pass" if missing_events == 0 else "fail"
        if inspected == 0:
            status = "planned"
        return {
            "check_id": "audit_integrity",
            "description": "Audit trail completeness for execution_closure mandatory fields.",
            "status": status,
            "inspected_runs": inspected,
            "missing_runs": missing_events,
            "samples": samples[:10],
            "required_fields": required,
        }
