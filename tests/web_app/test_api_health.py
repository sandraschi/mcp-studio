"""Tests for health API endpoints."""

import pytest
from fastapi.testclient import TestClient


def test_health_endpoint(client: TestClient):
    """Test the health check endpoint."""
    # API router is mounted at /api, has prefix /v1, health router at /health
    # Full path: /api/v1/health/health
    response = client.get("/api/v1/health/health")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "ok"
    assert "version" in data


def test_health_status(client: TestClient):
    """Test the status endpoint."""
    response = client.get("/api/v1/health/status")
    assert response.status_code == 200
    data = response.json()
    assert "service" in data
    assert "system" in data
    assert "resources" in data
    assert data["service"]["name"] == "MCP Studio"


def test_health_live(client: TestClient):
    """Test the liveness probe endpoint."""
    response = client.get("/api/v1/health/health/live")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] == "alive"


def test_health_ready(client: TestClient):
    """Test the readiness probe endpoint."""
    response = client.get("/api/v1/health/health/ready")
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert data["status"] in ["ready", "not_ready"]
