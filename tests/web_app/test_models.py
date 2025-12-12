"""Tests for web app data models."""

import pytest
from datetime import datetime
from mcp_studio.app.models.mcp import (
    MCPTool,
    MCPToolParameter,
    MCPServer,
    MCPServerHealth,
    ToolExecutionRequest,
    ToolExecutionResult
)
from mcp_studio.app.core.enums import ServerStatus, ServerType, ParameterType


def test_mcp_tool_model():
    """Test MCPTool model creation."""
    tool = MCPTool(
        name="test_tool",
        description="A test tool",
        parameters=[]
    )
    
    assert tool.name == "test_tool"
    assert tool.description == "A test tool"
    assert tool.parameters == []


def test_mcp_tool_parameter_model():
    """Test MCPToolParameter model creation."""
    param = MCPToolParameter(
        name="test_param",
        type=ParameterType.STRING,
        description="A test parameter"
    )
    
    assert param.name == "test_param"
    assert param.type == ParameterType.STRING
    assert param.description == "A test parameter"


def test_mcp_server_model():
    """Test MCPServer model creation."""
    server = MCPServer(
        id="test-server",
        name="Test Server",
        description="A test server",
        type="stdio",
        status=ServerStatus.OFFLINE
    )
    
    assert server.id == "test-server"
    assert server.name == "Test Server"
    assert server.type == "stdio"
    assert server.status == ServerStatus.OFFLINE


def test_mcp_server_health_model():
    """Test MCPServerHealth model creation."""
    health = MCPServerHealth(
        status=ServerStatus.ONLINE,
        uptime=100.0
    )
    
    assert health.status == ServerStatus.ONLINE
    assert health.uptime == 100.0
    assert health.timestamp is not None


def test_tool_execution_request_model():
    """Test ToolExecutionRequest model creation."""
    request = ToolExecutionRequest(
        server_id="test-server",
        tool_name="test_tool",
        parameters={"param1": "value1"}
    )
    
    assert request.server_id == "test-server"
    assert request.tool_name == "test_tool"
    assert request.parameters == {"param1": "value1"}


def test_tool_execution_result_model():
    """Test ToolExecutionResult model creation."""
    result = ToolExecutionResult(
        success=True,
        result={"output": "test"},
        execution_time=0.5
    )
    
    assert result.success is True
    assert result.result == {"output": "test"}
    assert result.execution_time == 0.5


def test_tool_execution_request_validation():
    """Test ToolExecutionRequest parameter validation."""
    # Empty parameters should be valid
    request = ToolExecutionRequest(
        server_id="test-server",
        tool_name="test_tool",
        parameters={}
    )
    assert request.parameters == {}
    
    # Parameters with valid JSON should pass
    request = ToolExecutionRequest(
        server_id="test-server",
        tool_name="test_tool",
        parameters={"key": "value", "number": 42}
    )
    assert request.parameters == {"key": "value", "number": 42}





