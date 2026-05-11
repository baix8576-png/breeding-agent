"""Audit stores for traceability and reproducibility."""

from __future__ import annotations

from datetime import datetime, timezone
import json
from pathlib import Path

from pydantic import BaseModel, Field


class AuditEvent(BaseModel):
    """Audit record kept for reproducibility and accountability."""

    schema_version: str = "audit_event.v2"
    task_id: str
    run_id: str
    event_type: str
    stage_id: str | None = None
    summary: str
    metadata: dict[str, object] = Field(default_factory=dict)
    traceability: dict[str, object] = Field(default_factory=dict)
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
        self._fallback_root = fallback_root or str(Path.cwd() / "logs" / "audit")
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

    def resolve_run_file(
        self,
        task_id: str,
        run_id: str,
        *,
        working_directory: str | None = None,
    ) -> str | None:
        cached = self._run_file_map.get((task_id, run_id))
        if cached and Path(cached).is_file():
            return cached
        for root in self._candidate_roots(working_directory):
            candidate = root / task_id / f"{run_id}.jsonl"
            if candidate.is_file():
                resolved = str(candidate)
                self._run_file_map[(task_id, run_id)] = resolved
                return resolved
        return cached

    def find_run_file(
        self,
        *,
        run_id: str,
        task_id: str | None = None,
        working_directory: str | None = None,
    ) -> str | None:
        if task_id:
            resolved = self.resolve_run_file(
                task_id,
                run_id,
                working_directory=working_directory,
            )
            if resolved:
                return resolved
        newest: Path | None = None
        for root in self._candidate_roots(working_directory):
            if not root.exists():
                continue
            for candidate in root.rglob(f"{run_id}.jsonl"):
                if not candidate.is_file():
                    continue
                if task_id and candidate.parent.name != task_id:
                    continue
                if newest is None or candidate.stat().st_mtime > newest.stat().st_mtime:
                    newest = candidate
        if newest is None:
            return None
        resolved = str(newest)
        self._run_file_map[(newest.parent.name, run_id)] = resolved
        return resolved

    def read_run_events(
        self,
        *,
        run_id: str,
        task_id: str | None = None,
        working_directory: str | None = None,
    ) -> tuple[list[AuditEvent], str | None]:
        file_path = self.find_run_file(
            run_id=run_id,
            task_id=task_id,
            working_directory=working_directory,
        )
        if file_path is None:
            return ([], None)
        events: list[AuditEvent] = []
        try:
            lines = Path(file_path).read_text(encoding="utf-8").splitlines()
        except OSError:
            return (events, file_path)
        for line in lines:
            raw = line.strip()
            if not raw:
                continue
            try:
                payload = json.loads(raw)
                events.append(AuditEvent.model_validate(payload))
            except Exception:
                continue
        return (events, file_path)

    def list_recent_runs(
        self,
        *,
        working_directory: str | None = None,
        limit: int = 20,
    ) -> list[dict[str, object]]:
        run_files: list[Path] = []
        seen: set[str] = set()
        for root in self._candidate_roots(working_directory):
            if not root.exists():
                continue
            for candidate in root.rglob("*.jsonl"):
                if not candidate.is_file():
                    continue
                key = str(candidate.resolve())
                if key in seen:
                    continue
                seen.add(key)
                run_files.append(candidate)
        run_files.sort(key=lambda item: item.stat().st_mtime, reverse=True)
        snapshots: list[dict[str, object]] = []
        for candidate in run_files:
            try:
                lines = candidate.read_text(encoding="utf-8").splitlines()
            except OSError:
                continue
            if not lines:
                continue
            latest: dict[str, object] | None = None
            for raw in reversed(lines):
                line = raw.strip()
                if not line:
                    continue
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(payload, dict):
                    latest = payload
                    break
            if latest is None:
                continue
            metadata = latest.get("metadata", {})
            if not isinstance(metadata, dict):
                metadata = {}
            runtime_lifecycle = metadata.get("runtime_lifecycle", {})
            if not isinstance(runtime_lifecycle, dict):
                runtime_lifecycle = {}
            artifact_index = metadata.get("artifact_index", {})
            if not isinstance(artifact_index, dict):
                artifact_index = {}
            report_paths = artifact_index.get("reports", [])
            if not isinstance(report_paths, list):
                report_paths = []
            snapshots.append(
                {
                    "task_id": str(latest.get("task_id", candidate.parent.name)),
                    "run_id": str(latest.get("run_id", candidate.stem)),
                    "event_type": str(latest.get("event_type", "")),
                    "stage_id": latest.get("stage_id"),
                    "created_at": latest.get("created_at"),
                    "summary": latest.get("summary"),
                    "job_id": metadata.get("job_id"),
                    "report_summary": metadata.get("report_summary"),
                    "runtime_stage": runtime_lifecycle.get("current_stage"),
                    "runtime_path": runtime_lifecycle.get("runtime_path"),
                    "report_paths": report_paths,
                    "audit_path": str(candidate),
                }
            )
            if len(snapshots) >= max(1, limit):
                break
        return snapshots

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
