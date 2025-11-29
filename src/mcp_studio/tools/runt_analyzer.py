"""
Runt Analyzer Tool for MCP Studio.

Scans MCP repositories and identifies "runts" - repos that need SOTA upgrades.
"""
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import structlog

from .decorators import ToolCategory, tool

logger = structlog.get_logger(__name__)

# SOTA thresholds
FASTMCP_LATEST = "2.13.1"
FASTMCP_RUNT_THRESHOLD = "2.12.0"
TOOL_PORTMANTEAU_THRESHOLD = 15  # Repos with >15 tools should have portmanteau


@tool(
    name="analyze_runts",
    description="""Analyze MCP repositories to identify "runts" needing SOTA upgrades.

    Scans a directory for MCP repositories and evaluates each against SOTA criteria:
    - FastMCP version (< 2.12 = runt)
    - Tool count (> 15 without portmanteau = runt)
    - CI workflow count (> 3 = bloated)
    - Missing CI = runt

    Returns categorized list of repos with specific upgrade recommendations.""",
    category=ToolCategory.DISCOVERY,
    tags=["runt", "analyzer", "sota", "upgrade"],
    estimated_runtime="2-10s"
)
async def analyze_runts(
    scan_path: str = "D:/Dev/repos",
    max_depth: int = 1,
    include_sota: bool = True
) -> Dict[str, Any]:
    """
    Analyze MCP repositories to identify runts needing upgrades.

    Args:
        scan_path: Directory containing MCP repositories (default: D:/Dev/repos)
        max_depth: How deep to scan for repos (default: 1 = direct children only)
        include_sota: Whether to include SOTA repos in results (default: True)

    Returns:
        Dictionary with runts, sota repos, and summary statistics
    """
    runts: List[Dict[str, Any]] = []
    sota_repos: List[Dict[str, Any]] = []

    path = Path(scan_path).expanduser().resolve()
    if not path.exists():
        return {
            "success": False,
            "error": f"Path does not exist: {scan_path}",
            "timestamp": time.time()
        }

    for item in path.iterdir():
        if not item.is_dir() or item.name.startswith('.'):
            continue

        repo_info = _analyze_repo(item)
        if repo_info:
            if repo_info.get("is_runt"):
                runts.append(repo_info)
            elif include_sota:
                sota_repos.append(repo_info)

    # Sort runts by severity (most issues first)
    runts.sort(key=lambda x: len(x.get("runt_reasons", [])), reverse=True)
    sota_repos.sort(key=lambda x: x.get("name", ""))

    return {
        "success": True,
        "summary": {
            "total_mcp_repos": len(runts) + len(sota_repos),
            "runts": len(runts),
            "sota": len(sota_repos),
            "runt_threshold": f"FastMCP < {FASTMCP_RUNT_THRESHOLD}",
            "portmanteau_threshold": f"> {TOOL_PORTMANTEAU_THRESHOLD} tools",
            "sota_version": FASTMCP_LATEST
        },
        "runts": runts,
        "sota_repos": sota_repos if include_sota else [],
        "scan_path": scan_path,
        "timestamp": time.time()
    }


@tool(
    name="get_repo_status",
    description="""Get detailed SOTA status for a specific MCP repository.

    Analyzes a single repo and returns comprehensive status including:
    - FastMCP version and upgrade path
    - Tool count and portmanteau status
    - CI/CD quality assessment
    - Specific upgrade recommendations""",
    category=ToolCategory.DISCOVERY,
    tags=["repo", "status", "sota"],
    estimated_runtime="1-2s"
)
async def get_repo_status(repo_path: str) -> Dict[str, Any]:
    """
    Get detailed SOTA status for a specific repository.

    Args:
        repo_path: Path to the repository

    Returns:
        Detailed repository status and recommendations
    """
    path = Path(repo_path).expanduser().resolve()
    if not path.exists():
        return {
            "success": False,
            "error": f"Repository not found: {repo_path}",
            "timestamp": time.time()
        }

    repo_info = _analyze_repo(path)
    if not repo_info:
        return {
            "success": False,
            "error": f"Not an MCP repository: {repo_path}",
            "timestamp": time.time()
        }

    # Add more detailed analysis
    repo_info["success"] = True
    repo_info["sota_score"] = _calculate_sota_score(repo_info)
    repo_info["upgrade_priority"] = _determine_priority(repo_info)
    repo_info["timestamp"] = time.time()

    return repo_info


