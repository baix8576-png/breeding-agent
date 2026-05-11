"""FastAPI application factory with v1-compat and v2-stable routes."""

from __future__ import annotations

from fastapi import Request
from fastapi import FastAPI

from api.routes.health import router as health_router
from api.routes.observability import router as observability_router
from api.routes.release import router as release_router
from api.routes.tasks import router as tasks_router
from api.routes.console import router as console_router
from api.routes.versioning import router as versioning_router
from runtime.settings import get_settings


def create_app() -> FastAPI:
    """Create the FastAPI application with versioned task and console routes."""

    settings = get_settings()
    app = FastAPI(
        title="GeneAgent API",
        version="0.1.0",
        summary="API for local genetics workflow orchestration, versioned stability, and runtime console.",
    )

    @app.middleware("http")
    async def _api_version_headers(request: Request, call_next):
        response = await call_next(request)
        path = request.url.path
        if path.startswith(settings.api_v1_prefix):
            response.headers["X-GeneAgent-API-Version"] = "v1"
            response.headers["Deprecation"] = "true"
            response.headers["Sunset"] = settings.api_v1_sunset_date
            response.headers["X-GeneAgent-Compatibility-Window-Days"] = str(settings.api_compatibility_window_days)
            response.headers["Link"] = f'<{settings.api_version_policy_path}>; rel="deprecation"; type="application/json"'
        elif path.startswith("/v2/"):
            response.headers["X-GeneAgent-API-Version"] = settings.api_current_version
            response.headers["X-GeneAgent-Stability"] = "stable"
        return response

    app.include_router(health_router)
    app.include_router(tasks_router)
    app.include_router(tasks_router, prefix="/v2")
    app.include_router(versioning_router)
    app.include_router(console_router)
    app.include_router(observability_router)
    app.include_router(release_router)
    return app


app = create_app()
