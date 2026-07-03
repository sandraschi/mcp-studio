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
    test_server_connection,
)
from mcp_studio.tools.runt_analyzer import analyze_runts, get_repo_status
from mcp_studio.tools.server_scaffold import create_mcp_server as scaffold_mcp_server
from mcp_studio.tools.server_updater import update_mcp_server as update_server
from mcp_studio.tools.server_deleter import delete_mcp_server as delete_server

# Import client discovery services
try:
    from mcp_studio.app.services.mcp_client_zoo import MCPClientZoo
    from mcp_studio.app.services.mcp_client_metadata import get_all_clients, get_client_metadata
    from working_sets.client_manager import ClientWorkingSetManager
    import json
except ImportError:
    # Fallback if services not available
    MCPClientZoo = None
    get_all_clients = None
    get_client_metadata = None
    ClientWorkingSetManager = None
    json = None

# Initialize FastMCP server
app = FastMCP(name="mcp-studio")

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
        return {"success": True, "servers": result, "scanned_paths": scan_paths}
    except Exception as e:
        return {"success": False, "error": str(e), "scanned_paths": scan_paths}


@app.tool()
async def discover_clients(include_servers: bool = True) -> Dict[str, Any]:
    """Discover all MCP clients and their configured servers.

    Scans all known MCP client configurations to find:
    - Claude Desktop
    - Cursor IDE
    - Windsurf IDE
    - Antigravity IDE
    - Zed Editor
    - VS Code extensions (Cline, Roo, Continue)
    - LM Studio
    - And other supported clients

    For each client found, returns metadata including:
    - Client name, type, and platform
    - Configuration file path
    - List of MCP servers configured in that client
    - Server count and details

    Args:
        include_servers: If True, includes detailed server information for each client.
                        If False, only returns client metadata and server counts.

    Returns:
        Dictionary containing:
        - success: bool indicating if discovery succeeded
        - total_clients: Number of clients found
        - clients_found: List of client IDs that were discovered
        - clients: List of client information dictionaries, each containing:
            - id: Client identifier (e.g., "claude-desktop", "cursor-ide")
            - name: Human-readable client name
            - type: Client type (Desktop, IDE, Extension, Library)
            - platform: Platform support (Windows, Mac, Linux, Cross-platform)
            - status: Status (Active, Deprecated, Beta)
            - config_path: Path to client's MCP configuration file (if found)
            - server_count: Number of servers configured in this client
            - servers: List of server details (if include_servers=True)
        - summary: Statistics about discovered clients and servers

    Examples:
        # Discover all clients with server details
        result = await discover_clients()

        # Discover clients without server details (faster)
        result = await discover_clients(include_servers=False)
    """
    try:
        if not MCPClientZoo:
            return {
                "success": False,
                "error": "Client discovery services not available",
                "clients": [],
                "total_clients": 0,
            }

        # Initialize client zoo
        zoo = MCPClientZoo()

        # Scan all clients
        client_results = zoo.scan_all_clients()

        # Get client metadata
        all_client_metadata = get_all_clients() if get_all_clients else []
        metadata_map = {client.id: client for client in all_client_metadata}

        # Build client information
        clients_info = []
        total_servers = 0

        for client_id, servers in client_results.items():
            client_meta = metadata_map.get(client_id)

            # Get config path if available
            config_path = None
            if zoo:
                try:
                    config_path_obj = zoo.get_client_config_path(client_id)
                    if config_path_obj:
                        config_path = str(config_path_obj)
                except Exception:
                    pass

            client_info = {
                "id": client_id,
                "name": client_meta.name if client_meta else client_id,
                "type": client_meta.client_type if client_meta else "Unknown",
                "platform": client_meta.platform if client_meta else "Unknown",
                "status": client_meta.status if client_meta else "Unknown",
                "config_path": config_path,
                "server_count": len(servers),
            }

            # Add server details if requested
            if include_servers:
                client_info["servers"] = [
                    {
                        "id": s.id,
                        "name": s.name,
                        "command": s.command,
                        "args": s.args[:3] if s.args else [],  # Limit args for brevity
                        "source": s.source,
                    }
                    for s in servers
                ]

            clients_info.append(client_info)
            total_servers += len(servers)

        # Also include clients that have metadata but weren't found in scan
        for client_meta in all_client_metadata:
            if client_meta.id not in client_results:
                clients_info.append(
                    {
                        "id": client_meta.id,
                        "name": client_meta.name,
                        "type": client_meta.client_type,
                        "platform": client_meta.platform,
                        "status": client_meta.status,
                        "config_path": None,
                        "server_count": 0,
                        "servers": [] if include_servers else None,
                    }
                )

        # Sort by name
        clients_info.sort(key=lambda x: x["name"])

        return {
            "success": True,
            "total_clients": len(clients_info),
            "clients_found": list(client_results.keys()),
            "clients": clients_info,
            "summary": {
                "total_clients": len(clients_info),
                "clients_with_servers": len([c for c in clients_info if c["server_count"] > 0]),
                "total_servers": total_servers,
                "by_type": {
                    client_type: len([c for c in clients_info if c["type"] == client_type])
                    for client_type in set(c["type"] for c in clients_info)
                },
                "by_status": {
                    status: len([c for c in clients_info if c["status"] == status])
                    for status in set(c["status"] for c in clients_info)
                },
            },
        }

    except Exception as e:
        return {"success": False, "error": str(e), "clients": [], "total_clients": 0}


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
        return {"success": True, "server": info}
    except Exception as e:
        return {"success": False, "error": str(e), "server_id": server_id}


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
        return {"success": True, "server_id": server_id, "tools": tools}
    except Exception as e:
        return {"success": False, "error": str(e), "server_id": server_id}


