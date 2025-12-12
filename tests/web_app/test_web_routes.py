"""Tests for web interface routes."""

import pytest
from fastapi.testclient import TestClient
from pathlib import Path


def test_root_route(client: TestClient):
    """Test the root route returns dashboard."""
    response = client.get("/")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    # Should contain MCP Studio title
    assert "MCP Studio" in response.text or "mcp-studio" in response.text.lower()


def test_dashboard_route(client: TestClient):
    """Test the dashboard route."""
    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_servers_list_route(client: TestClient, mock_server_service):
    """Test the servers list web page."""
    mock_server_service.get_servers.return_value = {}
    
    response = client.get("/servers")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_servers_list_with_filter(client: TestClient, mock_server_service):
    """Test servers list with status filter."""
    mock_server_service.get_servers.return_value = {}
    
    response = client.get("/servers?status=online")
    assert response.status_code == 200


def test_servers_list_with_search(client: TestClient, mock_server_service):
    """Test servers list with search query."""
    mock_server_service.get_servers.return_value = {}
    
    response = client.get("/servers?search=test")
    assert response.status_code == 200


def test_server_detail_route_not_found(client: TestClient, mock_server_service):
    """Test server detail page for non-existent server."""
    mock_server_service.get_server.return_value = None
    
    response = client.get("/servers/non-existent")
    assert response.status_code == 404


def test_tools_list_route(client: TestClient):
    """Test the tools list web page."""
    response = client.get("/tools")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_tools_execute_route(client: TestClient):
    """Test the tool execution web page."""
    response = client.get("/tools/execute")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_clients_list_route(client: TestClient, mock_config_service):
    """Test the clients list web page."""
    mock_config_service.get_clients.return_value = []
    
    response = client.get("/clients")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]





