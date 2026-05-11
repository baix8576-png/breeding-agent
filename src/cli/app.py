"""Typer-based CLI entrypoint for GeneAgent V1 workflows."""

from __future__ import annotations

import json
import shutil

import typer
from rich.console import Console
from scheduler.base import SchedulerExecutionError

from contracts.api import RequestIdentity
from contracts.validation import InputBundle, InputBundleEntry
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
    input_entry: list[str] | None = typer.Option(
        None,
        "--input-entry",
        help="Structured input entry in role=path form; repeat for multiple values.",
    ),
    input_species: str | None = typer.Option(None, "--input-species", help="Optional species label for InputBundle."),
    input_cohort: str | None = typer.Option(None, "--input-cohort", help="Optional cohort label for InputBundle."),
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
        input_bundle=_build_cli_input_bundle(
            input_entries=input_entry,
            species=input_species,
            cohort_name=input_cohort,
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
    reason: str | None = None,
    target_path: list[str] | None = typer.Option(
        None,
        "--target-path",
        help="Target path in scope for the reviewed action; repeat for multiple paths.",
    ),
    external_network: bool = False,
    cloud_llm: bool = False,
    approval_approver: str | None = typer.Option(None, "--approval-approver", help="Manual approval approver."),
    approval_reason: str | None = typer.Option(None, "--approval-reason", help="Manual approval reason."),
    approval_time: str | None = typer.Option(None, "--approval-time", help="Manual approval timestamp (ISO-8601)."),
    outbound_field: list[str] | None = typer.Option(
        None,
        "--outbound-field",
        help="Outbound payload field in key=value form; repeat for multiple fields.",
    ),
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
        reason=reason,
        target_paths=target_path,
        external_network=external_network,
        cloud_llm=cloud_llm,
        approval=_build_approval_payload(
            approver=approval_approver,
            reason=approval_reason,
            approved_at=approval_time,
        ),
        outbound_payload=_build_outbound_payload(outbound_field),
    )
    console.print_json(json.dumps(review.model_dump(mode="json")))


