"""Abstract scheduler adapter API with planning and optional real execution."""

from __future__ import annotations

from abc import ABC, abstractmethod
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shlex
import shutil
import subprocess
import time
from typing import Callable

from contracts.common import JobState, SchedulerKind
from contracts.execution import JobHandle, RunContext
from contracts.tasks import ResourceEstimate
from scheduler.models import SchedulerPaths, SchedulerResourceRequest, SubmissionPlan


class SchedulerExecutionError(RuntimeError):
    """Raised when a real scheduler command cannot complete successfully."""

    def __init__(
        self,
        message: str,
        *,
        command: list[str] | None = None,
        stdout: str = "",
        stderr: str = "",
        attempts: int = 0,
        error_code: str | None = None,
        retryable: bool | None = None,
        phase: str | None = None,
    ) -> None:
        super().__init__(message)
        self.command = command or []
        self.stdout = stdout
        self.stderr = stderr
        self.attempts = attempts
        self.error_code = error_code
        self.retryable = retryable
        self.phase = phase


class BaseSchedulerAdapter(ABC):
    """Scheduler abstraction used by SLURM and PBS adapters."""

    kind: SchedulerKind

    def __init__(
        self,
        *,
        real_execution_enabled: bool = False,
        retry_max_attempts: int = 3,
        retry_backoff_seconds: list[int] | None = None,
        command_timeout_seconds: int = 60,
        command_runner: Callable[[list[str], str | None, int], subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self._real_execution_enabled = real_execution_enabled
        self._retry_max_attempts = max(1, int(retry_max_attempts))
        self._retry_backoff_seconds = retry_backoff_seconds or [2, 5, 10]
        self._command_timeout_seconds = max(1, int(command_timeout_seconds))
        self._command_runner = command_runner or self._default_command_runner

    @property
    def real_execution_enabled(self) -> bool:
        return self._real_execution_enabled

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

        resolved_command = command or ["echo", "geneagent-noop"]
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
        submit_command = self._submit_command(paths.script_path)
        wrapper_preview = self._compose_wrapper(
            submit_command=submit_command,
            poll_command_hint=self._poll_command_hint(
                f"{self.kind.value.upper()}-JOB-PLACEHOLDER-{tracking['run_id']}"
            ),
            paths=paths,
            mode=mode,
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
        poll_strategy = self._poll_strategy(handle=handle)
        failure_recovery = self._failure_recovery_plan(handle=handle, request=request, paths=paths)
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
            wrapper_preview=wrapper_preview,
            submit_command=submit_command,
            job_handle=handle,
            warnings=warnings,
            compatibility_notes=self.compatibility_notes(),
            polling_hint=self._poll_command_hint(handle.job_id),
            poll_strategy=poll_strategy,
            failure_recovery=failure_recovery,
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
        """Submit a scheduler script in real mode, or return preview handle when disabled."""

        plan = self.build_submission_plan(
            command=command or ["echo", "geneagent-submit"],
            working_directory=working_directory,
            resources=resources,
            job_name=job_name,
            mode="submit",
            task_id=task_id,
            run_id=run_id,
        )
        if not self._real_execution_enabled:
            return plan.job_handle

        self._materialize_submission_files(plan=plan)
        errors: list[SchedulerExecutionError] = []
        for attempt in range(1, self._retry_max_attempts + 1):
            try:
                result = self._run_command(
                    command=plan.submit_command,
                    cwd=plan.paths.working_directory,
                    timeout_seconds=self._command_timeout_seconds,
                )
                if result.returncode != 0:
                    raise self._build_submit_returncode_error(
                        command=plan.submit_command,
                        result=result,
                        attempt=attempt,
                    )
                job_id = self._parse_submit_output(
                    stdout=result.stdout,
                    stderr=result.stderr,
                    returncode=result.returncode,
                )
                return JobHandle(
                    run_context=RunContext(
                        task_id=plan.task_id,
                        run_id=plan.run_id,
                        working_directory=plan.paths.working_directory,
                    ),
                    scheduler=self.kind,
                    job_id=job_id,
                    state=JobState.QUEUED,
                    stdout_path=plan.paths.stdout_path,
                    stderr_path=plan.paths.stderr_path,
                )
            except SchedulerExecutionError as error:
                errors.append(error)
                if attempt >= self._retry_max_attempts or not self._is_retryable_submit_error(error):
                    break
                backoff = self._retry_backoff_seconds[min(attempt - 1, len(self._retry_backoff_seconds) - 1)]
                time.sleep(max(0, backoff))

        last = errors[-1] if errors else SchedulerExecutionError("Scheduler submission failed.")
        raise SchedulerExecutionError(
            "Scheduler submission failed after retry attempts.",
            command=last.command,
            stdout=last.stdout,
            stderr=last.stderr,
            attempts=len(errors),
            error_code=last.error_code,
            retryable=last.retryable,
            phase=last.phase,
        )

    def poll(self, job_id: str) -> JobState:
        """Query scheduler state in real mode; otherwise infer from synthetic identifiers."""

        normalized = job_id.upper()
        if normalized.startswith(("DRYRUN-", "PLAN-", "SKIPPED-NONBIO-")):
            return JobState.DRAFT
        if self._real_execution_enabled:
            try:
                return self._poll_real(job_id)
            except SchedulerExecutionError:
                return JobState.UNKNOWN
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
    def _parse_submit_output(self, *, stdout: str, stderr: str, returncode: int) -> str:
        """Extract a scheduler job id from submit command output."""

    @abstractmethod
    def _poll_real(self, job_id: str) -> JobState:
        """Query real scheduler state for a concrete job id."""

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
            wrapper_path=str(script_dir / f"{safe_job_name}.wrapper.sh"),
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
        if self._real_execution_enabled:
            hints.append("Scheduler real execution is enabled; submit() may call sbatch/qsub.")
        else:
            hints.append("Submission remains plan-only until scheduler real execution is enabled.")
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
        lines.append("# Generated by GeneAgent scheduler adapter.")
        lines.append(shlex.join(command or ["echo", "geneagent-noop"]))
        return "\n".join(lines)

    def _compose_wrapper(
        self,
        *,
        submit_command: list[str],
        poll_command_hint: str,
        paths: SchedulerPaths,
        mode: str,
        task_id: str,
        run_id: str,
    ) -> str:
        """Compose a wrapper preview that documents submit and poll behavior."""

        path_cls = self._path_class(paths.working_directory)
        wrapper_dir = path_cls(paths.wrapper_path).parent
        lines = [
            "#!/usr/bin/env bash",
            "set -euo pipefail",
            "",
            f"# task_id: {task_id}",
            f"# run_id: {run_id}",
            f"# mode: {mode}",
            f"mkdir -p {shlex.quote(str(wrapper_dir))}",
            f"cd {shlex.quote(paths.working_directory)}",
            "",
            "# 1) Submit phase:",
            shlex.join(submit_command),
            "",
            "# 2) Poll loop hint:",
            f"echo \"poll_hint: {poll_command_hint}\"",
            "echo \"recommended: queued->running poll with backoff 15s/30s/60s\"",
            "",
            "# 3) Failure recovery hook:",
            "echo \"if failed: inspect stderr, auto-retry transient scheduler failures, then require manual confirmation\"",
        ]
        return "\n".join(lines)

    def _poll_strategy(self, handle: JobHandle) -> list[str]:
        """Return a deterministic poll strategy template for dry-run and submit-preview."""

        poll_hint = self._poll_command_hint(handle.job_id)
        return [
            f"queued: sleep 15s then poll -> {poll_hint}",
            f"running: sleep 30s then poll -> {poll_hint}",
            "stalled: after 10 polls collect scheduler diagnostics and queue constraints",
            "completed: collect outputs and build report index",
            "failed: trigger failure recovery checklist",
        ]

    def _failure_recovery_plan(
        self,
        *,
        handle: JobHandle,
        request: SchedulerResourceRequest,
        paths: SchedulerPaths,
    ) -> list[str]:
        """Return a conservative failure recovery checklist."""

        bumped_cpu = max(request.cpus_per_task + 2, int(request.cpus_per_task * 1.25))
        bumped_mem = max(request.memory_gb + 8, int(request.memory_gb * 1.25))
        return [
            f"capture logs: stdout={paths.stdout_path}, stderr={paths.stderr_path}",
            f"job_id={handle.job_id}: classify failure as resource, environment, or input issue",
            "auto retry strategy: transient submit errors retried with configured backoff before surfacing failure",
            "resource recovery: rerun dry-run with +25% CPU or memory before any resubmission",
            f"suggested retry resources: cpus_per_task={bumped_cpu}, memory_gb={bumped_mem}",
            "require manual approval before requeue when output overwrite or bulk recompute is involved",
        ]

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
        state = JobState.DRAFT if mode in {"dry-run", "submit-preview", "submit"} else JobState.UNKNOWN
        return JobHandle(
            run_context=RunContext(
                task_id=task_id,
                run_id=run_id,
                working_directory=paths.working_directory,
            ),
            scheduler=self.kind,
            job_id=f"{prefix}-{self.kind.value.upper()}-{self._safe_job_name(task_id)}-{self._safe_job_name(run_id)}-{job_name.upper()}",
            state=state,
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

        warnings: list[str] = []
        if not self._real_execution_enabled:
            warnings.append("No real scheduler command will be executed from this adapter.")
            warnings.append("Job identifiers are synthetic and suitable only for dry-run or planning flows.")
        else:
            warnings.append("Real scheduler execution is enabled; submit() may issue sbatch/qsub.")
            warnings.append(
                f"Transient submit failures will auto-retry up to {self._retry_max_attempts} attempts."
            )
        if request.conservative_default:
            warnings.append("Resource sizing still comes from conservative defaults, not empirical profiling.")
        if mode == "submit-preview":
            warnings.append("submit-preview mode does not issue real scheduler submission.")
        if not task_id_supplied:
            warnings.append("task_id was not supplied by upstream orchestration; a compatibility fallback was generated.")
        if not run_id_supplied:
            warnings.append("run_id was not supplied by upstream orchestration; a compatibility fallback was generated.")
        return warnings

    def _ready_for_gate_status(self, mode: str) -> str:
        """Return a stage-oriented gate status instead of a boolean readiness flag."""

        if mode in {"submit-preview", "submit"}:
            return "awaiting_submission_gate"
        return "scheduler_plan_ready"

    def _build_submit_returncode_error(
        self,
        *,
        command: list[str],
        result: subprocess.CompletedProcess[str],
        attempt: int,
    ) -> SchedulerExecutionError:
        """Build a scheduler-specific submit failure error for non-zero return code."""

        return SchedulerExecutionError(
            "Scheduler submit command returned non-zero exit code.",
            command=command,
            stdout=result.stdout,
            stderr=result.stderr,
            attempts=attempt,
            error_code="SUBMIT_FAILED",
            retryable=True,
            phase="submit",
        )

    def _is_retryable_submit_error(self, error: SchedulerExecutionError) -> bool:
        """Return whether a submit error should trigger automatic retry."""

        if error.retryable is not None:
            return error.retryable
        return True

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

    def _materialize_submission_files(self, plan: SubmissionPlan) -> None:
        """Write scheduler script and wrapper files before real submission."""

        try:
            script_path = Path(plan.paths.script_path)
            wrapper_path = Path(plan.paths.wrapper_path)
            script_path.parent.mkdir(parents=True, exist_ok=True)
            wrapper_path.parent.mkdir(parents=True, exist_ok=True)
            script_path.write_text(plan.script_preview + "\n", encoding="utf-8")
            wrapper_path.write_text(plan.wrapper_preview + "\n", encoding="utf-8")
        except OSError as error:
            raise SchedulerExecutionError(
                f"Failed to materialize scheduler files: {error}",
                command=plan.submit_command,
            ) from error

    def _run_command(
        self,
        *,
        command: list[str],
        cwd: str | None,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        try:
            return self._command_runner(command, cwd, timeout_seconds)
        except FileNotFoundError as error:
            raise SchedulerExecutionError(
                (
                    f"Scheduler command not found in runtime environment: {command[0] if command else '<empty>'}. "
                    "Use dry-run/submit-preview on local Windows, or run real submit/poll on a host with scheduler CLI."
                ),
                command=command,
                error_code="COMMAND_NOT_FOUND",
                retryable=False,
                phase="command",
            ) from error
        except subprocess.TimeoutExpired as error:
            raise SchedulerExecutionError(
                "Scheduler command timed out.",
                command=command,
                stdout=(error.stdout or "") if isinstance(error.stdout, str) else "",
                stderr=(error.stderr or "") if isinstance(error.stderr, str) else "",
                error_code="TIMEOUT",
                retryable=True,
                phase="command",
            ) from error
        except OSError as error:
            raise SchedulerExecutionError(
                f"Scheduler command execution failed: {error}",
                command=command,
                error_code="OS_ERROR",
                retryable=True,
                phase="command",
            ) from error

    def _default_command_runner(
        self,
        command: list[str],
        cwd: str | None,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        try:
            return subprocess.run(
                command,
                cwd=cwd,
                timeout=timeout_seconds,
                check=False,
                capture_output=True,
                text=True,
            )
        except FileNotFoundError:
            fallback = self._resolve_windows_shell_fallback(command)
            if fallback is None:
                raise
            return subprocess.run(
                fallback,
                cwd=cwd,
                timeout=timeout_seconds,
                check=False,
                capture_output=True,
                text=True,
            )

    def _resolve_windows_shell_fallback(self, command: list[str]) -> list[str] | None:
        """Resolve `.cmd/.bat/.exe` command fallback on Windows for local shim smoke tests."""

        if not command or not self._is_windows_runtime():
            return None
        executable = command[0]
        if Path(executable).suffix:
            return None
        for suffix in (".cmd", ".bat", ".exe", ".com"):
            candidate = shutil.which(f"{executable}{suffix}")
            if candidate:
                return [candidate, *command[1:]]
        return None

    def _is_windows_runtime(self) -> bool:
        return os.name == "nt"
