"""Common enums and models shared by runtime modules."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field


class TaskDomain(str, Enum):
    """Top-level task classes understood by the orchestrator."""

    BIOINFORMATICS = "bioinformatics"
    KNOWLEDGE = "knowledge"
    SYSTEM = "system"


class RiskLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MANUAL_APPROVAL = "manual_approval"


class GateDecision(str, Enum):
    PASS = "pass"
    REQUIRE_CONFIRMATION = "require_confirmation"
    BLOCK = "block"


class BreakerState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class SchedulerKind(str, Enum):
    SLURM = "slurm"
    PBS = "pbs"


class JobState(str, Enum):
    DRAFT = "draft"
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    UNKNOWN = "unknown"


class GateStatus(str, Enum):
    NOT_READY = "not_ready"
    DESIGN_PASS = "design_pass"
    IMPLEMENTATION_READY = "implementation_ready"
    TEST_READY = "test_ready"
    RELEASE_READY = "release_ready"


class RoleOutputHeader(BaseModel):
    """Common handoff header enforced across the role system."""

    role: str
    task_id: str
    run_id: str
    scope_in: list[str] = Field(default_factory=list)
    scope_out: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    next_actions: list[str] = Field(default_factory=list)
    ready_for_gate: GateStatus = GateStatus.NOT_READY