def _analyze_repo(repo_path: Path) -> Optional[Dict[str, Any]]:
    """Analyze a repository for MCP status."""
    info = {
        "name": repo_path.name,
        "path": str(repo_path),
        "fastmcp_version": None,
        "tool_count": 0,
        "has_portmanteau": False,
        "has_ci": False,
        "ci_workflows": 0,
        "is_runt": False,
        "runt_reasons": [],
        "recommendations": [],
        "status_emoji": "✅"
    }

    # Check for requirements.txt or pyproject.toml
    req_file = repo_path / "requirements.txt"
    pyproject_file = repo_path / "pyproject.toml"

    fastmcp_version = None

    # Extract FastMCP version
    for config_file in [req_file, pyproject_file]:
        if config_file.exists():
            try:
                content = config_file.read_text(encoding='utf-8')
                match = re.search(r'fastmcp.*?(\d+\.\d+\.?\d*)', content, re.IGNORECASE)
                if match:
                    fastmcp_version = match.group(1)
                    break
            except Exception:
                pass

    if not fastmcp_version:
        return None  # Not an MCP repo

    info["fastmcp_version"] = fastmcp_version

    # Check for portmanteau tools
    portmanteau_paths = [
        repo_path / "src" / f"{repo_path.name.replace('-', '_')}" / "tools" / "portmanteau",
        repo_path / "src" / f"{repo_path.name.replace('-', '_')}" / "portmanteau",
        repo_path / f"{repo_path.name.replace('-', '_')}" / "portmanteau",
        repo_path / "portmanteau",
    ]

    for p in portmanteau_paths:
        if p.exists() and any(p.glob("*.py")):
            info["has_portmanteau"] = True
            break

    # Count tools
    tool_patterns = [r"@app\.tool\(\)", r"@mcp\.tool\(\)", r"@tool\("]
    tool_count = 0
    src_dirs = [repo_path / "src", repo_path]

    for src_dir in src_dirs:
        if src_dir.exists():
            for py_file in src_dir.rglob("*.py"):
                if "test" in str(py_file).lower() or "__pycache__" in str(py_file):
                    continue
                try:
                    content = py_file.read_text(encoding='utf-8')
                    for pattern in tool_patterns:
                        tool_count += len(re.findall(pattern, content))
                except Exception:
                    pass

    info["tool_count"] = tool_count

    # Check CI
    ci_dir = repo_path / ".github" / "workflows"
    if ci_dir.exists():
        info["has_ci"] = True
        info["ci_workflows"] = len(list(ci_dir.glob("*.yml")))

    # Determine runt status
    _evaluate_runt_status(info, fastmcp_version)

    return info


def _evaluate_runt_status(info: Dict[str, Any], fastmcp_version: str) -> None:
    """Evaluate if repo is a runt and why."""
    # Check FastMCP version
    try:
        version_parts = [int(x) for x in fastmcp_version.split('.')[:2]]
        threshold_parts = [int(x) for x in FASTMCP_RUNT_THRESHOLD.split('.')[:2]]

        if version_parts < threshold_parts:
            info["is_runt"] = True
            info["runt_reasons"].append(f"FastMCP {fastmcp_version} < {FASTMCP_RUNT_THRESHOLD}")
            info["recommendations"].append(f"Upgrade to FastMCP {FASTMCP_LATEST}")
    except Exception:
        pass

    # Check tool count vs portmanteau
    if info["tool_count"] > TOOL_PORTMANTEAU_THRESHOLD and not info["has_portmanteau"]:
        info["is_runt"] = True
        info["runt_reasons"].append(
            f"{info['tool_count']} tools without portmanteau (threshold: {TOOL_PORTMANTEAU_THRESHOLD})"
        )
        info["recommendations"].append("Refactor to portmanteau tools")

    # Check CI
    if not info["has_ci"]:
        info["is_runt"] = True
        info["runt_reasons"].append("No CI/CD workflows")
        info["recommendations"].append("Add CI workflow with ruff + pytest")
    elif info["ci_workflows"] > 3:
        info["runt_reasons"].append(f"{info['ci_workflows']} CI workflows (recommend: 1)")
        info["recommendations"].append("Consolidate to single CI workflow")

    # Set status emoji
    if info["is_runt"]:
        info["status_emoji"] = "🐣" if len(info["runt_reasons"]) == 1 else "🐛"
    else:
        info["status_emoji"] = "✅"


def _calculate_sota_score(info: Dict[str, Any]) -> int:
    """Calculate SOTA compliance score (0-100)."""
    score = 100

    # Deduct for old FastMCP
    if info.get("fastmcp_version"):
        try:
            version = [int(x) for x in info["fastmcp_version"].split('.')[:2]]
            latest = [int(x) for x in FASTMCP_LATEST.split('.')[:2]]
            if version < latest:
                score -= 20
        except Exception:
            pass

    # Deduct for missing portmanteau when needed
    if info.get("tool_count", 0) > TOOL_PORTMANTEAU_THRESHOLD and not info.get("has_portmanteau"):
        score -= 25

    # Deduct for no CI
    if not info.get("has_ci"):
        score -= 30

    # Deduct for too many CI workflows
    if info.get("ci_workflows", 0) > 3:
        score -= 10

    return max(0, score)


def _determine_priority(info: Dict[str, Any]) -> str:
    """Determine upgrade priority based on runt reasons."""
    reasons = len(info.get("runt_reasons", []))
    if reasons == 0:
        return "none"
    elif reasons == 1:
        return "low"
    elif reasons == 2:
        return "medium"
    else:
        return "high"

