"""Remote SSH-backed SLURM adapter for PC control plane deployments."""

from __future__ import annotations

import base64
from pathlib import Path, PurePosixPath
import shlex
import subprocess
from typing import Callable

from contracts.common import ExecutionMode, SchedulerKind, SshAuthMode
from contracts.remote_execution import ManualSubmitCard, RemoteCheckResult, RemoteExecutionProfile
from scheduler.base import SchedulerExecutionError
from scheduler.models import SubmissionPlan
from scheduler.slurm import SlurmSchedulerAdapter


class SshCommandRunner:
    """Run one remote command through configured SSH authentication."""

    def __init__(
        self,
        *,
        profile: RemoteExecutionProfile,
        local_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self._profile = profile
        self._local_runner = local_runner or subprocess.run

    def __call__(
        self,
        command: list[str],
        cwd: str | None,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        target = self._profile.ssh_target
        if not target:
            return subprocess.CompletedProcess(
                command,
                255,
                stdout="",
                stderr="Remote SSH target is not configured.",
            )
        remote_command = shlex.join(command)
        if cwd:
            remote_command = f"cd {shlex.quote(cwd)} && {remote_command}"
        if self._profile.ssh_auth_mode == SshAuthMode.PASSWORD_ENV:
            return self._run_with_paramiko_password(
                command=command,
                remote_command=remote_command,
                timeout_seconds=timeout_seconds,
            )
        ssh_command = [
            self._profile.ssh_binary,
            "-p",
            str(self._profile.port),
            "-o",
            f"ConnectTimeout={self._profile.connect_timeout_seconds}",
            "-o",
            f"StrictHostKeyChecking={self._profile.strict_host_key_checking}",
        ]
        if self._profile.ssh_auth_mode == SshAuthMode.CONTROL_MASTER:
            if not self._profile.ssh_control_path:
                return subprocess.CompletedProcess(
                    command,
                    255,
                    stdout="",
                    stderr="SSH control master mode requires ssh_control_path.",
                )
            ssh_command.extend(
                [
                    "-o",
                    "BatchMode=yes",
                    "-o",
                    f"ControlPath={self._profile.ssh_control_path}",
                    "-o",
                    "ControlMaster=no",
                ]
            )
        else:
            ssh_command.extend(["-o", "BatchMode=yes"])
        ssh_command.extend([target, remote_command])
        return self._local_runner(
            ssh_command,
            timeout=timeout_seconds,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def _run_with_paramiko_password(
        self,
        *,
        command: list[str],
        remote_command: str,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        if not self._profile.ssh_password_configured:
            return subprocess.CompletedProcess(
                command,
                255,
                stdout="",
                stderr="SSH password auth mode requires GENEAGENT_HPC_SSH_PASSWORD in the local ignored .env or process environment.",
            )
        if not self._profile.host:
            return subprocess.CompletedProcess(command, 255, stdout="", stderr="Remote SSH host is not configured.")
        paramiko = _load_paramiko()
        if paramiko is None:
            return subprocess.CompletedProcess(
                command,
                255,
                stdout="",
                stderr="Paramiko is required for password_env SSH auth. Install dependency `paramiko>=3.4,<4.0`.",
            )
        client = paramiko.SSHClient()
        strict = self._profile.strict_host_key_checking.strip().lower()
        if strict in {"yes", "true", "strict"}:
            client.set_missing_host_key_policy(paramiko.RejectPolicy())
        else:
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        try:
            client.connect(
                hostname=self._profile.host,
                port=self._profile.port,
                username=self._profile.user,
                password=self._profile.ssh_password.get_secret_value() if self._profile.ssh_password else None,
                timeout=self._profile.connect_timeout_seconds,
                banner_timeout=self._profile.connect_timeout_seconds,
                auth_timeout=self._profile.connect_timeout_seconds,
                look_for_keys=False,
                allow_agent=False,
            )
            stdin_stream, stdout_stream, stderr_stream = client.exec_command(
                remote_command,
                timeout=timeout_seconds,
                get_pty=False,
            )
            try:
                stdout_bytes = stdout_stream.read()
                stderr_bytes = stderr_stream.read()
                returncode = stdout_stream.channel.recv_exit_status()
            finally:
                for stream in (stdin_stream, stdout_stream, stderr_stream):
                    close = getattr(stream, "close", None)
                    if callable(close):
                        close()
            return subprocess.CompletedProcess(
                command,
                returncode,
                stdout=_decode_ssh_bytes(stdout_bytes),
                stderr=_decode_ssh_bytes(stderr_bytes),
            )
        except Exception as error:  # paramiko raises multiple transport/auth/socket subclasses.
            return subprocess.CompletedProcess(
                command,
                255,
                stdout="",
                stderr=_sanitize_ssh_error(error),
            )
        finally:
            client.close()


def _load_paramiko():
    try:
        import paramiko  # type: ignore[import-not-found]
    except ImportError:
        return None
    return paramiko


def _decode_ssh_bytes(payload) -> str:
    if isinstance(payload, str):
        return payload
    return bytes(payload).decode("utf-8", errors="replace")


def _sanitize_ssh_error(error: Exception) -> str:
    text = str(error)
    return text.replace("\r", " ").replace("\n", " ")


class SshControlMasterManager:
    """Open, check, and close an operator-authenticated SSH control socket."""

    def __init__(
        self,
        *,
        profile: RemoteExecutionProfile,
        local_runner: Callable[..., subprocess.CompletedProcess[str]] | None = None,
    ) -> None:
        self.profile = profile
        self._local_runner = local_runner or subprocess.run

    def open_command(self) -> list[str]:
        """Build an SSH master command that lets the operator type a password."""

        target = self._target()
        control_path = self._control_path()
        return [
            self.profile.ssh_binary,
            "-p",
            str(self.profile.port),
            "-o",
            f"ConnectTimeout={self.profile.connect_timeout_seconds}",
            "-o",
            f"StrictHostKeyChecking={self.profile.strict_host_key_checking}",
            "-o",
            "ControlMaster=yes",
            "-o",
            f"ControlPath={control_path}",
            "-o",
            f"ControlPersist={self.profile.ssh_control_persist}",
            "-N",
            "-f",
            target,
        ]

    def check_command(self) -> list[str]:
        """Build an SSH control command that checks whether the master is alive."""

        return self._control_command("check")

    def close_command(self) -> list[str]:
        """Build an SSH control command that closes the master session."""

        return self._control_command("exit")

    def open(self) -> subprocess.CompletedProcess[str]:
        """Open the control socket, inheriting the terminal for password entry."""

        self._ensure_control_dir()
        return self._local_runner(self.open_command(), check=False)

    def check(self) -> subprocess.CompletedProcess[str]:
        """Check the control socket without prompting for a password."""

        return self._local_runner(
            self.check_command(),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def close(self) -> subprocess.CompletedProcess[str]:
        """Close the control socket without prompting for a password."""

        return self._local_runner(
            self.close_command(),
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )

    def _control_command(self, action: str) -> list[str]:
        return [
            self.profile.ssh_binary,
            "-p",
            str(self.profile.port),
            "-o",
            f"ControlPath={self._control_path()}",
            "-O",
            action,
            self._target(),
        ]

    def _ensure_control_dir(self) -> None:
        Path(self._control_path()).expanduser().parent.mkdir(parents=True, exist_ok=True)

    def _control_path(self) -> str:
        if not self.profile.ssh_control_path:
            raise ValueError("SSH control master mode requires ssh_control_path.")
        return self.profile.ssh_control_path

    def _target(self) -> str:
        target = self.profile.ssh_target
        if not target:
            raise ValueError("Remote SSH target is not configured.")
        return target


class RemoteSlurmSchedulerAdapter(SlurmSchedulerAdapter):
    """SLURM adapter that materializes scripts and submits through SSH."""

    def __init__(
        self,
        *,
        profile: RemoteExecutionProfile,
        local_cache_root: str | Path | None = None,
        command_runner=None,
        **kwargs,
    ) -> None:
        self.profile = profile
        self._local_cache_root = Path(local_cache_root or ".geneagent")
        remote_runner = command_runner or SshCommandRunner(profile=profile)
        super().__init__(command_runner=remote_runner, **kwargs)

    def _materialize_submission_files(self, plan: SubmissionPlan) -> None:
        script_payload = base64.b64encode((plan.script_preview + "\n").encode("utf-8")).decode("ascii")
        wrapper_payload = base64.b64encode((plan.wrapper_preview + "\n").encode("utf-8")).decode("ascii")
        work_dir = PurePosixPath(plan.paths.working_directory)
        script_path = PurePosixPath(plan.paths.script_path)
        wrapper_path = PurePosixPath(plan.paths.wrapper_path)
        log_dir = PurePosixPath(plan.paths.stdout_path).parent
        remote_script = "\n".join(
            [
                "set -euo pipefail",
                (
                    f"mkdir -p {shlex.quote(str(work_dir))} {shlex.quote(str(script_path.parent))} "
                    f"{shlex.quote(str(wrapper_path.parent))} {shlex.quote(str(log_dir))}"
                ),
                f"printf %s {shlex.quote(script_payload)} | base64 -d > {shlex.quote(str(script_path))}",
                f"printf %s {shlex.quote(wrapper_payload)} | base64 -d > {shlex.quote(str(wrapper_path))}",
                f"chmod 700 {shlex.quote(str(script_path))} {shlex.quote(str(wrapper_path))}",
            ]
        )
        result = self._run_command(
            command=["bash", "-lc", remote_script],
            cwd=None,
            timeout_seconds=self._command_timeout_seconds,
        )
        if result.returncode != 0:
            raise SchedulerExecutionError(
                "Failed to materialize remote scheduler files.",
                command=["bash", "-lc", "<remote-materialize>"],
                stdout=result.stdout,
                stderr=result.stderr,
                error_code="REMOTE_MATERIALIZE_FAILED",
                retryable=True,
                phase="materialize",
            )

    def _submission_cache_path(self, *, plan: SubmissionPlan) -> Path:
        profile_name = self._safe_job_name(self.profile.profile_name)
        return (
            self._local_cache_root
            / "scheduler"
            / "remote_submissions"
            / profile_name
            / plan.task_id
            / f"{plan.run_id}.json"
        )

    def remote_check(self, *, timeout_seconds: int | None = None) -> RemoteCheckResult:
        """Check SSH, scheduler commands, configured tools, and work root."""

        timeout = timeout_seconds or self._command_timeout_seconds
        messages: list[str] = []
        if not self.profile.host:
            messages.append("missing_hpc_host")
        if not self.profile.user:
            messages.append("missing_hpc_user")
        if messages:
            return RemoteCheckResult(
                profile_name=self.profile.profile_name,
                execution_mode=ExecutionMode.SSH_SLURM_TRUSTED,
                scheduler=SchedulerKind.SLURM,
                ssh_target=self.profile.ssh_target,
                work_root=self.profile.work_root,
                reachable=False,
                safe_for_submit=False,
                command_checks={},
                tool_checks={},
                missing_commands=[],
                messages=messages,
            )

        commands = ["bash", "sinfo", "scontrol", "sbatch", "squeue", "sacct"]
        command_probe = "; ".join(
            [
                "for t in "
                + " ".join(shlex.quote(command) for command in commands)
                + '; do if command -v "$t" >/dev/null 2>&1; then echo "command:$t=ok"; else echo "command:$t=missing"; fi; done',
                f"if test -d {shlex.quote(self.profile.work_root)}; then echo work_root=ok; else echo work_root=missing; fi",
                *[
                    f"if test -x {shlex.quote(path)}; then echo tool:{shlex.quote(name)}=ok; else echo tool:{shlex.quote(name)}=missing; fi"
                    for name, path in self.profile.tool_paths.items()
                ],
            ]
        )
        try:
            result = self._run_command(
                command=["bash", "-lc", command_probe],
                cwd=self.profile.work_root,
                timeout_seconds=timeout,
            )
        except SchedulerExecutionError as error:
            return RemoteCheckResult(
                profile_name=self.profile.profile_name,
                execution_mode=ExecutionMode.SSH_SLURM_TRUSTED,
                scheduler=SchedulerKind.SLURM,
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
        result_messages = list(messages)
        if not reachable:
            result_messages.append("ssh_probe_nonzero")
        if not work_root_ok:
            result_messages.append("work_root_missing")
        result_messages.extend(f"missing_command:{name}" for name in missing_commands)
        return RemoteCheckResult(
            profile_name=self.profile.profile_name,
            execution_mode=ExecutionMode.SSH_SLURM_TRUSTED,
            scheduler=SchedulerKind.SLURM,
            ssh_target=self.profile.ssh_target,
            work_root=self.profile.work_root,
            reachable=reachable,
            safe_for_submit=safe_for_submit,
            command_checks=command_checks,
            tool_checks=tool_checks,
            missing_commands=missing_commands,
            messages=result_messages,
        )


def build_manual_submit_card(
    *,
    plan: SubmissionPlan,
    profile: RemoteExecutionProfile,
) -> ManualSubmitCard:
    """Build a SBASE/web-console copy card from a planned SLURM submission."""

    request = plan.resource_request
    partition = request.partition or profile.default_partition
    sbatch_command = [
        "sbatch",
        "-J",
        request.job_name,
    ]
    if partition:
        sbatch_command.extend(["-p", partition])
    sbatch_command.extend(
        [
            "-c",
            str(request.cpus_per_task),
            f"--mem={request.memory_gb}G",
            f"--time={request.walltime}",
            "-o",
            plan.paths.stdout_path,
            "-e",
            plan.paths.stderr_path,
            "--wrap",
            plan.command_preview,
        ]
    )
    return ManualSubmitCard(
        scheduler="slurm",
        profile_name=profile.profile_name,
        working_directory=plan.paths.working_directory,
        command_text=plan.command_preview,
        partition=partition,
        cpus=request.cpus_per_task,
        memory_gb=request.memory_gb,
        walltime=request.walltime,
        stdout_path=plan.paths.stdout_path,
        stderr_path=plan.paths.stderr_path,
        sbatch_wrap_command=shlex.join(sbatch_command),
        sbase_steps=[
            "Open the HPC workbench web page.",
            "Open the SBASE submission entry.",
            f"Set the working directory to {plan.paths.working_directory}.",
            "Paste the command_text into the command field.",
            "Set partition, CPU, memory, and walltime from this card.",
            "Submit and record the returned job id in the GeneAgent run state.",
        ],
    )
