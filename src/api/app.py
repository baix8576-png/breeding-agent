"""FastAPI application factory for the GeneAgent skeleton."""

from __future__ import annotations

from fastapi import FastAPI

from api.routes.health import router as health_router
from api.routes.tasks import router as tasks_router


def create_app() -> FastAPI:
    """Create the FastAPI application with the first-pass routes."""

    app = FastAPI(
        title="GeneAgent API",
        version="0.1.0",
        summary="Skeleton API for local genetics workflow orchestration.",
    )
    app.include_router(health_router)
    app.include_router(tasks_router)
    return app


app = create_app()
