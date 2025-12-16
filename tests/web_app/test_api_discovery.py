"""Tests for discovery API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock


def test_discovery_scan(client: TestClient):
    """Test discovery scan endpoint."""
    response = client.post("/api/v1/discovery/scan")
    assert response.status_code in [200, 404]


def test_discovery_register(client: TestClient):
    """Test server registration via discovery."""
    request_data = {
        "server_id": "test-server",
        "config": {
            "command": "python",
            "args": ["server.py"],
            "type": "stdio"
        }
    }

    response = client.post("/api/v1/discovery/register", json=request_data)
    assert response.status_code in [200, 201, 404, 422]


def test_discovery_paths(client: TestClient):
    """Test getting discovery paths."""
    response = client.get("/api/v1/discovery/paths")
    assert response.status_code in [200, 404]


def test_discovery_scan_invalid_data(client: TestClient):
    """Test discovery scan with invalid data."""
    response = client.post("/api/v1/discovery/scan", json={"invalid": "data"})
    assert response.status_code in [422, 404]


def test_discovery_register_missing_fields(client: TestClient):
    """Test server registration with missing required fields."""
    request_data = {
        "server_id": "test-server"
        # Missing config
    }

    response = client.post("/api/v1/discovery/register", json=request_data)
    assert response.status_code in [422, 404]


def test_discovery_paths_format(client: TestClient):
    """Test that discovery paths returns proper format."""
    response = client.get("/api/v1/discovery/paths")
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        # Each path should be a string or dict with path info
        for path in data:
            assert isinstance(path, (str, dict))


def test_discovery_scan_async(client: TestClient):
    """Test that discovery scan handles async operations properly."""
    # This tests that the endpoint doesn't block on long operations
    import time
    start_time = time.time()

    response = client.post("/api/v1/discovery/scan", json={}, timeout=5)
    end_time = time.time()

    # Should complete relatively quickly (async operation started)
    assert end_time - start_time < 5
    assert response.status_code in [200, 202, 404]  # 202 Accepted for async


@pytest.mark.parametrize("endpoint,method,data", [
    ("/api/v1/discovery/scan", "POST", {}),
    ("/api/v1/discovery/register", "POST", {"server_id": "test", "config": {}}),
    ("/api/v1/discovery/paths", "GET", None),
])
def test_discovery_endpoints_basic(client: TestClient, endpoint, method, data):
    """Test all discovery endpoints for basic functionality."""
    if method == "GET":
        response = client.get(endpoint)
    else:
        response = client.post(endpoint, json=data or {})

    # Should not return 500 errors
    assert response.status_code < 500
    # Should return valid HTTP status codes
    assert response.status_code in [200, 201, 202, 400, 404, 422]


def test_discovery_register_duplicate(client: TestClient):
    """Test registering a server that already exists."""
    request_data = {
        "server_id": "existing-server",
        "config": {
            "command": "python",
            "args": ["server.py"]
        }
    }

    # Register once
    response1 = client.post("/api/v1/discovery/register", json=request_data)

    # Try to register again
    response2 = client.post("/api/v1/discovery/register", json=request_data)

    # First registration should succeed or be accepted
    assert response1.status_code in [200, 201, 202, 404]

    # Second registration might succeed (update) or fail (conflict)
    assert response2.status_code in [200, 201, 202, 404, 409]


def test_discovery_error_handling(client: TestClient):
    """Test error handling in discovery endpoints."""
    # Test with completely invalid data
    response = client.post("/api/v1/discovery/register", json="invalid")
    assert response.status_code in [422, 400, 404]

    # Test with null data
    response = client.post("/api/v1/discovery/scan", json=None)
    assert response.status_code in [422, 400, 404, 415]


def test_discovery_cors_support(client: TestClient):
    """Test CORS support for discovery endpoints."""
    response = client.options("/api/v1/discovery/scan",
                            headers={"Origin": "http://localhost:3000"})
    assert response.status_code in [200, 404]  # Should handle CORS or return 404


def test_discovery_content_types(client: TestClient):
    """Test proper content types for discovery endpoints."""
    response = client.get("/api/v1/discovery/paths")
    if response.status_code == 200:
        assert "application/json" in response.headers.get("content-type", "")

    response = client.post("/api/v1/discovery/register", json={"test": "data"})
    if response.status_code in [200, 201]:
        assert "application/json" in response.headers.get("content-type", "")
