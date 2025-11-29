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

# Required SOTA features
REQUIRED_TOOLS = ["help", "status"]  # Every MCP server should have these
DXT_FILES = ["manifest.json", "dxt.json"]  # Desktop extension packaging

# Quality tooling
RUFF_CONFIG_FILES = ["ruff.toml", ".ruff.toml"]  # Or [tool.ruff] in pyproject.toml
TEST_DIRS = ["tests", "test"]  # Standard test directories
PYTEST_MARKERS = ["pytest", "test_", "_test.py"]  # Evidence of pytest usage

# Logging patterns (good)
LOGGING_PATTERNS = [
    r'import\s+logging',
    r'import\s+structlog',
    r'from\s+logging\s+import',
    r'from\s+structlog\s+import',
    r'logger\s*=\s*logging\.getLogger',
    r'logger\s*=\s*structlog\.get_logger',
]

# Bad patterns (print/console in non-test code)
BAD_STDOUT_PATTERNS = [
    r'^\s*print\s*\(',  # print() calls
    r'console\.log\s*\(',  # JS-style logging
    r'sys\.stdout\.write\s*\(',  # Direct stdout writes
]

# Error handling patterns (bad)
BAD_ERROR_PATTERNS = [
    r'except\s*:',  # Bare except (catches everything including KeyboardInterrupt)
    r'except\s+Exception\s*:',  # Broad exception without handling
]

# Good error handling patterns
GOOD_ERROR_PATTERNS = [
    r'except\s+\w+Error',  # Specific exception types
    r'logger\.\w+\(.*error',  # Logging errors
    r'raise\s+\w+Error',  # Re-raising specific errors
]