@app.tool()
async def get_client_config(client_id: str) -> Dict[str, Any]:
    """Get the current configuration for a specific MCP client.

    Retrieves the full configuration file content for an MCP client including:
    - All configured MCP servers
    - Server configurations (command, args, env, etc.)
    - Configuration file path and metadata

    Args:
        client_id: Client identifier (e.g., "claude-desktop", "cursor-ide", "windsurf-ide")

    Returns:
        Dictionary containing:
        - success: bool indicating if operation succeeded
        - client_id: The client identifier
        - config_path: Path to the configuration file
        - config_exists: Whether the config file exists
        - config: The full configuration content (if exists)
        - server_count: Number of servers in the config
        - servers: List of server IDs configured in this client

    Examples:
        # Get Claude Desktop config
        result = await get_client_config("claude-desktop")

        # Get Cursor IDE config
        result = await get_client_config("cursor-ide")
    """
    try:
        if not ClientWorkingSetManager or not MCPClientZoo:
            return {
                "success": False,
                "error": "Client config services not available",
                "client_id": client_id,
            }

        # Initialize managers
        client_manager = ClientWorkingSetManager()
        client_zoo = MCPClientZoo()

        # Get config path
        config_path = client_zoo.get_client_config_path(client_id)
        if not config_path:
            return {
                "success": False,
                "error": f"Client '{client_id}' not found or config path unknown",
                "client_id": client_id,
            }

        # Get config info
        config_info = client_manager.get_client_config_info(client_id)
        if not config_info:
            return {
                "success": False,
                "error": f"Could not get config info for client '{client_id}'",
                "client_id": client_id,
            }

        # Read config file if it exists
        config_data = None
        servers = []
        if config_path.exists():
            try:
                with open(config_path, "r", encoding="utf-8-sig") as f:
                    config_data = json.load(f)
                    # Extract server IDs
                    servers = list(config_data.get("mcpServers", {}).keys())
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to read config file: {str(e)}",
                    "client_id": client_id,
                    "config_path": str(config_path),
                }

        return {
            "success": True,
            "client_id": client_id,
            "config_path": str(config_path),
            "config_exists": config_path.exists(),
            "config": config_data,
            "server_count": len(servers),
            "servers": servers,
            "backup_dir": config_info.get("backup_dir"),
        }

    except Exception as e:
        return {"success": False, "error": str(e), "client_id": client_id}


@app.tool()
async def set_client_config(
    client_id: str, config: Dict[str, Any], create_backup: bool = True
) -> Dict[str, Any]:
    """Set or update the configuration for a specific MCP client.

    Writes configuration data to the client's config file. Can create a backup
    of the existing config before making changes.

    Args:
        client_id: Client identifier (e.g., "claude-desktop", "cursor-ide")
        config: Configuration dictionary to write. Should contain "mcpServers" key
                with server configurations, or can be a full config object.
        create_backup: If True, creates a backup of existing config before writing

    Returns:
        Dictionary containing:
        - success: bool indicating if operation succeeded
        - client_id: The client identifier
        - config_path: Path to the configuration file
        - backup_created: Whether a backup was created
        - backup_path: Path to backup file (if created)
        - message: Human-readable status message

    Examples:
        # Set full config
        result = await set_client_config(
            "claude-desktop",
            {"mcpServers": {"server1": {...}, "server2": {...}}}
        )

        # Update config without backup
        result = await set_client_config(
            "cursor-ide",
            {"mcpServers": {...}},
            create_backup=False
        )
    """
    try:
        if not ClientWorkingSetManager or not MCPClientZoo or not json:
            return {
                "success": False,
                "error": "Client config services not available",
                "client_id": client_id,
            }

        # Initialize managers
        client_manager = ClientWorkingSetManager()
        client_zoo = MCPClientZoo()

        # Get config path
        config_path = client_zoo.get_client_config_path(client_id)
        if not config_path:
            return {
                "success": False,
                "error": f"Client '{client_id}' not found or config path unknown",
                "client_id": client_id,
            }

        # Ensure parent directory exists
        config_path.parent.mkdir(parents=True, exist_ok=True)

        # Create backup if requested and config exists
        backup_path = None
        backup_created = False
        if create_backup and config_path.exists():
            try:
                from datetime import datetime

                backup_dir = config_path.parent / "backup"
                try:
                    backup_dir.mkdir(exist_ok=True)
                except Exception as e:
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Could not create backup directory: {e}")
                    # If we can't create backup dir, we can't create backup
                    raise e
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_dir / f"{config_path.stem}_{timestamp}.json"

                # Copy existing config to backup
                import shutil

                shutil.copy2(config_path, backup_path)
                backup_created = True
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Failed to create backup: {str(e)}",
                    "client_id": client_id,
                }

        # Ensure config has proper structure
        if "mcpServers" not in config:
            # If config is just servers, wrap it
            if isinstance(config, dict) and all(isinstance(k, str) for k in config.keys()):
                config = {"mcpServers": config}
            else:
                return {
                    "success": False,
                    "error": "Config must contain 'mcpServers' key or be a dictionary of servers",
                    "client_id": client_id,
                }

        # Write config file
        try:
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
        except Exception as e:
            return {
                "success": False,
                "error": f"Failed to write config file: {str(e)}",
                "client_id": client_id,
                "config_path": str(config_path),
            }

        # Get server count
        server_count = len(config.get("mcpServers", {}))

        return {
            "success": True,
            "client_id": client_id,
            "config_path": str(config_path),
            "backup_created": backup_created,
            "backup_path": str(backup_path) if backup_path else None,
            "server_count": server_count,
            "message": f"Configuration updated successfully. {server_count} server(s) configured.",
        }

    except Exception as e:
        return {"success": False, "error": str(e), "client_id": client_id}


