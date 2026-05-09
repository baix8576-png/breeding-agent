from __future__ import annotations

import pytest

from contracts.common import TaskDomain
from runtime.state_machine import (
    BIO_STAGE_CHAIN,
    NON_BIO_STAGE_CHAIN,
    RuntimeStage,
    create_stage_trace,
    progression_until_completed,
)


def test_bio_stage_trace_advances_to_completion() -> None:
    trace = create_stage_trace(task_id="task-state-001", run_id="run-state-001", domain=TaskDomain.BIOINFORMATICS)
    trace.advance_many(progression_until_completed(TaskDomain.BIOINFORMATICS))

    assert trace.current_stage == RuntimeStage.COMPLETED.value
    assert trace.terminal is True
    assert trace.chain == BIO_STAGE_CHAIN
    assert len(trace.transitions) == len(BIO_STAGE_CHAIN) - 1


def test_non_bio_stage_trace_advances_to_completion() -> None:
    trace = create_stage_trace(task_id="task-state-002", run_id="run-state-002", domain=TaskDomain.KNOWLEDGE)
    trace.advance_many(progression_until_completed(TaskDomain.KNOWLEDGE))

    assert trace.current_stage == RuntimeStage.COMPLETED.value
    assert trace.terminal is True
    assert trace.chain == NON_BIO_STAGE_CHAIN


def test_stage_trace_rejects_skipped_transition() -> None:
    trace = create_stage_trace(task_id="task-state-003", run_id="run-state-003", domain=TaskDomain.BIOINFORMATICS)

    with pytest.raises(ValueError):
        trace.advance(RuntimeStage.STAGE_05_BLUEPRINT_SELECTION.value)

