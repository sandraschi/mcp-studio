"""
Server API Endpoints for MCP Studio

This module provides API endpoints for managing MCP servers.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, HttpUrl

from mcp_studio.tools.server import (
    discover_servers,
    execute_remote_tool,
    get_server_info,
    list_server_tools,
    test_server_connection,
)

from .auth import get_current_active_user

router = APIRouter()


# Pydantic models
class ServerInfo(BaseModel):
    """Server information model."""

    name: str
    url: HttpUrl
    version: str = "1.0.0"
    description: str = ""
    tags: list[str] = []
    metadata: dict[str, Any] = {}


class ServerDiscoveryRequest(BaseModel):
    """Server discovery request model."""

    network: str = "192.168.1.0/24"
    ports: list[int] = [8000]
    timeout: float = 5.0


class ServerToolInfo(BaseModel):
    """Server tool information model."""

    name: str
    description: str
    parameters: dict[str, Any] = {}
    tags: list[str] = []


class ToolExecutionRequest(BaseModel):
    """Tool execution request model."""

    tool_name: str
    parameters: dict[str, Any] = {}
    timeout: float | None = None


class ToolExecutionResponse(BaseModel):
    """Tool execution response model."""

    success: bool
    result: Any
    execution_time: float
    error: str | None = None


# API Endpoints
@router.post("/discover", response_model=list[ServerInfo])
async def discover_mcp_servers(
    request: ServerDiscoveryRequest, current_user: Any = Depends(get_current_active_user)
) -> Any:
    """
    Discover MCP servers on the network.

    Args:
        request: Discovery parameters (network, ports, timeout)

    Returns:
        List of discovered servers
    """
    try:
        # FIXME(BUG-078 typing pass): discover_servers scans the configured paths; it has no
        # network/ports/timeout parameters, so those request fields are not used.
        discovery = await discover_servers()
        servers: list[dict[str, Any]] = discovery.get("servers", [])
        return [
            ServerInfo(
                name=s.get("name", "Unknown"),
                url=s["url"],
                version=s.get("version", "1.0.0"),
                description=s.get("description", ""),
                tags=s.get("tags", []),
                metadata=s.get("metadata", {}),
            )
            for s in servers
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Server discovery failed: {e!s}")


@router.get("/{server_url}/info", response_model=ServerInfo)
async def get_server_information(server_url: str, current_user: Any = Depends(get_current_active_user)) -> Any:
    """
    Get information about a specific MCP server.

    Args:
        server_url: Base URL of the MCP server

    Returns:
        Server information
    """
    try:
        info = await get_server_info(server_url)
        return ServerInfo(
            name=info.get("name", "Unknown"),
            url=info["url"],
            version=info.get("version", "1.0.0"),
            description=info.get("description", ""),
            tags=info.get("tags", []),
            metadata=info.get("metadata", {}),
        )
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to get server info: {e!s}")


@router.get("/{server_url}/tools", response_model=list[ServerToolInfo])
async def list_server_tools_endpoint(server_url: str, current_user: Any = Depends(get_current_active_user)) -> Any:
    """
    List tools available on a specific MCP server.

    Args:
        server_url: Base URL of the MCP server

    Returns:
        List of available tools
    """
    try:
        tools_result = await list_server_tools(server_url)
        tools: list[dict[str, Any]] = tools_result.get("tools", [])
        return [
            ServerToolInfo(
                name=tool.get("name", ""),
                description=tool.get("description", ""),
                parameters=tool.get("parameters", {}),
                tags=tool.get("tags", []),
            )
            for tool in tools
        ]
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Failed to list server tools: {e!s}")


@router.post("/{server_url}/execute", response_model=ToolExecutionResponse)
async def execute_remote_tool_endpoint(
    server_url: str, request: ToolExecutionRequest, current_user: Any = Depends(get_current_active_user)
) -> Any:
    """
    Execute a tool on a remote MCP server.

    Args:
        server_url: Base URL of the MCP server
        request: Tool execution request

    Returns:
        Tool execution result
    """
    import time

    try:
        start_time = time.time()
        result = await execute_remote_tool(
            server_path=server_url,
            tool_name=request.tool_name,
            parameters=request.parameters,
            timeout=request.timeout or 30.0,
        )
        execution_time = time.time() - start_time

        return ToolExecutionResponse(success=True, result=result, execution_time=execution_time)
    except Exception as e:
        return ToolExecutionResponse(success=False, result=None, execution_time=0, error=str(e))


@router.get("/{server_url}/test-connection", response_model=dict[str, Any])
async def test_server_connection_endpoint(
    server_url: str, timeout: float = 5.0, current_user: Any = Depends(get_current_active_user)
) -> Any:
    """
    Test connection to an MCP server.

    Args:
        server_url: Base URL of the MCP server
        timeout: Connection timeout in seconds

    Returns:
        Connection test results
    """
    try:
        result = await test_server_connection(server_url, timeout)
        return result
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Connection test failed: {e!s}")
