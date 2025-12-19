"""STDIO transport for MCP server communication using FastMCP 2.11."""

import asyncio
import json
import logging
import os
import sys
import time
import uuid
from asyncio import StreamReader, StreamWriter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import structlog
from fastmcp import Client
from fastmcp.client.transports import StdioTransport
from pydantic import BaseModel

from .config import settings
from .enums import ServerStatus
from .logging_utils import get_logger
from ..models.mcp import MCPServer, ToolExecutionRequest, ToolExecutionResult

logger = get_logger(__name__)

# Constants for message handling
MESSAGE_DELIMITER = b'\n'
MAX_MESSAGE_SIZE = 1024 * 1024  # 1MB


class MCPStdioTransport:
    """Modern STDIO transport for MCP server communication using FastMCP 2.11."""

    def __init__(self, server: MCPServer):
        """Initialize the STDIO transport.

        Args:
            server: The MCP server to communicate with
        """
        self.server = server
        self.client: Optional[Client] = None
        self.transport: Optional[StdioTransport] = None
        self._is_connected = False
        self._process = None

    async def connect(self) -> bool:
        """Connect to the MCP server via STDIO using FastMCP 2.11.

        Returns:
            bool: True if connection was successful, False otherwise
        """
        if self._is_connected and self.client:
            return True

        try:
            # Validate server configuration
            if not self.server.path:
                logger.error("Server path is required for STDIO transport", server_id=self.server.id)
                return False

            server_path = Path(self.server.path)
            if not server_path.exists():
                logger.error("Server path does not exist", server_id=self.server.id, path=str(server_path))
                return False

            # Prepare environment variables
            env = os.environ.copy()
            if hasattr(self.server, 'env') and self.server.env:
                env.update(self.server.env)

            # Create STDIO transport
            self.transport = StdioTransport(
                command="python",
                args=[str(server_path)],
                env=env,
                cwd=str(server_path.parent) if hasattr(self.server, 'cwd') and self.server.cwd else None
            )

            # Create FastMCP client
            self.client = Client(self.transport)

            # Test connection
            async with self.client:
                # Initialize the connection
                await self.client.initialize()

                # Verify connection with a ping
                tools = await self.client.list_tools()
                logger.info(
                    "Connected to MCP server via STDIO",
                    server_id=self.server.id,
                    tools_count=len(tools)
                )

            self._is_connected = True
            return True

        except Exception as e:
            logger.error(
                "Failed to connect to MCP server",
                server_id=self.server.id,
                error=str(e),
                exc_info=True
            )
            await self.close()
            return False

    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout: float = 30.0,
    ) -> ToolExecutionResult:
        """Execute a tool on the MCP server.

        This method sends a tool execution request to the MCP server and waits for a response.
        It handles timeouts, connection errors, and invalid responses.

        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            timeout: Maximum time to wait for a response (in seconds)

        Returns:
            The tool execution result

        Raises:
            RuntimeError: If there is an error executing the tool
        """
        if not self._is_connected or not self.client:
            raise RuntimeError("Not connected to MCP server")

        start_time = time.monotonic()
        request_id = str(uuid.uuid4())

        try:
            # Log the request
            logger.debug(
                "Executing tool on MCP server",
                server_id=self.server.id,
                tool_name=tool_name,
                request_id=request_id,
                parameters=parameters,
            )

            # Execute tool using FastMCP client
            async with self.client:
                result = await asyncio.wait_for(
                    self.client.call_tool(tool_name, **parameters),
                    timeout=timeout,
                )

            # Calculate execution time
            execution_time = time.monotonic() - start_time

            # Log successful execution
            logger.debug(
                "Tool execution completed",
                server_id=self.server.id,
                tool_name=tool_name,
                request_id=request_id,
                execution_time=f"{execution_time:.3f}s",
            )

            return ToolExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
            )

        except asyncio.TimeoutError as e:
            error_msg = f"Tool execution timed out after {timeout} seconds"
            logger.warning(
                error_msg,
                server_id=self.server.id,
                tool_name=tool_name,
                request_id=request_id,
            )
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                execution_time=time.monotonic() - start_time,
            )

        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            logger.error(
                error_msg,
                server_id=self.server.id,
                tool_name=tool_name,
                request_id=request_id,
                exc_info=True,
            )
            return ToolExecutionResult(
                success=False,
                error=error_msg,
                execution_time=time.monotonic() - start_time,
            )

    async def list_tools(self) -> List[Dict[str, Any]]:
        """List available tools on the MCP server.

        Returns:
            List of tool information dictionaries

        Raises:
            RuntimeError: If not connected or tool listing fails
        """
        if not self._is_connected or not self.client:
            raise RuntimeError("Not connected to MCP server")

        try:
            async with self.client:
                tools = await self.client.list_tools()

                # Convert FastMCP tool objects to dictionaries
                tool_list = []
                for tool in tools:
                    tool_dict = {
                        "name": tool.name,
                        "description": tool.description,
                        "inputSchema": tool.inputSchema,
                    }
                    tool_list.append(tool_dict)

                logger.debug(
                    "Listed tools from MCP server",
                    server_id=self.server.id,
                    tool_count=len(tool_list)
                )

                return tool_list

        except Exception as e:
            error_msg = f"Failed to list tools: {str(e)}"
            logger.error(
                error_msg,
                server_id=self.server.id,
                exc_info=True
            )
            raise RuntimeError(error_msg) from e

    async def ping(self) -> bool:
        """Ping the MCP server to check if it's responsive.

        Returns:
            bool: True if server responds, False otherwise
        """
        if not self._is_connected or not self.client:
            return False

        try:
            async with self.client:
                # Try to list tools as a basic connectivity check
                await self.client.list_tools()
                return True

        except Exception as e:
            logger.warning(
                "Ping failed",
                server_id=self.server.id,
                error=str(e)
            )
            return False

    async def get_server_info(self) -> Dict[str, Any]:
        """Get server information and capabilities.

        Returns:
            Dictionary containing server information
        """
        if not self._is_connected or not self.client:
            raise RuntimeError("Not connected to MCP server")

        try:
            async with self.client:
                # Get basic server info
                tools = await self.client.list_tools()

                server_info = {
                    "server_id": self.server.id,
                    "name": self.server.name,
                    "version": getattr(self.server, 'version', '1.0.0'),
                    "status": "connected",
                    "tools_count": len(tools),
                    "tools": [
                        {
                            "name": tool.name,
                            "description": tool.description
                        }
                        for tool in tools
                    ],
                    "capabilities": {
                        "tools": True,
                        "resources": True,  # Assume supported
                        "prompts": True,    # Assume supported
                    }
                }

                return server_info

        except Exception as e:
            logger.error(
                "Failed to get server info",
                server_id=self.server.id,
                error=str(e),
                exc_info=True
            )
            raise RuntimeError(f"Failed to get server info: {str(e)}") from e

    async def close(self) -> None:
        """Close the connection to the MCP server and clean up resources.

        This method ensures all resources are properly cleaned up, including:
        - Closing the FastMCP client
        - Cleaning up transport
        - Resetting connection state
        """
        self._is_connected = False

        # Close FastMCP client
        if self.client:
            try:
                # FastMCP client handles cleanup automatically when used with async context
                # No explicit close needed for FastMCP 2.11 client
                pass
            except Exception as e:
                logger.warning(
                    "Error closing FastMCP client",
                    server_id=self.server.id,
                    error=str(e)
                )
            finally:
                self.client = None

        # Clean up transport
        if self.transport:
            try:
                # Transport cleanup is handled by FastMCP
                pass
            except Exception as e:
                logger.warning(
                    "Error cleaning up transport",
                    server_id=self.server.id,
                    error=str(e)
                )
            finally:
                self.transport = None

        logger.debug("Closed connection to MCP server", server_id=self.server.id)


