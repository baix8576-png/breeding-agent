"""Audit stores for traceability and reproducibility."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    """Audit record kept for reproducibility and accountability."""

    task_id: str
    run_id: str
    event_type: str
    summary: str
    metadata: dict[str, object] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class InMemoryAuditStore:
    """Temporary in-memory audit log used during early development."""

    def __init__(self) -> None:
        self._events: list[AuditEvent] = []

    def append(self, event: AuditEvent) -> None:
        self._events.append(event)

    def list_events(self) -> list[AuditEvent]:
        return list(self._events)


class FileAuditStore:
    """Append audit events to JSONL files while preserving in-memory snapshots."""

    def __init__(
        self,
        *,
        fallback_root: str | None = None,
        memory_store: InMemoryAuditStore | None = None,
    ) -> None:
        self._fallback_root = fallback_root or str(Path.cwd() / ".tmp" / "audit")
        self._memory_store = memory_store or InMemoryAuditStore()
        self._run_file_map: dict[tuple[str, str], str] = {}

    def append(self, event: AuditEvent, *, working_directory: str | None = None) -> str | None:
        """Persist one event to a task/run JSONL file and return the file path when successful."""

        self._memory_store.append(event)
        payload = event.model_dump(mode="json")
        for root in self._candidate_roots(working_directory):
            file_path = root / event.task_id / f"{event.run_id}.jsonl"
            try:
                file_path.parent.mkdir(parents=True, exist_ok=True)
                with file_path.open("a", encoding="utf-8") as handle:
                    handle.write(json.dumps(payload, ensure_ascii=False) + "\n")
            except OSError:
                continue
            resolved = str(file_path)
            self._run_file_map[(event.task_id, event.run_id)] = resolved
            return resolved
        return None

    def list_events(self) -> list[AuditEvent]:
        return self._memory_store.list_events()

    def resolve_run_file(self, task_id: str, run_id: str) -> str | None:
        return self._run_file_map.get((task_id, run_id))

    def _candidate_roots(self, working_directory: str | None) -> list[Path]:
        roots: list[Path] = []
        if working_directory:
            roots.append(Path(working_directory) / ".geneagent" / "audit")
        roots.append(Path(self._fallback_root))
        dedup: list[Path] = []
        seen: set[str] = set()
        for root in roots:
            key = str(root)
            if key in seen:
                continue
            seen.add(key)
            dedup.append(root)
        return dedup
