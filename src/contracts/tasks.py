"""Typed request and resource models used across GeneAgent."""

from __future__ import annotations

from pydantic import BaseModel, Field

class UserRequest(BaseModel):
    """Normalized request object built from CLI or API input."""

    text: str
    working_directory: str | None = None
    requested_outputs: list[str] = Field(default_factory=list)


class ResourceEstimate(BaseModel):
    """Conservative resource placeholder used before real estimation is implemented."""

    cpus: int = 4
    memory_gb: int = 16
    walltime: str = "04:00:00"
    partition: str | None = None
    conservative_default: bool = True
