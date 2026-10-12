"""
Tool Service for MCP Studio

This service handles tool discovery, execution, and management with WebSocket support.
"""

"""
Tool Service for MCP Studio

This service handles tool discovery, execution, and management with WebSocket support.
"""
import asyncio
import inspect
import logging
import time
from collections.abc import Awaitable, Callable
from enum import StrEnum
from typing import Any, TypeVar
from uuid import uuid4

from fastapi import WebSocket
from pydantic import BaseModel, ConfigDict, Field

from ..core.exceptions import ForbiddenError, ToolExecutionError, UnauthorizedError
from ..core.websocket import ToolExecutionMessage, ToolExecutionStatus, manager
from ..models.user import User

# Type variable for generic tool functions
T = TypeVar("T")


class ToolExecutionState(StrEnum):
    """Execution state of a tool."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class ExecutionContext:
    """Context for tool execution with progress tracking."""

    def __init__(
        self, execution_id: str, tool_name: str, user: User | None = None, client_id: str | None = None
    ) -> None:
        """Initialize the execution context."""
        self.execution_id = execution_id
        self.tool_name = tool_name
        self.user = user
        self.client_id = client_id
        self.start_time = time.time()
        self.end_time: float | None = None
        self.progress: float = 0.0
        self.status: ToolExecutionState = ToolExecutionState.PENDING
        self.metadata: dict[str, Any] = {}
        self._cancelled = False
        self._progress_callbacks: list[Callable[[float, str], Awaitable[None]]] = []

    async def update_progress(self, progress: float, message: str = "") -> None:
        """Update the execution progress.

        Args:
            progress: Progress value between 0.0 and 1.0
            message: Optional progress message
        """
        if self._cancelled:
            raise asyncio.CancelledError("Execution was cancelled")

        progress = max(0.0, min(1.0, progress))
        self.progress = progress

        # Notify all progress callbacks
        for callback in self._progress_callbacks:
            await callback(progress, message)

    def add_progress_callback(self, callback: Callable[[float, str], Awaitable[None]]) -> None:
        """Add a progress callback function.

        Args:
            callback: Async function that takes (progress: float, message: str)
        """
        self._progress_callbacks.append(callback)

    def set_metadata(self, **metadata: Any) -> None:
        """Set execution metadata."""
        self.metadata.update(metadata)

    def cancel(self) -> None:
        """Cancel the execution."""
        self._cancelled = True
        self.status = ToolExecutionState.CANCELLED
        self.end_time = time.time()

    def complete(self) -> None:
        """Mark the execution as completed."""
        self.status = ToolExecutionState.COMPLETED
        self.progress = 1.0
        self.end_time = time.time()

    def fail(self, error: Exception) -> None:
        """Mark the execution as failed.

        Args:
            error: The exception that caused the failure
        """
        self.status = ToolExecutionState.FAILED
        self.end_time = time.time()
        self.metadata["error"] = str(error)
        self.metadata["error_type"] = error.__class__.__name__

    @property
    def is_running(self) -> bool:
        """Check if the execution is running."""
        return self.status == ToolExecutionState.RUNNING

    @property
    def is_completed(self) -> bool:
        """Check if the execution is completed."""
        return self.status == ToolExecutionState.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check if the execution failed."""
        return self.status == ToolExecutionState.FAILED

    @property
    def is_cancelled(self) -> bool:
        """Check if the execution was cancelled."""
        return self.status == ToolExecutionState.CANCELLED

    @property
    def execution_time(self) -> float:
        """Get the execution time in seconds."""
        end = self.end_time or time.time()
        return end - self.start_time

    def to_dict(self) -> dict[str, Any]:
        """Convert context to a dictionary."""
        return {
            "execution_id": self.execution_id,
            "tool_name": self.tool_name,
            "user_id": self.user.id if self.user else None,
            "client_id": self.client_id,
            "status": self.status.value,
            "progress": self.progress,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "execution_time": self.execution_time,
            "metadata": self.metadata,
        }


logger = logging.getLogger(__name__)