@app.command("dry-run")
def dry_run(
    working_directory: str | None = None,
    request_text: str = "Prepare a dry-run submission",
    task_id: str | None = None,
    run_id: str | None = None,
    session_id: str | None = None,
    input_entry: list[str] | None = typer.Option(
        None,
        "--input-entry",
        help="Structured input entry in role=path form; repeat for multiple values.",
    ),
    input_species: str | None = typer.Option(None, "--input-species", help="Optional species label for InputBundle."),
    input_cohort: str | None = typer.Option(None, "--input-cohort", help="Optional cohort label for InputBundle."),
    approval_approver: str | None = typer.Option(None, "--approval-approver", help="Manual approval approver."),
    approval_reason: str | None = typer.Option(None, "--approval-reason", help="Manual approval reason."),
    approval_time: str | None = typer.Option(None, "--approval-time", help="Manual approval timestamp (ISO-8601)."),
    outbound_field: list[str] | None = typer.Option(
        None,
        "--outbound-field",
        help="Outbound payload field in key=value form; repeat for multiple fields.",
    ),
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
        input_bundle=_build_cli_input_bundle(
            input_entries=input_entry,
            species=input_species,
            cohort_name=input_cohort,
        ),
        approval=_build_approval_payload(
            approver=approval_approver,
            reason=approval_reason,
            approved_at=approval_time,
        ),
        outbound_payload=_build_outbound_payload(outbound_field),
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
    input_entry: list[str] | None = typer.Option(
        None,
        "--input-entry",
        help="Structured input entry in role=path form; repeat for multiple values.",
    ),
    input_species: str | None = typer.Option(None, "--input-species", help="Optional species label for InputBundle."),
    input_cohort: str | None = typer.Option(None, "--input-cohort", help="Optional cohort label for InputBundle."),
    approval_approver: str | None = typer.Option(None, "--approval-approver", help="Manual approval approver."),
    approval_reason: str | None = typer.Option(None, "--approval-reason", help="Manual approval reason."),
    approval_time: str | None = typer.Option(None, "--approval-time", help="Manual approval timestamp (ISO-8601)."),
    outbound_field: list[str] | None = typer.Option(
        None,
        "--outbound-field",
        help="Outbound payload field in key=value form; repeat for multiple fields.",
    ),
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
        input_bundle=_build_cli_input_bundle(
            input_entries=input_entry,
            species=input_species,
            cohort_name=input_cohort,
        ),
        approval=_build_approval_payload(
            approver=approval_approver,
            reason=approval_reason,
            approved_at=approval_time,
        ),
        outbound_payload=_build_outbound_payload(outbound_field),
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
    input_entry: list[str] | None = typer.Option(
        None,
        "--input-entry",
        help="Structured input entry in role=path form; repeat for multiple values.",
    ),
    input_species: str | None = typer.Option(None, "--input-species", help="Optional species label for InputBundle."),
    input_cohort: str | None = typer.Option(None, "--input-cohort", help="Optional cohort label for InputBundle."),
    approval_approver: str | None = typer.Option(None, "--approval-approver", help="Manual approval approver."),
    approval_reason: str | None = typer.Option(None, "--approval-reason", help="Manual approval reason."),
    approval_time: str | None = typer.Option(None, "--approval-time", help="Manual approval timestamp (ISO-8601)."),
    outbound_field: list[str] | None = typer.Option(
        None,
        "--outbound-field",
        help="Outbound payload field in key=value form; repeat for multiple fields.",
    ),
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
            input_bundle=_build_cli_input_bundle(
                input_entries=input_entry,
                species=input_species,
                cohort_name=input_cohort,
            ),
            approval=_build_approval_payload(
                approver=approval_approver,
                reason=approval_reason,
                approved_at=approval_time,
            ),
            outbound_payload=_build_outbound_payload(outbound_field),
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


@app.command("audit-export")
def audit_export(
    run_id: str,
    task_id: str | None = None,
    working_directory: str | None = None,
    output_path: str | None = None,
    include_files: bool = typer.Option(
        True,
        "--include-files/--manifest-only",
        help="Include real log/report/result attachments in zip, or export manifest-only package.",
    ),
) -> None:
    """Export one run-level audit package (input/plan/command/job/log/report/approval trail)."""

    context = create_application_context()
    try:
        bundle = context.facade.export_audit_bundle(
            run_id=run_id,
            task_id=task_id,
            identity=RequestIdentity(
                task_id=task_id,
                run_id=run_id,
                working_directory=working_directory,
            ),
            output_path=output_path,
            include_files=include_files,
        )
    except ValueError as error:
        console.print_json(json.dumps({"error": str(error), "gate": "audit_trace_not_found"}))
        raise typer.Exit(code=1) from error
    console.print_json(json.dumps(bundle.model_dump(mode="json")))


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


@app.command("observability")
def observability(
    working_directory: str | None = None,
    limit: int = 200,
) -> None:
    """Show observability metrics (task, scheduler, and failure taxonomy)."""

    context = create_application_context()
    payload = context.facade.observability_metrics(
        working_directory=working_directory,
        limit=max(1, limit),
    )
    console.print_json(json.dumps(payload))


@app.command("production-gate")
def production_gate(
    working_directory: str | None = None,
    execute_tests: bool = False,
    timeout_seconds: int = 300,
) -> None:
    """Run production gate pipeline checks for contracts/scheduler/knowledge/audit."""

    context = create_application_context()
    payload = context.facade.production_gate_pipeline(
        working_directory=working_directory,
        execute_tests=execute_tests,
        timeout_seconds=timeout_seconds,
    )
    console.print_json(json.dumps(payload))


@app.command("release-plan")
def release_plan(
    version_tag: str = "v2.0.0",
    change_summary: str = "",
    stage_id: list[str] | None = typer.Option(
        None,
        "--stage-id",
        help="Stage ids mapped to this release; repeat for multiple values.",
    ),
) -> None:
    """Generate standardized release package plan with rollback template."""

    context = create_application_context()
    payload = context.facade.release_plan(
        version_tag=version_tag,
        change_summary=change_summary,
        stage_ids=stage_id or [],
    )
    console.print_json(json.dumps(payload))


@app.command("final-review")
def final_review(working_directory: str | None = None) -> None:
    """Run V2.0 final acceptance review (architecture/governance/operability)."""

    context = create_application_context()
    payload = context.facade.final_acceptance_review(
        working_directory=working_directory,
    )
    console.print_json(json.dumps(payload))


def _scheduler_command_set(scheduler: str) -> list[str]:
    if scheduler.lower() == "pbs":
        return ["qsub", "qstat"]
    return ["sbatch", "squeue", "sacct"]


def _build_cli_input_bundle(
    *,
    input_entries: list[str] | None,
    species: str | None,
    cohort_name: str | None,
) -> InputBundle | None:
    raw_entries = input_entries or []
    if not raw_entries and species is None and cohort_name is None:
        return None
    entries: list[InputBundleEntry] = []
    for index, item in enumerate(raw_entries):
        role, separator, path = item.partition("=")
        if separator and role.strip() and path.strip():
            entries.append(InputBundleEntry(role=role.strip(), path=path.strip()))
            continue
        entries.append(InputBundleEntry(role=f"input_{index + 1}", path=item.strip()))
    return InputBundle(species=species, cohort_name=cohort_name, entries=entries)


def _build_approval_payload(
    *,
    approver: str | None,
    reason: str | None,
    approved_at: str | None,
) -> dict[str, object] | None:
    if not any([approver, reason, approved_at]):
        return None
    return {
        "approved": True,
        "approver": approver,
        "reason": reason,
        "approved_at": approved_at,
    }


def _build_outbound_payload(entries: list[str] | None) -> dict[str, object] | None:
    raw_entries = entries or []
    if not raw_entries:
        return None
    payload: dict[str, object] = {}
    for item in raw_entries:
        key, separator, value = item.partition("=")
        if not separator:
            continue
        key_norm = key.strip()
        value_norm = value.strip()
        if not key_norm:
            continue
        payload[key_norm] = value_norm
    return payload or None


def main() -> None:
    """Run the Typer application."""

    app()


if __name__ == "__main__":
    main()
