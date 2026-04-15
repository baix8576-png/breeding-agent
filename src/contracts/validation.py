"""Validation result contracts shared across pipeline, API, and tests."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ValidationIssue(BaseModel):
    """Issue returned by local input validation."""

    code: str
    message: str
    path: str | None = None


class ValidationReport(BaseModel):
    """Structured validation summary used by planning and submission flows."""

    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
