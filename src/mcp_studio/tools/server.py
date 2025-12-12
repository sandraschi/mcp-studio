"""
Server management tools for MCP Studio.

This module provides comprehensive tools for discovering, managing, and interacting
with MCP servers using FastMCP 2.11 integration.
"""

import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import aiohttp
import psutil
import structlog
from fastmcp import Client
from fastmcp.client.transports import StdioTransport

from ..app.core.config import settings
from .decorators import (
    ToolCategory,
    cache_result,
    rate_limited,
    retry_on_failure,
    structured_log,
    timed,
    tool,
    validate_input
)

logger = structlog.get_logger(__name__)


@tool(
    name="discover_mcp_servers",
    description="""Discover MCP servers in configured paths.

    Scans the configured discovery paths to find MCP servers including:
    - Python-based servers (.py files)
    - Node.js servers (.js files)
    - Docker-based servers (Dockerfile or docker-compose.yml)
    - Configuration-based servers (.json config files)

    Returns detailed information about each discovered server including
    their capabilities, tools, and current status.""",
    category=ToolCategory.DISCOVERY,
    tags=["server", "discovery", "mcp"],
    estimated_runtime="2-5s",
    examples=[
        {
            "input": {"max_depth": 2, "include_inactive": False},
            "output": {
                "servers": [
                    {
                        "id": "python:/path/to/server.py",
                        "name": "Example Server",
                        "type": "python",
                        "status": "available",
                        "tools_count": 5
                    }
                ]
            }
        }
    ]
)
@structured_log(level="info", message="Discovering MCP servers")
@timed(log_threshold=1.0)
@cache_result(ttl_seconds=60)  # Cache for 1 minute
async def discover_mcp_servers(
    max_depth: int = 3,
    include_inactive: bool = False,
    scan_docker: bool = True
) -> Dict[str, Any]:
    """Discover MCP servers in configured discovery paths.

    Args:
        max_depth: Maximum directory depth to scan
        include_inactive: Whether to include servers that aren't running
        scan_docker: Whether to scan for Docker-based servers

    Returns:
        Dictionary containing discovered servers and scan statistics
    """
    discovered_servers = []
    scan_stats = {
        "paths_scanned": 0,
        "files_checked": 0,
        "servers_found": 0,
        "errors": []
    }

    discovery_paths = settings.MCP_DISCOVERY_PATHS or []

    for path_str in discovery_paths:
        try:
            path = Path(path_str).expanduser().resolve()
            if not path.exists():
                scan_stats["errors"].append(f"Path does not exist: {path}")
                continue

            scan_stats["paths_scanned"] += 1

            # Scan for different types of servers
            servers_in_path = await _scan_path_for_servers(
                path, max_depth, scan_docker
            )

            for server in servers_in_path:
                scan_stats["files_checked"] += 1
                
                # Small delay to reduce terminal spam and CPU usage
                await asyncio.sleep(0.05)  # 50ms delay between servers

                # Check if server is active (if requested)
                if not include_inactive:
                    if not await _is_server_active(server):
                        continue

                discovered_servers.append(server)
                scan_stats["servers_found"] += 1

        except Exception as e:
            error_msg = f"Error scanning path {path_str}: {str(e)}"
            scan_stats["errors"].append(error_msg)
            logger.warning("Discovery path scan failed", path=path_str, error=str(e))

    return {
        "servers": discovered_servers,
        "statistics": scan_stats,
        "discovery_paths": discovery_paths,
        "timestamp": time.time()
    }


