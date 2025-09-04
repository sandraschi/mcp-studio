"""Service for managing MCP server connections and tool execution."""

import asyncio
import json
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, cast

from fastapi import HTTPException, status
from fastmcp import FastMCP

from ...app.core.logging_utils import get_logger
from ...app.core.types import (
    MCPServerConfig,
    ToolExecutionRequest as ToolExecutionRequestType,
    ToolExecutionResult as ToolExecutionResultType
)
from ...app.core.config import settings
from ...app.core.stdio import StdioTransport, transport_manager
from ...app.core.enums import ServerStatus, ServerType
from ...app.models.server import Server
from ..models.mcp import MCPTool, MCPToolParameter

logger = get_logger(__name__)

class ServerService:
    """
    Service for managing MCP server connections and tool execution.

    This class provides methods to manage MCP servers, execute tools on them,
    and handle server lifecycle events. It maintains a registry of servers and
    their connections, and provides thread-safe operations for concurrent access.
    """

    def __init__(self) -> None:
        """Initialize the server service with empty server and client registries."""
        self.servers: Dict[str, Server] = {}
        self.clients: Dict[str, FastMCP] = {}
        self._lock: asyncio.Lock = asyncio.Lock()
        logger.info("Initialized ServerService")

    async def register_server(self, server_id: str, config: Dict[str, Any]) -> Server:
        """Register a new MCP server from configuration.

        Args:
            server_id: The unique identifier for the server
            config: Dictionary containing server configuration with the following keys:
                - name: Display name of the server (optional)
                - type: Server type (e.g., 'python', 'docker', 'node') (optional)
                - command: List of command arguments to start the server
                - args: Additional command-line arguments (optional)
                - cwd: Working directory for the server process (optional)
                - env: Environment variables for the server process (optional)
                - description: Human-readable description of the server (optional)

        Returns:
            Server: The newly registered server instance

        Raises:
            HTTPException:
                - 400: If the server ID already exists or configuration is invalid
                - 422: If the configuration fails validation
                - 500: If an unexpected error occurs during registration
        """
        logger.debug("Registering new server", server_id=server_id, config=config)

        async with self._lock:
            # Check for existing server with the same ID
            if server_id in self.servers:
                error_msg = f"Server with ID '{server_id}' already exists"
                logger.warning(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=error_msg
                )

            try:
                # Create server instance from config with validation
                server = Server(
                    id=server_id,
                    name=config.get('name', f"Server-{server_id}"),
                    type=self._detect_server_type(config),
                    status=ServerStatus.OFFLINE,
                    command=config.get('command', []),
                    args=config.get('args', []),
                    cwd=config.get('cwd'),
                    env=config.get('env', {}),
                    description=config.get('description', '')
                )

                # Add to server registry
                self.servers[server_id] = server
                logger.info(
                    "Registered new server",
                    server_id=server_id,
                    server_name=server.name,
                    server_type=server.type
                )
                return server

            except ValidationError as e:
                error_msg = f"Invalid server configuration: {str(e)}"
                logger.error(error_msg, errors=e.errors() if hasattr(e, 'errors') else str(e))
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"error": "Validation failed", "details": str(e)}
                ) from e

            except Exception as e:
                error_msg = f"Failed to register server '{server_id}': {str(e)}"
                logger.error(error_msg, exc_info=True)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                ) from e

    def _detect_server_type(self, config: Dict[str, Any]) -> ServerType:
        """Detect the server type from its configuration.

        This method attempts to determine the server type from the configuration.
        It first checks the 'type' field, and if not specified or invalid, it tries
        to infer the type from the command used to start the server.

        Args:
            config: Dictionary containing server configuration with optional keys:
                - type: Explicit server type (e.g., 'python', 'node', 'docker')
                - command: Command used to start the server (for type inference)

        Returns:
            ServerType: The detected server type, or ServerType.UNKNOWN if detection fails

        Note:
            The method is case-insensitive when matching server types.
        """
        logger.debug("Detecting server type from config", config=config)

        # Try to get the server type from the config
        server_type_str = str(config.get("type", "")).strip().lower()

        # If type is explicitly provided and valid, use it
        if server_type_str:
            try:
                server_type = ServerType(server_type_str)
                logger.debug("Using explicit server type", type=server_type)
                return server_type
            except ValueError:
                logger.warning(
                    "Invalid server type specified, attempting to infer from command",
                    specified_type=server_type_str
                )

        # If type is not specified or invalid, try to infer from command
        command = config.get("command", [])
        if not command or not isinstance(command, list) or not command[0]:
            logger.warning("No command specified, using UNKNOWN server type")
            return ServerType.UNKNOWN

        # Normalize the command for comparison
        cmd = command[0].lower()
        logger.debug("Inferring server type from command", command=cmd)

        # Check for common server commands
        if any(x in cmd for x in ["python", "python3", "py"]):
            detected_type = ServerType.PYTHON
        elif any(x in cmd for x in ["node", "nodejs", "npm", "yarn", "npx"]):
            detected_type = ServerType.NODE
        elif any(x in cmd for x in ["docker", "podman", "docker-compose"]):
            detected_type = ServerType.DOCKER
        else:
            detected_type = ServerType.UNKNOWN

        logger.info(
            "Inferred server type from command",
            command=cmd,
            detected_type=detected_type
        )
        return detected_type

    async def unregister_server(self, server_id: str) -> bool:
        """Unregister an MCP server and clean up its resources.

        This method:
        1. Removes the server from the internal registry
        2. Closes any active client connections
        3. Cleans up transport resources

        Args:
            server_id: The unique identifier of the server to unregister

        Returns:
            bool:
                - True if the server was successfully unregistered
                - False if no server with the given ID was found

        Raises:
            HTTPException:
                - 500: If an error occurs during resource cleanup
        """
        logger.info("Unregistering server", server_id=server_id)

        async with self._lock:
            # Check if server exists
            if server_id not in self.servers:
                logger.debug("Server not found during unregistration", server_id=server_id)
                return False

            server_name = self.servers[server_id].name

            try:
                # Close and remove client connection if it exists
                if server_id in self.clients:
                    try:
                        client = self.clients.pop(server_id)
                        if hasattr(client, "close"):
                            logger.debug("Closing client connection", server_id=server_id)
                            await client.close()
                    except Exception as e:
                        logger.error(
                            "Error closing client connection",
                            server_id=server_id,
                            error=str(e),
                            exc_info=True
                        )

                # Close transport if transport manager is available
                if hasattr(transport_manager, 'close_transport'):
                    try:
                        logger.debug("Closing transport", server_id=server_id)
                        await transport_manager.close_transport(server_id)
                    except Exception as e:
                        logger.error(
                            "Error closing transport",
                            server_id=server_id,
                            error=str(e),
                            exc_info=True
                        )
                        # Continue with unregistration even if transport close fails

                # Remove the server from the registry
                del self.servers[server_id]

                logger.info(
                    "Successfully unregistered server",
                    server_id=server_id,
                    server_name=server_name
                )
                return True

            except Exception as e:
                error_msg = f"Failed to unregister server '{server_id}': {str(e)}"
                logger.error(
                    error_msg,
                    server_id=server_id,
                    error=str(e),
                    exc_info=True
                )
                # Don't raise the exception, just log it and continue
                return False

    def get_server(self, server_id: str) -> Optional[Server]:
        """Retrieve a server by its unique identifier.

        This is a thread-safe method that returns a copy of the server object
        to prevent external modifications to the internal server state.

        Args:
            server_id: The unique identifier of the server to retrieve

        Returns:
            Optional[Server]:
                - A copy of the Server object if found
                - None if no server with the given ID exists

        Example:
            ```python
            # Get a server by ID
            server = await server_service.get_server("my-server-1")
            if server:
                print(f"Found server: {server.name}")
            else:
                print("Server not found")
            ```
        """
        if not server_id or not isinstance(server_id, str):
            logger.warning("Invalid server ID provided", server_id=server_id)
            return None

        # Return a copy to prevent external modifications to our internal state
        server = self.servers.get(server_id)
        if server:
            logger.debug("Retrieved server", server_id=server_id, server_name=server.name)
            return server.copy(deep=True)

        logger.debug("Server not found", server_id=server_id)
        return None

    def get_servers(self) -> Dict[str, Server]:
        """Retrieve a copy of all registered servers.

        This method returns a deep copy of the internal server registry to ensure
        thread safety and prevent external modifications to the internal state.

        Returns:
            Dict[str, Server]:
                A dictionary mapping server IDs to Server objects.
                Returns an empty dictionary if no servers are registered.

        Example:
            ```python
            # Get all servers
            servers = server_service.get_servers()
            for server_id, server in servers.items():
                print(f"{server_id}: {server.name} ({server.status.value})")
            ```

        Note:
            The returned dictionary is a deep copy, so modifications to the
            returned servers will not affect the internal registry.
        """
        # Return a deep copy to ensure thread safety and prevent external modifications
        servers_copy = {}
        for server_id, server in self.servers.items():
            try:
                servers_copy[server_id] = server.copy(deep=True)
            except Exception as e:
                logger.error(
                    "Failed to copy server data",
                    server_id=server_id,
                    error=str(e),
                    exc_info=True
                )
                # If copy fails, return the original (but still make a shallow copy)
                servers_copy[server_id] = server.copy()

        logger.debug("Retrieved all servers", server_count=len(servers_copy))
        return servers_copy

    async def get_server_tools(self, server_id: str) -> List[Dict[str, Any]]:
        """Get tools provided by a server.

        Args:
            server_id: ID of the server

        Returns:
            List of tool information dictionaries

        Raises:
            HTTPException: If the server is not found or not online
        """
        server = self.servers.get(server_id)
        if not server:
            error_msg = f"Server with ID '{server_id}' not found"
            logger.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )

        if server.status != ServerStatus.ONLINE:
            error_msg = f"Server '{server_id}' is not online (status: {server.status})"
            logger.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        try:
            # Create server config
            server_config = MCPServerConfig(
                id=server.id,
                name=server.name,
                path=server.command[0] if server.command else None,
                args=server.args,
                cwd=server.cwd,
                env=server.env
            )

            # Get transport for the server with timeout
            try:
                transport = await asyncio.wait_for(
                    transport_manager.get_transport(server_config),
                    timeout=settings.TRANSPORT_TIMEOUT
                )
            except asyncio.TimeoutError:
                error_msg = f"Timeout while connecting to server '{server_id}'"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=error_msg
                )

            if not transport or not hasattr(transport, 'client') or not transport.client:
                error_msg = f"Failed to connect to server '{server_id}': No transport or client available"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=error_msg
                )

            # Get tools from the server with timeout
            try:
                tools_response = await asyncio.wait_for(
                    transport.client.call("tools/list"),
                    timeout=settings.TOOL_EXECUTION_TIMEOUT
                )
            except asyncio.TimeoutError:
                error_msg = f"Timeout while fetching tools from server '{server_id}'"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=error_msg
                )

            # Validate response format
            if not isinstance(tools_response, dict) or "tools" not in tools_response:
                error_msg = f"Invalid response format from server '{server_id}'"
                logger.error(error_msg, response=tools_response)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )

            tools = tools_response.get("tools", [])
            logger.info("Retrieved tools from server", server_id=server_id, tool_count=len(tools))
            return tools

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise

        except Exception as e:
            error_msg = f"Failed to get tools from server '{server_id}': {str(e)}"
            logger.error(
                error_msg,
                server_id=server_id,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

    async def execute_tool(self, server_id: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on the specified server.

        Args:
            server_id: ID of the server to execute the tool on
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool

        Returns:
            Execution result with status, result, and metadata

        Raises:
            HTTPException: If the server is not found or tool execution fails

        This method provides comprehensive error handling for async operations,
        including timeouts, connection errors, and invalid responses.
        """
        logger.info(
            "Executing tool",
            server_id=server_id,
            tool_name=tool_name,
            parameters=parameters
        )

        # Get server with validation
        server = self.servers.get(server_id)
        if not server:
            error_msg = f"Server with ID '{server_id}' not found"
            logger.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )

        if server.status != ServerStatus.ONLINE:
            error_msg = f"Server '{server_id}' is not online (status: {server.status})"
            logger.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Create MCP server configuration
        mcp_server = MCPServer(
            id=server.id,
            name=server.name,
            path=server.command[0] if server.command else None,
            args=server.args,
            cwd=server.cwd,
            env=server.env
        )

        try:
            # Get transport with timeout
            try:
                transport = await asyncio.wait_for(
                    transport_manager.get_transport(mcp_server),
                    timeout=settings.TRANSPORT_TIMEOUT
                )
            except asyncio.TimeoutError:
                error_msg = f"Timeout while connecting to server '{server_id}'"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=error_msg
                )

            if not transport or not transport.client:
                error_msg = f"Failed to connect to server '{server_id}': No transport or client available"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=error_msg
                )

            # Execute the tool with timeout
            try:
                result = await asyncio.wait_for(
                    transport.client.call(
                        "tools/execute",
                        tool=tool_name,
                        parameters=parameters
                    ),
                    timeout=settings.TOOL_EXECUTION_TIMEOUT
                )
            except asyncio.TimeoutError:
                error_msg = f"Tool execution timed out for '{tool_name}' on server '{server_id}'"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=error_msg
                )

            # Validate response format
            if not isinstance(result, dict):
                error_msg = f"Invalid response format from server '{server_id}': {type(result).__name__} received, expected dict"
                logger.error(error_msg, response=result)
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=error_msg
                )

            logger.info(
                "Tool executed successfully",
                server_id=server_id,
                tool_name=tool_name,
                result=result.get('status', 'unknown')
            )
            return result

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise

        except Exception as e:
            error_msg = f"Failed to execute tool '{tool_name}' on server '{server_id}': {str(e)}"
            logger.error(
                error_msg,
                server_id=server_id,
                tool_name=tool_name,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

    async def start_server(self, server_id: str) -> bool:
        """Start an MCP server.

        Args:
            server_id: ID of the server to start

        Returns:
            True if the server was started successfully, False otherwise

        Raises:
            HTTPException: If the server is not found or fails to start
        """
        server = self.servers.get(server_id)
        if not server:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Server with ID '{server_id}' not found"
            )

        if server.status == ServerStatus.ONLINE:
            logger.warning("Server is already running", server_id=server_id)
            return True

        try:
            # Update server status
            server.status = ServerStatus.STARTING

            # Create the server process
            process = await asyncio.create_subprocess_exec(
                *server.command,
                *server.args,
                cwd=server.cwd,
                env=server.env,
                stdin=asyncio.subprocess.PIPE,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                limit=1024 * 1024  # 1MB buffer
            )

            if process.returncode is not None and process.returncode != 0:
                error = await process.stderr.read()
                raise RuntimeError(
                    f"Server process failed to start with return code {process.returncode}: {error.decode()}"
                )

            # Wait for the server to be ready (implement proper health check)
            max_attempts = 10
            for attempt in range(max_attempts):
                try:
                    transport = await transport_manager.get_transport(MCPServer(
                        id=server.id,
                        name=server.name,
                        path=server.command[0] if server.command else None,
                        args=server.args,
                        cwd=server.cwd,
                        env=server.env
                    ))

                    if transport and transport.client:
                        # Try to ping the server
                        await transport.client.call("ping")
                        server.status = ServerStatus.ONLINE
                        logger.info("Server started successfully", server_id=server_id)
                        return True

                except Exception:
                    if attempt == max_attempts - 1:
                        raise
                    await asyncio.sleep(0.5)

            # If we get here, the server didn't start properly
            raise RuntimeError("Server failed to start within the expected time")

        except Exception as e:
            server.status = ServerStatus.ERROR
            logger.error(
                "Failed to start server",
                server_id=server_id,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to start server '{server_id}': {str(e)}"
            )

    async def stop_server(self, server_id: str) -> bool:
        """Stop an MCP server.

        This method attempts to gracefully stop a running server by:
        1. Marking the server as STOPPING
        2. Closing any open client connections
        3. Closing the transport
        4. Terminating the server process

        Args:
            server_id: The unique identifier of the server to stop

        Returns:
            bool:
                - True if the server was stopped successfully
                - False if the server was not found or already stopped

        Raises:
            HTTPException:
                - 500: If an error occurs while stopping the server
        """
        logger.info("Stopping server", server_id=server_id)

        # Get the server
        server = self.get_server(server_id)
        if not server:
            logger.warning("Cannot stop non-existent server", server_id=server_id)
            return False

        if server.status == ServerStatus.OFFLINE:
            logger.info("Server is already stopped", server_id=server_id)
            return False

        try:
            # Update status to stopping
            server.status = ServerStatus.STOPPING

            # Close any open connections
            if server_id in self.clients:
                try:
                    client = self.clients.pop(server_id)
                    if hasattr(client, "close"):
                        await client.close()
                except Exception as e:
                    logger.warning(
                        "Error closing client connection",
                        server_id=server_id,
                        error=str(e)
                    )

            # Close the transport
            if hasattr(transport_manager, 'close_transport'):
                try:
                    await transport_manager.close_transport(server_id)
                except Exception as e:
                    logger.warning(
                        "Error closing transport",
                        server_id=server_id,
                        error=str(e)
                    )

            # Terminate the server process if it's still running
            transport = getattr(transport_manager, 'transports', {}).get(server_id)
            if transport and hasattr(transport, 'process') and transport.process:
                try:
                    # Try to terminate gracefully first
                    transport.process.terminate()
                    try:
                        # Wait for the process to terminate
                        await asyncio.wait_for(transport.process.wait(), timeout=5.0)
                    except asyncio.TimeoutError:
                        # Force kill if it doesn't terminate in time
                        transport.process.kill()
                        await transport.process.wait()
                except ProcessLookupError:
                    # Process already terminated
                    pass
                except Exception as e:
                    logger.warning(
                        "Error stopping server process",
                        server_id=server_id,
                        error=str(e),
                        exc_info=True
                    )

            # Update status
            server.status = ServerStatus.OFFLINE
            logger.info("Server stopped successfully", server_id=server_id)
            return True

        except Exception as e:
            server.status = ServerStatus.ERROR
            logger.error(
                "Failed to stop server",
                server_id=server_id,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to stop server '{server_id}': {str(e)}"
            )

    async def execute_tool(self, server_id: str, tool_name: str, parameters: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a tool on the specified server with comprehensive error handling.

        This method handles the entire tool execution flow including:
        1. Validating the server exists and is online
        2. Establishing a connection to the server
        3. Executing the tool with proper timeout handling
        4. Formatting the response
        5. Handling various error conditions

        Args:
            server_id: The unique identifier of the server to execute the tool on
            tool_name: The name of the tool to execute (must be registered on the server)
            parameters: A dictionary of parameters to pass to the tool

        Returns:
            Dict[str, Any]: A dictionary containing:
                - status: "success" or "error"
                - result: The tool's return value (on success)
                - metadata: Additional execution metadata including timing information
                - error: Error details (if execution failed)

        Raises:
            HTTPException:
                - 400: If the server is not online or parameters are invalid
                - 404: If the server or tool is not found
                - 503: If unable to connect to the server
                - 504: If the tool execution times out
                - 500: For other unexpected errors

        Example:
            ```python
            # Example usage
            try:
                result = await server_service.execute_tool(
                    server_id="my-server-1",
                    tool_name="calculate_sum",
                    parameters={"a": 5, "b": 7}
                )
                print(f"Tool result: {result['result']}")
            except HTTPException as e:
                print(f"Error executing tool: {e.detail}")
            ```
        """
        logger.info(
            "Executing tool",
            server_id=server_id,
            tool_name=tool_name,
            parameters=parameters
        )

        # Input validation
        if not tool_name or not isinstance(tool_name, str):
            error_msg = "Invalid tool name"
            logger.warning(error_msg, tool_name=tool_name)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        if not isinstance(parameters, dict):
            error_msg = "Parameters must be a dictionary"
            logger.warning(error_msg, parameters=parameters)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        # Get the server
        server = self.get_server(server_id)
        if not server:
            error_msg = f"Server with ID '{server_id}' not found"
            logger.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )

        # Check if server is online
        if server.status != ServerStatus.ONLINE:
            error_msg = f"Server '{server_id}' is not online (status: {server.status.value})"
            logger.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=error_msg
            )

        try:
            # Create server config
            server_config = MCPServerConfig(
                id=server.id,
                name=server.name,
                path=server.command[0] if server.command else None,
                args=server.args,
                cwd=server.cwd,
                env=server.env
            )

            # Get transport with timeout
            try:
                transport = await asyncio.wait_for(
                    transport_manager.get_transport(server_config),
                    timeout=settings.TRANSPORT_TIMEOUT
                )
            except asyncio.TimeoutError:
                error_msg = f"Connection to server '{server_id}' timed out after {settings.TRANSPORT_TIMEOUT} seconds"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=error_msg
                )

            if not transport or not hasattr(transport, 'client') or not transport.client:
                error_msg = f"Failed to connect to server '{server_id}': No transport or client available"
                logger.error(error_msg)
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail=error_msg
                )

            # Execute the tool with timeout
            start_time = datetime.utcnow()
            try:
                logger.debug("Executing tool on server",
                           server_id=server_id,
                           tool_name=tool_name)

                result = await asyncio.wait_for(
                    transport.client.call("tools/execute", {
                        "name": tool_name,
                        "parameters": parameters or {}
                    }),
                    timeout=settings.TOOL_EXECUTION_TIMEOUT
                )

                execution_time = (datetime.utcnow() - start_time).total_seconds()

                # Validate response format
                if not isinstance(result, dict):
                    error_msg = "Invalid response format from server: expected a dictionary"
                    logger.error(error_msg, response=result)
                    raise ValueError(error_msg)

                # Log successful execution
                logger.info(
                    "Tool executed successfully",
                    server_id=server_id,
                    tool_name=tool_name,
                    execution_time=execution_time
                )

                # Return formatted response
                return {
                    "status": "success",
                    "result": result.get("result"),
                    "metadata": {
                        "server_id": server_id,
                        "tool_name": tool_name,
                        "execution_time": execution_time,
                        "timestamp": start_time.isoformat(),
                        "server_metadata": result.get("metadata", {})
                    }
                }

            except asyncio.TimeoutError:
                execution_time = (datetime.utcnow() - start_time).total_seconds()
                error_msg = f"Tool execution timed out after {settings.TOOL_EXECUTION_TIMEOUT} seconds"
                logger.error(
                    error_msg,
                    server_id=server_id,
                    tool_name=tool_name,
                    execution_time=execution_time
                )
                raise HTTPException(
                    status_code=status.HTTP_504_GATEWAY_TIMEOUT,
                    detail=error_msg
                )

            except Exception as e:
                logger.error(
                    "Tool execution failed",
                    server_id=server_id,
                    tool_name=tool_name,
                    error=str(e),
                    exc_info=True
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail=f"Tool execution failed: {str(e)}"
                )

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise

        except Exception as e:
            error_msg = f"Unexpected error executing tool '{tool_name}': {str(e)}"
            logger.error(
                error_msg,
                server_id=server_id,
                tool_name=tool_name,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

    async def get_server_status(self, server_id: str) -> Dict[str, Any]:
        """Get the detailed status of a server.

        This method provides comprehensive status information about a server, including:
        1. Basic server information (ID, name, type)
        2. Current status and health
        3. Connection information
        4. Resource usage (if available)
        5. Last error (if any)

        Args:
            server_id: The unique identifier of the server to get status for

        Returns:
            Dict[str, Any]: A dictionary containing detailed status information, including:
                - server_id: The server's unique identifier
                - name: The server's display name
                - type: The server type (e.g., 'python', 'docker', 'node')
                - status: Current status (ONLINE, OFFLINE, ERROR, etc.)
                - health: Health status (ok, warning, error)
                - uptime: Server uptime in seconds (if available)
                - last_error: Last error message (if any)
                - connection_info: Connection details (if connected)
                - resources: Resource usage information (CPU, memory, etc.)
                - metadata: Additional server-specific metadata

        Raises:
            HTTPException:
                - 404: If the server is not found
                - 500: If an unexpected error occurs while getting status

        Example:
            ```python
            # Example usage
            try:
                status = await server_service.get_server_status("my-server-1")
                print(f"Server status: {status['status']}")
                print(f"Health: {status['health']}")
                if 'last_error' in status:
                    print(f"Last error: {status['last_error']}")
            except HTTPException as e:
                print(f"Error getting server status: {e.detail}")
            ```
        """
        logger.debug("Getting server status", server_id=server_id)

        # Get the server and validate it exists
        server = self.get_server(server_id)
        if not server:
            error_msg = f"Server with ID '{server_id}' not found"
            logger.warning(error_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )

        try:
            # Prepare basic status information
            status_info: Dict[str, Any] = {
                "server_id": server.id,
                "name": server.name,
                "type": server.type.value if hasattr(server, 'type') else "unknown",
                "status": server.status.value,
                "health": "ok",  # Default health status
                "metadata": {}
            }

            # Add description if available
            if hasattr(server, 'description') and server.description:
                status_info["description"] = server.description

            # Check server status and set health accordingly
            if server.status == ServerStatus.ERROR:
                status_info["health"] = "error"
                if hasattr(server, 'last_error') and server.last_error:
                    status_info["last_error"] = server.last_error
            elif server.status in [ServerStatus.STARTING, ServerStatus.STOPPING]:
                status_info["health"] = "warning"

            # Add uptime if available
            if hasattr(server, 'started_at') and server.started_at:
                uptime = (datetime.utcnow() - server.started_at).total_seconds()
                status_info["uptime"] = int(uptime)

            # Add connection information if the server is online
            if server.status == ServerStatus.ONLINE:
                # Try to get transport for additional connection details
                try:
                    transport = await transport_manager.get_transport(MCPServerConfig(
                        id=server.id,
                        name=server.name,
                        path=server.command[0] if server.command else None,
                        args=server.args or [],
                        cwd=server.cwd or os.getcwd(),
                        env=server.env or {}
                    ))

                    if transport and hasattr(transport, 'get_connection_info'):
                        try:
                            conn_info = await transport.get_connection_info()
                            if conn_info:
                                status_info["connection_info"] = conn_info
                        except Exception as e:
                            logger.warning(
                                "Failed to get connection info",
                                server_id=server_id,
                                error=str(e)
                            )

                    # Add resource usage if available
                    if hasattr(transport, 'get_resource_usage'):
                        try:
                            resources = await transport.get_resource_usage()
                            if resources:
                                status_info["resources"] = resources
                        except Exception as e:
                            logger.warning(
                                "Failed to get resource usage",
                                server_id=server_id,
                                error=str(e)
                            )
                except Exception as e:
                    logger.warning(
                        "Failed to get transport for status check",
                        server_id=server_id,
                        error=str(e)
                    )

            logger.debug("Retrieved server status",
                       server_id=server_id,
                       status=status_info["status"],
                       health=status_info["health"])

            return status_info

        except HTTPException:
            # Re-raise HTTP exceptions as-is
            raise

        except Exception as e:
            error_msg = f"Failed to get status for server '{server_id}': {str(e)}"
            logger.error(
                error_msg,
                server_id=server_id,
                error=str(e),
                exc_info=True
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=error_msg
            )

    async def _connect_server(self, server_id: str) -> bool:
        """Establish a connection to an MCP server.

        This method handles the connection process to an MCP server, including:
        1. Validating the server exists and is in a connectable state
        2. Creating and configuring the transport
        3. Establishing the connection with proper timeouts
        4. Updating the server status based on the connection result

        Args:
            server_id: The unique identifier of the server to connect to

        Returns:
            bool:
                - True if the connection was successfully established
                - False if the connection failed or the server doesn't exist
        """
        logger.debug("Connecting to server", server_id=server_id)

        # Get the server and validate it exists
        server = self.get_server(server_id)
        if not server:
            logger.warning("Cannot connect to non-existent server", server_id=server_id)
            return False

        # If already connected, return success
        if server.status == ServerStatus.ONLINE:
            logger.debug("Server is already connected", server_id=server_id)
            return True

        # Don't try to connect if the server is in an error state
        if server.status == ServerStatus.ERROR:
            logger.warning("Cannot connect to server in error state", server_id=server_id)
            return False

        try:
            # Create server configuration
            server_config = MCPServerConfig(
                id=server.id,
                name=server.name,
                path=server.command[0] if server.command else None,
                args=server.args or [],
                cwd=server.cwd or os.getcwd(),
                env=server.env or {}
            )

            # Update status to connecting
            server.status = ServerStatus.CONNECTING
            logger.debug("Initiating connection to server", server_id=server_id)

            # Get transport with timeout
            try:
                transport = await asyncio.wait_for(
                    transport_manager.get_transport(server_config),
                    timeout=settings.TRANSPORT_TIMEOUT
                )

                # Verify the transport and client are valid
                if transport and hasattr(transport, 'client') and transport.client:
                    # Test the connection with a ping
                    try:
                        await asyncio.wait_for(
                            transport.client.call("ping"),
                            timeout=settings.TRANSPORT_TIMEOUT
                        )
                        server.status = ServerStatus.ONLINE
                        logger.info("Successfully connected to server", server_id=server_id)
                        return True
                    except (asyncio.TimeoutError, Exception) as e:
                        logger.warning(
                            "Server connection test failed",
                            server_id=server_id,
                            error=str(e)
                        )

                # If we get here, the connection wasn't successful
                server.status = ServerStatus.ERROR
                logger.error(
                    "Failed to establish connection to server",
                    server_id=server_id,
                    has_transport=transport is not None,
                    has_client=hasattr(transport, 'client') if transport else False
                )
                return False

            except asyncio.TimeoutError:
                error_msg = f"Connection to server '{server_id}' timed out after {settings.TRANSPORT_TIMEOUT} seconds"
                logger.error(error_msg)
                server.status = ServerStatus.ERROR
                return False

        except Exception as e:
            error_msg = f"Unexpected error connecting to server '{server_id}': {str(e)}"
            logger.error(
                error_msg,
                server_id=server_id,
                error=str(e),
                exc_info=True
            )
            server.status = ServerStatus.ERROR
            return False

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
                if hasattr(server, "close"):
                    try:
                        await server.close()
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
