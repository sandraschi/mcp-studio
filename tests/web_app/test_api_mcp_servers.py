"""Tests for MCP servers API endpoints."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, AsyncMock


def test_list_mcp_servers_empty(client: TestClient, mock_server_service):
    """Test listing MCP servers when none are configured."""
    mock_server_service.get_servers.return_value = {}

    response = client.get("/api/v1/mcp/servers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0


def test_list_mcp_servers_with_data(client: TestClient, mock_server_service):
    """Test listing MCP servers with mock data."""
    from mcp_studio.app.models.mcp import MCPServer
    from mcp_studio.app.core.enums import ServerStatus, ServerType

    mock_server = MCPServer(
        id="test-mcp-server",
        name="Test MCP Server",
        description="A test MCP server",
        type=ServerType.STDIO,
        status=ServerStatus.OFFLINE,
        command="python",
        args=["test_server.py"]
    )

    mock_server_service.get_servers.return_value = {"test-mcp-server": mock_server}

    response = client.get("/api/v1/mcp/servers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == "test-mcp-server"
    assert data[0]["name"] == "Test MCP Server"
    assert data[0]["type"] == "stdio"
    assert data[0]["status"] == "offline"


def test_get_mcp_server_not_found(client: TestClient, mock_server_service):
    """Test getting a non-existent MCP server."""
    mock_server_service.get_server.return_value = None

    response = client.get("/api/v1/mcp/servers/non-existent")
    assert response.status_code == 404


def test_get_mcp_server_success(client: TestClient, mock_server_service):
    """Test getting an existing MCP server."""
    from mcp_studio.app.models.mcp import MCPServer
    from mcp_studio.app.core.enums import ServerStatus, ServerType

    mock_server = MCPServer(
        id="test-mcp-server",
        name="Test MCP Server",
        description="A test MCP server",
        type=ServerType.STDIO,
        status=ServerStatus.RUNNING,
        command="python",
        args=["test_server.py"],
        port=3000,
        endpoint_url="http://localhost:3000"
    )

    mock_server_service.get_server.return_value = mock_server

    response = client.get("/api/v1/mcp/servers/test-mcp-server")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "test-mcp-server"
    assert data["name"] == "Test MCP Server"
    assert data["status"] == "running"
    assert data["port"] == 3000
    assert data["endpoint_url"] == "http://localhost:3000"


@pytest.mark.asyncio
async def test_start_mcp_server_success(client: TestClient, mock_server_service):
    """Test starting an MCP server successfully."""
    from mcp_studio.app.models.mcp import MCPServer
    from mcp_studio.app.core.enums import ServerStatus, ServerType

    mock_server = MCPServer(
        id="test-mcp-server",
        name="Test MCP Server",
        type=ServerType.STDIO,
        status=ServerStatus.OFFLINE,
        command="python",
        args=["test_server.py"]
    )

    mock_server_service.get_server.return_value = mock_server
    mock_server_service.start_server = AsyncMock(return_value={
        "success": True,
        "message": "Server started successfully",
        "server_id": "test-mcp-server"
    })

    response = client.post("/api/v1/mcp/servers/test-mcp-server/start")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "started successfully" in data["message"]
    assert data["server_id"] == "test-mcp-server"


@pytest.mark.asyncio
async def test_start_mcp_server_not_found(client: TestClient, mock_server_service):
    """Test starting a non-existent MCP server."""
    mock_server_service.get_server.return_value = None

    response = client.post("/api/v1/mcp/servers/non-existent/start")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_stop_mcp_server_success(client: TestClient, mock_server_service):
    """Test stopping an MCP server successfully."""
    from mcp_studio.app.models.mcp import MCPServer
    from mcp_studio.app.core.enums import ServerStatus, ServerType

    mock_server = MCPServer(
        id="test-mcp-server",
        name="Test MCP Server",
        type=ServerType.STDIO,
        status=ServerStatus.RUNNING,
        command="python",
        args=["test_server.py"]
    )

    mock_server_service.get_server.return_value = mock_server
    mock_server_service.stop_server = AsyncMock(return_value={
        "success": True,
        "message": "Server stopped successfully",
        "server_id": "test-mcp-server"
    })

    response = client.post("/api/v1/mcp/servers/test-mcp-server/stop")
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "stopped successfully" in data["message"]


@pytest.mark.asyncio
async def test_stop_mcp_server_not_found(client: TestClient, mock_server_service):
    """Test stopping a non-existent MCP server."""
    mock_server_service.get_server.return_value = None

    response = client.post("/api/v1/mcp/servers/non-existent/stop")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_mcp_server_tools_success(client: TestClient, mock_server_service):
    """Test getting tools for an MCP server."""
    from mcp_studio.app.models.mcp import MCPServer
    from mcp_studio.app.core.enums import ServerStatus, ServerType

    mock_server = MCPServer(
        id="test-mcp-server",
        name="Test MCP Server",
        type=ServerType.STDIO,
        status=ServerStatus.RUNNING
    )

    mock_server_service.get_server.return_value = mock_server
    mock_server_service.get_server_tools = AsyncMock(return_value=[
        {
            "name": "test_tool",
            "description": "A test tool for demonstration",
            "input_schema": {
                "type": "object",
                "properties": {
                    "message": {"type": "string"}
                }
            }
        },
        {
            "name": "another_tool",
            "description": "Another test tool",
            "input_schema": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer"}
                }
            }
        }
    ])

    response = client.get("/api/v1/mcp/servers/test-mcp-server/tools")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 2
    assert data[0]["name"] == "test_tool"
    assert data[1]["name"] == "another_tool"
    assert "input_schema" in data[0]


@pytest.mark.asyncio
async def test_get_mcp_server_tools_server_not_found(client: TestClient, mock_server_service):
    """Test getting tools for a non-existent MCP server."""
    mock_server_service.get_server.return_value = None

    response = client.get("/api/v1/mcp/servers/non-existent/tools")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_execute_mcp_server_tool_success(client: TestClient, mock_server_service):
    """Test executing a tool on an MCP server."""
    from mcp_studio.app.models.mcp import MCPServer
    from mcp_studio.app.core.enums import ServerStatus, ServerType

    mock_server = MCPServer(
        id="test-mcp-server",
        name="Test MCP Server",
        type=ServerType.STDIO,
        status=ServerStatus.RUNNING
    )

    mock_server_service.get_server.return_value = mock_server
    mock_server_service.execute_tool = AsyncMock(return_value={
        "success": True,
        "result": "Tool executed successfully",
        "execution_time": 0.123,
        "tool_name": "test_tool"
    })

    request_data = {
        "tool_name": "test_tool",
        "arguments": {"message": "hello world"}
    }

    response = client.post("/api/v1/mcp/servers/test-mcp-server/tools/test_tool", json=request_data)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["result"] == "Tool executed successfully"
    assert data["tool_name"] == "test_tool"
    assert "execution_time" in data


@pytest.mark.asyncio
async def test_execute_mcp_server_tool_server_not_found(client: TestClient, mock_server_service):
    """Test executing a tool on a non-existent MCP server."""
    mock_server_service.get_server.return_value = None

    request_data = {
        "tool_name": "test_tool",
        "arguments": {"message": "hello world"}
    }

    response = client.post("/api/v1/mcp/servers/non-existent/tools/test_tool", json=request_data)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_execute_mcp_server_tool_invalid_request(client: TestClient, mock_server_service):
    """Test executing a tool with invalid request data."""
    from mcp_studio.app.models.mcp import MCPServer
    from mcp_studio.app.core.enums import ServerStatus, ServerType

    mock_server = MCPServer(
        id="test-mcp-server",
        name="Test MCP Server",
        type=ServerType.STDIO,
        status=ServerStatus.RUNNING
    )

    mock_server_service.get_server.return_value = mock_server

    # Missing tool_name
    request_data = {
        "arguments": {"message": "hello world"}
    }

    response = client.post("/api/v1/mcp/servers/test-mcp-server/tools/test_tool", json=request_data)
    # Should still work as the tool_name is in the URL path
    assert response.status_code in [200, 400, 422]  # Depends on validation implementation
