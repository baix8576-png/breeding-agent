"""Dependency wiring for the first runnable GeneAgent skeleton."""

from __future__ import annotations

from dataclasses import dataclass

from contracts.common import SchedulerKind
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
    facade: ApplicationFacade


def create_application_context(settings: Settings | None = None) -> ApplicationContext:
    """Create a light-weight service container for the current process."""

    settings = settings or get_settings()
    scheduler = _build_scheduler(settings.scheduler_type)
    safety_gate = SafetyGateService()
    circuit_breaker = CircuitBreaker()
    input_validator = InputValidator()
    resource_estimator = ConservativeResourceEstimator(default_partition=None)
    orchestrator = OrchestratorService(
        resource_estimator=resource_estimator,
        safety_gate=safety_gate,
        circuit_breaker=circuit_breaker,
    )
    facade = ApplicationFacade(
        settings=settings,
        orchestrator=orchestrator,
        scheduler=scheduler,
        safety_gate=safety_gate,
        input_validator=input_validator,
    )
    return ApplicationContext(
        settings=settings,
        orchestrator=orchestrator,
        scheduler=scheduler,
        safety_gate=safety_gate,
        circuit_breaker=circuit_breaker,
        input_validator=input_validator,
        facade=facade,
    )


def _build_scheduler(kind: SchedulerKind) -> BaseSchedulerAdapter:
    """Build the scheduler adapter requested by configuration."""

    if kind == SchedulerKind.PBS:
        return PbsSchedulerAdapter()
    return SlurmSchedulerAdapter()
