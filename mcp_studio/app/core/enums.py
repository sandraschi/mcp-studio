"""Common enums used throughout the application."""
from enum import Enum

class ServerStatus(str, Enum):
    """Status of an MCP server."""
    ONLINE = "online"
    OFFLINE = "offline"
    STARTING = "starting"
    STOPPING = "stopping"
    ERROR = "error"

class ServerType(str, Enum):
    """Types of MCP servers."""
    PYTHON = "python"
    DOCKER = "docker"
    NODE = "node"
    UNKNOWN = "unknown"

class ParameterType(str, Enum):
    """Supported parameter types for MCP tools."""
    STRING = "string"
    INTEGER = "integer"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    FILE = "file"
