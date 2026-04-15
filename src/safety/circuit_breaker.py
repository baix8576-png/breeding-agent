"""Three-state circuit breaker used to protect unsafe automation."""

from __future__ import annotations

from collections import deque
from datetime import datetime, timezone

from pydantic import BaseModel, Field

from contracts.common import BreakerState


class CircuitBreakerEvent(BaseModel):
    """Breaker transition or advisory record for audit and polling."""

    task_id: str = "unknown-task"
    run_id: str = "unknown-run"
    event_type: str
    from_state: BreakerState
    to_state: BreakerState
    reason: str
    suggestions: list[str] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class CircuitBreakerSnapshot(BaseModel):
    state: BreakerState
    task_id: str = "unknown-task"
    run_id: str = "unknown-run"
    allows_automatic_submission: bool
    event_count: int
    last_reason: str | None = None
    suggestions: list[str] = Field(default_factory=list)


class CircuitBreaker:
    """Closed -> Open -> Half-Open state machine with event history."""

    def __init__(self, max_events: int = 50) -> None:
        self._state = BreakerState.CLOSED
        self._events: deque[CircuitBreakerEvent] = deque(maxlen=max_events)

    @property
    def state(self) -> BreakerState:
        """Return the current breaker state."""

        return self._state

    @property
    def events(self) -> list[CircuitBreakerEvent]:
        """Return chronological breaker events."""

        return list(self._events)

    @property
    def last_event(self) -> CircuitBreakerEvent | None:
        """Return the latest breaker event if any."""

        return self._events[-1] if self._events else None

    def trip(
        self,
        reason: str = "unsafe_condition_detected",
        *,
        task_id: str = "unknown-task",
        run_id: str = "unknown-run",
        suggestions: list[str] | None = None,
    ) -> BreakerState:
        """Open the breaker and stop automatic submission."""

        self._record("trip", BreakerState.OPEN, reason, task_id, run_id, suggestions)
        return self._state

    def allow_half_open_retry(
        self,
        reason: str = "manual_confirmation_received",
        *,
        task_id: str = "unknown-task",
        run_id: str = "unknown-run",
        suggestions: list[str] | None = None,
    ) -> BreakerState:
        """Move into a small-scope retry state after human confirmation."""

        self._record("half_open", BreakerState.HALF_OPEN, reason, task_id, run_id, suggestions)
        return self._state

    def reset(
        self,
        reason: str = "checks_passed",
        *,
        task_id: str = "unknown-task",
        run_id: str = "unknown-run",
        suggestions: list[str] | None = None,
    ) -> BreakerState:
        """Return the breaker to normal automatic execution."""

        self._record("reset", BreakerState.CLOSED, reason, task_id, run_id, suggestions)
        return self._state

    def record_advice(
        self,
        reason: str,
        *,
        task_id: str = "unknown-task",
        run_id: str = "unknown-run",
        suggestions: list[str] | None = None,
    ) -> CircuitBreakerEvent:
        """Record a non-transition advisory event."""

        event = CircuitBreakerEvent(
            task_id=task_id,
            run_id=run_id,
            event_type="advice",
            from_state=self._state,
            to_state=self._state,
            reason=reason,
            suggestions=suggestions or self.recommended_next_actions(),
        )
        self._events.append(event)
        return event

    def allows_automatic_submission(self) -> bool:
        """Whether the current state still permits automated submission."""

        return self._state != BreakerState.OPEN

    def recommended_next_actions(self) -> list[str]:
        """Return state-based guidance without taking any unsafe action."""

        if self._state == BreakerState.OPEN:
            return [
                "Stop automatic submission.",
                "Review the failed preflight checks and require operator confirmation.",
                "Retry only in half-open mode with reduced scope.",
            ]
        if self._state == BreakerState.HALF_OPEN:
            return [
                "Limit execution to a dry-run or small sample subset.",
                "Return to closed only after the retry succeeds.",
            ]
        return [
            "Continue with preflight checks enabled.",
            "Trip the breaker immediately on repeated gate failures.",
        ]

    def status_snapshot(
        self,
        *,
        task_id: str = "unknown-task",
        run_id: str = "unknown-run",
    ) -> CircuitBreakerSnapshot:
        """Return a compact status snapshot for orchestrators or pollers."""

        return CircuitBreakerSnapshot(
            state=self._state,
            task_id=task_id,
            run_id=run_id,
            allows_automatic_submission=self.allows_automatic_submission(),
            event_count=len(self._events),
            last_reason=self.last_event.reason if self.last_event else None,
            suggestions=self.recommended_next_actions(),
        )

    def _record(
        self,
        event_type: str,
        target_state: BreakerState,
        reason: str,
        task_id: str,
        run_id: str,
        suggestions: list[str] | None,
    ) -> None:
        event = CircuitBreakerEvent(
            task_id=task_id,
            run_id=run_id,
            event_type=event_type,
            from_state=self._state,
            to_state=target_state,
            reason=reason,
            suggestions=suggestions or self.recommended_next_actions(),
        )
        self._state = target_state
        self._events.append(event)
