"""
Smoke Test API Routes for MCP Studio.

Provides REST endpoints for MCP server connectivity testing.
"""
from typing import Optional

from fastapi import APIRouter, Query

from ..tools.smoke_test import smoke_test_all_servers, smoke_test_server

router = APIRouter(prefix="/api/smoke-test", tags=["smoke-test"])


@router.get("/server")
async def test_single_server(
    server_path: str = Query(..., description="Path to server entry point"),
    timeout: float = Query(default=10.0, description="Connection timeout"),
):
    """
    Run smoke test on a single MCP server.
    
    Test steps:
    1. Connect over stdio
    2. Initialize connection
    3. List tools
    4. Call help/status tool
    5. Verify response
    """
    result = await smoke_test_server(server_path=server_path, timeout=timeout)
    return result


@router.get("/all")
async def test_all_servers(
    scan_path: str = Query(default="D:/Dev/repos", description="Directory to scan"),
    max_concurrent: int = Query(default=3, description="Max concurrent tests"),
):
    """
    Run smoke tests on all MCP servers in a directory.
    
    Returns summary with pass/fail counts and individual results.
    """
    result = await smoke_test_all_servers(
        scan_path=scan_path,
        max_concurrent=max_concurrent,
    )
    return result


@router.get("/quick")
async def quick_test(
    scan_path: str = Query(default="D:/Dev/repos", description="Directory to scan"),
):
    """
    Quick connectivity check - just counts pass/fail without full details.
    """
    result = await smoke_test_all_servers(scan_path=scan_path, max_concurrent=5)
    return {
        "success": result["success"],
        "servers_tested": result["servers_tested"],
        "servers_passed": result["servers_passed"],
        "servers_failed": result["servers_failed"],
        "pass_rate": (
            f"{(result['servers_passed'] / result['servers_tested'] * 100):.0f}%"
            if result["servers_tested"] > 0 else "N/A"
        ),
        "scan_path": result["scan_path"],
        "timestamp": result["timestamp"],
    }

