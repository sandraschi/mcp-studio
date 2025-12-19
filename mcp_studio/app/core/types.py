"""Shared types and interfaces for the MCP Studio application."""
from typing import Any, Dict, List, Optional, Protocol, runtime_checkable

from pydantic import BaseModel

class MCPServerConfig(BaseModel):
    """Configuration for an MCP server."""
    id: str
    name: str
    path: Optional[str] = None
    args: List[str] = []
    cwd: Optional[str] = None
    env: Dict[str, str] = {}

@runtime_checkable
class TransportProtocol(Protocol):
    """Protocol for transport implementations."""
    
    async def connect(self) -> bool:
        """Connect to the server."""
        ...
        
    async def execute_tool(self, request: 'ToolExecutionRequest') -> 'ToolExecutionResult':
        """Execute a tool on the server."""
        ...
        
    async def close(self) -> None:
        """Close the connection."""
        ...

class ToolExecutionRequest(BaseModel):
    """Request to execute a tool on an MCP server."""
    server_id: str
    tool_name: str
    parameters: Dict[str, Any]
    timeout: Optional[float] = 30.0

class ToolExecutionResult(BaseModel):
    """Result of a tool execution."""
    success: bool
    result: Optional[Any] = None
    error: Optional[str] = None
    execution_time: float
    timestamp: str
