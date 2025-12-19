"""
Real MCP Discovery Service - Connects to actual MCP servers
Implements the MCP protocol for server discovery and tool execution
"""

import asyncio
import json
import os
import signal
import subprocess
import sys
import time
import uuid
from asyncio import StreamReader, StreamWriter, create_subprocess_exec, subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import aiofiles
from fastapi import HTTPException, status
from fastmcp import FastMCP, MCPClient, MCPError
from pydantic import ValidationError

from ..core.config import settings
from ..core.enums import ServerStatus, ServerType
from ..core.logging_utils import get_logger
from ..core.stdio import StdioTransport
from ..models.mcp import MCPServer, MCPTool, MCPToolParameter, ToolExecutionRequest, ToolExecutionResult

# Import config parser
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))
from mcp_config_parser import MCPConfigParser, MCPServerInfo

logger = get_logger(__name__)

class LiveMCPServer(MCPServer):
    """Extended MCPServer with runtime information and status."""
    
    def __init__(self, **data):
        super().__init__(**data)
        self.process: Optional[asyncio.subprocess.Process] = None
        self.transport = None
        self.last_seen: Optional[datetime] = None
        self.error_message: Optional[str] = None
        self.source: Optional[str] = None
    
    def update_status(self, status: ServerStatus, error: Optional[str] = None) -> None:
        """Update server status and error message."""
        self.status = status
        self.error_message = error
        self.updated_at = datetime.utcnow()
    
    async def start(self) -> bool:
        """Start the MCP server process."""
        if self.process and self.process.returncode is None:
            return True  # Already running
            
        try:
            self.update_status(ServerStatus.STARTING)
            
            # Prepare environment
            env = os.environ.copy()
            if self.env:
                env.update(self.env)
            
            # Start the process
            self.process = await asyncio.create_subprocess_exec(
                self.path,
                *self.args,
                cwd=self.cwd or os.getcwd(),
                env=env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024  # 1MB buffer
            )
            
            # Create transport
            self.transport = await transport_manager.get_transport(self)
            if not self.transport:
                raise RuntimeError("Failed to create transport for server")
            
            # Connect
            connected = await self.transport.connect()
            if not connected:
                raise RuntimeError("Failed to connect to server")
            
            # Verify connection by listing tools
            await self.discover_tools()
            self.update_status(ServerStatus.ONLINE)
            return True
            
        except Exception as e:
            self.update_status(ServerStatus.ERROR, str(e))
            logger.error(f"Failed to start server {self.id}: {e}", exc_info=True)
            await self.stop()
            return False
    
    async def stop(self) -> None:
        """Stop the MCP server process."""
        if self.process:
            try:
                if self.process.returncode is None:
                    self.process.terminate()
                    try:
                        await asyncio.wait_for(self.process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        self.process.kill()
                        await self.process.wait()
            except Exception as e:
                logger.warning(f"Error stopping server process {self.id}: {e}")
            finally:
                self.process = None
                self.transport = None
                self.update_status(ServerStatus.OFFLINE)
    
    async def discover_tools(self) -> List[MCPTool]:
        """Discover tools from the MCP server."""
        if not self.transport or not self.transport.is_connected():
            raise RuntimeError("Not connected to server")
        
        try:
            # Use MCP protocol to list tools
            response = await self.transport.execute_tool("tools/list", {})
            if not response or not response.get("success"):
                raise RuntimeError("Failed to list tools from server")
            
            # Parse tools from response
            tools_data = response.get("result", {})
            self.tools = []
            
            for tool_name, tool_info in tools_data.items():
                self.tools.append(
                    MCPTool(
                        name=tool_name,
                        description=tool_info.get("description", ""),
                        parameters=[
                            MCPToolParameter(
                                name=param_name,
                                type=param_info.get("type", "string"),
                                description=param_info.get("description", ""),
                                required=param_info.get("required", True),
                                default=param_info.get("default"),
                            )
                            for param_name, param_info in tool_info.get("parameters", {}).items()
                        ]
                    )
                )
            
            self.last_seen = datetime.utcnow()
            return self.tools
            
        except Exception as e:
            self.update_status(ServerStatus.ERROR, f"Tool discovery failed: {e}")
            logger.error(f"Tool discovery failed for {self.id}: {e}", exc_info=True)
            raise
    
    async def execute_tool(self, tool_name: str, parameters: Dict[str, Any]) -> ToolExecutionResult:
        """Execute a tool on this server."""
        if not self.transport or not self.transport.is_connected():
            # Try to reconnect if not connected
            if not await self.start():
                raise RuntimeError("Server is not available")
        
        try:
            start_time = asyncio.get_event_loop().time()
            response = await self.transport.execute_tool(tool_name, parameters)
            
            if not response or "success" not in response:
                raise RuntimeError(f"Invalid response from server: {response}")
            
            execution_time = asyncio.get_event_loop().time() - start_time
            
            return ToolExecutionResult(
                success=response.get("success", False),
                result=response.get("result"),
                error=response.get("error"),
                execution_time=execution_time
            )
            
        except Exception as e:
            self.update_status(ServerStatus.ERROR, f"Tool execution failed: {e}")
            logger.error(
                f"Tool execution failed: {tool_name} on {self.id}", 
                error=str(e), 
                exc_info=True
            )
            raise

class RealMCPDiscoveryService:
    """Real MCP discovery service that connects to actual servers."""
    
    def __init__(self):
        self.servers: Dict[str, LiveMCPServer] = {}
        self.config_parser = MCPConfigParser()
        self.discovery_running = False
        self.type = ServerType.PYTHON
        self._discovery_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        
    async def start_discovery(self) -> None:
        """Start the discovery service."""
        if self.discovery_running:
            logger.info("Discovery service already running")
            return
            
        self.discovery_running = True
        logger.info("Starting MCP discovery service...")
        
        # Initial discovery
        await self.discover_servers()
        
        # Start background task for periodic updates
        self._discovery_task = asyncio.create_task(self._periodic_discovery())
        
    async def stop_discovery(self) -> None:
        """Stop the discovery service and clean up resources."""
        self.discovery_running = False
        
        # Cancel the discovery task if it's running
        if self._discovery_task and not self._discovery_task.done():
            self._discovery_task.cancel()
            try:
                await self._discovery_task
            except asyncio.CancelledError:
                pass
        
        # Stop all server processes
        await self._stop_all_servers()
        logger.info("MCP discovery service stopped")
    
    async def _stop_all_servers(self) -> None:
        """Stop all managed server processes."""
        async with self._lock:
            for server in list(self.servers.values()):
                try:
                    await server.stop()
                except Exception as e:
                    logger.warning(f"Error stopping server {server.id}: {e}")
        
    async def discover_servers(self) -> List[LiveMCPServer]:
        """Discover all MCP servers from configurations."""
        try:
            logger.info("Discovering MCP servers...")
            
            # Parse all configs
            summary = self.config_parser.parse_all_configs()
            logger.info(f"Found {len(summary.servers)} servers in configs")
            
            # Track which servers we've seen in this discovery
            seen_server_ids = set()
            discovered = []
            
            # Process each server
            for server_info in summary.servers:
                try:
                    server_id = server_info.id
                    seen_server_ids.add(server_id)
                    
                    # Check if we already know about this server
                    existing = self.servers.get(server_id)
                    
                    if existing:
                        # Update existing server info
                        existing.name = server_info.name
                        existing.path = server_info.command
                        existing.args = server_info.args
                        existing.cwd = server_info.cwd
                        existing.env = server_info.env or {}
                        existing.source = server_info.source
                        
                        # If server was in error state, try to restart it
                        if existing.status == ServerStatus.ERROR:
                            await existing.start()
                        
                        discovered.append(existing)
                        continue
                    
                    # Create new server
                    server = LiveMCPServer(
                        id=server_id,
                        name=server_info.name,
                        path=server_info.command,
                        args=server_info.args or [],
                        cwd=server_info.cwd,
                        env=server_info.env or {},
                        type="python",  # Default type, can be overridden by server
                        status=ServerStatus.OFFLINE,
                        tools=[],
                        source=server_info.source,
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    
                    # Try to start the server
                    if await server.start():
                        self.servers[server_id] = server
                        discovered.append(server)
                        
                except Exception as e:
                    logger.error(f"Error processing server {server_info.id}: {e}", exc_info=True)
            
            # Clean up servers that are no longer in config
            await self._cleanup_servers(seen_server_ids)
            
            logger.info(f"Discovery complete: {len(discovered)} servers processed")
            return discovered
            
        except Exception as e:
            logger.error(f"Discovery failed: {e}", exc_info=True)
            return []
    
    async def _cleanup_servers(self, active_server_ids: set) -> None:
        """Stop and remove servers that are no longer in the config."""
        async with self._lock:
            for server_id in list(self.servers.keys()):
                if server_id not in active_server_ids:
                    server = self.servers.pop(server_id, None)
                    if server:
                        try:
                            await server.stop()
                        except Exception as e:
                            logger.warning(f"Error stopping removed server {server_id}: {e}")
    
    async def get_server(self, server_id: str) -> Optional[LiveMCPServer]:
        """Get a server by ID."""
        return self.servers.get(server_id)
    
    async def get_servers(self) -> List[LiveMCPServer]:
        """Get all discovered servers."""
        return list(self.servers.values())
    
    async def execute_tool(
        self, 
        server_id: str, 
        tool_name: str, 
        parameters: Dict[str, Any]
    ) -> ToolExecutionResult:
        """Execute a tool on a server."""
        server = self.servers.get(server_id)
        if not server:
            raise HTTPException(status_code=404, detail=f"Server {server_id} not found")
        
        if server.status != ServerStatus.ONLINE:
            # Try to start the server if it's not online
            if not await server.start():
                raise HTTPException(
                    status_code=503, 
                    detail=f"Server {server_id} is not available: {server.error_message}"
                )
        
        try:
            return await server.execute_tool(tool_name, parameters)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Tool execution failed: {str(e)}"
            )
    
    async def _discover_server_tools(self, server: LiveMCPServer) -> None:
        """Discover tools from a server and update its tool list."""
        try:
            if server.transport and server.transport.is_connected():
                tools = await server.discover_tools()
                logger.info(
                    f"Discovered {len(tools)} tools from {server.id}",
                    server_id=server.id,
                    tool_count=len(tools)
                )
                return tools
            return []
        except Exception as e:
            logger.error(
                f"Failed to discover tools from {server.id}: {e}",
                server_id=server.id,
                error=str(e),
                exc_info=True
            )
            server.update_status(ServerStatus.ERROR, f"Tool discovery failed: {e}")
            return []
    
    async def _periodic_discovery(self) -> None:
        """Periodically check for server updates and health."""
        while self.discovery_running:
            try:
                # Check server health and reconnect if needed
                await self._check_server_health()
                
                # Rediscover servers periodically
                if len(self.servers) == 0 or len([s for s in self.servers.values() 
                                                if s.status == ServerStatus.ONLINE]) == 0:
                    await self.discover_servers()
                
                # Wait before next check
                await asyncio.sleep(30)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error during periodic discovery: {e}", exc_info=True)
                await asyncio.sleep(10)  # Wait before retrying
    
    async def _check_server_health(self) -> None:
        """Check health of all servers and reconnect if needed."""
        async with self._lock:
            for server in list(self.servers.values()):
                try:
                    if server.status == ServerStatus.ONLINE:
                        # Try a simple ping to check if server is still responsive
                        try:
                            await server.transport.client.call("ping")
                            server.last_seen = datetime.utcnow()
                        except Exception as e:
                            logger.warning(f"Server {server.id} is not responding: {e}")
                            await server.stop()
                            await server.start()  # Try to restart
                    elif server.status in [ServerStatus.OFFLINE, ServerStatus.ERROR]:
                        # Try to restart offline/error servers
                        await server.start()
                except Exception as e:
                    logger.error(f"Error checking health of {server.id}: {e}", exc_info=True)
                    server.update_status(ServerStatus.ERROR, str(e))

# Import MCPClient if needed
# from ...core.client import MCPClient

# Global instance
discovery_service = RealMCPDiscoveryService()

# Compatibility functions for existing code
async def discover_mcp_servers() -> List[LiveMCPServer]:
    """Discover and return all MCP servers."""
    await discovery_service.discover_servers()
    return await discovery_service.get_servers()

def get_servers() -> List[LiveMCPServer]:
    """Get all discovered servers (synchronous wrapper)."""
    # Note: This is a synchronous wrapper around an async function
    # and should only be used in contexts where you can't use async
    loop = asyncio.get_event_loop()
    if loop.is_running():
        # If we're already in an event loop, create a new task
        task = loop.create_task(discovery_service.get_servers())
        return task.result() if task.done() else []
    else:
        # Otherwise, run the coroutine in the current loop
        return loop.run_until_complete(discovery_service.get_servers())

def get_server(server_id: str) -> Optional[LiveMCPServer]:
    """Get a server by ID (synchronous wrapper)."""
    loop = asyncio.get_event_loop()
    if loop.is_running():
        task = loop.create_task(discovery_service.get_server(server_id))
        return task.result() if task.done() else None
    else:
        return loop.run_until_complete(discovery_service.get_server(server_id))

async def execute_tool(
    server_id: str, 
    tool_name: str, 
    parameters: Dict[str, Any]
) -> Dict[str, Any]:
    """Execute a tool on an MCP server."""
    try:
        result = await discovery_service.execute_tool(server_id, tool_name, parameters)
        return {
            "success": result.success,
            "result": result.result,
            "error": result.error,
            "execution_time": result.execution_time,
            "timestamp": datetime.utcnow().isoformat()
        }
    except HTTPException as e:
        raise
    except Exception as e:
        logger.error(
            f"Unexpected error executing tool {tool_name} on {server_id}",
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}"
        )

# Initialize the discovery service when the module is imported
async def _init_discovery() -> None:
    """Initialize the discovery service."""
    try:
        await discovery_service.start_discovery()
    except Exception as e:
        logger.error(f"Failed to initialize discovery service: {e}", exc_info=True)

# Start the discovery service in the background
if __name__ != "__main__":
    asyncio.create_task(_init_discovery())
