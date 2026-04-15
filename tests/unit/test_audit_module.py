from __future__ import annotations

from audit import AuditEvent, InMemoryAuditStore


def test_audit_store_append_and_list() -> None:
    store = InMemoryAuditStore()

    store.append(
        AuditEvent(
            task_id="task-audit-001",
            run_id="run-audit-001",
            event_type="plan_drafted",
            summary="Draft plan created in dry-run mode.",
        )
    )

    events = store.list_events()
    assert len(events) == 1
    assert events[0].event_type == "plan_drafted"
    assert events[0].task_id == "task-audit-001"


def test_audit_store_list_returns_copy() -> None:
    store = InMemoryAuditStore()
    store.append(
        AuditEvent(
            task_id="task-audit-002",
            run_id="run-audit-002",
            event_type="gate_checked",
            summary="Safety gate was checked.",
        )
    )

    snapshot = store.list_events()
    snapshot.append(
        AuditEvent(
            task_id="task-audit-003",
            run_id="run-audit-003",
            event_type="external_mutation",
            summary="Should not change the internal store.",
        )
    )

    assert len(store.list_events()) == 1
