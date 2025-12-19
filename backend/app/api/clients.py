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

router = APIRouter()
logger = get_logger(__name__)

# Lazy-loaded singleton to prevent blocking on module import
_client_zoo: Optional[MCPClientZoo] = None

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
    running: bool = Field(False, description="Whether this client process is currently running")
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
        print("DEBUG: list_clients endpoint called!")
        logger.info("list_clients endpoint called", client_type=client_type, status=status)
        # Get all clients
        if client_type:
            clients = get_clients_by_type(client_type)
        elif status:
            clients = [c for c in get_all_clients() if c.status == status]
        else:
            clients = get_all_clients()

        logger.info(f"Found {len(clients)} clients")
        
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
                running=client.running,
                server_count=client.server_count,
            )
            for client in clients
        ]
        
        return ClientsListResponse(
            total=999,  # Test if this changes
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
            running=client.running,
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


# Working sets functionality temporarily disabled due to import issues
# @router.get(
#     "/{client_id}/working-sets",
#     summary="Get working sets for a client",
#     description="Get available working sets for a specific client",
# )
# async def get_client_working_sets(client_id: str) -> Dict[str, Any]:
#     """Working sets functionality temporarily disabled."""


# @router.post(
#     "/{client_id}/working-sets/{set_id}/activate",
#     summary="Activate working set for a client",
#     description="Switch client to a specific working set",
# )
# async def activate_client_working_set(
#     client_id: str,
#     set_id: str,
#     create_backup: bool = True
# ) -> Dict[str, Any]:
#     """Working sets functionality temporarily disabled."""


# @router.get(
#     "/{client_id}/working-sets/{set_id}/preview",
#     summary="Preview working set changes",
#     description="Preview what changes would be made by activating a working set",
# )
# async def preview_client_working_set(client_id: str, set_id: str) -> Dict[str, Any]:
#     """Working sets functionality temporarily disabled."""


@router.get(
    "/{client_id}/tools",
    summary="Get client tools",
    description="Get all tools available from MCP servers configured for a client",
)
async def get_client_tools(client_id: str) -> Dict[str, Any]:
    """
    Get tools from all MCP servers configured for a client.

    Args:
        client_id: Client identifier

    Returns:
        List of tools with their metadata
    """
    try:
        from ..services.mcp_client_zoo import MCPClientZoo
        from ..core.stdio import StdioTransport
        from ..services.mcp_discovery_service import MCPDiscoveryService

        # Get the servers configured for this client
        zoo = MCPClientZoo()
        servers_data = zoo.scan_all_clients()
        client_servers = servers_data.get(client_id, [])

        if not client_servers:
            logger.info(f"No servers found for client {client_id}")
            return {"client_id": client_id, "tools": [], "total_tools": 0, "servers_count": 0}

        all_tools = []
        discovery_service = MCPDiscoveryService()

        # For each server, try to connect and get its tools
        for server in client_servers:
            try:
                logger.info(f"Attempting to connect to server {server.name} for tool discovery")

                # Create server config
                from ..services.mcp_discovery_service import MCPServerConfig
                config = MCPServerConfig(
                    id=f"{client_id}:{server.id}",
                    name=server.name,
                    command=server.command,
                    args=server.args,
                    cwd=server.cwd,
                    env=server.env,
                    source=client_id
                )

                # Try to connect and get tools
                tools = await _get_server_tools(config)
                logger.info(f"Got {len(tools)} tools from server {server.name}")

                for tool in tools:
                    tool["server_name"] = server.name
                    tool["server_id"] = server.id
                all_tools.extend(tools)

            except Exception as e:
                logger.warning(f"Failed to get tools for server {server.name}: {e}")
                # Add a placeholder tool indicating connection failed
                all_tools.append({
                    "name": "connection_error",
                    "description": f"Failed to connect to {server.name}: {str(e)}",
                    "server_name": server.name,
                    "server_id": server.id,
                    "inputSchema": {"type": "object", "properties": {}}
                })
                continue

        logger.info(f"Total tools collected for client {client_id}: {len(all_tools)}")
        return {
            "client_id": client_id,
            "tools": all_tools,
            "total_tools": len(all_tools),
            "servers_count": len(client_servers),
        }

    except Exception as e:
        logger.error("Failed to get client tools", client_id=client_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client tools: {str(e)}"
        )


async def _get_server_tools(config) -> List[Dict[str, Any]]:
    """
    Connect to an MCP server and get its available tools.

    Args:
        config: MCPServerConfig object with server details

    Returns:
        List of tool definitions from the server
    """
    import asyncio
    import json
    from ..core.stdio import StdioTransport

    try:
        # Create transport for the server
        transport = StdioTransport(
            command=config.command,
            args=config.args,
            cwd=config.cwd,
            env=config.env
        )

        # Start the server process
        await transport.start()

        try:
            # Send initialize request
            init_request = {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {},
                    "clientInfo": {
                        "name": "mcp-studio-tools-discovery",
                        "version": "1.0.0"
                    }
                }
            }

            await transport.send(json.dumps(init_request))

            # Read initialize response
            init_response = await transport.receive()
            init_data = json.loads(init_response)

            if "error" in init_data:
                logger.warning(f"Server {config.name} initialize error: {init_data['error']}")
                # Return basic info even if initialize fails
                return [{
                    "name": "server_info",
                    "description": f"Server {config.name} (connection issues)",
                    "inputSchema": {"type": "object", "properties": {}},
                    "enabled": False  # Disabled when connection fails
                }]

            # Send tools/list request
            tools_request = {
                "jsonrpc": "2.0",
                "id": 2,
                "method": "tools/list",
                "params": {}
            }

            await transport.send(json.dumps(tools_request))

            # Read tools response
            tools_response = await transport.receive()
            tools_data = json.loads(tools_response)

            if "error" in tools_data:
                logger.warning(f"Server {config.name} tools/list error: {tools_data['error']}")
                return []

            # Extract tools
            tools = []
            if "result" in tools_data and "tools" in tools_data["result"]:
                for tool in tools_data["result"]["tools"]:
                    tools.append({
                        "name": tool.get("name", "unknown"),
                        "description": tool.get("description", ""),
                        "inputSchema": tool.get("inputSchema", {"type": "object", "properties": {}}),
                        "enabled": True  # Default to enabled for now
                    })

            logger.info(f"Successfully retrieved {len(tools)} tools from {config.name}")
            return tools

        finally:
            # Always try to shutdown the transport
            try:
                await transport.shutdown()
            except Exception:
                pass

    except Exception as e:
        logger.warning(f"Failed to connect to MCP server {config.name}: {e}")
        # Return a placeholder tool indicating the server is not accessible
        return [{
            "name": "server_unavailable",
            "description": f"Server {config.name} is not currently accessible",
            "inputSchema": {"type": "object", "properties": {}},
            "enabled": False  # Disabled when server is unreachable
        }]


