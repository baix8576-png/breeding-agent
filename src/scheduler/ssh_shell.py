"""Remote SSH-backed shell adapter for ordinary Linux servers."""

from __future__ import annotations

import base64
from pathlib import Path, PurePosixPath
import shlex
import subprocess
import time

from contracts.common import ExecutionMode, JobState, SchedulerKind
from contracts.execution import JobHandle, RunContext
from contracts.remote_execution import RemoteCheckResult, RemoteExecutionProfile, RunState
from contracts.tasks import ResourceEstimate
from scheduler.base import BaseSchedulerAdapter, SchedulerExecutionError
from scheduler.models import SchedulerPaths, SchedulerResourceRequest, SubmissionPlan
from scheduler.remote import SshCommandRunner


class RemoteShellSchedulerAdapter(BaseSchedulerAdapter):
    """Run remote jobs directly through SSH + bash/nohup on a normal Linux server."""

    kind = SchedulerKind.SHELL
    _dangerous_work_roots = {
        "/",
        "/bin",
        "/boot",
        "/data",
        "/data2",
        "/dev",
        "/etc",
        "/home",
        "/lib",
        "/lib64",
        "/opt",
        "/proc",
        "/root",
        "/sbin",
        "/sys",
        "/tmp",
        "/usr",
        "/var",
    }

    def __init__(
        self,
        *,
        profile: RemoteExecutionProfile,
        local_cache_root: str | Path | None = None,
        command_runner=None,
        remote_cpu_cap: int = 32,
        remote_memory_gb_cap: int = 256,
        remote_walltime_cap: str = "24:00:00",
        remote_max_concurrent_runs: int = 2,
        process_limits_enabled: bool = True,
        **kwargs,
    ) -> None:
        self.profile = profile
        self._local_cache_root = Path(local_cache_root or ".geneagent")
        self._remote_cpu_cap = max(1, int(remote_cpu_cap))
        self._remote_memory_gb_cap = max(1, int(remote_memory_gb_cap))
        self._remote_walltime_cap = self._normalize_walltime(remote_walltime_cap)
        self._remote_max_concurrent_runs = max(1, int(remote_max_concurrent_runs))
        self._process_limits_enabled = bool(process_limits_enabled)
        remote_runner = command_runner or SshCommandRunner(profile=profile)
        super().__init__(command_runner=remote_runner, **kwargs)

    def build_submission_plan(
        self,
        command: list[str],
        working_directory: str,
        resources: ResourceEstimate,
        job_name: str | None = None,
        mode: str = "dry-run",
        task_id: str | None = None,
        run_id: str | None = None,
        atomic_tools: list[str] | None = None,
    ) -> SubmissionPlan:
        tracking = self._resolve_tracking_ids(task_id=task_id, run_id=run_id, job_name=job_name or "geneagent-job")
        remote_run_dir = self._remote_run_dir(task_id=tracking["task_id"], run_id=tracking["run_id"])
        self._validate_remote_working_directory(working_directory)
        return super().build_submission_plan(
            command=command,
            working_directory=remote_run_dir,
            resources=resources,
            job_name=job_name,
            mode=mode,
            task_id=tracking["task_id"],
            run_id=tracking["run_id"],
            atomic_tools=atomic_tools,
        )

    def submit(
        self,
        working_directory: str,
        resources: ResourceEstimate,
        command: list[str] | None = None,
        job_name: str | None = None,
        task_id: str | None = None,
        run_id: str | None = None,
        atomic_tools: list[str] | None = None,
    ) -> JobHandle:
        plan = self.build_submission_plan(
            command=command or ["echo", "geneagent-submit"],
            working_directory=working_directory,
            resources=resources,
            job_name=job_name,
            mode="submit",
            task_id=task_id,
            run_id=run_id,
            atomic_tools=atomic_tools,
        )
        if not self._real_execution_enabled:
            return plan.job_handle

        self._raise_if_resource_guard_blocked(plan)
        cached_handle = self._load_idempotent_submission(plan)
        if cached_handle is not None:
            return cached_handle

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
                handle = JobHandle(
                    run_context=RunContext(
                        task_id=plan.task_id,
                        run_id=plan.run_id,
                        working_directory=plan.paths.working_directory,
                    ),
                    scheduler=self.kind,
                    job_id=job_id,
                    state=JobState.RUNNING,
                    stdout_path=plan.paths.stdout_path,
                    stderr_path=plan.paths.stderr_path,
                )
                self._persist_idempotent_submission(plan=plan, handle=handle)
                return handle
            except SchedulerExecutionError as error:
                errors.append(error)
                if attempt >= self._retry_max_attempts or not self._is_retryable_submit_error(error):
                    break
                backoff = self._retry_backoff_seconds[min(attempt - 1, len(self._retry_backoff_seconds) - 1)]
                time.sleep(max(0, backoff))

        last = errors[-1] if errors else SchedulerExecutionError("Remote shell submission failed.")
        raise SchedulerExecutionError(
            "Remote shell submission failed after retry attempts.",
            command=last.command,
            stdout=last.stdout,
            stderr=last.stderr,
            attempts=len(errors),
            error_code=last.error_code,
            retryable=last.retryable,
            phase=last.phase,
        )

    def poll_run(self, state: RunState) -> JobState:
        """Poll a persisted run using task_id/run_id to recover the remote run directory."""

        run_dir = self._remote_run_dir(task_id=state.task_id, run_id=state.run_id)
        return self._poll_remote_run(run_dir=run_dir, job_id=state.job_id or "")

    def remote_check(self, *, timeout_seconds: int | None = None) -> RemoteCheckResult:
        """Check SSH and ordinary shell prerequisites without requiring SLURM."""

        timeout = timeout_seconds or self._command_timeout_seconds
        messages: list[str] = []
        if not self.profile.host:
            messages.append("missing_hpc_host")
        if not self.profile.user:
            messages.append("missing_hpc_user")
        if messages:
            return RemoteCheckResult(
                profile_name=self.profile.profile_name,
                execution_mode=ExecutionMode.SSH_SHELL_TRUSTED,
                scheduler=SchedulerKind.SHELL,
                ssh_target=self.profile.ssh_target,
                work_root=self.profile.work_root,
                reachable=False,
                safe_for_submit=False,
                command_checks={},
                tool_checks={},
                missing_commands=[],
                messages=messages,
            )
        try:
            self._validate_remote_work_root()
        except ValueError as error:
            return RemoteCheckResult(
                profile_name=self.profile.profile_name,
                execution_mode=ExecutionMode.SSH_SHELL_TRUSTED,
                scheduler=SchedulerKind.SHELL,
                ssh_target=self.profile.ssh_target,
                work_root=self.profile.work_root,
                reachable=False,
                safe_for_submit=False,
                command_checks={},
                tool_checks={},
                missing_commands=[],
                messages=["work_root_policy_violation", str(error)],
            )

        commands = ["bash", "nohup", "ps", "kill", "mkdir", "chmod", "test", "cat", "base64"]
        command_probe = "; ".join(
            [
                "for t in "
                + " ".join(shlex.quote(command) for command in commands)
                + '; do if command -v "$t" >/dev/null 2>&1; then echo "command:$t=ok"; else echo "command:$t=missing"; fi; done',
                (
                    f"if test -d {shlex.quote(self.profile.work_root)} "
                    f"|| mkdir -p {shlex.quote(self.profile.work_root)}; "
                    "then echo work_root=ok; else echo work_root=missing; fi"
                ),
                *[
                    f"if test -x {shlex.quote(path)}; then echo tool:{shlex.quote(name)}=ok; else echo tool:{shlex.quote(name)}=missing; fi"
                    for name, path in self.profile.tool_paths.items()
                ],
            ]
        )
        try:
            result = self._run_command(
                command=["bash", "-lc", command_probe],
                cwd=None,
                timeout_seconds=timeout,
            )
        except SchedulerExecutionError as error:
            return RemoteCheckResult(
                profile_name=self.profile.profile_name,
                execution_mode=ExecutionMode.SSH_SHELL_TRUSTED,
                scheduler=SchedulerKind.SHELL,
                ssh_target=self.profile.ssh_target,
                work_root=self.profile.work_root,
                reachable=False,
                safe_for_submit=False,
                messages=["ssh_probe_failed", str(error)],
            )

        command_checks: dict[str, bool] = {}
        tool_checks: dict[str, bool] = {}
        work_root_ok = False
        for line in result.stdout.splitlines():
            stripped = line.strip()
            if stripped.startswith("command:"):
                name, _, value = stripped.removeprefix("command:").partition("=")
                command_checks[name] = value == "ok"
            elif stripped.startswith("tool:"):
                name, _, value = stripped.removeprefix("tool:").partition("=")
                tool_checks[name] = value == "ok"
            elif stripped == "work_root=ok":
                work_root_ok = True
        missing_commands = [name for name, ok in command_checks.items() if not ok]
        reachable = result.returncode == 0
        safe_for_submit = reachable and work_root_ok and not missing_commands
        result_messages = []
        if not reachable:
            result_messages.append("ssh_probe_nonzero")
        if not work_root_ok:
            result_messages.append("work_root_missing")
        result_messages.extend(f"missing_command:{name}" for name in missing_commands)
        return RemoteCheckResult(
            profile_name=self.profile.profile_name,
            execution_mode=ExecutionMode.SSH_SHELL_TRUSTED,
            scheduler=SchedulerKind.SHELL,
            ssh_target=self.profile.ssh_target,
            work_root=self.profile.work_root,
            reachable=reachable,
            safe_for_submit=safe_for_submit,
            command_checks=command_checks,
            tool_checks=tool_checks,
            missing_commands=missing_commands,
            messages=result_messages,
        )

    def _build_paths(self, working_directory: str, job_name: str | None) -> SchedulerPaths:
        workdir = PurePosixPath(working_directory)
        log_dir = workdir / "logs"
        return SchedulerPaths(
            working_directory=str(workdir),
            script_path=str(workdir / "run.sh"),
            wrapper_path=str(workdir / ".geneagent" / "scheduler" / f"{self._safe_job_name(job_name or 'geneagent-job')}.wrapper.sh"),
            stdout_path=str(log_dir / "stdout.log"),
            stderr_path=str(log_dir / "stderr.log"),
        )

    def _directive_lines(self, request: SchedulerResourceRequest, paths: SchedulerPaths) -> list[str]:
        _ = paths
        return [
            "# shell_backend: ssh_shell_trusted",
            f"# requested_cpus: {request.cpus_per_task}",
            f"# requested_memory_gb: {request.memory_gb}",
            f"# requested_walltime: {request.walltime}",
            f"# remote_cpu_cap: {self._remote_cpu_cap}",
            f"# remote_memory_gb_cap: {self._remote_memory_gb_cap}",
            f"# remote_walltime_cap: {self._remote_walltime_cap}",
            "# note: ordinary Linux shell mode has no scheduler-side resource isolation.",
        ]

    def _normalize_resources(
        self,
        resources: ResourceEstimate,
        paths: SchedulerPaths,
        job_name: str | None,
        atomic_tools: list[str] | None = None,
    ) -> SchedulerResourceRequest:
        request = super()._normalize_resources(
            resources=resources,
            paths=paths,
            job_name=job_name,
            atomic_tools=atomic_tools,
        )
        thread_count = str(min(request.cpus_per_task, self._remote_cpu_cap))
        exports = dict(request.environment_exports)
        exports.update(
            {
                "OMP_NUM_THREADS": thread_count,
                "OPENBLAS_NUM_THREADS": thread_count,
                "MKL_NUM_THREADS": thread_count,
                "VECLIB_MAXIMUM_THREADS": thread_count,
                "NUMEXPR_NUM_THREADS": thread_count,
                "GOTO_NUM_THREADS": thread_count,
                "GENEAGENT_REMOTE_CPU_CAP": str(self._remote_cpu_cap),
                "GENEAGENT_REMOTE_MEMORY_GB_CAP": str(self._remote_memory_gb_cap),
                "GENEAGENT_REMOTE_WALLTIME_CAP": self._remote_walltime_cap,
            }
        )
        return request.model_copy(
            update={
                "environment_exports": exports,
                "scheduler_hints": [
                    *request.scheduler_hints,
                    "Remote shell guard: common thread environment variables are capped for ordinary server safety.",
                ],
            }
        )

    def _compose_script(
        self,
        command: list[str],
        request: SchedulerResourceRequest,
        paths: SchedulerPaths,
        task_id: str,
        run_id: str,
    ) -> str:
        script = super()._compose_script(
            command=command,
            request=request,
            paths=paths,
            task_id=task_id,
            run_id=run_id,
        )
        if not self._process_limits_enabled:
            return script
        requested_seconds = self._walltime_to_seconds(request.walltime)
        cap_seconds = self._walltime_to_seconds(self._remote_walltime_cap)
        cpu_seconds = min(value for value in (requested_seconds, cap_seconds) if value > 0)
        memory_kb = min(request.memory_gb, self._remote_memory_gb_cap) * 1024 * 1024
        guard_lines = [
            "# GeneAgent ordinary-server process guard.",
            f"ulimit -t {cpu_seconds} || echo \"geneagent_warning: cpu_time_ulimit_unavailable\" >&2",
            f"ulimit -v {memory_kb} || echo \"geneagent_warning: memory_ulimit_unavailable\" >&2",
        ]
        lines = script.splitlines()
        insert_at = 1
        for index, line in enumerate(lines):
            if line.strip() == "set -euo pipefail":
                insert_at = index + 1
                break
        return "\n".join([*lines[:insert_at], *guard_lines, *lines[insert_at:]])

    def _assess_quota(self, request: SchedulerResourceRequest) -> dict[str, object]:
        assessment = super()._assess_quota(request)
        reasons = [str(item) for item in assessment.get("reasons", [])]
        status = str(assessment.get("status", "pass"))

        def block(reason: str) -> None:
            nonlocal status
            status = "blocked"
            reasons.append(reason)

        if request.cpus_per_task > self._remote_cpu_cap:
            block(f"shell_cpu_cap_exceeded(requested={request.cpus_per_task},limit={self._remote_cpu_cap})")
        if request.memory_gb > self._remote_memory_gb_cap:
            block(f"shell_memory_cap_exceeded(requested={request.memory_gb},limit={self._remote_memory_gb_cap})")
        if self._walltime_to_seconds(request.walltime) > self._walltime_to_seconds(self._remote_walltime_cap):
            block(f"shell_walltime_cap_exceeded(requested={request.walltime},limit={self._remote_walltime_cap})")
        concurrent_after_submit = self._current_active_jobs + request.tasks
        if concurrent_after_submit > self._remote_max_concurrent_runs:
            block(
                "shell_concurrency_cap_exceeded("
                f"active={self._current_active_jobs},requested={request.tasks},limit={self._remote_max_concurrent_runs})"
            )

        usage = dict(assessment.get("usage", {}))
        usage.update(
            {
                "remote_shell_cpu_cap": self._remote_cpu_cap,
                "remote_shell_memory_gb_cap": self._remote_memory_gb_cap,
                "remote_shell_walltime_cap_seconds": self._walltime_to_seconds(self._remote_walltime_cap),
                "remote_shell_max_concurrent_runs": self._remote_max_concurrent_runs,
            }
        )
        assessment["status"] = status
        assessment["reasons"] = reasons
        assessment["usage"] = usage
        return assessment

    def _submit_command(self, script_path: str) -> list[str]:
        run_dir = str(PurePosixPath(script_path).parent)
        launch = "; ".join(
            [
                "set -euo pipefail",
                f"cd {shlex.quote(run_dir)}",
                (
                    "if test -e state/pid || test -e state/done || test -e state/failed; "
                    "then echo existing_state_file >&2; exit 70; fi"
                ),
                (
                    "nohup bash -lc "
                    + shlex.quote(
                        "cd "
                        + shlex.quote(run_dir)
                        + " && bash run.sh > logs/stdout.log 2> logs/stderr.log; "
                        "code=$?; echo \"$code\" > state/exit_code; "
                        "if [ \"$code\" -eq 0 ]; then touch state/done; else touch state/failed; fi"
                    )
                    + " >/dev/null 2>&1 & pid=$!"
                ),
                "echo \"$pid\" > state/pid",
                "echo \"$pid\"",
            ]
        )
        return ["bash", "-lc", launch]

    def _poll_command_hint(self, job_id: str) -> str:
        return f"ssh shell poll for {job_id}: check state/done, state/failed, and kill -0 pid"

    def _parse_submit_output(self, *, stdout: str, stderr: str, returncode: int) -> str:
        _ = (stderr, returncode)
        for line in stdout.splitlines():
            stripped = line.strip()
            if stripped.isdigit():
                return f"shell:{stripped}"
        raise SchedulerExecutionError(
            "Unable to parse remote shell PID from submit output.",
            stdout=stdout,
            stderr=stderr,
            error_code="SHELL_PID_PARSE_FAILED",
            retryable=False,
            phase="submit",
        )

    def _poll_real(self, job_id: str) -> JobState:
        return self._poll_remote_run(run_dir=self.profile.work_root, job_id=job_id)

    def compatibility_notes(self) -> list[str]:
        return [
            "Remote shell mode targets ordinary Linux servers without SLURM/PBS.",
            "Jobs run via SSH + bash/nohup and are tracked with PID plus state sentinel files.",
            "The server does not enforce scheduler-side CPU, memory, walltime, partition, or queue limits.",
            "GeneAgent resource caps are pre-submit safety gates and script parameters only in shell mode.",
            "Use ssh_slurm_trusted instead when sbatch/squeue/sacct are available.",
        ]

    def _materialize_submission_files(self, plan: SubmissionPlan) -> None:
        self._validate_remote_working_directory(plan.paths.working_directory)
        script_payload = base64.b64encode((plan.script_preview + "\n").encode("utf-8")).decode("ascii")
        wrapper_payload = base64.b64encode((plan.wrapper_preview + "\n").encode("utf-8")).decode("ascii")
        work_dir = PurePosixPath(plan.paths.working_directory)
        wrapper_path = PurePosixPath(plan.paths.wrapper_path)
        remote_script = "\n".join(
            [
                "set -euo pipefail",
                (
                    f"mkdir -p {shlex.quote(str(work_dir))} "
                    f"{shlex.quote(str(work_dir / 'logs'))} "
                    f"{shlex.quote(str(work_dir / 'state'))} "
                    f"{shlex.quote(str(work_dir / 'results'))} "
                    f"{shlex.quote(str(work_dir / 'reports'))} "
                    f"{shlex.quote(str(wrapper_path.parent))}"
                ),
                f"printf %s {shlex.quote(script_payload)} | base64 -d > {shlex.quote(str(work_dir / 'run.sh'))}",
                f"printf %s {shlex.quote(wrapper_payload)} | base64 -d > {shlex.quote(str(wrapper_path))}",
                f"chmod 700 {shlex.quote(str(work_dir / 'run.sh'))} {shlex.quote(str(wrapper_path))}",
            ]
        )
        result = self._run_command(
            command=["bash", "-lc", remote_script],
            cwd=None,
            timeout_seconds=self._command_timeout_seconds,
        )
        if result.returncode != 0:
            raise SchedulerExecutionError(
                "Failed to materialize remote shell files.",
                command=["bash", "-lc", "<remote-shell-materialize>"],
                stdout=result.stdout,
                stderr=result.stderr,
                error_code="REMOTE_SHELL_MATERIALIZE_FAILED",
                retryable=True,
                phase="materialize",
            )

    def _submission_cache_path(self, *, plan: SubmissionPlan) -> Path:
        profile_name = self._safe_job_name(self.profile.profile_name)
        return (
            self._local_cache_root
            / "scheduler"
            / "remote_shell_submissions"
            / profile_name
            / plan.task_id
            / f"{plan.run_id}.json"
        )

    def _poll_remote_run(self, *, run_dir: str, job_id: str) -> JobState:
        pid = self._pid_from_job_id(job_id)
        poll_script = "\n".join(
            [
                "set -euo pipefail",
                f"cd {shlex.quote(run_dir)}",
                'if test -f state/done; then code="$(cat state/exit_code 2>/dev/null || echo 0)"; echo "completed:${code}"; exit 0; fi',
                'if test -f state/failed; then code="$(cat state/exit_code 2>/dev/null || echo 1)"; echo "failed:${code}"; exit 0; fi',
                (
                    f"pid={shlex.quote(pid)}"
                    if pid
                    else 'pid="$(cat state/pid 2>/dev/null || true)"'
                ),
                'if test -n "$pid" && kill -0 "$pid" >/dev/null 2>&1; then echo running; exit 0; fi',
                "echo unknown",
            ]
        )
        result = self._run_command(
            command=["bash", "-lc", poll_script],
            cwd=None,
            timeout_seconds=self._command_timeout_seconds,
        )
        if result.returncode != 0:
            raise SchedulerExecutionError(
                "Unable to poll remote shell run state.",
                command=["bash", "-lc", "<remote-shell-poll>"],
                stdout=result.stdout,
                stderr=result.stderr,
                error_code="REMOTE_SHELL_POLL_FAILED",
                retryable=True,
                phase="poll",
            )
        state_line = next((line.strip() for line in result.stdout.splitlines() if line.strip()), "")
        if state_line.startswith("completed:"):
            return JobState.COMPLETED
        if state_line.startswith("failed:"):
            return JobState.FAILED
        if state_line == "running":
            return JobState.RUNNING
        return JobState.UNKNOWN

    def _remote_run_dir(self, *, task_id: str, run_id: str) -> str:
        work_root = self._validate_remote_work_root()
        return str(work_root / self._safe_path_component(task_id) / self._safe_path_component(run_id))

    def _validate_remote_work_root(self) -> PurePosixPath:
        raw = self.profile.work_root
        if "\\" in raw or not raw.startswith("/"):
            raise ValueError("Remote shell work_root must be an absolute POSIX path.")
        work_root = PurePosixPath(raw)
        parts = work_root.parts
        if ".." in parts:
            raise ValueError("Remote shell work_root cannot contain '..'.")
        if str(work_root) in self._dangerous_work_roots:
            raise ValueError("Remote shell work_root is too broad; use a dedicated user-owned run directory.")
        allowed_roots = [self._validate_allowed_write_root(item) for item in self.profile.allowed_write_roots]
        if allowed_roots and not any(work_root == root or root in work_root.parents for root in allowed_roots):
            raise ValueError("Remote shell work_root must stay inside allowed_write_roots.")
        return work_root

    def _validate_allowed_write_root(self, raw: str) -> PurePosixPath:
        if "\\" in raw or not raw.startswith("/"):
            raise ValueError("Remote shell allowed_write_roots must use absolute POSIX paths.")
        root = PurePosixPath(raw)
        if ".." in root.parts:
            raise ValueError("Remote shell allowed_write_roots cannot contain '..'.")
        if str(root) in self._dangerous_work_roots:
            raise ValueError("Remote shell allowed_write_roots entry is too broad.")
        return root

    def _validate_remote_working_directory(self, working_directory: str) -> None:
        if "\\" in working_directory:
            raise ValueError("Remote shell working_directory must use POSIX '/' separators.")
        if not working_directory.startswith("/"):
            raise ValueError("Remote shell working_directory must be an absolute POSIX path.")
        work_root = self._validate_remote_work_root()
        candidate = PurePosixPath(working_directory)
        if ".." in candidate.parts:
            raise ValueError("Remote shell working_directory cannot contain '..'.")
        if candidate != work_root and work_root not in candidate.parents:
            raise ValueError("Remote shell working_directory must stay inside work_root.")

    def _safe_path_component(self, value: str) -> str:
        component = self._safe_job_name(value)
        if component in {"", ".", ".."}:
            raise ValueError("Remote shell path component is unsafe.")
        return component

    def _pid_from_job_id(self, job_id: str) -> str:
        if not job_id.startswith("shell:"):
            return ""
        pid = job_id.removeprefix("shell:").strip()
        return pid if pid.isdigit() else ""

    def _raise_if_resource_guard_blocked(self, plan: SubmissionPlan) -> None:
        if plan.quota_gate_status != "blocked":
            return
        raise SchedulerExecutionError(
            "Remote shell resource guard blocked real submission.",
            command=plan.submit_command,
            stderr="; ".join(plan.quota_gate_reasons),
            error_code="REMOTE_SHELL_RESOURCE_GUARD_BLOCKED",
            retryable=False,
            phase="resource_guard",
        )
