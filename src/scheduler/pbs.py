"""PBS compatibility adapter kept behind the SLURM-first planning layer."""

from __future__ import annotations

from contracts.common import SchedulerKind
from scheduler.models import SchedulerPaths, SchedulerResourceRequest
from scheduler.base import BaseSchedulerAdapter


class PbsSchedulerAdapter(BaseSchedulerAdapter):
    """PBS adapter retained for compatibility planning without real scheduler calls."""

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

    def compatibility_notes(self) -> list[str]:
        """Describe the current PBS compatibility boundaries."""

        return [
            "The PBS layer is a compatibility bridge and collapses the request into a single select chunk.",
            "Node and task topology are not modeled explicitly; total CPU count is rendered into one select specification.",
            "No PBS array jobs, placement rules, or site-specific resource selectors are emitted in the current planning layer.",
            "poll() only interprets synthetic IDs or injected state tokens; it does not contact qstat yet.",
        ]
