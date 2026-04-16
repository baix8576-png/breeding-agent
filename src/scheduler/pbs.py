"""PBS compatibility adapter with preview and real execution modes."""

from __future__ import annotations

import re

from contracts.common import JobState, SchedulerKind
from scheduler.base import BaseSchedulerAdapter, SchedulerExecutionError
from scheduler.models import SchedulerPaths, SchedulerResourceRequest


class PbsSchedulerAdapter(BaseSchedulerAdapter):
    """PBS compatibility adapter for planning, submit, and polling."""

    kind = SchedulerKind.PBS

    def _directive_lines(self, request: SchedulerResourceRequest, paths: SchedulerPaths) -> list[str]:
        """Return PBS-specific submission directives."""

        lines = [
            f"#PBS -N {request.job_name}",
            f"#PBS -l select=1:ncpus={request.total_cpus}:mem={request.memory_gb}gb",
            f"#PBS -l walltime={request.walltime}",
            f"#PBS -o {paths.stdout_path}",
            f"#PBS -e {paths.stderr_path}",
        ]
        if request.partition:
            lines.append(f"#PBS -q {request.partition}")
        if request.account:
            lines.append(f"#PBS -A {request.account}")
        return lines

    def _submit_command(self, script_path: str) -> list[str]:
        """Return the preview submission command for PBS."""

        return ["qsub", script_path]

    def _poll_command_hint(self, job_id: str) -> str:
        """Return the PBS polling command hint."""

        return f"qstat -f {job_id}"

    def _parse_submit_output(self, *, stdout: str, stderr: str, returncode: int) -> str:
        """Extract PBS job id from qsub output."""

        _ = returncode
        combined = "\n".join(
            part.strip()
            for part in (stdout, stderr)
            if part and part.strip()
        ).strip()
        if not combined:
            raise SchedulerExecutionError("qsub returned no output; cannot parse job id.")

        primary_match = re.search(r"\b([0-9]+(?:\.[A-Za-z0-9_.-]+)?)\b", combined)
        if primary_match:
            return primary_match.group(1)

        fallback_match = re.search(r"\b([A-Za-z0-9_.-]+)\b", combined)
        if fallback_match:
            return fallback_match.group(1)

        raise SchedulerExecutionError(
            "Unable to parse PBS job id from qsub output.",
            stdout=stdout,
            stderr=stderr,
        )

    def _poll_real(self, job_id: str) -> JobState:
        """Poll a real PBS job using qstat -f with -xf fallback."""

        qstat_commands = [
            ["qstat", "-f", job_id],
            ["qstat", "-xf", job_id],
        ]
        last_result = None
        for command in qstat_commands:
            result = self._run_command(
                command=command,
                cwd=None,
                timeout_seconds=self._command_timeout_seconds,
            )
            last_result = result
            if result.returncode != 0:
                if self._is_unknown_job_error(result.stderr):
                    continue
                raise SchedulerExecutionError(
                    "Unable to poll PBS state.",
                    command=command,
                    stdout=result.stdout,
                    stderr=result.stderr,
                )
            job_state = self._parse_qstat_job_state(result.stdout)
            if job_state:
                return self._state_from_pbs_token(job_state, result.stdout)

        if last_result and self._is_unknown_job_error(last_result.stderr):
            return JobState.UNKNOWN
        raise SchedulerExecutionError(
            "Unable to derive PBS job state from qstat output.",
            stdout=last_result.stdout if last_result else "",
            stderr=last_result.stderr if last_result else "",
        )

    def compatibility_notes(self) -> list[str]:
        """Describe the current PBS compatibility boundaries."""

        return [
            "The PBS layer is a compatibility bridge and collapses the request into a single select chunk.",
            "Node and task topology are not modeled explicitly; total CPU count is rendered into one select specification.",
            "No PBS array jobs, placement rules, or site-specific resource selectors are emitted in the current planning layer.",
            "Real submit mode executes qsub with retry/backoff and parses the returned job id.",
            "Real poll mode queries qstat -f and falls back to qstat -xf for finished jobs.",
        ]

    def _parse_qstat_job_state(self, output: str) -> str | None:
        match = re.search(r"job_state\s*=\s*([A-Za-z])", output)
        if match:
            return match.group(1).upper()
        return None

    def _parse_exit_status(self, output: str) -> int | None:
        match = re.search(r"(?:Exit_status|exit_status)\s*=\s*(-?\d+)", output)
        if not match:
            return None
        try:
            return int(match.group(1))
        except ValueError:
            return None

    def _state_from_pbs_token(self, token: str, output: str) -> JobState:
        normalized = token.strip().upper()
        if normalized in {"Q", "H", "W"}:
            return JobState.QUEUED
        if normalized in {"R", "E", "B", "S", "T"}:
            return JobState.RUNNING
        if normalized in {"F", "C"}:
            exit_status = self._parse_exit_status(output)
            if exit_status is None or exit_status == 0:
                return JobState.COMPLETED
            return JobState.FAILED
        return JobState.UNKNOWN

    def _is_unknown_job_error(self, stderr: str) -> bool:
        lowered = stderr.lower()
        return "unknown job id" in lowered or "unknown job_id" in lowered
