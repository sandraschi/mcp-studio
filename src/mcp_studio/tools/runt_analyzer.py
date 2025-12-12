"""
Runt Analyzer Tool for MCP Studio.

Scans MCP repositories and identifies "runts" - repos that need SOTA upgrades.
"""
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

import structlog

from .decorators import ToolCategory, tool
from .runt_analyzer_rules import (
    evaluate_rules,
    calculate_sota_score,
    SOTA_RULES,
    RuleCategory,
    RuleSeverity,
    get_rules_by_category,
    get_rule_by_id,
)
from .repo_detail_collector import collect_repo_details
from .scan_cache import (
    get_cached_scan,
    cache_scan_result,
    get_cached_repo_status,
    cache_repo_status,
    clear_cache,
    get_cache_stats,
)
from .scan_formatter import format_scan_result_markdown, format_repo_status_markdown

logger = structlog.get_logger(__name__)

# SOTA thresholds (kept for backward compatibility)
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

# ============================================================================
# MCP ZOO CLASSIFICATION 🦁🐘🦒
# Not a flea circus - these are proper beasts!
# ============================================================================

# Keywords indicating heavy/jumbo MCPs (database, virtualization, etc.)
JUMBO_INDICATORS = [
    "database", "postgres", "mysql", "sqlite", "mongo", "redis",  # Databases
    "docker", "kubernetes", "k8s", "container", "virtualization",  # Virtualization
    "virtualbox", "vmware", "qemu", "hyperv",  # VMs
    "davinci", "resolve", "premiere", "video", "render",  # Heavy video
    "blender", "3d", "modeling",  # 3D software
    "ai-", "llm-", "ml-", "machine-learning",  # AI/ML heavy
    "obs", "stream", "broadcast",  # Streaming
]

# Keywords indicating mini/chipmunk MCPs (simple, single-purpose)
CHIPMUNK_INDICATORS = [
    "txt", "text", "generator", "simple", "mini", "tiny", "lite",
    "basic", "hello", "echo", "demo", "example", "starter", "template",
    "clipboard", "timer", "counter", "converter", "calculator",
]

# Zoo animal classification based on tool count and complexity
ZOO_ANIMALS = {
    # Jumbos - Heavy/Complex MCPs (🐘 Elephant, 🦛 Hippo, 🦏 Rhino)
    "jumbo": {
        "emoji": "🐘",
        "label": "Jumbo",
        "description": "Heavy MCP - DB, virtualization, video processing",
        "min_tools": 20,
    },
    # Large - Substantial MCPs (🦁 Lion, 🐻 Bear, 🦒 Giraffe)
    "large": {
        "emoji": "🦁",
        "label": "Large",
        "description": "Substantial MCP with many features",
        "min_tools": 10,
    },
    # Medium - Standard MCPs (🦊 Fox, 🐺 Wolf, 🦌 Deer)
    "medium": {
        "emoji": "🦊",
        "label": "Medium",
        "description": "Standard MCP with moderate complexity",
        "min_tools": 5,
    },
    # Small - Lightweight MCPs (🐰 Rabbit, 🦝 Raccoon, 🦡 Badger)
    "small": {
        "emoji": "🐰",
        "label": "Small",
        "description": "Lightweight MCP with focused purpose",
        "min_tools": 2,
    },
    # Chipmunk - Mini MCPs (🐿️ Chipmunk, 🐹 Hamster, 🐁 Mouse)
    "chipmunk": {
        "emoji": "🐿️",
        "label": "Chipmunk",
        "description": "Mini MCP - simple, single-purpose tool",
        "min_tools": 0,
    },
}