@app.tool()
async def execute_remote_tool(
    server_id: str, tool_name: str, parameters: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
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
        return {"success": True, "server_id": server_id, "tool_name": tool_name, "result": result}
    except Exception as e:
        return {"success": False, "error": str(e), "server_id": server_id, "tool_name": tool_name}


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
        return {"success": True, "server_id": server_id, "connection_status": result}
    except Exception as e:
        return {"success": False, "error": str(e), "server_id": server_id}


@app.tool()
async def help(level: str = "basic", topic: Optional[str] = None) -> str:
    """Get help information about MCP Studio tools and capabilities.

    Provides comprehensive documentation about available tools, usage patterns,
    and best practices for working with MCP servers through MCP Studio.

    **Levels:**
    - **basic**: Quick overview of available tools
    - **intermediate**: Detailed tool descriptions with examples
    - **advanced**: Complete API reference and advanced patterns

    **Topics:**
    - **tools**: Information about all available tools
    - **discovery**: How server discovery works
    - **execution**: Tool execution patterns and best practices
    - **configuration**: Server configuration and setup

    Args:
        level: Help detail level (basic, intermediate, advanced)
        topic: Optional specific topic to focus on

    Returns:
        Formatted help documentation as markdown string

    Examples:
        help() - Basic overview
        help("intermediate") - Detailed tool descriptions
        help("advanced", "execution") - Advanced execution patterns
        help("basic", "tools") - Quick tool reference
    """
    if topic:
        return _get_topic_help(topic, level)

    if level == "basic":
        return _get_basic_help()
    elif level == "intermediate":
        return _get_intermediate_help()
    elif level == "advanced":
        return _get_advanced_help()
    else:
        return f'''# Help - Invalid Level

Unknown help level: "{level}"

Available levels:
- **basic**: Quick overview of available tools
- **intermediate**: Detailed tool descriptions with examples
- **advanced**: Complete API reference and advanced patterns

Try: `help("basic")`'''


@app.tool()
async def set_discovery_path(path: str) -> Dict[str, Any]:
    """Set the MCP server discovery path.

    Updates the discovery path used for finding MCP servers. This path
    will be scanned recursively to discover available MCP servers.

    Args:
        path: The new discovery path to set (can be absolute or relative)

    Returns:
        Dictionary containing:
        - success: bool indicating if the path was set successfully
        - path: The resolved absolute path that was set
        - previous_paths: List of previous discovery paths
        - message: Human-readable status message

    Examples:
        # Set to a specific directory
        result = await set_discovery_path("D:/Dev/repos")

        # Set to a relative path (resolved to absolute)
        result = await set_discovery_path("./mcp-servers")
    """
    try:
        from mcp_studio.app.core.config import settings, update_settings

        # Resolve the path
        path_obj = Path(path).expanduser().resolve()

        if not path_obj.exists():
            return {
                "success": False,
                "error": f"Path does not exist: {path_obj}",
                "path": str(path_obj),
            }

        # Get previous paths
        previous_paths = list(settings.MCP_DISCOVERY_PATHS) if settings.MCP_DISCOVERY_PATHS else []

        # Update settings - add to list if not already present
        new_path = str(path_obj)
        if settings.MCP_DISCOVERY_PATHS:
            if new_path not in settings.MCP_DISCOVERY_PATHS:
                updated_paths = list(settings.MCP_DISCOVERY_PATHS) + [new_path]
            else:
                updated_paths = list(settings.MCP_DISCOVERY_PATHS)
        else:
            updated_paths = [new_path]

        update_settings(MCP_DISCOVERY_PATHS=updated_paths)

        # Update global DISCOVERY_PATHS for this session
        global DISCOVERY_PATHS
        DISCOVERY_PATHS = updated_paths

        return {
            "success": True,
            "path": new_path,
            "previous_paths": previous_paths,
            "current_paths": updated_paths,
            "message": f"Discovery path set to: {new_path}",
        }
    except Exception as e:
        return {"success": False, "error": str(e), "path": path}


@app.tool()
async def status(level: str = "basic", focus: Optional[str] = None) -> str:
    """Get comprehensive status information about MCP Studio.

    Provides system status, server connectivity, and operational metrics
    at different detail levels for monitoring and troubleshooting.

    **Levels:**
    - **basic**: Core system status and server counts
    - **intermediate**: Detailed server information and tool counts
    - **advanced**: Performance metrics and system resources

    **Focus Areas:**
    - **servers**: Status of discovered MCP servers
    - **tools**: Tool availability and counts
    - **system**: System resources and performance
    - **discovery**: Discovery service status

    Args:
        level: Status detail level (basic, intermediate, advanced)
        focus: Optional focus area (servers, tools, system, discovery)

    Returns:
        Formatted status report as markdown string

    Examples:
        status() - Basic system overview
        status("intermediate") - Detailed server information
        status("advanced", "servers") - Advanced server metrics
        status("basic", "tools") - Quick tool status
    """
    if focus:
        return _get_focused_status(focus, level)

    if level == "basic":
        return _get_basic_status()
    elif level == "intermediate":
        return _get_intermediate_status()
    elif level == "advanced":
        return _get_advanced_status()
    else:
        return f'''# Status - Invalid Level

Unknown status level: "{level}"

Available levels:
- **basic**: Core system status and server counts
- **intermediate**: Detailed server information and tool counts
- **advanced**: Performance metrics and system resources

Try: `status("basic")`'''


def _get_basic_help() -> str:
    """Basic help - quick overview."""
    return """# MCP Studio Help - Basic Overview

## What is MCP Studio?

MCP Studio is a comprehensive management platform for MCP (Model Context Protocol) servers.
It provides tools for discovering, managing, and interacting with MCP servers.

## Available Tools

1. **discover_clients** - Discover all MCP clients and their configured servers
2. **get_client_config** - Get configuration for a specific MCP client
3. **set_client_config** - Set or update configuration for a specific MCP client
4. **discover_mcp_servers** - Scan configured paths to find MCP servers
5. **get_server_info** - Get detailed information about a specific server
6. **list_server_tools** - List all tools provided by a server
7. **execute_remote_tool** - Execute a tool on a remote MCP server
8. **test_server_connection** - Test connectivity to an MCP server
9. **scan_repos_for_sota_compliance** - Scan directory for MCP repos and analyze SOTA status
10. **analyze_repo_sota_status** - Analyze a single repo for SOTA compliance
11. **help** - Get help documentation (this tool)
12. **status** - Get system status information

## Quick Start

1. Discover clients: `discover_clients()` - Find all MCP clients and their servers
2. Get client config: `get_client_config("claude-desktop")` - Read client configuration
3. Set client config: `set_client_config("claude-desktop", {"mcpServers": {...}})` - Update client configuration
4. Discover servers: `discover_mcp_servers()` - Scan paths for MCP servers
5. Get server info: `get_server_info("server-id")`
6. List tools: `list_server_tools("server-id")`
7. Execute tool: `execute_remote_tool("server-id", "tool-name", {"param": "value"})`

## Getting More Help

- `help("intermediate")` - Detailed tool descriptions
- `help("advanced")` - Complete API reference
- `help("basic", "tools")` - Tool-specific help
"""


def _get_intermediate_help() -> str:
    """Intermediate help - detailed descriptions."""
    return """# MCP Studio Help - Intermediate

## Tool Descriptions

### discover_clients

Discovers all MCP clients (Claude Desktop, Cursor IDE, Windsurf, etc.) and their configured servers.
Returns metadata about each client including type, platform, status, and list of servers.

**Example:**
```python
result = await discover_clients()
# Returns: {"success": True, "total_clients": 5, "clients": [...], "summary": {...}}
```

### discover_mcp_servers

Scans configured discovery paths to find MCP servers. Supports:
- Python-based servers (.py files)
- Node.js servers (.js files)
- Docker-based servers (Dockerfile or docker-compose.yml)
- Configuration-based servers (.json config files)

**Example:**
```python
result = await discover_mcp_servers()
# Returns: {"success": True, "servers": [...], "scanned_paths": [...]}
```

### get_server_info

Retrieves comprehensive metadata about an MCP server including:
- Server configuration and capabilities
- Available tools and their schemas
- Current status and health information
- Connection details and endpoints

**Example:**
```python
info = await get_server_info("my-server-id")
# Returns: {"success": True, "server": {...}}
```

### list_server_tools

Gets the complete list of tools available from an MCP server,
including their names, descriptions, and input schemas.

**Example:**
```python
tools = await list_server_tools("my-server-id")
# Returns: {"success": True, "server_id": "...", "tools": [...]}
```

### execute_remote_tool

Connects to a remote MCP server and executes the specified tool
with the provided parameters. Returns the tool execution result.

**Example:**
```python
result = await execute_remote_tool(
    "my-server-id",
    "my_tool",
    {"param1": "value1", "param2": 42}
)
# Returns: {"success": True, "server_id": "...", "tool_name": "...", "result": {...}}
```

### test_server_connection

Performs a connectivity test to verify that an MCP server is
accessible and responding correctly.

**Example:**
```python
status = await test_server_connection("my-server-id")
# Returns: {"success": True, "server_id": "...", "connection_status": {...}}
```

## Configuration

MCP Studio uses environment variables for configuration:
- `DISCOVERY_PATHS`: Comma-separated paths to scan (default: "./servers,./mcp-servers")
- `AUTO_DISCOVERY`: Enable auto-discovery on startup (default: "true")
"""


def _get_advanced_help() -> str:
    """Advanced help - complete API reference."""
    return """# MCP Studio Help - Advanced

## Complete API Reference

### Tool Execution Patterns

**Synchronous Pattern:**
```python
# Discover servers
servers = await discover_mcp_servers()

# Get first server
server_id = servers["servers"][0]["id"]

# List tools
tools = await list_server_tools(server_id)

# Execute tool
result = await execute_remote_tool(server_id, tools["tools"][0]["name"], {})
```

**Error Handling:**
```python
try:
    result = await execute_remote_tool("server-id", "tool-name", {})
    if result["success"]:
        print(f"Result: {result['result']}")
    else:
        print(f"Error: {result['error']}")
except Exception as e:
    print(f"Exception: {e}")
```

## Server Discovery

Discovery paths are scanned recursively for:
- `*.py` files with FastMCP imports
- `*.js` files with MCP server patterns
- `Dockerfile` or `docker-compose.yml` files
- `*.json` configuration files

## Tool Execution

Tool execution uses stdio transport:
1. Spawns server process
2. Establishes JSON-RPC connection
3. Sends tool execution request
4. Waits for response (30s timeout default)
5. Returns result or error

## Best Practices

1. **Always check success**: Verify `result["success"]` before using data
2. **Handle errors**: Wrap calls in try/except blocks
3. **Test connections**: Use `test_server_connection` before execution
4. **Cache server info**: Store server metadata to avoid repeated discovery
5. **Monitor status**: Use `status()` to track system health

## Troubleshooting

**Server not found:**
- Check discovery paths are correct
- Verify server files exist and are executable
- Check file permissions

**Tool execution fails:**
- Verify server is running and accessible
- Check tool name and parameters are correct
- Review server logs for errors

**Connection timeouts:**
- Increase timeout value
- Check server startup time
- Verify no blocking operations
"""


def _get_topic_help(topic: str, level: str) -> str:
    """Get help for a specific topic."""
    topic = topic.lower()

    if topic == "tools":
        return """# Tools Help

## Available Tools

MCP Studio provides 15 tools for managing MCP servers:

**Server Discovery & Management:**
1. **discover_clients** - Discover all MCP clients and their configured servers
2. **get_client_config** - Get configuration for a specific MCP client
3. **set_client_config** - Set or update configuration for a specific MCP client
4. **discover_mcp_servers** - Find MCP servers in configured paths
5. **get_server_info** - Get detailed server information
6. **list_server_tools** - List tools available on a server
7. **execute_remote_tool** - Execute a tool on a remote server
8. **test_server_connection** - Test server connectivity

**Server Lifecycle (CRUD):**
6. **create_mcp_server** - Create new SOTA-compliant MCP server
7. **update_mcp_server** - Add missing SOTA components to existing server
8. **delete_mcp_server** - Safely delete test/throwaway servers

**SOTA Analysis:**
9. **scan_repos_for_sota_compliance** - Scan directory for repos and analyze SOTA status
10. **analyze_repo_sota_status** - Analyze single repo for SOTA compliance

**System:**
11. **help** - Get help documentation
12. **status** - Get system status

For detailed information, use: `help("intermediate")`
"""
    elif topic == "discovery":
        return """# Discovery Help

## How Server Discovery Works

MCP Studio scans configured paths recursively to find MCP servers.

**Supported Server Types:**
- Python servers using FastMCP
- Node.js servers using MCP SDK
- Docker containers with MCP servers
- Configuration files defining servers

**Discovery Process:**
1. Scan all configured paths
2. Identify potential server files
3. Validate server configuration
4. Extract server metadata
5. Register discovered servers

**Configuration:**
Set `DISCOVERY_PATHS` environment variable with comma-separated paths.
"""
    elif topic == "execution":
        return """# Tool Execution Help

## Executing Tools on Remote Servers

**Basic Execution:**
```python
result = await execute_remote_tool(
    server_id="my-server",
    tool_name="my_tool",
    parameters={"param1": "value1"}
)
```

**Error Handling:**
Always check the `success` field in the response.

**Timeouts:**
Default timeout is 30 seconds. Long-running tools may need adjustment.

**Best Practices:**
- Test connection before execution
- Validate parameters match tool schema
- Handle errors gracefully
- Log execution results
"""
    elif topic == "configuration":
        return """# Configuration Help

## MCP Studio Configuration

**Environment Variables:**
- `DISCOVERY_PATHS`: Paths to scan (comma-separated)
- `AUTO_DISCOVERY`: Enable auto-discovery (true/false)

**Default Values:**
- Discovery paths: `./servers,./mcp-servers`
- Auto-discovery: `true`

**Server Configuration:**
Each discovered server maintains its own configuration including:
- Server path and command
- Environment variables
- Working directory
- Connection settings
"""
    else:
        return f'''# Help - Unknown Topic

Unknown topic: "{topic}"

Available topics:
- **tools**: Information about all available tools
- **discovery**: How server discovery works
- **execution**: Tool execution patterns and best practices
- **configuration**: Server configuration and setup

Try: `help("basic", "tools")`
'''


def _get_basic_status() -> str:
    """Basic status - core information."""
    try:
        from mcp_studio.app.services.discovery_service import discovered_servers

        server_count = len(discovered_servers)
        tool_count = sum(len(server.tools) for server in discovered_servers.values())

        return f"""# MCP Studio Status - Basic

## System Overview

- **Discovered Servers**: {server_count}
- **Total Tools Available**: {tool_count}
- **Server Status**: Active

## Quick Stats

- **Discovery Paths**: {", ".join(DISCOVERY_PATHS)}
- **Auto-Discovery**: {"Enabled" if AUTO_DISCOVERY else "Disabled"}

## Available Tools

MCP Studio provides 15 tools for server management.

For detailed status, use: `status("intermediate")`
"""
    except Exception as e:
        return f"""# MCP Studio Status - Basic

**Error retrieving status**: {str(e)}

Use `status("intermediate")` for more details.
"""


def _get_intermediate_status() -> str:
    """Intermediate status - detailed information."""
    try:
        from mcp_studio.app.services.discovery_service import discovered_servers
        import platform

        server_count = len(discovered_servers)
        tool_count = sum(len(server.tools) for server in discovered_servers.values())

        status_lines = [
            "# MCP Studio Status - Intermediate",
            "",
            "## Server Information",
            f"- **Discovered Servers**: {server_count}",
            f"- **Total Tools Available**: {tool_count}",
            "",
            "## Discovered Servers",
        ]

        for server_id, server in list(discovered_servers.items())[:10]:
            status_lines.append(f"- **{server.name}** ({server_id}): {len(server.tools)} tools")

        if server_count > 10:
            status_lines.append(f"- ... and {server_count - 10} more servers")

        status_lines.extend(
            [
                "",
                "## System Information",
                f"- **Platform**: {platform.system()} {platform.release()}",
                f"- **Python**: {platform.python_version()}",
                f"- **Architecture**: {platform.machine()}",
                "",
                "## Configuration",
                f"- **Discovery Paths**: {', '.join(DISCOVERY_PATHS)}",
                f"- **Auto-Discovery**: {'Enabled' if AUTO_DISCOVERY else 'Disabled'}",
            ]
        )

        return "\n".join(status_lines)
    except Exception as e:
        return f"""# MCP Studio Status - Intermediate

**Error retrieving status**: {str(e)}
"""


def _get_advanced_status() -> str:
    """Advanced status - performance metrics."""
    try:
        from mcp_studio.app.services.discovery_service import discovered_servers
        import platform
        import os

        server_count = len(discovered_servers)
        tool_count = sum(len(server.tools) for server in discovered_servers.values())

        status_lines = [
            "# MCP Studio Status - Advanced",
            "",
            "## Server Metrics",
            f"- **Discovered Servers**: {server_count}",
            f"- **Total Tools**: {tool_count}",
            f"- **Average Tools per Server**: {tool_count / server_count if server_count > 0 else 0:.1f}",
            "",
            "## System Resources",
            f"- **Platform**: {platform.system()} {platform.release()}",
            f"- **Python**: {platform.python_version()}",
            f"- **Architecture**: {platform.machine()}",
            f"- **Processor**: {platform.processor() or 'Unknown'}",
            f"- **Process ID**: {os.getpid()}",
        ]

        # Try to get memory usage if psutil available
        try:
            import psutil

            process = psutil.Process(os.getpid())
            memory_mb = process.memory_info().rss / 1024 / 1024
            cpu_percent = process.cpu_percent(interval=0.1)
            status_lines.extend(
                [
                    f"- **Memory Usage**: {memory_mb:.1f} MB",
                    f"- **CPU Usage**: {cpu_percent:.1f}%",
                ]
            )
        except ImportError:
            status_lines.append("- **Performance Metrics**: psutil not available")

        status_lines.extend(
            [
                "",
                "## Configuration Details",
                f"- **Discovery Paths**: {', '.join(DISCOVERY_PATHS)}",
                f"- **Auto-Discovery**: {'Enabled' if AUTO_DISCOVERY else 'Disabled'}",
                "",
                "## Server Breakdown",
            ]
        )

        for server_id, server in list(discovered_servers.items())[:20]:
            status_lines.append(
                f"- **{server.name}** ({server_id}): "
                f"{len(server.tools)} tools, status: {server.status.value}"
            )

        if server_count > 20:
            status_lines.append(f"- ... and {server_count - 20} more servers")

        return "\n".join(status_lines)
    except Exception as e:
        return f"""# MCP Studio Status - Advanced

**Error retrieving status**: {str(e)}
"""


@app.tool()
async def analyze_repo_sota_status(
    repo_path: str, scan_path: Optional[str] = None
) -> Dict[str, Any]:
    """Analyze a single MCP repository for SOTA compliance.

    Evaluates a repository against FastMCP 2.13 SOTA standards and returns
    detailed status including compliance level, issues, and recommendations.

    **Status Levels:**
    - **SOTA** ✅: Fully compliant with FastMCP 2.13 standards
    - **Improvable** ⚠️: Minor issues, mostly compliant
    - **Runt** 🐛: Needs significant upgrades

    **Checks Performed:**
    - FastMCP version (2.13+ required for SOTA)
    - Help and status tools (required)
    - Portmanteau pattern usage (>15 tools)
    - CI/CD workflows
    - Project structure (src/, tests/, tools/)
    - Tool registration patterns
    - Code quality (logging, error handling)

    Args:
        repo_path: Path to the repository to analyze
        scan_path: Optional base path if repo_path is relative (default: from REPOS_DIR env var or platform default)

    Returns:
        Dictionary containing:
        - success: bool indicating if analysis succeeded
        - status: SOTA compliance status (SOTA/Improvable/Runt)
        - fastmcp_version: Detected FastMCP version
        - tool_count: Number of tools found
        - portmanteau_tools: Number of portmanteau tools
        - individual_tools: Number of individual tools
        - is_runt: bool indicating if repo is a runt
        - runt_reasons: List of issues found
        - recommendations: List of upgrade recommendations
        - zoo_class: Repository size classification (jumbo/large/medium/small/chipmunk)
        - sota_score: Numeric SOTA compliance score

    Examples:
        # Analyze specific repo
        from mcp_studio.app.core.config import DEFAULT_REPOS_PATH
        result = await analyze_repo_sota_status(f"{DEFAULT_REPOS_PATH}/mcp-studio")

        # Analyze relative to scan path
        result = await analyze_repo_sota_status("mcp-studio", DEFAULT_REPOS_PATH)
    """
    try:
        from mcp_studio.app.core.config import DEFAULT_REPOS_PATH

        # Use default scan_path if not provided
        if scan_path is None:
            scan_path = DEFAULT_REPOS_PATH

        # If repo_path is relative and scan_path provided, combine them
        if scan_path and not Path(repo_path).is_absolute():
            full_path = Path(scan_path) / repo_path
        else:
            full_path = Path(repo_path).expanduser().resolve()

        result = await get_repo_status(str(full_path))
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "repo_path": repo_path}