class ToolExecutionResult(BaseModel):
    """Result of a tool execution."""

    success: bool = Field(..., description="Whether the execution was successful")
    result: Any | None = Field(None, description="The execution result")
    error: str | None = Field(None, description="Error message if execution failed")
    execution_id: str | None = Field(None, description="Unique ID of the execution")
    execution_time: float = Field(..., description="Execution time in seconds")
    metadata: dict[str, Any] = Field(default_factory=dict, description="Additional metadata about the execution")

    @classmethod
    def from_context(
        cls, context: ExecutionContext, result: Any | None = None, error: Exception | None = None
    ) -> "ToolExecutionResult":
        """Create a result from an execution context."""
        success = context.is_completed and error is None
        error_msg = str(error) if error else None

        if error and not error_msg:
            error_msg = f"{error.__class__.__name__} occurred"

        return cls(
            success=success,
            result=result,
            error=error_msg,
            execution_id=context.execution_id,
            execution_time=context.execution_time,
            metadata=context.metadata,
        )


class ToolMetadata(BaseModel):
    """Metadata for a tool."""

    name: str = Field(..., description="Name of the tool")
    description: str = Field(..., description="Description of the tool's purpose")
    parameters: dict[str, Any] = Field(default_factory=dict, description="Parameter schema for the tool")
    tags: list[str] = Field(default_factory=list, description="Tags for categorizing the tool")
    is_async: bool = Field(default=False, description="Whether the tool is asynchronous")
    requires_auth: bool = Field(default=False, description="Whether the tool requires authentication")
    allowed_roles: list[str] = Field(default_factory=list, description="List of roles allowed to execute this tool")
    timeout: float | None = Field(
        default=None, description="Maximum execution time in seconds (None for no timeout)", ge=0.0
    )

    def has_permission(self, user: User | None) -> bool:
        """Check if a user has permission to use this tool."""
        if not self.requires_auth:
            return True

        if user is None:
            return False

        if not self.allowed_roles:
            return True

        return any(role in user.roles for role in self.allowed_roles)


class Tool(BaseModel):
    """A tool that can be executed."""

    func: Callable
    metadata: ToolMetadata

    model_config = ConfigDict(arbitrary_types_allowed=True)


