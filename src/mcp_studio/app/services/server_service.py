"""Service for managing MCP server connections and tool execution."""

import asyncio
import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

import structlog
from fastapi import HTTPException, status
from fastmcp import MCPClient

from ...app.core.config import settings
from ...app.core.stdio import StdioTransport, transport_manager
from ...models.server import Server, ServerStatus, ServerType, ToolInfo, ToolParameter
from ...models.mcp import (
    MCPServer,
    MCPTool,
    MCPToolParameter,
    ToolExecutionRequest,
    ToolExecutionResult,
)

logger = structlog.get_logger(__name__)

class ServerService:
    """Service for managing MCP server connections and tool execution."""
    
    def __init__(self):
        """Initialize the server service."""
        self.servers: Dict[str, Server] = {}
        self.clients: Dict[str, MCPClient] = {}
        self._lock = asyncio.Lock()
    
    async def register_server(self, server_id: str, config: Dict[str, Any]) -> Server:
        """Register a new MCP server from configuration.
        
        Args:
            server_id: The ID of the server to register
            config: The server configuration
            
        Returns:
            The registered server
            
        Raises:
            HTTPException: If the server cannot be registered
        """
        async with self._lock:
            if server_id in self.servers:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Server with ID '{server_id}' already exists",
                )
            
            # Create server from config
            server = Server(
                id=server_id,
                name=server_id.replace("-", " ").title(),
                type=self._detect_server_type(config),
                status=ServerStatus.OFFLINE,
                command=config["command"],
                args=config.get("args", []),
                cwd=config.get("cwd"),
                env=config.get("env", {}),
                description=f"{self._detect_server_type(config).value.title()} MCP Server"
            )
            
            # Add the server
            self.servers[server_id] = server
            
            return server
    
    def _detect_server_type(self, config: Dict[str, Any]) -> ServerType:
        """Detect the server type from its configuration.
        
        Args:
            config: The server configuration
            
        Returns:
            The detected server type
        """
        command = config.get("command", "").lower()
        if "docker" in command or "docker" in config.get("args", []):
            return ServerType.DOCKER
        elif "python" in command or any("python" in arg.lower() for arg in config.get("args", [])):
            return ServerType.PYTHON
        elif "node" in command or "npx" in command or any("node" in arg.lower() or "npx" in arg.lower() for arg in config.get("args", [])):
            return ServerType.NODE
        return ServerType.UNKNOWN
    
    async def unregister_server(self, server_id: str) -> bool:
        """Unregister an MCP server.
        
        Args:
            server_id: ID of the server to unregister
            
        Returns:
            True if the server was unregistered, False if it wasn't found
        """
        async with self._lock:
            if server_id not in self.servers:
                return False
            
            # Close the connection if it exists
            if server_id in self.clients:
                client = self.clients.pop(server_id)
                if hasattr(client, "close"):
                    await client.close()
            
            # Close the transport
            if hasattr(transport_manager, 'close_transport'):
                await transport_manager.close_transport(server_id)
            
            # Remove the server
            del self.servers[server_id]
            return True
    
    def get_server(self, server_id: str) -> Optional[Server]:
        """Get a server by ID.
        
        Args:
            server_id: ID of the server to get
            
        Returns:
            The server, or None if not found
        """
        return self.servers.get(server_id)
    
    def get_servers(self) -> Dict[str, Server]:
        """Get all registered servers.
        
        Returns:
            Dictionary of server ID to Server objects
        """
        return self.servers.copy()
    
    def get_server_tools(self, server_id: str) -> List[Dict[str, Any]]:
        """Get tools provided by a server.
        
        Args:
            server_id: ID of the server
            
        Returns:
            List of tool information dictionaries
            
        Note:
            This is a placeholder that returns mock data. In a real implementation,
            this would query the MCP server for its available tools.
        """
        server = self.servers.get(server_id)
        if not server:
            return []
            
        # Mock tools - in a real implementation, this would query the MCP server
        return [
            {
                "name": "execute_command",
                "description": "Execute a shell command on the server",
                "version": "1.0.0",
                "tags": ["system", "admin"]
            },
            {
                "name": "list_files",
                "description": "List files in a directory",
                "version": "1.0.0",
                "tags": ["filesystem"]
            },
            {
                "name": "get_processes",
                "description": "Get list of running processes",
                "version": "1.0.0",
                "tags": ["system", "monitoring"]
            }
        ]
    
    async def start_server(self, server_id: str) -> bool:
        """Start an MCP server.
        
        Args:
            server_id: ID of the server to start
            
        Returns:
            True if the server was started successfully, False otherwise
        """
        server = self.servers.get(server_id)
        if not server:
            return False
            
        try:
            # Update server status
            server.status = ServerStatus.STARTING
            
            # In a real implementation, we would start the server process here
            # For now, we'll just simulate a successful start
            await asyncio.sleep(1)
            
            server.status = ServerStatus.ONLINE
            return True
            
        except Exception as e:
            logger.error("Failed to start server", server_id=server_id, error=str(e))
            server.status = ServerStatus.ERROR
            return False
    
    async def stop_server(self, server_id: str) -> bool:
        """Stop an MCP server.
        
        Args:
            server_id: ID of the server to stop
            
        Returns:
            True if the server was stopped successfully, False otherwise
        """
        server = self.servers.get(server_id)
        if not server:
            return False
            
        try:
            # Update server status
            server.status = ServerStatus.STOPPING
            
            # In a real implementation, we would stop the server process here
            # For now, we'll just simulate a successful stop
            await asyncio.sleep(0.5)
            
            # Close any open connections
            if server_id in self.clients:
                client = self.clients.pop(server_id)
                if hasattr(client, "close"):
                    await client.close()
            
            server.status = ServerStatus.OFFLINE
            return True
            
        except Exception as e:
            logger.error("Failed to stop server", server_id=server_id, error=str(e))
            server.status = ServerStatus.ERROR
            return False
    
    async def execute_tool(self, server_id: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on an MCP server.
        
        Args:
            server_id: ID of the server
            tool_name: Name of the tool to execute
            parameters: Tool parameters
            
        Returns:
            The tool execution result
            
        Raises:
            HTTPException: If the server or tool is not found, or if execution fails
        """
        server = self.servers.get(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with ID '{server_id}' not found",
            )
            
        if server.status != ServerStatus.ONLINE:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Server '{server_id}' is not online (status: {server.status})",
            )
        
        # In a real implementation, we would execute the tool via the MCP protocol
        # For now, we'll return a mock response
        return {
            "success": True,
            "result": f"Executed {tool_name} on {server_id} with params: {parameters}",
            "server_id": server_id,
            "tool": tool_name
        }
    
    async def _connect_server(self, server_id: str) -> bool:
        """Connect to an MCP server.
        
        Args:
            server_id: ID of the server to connect to
            
        Returns:
            True if the connection was successful, False otherwise
        """
        server = self.servers.get(server_id)
        if not server:
            return False
            
        # In a real implementation, we would establish a connection to the MCP server
        # For now, we'll simulate a successful connection
        server.status = ServerStatus.ONLINE
        return True
    
    async def close(self) -> None:
        """Close all server connections."""
        async with self._lock:
            # Close all clients
            for server_id, client in list(self.clients.items()):
                try:
                    if hasattr(client, "close"):
                        await client.close()
                except Exception as e:
                    logger.error("Error closing client", server_id=server_id, error=str(e))
            
            # Clear the clients dictionary
            self.clients.clear()
            
            # Update all server statuses to offline
            for server in self.servers.values():
                server.status = ServerStatus.OFFLINE
                if hasattr(client, "close"):
                    try:
                        await client.close()
                    except Exception as e:
                        logger.error(
                            "Error closing MCP client",
                            error=str(e),
                            exc_info=True,
                        )
            
            # Close all transports
            await transport_manager.close_all()
            
            # Clear collections
            self.clients.clear()
            self.servers.clear()

# Global server service instance
server_service = ServerService()

# Initialize the server service when the module is imported
async def init_server_service() -> None:
    """Initialize the server service."""
    try:
        # Import here to avoid circular imports
        from ...app.services.config_service import config_service
        
        # Register all servers from the config
        for server_id, config in config_service.get_all_servers().items():
            try:
                await server_service.register_server(server_id, config)
                logger.info("Registered MCP server", server_id=server_id)
            except Exception as e:
                logger.error("Failed to register MCP server", server_id=server_id, error=str(e))
                
    except Exception as e:
        logger.error("Failed to initialize server service", error=str(e))

# Run the initialization when the module is imported
if __name__ != "__main__":
    asyncio.create_task(init_server_service())