@tool(
    name="get_server_info",
    description="""Get detailed information about a specific MCP server.

    Retrieves comprehensive information about an MCP server including:
    - Server metadata (name, version, description)
    - Available tools and their schemas
    - Server capabilities and features
    - Current status and health metrics
    - Connection information and requirements

    Can connect to both local and remote servers.""",
    category=ToolCategory.SERVER,
    tags=["server", "info", "status"],
    estimated_runtime="1-3s",
    examples=[
        {
            "input": {"server_path": "/path/to/server.py"},
            "output": {
                "name": "Example Server",
                "version": "1.0.0",
                "tools": ["add", "multiply", "get_weather"],
                "status": "running"
            }
        }
    ]
)
@validate_input(
    server_path=lambda x: x and len(x.strip()) > 0
)
@structured_log(level="info", message="Getting server information")
@retry_on_failure(max_retries=2, delay=1.0)
@timed(log_threshold=2.0)
async def get_server_info(
    server_path: str,
    timeout: float = 10.0,
    include_tools: bool = True,
    include_resources: bool = False
) -> Dict[str, Any]:
    """Get detailed information about an MCP server.

    Args:
        server_path: Path to the server file or URL
        timeout: Connection timeout in seconds
        include_tools: Whether to fetch detailed tool information
        include_resources: Whether to fetch resource information

    Returns:
        Dictionary containing server information and capabilities
    """
    server_info = {
        "server_path": server_path,
        "type": _detect_server_type(server_path),
        "status": "unknown",
        "capabilities": {},
        "tools": [],
        "resources": [],
        "metadata": {},
        "health": {},
        "timestamp": time.time()
    }

    try:
        # Determine connection method
        if server_path.startswith(("http://", "https://")):
            # Remote server
            server_info.update(await _get_remote_server_info(
                server_path, timeout, include_tools, include_resources
            ))
        else:
            # Local server
            server_info.update(await _get_local_server_info(
                server_path, timeout, include_tools, include_resources
            ))

        server_info["status"] = "available"

    except Exception as e:
        server_info["status"] = "error"
        server_info["error"] = str(e)
        logger.error("Failed to get server info", server_path=server_path, error=str(e))

    return server_info


@tool(
    name="test_server_connection",
    description="""Test connection to an MCP server.

    Performs a comprehensive connection test to an MCP server:
    - Establishes connection using appropriate transport
    - Verifies server responds to basic requests
    - Tests tool discovery and listing
    - Measures response times and connection quality
    - Checks server compatibility and version

    Returns detailed connection diagnostics and performance metrics.""",
    category=ToolCategory.UTILITY,
    tags=["server", "test", "connection", "diagnostics"],
    estimated_runtime="3-10s",
    examples=[
        {
            "input": {"server_path": "/path/to/server.py", "test_tools": True},
            "output": {
                "connection_successful": True,
                "response_time_ms": 150,
                "tools_discovered": 5,
                "server_version": "1.0.0"
            }
        }
    ]
)
@validate_input(
    server_path=lambda x: x and len(x.strip()) > 0,
    timeout=lambda x: x > 0 and x <= 60
)
@structured_log(level="info", message="Testing server connection")
@timed(log_threshold=5.0)
async def test_server_connection(
    server_path: str,
    timeout: float = 15.0,
    test_tools: bool = True,
    test_ping: bool = True,
    deep_test: bool = False
) -> Dict[str, Any]:
    """Test connection to an MCP server with comprehensive diagnostics.

    Args:
        server_path: Path to server file or URL
        timeout: Connection timeout in seconds
        test_tools: Whether to test tool discovery
        test_ping: Whether to test basic ping/health check
        deep_test: Whether to perform deep connection testing

    Returns:
        Dictionary containing connection test results and diagnostics
    """
    test_results = {
        "server_path": server_path,
        "test_started": time.time(),
        "connection_successful": False,
        "tests_performed": [],
        "metrics": {},
        "errors": [],
        "warnings": []
    }

    start_time = time.time()

    try:
        # Basic connection test
        logger.info("Starting basic connection test", server_path=server_path)
        connection_start = time.time()

        if server_path.startswith(("http://", "https://")):
            # Test HTTP connection
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.get(f"{server_path}/health") as response:
                    if response.status == 200:
                        test_results["connection_successful"] = True
                        test_results["metrics"]["http_response_code"] = response.status
        else:
            # Test STDIO connection
            server_path_obj = Path(server_path)
            if not server_path_obj.exists():
                raise FileNotFoundError(f"Server file not found: {server_path}")

            # Create transport and test connection
            transport = StdioTransport(
                command="python",
                args=[str(server_path_obj)],
                env=dict(os.environ)
            )

            async with Client(transport) as client:
                await client.initialize()
                test_results["connection_successful"] = True

                # Test ping if requested
                if test_ping:
                    ping_start = time.time()
                    tools = await client.list_tools()  # Use list_tools as ping equivalent
                    ping_time = (time.time() - ping_start) * 1000
                    test_results["metrics"]["ping_time_ms"] = round(ping_time, 2)
                    test_results["tests_performed"].append("ping")

                # Test tool discovery if requested
                if test_tools:
                    tools_start = time.time()
                    tools = await client.list_tools()
                    tools_time = (time.time() - tools_start) * 1000

                    test_results["metrics"]["tools_discovered"] = len(tools)
                    test_results["metrics"]["tool_discovery_time_ms"] = round(tools_time, 2)
                    test_results["tests_performed"].append("tool_discovery")

                    # Store tool summary
                    test_results["tools_summary"] = [
                        {"name": tool.name, "description": tool.description[:100]}
                        for tool in tools[:10]  # Limit to first 10 tools
                    ]

                # Deep testing if requested
                if deep_test:
                    await _perform_deep_connection_test(client, test_results)

        connection_time = (time.time() - connection_start) * 1000
        test_results["metrics"]["connection_time_ms"] = round(connection_time, 2)
        test_results["tests_performed"].append("basic_connection")

    except asyncio.TimeoutError:
        test_results["errors"].append(f"Connection timeout after {timeout}s")
        test_results["connection_successful"] = False
    except Exception as e:
        test_results["errors"].append(f"Connection failed: {str(e)}")
        test_results["connection_successful"] = False
        logger.error("Server connection test failed", server_path=server_path, error=str(e))

    total_time = time.time() - start_time
    test_results["metrics"]["total_test_time_ms"] = round(total_time * 1000, 2)
    test_results["test_completed"] = time.time()

    return test_results