@router.post(
    "/{client_id}/tools/{tool_name}/toggle",
    summary="Toggle tool enablement",
    description="Enable or disable a specific tool for a client",
)
async def toggle_tool(
    client_id: str,
    tool_name: str,
    request: Dict[str, bool]
) -> Dict[str, Any]:
    """
    Toggle the enabled/disabled status of a specific tool.
    """
    try:
        enabled = request.get("enabled", True)

        # For now, we'll store this in memory
        # In a real implementation, this would be persisted to a database
        logger.info(f"Toggling tool {tool_name} for client {client_id} to {'enabled' if enabled else 'disabled'}")

        # TODO: Implement persistent storage for tool enablement settings

        return {
            "client_id": client_id,
            "tool_name": tool_name,
            "enabled": enabled,
            "message": f"Tool {tool_name} {'enabled' if enabled else 'disabled'} successfully"
        }

    except Exception as e:
        logger.error(f"Failed to toggle tool {tool_name} for client {client_id}", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to toggle tool: {str(e)}"
        )


# ═══════════════════════════════════════════════════════════════
# SETTINGS MANAGEMENT ENDPOINTS
# ═══════════════════════════════════════════════════════════════

@router.get(
    "/settings/categories",
    summary="Get setting categories",
    description="Get information about available client setting categories"
)
async def get_setting_categories() -> Dict[str, Any]:
    """
    Get all available setting categories with descriptions and icons.
    """
    try:
        zoo = get_client_zoo()
        categories = zoo.get_setting_categories()
        return {
            "categories": categories,
            "total": len(categories)
        }
    except Exception as e:
        logger.error("Failed to get setting categories", error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get setting categories: {str(e)}"
        )


