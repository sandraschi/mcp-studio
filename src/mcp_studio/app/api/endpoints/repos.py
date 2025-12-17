from pathlib import Path
from typing import Any, Dict, List
import logging

from fastapi import APIRouter, Query, BackgroundTasks

from mcp_studio.app.services.repo_scanner_service import repo_scanner

logger = logging.getLogger(__name__)

router = APIRouter(tags=["repos"])


@router.get("/")
async def get_repos():
    """Get repository data. Returns 'no data yet' if no scan has been completed."""
    logger.info("get_repos() called")

    # Check if we have scan results
    results = repo_scanner.get_results()
    if results:
        return {
            "status": "success",
            "data": results,
            "count": len(results),
            "scan_url": "/api/v1/repos/run_scan"
        }
    else:
        return {
            "status": "no_data",
            "message": "No scan data yet. Click 'START REPO SCAN' to analyze repositories.",
            "scan_url": "/api/v1/repos/run_scan"
        }


@router.post("/run_scan")
async def run_repo_scan(
    background_tasks: BackgroundTasks,
    scan_path: str = Query(default=None, description="Directory to scan"),
    include_sota: bool = Query(default=True, description="Include SOTA repos in response")
):
    """
    Start a repository scan.

    Returns immediately while scan runs in background.
    """
    logger.info(f"Starting repo scan: path={scan_path}, include_sota={include_sota}")

    # Convert scan_path to Path if provided
    scan_path_obj = Path(scan_path) if scan_path else None

    # Start scan in background
    background_tasks.add_task(repo_scanner.scan_repos, scan_path_obj)

    logger.info("Repository scan started in background using repo_scanner service")
    return {
        "status": "scan_started",
        "message": "Repository scan started in background. Check progress with /api/v1/repos/progress"
    }


@router.get("/progress")
async def get_scan_progress():
    """Get real-time progress of the current scan."""
    return repo_scanner.get_progress()