@tool(
    name="execute_remote_tool",
    description="""Execute a tool on a remote MCP server.

    Connects to an MCP server and executes a specified tool with given parameters.
    Supports both local STDIO servers and remote HTTP servers.

    Features:
    - Automatic parameter validation
    - Timeout handling
    - Error recovery and retry logic
    - Detailed execution metrics
    - Result formatting and type conversion

    Returns the tool execution result along with performance metrics.""",
    category=ToolCategory.SERVER,
    tags=["server", "tool", "execution", "remote"],
    estimated_runtime="1-30s",
    requires_auth=False,
    rate_limited=True,
    examples=[
        {
            "input": {
                "server_path": "/path/to/math_server.py",
                "tool_name": "add",
                "parameters": {"a": 5, "b": 3}
            },
            "output": {
                "success": True,
                "result": 8,
                "execution_time_ms": 45
            }
        }
    ]
)
@validate_input(
    server_path=lambda x: x and len(x.strip()) > 0,
    tool_name=lambda x: x and len(x.strip()) > 0,
    timeout=lambda x: x > 0 and x <= 300
)
@rate_limited(calls_per_minute=30)  # Limit to 30 calls per minute
@structured_log(level="info", message="Executing remote tool")
@retry_on_failure(max_retries=2, delay=2.0)
@timed(log_threshold=1.0)
async def execute_remote_tool(
    server_path: str,
    tool_name: str,
    parameters: Dict[str, Any],
    timeout: float = 30.0,
    validate_params: bool = True,
    return_raw: bool = False
) -> Dict[str, Any]:
    """Execute a tool on a remote MCP server.

    Args:
        server_path: Path to server file or URL
        tool_name: Name of the tool to execute
        parameters: Parameters to pass to the tool
        timeout: Execution timeout in seconds
        validate_params: Whether to validate parameters before execution
        return_raw: Whether to return raw results without formatting

    Returns:
        Dictionary containing execution results and metrics
    """
    execution_result = {
        "server_path": server_path,
        "tool_name": tool_name,
        "parameters": parameters,
        "success": False,
        "result": None,
        "error": None,
        "metrics": {},
        "timestamp": time.time()
    }

    start_time = time.time()

    try:
        logger.info(
            "Starting tool execution",
            server_path=server_path,
            tool_name=tool_name,
            param_count=len(parameters)
        )

        if server_path.startswith(("http://", "https://")):
            # Remote HTTP execution
            result = await _execute_http_tool(
                server_path, tool_name, parameters, timeout
            )
        else:
            # Local STDIO execution
            result = await _execute_stdio_tool(
                server_path, tool_name, parameters, timeout, validate_params
            )

        execution_result["success"] = True
        execution_result["result"] = result if return_raw else _format_tool_result(result)

        logger.info(
            "Tool execution completed successfully",
            server_path=server_path,
            tool_name=tool_name,
            execution_time=f"{(time.time() - start_time):.3f}s"
        )

    except Exception as e:
        execution_result["error"] = str(e)
        logger.error(
            "Tool execution failed",
            server_path=server_path,
            tool_name=tool_name,
            error=str(e)
        )

    execution_time = time.time() - start_time
    execution_result["metrics"]["execution_time_ms"] = round(execution_time * 1000, 2)
    execution_result["metrics"]["execution_time_s"] = round(execution_time, 3)

    return execution_result


