"""API endpoints for managing MCP servers."""

from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import HttpUrl

from ...models.mcp import MCPServer, ServerRegistration, ServerStatus, MCPServerHealth
from ...services.discovery_service import discovered_servers, get_server, execute_tool

router = APIRouter()

@router.get(
    "/",
    response_model=List[MCPServer],
    summary="List all MCP servers",
    description="Get a list of all discovered MCP servers.",
)
async def list_servers(
    status: Optional[ServerStatus] = Query(
        None, description="Filter servers by status"
    ),
    type: Optional[str] = Query(
        None, description="Filter servers by type (e.g., 'python', 'dxt')"
    ),
    tag: Optional[str] = Query(
        None, description="Filter servers by tag"
    ),
) -> List[MCPServer]:
    """
    List all discovered MCP servers with optional filtering.
    
    Args:
        status: Filter servers by status
        type: Filter servers by type
        tag: Filter servers by tag
        
    Returns:
        List of MCP servers matching the filters
    """
    servers = list(discovered_servers.values())
    
    # Apply filters
    if status is not None:
        servers = [s for s in servers if s.status == status]
    if type is not None:
        servers = [s for s in servers if s.type == type]
    if tag is not None:
        servers = [s for s in servers if tag in s.tags]
    
    return servers

@router.post(
    "/",
    response_model=MCPServer,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new MCP server",
    description="Register a new MCP server with the given details.",
)
async def register_server(registration: ServerRegistration) -> MCPServer:
    """
    Register a new MCP server.
    
    Args:
        registration: Server registration details
        
    Returns:
        The registered server
        
    Raises:
        HTTPException: If the server could not be registered
    """
    # Generate a unique ID for the server
    server_id = f"{registration.type}:{registration.url or registration.path}"
    
    if server_id in discovered_servers:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Server with ID '{server_id}' already exists",
        )
    
    # Create the server
    server = MCPServer(
        id=server_id,
        name=registration.name,
        description=registration.description,
        url=registration.url,
        path=registration.path,
        type=registration.type,
        status=ServerStatus.ONLINE,  # Assume it's online since we just registered it
        tags=registration.tags,
    )
    
    # Add to discovered servers
    discovered_servers[server_id] = server
    
    return server

@router.get(
    "/{server_id}",
    response_model=MCPServer,
    summary="Get server by ID",
    description="Get detailed information about a specific MCP server.",
    responses={
        404: {"description": "Server not found"},
    },
)
async def get_server_by_id(server_id: str) -> MCPServer:
    """
    Get an MCP server by its ID.
    
    Args:
        server_id: ID of the server to retrieve
        
    Returns:
        The requested server
        
    Raises:
        HTTPException: If the server is not found
    """
    server = await get_server(server_id)
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID '{server_id}' not found",
        )
    return server

@router.delete(
    "/{server_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Unregister an MCP server",
    description="Unregister an MCP server by its ID.",
    responses={
        204: {"description": "Server successfully unregistered"},
        404: {"description": "Server not found"},
    },
)
async def unregister_server(server_id: str) -> None:
    """
    Unregister an MCP server.
    
    Args:
        server_id: ID of the server to unregister
        
    Raises:
        HTTPException: If the server is not found
    """
    if server_id not in discovered_servers:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID '{server_id}' not found",
        )
    
    del discovered_servers[server_id]
    return None

@router.get(
    "/{server_id}/health",
    response_model=MCPServerHealth,
    summary="Get server health",
    description="Get the health status of an MCP server.",
    responses={
        404: {"description": "Server not found"},
    },
)
async def get_server_health(server_id: str) -> MCPServerHealth:
    """
    Get the health status of an MCP server.
    
    Args:
        server_id: ID of the server
        
    Returns:
        The health status of the server
        
    Raises:
        HTTPException: If the server is not found
    """
    server = await get_server(server_id)
    if server is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID '{server_id}' not found",
        )
    
    # TODO: Actually check the server's health
    # For now, return a mock health status
    return MCPServerHealth(
        status=server.status,
        version=server.version,
        timestamp=server.updated_at or server.created_at,
    )

@router.post(
    "/{server_id}/tools/{tool_name}/execute",
    summary="Execute a tool",
    description="Execute a tool on the specified MCP server.",
    responses={
        200: {"description": "Tool executed successfully"},
        400: {"description": "Invalid parameters"},
        404: {"description": "Server or tool not found"},
        500: {"description": "Tool execution failed"},
    },
)
async def execute_server_tool(
    server_id: str,
    tool_name: str,
    parameters: dict,
) -> dict:
    """
    Execute a tool on an MCP server.
    
    Args:
        server_id: ID of the server
        tool_name: Name of the tool to execute
        parameters: Parameters to pass to the tool
        
    Returns:
        The result of the tool execution
        
    Raises:
        HTTPException: If the server, tool, or execution fails
    """
    try:
        return await execute_tool(server_id, tool_name, parameters)
    except Exception as e:
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute tool: {str(e)}",
        )
