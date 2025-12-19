"""API endpoints for MCP server discovery."""

from typing import Dict, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from ..models.mcp import MCPServer, ServerRegistration
from ..services.mcp_discovery_service import discovery_service

router = APIRouter()

@router.post(
    "/scan",
    status_code=status.HTTP_202_ACCEPTED,
    summary="Start a discovery scan",
    description="Start a background scan for MCP servers in the configured paths.",
)
async def start_discovery_scan(background_tasks: BackgroundTasks) -> Dict[str, str]:
    """
    Start a background scan for MCP servers.
    
    Args:
        background_tasks: FastAPI background tasks
        
    Returns:
        Confirmation message
    """
    # Start a new discovery task
    background_tasks.add_task(discovery_service.start_discovery)
    
    return {"message": "Discovery scan started in the background"}

@router.post(
    "/register",
    response_model=MCPServer,
    status_code=status.HTTP_201_CREATED,
    summary="Register a server manually",
    description="Manually register an MCP server by its path or URL.",
    responses={
        400: {"description": "Invalid server path or URL"},
    },
)
async def register_server(registration: ServerRegistration) -> MCPServer:
    """
    Manually register an MCP server.
    
    Args:
        registration: Server registration details
        
    Returns:
        The registered server
        
    Raises:
        HTTPException: If the server cannot be registered
    """
    try:
        # Generate a unique ID for the server
        server_id = f"{registration.type}:{registration.url or registration.path}"
        
        # Check if server already exists
        all_servers = server_service.get_servers()
        if server_id in all_servers:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Server with ID '{server_id}' already exists",
            )
        
        # Register the server using server_service
        config = {
            "name": registration.name,
            "description": registration.description,
            "type": registration.type,
            "command": registration.path.split() if registration.path else [],
        }
        if registration.url:
            config["url"] = registration.url
        
        registered_server = await server_service.register_server(server_id, config)
        
        # Convert to MCPServer format
        server = MCPServer(
            id=registered_server.id,
            name=registered_server.name,
            description=registered_server.description or "",
            url=None,
            path=None,
            type=registered_server.type.value if hasattr(registered_server.type, 'value') else str(registered_server.type),
            status=registered_server.status,
            version=None,
            tags=[],
            created_at=registered_server.created_at,
            updated_at=registered_server.updated_at,
        )
        
        return server
        
    except Exception as e:
        logger.error("Failed to register server", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to register server: {str(e)}",
        )

@router.get(
    "/paths",
    response_model=List[str],
    summary="Get discovery paths",
    description="Get the current list of paths being scanned for MCP servers.",
)
async def get_discovery_paths() -> List[str]:
    """
    Get the current list of discovery paths.
    
    Returns:
        List of paths being scanned for MCP servers
    """
    from ..core.config import settings
    return settings.MCP_DISCOVERY_PATHS

@router.put(
    "/paths",
    response_model=List[str],
    summary="Update discovery paths",
    description="Update the list of paths to scan for MCP servers.",
)
async def update_discovery_paths(paths: List[str]) -> List[str]:
    """
    Update the list of discovery paths.
    
    Args:
        paths: New list of paths to scan
        
    Returns:
        Updated list of discovery paths
    """
    # Validate paths
    valid_paths = []
    for path in paths:
        try:
            path_obj = Path(path).expanduser().resolve()
            valid_paths.append(str(path_obj))
        except Exception as e:
            logger.warning("Invalid discovery path", path=path, error=str(e))
    
    # Update settings
    from ..core.config import settings, update_settings
    update_settings(MCP_DISCOVERY_PATHS=valid_paths)
    
    return valid_paths
