"""MCP server discovery service."""

import asyncio
import importlib
import importlib.util
import inspect
import json
import logging
import os
import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import aiohttp
from fastapi import HTTPException
from fastmcp import FastMCP
from pydantic import AnyHttpUrl, ValidationError

from ..core.config import settings
from ..core.logging_utils import get_logger
from ..core.stdio import transport_manager
from ..models.mcp import MCPServer, MCPTool, MCPToolParameter, ServerStatus

logger = get_logger(__name__)

# In-memory cache of discovered MCP servers
discovered_servers: Dict[str, MCPServer] = {}

# Set of server IDs that are currently being discovered
discovering_servers: Set[str] = set()

# Lock for thread-safe server discovery
discovery_lock = asyncio.Lock()

async def discover_mcp_servers() -> None:
    """Discover and register MCP servers from configured paths."""
    while True:
        try:
            logger.debug("Starting MCP server discovery")

            # Get all potential server paths
            server_paths = await _find_potential_servers()

            # Discover servers from each path
            discovery_tasks = []
            for server_path, server_type in server_paths:
                task = asyncio.create_task(
                    _discover_server(server_path, server_type)
                )
                discovery_tasks.append(task)

            # Wait for all discoveries to complete
            await asyncio.gather(*discovery_tasks, return_exceptions=True)

            # Remove servers that are no longer available
            await _cleanup_servers(server_paths)

            logger.debug("MCP server discovery completed", server_count=len(discovered_servers))

        except Exception as e:
            logger.error("Error during MCP server discovery", error=str(e), exc_info=True)

        # Wait before next discovery cycle
        await asyncio.sleep(30)  # Check every 30 seconds

async def _find_potential_servers() -> List[Tuple[Path, str]]:
    """Find potential MCP server paths."""
    server_paths = []

    # Check each discovery path
    for path_str in settings.MCP_DISCOVERY_PATHS:
        path = Path(path_str).expanduser().resolve()

        if not path.exists():
            logger.debug("Discovery path does not exist", path=str(path))
            continue

        if path.is_file() and path.suffix == ".py":
            # Single Python file
            server_paths.append((path, "python"))
        elif path.is_file() and path.suffix in (".mcpb", ".dxt"):
            # Packaged MCP server
            package_type = "mcpb" if path.suffix == ".mcpb" else "dxt"
            server_paths.append((path, package_type))
        elif path.is_dir():
            # Directory - look for Python modules or MCPB/DXT packages
            for item in path.iterdir():
                if item.is_file() and item.suffix == ".py" and item.stem != "__init__":
                    server_paths.append((item, "python"))
                elif item.is_dir() and (item / "__init__.py").exists():
                    server_paths.append((item, "python"))
                elif item.is_file() and item.suffix == ".mcpb":
                    server_paths.append((item, "mcpb"))
                elif item.is_file() and item.suffix == ".dxt":
                    server_paths.append((item, "dxt"))

    logger.debug("Found potential MCP servers", count=len(server_paths))
    return server_paths

async def _discover_server(server_path: Path, server_type: str) -> None:
    """Discover and register a single MCP server."""
    server_id = f"{server_type}:{server_path}"

    # Skip if already discovering this server
    if server_id in discovering_servers:
        return

    async with discovery_lock:
        try:
            discovering_servers.add(server_id)

            if server_type == "python":
                await _discover_python_server(server_path)
            elif server_type in ("dxt", "mcpb"):
                await _discover_dxt_server(server_path)

        except Exception as e:
            logger.error(
                "Error discovering MCP server",
                server_path=str(server_path),
                server_type=server_type,
                error=str(e),
                exc_info=True,
            )
        finally:
            discovering_servers.discard(server_id)

