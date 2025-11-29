"""
MCP Server Smoke Test Tool.

Bare minimum connectivity test for MCP servers:
1. Connect over stdio
2. Call help/status tool
3. Verify non-empty response

No LLM required - just validates the server is alive and responding.
"""
import asyncio
import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger(__name__)

# Timeout for connection and tool calls
CONNECTION_TIMEOUT = 10.0
TOOL_CALL_TIMEOUT = 5.0

# Tools to try calling (in order of preference)
SMOKE_TEST_TOOLS = ["help", "status", "get_help", "get_status", "info", "health"]


async def smoke_test_server(
    server_path: str,
    timeout: float = CONNECTION_TIMEOUT,
) -> Dict[str, Any]:
    """
    Perform a bare minimum smoke test on an MCP server.

    Test steps:
    1. Spawn server process via stdio
    2. Send initialize request
    3. List available tools
    4. Call help/status tool (if available)
    5. Verify response is non-empty

    Args:
        server_path: Path to the server entry point (e.g., server.py)
        timeout: Connection timeout in seconds

    Returns:
        Test result with success status, latency, and any errors
    """
    result = {
        "server_path": server_path,
        "success": False,
        "steps_completed": [],
        "tools_found": [],
        "smoke_tool_called": None,
        "smoke_response_length": 0,
        "latency_ms": {},
        "errors": [],
        "timestamp": time.time(),
    }

    server_file = Path(server_path)
    if not server_file.exists():
        result["errors"].append(f"Server file not found: {server_path}")
        return result

    process = None
    try:
        # Step 1: Spawn server process
        start_time = time.time()
        
        # Determine how to run the server
        if server_file.suffix == ".py":
            cmd = [sys.executable, str(server_file)]
        elif server_file.suffix == ".js":
            cmd = ["node", str(server_file)]
        else:
            result["errors"].append(f"Unsupported server type: {server_file.suffix}")
            return result

        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=str(server_file.parent),
            env={**os.environ, "PYTHONUNBUFFERED": "1"},
        )
        
        spawn_time = (time.time() - start_time) * 1000
        result["latency_ms"]["spawn"] = round(spawn_time, 2)
        result["steps_completed"].append("spawn_process")

        # Step 2: Send initialize request
        init_request = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": "initialize",
            "params": {
                "protocolVersion": "2024-11-05",
                "capabilities": {},
                "clientInfo": {"name": "mcp-studio-smoke-test", "version": "1.0.0"},
            },
        }
        
        start_time = time.time()
        response = await _send_request(process, init_request, timeout)
        init_time = (time.time() - start_time) * 1000
        result["latency_ms"]["initialize"] = round(init_time, 2)
        
        if not response or "error" in response:
            result["errors"].append(f"Initialize failed: {response.get('error', 'no response')}")
            return result
        
        result["steps_completed"].append("initialize")

        # Step 3: List tools
        list_tools_request = {
            "jsonrpc": "2.0",
            "id": 2,
            "method": "tools/list",
            "params": {},
        }
        
        start_time = time.time()
        response = await _send_request(process, list_tools_request, timeout)
        list_time = (time.time() - start_time) * 1000
        result["latency_ms"]["list_tools"] = round(list_time, 2)
        
        if not response or "error" in response:
            result["errors"].append(f"List tools failed: {response.get('error', 'no response')}")
            return result
        
        tools = response.get("result", {}).get("tools", [])
        result["tools_found"] = [t.get("name") for t in tools]
        result["steps_completed"].append("list_tools")

        # Step 4: Find and call a smoke test tool
        smoke_tool = None
        for preferred_tool in SMOKE_TEST_TOOLS:
            if preferred_tool in result["tools_found"]:
                smoke_tool = preferred_tool
                break
        
        if not smoke_tool and result["tools_found"]:
            # Fall back to first available tool
            smoke_tool = result["tools_found"][0]
        
        if smoke_tool:
            call_request = {
                "jsonrpc": "2.0",
                "id": 3,
                "method": "tools/call",
                "params": {
                    "name": smoke_tool,
                    "arguments": {},
                },
            }
            
            start_time = time.time()
            response = await _send_request(process, call_request, TOOL_CALL_TIMEOUT)
            call_time = (time.time() - start_time) * 1000
            result["latency_ms"]["tool_call"] = round(call_time, 2)
            
            if response and "result" in response:
                result["smoke_tool_called"] = smoke_tool
                content = response.get("result", {}).get("content", [])
                if content:
                    text = str(content[0].get("text", ""))
                    result["smoke_response_length"] = len(text)
                result["steps_completed"].append("tool_call")
            else:
                result["errors"].append(f"Tool call failed: {response.get('error', 'no response')}")
        else:
            result["errors"].append("No tools found to test")

        # Step 5: Determine success
        result["success"] = (
            "initialize" in result["steps_completed"]
            and "list_tools" in result["steps_completed"]
            and len(result["tools_found"]) > 0
        )
        
        # Bonus points for successful tool call
        if "tool_call" in result["steps_completed"] and result["smoke_response_length"] > 0:
            result["success"] = True

    except asyncio.TimeoutError:
        result["errors"].append(f"Timeout after {timeout}s")
    except Exception as e:
        result["errors"].append(f"Exception: {str(e)}")
        logger.error("Smoke test failed", server_path=server_path, error=str(e))
    finally:
        if process:
            try:
                process.terminate()
                await asyncio.wait_for(process.wait(), timeout=2.0)
            except:
                process.kill()

    return result


