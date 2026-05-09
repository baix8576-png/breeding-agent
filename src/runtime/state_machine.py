"""Runtime stage machine for bio and non-bio execution chains."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field

from contracts.common import TaskDomain


class RuntimePath(str, Enum):
    """Supported runtime paths in the current release."""

    BIO_MAIN_CHAIN = "bio_main_chain"
    NON_BIO_LIGHTWEIGHT = "non_bio_lightweight"


class RuntimeStage(str, Enum):
    """Stable stage ids mirrored from the project execution charter."""

    STAGE_01_INTAKE = "stage_01_intake"
    STAGE_02_INTENT_AND_SCOPE = "stage_02_intent_and_scope"
    STAGE_03_INPUT_VALIDATION = "stage_03_input_validation"
    STAGE_04_LOCAL_FIRST_RAG = "stage_04_local_first_rag"
    STAGE_05_BLUEPRINT_SELECTION = "stage_05_blueprint_selection"
    STAGE_06_RESOURCE_AND_SAFETY_GATE = "stage_06_resource_and_safety_gate"
    STAGE_07_EXECUTION = "stage_07_execution"
    STAGE_08_ARTIFACT_AND_REPORT = "stage_08_artifact_and_report"
    STAGE_09_AUDIT_AND_MEMORY = "stage_09_audit_and_memory"
    LITE_01_INTAKE = "lite_01_intake"
    LITE_02_LOCAL_RETRIEVAL = "lite_02_local_retrieval"
    LITE_03_ANSWER_BLUEPRINT = "lite_03_answer_blueprint"
    LITE_04_OPTIONAL_SAFETY_REVIEW = "lite_04_optional_safety_review"
    COMPLETED = "completed"


BIO_STAGE_CHAIN: list[str] = [
    RuntimeStage.STAGE_01_INTAKE.value,
    RuntimeStage.STAGE_02_INTENT_AND_SCOPE.value,
    RuntimeStage.STAGE_03_INPUT_VALIDATION.value,
    RuntimeStage.STAGE_04_LOCAL_FIRST_RAG.value,
    RuntimeStage.STAGE_05_BLUEPRINT_SELECTION.value,
    RuntimeStage.STAGE_06_RESOURCE_AND_SAFETY_GATE.value,
    RuntimeStage.STAGE_07_EXECUTION.value,
    RuntimeStage.STAGE_08_ARTIFACT_AND_REPORT.value,
    RuntimeStage.STAGE_09_AUDIT_AND_MEMORY.value,
    RuntimeStage.COMPLETED.value,
]

NON_BIO_STAGE_CHAIN: list[str] = [
    RuntimeStage.LITE_01_INTAKE.value,
    RuntimeStage.LITE_02_LOCAL_RETRIEVAL.value,
    RuntimeStage.LITE_03_ANSWER_BLUEPRINT.value,
    RuntimeStage.COMPLETED.value,
]


class RuntimeStageTrace(BaseModel):
    """Trace of runtime state transitions for one task/run."""

    task_id: str
    run_id: str
    domain: TaskDomain
    runtime_path: RuntimePath
    current_stage: str
    transitions: list[str] = Field(default_factory=list)

    @property
    def terminal(self) -> bool:
        return self.current_stage == RuntimeStage.COMPLETED.value

    @property
    def chain(self) -> list[str]:
        return BIO_STAGE_CHAIN if self.runtime_path == RuntimePath.BIO_MAIN_CHAIN else NON_BIO_STAGE_CHAIN

    def advance(self, next_stage: str) -> None:
        if next_stage not in self.chain:
            raise ValueError(f"Unknown stage '{next_stage}' for runtime path '{self.runtime_path.value}'.")
        if self.current_stage == next_stage:
            return
        current_index = self.chain.index(self.current_stage)
        next_index = self.chain.index(next_stage)
        if next_index < current_index:
            raise ValueError(
                f"Invalid runtime transition: cannot move backward from '{self.current_stage}' to '{next_stage}'."
            )
        if next_index > current_index + 1:
            raise ValueError(
                f"Invalid runtime transition: cannot skip stages from '{self.current_stage}' to '{next_stage}'."
            )
        self.transitions.append(f"{self.current_stage}->{next_stage}")
        self.current_stage = next_stage

    def advance_many(self, stages: list[str]) -> None:
        for stage in stages:
            self.advance(stage)

    def to_contract(self) -> dict[str, object]:
        return {
            "domain": self.domain.value,
            "runtime_path": self.runtime_path.value,
            "current_stage": self.current_stage,
            "transitions": list(self.transitions),
            "terminal": self.terminal,
        }


def create_stage_trace(*, task_id: str, run_id: str, domain: TaskDomain) -> RuntimeStageTrace:
    """Create an initialized runtime stage trace for a domain."""

    if domain == TaskDomain.BIOINFORMATICS:
        return RuntimeStageTrace(
            task_id=task_id,
            run_id=run_id,
            domain=domain,
            runtime_path=RuntimePath.BIO_MAIN_CHAIN,
            current_stage=RuntimeStage.STAGE_01_INTAKE.value,
        )
    return RuntimeStageTrace(
        task_id=task_id,
        run_id=run_id,
        domain=domain,
        runtime_path=RuntimePath.NON_BIO_LIGHTWEIGHT,
        current_stage=RuntimeStage.LITE_01_INTAKE.value,
    )


def progression_until_completed(domain: TaskDomain, *, include_optional_safety_review: bool = False) -> list[str]:
    """Return sequential stage progression from the second stage to completion."""

    if domain == TaskDomain.BIOINFORMATICS:
        return BIO_STAGE_CHAIN[1:]
    if include_optional_safety_review:
        return [
            RuntimeStage.LITE_02_LOCAL_RETRIEVAL.value,
            RuntimeStage.LITE_03_ANSWER_BLUEPRINT.value,
            RuntimeStage.LITE_04_OPTIONAL_SAFETY_REVIEW.value,
            RuntimeStage.COMPLETED.value,
        ]
    return NON_BIO_STAGE_CHAIN[1:]

