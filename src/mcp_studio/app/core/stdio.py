"""STDIO transport for MCP server communication.

This module implements a robust STDIO transport for communicating with MCP servers
using JSON-RPC over standard input/output streams. It handles binary data, large
responses, and connection management.
"""

import asyncio
import json
import os
import sys
import time
import uuid
from asyncio import StreamReader, StreamWriter, TimeoutError as AsyncTimeoutError
from typing import Any, AsyncGenerator, Callable, Dict, List, Optional, Tuple, Union, cast

import structlog
from fastmcp import FastMCP, MCPClient, MCPError
from pydantic import ValidationError

from .config import settings
from .enums import ServerStatus
from .logging_utils import get_logger
from ..models.mcp import MCPServer, ToolExecutionRequest, ToolExecutionResult

logger = get_logger(__name__)

# Maximum message size (1MB)
MAX_MESSAGE_SIZE = 1024 * 1024

# Message delimiter for JSON-RPC over stdio
MESSAGE_DELIMITER = b"\n"

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
        """Read data from the subprocess stdout and feed it to the reader.
        
        This method handles the low-level reading of data from the subprocess stdout
        and feeds it to the StreamReader for processing. It handles connection resets
        and other I/O errors gracefully.
        """
        if self.process is None or self.process.stdout is None or self.reader is None:
            return
            
        buffer = bytearray()
        try:
            while True:
                # Read data in chunks
                chunk = await self.process.stdout.read(4096)
                if not chunk:  # EOF
                    break
                    
                # Add to buffer and process complete messages
                buffer.extend(chunk)
                
                # Process all complete messages in the buffer
                while True:
                    # Find message boundary
                    message_end = buffer.find(MESSAGE_DELIMITER)
                    if message_end == -1:
                        # No complete message yet, keep reading
                        if len(buffer) > MAX_MESSAGE_SIZE:
                            raise RuntimeError("Message size exceeds maximum allowed size")
                        break
                        
                    # Extract message
                    message_bytes = buffer[:message_end]
                    buffer = buffer[message_end + len(MESSAGE_DELIMITER):]
                    
                    # Feed complete message to reader
                    self.reader.feed_data(message_bytes + MESSAGE_DELIMITER)
        
        except (ConnectionResetError, BrokenPipeError):
            # Process was terminated or connection was reset
            logger.debug("Connection to MCP server reset", server_id=self.server.id)
        except Exception as e:
            logger.error(
                "Error reading from MCP server stdout",
                server_id=self.server.id,
                error=str(e),
                exc_info=True,
            )
        finally:
            # Signal EOF to the reader
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
        
        This method sends a JSON-RPC request to the MCP server and waits for a response.
        It handles timeouts, connection errors, and invalid responses.
        
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
        
        start_time = time.monotonic()
        request_id = str(uuid.uuid4())
        
        try:
            # Log the request
            logger.debug(
                "Executing tool",
                server_id=self.server.id,
                tool_name=tool_name,
                request_id=request_id,
                parameters=parameters,
            )
            
            # Prepare JSON-RPC request
            request = {
                "jsonrpc": "2.0",
                "id": request_id,
                "method": tool_name,
                "params": parameters or {},
            }
            
            # Send request and wait for response
            response = await asyncio.wait_for(
                self.client.call(tool_name, **parameters),
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
                result=response,
                execution_time=execution_time,
            )
            
        except AsyncTimeoutError as e:
            error_msg = f"Tool execution timed out after {timeout} seconds"
            logger.warning(
                error_msg,
                server_id=self.server.id,
                tool_name=tool_name,
                request_id=request_id,
            )
            raise TimeoutError(error_msg) from e
            
        except MCPError as e:
            error_msg = f"MCP error: {str(e)}"
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
    
    async def close(self) -> None:
        """Close the connection to the MCP server and clean up resources.
        
        This method ensures all resources are properly cleaned up, including:
        - Closing the writer
        - Terminating the subprocess
        - Cleaning up references
        """
        self._is_connected = False
        
        # Close writer if it exists
        if self.writer:
            try:
                if not self.writer.is_closing():
                    self.writer.close()
                    try:
                        await asyncio.wait_for(
                            self.writer.wait_closed(),
                            timeout=2.0
                        )
                    except (asyncio.TimeoutError, Exception) as e:
                        logger.debug(
                            "Timeout waiting for writer to close",
                            server_id=self.server.id,
                            error=str(e),
                        )
            except Exception as e:
                logger.warning(
                    "Error closing writer",
                    server_id=self.server.id,
                    error=str(e),
                    exc_info=True,
                )
            finally:
                self.writer = None
        
        # Terminate process if it exists
        if self.process:
            try:
                # Try to terminate gracefully first
                if self.process.returncode is None:
                    self.process.terminate()
                    
                    try:
                        # Wait for process to terminate
                        await asyncio.wait_for(
                            self.process.wait(),
                            timeout=5.0
                        )
                    except asyncio.TimeoutError:
                        # Force kill if it doesn't terminate in time
                        if self.process.returncode is None:
                            self.process.kill()
                            await self.process.wait()
                            
            except ProcessLookupError:
                # Process already terminated
                pass
                
            except Exception as e:
                logger.warning(
                    "Error terminating MCP server process",
                    server_id=self.server.id,
                    error=str(e),
                    exc_info=True,
                )
            finally:
                self.process = None
        
        # Clean up remaining references
        self.reader = None
        self.client = None
        
        logger.debug("Closed connection to MCP server", server_id=self.server.id)

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
