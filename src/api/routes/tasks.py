"""Task planning and execution endpoints for GeneAgent V1."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from contracts.api import (
    DraftPlanRequest,
    DryRunRequest,
    PollExplainRequest,
    ReviewActionRequest,
    SubmitRequest,
    SubmitPreviewRequest,
    ValidateInputsRequest,
)
from runtime.bootstrap import create_application_context
from scheduler.base import SchedulerExecutionError

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/draft-plan")
def draft_plan(payload: DraftPlanRequest) -> dict[str, object]:
    """Return structured orchestration output for a user request."""

    context = create_application_context()
    plan_result = context.facade.draft_plan(
        text=payload.text,
        identity=payload.identity,
        requested_outputs=payload.requested_outputs,
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


@router.post("/dry-run")
def dry_run(payload: DryRunRequest) -> dict[str, object]:
    """Preview scheduler submission artifacts without real execution."""

    context = create_application_context()
    submission = context.facade.build_dry_run_submission(
        command=payload.command,
        request_text=payload.request_text,
        identity=payload.identity,
    )
    return {"submission": submission.model_dump(mode="json")}


@router.post("/submit-preview")
def submit_preview(payload: SubmitPreviewRequest) -> dict[str, object]:
    """Build scheduler submit-preview artifacts without issuing a real submit command."""

    context = create_application_context()
    submission = context.facade.build_submit_preview(
        command=payload.command,
        request_text=payload.request_text,
        identity=payload.identity,
        dry_run_completed=payload.dry_run_completed,
    )
    return {"submission": submission.model_dump(mode="json")}


@router.post("/submit")
def submit(payload: SubmitRequest) -> dict[str, object]:
    """Submit a real scheduler job when the safety gate allows execution."""

    context = create_application_context()
    try:
        submission = context.facade.submit(
            command=payload.command,
            request_text=payload.request_text,
            identity=payload.identity,
            dry_run_completed=payload.dry_run_completed,
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
