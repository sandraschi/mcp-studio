"""Tests for tools API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock


@pytest.mark.asyncio
async def test_list_tools_empty(client: TestClient, mock_server_service):
    """Test listing tools when no servers have tools."""
    mock_server_service.get_servers.return_value = {}
    mock_server_service.get_server_tools = AsyncMock(return_value=[])
    
    response = client.get("/api/v1/tools")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


@pytest.mark.asyncio
async def test_list_tools_with_filter(client: TestClient, mock_server_service):
    """Test listing tools with server_id filter."""
    from mcp_studio.app.models.mcp import MCPServer
    from mcp_studio.app.core.enums import ServerStatus, ServerType
    
    mock_server = MCPServer(
        id="test-server",
        name="Test Server",
        type=ServerType.STDIO,
        status=ServerStatus.OFFLINE,
        command="python",
        args=["test.py"]
    )
    
    mock_server_service.get_servers.return_value = {"test-server": mock_server}
    mock_server_service.get_server_tools = AsyncMock(return_value=[
        {"name": "test_tool", "description": "A test tool"}
    ])
    
    response = client.get("/api/v1/tools?server_id=test-server")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


@pytest.mark.asyncio
async def test_list_tools_with_search(client: TestClient, mock_server_service):
    """Test listing tools with search filter."""
    from mcp_studio.app.models.mcp import MCPServer
    from mcp_studio.app.core.enums import ServerStatus, ServerType
    
    mock_server = MCPServer(
        id="test-server",
        name="Test Server",
        type=ServerType.STDIO,
        status=ServerStatus.OFFLINE,
        command="python",
        args=["test.py"]
    )
    
    mock_server_service.get_servers.return_value = {"test-server": mock_server}
    mock_server_service.get_server_tools = AsyncMock(return_value=[
        {"name": "test_tool", "description": "A test tool for searching"}
    ])
    
    response = client.get("/api/v1/tools?search=test")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_tool_by_name_not_found(client: TestClient, mock_server_service):
    """Test getting a tool that doesn't exist."""
    mock_server_service.get_servers.return_value = {}
    mock_server_service.get_server_tools = AsyncMock(return_value=[])
    
    response = client.get("/api/v1/tools/non-existent-tool")
    assert response.status_code == 404


def test_list_categories(client: TestClient, mock_server_service):
    """Test listing tool categories."""
    from mcp_studio.app.models.mcp import MCPServer
    from mcp_studio.app.core.enums import ServerStatus, ServerType
    
    mock_server = MCPServer(
        id="test-server",
        name="Test Server",
        type=ServerType.STDIO,
        status=ServerStatus.OFFLINE,
        command="python",
        args=["test.py"]
    )
    
    mock_server_service.get_servers.return_value = {"test-server": mock_server}
    mock_server_service.get_server_tools = AsyncMock(return_value=[
        {"name": "test_tool", "categories": ["test", "utility"]}
    ])
    
    response = client.get("/api/v1/tools/categories")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)

