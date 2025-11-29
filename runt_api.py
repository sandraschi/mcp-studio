"""
MCP Zoo Runt Analyzer v2.2.1
============================
Standalone dashboard for analyzing MCP server quality.

Dashboard: http://localhost:8888
API Docs: docs/MCP_ZOO_RUNT_ANALYZER.md

Features:
- Real-time scan progress with SSE streaming
- Zoo classification: Jumbo/Large/Medium/Small/Chipmunk
- Status: SOTA/Improvable/Runt/Critical
- Tool counting: Portmanteau tools, operations, individual tools
- Detail modal with README, tools, docstrings

Progress Notes (2025-11-29):
- Added progress reporting with live SSE updates
- Added log collection and display
- Added detail modal with full repo analysis
- Separated portmanteau vs individual tool counts
- Added operations count (Literal values in portmanteaus)
- Tuned runt/improvable/SOTA criteria for balance
- Added structure checks: src/, tests/, scripts/, tools/
- Added non-conforming registration detection
"""
import asyncio
import json
import logging
import re
import sys
import time
from collections import deque
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, StreamingResponse
import uvicorn

# ============================================================================
# LOGGING SETUP
# ============================================================================

class LogCollector(logging.Handler):
    """Collects logs in memory for API access."""
    def __init__(self, maxlen: int = 500):
        super().__init__()
        self.logs: deque = deque(maxlen=maxlen)
    
    def emit(self, record):
        entry = {
            "time": datetime.now().isoformat(),
            "level": record.levelname,
            "msg": self.format(record),
        }
        self.logs.append(entry)
    
    def get_logs(self, limit: int = 100) -> List[Dict]:
        return list(self.logs)[-limit:]
    
    def clear(self):
        self.logs.clear()

# Setup logging
log_collector = LogCollector(maxlen=1000)
log_collector.setFormatter(logging.Formatter('%(message)s'))

logger = logging.getLogger("runt_analyzer")
logger.setLevel(logging.INFO)
logger.addHandler(log_collector)

# Also log to console with colors
console = logging.StreamHandler(sys.stdout)
console.setFormatter(logging.Formatter('%(asctime)s | %(message)s', datefmt='%H:%M:%S'))
logger.addHandler(console)

# Progress state
scan_progress = {
    "status": "idle",
    "current_repo": None,
    "scanned": 0,
    "total": 0,
    "mcp_found": 0,
    "start_time": None,
    "elapsed": 0,
}