class MCPTransportManager:
    """Manager for MCP transport connections using FastMCP 2.11."""

    def __init__(self):
        """Initialize the transport manager."""
        self.transports: Dict[str, MCPStdioTransport] = {}
        self._lock = asyncio.Lock()

    async def get_transport(self, server: MCPServer) -> Optional[MCPStdioTransport]:
        """Get or create a transport for the given server.

        Args:
            server: The MCP server to get a transport for

        Returns:
            The transport, or None if connection failed
        """
        if not server.path:
            logger.warning("Cannot create transport for server without path", server_id=server.id)
            return None

        async with self._lock:
            if server.id in self.transports:
                transport = self.transports[server.id]
                if await transport.ping():
                    return transport
                else:
                    # Clean up old transport
                    await transport.close()
                    del self.transports[server.id]

            # Create new transport
            transport = MCPStdioTransport(server)
            if await transport.connect():
                self.transports[server.id] = transport
                return transport
            return None

    async def close_transport(self, server_id: str) -> None:
        """Close the transport for a server.

        Args:
            server_id: ID of the server to close the transport for
        """
        async with self._lock:
            if server_id in self.transports:
                transport = self.transports.pop(server_id)
                await transport.close()

    async def close_all(self) -> None:
        """Close all transports."""
        async with self._lock:
            for transport in self.transports.values():
                try:
                    await transport.close()
                except Exception as e:
                    logger.error("Error closing transport", error=str(e))
            self.transports.clear()

    async def get_all_server_info(self) -> Dict[str, Dict[str, Any]]:
        """Get information about all connected servers.

        Returns:
            Dictionary mapping server IDs to their information
        """
        server_info = {}
        async with self._lock:
            for server_id, transport in self.transports.items():
                try:
                    if transport._is_connected:
                        info = await transport.get_server_info()
                        server_info[server_id] = info
                    else:
                        server_info[server_id] = {
                            "server_id": server_id,
                            "status": "disconnected"
                        }
                except Exception as e:
                    server_info[server_id] = {
                        "server_id": server_id,
                        "status": "error",
                        "error": str(e)
                    }

        return server_info


# Global transport manager instance
transport_manager = MCPTransportManager()


# Compatibility aliases for backward compatibility
StdioTransport = MCPStdioTransport
StdioTransportManager = MCPTransportManager
