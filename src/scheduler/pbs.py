"""PBS compatibility adapter with preview and real execution modes."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import re
import subprocess

from contracts.common import JobState, SchedulerKind
from scheduler.base import BaseSchedulerAdapter, SchedulerExecutionError
from scheduler.models import SchedulerPaths, SchedulerResourceRequest


class _PbsErrorCode(str, Enum):
    COMMAND_NOT_FOUND = "COMMAND_NOT_FOUND"
    SUBMIT_FAILED = "SUBMIT_FAILED"
    SUBMIT_TRANSPORT_ERROR = "SUBMIT_TRANSPORT_ERROR"
    SUBMIT_PERMISSION_DENIED = "SUBMIT_PERMISSION_DENIED"
    SUBMIT_INVALID_REQUEST = "SUBMIT_INVALID_REQUEST"
    SUBMIT_POLICY_REJECTED = "SUBMIT_POLICY_REJECTED"
    SUBMIT_PARSE_JOB_ID_FAILED = "SUBMIT_PARSE_JOB_ID_FAILED"
    POLL_FAILED = "POLL_FAILED"
    POLL_TRANSPORT_ERROR = "POLL_TRANSPORT_ERROR"
    POLL_PERMISSION_DENIED = "POLL_PERMISSION_DENIED"
    POLL_PARSE_STATE_FAILED = "POLL_PARSE_STATE_FAILED"
    PBS_UNKNOWN_JOB = "PBS_UNKNOWN_JOB"


@dataclass(slots=True)
class _PbsErrorClass:
    code: _PbsErrorCode
    message: str
    retryable: bool


class PbsSchedulerAdapter(BaseSchedulerAdapter):
    """PBS compatibility adapter for planning, submit, and polling."""

    kind = SchedulerKind.PBS

    _QSUB_JOB_ID_PATTERN = re.compile(
        r"^\s*([0-9]+(?:\[[0-9,\-:]+\])?(?:\.[A-Za-z0-9_.-]+)?)\s*$"
    )

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
            raise SchedulerExecutionError(
                "qsub returned no output; cannot parse job id.",
                stdout=stdout,
                stderr=stderr,
                error_code=_PbsErrorCode.SUBMIT_PARSE_JOB_ID_FAILED.value,
                retryable=False,
                phase="submit",
            )

        job_id = self._extract_job_id_from_qsub_output(combined)
        if job_id:
            return job_id

        classification = _PbsErrorClass(
            code=_PbsErrorCode.SUBMIT_PARSE_JOB_ID_FAILED,
            message="Unable to parse PBS job id from qsub output.",
            retryable=False,
        )

        raise SchedulerExecutionError(
            classification.message,
            stdout=stdout,
            stderr=stderr,
            error_code=classification.code.value,
            retryable=classification.retryable,
            phase="submit",
        )

    def _poll_real(self, job_id: str) -> JobState:
        """Poll a real PBS job using qstat -f with -xf fallback."""

        qstat_commands = [
            ["qstat", "-f", job_id],
            ["qstat", "-xf", job_id],
        ]
        last_result: subprocess.CompletedProcess[str] | None = None
        seen_unknown_job = False
        for command in qstat_commands:
            result = self._run_qstat_with_retry(
                command=command,
            )
            last_result = result
            if result.returncode != 0:
                if self._is_unknown_job_error(stdout=result.stdout, stderr=result.stderr):
                    seen_unknown_job = True
                    continue
                classification = self._classify_poll_failure(
                    stdout=result.stdout,
                    stderr=result.stderr,
                    returncode=result.returncode,
                )
                raise SchedulerExecutionError(
                    classification.message,
                    command=command,
                    stdout=result.stdout,
                    stderr=result.stderr,
                    error_code=classification.code.value,
                    retryable=classification.retryable,
                    phase="poll",
                )
            job_state = self._parse_qstat_job_state(result.stdout)
            if job_state:
                return self._state_from_pbs_token(job_state, result.stdout)
            classification = _PbsErrorClass(
                code=_PbsErrorCode.POLL_PARSE_STATE_FAILED,
                message="Unable to parse PBS job_state from qstat output.",
                retryable=False,
            )
            raise SchedulerExecutionError(
                classification.message,
                command=command,
                stdout=result.stdout,
                stderr=result.stderr,
                error_code=classification.code.value,
                retryable=classification.retryable,
                phase="poll",
            )

        if seen_unknown_job or (
            last_result
            and self._is_unknown_job_error(stdout=last_result.stdout, stderr=last_result.stderr)
        ):
            return JobState.UNKNOWN
        raise SchedulerExecutionError(
            "Unable to derive PBS job state from qstat output.",
            stdout=last_result.stdout if last_result else "",
            stderr=last_result.stderr if last_result else "",
            error_code=_PbsErrorCode.POLL_PARSE_STATE_FAILED.value,
            retryable=False,
            phase="poll",
        )

    def compatibility_notes(self) -> list[str]:
        """Describe the current PBS compatibility boundaries."""

        return [
            "The PBS layer is a compatibility bridge and collapses the request into a single select chunk.",
            "Node and task topology are not modeled explicitly; total CPU count is rendered into one select specification.",
            "No PBS array jobs, placement rules, or site-specific resource selectors are emitted in the current planning layer.",
            "Real submit mode executes qsub with retry/backoff and parses the returned job id.",
            "Real poll mode queries qstat -f and falls back to qstat -xf for finished jobs.",
            "PBS submit and poll errors are classified into retryable and non-retryable categories.",
        ]

    def _build_submit_returncode_error(
        self,
        *,
        command: list[str],
        result: subprocess.CompletedProcess[str],
        attempt: int,
    ) -> SchedulerExecutionError:
        classification = self._classify_submit_failure(
            stdout=result.stdout,
            stderr=result.stderr,
            returncode=result.returncode,
        )
        return SchedulerExecutionError(
            classification.message,
            command=command,
            stdout=result.stdout,
            stderr=result.stderr,
            attempts=attempt,
            error_code=classification.code.value,
            retryable=classification.retryable,
            phase="submit",
        )

    def _failure_recovery_plan(
        self,
        *,
        handle,
        request,
        paths,
    ) -> list[str]:
        plan = super()._failure_recovery_plan(handle=handle, request=request, paths=paths)
        plan.extend(
            [
                f"pbs diagnostics: qstat -f {handle.job_id}",
                f"pbs fallback diagnostics: qstat -xf {handle.job_id}",
                "if submit outcome is ambiguous, require manual confirmation before requeue to avoid duplicate jobs",
            ]
        )
        return plan

    def _run_qstat_with_retry(
        self,
        *,
        command: list[str],
        retries: int = 2,
    ) -> subprocess.CompletedProcess[str]:
        last_error: SchedulerExecutionError | None = None
        last_result: subprocess.CompletedProcess[str] | None = None
        attempts = max(1, retries)
        for _ in range(attempts):
            try:
                result = self._run_command(
                    command=command,
                    cwd=None,
                    timeout_seconds=self._command_timeout_seconds,
                )
            except SchedulerExecutionError as error:
                last_error = error
                if not self._is_retryable_poll_error(error):
                    raise
                continue
            last_result = result
            if result.returncode == 0:
                return result
            classification = self._classify_poll_failure(
                stdout=result.stdout,
                stderr=result.stderr,
                returncode=result.returncode,
            )
            if classification.code == _PbsErrorCode.PBS_UNKNOWN_JOB or not classification.retryable:
                return result
        if last_result is not None:
            return last_result
        if last_error is not None:
            raise last_error
        return subprocess.CompletedProcess(command, 1, stdout="", stderr="")

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
            if exit_status == 0:
                return JobState.COMPLETED
            if exit_status is None:
                return JobState.UNKNOWN
            return JobState.FAILED
        if normalized in {"X"}:
            return JobState.FAILED
        return JobState.UNKNOWN

    def _extract_job_id_from_qsub_output(self, text: str) -> str | None:
        for line in text.splitlines():
            match = self._QSUB_JOB_ID_PATTERN.match(line)
            if match:
                return self._normalize_pbs_job_id(match.group(1))
        return None

    def _normalize_pbs_job_id(self, raw: str) -> str:
        return raw.strip()

    def _is_unknown_job_error(self, *, stdout: str = "", stderr: str = "") -> bool:
        lowered = f"{stdout}\n{stderr}".lower()
        return (
            "unknown job id" in lowered
            or "unknown job_id" in lowered
            or "job has finished" in lowered
            or "cannot locate job" in lowered
            or "does not exist" in lowered
        )

    def _classify_submit_failure(self, *, stdout: str, stderr: str, returncode: int) -> _PbsErrorClass:
        _ = returncode
        lowered = f"{stdout}\n{stderr}".lower()
        if self._contains_any(
            lowered,
            [
                "cannot connect",
                "connection refused",
                "timed out",
                "temporarily unavailable",
                "try again",
                "transient",
            ],
        ):
            return _PbsErrorClass(
                code=_PbsErrorCode.SUBMIT_TRANSPORT_ERROR,
                message="PBS submit failed due to transient scheduler transport issue.",
                retryable=True,
            )
        if self._contains_any(lowered, ["permission denied", "not authorized", "unauthorized", "access denied"]):
            return _PbsErrorClass(
                code=_PbsErrorCode.SUBMIT_PERMISSION_DENIED,
                message="PBS submit rejected due to permission/auth policy.",
                retryable=False,
            )
        if self._contains_any(lowered, ["invalid", "illegal", "unknown queue", "cannot open", "no such file"]):
            return _PbsErrorClass(
                code=_PbsErrorCode.SUBMIT_INVALID_REQUEST,
                message="PBS submit rejected due to invalid request or script path.",
                retryable=False,
            )
        if self._contains_any(lowered, ["quota", "exceeds", "walltime", "limit", "policy"]):
            return _PbsErrorClass(
                code=_PbsErrorCode.SUBMIT_POLICY_REJECTED,
                message="PBS submit rejected by scheduler policy or quota.",
                retryable=False,
            )
        return _PbsErrorClass(
            code=_PbsErrorCode.SUBMIT_FAILED,
            message="PBS submit command returned non-zero exit code.",
            retryable=True,
        )

    def _classify_poll_failure(self, *, stdout: str, stderr: str, returncode: int) -> _PbsErrorClass:
        _ = returncode
        lowered = f"{stdout}\n{stderr}".lower()
        if self._is_unknown_job_error(stdout=stdout, stderr=stderr):
            return _PbsErrorClass(
                code=_PbsErrorCode.PBS_UNKNOWN_JOB,
                message="PBS poll returned unknown job identifier.",
                retryable=False,
            )
        if self._contains_any(
            lowered,
            ["cannot connect", "connection refused", "timed out", "temporarily unavailable", "try again"],
        ):
            return _PbsErrorClass(
                code=_PbsErrorCode.POLL_TRANSPORT_ERROR,
                message="PBS poll failed due to transient scheduler transport issue.",
                retryable=True,
            )
        if self._contains_any(lowered, ["permission denied", "not authorized", "unauthorized", "access denied"]):
            return _PbsErrorClass(
                code=_PbsErrorCode.POLL_PERMISSION_DENIED,
                message="PBS poll rejected due to permission/auth policy.",
                retryable=False,
            )
        return _PbsErrorClass(
            code=_PbsErrorCode.POLL_FAILED,
            message="PBS poll command returned non-zero exit code.",
            retryable=False,
        )

    def _is_retryable_poll_error(self, error: SchedulerExecutionError) -> bool:
        if error.retryable is not None:
            return error.retryable
        return bool(error.error_code in {"TIMEOUT", _PbsErrorCode.POLL_TRANSPORT_ERROR.value})

    def _contains_any(self, text: str, needles: list[str]) -> bool:
        return any(needle in text for needle in needles)
