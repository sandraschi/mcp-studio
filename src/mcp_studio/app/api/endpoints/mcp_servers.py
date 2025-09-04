"""
MCP Server API endpoints for FastMCP 2.10+ integration.
"""
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from mcp_studio.app.services.mcp_discovery_service import get_discovery_service, discovery_service
from mcp_studio.app.core.enums import ServerStatus

router = APIRouter(prefix="/mcp/servers", tags=["mcp-servers"])

class MCPServerCreate(BaseModel):
    """Request model for creating a new MCP server."""
    name: str = Field(..., description="Display name for the server")
    command: str = Field(..., description="Command to start the server")
    args: List[str] = Field(default_factory=list, description="Command line arguments")
    cwd: Optional[str] = Field(None, description="Working directory")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    auto_start: bool = Field(True, description="Whether to start this server automatically")

@router.get("/", response_model=List[Dict[str, Any]])
async def list_servers() -> List[Dict[str, Any]]:
    """List all discovered MCP servers."""
    try:
        return await discovery_service.get_servers()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list servers: {str(e)}"
        )

@router.post("/", status_code=status.HTTP_201_CREATED)
async def add_server(server: MCPServerCreate) -> Dict[str, Any]:
    """Add a new MCP server configuration."""
    server_id = server.name.lower().replace(" ", "-")
    config = {
        "id": server_id,
        "name": server.name,
        "command": server.command,
        "args": server.args,
        "cwd": server.cwd,
        "env": server.env or {},
        "source": "api",
        "auto_start": server.auto_start
    }
    
    try:
        server_config = discovery_service.MCPServerConfig(**config)
        success = await discovery_service.add_server(server_config)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Server with ID {server_id} already exists"
            )
        return {"id": server_id, "status": "added"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to add server: {str(e)}"
        )

@router.get("/{server_id}", response_model=Dict[str, Any])
async def get_server(server_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific MCP server."""
    try:
        servers = await discovery_service.get_servers()
        for server in servers:
            if server.get("id") == server_id:
                return server
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server {server_id} not found"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get server info: {str(e)}"
        )

@router.post("/{server_id}/start", response_model=Dict[str, Any])
async def start_server(server_id: str) -> Dict[str, Any]:
    """Start an MCP server."""
    try:
        if server_id in discovery_service.servers:
            return {"id": server_id, "status": "already_running"}
            
        success = await discovery_service._connect_server(server_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start server {server_id}"
            )
        return {"id": server_id, "status": "started"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start server: {str(e)}"
        )

@router.post("/{server_id}/stop", response_model=Dict[str, Any])
async def stop_server(server_id: str) -> Dict[str, Any]:
    """Stop an MCP server."""
    try:
        if server_id not in discovery_service.servers:
            return {"id": server_id, "status": "not_running"}
            
        await discovery_service._disconnect_server(server_id)
        return {"id": server_id, "status": "stopped"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop server: {str(e)}"
        )

@router.get("/{server_id}/tools", response_model=List[Dict[str, Any]])
async def list_server_tools(server_id: str) -> List[Dict[str, Any]]:
    """List tools provided by an MCP server."""
    try:
        if server_id not in discovery_service.servers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Server {server_id} is not connected"
            )
            
        client = discovery_service.servers[server_id]
        tools = await client.list_tools()
        return [{"name": t.name, "description": t.description} for t in tools]
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list tools: {str(e)}"
        )

@router.post("/{server_id}/tools/{tool_name}", response_model=Dict[str, Any])
async def execute_tool(
    server_id: str, 
    tool_name: str, 
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a tool on an MCP server."""
    try:
        return await discovery_service.execute_tool(server_id, tool_name, parameters)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to execute tool: {str(e)}"
        )

# WebSocket endpoint for real-time updates
@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time server updates."""
    await websocket.accept()
    
    try:
        while True:
            # Send current server status
            servers = await discovery_service.get_servers()
            await websocket.send_json({
                "type": "update",
                "data": servers
            })
            
            # Wait for a while before sending the next update
            await asyncio.sleep(5)
            
    except WebSocketDisconnect:
        # Client disconnected
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        await websocket.close()

# Register startup and shutdown events
@router.on_event("startup")
async def startup_event():
    """Start the discovery service when the app starts."""
    await discovery_service.start_discovery()

@router.on_event("shutdown")
async def shutdown_event():
    """Stop the discovery service when the app shuts down."""
    await discovery_service.stop_discovery()
