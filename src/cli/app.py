"""Typer-based CLI entrypoint for the GeneAgent skeleton."""

from __future__ import annotations

import json

import typer
from rich.console import Console

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
    report = context.facade.validate_inputs(paths=paths)
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
