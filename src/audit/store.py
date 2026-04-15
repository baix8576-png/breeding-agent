"""Audit store placeholders for traceability."""

from __future__ import annotations

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    """Audit record kept for reproducibility and accountability."""

    task_id: str
    run_id: str
    event_type: str
    summary: str
    metadata: dict[str, str] = Field(default_factory=dict)


class InMemoryAuditStore:
    """Temporary in-memory audit log used during early development."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self._events.append(event)

    def list_events(self) -> list[AuditEvent]:
        return list(self._events)
