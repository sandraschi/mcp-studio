"""
MCP Server Tools

This module provides tools for discovering and managing MCP servers.
"""
import asyncio
import json
import logging
import socket
from typing import Dict, List, Optional, Union, Any

import aiohttp
import yaml
from pydantic import BaseModel, Field, HttpUrl, validator

from mcp_studio.tools import (
    tool, 
    structured_log, 
    validate_input, 
    rate_limited,
    retry_on_failure,
    cache_result,
    timed
)

logger = logging.getLogger("mcp.tools.server")

# Constants
DEFAULT_MCP_PORT = 8000
DEFAULT_TIMEOUT = 5.0

class ServerInfo(BaseModel):
    """Information about an MCP server."""
    name: str = Field(..., description="Name of the MCP server")
    url: HttpUrl = Field(..., description="Base URL of the MCP server")
    version: str = Field("1.0.0", description="Version of the MCP server")
    description: str = Field("", description="Description of the MCP server")
    tags: List[str] = Field(default_factory=list, description="Tags for categorization")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_encoders = {
            HttpUrl: lambda v: str(v)
        }

class ServerDiscoveryInput(BaseModel):
    """Input for server discovery."""
    network: str = Field("192.168.1.0/24", description="Network range to scan (CIDR notation)")
    ports: List[int] = Field([DEFAULT_MCP_PORT], description="Ports to scan")
    timeout: float = Field(DEFAULT_TIMEOUT, description="Connection timeout in seconds")

@tool(
    name="discover_servers",
    description="Discover MCP servers on the network",
    tags=["discovery", "network", "servers"]
)
@structured_log()
@validate_input(ServerDiscoveryInput)
@retry_on_failure(max_attempts=3, delay=1.0)
@rate_limited(calls=10, period=60.0)
@timed(print_result=True)
async def discover_servers(
    network: str = "192.168.1.0/24",
    ports: List[int] = [DEFAULT_MCP_PORT],
    timeout: float = DEFAULT_TIMEOUT
) -> List[Dict[str, Any]]:
    """
    Discover MCP servers on the network.
    
    Args:
        network: Network range in CIDR notation (e.g., '192.168.1.0/24')
        ports: List of ports to scan
        timeout: Connection timeout in seconds
        
    Returns:
        List of discovered servers with their information
    """
    import ipaddress
    from concurrent.futures import ThreadPoolExecutor
    
    network_obj = ipaddress.ip_network(network, strict=False)
    hosts = [str(host) for host in network_obj.hosts()]
    
    async def check_host(host: str, port: int) -> Optional[Dict[str, Any]]:
        """Check if a host is running an MCP server."""
        try:
            url = f"http://{host}:{port}/mcp/status"
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=timeout) as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "name": data.get("name", f"mcp-{host}"),
                            "url": f"http://{host}:{port}",
                            "version": data.get("version", "1.0.0"),
                            "description": data.get("description", ""),
                            "metadata": data
                        }
        except Exception as e:
            logger.debug(f"Failed to connect to {host}:{port}: {str(e)}")
        return None
    
    # Check all hosts and ports
    tasks = []
    for host in hosts:
        for port in ports:
            tasks.append(check_host(host, port))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Filter out None results and exceptions
    servers = [r for r in results if r is not None and not isinstance(r, Exception)]
    
    logger.info(
        "server_discovery_complete",
        extra={
            "network": network,
            "ports": ports,
            "servers_found": len(servers),
            "servers": servers
        }
    )
    
    return servers

@tool(
    name="get_server_info",
    description="Get information about an MCP server",
    tags=["servers", "info"]
)
@structured_log()
@retry_on_failure(max_attempts=3, delay=1.0)
@cache_result(ttl=300)  # Cache for 5 minutes
async def get_server_info(server_url: str) -> Dict[str, Any]:
    """
    Get information about an MCP server.
    
    Args:
        server_url: Base URL of the MCP server
        
    Returns:
        Server information including name, version, and available tools
    """
    try:
        # Ensure URL has a trailing slash
        if not server_url.endswith('/'):
            server_url += '/'
            
        async with aiohttp.ClientSession() as session:
            # Get server status
            status_url = f"{server_url}mcp/status"
            async with session.get(status_url) as response:
                response.raise_for_status()
                status_data = await response.json()
            
            # Get available tools
            tools_url = f"{server_url}mcp/tools"
            async with session.get(tools_url) as response:
                response.raise_for_status()
                tools_data = await response.json()
            
            return {
                "name": status_data.get("name", "Unknown"),
                "version": status_data.get("version", "1.0.0"),
                "description": status_data.get("description", ""),
                "url": server_url,
                "tools": tools_data.get("tools", []),
                "metadata": status_data.get("metadata", {})
            }
            
    except Exception as e:
        logger.error(
            "failed_to_get_server_info",
            extra={
                "server_url": server_url,
                "error": str(e)
            },
            exc_info=True
        )
        raise

