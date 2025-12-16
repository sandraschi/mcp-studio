from pathlib import Path
from typing import Any

from fastapi import APIRouter

from mcp_studio.app.services.repo_scanner_service import repo_scanner

router = APIRouter(prefix="/repos", tags=["repos"])


@router.get("", response_model=list[dict[str, Any]])
def scan_repos(scan_path: str | None = None):
    """
    Trigger a repository scan.
    Returns previous results immediately if available, or empty list if first run.
    The actual scan runs in the background or thread to ensure non-blocking UI.
    Note: For immediate feedback, we run it synchronously in a thread (FastAPI defaults def to threadpool).
    """
    # Using 'def' in FastAPI runs in threadpool, preventing event loop blocking
    # This matches the successful fix from the prototype

    path_override = Path(scan_path) if scan_path else None
    return repo_scanner.scan_repos(scan_path=path_override)


@router.get("/progress")
async def get_scan_progress():
    """Get real-time progress of the current scan."""
    return repo_scanner.get_progress()


@router.get("/results")
async def get_scan_results():
    """Get results of the last completed scan."""
    return repo_scanner.get_results()
