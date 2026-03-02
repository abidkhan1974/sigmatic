"""Tests for the /v1/health endpoint."""

from fastapi.testclient import TestClient


def test_health_returns_200(client: TestClient) -> None:
    """Health endpoint should return 200 OK."""
    response = client.get("/v1/health")
    assert response.status_code == 200


def test_health_response_schema(client: TestClient) -> None:
    """Health response should contain required fields."""
    response = client.get("/v1/health")
    data = response.json()
    assert "status" in data
    assert "database" in data
    assert "redis" in data
    assert "version" in data
    assert data["status"] == "healthy"
    assert data["version"] == "0.1.0"


def test_health_has_version(client: TestClient) -> None:
    """Health endpoint should report version 0.1.0."""
    response = client.get("/v1/health")
    assert response.json()["version"] == "0.1.0"
