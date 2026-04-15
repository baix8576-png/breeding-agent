"""API- and CLI-facing request envelopes shared across entry points."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RequestIdentity(BaseModel):
    """Optional caller-supplied identity fields normalized into a RunContext."""

    task_id: str | None = None
    run_id: str | None = None
    session_id: str | None = None
    working_directory: str | None = None


class DraftPlanRequest(BaseModel):
    """Payload for planning a natural-language request."""

    text: str
    requested_outputs: list[str] = Field(default_factory=list)
    identity: RequestIdentity = Field(default_factory=RequestIdentity)


class ValidateInputsRequest(BaseModel):
    """Payload for validating local inputs before planning or execution."""

    paths: list[str]
    identity: RequestIdentity = Field(default_factory=RequestIdentity)


class ReviewActionRequest(BaseModel):
    """Payload for reviewing a high-risk action."""

    action_name: str
    reason: str | None = None
    target_paths: list[str] = Field(default_factory=list)
    identity: RequestIdentity = Field(default_factory=RequestIdentity)


class DryRunRequest(BaseModel):
    """Payload for generating a scheduler dry-run preview."""

    request_text: str = "Prepare a dry-run submission"
    command: list[str] | None = None
    identity: RequestIdentity = Field(default_factory=RequestIdentity)
