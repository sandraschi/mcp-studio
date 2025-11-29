"""
Runt Analyzer API Routes for MCP Studio Dashboard.

Provides REST endpoints for the runt analyzer feature.
"""
from typing import Optional

from fastapi import APIRouter, Query

from ..tools.runt_analyzer import analyze_runts, get_repo_status

router = APIRouter(prefix="/api/runts", tags=["runts"])


@router.get("/")
async def get_runts(
    scan_path: str = Query(default="D:/Dev/repos", description="Directory to scan"),
    include_sota: bool = Query(default=True, description="Include SOTA repos in response")
):
    """
    Get all MCP repositories with runt analysis.
    
    Returns categorized list of repos:
    - runts: Repos needing upgrades
    - sota_repos: Repos meeting SOTA standards
    """
    result = await analyze_runts(scan_path=scan_path, include_sota=include_sota)
    return result


@router.get("/summary")
async def get_runts_summary(
    scan_path: str = Query(default="D:/Dev/repos", description="Directory to scan")
):
    """
    Get summary statistics for runt analysis.
    
    Returns quick stats without full repo details.
    """
    result = await analyze_runts(scan_path=scan_path, include_sota=False)
    return {
        "success": result.get("success"),
        "summary": result.get("summary"),
        "scan_path": result.get("scan_path"),
        "timestamp": result.get("timestamp")
    }


@router.get("/repo/{repo_name}")
async def get_repo_details(
    repo_name: str,
    base_path: str = Query(default="D:/Dev/repos", description="Base path for repos")
):
    """
    Get detailed SOTA status for a specific repository.
    """
    repo_path = f"{base_path}/{repo_name}"
    result = await get_repo_status(repo_path=repo_path)
    return result


@router.get("/thresholds")
async def get_thresholds():
    """
    Get current SOTA thresholds and criteria.
    """
    from ..tools.runt_analyzer import (
        FASTMCP_LATEST,
        FASTMCP_RUNT_THRESHOLD,
        TOOL_PORTMANTEAU_THRESHOLD,
    )
    
    return {
        "fastmcp_latest": FASTMCP_LATEST,
        "fastmcp_runt_threshold": FASTMCP_RUNT_THRESHOLD,
        "portmanteau_threshold": TOOL_PORTMANTEAU_THRESHOLD,
        "criteria": [
            f"FastMCP < {FASTMCP_RUNT_THRESHOLD} = runt",
            f"> {TOOL_PORTMANTEAU_THRESHOLD} tools without portmanteau = runt",
            "No CI/CD = runt",
            "> 3 CI workflows = bloated"
        ]
    }

