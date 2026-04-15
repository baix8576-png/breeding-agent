"""In-memory stores used until persistent storage is introduced."""

from __future__ import annotations

from pydantic import BaseModel, Field

from contracts.common import TaskDomain


class SessionRecord(BaseModel):
    """Short-term conversation state."""

    session_id: str
    messages: list[str] = Field(default_factory=list)
    last_task_id: str | None = None
    active_domain: TaskDomain | None = None


class StageSnapshot(BaseModel):
    """Planned or completed stage state stored for later handoff."""

    stage_id: str
    owner: str
    status: str = "planned"
    outputs: list[str] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)


class WorkflowHandoff(BaseModel):
    """Context passed from one workflow stage to the next."""

    task_id: str
    run_id: str
    from_stage: str
    to_stage: str
    summary: str
    carried_context: list[str] = Field(default_factory=list)
    open_questions: list[str] = Field(default_factory=list)


class RunRecord(BaseModel):
    """Single execution trace stored by the worker runtime."""

    run_id: str
    task_id: str
    input_summary: str
    job_ids: list[str] = Field(default_factory=list)
    domain: TaskDomain | None = None
    request_text: str = ""
    available_tools: list[str] = Field(default_factory=list)
    retrieval_sources: list[str] = Field(default_factory=list)
    stage_history: list[StageSnapshot] = Field(default_factory=list)
    handoffs: list[WorkflowHandoff] = Field(default_factory=list)


class InMemorySessionStore:
    """Simple in-process store for session context."""

    def __init__(self) -> None:
        self._items: dict[str, SessionRecord] = {}

    def save(self, record: SessionRecord) -> None:
        self._items[record.session_id] = record

    def get(self, session_id: str) -> SessionRecord | None:
        return self._items.get(session_id)


class InMemoryRunStore:
    """Simple in-process store for run context."""

    def __init__(self) -> None:
        self._items: dict[str, RunRecord] = {}

    def save(self, record: RunRecord) -> None:
        self._items[record.run_id] = record

    def get(self, run_id: str) -> RunRecord | None:
        return self._items.get(run_id)


class MemoryCoordinator:
    """Create deterministic run records and stage handoff placeholders."""

    def __init__(
        self,
        session_store: InMemorySessionStore | None = None,
        run_store: InMemoryRunStore | None = None,
    ) -> None:
        self._session_store = session_store or InMemorySessionStore()
        self._run_store = run_store or InMemoryRunStore()

    def plan_run(
        self,
        *,
        task_id: str,
        run_id: str,
        request_text: str,
        domain: TaskDomain,
        stage_specs: list[dict[str, object]],
        available_tools: list[str],
        retrieval_sources: list[str],
    ) -> RunRecord:
        """Persist a deterministic run plan and return the resulting record."""

        stage_history = [
            StageSnapshot(
                stage_id=str(stage["stage_id"]),
                owner=str(stage["owner"]),
                outputs=list(stage.get("outputs", [])),
                notes=list(stage.get("notes", [])),
            )
            for stage in stage_specs
        ]

        handoffs: list[WorkflowHandoff] = []
        for index in range(len(stage_history) - 1):
            current_stage = stage_history[index]
            next_stage = stage_history[index + 1]
            handoffs.append(
                WorkflowHandoff(
                    task_id=task_id,
                    run_id=run_id,
                    from_stage=current_stage.stage_id,
                    to_stage=next_stage.stage_id,
                    summary=(
                        f"Carry outputs from {current_stage.stage_id} to {next_stage.stage_id} "
                        "without recomputing previous stage decisions."
                    ),
                    carried_context=[
                        f"owner={current_stage.owner}",
                        f"outputs={','.join(current_stage.outputs) if current_stage.outputs else 'none'}",
                    ],
                    open_questions=[
                        "Replace this placeholder with runtime observations after tool execution is wired in."
                    ],
                )
            )

        record = RunRecord(
            run_id=run_id,
            task_id=task_id,
            input_summary=request_text[:160],
            domain=domain,
            request_text=request_text,
            available_tools=available_tools,
            retrieval_sources=retrieval_sources,
            stage_history=stage_history,
            handoffs=handoffs,
        )
        self._run_store.save(record)
        return record