# Expose CRUD tools for MCP server lifecycle management
@app.tool()
async def create_mcp_server(
    server_name: str,
    description: str,
    author: str = "MCP Studio",
    license_type: str = "MIT",
    target_path: Optional[str] = None,
    include_examples: bool = True,
    init_git: bool = True,
    include_frontend: bool = False,
    frontend_type: str = "fullstack",
) -> Dict[str, Any]:
    """Create a new SOTA-compliant MCP server from scratch.

    Scaffolds a complete MCP server with all SOTA requirements including
    FastMCP 2.13.1 setup, help/status tools, CI/CD, tests, documentation,
    and DXT packaging.

    With include_frontend=True, generates a complete fullstack app with
    React frontend, MCP client dashboard, and Docker deployment.

    Args:
        server_name: Name of the server to create (hyphen-case recommended)
        description: Description of what the server does
        author: Author name (default: "MCP Studio")
        license_type: License type (default: "MIT")
        target_path: Where to create server (default: from REPOS_DIR env var or platform default)
        include_examples: Include example tools (default: True)
        init_git: Initialize git repository (default: True)
        include_frontend: Generate frontend dashboard (default: False)
        frontend_type: Frontend type if include_frontend=True (default: "fullstack")

    Args:
        server_name: Kebab-case server name (e.g., "my-awesome-server")
        description: Server description
        author: Author name (default: "MCP Studio")
        license_type: License type (default: "MIT")
        target_path: Where to create server (default: "D:/Dev/repos")
        include_examples: Include example tools (default: True)
        init_git: Initialize git repository (default: True)
        include_frontend: Generate React frontend (default: False)
        frontend_type: "fullstack" for complete app, "minimal" for basic UI (default: "fullstack")

    Returns:
        Dictionary with creation status and server path
    """
    from mcp_studio.tools.server_scaffold import create_mcp_server as scaffold_server

    return await scaffold_server(
        server_name=server_name,
        description=description,
        author=author,
        license_type=license_type,
        target_path=target_path,
        include_examples=include_examples,
        init_git=init_git,
        include_frontend=include_frontend,
        frontend_type=frontend_type,
    )


