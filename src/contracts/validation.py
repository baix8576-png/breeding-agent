"""Validation result contracts shared across pipeline, API, and tests."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class ValidationSeverity(str, Enum):
    """Severity levels used by validation issues and contract payloads."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ConsistencyStatus(str, Enum):
    """Consistency-check status values for normalized input bundles."""

    PASS = "pass"
    WARN = "warn"
    FAIL = "fail"


class InputBundleEntry(BaseModel):
    """Stable input entry contract carried from entry points into the pipeline layer."""

    role: str
    path: str
    data_type: str | None = None
    required: bool = True
    description: str | None = None
    original_path: str | None = None
    normalized_path: str | None = None


class InputBundle(BaseModel):
    """Structured bundle of local inputs used by plan/dry-run/submit flows."""

    task_id: str | None = None
    run_id: str | None = None
    species: str | None = None
    cohort_name: str | None = None
    entries: list[InputBundleEntry] = Field(default_factory=list)


class NormalizedInputEntry(BaseModel):
    """Normalized entry rendered after InputBundle path and role normalization."""

    role: str
    original_path: str
    normalized_path: str
    data_type: str | None = None
    required: bool = True
    exists: bool = False


class ConsistencyCheck(BaseModel):
    """Structured consistency check output across genotype and metadata bundles."""

    check_id: str
    status: ConsistencyStatus
    message: str
    related_roles: list[str] = Field(default_factory=list)
    related_paths: list[str] = Field(default_factory=list)


class ValidationIssue(BaseModel):
    """Issue returned by local input validation."""

    code: str
    message: str
    path: str | None = None
    severity: ValidationSeverity = ValidationSeverity.ERROR
    blocking: bool = True
    hint: str | None = None


class ValidationReport(BaseModel):
    """Structured validation summary used by planning and submission flows."""

    valid: bool
    issues: list[ValidationIssue] = Field(default_factory=list)
    normalized_inputs: list[NormalizedInputEntry] = Field(default_factory=list)
    detected_types: list[str] = Field(default_factory=list)
    consistency_checks: list[ConsistencyCheck] = Field(default_factory=list)
    ready_for_gate: str | None = None
    recommended_next_actions: list[str] = Field(default_factory=list)