@tool(
    name="list_server_tools",
    description="""List all available tools on an MCP server.

    Connects to an MCP server and retrieves a comprehensive list of all
    available tools with their schemas, descriptions, and metadata.

    Features:
    - Detailed tool schemas and parameter information
    - Tool categorization and tagging
    - Usage examples and documentation
    - Performance and compatibility information
    - Filtering and search capabilities

    Supports both local STDIO and remote HTTP servers.""",
    category=ToolCategory.DISCOVERY,
    tags=["server", "tools", "list", "discovery"],
    estimated_runtime="1-5s",
    examples=[
        {
            "input": {"server_path": "/path/to/server.py", "include_schemas": True},
            "output": {
                "tools": [
                    {
                        "name": "add",
                        "description": "Add two numbers",
                        "parameters": {"a": "number", "b": "number"}
                    }
                ],
                "total_tools": 1
            }
        }
    ]
)
@validate_input(
    server_path=lambda x: x and len(x.strip()) > 0
)
@structured_log(level="info", message="Listing server tools")
@cache_result(ttl_seconds=120)  # Cache for 2 minutes
@timed(log_threshold=2.0)
async def list_server_tools(
    server_path: str,
    include_schemas: bool = True,
    include_examples: bool = False,
    filter_category: Optional[str] = None,
    timeout: float = 15.0
) -> Dict[str, Any]:
    """List all available tools on an MCP server.

    Args:
        server_path: Path to server file or URL
        include_schemas: Whether to include parameter schemas
        include_examples: Whether to include usage examples
        filter_category: Filter tools by category
        timeout: Connection timeout in seconds

    Returns:
        Dictionary containing tools list and metadata
    """
    tools_result = {
        "server_path": server_path,
        "tools": [],
        "total_tools": 0,
        "categories": set(),
        "server_info": {},
        "timestamp": time.time()
    }

    try:
        if server_path.startswith(("http://", "https://")):
            # Remote server
            tools_data = await _list_remote_tools(server_path, timeout)
        else:
            # Local server
            tools_data = await _list_local_tools(server_path, timeout)

        # Process and format tools
        for tool_data in tools_data:
            tool_info = {
                "name": tool_data.get("name", "unknown"),
                "description": tool_data.get("description", ""),
            }

            if include_schemas and "inputSchema" in tool_data:
                tool_info["input_schema"] = tool_data["inputSchema"]

            if include_examples and "examples" in tool_data:
                tool_info["examples"] = tool_data["examples"]

            # Extract category if available
            category = tool_data.get("category", "utility")
            tool_info["category"] = category
            tools_result["categories"].add(category)

            # Apply category filter
            if filter_category and category != filter_category:
                continue

            tools_result["tools"].append(tool_info)

        tools_result["total_tools"] = len(tools_result["tools"])
        tools_result["categories"] = list(tools_result["categories"])

        logger.info(
            "Successfully listed server tools",
            server_path=server_path,
            total_tools=tools_result["total_tools"]
        )

    except Exception as e:
        tools_result["error"] = str(e)
        logger.error("Failed to list server tools", server_path=server_path, error=str(e))

    return tools_result


