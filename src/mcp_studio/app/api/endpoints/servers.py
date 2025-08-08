"""API endpoints for managing MCP servers."""
from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import JSONResponse

from mcp_studio.app.services.config_service import config_service
from mcp_studio.app.services.server_service import server_service
from mcp_studio.app.models.server import Server, ServerStatus, ServerType

router = APIRouter()


def get_server_status(server_id: str) -> ServerStatus:
    """Get the current status of an MCP server.
    
    This is a placeholder that should be replaced with actual server status checks.
    For now, we'll assume all servers are online if they're in the config.
    """
    if server_id in server_service.get_servers():
        return ServerStatus.ONLINE
    return ServerStatus.OFFLINE


@router.get("/", response_model=List[Dict[str, Any]])
async def list_servers() -> List[Dict[str, Any]]:
    """List all configured MCP servers with their current status."""
    servers = []
    
    # Get all server configurations
    configs = config_service.get_all_servers()
    
    # Get server statuses from the server service
    active_servers = server_service.get_servers()
    
    for server_id, config in configs.items():
        # Determine server type based on command
        server_type = ServerType.UNKNOWN
        if "docker" in server_id.lower() or "docker" in config.get("command", "").lower():
            server_type = ServerType.DOCKER
        elif "python" in config.get("command", "").lower():
            server_type = ServerType.PYTHON
        elif "node" in config.get("command", "").lower() or "npx" in config.get("command", ""):
            server_type = ServerType.NODE
            
        # Check if server is running
        status = ServerStatus.ONLINE if server_id in active_servers else ServerStatus.OFFLINE
        
        servers.append({
            "id": server_id,
            "name": server_id.replace("-", " ").title(),
            "type": server_type.value,
            "status": status.value,
            "command": config["command"],
            "args": config.get("args", []),
            "cwd": config.get("cwd"),
            "env": list(config.get("env", {}).keys()) if config.get("env") else []
        })
    
    return servers


@router.get("/{server_id}", response_model=Dict[str, Any])
async def get_server(server_id: str) -> Dict[str, Any]:
    """Get detailed information about a specific MCP server."""
    config = config_service.get_server_config(server_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Server '{server_id}' not found")
    
    # Check if server is running
    status = ServerStatus.ONLINE if server_id in server_service.get_servers() else ServerStatus.OFFLINE
    
    # Determine server type based on command
    server_type = ServerType.UNKNOWN
    if "docker" in server_id.lower() or "docker" in config.get("command", "").lower():
        server_type = ServerType.DOCKER
    elif "python" in config.get("command", "").lower():
        server_type = ServerType.PYTHON
    elif "node" in config.get("command", "").lower() or "npx" in config.get("command", ""):
        server_type = ServerType.NODE
    
    return {
        "id": server_id,
        "name": server_id.replace("-", " ").title(),
        "type": server_type.value,
        "status": status.value,
        "command": config["command"],
        "args": config.get("args", []),
        "cwd": config.get("cwd"),
        "env": config.get("env", {}),
        "description": f"{server_type.value.title()} MCP Server"
    }


@router.post("/{server_id}/start", response_model=Dict[str, Any])
async def start_server(server_id: str) -> Dict[str, Any]:
    """Start an MCP server."""
    config = config_service.get_server_config(server_id)
    if not config:
        raise HTTPException(status_code=404, detail=f"Server '{server_id}' not found")
    
    try:
        # Start the server using the server service
        # This is a placeholder - actual implementation would start the server process
        server_service.register_server(server_id, config)
        
        return {
            "status": "success",
            "message": f"Started server '{server_id}'",
            "server_id": server_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{server_id}/stop", response_model=Dict[str, Any])
async def stop_server(server_id: str) -> Dict[str, Any]:
    """Stop an MCP server."""
    if server_id not in server_service.get_servers():
        raise HTTPException(status_code=404, detail=f"Server '{server_id}' is not running")
    
    try:
        # Stop the server using the server service
        # This is a placeholder - actual implementation would stop the server process
        server_service.unregister_server(server_id)
        
        return {
            "status": "success",
            "message": f"Stopped server '{server_id}'",
            "server_id": server_id
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{server_id}/tools", response_model=List[Dict[str, Any]])
async def list_server_tools(server_id: str) -> List[Dict[str, Any]]:
    """List tools provided by an MCP server."""
    if server_id not in server_service.get_servers():
        raise HTTPException(status_code=404, detail=f"Server '{server_id}' is not running")
    
    try:
        # Get tools from the server service
        # This is a placeholder - actual implementation would query the server for its tools
        tools = server_service.get_server_tools(server_id)
        
        return tools or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