app = FastAPI(title="MCP Zoo Runt Analyzer 🦁🐘🦒", version="2.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ============================================================================
# CONSTANTS
# ============================================================================

FASTMCP_LATEST = "2.13.1"
FASTMCP_RUNT_THRESHOLD = "2.10.0"  # Below this = runt
FASTMCP_WARN_THRESHOLD = "2.12.0"  # Below this = improvable
TOOL_PORTMANTEAU_THRESHOLD = 15

JUMBO_INDICATORS = [
    "database", "postgres", "mysql", "sqlite", "mongo", "redis",
    "docker", "kubernetes", "k8s", "container", "virtualization",
    "virtualbox", "vmware", "qemu", "hyperv",
    "davinci", "resolve", "premiere", "video", "render",
    "blender", "3d", "modeling",
    "ai-", "llm-", "ml-", "machine-learning",
    "obs", "stream", "broadcast",
]

CHIPMUNK_INDICATORS = [
    "txt", "text", "generator", "simple", "mini", "tiny", "lite",
    "basic", "hello", "echo", "demo", "example", "starter", "template",
    "clipboard", "timer", "counter", "converter", "calculator",
]

ZOO_ANIMALS = {
    "jumbo": {"emoji": "🐘", "label": "Jumbo", "min_tools": 20},
    "large": {"emoji": "🦁", "label": "Large", "min_tools": 10},
    "medium": {"emoji": "🦊", "label": "Medium", "min_tools": 5},
    "small": {"emoji": "🐰", "label": "Small", "min_tools": 2},
    "chipmunk": {"emoji": "🐿️", "label": "Chipmunk", "min_tools": 0},
}

SKIP_DIRS = {
    "node_modules", "__pycache__", ".git", ".venv", "venv", "env",
    "dist", "build", ".tox", ".pytest_cache", ".mypy_cache",
    "eggs", "htmlcov", "site-packages", "_legacy", "deprecated",
}

# Patterns that indicate we're inside a venv (check full path)
VENV_PATTERNS = {".venv", "venv", "Lib", "site-packages"}

# ============================================================================
# ANALYZER
# ============================================================================

def fast_py_glob(directory: Path, max_depth: int = 3) -> List[Path]:
    """Fast python file glob with depth limit and skip dirs."""
    results = []
    def _walk(path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for item in path.iterdir():
                if item.is_dir():
                    # Skip known dirs and venv patterns
                    if item.name in SKIP_DIRS or item.name.startswith('.') or item.name.endswith('.egg-info'):
                        continue
                    # Skip if any venv pattern in full path
                    if any(vp in str(item) for vp in VENV_PATTERNS):
                        continue
                    _walk(item, depth + 1)
                elif item.suffix == '.py' and 'test' not in item.name.lower():
                    # Skip if inside venv
                    if any(vp in str(item) for vp in VENV_PATTERNS):
                        continue
                    results.append(item)
        except (PermissionError, OSError):
            pass
    _walk(directory, 0)
    return results


def analyze_repo(repo_path: Path) -> Optional[Dict[str, Any]]:
    """Analyze a single MCP repository."""
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
        "status_emoji": "✅",
        "status_color": "green",
        "status_label": "SOTA",
        "zoo_class": "unknown",
        "zoo_animal": "🦔",
    }

    # Check for requirements.txt or pyproject.toml
    req_file = repo_path / "requirements.txt"
    pyproject_file = repo_path / "pyproject.toml"

    fastmcp_version = None
    for config_file in [req_file, pyproject_file]:
        if config_file.exists():
            try:
                content = config_file.read_text(encoding='utf-8', errors='ignore')
                match = re.search(r'fastmcp.*?(\d+\.\d+\.?\d*)', content, re.IGNORECASE)
                if match:
                    fastmcp_version = match.group(1)
                    break
            except Exception:
                pass

    if not fastmcp_version:
        return None  # Not an MCP repo

    info["fastmcp_version"] = fastmcp_version

    # Check for portmanteau
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

    # Count tools - SMART APPROACH:
    # 1. Check tools/__init__.py for what's actually imported (most accurate)
    # 2. Fall back to scanning all files if no init found
    tool_pattern = re.compile(r'@(?:app|mcp|self\.mcp|server)\.tool(?:\s*\(|(?=\s*(?:\r?\n|def\s)))', re.MULTILINE)
    nonconforming_pattern = re.compile(r'def register_\w+_tool\s*\(|\.add_tool\s*\(|register_tool\s*\(')
    tool_count = 0
    
    pkg_name = repo_path.name.replace('-', '_')
    
    # Find the tools directory and its __init__.py
    tools_init_paths = [
        repo_path / "src" / pkg_name / "mcp" / "tools" / "__init__.py",  # advanced-memory style
        repo_path / "src" / pkg_name / "tools" / "__init__.py",
        repo_path / pkg_name / "tools" / "__init__.py",
        repo_path / "tools" / "__init__.py",
    ]
    
    imported_modules = set()
    tools_dir = None
    for init_path in tools_init_paths:
        if init_path.exists():
            tools_dir = init_path.parent
            try:
                init_content = init_path.read_text(encoding='utf-8', errors='ignore')
                # Extract imported module names from "from .module import ..." lines
                # Only count else block (portmanteau mode) if exists
                if 'else:' in init_content:
                    # Split at else: and only use the second part
                    else_block = init_content.split('else:')[-1]
                    imports = re.findall(r'from\s+\.(\w+)\s+import', else_block)
                else:
                    imports = re.findall(r'from\s+\.(\w+)\s+import', init_content)
                imported_modules.update(imports)
            except Exception:
                pass
            break
    
    # Search directories
    search_dirs = []
    if tools_dir and tools_dir.exists():
        search_dirs.append(tools_dir)
    else:
        src_dir = repo_path / "src"
        if src_dir.exists():
            search_dirs.append(src_dir)
        pkg_dir = repo_path / pkg_name
        if pkg_dir.exists() and pkg_dir.is_dir():
            search_dirs.append(pkg_dir)
        if not search_dirs:
            search_dirs.append(repo_path)
    
    has_nonconforming = False
    nonconforming_count = 0
    portmanteau_tools = 0
    portmanteau_ops = 0
    individual_tools = 0
    
    literal_pattern = re.compile(r'Literal\[([^\]]+)\]')
    simple_tool_names = {'help', 'status', 'info', 'health', 'version', 'list', 'search', 'log', 'debug'}
    
    for search_dir in search_dirs:
        py_files = fast_py_glob(search_dir, max_depth=4)
        for py_file in py_files:
            # If we have an __init__.py with imports, only count imported modules
            if imported_modules:
                if py_file.stem not in imported_modules:
                    continue
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                matches = tool_pattern.findall(content)
                file_tools = len(matches)
                
                path_str = str(py_file).lower()
                filename = py_file.stem.lower()
                is_portmanteau_file = (
                    "portmanteau" in path_str or 
                    path_str.endswith("_tool.py") or
                    path_str.endswith("_tools.py")
                )
                is_simple_file = any(s in filename for s in simple_tool_names)
                
                if is_portmanteau_file:
                    portmanteau_tools += file_tools
                    # Count operations (Literal values)
                    for lit_match in literal_pattern.findall(content):
                        # Count quoted strings in Literal
                        ops = len(re.findall(r'["\'][^"\']+["\']', lit_match))
                        if ops > 1:  # Only count if multiple operations
                            portmanteau_ops += ops
                elif is_simple_file:
                    individual_tools += file_tools
                else:
                    # Other tools - check if they look like simple utilities
                    individual_tools += file_tools
                
                tool_count += file_tools
                
                # Detect non-conforming registration patterns
                nc_matches = nonconforming_pattern.findall(content)
                if nc_matches:
                    has_nonconforming = True
                    nonconforming_count += len(nc_matches)
            except Exception:
                pass
    
    info["tool_count"] = tool_count
    info["portmanteau_tools"] = portmanteau_tools
    info["portmanteau_ops"] = portmanteau_ops
    info["individual_tools"] = individual_tools
    info["has_nonconforming_registration"] = has_nonconforming
    info["nonconforming_count"] = nonconforming_count

    # Check CI
    workflows_dir = repo_path / ".github" / "workflows"
    if workflows_dir.exists():
        info["has_ci"] = True
        info["ci_workflows"] = len(list(workflows_dir.glob("*.yml")))

    # Check project structure
    has_src = (repo_path / "src").exists()
    has_tests = (repo_path / "tests").exists()
    has_scripts = (repo_path / "scripts").exists()
    
    # Check for tools/ subdirectory (proper tool organization)
    pkg_name = repo_path.name.replace('-', '_')
    tools_paths = [
        repo_path / "src" / pkg_name / "tools",
        repo_path / pkg_name / "tools",
        repo_path / "tools",
    ]
    has_tools_dir = any(p.exists() and p.is_dir() for p in tools_paths)
    
    info["has_src"] = has_src
    info["has_tests"] = has_tests
    info["has_scripts"] = has_scripts
    info["has_tools_dir"] = has_tools_dir

    # Evaluate FastMCP version
    try:
        version_parts = [int(x) for x in fastmcp_version.split('.')[:2]]
        runt_parts = [int(x) for x in FASTMCP_RUNT_THRESHOLD.split('.')[:2]]
        warn_parts = [int(x) for x in FASTMCP_WARN_THRESHOLD.split('.')[:2]]
        
        if version_parts < runt_parts:
            # Ancient version (< 2.10) - definite runt
            info["is_runt"] = True
            info["runt_reasons"].append(f"FastMCP {fastmcp_version} is ancient")
            info["recommendations"].append(f"Upgrade to FastMCP {FASTMCP_LATEST}")
        elif version_parts < warn_parts:
            # Old but usable (2.10-2.11) - just a recommendation
            info["recommendations"].append(f"Upgrade FastMCP {fastmcp_version} → {FASTMCP_LATEST}")
    except Exception:
        pass

    # Check portmanteau usage - individual tools (help, status) are fine
    # Only warn if too many non-portmanteau tools that should be consolidated
    non_simple_individual = individual_tools  # These are fine - help, status, etc.
    if portmanteau_tools == 0 and tool_count > 20:
        # Many tools but no portmanteau pattern
        info["runt_reasons"].append(f"{tool_count} tools, no portmanteau pattern")
        info["recommendations"].append("Consider consolidating to portmanteau tools")

    # CI check - only runt for larger repos
    if not info["has_ci"]:
        if tool_count >= 10:
            info["is_runt"] = True
            info["runt_reasons"].append("No CI/CD workflows")
        else:
            info["runt_reasons"].append("No CI/CD (small repo)")
        info["recommendations"].append("Add CI workflow")

    # Structure checks - only runt if no src AND no pkg dir
    if not has_src and not (repo_path / pkg_name).exists():
        info["is_runt"] = True
        info["runt_reasons"].append("No src/ directory")
        info["recommendations"].append("Use proper src/ layout")
    elif not has_src:
        # Has pkg dir in root - just a warning
        info["runt_reasons"].append("No src/ (has pkg/ in root)")
        info["recommendations"].append("Consider src/ layout")
    
    # Missing tests - only warn for larger repos
    if not has_tests and tool_count >= 10:
        info["runt_reasons"].append("No tests/ directory")
        info["recommendations"].append("Add tests/ with pytest")
    elif not has_tests:
        info["recommendations"].append("Consider adding tests/")
    
    # Missing scripts - just a recommendation, doesn't affect status
    if not has_scripts:
        info["recommendations"].append("Consider adding scripts/")
    
    # Warn if no tools/ dir only for large repos
    if not has_tools_dir and tool_count >= 20:
        info["runt_reasons"].append(f"No tools/ dir ({tool_count} tools)")
        info["recommendations"].append("Split tools into src/<pkg>/tools/")
    elif not has_tools_dir and tool_count >= 10:
        info["recommendations"].append("Consider splitting tools into tools/ dir")
    
    # Non-conforming registration - only matters if significant
    if has_nonconforming:
        if tool_count == 0 and nonconforming_count > 10:
            # ALL tools are non-conforming - runt
            info["is_runt"] = True
            info["runt_reasons"].append(f"All tools non-FastMCP ({nonconforming_count}x)")
            info["recommendations"].append("Use @app.tool or @mcp.tool decorators")
        elif nonconforming_count > tool_count:
            # More non-conforming than proper - warn
            info["runt_reasons"].append(f"Mostly non-FastMCP ({nonconforming_count}x)")
            info["recommendations"].append("Use @app.tool or @mcp.tool decorators")
        else:
            # Just a few - recommendation only
            info["recommendations"].append(f"Fix {nonconforming_count} non-decorator registrations")

    # Set status
    runt_count = len(info["runt_reasons"])
    if info["is_runt"]:
        info["status_color"] = "red"
        if runt_count >= 5:
            info["status_emoji"] = "💀"
            info["status_label"] = "Critical Runt"
        elif runt_count >= 3:
            info["status_emoji"] = "🐛"
            info["status_label"] = "Runt"
        else:
            info["status_emoji"] = "🐣"
            info["status_label"] = "Minor Runt"
    elif runt_count > 0:
        info["status_emoji"] = "⚠️"
        info["status_color"] = "orange"
        info["status_label"] = "Needs Improvement"

    # Zoo classification
    name_lower = info["name"].lower()
    is_jumbo = any(ind in name_lower for ind in JUMBO_INDICATORS)
    is_chipmunk = any(ind in name_lower for ind in CHIPMUNK_INDICATORS)

    if is_jumbo or tool_count >= 20:
        info["zoo_class"] = "jumbo"
        info["zoo_animal"] = "🐘"
    elif is_chipmunk and tool_count <= 3:
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

    return info


# ============================================================================
# API ROUTES
# ============================================================================

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the runt analyzer dashboard with live progress."""
    return """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦁 MCP Zoo - Runt Analyzer</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <style>
        .card-red { background: linear-gradient(135deg, #fecaca 0%, #fee2e2 100%); border-color: #ef4444; }
        .card-orange { background: linear-gradient(135deg, #fed7aa 0%, #ffedd5 100%); border-color: #f97316; }
        .card-green { background: linear-gradient(135deg, #bbf7d0 0%, #dcfce7 100%); border-color: #22c55e; }
        .badge-red { background: #ef4444; }
        .badge-orange { background: #f97316; }
        .badge-green { background: #22c55e; }
        .log-entry { font-family: monospace; font-size: 12px; }
    </style>
</head>
<body class="bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 min-h-screen text-white">
    <div class="container mx-auto px-4 py-8">
        <header class="text-center mb-8">
            <h1 class="text-5xl font-bold mb-4">🦁 MCP Zoo 🐘🦒🐿️</h1>
            <p class="text-xl text-purple-200">Runt Analyzer Dashboard</p>
            <p class="text-sm text-purple-300 mt-2">Scanning: <code class="bg-purple-800 px-2 py-1 rounded">D:/Dev/repos</code></p>
        </header>

        <!-- Progress Panel -->
        <div id="progress-panel" class="bg-black/30 rounded-xl p-4 mb-6">
            <div class="flex items-center justify-between mb-2">
                <span class="text-lg font-semibold">📡 Scan Progress</span>
                <span id="status-badge" class="px-3 py-1 rounded-full bg-gray-600 text-sm">Idle</span>
            </div>
            <div class="w-full bg-gray-700 rounded-full h-3 mb-2">
                <div id="progress-bar" class="bg-purple-500 h-3 rounded-full transition-all" style="width: 0%"></div>
            </div>
            <div class="flex justify-between text-sm text-purple-300">
                <span id="progress-text">Ready to scan...</span>
                <span id="progress-count">0 / 0</span>
            </div>
            <div id="current-repo" class="text-sm text-purple-400 mt-1"></div>
        </div>

        <!-- Log Panel (collapsible) -->
        <details class="bg-black/30 rounded-xl mb-6">
            <summary class="p-4 cursor-pointer text-lg font-semibold">📋 Scan Logs <span id="log-count" class="text-sm text-purple-400">(0)</span></summary>
            <div id="log-container" class="max-h-48 overflow-y-auto p-4 pt-0 space-y-1">
            </div>
        </details>

        <div id="loading" class="text-center py-12">
            <div class="animate-spin inline-block w-12 h-12 border-4 border-purple-400 border-t-transparent rounded-full"></div>
            <p class="mt-4 text-purple-200">Scanning the zoo...</p>
        </div>

        <div id="summary" class="hidden grid grid-cols-2 md:grid-cols-5 gap-4 mb-8"></div>
        <div id="repos" class="hidden grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6"></div>
    </div>

    <!-- Detail Modal - Redesigned -->
    <div id="detail-modal" class="fixed inset-0 bg-black/90 z-50 hidden overflow-y-auto backdrop-blur-sm">
        <div class="min-h-screen px-4 py-6 flex items-start justify-center">
            <div class="bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl max-w-5xl w-full shadow-2xl border border-slate-700">
                <!-- Header -->
                <div id="modal-header" class="p-5 border-b border-slate-700/50 bg-black/20">
                    <div class="flex justify-between items-start">
                        <div class="flex items-center gap-4">
                            <div class="text-5xl" id="modal-zoo"></div>
                            <div>
                                <div class="flex items-center gap-2">
                                    <h2 id="modal-title" class="text-2xl font-bold"></h2>
                                    <span id="modal-status" class="text-2xl"></span>
                                    <span id="modal-badge" class="px-3 py-1 rounded-full text-xs font-bold"></span>
                                </div>
                                <div id="modal-path" class="text-sm text-slate-400 font-mono mt-1"></div>
                            </div>
                        </div>
                        <button onclick="closeModal()" class="text-3xl text-slate-400 hover:text-white transition-colors">&times;</button>
                    </div>
                </div>
                
                <div id="modal-body" class="p-5 max-h-[80vh] overflow-y-auto">
                    <!-- Loading -->
                    <div id="modal-loading" class="text-center py-12">
                        <div class="animate-spin inline-block w-10 h-10 border-4 border-purple-500 border-t-transparent rounded-full"></div>
                        <p class="mt-3 text-slate-400">Loading analysis...</p>
                    </div>
                    
                    <!-- Content -->
                    <div id="modal-content" class="hidden space-y-5">
                        <!-- Stats Row -->
                        <div class="grid grid-cols-3 md:grid-cols-6 gap-3">
                            <div class="bg-purple-900/30 border border-purple-700/30 rounded-xl p-3 text-center">
                                <div id="stat-version" class="text-lg font-bold text-purple-300"></div>
                                <div class="text-xs text-purple-400">FastMCP</div>
                            </div>
                            <div class="bg-green-900/30 border border-green-700/30 rounded-xl p-3 text-center">
                                <div id="stat-portmanteau" class="text-lg font-bold text-green-300"></div>
                                <div class="text-xs text-green-400">Portmanteaus</div>
                            </div>
                            <div class="bg-blue-900/30 border border-blue-700/30 rounded-xl p-3 text-center">
                                <div id="stat-ops" class="text-lg font-bold text-blue-300"></div>
                                <div class="text-xs text-blue-400">Operations</div>
                            </div>
                            <div class="bg-yellow-900/30 border border-yellow-700/30 rounded-xl p-3 text-center">
                                <div id="stat-individual" class="text-lg font-bold text-yellow-300"></div>
                                <div class="text-xs text-yellow-400">Individual</div>
                            </div>
                            <div class="bg-cyan-900/30 border border-cyan-700/30 rounded-xl p-3 text-center">
                                <div id="stat-ci" class="text-lg font-bold text-cyan-300"></div>
                                <div class="text-xs text-cyan-400">CI/CD</div>
                            </div>
                            <div class="bg-pink-900/30 border border-pink-700/30 rounded-xl p-3 text-center">
                                <div id="stat-class" class="text-lg font-bold text-pink-300"></div>
                                <div class="text-xs text-pink-400">Zoo Class</div>
                            </div>
                        </div>
                        
                        <!-- Structure Badges -->
                        <div class="flex flex-wrap gap-2" id="structure-badges"></div>
                        
                        <!-- Two Column Layout -->
                        <div class="grid md:grid-cols-2 gap-4">
                            <!-- Left: Issues & Recs -->
                            <div class="space-y-4">
                                <div id="issues-section" class="hidden">
                                    <div class="bg-red-950/50 border border-red-800/50 rounded-xl overflow-hidden">
                                        <div class="px-4 py-2 bg-red-900/30 border-b border-red-800/30 font-semibold text-red-300 flex items-center gap-2">
                                            <span>🚨</span> Issues
                                        </div>
                                        <ul id="issues-list" class="p-3 space-y-2 text-sm"></ul>
                                    </div>
                                </div>
                                <div id="recs-section" class="hidden">
                                    <div class="bg-amber-950/50 border border-amber-800/50 rounded-xl overflow-hidden">
                                        <div class="px-4 py-2 bg-amber-900/30 border-b border-amber-800/30 font-semibold text-amber-300 flex items-center gap-2">
                                            <span>💡</span> Recommendations
                                        </div>
                                        <ul id="recs-list" class="p-3 space-y-2 text-sm"></ul>
                                    </div>
                                </div>
                                <div id="sota-section" class="hidden">
                                    <div class="bg-emerald-950/50 border border-emerald-800/50 rounded-xl p-4 text-center">
                                        <div class="text-4xl mb-2">✅</div>
                                        <div class="font-bold text-emerald-300">State of the Art!</div>
                                        <div class="text-sm text-emerald-400">No issues detected</div>
                                    </div>
                                </div>
                            </div>
                            
                            <!-- Right: README Preview -->
                            <div class="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden">
                                <div class="px-4 py-2 bg-slate-700/30 border-b border-slate-600/30 font-semibold text-slate-300 flex items-center gap-2">
                                    <span>📖</span> README Preview
                                </div>
                                <div id="readme-content" class="p-3 text-xs text-slate-400 font-mono whitespace-pre-wrap max-h-48 overflow-y-auto leading-relaxed"></div>
                            </div>
                        </div>
                        
                        <!-- Tools Section -->
                        <div class="bg-slate-800/50 border border-slate-700/50 rounded-xl overflow-hidden">
                            <details open>
                                <summary class="px-4 py-3 bg-slate-700/30 border-b border-slate-600/30 font-semibold text-slate-200 cursor-pointer flex items-center justify-between">
                                    <span class="flex items-center gap-2">
                                        <span>🔧</span> Tools
                                        <span id="tools-count" class="text-sm font-normal text-slate-400"></span>
                                    </span>
                                    <span class="text-xs text-slate-500">click to collapse</span>
                                </summary>
                                <div id="tools-list" class="p-3 space-y-1 max-h-80 overflow-y-auto"></div>
                            </details>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let eventSource = null;
        
        function startProgressStream() {
            eventSource = new EventSource('/api/progress/stream');
            eventSource.onmessage = (e) => {
                const data = JSON.parse(e.data);
                updateProgress(data);
            };
            eventSource.onerror = () => {
                eventSource.close();
            };
        }
        
        function updateProgress(p) {
            const pct = p.total > 0 ? Math.round((p.scanned / p.total) * 100) : 0;
            document.getElementById('progress-bar').style.width = pct + '%';
            document.getElementById('progress-count').textContent = `${p.scanned} / ${p.total}`;
            document.getElementById('progress-text').textContent = 
                p.status === 'scanning' ? `Found ${p.mcp_found} MCP repos...` :
                p.status === 'done' ? `Complete! Found ${p.mcp_found} MCP repos in ${p.elapsed.toFixed(1)}s` :
                'Ready to scan...';
            
            const badge = document.getElementById('status-badge');
            badge.textContent = p.status.charAt(0).toUpperCase() + p.status.slice(1);
            badge.className = 'px-3 py-1 rounded-full text-sm ' + 
                (p.status === 'scanning' ? 'bg-yellow-500' : 
                 p.status === 'done' ? 'bg-green-500' : 'bg-gray-600');
            
            if (p.current_repo) {
                document.getElementById('current-repo').textContent = '→ ' + p.current_repo;
            }
        }
        
        async function loadLogs() {
            try {
                const res = await fetch('/api/logs?limit=50');
                const logs = await res.json();
                const container = document.getElementById('log-container');
                container.innerHTML = logs.map(l => 
                    `<div class="log-entry text-purple-300">[${l.time.split('T')[1].split('.')[0]}] ${l.msg}</div>`
                ).join('');
                document.getElementById('log-count').textContent = `(${logs.length})`;
            } catch (e) {}
        }

        async function loadData() {
            startProgressStream();
            try {
                const res = await fetch('/api/runts/');
                const data = await res.json();
                if (eventSource) eventSource.close();
                renderDashboard(data);
                loadLogs();
            } catch (e) {
                document.getElementById('loading').innerHTML = '<p class="text-red-400">Failed to load data</p>';
            }
        }

        function renderDashboard(data) {
            document.getElementById('loading').classList.add('hidden');

            const summary = document.getElementById('summary');
            summary.classList.remove('hidden');
            summary.innerHTML = `
                <div class="bg-white/10 rounded-xl p-4 text-center cursor-pointer hover:bg-white/20" onclick="filterRepos('all')">
                    <div class="text-3xl font-bold">${data.summary.total_mcp_repos}</div>
                    <div class="text-sm text-purple-200">Total</div>
                </div>
                <div class="bg-white/10 rounded-xl p-4 text-center cursor-pointer hover:bg-white/20" onclick="filterRepos('jumbo')">
                    <div class="text-3xl">🐘</div>
                    <div class="text-sm text-purple-200">Jumbos</div>
                </div>
                <div class="bg-red-500/20 rounded-xl p-4 text-center cursor-pointer hover:bg-red-500/30" onclick="filterRepos('red')">
                    <div class="text-3xl font-bold text-red-400">${data.summary.runts}</div>
                    <div class="text-sm text-red-200">Runts 🐛</div>
                </div>
                <div class="bg-orange-500/20 rounded-xl p-4 text-center cursor-pointer hover:bg-orange-500/30" onclick="filterRepos('orange')">
                    <div class="text-3xl font-bold text-orange-400">${data.summary.improvable || 0}</div>
                    <div class="text-sm text-orange-200">Improvable ⚠️</div>
                </div>
                <div class="bg-green-500/20 rounded-xl p-4 text-center cursor-pointer hover:bg-green-500/30" onclick="filterRepos('green')">
                    <div class="text-3xl font-bold text-green-400">${data.summary.sota}</div>
                    <div class="text-sm text-green-200">SOTA ✅</div>
                </div>
            `;

            const repos = document.getElementById('repos');
            repos.classList.remove('hidden');
            const allRepos = [...data.runts, ...data.sota_repos];
            window.allRepos = allRepos;
            renderRepos(allRepos);
        }

        function renderRepos(repos) {
            const container = document.getElementById('repos');
            container.innerHTML = repos.map(repo => `
                <div class="card-${repo.status_color} border-2 rounded-xl p-4 transition-all hover:scale-105 cursor-pointer"
                     onclick="showDetails('${repo.name}')">
                    <div class="flex items-center justify-between mb-3">
                        <div class="flex items-center gap-2">
                            <span class="text-3xl">${repo.zoo_animal}</span>
                            <span class="text-2xl">${repo.status_emoji}</span>
                            <h3 class="font-bold text-lg text-gray-800">${repo.name}</h3>
                        </div>
                        <span class="badge-${repo.status_color} px-3 py-1 rounded-full text-white text-sm">
                            ${repo.status_label}
                        </span>
                    </div>
                    <div class="flex gap-4 text-sm text-gray-600">
                        <span>FastMCP: <strong>${repo.fastmcp_version || '-'}</strong></span>
                        <span>Tools: <strong>${repo.tool_count}</strong>${repo.portmanteau_ops > 0 ? ` (${repo.portmanteau_ops} ops)` : ''}</span>
                        <span>${repo.zoo_class}</span>
                    </div>
                    ${repo.runt_reasons.length > 0 ? `
                        <div class="mt-2 text-sm text-gray-500">
                            ${repo.runt_reasons.length} issue${repo.runt_reasons.length > 1 ? 's' : ''}
                        </div>
                    ` : ''}
                </div>
            `).join('');
        }

        function filterRepos(filter) {
            let filtered = window.allRepos;
            if (filter === 'red') filtered = window.allRepos.filter(r => r.status_color === 'red');
            else if (filter === 'orange') filtered = window.allRepos.filter(r => r.status_color === 'orange');
            else if (filter === 'green') filtered = window.allRepos.filter(r => r.status_color === 'green');
            else if (filter === 'jumbo') filtered = window.allRepos.filter(r => r.zoo_class === 'jumbo');
            renderRepos(filtered);
        }

        async function showDetails(name) {
            const repo = window.allRepos.find(r => r.name === name);
            if (!repo) return;
            
            // Show modal with basic info
            document.getElementById('detail-modal').classList.remove('hidden');
            document.getElementById('modal-zoo').textContent = repo.zoo_animal;
            document.getElementById('modal-status').textContent = repo.status_emoji;
            document.getElementById('modal-title').textContent = repo.name;
            document.getElementById('modal-loading').classList.remove('hidden');
            document.getElementById('modal-content').classList.add('hidden');
            
            // Fetch detailed info
            try {
                const res = await fetch(`/api/repo/${name}`);
                const data = await res.json();
                if (!data.success) throw new Error(data.error);
                
                const r = data.repo;
                
                // Header extras
                document.getElementById('modal-path').textContent = r.path || '';
                const badge = document.getElementById('modal-badge');
                badge.textContent = r.status_label || 'Unknown';
                badge.className = 'px-3 py-1 rounded-full text-xs font-bold ' + 
                    (r.status_color === 'green' ? 'bg-green-600' : 
                     r.status_color === 'orange' ? 'bg-orange-600' : 'bg-red-600');
                
                // Stats
                document.getElementById('stat-version').textContent = r.fastmcp_version || '-';
                document.getElementById('stat-portmanteau').textContent = r.portmanteau_tools || 0;
                document.getElementById('stat-ops').textContent = r.portmanteau_ops || 0;
                document.getElementById('stat-individual').textContent = r.individual_tools || 0;
                document.getElementById('stat-ci').textContent = r.has_ci ? `✓ ${r.ci_workflows || 0}` : '✗';
                document.getElementById('stat-class').textContent = r.zoo_class || '-';
                
                // Structure badges
                const badges = [];
                badges.push(r.has_src ? 
                    '<span class="px-2 py-1 bg-green-800/50 text-green-300 rounded text-xs">✓ src/</span>' :
                    '<span class="px-2 py-1 bg-red-800/50 text-red-300 rounded text-xs">✗ src/</span>');
                badges.push(r.has_tests ? 
                    '<span class="px-2 py-1 bg-green-800/50 text-green-300 rounded text-xs">✓ tests/</span>' :
                    '<span class="px-2 py-1 bg-slate-700/50 text-slate-400 rounded text-xs">✗ tests/</span>');
                badges.push(r.has_scripts ? 
                    '<span class="px-2 py-1 bg-green-800/50 text-green-300 rounded text-xs">✓ scripts/</span>' :
                    '<span class="px-2 py-1 bg-slate-700/50 text-slate-400 rounded text-xs">✗ scripts/</span>');
                badges.push(r.has_tools_dir ? 
                    '<span class="px-2 py-1 bg-green-800/50 text-green-300 rounded text-xs">✓ tools/</span>' :
                    '<span class="px-2 py-1 bg-slate-700/50 text-slate-400 rounded text-xs">✗ tools/</span>');
                badges.push(r.has_portmanteau ? 
                    '<span class="px-2 py-1 bg-green-800/50 text-green-300 rounded text-xs">✓ portmanteau</span>' :
                    '<span class="px-2 py-1 bg-slate-700/50 text-slate-400 rounded text-xs">✗ portmanteau</span>');
                if (r.has_nonconforming_registration) {
                    badges.push(`<span class="px-2 py-1 bg-orange-800/50 text-orange-300 rounded text-xs">⚠ ${r.nonconforming_count} non-decorator</span>`);
                }
                document.getElementById('structure-badges').innerHTML = badges.join('');
                
                // Issues, Recs, SOTA
                const hasIssues = r.runt_reasons && r.runt_reasons.length > 0;
                const hasRecs = r.recommendations && r.recommendations.length > 0;
                
                if (hasIssues) {
                    document.getElementById('issues-section').classList.remove('hidden');
                    document.getElementById('issues-list').innerHTML = r.runt_reasons.map(i => 
                        `<li class="flex items-start gap-2"><span class="text-red-400">✗</span><span class="text-red-200">${i}</span></li>`
                    ).join('');
                } else {
                    document.getElementById('issues-section').classList.add('hidden');
                }
                
                if (hasRecs) {
                    document.getElementById('recs-section').classList.remove('hidden');
                    document.getElementById('recs-list').innerHTML = r.recommendations.map(i => 
                        `<li class="flex items-start gap-2"><span class="text-amber-400">→</span><span class="text-amber-200">${i}</span></li>`
                    ).join('');
                } else {
                    document.getElementById('recs-section').classList.add('hidden');
                }
                
                // SOTA celebration
                if (!hasIssues && r.status_color === 'green') {
                    document.getElementById('sota-section').classList.remove('hidden');
                } else {
                    document.getElementById('sota-section').classList.add('hidden');
                }
                
                // README
                const readme = r.readme || '';
                document.getElementById('readme-content').textContent = readme.substring(0, 2000) || '(No README found)';
                
                // Tools with better formatting
                const tools = r.tools_detail || [];
                const portTools = tools.filter(t => t.type === 'portmanteau');
                const indivTools = tools.filter(t => t.type !== 'portmanteau');
                document.getElementById('tools-count').textContent = `(${portTools.length} portmanteau, ${indivTools.length} individual)`;
                
                let toolsHtml = '';
                if (portTools.length > 0) {
                    toolsHtml += '<div class="mb-3"><div class="text-xs text-green-400 mb-2 font-semibold">📦 PORTMANTEAU TOOLS</div>';
                    toolsHtml += portTools.map(t => `
                        <details class="bg-green-900/20 border border-green-800/30 rounded-lg mb-1 overflow-hidden">
                            <summary class="px-3 py-2 cursor-pointer hover:bg-green-800/20 flex items-center gap-2">
                                <span class="text-green-400">📦</span>
                                <code class="font-bold text-green-200">${t.name}</code>
                                <span class="text-xs text-slate-500 ml-auto">${t.file}</span>
                            </summary>
                            <div class="px-3 py-2 bg-black/20 text-xs text-slate-300 whitespace-pre-wrap border-t border-green-800/20">${t.docstring || '(no docstring)'}</div>
                        </details>
                    `).join('');
                    toolsHtml += '</div>';
                }
                if (indivTools.length > 0) {
                    toolsHtml += '<div><div class="text-xs text-yellow-400 mb-2 font-semibold">🔹 INDIVIDUAL TOOLS</div>';
                    toolsHtml += indivTools.map(t => `
                        <details class="bg-yellow-900/10 border border-yellow-800/20 rounded-lg mb-1 overflow-hidden">
                            <summary class="px-3 py-2 cursor-pointer hover:bg-yellow-800/10 flex items-center gap-2">
                                <span class="text-yellow-400">🔹</span>
                                <code class="font-bold text-yellow-200">${t.name}</code>
                                <span class="text-xs text-slate-500 ml-auto">${t.file}</span>
                            </summary>
                            <div class="px-3 py-2 bg-black/20 text-xs text-slate-300 whitespace-pre-wrap border-t border-yellow-800/20">${t.docstring || '(no docstring)'}</div>
                        </details>
                    `).join('');
                    toolsHtml += '</div>';
                }
                document.getElementById('tools-list').innerHTML = toolsHtml || '<p class="text-slate-500 text-center py-4">No tools found</p>';
                
                document.getElementById('modal-loading').classList.add('hidden');
                document.getElementById('modal-content').classList.remove('hidden');
            } catch (e) {
                document.getElementById('modal-loading').innerHTML = `<p class="text-red-400 text-center py-8">Error: ${e.message}</p>`;
            }
        }
        
        function closeModal() {
            document.getElementById('detail-modal').classList.add('hidden');
        }
        
        // Close modal on escape
        document.addEventListener('keydown', e => {
            if (e.key === 'Escape') closeModal();
        });

        loadData();
    </script>
</body>
</html>
"""


@app.get("/api/progress")
async def get_progress():
    """Get current scan progress."""
    return scan_progress


@app.get("/api/progress/stream")
async def progress_stream():
    """SSE stream for real-time progress updates."""
    async def generate():
        while scan_progress["status"] in ("idle", "scanning"):
            yield f"data: {json.dumps(scan_progress)}\n\n"
            await asyncio.sleep(0.3)
        yield f"data: {json.dumps(scan_progress)}\n\n"
    
    return StreamingResponse(generate(), media_type="text/event-stream")


@app.get("/api/logs")
async def get_logs(limit: int = Query(default=100)):
    """Get collected scan logs."""
    return log_collector.get_logs(limit)


@app.get("/api/runts/")
async def get_runts(scan_path: str = Query(default="D:/Dev/repos")):
    """Get runt analysis for all MCP repos with progress logging."""
    global scan_progress
    
    runts = []
    sota_repos = []
    improvable = 0

    path = Path(scan_path).expanduser().resolve()
    if not path.exists():
        return {"success": False, "error": f"Path not found: {scan_path}"}

    # Get list of directories first
    dirs = [d for d in path.iterdir() if d.is_dir() and not d.name.startswith('.')]
    total = len(dirs)
    
    # Initialize progress
    scan_progress = {
        "status": "scanning",
        "current_repo": None,
        "scanned": 0,
        "total": total,
        "mcp_found": 0,
        "start_time": time.time(),
        "elapsed": 0,
    }
    
    logger.info(f"🔍 Starting scan of {total} directories in {scan_path}")
    log_collector.clear()
    
    for idx, item in enumerate(dirs):
        scan_progress["current_repo"] = item.name
        scan_progress["scanned"] = idx + 1
        scan_progress["elapsed"] = time.time() - scan_progress["start_time"]
        
        logger.info(f"[{idx+1}/{total}] Scanning {item.name}...")
        
        repo_info = analyze_repo(item)
        if repo_info:
            scan_progress["mcp_found"] += 1
            zoo = repo_info["zoo_animal"]
            status = repo_info["status_emoji"]
            ver = repo_info["fastmcp_version"]
            pt = repo_info.get("portmanteau_tools", 0)  # Portmanteau tools
            ops = repo_info.get("portmanteau_ops", 0)   # Operations in portmanteaus
            ind = repo_info.get("individual_tools", 0)  # Simple individual tools
            total = repo_info.get("tool_count", 0)
            # Structure flags
            flags = []
            if not repo_info.get("has_src"): flags.append("!src")
            if not repo_info.get("has_tests") and total >= 10: flags.append("!tests")
            if not repo_info.get("has_tools_dir") and total >= 20: flags.append("!tools/")
            if repo_info.get("has_nonconforming_registration"):
                nc = repo_info.get("nonconforming_count", 0)
                if nc > total:
                    flags.append(f"!reg:{nc}")
            struct = " ".join(flags) if flags else "✓"
            # Format: port(ops)+indiv  e.g., 5(42)+3
            tool_str = f"{pt}({ops})+{ind}" if ops > 0 else f"{pt}+{ind}"
            logger.info(f"  {zoo} {status} v{ver} {tool_str} [{struct}]")
            
            if repo_info.get("is_runt"):
                runts.append(repo_info)
            else:
                sota_repos.append(repo_info)
                if repo_info.get("status_color") == "orange":
                    improvable += 1
        
        # Yield control to allow progress updates
        await asyncio.sleep(0)

    elapsed = time.time() - scan_progress["start_time"]
    scan_progress["status"] = "done"
    scan_progress["elapsed"] = elapsed
    
    runts.sort(key=lambda x: len(x.get("runt_reasons", [])), reverse=True)
    sota_repos.sort(key=lambda x: x.get("name", ""))

    logger.info(f"✅ Scan complete in {elapsed:.1f}s - Found {len(runts)+len(sota_repos)} MCP repos")
    logger.info(f"   🐛 Runts: {len(runts)} | ✅ SOTA: {len(sota_repos)-improvable} | ⚠️ Improvable: {improvable}")

    return {
        "success": True,
        "summary": {
            "total_mcp_repos": len(runts) + len(sota_repos),
            "runts": len(runts),
            "sota": len(sota_repos) - improvable,
            "improvable": improvable,
        },
        "runts": runts,
        "sota_repos": sota_repos,
        "scan_path": scan_path,
        "timestamp": time.time(),
        "elapsed_seconds": elapsed,
    }


def get_detailed_repo_info(repo_path: Path) -> Dict[str, Any]:
    """Get detailed info for a single repo including README and tool docstrings."""
    base_info = analyze_repo(repo_path)
    if not base_info:
        return None
    
    details = {**base_info}
    
    # Read README
    readme_content = ""
    for readme_name in ["README.md", "readme.md", "README.rst", "README.txt"]:
        readme_file = repo_path / readme_name
        if readme_file.exists():
            try:
                readme_content = readme_file.read_text(encoding='utf-8', errors='ignore')[:5000]  # Limit size
            except:
                pass
            break
    details["readme"] = readme_content
    
    # Extract tool details with docstrings
    tools_detail = []
    pkg_name = repo_path.name.replace('-', '_')
    search_dirs = []
    if (repo_path / "src").exists():
        search_dirs.append(repo_path / "src")
    if (repo_path / pkg_name).exists():
        search_dirs.append(repo_path / pkg_name)
    if not search_dirs:
        search_dirs.append(repo_path)
    
    # Pattern to extract tool function with docstring
    tool_extract_pattern = re.compile(
        r'@(?:app|mcp|self\.mcp|server)\.tool[^\n]*\n'
        r'(?:\s*async\s+)?def\s+(\w+)\s*\([^)]*\)[^:]*:\s*'
        r'(?:"""([\s\S]*?)"""|\'\'\'([\s\S]*?)\'\'\')?',
        re.MULTILINE
    )
    
    for search_dir in search_dirs:
        for py_file in fast_py_glob(search_dir, max_depth=4):
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                rel_path = py_file.relative_to(repo_path)
                
                for match in tool_extract_pattern.finditer(content):
                    func_name = match.group(1)
                    docstring = match.group(2) or match.group(3) or ""
                    docstring = docstring.strip()[:500]  # Limit docstring size
                    
                    # Determine tool type
                    path_str = str(py_file).lower()
                    is_portmanteau = (
                        "portmanteau" in path_str or 
                        path_str.endswith("_tool.py") or
                        path_str.endswith("_tools.py")
                    )
                    
                    tools_detail.append({
                        "name": func_name,
                        "file": str(rel_path),
                        "docstring": docstring,
                        "type": "portmanteau" if is_portmanteau else "individual",
                    })
            except:
                pass
    
    details["tools_detail"] = tools_detail
    return details


@app.get("/api/repo/{repo_name}")
async def get_repo_details(repo_name: str, scan_path: str = Query(default="D:/Dev/repos")):
    """Get detailed analysis for a single MCP repo."""
    path = Path(scan_path).expanduser().resolve()
    repo_path = path / repo_name
    
    if not repo_path.exists():
        return {"success": False, "error": f"Repo not found: {repo_name}"}
    
    details = get_detailed_repo_info(repo_path)
    if not details:
        return {"success": False, "error": f"Not an MCP repo: {repo_name}"}
    
    return {"success": True, "repo": details}


if __name__ == "__main__":
    print("🦁 MCP Zoo Runt Analyzer v2.2.1 starting...")
    print("🐘 Dashboard: http://localhost:8888")
    print("🦒 API: http://localhost:8888/api/runts/")
    print("🔍 Detail: http://localhost:8888/api/repo/{name}")
    print("📋 Logs: http://localhost:8888/api/logs")
    print("📡 Progress: http://localhost:8888/api/progress")
    uvicorn.run(app, host="0.0.0.0", port=8888)
