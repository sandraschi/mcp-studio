"""
API endpoints for MCP client information.
"""

from typing import Dict, List, Any, Optional
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from ..services.mcp_client_metadata import (
    get_client_metadata,
    get_all_clients,
    get_clients_by_type,
    get_active_clients,
    format_client_info,
    MCPClientMetadata
)
from ..services.mcp_client_zoo import MCPClientZoo
from ..core.logging_utils import get_logger

# Import working sets manager - handle different import paths
try:
    from working_sets.client_manager import ClientWorkingSetManager
except ImportError:
    try:
        from ...working_sets.client_manager import ClientWorkingSetManager
    except ImportError:
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
        from working_sets.client_manager import ClientWorkingSetManager

router = APIRouter()
logger = get_logger(__name__)

# Lazy-loaded singletons to prevent blocking on module import
_client_ws_manager: Optional[ClientWorkingSetManager] = None
_client_zoo: Optional[MCPClientZoo] = None

def get_client_ws_manager() -> ClientWorkingSetManager:
    """Get or create the client working set manager."""
    global _client_ws_manager
    if _client_ws_manager is None:
        _client_ws_manager = ClientWorkingSetManager()
    return _client_ws_manager

def get_client_zoo() -> MCPClientZoo:
    """Get or create the client zoo."""
    global _client_zoo
    if _client_zoo is None:
        _client_zoo = MCPClientZoo()
    return _client_zoo


class ClientInfoResponse(BaseModel):
    """Response model for client information."""
    id: str = Field(..., description="Client identifier")
    name: str = Field(..., description="Client name")
    short_description: str = Field(..., description="Short description")
    full_description: str = Field(..., description="Full description")
    homepage: Optional[str] = Field(None, description="Homepage URL")
    github: Optional[str] = Field(None, description="GitHub repository URL")
    documentation: Optional[str] = Field(None, description="Documentation URL")
    platform: str = Field(..., description="Platform (Windows, Mac, Linux, Cross-platform)")
    client_type: str = Field(..., description="Client type (Desktop, IDE, Extension)")
    status: str = Field(..., description="Status (Active, Deprecated, Beta)")
    features: List[str] = Field(default_factory=list, description="Key features")
    installed: bool = Field(False, description="Whether this client is detected as installed")
    server_count: int = Field(0, description="Number of MCP servers configured")


class ClientsListResponse(BaseModel):
    """Response model for list of clients."""
    total: int = Field(..., description="Total number of clients")
    clients: List[ClientInfoResponse] = Field(..., description="List of clients")


@router.get(
    "/",
    response_model=ClientsListResponse,
    summary="List all MCP clients",
    description="Get information about all known MCP clients supported by MCP Studio",
)
async def list_clients(
    client_type: Optional[str] = None,
    status: Optional[str] = None,
) -> ClientsListResponse:
    """
    List all known MCP clients with their metadata.
    
    Args:
        client_type: Filter by type (Desktop, IDE, Extension, Library)
        status: Filter by status (Active, Deprecated, Beta)
        
    Returns:
        List of MCP clients with metadata
    """
    try:
        # Get all clients
        if client_type:
            clients = get_clients_by_type(client_type)
        elif status:
            clients = [c for c in get_all_clients() if c.status == status]
        else:
            clients = get_all_clients()
        
        # Convert to response models
        client_responses = [
            ClientInfoResponse(
                id=client.id,
                name=client.name,
                short_description=client.short_description,
                full_description=client.full_description,
                homepage=client.homepage,
                github=client.github,
                documentation=client.documentation,
                platform=client.platform,
                client_type=client.client_type,
                status=client.status,
                features=client.features or [],
                installed=client.installed,
                server_count=client.server_count,
            )
            for client in clients
        ]
        
        return ClientsListResponse(
            total=len(client_responses),
            clients=client_responses
        )
        
    except Exception as e:
        logger.error("Failed to list clients", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list clients: {str(e)}"
        )


@router.get(
    "/{client_id}",
    response_model=ClientInfoResponse,
    summary="Get client information",
    description="Get detailed information about a specific MCP client",
)
async def get_client(client_id: str) -> ClientInfoResponse:
    """
    Get detailed information about a specific MCP client.
    
    Args:
        client_id: Client identifier (e.g., "claude-desktop", "cursor-ide")
        
    Returns:
        Client metadata with full details
    """
    try:
        client = get_client_metadata(client_id)
        
        if not client:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client '{client_id}' not found"
            )
        
        return ClientInfoResponse(
            id=client.id,
            name=client.name,
            short_description=client.short_description,
            full_description=client.full_description,
            homepage=client.homepage,
            github=client.github,
            documentation=client.documentation,
            platform=client.platform,
            client_type=client.client_type,
            status=client.status,
            features=client.features or [],
            installed=client.installed,
            server_count=client.server_count,
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get client info", client_id=client_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client info: {str(e)}"
        )


@router.get(
    "/{client_id}/markdown",
    summary="Get client information as markdown",
    description="Get formatted markdown documentation for a client",
)
async def get_client_markdown(client_id: str) -> Dict[str, str]:
    """
    Get client information formatted as markdown.
    
    Args:
        client_id: Client identifier
        
    Returns:
        Markdown-formatted client information
    """
    try:
        markdown = format_client_info(client_id, format="markdown")
        
        if markdown.startswith("Unknown client"):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client '{client_id}' not found"
            )
        
        return {"markdown": markdown}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to format client info", client_id=client_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to format client info: {str(e)}"
        )


