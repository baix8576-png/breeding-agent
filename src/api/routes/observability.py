"""Observability endpoints for runtime/task/scheduler dashboards."""

from __future__ import annotations

from fastapi import APIRouter, Query

from runtime.bootstrap import create_application_context

router = APIRouter(tags=["observability"])


@router.get("/v2/observability/metrics")
def metrics(
    working_directory: str | None = None,
    limit: int = Query(default=200, ge=1, le=2000),
) -> dict[str, object]:
    """Return aggregated observability metrics for task/scheduler/failure dimensions."""

    context = create_application_context()
    payload = context.facade.observability_metrics(
        working_directory=working_directory,
        limit=limit,
    )
    return {"metrics": payload}


@router.get("/v2/observability/dashboard")
def dashboard(
    working_directory: str | None = None,
    limit: int = Query(default=100, ge=1, le=1000),
) -> dict[str, object]:
    """Return dashboard payload (metrics + board + failure classes)."""

    context = create_application_context()
    payload = context.facade.observability_dashboard(
        working_directory=working_directory,
        limit=limit,
    )
    return {"dashboard": payload}
