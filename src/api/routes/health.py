"""Health and runtime information endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from runtime.settings import get_settings

router = APIRouter(tags=["health"])


@router.get("/health")
def health() -> dict[str, object]:
    """Return a small runtime health payload."""

    settings = get_settings()
    return {
        "status": "ok",
        "app_name": settings.app_name,
        "scheduler_type": settings.scheduler_type.value,
        "dry_run_default": settings.dry_run_default,
    }
