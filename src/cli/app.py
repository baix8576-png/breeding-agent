"""Typer-based CLI entrypoint for the GeneAgent skeleton."""

from __future__ import annotations

import json

import typer
from rich.console import Console
from scheduler.base import SchedulerExecutionError

from contracts.api import RequestIdentity
from runtime.bootstrap import create_application_context

app = typer.Typer(help="GeneAgent CLI skeleton for local genetics workflow orchestration.")
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
    """Display the current runtime skeleton configuration."""

    context = create_application_context()
    console.print(
        {
            "app_name": context.settings.app_name,
            "scheduler_type": context.settings.scheduler_type.value,
            "dry_run_default": context.settings.dry_run_default,
            "work_root": context.settings.work_root,
        }
    )


def main() -> None:
    """Run the Typer application."""

    app()


if __name__ == "__main__":
    main()
