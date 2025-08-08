"""API endpoints for MCP server discovery."""

from typing import Dict, List

from fastapi import APIRouter, BackgroundTasks, HTTPException, status

from ...models.mcp import MCPServer, ServerRegistration
from ...services import discovery_service

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
    background_tasks.add_task(discovery_service.discover_mcp_servers)
    
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
        
        if server_id in discovery_service.discovered_servers:
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
            tags=registration.tags,
        )
        
        # Add to discovered servers
        discovery_service.discovered_servers[server_id] = server
        
        # Try to discover tools from the server
        try:
            if registration.path:
                await discovery_service._discover_python_server(Path(registration.path))
            # TODO: Add support for URL-based discovery
        except Exception as e:
            logger.warning(
                "Failed to discover tools from server",
                server_id=server_id,
                error=str(e),
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
    return discovery_service.settings.MCP_DISCOVERY_PATHS

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
    discovery_service.settings.MCP_DISCOVERY_PATHS = valid_paths
    
    # Save settings to disk (if applicable)
    if hasattr(discovery_service.settings, "save"):
        discovery_service.settings.save()
    
    return valid_paths