# Non-informative error messages (lazy/useless)
LAZY_ERROR_MESSAGES = [
    r'["\']error["\']',  # Just "error"
    r'["\']an?\s+error\s+(occurred|happened)["\']',  # "an error occurred"
    r'["\']something\s+went\s+wrong["\']',  # "something went wrong"
    r'["\']failed["\']',  # Just "failed"
    r'["\']unknown\s+error["\']',  # "unknown error"
    r'["\']error:\s*["\']',  # "error: " with nothing after
    r'["\']exception["\']',  # Just "exception"
    r'["\']oops["\']',  # "oops"
    r'["\']uh\s*oh["\']',  # "uh oh"
    r'["\']something\s+broke["\']',  # "something broke"
    r'["\']it\s+failed["\']',  # "it failed"
    r'["\']error\s+in\s+\w+["\']',  # "error in X" without details
    r'raise\s+Exception\s*\(\s*["\'][^"\']{0,15}["\']\s*\)',  # raise Exception("short msg")
]


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
        "has_dxt": False,
        "has_help_tool": False,
        "has_status_tool": False,
        "has_proper_docstrings": False,
        "has_ruff": False,
        "has_tests": False,
        "has_unit_tests": False,
        "has_integration_tests": False,
        "has_pytest_config": False,
        "has_coverage_config": False,
        "test_file_count": 0,
        "has_proper_logging": False,
        "has_good_error_handling": True,  # Assume good until proven bad
        "print_statement_count": 0,
        "bare_except_count": 0,
        "lazy_error_msg_count": 0,
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

    # Check for DXT packaging
    for dxt_file in DXT_FILES:
        if (repo_path / dxt_file).exists():
            info["has_dxt"] = True
            break

    # Count tools and check for help/status + docstrings
    tool_patterns = [r"@app\.tool\(\)", r"@mcp\.tool\(\)", r"@tool\("]
    tool_count = 0
    proper_docstrings = 0
    total_tools_checked = 0
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
                    
                    # Check for help tool
                    if re.search(r'(def\s+help|def\s+get_help|"help"|\'help\')\s*\(', content, re.IGNORECASE):
                        info["has_help_tool"] = True
                    
                    # Check for status tool
                    if re.search(r'(def\s+status|def\s+get_status|"status"|\'status\')\s*\(', content, re.IGNORECASE):
                        info["has_status_tool"] = True
                    
                    # Check for proper multiline docstrings (triple quotes with newlines)
                    # Pattern: function def followed by triple-quoted docstring with Args/Returns
                    docstring_matches = re.findall(
                        r'@(?:app|mcp)\.tool.*?\n\s*(?:async\s+)?def\s+\w+[^:]+:\s*\n\s*"""[\s\S]*?(?:Args:|Returns:|Examples:)[\s\S]*?"""',
                        content
                    )
                    if docstring_matches:
                        proper_docstrings += len(docstring_matches)
                        total_tools_checked += len(docstring_matches)
                except Exception:
                    pass

    # Check for proper logging, print statements, and error handling
    print_count = 0
    bare_except_count = 0
    lazy_error_count = 0
    has_logging = False
    has_good_errors = True
    
    for src_dir in src_dirs:
        if src_dir.exists():
            for py_file in src_dir.rglob("*.py"):
                # Skip test files for print/logging checks
                is_test_file = "test" in str(py_file).lower()
                if "__pycache__" in str(py_file):
                    continue
                    
                try:
                    content = py_file.read_text(encoding='utf-8')
                    content_lower = content.lower()
                    
                    # Check for logging setup (only need to find it once)
                    if not has_logging:
                        for pattern in LOGGING_PATTERNS:
                            if re.search(pattern, content):
                                has_logging = True
                                break
                    
                    # Check for print statements in non-test files
                    if not is_test_file:
                        for pattern in BAD_STDOUT_PATTERNS:
                            matches = re.findall(pattern, content, re.MULTILINE)
                            print_count += len(matches)
                    
                    # Check for bare except clauses
                    for pattern in BAD_ERROR_PATTERNS:
                        matches = re.findall(pattern, content)
                        bare_except_count += len(matches)
                    
                    # Check for lazy/non-informative error messages
                    if not is_test_file:
                        for pattern in LAZY_ERROR_MESSAGES:
                            matches = re.findall(pattern, content_lower, re.IGNORECASE)
                            lazy_error_count += len(matches)
                        
                except Exception:
                    pass
    
    info["has_proper_logging"] = has_logging
    info["print_statement_count"] = print_count
    info["bare_except_count"] = bare_except_count
    info["lazy_error_msg_count"] = lazy_error_count
    info["has_good_error_handling"] = bare_except_count < 3 and lazy_error_count < 5

    info["tool_count"] = tool_count
    # Consider proper docstrings if >50% of tools have them
    info["has_proper_docstrings"] = (proper_docstrings > 0 and 
                                      (total_tools_checked == 0 or proper_docstrings / max(tool_count, 1) > 0.5))

    # Check CI
    ci_dir = repo_path / ".github" / "workflows"
    if ci_dir.exists():
        info["has_ci"] = True
        info["ci_workflows"] = len(list(ci_dir.glob("*.yml")))
        
        # Check for ruff in CI
        for workflow in ci_dir.glob("*.yml"):
            try:
                ci_content = workflow.read_text(encoding='utf-8').lower()
                if 'ruff' in ci_content:
                    info["has_ruff"] = True
                    break
            except Exception:
                pass

    # Check for ruff config files
    if not info["has_ruff"]:
        for ruff_file in RUFF_CONFIG_FILES:
            if (repo_path / ruff_file).exists():
                info["has_ruff"] = True
                break
        
        # Check pyproject.toml for [tool.ruff]
        if not info["has_ruff"] and pyproject_file.exists():
            try:
                pyproject_content = pyproject_file.read_text(encoding='utf-8')
                if '[tool.ruff]' in pyproject_content:
                    info["has_ruff"] = True
            except Exception:
                pass

    # Check test harness
    test_file_count = 0
    for test_dir_name in TEST_DIRS:
        test_dir = repo_path / test_dir_name
        if test_dir.exists():
            info["has_tests"] = True
            
            # Check for unit tests
            unit_dir = test_dir / "unit"
            if unit_dir.exists() and any(unit_dir.glob("test_*.py")):
                info["has_unit_tests"] = True
            
            # Check for integration tests
            integration_dir = test_dir / "integration"
            if integration_dir.exists() and any(integration_dir.glob("test_*.py")):
                info["has_integration_tests"] = True
            
            # Count test files
            test_file_count += len(list(test_dir.rglob("test_*.py")))
            test_file_count += len(list(test_dir.rglob("*_test.py")))
    
    info["test_file_count"] = test_file_count

    # Check for pytest configuration
    pytest_ini = repo_path / "pytest.ini"
    pyproject_pytest = False
    if pyproject_file.exists():
        try:
            pyproject_content = pyproject_file.read_text(encoding='utf-8')
            if '[tool.pytest' in pyproject_content:
                pyproject_pytest = True
        except Exception:
            pass
    
    if pytest_ini.exists() or pyproject_pytest:
        info["has_pytest_config"] = True

    # Check for coverage configuration
    coveragerc = repo_path / ".coveragerc"
    pyproject_coverage = False
    if pyproject_file.exists():
        try:
            pyproject_content = pyproject_file.read_text(encoding='utf-8')
            if '[tool.coverage' in pyproject_content:
                pyproject_coverage = True
        except Exception:
            pass
    
    if coveragerc.exists() or pyproject_coverage:
        info["has_coverage_config"] = True

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

    # Check DXT packaging
    if not info["has_dxt"]:
        info["runt_reasons"].append("No DXT packaging (manifest.json)")
        info["recommendations"].append("Add manifest.json for desktop extension support")

    # Check help tool
    if not info["has_help_tool"]:
        info["is_runt"] = True
        info["runt_reasons"].append("No help tool")
        info["recommendations"].append("Add help() tool for discoverability")

    # Check status tool
    if not info["has_status_tool"]:
        info["is_runt"] = True
        info["runt_reasons"].append("No status tool")
        info["recommendations"].append("Add status() tool for diagnostics")

    # Check proper docstrings
    if not info["has_proper_docstrings"] and info["tool_count"] > 0:
        info["runt_reasons"].append("Missing proper multiline docstrings (Args/Returns)")
        info["recommendations"].append("Add comprehensive docstrings with Args, Returns, Examples")

    # Check ruff linting
    if not info["has_ruff"]:
        info["is_runt"] = True
        info["runt_reasons"].append("No ruff linting configured")
        info["recommendations"].append("Add ruff to pyproject.toml and CI workflow")

    # Check test harness
    if not info["has_tests"]:
        info["is_runt"] = True
        info["runt_reasons"].append("No test directory (tests/)")
        info["recommendations"].append("Add tests/ directory with unit tests")
    else:
        if not info["has_unit_tests"]:
            info["runt_reasons"].append("No unit tests (tests/unit/)")
            info["recommendations"].append("Add tests/unit/ with test_*.py files")
        
        if not info["has_integration_tests"]:
            info["runt_reasons"].append("No integration tests (tests/integration/)")
            info["recommendations"].append("Add tests/integration/ for API/E2E tests")
        
        if info["test_file_count"] < 3:
            info["runt_reasons"].append(f"Only {info['test_file_count']} test files (recommend: 5+)")
            info["recommendations"].append("Add more test coverage")

    # Check pytest config
    if not info["has_pytest_config"]:
        info["runt_reasons"].append("No pytest configuration")
        info["recommendations"].append("Add [tool.pytest.ini_options] to pyproject.toml")

    # Check coverage config
    if not info["has_coverage_config"]:
        info["runt_reasons"].append("No coverage configuration")
        info["recommendations"].append("Add [tool.coverage] to pyproject.toml")

    # Check logging
    if not info["has_proper_logging"]:
        info["is_runt"] = True
        info["runt_reasons"].append("No proper logging (structlog/logging)")
        info["recommendations"].append("Add structlog or logging module for observability")

    # Check print statements
    if info["print_statement_count"] > 0:
        info["runt_reasons"].append(f"{info['print_statement_count']} print() calls in non-test code")
        info["recommendations"].append("Replace print() with logger calls")
        if info["print_statement_count"] > 5:
            info["is_runt"] = True  # Too many prints = runt

    # Check error handling
    if info["bare_except_count"] >= 3:
        info["is_runt"] = True
        info["runt_reasons"].append(f"{info['bare_except_count']} bare except clauses")
        info["recommendations"].append("Use specific exception types (ValueError, TypeError, etc.)")

    # Check lazy error messages
    if info["lazy_error_msg_count"] > 0:
        info["runt_reasons"].append(f"{info['lazy_error_msg_count']} non-informative error messages")
        info["recommendations"].append("Use descriptive error messages with context (what failed, why, how to fix)")
        if info["lazy_error_msg_count"] >= 5:
            info["is_runt"] = True  # Too many lazy messages = runt

    # Set status emoji based on severity
    runt_count = len(info["runt_reasons"])
    if info["is_runt"]:
        if runt_count >= 5:
            info["status_emoji"] = "💀"  # Critical
        elif runt_count >= 3:
            info["status_emoji"] = "🐛"  # Bug
        else:
            info["status_emoji"] = "🐣"  # Chick (minor)
    else:
        if runt_count > 0:
            info["status_emoji"] = "⚠️"  # Warning (has issues but not runt)
        else:
            info["status_emoji"] = "✅"  # Perfect


