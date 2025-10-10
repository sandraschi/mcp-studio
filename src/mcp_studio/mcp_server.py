#!/usr/bin/env python3
"""
MCP Studio MCP Server

This is the MCP server implementation for MCP Studio, providing tools for
managing and interacting with MCP servers through the Model Control Protocol.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

# Add the project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from mcp_studio.tools import (
    discover_servers,
    get_server_info,
    execute_remote_tool,
    list_server_tools,
    test_server_connection
)

# Initialize FastMCP server
app = FastMCP(
    name="mcp-studio",
    version="1.0.0",
    description="Professional MCP Server Management and Development Tools"
)

# Get user configuration from environment
DISCOVERY_PATHS = os.getenv("DISCOVERY_PATHS", "./servers,./mcp-servers").split(",")
AUTO_DISCOVERY = os.getenv("AUTO_DISCOVERY", "true").lower() == "true"

@app.tool()
async def discover_mcp_servers(paths: Optional[List[str]] = None) -> Dict[str, Any]:
    """
    Discover MCP servers in configured paths.

    Scans the configured discovery paths to find MCP servers including:
    - Python-based servers (.py files)
    - Node.js servers (.js files)
    - Docker-based servers (Dockerfile or docker-compose.yml)
    - Configuration-based servers (.json config files)

    Returns detailed information about each discovered server including
    their capabilities, tools, and current status.

    Args:
        paths: Optional list of specific paths to scan. If not provided,
               uses configured discovery paths.

    Returns:
        Dictionary containing discovered servers with their metadata.
    """
    try:
        scan_paths = paths or DISCOVERY_PATHS
        result = await discover_servers(scan_paths)
        return {
            "success": True,
            "servers": result,
            "scanned_paths": scan_paths
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "scanned_paths": scan_paths
        }

@app.tool()
async def get_server_info(server_id: str) -> Dict[str, Any]:
    """
    Get detailed information about a specific MCP server.

    Retrieves comprehensive metadata about an MCP server including:
    - Server configuration and capabilities
    - Available tools and their schemas
    - Current status and health information
    - Connection details and endpoints

    Args:
        server_id: Unique identifier of the MCP server

    Returns:
        Detailed server information dictionary
    """
    try:
        info = await get_server_info(server_id)
        return {
            "success": True,
            "server": info
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "server_id": server_id
        }

@app.tool()
async def list_server_tools(server_id: str) -> Dict[str, Any]:
    """
    List all tools provided by a specific MCP server.

    Retrieves the complete list of tools available from an MCP server,
    including their names, descriptions, and input schemas.

    Args:
        server_id: Unique identifier of the MCP server

    Returns:
        List of tools with their metadata
    """
    try:
        tools = await list_server_tools(server_id)
        return {
            "success": True,
            "server_id": server_id,
            "tools": tools
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "server_id": server_id
        }

@app.tool()
async def execute_remote_tool(server_id: str, tool_name: str, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """
    Execute a tool on a remote MCP server.

    Connects to a remote MCP server and executes the specified tool with
    the provided parameters. Returns the tool execution result.

    Args:
        server_id: Unique identifier of the MCP server
        tool_name: Name of the tool to execute
        parameters: Parameters to pass to the tool (optional)

    Returns:
        Tool execution result
    """
    try:
        result = await execute_remote_tool(server_id, tool_name, parameters or {})
        return {
            "success": True,
            "server_id": server_id,
            "tool_name": tool_name,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "server_id": server_id,
            "tool_name": tool_name
        }

@app.tool()
async def test_server_connection(server_id: str) -> Dict[str, Any]:
    """
    Test connection to an MCP server.

    Performs a connectivity test to verify that an MCP server is
    accessible and responding correctly.

    Args:
        server_id: Unique identifier of the MCP server

    Returns:
        Connection test results
    """
    try:
        result = await test_server_connection(server_id)
        return {
            "success": True,
            "server_id": server_id,
            "connection_status": result
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "server_id": server_id
        }

if __name__ == "__main__":
    # Run the MCP server
    import asyncio

    async def main():
        # Auto-discover servers if enabled
        if AUTO_DISCOVERY:
            print(f"Auto-discovering MCP servers in: {', '.join(DISCOVERY_PATHS)}", file=sys.stderr)
            try:
                discovered = await discover_servers(DISCOVERY_PATHS)
                print(f"Discovered {len(discovered)} MCP servers", file=sys.stderr)
            except Exception as e:
                print(f"Auto-discovery failed: {e}", file=sys.stderr)

        # Start the MCP server
        print("Starting MCP Studio MCP Server...", file=sys.stderr)
        await app.run_stdio_async()

    asyncio.run(main())
