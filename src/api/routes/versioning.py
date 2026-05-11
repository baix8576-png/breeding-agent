"""API versioning policy endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from runtime.settings import get_settings

router = APIRouter(tags=["versioning"])


@router.get("/v2/version-policy")
def version_policy() -> dict[str, object]:
    """Expose API stability policy, compatibility window, and deprecation timeline."""

    settings = get_settings()
    return {
        "schema_version": "api_version_policy.v1",
        "current_api_version": settings.api_current_version,
        "stable_prefix": settings.api_v2_prefix,
        "legacy_prefix": settings.api_v1_prefix,
        "deprecation_started_at": settings.api_v1_deprecation_started_at,
        "sunset_date": settings.api_v1_sunset_date,
        "compatibility_window_days": settings.api_compatibility_window_days,
        "policy": {
            "v2": "stable; additive changes only",
            "v1": "deprecated but supported within compatibility window",
            "breaking_change_rule": "breaking changes are introduced under /v{n+1}",
        },
    }