@tool(
    name="analyze_runts",
    description="""Analyze MCP repositories to identify "runts" needing SOTA upgrades.

    Scans a directory for MCP repositories and evaluates each against SOTA criteria:
    - FastMCP version (< 2.12 = runt)
    - Tool count (> 15 without portmanteau = runt)
    - CI workflow count (> 3 = bloated)
    - Missing CI = runt

    Returns categorized list of repos with specific upgrade recommendations.
    Results are cached to avoid re-scanning on every request.""",
    category=ToolCategory.DISCOVERY,
    tags=["runt", "analyzer", "sota", "upgrade"],
    estimated_runtime="2-10s"
)
async def analyze_runts(
    scan_path: Optional[str] = None,
    max_depth: int = 1,
    include_sota: bool = True,
    format: str = "json",
    use_cache: bool = True,
    cache_ttl: int = 3600
) -> Union[Dict[str, Any], str]:
    """
    Analyze MCP repositories to identify runts needing upgrades.

    Args:
        scan_path: Directory containing MCP repositories (default: from REPOS_DIR env var or platform default)
        max_depth: How deep to scan for repos (default: 1 = direct children only)
        include_sota: Whether to include SOTA repos in results (default: True)
        format: Output format - "json" or "markdown" (default: "json")
        use_cache: Whether to use cached results (default: True)
        cache_ttl: Cache time-to-live in seconds (default: 3600 = 1 hour)

    Returns:
        Dictionary with runts, sota repos, and summary statistics, or markdown string if format="markdown"
    """
    # Use default scan_path if not provided
    if scan_path is None:
        from mcp_studio.app.core.config import DEFAULT_REPOS_PATH
        scan_path = DEFAULT_REPOS_PATH
    
    # Check cache first
    if use_cache:
        cached = get_cached_scan(scan_path, max_depth, cache_ttl)
        if cached:
            if format == "markdown":
                return format_scan_result_markdown(cached)
            return cached
    
    runts: List[Dict[str, Any]] = []
    sota_repos: List[Dict[str, Any]] = []

    path = Path(scan_path).expanduser().resolve()
    if not path.exists():
        error_result = {
            "success": False,
            "error": f"Path does not exist: {scan_path}",
            "timestamp": time.time()
        }
        if format == "markdown":
            return f"# Scan Failed\n\n**Error:** {error_result['error']}\n"
        return error_result

    import asyncio
    for item in path.iterdir():
        if not item.is_dir() or item.name.startswith('.'):
            continue

        # Small delay to reduce terminal spam and CPU usage
        await asyncio.sleep(0.1)  # 100ms delay between repos

        repo_info = _analyze_repo(item)
        if repo_info:
            if repo_info.get("is_runt"):
                runts.append(repo_info)
            elif include_sota:
                sota_repos.append(repo_info)

    # Sort runts by severity (most issues first)
    runts.sort(key=lambda x: len(x.get("runt_reasons", [])), reverse=True)
    sota_repos.sort(key=lambda x: x.get("name", ""))

    result = {
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
    
    # Cache the result
    if use_cache:
        cache_scan_result(scan_path, max_depth, result)
    
    # Return in requested format
    if format == "markdown":
        return format_scan_result_markdown(result)
    
    return result


@tool(
    name="get_repo_status",
    description="""Get detailed SOTA status for a specific MCP repository.

    Analyzes a single repo and returns comprehensive status including:
    - FastMCP version and upgrade path
    - Tool count and portmanteau status
    - CI/CD quality assessment
    - Specific upgrade recommendations
    - Detailed repository structure, dependencies, tools, and configuration
    - All information needed for AI to answer questions about the repo without re-analysis
    
    Results are cached to avoid re-scanning on every request.""",
    category=ToolCategory.DISCOVERY,
    tags=["repo", "status", "sota"],
    estimated_runtime="2-5s"
)
async def get_repo_status(
    repo_path: str,
    format: str = "json",
    use_cache: bool = True,
    cache_ttl: int = 3600
) -> Union[Dict[str, Any], str]:
    """
    Get detailed SOTA status for a specific repository.

    Args:
        repo_path: Path to the repository
        format: Output format - "json" or "markdown" (default: "json")
        use_cache: Whether to use cached results (default: True)
        cache_ttl: Cache time-to-live in seconds (default: 3600 = 1 hour)

    Returns:
        Detailed repository status and recommendations, or markdown string if format="markdown"
    """
    # Check cache first
    if use_cache:
        cached = get_cached_repo_status(repo_path, cache_ttl)
        if cached:
            if format == "markdown":
                return format_repo_status_markdown(cached)
            return cached
    
    path = Path(repo_path).expanduser().resolve()
    if not path.exists():
        error_result = {
            "success": False,
            "error": f"Repository not found: {repo_path}",
            "timestamp": time.time()
        }
        if format == "markdown":
            return f"# Repository Status Failed\n\n**Error:** {error_result['error']}\n"
        return error_result

    repo_info = _analyze_repo(path)
    if not repo_info:
        error_result = {
            "success": False,
            "error": f"Not an MCP repository: {repo_path}",
            "timestamp": time.time()
        }
        if format == "markdown":
            return f"# Repository Status Failed\n\n**Error:** {error_result['error']}\n"
        return error_result

    # Add more detailed analysis
    repo_info["success"] = True
    repo_info["sota_score"] = _calculate_sota_score(repo_info)
    repo_info["upgrade_priority"] = _determine_priority(repo_info)
    repo_info["timestamp"] = time.time()
    
    # Add comprehensive repository details for AI consumption
    try:
        repo_info["details"] = collect_repo_details(path)
    except Exception as e:
        logger.warning(f"Failed to collect detailed repo info: {e}")
        repo_info["details"] = None
    
    # Cache the result
    if use_cache:
        cache_repo_status(repo_path, repo_info)
    
    # Return in requested format
    if format == "markdown":
        return format_repo_status_markdown(repo_info)

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
        "status_emoji": "✅",
        "status_color": "green",
        "status_label": "SOTA",
        "zoo_class": "unknown",
        "zoo_animal": "🦔"  # Default: hedgehog (unknown size)
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

    # Evaluate using rule-based system
    _evaluate_runt_status(info, fastmcp_version)

    return info


def _evaluate_runt_status(info: Dict[str, Any], fastmcp_version: str) -> None:
    """Evaluate if repo is a runt using rule-based system."""
    # Ensure fastmcp_version is in info for rule evaluation
    if fastmcp_version:
        info["fastmcp_version"] = fastmcp_version
    
    # Evaluate all rules
    rule_result = evaluate_rules(info)
    
    # Update info with rule evaluation results
    info["is_runt"] = rule_result["is_runt"]
    info["runt_reasons"] = rule_result["runt_reasons"]
    info["recommendations"] = rule_result["recommendations"]
    
    # Set status emoji, color, and label based on severity
    violation_count = rule_result["violation_count"]
    critical_count = rule_result["critical_count"]
    
    if info["is_runt"]:
        # RED - Real runts
        info["status_color"] = "red"
        if critical_count >= 5:
            info["status_emoji"] = "💀"
            info["status_label"] = "Critical Runt"
        elif critical_count >= 3:
            info["status_emoji"] = "🐛"
            info["status_label"] = "Runt"
        else:
            info["status_emoji"] = "🐣"
            info["status_label"] = "Minor Runt"
    else:
        if violation_count > 0:
            # ORANGE - Improvable (has warnings but not runt)
            info["status_emoji"] = "⚠️"
            info["status_color"] = "orange"
            info["status_label"] = "Needs Improvement"
        else:
            # GREEN - Perfect
            info["status_emoji"] = "✅"
            info["status_color"] = "green"
            info["status_label"] = "SOTA"
    
    # Store rule evaluation details for debugging
    info["_rule_evaluation"] = {
        "violations": rule_result["violations"],
        "critical_violations": rule_result["critical_violations"],
        "score_deduction": rule_result["score_deduction"],
    }
    
    # Add zoo classification
    _classify_zoo_animal(info)


def _classify_zoo_animal(info: Dict[str, Any]) -> None:
    """Classify repo into MCP Zoo animal size category."""
    name_lower = info.get("name", "").lower()
    tool_count = info.get("tool_count", 0)

    # Check for jumbo indicators in name
    is_jumbo_type = any(ind in name_lower for ind in JUMBO_INDICATORS)

    # Check for chipmunk indicators in name
    is_chipmunk_type = any(ind in name_lower for ind in CHIPMUNK_INDICATORS)

    # Determine class based on indicators and tool count
    if is_jumbo_type or tool_count >= 20:
        info["zoo_class"] = "jumbo"
        info["zoo_animal"] = "🐘"
    elif is_chipmunk_type and tool_count <= 3:
        info["zoo_class"] = "chipmunk"
        info["zoo_animal"] = "🐿️"
    elif tool_count >= 10:
        info["zoo_class"] = "large"
        info["zoo_animal"] = "🦁"
    elif tool_count >= 5:
        info["zoo_class"] = "medium"
        info["zoo_animal"] = "🦊"
    elif tool_count >= 2:
        info["zoo_class"] = "small"
        info["zoo_animal"] = "🐰"
    else:
        info["zoo_class"] = "chipmunk"
        info["zoo_animal"] = "🐿️"


def _calculate_sota_score(info: Dict[str, Any]) -> int:
    """Calculate SOTA compliance score (0-100) using rule-based system."""
    return calculate_sota_score(info, base_score=100)


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

