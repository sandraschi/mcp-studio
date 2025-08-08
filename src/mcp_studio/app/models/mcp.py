"""Pydantic models for MCP-related data structures."""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, Field, HttpUrl, validator

class ServerStatus(str, Enum):
    """Status of an MCP server."""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    STARTING = "starting"
    STOPPING = "stopping"

class ParameterType(str, Enum):
    """Supported parameter types for MCP tools."""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"

class MCPToolParameter(BaseModel):
    """Parameter definition for an MCP tool."""
    name: str = Field(..., description="Name of the parameter")
    type: ParameterType = Field(..., description="Data type of the parameter")
    description: str = Field("", description="Description of the parameter")
    required: bool = Field(True, description="Whether the parameter is required")
    default: Optional[Any] = Field(None, description="Default value for the parameter")
    enum: Optional[List[Any]] = Field(None, description="Allowed values for the parameter")
    format: Optional[str] = Field(None, description="Format of the parameter")
    minimum: Optional[Union[int, float]] = Field(None, description="Minimum value for numeric parameters")
    maximum: Optional[Union[int, float]] = Field(None, description="Maximum value for numeric parameters")
    min_length: Optional[int] = Field(None, alias="minLength", description="Minimum length for string parameters")
    max_length: Optional[int] = Field(None, alias="maxLength", description="Maximum length for string parameters")
    pattern: Optional[str] = Field(None, description="Regex pattern for string validation")
    items: Optional[Dict[str, Any]] = Field(None, description="Schema for array items")
    properties: Optional[Dict[str, Any]] = Field(None, description="Properties for object parameters")

    class Config:
        allow_population_by_field_name = True
        use_enum_values = True

class MCPTool(BaseModel):
    """Definition of an MCP tool."""
    name: str = Field(..., description="Name of the tool")
    description: str = Field("", description="Description of the tool")
    parameters: List[MCPToolParameter] = Field(default_factory=list, description="List of parameters")
    categories: List[str] = Field(default_factory=list, description="Categories for the tool")
    version: str = Field("0.1.0", description="Version of the tool")
    deprecated: bool = Field(False, description="Whether the tool is deprecated")
    
    # Runtime information
    last_used: Optional[datetime] = Field(None, description="When the tool was last used")
    usage_count: int = Field(0, description="Number of times the tool has been used")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class MCPServerHealth(BaseModel):
    """Health status of an MCP server."""
    status: ServerStatus = Field(..., description="Current status of the server")
    uptime: Optional[float] = Field(None, description="Uptime in seconds")
    version: Optional[str] = Field(None, description="Server version")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the health was checked")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class MCPServer(BaseModel):
    """Information about an MCP server."""
    id: str = Field(..., description="Unique identifier for the server")
    name: str = Field(..., description="Display name of the server")
    description: str = Field("", description="Description of the server")
    version: str = Field("0.1.0", description="Version of the server")
    
    # Connection details
    url: Optional[HttpUrl] = Field(None, description="URL of the server")
    path: Optional[str] = Field(None, description="Filesystem path to the server")
    type: str = Field("python", description="Type of the server (python, dxt, http, etc.)")
    
    # Status
    status: ServerStatus = Field(ServerStatus.OFFLINE, description="Current status of the server")
    last_seen: Optional[datetime] = Field(None, description="When the server was last seen")
    health: Optional[MCPServerHealth] = Field(None, description="Health status of the server")
    
    # Tools
    tools: List[MCPTool] = Field(default_factory=list, description="List of available tools")
    
    # Metadata
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="When the server was discovered")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="When the server was last updated")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }
    
    def update_health(self, health: 'MCPServerHealth') -> None:
        """Update the health status of the server."""
        self.health = health
        self.status = health.status
        self.updated_at = datetime.utcnow()
    
    def add_tool(self, tool: MCPTool) -> None:
        """Add a tool to the server."""
        # Check if tool already exists
        existing_tool = next((t for t in self.tools if t.name == tool.name), None)
        if existing_tool:
            # Update existing tool
            index = self.tools.index(existing_tool)
            self.tools[index] = tool
        else:
            # Add new tool
            self.tools.append(tool)
        
        self.updated_at = datetime.utcnow()
    
    def remove_tool(self, tool_name: str) -> bool:
        """Remove a tool from the server."""
        initial_length = len(self.tools)
        self.tools = [t for t in self.tools if t.name != tool_name]
        
        if len(self.tools) < initial_length:
            self.updated_at = datetime.utcnow()
            return True
        return False

class ToolExecutionRequest(BaseModel):
    """Request to execute a tool on an MCP server."""
    server_id: str = Field(..., description="ID of the server to execute the tool on")
    tool_name: str = Field(..., description="Name of the tool to execute")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Parameters for the tool")
    timeout: Optional[float] = Field(60.0, description="Timeout in seconds")
    
    @validator('parameters')
    def validate_parameters(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that parameters are JSON-serializable."""
        try:
            import json
            json.dumps(v)
            return v
        except (TypeError, ValueError) as e:
            raise ValueError(f"Parameters must be JSON-serializable: {str(e)}")

class ToolExecutionResult(BaseModel):
    """Result of a tool execution."""
    success: bool = Field(..., description="Whether the execution was successful")
    result: Optional[Any] = Field(None, description="Result of the execution")
    error: Optional[str] = Field(None, description="Error message if execution failed")
    execution_time: float = Field(..., description="Execution time in seconds")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="When the execution completed")
    
    class Config:
        json_encoders = {
            datetime: lambda v: v.isoformat() if v else None
        }

class ServerRegistration(BaseModel):
    """Request to register a new MCP server."""
    name: str = Field(..., description="Name of the server")
    url: Optional[HttpUrl] = Field(None, description="URL of the server")
    path: Optional[str] = Field(None, description="Filesystem path to the server")
    type: str = Field("python", description="Type of the server (python, dxt, http, etc.)")
    description: str = Field("", description="Description of the server")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
