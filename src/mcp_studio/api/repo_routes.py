"""
Repo Scanner API Routes for MCP Studio Dashboard.

Provides REST endpoints for the repo scanner feature.
"""
from typing import Optional

from fastapi import APIRouter, Query

from ..tools.runt_analyzer import analyze_runts, get_repo_status
from ..app.core.config import settings

router = APIRouter(prefix="/repos", tags=["repos"])


@router.get("/")
async def get_repos(
    scan_path: str = Query(default=None, description="Directory to scan"),
    include_sota: bool = Query(default=True, description="Include SOTA repos in response")
):
    """
    Get all MCP repositories with repo analysis.

    Returns categorized list of repos:
    - repos: Repos needing upgrades
    - sota_repos: Repos meeting SOTA standards
    """
    # Use configured repos path if none provided
    if scan_path is None:
        scan_path = settings.REPOS_PATH

    result = await analyze_runts(scan_path=scan_path, include_sota=include_sota)
    return result


@router.get("/summary")
async def get_repos_summary(
    scan_path: str = Query(default=None, description="Directory to scan")
):
    """
    Get summary statistics for repo analysis.

    Returns quick stats without full repo details.
    """
    # Use configured repos path if none provided
    if scan_path is None:
        scan_path = settings.REPOS_PATH

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


@router.get("/test")
async def test_endpoint():
    """Simple test endpoint to verify routing works."""
    return {"message": "Repo scanner routes are working!", "timestamp": "2025-12-11"}

@router.get("/thresholds")
async def get_thresholds():
    """
    Get current SOTA thresholds and criteria for repo scanning.
    """
    from ..tools.runt_analyzer import (
        DXT_FILES,
        FASTMCP_LATEST,
        FASTMCP_RUNT_THRESHOLD,
        REQUIRED_TOOLS,
        RUFF_CONFIG_FILES,
        TEST_DIRS,
        TOOL_PORTMANTEAU_THRESHOLD,
    )

    return {
        "fastmcp_latest": FASTMCP_LATEST,
        "fastmcp_runt_threshold": FASTMCP_RUNT_THRESHOLD,
        "portmanteau_threshold": TOOL_PORTMANTEAU_THRESHOLD,
        "required_tools": REQUIRED_TOOLS,
        "dxt_files": DXT_FILES,
        "ruff_config_files": RUFF_CONFIG_FILES,
        "test_dirs": TEST_DIRS,
        "criteria": {
            "critical_runt": [
                f"FastMCP < {FASTMCP_RUNT_THRESHOLD}",
                f"> {TOOL_PORTMANTEAU_THRESHOLD} tools without portmanteau",
                "No CI/CD workflows",
                "No help tool",
                "No status tool",
                "No ruff linting",
                "No test directory",
                "No proper logging (structlog/logging)",
                "> 5 print() calls in non-test code",
                "> 3 bare except clauses",
            ],
            "warning": [
                "> 3 CI workflows (bloated)",
                "No DXT packaging (manifest.json)",
                "Missing proper multiline docstrings",
                "No unit tests (tests/unit/)",
                "No integration tests (tests/integration/)",
                "No pytest configuration",
                "No coverage configuration",
                "< 5 test files",
                "1-5 print() calls in non-test code",
            ],
            "needs_polish": [
                "Non-informative error messages (any count)",
            ],
            "lazy_error_examples": [
                '"error"',
                '"an error occurred"',
                '"something went wrong"',
                '"failed"',
                '"unknown error"',
                '"oops"',
                'raise Exception("short")',
            ]
        },
        "scoring": {
            "fastmcp_old": -20,
            "no_portmanteau": -25,
            "no_ci": -20,
            "no_help": -10,
            "no_status": -10,
            "no_dxt": -10,
            "no_docstrings": -10,
            "no_ruff": -10,
            "no_tests": -15,
            "no_unit_tests": -5,
            "no_integration_tests": -5,
            "no_pytest_config": -5,
            "no_coverage_config": -5,
            "too_many_ci": -5,
            "no_logging": -10,
            "print_statements_few": -5,
            "print_statements_many": -10,
            "bare_excepts": -10,
            "lazy_errors_few": -5,
            "lazy_errors_many": -10,
        },
        "status_emojis": {
            "💀": "Critical (5+ issues)",
            "🐛": "Bug (3-4 issues)",
            "🐣": "Minor (1-2 issues)",
            "⚠️": "Warning (non-critical issues)",
            "✅": "SOTA compliant"
        }
    }