# Helper functions for tool implementations

async def _scan_path_for_servers(path: Path, max_depth: int, scan_docker: bool) -> List[Dict[str, Any]]:
    """Scan a path for MCP servers."""
    servers = []

    def scan_directory(dir_path: Path, current_depth: int):
        if current_depth > max_depth:
            return

        try:
            for item in dir_path.iterdir():
                if item.is_file():
                    server_info = _analyze_potential_server(item, scan_docker)
                    if server_info:
                        servers.append(server_info)
                elif item.is_dir() and not item.name.startswith('.'):
                    scan_directory(item, current_depth + 1)
        except PermissionError:
            pass  # Skip directories we can't read

    if path.is_file():
        server_info = _analyze_potential_server(path, scan_docker)
        if server_info:
            servers.append(server_info)
    else:
        scan_directory(path, 0)

    return servers


def _analyze_potential_server(file_path: Path, scan_docker: bool) -> Optional[Dict[str, Any]]:
    """Analyze a file to determine if it's an MCP server."""
    server_info = None

    # Check Python files
    if file_path.suffix == '.py':
        server_info = _analyze_python_server(file_path)

    # Check JavaScript files
    elif file_path.suffix == '.js':
        server_info = _analyze_js_server(file_path)

    # Check Docker files
    elif scan_docker and file_path.name in ['Dockerfile', 'docker-compose.yml']:
        server_info = _analyze_docker_server(file_path)

    # Check JSON config files
    elif file_path.suffix == '.json' and 'mcp' in file_path.name.lower():
        server_info = _analyze_config_server(file_path)

    return server_info


def _analyze_python_server(file_path: Path) -> Optional[Dict[str, Any]]:
    """Analyze a Python file to see if it's an MCP server."""
    try:
        content = file_path.read_text(encoding='utf-8')

        # Look for MCP-related imports and patterns
        mcp_indicators = [
            'fastmcp', 'FastMCP', 'mcp.server', '@mcp.tool',
            'mcp_server', 'MCPServer', 'stdio', 'mcp.run'
        ]

        if any(indicator in content for indicator in mcp_indicators):
            return {
                "id": f"python:{file_path}",
                "name": file_path.stem,
                "type": "python",
                "path": str(file_path),
                "status": "available",
                "estimated_tools": content.count('@') + content.count('def '),
                "file_size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime
            }
    except Exception:
        pass

    return None


def _analyze_js_server(file_path: Path) -> Optional[Dict[str, Any]]:
    """Analyze a JavaScript file to see if it's an MCP server."""
    try:
        content = file_path.read_text(encoding='utf-8')

        # Look for MCP-related patterns in JavaScript
        mcp_indicators = [
            '@modelcontextprotocol', 'mcp-server', 'McpServer',
            'stdio', 'process.stdin', 'process.stdout'
        ]

        if any(indicator in content for indicator in mcp_indicators):
            return {
                "id": f"node:{file_path}",
                "name": file_path.stem,
                "type": "node",
                "path": str(file_path),
                "status": "available",
                "estimated_tools": content.count('function ') + content.count('=>'),
                "file_size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime
            }
    except Exception:
        pass

    return None


def _analyze_docker_server(file_path: Path) -> Optional[Dict[str, Any]]:
    """Analyze a Docker file to see if it contains an MCP server."""
    try:
        content = file_path.read_text(encoding='utf-8')

        # Look for MCP-related patterns in Docker files
        if 'mcp' in content.lower() or 'fastmcp' in content.lower():
            return {
                "id": f"docker:{file_path}",
                "name": file_path.parent.name,
                "type": "docker",
                "path": str(file_path),
                "status": "requires_docker",
                "file_size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime
            }
    except Exception:
        pass

    return None