def _calculate_sota_score(info: Dict[str, Any]) -> int:
    """Calculate SOTA compliance score (0-100)."""
    score = 100

    # Deduct for old FastMCP (-20)
    if info.get("fastmcp_version"):
        try:
            version = [int(x) for x in info["fastmcp_version"].split('.')[:2]]
            latest = [int(x) for x in FASTMCP_LATEST.split('.')[:2]]
            if version < latest:
                score -= 20
        except Exception:
            pass

    # Deduct for missing portmanteau when needed (-25)
    if info.get("tool_count", 0) > TOOL_PORTMANTEAU_THRESHOLD and not info.get("has_portmanteau"):
        score -= 25

    # Deduct for no CI (-20)
    if not info.get("has_ci"):
        score -= 20

    # Deduct for too many CI workflows (-5)
    if info.get("ci_workflows", 0) > 3:
        score -= 5

    # Deduct for no DXT packaging (-10)
    if not info.get("has_dxt"):
        score -= 10

    # Deduct for no help tool (-10)
    if not info.get("has_help_tool"):
        score -= 10

    # Deduct for no status tool (-10)
    if not info.get("has_status_tool"):
        score -= 10

    # Deduct for poor docstrings (-10)
    if not info.get("has_proper_docstrings") and info.get("tool_count", 0) > 0:
        score -= 10

    # Deduct for no ruff (-10)
    if not info.get("has_ruff"):
        score -= 10

    # Deduct for no tests (-15)
    if not info.get("has_tests"):
        score -= 15
    else:
        # Deduct for missing test types (-5 each)
        if not info.get("has_unit_tests"):
            score -= 5
        if not info.get("has_integration_tests"):
            score -= 5

    # Deduct for no pytest config (-5)
    if not info.get("has_pytest_config"):
        score -= 5

    # Deduct for no coverage config (-5)
    if not info.get("has_coverage_config"):
        score -= 5

    # Deduct for no proper logging (-10)
    if not info.get("has_proper_logging"):
        score -= 10

    # Deduct for print statements (-5, or -10 if many)
    print_count = info.get("print_statement_count", 0)
    if print_count > 5:
        score -= 10
    elif print_count > 0:
        score -= 5

    # Deduct for bare except clauses (-10)
    if info.get("bare_except_count", 0) >= 3:
        score -= 10

    # Deduct for lazy error messages (-5 or -10)
    lazy_count = info.get("lazy_error_msg_count", 0)
    if lazy_count >= 5:
        score -= 10
    elif lazy_count > 0:
        score -= 5

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

