"""STDIO transport for MCP server communication."""

import asyncio
import json
import logging
import sys
from asyncio import StreamReader, StreamWriter
from typing import Any, AsyncGenerator, Callable, Dict, Optional, Tuple, Union

import structlog
from fastmcp import FastMCP, MCPClient
from pydantic import ValidationError

from .config import settings
from ..models.mcp import MCPServer, ToolExecutionRequest, ToolExecutionResult

logger = structlog.get_logger(__name__)

class StdioTransport:
    """STDIO transport for MCP server communication."""
    
    def __init__(self, server: MCPServer):
        """Initialize the STDIO transport.
        
        Args:
            server: The MCP server to communicate with
        """
        self.server = server
        self.reader: Optional[StreamReader] = None
        self.writer: Optional[StreamWriter] = None
        self.process: Optional[asyncio.subprocess.Process] = None
        self.client: Optional[MCPClient] = None
        self._is_connected = False
        
    async def connect(self) -> bool:
        """Connect to the MCP server via STDIO.
        
        Returns:
            bool: True if connection was successful, False otherwise
        """
        if self._is_connected:
            return True
            
        try:
            # Create the subprocess
            self.process = await asyncio.create_subprocess_exec(
                sys.executable,
                self.server.path,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024,  # 1MB buffer
            )
            
            if self.process.stdin is None or self.process.stdout is None:
                raise RuntimeError("Failed to create subprocess pipes")
            
            self.reader = asyncio.StreamReader()
            self.writer = asyncio.StreamWriter(
                self.process.stdin,
                None,  # No transport
                None,   # No protocol
                self._on_connection_lost,
            )
            
            # Start reading from stdout
            asyncio.create_task(self._read_stdout())
            
            # Create MCP client
            self.client = MCPClient(
                reader=self.reader,
                writer=self.writer,
            )
            
            self._is_connected = True
            logger.info("Connected to MCP server via STDIO", server_id=self.server.id)
            return True
            
        except Exception as e:
            logger.error(
                "Failed to connect to MCP server",
                server_id=self.server.id,
                error=str(e),
                exc_info=True,
            )
            await self.close()
            return False
    
    async def _read_stdout(self) -> None:
        """Read data from the subprocess stdout and feed it to the reader."""
        if self.process is None or self.process.stdout is None:
            return
            
        try:
            while True:
                data = await self.process.stdout.read(4096)
                if not data:
                    break
                    
                if self.reader:
                    self.reader.feed_data(data)
        except ConnectionResetError:
            pass  # Process was terminated
        except Exception as e:
            logger.error(
                "Error reading from MCP server stdout",
                server_id=self.server.id,
                error=str(e),
                exc_info=True,
            )
        finally:
            if self.reader:
                self.reader.feed_eof()
    
    def _on_connection_lost(self, exc: Optional[Exception] = None) -> None:
        """Handle connection loss."""
        self._is_connected = False
        if exc:
            logger.warning(
                "Connection to MCP server lost",
                server_id=self.server.id,
                error=str(exc),
                exc_info=exc,
            )
        else:
            logger.info("Disconnected from MCP server", server_id=self.server.id)
    
    async def execute_tool(
        self,
        tool_name: str,
        parameters: Dict[str, Any],
        timeout: float = 30.0,
    ) -> ToolExecutionResult:
        """Execute a tool on the MCP server.
        
        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            timeout: Maximum time to wait for a response (in seconds)
            
        Returns:
            The tool execution result
            
        Raises:
            TimeoutError: If the operation times out
            RuntimeError: If there is an error executing the tool
        """
        if not self._is_connected or self.client is None:
            raise RuntimeError("Not connected to MCP server")
        
        try:
            # Create execution request
            request = ToolExecutionRequest(
                server_id=self.server.id,
                tool_name=tool_name,
                parameters=parameters,
                timeout=timeout,
            )
            
            # Execute the tool
            result = await asyncio.wait_for(
                self.client.call(tool_name, **parameters),
                timeout=timeout,
            )
            
            return ToolExecutionResult(
                success=True,
                result=result,
                execution_time=0.0,  # TODO: Measure actual execution time
            )
            
        except asyncio.TimeoutError:
            raise TimeoutError(f"Tool execution timed out after {timeout} seconds")
        except Exception as e:
            return ToolExecutionResult(
                success=False,
                error=str(e),
                execution_time=0.0,
            )
    
    async def close(self) -> None:
        """Close the connection to the MCP server."""
        if self.writer:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except Exception:
                pass
            
        if self.process:
            try:
                self.process.terminate()
                await asyncio.wait_for(self.process.wait(), timeout=5.0)
            except (asyncio.TimeoutError, ProcessLookupError):
                try:
                    self.process.kill()
                    await self.process.wait()
                except (ProcessLookupError, asyncio.CancelledError):
                    pass
            except Exception as e:
                logger.warning(
                    "Error terminating MCP server process",
                    server_id=self.server.id,
                    error=str(e),
                )
        
        self._is_connected = False
        self.reader = None
        self.writer = None
        self.process = None
        self.client = None

class StdioTransportManager:
    """Manager for STDIO transport connections to MCP servers."""
    
    def __init__(self):
        """Initialize the transport manager."""
        self.transports: Dict[str, StdioTransport] = {}
        self._lock = asyncio.Lock()
    
    async def get_transport(self, server: MCPServer) -> Optional[StdioTransport]:
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
                if transport._is_connected:
                    return transport
                else:
                    # Clean up old transport
                    await transport.close()
            
            # Create new transport
            transport = StdioTransport(server)
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
            for transport in list(self.transports.values()):
                await transport.close()
            self.transports.clear()

# Global transport manager instance
transport_manager = StdioTransportManager()