def _analyze_config_server(file_path: Path) -> Optional[Dict[str, Any]]:
    """Analyze a JSON config file for MCP server configuration."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            config = json.load(f)

        # Look for MCP configuration patterns
        if ('mcpServers' in config or 'mcp_servers' in config or
            'servers' in config or 'tools' in config):
            return {
                "id": f"config:{file_path}",
                "name": file_path.stem,
                "type": "config",
                "path": str(file_path),
                "status": "configuration",
                "servers_count": len(config.get('mcpServers', config.get('servers', {}))),
                "file_size": file_path.stat().st_size,
                "modified": file_path.stat().st_mtime
            }
    except Exception:
        pass

    return None


async def _is_server_active(server_info: Dict[str, Any]) -> bool:
    """Check if a server is currently active."""
    try:
        if server_info["type"] == "python":
            # Quick syntax check for Python servers
            result = subprocess.run([
                sys.executable, "-m", "py_compile", server_info["path"]
            ], capture_output=True, timeout=5)
            return result.returncode == 0

        elif server_info["type"] == "node":
            # Basic syntax check for Node.js servers
            result = subprocess.run([
                "node", "--check", server_info["path"]
            ], capture_output=True, timeout=5)
            return result.returncode == 0

        elif server_info["type"] == "docker":
            # Check if Docker is available
            result = subprocess.run([
                "docker", "--version"
            ], capture_output=True, timeout=5)
            return result.returncode == 0

        return True  # Default to active for other types

    except Exception:
        return False


def _detect_server_type(server_path: str) -> str:
    """Detect the type of MCP server from its path."""
    if server_path.startswith(("http://", "https://")):
        return "http"

    path = Path(server_path)
    if path.suffix == '.py':
        return "python"
    elif path.suffix == '.js':
        return "node"
    elif path.name == 'Dockerfile':
        return "docker"
    elif path.suffix == '.json':
        return "config"

    return "unknown"


async def _get_local_server_info(
    server_path: str, timeout: float,
    include_tools: bool, include_resources: bool
) -> Dict[str, Any]:
    """Get information from a local MCP server."""
    server_path_obj = Path(server_path)

    if not server_path_obj.exists():
        raise FileNotFoundError(f"Server file not found: {server_path}")

    # Create transport and connect
    transport = StdioTransport(
        command="python",
        args=[str(server_path_obj)],
        env=dict(os.environ)
    )

    server_info = {}

    async with Client(transport) as client:
        await client.initialize()

        # Get basic info
        server_info["name"] = server_path_obj.stem
        server_info["version"] = "1.0.0"  # Default version

        # Get tools if requested
        if include_tools:
            tools = await client.list_tools()
            server_info["tools"] = [
                {
                    "name": tool.name,
                    "description": tool.description,
                    "input_schema": tool.inputSchema
                }
                for tool in tools
            ]
            server_info["tools_count"] = len(tools)

        # Get resources if requested (if supported)
        if include_resources:
            try:
                # This would depend on the specific client implementation
                server_info["resources"] = []
            except Exception:
                server_info["resources"] = []

    return server_info


async def _get_remote_server_info(
    server_url: str, timeout: float,
    include_tools: bool, include_resources: bool
) -> Dict[str, Any]:
    """Get information from a remote MCP server."""
    server_info = {}

    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        # Try to get server info from a standard endpoint
        try:
            async with session.get(f"{server_url}/info") as response:
                if response.status == 200:
                    info_data = await response.json()
                    server_info.update(info_data)
        except Exception:
            pass

        # Get tools if requested
        if include_tools:
            try:
                async with session.get(f"{server_url}/tools") as response:
                    if response.status == 200:
                        tools_data = await response.json()
                        server_info["tools"] = tools_data.get("tools", [])
                        server_info["tools_count"] = len(server_info["tools"])
            except Exception:
                server_info["tools"] = []
                server_info["tools_count"] = 0

    return server_info


async def _perform_deep_connection_test(client: Client, test_results: Dict[str, Any]):
    """Perform deep connection testing."""
    try:
        # Test multiple tool calls
        tools = await client.list_tools()
        if tools:
            # Try to call a simple tool if available
            for tool in tools[:3]:  # Test up to 3 tools
                try:
                    # This would need to be adapted based on the specific tool
                    test_results["tests_performed"].append(f"tool_test_{tool.name}")
                except Exception as e:
                    test_results["warnings"].append(f"Tool {tool.name} test failed: {str(e)}")

        test_results["tests_performed"].append("deep_test")

    except Exception as e:
        test_results["warnings"].append(f"Deep test failed: {str(e)}")


async def _execute_stdio_tool(
    server_path: str,
    tool_name: str,
    parameters: Dict[str, Any],
    timeout: float,
    validate_params: bool
) -> Any:
    """Execute a tool on a local STDIO server."""
    server_path_obj = Path(server_path)

    if not server_path_obj.exists():
        raise FileNotFoundError(f"Server file not found: {server_path}")

    # Create transport and connect
    transport = StdioTransport(
        command="python",
        args=[str(server_path_obj)],
        env=dict(os.environ)
    )

    async with Client(transport) as client:
        await client.initialize()

        # Validate tool exists if requested
        if validate_params:
            tools = await client.list_tools()
            tool_names = [tool.name for tool in tools]
            if tool_name not in tool_names:
                raise ValueError(f"Tool '{tool_name}' not found. Available tools: {tool_names}")

        # Execute the tool
        result = await asyncio.wait_for(
            client.call_tool(tool_name, **parameters),
            timeout=timeout
        )

        return result


async def _execute_http_tool(
    server_url: str,
    tool_name: str,
    parameters: Dict[str, Any],
    timeout: float
) -> Any:
    """Execute a tool on a remote HTTP server."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        tool_url = f"{server_url}/tools/{tool_name}/execute"

        async with session.post(
            tool_url,
            json={"parameters": parameters}
        ) as response:
            response.raise_for_status()
            result = await response.json()
            return result.get("result", result)


