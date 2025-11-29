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
from ..core.logging_utils import get_logger

router = APIRouter()
logger = get_logger(__name__)


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
                features=client.features or []
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
            features=client.features or []
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

