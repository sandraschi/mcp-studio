"""Data models for MCP servers."""

from pydantic import BaseModel, Field

from ..core.enums import ServerStatus, ServerType

# ServerType and ServerStatus enums moved to core.enums


class ServerBase(BaseModel):
    """Base model for MCP servers."""

    id: str = Field(..., description="Unique identifier for the server")
    name: str = Field(..., description="Display name of the server")
    type: ServerType = Field(..., description="Type of the server")
    status: ServerStatus = Field(..., description="Current status of the server")
    description: str | None = Field(None, description="Description of the server")


class Server(ServerBase):
    """Detailed MCP server model with configuration."""

    command: str = Field(..., description="Command to start the server")
    args: list[str] = Field(default_factory=list, description="Command-line arguments")
    cwd: str | None = Field(None, description="Working directory for the server")
    env: dict[str, str] = Field(default_factory=dict, description="Environment variables")
    last_seen: str | None = Field(None, description="Last seen timestamp")
    uptime: str | None = Field(None, description="Server uptime")
    version: str | None = Field(None, description="Server version")


class ServerCreate(ServerBase):
    """Model for creating a new MCP server."""

    command: str = Field(..., description="Command to start the server")
    args: list[str] = Field(default_factory=list, description="Command-line arguments")
    cwd: str | None = Field(None, description="Working directory for the server")
    env: dict[str, str] | None = Field(None, description="Environment variables")


class ServerUpdate(BaseModel):
    """Model for updating an existing MCP server."""

    name: str | None = Field(None, description="Display name of the server")
    description: str | None = Field(None, description="Description of the server")
    command: str | None = Field(None, description="Command to start the server")
    args: list[str] | None = Field(None, description="Command-line arguments")
    cwd: str | None = Field(None, description="Working directory for the server")
    env: dict[str, str] | None = Field(None, description="Environment variables")


class ToolParameter(BaseModel):
    """Model for MCP tool parameters."""

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type")
    description: str | None = Field(None, description="Parameter description")
    required: bool = Field(True, description="Whether the parameter is required")
    default: str | None = Field(None, description="Default value")


class ToolInfo(BaseModel):
    """Model for MCP tool information."""

    name: str = Field(..., description="Tool name")
    description: str = Field(..., description="Tool description")
    parameters: list[ToolParameter] = Field(default_factory=list, description="Tool parameters")
    return_type: str = Field(..., description="Return type")
    version: str | None = Field(None, description="Tool version")
    tags: list[str] = Field(default_factory=list, description="Tool tags")


class ServerToolsResponse(BaseModel):
    """Response model for server tools."""

    server_id: str = Field(..., description="Server ID")
    tools: list[ToolInfo] = Field(..., description="List of available tools")
