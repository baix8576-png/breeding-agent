from __future__ import annotations

from contracts.common import TaskDomain
from memory import InMemoryRunStore, InMemorySessionStore, MemoryCoordinator, SessionRecord


def test_session_store_round_trip() -> None:
    store = InMemorySessionStore()
    record = SessionRecord(session_id="session-001", messages=["hello"], last_task_id="task-001")

    store.save(record)
    loaded = store.get("session-001")

    assert loaded is not None
    assert loaded.session_id == "session-001"
    assert loaded.messages == ["hello"]
    assert loaded.last_task_id == "task-001"


def test_memory_coordinator_plan_run_persists_handoffs() -> None:
    run_store = InMemoryRunStore()
    coordinator = MemoryCoordinator(run_store=run_store)

    record = coordinator.plan_run(
        task_id="task-memory-001",
        run_id="run-memory-001",
        request_text="Draft a simple genetics workflow and preserve stage context.",
        domain=TaskDomain.BIOINFORMATICS,
        stage_specs=[
            {"stage_id": "stage_01_scope", "owner": "orchestrator", "outputs": ["scope_summary"]},
            {"stage_id": "stage_02_validate", "owner": "orchestrator", "outputs": ["validation_snapshot"]},
        ],
        available_tools=["input_validator"],
        retrieval_sources=["Input Compliance Checklist"],
    )

    loaded = run_store.get("run-memory-001")
    assert loaded is not None
    assert loaded.run_id == "run-memory-001"
    assert record.stage_history[0].stage_id == "stage_01_scope"
    assert record.stage_history[1].stage_id == "stage_02_validate"
    assert len(record.handoffs) == 1
    assert record.handoffs[0].from_stage == "stage_01_scope"
    assert record.handoffs[0].to_stage == "stage_02_validate"
