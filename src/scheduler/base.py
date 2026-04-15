"""Abstract scheduler adapter API with dry-run planning support."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import PurePosixPath, PureWindowsPath
import re
import shlex

from contracts.common import JobState, SchedulerKind
from contracts.execution import JobHandle, RunContext
from contracts.tasks import ResourceEstimate
from scheduler.models import SchedulerPaths, SchedulerResourceRequest, SubmissionPlan


class BaseSchedulerAdapter(ABC):
    """Scheduler abstraction used by SLURM and PBS adapters."""

    kind: SchedulerKind

    def render_submission_script(
        self,
        command: list[str],
        resources: ResourceEstimate,
        working_directory: str | None = None,
        job_name: str | None = None,
        task_id: str | None = None,
        run_id: str | None = None,
    ) -> str:
        """Render a scheduler submission script without calling the real scheduler."""

        resolved_workdir = working_directory or "."
        paths = self._build_paths(resolved_workdir, job_name)
        request = self._normalize_resources(resources=resources, paths=paths, job_name=job_name)
        tracking = self._resolve_tracking_ids(task_id=task_id, run_id=run_id, job_name=request.job_name)
        return self._compose_script(
            command=command,
            request=request,
            paths=paths,
            task_id=tracking["task_id"],
            run_id=tracking["run_id"],
        )

    def build_submission_plan(
        self,
        command: list[str],
        working_directory: str,
        resources: ResourceEstimate,
        job_name: str | None = None,
        mode: str = "dry-run",
        task_id: str | None = None,
        run_id: str | None = None,
    ) -> SubmissionPlan:
        """Build a structured submission plan without touching a real scheduler."""

        resolved_command = command or ["echo", "geneagent-placeholder"]
        paths = self._build_paths(working_directory=working_directory, job_name=job_name)
        request = self._normalize_resources(resources=resources, paths=paths, job_name=job_name)
        tracking = self._resolve_tracking_ids(task_id=task_id, run_id=run_id, job_name=request.job_name)
        script_preview = self._compose_script(
            command=resolved_command,
            request=request,
            paths=paths,
            task_id=tracking["task_id"],
            run_id=tracking["run_id"],
        )
        handle = self._build_job_handle(
            paths=paths,
            job_name=request.job_name,
            mode=mode,
            task_id=tracking["task_id"],
            run_id=tracking["run_id"],
        )
        warnings = self._plan_warnings(
            request=request,
            mode=mode,
            task_id_supplied=task_id is not None,
            run_id_supplied=run_id is not None,
        )
        return SubmissionPlan(
            task_id=tracking["task_id"],
            run_id=tracking["run_id"],
            scheduler=self.kind,
            mode=mode,
            ready_for_gate=self._ready_for_gate_status(mode=mode),
            resource_request=request,
            paths=paths,
            command=resolved_command,
            command_preview=shlex.join(resolved_command),
            script_preview=script_preview,
            submit_command=self._submit_command(paths.script_path),
            job_handle=handle,
            warnings=warnings,
            compatibility_notes=self.compatibility_notes(),
            polling_hint=self._poll_command_hint(handle.job_id),
        )

    def dry_run_submit(
        self,
        working_directory: str,
        resources: ResourceEstimate,
        command: list[str] | None = None,
        job_name: str | None = None,
        task_id: str | None = None,
        run_id: str | None = None,
    ) -> JobHandle:
        """Return a synthetic dry-run job handle without touching the real scheduler."""

        plan = self.build_submission_plan(
            command=command or ["echo", "geneagent-dry-run"],
            working_directory=working_directory,
            resources=resources,
            job_name=job_name,
            mode="dry-run",
            task_id=task_id,
            run_id=run_id,
        )
        return plan.job_handle

    def submit(
        self,
        working_directory: str,
        resources: ResourceEstimate,
        command: list[str] | None = None,
        job_name: str | None = None,
        task_id: str | None = None,
        run_id: str | None = None,
    ) -> JobHandle:
        """Return a plan-only handle and intentionally avoid real cluster submission."""

        plan = self.build_submission_plan(
            command=command or ["echo", "geneagent-submit-preview"],
            working_directory=working_directory,
            resources=resources,
            job_name=job_name,
            mode="submit-preview",
            task_id=task_id,
            run_id=run_id,
        )
        return plan.job_handle

    def poll(self, job_id: str) -> JobState:
        """Infer a state from a synthetic job identifier without calling the scheduler."""

        normalized = job_id.upper()
        if normalized.startswith(("DRYRUN-", "PLAN-")):
            return JobState.DRAFT
        if any(token in normalized for token in ("PENDING", "QUEUED", "WAIT", "HOLD")):
            return JobState.QUEUED
        if any(token in normalized for token in ("RUN", "EXEC")):
            return JobState.RUNNING
        if any(token in normalized for token in ("DONE", "SUCCESS", "COMPLETE")):
            return JobState.COMPLETED
        if any(token in normalized for token in ("FAIL", "ERROR", "CANCEL")):
            return JobState.FAILED
        return JobState.UNKNOWN

    @abstractmethod
    def _directive_lines(self, request: SchedulerResourceRequest, paths: SchedulerPaths) -> list[str]:
        """Return scheduler-specific header directives."""

    @abstractmethod
    def _submit_command(self, script_path: str) -> list[str]:
        """Return the scheduler-specific submission command preview."""

    @abstractmethod
    def _poll_command_hint(self, job_id: str) -> str:
        """Return the scheduler-specific poll command hint."""

    @abstractmethod
    def compatibility_notes(self) -> list[str]:
        """Describe the current compatibility boundaries of the adapter."""

    def _build_paths(self, working_directory: str, job_name: str | None) -> SchedulerPaths:
        """Resolve script and log paths for a synthetic scheduler plan."""

        safe_job_name = self._safe_job_name(job_name or "geneagent-job")
        path_cls = self._path_class(working_directory)
        workdir = path_cls(working_directory)
        script_dir = workdir / ".geneagent" / "scheduler"
        log_dir = workdir / "logs"
        extension = "sbatch" if self.kind == SchedulerKind.SLURM else "pbs"
        return SchedulerPaths(
            working_directory=str(workdir),
            script_path=str(script_dir / f"{safe_job_name}.{extension}.sh"),
            stdout_path=str(log_dir / f"{safe_job_name}.{self.kind.value}.stdout.log"),
            stderr_path=str(log_dir / f"{safe_job_name}.{self.kind.value}.stderr.log"),
        )

    def _normalize_resources(
        self,
        resources: ResourceEstimate,
        paths: SchedulerPaths,
        job_name: str | None,
    ) -> SchedulerResourceRequest:
        """Normalize a coarse resource estimate into a richer scheduler request."""

        hints: list[str] = []
        if resources.conservative_default:
            hints.append("Resource request still uses conservative defaults from the estimator.")
        hints.append("Submission remains plan-only until the real cluster integration is enabled.")
        return SchedulerResourceRequest(
            job_name=self._safe_job_name(job_name or "geneagent-job"),
            nodes=1,
            tasks=1,
            cpus_per_task=max(1, int(resources.cpus)),
            memory_gb=max(1, int(resources.memory_gb)),
            walltime=self._normalize_walltime(resources.walltime),
            partition=resources.partition,
            conservative_default=resources.conservative_default,
            scheduler_hints=hints,
            environment_exports={
                "GENEAGENT_SCHEDULER_KIND": self.kind.value,
                "GENEAGENT_STDOUT_PATH": paths.stdout_path,
                "GENEAGENT_STDERR_PATH": paths.stderr_path,
            },
        )

    def _compose_script(
        self,
        command: list[str],
        request: SchedulerResourceRequest,
        paths: SchedulerPaths,
        task_id: str,
        run_id: str,
    ) -> str:
        """Compose a bash submission script preview."""

        path_cls = self._path_class(paths.working_directory)
        script_dir = path_cls(paths.script_path).parent
        log_dir = path_cls(paths.stdout_path).parent
        lines = ["#!/usr/bin/env bash"]
        lines.extend(self._directive_lines(request=request, paths=paths))
        lines.extend(
            [
                "",
                "set -euo pipefail",
                "",
                f"# task_id: {task_id}",
                f"# run_id: {run_id}",
                f"mkdir -p {shlex.quote(str(script_dir))}",
                f"mkdir -p {shlex.quote(str(log_dir))}",
                f"cd {shlex.quote(paths.working_directory)}",
            ]
        )
        if request.conda_env_name:
            lines.extend(
                [
                    'if command -v conda >/dev/null 2>&1; then',
                    '  eval "$(conda shell.bash hook)"',
                    f"  conda activate {shlex.quote(request.conda_env_name)}",
                    "fi",
                ]
            )
        for key, value in request.environment_exports.items():
            lines.append(f"export {key}={shlex.quote(value)}")
        lines.append("")
        lines.append("# Synthetic plan: do not assume this script has been submitted.")
        lines.append(shlex.join(command or ["echo", "geneagent-placeholder"]))
        return "\n".join(lines)

    def _build_job_handle(
        self,
        paths: SchedulerPaths,
        job_name: str,
        mode: str,
        task_id: str,
        run_id: str,
    ) -> JobHandle:
        """Create a synthetic job handle for dry-run or submit-preview flows."""

        prefix = "DRYRUN" if mode == "dry-run" else "PLAN"
        return JobHandle(
            run_context=RunContext(
                task_id=task_id,
                run_id=run_id,
                working_directory=paths.working_directory,
            ),
            scheduler=self.kind,
            job_id=f"{prefix}-{self.kind.value.upper()}-{self._safe_job_name(task_id)}-{self._safe_job_name(run_id)}-{job_name.upper()}",
            state=JobState.DRAFT,
            stdout_path=paths.stdout_path,
            stderr_path=paths.stderr_path,
        )

    def _plan_warnings(
        self,
        request: SchedulerResourceRequest,
        mode: str,
        task_id_supplied: bool,
        run_id_supplied: bool,
    ) -> list[str]:
        """Return planning-time warnings that should be shown to the caller."""

        warnings = [
            "No real scheduler command will be executed from this adapter.",
            "Job identifiers are synthetic and suitable only for dry-run or planning flows.",
        ]
        if request.conservative_default:
            warnings.append("Resource sizing still comes from conservative defaults, not empirical profiling.")
        if mode != "dry-run":
            warnings.append("submit() currently returns a submit-preview handle until real submission is enabled.")
        if not task_id_supplied:
            warnings.append("task_id was not supplied by upstream orchestration; a compatibility fallback was generated.")
        if not run_id_supplied:
            warnings.append("run_id was not supplied by upstream orchestration; a compatibility fallback was generated.")
        return warnings

    def _ready_for_gate_status(self, mode: str) -> str:
        """Return a stage-oriented gate status instead of a boolean readiness flag."""

        if mode == "submit-preview":
            return "awaiting_submission_gate"
        return "scheduler_plan_ready"

    def _normalize_walltime(self, walltime: str) -> str:
        """Normalize a scheduler walltime string into HH:MM:SS."""

        if re.fullmatch(r"\d{2}:\d{2}:\d{2}", walltime):
            return walltime
        if re.fullmatch(r"\d{1,2}:\d{2}", walltime):
            hours, minutes = walltime.split(":")
            return f"{int(hours):02d}:{int(minutes):02d}:00"
        return "04:00:00"

    def _safe_job_name(self, value: str) -> str:
        """Return a scheduler-safe job name with stable characters only."""

        cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", value.strip())
        cleaned = cleaned.strip("-._")
        return cleaned[:64] or "geneagent-job"

    def _resolve_tracking_ids(self, task_id: str | None, run_id: str | None, job_name: str) -> dict[str, str]:
        """Resolve chain-wide tracking identifiers with compatibility fallbacks."""

        safe_job_name = self._safe_job_name(job_name)
        return {
            "task_id": task_id or f"compat-task-{safe_job_name}",
            "run_id": run_id or f"compat-run-{safe_job_name}",
        }

    def _path_class(self, raw_path: str):
        """Choose a path flavor that preserves the caller's path style."""

        if raw_path.startswith("/") or ("/" in raw_path and "\\" not in raw_path):
            return PurePosixPath
        return PureWindowsPath
