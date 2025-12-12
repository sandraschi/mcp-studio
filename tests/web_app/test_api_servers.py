"""Tests for servers API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock


def test_list_servers_empty(client: TestClient, mock_server_service):
    """Test listing servers when none are configured."""
    mock_server_service.get_servers.return_value = {}
    
    response = client.get("/api/v1/servers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_servers_with_data(client: TestClient, mock_server_service):
    """Test listing servers with mock data."""
    from mcp_studio.app.models.mcp import MCPServer
    from mcp_studio.app.core.enums import ServerStatus, ServerType
    
    mock_server = MCPServer(
        id="test-server",
        name="Test Server",
        description="A test server",
        type=ServerType.STDIO,
        status=ServerStatus.OFFLINE,
        command="python",
        args=["test.py"]
    )
    
    mock_server_service.get_servers.return_value = {"test-server": mock_server}
    
    response = client.get("/api/v1/servers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "test-server"
    assert data[0]["name"] == "Test Server"


def test_get_server_not_found(client: TestClient, mock_server_service):
    """Test getting a non-existent server."""
    mock_server_service.get_server.return_value = None
    
    response = client.get("/api/v1/servers/non-existent")
    assert response.status_code == 404


def test_get_server_success(client: TestClient, mock_server_service):
    """Test getting an existing server."""
    from mcp_studio.app.models.mcp import MCPServer
    from mcp_studio.app.core.enums import ServerStatus, ServerType
    
    mock_server = MCPServer(
        id="test-server",
        name="Test Server",
        description="A test server",
        type=ServerType.STDIO,
        status=ServerStatus.OFFLINE,
        command="python",
        args=["test.py"]
    )
    
    mock_server_service.get_server.return_value = mock_server
    
    response = client.get("/api/v1/servers/test-server")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-server"
    assert data["name"] == "Test Server"


@pytest.mark.asyncio
async def test_get_server_tools(client: TestClient, mock_server_service):
    """Test getting tools for a server."""
    mock_server_service.get_server_tools = AsyncMock(return_value=[
        {"name": "test_tool", "description": "A test tool"}
    ])
    
    response = client.get("/api/v1/servers/test-server/tools")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["name"] == "test_tool"

