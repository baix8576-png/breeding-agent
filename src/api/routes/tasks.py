"""Task planning endpoints for the first project skeleton."""

from __future__ import annotations

from fastapi import APIRouter

from contracts.api import DraftPlanRequest, DryRunRequest, ReviewActionRequest, ValidateInputsRequest
from runtime.bootstrap import create_application_context

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/draft-plan")
def draft_plan(payload: DraftPlanRequest) -> dict[str, object]:
    """Return the orchestration skeleton output for a user request."""

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
    report = context.facade.validate_inputs(paths=payload.paths)
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
