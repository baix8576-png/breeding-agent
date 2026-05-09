"""Task planning and execution endpoints for GeneAgent V1."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from contracts.api import (
    DiagnosticPreviewRequest,
    DraftPlanRequest,
    DryRunRequest,
    PollExplainRequest,
    ReportPreviewRequest,
    ReviewActionRequest,
    SubmitRequest,
    SubmitPreviewRequest,
    ValidateInputsRequest,
)
from runtime.bootstrap import create_application_context
from runtime.compat import (
    envelope_from_diagnostic,
    envelope_from_draft_plan,
    envelope_from_dry_run,
    envelope_from_report,
    envelope_from_submit,
    envelope_from_submit_preview,
)
from scheduler.base import SchedulerExecutionError

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/draft-plan")
def draft_plan(payload: DraftPlanRequest) -> dict[str, object]:
    """Return structured orchestration output for a user request."""

    context = create_application_context()
    envelope = envelope_from_draft_plan(payload)
    plan_result = context.facade.draft_plan(
        text=envelope.request_text,
        identity=envelope.identity,
        requested_outputs=envelope.requested_outputs,
        input_bundle=envelope.input_bundle,
    )
    return {"plan": plan_result.model_dump(mode="json")}


@router.post("/validate-inputs")
def validate_inputs(payload: ValidateInputsRequest) -> dict[str, object]:
    """Validate local workflow inputs."""

    context = create_application_context()
    if payload.entries:
        report = context.facade.validate_inputs(
            {
                "task_id": payload.task_id or payload.identity.task_id,
                "run_id": payload.run_id or payload.identity.run_id,
                "species": payload.species,
                "cohort_name": payload.cohort_name,
                "entries": payload.entries,
            }
        )
    else:
        report = context.facade.validate_inputs(payload.paths)
    return {"validation": report.model_dump(mode="json")}


@router.post("/review-action")
def review_action(payload: ReviewActionRequest) -> dict[str, object]:
    """Review a named action through the safety gate."""

    context = create_application_context()
    result = context.facade.review_action(
        action_name=payload.action_name,
        identity=payload.identity,
        reason=payload.reason,
        target_paths=payload.target_paths,
    )
    return {"review": result.model_dump(mode="json")}


@router.post("/report")
def report(payload: ReportPreviewRequest) -> dict[str, object]:
    """Generate a report-oriented preview payload from a user request."""

    context = create_application_context()
    envelope = envelope_from_report(payload)
    report_preview = context.facade.build_report_preview(
        request_text=envelope.request_text,
        requested_outputs=envelope.requested_outputs,
        identity=envelope.identity,
    )
    return {"report": report_preview.model_dump(mode="json")}


@router.post("/diagnostic")
def diagnostic(payload: DiagnosticPreviewRequest) -> dict[str, object]:
    """Generate diagnostic guidance without triggering cluster execution for non-bio intent."""

    context = create_application_context()
    envelope = envelope_from_diagnostic(payload)
    diagnostic_preview = context.facade.build_diagnostic_preview(
        request_text=envelope.request_text,
        identity=envelope.identity,
    )
    return {"diagnostic": diagnostic_preview.model_dump(mode="json")}


@router.post("/dry-run")
def dry_run(payload: DryRunRequest) -> dict[str, object]:
    """Preview scheduler submission artifacts without real execution."""

    context = create_application_context()
    envelope = envelope_from_dry_run(payload)
    submission = context.facade.build_dry_run_submission(
        command=envelope.command,
        request_text=envelope.request_text,
        identity=envelope.identity,
        input_bundle=envelope.input_bundle,
    )
    return {"submission": submission.model_dump(mode="json")}


@router.post("/submit-preview")
def submit_preview(payload: SubmitPreviewRequest) -> dict[str, object]:
    """Build scheduler submit-preview artifacts without issuing a real submit command."""

    context = create_application_context()
    envelope = envelope_from_submit_preview(payload)
    submission = context.facade.build_submit_preview(
        command=envelope.command,
        request_text=envelope.request_text,
        identity=envelope.identity,
        dry_run_completed=envelope.dry_run_completed,
        input_bundle=envelope.input_bundle,
    )
    return {"submission": submission.model_dump(mode="json")}


@router.post("/submit")
def submit(payload: SubmitRequest) -> dict[str, object]:
    """Submit a real scheduler job when the safety gate allows execution."""

    context = create_application_context()
    envelope = envelope_from_submit(payload)
    try:
        submission = context.facade.submit(
            command=envelope.command,
            request_text=envelope.request_text,
            identity=envelope.identity,
            dry_run_completed=envelope.dry_run_completed,
            input_bundle=envelope.input_bundle,
        )
    except PermissionError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except SchedulerExecutionError as error:
        raise HTTPException(
            status_code=502,
            detail={
                "message": str(error),
                "command": error.command,
                "stdout": error.stdout,
                "stderr": error.stderr,
                "attempts": error.attempts,
            },
        ) from error
    return {"submission": submission.model_dump(mode="json")}


@router.post("/poll-explain")
def poll_explain(payload: PollExplainRequest) -> dict[str, object]:
    """Explain a scheduler poll state for a job id."""

    context = create_application_context()
    explanation = context.facade.explain_poll_state(payload.job_id)
    return {"poll": explanation.model_dump(mode="json")}
