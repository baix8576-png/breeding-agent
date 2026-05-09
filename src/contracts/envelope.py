"""Unified request envelope contracts for plan/dry-run/submit runtime flows."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from contracts.api import RequestIdentity
from contracts.validation import InputBundle


class ExecutionIntent(str, Enum):
    """Normalized intent values used by runtime adapters."""

    PLAN = "plan"
    DRY_RUN = "dry_run"
    SUBMIT_PREVIEW = "submit_preview"
    SUBMIT = "submit"
    REPORT = "report"
    DIAGNOSTIC = "diagnostic"


class RuntimeRequestEnvelopeV2(BaseModel):
    """Single envelope used for runtime entry normalization."""

    schema_version: str = "request_envelope.v2"
    intent: ExecutionIntent
    request_text: str
    identity: RequestIdentity = Field(default_factory=RequestIdentity)
    working_directory: str | None = None
    input_bundle: InputBundle | None = None
    requested_outputs: list[str] = Field(default_factory=list)
    command: list[str] | None = None
    dry_run_completed: bool = False
    metadata: dict[str, object] = Field(default_factory=dict)

    def resolved_working_directory(self) -> str | None:
        return self.working_directory or self.identity.working_directory

