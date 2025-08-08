""MCP server discovery service."""

import asyncio
import importlib
import importlib.util
import inspect
import json
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import aiohttp
import structlog
from fastapi import HTTPException
from fastmcp import FastMCP, MCPClient
from pydantic import AnyHttpUrl, ValidationError

from ..core.config import settings
from ..models.mcp import MCPServer, MCPTool, MCPToolParameter, ServerStatus

logger = structlog.get_logger(__name__)

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
        elif path.is_dir():
            # Directory - look for Python modules or DXT packages
            for item in path.iterdir():
                if item.is_file() and item.suffix == ".py" and item.stem != "__init__":
                    server_paths.append((item, "python"))
                elif item.is_dir() and (item / "__init__.py").exists():
                    server_paths.append((item, "python"))
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
            elif server_type == "dxt":
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
    """Discover a Python-based MCP server."""
    try:
        # Import the module
        module_name = server_path.stem
        if server_path.parent.is_dir():
            sys.path.insert(0, str(server_path.parent))
            
        spec = importlib.util.spec_from_file_location(module_name, str(server_path))
        if spec is None or spec.loader is None:
            logger.warning("Could not load Python module", path=str(server_path))
            return
            
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        
        # Find the FastMCP instance
        mcp = None
        for name, obj in inspect.getmembers(module):
            if isinstance(obj, FastMCP):
                mcp = obj
                break
        
        if mcp is None:
            logger.warning("No FastMCP instance found in module", module=module_name)
            return
        
        # Create server info
        server = MCPServer(
            id=f"python:{server_path}",
            name=getattr(mcp, "name", module_name),
            version=getattr(mcp, "version", "0.1.0"),
            description=getattr(mcp, "description", ""),
            path=str(server_path),
            type="python",
            status=ServerStatus.ONLINE,
            tools=[],
        )
        
        # Extract tools
        for tool_name, tool_func in mcp._tools.items():
            tool = _extract_tool_info(tool_name, tool_func)
            if tool:
                server.tools.append(tool)
        
        # Register the server
        discovered_servers[server.id] = server
        logger.info("Discovered Python MCP server", server_id=server.id, tool_count=len(server.tools))
        
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
    """Discover a DXT-packaged MCP server."""
    # TODO: Implement DXT package discovery
    logger.warning("DXT package discovery not yet implemented", path=str(dxt_path))

def _extract_tool_info(tool_name: str, tool_func: Any) -> Optional[MCPTool]:
    """Extract tool information from a tool function."""
    try:
        # Get function signature
        sig = inspect.signature(tool_func)
        
        # Extract parameters
        parameters = []
        for param_name, param in sig.parameters.items():
            if param_name == "self":
                continue
                
            param_type = "string"
            if param.annotation != inspect.Parameter.empty:
                param_type = _get_type_name(param.annotation)
            
            param_info = MCPToolParameter(
                name=param_name,
                type=param_type,
                required=param.default == inspect.Parameter.empty,
                default=param.default if param.default != inspect.Parameter.empty else None,
                description="",  # TODO: Extract from docstring
            )
            parameters.append(param_info)
        
        # Extract docstring
        description = tool_func.__doc__ or ""
        
        return MCPTool(
            name=tool_name,
            description=description.strip(),
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

async def execute_tool(server_id: str, tool_name: str, parameters: Dict[str, Any]) -> Any:
    """Execute a tool on an MCP server."""
    server = discovered_servers.get(server_id)
    if not server:
        raise HTTPException(status_code=404, detail=f"Server {server_id} not found")
    
    # Find the tool
    tool = next((t for t in server.tools if t.name == tool_name), None)
    if not tool:
        raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found on server {server_id}")
    
    # TODO: Implement tool execution
    # This will require connecting to the MCP server and sending the tool execution request
    
    return {"status": "success", "message": "Tool execution not yet implemented"}