class ToolService:
    """Service for managing and executing tools with WebSocket support."""

    def __init__(self) -> None:
        """Initialize the tool service."""
        self._tools: dict[str, Tool] = {}
        self._executions: dict[str, asyncio.Task] = {}
        self._execution_contexts: dict[str, ExecutionContext] = {}
        self._lock = asyncio.Lock()

    async def _notify_execution_update(
        self,
        context: ExecutionContext,
        status: ToolExecutionStatus | None = None,
        progress: float | None = None,
        message: str | None = None,
        result: Any | None = None,
        error: Exception | None = None,
    ) -> None:
        """Send a WebSocket update about tool execution.

        Args:
            context: The execution context
            status: New status of the execution
            progress: Current progress (0.0 to 1.0)
            message: Optional status message
            result: Execution result if completed
            error: Error if execution failed
        """
        if status is not None:
            context.status = ToolExecutionState(status.value)

        if progress is not None:
            context.progress = progress

        # Create the update message
        msg = ToolExecutionMessage(
            execution_id=context.execution_id,
            tool_name=context.tool_name,
            status=context.status,
            progress=context.progress,
            message=message,
            metadata=context.metadata,
            result=result,
            error=str(error) if error else None,
        )

        # Send to the client that initiated the execution
        if context.client_id:
            await manager.send_message(context.client_id, msg.dict(exclude_unset=True), message_type="tool_execution")

        # Also broadcast to any execution-specific subscribers
        await manager.broadcast_execution_update(
            context.execution_id, msg.dict(exclude_unset=True), message_type="tool_execution"
        )

    async def _execute_tool_internal(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        user: User | None = None,
        client_id: str | None = None,
        execution_id: str | None = None,
    ) -> Any:
        """Internal method to execute a tool with proper error handling.

        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            user: The user executing the tool
            client_id: ID of the WebSocket client
            execution_id: Optional execution ID (generated if not provided)

        Returns:
            The result of the tool execution

        Raises:
            ValueError: If the tool is not found
            UnauthorizedError: If the user is not authorized
            ToolExecutionError: If the tool execution fails
        """
        from ..core.server_service import server_service
        from ..core.websocket import ToolExecutionStatus

        # Get the tool
        tool = self.get_tool(tool_name)
        if not tool:
            raise ValueError(f"Tool not found: {tool_name}")

        # Check authentication and permissions
        if tool.metadata.requires_auth and not user:
            raise UnauthorizedError("Authentication required to execute this tool")

        if not tool.metadata.has_permission(user):
            raise ForbiddenError("Insufficient permissions to execute this tool")

        # Create execution context
        execution_id = execution_id or f"exec_{uuid4().hex[:8]}"
        context = ExecutionContext(execution_id=execution_id, tool_name=tool_name, user=user, client_id=client_id)

        # Store the context
        self._execution_contexts[execution_id] = context

        try:
            # Notify execution started
            await self._notify_execution_update(
                context=context,
                status=ToolExecutionStatus.RUNNING,
                progress=0.0,
                message=f"Starting execution of {tool_name}",
            )

            # Get the server ID from parameters or use default
            server_id = parameters.pop("server_id", "default")

            # Get the MCP client
            try:
                client = await server_service.get_client(server_id)
                if not client:
                    raise ToolExecutionError(f"Could not connect to server: {server_id}")

                # Prepare progress callback
                async def progress_callback(progress: float, message: str = "") -> None:
                    await self._notify_execution_update(
                        context=context, status=ToolExecutionStatus.RUNNING, progress=progress, message=message
                    )

                context.add_progress_callback(progress_callback)

                # Execute the tool via MCP protocol
                start_time = time.time()

                try:
                    # Call the tool on the MCP server
                    result = await client.call(tool_name, **parameters)

                    # Update status and notify
                    execution_time = time.time() - start_time
                    context.metadata["execution_time"] = execution_time

                    await self._notify_execution_update(
                        context=context,
                        status=ToolExecutionStatus.COMPLETED,
                        progress=1.0,
                        message=f"Successfully executed {tool_name}",
                        result=result,
                    )

                    return result

                except asyncio.CancelledError:
                    # Handle cancellation
                    context.cancel()
                    await self._notify_execution_update(
                        context=context,
                        status=ToolExecutionStatus.CANCELLED,
                        message=f"Execution of {tool_name} was cancelled",
                    )
                    raise

                except Exception as e:
                    # Handle execution errors
                    error_msg = f"Tool execution failed: {e!s}"
                    context.fail(e)
                    await self._notify_execution_update(
                        context=context,
                        status=ToolExecutionStatus.FAILED,
                        message=f"Failed to execute {tool_name}",
                        error=e,
                    )
                    raise ToolExecutionError(error_msg) from e

            except Exception as e:
                # Handle connection or other errors
                error_msg = f"Failed to connect to MCP server: {e!s}"
                context.fail(e)
                await self._notify_execution_update(
                    context=context,
                    status=ToolExecutionStatus.FAILED,
                    message=f"Failed to connect to MCP server: {server_id}",
                    error=e,
                )
                raise ToolExecutionError(error_msg) from e

        except Exception as e:
            # Handle any other errors
            if not isinstance(e, ToolExecutionError):
                error_msg = f"Unexpected error during tool execution: {e!s}"
                context.fail(e)
                await self._notify_execution_update(
                    context=context,
                    status=ToolExecutionStatus.FAILED,
                    message=f"Unexpected error during execution of {tool_name}",
                    error=e,
                )
                raise ToolExecutionError(error_msg) from e

        finally:
            # Clean up
            if execution_id in self._execution_contexts:
                del self._execution_contexts[execution_id]

    def register_tool(
        self,
        func: Callable[..., Any],
        name: str | None = None,
        description: str | None = None,
        parameters: dict[str, Any] | None = None,
        tags: list[str] | None = None,
        requires_auth: bool = False,
        allowed_roles: list[str] | None = None,
        timeout: float | None = None,
    ) -> Callable[..., Any]:
        """Register a new tool.

        Args:
            func: The function to register as a tool
            name: Name of the tool (defaults to function name)
            description: Description of the tool
            parameters: Parameter schema for the tool
            tags: Tags for categorizing the tool
            requires_auth: Whether the tool requires authentication
            allowed_roles: List of roles allowed to execute this tool
            timeout: Maximum execution time in seconds (None for no timeout)

        Returns:
            The decorated function
        """
        if name is None:
            name = func.__name__

        if description is None:
            description = func.__doc__ or ""

        if parameters is None:
            # Try to extract parameters from function signature
            sig = inspect.signature(func)
            parameters = {}
            for param in sig.parameters.values():
                if param.name == "context":
                    continue  # Skip the context parameter

                param_info = {
                    "type": param.annotation.__name__ if param.annotation != inspect.Parameter.empty else "Any",
                    "required": param.default == inspect.Parameter.empty,
                }
                if param.default != inspect.Parameter.empty:
                    param_info["default"] = param.default
                parameters[param.name] = param_info

        if tags is None:
            tags = []

        if allowed_roles is None:
            allowed_roles = []

        # Create tool metadata
        metadata = ToolMetadata(
            name=name,
            description=description,
            parameters=parameters,
            tags=tags,
            is_async=asyncio.iscoroutinefunction(func),
            requires_auth=requires_auth,
            allowed_roles=allowed_roles,
            timeout=timeout,
        )

        # Register the tool
        self._tools[name] = Tool(func=func, metadata=metadata)
        logger.info(f"Registered tool: {name}")
        return func

    def get_tool(self, name: str) -> Tool | None:
        """Get a tool by name.

        Args:
            name: Name of the tool to get

        Returns:
            The tool if found, None otherwise
        """
        return self._tools.get(name)

    def list_tools(self) -> list[ToolMetadata]:
        """List all available tools.

        Returns:
            List of tool metadata
        """
        return [tool.metadata for tool in self._tools.values()]

    async def execute_tool(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        user: User | None = None,
        execution_id: str | None = None,
        websocket: WebSocket | None = None,
        progress_callback: Callable[[float, str], Awaitable[None]] | None = None,
    ) -> ToolExecutionResult:
        """Execute a tool with the given parameters.

        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            user: The user executing the tool
            execution_id: Optional execution ID for tracking
            websocket: Optional WebSocket for real-time updates
            progress_callback: Optional callback for progress updates

        Returns:
            The result of the tool execution
        """
        import time

        start_time = time.time()

        if execution_id is None:
            execution_id = f"exec_{uuid4().hex[:8]}"

        # Get the tool
        tool = self.get_tool(tool_name)
        if not tool:
            return ToolExecutionResult(
                success=False, error=f"Tool not found: {tool_name}", execution_time=time.time() - start_time
            )

        # Check authentication
        if tool.metadata.requires_auth and not user:
            return ToolExecutionResult(
                success=False, error="Authentication required", execution_time=time.time() - start_time
            )

        # Check authorization
        if tool.metadata.allowed_roles and user:
            if not any(role in user.roles for role in tool.metadata.allowed_roles):
                return ToolExecutionResult(
                    success=False, error="Insufficient permissions", execution_time=time.time() - start_time
                )

        # Prepare parameters
        func_params: dict[str, Any] = {}
        sig = inspect.signature(tool.func)

        # Add user to parameters if the function accepts a 'user' parameter
        if "user" in sig.parameters:
            func_params["user"] = user

        # Add progress callback if the function accepts it
        if "progress_callback" in sig.parameters:
            func_params["progress_callback"] = progress_callback

        # Add other parameters
        for param_name, param_info in sig.parameters.items():
            if param_name in ["user", "progress_callback"]:
                continue

            if param_name in parameters:
                func_params[param_name] = parameters[param_name]
            elif param_info.default != inspect.Parameter.empty:
                func_params[param_name] = param_info.default
            elif param_info.kind == inspect.Parameter.VAR_POSITIONAL:
                func_params[param_name] = []
            elif param_info.kind == inspect.Parameter.VAR_KEYWORD:
                func_params[param_name] = {}
            else:
                return ToolExecutionResult(
                    success=False,
                    error=f"Missing required parameter: {param_name}",
                    execution_time=time.time() - start_time,
                )

        # Execute the tool
        try:
            # Send start notification
            if websocket:
                await websocket.send_json(
                    {
                        "type": "execution_started",
                        "execution_id": execution_id,
                        "tool": tool_name,
                        "timestamp": start_time,
                    }
                )

            # Execute the tool
            if tool.metadata.is_async:
                result = await tool.func(**func_params)
            else:
                # Run synchronous functions in a thread pool
                loop = asyncio.get_event_loop()
                result = await loop.run_in_executor(None, lambda: tool.func(**func_params))

            execution_time = time.time() - start_time

            # Send completion notification
            if websocket:
                await websocket.send_json(
                    {
                        "type": "execution_completed",
                        "execution_id": execution_id,
                        "tool": tool_name,
                        "execution_time": execution_time,
                        "timestamp": time.time(),
                    }
                )

            return ToolExecutionResult(
                success=True,
                result=result,
                execution_time=execution_time,
                metadata={"tool": tool_name, "execution_id": execution_id, "user": user.username if user else None},
            )

        except Exception as e:
            logger.error(f"Error executing tool {tool_name}: {e}", exc_info=True)

            # Send error notification
            if websocket:
                await websocket.send_json(
                    {
                        "type": "execution_failed",
                        "execution_id": execution_id,
                        "tool": tool_name,
                        "error": str(e),
                        "execution_time": time.time() - start_time,
                        "timestamp": time.time(),
                    }
                )

            return ToolExecutionResult(
                success=False,
                error=str(e),
                execution_time=time.time() - start_time,
                metadata={"tool": tool_name, "execution_id": execution_id, "user": user.username if user else None},
            )

    async def execute_tool_ws(
        self,
        tool_name: str,
        parameters: dict[str, Any],
        websocket: WebSocket,
        user: User | None = None,
        execution_id: str | None = None,
    ) -> None:
        """Execute a tool and stream results over WebSocket.

        Args:
            tool_name: Name of the tool to execute
            parameters: Parameters to pass to the tool
            websocket: WebSocket connection for streaming results
            user: The user executing the tool
            execution_id: Optional execution ID for tracking
        """
        if execution_id is None:
            execution_id = f"ws_exec_{uuid4().hex[:8]}"

        # Create a progress callback
        async def progress_callback(progress: float, message: str = "") -> None:
            """Send progress updates to the WebSocket."""
            await websocket.send_json(
                {
                    "type": "progress",
                    "execution_id": execution_id,
                    "tool": tool_name,
                    "progress": progress,
                    "message": message,
                    "timestamp": time.time(),
                }
            )

        # Execute the tool
        result = await self.execute_tool(
            tool_name=tool_name,
            parameters=parameters,
            user=user,
            execution_id=execution_id,
            websocket=websocket,
            progress_callback=progress_callback,
        )

        # Send the final result
        await websocket.send_json(
            {
                "type": "result",
                "execution_id": execution_id,
                "tool": tool_name,
                "success": result.success,
                "result": result.result,
                "error": result.error,
                "execution_time": result.execution_time,
                "timestamp": time.time(),
            }
        )


# Global tool service instance
tool_service = ToolService()


def tool(
    name: str | None = None,
    description: str | None = None,
    parameters: dict[str, Any] | None = None,
    tags: list[str] | None = None,
    requires_auth: bool = False,
    allowed_roles: list[str] | None = None,
) -> Any:
    """Decorator to register a function as a tool.

    Args:
        name: Name of the tool (defaults to function name)
        description: Description of the tool
        parameters: Parameter schema for the tool
        tags: Tags for categorizing the tool
        requires_auth: Whether the tool requires authentication
        allowed_roles: List of roles allowed to execute this tool

    Returns:
        The decorated function
    """

    def decorator(func: Any) -> Any:
        nonlocal name, description

        if name is None:
            name = func.__name__

        if description is None:
            description = func.__doc__ or ""

        tool_service.register_tool(
            func=func,
            name=name,
            description=description,
            parameters=parameters,
            tags=tags or [],
            requires_auth=requires_auth,
            allowed_roles=allowed_roles or [],
        )
        return func

    return decorator
