from fastapi.testclient import TestClient

from api.app import create_app


def test_health_route_returns_runtime_metadata() -> None:
    client = TestClient(create_app())

    response = client.get("/health")

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "ok"
    assert payload["scheduler_type"] in {"slurm", "pbs"}