@app.tool()
async def update_mcp_server(
    repo_path: str, components: Optional[List[str]] = None, dry_run: bool = True
) -> Dict[str, Any]:
    """Update an MCP server to add missing SOTA components.

    Analyzes a server and adds missing components to bring it to SOTA compliance.
    Can update specific components or auto-detect and add all missing ones.

    Args:
        repo_path: Path to the repository
        components: List of components to add (or None for auto-detect)
        dry_run: Preview changes without applying (default: True)

    Returns:
        Dictionary with update status and changes made
    """
    return await update_server(repo_path=repo_path, components=components, dry_run=dry_run)


@app.tool()
async def delete_mcp_server(
    repo_path: str, force: bool = False, backup: bool = True, dry_run: bool = True
) -> Dict[str, Any]:
    """Safely delete an MCP server repository.

    Performs safety checks before deletion including git repository detection,
    uncommitted changes check, and remote repository check.

    Args:
        repo_path: Path to the repository to delete
        force: Skip safety checks (default: False)
        backup: Create backup before deletion (default: True)
        dry_run: Preview deletion without applying (default: True)

    Returns:
        Dictionary with deletion status and warnings
    """
    return await delete_server(repo_path=repo_path, force=force, backup=backup, dry_run=dry_run)


@app.tool()
async def scan_repos_for_sota_compliance(
    scan_path: Optional[str] = None, max_depth: int = 1, include_sota: bool = True
) -> Dict[str, Any]:
    """Scan a directory for MCP repositories and analyze SOTA compliance.

    Scans a directory for MCP repositories and evaluates each against FastMCP 2.13
    SOTA standards. Returns categorized results showing which repos are SOTA compliant,
    which need improvements, and which are runts requiring upgrades.

    **Output Categories:**
    - **SOTA Repos** ✅: Fully compliant repositories
    - **Runts** 🐛: Repositories needing significant upgrades
    - **Summary**: Statistics and counts

    **Analysis Includes:**
    - FastMCP version compliance
    - Tool count and portmanteau usage
    - CI/CD presence and quality
    - Project structure compliance
    - Code quality metrics

    Args:
        scan_path: Directory to scan for MCP repositories (default: D:/Dev/repos)
        max_depth: How deep to scan subdirectories (default: 1 = direct children only)
        include_sota: Whether to include SOTA repos in results (default: True)

    Returns:
        Dictionary containing:
        - success: bool indicating if scan succeeded
        - summary: Statistics (total repos, runts count, sota count)
        - runts: List of runt repositories with details
        - sota_repos: List of SOTA-compliant repositories (if include_sota=True)
        - scan_path: Path that was scanned
        - timestamp: When scan was performed

    Examples:
        # Scan default path
        result = await scan_repos_for_sota_compliance()

        # Scan specific path, exclude SOTA repos
        from mcp_studio.app.core.config import DEFAULT_REPOS_PATH
        result = await scan_repos_for_sota_compliance(
            scan_path=f"{DEFAULT_REPOS_PATH}/mcp-servers",
            include_sota=False
        )

        # Deep scan (2 levels deep)
        result = await scan_repos_for_sota_compliance(
            scan_path=DEFAULT_REPOS_PATH,
            max_depth=2
        )
    """
    try:
        from mcp_studio.app.core.config import DEFAULT_REPOS_PATH

        # Use default scan_path if not provided
        if scan_path is None:
            scan_path = DEFAULT_REPOS_PATH

        result = await analyze_runts(
            scan_path=scan_path, max_depth=max_depth, include_sota=include_sota
        )
        return result
    except Exception as e:
        return {"success": False, "error": str(e), "scan_path": scan_path}


