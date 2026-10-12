"""Shared types and interfaces for the MCP Studio application."""

from typing import Any, Protocol, runtime_checkable

from pydantic import BaseModel


class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""

    id: str
    name: str
    path: str | None = None
    args: list[str] = []
    cwd: str | None = None
    env: dict[str, str] = {}


@runtime_checkable
class TransportProtocol(Protocol):
    """Protocol for transport implementations."""

    async def connect(self) -> bool:
        """Connect to the server."""
        ...

    async def execute_tool(self, request: "ToolExecutionRequest") -> "ToolExecutionResult":
        """Execute a tool on the server."""
        ...

    async def close(self) -> None:
        """Close the connection."""
        ...


class ToolExecutionRequest(BaseModel):
    """Request to execute a tool on an MCP server."""

    server_id: str
    tool_name: str
    parameters: dict[str, Any]
    timeout: float | None = 30.0


class ToolExecutionResult(BaseModel):
    """Result of a tool execution."""

    success: bool
    result: Any | None = None
    error: str | None = None
    execution_time: float
    timestamp: str
