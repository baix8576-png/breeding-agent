"""Dependency wiring for the first runnable GeneAgent skeleton."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from audit.store import FileAuditStore
from contracts.common import SchedulerKind
from memory.stores import MemoryCoordinator
from orchestration.service import OrchestratorService
from pipeline.validators import InputValidator
from safety.circuit_breaker import CircuitBreaker
from safety.gates import SafetyGateService
from scheduler.base import BaseSchedulerAdapter
from scheduler.pbs import PbsSchedulerAdapter
from scheduler.resource_estimator import ConservativeResourceEstimator
from scheduler.slurm import SlurmSchedulerAdapter
from runtime.facade import ApplicationFacade
from runtime.settings import Settings, get_settings


@dataclass(slots=True)
class ApplicationContext:
    """Bundle of core services used by API and CLI entry points."""

    settings: Settings
    orchestrator: OrchestratorService
    scheduler: BaseSchedulerAdapter
    safety_gate: SafetyGateService
    circuit_breaker: CircuitBreaker
    input_validator: InputValidator
    memory_coordinator: MemoryCoordinator
    audit_store: FileAuditStore
    facade: ApplicationFacade


def create_application_context(settings: Settings | None = None) -> ApplicationContext:
    """Create a light-weight service container for the current process."""

    settings = settings or get_settings()
    scheduler = _build_scheduler(settings)
    safety_gate = SafetyGateService()
    circuit_breaker = CircuitBreaker()
    input_validator = InputValidator()
    memory_coordinator = MemoryCoordinator()
    audit_store = FileAuditStore(fallback_root=str(Path.cwd() / ".tmp" / "audit"))
    resource_estimator = ConservativeResourceEstimator(default_partition=None)
    orchestrator = OrchestratorService(
        resource_estimator=resource_estimator,
        safety_gate=safety_gate,
        circuit_breaker=circuit_breaker,
        memory_coordinator=memory_coordinator,
    )
    facade = ApplicationFacade(
        settings=settings,
        orchestrator=orchestrator,
        scheduler=scheduler,
        safety_gate=safety_gate,
        input_validator=input_validator,
        memory_coordinator=memory_coordinator,
        audit_store=audit_store,
    )
    return ApplicationContext(
        settings=settings,
        orchestrator=orchestrator,
        scheduler=scheduler,
        safety_gate=safety_gate,
        circuit_breaker=circuit_breaker,
        input_validator=input_validator,
        memory_coordinator=memory_coordinator,
        audit_store=audit_store,
        facade=facade,
    )


def _build_scheduler(settings: Settings) -> BaseSchedulerAdapter:
    """Build the scheduler adapter requested by configuration."""

    scheduler_kwargs = {
        "real_execution_enabled": settings.scheduler_real_execution_enabled,
        "retry_max_attempts": settings.scheduler_retry_max_attempts,
        "retry_backoff_seconds": settings.scheduler_retry_backoff_seconds,
        "command_timeout_seconds": settings.scheduler_command_timeout_seconds,
    }
    kind = settings.scheduler_type
    if kind == SchedulerKind.PBS:
        return PbsSchedulerAdapter(**scheduler_kwargs)
    return SlurmSchedulerAdapter(**scheduler_kwargs)
