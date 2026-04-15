from safety.circuit_breaker import CircuitBreaker


def test_circuit_breaker_state_transitions() -> None:
    breaker = CircuitBreaker()

    assert breaker.state.value == "closed"
    assert breaker.allows_automatic_submission() is True

    breaker.trip()
    assert breaker.state.value == "open"
    assert breaker.allows_automatic_submission() is False

    breaker.allow_half_open_retry()
    assert breaker.state.value == "half_open"

    breaker.reset()
    assert breaker.state.value == "closed"
