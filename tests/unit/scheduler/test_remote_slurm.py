from __future__ import annotations

import subprocess
from types import SimpleNamespace
from pathlib import Path

import pytest
from pydantic import SecretStr

from contracts.common import SshAuthMode
from contracts.remote_execution import RemoteExecutionProfile
from contracts.tasks import ResourceEstimate
from scheduler.base import SchedulerExecutionError
from scheduler.remote import (
    RemoteSlurmSchedulerAdapter,
    SshCommandRunner,
    SshControlMasterManager,
    build_manual_submit_card,
)
from scheduler.ssh_shell import RemoteShellSchedulerAdapter


class RecordingLocalRunner:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []

    def __call__(self, command: list[str], **kwargs) -> subprocess.CompletedProcess[str]:
        _ = kwargs
        self.calls.append(command)
        return subprocess.CompletedProcess(command, 0, stdout="ok\n", stderr="")


class RecordingRemoteRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str | None, int]] = []

    def __call__(
        self,
        command: list[str],
        cwd: str | None,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append((command, cwd, timeout_seconds))
        if command and command[0] == "sbatch":
            return subprocess.CompletedProcess(command, 0, stdout="Submitted batch job 12345\n", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


class MissingWorkdirRemoteRunner:
    def __init__(self) -> None:
        self.calls: list[tuple[list[str], str | None, int]] = []
        self.workdir_created = False

    def __call__(
        self,
        command: list[str],
        cwd: str | None,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append((command, cwd, timeout_seconds))
        joined = " ".join(command)
        if cwd is None and "mkdir -p /cluster/work/alice/geneagent/new_run" in joined:
            self.workdir_created = True
        if cwd == "/cluster/work/alice/geneagent/new_run" and not self.workdir_created:
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="cd: no such file or directory")
        if command and command[0] == "sbatch":
            return subprocess.CompletedProcess(command, 0, stdout="Submitted batch job 12345\n", stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


def test_remote_execution_profile_rejects_secret_fields() -> None:
    with pytest.raises(ValueError):
        RemoteExecutionProfile.model_validate(
            {
                "profile_name": "prod",
                "host": "hpc.example.org",
                "user": "alice",
                "password": "never-store-this",
            }
        )


def test_remote_execution_profile_masks_explicit_password_auth_secret() -> None:
    profile = RemoteExecutionProfile(
        profile_name="server",
        host="server.example.org",
        user="alice",
        work_root="/data2/alice/geneagent_runs",
        ssh_auth_mode=SshAuthMode.PASSWORD_ENV,
        ssh_password=SecretStr("do-not-print"),
    )

    dumped = profile.model_dump()
    rendered = repr(profile)

    assert profile.ssh_password_configured is True
    assert "ssh_password" not in dumped
    assert "do-not-print" not in rendered


def test_ssh_command_runner_uses_batchmode_without_credentials() -> None:
    local_runner = RecordingLocalRunner()
    profile = RemoteExecutionProfile(
        profile_name="prod",
        host="hpc.example.org",
        user="alice",
        port=2222,
        work_root="/cluster/work/alice/geneagent",
    )
    runner = SshCommandRunner(profile=profile, local_runner=local_runner)

    result = runner(["sbatch", "/cluster/work/alice/geneagent/job.sbatch.sh"], "/cluster/work/alice/geneagent", 20)

    assert result.returncode == 0
    assert len(local_runner.calls) == 1
    ssh_command = local_runner.calls[0]
    joined = " ".join(ssh_command)
    assert ssh_command[0] == "ssh"
    assert "BatchMode=yes" in joined
    assert "ConnectTimeout=15" in joined
    assert "-p 2222" in joined
    assert "alice@hpc.example.org" in joined
    assert "cd /cluster/work/alice/geneagent" in joined
    assert "password" not in joined.lower()
    assert "private" not in joined.lower()


def test_ssh_command_runner_password_env_uses_paramiko_without_leaking_secret(monkeypatch) -> None:
    calls: list[dict[str, object]] = []

    class FakeChannel:
        def recv_exit_status(self) -> int:
            return 0

    class FakeStream:
        def __init__(self, text: str = "", name: str = "stream") -> None:
            self._text = text
            self._name = name
            self.channel = FakeChannel()

        def read(self) -> bytes:
            return self._text.encode("utf-8")

        def close(self) -> None:
            calls.append({"closed_stream": self._name})

    class FakeClient:
        def set_missing_host_key_policy(self, policy) -> None:
            _ = policy

        def connect(self, **kwargs) -> None:
            calls.append(kwargs)

        def exec_command(self, command: str, timeout: int, get_pty: bool):
            calls.append({"command": command, "timeout": timeout, "get_pty": get_pty})
            return (FakeStream(name="stdin"), FakeStream("ok\n", name="stdout"), FakeStream("", name="stderr"))

        def close(self) -> None:
            calls.append({"closed": True})

    fake_paramiko = SimpleNamespace(
        SSHClient=FakeClient,
        AutoAddPolicy=lambda: object(),
        RejectPolicy=lambda: object(),
        SSHException=Exception,
        AuthenticationException=Exception,
    )
    monkeypatch.setattr("scheduler.remote._load_paramiko", lambda: fake_paramiko)
    profile = RemoteExecutionProfile(
        profile_name="server",
        host="server.example.org",
        user="alice",
        work_root="/data2/alice/geneagent_runs",
        ssh_auth_mode=SshAuthMode.PASSWORD_ENV,
        ssh_password=SecretStr("top-secret"),
    )
    runner = SshCommandRunner(profile=profile)

    result = runner(["hostname"], "/data2/alice/geneagent_runs", 20)

    assert result.returncode == 0
    assert result.stdout == "ok\n"
    assert calls[0]["hostname"] == "server.example.org"
    assert calls[0]["username"] == "alice"
    assert calls[0]["password"] == "top-secret"
    assert "top-secret" not in " ".join(result.args)
    assert "top-secret" not in result.stdout
    assert "top-secret" not in result.stderr
    assert {"closed_stream": "stdin"} in calls
    assert {"closed_stream": "stdout"} in calls
    assert {"closed_stream": "stderr"} in calls


def test_ssh_command_runner_uses_control_master_socket_without_credentials() -> None:
    local_runner = RecordingLocalRunner()
    profile = RemoteExecutionProfile(
        profile_name="server",
        host="server.example.org",
        user="alice",
        work_root="/data2/alice/geneagent_runs",
        ssh_auth_mode=SshAuthMode.CONTROL_MASTER,
        ssh_control_path=".geneagent/ssh_control/server.sock",
    )
    runner = SshCommandRunner(profile=profile, local_runner=local_runner)

    result = runner(["hostname"], "/data2/alice/geneagent_runs", 20)

    assert result.returncode == 0
    ssh_command = local_runner.calls[0]
    joined = " ".join(ssh_command)
    assert "ControlPath=.geneagent/ssh_control/server.sock" in joined
    assert "BatchMode=yes" in joined
    assert "server.example.org" in joined
    assert "password" not in joined.lower()
    assert "private" not in joined.lower()


def test_control_master_open_command_allows_operator_password_prompt_without_storing_secret() -> None:
    profile = RemoteExecutionProfile(
        profile_name="server",
        host="server.example.org",
        user="alice",
        work_root="/data2/alice/geneagent_runs",
        ssh_auth_mode=SshAuthMode.CONTROL_MASTER,
        ssh_control_path=".geneagent/ssh_control/server.sock",
        ssh_control_persist="2h",
    )
    manager = SshControlMasterManager(profile=profile)

    command = manager.open_command()
    joined = " ".join(command)

    assert command[0] == "ssh"
    assert "ControlMaster=yes" in joined
    assert "ControlPath=.geneagent/ssh_control/server.sock" in joined
    assert "ControlPersist=2h" in joined
    assert "BatchMode=yes" not in joined
    assert "alice@server.example.org" in joined
    assert "password" not in joined.lower()
    assert "private" not in joined.lower()


def test_remote_slurm_submit_materializes_remote_files_and_keeps_local_cache(tmp_path: Path) -> None:
    remote_runner = RecordingRemoteRunner()
    profile = RemoteExecutionProfile(
        profile_name="prod",
        host="hpc.example.org",
        user="alice",
        work_root="/cluster/work/alice/geneagent",
    )
    adapter = RemoteSlurmSchedulerAdapter(
        profile=profile,
        local_cache_root=tmp_path / ".geneagent",
        real_execution_enabled=True,
        retry_backoff_seconds=[0],
        command_runner=remote_runner,
    )

    handle = adapter.submit(
        working_directory="/cluster/work/alice/geneagent/run1",
        resources=ResourceEstimate(cpus=2, memory_gb=8, walltime="01:00:00"),
        command=["echo", "ok"],
        task_id="task-remote-001",
        run_id="run-remote-001",
    )

    assert handle.job_id == "12345"
    assert handle.state.value == "queued"
    assert any(call[0][0] == "bash" and "base64 -d" in " ".join(call[0]) for call in remote_runner.calls)
    assert any(call[0][0] == "sbatch" for call in remote_runner.calls)
    plan = adapter.build_submission_plan(
        command=["echo", "ok"],
        working_directory="/cluster/work/alice/geneagent/run1",
        resources=ResourceEstimate(cpus=2, memory_gb=8, walltime="01:00:00"),
        mode="submit",
        task_id="task-remote-001",
        run_id="run-remote-001",
    )
    cache_path = adapter._submission_cache_path(plan=plan)
    assert str(cache_path).startswith(str(tmp_path))
    assert "/cluster/work" not in str(cache_path).replace("\\", "/")


def test_remote_slurm_materialize_creates_missing_workdir_before_sbatch(tmp_path: Path) -> None:
    remote_runner = MissingWorkdirRemoteRunner()
    profile = RemoteExecutionProfile(
        profile_name="prod",
        host="hpc.example.org",
        user="alice",
        work_root="/cluster/work/alice/geneagent",
    )
    adapter = RemoteSlurmSchedulerAdapter(
        profile=profile,
        local_cache_root=tmp_path / ".geneagent",
        real_execution_enabled=True,
        retry_backoff_seconds=[0],
        command_runner=remote_runner,
    )

    handle = adapter.submit(
        working_directory="/cluster/work/alice/geneagent/new_run",
        resources=ResourceEstimate(cpus=2, memory_gb=8, walltime="01:00:00"),
        command=["echo", "ok"],
        task_id="task-remote-missing-workdir-001",
        run_id="run-remote-missing-workdir-001",
    )

    materialize_call = remote_runner.calls[0]
    materialize_command = " ".join(materialize_call[0])
    assert handle.job_id == "12345"
    assert materialize_call[1] is None
    assert "mkdir -p /cluster/work/alice/geneagent/new_run" in materialize_command
    assert remote_runner.calls[-1][0][0] == "sbatch"
    assert remote_runner.calls[-1][1] == "/cluster/work/alice/geneagent/new_run"


def test_remote_check_uses_connect_timeout_override() -> None:
    remote_runner = RecordingRemoteRunner()
    profile = RemoteExecutionProfile(
        profile_name="prod",
        host="hpc.example.org",
        user="alice",
        work_root="/cluster/work/alice/geneagent",
    )
    adapter = RemoteSlurmSchedulerAdapter(
        profile=profile,
        command_timeout_seconds=60,
        command_runner=remote_runner,
    )

    adapter.remote_check(timeout_seconds=7)

    assert remote_runner.calls
    assert remote_runner.calls[0][2] == 7


def test_manual_sbase_card_contains_copyable_submit_fields() -> None:
    profile = RemoteExecutionProfile(
        profile_name="manual",
        host="hpc.example.org",
        user="alice",
        work_root="/cluster/work/alice/geneagent",
        default_partition="x86-shared",
    )
    adapter = RemoteSlurmSchedulerAdapter(profile=profile, real_execution_enabled=False)
    plan = adapter.build_submission_plan(
        command=["/opt/miniconda/envs/common/bin/plink", "--help"],
        working_directory="/cluster/work/alice/geneagent/manual",
        resources=ResourceEstimate(cpus=2, memory_gb=5, walltime="01:00:00", partition="x86-shared"),
        mode="submit-preview",
        task_id="task-sbase-001",
        run_id="run-sbase-001",
    )

    card = build_manual_submit_card(plan=plan, profile=profile)

    assert card.scheduler == "slurm"
    assert card.working_directory == "/cluster/work/alice/geneagent/manual"
    assert card.partition == "x86-shared"
    assert card.cpus == plan.resource_request.cpus_per_task
    assert card.memory_gb == plan.resource_request.memory_gb
    assert card.walltime == plan.resource_request.walltime
    assert "sbatch" in card.sbatch_wrap_command
    assert "--wrap" in card.sbatch_wrap_command
    assert "plink --help" in card.sbatch_wrap_command
    assert len(card.sbase_steps) >= 5


class ShellRemoteRunner:
    def __init__(self, poll_stdout: str = "running\n") -> None:
        self.poll_stdout = poll_stdout
        self.calls: list[tuple[list[str], str | None, int]] = []

    def __call__(
        self,
        command: list[str],
        cwd: str | None,
        timeout_seconds: int,
    ) -> subprocess.CompletedProcess[str]:
        self.calls.append((command, cwd, timeout_seconds))
        joined = " ".join(command)
        if "command:" in joined:
            stdout = "\n".join(
                [
                    "command:bash=ok",
                    "command:nohup=ok",
                    "command:ps=ok",
                    "command:kill=ok",
                    "command:mkdir=ok",
                    "command:chmod=ok",
                    "command:test=ok",
                    "command:cat=ok",
                    "command:base64=ok",
                    "work_root=ok",
                ]
            )
            return subprocess.CompletedProcess(command, 0, stdout=f"{stdout}\n", stderr="")
        if "nohup" in joined:
            return subprocess.CompletedProcess(command, 0, stdout="4242\n", stderr="")
        if "if test -f" in joined and "state/done" in joined:
            return subprocess.CompletedProcess(command, 0, stdout=self.poll_stdout, stderr="")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")


def test_remote_shell_check_does_not_require_slurm_commands() -> None:
    remote_runner = ShellRemoteRunner()
    profile = RemoteExecutionProfile(
        profile_name="server",
        host="server.example.org",
        user="alice",
        work_root="/data2/alice/geneagent_runs",
    )
    adapter = RemoteShellSchedulerAdapter(profile=profile, command_runner=remote_runner)

    result = adapter.remote_check(timeout_seconds=6)

    assert result.execution_mode.value == "ssh_shell_trusted"
    assert result.scheduler.value == "shell"
    assert result.safe_for_submit is True
    assert result.command_checks["bash"] is True
    assert result.command_checks["base64"] is True
    assert "sbatch" not in result.command_checks
    assert result.missing_commands == []
    assert remote_runner.calls[0][2] == 6
    assert "base64" in " ".join(remote_runner.calls[0][0])


def test_remote_shell_submit_creates_run_directory_and_returns_pid_handle(tmp_path: Path) -> None:
    remote_runner = ShellRemoteRunner()
    profile = RemoteExecutionProfile(
        profile_name="server",
        host="server.example.org",
        user="alice",
        work_root="/data2/alice/geneagent_runs",
    )
    adapter = RemoteShellSchedulerAdapter(
        profile=profile,
        local_cache_root=tmp_path / ".geneagent",
        real_execution_enabled=True,
        retry_backoff_seconds=[0],
        command_runner=remote_runner,
    )
    preview_plan = adapter.build_submission_plan(
        command=["bash", "-lc", "hostname && date && sleep 5"],
        working_directory="/data2/alice/geneagent_runs",
        resources=ResourceEstimate(cpus=2, memory_gb=8, walltime="01:00:00"),
        mode="submit",
        task_id="task-shell-001",
        run_id="run-shell-001",
    )

    handle = adapter.submit(
        working_directory="/data2/alice/geneagent_runs",
        resources=ResourceEstimate(cpus=2, memory_gb=8, walltime="01:00:00"),
        command=["bash", "-lc", "hostname && date && sleep 5"],
        task_id="task-shell-001",
        run_id="run-shell-001",
    )

    joined_calls = "\n".join(" ".join(call[0]) for call in remote_runner.calls)
    assert handle.job_id == "shell:4242"
    assert handle.state.value == "running"
    assert "/data2/alice/geneagent_runs/task-shell-001/run-shell-001" in joined_calls
    assert "run.sh" in joined_calls
    assert "logs/stdout.log" in joined_calls
    assert "state/pid" in joined_calls
    assert preview_plan.script_preview.startswith("#!/usr/bin/env bash")
    assert "nohup" in joined_calls
    assert "rm -f" not in joined_calls
    assert "existing_state_file" in joined_calls
    cache_plan = adapter.build_submission_plan(
        command=["bash", "-lc", "hostname && date && sleep 5"],
        working_directory="/data2/alice/geneagent_runs",
        resources=ResourceEstimate(cpus=2, memory_gb=8, walltime="01:00:00"),
        mode="submit",
        task_id="task-shell-001",
        run_id="run-shell-001",
    )
    cache_path = adapter._submission_cache_path(plan=cache_plan)
    assert str(cache_path).startswith(str(tmp_path))
    assert "/data2/alice" not in str(cache_path).replace("\\", "/")


def test_remote_shell_submit_command_uses_valid_background_separator() -> None:
    profile = RemoteExecutionProfile(
        profile_name="server",
        host="server.example.org",
        user="alice",
        work_root="/data2/alice/geneagent_runs",
    )
    adapter = RemoteShellSchedulerAdapter(profile=profile)

    plan = adapter.build_submission_plan(
        command=["bash", "-lc", "hostname && date && sleep 5"],
        working_directory="/data2/alice/geneagent_runs",
        resources=ResourceEstimate(cpus=2, memory_gb=8, walltime="01:00:00"),
        mode="submit",
        task_id="task-shell-separator-001",
        run_id="run-shell-separator-001",
    )

    launch = plan.submit_command[2]
    assert " &;" not in launch
    assert " >/dev/null 2>&1 & pid=$!" in launch


def test_remote_shell_blocks_plan_when_server_resource_caps_are_exceeded() -> None:
    profile = RemoteExecutionProfile(
        profile_name="server",
        host="server.example.org",
        user="alice",
        work_root="/data2/alice/geneagent_runs",
    )
    adapter = RemoteShellSchedulerAdapter(
        profile=profile,
        remote_cpu_cap=4,
        remote_memory_gb_cap=16,
        remote_walltime_cap="02:00:00",
        remote_max_concurrent_runs=1,
    )

    plan = adapter.build_submission_plan(
        command=["bash", "-lc", "echo too-big"],
        working_directory="/data2/alice/geneagent_runs",
        resources=ResourceEstimate(cpus=8, memory_gb=32, walltime="03:00:00"),
        mode="submit",
        task_id="task-shell-cap-001",
        run_id="run-shell-cap-001",
    )

    assert plan.ready_for_gate == "quota_blocked"
    assert plan.quota_gate_status == "blocked"
    assert "shell_cpu_cap_exceeded(requested=8,limit=4)" in plan.quota_gate_reasons
    assert "shell_memory_cap_exceeded(requested=32,limit=16)" in plan.quota_gate_reasons
    assert "shell_walltime_cap_exceeded(requested=04:00:00,limit=02:00:00)" in plan.quota_gate_reasons


def test_remote_shell_real_submit_does_not_touch_remote_when_resource_guard_blocks(tmp_path: Path) -> None:
    remote_runner = ShellRemoteRunner()
    profile = RemoteExecutionProfile(
        profile_name="server",
        host="server.example.org",
        user="alice",
        work_root="/data2/alice/geneagent_runs",
    )
    adapter = RemoteShellSchedulerAdapter(
        profile=profile,
        local_cache_root=tmp_path / ".geneagent",
        real_execution_enabled=True,
        remote_cpu_cap=2,
        remote_memory_gb_cap=4,
        remote_walltime_cap="00:30:00",
        retry_backoff_seconds=[0],
        command_runner=remote_runner,
    )

    with pytest.raises(SchedulerExecutionError) as raised:
        adapter.submit(
            working_directory="/data2/alice/geneagent_runs",
            resources=ResourceEstimate(cpus=8, memory_gb=32, walltime="03:00:00"),
            command=["bash", "-lc", "echo blocked"],
            task_id="task-shell-guard-001",
            run_id="run-shell-guard-001",
        )

    assert raised.value.error_code == "REMOTE_SHELL_RESOURCE_GUARD_BLOCKED"
    assert raised.value.retryable is False
    assert remote_runner.calls == []


def test_remote_shell_script_exports_thread_limits_and_ulimits() -> None:
    profile = RemoteExecutionProfile(
        profile_name="server",
        host="server.example.org",
        user="alice",
        work_root="/data2/alice/geneagent_runs",
    )
    adapter = RemoteShellSchedulerAdapter(
        profile=profile,
        remote_cpu_cap=4,
        remote_memory_gb_cap=16,
        remote_walltime_cap="04:00:00",
    )

    plan = adapter.build_submission_plan(
        command=["bash", "-lc", "echo safe"],
        working_directory="/data2/alice/geneagent_runs",
        resources=ResourceEstimate(cpus=2, memory_gb=8, walltime="01:00:00"),
        task_id="task-shell-limits-001",
        run_id="run-shell-limits-001",
    )

    assert "export OMP_NUM_THREADS=4" in plan.script_preview
    assert "export OPENBLAS_NUM_THREADS=4" in plan.script_preview
    assert "export MKL_NUM_THREADS=4" in plan.script_preview
    assert "ulimit -t 14400" in plan.script_preview
    assert "ulimit -v 16777216" in plan.script_preview


def test_remote_shell_requires_work_root_inside_allowed_write_roots() -> None:
    profile = RemoteExecutionProfile(
        profile_name="server",
        host="server.example.org",
        user="alice",
        work_root="/data2/bob/geneagent_runs",
        allowed_write_roots=["/data2/alice"],
    )
    adapter = RemoteShellSchedulerAdapter(profile=profile)

    with pytest.raises(ValueError, match="allowed_write_roots"):
        adapter.build_submission_plan(
            command=["echo", "nope"],
            working_directory="/data2/bob/geneagent_runs",
            resources=ResourceEstimate(cpus=1, memory_gb=2, walltime="00:10:00"),
            task_id="task-shell-root-001",
            run_id="run-shell-root-001",
        )


@pytest.mark.parametrize(
    ("stdout", "expected"),
    [
        ("completed:0\n", "completed"),
        ("failed:2\n", "failed"),
        ("running\n", "running"),
        ("unknown\n", "unknown"),
    ],
)
def test_remote_shell_poll_maps_state_files(stdout: str, expected: str) -> None:
    remote_runner = ShellRemoteRunner(poll_stdout=stdout)
    profile = RemoteExecutionProfile(
        profile_name="server",
        host="server.example.org",
        user="alice",
        work_root="/data2/alice/geneagent_runs",
    )
    adapter = RemoteShellSchedulerAdapter(
        profile=profile,
        real_execution_enabled=True,
        command_runner=remote_runner,
    )

    state = adapter.poll("shell:4242")

    assert state.value == expected


@pytest.mark.parametrize(
    "bad_working_directory",
    [
        "../outside",
        "/data2/alice/other",
        "D:\\geneagent",
    ],
)
def test_remote_shell_rejects_paths_outside_remote_work_root(bad_working_directory: str) -> None:
    profile = RemoteExecutionProfile(
        profile_name="server",
        host="server.example.org",
        user="alice",
        work_root="/data2/alice/geneagent_runs",
    )
    adapter = RemoteShellSchedulerAdapter(
        profile=profile,
        real_execution_enabled=True,
        command_runner=ShellRemoteRunner(),
    )

    with pytest.raises(ValueError):
        adapter.submit(
            working_directory=bad_working_directory,
            resources=ResourceEstimate(cpus=1, memory_gb=2, walltime="00:10:00"),
            command=["echo", "nope"],
            task_id="task-shell-bad",
            run_id="run-shell-bad",
        )
