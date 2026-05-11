"""Release and governance endpoints (production gate, release plan, final review)."""

from __future__ import annotations

from fastapi import APIRouter

from contracts.api import ProductionGateRequest, ReleasePlanRequest
from runtime.bootstrap import create_application_context

router = APIRouter(tags=["release"])


@router.post("/v2/release/production-gate")
def production_gate(payload: ProductionGateRequest) -> dict[str, object]:
    """Run or plan production gate checks for release readiness."""

    context = create_application_context()
    report = context.facade.production_gate_pipeline(
        working_directory=payload.working_directory,
        execute_tests=payload.execute_tests,
        timeout_seconds=payload.timeout_seconds,
    )
    return {"production_gate": report}


@router.post("/v2/release/plan")
def release_plan(payload: ReleasePlanRequest) -> dict[str, object]:
    """Generate standardized release plan (version tag + notes template + rollback)."""

    context = create_application_context()
    plan = context.facade.release_plan(
        version_tag=payload.version_tag,
        change_summary=payload.change_summary,
        stage_ids=payload.stage_ids,
    )
    return {"release_plan": plan}


@router.get("/v2/release/final-review")
def final_review(working_directory: str | None = None) -> dict[str, object]:
    """Run V2.0 final acceptance review from architecture/governance/operability gates."""

    context = create_application_context()
    report = context.facade.final_acceptance_review(
        working_directory=working_directory,
    )
    return {"final_review": report}
