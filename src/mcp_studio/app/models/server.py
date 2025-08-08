"""Data models for MCP servers."""
from enum import Enum
from typing import Dict, List, Optional
from pydantic import BaseModel, Field


class ServerType(str, Enum):
    """Types of MCP servers."""
    PYTHON = "python"
    DOCKER = "docker"
    NODE = "node"
    UNKNOWN = "unknown"


class ServerStatus(str, Enum):
    """Status of an MCP server."""
    ONLINE = "online"
    OFFLINE = "offline"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"


class ServerBase(BaseModel):
    """Base model for MCP servers."""
    id: str = Field(..., description="Unique identifier for the server")
    name: str = Field(..., description="Display name of the server")
    type: ServerType = Field(..., description="Type of the server")
    status: ServerStatus = Field(..., description="Current status of the server")
    description: Optional[str] = Field(None, description="Description of the server")


class Server(ServerBase):
    """Detailed MCP server model with configuration."""
    command: str = Field(..., description="Command to start the server")
    args: List[str] = Field(default_factory=list, description="Command-line arguments")
    cwd: Optional[str] = Field(None, description="Working directory for the server")
    env: Dict[str, str] = Field(default_factory=dict, description="Environment variables")
    last_seen: Optional[str] = Field(None, description="Last seen timestamp")
    uptime: Optional[str] = Field(None, description="Server uptime")
    version: Optional[str] = Field(None, description="Server version")


class ServerCreate(ServerBase):
    """Model for creating a new MCP server."""
    command: str = Field(..., description="Command to start the server")
    args: List[str] = Field(default_factory=list, description="Command-line arguments")
    cwd: Optional[str] = Field(None, description="Working directory for the server")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")


class ServerUpdate(BaseModel):
    """Model for updating an existing MCP server."""
    name: Optional[str] = Field(None, description="Display name of the server")
    description: Optional[str] = Field(None, description="Description of the server")
    command: Optional[str] = Field(None, description="Command to start the server")
    args: Optional[List[str]] = Field(None, description="Command-line arguments")
    cwd: Optional[str] = Field(None, description="Working directory for the server")
    env: Optional[Dict[str, str]] = Field(None, description="Environment variables")


class ToolParameter(BaseModel):
    """Model for MCP tool parameters."""
    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type")
    description: Optional[str] = Field(None, description="Parameter description")
    required: bool = Field(True, description="Whether the parameter is required")
    default: Optional[str] = Field(None, description="Default value")


class ToolInfo(BaseModel):
    """Model for MCP tool information."""
    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: List[ToolParameter] = Field(default_factory=list, description="Tool parameters")
    return_type: str = Field(..., description="Return type")
    version: Optional[str] = Field(None, description="Tool version")
    tags: List[str] = Field(default_factory=list, description="Tool tags")


class ServerToolsResponse(BaseModel):
    """Response model for server tools."""
    server_id: str = Field(..., description="Server ID")
    tools: List[ToolInfo] = Field(..., description="List of available tools")
