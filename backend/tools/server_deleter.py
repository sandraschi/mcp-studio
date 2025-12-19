"""MCP Server Deletion Tool.

Safely removes test/throwaway MCP servers with safety checks.
"""

import shutil
from pathlib import Path
from typing import Any, Dict, Optional
import subprocess

import structlog

from .decorators import ToolCategory, tool
from .scan_cache import clear_cache

logger = structlog.get_logger(__name__)


def _is_git_repo(path: Path) -> bool:
    """Check if path is a git repository."""
    return (path / ".git").exists()


def _has_uncommitted_changes(path: Path) -> bool:
    """Check if git repo has uncommitted changes."""
    if not _is_git_repo(path):
        return False
    
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        return bool(result.stdout.strip())
    except Exception:
        return False


def _get_git_remote(path: Path) -> Optional[str]:
    """Get git remote URL if exists."""
    if not _is_git_repo(path):
        return None
    
    try:
        result = subprocess.run(
            ["git", "remote", "get-url", "origin"],
            cwd=path,
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout.strip()
    except Exception:
        return None


@tool(
    name="delete_mcp_server",
    description="""Safely delete an MCP server repository.

    Performs safety checks before deletion:
    - Git repository detection (warns if not throwaway)
    - Uncommitted changes check
    - Remote repository check
    - Backup option
    
    Use with caution - deletion is permanent!""",
    category=ToolCategory.DISCOVERY,
    tags=["server", "delete", "remove", "cleanup"],
    estimated_runtime="1-2s"
)
async def delete_mcp_server(
    repo_path: str,
    force: bool = False,
    backup: bool = True,
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Delete an MCP server repository.
    
    Args:
        repo_path: Path to the repository to delete
        force: Skip safety checks (default: False)
        backup: Create backup before deletion (default: True)
        dry_run: Preview deletion without applying (default: True)
    
    Returns:
        Dictionary with deletion status and warnings
    """
    try:
        path = Path(repo_path).expanduser().resolve()
        
        if not path.exists():
            return {
                "success": False,
                "error": f"Repository not found: {repo_path}"
            }
        
        server_name = path.name
        warnings = []
        safety_checks = {}
        
        # Safety checks
        is_git = _is_git_repo(path)
        safety_checks["is_git_repo"] = is_git
        
        if is_git:
            has_uncommitted = _has_uncommitted_changes(path)
            safety_checks["has_uncommitted_changes"] = has_uncommitted
            
            remote = _get_git_remote(path)
            safety_checks["has_remote"] = bool(remote)
            safety_checks["remote_url"] = remote
            
            if remote:
                warnings.append(f"⚠️ Repository has remote: {remote}")
                if not force:
                    return {
                        "success": False,
                        "error": "Repository has remote. Use force=True to delete anyway.",
                        "safety_checks": safety_checks,
                        "warnings": warnings
                    }
            
            if has_uncommitted:
                warnings.append("⚠️ Repository has uncommitted changes")
        
        # Check if it's in a common repos directory (safer to delete)
        path_str = str(path).lower()
        is_in_repos = any(marker in path_str for marker in [
            "dev/repos",
            "repositories",
            "projects",
            "workspace"
        ])
        safety_checks["is_in_repos_directory"] = is_in_repos
        
        if not is_in_repos and not force:
            warnings.append("⚠️ Repository is not in a standard repos directory")
        
        # Create backup if requested
        backup_path = None
        if backup and not dry_run:
            backup_dir = path.parent / f"{server_name}.backup"
            if backup_dir.exists():
                backup_dir = path.parent / f"{server_name}.backup.{int(__import__('time').time())}"
            
            try:
                shutil.copytree(path, backup_dir)
                backup_path = str(backup_dir)
                logger.info(f"Created backup: {backup_path}")
            except Exception as e:
                warnings.append(f"⚠️ Failed to create backup: {e}")
        
        # Perform deletion
        if dry_run:
            return {
                "success": True,
                "dry_run": True,
                "repo_path": str(path),
                "server_name": server_name,
                "safety_checks": safety_checks,
                "warnings": warnings,
                "would_delete": True,
                "backup_path": backup_path,
                "message": "Dry run - no changes made. Set dry_run=False to delete."
            }
        
        if not force and warnings:
            return {
                "success": False,
                "error": "Safety checks failed. Review warnings and use force=True to proceed.",
                "safety_checks": safety_checks,
                "warnings": warnings
            }
        
        # Delete the directory
        try:
            shutil.rmtree(path)
            logger.info(f"Deleted repository: {path}")
            
            # Clear cache for this repo
            try:
                clear_cache(repo_path=repo_path)
            except Exception as e:
                logger.warning(f"Failed to clear cache: {e}")
            
            return {
                "success": True,
                "repo_path": str(path),
                "server_name": server_name,
                "deleted": True,
                "backup_path": backup_path,
                "safety_checks": safety_checks,
                "warnings": warnings,
                "message": f"Repository {server_name} deleted successfully"
            }
        
        except Exception as e:
            logger.error(f"Failed to delete repository: {e}", exc_info=True)
            return {
                "success": False,
                "error": f"Failed to delete: {str(e)}",
                "backup_path": backup_path
            }
    
    except Exception as e:
        logger.error(f"Failed to delete MCP server: {e}", exc_info=True)
        return {
            "success": False,
            "error": str(e)
        }
