"""Protocol-style interfaces used to stabilize the runtime facade."""

from __future__ import annotations

from typing import Protocol

from contracts.execution import JobHandle, SafetyReviewRequest, SafetyReviewResult, SubmissionSpec, TaskPlan
from contracts.tasks import UserRequest
from contracts.validation import ValidationReport


class OrchestratorPort(Protocol):
    """Capability needed from the orchestration layer."""

    def draft_plan(self, request: UserRequest, run_context) -> TaskPlan:
        """Create a structured draft plan for a normalized request."""


class InputValidationPort(Protocol):
    """Capability needed from the input validation layer."""

    def validate(self, paths: list[str]) -> ValidationReport:
        """Validate a list of local input paths."""


class SafetyGatePort(Protocol):
    """Capability needed from the safety review layer."""

    def review(self, review_request: SafetyReviewRequest) -> SafetyReviewResult:
        """Review a structured action request and return a gate decision."""


class SchedulerPort(Protocol):
    """Capability needed from the scheduler adapter."""

    def render_submission_script(self, spec: SubmissionSpec) -> str:
        """Render a scheduler script preview from a submission spec."""

    def dry_run_submit(self, spec: SubmissionSpec) -> JobHandle:
        """Return a synthetic job handle without touching the real scheduler."""
