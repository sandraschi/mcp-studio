"""
MCP Discovery Service - Implements real MCP server discovery and management.
Uses FastMCP 2.11+ for server connections and tool execution.
"""

import asyncio
import json
import logging
import os
import signal
import sys
import uuid
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import aiofiles
from fastapi import HTTPException, status
from fastmcp import MCPClient, MCPError, MCPServerInfo, MCPTool, MCPToolParameter
from pydantic import BaseModel, Field, validator

from ..core.config import settings
from ..core.enums import ServerStatus, ServerType
from ..core.logging_utils import get_logger
from ..core.stdio import StdioTransport

logger = get_logger(__name__)

class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""
    id: str = Field(..., description="Unique identifier for the server")
    name: str = Field(..., description="Display name for the server")
    command: str = Field(..., description="Command to start the server")
    args: List[str] = Field(default_factory=list, description="Command line arguments")
    cwd: Optional[str] = Field(None, description="Working directory")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")
    source: str = Field("unknown", description="Source of this configuration")
    auto_start: bool = Field(True, description="Whether to start this server automatically")
    
    @validator('id')
    def validate_id(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Server ID must be a non-empty string")
        return v

class MCPDiscoveryService:
    """Service for discovering and managing MCP servers."""
    
    def __init__(self):
        self.servers: Dict[str, 'MCPClient'] = {}
        self.server_configs: Dict[str, MCPServerConfig] = {}
        self.discovery_running = False
        self._discovery_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
    
    async def start_discovery(self) -> None:
        """Start the discovery service."""
        if self.discovery_running:
            return
            
        self.discovery_running = True
        self._discovery_task = asyncio.create_task(self._discovery_loop())
        logger.info("MCP Discovery Service started")
    
    async def stop_discovery(self) -> None:
        """Stop the discovery service and clean up resources."""
        self.discovery_running = False
        if self._discovery_task:
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
        
        # Clean up all server connections
        for server_id in list(self.servers.keys()):
            await self._disconnect_server(server_id)
        
        logger.info("MCP Discovery Service stopped")
    
    async def add_server(self, config: MCPServerConfig) -> bool:
        """Add a new MCP server configuration."""
        async with self._lock:
            if config.id in self.server_configs:
                logger.warning(f"Server with ID {config.id} already exists")
                return False
                
            self.server_configs[config.id] = config
            logger.info(f"Added MCP server {config.name} (ID: {config.id})")
            
            # Auto-start the server if configured to do so
            if config.auto_start:
                await self._connect_server(config.id)
                
            return True
    
    async def remove_server(self, server_id: str) -> bool:
        """Remove an MCP server and disconnect it."""
        async with self._lock:
            if server_id not in self.server_configs:
                return False
                
            await self._disconnect_server(server_id)
            del self.server_configs[server_id]
            logger.info(f"Removed MCP server {server_id}")
            return True
    
    async def get_servers(self) -> List[Dict[str, Any]]:
        """Get information about all discovered servers."""
        servers = []
        for server_id, client in self.servers.items():
            try:
                server_info = await self._get_server_info(server_id)
                servers.append(server_info)
            except Exception as e:
                logger.error(f"Failed to get info for server {server_id}: {e}")
                servers.append({
                    "id": server_id,
                    "status": "error",
                    "error": str(e)
                })
        return servers
    
    async def execute_tool(
        self, 
        server_id: str, 
        tool_name: str, 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute a tool on an MCP server."""
        if server_id not in self.servers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server {server_id} not found"
            )
            
        client = self.servers[server_id]
        try:
            result = await client.call_tool(tool_name, parameters)
            return {"status": "success", "result": result}
        except MCPError as e:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e)
            )
        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to execute tool: {str(e)}"
            )
    
    async def _discovery_loop(self) -> None:
        """Background task for server discovery and health checks."""
        while self.discovery_running:
            try:
                # Reconnect to disconnected servers
                for server_id in list(self.server_configs.keys()):
                    if server_id not in self.servers:
                        await self._connect_server(server_id)
                
                # Check server health
                await self._check_server_health()
                
            except Exception as e:
                logger.error(f"Error in discovery loop: {e}", exc_info=True)
            
            # Wait before next iteration
            await asyncio.sleep(30)  # Check every 30 seconds
    
    async def _connect_server(self, server_id: str) -> bool:
        """Connect to an MCP server."""
        if server_id in self.servers:
            return True  # Already connected
            
        config = self.server_configs.get(server_id)
        if not config:
            logger.error(f"No config found for server {server_id}")
            return False
            
        try:
            # Create transport for the server
            transport = StdioTransport(
                command=config.command,
                args=config.args,
                cwd=config.cwd,
                env=config.env
            )
            
            # Create MCP client
            client = MCPClient(transport)
            
            # Connect to the server
            await client.connect()
            
            # Verify connection by listing tools
            tools = await client.list_tools()
            logger.info(f"Connected to MCP server {config.name} with {len(tools)} tools")
            
            # Store the client
            self.servers[server_id] = client
            return True
            
        except Exception as e:
            logger.error(f"Failed to connect to MCP server {config.name}: {e}", exc_info=True)
            return False
    
    async def _disconnect_server(self, server_id: str) -> None:
        """Disconnect from an MCP server."""
        if server_id not in self.servers:
            return
            
        client = self.servers[server_id]
        try:
            await client.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting from server {server_id}: {e}")
        finally:
            del self.servers[server_id]
    
    async def _get_server_info(self, server_id: str) -> Dict[str, Any]:
        """Get information about a server."""
        if server_id not in self.server_configs:
            raise ValueError(f"Unknown server: {server_id}")
            
        config = self.server_configs[server_id]
        client = self.servers.get(server_id)
        
        info = {
            "id": server_id,
            "name": config.name,
            "source": config.source,
            "status": "online" if client else "offline",
            "tools": [],
            "last_seen": datetime.now(timezone.utc).isoformat(),
            "config": config.dict()
        }
        
        if client:
            try:
                tools = await client.list_tools()
                info["tools"] = [{"name": t.name, "description": t.description} for t in tools]
            except Exception as e:
                logger.error(f"Failed to list tools for server {server_id}: {e}")
                info["error"] = str(e)
                info["status"] = "error"
        
        return info
    
    async def _check_server_health(self) -> None:
        """Check the health of all connected servers."""
        for server_id in list(self.servers.keys()):
            client = self.servers[server_id]
            try:
                # Simple ping to check if server is responsive
                await client.ping()
            except Exception as e:
                logger.warning(f"Server {server_id} is not responding: {e}")
                await self._disconnect_server(server_id)

# Global instance for easy access
discovery_service = MCPDiscoveryService()

async def start_discovery():
    """Start the MCP discovery service."""
    await discovery_service.start_discovery()

async def stop_discovery():
    """Stop the MCP discovery service."""
    await discovery_service.stop_discovery()

def get_discovery_service() -> MCPDiscoveryService:
    """Get the global discovery service instance."""
    return discovery_service
