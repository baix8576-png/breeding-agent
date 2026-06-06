"""Local durable run-state storage for trusted remote execution."""

from __future__ import annotations

import json
from pathlib import Path

from contracts.remote_execution import RunState


class RunStateStore:
    """Persist run state under local .geneagent/runs, never remote work roots."""

    def __init__(self, root: str | Path = ".geneagent") -> None:
        self.root = Path(root)

    def state_path(self, *, task_id: str, run_id: str) -> Path:
        return self.root / "runs" / task_id / run_id / "state.json"

    def save(self, state: RunState) -> Path:
        path = self.state_path(task_id=state.task_id, run_id=state.run_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = state.model_copy(update={"state_path": str(path)}).model_dump(mode="json")
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return path

    def load(self, *, task_id: str, run_id: str) -> RunState | None:
        path = self.state_path(task_id=task_id, run_id=run_id)
        if not path.exists():
            return None
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        return RunState.model_validate(payload)
