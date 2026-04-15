"""SLURM-first scheduler adapter for dry-run and submit-preview planning."""

from __future__ import annotations

from contracts.common import SchedulerKind
from scheduler.models import SchedulerPaths, SchedulerResourceRequest
from scheduler.base import BaseSchedulerAdapter


class SlurmSchedulerAdapter(BaseSchedulerAdapter):
    """SLURM-first scheduler adapter for the first practical planning layer."""

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

    def compatibility_notes(self) -> list[str]:
        """Describe the current SLURM compatibility boundaries."""

        return [
            "The adapter targets single-job submission scripts and does not yet model job arrays or dependencies.",
            "Memory is rendered as total job memory via --mem, not per-CPU memory via --mem-per-cpu.",
            "No GPU, TRES, reservation, license, or advanced sbatch flags are emitted in the current planning layer.",
            "poll() only interprets synthetic IDs or injected state tokens; it does not contact squeue or sacct yet.",
        ]