@router.get(
    "/{client_id}/settings",
    summary="Get client settings",
    description="Get all editable settings for a specific client, organized by category"
)
async def get_client_settings(client_id: str) -> Dict[str, Any]:
    """
    Get all settings for a client, organized by category.
    """
    try:
        zoo = get_client_zoo()
        settings = zoo.get_client_settings(client_id)

        if settings is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client '{client_id}' not found or has no accessible settings"
            )

        return settings

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get client settings", client_id=client_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client settings: {str(e)}"
        )


@router.get(
    "/{client_id}/settings/{setting_key}",
    summary="Get specific client setting",
    description="Get a specific setting for a client"
)
async def get_client_setting(client_id: str, setting_key: str) -> Dict[str, Any]:
    """
    Get a specific setting for a client.
    """
    try:
        zoo = get_client_zoo()

        # First ensure settings are loaded
        zoo.get_client_settings(client_id)

        # Get the specific setting from the settings manager
        setting = zoo.settings_manager.get_setting(client_id, setting_key)

        if setting is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Setting '{setting_key}' not found for client '{client_id}'"
            )

        return setting

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to get client setting", client_id=client_id, setting_key=setting_key, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get client setting: {str(e)}"
        )


@router.put(
    "/{client_id}/settings/{setting_key}",
    summary="Update client setting",
    description="Update a specific setting for a client with automatic backup"
)
async def update_client_setting(
    client_id: str,
    setting_key: str,
    value: Any,
    create_backup: bool = True
) -> Dict[str, Any]:
    """
    Update a specific setting for a client.

    Creates an automatic backup before making changes.
    """
    try:
        zoo = get_client_zoo()

        success = zoo.update_client_setting(client_id, setting_key, value, create_backup)

        if not success:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Failed to update setting '{setting_key}' for client '{client_id}'"
            )

        # Return updated setting info
        updated_setting = zoo.settings_manager.get_setting(client_id, setting_key)

        return {
            "success": True,
            "message": f"Setting '{setting_key}' updated successfully",
            "client_id": client_id,
            "setting": updated_setting,
            "backup_created": create_backup
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to update client setting", client_id=client_id, setting_key=setting_key, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update client setting: {str(e)}"
        )


@router.post(
    "/{client_id}/settings/discover",
    summary="Discover client settings",
    description="Force discovery/re-discovery of settings for a client"
)
async def discover_client_settings(client_id: str) -> Dict[str, Any]:
    """
    Discover or re-discover settings for a client.
    """
    try:
        zoo = get_client_zoo()
        config = zoo.discover_client_settings(client_id)

        if config is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Client '{client_id}' not found or config file not accessible"
            )

        settings_info = zoo.get_client_settings(client_id)

        return {
            "success": True,
            "message": f"Discovered settings for client '{client_id}'",
            "client_id": client_id,
            "settings_count": settings_info["total_settings"] if settings_info else 0,
            "editable_count": settings_info["editable_settings"] if settings_info else 0,
            "config_path": str(config.config_path)
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error("Failed to discover client settings", client_id=client_id, error=str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to discover client settings: {str(e)}"
        )


# @router.get(
#     "/{client_id}/config",
#     summary="Get client config",
#     description="Get current configuration for a client",
# )
# async def get_client_config(client_id: str) -> Dict[str, Any]:
#     """Working sets functionality temporarily disabled."""