async def _discover_python_server(server_path: Path) -> None:
    """Discover a Python-based MCP server by launching it and connecting via stdio."""
    server_id = f"python:{server_path}"

    try:
        # Skip if already registered and recently checked
        if server_id in discovered_servers:
            server = discovered_servers[server_id]
            if server.last_seen and (datetime.utcnow() - server.last_seen).total_seconds() < 300:  # 5 minutes
                return

        # Launch the server process
        process = await asyncio.create_subprocess_exec(
            sys.executable, str(server_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        # Create MCP server model
        server = MCPServer(
            id=server_id,
            name=f"Python Server: {server_path.name}",
            path=str(server_path),
            args=[],
            cwd=str(server_path.parent),
            env=os.environ.copy(),
            status=ServerStatus.STARTING,
            metadata={
                "type": "python",
                "path": str(server_path),
                "discovered_at": datetime.utcnow().isoformat(),
                "last_seen": datetime.utcnow().isoformat()
            }
        )

        # Get transport and connect
        transport = await transport_manager.get_transport(server)
        if not transport:
            logger.error("Failed to get transport for server", server_id=server_id)
            return

        connected = await transport.connect()
        if not connected:
            logger.error("Failed to connect to server", server_id=server_id)
            return

        # Get server info via MCP protocol
        try:
            # List tools using MCP protocol
            tools_response = await transport.execute_tool("list_tools", {})
            if not tools_response or not tools_response.get("success"):
                logger.error("Failed to list tools from server", server_id=server_id)
                return

            tools_data = tools_response.get("result", {})
            tools = []

            for tool_name, tool_info in tools_data.items():
                tools.append(
                    MCPTool(
                        name=tool_name,
                        description=tool_info.get("description", ""),
                        parameters=[
                            MCPToolParameter(
                                name=param_name,
                                type=param_info.get("type", "string"),
                                description=param_info.get("description", ""),
                                required=param_info.get("required", True),
                                default=param_info.get("default"),
                            )
                            for param_name, param_info in tool_info.get("parameters", {}).items()
                        ],
                    )
                )

            # Update server status and tools
            server.status = ServerStatus.ONLINE
            server.tools = tools
            server.metadata.update({
                "version": tools_response.get("version", "1.0.0"),
                "last_seen": datetime.utcnow().isoformat()
            })

            # Register the server
            discovered_servers[server_id] = server
            logger.info("Discovered MCP server",
                      server_id=server_id,
                      tools=len(tools),
                      status=server.status.value)

        except Exception as e:
            logger.error(
                "Error discovering Python MCP server",
                path=str(server_path),
                error=str(e),
                exc_info=True,
            )
    finally:
        # Clean up
        if server_path.parent.is_dir() and str(server_path.parent) in sys.path:
            sys.path.remove(str(server_path.parent))

async def _discover_dxt_server(dxt_path: Path) -> None:
    """Discover a DXT/MCPB-packaged MCP server."""
    from .mcpb_loader import load_mcpb_package
    
    try:
        logger.info(
            "Loading packaged server",
            path=str(dxt_path),
            type="dxt/mcpb"
        )
        
        # Load the package
        server_config = await load_mcpb_package(dxt_path)
        
        if not server_config:
            logger.error(
                "Failed to load packaged server",
                path=str(dxt_path)
            )
            return
        
        # Create server ID
        server_id = f"package:{server_config['id']}"
        
        # Register the server
        server = MCPServer(
            id=server_id,
            name=server_config["name"],
            description=server_config.get("description", ""),
            path=server_config["command"],
            args=server_config["args"],
            cwd=server_config.get("cwd"),
            env=server_config.get("env", {}),
            status=ServerStatus.OFFLINE,
            metadata=server_config.get("metadata", {}),
            version=server_config.get("version", "unknown"),
            type=server_config["type"],
        )
        
        discovered_servers[server_id] = server
        
        logger.info(
            "Packaged server registered",
            server_id=server_id,
            name=server["name"],
            version=server.get("version", "unknown")
        )
        
    except Exception as e:
        logger.error(
            "Error loading packaged server",
            path=str(dxt_path),
            error=str(e),
            exc_info=True
        )

def _extract_tool_info(tool_name: str, tool_func: Any) -> Optional[MCPTool]:
    """Extract tool information from a tool function."""
    try:
        # Get function signature
        sig = inspect.signature(tool_func)

        # Extract docstring and parse Args section
        docstring = tool_func.__doc__ or ""
        param_descriptions = _parse_docstring_args(docstring)

        # Extract parameters
        parameters = []
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue

            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                param_type = _get_type_name(param.annotation)

            # Get description from parsed docstring or use default
            param_description = param_descriptions.get(param_name, "")

            param_info = MCPToolParameter(
                name=param_name,
                type=param_type,
                required=param.default == inspect.Parameter.empty,
                default=param.default if param.default != inspect.Parameter.empty else None,
                description=param_description,
            )
            parameters.append(param_info)

        # Extract docstring (full description)
        description = docstring.strip()

        return MCPTool(
            name=tool_name,
            description=description,
            parameters=parameters,
        )
    except Exception as e:
        logger.error("Error extracting tool info", tool=tool_name, error=str(e), exc_info=True)
        return None

def _get_type_name(type_obj: Any) -> str:
    """Get a string representation of a type."""
    if hasattr(type_obj, "__name__"):
        return type_obj.__name__.lower()
    return str(type_obj).lower()


def _parse_docstring_args(docstring: str) -> Dict[str, str]:
    """Parse docstring to extract parameter descriptions from Args section.
    
    Supports Google-style docstrings:
        Args:
            param_name: Parameter description
            param_name (type): Parameter description with type
            
    Returns:
        Dictionary mapping parameter names to their descriptions
    """
    if not docstring:
        return {}
    
    param_descriptions = {}
    
    # Find Args section (case-insensitive, handles "Args:" or "Parameters:")
    args_pattern = re.compile(r'^(Args|Parameters):\s*$', re.IGNORECASE | re.MULTILINE)
    match = args_pattern.search(docstring)
    
    if not match:
        return param_descriptions
    
    # Extract everything after Args:
    args_start = match.end()
    args_text = docstring[args_start:]
    
    # Stop at next section (Returns, Examples, Raises, etc.) or end of docstring
    next_section_pattern = re.compile(r'^(Returns?|Examples?|Raises?|Yields?|Note|See Also|Usage):\s*$', re.IGNORECASE | re.MULTILINE)
    next_match = next_section_pattern.search(args_text)
    if next_match:
        args_text = args_text[:next_match.start()]
    
    # Parse each parameter line
    # Pattern: param_name: description or param_name (type): description
    # Handles indented continuation lines
    lines = args_text.split('\n')
    current_param = None
    current_desc = []
    
    for line in lines:
        # Check if this is a parameter line (starts with word, then colon)
        # Handles: "param:", "param (type):", "param_name:", etc.
        param_match = re.match(r'^\s*(\w+)(?:\s*\([^)]+\))?:\s*(.+)?$', line)
        
        if param_match:
            # Save previous parameter
            if current_param and current_desc:
                param_descriptions[current_param] = ' '.join(current_desc).strip()
            
            # Start new parameter
            current_param = param_match.group(1)
            current_desc = [param_match.group(2)] if param_match.group(2) else []
        elif current_param:
            # Continuation line (indented or empty)
            stripped = line.strip()
            if stripped:
                current_desc.append(stripped)
            elif current_desc:  # Empty line ends description
                param_descriptions[current_param] = ' '.join(current_desc).strip()
                current_param = None
                current_desc = []
    
    # Save last parameter
    if current_param and current_desc:
        param_descriptions[current_param] = ' '.join(current_desc).strip()
    
    return param_descriptions

async def _cleanup_servers(active_paths: List[Tuple[Path, str]]) -> None:
    """Remove servers that are no longer available."""
    active_ids = {f"{server_type}:{path}" for path, server_type in active_paths}

    for server_id in list(discovered_servers.keys()):
        if server_id not in active_ids:
            logger.info("Removing inactive MCP server", server_id=server_id)
            del discovered_servers[server_id]

async def get_servers() -> List[MCPServer]:
    """Get all discovered MCP servers."""
    return list(discovered_servers.values())

async def get_server(server_id: str) -> Optional[MCPServer]:
    """Get a specific MCP server by ID."""
    return discovered_servers.get(server_id)

async def execute_tool(
    server_id: str, 
    tool_name: str, 
    parameters: Dict[str, Any],
    timeout: float = 30.0
) -> Dict[str, Any]:
    """Execute a tool on an MCP server.
    
    Args:
        server_id: ID of the MCP server
        tool_name: Name of the tool to execute
        parameters: Parameters to pass to the tool
        timeout: Maximum time to wait for execution (seconds)
        
    Returns:
        Dictionary containing execution result with keys:
        - success: bool indicating if execution succeeded
        - result: The tool execution result (if successful)
        - error: Error message (if failed)
        - execution_time: Time taken to execute (seconds)
        
    Raises:
        HTTPException: If server or tool not found, or execution fails
    """
    server = discovered_servers.get(server_id)
    if not server:
        raise HTTPException(
            status_code=404, 
            detail=f"Server {server_id} not found"
        )

    # Find the tool
    tool = next((t for t in server.tools if t.name == tool_name), None)
    if not tool:
        raise HTTPException(
            status_code=404, 
            detail=f"Tool {tool_name} not found on server {server_id}"
        )

    try:
        # Get transport for the server
        transport = await transport_manager.get_transport(server)
        if not transport:
            raise HTTPException(
                status_code=503,
                detail=f"Failed to connect to server {server_id}. Server may be unavailable."
            )

        # Execute the tool
        logger.info(
            "Executing tool",
            server_id=server_id,
            tool_name=tool_name,
            parameters=parameters
        )
        
        result = await transport.execute_tool(
            tool_name=tool_name,
            parameters=parameters,
            timeout=timeout
        )

        if result.success:
            return {
                "status": "success",
                "success": True,
                "result": result.result,
                "execution_time": result.execution_time,
            }
        else:
            raise HTTPException(
                status_code=500,
                detail=f"Tool execution failed: {result.error}"
            )

    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
    except Exception as e:
        logger.error(
            "Unexpected error executing tool",
            server_id=server_id,
            tool_name=tool_name,
            error=str(e),
            exc_info=True
        )
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error executing tool: {str(e)}"
        )


# Create a simple discovery service class
class DiscoveryService:
    """Simple discovery service implementation."""

    def __init__(self):
        self.settings = settings

    async def discover_mcp_servers(self):
        """Start MCP server discovery."""
        return await discover_mcp_servers()


# Global discovery service instance
discovery_service = DiscoveryService()