async def _send_request(
    process: asyncio.subprocess.Process,
    request: Dict[str, Any],
    timeout: float,
) -> Optional[Dict[str, Any]]:
    """Send a JSON-RPC request and wait for response."""
    try:
        # Send request
        request_str = json.dumps(request)
        message = f"Content-Length: {len(request_str)}\r\n\r\n{request_str}"
        process.stdin.write(message.encode())
        await process.stdin.drain()

        # Read response with timeout
        response_data = await asyncio.wait_for(
            _read_response(process.stdout),
            timeout=timeout,
        )
        
        if response_data:
            return json.loads(response_data)
        return None

    except asyncio.TimeoutError:
        raise
    except Exception as e:
        logger.error("Request failed", error=str(e))
        return None


async def _read_response(stdout: asyncio.StreamReader) -> Optional[str]:
    """Read a JSON-RPC response from stdout."""
    # Read headers
    headers = {}
    while True:
        line = await stdout.readline()
        if not line:
            return None
        line = line.decode().strip()
        if not line:
            break
        if ":" in line:
            key, value = line.split(":", 1)
            headers[key.strip().lower()] = value.strip()

    # Read body
    content_length = int(headers.get("content-length", 0))
    if content_length > 0:
        body = await stdout.read(content_length)
        return body.decode()
    
    return None


async def smoke_test_all_servers(
    scan_path: str = "D:/Dev/repos",
    max_concurrent: int = 3,
) -> Dict[str, Any]:
    """
    Run smoke tests on all MCP servers in a directory.

    Args:
        scan_path: Directory to scan for MCP servers
        max_concurrent: Max concurrent tests

    Returns:
        Summary with all test results
    """
    from .runt_analyzer import _analyze_repo
    
    results = {
        "success": True,
        "scan_path": scan_path,
        "servers_tested": 0,
        "servers_passed": 0,
        "servers_failed": 0,
        "results": [],
        "timestamp": time.time(),
    }
    
    path = Path(scan_path)
    if not path.exists():
        results["success"] = False
        results["error"] = f"Path not found: {scan_path}"
        return results
    
    # Find server entry points
    servers_to_test = []
    for repo_dir in path.iterdir():
        if not repo_dir.is_dir() or repo_dir.name.startswith('.'):
            continue
        
        # Check if it's an MCP repo
        repo_info = _analyze_repo(repo_dir)
        if not repo_info:
            continue
        
        # Find server entry point
        server_paths = [
            repo_dir / "server.py",
            repo_dir / "src" / f"{repo_dir.name.replace('-', '_')}" / "server.py",
            repo_dir / f"{repo_dir.name.replace('-', '_')}" / "server.py",
        ]
        
        for server_path in server_paths:
            if server_path.exists():
                servers_to_test.append({
                    "name": repo_dir.name,
                    "path": str(server_path),
                    "repo_info": repo_info,
                })
                break
    
    # Run tests with concurrency limit
    semaphore = asyncio.Semaphore(max_concurrent)
    
    async def test_with_limit(server_info):
        async with semaphore:
            test_result = await smoke_test_server(server_info["path"])
            return {
                "name": server_info["name"],
                "repo_status": server_info["repo_info"]["status_color"],
                **test_result,
            }
    
    tasks = [test_with_limit(s) for s in servers_to_test]
    test_results = await asyncio.gather(*tasks, return_exceptions=True)
    
    for r in test_results:
        if isinstance(r, Exception):
            results["results"].append({"error": str(r)})
            results["servers_failed"] += 1
        else:
            results["results"].append(r)
            results["servers_tested"] += 1
            if r.get("success"):
                results["servers_passed"] += 1
            else:
                results["servers_failed"] += 1
    
    return results