@tool(
    name="execute_remote_tool",
    description="Execute a tool on a remote MCP server",
    tags=["execution", "remote"]
)
@structured_log()
@retry_on_failure(max_attempts=3, delay=1.0)
async def execute_remote_tool(
    server_url: str,
    tool_name: str,
    parameters: Dict[str, Any],
    timeout: float = 30.0
) -> Dict[str, Any]:
    """
    Execute a tool on a remote MCP server.
    
    Args:
        server_url: Base URL of the MCP server
        tool_name: Name of the tool to execute
        parameters: Parameters to pass to the tool
        timeout: Request timeout in seconds
        
    Returns:
        Tool execution result
    """
    try:
        # Ensure URL has a trailing slash
        if not server_url.endswith('/'):
            server_url += '/'
            
        tool_url = f"{server_url}mcp/tools/{tool_name}/execute"
        
        async with aiohttp.ClientSession() as session:
            async with session.post(
                tool_url,
                json={"parameters": parameters},
                timeout=timeout
            ) as response:
                response.raise_for_status()
                return await response.json()
                
    except Exception as e:
        logger.error(
            "failed_to_execute_remote_tool",
            extra={
                "server_url": server_url,
                "tool_name": tool_name,
                "error": str(e)
            },
            exc_info=True
        )
        raise

@tool(
    name="list_server_tools",
    description="List tools available on an MCP server",
    tags=["servers", "tools", "discovery"]
)
@structured_log()
@retry_on_failure(max_attempts=2, delay=1.0)
@cache_result(ttl=60)  # Cache for 1 minute
async def list_server_tools(server_url: str) -> List[Dict[str, Any]]:
    """
    List tools available on an MCP server.
    
    Args:
        server_url: Base URL of the MCP server
        
    Returns:
        List of available tools with their metadata
    """
    try:
        # Ensure URL has a trailing slash
        if not server_url.endswith('/'):
            server_url += '/'
            
        tools_url = f"{server_url}mcp/tools"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(tools_url) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("tools", [])
                
    except Exception as e:
        logger.error(
            "failed_to_list_server_tools",
            extra={
                "server_url": server_url,
                "error": str(e)
            },
            exc_info=True
        )
        raise

@tool(
    name="test_server_connection",
    description="Test connection to an MCP server",
    tags=["servers", "diagnostics"]
)
@structured_log()
async def test_server_connection(server_url: str, timeout: float = 5.0) -> Dict[str, Any]:
    """
    Test connection to an MCP server.
    
    Args:
        server_url: Base URL of the MCP server
        timeout: Connection timeout in seconds
        
    Returns:
        Connection test results
    """
    import time
    from urllib.parse import urlparse
    
    result = {
        "server_url": server_url,
        "timestamp": time.time(),
        "success": False,
        "latency_ms": None,
        "error": None,
        "details": {}
    }
    
    try:
        # Parse URL to extract hostname and port
        parsed_url = urlparse(server_url)
        hostname = parsed_url.hostname
        port = parsed_url.port or 80
        
        # Test TCP connection
        start_time = time.monotonic()
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(hostname, port),
            timeout=timeout
        )
        writer.close()
        await writer.wait_closed()
        tcp_time = (time.monotonic() - start_time) * 1000  # Convert to ms
        
        result.update({
            "tcp_connect": True,
            "tcp_latency_ms": round(tcp_time, 2)
        })
        
        # Test HTTP connection
        start_time = time.monotonic()
        async with aiohttp.ClientSession() as session:
            status_url = f"{server_url}mcp/status"
            async with session.get(status_url, timeout=timeout) as response:
                http_time = (time.monotonic() - start_time) * 1000  # Convert to ms
                status_data = await response.json()
                
                result.update({
                    "http_connect": True,
                    "http_status": response.status,
                    "http_latency_ms": round(http_time, 2),
                    "server_name": status_data.get("name", "Unknown"),
                    "server_version": status_data.get("version", "Unknown"),
                    "success": response.status == 200
                })
        
        return result
        
    except asyncio.TimeoutError:
        error_msg = f"Connection to {server_url} timed out after {timeout} seconds"
        result["error"] = error_msg
        logger.warning("connection_timeout", extra={"server_url": server_url})
        return result
        
    except Exception as e:
        error_msg = str(e)
        result["error"] = error_msg
        logger.error(
            "connection_test_failed",
            extra={"server_url": server_url, "error": error_msg},
            exc_info=True
        )
        return result
