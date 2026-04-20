"""Typer-based CLI entrypoint for GeneAgent V1 workflows."""

from __future__ import annotations

import json
import shutil

import typer
from rich.console import Console
from scheduler.base import SchedulerExecutionError

from contracts.api import RequestIdentity
from runtime.bootstrap import create_application_context

app = typer.Typer(help="GeneAgent CLI for local genetics workflow orchestration.")
console = Console()


@app.command("plan")
def plan(
    request_text: str,
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
    working_directory: str | None = None,
) -> None:
    """Draft a plan from a natural-language request."""

    context = create_application_context()
    plan_result = context.facade.draft_plan(
        text=request_text,
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            session_id=session_id,
            working_directory=working_directory,
        ),
    )
    console.print_json(json.dumps(plan_result.model_dump(mode="json")))


@app.command("report")
def report(
    working_directory: str | None = None,
    request_text: str = "Prepare report preview",
    requested_outputs: list[str] | None = typer.Option(
        None,
        "--requested-output",
        help="Requested report outputs; repeat this option for multiple values.",
    ),
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
) -> None:
    """Generate a report-oriented preview payload without adding runtime business logic here."""

    context = create_application_context()
    report_preview = context.facade.build_report_preview(
        request_text=request_text,
        requested_outputs=requested_outputs or [],
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            session_id=session_id,
            working_directory=working_directory,
        ),
    )
    console.print_json(json.dumps(report_preview.model_dump(mode="json")))


@app.command("diagnostic")
def diagnostic(
    working_directory: str | None = None,
    request_text: str = "Prepare diagnostic preview",
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
) -> None:
    """Generate diagnostic preview guidance while keeping non-bio intent off cluster execution paths."""

    context = create_application_context()
    diagnostic_preview = context.facade.build_diagnostic_preview(
        request_text=request_text,
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            session_id=session_id,
            working_directory=working_directory,
        ),
    )
    console.print_json(json.dumps(diagnostic_preview.model_dump(mode="json")))


@app.command("validate-inputs")
def validate_inputs(paths: list[str]) -> None:
    """Validate local input files before workflow construction."""

    context = create_application_context()
    report = context.facade.validate_inputs(paths)
    console.print_json(json.dumps(report.model_dump(mode="json")))


@app.command("review-action")
def review_action(
    action_name: str,
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
    working_directory: str | None = None,
) -> None:
    """Review a named action through the safety gate."""

    context = create_application_context()
    review = context.facade.review_action(
        action_name=action_name,
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            session_id=session_id,
            working_directory=working_directory,
        ),
    )
    console.print_json(json.dumps(review.model_dump(mode="json")))


@app.command("dry-run")
def dry_run(
    working_directory: str | None = None,
    request_text: str = "Prepare a dry-run submission",
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
) -> None:
    """Generate a scheduler script preview without submitting a real job."""

    context = create_application_context()
    submission = context.facade.build_dry_run_submission(
        request_text=request_text,
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            session_id=session_id,
            working_directory=working_directory,
        ),
    )
    console.print_json(json.dumps(submission.model_dump(mode="json")))


@app.command("submit-preview")
def submit_preview(
    working_directory: str | None = None,
    request_text: str = "Prepare a submit-preview",
    dry_run_completed: bool = False,
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
) -> None:
    """Generate submit-preview artifacts without issuing a real scheduler submission."""

    context = create_application_context()
    submission = context.facade.build_submit_preview(
        request_text=request_text,
        dry_run_completed=dry_run_completed,
        identity=RequestIdentity(
            task_id=task_id,
            run_id=run_id,
            session_id=session_id,
            working_directory=working_directory,
        ),
    )
    console.print_json(json.dumps(submission.model_dump(mode="json")))


@app.command("submit")
def submit(
    working_directory: str | None = None,
    request_text: str = "Submit scheduler job",
    dry_run_completed: bool = False,
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
) -> None:
    """Submit a real scheduler job after safety checks pass."""

    context = create_application_context()
    try:
        submission = context.facade.submit(
            request_text=request_text,
            dry_run_completed=dry_run_completed,
            identity=RequestIdentity(
                task_id=task_id,
                run_id=run_id,
                session_id=session_id,
                working_directory=working_directory,
            ),
        )
    except PermissionError as error:
        console.print_json(json.dumps({"error": str(error), "gate": "blocked_or_confirmation_required"}))
        raise typer.Exit(code=1) from error
    except SchedulerExecutionError as error:
        console.print_json(
            json.dumps(
                {
                    "error": str(error),
                    "command": error.command,
                    "stdout": error.stdout,
                    "stderr": error.stderr,
                    "attempts": error.attempts,
                }
            )
        )
        raise typer.Exit(code=1) from error
    console.print_json(json.dumps(submission.model_dump(mode="json")))


@app.command("poll-explain")
def poll_explain(job_id: str) -> None:
    """Explain a scheduler poll state from a job identifier."""

    context = create_application_context()
    poll = context.facade.explain_poll_state(job_id=job_id)
    console.print_json(json.dumps(poll.model_dump(mode="json")))


@app.command("doctor")
def doctor() -> None:
    """Display current runtime configuration and scheduler readiness."""

    context = create_application_context()
    scheduler_commands = _scheduler_command_set(context.settings.scheduler_type.value)
    command_paths = {command: shutil.which(command) for command in ["bash", *scheduler_commands]}
    missing_commands = [name for name, resolved in command_paths.items() if resolved is None]
    real_submit_ready = (
        context.settings.scheduler_real_execution_enabled and all(command_paths[name] for name in scheduler_commands)
    )
    recommendation = (
        "real submit/poll ready"
        if real_submit_ready
        else "use dry-run/submit-preview locally, or run real submit/poll on scheduler host"
    )
    console.print(
        {
            "app_name": context.settings.app_name,
            "scheduler_type": context.settings.scheduler_type.value,
            "dry_run_default": context.settings.dry_run_default,
            "scheduler_real_execution_enabled": context.settings.scheduler_real_execution_enabled,
            "work_root": context.settings.work_root,
            "command_paths": command_paths,
            "missing_commands": missing_commands,
            "recommendation": recommendation,
        }
    )


def _scheduler_command_set(scheduler: str) -> list[str]:
    if scheduler.lower() == "pbs":
        return ["qsub", "qstat"]
    return ["sbatch", "squeue", "sacct"]


def main() -> None:
    """Run the Typer application."""

    app()


if __name__ == "__main__":
    main()
