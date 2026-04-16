"""SLURM-first scheduler adapter with preview and real execution modes."""

from __future__ import annotations

import re

from contracts.common import JobState, SchedulerKind
from scheduler.base import BaseSchedulerAdapter, SchedulerExecutionError
from scheduler.models import SchedulerPaths, SchedulerResourceRequest


class SlurmSchedulerAdapter(BaseSchedulerAdapter):
    """SLURM-first scheduler adapter for planning, submit, and polling."""

    kind = SchedulerKind.SLURM

    def _directive_lines(self, request: SchedulerResourceRequest, paths: SchedulerPaths) -> list[str]:
        """Return SLURM-specific submission directives."""

        lines = [
            f"#SBATCH --job-name={request.job_name}",
            f"#SBATCH --nodes={request.nodes}",
            f"#SBATCH --ntasks={request.tasks}",
            f"#SBATCH --cpus-per-task={request.cpus_per_task}",
            f"#SBATCH --mem={request.memory_gb}G",
            f"#SBATCH --time={request.walltime}",
            f"#SBATCH --output={paths.stdout_path}",
            f"#SBATCH --error={paths.stderr_path}",
        ]
        if request.partition:
            lines.append(f"#SBATCH --partition={request.partition}")
        if request.account:
            lines.append(f"#SBATCH --account={request.account}")
        if request.qos:
            lines.append(f"#SBATCH --qos={request.qos}")
        return lines

    def _submit_command(self, script_path: str) -> list[str]:
        """Return the preview submission command for SLURM."""

        return ["sbatch", script_path]

    def _poll_command_hint(self, job_id: str) -> str:
        """Return the SLURM polling command hint."""

        return f"squeue -j {job_id} -o '%i %t %M %D %R'"

    def _parse_submit_output(self, *, stdout: str, stderr: str, returncode: int) -> str:
        """Extract SLURM job id from sbatch output."""

        _ = returncode
        combined = "\n".join(
            part.strip()
            for part in (stdout, stderr)
            if part and part.strip()
        ).strip()
        if not combined:
            raise SchedulerExecutionError("sbatch returned no output; cannot parse job id.")

        primary_match = re.search(r"submitted\s+batch\s+job\s+([A-Za-z0-9_.-]+)", combined, flags=re.IGNORECASE)
        if primary_match:
            return primary_match.group(1)

        fallback_match = re.search(r"\b([0-9]+(?:_[0-9]+)?)\b", combined)
        if fallback_match:
            return fallback_match.group(1)

        raise SchedulerExecutionError(
            "Unable to parse SLURM job id from sbatch output.",
            stdout=stdout,
            stderr=stderr,
        )

    def _poll_real(self, job_id: str) -> JobState:
        """Poll a real SLURM job using squeue, then fallback to sacct."""

        squeue = self._run_command(
            command=["squeue", "-h", "-j", job_id, "-o", "%T"],
            cwd=None,
            timeout_seconds=self._command_timeout_seconds,
        )
        if squeue.returncode == 0:
            state_token = self._first_state_line(squeue.stdout)
            if state_token:
                return self._state_from_slurm_token(state_token)

        sacct = self._run_command(
            command=["sacct", "-n", "-X", "-j", job_id, "--format=State"],
            cwd=None,
            timeout_seconds=self._command_timeout_seconds,
        )
        if sacct.returncode != 0:
            raise SchedulerExecutionError(
                "Unable to poll SLURM state via squeue/sacct.",
                command=["sacct", "-n", "-X", "-j", job_id, "--format=State"],
                stdout=sacct.stdout,
                stderr=sacct.stderr,
            )
        state_token = self._first_state_line(sacct.stdout)
        if not state_token:
            return JobState.UNKNOWN
        return self._state_from_slurm_token(state_token)

    def compatibility_notes(self) -> list[str]:
        """Describe the current SLURM compatibility boundaries."""

        return [
            "The adapter targets single-job submission scripts and does not yet model job arrays or dependencies.",
            "Memory is rendered as total job memory via --mem, not per-CPU memory via --mem-per-cpu.",
            "No GPU, TRES, reservation, license, or advanced sbatch flags are emitted in the current planning layer.",
            "Real submit mode executes sbatch with retry/backoff and parses the returned job id.",
            "Real poll mode checks squeue first, then falls back to sacct when queue output is empty.",
        ]

    def _first_state_line(self, output: str) -> str | None:
        for line in output.splitlines():
            stripped = line.strip()
            if stripped:
                return stripped.split()[0]
        return None

    def _state_from_slurm_token(self, token: str) -> JobState:
        normalized = self._normalize_state_token(token)
        if normalized in {"PENDING", "CONFIGURING"}:
            return JobState.QUEUED
        if normalized in {"RUNNING", "COMPLETING", "STAGE_OUT"}:
            return JobState.RUNNING
        if normalized in {"COMPLETED"}:
            return JobState.COMPLETED
        if normalized in {
            "FAILED",
            "CANCELLED",
            "BOOT_FAIL",
            "DEADLINE",
            "NODE_FAIL",
            "OUT_OF_MEMORY",
            "PREEMPTED",
            "TIMEOUT",
            "REVOKED",
        }:
            return JobState.FAILED
        return JobState.UNKNOWN

    def _normalize_state_token(self, token: str) -> str:
        cleaned = token.strip().upper().replace("-", "_")
        cleaned = re.split(r"[+( ]", cleaned, maxsplit=1)[0]
        return cleaned