def _get_focused_status(focus: str, level: str) -> str:
    """Get status focused on a specific area."""
    focus = focus.lower()

    if focus == "servers":
        try:
            from mcp_studio.app.services.discovery_service import discovered_servers

            status_lines = ["# Server Status"]
            for server_id, server in discovered_servers.items():
                status_lines.append(
                    f"- **{server.name}** ({server_id}): "
                    f"{len(server.tools)} tools, status: {server.status.value}"
                )
            return "\n".join(status_lines)
        except Exception as e:
            return f"# Server Status\n\n**Error**: {e}"

    elif focus == "tools":
        try:
            from mcp_studio.app.services.discovery_service import discovered_servers

            tool_count = sum(len(server.tools) for server in discovered_servers.values())
            return f"""# Tool Status

- **Total Tools**: {tool_count}
- **MCP Studio Tools**: 15
- **Remote Server Tools**: {tool_count - 15 if tool_count >= 15 else 0}
"""
        except Exception as e:
            return f"# Tool Status\n\n**Error**: {e}"

    elif focus == "system":
        return _get_advanced_status()

    elif focus == "discovery":
        auto_status = "Enabled" if AUTO_DISCOVERY else "Disabled"
        return f"""# Discovery Status

- **Discovery Paths**: {", ".join(DISCOVERY_PATHS)}
- **Auto-Discovery**: {auto_status}
- **Status**: Active

Use `discover_mcp_servers()` to scan for servers.
Use `discover_clients()` to find all MCP clients and their servers.
"""

    else:
        return f'''# Status - Unknown Focus

Unknown focus area: "{focus}"

Available focus areas:
- **servers**: Status of discovered MCP servers
- **tools**: Tool availability and counts
- **system**: System resources and performance
- **discovery**: Discovery service status

Try: `status("basic", "servers")`
'''


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