@router.get(
    "/stats/summary",
    summary="Get client statistics",
    description="Get summary statistics about supported MCP clients",
)
async def get_client_stats() -> Dict[str, Any]:
    """
    Get summary statistics about supported MCP clients.
    
    Returns:
        Statistics about clients (counts by type, status, etc.)
    """
    try:
        all_clients = get_all_clients()
        
        # Count by type
        by_type = {}
        for client in all_clients:
            client_type = client.client_type
            by_type[client_type] = by_type.get(client_type, 0) + 1
        
        # Count by status
        by_status = {}
        for client in all_clients:
            client_status = client.status
            by_status[client_status] = by_status.get(client_status, 0) + 1
        
        # Count by platform
        by_platform = {}
        for client in all_clients:
            platform = client.platform
            by_platform[platform] = by_platform.get(platform, 0) + 1
        
        return {
            "total_clients": len(all_clients),
            "by_type": by_type,
            "by_status": by_status,
            "by_platform": by_platform,
            "client_ids": [client.id for client in all_clients],
        }
        
    except Exception as e:
        logger.error("Failed to get client stats", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client stats: {str(e)}"
        )


@router.get(
    "/{client_id}/servers",
    summary="Get servers for a client",
    description="Get list of MCP servers configured for a specific client",
)
async def get_client_servers(client_id: str) -> Dict[str, Any]:
    """
    Get MCP servers configured for a specific client.
    
    Args:
        client_id: Client identifier
        
    Returns:
        List of servers configured for the client
    """
    try:
        # Scan client to get servers
        results = get_client_zoo().scan_all_clients()
        servers = results.get(client_id, [])
        
        return {
            "client_id": client_id,
            "servers": [
                {
                    "id": s.id,
                    "name": s.name,
                    "command": s.command,
                    "args": s.args,
                    "source": s.source,
                }
                for s in servers
            ],
            "count": len(servers),
        }
    except Exception as e:
        logger.error("Failed to get client servers", client_id=client_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client servers: {str(e)}"
        )


@router.get(
    "/{client_id}/working-sets",
    summary="Get working sets for a client",
    description="Get available working sets for a specific client",
)
async def get_client_working_sets(client_id: str) -> Dict[str, Any]:
    """
    Get working sets available for a specific client.
    
    Args:
        client_id: Client identifier
        
    Returns:
        List of working sets and current active set
    """
    try:
        manager = get_client_ws_manager().get_manager(client_id)
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client '{client_id}' config not found"
            )
        
        working_sets = manager.list_working_sets()
        current_working_set = manager.get_current_working_set()
        
        return {
            "client_id": client_id,
            "working_sets": working_sets,
            "current_working_set": current_working_set,
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get client working sets", client_id=client_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client working sets: {str(e)}"
        )


@router.post(
    "/{client_id}/working-sets/{set_id}/activate",
    summary="Activate working set for a client",
    description="Switch client to a specific working set",
)
async def activate_client_working_set(
    client_id: str,
    set_id: str,
    create_backup: bool = True
) -> Dict[str, Any]:
    """
    Activate a working set for a specific client.
    
    Args:
        client_id: Client identifier
        set_id: Working set identifier
        create_backup: Whether to create backup before switching
        
    Returns:
        Success status and details
    """
    try:
        manager = get_client_ws_manager().get_manager(client_id)
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client '{client_id}' config not found"
            )
        
        success = manager.switch_to_working_set(set_id, create_backup)
        
        if success:
            return {
                "success": True,
                "client_id": client_id,
                "working_set_id": set_id,
                "message": f"Switched to working set: {set_id}",
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to switch working set"
            )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to activate working set", client_id=client_id, set_id=set_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to activate working set: {str(e)}"
        )


@router.get(
    "/{client_id}/working-sets/{set_id}/preview",
    summary="Preview working set changes",
    description="Preview what changes would be made by activating a working set",
)
async def preview_client_working_set(client_id: str, set_id: str) -> Dict[str, Any]:
    """
    Preview changes for a working set without applying.
    
    Args:
        client_id: Client identifier
        set_id: Working set identifier
        
    Returns:
        Preview of changes
    """
    try:
        manager = get_client_ws_manager().get_manager(client_id)
        if not manager:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client '{client_id}' config not found"
            )
        
        preview = manager.preview_working_set_config(set_id)
        return {
            "client_id": client_id,
            "working_set_id": set_id,
            **preview,
        }
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to preview working set", client_id=client_id, set_id=set_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to preview working set: {str(e)}"
        )


@router.get(
    "/{client_id}/config",
    summary="Get client config",
    description="Get current configuration for a client",
)
async def get_client_config(client_id: str) -> Dict[str, Any]:
    """
    Get current configuration info for a client.
    
    Args:
        client_id: Client identifier
        
    Returns:
        Configuration information
    """
    try:
        config_info = get_client_ws_manager().get_client_config_info(client_id)
        if not config_info:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client '{client_id}' config not found"
            )
        
        # Get current servers
        manager = _client_ws_manager.get_manager(client_id)
        current_servers = []
        if manager:
            current_config = manager._current_config
            current_servers = list(current_config.get("mcpServers", {}).keys())
        
        return {
            **config_info,
            "current_servers": current_servers,
            "server_count": len(current_servers),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get client config", client_id=client_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client config: {str(e)}"
        )