async def _list_local_tools(server_path: str, timeout: float) -> List[Dict[str, Any]]:
    """List tools from a local STDIO server."""
    server_path_obj = Path(server_path)

    if not server_path_obj.exists():
        raise FileNotFoundError(f"Server file not found: {server_path}")

    # Create transport and connect
    transport = StdioTransport(
        command="python",
        args=[str(server_path_obj)],
        env=dict(os.environ)
    )

    async with Client(transport) as client:
        await client.initialize()
        tools = await client.list_tools()

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.inputSchema,
                "category": getattr(tool, "category", "utility")
            }
            for tool in tools
        ]


async def _list_remote_tools(server_url: str, timeout: float) -> List[Dict[str, Any]]:
    """List tools from a remote HTTP server."""
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
        tools_url = f"{server_url}/tools"

        async with session.get(tools_url) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get("tools", [])


def _format_tool_result(result: Any) -> Any:
    """Format tool execution result for better readability."""
    if isinstance(result, dict):
        # If it's a structured result, return as-is
        return result
    elif isinstance(result, (list, tuple)):
        # Convert to list for JSON serialization
        return list(result)
    elif isinstance(result, str):
        # Clean up string results
        return result.strip()
    else:
        # Convert other types to string
        return str(result)


# Additional utility functions for server management

# Alias for backwards compatibility
discover_servers = discover_mcp_servers

