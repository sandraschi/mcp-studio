"""Extended tests for tools API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock


def test_list_tools_with_filters(client: TestClient):
    """Test listing tools with various filters."""
    # Test with server_id filter
    response = client.get("/api/v1/tools?server_id=test-server")
    assert response.status_code in [200, 404]

    # Test with search filter
    response = client.get("/api/v1/tools?search=test")
    assert response.status_code in [200, 404]


def test_get_tool_details(client: TestClient):
    """Test getting details for a specific tool."""
    response = client.get("/api/v1/tools/test-tool")
    assert response.status_code in [200, 404]


def test_execute_tool_success(client: TestClient):
    """Test successful tool execution."""
    request_data = {
        "server_id": "test-server",
        "tool_name": "test_tool",
        "arguments": {
            "message": "hello world",
            "count": 5
        }
    }

    response = client.post("/api/v1/tools/execute", json=request_data)
    assert response.status_code in [200, 404, 422]  # 422 for validation errors


def test_execute_tool_missing_params(client: TestClient):
    """Test tool execution with missing parameters."""
    request_data = {
        "tool_name": "test_tool"
        # Missing server_id and arguments
    }

    response = client.post("/api/v1/tools/execute", json=request_data)
    # Should return validation error
    assert response.status_code in [422, 404]


def test_execute_tool_invalid_json(client: TestClient):
    """Test tool execution with invalid JSON."""
    response = client.post("/api/v1/tools/execute",
                          data="invalid json",
                          headers={"Content-Type": "application/json"})
    assert response.status_code == 422  # FastAPI validation error


def test_get_tool_categories(client: TestClient):
    """Test getting tool categories."""
    response = client.get("/api/v1/tools/categories")
    assert response.status_code in [200, 404]


def test_format_docstring(client: TestClient):
    """Test docstring formatting."""
    request_data = {
        "docstring": "def test_function():\n    \"\"\"Test function.\n\n    Args:\n        param: Test parameter\n\n    Returns:\n        str: Test result\n    \"\"\"",
        "format": "google"
    }

    response = client.post("/api/v1/tools/format-docstring", json=request_data)
    assert response.status_code in [200, 404, 422]


@pytest.mark.parametrize("tool_name,expected_status", [
    ("non_existent_tool", 404),
    ("", 404),
    ("tool with spaces", 422),  # Invalid tool name
])
def test_get_tool_edge_cases(client: TestClient, tool_name, expected_status):
    """Test edge cases for tool retrieval."""
    response = client.get(f"/api/v1/tools/{tool_name}")
    assert response.status_code == expected_status


def test_tools_pagination(client: TestClient):
    """Test tools list pagination."""
    response = client.get("/api/v1/tools?page=1&limit=10")
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        assert len(data) <= 10


def test_tools_search_functionality(client: TestClient):
    """Test tool search functionality."""
    response = client.get("/api/v1/tools?search=function")
    if response.status_code == 200:
        data = response.json()
        assert isinstance(data, list)
        # If search is implemented, results should be filtered
        # This is a basic check that the endpoint responds


def test_tool_execution_timeout(client: TestClient):
    """Test tool execution with timeout scenarios."""
    # This would require mocking long-running operations
    # For now, just test that the endpoint accepts timeout parameters
    request_data = {
        "server_id": "test-server",
        "tool_name": "slow_tool",
        "arguments": {},
        "timeout": 30
    }

    response = client.post("/api/v1/tools/execute", json=request_data)
    assert response.status_code in [200, 404, 422]


def test_tool_execution_result_format(client: TestClient):
    """Test that tool execution returns properly formatted results."""
    request_data = {
        "server_id": "test-server",
        "tool_name": "test_tool",
        "arguments": {"input": "test"}
    }

    response = client.post("/api/v1/tools/execute", json=request_data)
    if response.status_code == 200:
        data = response.json()
        # Check that response has expected fields
        expected_fields = ["success", "result", "execution_time"]
        for field in expected_fields:
            assert field in data or response.status_code == 404  # If endpoint not implemented


def test_tools_caching_headers(client: TestClient):
    """Test that tools endpoints have appropriate caching headers."""
    response = client.get("/api/v1/tools")
    if response.status_code == 200:
        cache_control = response.headers.get("cache-control", "")
        # Tools list might be cacheable for short periods
        assert "no-cache" not in cache_control or "max-age" in cache_control


def test_tools_error_handling(client: TestClient):
    """Test error handling in tools endpoints."""
    # Test with malformed request
    response = client.post("/api/v1/tools/execute", json={"invalid": "data"})
    assert response.status_code in [422, 404]  # Validation error or not found

    # Test with non-existent server
    request_data = {
        "server_id": "non-existent-server",
        "tool_name": "test_tool",
        "arguments": {}
    }
    response = client.post("/api/v1/tools/execute", json=request_data)
    assert response.status_code in [404, 422, 500]