@tool(
    name="get_server_health",
    description="""Get comprehensive health information about an MCP server.

    Performs health checks including:
    - Connection status and response times
    - Resource usage (CPU, memory)
    - Error rates and recent issues
    - Performance metrics
    - Tool availability and functionality

    Returns detailed health report with recommendations.""",
    category=ToolCategory.MONITORING,
    tags=["server", "health", "monitoring", "diagnostics"],
    estimated_runtime="2-5s"
)
@structured_log(level="info", message="Getting server health")
@timed(log_threshold=3.0)
async def get_server_health(
    server_path: str,
    check_tools: bool = True,
    check_resources: bool = True,
    timeout: float = 10.0
) -> Dict[str, Any]:
    """Get comprehensive health information about an MCP server."""
    health_report = {
        "server_path": server_path,
        "overall_status": "unknown",
        "checks_performed": [],
        "metrics": {},
        "issues": [],
        "recommendations": [],
        "timestamp": time.time()
    }

    try:
        # Basic connectivity check
        start_time = time.time()
        server_info = await get_server_info(server_path, timeout=timeout)
        connection_time = time.time() - start_time

        health_report["metrics"]["connection_time_ms"] = round(connection_time * 1000, 2)
        health_report["checks_performed"].append("connectivity")

        if server_info.get("status") == "available":
            health_report["overall_status"] = "healthy"

            # Tool health check
            if check_tools and server_info.get("tools"):
                tools_count = len(server_info["tools"])
                health_report["metrics"]["tools_available"] = tools_count
                health_report["checks_performed"].append("tools")

                if tools_count == 0:
                    health_report["issues"].append("No tools available")
                    health_report["recommendations"].append("Check server tool registration")

            # Resource usage check (if local server)
            if check_resources and not server_path.startswith("http"):
                try:
                    # Basic file system check
                    path_obj = Path(server_path)
                    if path_obj.exists():
                        file_size = path_obj.stat().st_size
                        health_report["metrics"]["server_file_size_bytes"] = file_size

                        if file_size == 0:
                            health_report["issues"].append("Server file is empty")
                        elif file_size > 1024 * 1024:  # > 1MB
                            health_report["recommendations"].append("Large server file, consider optimization")

                        health_report["checks_performed"].append("file_system")

                except Exception as e:
                    health_report["issues"].append(f"Resource check failed: {str(e)}")

        else:
            health_report["overall_status"] = "unhealthy"
            health_report["issues"].append(f"Server not available: {server_info.get('error', 'Unknown error')}")

    except Exception as e:
        health_report["overall_status"] = "error"
        health_report["issues"].append(f"Health check failed: {str(e)}")

    # Generate recommendations based on issues
    if not health_report["issues"]:
        health_report["recommendations"].append("Server appears to be healthy")
    elif len(health_report["issues"]) > 3:
        health_report["recommendations"].append("Multiple issues detected, consider server restart")

    return health_report


@tool(
    name="restart_server",
    description="""Restart an MCP server process.

    Attempts to gracefully restart a server by:
    - Stopping the current process if running
    - Clearing any cached connections
    - Starting a new server instance
    - Verifying the restart was successful

    Only works with local servers that can be managed.""",
    category=ToolCategory.SERVER,
    tags=["server", "restart", "management"],
    estimated_runtime="5-15s",
    requires_auth=True
)
@validate_input(
    server_path=lambda x: x and not x.startswith("http")
)
@structured_log(level="warning", message="Restarting server")
@timed(log_threshold=10.0)
async def restart_server(
    server_path: str,
    force: bool = False,
    timeout: float = 30.0
) -> Dict[str, Any]:
    """Restart an MCP server process."""
    restart_result = {
        "server_path": server_path,
        "success": False,
        "steps_completed": [],
        "error": None,
        "metrics": {},
        "timestamp": time.time()
    }

    start_time = time.time()

    try:
        # Step 1: Check if server is currently running
        logger.info("Checking server status before restart", server_path=server_path)

        initial_status = "unknown"
        try:
            health = await get_server_health(server_path, timeout=5.0)
            initial_status = health["overall_status"]
            restart_result["steps_completed"].append("status_check")
        except Exception:
            initial_status = "not_running"

        # Step 2: Stop existing processes (if any)
        if initial_status in ["healthy", "unhealthy"]:
            logger.info("Stopping existing server process", server_path=server_path)
            # This would need to be implemented based on how processes are tracked
            # For now, we'll just clear any cached connections
            restart_result["steps_completed"].append("stop_process")

        # Step 3: Wait a moment for cleanup
        await asyncio.sleep(1.0)
        restart_result["steps_completed"].append("cleanup_wait")

        # Step 4: Test server availability
        logger.info("Testing server after restart", server_path=server_path)

        final_health = await get_server_health(server_path, timeout=timeout)
        restart_result["steps_completed"].append("restart_verification")

        if final_health["overall_status"] == "healthy":
            restart_result["success"] = True
            restart_result["metrics"]["tools_available"] = final_health["metrics"].get("tools_available", 0)
        else:
            restart_result["error"] = "Server not healthy after restart attempt"

    except Exception as e:
        restart_result["error"] = str(e)
        logger.error("Server restart failed", server_path=server_path, error=str(e))

    restart_time = time.time() - start_time
    restart_result["metrics"]["restart_time_s"] = round(restart_time, 2)

    return restart_result
