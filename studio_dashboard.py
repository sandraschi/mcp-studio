"""
MCP Studio Dashboard v1.0.0
===========================
The unified dashboard for the MCP Zoo 🦁🐘🦒

Combines:
- Static Analysis: Runt checking, code quality, structure validation
- Runtime Analysis: Live server connections, tool discovery, execution
- Client Discovery: Finds servers from Claude Desktop, Cursor, Windsurf, etc.

Usage:
    python studio_dashboard.py
    
Dashboard: http://localhost:8888
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
import uvicorn

# FastMCP client imports
try:
    from fastmcp import Client
    from fastmcp.client.transports import StdioTransport
    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

REPOS_DIR = Path(r"D:\Dev\repos")
PORT = 8888
VERSION = "1.0.0"

# MCP Client config locations
MCP_CLIENT_CONFIGS = {
    "claude-desktop": [
        Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
        Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
    ],
    "cursor": [
        Path(os.environ.get("APPDATA", "")) / "Cursor" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
        Path.home() / ".cursor" / "mcp.json",
    ],
    "windsurf": [
        Path(os.environ.get("APPDATA", "")) / "Windsurf" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "mcp_settings.json",
    ],
    "cline": [
        Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
    ],
}

# Skip these directories when scanning - MUST include all venv patterns
SKIP_DIRS = {
    'node_modules', '__pycache__', '.git', 'venv', '.venv', 'dist', 'build', 
    'env', '.env', 'eggs', '.eggs', '.tox', '.mypy_cache', '.pytest_cache',
    'site-packages', '.ruff_cache', 'coverage', 'htmlcov', '.idea', '.vscode',
    '_legacy', 'deprecated', 'Lib', 'Scripts', 'Include',  # Windows venv
    'lib', 'bin', 'lib64',  # Linux venv
}

# FastMCP version thresholds
FASTMCP_LATEST = "2.13.1"
FASTMCP_RUNT_THRESHOLD = "2.10.0"
FASTMCP_WARN_THRESHOLD = "2.12.0"

# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(title="MCP Studio", version=VERSION)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Global state
state = {
    "discovered_servers": {},      # From MCP client configs
    "repo_analysis": {},           # Static analysis results
    "connected_servers": {},       # Live connections (client instances)
    "scan_progress": {"current": "", "total": 0, "done": 0, "status": "idle"},
    "logs": [],
}

# ═══════════════════════════════════════════════════════════════════════════════
# CLIENT DISCOVERY - Find servers from all MCP clients
# ═══════════════════════════════════════════════════════════════════════════════

def discover_mcp_clients() -> Dict[str, List[Dict]]:
    """Discover MCP servers from all known client configurations."""
    results = {}
    
    for client_name, config_paths in MCP_CLIENT_CONFIGS.items():
        for config_path in config_paths:
            if not config_path.exists():
                continue
            
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                servers = config.get("mcpServers", {})
                if servers:
                    results[client_name] = {
                        "path": str(config_path),
                        "servers": []
                    }
                    for server_id, server_config in servers.items():
                        results[client_name]["servers"].append({
                            "id": server_id,
                            "name": server_id.replace("-", " ").replace("_", " ").title(),
                            "command": server_config.get("command", ""),
                            "args": server_config.get("args", []),
                            "cwd": server_config.get("cwd"),
                            "env": server_config.get("env", {}),
                            "status": "discovered",
                        })
                    break  # Found config for this client
            except Exception as e:
                log(f"Error reading {client_name} config: {e}")
    
    return results

# ═══════════════════════════════════════════════════════════════════════════════
# STATIC ANALYSIS - Runt checker
# ═══════════════════════════════════════════════════════════════════════════════

def fast_py_glob(directory: Path, max_depth: int = 3) -> List[Path]:
    """Fast python file glob with depth limit and skip dirs."""
    results = []
    
    # Pre-check: don't scan if directory itself is in a venv
    dir_str = str(directory).lower()
    if '.venv' in dir_str or 'site-packages' in dir_str or '\\lib\\' in dir_str:
        return results
    
    def _walk(path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for item in path.iterdir():
                name_lower = item.name.lower()
                if item.is_dir():
                    # Skip venv, cache, and hidden dirs
                    if name_lower in SKIP_DIRS or item.name.startswith('.') or item.name.endswith('.egg-info'):
                        continue
                    _walk(item, depth + 1)
                elif item.suffix == '.py' and 'test' not in name_lower and name_lower != '__init__.py':
                    # Skip backup/development files
                    if any(x in name_lower for x in ['_fixed', '_backup', '_old', '_dev', '_wip']):
                        continue
                    results.append(item)
        except (PermissionError, OSError):
            pass
    _walk(directory, 0)
    return results

def analyze_repo(repo_path: Path) -> Optional[Dict[str, Any]]:
    """Analyze a single MCP repository - COPIED FROM WORKING runt_api.py."""
    info = {
        "name": repo_path.name,
        "path": str(repo_path),
        "fastmcp_version": None,
        "tool_count": 0,
        "tools": 0,  # Alias for compatibility
        "has_portmanteau": False,
        "has_ci": False,
        "has_cicd": False,  # Alias
        "ci_workflows": 0,
        "cicd_count": 0,  # Alias
        "is_runt": False,
        "runt_reasons": [],
        "issues": [],  # Alias
        "recommendations": [],
        "status_emoji": "✅",
        "status_color": "green",
        "status_label": "SOTA",
        "status": "sota",
        "zoo_class": "unknown",
        "zoo_emoji": "🦔",
        "portmanteau_tools": 0,
        "portmanteau_ops": 0,
        "individual_tools": 0,
        "has_src": False,
        "has_tests": False,
        "has_scripts": False,
        "has_tools_dir": False,
        "has_mcpb": False,
        "has_dxt": False,
        "has_dual_interface": False,
        "has_http_interface": False,
        "has_health_endpoint": False,
        "has_proper_docstrings": False,
        "has_prompt_templates": False,
        "has_type_hints": False,
        "has_logging": False,
        "test_count": 0,
        "features": [],
    }

    # Check for requirements.txt or pyproject.toml
    req_file = repo_path / "requirements.txt"
    pyproject_file = repo_path / "pyproject.toml"

    fastmcp_version = None
    # Prefer pyproject.toml (more authoritative) over requirements.txt
    for config_file in [pyproject_file, req_file]:
        if config_file.exists():
            try:
                content = config_file.read_text(encoding='utf-8', errors='ignore')
                # Prefer version specifiers (>=, ==, ~=) over plain text mentions
                match = re.search(r'fastmcp[>=<~]+(\d+\.\d+\.?\d*)', content, re.IGNORECASE)
                if not match:
                    match = re.search(r'fastmcp.*?(\d+\.\d+\.?\d*)', content, re.IGNORECASE)
                if match:
                    fastmcp_version = match.group(1)
                    break
            except Exception:
                pass

    if not fastmcp_version:
        return None  # Not an MCP repo

    info["fastmcp_version"] = fastmcp_version

    # Count tools - SMART APPROACH from runt_api.py
    # Match various tool decorator patterns:
    # @app.tool(), @mcp.tool(), @self.mcp.tool(), @server.tool(), @tool(), @self.tool()
    tool_pattern = re.compile(r'@(?:(?:app|mcp|self(?:\.(?:app|mcp))?(?:_server\.mcp)?|server)\.)?tool(?:\s*\(|(?=\s*(?:\r?\n|def\s)))', re.MULTILINE)
    nonconforming_pattern = re.compile(r'def register_\w+_tool\s*\(|\.add_tool\s*\(|register_tool\s*\(')
    tool_count = 0
    
    pkg_name = repo_path.name.replace('-', '_')
    # Try multiple package name variations
    pkg_name_short = pkg_name.replace('_mcp', '').replace('mcp_', '')
    # Also try inserting underscore before mcp (calibremcp -> calibre_mcp)
    pkg_name_underscore = pkg_name.replace('mcp', '_mcp') if 'mcp' in pkg_name and '_mcp' not in pkg_name else pkg_name
    
    # Find the tools directory and its __init__.py
    tools_init_paths = [
        # Try underscore variant first (calibre_mcp)
        repo_path / "src" / pkg_name_underscore / "mcp" / "tools" / "__init__.py",
        repo_path / "src" / pkg_name_underscore / "tools" / "__init__.py",
        # Try short name (advanced_memory)
        repo_path / "src" / pkg_name_short / "mcp" / "tools" / "__init__.py",
        repo_path / "src" / pkg_name_short / "tools" / "__init__.py",
        # Try full name (advanced_memory_mcp)
        repo_path / "src" / pkg_name / "mcp" / "tools" / "__init__.py",
        repo_path / "src" / pkg_name / "tools" / "__init__.py",
        # Root package dirs
        repo_path / pkg_name_underscore / "tools" / "__init__.py",
        repo_path / pkg_name_short / "tools" / "__init__.py",
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
                # Only count else block (portmanteau mode) if exists
                if 'else:' in init_content:
                    else_block = init_content.split('else:')[-1]
                    imports = re.findall(r'from\s+\.(\w+)\s+import', else_block)
                else:
                    imports = re.findall(r'from\s+\.(\w+)\s+import', init_content)
                imported_modules.update(imports)
            except Exception:
                pass
            break
    
    # Search directories - ALWAYS include the package root for tools in server.py
    search_dirs = []
    
    # Always check main package directories for tools in server.py
    for pkg_dir_name in [pkg_name, pkg_name_short, pkg_name_underscore]:
        for base in [repo_path / "src", repo_path]:
            pkg_dir = base / pkg_dir_name
            if pkg_dir.exists() and pkg_dir.is_dir() and pkg_dir not in search_dirs:
                search_dirs.append(pkg_dir)
    
    # Only add tools/ subdirectory if NOT already covered by a parent search_dir
    if tools_dir and tools_dir.exists():
        is_child_of_existing = any(
            tools_dir.is_relative_to(d) for d in search_dirs
        )
        if not is_child_of_existing:
            search_dirs.append(tools_dir)
    
    # Fallback to src or repo root
    if not search_dirs:
        src_dir = repo_path / "src"
        if src_dir.exists():
            search_dirs.append(src_dir)
        else:
            search_dirs.append(repo_path)
    
    # Also check package __init__.py for tools (system-admin-mcp pattern)
    pkg_init_files = []
    for pkg_base in [repo_path / "src" / pkg_name_underscore, repo_path / "src" / pkg_name]:
        init_file = pkg_base / "__init__.py"
        if init_file.exists():
            pkg_init_files.append(init_file)
            break
    
    # Also check plugins/ directory if it exists (virtualization-mcp pattern)
    plugins_dir = None
    for base in [repo_path / "src" / pkg_name_underscore, repo_path / "src" / pkg_name, repo_path / pkg_name]:
        candidate = base / "plugins"
        if candidate.exists() and candidate.is_dir():
            plugins_dir = candidate
            break
    
    has_nonconforming = False
    nonconforming_count = 0
    portmanteau_tools = 0
    portmanteau_ops = 0
    individual_tools = 0
    
    literal_pattern = re.compile(r'Literal\[([^\]]+)\]')
    
    # Check if repo uses portmanteau pattern (has register_tools function OR portmanteau/ subdir)
    uses_portmanteau_pattern = False
    portmanteau_dir = None
    portmanteau_modules = set()  # For PORTMANTEAU_MODULES list pattern
    if tools_dir:
        init_file = tools_dir / '__init__.py'
        if init_file.exists():
            init_text = init_file.read_text(encoding='utf-8', errors='ignore')
            # Portmanteau pattern requires BOTH register_tools AND from .manage_ or .query_ imports
            # This distinguishes it from general register_tools functions (like blender-mcp)
            has_register_tools = 'def register_tools' in init_text
            has_portmanteau_imports = (
                'from .manage_' in init_text or 
                'from .query_' in init_text or
                'from .analyze_' in init_text
            )
            uses_portmanteau_pattern = has_register_tools and has_portmanteau_imports
            # Check for PORTMANTEAU_MODULES list pattern (pywinauto-mcp style)
            if 'PORTMANTEAU_MODULES' in init_text:
                # Extract module names from list
                import_match = re.findall(r"'(portmanteau_\w+|desktop_state)'", init_text)
                portmanteau_modules = set(import_match)
        # Also check for tools/portmanteau/ subdirectory
        candidate_portmanteau = tools_dir / 'portmanteau'
        if candidate_portmanteau.exists() and candidate_portmanteau.is_dir():
            portmanteau_dir = candidate_portmanteau
    
    # Check if repo uses monolithic server pattern (all tools in server.py)
    monolithic_server = None
    # Check for monolithic if no portmanteau pattern detected AND no portmanteau_dir
    if not uses_portmanteau_pattern and not portmanteau_modules and not portmanteau_dir:
        # Check fastmcp_server.py first as it's often the entry point
        for server_file in ['fastmcp_server.py', 'mcp_server.py', 'server.py', 'main.py', '__main__.py']:
            candidate = (repo_path / "src" / pkg_name_underscore / server_file)
            if not candidate.exists():
                candidate = (repo_path / "src" / pkg_name / server_file)
            if not candidate.exists():
                candidate = (repo_path / pkg_name / server_file)
            if candidate.exists():
                try:
                    server_content = candidate.read_text(encoding='utf-8', errors='ignore')
                    # Check for actual tool decorators (not just mentions in comments)
                    # Look for decorator at start of line with proper indentation
                    actual_tools = tool_pattern.findall(server_content)
                    if actual_tools:
                        monolithic_server = candidate
                        break
                except Exception as e:
                    logger.debug(f"Error reading {candidate}: {e}")
    
    # Check for modular entry point pattern (mcp_main.py -> mcp_server_clean.py -> tools/)
    imported_tool_modules = set()
    for entry_file in ['mcp_main.py', 'mcp_server_clean.py', 'mcp_server.py']:
        for base in [repo_path / "src" / pkg_name_underscore, repo_path / "src" / pkg_name, repo_path / pkg_name]:
            candidate = base / entry_file
            if candidate.exists():
                try:
                    content = candidate.read_text(encoding='utf-8', errors='ignore')
                    # Look for imports like: import avatarmcp.tools.core.core_tools
                    tool_imports = re.findall(r'import\s+\w+\.tools\.(\w+)\.(\w+)', content)
                    for pkg, mod in tool_imports:
                        imported_tool_modules.add(f"{pkg}/{mod}.py")
                except Exception as e:
                    logger.debug(f"Error parsing imports in {candidate}: {e}")
    
    # If monolithic server, ONLY count from that file
    if monolithic_server:
        search_dirs = []
        py_files_to_scan = [monolithic_server]
    # If modular imports detected (mcp_server_clean.py), use those (takes precedence)
    elif imported_tool_modules:
        py_files_to_scan = None  # Will filter by imported_tool_modules
    # If PORTMANTEAU_MODULES list found, only count those files
    elif portmanteau_modules:
        py_files_to_scan = [tools_dir / f"{m}.py" for m in portmanteau_modules if (tools_dir / f"{m}.py").exists()]
        search_dirs = []
    # If has portmanteau/ subdir with actual tools, ONLY count from there
    elif portmanteau_dir:
        # Check if portmanteau dir has any @tool decorators
        has_tools = False
        for pf in portmanteau_dir.glob('*.py'):
            if pf.name != '__init__.py':
                try:
                    if '@mcp.tool' in pf.read_text(encoding='utf-8', errors='ignore') or '@app.tool' in pf.read_text(encoding='utf-8', errors='ignore'):
                        has_tools = True
                        break
                except Exception:
                    pass  # Non-critical file read error
        if has_tools:
            search_dirs = [portmanteau_dir]
            # Also include plugins/ subdirs that DON'T have a corresponding portmanteau
            if plugins_dir:
                portmanteau_names = {p.stem.replace('_management', '') for p in portmanteau_dir.glob('*_management.py')}
                for plugin_subdir in plugins_dir.iterdir():
                    if plugin_subdir.is_dir() and plugin_subdir.name not in portmanteau_names:
                        search_dirs.append(plugin_subdir)
            py_files_to_scan = None
        else:
            py_files_to_scan = None
    else:
        py_files_to_scan = None  # Will be computed per search_dir
    
    for search_dir in search_dirs if py_files_to_scan is None else [None]:
        if py_files_to_scan is None:
            py_files = fast_py_glob(search_dir, max_depth=4)
        else:
            py_files = py_files_to_scan
            
        for py_file in py_files:
            filename = py_file.stem.lower()
            
            # For portmanteau repos, ONLY count portmanteau-style files
            if uses_portmanteau_pattern:
                is_portmanteau_entry = (
                    filename.startswith('manage_') or
                    filename.startswith('query_') or
                    filename.startswith('analyze_') or
                    filename.endswith('_portmanteau') or
                    filename in {'test_calibre_connection', 'calibre_ocr_tool'}  # Known entry points
                )
                if not is_portmanteau_entry:
                    continue
            # If modular entry imports specific tool modules, only count those
            elif imported_tool_modules:
                rel_path = f"{py_file.parent.name}/{py_file.name}"
                if rel_path not in imported_tool_modules:
                    continue
            # If we have an __init__.py with imports, only count imported modules
            # BUT only apply this filter when scanning tools/ directory, not main package
            elif imported_modules and tools_dir and py_file.is_relative_to(tools_dir):
                # Check if file matches OR if file's parent dir matches (for packages)
                file_matches = py_file.stem in imported_modules
                parent_matches = py_file.parent.name in imported_modules
                if not file_matches and not parent_matches:
                    continue
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                matches = tool_pattern.findall(content)
                file_tools = len(matches)
                
                path_str = str(py_file).lower()
                is_portmanteau_file = (
                    "portmanteau" in path_str or 
                    path_str.endswith("_tool.py") or
                    path_str.endswith("_tools.py")
                )
                
                if is_portmanteau_file:
                    portmanteau_tools += file_tools
                    for lit_match in literal_pattern.findall(content):
                        ops = len(re.findall(r'["\'][^"\']+["\']', lit_match))
                        if ops > 1:
                            portmanteau_ops += ops
                else:
                    individual_tools += file_tools
                
                tool_count += file_tools
                
                nc_matches = nonconforming_pattern.findall(content)
                if nc_matches:
                    has_nonconforming = True
                    nonconforming_count += len(nc_matches)
            except Exception:
                pass
    
    # Also scan package __init__.py for tools (some repos define tools there)
    for init_file in pkg_init_files:
        try:
            content = init_file.read_text(encoding='utf-8', errors='ignore')
            matches = tool_pattern.findall(content)
            tool_count += len(matches)
            individual_tools += len(matches)
        except Exception:
            pass
    
    info["tool_count"] = tool_count
    info["tools"] = tool_count  # Alias
    info["portmanteau_tools"] = portmanteau_tools
    info["portmanteau_ops"] = portmanteau_ops
    info["individual_tools"] = individual_tools
    info["has_portmanteau"] = portmanteau_tools > 0
    info["has_nonconforming_registration"] = has_nonconforming
    info["nonconforming_count"] = nonconforming_count
    
    # Check for split tools antipattern: tools in BOTH server.py AND tools/ directory
    # This indicates incomplete refactoring
    has_server_tools = False
    has_tools_dir_tools = False
    for base in [repo_path / "src" / pkg_name_underscore, repo_path / "src" / pkg_name, repo_path / pkg_name]:
        for server_file in ['server.py', 'mcp_server.py', 'fastmcp_server.py']:
            candidate = base / server_file
            if candidate.exists():
                try:
                    content = candidate.read_text(encoding='utf-8', errors='ignore')
                    if tool_pattern.search(content):
                        has_server_tools = True
                        break
                except Exception:
                    pass  # Non-critical file read error
        if has_server_tools:
            break
    
    if tools_dir and tools_dir.exists():
        for py_file in tools_dir.glob('*.py'):
            if py_file.name != '__init__.py':
                try:
                    content = py_file.read_text(encoding='utf-8', errors='ignore')
                    if tool_pattern.search(content):
                        has_tools_dir_tools = True
                        break
                except Exception:
                    pass  # Non-critical file read error
    
    if has_server_tools and has_tools_dir_tools:
        info["runt_reasons"].append("Tools split between server.py and tools/ (incomplete refactor)")
        info["issues"].append("Split tools (server.py + tools/)")
        info["recommendations"].append("Move all tools to tools/ directory, keep server.py clean")

    # Check CI
    workflows_dir = repo_path / ".github" / "workflows"
    if workflows_dir.exists():
        info["has_ci"] = True
        info["has_cicd"] = True
        info["ci_workflows"] = len(list(workflows_dir.glob("*.yml")))
        info["cicd_count"] = info["ci_workflows"]

    # Check project structure
    has_src = (repo_path / "src").exists()
    has_tests = (repo_path / "tests").exists()
    has_scripts = (repo_path / "scripts").exists()
    
    tools_paths = [
        repo_path / "src" / pkg_name_underscore / "tools",
        repo_path / "src" / pkg_name / "tools",
        repo_path / pkg_name_underscore / "tools",
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
            info["is_runt"] = True
            info["runt_reasons"].append(f"FastMCP {fastmcp_version} is ancient")
            info["issues"].append(f"FastMCP {fastmcp_version} is ancient")
            info["recommendations"].append(f"Upgrade to FastMCP {FASTMCP_LATEST}")
        elif version_parts < warn_parts:
            info["recommendations"].append(f"Upgrade FastMCP {fastmcp_version} → {FASTMCP_LATEST}")
    except Exception:
        pass

    # Check portmanteau usage
    if portmanteau_tools == 0 and tool_count > 20:
        info["runt_reasons"].append(f"{tool_count} tools, no portmanteau pattern")
        info["issues"].append(f"{tool_count} tools, no portmanteau pattern")
        info["recommendations"].append("Consider consolidating to portmanteau tools")

    # CI check
    if not info["has_ci"]:
        if tool_count >= 10:
            info["is_runt"] = True
            info["runt_reasons"].append("No CI/CD workflows")
            info["issues"].append("No CI/CD workflows")
        info["recommendations"].append("Add CI workflow")

    # Structure checks
    if not has_src and not (repo_path / pkg_name).exists():
        info["is_runt"] = True
        info["runt_reasons"].append("No src/ directory")
        info["issues"].append("No src/ directory")
        info["recommendations"].append("Use proper src/ layout")
    
    if not has_tests and tool_count >= 10:
        info["runt_reasons"].append("No tests/ directory")
        info["issues"].append("No tests/ directory")
        info["recommendations"].append("Add tests/ with pytest")
    
    # Check for multiple server files (code smell)
    server_files = []
    for server_name in ['server.py', 'fastmcp_server.py', 'mcp_server.py', 'simple_mcp_server.py', 'mcp_compliant_server.py']:
        for base in [repo_path / "src" / pkg_name_underscore, repo_path / "src" / pkg_name, repo_path / pkg_name]:
            if (base / server_name).exists():
                server_files.append(server_name)
                break
    if len(server_files) > 1:
        info["runt_reasons"].append(f"Multiple server files: {', '.join(server_files)}")
        info["issues"].append(f"Multiple server files ({len(server_files)})")
        info["recommendations"].append("Keep only the main server file, delete obsolete ones")
    
    # Check for MCPB packaging (manifest.json)
    has_mcpb = (repo_path / "manifest.json").exists()
    has_dxt = (repo_path / "dxt").exists() or (repo_path / "dxt").is_dir() if (repo_path / "dxt").exists() else False
    info["has_mcpb"] = has_mcpb
    info["has_dxt"] = has_dxt
    
    if not has_mcpb and tool_count >= 5:
        info["runt_reasons"].append("No MCPB packaging (manifest.json)")
        info["issues"].append("No MCPB packaging")
        info["recommendations"].append("Add manifest.json for MCPB distribution")
    
    if has_dxt and not has_mcpb:
        info["runt_reasons"].append("Uses deprecated DXT instead of MCPB")
        info["issues"].append("DXT without MCPB")
        info["recommendations"].append("Migrate from DXT to MCPB (manifest.json)")
    
    # Check for README
    has_readme = any((repo_path / f).exists() for f in ['README.md', 'README.rst', 'README.txt', 'README'])
    if not has_readme:
        info["runt_reasons"].append("No README")
        info["issues"].append("No README")
        info["recommendations"].append("Add README.md with usage instructions")
    
    # Check for LICENSE
    has_license = any((repo_path / f).exists() for f in ['LICENSE', 'LICENSE.md', 'LICENSE.txt', 'COPYING'])
    if not has_license:
        info["runt_reasons"].append("No LICENSE file")
        info["issues"].append("No LICENSE")
        info["recommendations"].append("Add LICENSE file (MIT recommended)")
    
    # Check for .cursorrules
    has_cursorrules = (repo_path / ".cursorrules").exists()
    if not has_cursorrules:
        info["runt_reasons"].append("No .cursorrules")
        info["issues"].append("No .cursorrules")
        info["recommendations"].append("Add .cursorrules for Cursor AI context")
    
    # Check for git repository
    has_git = (repo_path / ".git").exists()
    if not has_git:
        info["runt_reasons"].append("No git repository")
        info["issues"].append("No .git")
        info["recommendations"].append("Initialize git: git init")
    else:
        # Check for git remote
        git_config = repo_path / ".git" / "config"
        has_remote = False
        if git_config.exists():
            try:
                config_content = git_config.read_text(encoding='utf-8', errors='ignore')
                has_remote = '[remote "origin"]' in config_content or '[remote ' in config_content
            except Exception:
                pass  # Git config read error
        if not has_remote:
            info["runt_reasons"].append("No git remote configured")
            info["issues"].append("No git remote")
            info["recommendations"].append("Add remote: git remote add origin <url>")
    
    # Check for setup.py without pyproject.toml (old packaging)
    has_setup_py = (repo_path / "setup.py").exists()
    has_pyproject = (repo_path / "pyproject.toml").exists()
    if has_setup_py and not has_pyproject:
        info["runt_reasons"].append("Uses setup.py without pyproject.toml")
        info["issues"].append("Old packaging (setup.py)")
        info["recommendations"].append("Migrate to pyproject.toml")
    
    # Check for print() statements outside tests (scan main server file)
    print_count = 0
    if monolithic_server:
        try:
            server_content = monolithic_server.read_text(encoding='utf-8', errors='ignore')
            # Count print( but not:
            # - print(file=sys.stderr) or print(..., file=
            # - console.print() (Rich console to stderr)
            # - logger.print() or similar
            import re as re_module
            prints = re_module.findall(r'(?<!\w)print\s*\(', server_content)
            stderr_prints = re_module.findall(r'print\s*\([^)]*file\s*=', server_content)
            console_prints = re_module.findall(r'console\.print\s*\(', server_content)
            print_count = len(prints) - len(stderr_prints) - len(console_prints)
        except Exception:
            pass  # Print count check failed
    if print_count > 3:
        info["runt_reasons"].append(f"{print_count} print() calls in server (use logging)")
        info["issues"].append(f"{print_count} print() statements")
        info["recommendations"].append("Replace print() with logging or print(file=sys.stderr)")
    
    # Check for oversized server file (>1000 lines)
    server_lines = 0
    if monolithic_server:
        try:
            server_lines = len(monolithic_server.read_text(encoding='utf-8', errors='ignore').splitlines())
        except Exception:
            pass  # Server file line count failed
    if server_lines > 1000:
        info["runt_reasons"].append(f"Monolithic server.py ({server_lines} lines)")
        info["issues"].append(f"Server file too large ({server_lines} lines)")
        info["recommendations"].append("Split server.py into modules (tools/, handlers/)")
    
    # Check for dual interface (stdio MCP + HTTP/FastAPI)
    has_mcp_server = False
    has_fastapi_server = False
    has_health_endpoint = False
    
    # Build comprehensive search dirs including actual src subdirectories
    dual_search_dirs = [
        repo_path / 'src' / pkg_name, 
        repo_path / 'src' / pkg_name_short, 
        repo_path / 'src' / pkg_name_underscore, 
        repo_path / pkg_name,
        repo_path / pkg_name_short, 
        repo_path
    ]
    # Add actual subdirectories under src/
    src_dir = repo_path / 'src'
    if src_dir.exists():
        for subdir in src_dir.iterdir():
            if subdir.is_dir() and not subdir.name.startswith('.') and not subdir.name.startswith('_'):
                dual_search_dirs.append(subdir)
    
    # Look for MCP server file
    mcp_server_files = ['mcp_server.py', 'fastmcp_server.py']
    for mcp_file in mcp_server_files:
        for search_dir in dual_search_dirs:
            if search_dir.exists() and (search_dir / mcp_file).exists():
                has_mcp_server = True
                break
    
    # Look for FastAPI server file (main.py, server.py with FastAPI)
    fastapi_files = ['main.py', 'server.py', 'app.py']
    for fa_file in fastapi_files:
        for search_dir in dual_search_dirs:
            if search_dir.exists():
                file_path = search_dir / fa_file
                if file_path.exists():
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        if 'FastAPI' in content or 'fastapi' in content:
                            has_fastapi_server = True
                            # Check for health endpoint
                            if '/health' in content or '@app.get("/health")' in content or "health" in content.lower():
                                has_health_endpoint = True
                            break
                    except Exception:
                        pass  # FastAPI file read error
    
    info["has_dual_interface"] = has_mcp_server and has_fastapi_server
    info["has_http_interface"] = has_fastapi_server
    info["has_health_endpoint"] = has_health_endpoint
    
    # Flag dual interface as advantage
    if has_mcp_server and has_fastapi_server:
        if has_health_endpoint:
            info["features"].append("Dual interface (stdio + HTTP)")
        else:
            info["runt_reasons"].append("HTTP interface missing /health endpoint")
            info["issues"].append("No /health endpoint")
            info["recommendations"].append("Add @app.get('/health') endpoint to FastAPI server")
    elif has_fastapi_server and not has_mcp_server and tool_count == 0:
        # Has FastAPI but no MCP tools - needs MCP server
        info["runt_reasons"].append("REST API only, no MCP tools")
        info["issues"].append("No MCP interface")
        info["recommendations"].append("Add mcp_server.py with @mcp.tool decorators")
    
    if has_nonconforming:
        if tool_count == 0 and nonconforming_count > 10:
            info["is_runt"] = True
            info["runt_reasons"].append(f"All tools non-FastMCP ({nonconforming_count}x)")
            info["issues"].append(f"All tools non-FastMCP ({nonconforming_count}x)")
        info["recommendations"].append("Use @app.tool decorators")
    
    # Check for proper multiline docstrings with Args/Returns
    proper_docstrings = 0
    if tool_count > 0:
        # Pattern matches @tool() decorator followed by def with proper docstring
        # Uses [^)]* for params and [^:]* for return type to avoid greedy matching
        docstring_pattern = re.compile(
            r'@(?:app|mcp|self\.(?:app|mcp)|server)\.tool\(\)\s*\n(?:async\s+)?def\s+\w+\([^)]*\)[^:]*:\s*\n\s*"""[\s\S]*?(?:Args:|Returns:|Examples:)[\s\S]*?"""',
            re.MULTILINE
        )
        for search_dir in dual_search_dirs:
            if search_dir.exists():
                for py_file in search_dir.rglob("*.py"):
                    if any(skip in str(py_file) for skip in SKIP_DIRS):
                        continue
                    try:
                        content = py_file.read_text(encoding='utf-8', errors='ignore')
                        matches = docstring_pattern.findall(content)
                        proper_docstrings += len(matches)
                    except Exception:
                        pass  # Docstring scan error
    
    info["has_proper_docstrings"] = proper_docstrings > 0 and proper_docstrings >= tool_count * 0.5
    if tool_count >= 3 and not info["has_proper_docstrings"]:
        info["runt_reasons"].append("Missing proper docstrings (Args/Returns)")
        info["issues"].append("Poor docstrings")
        info["recommendations"].append("Add multiline docstrings with Args, Returns, Examples sections")
    elif info["has_proper_docstrings"]:
        info["features"].append("Good docstrings")
    
    # Check for prompt templates (assets/prompts/)
    prompts_dir = repo_path / "assets" / "prompts"
    has_prompts = prompts_dir.exists() and any(prompts_dir.glob("*.md"))
    mcpb_prompts = repo_path / "mcpb" / "assets" / "prompts"
    has_mcpb_prompts = mcpb_prompts.exists() and any(mcpb_prompts.glob("*.md"))
    
    info["has_prompt_templates"] = has_prompts or has_mcpb_prompts
    if has_prompts or has_mcpb_prompts:
        prompt_count = len(list(prompts_dir.glob("*.md"))) if has_prompts else 0
        prompt_count += len(list(mcpb_prompts.glob("*.md"))) if has_mcpb_prompts else 0
        info["features"].append(f"Prompt templates ({prompt_count})")
    
    # Check for type hints usage
    has_type_hints = False
    for search_dir in dual_search_dirs:
        if search_dir.exists():
            for py_file in search_dir.rglob("*.py"):
                if any(skip in str(py_file) for skip in SKIP_DIRS):
                    continue
                try:
                    content = py_file.read_text(encoding='utf-8', errors='ignore')
                    # Check for type annotations: -> Type, : Type, List[, Dict[, Optional[
                    if re.search(r'def \w+\([^)]*:\s*\w+|-> \w+|\[[\w\[\], ]+\]', content):
                        has_type_hints = True
                        break
                except Exception:
                    pass  # Non-critical file read error
            if has_type_hints:
                break
    
    info["has_type_hints"] = has_type_hints
    if has_type_hints:
        info["features"].append("Type hints")
    
    # Check for proper logging (not just print)
    has_logging = False
    for search_dir in dual_search_dirs:
        if search_dir.exists():
            for py_file in search_dir.rglob("*.py"):
                if any(skip in str(py_file) for skip in SKIP_DIRS):
                    continue
                try:
                    content = py_file.read_text(encoding='utf-8', errors='ignore')
                    if 'import logging' in content or 'from logging' in content:
                        has_logging = True
                        break
                except Exception:
                    pass  # Non-critical file read error
            if has_logging:
                break
    
    info["has_logging"] = has_logging
    if has_logging:
        info["features"].append("Proper logging")
    
    # Check for comprehensive tests
    tests_dir = repo_path / "tests"
    test_count = 0
    if tests_dir.exists():
        test_files = list(tests_dir.rglob("test_*.py")) + list(tests_dir.rglob("*_test.py"))
        test_count = len(test_files)
    
    info["test_count"] = test_count
    if test_count >= 3:
        info["features"].append(f"Test suite ({test_count} files)")
    elif test_count == 0 and tool_count >= 5:
        info["recommendations"].append("Add tests/ directory with test files")

    # Set status
    runt_count = len(info["runt_reasons"])
    if info["is_runt"]:
        info["status_color"] = "red"
        info["status"] = "runt"
        info["status_emoji"] = "🐛"
        info["status_label"] = "Runt"
    elif runt_count > 0:
        info["status_emoji"] = "⚠️"
        info["status_color"] = "yellow"
        info["status_label"] = "Improvable"
        info["status"] = "improvable"
    else:
        info["status"] = "sota"
        info["status_emoji"] = "✅"
        info["status_label"] = "SOTA"
        info["status_color"] = "green"

    # Zoo classification
    if tool_count >= 20:
        info["zoo_class"] = "jumbo"
        info["zoo_emoji"] = "🐘"
    elif tool_count >= 10:
        info["zoo_class"] = "large"
        info["zoo_emoji"] = "🦁"
    elif tool_count >= 5:
        info["zoo_class"] = "medium"
        info["zoo_emoji"] = "🦊"
    elif tool_count >= 2:
        info["zoo_class"] = "small"
        info["zoo_emoji"] = "🐰"
    else:
        info["zoo_class"] = "chipmunk"
        info["zoo_emoji"] = "🐿️"

    return info

def scan_repos() -> List[Dict[str, Any]]:
    """Scan all repositories for MCP servers."""
    results = []
    
    if not REPOS_DIR.exists():
        return results
    
    dirs = [d for d in REPOS_DIR.iterdir() if d.is_dir() and not d.name.startswith('.')]
    state["scan_progress"]["total"] = len(dirs)
    state["scan_progress"]["status"] = "scanning"
    
    for i, repo_path in enumerate(dirs):
        state["scan_progress"]["current"] = repo_path.name
        state["scan_progress"]["done"] = i + 1
        
        try:
            # analyze_repo returns None if not MCP repo
            info = analyze_repo(repo_path)
            if info:
                results.append(info)
                log(f"  {info['zoo_emoji']} {info['status_emoji']} {info['name']} v{info['fastmcp_version'] or '?'} tools={info['tools']}")
        except Exception as e:
            logger.error(f"Error analyzing {repo_path.name}: {e}", exc_info=True)
            log(f"  ❌ {repo_path.name}: SCAN ERROR - {str(e)[:50]}")
    
    state["scan_progress"]["status"] = "complete"
    log(f"✅ Found {len(results)} MCP repos")
    
    return results

# ═══════════════════════════════════════════════════════════════════════════════
# RUNTIME - Live server connections with FastMCP
# ═══════════════════════════════════════════════════════════════════════════════

# Cache for Cursor config
_cursor_config_cache: Optional[Dict] = None

def load_cursor_config() -> Dict[str, Dict]:
    """Load Cursor MCP config from ~/.cursor/mcp.json"""
    global _cursor_config_cache
    if _cursor_config_cache is not None:
        return _cursor_config_cache
    
    cursor_config_path = Path.home() / ".cursor" / "mcp.json"
    if not cursor_config_path.exists():
        _cursor_config_cache = {}
        return _cursor_config_cache
    
    try:
        with open(cursor_config_path) as f:
            data = json.load(f)
            _cursor_config_cache = data.get("mcpServers", {})
    except Exception as e:
        log(f"⚠️ Failed to load Cursor config: {e}")
        _cursor_config_cache = {}
    
    return _cursor_config_cache

def find_cursor_config_for_repo(repo_name: str, repo_path: Path) -> Optional[Dict]:
    """Find matching Cursor MCP server config for a repository."""
    configs = load_cursor_config()
    repo_path_str = str(repo_path).replace("\\", "/").lower()
    
    # Try to match by cwd or path in args
    for server_id, config in configs.items():
        cwd = config.get("cwd", "").replace("\\", "/").lower()
        args = " ".join(config.get("args", [])).replace("\\", "/").lower()
        
        if repo_path_str in cwd or repo_path_str in args or repo_name.lower() in cwd:
            return {"id": server_id, **config}
    
    return None

def parse_pyproject_entrypoint(repo_path: Path) -> Optional[Dict]:
    """Parse pyproject.toml to find the MCP server entrypoint."""
    pyproject = repo_path / "pyproject.toml"
    if not pyproject.exists():
        return None
    
    try:
        content = pyproject.read_text()
        
        # Look for [project.scripts] section
        if "[project.scripts]" in content:
            import re
            # Match patterns like: server = "package.module:main"
            match = re.search(r'\[project\.scripts\][^\[]*?(\w+)\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL)
            if match:
                script_name, entry = match.groups()
                # Parse "package.module:main" -> "-m package.module"
                if ":" in entry:
                    module_path = entry.split(":")[0]
                    return {
                        "command": "python",
                        "args": ["-m", module_path],
                        "cwd": str(repo_path),
                        "env": {"PYTHONPATH": str(repo_path / "src")},
                        "source": "pyproject.toml"
                    }
        
        # Look for [tool.poetry.scripts]
        if "[tool.poetry.scripts]" in content:
            import re
            match = re.search(r'\[tool\.poetry\.scripts\][^\[]*?(\w+)\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL)
            if match:
                script_name, entry = match.groups()
                if ":" in entry:
                    module_path = entry.split(":")[0]
                    return {
                        "command": "python",
                        "args": ["-m", module_path],
                        "cwd": str(repo_path),
                        "env": {"PYTHONPATH": str(repo_path / "src")},
                        "source": "pyproject.toml"
                    }
    except Exception as e:
        log(f"⚠️ Failed to parse pyproject.toml for {repo_path.name}: {e}")
    
    return None

async def connect_repo_server(repo_name: str) -> Dict[str, Any]:
    """Connect to an MCP server from a repository using Cursor config or pyproject.toml."""
    repo_path = REPOS_DIR / repo_name
    
    if not repo_path.exists():
        raise HTTPException(404, f"Repository {repo_name} not found")
    
    connection_id = f"repo:{repo_name}"
    
    # Check if already connected
    if connection_id in state["connected_servers"]:
        conn = state["connected_servers"][connection_id]
        if conn.get("status") == "connected":
            return {
                "id": connection_id,
                "name": repo_name,
                "status": "connected",
                "tools": conn.get("tools", []),
            }
    
    result = {
        "id": connection_id,
        "name": repo_name,
        "status": "connecting",
        "tools": [],
        "error": None,
    }
    
    if not FASTMCP_AVAILABLE:
        result["status"] = "error"
        result["error"] = "FastMCP not installed. Install with: pip install fastmcp"
        return result
    
    try:
        # 1. Try Cursor config first (best option - has tested command/args/env)
        cursor_config = find_cursor_config_for_repo(repo_name, repo_path)
        
        # 2. Fallback to pyproject.toml
        if not cursor_config:
            cursor_config = parse_pyproject_entrypoint(repo_path)
        
        if not cursor_config:
            result["status"] = "error"
            result["error"] = f"No config found for {repo_name}. Add to Cursor mcp.json or define in pyproject.toml"
            return result
        
        # Extract config
        command = cursor_config.get("command", "python")
        args = cursor_config.get("args", [])
        cwd = cursor_config.get("cwd", str(repo_path))
        config_env = cursor_config.get("env", {})
        source = cursor_config.get("source", "cursor")
        
        log(f"🔌 Connecting to {repo_name} via {source} config...")
        log(f"   cmd: {command} {' '.join(args[:3])}{'...' if len(args) > 3 else ''}")
        
        # Prepare environment
        env = os.environ.copy()
        env.update(config_env)
        env["PYTHONUNBUFFERED"] = "1"  # Always unbuffered for stdio
        
        # Create stdio transport
        transport = StdioTransport(
            command=command,
            args=args,
            env=env,
            cwd=cwd,
        )
        
        # Create client and connect
        client = Client(transport)
        
        async with client:
            await client.initialize()
            tools = await client.list_tools()
            
            # Convert tools to dict format
            tool_list = []
            for tool in tools:
                tool_list.append({
                    "name": tool.name,
                    "description": tool.description or "No description",
                    "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                })
            
            result["status"] = "connected"
            result["tools"] = tool_list
            
            state["connected_servers"][connection_id] = {
                "status": "connected",
                "tools": tool_list,
                "config": cursor_config,
            }
            
            log(f"✅ Connected to {repo_name}: {len(tool_list)} tools")
    
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        log(f"❌ Failed to connect to {repo_name}: {e}")
    
    return result

async def connect_config_server(client: str, server_id: str, server_config: Dict) -> Dict[str, Any]:
    """Connect to an MCP server from client configuration."""
    connection_id = f"{client}:{server_id}"
    
    if connection_id in state["connected_servers"]:
        conn = state["connected_servers"][connection_id]
        if conn.get("status") == "connected":
            return {
                "id": connection_id,
                "name": server_config["name"],
                "status": "connected",
                "tools": conn.get("tools", []),
            }
    
    result = {
        "id": connection_id,
        "name": server_config["name"],
        "status": "connecting",
        "tools": [],
        "error": None,
    }
    
    if not FASTMCP_AVAILABLE:
        result["status"] = "error"
        result["error"] = "FastMCP not installed"
        return result
    
    try:
        cmd = server_config["command"]
        args = server_config.get("args", [])
        cwd = server_config.get("cwd")
        env = {**os.environ, **server_config.get("env", {})}
        
        log(f"🔌 Connecting to {server_config['name']}...")
        
        transport = StdioTransport(
            command=cmd,
            args=args,
            env=env,
            cwd=cwd,
        )
        
        client_obj = Client(transport)
        
        async with client_obj:
            await client_obj.initialize()
            tools = await client_obj.list_tools()
            
            tool_list = []
            for tool in tools:
                tool_list.append({
                    "name": tool.name,
                    "description": tool.description or "No description",
                    "inputSchema": tool.inputSchema if hasattr(tool, 'inputSchema') else {},
                })
            
            result["status"] = "connected"
            result["tools"] = tool_list
            
            state["connected_servers"][connection_id] = {
                "status": "connected",
                "tools": tool_list,
            }
            
            log(f"✅ Connected to {server_config['name']}: {len(tool_list)} tools")
    
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        log(f"❌ Failed to connect: {e}")
    
    return result

# ═══════════════════════════════════════════════════════════════════════════════
# LOGGING
# ═══════════════════════════════════════════════════════════════════════════════

def log(message: str):
    """Add a log message with timestamp."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    state["logs"].append(f"{timestamp} | {message}")
    if len(state["logs"]) > 500:
        state["logs"] = state["logs"][-500:]
    print(f"{timestamp} | {message}")

# ═══════════════════════════════════════════════════════════════════════════════
# API ENDPOINTS
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/api/clients")
async def get_discovered_clients():
    """Get all discovered MCP client configurations."""
    return discover_mcp_clients()

@app.get("/api/repos")
async def get_repo_analysis():
    """Get static analysis of all MCP repositories."""
    return scan_repos()

@app.get("/api/servers/{client}/{server_id}")
async def get_server_details(client: str, server_id: str):
    """Get details about a specific server."""
    clients = discover_mcp_clients()
    if client not in clients:
        raise HTTPException(404, f"Client {client} not found")
    
    for server in clients[client]["servers"]:
        if server["id"] == server_id:
            return server
    
    raise HTTPException(404, f"Server {server_id} not found")

@app.post("/api/servers/{client}/{server_id}/connect")
async def connect_to_server(client: str, server_id: str):
    """Connect to a server from client config and discover its tools."""
    clients = discover_mcp_clients()
    if client not in clients:
        raise HTTPException(404, f"Client {client} not found")
    
    for server in clients[client]["servers"]:
        if server["id"] == server_id:
            result = await connect_config_server(client, server_id, server)
            return result
    
    raise HTTPException(404, f"Server {server_id} not found")

@app.post("/api/repos/{repo_name}/connect")
async def connect_repo_endpoint(repo_name: str):
    """Connect to an MCP server from a repository."""
    return await connect_repo_server(repo_name)

@app.get("/api/connections")
async def list_connections():
    """List all connected servers."""
    connections = []
    for conn_id, conn in state["connected_servers"].items():
        if conn.get("status") == "connected":
            connections.append({
                "id": conn_id,
                "name": conn_id.split(":")[-1] if ":" in conn_id else conn_id,
                "tools": conn.get("tools", []),
                "tool_count": len(conn.get("tools", [])),
            })
    return {"connections": connections}

@app.get("/api/connections/{connection_id}/tools")
async def get_connection_tools(connection_id: str):
    """Get tools from a connected server."""
    if connection_id not in state["connected_servers"]:
        raise HTTPException(404, f"Connection {connection_id} not found")
    
    conn = state["connected_servers"][connection_id]
    if conn.get("status") != "connected":
        raise HTTPException(400, f"Server not connected: {conn.get('error', 'Unknown error')}")
    
    return {"tools": conn.get("tools", [])}

@app.post("/api/execute")
async def execute_tool_endpoint(request: Request):
    """Execute a tool on a server - reconnects to execute."""
    data = await request.json()
    repo_name = data.get("repo_name")
    tool_name = data.get("tool_name")
    parameters = data.get("parameters", {})
    
    if not repo_name or not tool_name:
        raise HTTPException(400, "repo_name and tool_name required")
    
    if not FASTMCP_AVAILABLE:
        raise HTTPException(503, "FastMCP not available")
    
    repo_path = REPOS_DIR / repo_name
    if not repo_path.exists():
        raise HTTPException(404, f"Repository {repo_name} not found")
    
    # Find config for this repo
    cursor_config = find_cursor_config_for_repo(repo_name, repo_path)
    if not cursor_config:
        cursor_config = parse_pyproject_entrypoint(repo_path)
    
    if not cursor_config:
        raise HTTPException(400, f"No config found for {repo_name}")
    
    try:
        command = cursor_config.get("command", "python")
        args = cursor_config.get("args", [])
        cwd = cursor_config.get("cwd", str(repo_path))
        config_env = cursor_config.get("env", {})
        
        env = os.environ.copy()
        env.update(config_env)
        env["PYTHONUNBUFFERED"] = "1"
        
        log(f"🔧 Executing {tool_name} on {repo_name}...")
        
        transport = StdioTransport(
            command=command,
            args=args,
            env=env,
            cwd=cwd,
        )
        
        client = Client(transport)
        
        async with client:
            await client.initialize()
            result = await client.call_tool(tool_name, parameters)
            
            log(f"✅ Executed {tool_name} successfully")
            
            return {
                "status": "success",
                "tool": tool_name,
                "result": result,
            }
    
    except Exception as e:
        log(f"❌ Tool execution failed: {e}")
        raise HTTPException(500, f"Execution failed: {str(e)}")

@app.get("/api/progress")
async def get_progress():
    """Get current scan progress."""
    return state["scan_progress"]

@app.get("/api/logs")
async def get_logs():
    """Get recent log messages."""
    return {"logs": state["logs"][-100:]}

@app.get("/api/ai/read-file")
async def ai_read_file(path: str):
    """Read a file from the repos directory for AI context."""
    # Security: only allow reading from REPOS_DIR
    try:
        file_path = Path(path)
        if not file_path.is_absolute():
            file_path = REPOS_DIR / path
        
        # Ensure path is within repos dir
        file_path = file_path.resolve()
        if not str(file_path).startswith(str(REPOS_DIR.resolve())):
            return {"error": "Access denied: path must be within repos directory"}
        
        if not file_path.exists():
            return {"error": f"File not found: {path}"}
        
        if file_path.is_dir():
            # List directory contents
            items = []
            for item in sorted(file_path.iterdir())[:100]:  # Limit to 100 items
                items.append({
                    "name": item.name,
                    "type": "dir" if item.is_dir() else "file",
                    "size": item.stat().st_size if item.is_file() else None
                })
            return {"type": "directory", "path": str(file_path), "items": items}
        
        # Read file (limit size)
        size = file_path.stat().st_size
        if size > 100_000:  # 100KB limit
            return {"error": f"File too large ({size} bytes). Max 100KB."}
        
        try:
            content = file_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            return {"error": "Binary file, cannot read as text"}
        
        return {"type": "file", "path": str(file_path), "content": content, "size": size}
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/ai/search-web")
async def ai_search_web(query: str, num_results: int = 5):
    """Search the web using DuckDuckGo (no API key needed)."""
    import httpx
    
    try:
        # Use DuckDuckGo HTML search (no API key required)
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
            )
            
            if resp.status_code != 200:
                return {"error": f"Search failed: {resp.status_code}"}
            
            # Parse results (simple regex extraction)
            import re
            html = resp.text
            
            results = []
            # Find result links and snippets
            pattern = r'<a rel="nofollow" class="result__a" href="([^"]+)"[^>]*>([^<]+)</a>.*?<a class="result__snippet"[^>]*>([^<]*)</a>'
            matches = re.findall(pattern, html, re.DOTALL)[:num_results]
            
            for url, title, snippet in matches:
                # Clean up URL (DuckDuckGo redirects)
                if "uddg=" in url:
                    actual_url = re.search(r'uddg=([^&]+)', url)
                    if actual_url:
                        from urllib.parse import unquote
                        url = unquote(actual_url.group(1))
                
                results.append({
                    "title": title.strip(),
                    "url": url,
                    "snippet": snippet.strip()
                })
            
            return {"query": query, "results": results, "count": len(results)}
    
    except Exception as e:
        return {"error": str(e)}

@app.get("/api/ai/list-repos")
async def ai_list_repos():
    """List all repos in the repos directory with basic info."""
    repos = []
    for item in sorted(REPOS_DIR.iterdir()):
        if item.is_dir() and not item.name.startswith('.'):
            info = {"name": item.name, "path": str(item)}
            # Check for common files
            if (item / "README.md").exists():
                info["has_readme"] = True
            if (item / "pyproject.toml").exists():
                info["type"] = "python"
            elif (item / "package.json").exists():
                info["type"] = "node"
            elif (item / "Cargo.toml").exists():
                info["type"] = "rust"
            repos.append(info)
    return {"repos": repos, "count": len(repos), "base_path": str(REPOS_DIR)}

@app.get("/api/ollama/models")
async def get_ollama_models():
    """Get list of available Ollama models."""
    import httpx
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get("http://localhost:11434/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                models = []
                for model in data.get("models", []):
                    name = model.get("name", "")
                    size_gb = model.get("size", 0) / (1024**3)
                    models.append({
                        "name": name,
                        "size": f"{size_gb:.1f}GB",
                        "modified": model.get("modified_at", "")[:10],
                        "family": model.get("details", {}).get("family", "unknown")
                    })
                return {"models": models, "count": len(models)}
            else:
                return {"models": [], "error": f"Ollama returned {resp.status_code}"}
    except Exception as e:
        return {"models": [], "error": str(e)}

@app.post("/api/ai/chat")
async def ai_chat(request: Request):
    """Chat with Ollama for AI-powered analysis with tool capabilities."""
    import httpx
    
    data = await request.json()
    model_id = data.get("model_id", "llama3.2:3b")
    message = data.get("message", "")
    include_repo_context = data.get("include_repo_context", False)
    file_path = data.get("file_path")  # Optional file to include
    web_search = data.get("web_search")  # Optional web search query
    
    if not message:
        raise HTTPException(400, "message required")
    
    log(f"🤖 AI chat with {model_id}: {message[:50]}...")
    
    # Build enhanced context
    context_parts = []
    
    # Add file content if requested
    if file_path:
        file_result = await ai_read_file(file_path)
        if "content" in file_result:
            context_parts.append(f"FILE: {file_path}\n```\n{file_result['content'][:10000]}\n```")
        elif "items" in file_result:
            items_str = "\n".join([f"  {'📁' if i['type']=='dir' else '📄'} {i['name']}" for i in file_result['items'][:50]])
            context_parts.append(f"DIRECTORY: {file_path}\n{items_str}")
    
    # Add web search results if requested
    if web_search:
        search_result = await ai_search_web(web_search)
        if "results" in search_result:
            results_str = "\n".join([f"- [{r['title']}]({r['url']}): {r['snippet']}" for r in search_result['results']])
            context_parts.append(f"WEB SEARCH for '{web_search}':\n{results_str}")
    
    # Add repo list context if requested
    if include_repo_context:
        repos_result = await ai_list_repos()
        repos_str = "\n".join([f"- {r['name']} ({r.get('type', 'unknown')})" for r in repos_result['repos'][:30]])
        context_parts.append(f"AVAILABLE REPOS in {repos_result['base_path']}:\n{repos_str}")
    
    # Build full prompt
    system_prompt = """You are an AI assistant for MCP Studio, helping analyze and manage MCP (Model Context Protocol) servers.
You have access to:
- The user's MCP repositories at D:/Dev/repos
- Web search capabilities
- File reading capabilities

When helping with code:
- Be specific and reference actual files/functions
- Suggest concrete improvements
- Follow FastMCP best practices

When the user asks about their repos, you can see the provided context."""

    full_message = message
    if context_parts:
        full_message = "\n\n".join(context_parts) + "\n\nUSER QUESTION: " + message
    
    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                "http://localhost:11434/api/chat",
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": full_message}
                    ],
                    "stream": False,
                }
            )
            
            if resp.status_code != 200:
                return {"error": f"Ollama returned {resp.status_code}: {resp.text}"}
            
            result = resp.json()
            response = result.get("message", {}).get("content", "")
            
            if not response:
                response = str(result)
            
            log(f"✅ AI response received ({len(response)} chars)")
            return {"response": response, "context_used": list(context_parts) if context_parts else None}
    
    except httpx.TimeoutException:
        log("❌ AI chat timeout")
        return {"error": "Request timed out. The model may be loading or the response is too long."}
    except Exception as e:
        log(f"❌ AI chat error: {e}")
        return {"error": str(e)}

# ═══════════════════════════════════════════════════════════════════════════════
# DASHBOARD HTML
# ═══════════════════════════════════════════════════════════════════════════════

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    """Serve the unified MCP Studio dashboard."""
    return f'''<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦁 MCP Studio - Mission Control</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {{
            darkMode: 'class',
            theme: {{
                extend: {{
                    colors: {{
                        midnight: {{ 900: '#0a0a0f', 800: '#12121a', 700: '#1a1a25' }},
                        accent: {{ 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca' }},
                        glow: {{ cyan: '#22d3ee', purple: '#a855f7', pink: '#ec4899' }}
                    }}
                }}
            }}
        }}
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=JetBrains+Mono:wght@400;600&family=Space+Grotesk:wght@400;500;600;700&display=swap');
        body {{ font-family: 'Space Grotesk', sans-serif; }}
        code, .mono {{ font-family: 'JetBrains Mono', monospace; }}
        .glass {{ background: rgba(255,255,255,0.03); backdrop-filter: blur(10px); border: 1px solid rgba(255,255,255,0.1); }}
        .glow-border {{ box-shadow: 0 0 20px rgba(99, 102, 241, 0.3), inset 0 0 20px rgba(99, 102, 241, 0.1); }}
        .card-hover {{ transition: all 0.3s ease; }}
        .card-hover:hover {{ transform: translateY(-2px); box-shadow: 0 10px 40px rgba(0,0,0,0.3); }}
        .tab-active {{ border-bottom: 2px solid #6366f1; color: #6366f1; }}
        .pulse {{ animation: pulse 2s infinite; }}
        @keyframes pulse {{ 0%, 100% {{ opacity: 1; }} 50% {{ opacity: 0.5; }} }}
        .gradient-text {{ background: linear-gradient(135deg, #6366f1, #a855f7, #ec4899); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    </style>
</head>
<body class="bg-midnight-900 text-gray-100 min-h-screen">
    <!-- Header -->
    <header class="glass sticky top-0 z-50 border-b border-white/10">
        <div class="max-w-7xl mx-auto px-6 py-4">
            <div class="flex items-center justify-between">
                <div class="flex items-center gap-4">
                    <h1 class="text-2xl font-bold gradient-text">🦁 MCP Studio</h1>
                    <span class="text-xs text-gray-500 mono">v{VERSION}</span>
                </div>
                <div class="flex items-center gap-6">
                    <div id="status-indicator" class="flex items-center gap-2 text-sm">
                        <span class="w-2 h-2 rounded-full bg-green-500 pulse"></span>
                        <span class="text-gray-400">Ready</span>
                    </div>
                    <div class="text-sm text-gray-500">
                        <span id="repo-count">0</span> repos | <span id="server-count">0</span> servers
                    </div>
                </div>
            </div>
        </div>
    </header>

    <!-- Tabs -->
    <div class="border-b border-white/10">
        <div class="max-w-7xl mx-auto px-6">
            <nav class="flex gap-8">
                <button onclick="switchTab('overview')" id="tab-overview" class="py-4 px-2 text-sm font-medium tab-active">
                    📊 Overview
                </button>
                <button onclick="switchTab('clients')" id="tab-clients" class="py-4 px-2 text-sm font-medium text-gray-400 hover:text-white">
                    🔌 MCP Clients
                </button>
                <button onclick="switchTab('repos')" id="tab-repos" class="py-4 px-2 text-sm font-medium text-gray-400 hover:text-white">
                    📦 Repositories
                </button>
                <button onclick="switchTab('tools')" id="tab-tools" class="py-4 px-2 text-sm font-medium text-gray-400 hover:text-white">
                    🔧 Tools
                </button>
                <button onclick="switchTab('console')" id="tab-console" class="py-4 px-2 text-sm font-medium text-gray-400 hover:text-white">
                    💻 Console
                </button>
                <button onclick="switchTab('ai')" id="tab-ai" class="py-4 px-2 text-sm font-medium text-gray-400 hover:text-white">
                    🤖 AI Assistant
                </button>
            </nav>
        </div>
    </div>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-6 py-8">
        <!-- Overview Tab -->
        <div id="content-overview" class="tab-content">
            <!-- Stats Grid -->
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                <div class="glass rounded-xl p-6 card-hover">
                    <div class="flex items-center gap-4">
                        <div class="w-12 h-12 rounded-lg bg-indigo-500/20 flex items-center justify-center text-2xl">🔌</div>
                        <div>
                            <div class="text-2xl font-bold" id="stat-clients">0</div>
                            <div class="text-sm text-gray-400">MCP Clients</div>
                        </div>
                    </div>
                </div>
                <div class="glass rounded-xl p-6 card-hover">
                    <div class="flex items-center gap-4">
                        <div class="w-12 h-12 rounded-lg bg-green-500/20 flex items-center justify-center text-2xl">📦</div>
                        <div>
                            <div class="text-2xl font-bold" id="stat-repos">0</div>
                            <div class="text-sm text-gray-400">MCP Repos</div>
                        </div>
                    </div>
                </div>
                <div class="glass rounded-xl p-6 card-hover">
                    <div class="flex items-center gap-4">
                        <div class="w-12 h-12 rounded-lg bg-purple-500/20 flex items-center justify-center text-2xl">🔧</div>
                        <div>
                            <div class="text-2xl font-bold" id="stat-tools">0</div>
                            <div class="text-sm text-gray-400">Total Tools</div>
                        </div>
                    </div>
                </div>
                <div class="glass rounded-xl p-6 card-hover">
                    <div class="flex items-center gap-4">
                        <div class="w-12 h-12 rounded-lg bg-cyan-500/20 flex items-center justify-center text-2xl">✅</div>
                        <div>
                            <div class="text-2xl font-bold" id="stat-sota">0</div>
                            <div class="text-sm text-gray-400">SOTA Repos</div>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Two Column Layout -->
            <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
                <!-- Discovered Clients -->
                <div class="glass rounded-xl overflow-hidden">
                    <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                        <h2 class="font-semibold">🔌 Discovered MCP Clients</h2>
                        <button onclick="loadClients()" class="text-xs text-indigo-400 hover:text-indigo-300">Refresh</button>
                    </div>
                    <div id="clients-list" class="p-4 space-y-3 max-h-96 overflow-y-auto">
                        <div class="text-gray-500 text-sm">Loading...</div>
                    </div>
                </div>

                <!-- Repo Health -->
                <div class="glass rounded-xl overflow-hidden">
                    <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                        <h2 class="font-semibold">📊 Repository Health</h2>
                        <button onclick="loadRepos()" class="text-xs text-indigo-400 hover:text-indigo-300">Scan</button>
                    </div>
                    <div id="repos-health" class="p-4 space-y-3 max-h-96 overflow-y-auto">
                        <div class="text-gray-500 text-sm">Click "Scan" to analyze repos...</div>
                    </div>
                </div>
            </div>

            <!-- Activity Log -->
            <div class="mt-8 glass rounded-xl overflow-hidden">
                <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                    <h2 class="font-semibold">📋 Activity Log</h2>
                    <span class="text-xs text-gray-500" id="log-count">0 entries</span>
                </div>
                <div id="activity-log" class="p-4 mono text-xs max-h-48 overflow-y-auto bg-black/30">
                    <div class="text-gray-500">Waiting for activity...</div>
                </div>
            </div>
        </div>

        <!-- Clients Tab -->
        <div id="content-clients" class="tab-content hidden">
            <div class="glass rounded-xl overflow-hidden">
                <div class="px-6 py-4 border-b border-white/10">
                    <h2 class="font-semibold">🔌 MCP Client Configurations</h2>
                    <p class="text-sm text-gray-400 mt-1">Servers discovered from Claude Desktop, Cursor, Windsurf, etc.</p>
                </div>
                <div id="clients-detail" class="p-6">
                    <div class="text-gray-500">Loading client configurations...</div>
                </div>
            </div>
        </div>

        <!-- Repos Tab -->
        <div id="content-repos" class="tab-content hidden">
            <div class="glass rounded-xl overflow-hidden">
                <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                    <div>
                        <h2 class="font-semibold">📦 Repository Analysis</h2>
                        <p class="text-sm text-gray-400 mt-1">Static analysis of MCP repos in {REPOS_DIR}</p>
                    </div>
                    <div class="flex gap-4">
                        <select id="repo-filter" class="bg-midnight-800 border border-white/10 rounded px-3 py-1 text-sm">
                            <option value="all">All</option>
                            <option value="sota">✅ SOTA</option>
                            <option value="improvable">⚠️ Improvable</option>
                            <option value="runt">🐛 Runts</option>
                        </select>
                        <button onclick="loadRepos()" class="px-4 py-1 bg-indigo-600 hover:bg-indigo-500 rounded text-sm">
                            🔍 Scan
                        </button>
                    </div>
                </div>
                <div id="repos-detail" class="p-6">
                    <div class="text-gray-500">Click "Scan" to analyze repositories...</div>
                </div>
            </div>
        </div>

        <!-- Tools Tab -->
        <div id="content-tools" class="tab-content hidden">
            <div class="glass rounded-xl overflow-hidden">
                <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                    <div>
                        <h2 class="font-semibold">🔧 Tool Explorer</h2>
                        <p class="text-sm text-gray-400 mt-1">Browse tools from your MCP repos</p>
                    </div>
                    <div class="flex gap-4 items-center">
                        <select id="tools-repo-select" onchange="loadRepoTools()" class="bg-midnight-800 border border-white/10 rounded-lg px-4 py-2 text-sm min-w-64">
                            <option value="">Select a repository...</option>
                        </select>
                    </div>
                </div>
                <div id="tools-detail" class="p-6">
                    <div class="text-center py-12 text-gray-500">
                        <div class="text-4xl mb-4">🔧</div>
                        <div>Select a repository above to explore its tools</div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Console Tab -->
        <div id="content-console" class="tab-content hidden">
            <div class="glass rounded-xl overflow-hidden">
                <div class="px-6 py-4 border-b border-white/10">
                    <h2 class="font-semibold">💻 Execution Console</h2>
                    <p class="text-sm text-gray-400 mt-1">Execute tools without an LLM - connect to a server first in the Tools tab</p>
                </div>
                <div class="p-6">
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div>
                            <label class="block text-sm font-medium mb-2">Connected Server</label>
                            <select id="console-server" class="w-full bg-midnight-800 border border-white/10 rounded px-3 py-2">
                                <option value="">Select a connected server...</option>
                            </select>
                            <p class="text-xs text-gray-500 mt-1">Connect to servers via the Tools tab first</p>
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Tool</label>
                            <select id="console-tool" class="w-full bg-midnight-800 border border-white/10 rounded px-3 py-2">
                                <option value="">Select a tool...</option>
                            </select>
                        </div>
                    </div>
                    
                    <!-- Tool description/schema -->
                    <div id="tool-schema" class="mt-4 hidden"></div>
                    
                    <div class="mt-6">
                        <label class="block text-sm font-medium mb-2">Parameters (JSON)</label>
                        <textarea id="console-params" class="w-full h-40 bg-midnight-800 border border-white/10 rounded px-3 py-2 mono text-sm" placeholder='{{"key": "value"}}'>{{}}</textarea>
                    </div>
                    <div class="mt-4 flex gap-4">
                        <button onclick="executeToolConsole()" class="px-6 py-2 bg-green-600 hover:bg-green-500 rounded font-medium">
                            ▶ Execute Tool
                        </button>
                        <button onclick="document.getElementById('console-result').textContent = 'Ready...'; document.getElementById('console-result').className = 'bg-black/30 rounded p-4 mono text-sm min-h-32 overflow-auto';" class="px-6 py-2 bg-gray-600 hover:bg-gray-500 rounded font-medium">
                            Clear
                        </button>
                    </div>
                    <div class="mt-6">
                        <label class="block text-sm font-medium mb-2">Result</label>
                        <pre id="console-result" class="bg-black/30 rounded p-4 mono text-sm min-h-32 max-h-96 overflow-auto">Ready...</pre>
                    </div>
                </div>
            </div>
        </div>

        <!-- AI Assistant Tab -->
        <div id="content-ai" class="tab-content hidden">
            <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">
                <!-- Left: Chat Interface -->
                <div class="lg:col-span-2 glass rounded-xl overflow-hidden flex flex-col" style="height: 90vh; min-height: 800px;">
                    <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                        <div>
                            <h2 class="font-semibold flex items-center gap-2">
                                🤖 AI Assistant
                                <span id="ai-status" class="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-400">Not Connected</span>
                            </h2>
                            <p class="text-sm text-gray-400 mt-1">Powered by Ollama</p>
                        </div>
                        <div class="flex gap-2">
                            <button onclick="clearAIChat()" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded text-sm font-medium" title="Clear chat">
                                🗑️ Clear
                            </button>
                            <button onclick="connectAI()" id="ai-connect-btn" class="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded text-sm font-medium">
                                🔌 Connect to LLM
                            </button>
                        </div>
                    </div>
                    
                    <!-- Chat Messages -->
                    <div id="ai-chat" class="flex-1 p-4 overflow-y-auto space-y-4">
                        <div class="text-center text-gray-500 py-8">
                            <div class="text-4xl mb-4">🧠</div>
                            <div>Connect to local-llm-mcp to start chatting</div>
                            <div class="text-sm mt-2">The AI can analyze your MCP repos, suggest improvements, and help with tool design</div>
                        </div>
                    </div>
                    
                    <!-- Input Area -->
                    <div class="p-4 border-t border-white/10">
                        <div class="flex gap-2">
                            <textarea id="ai-input" class="flex-1 bg-midnight-800 border border-white/10 rounded-lg px-4 py-3 text-sm resize-none" 
                                      rows="2" placeholder="Ask about your MCP servers, tools, or get suggestions..."
                                      onkeydown="if(event.key==='Enter' && !event.shiftKey){{event.preventDefault();sendAIMessage();}}"></textarea>
                            <button onclick="sendAIMessage()" class="px-6 bg-purple-600 hover:bg-purple-500 rounded-lg font-medium">
                                Send
                            </button>
                        </div>
                    </div>
                </div>
                
                <!-- Right: Quick Actions & Context -->
                <div class="space-y-6">
                    <!-- Tools Panel -->
                    <div class="glass rounded-xl overflow-hidden">
                        <div class="px-4 py-3 border-b border-white/10">
                            <h3 class="font-semibold text-sm">🛠️ AI Tools</h3>
                        </div>
                        <div class="p-4 space-y-3">
                            <div>
                                <label class="text-xs text-gray-400 flex items-center gap-2">
                                    <input type="checkbox" id="ai-include-repos" class="rounded"> Include repo list
                                </label>
                            </div>
                            <div>
                                <label class="text-xs text-gray-400">📁 Read file/folder</label>
                                <input id="ai-file-path" type="text" placeholder="repo-name/src/main.py" 
                                       class="w-full mt-1 bg-midnight-800 border border-white/10 rounded px-2 py-1 text-xs">
                            </div>
                            <div>
                                <label class="text-xs text-gray-400">🌐 Web search</label>
                                <input id="ai-web-search" type="text" placeholder="FastMCP best practices" 
                                       class="w-full mt-1 bg-midnight-800 border border-white/10 rounded px-2 py-1 text-xs">
                            </div>
                        </div>
                    </div>
                    
                    <!-- Quick Prompts -->
                    <div class="glass rounded-xl overflow-hidden">
                        <div class="px-4 py-3 border-b border-white/10">
                            <h3 class="font-semibold text-sm">⚡ Quick Prompts</h3>
                        </div>
                        <div class="p-4 space-y-2">
                            <button onclick="setAIPrompt('Analyze my MCP zoo and identify runts that need the most improvement', true)" 
                                    class="w-full text-left p-3 bg-white/5 hover:bg-white/10 rounded-lg text-sm">
                                🔍 Analyze runts
                            </button>
                            <button onclick="setAIPrompt('Suggest which tools could be combined into portmanteau patterns', true)" 
                                    class="w-full text-left p-3 bg-white/5 hover:bg-white/10 rounded-lg text-sm">
                                🔧 Suggest portmanteaus
                            </button>
                            <button onclick="setAIPrompt('Review tool naming conventions and suggest improvements', true)" 
                                    class="w-full text-left p-3 bg-white/5 hover:bg-white/10 rounded-lg text-sm">
                                📝 Review naming
                            </button>
                            <button onclick="askWithWebSearch('FastMCP 2.x best practices and patterns')" 
                                    class="w-full text-left p-3 bg-white/5 hover:bg-white/10 rounded-lg text-sm">
                                🌐 FastMCP best practices
                            </button>
                            <button onclick="setAIPrompt('Generate a summary of all my MCP servers and their capabilities', true)" 
                                    class="w-full text-left p-3 bg-white/5 hover:bg-white/10 rounded-lg text-sm">
                                📊 Zoo summary
                            </button>
                        </div>
                    </div>
                    
                    <!-- Context -->
                    <div class="glass rounded-xl overflow-hidden">
                        <div class="px-4 py-3 border-b border-white/10">
                            <h3 class="font-semibold text-sm">📋 Context</h3>
                        </div>
                        <div class="p-4 text-sm text-gray-400 space-y-2">
                            <div class="flex justify-between">
                                <span>Repos scanned:</span>
                                <span id="ai-context-repos" class="text-white">0</span>
                            </div>
                            <div class="flex justify-between">
                                <span>Total tools:</span>
                                <span id="ai-context-tools" class="text-white">0</span>
                            </div>
                            <div class="flex justify-between">
                                <span>SOTA repos:</span>
                                <span id="ai-context-sota" class="text-green-400">0</span>
                            </div>
                            <div class="flex justify-between">
                                <span>Runts:</span>
                                <span id="ai-context-runts" class="text-red-400">0</span>
                            </div>
                        </div>
                    </div>
                    
                    <!-- Model Settings -->
                    <div class="glass rounded-xl overflow-hidden">
                        <div class="px-4 py-3 border-b border-white/10 flex items-center justify-between">
                            <h3 class="font-semibold text-sm">⚙️ Model</h3>
                            <button onclick="loadOllamaModels()" class="text-xs text-purple-400 hover:text-purple-300">↻ Refresh</button>
                        </div>
                        <div class="p-4 space-y-3">
                            <div>
                                <label class="text-xs text-gray-400">Ollama Model</label>
                                <select id="ai-model" class="w-full mt-1 bg-midnight-800 border border-white/10 rounded px-3 py-2 text-sm">
                                    <option value="">Loading models...</option>
                                </select>
                            </div>
                            <div id="ai-model-info" class="text-xs text-gray-500">
                                Click Refresh to load available Ollama models
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </main>

    <!-- Detail Modal -->
    <div id="modal" class="fixed inset-0 bg-black/80 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4">
        <div class="glass rounded-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
            <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                <h2 id="modal-title" class="font-semibold text-lg">Details</h2>
                <button onclick="closeModal()" class="text-gray-400 hover:text-white text-2xl">&times;</button>
            </div>
            <div id="modal-content" class="p-6 overflow-y-auto max-h-[70vh]">
            </div>
        </div>
    </div>

    <script>
        // State
        let clientsData = {{}};
        let reposData = [];

        // Tab switching
        function switchTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('[id^="tab-"]').forEach(el => {{
                el.classList.remove('tab-active');
                el.classList.add('text-gray-400');
            }});
            document.getElementById('content-' + tabId).classList.remove('hidden');
            document.getElementById('tab-' + tabId).classList.add('tab-active');
            document.getElementById('tab-' + tabId).classList.remove('text-gray-400');
        }}

        // Load clients
        async function loadClients() {{
            try {{
                const res = await fetch('/api/clients');
                clientsData = await res.json();
                renderClients();
                updateStats();
            }} catch(e) {{
                console.error('Error loading clients:', e);
            }}
        }}

        function renderClients() {{
            const list = document.getElementById('clients-list');
            const detail = document.getElementById('clients-detail');
            
            if (Object.keys(clientsData).length === 0) {{
                list.innerHTML = '<div class="text-gray-500 text-sm">No MCP clients found</div>';
                detail.innerHTML = '<div class="text-gray-500">No MCP client configurations found</div>';
                return;
            }}

            // Compact list for overview
            let listHtml = '';
            for (const [client, data] of Object.entries(clientsData)) {{
                const icon = client.includes('claude') ? '🟣' : client.includes('cursor') ? '🔵' : '🟢';
                listHtml += `
                    <div class="flex items-center justify-between p-3 bg-white/5 rounded-lg hover:bg-white/10 cursor-pointer" onclick="showClientDetail('${{client}}')">
                        <div class="flex items-center gap-3">
                            <span class="text-lg">${{icon}}</span>
                            <div>
                                <div class="font-medium">${{client.replace('-', ' ').replace(/\\b\\w/g, l => l.toUpperCase())}}</div>
                                <div class="text-xs text-gray-400">${{data.servers.length}} servers</div>
                            </div>
                        </div>
                        <span class="text-gray-400">→</span>
                    </div>
                `;
            }}
            list.innerHTML = listHtml;

            // Detailed view
            let detailHtml = '<div class="space-y-6">';
            for (const [client, data] of Object.entries(clientsData)) {{
                const icon = client.includes('claude') ? '🟣' : client.includes('cursor') ? '🔵' : '🟢';
                detailHtml += `
                    <div class="border border-white/10 rounded-xl overflow-hidden">
                        <div class="px-4 py-3 bg-white/5 flex items-center gap-3">
                            <span class="text-xl">${{icon}}</span>
                            <div>
                                <div class="font-medium">${{client.replace('-', ' ').replace(/\\b\\w/g, l => l.toUpperCase())}}</div>
                                <div class="text-xs text-gray-400 mono">${{data.path}}</div>
                            </div>
                        </div>
                        <div class="p-4 space-y-2">
                `;
                for (const server of data.servers) {{
                    detailHtml += `
                        <div class="flex items-center justify-between p-3 bg-white/5 rounded-lg">
                            <div>
                                <div class="font-medium">${{server.name}}</div>
                                <div class="text-xs text-gray-400 mono">${{server.command}} ${{server.args.join(' ')}}</div>
                            </div>
                            <button onclick="connectServer('${{client}}', '${{server.id}}')" 
                                    class="px-3 py-1 bg-indigo-600 hover:bg-indigo-500 rounded text-xs">
                                Connect
                            </button>
                        </div>
                    `;
                }}
                detailHtml += '</div></div>';
            }}
            detailHtml += '</div>';
            detail.innerHTML = detailHtml;
        }}

        // Load repos
        async function loadRepos() {{
            document.getElementById('repos-health').innerHTML = '<div class="text-gray-400">Scanning repositories...</div>';
            document.getElementById('repos-detail').innerHTML = '<div class="text-gray-400">Scanning repositories...</div>';
            
            try {{
                const res = await fetch('/api/repos');
                reposData = await res.json();
                renderRepos();
                populateRepoSelector();
                updateStats();
                loadLogs();
            }} catch(e) {{
                console.error('Error loading repos:', e);
            }}
        }}

        function renderRepos() {{
            const health = document.getElementById('repos-health');
            const detail = document.getElementById('repos-detail');
            const filter = document.getElementById('repo-filter').value;
            
            let filtered = reposData;
            if (filter !== 'all') {{
                filtered = reposData.filter(r => r.status === filter);
            }}

            // Health summary for overview
            const sota = reposData.filter(r => r.status === 'sota').length;
            const improvable = reposData.filter(r => r.status === 'improvable').length;
            const runts = reposData.filter(r => r.status === 'runt').length;
            
            health.innerHTML = `
                <div class="grid grid-cols-3 gap-3 mb-4">
                    <div class="p-3 bg-green-500/10 rounded-lg text-center">
                        <div class="text-2xl font-bold text-green-400">${{sota}}</div>
                        <div class="text-xs text-gray-400">✅ SOTA</div>
                    </div>
                    <div class="p-3 bg-yellow-500/10 rounded-lg text-center">
                        <div class="text-2xl font-bold text-yellow-400">${{improvable}}</div>
                        <div class="text-xs text-gray-400">⚠️ Improvable</div>
                    </div>
                    <div class="p-3 bg-red-500/10 rounded-lg text-center">
                        <div class="text-2xl font-bold text-red-400">${{runts}}</div>
                        <div class="text-xs text-gray-400">🐛 Runts</div>
                    </div>
                </div>
                <div class="space-y-2">
                    ${{reposData.slice(0, 8).map(r => `
                        <div class="flex items-center justify-between p-2 bg-white/5 rounded cursor-pointer hover:bg-white/10" onclick="showRepoDetail('${{r.name}}')">
                            <div class="flex items-center gap-2">
                                <span>${{r.zoo_emoji}}</span>
                                <span>${{r.status_emoji}}</span>
                                <span class="font-medium">${{r.name}}</span>
                            </div>
                            <span class="text-xs text-gray-400">${{r.tools}} tools</span>
                        </div>
                    `).join('')}}
                    ${{reposData.length > 8 ? '<div class="text-center text-xs text-gray-500 pt-2">+' + (reposData.length - 8) + ' more...</div>' : ''}}
                </div>
            `;

            // Detailed grid
            detail.innerHTML = `
                <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    ${{filtered.map(r => `
                        <div class="p-4 bg-white/5 rounded-xl hover:bg-white/10 cursor-pointer transition-all" onclick="showRepoDetail('${{r.name}}')">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="text-xl">${{r.zoo_emoji}}</span>
                                <span class="text-xl">${{r.status_emoji}}</span>
                                <span class="font-semibold truncate">${{r.name}}</span>
                            </div>
                            <div class="text-xs text-gray-400 mb-2">FastMCP ${{r.fastmcp_version || '?'}}</div>
                            <div class="flex gap-2 text-xs">
                                <span class="px-2 py-0.5 bg-indigo-500/20 rounded">${{r.tools}} tools</span>
                                <span class="px-2 py-0.5 bg-purple-500/20 rounded">${{r.zoo_class}}</span>
                            </div>
                            ${{r.issues.length > 0 ? '<div class="mt-2 text-xs text-red-400">' + r.issues.length + ' issues</div>' : ''}}
                        </div>
                    `).join('')}}
                </div>
            `;
        }}

        function showRepoDetail(name) {{
            const repo = reposData.find(r => r.name === name);
            if (!repo) return;

            document.getElementById('modal-title').textContent = repo.zoo_emoji + ' ' + repo.name;
            document.getElementById('modal-content').innerHTML = `
                <div class="space-y-6">
                    <div class="flex items-center gap-4">
                        <span class="text-4xl">${{repo.zoo_emoji}}</span>
                        <div>
                            <div class="text-xl font-bold">${{repo.name}}</div>
                            <div class="text-sm text-gray-400">${{repo.path}}</div>
                        </div>
                        <span class="ml-auto px-3 py-1 rounded ${{repo.status === 'sota' ? 'bg-green-500/20 text-green-400' : repo.status === 'improvable' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}}">
                            ${{repo.status_emoji}} ${{repo.status_label}}
                        </span>
                    </div>
                    
                    <div class="grid grid-cols-4 gap-4">
                        <div class="p-3 bg-white/5 rounded text-center">
                            <div class="text-xl font-bold">${{repo.fastmcp_version || '?'}}</div>
                            <div class="text-xs text-gray-400">FastMCP</div>
                        </div>
                        <div class="p-3 bg-white/5 rounded text-center">
                            <div class="text-xl font-bold">${{repo.tools}}</div>
                            <div class="text-xs text-gray-400">Tools</div>
                        </div>
                        <div class="p-3 bg-white/5 rounded text-center">
                            <div class="text-xl font-bold">${{repo.portmanteau_ops}}</div>
                            <div class="text-xs text-gray-400">Operations</div>
                        </div>
                        <div class="p-3 bg-white/5 rounded text-center">
                            <div class="text-xl font-bold">${{repo.cicd_count}}</div>
                            <div class="text-xs text-gray-400">CI/CD</div>
                        </div>
                    </div>

                    <div class="flex gap-2 flex-wrap">
                        <span class="px-2 py-1 rounded text-xs ${{repo.has_src ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}}">${{repo.has_src ? '✓' : '✗'}} src/</span>
                        <span class="px-2 py-1 rounded text-xs ${{repo.has_tests ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}}">${{repo.has_tests ? '✓' : '✗'}} tests/</span>
                        <span class="px-2 py-1 rounded text-xs ${{repo.has_scripts ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}}">${{repo.has_scripts ? '✓' : '✗'}} scripts/</span>
                        <span class="px-2 py-1 rounded text-xs ${{repo.has_cicd ? 'bg-green-500/20 text-green-400' : 'bg-red-500/20 text-red-400'}}">${{repo.has_cicd ? '✓' : '✗'}} CI/CD</span>
                    </div>

                    ${{repo.issues.length > 0 ? `
                        <div>
                            <h3 class="font-semibold mb-2 text-red-400">🚨 Issues</h3>
                            <ul class="space-y-1">
                                ${{repo.issues.map(i => '<li class="text-sm text-gray-300">• ' + i + '</li>').join('')}}
                            </ul>
                        </div>
                    ` : ''}}

                    ${{repo.recommendations.length > 0 ? `
                        <div>
                            <h3 class="font-semibold mb-2 text-indigo-400">💡 Recommendations</h3>
                            <ul class="space-y-1">
                                ${{repo.recommendations.map(r => '<li class="text-sm text-gray-300">→ ' + r + '</li>').join('')}}
                            </ul>
                        </div>
                    ` : ''}}
                </div>
            `;
            document.getElementById('modal').classList.remove('hidden');
        }}

        async function connectServer(client, serverId) {{
            try {{
                const res = await fetch('/api/servers/' + client + '/' + serverId + '/connect', {{method: 'POST'}});
                const data = await res.json();
                alert('Connected! Status: ' + data.status);
            }} catch(e) {{
                alert('Connection failed: ' + e.message);
            }}
        }}

        async function loadLogs() {{
            try {{
                const res = await fetch('/api/logs');
                const data = await res.json();
                const log = document.getElementById('activity-log');
                document.getElementById('log-count').textContent = data.logs.length + ' entries';
                log.innerHTML = data.logs.map(l => '<div class="text-gray-300">' + l + '</div>').join('') || '<div class="text-gray-500">No activity</div>';
                log.scrollTop = log.scrollHeight;
            }} catch(e) {{
                console.error('Error loading logs:', e);
            }}
        }}

        function updateStats() {{
            const clientCount = Object.values(clientsData).reduce((acc, c) => acc + c.servers.length, 0);
            const toolCount = reposData.reduce((acc, r) => acc + r.tools, 0);
            const sotaCount = reposData.filter(r => r.status === 'sota').length;
            
            document.getElementById('stat-clients').textContent = Object.keys(clientsData).length;
            document.getElementById('stat-repos').textContent = reposData.length;
            document.getElementById('stat-tools').textContent = toolCount;
            document.getElementById('stat-sota').textContent = sotaCount;
            document.getElementById('repo-count').textContent = reposData.length;
            document.getElementById('server-count').textContent = clientCount;
        }}

        function closeModal() {{
            document.getElementById('modal').classList.add('hidden');
        }}

        // Populate repo selector for Tools tab
        function populateRepoSelector() {{
            const select = document.getElementById('tools-repo-select');
            if (!select || reposData.length === 0) return;
            
            select.innerHTML = '<option value="">Select a repository...</option>' +
                reposData.map(r => `<option value="${{r.name}}">${{r.zoo_emoji}} ${{r.name}} (${{r.tools}} tools)</option>`).join('');
        }}

        // Load tools for selected repo
        async function loadRepoTools() {{
            const select = document.getElementById('tools-repo-select');
            const detail = document.getElementById('tools-detail');
            const repoName = select.value;
            
            if (!repoName) {{
                detail.innerHTML = `
                    <div class="text-center py-12 text-gray-500">
                        <div class="text-4xl mb-4">🔧</div>
                        <div>Select a repository above to explore its tools</div>
                    </div>
                `;
                return;
            }}
            
            const repo = reposData.find(r => r.name === repoName);
            if (!repo) return;
            
            detail.innerHTML = `
                <div class="mb-6">
                    <div class="flex items-center gap-3 mb-4">
                        <span class="text-3xl">${{repo.zoo_emoji}}</span>
                        <div>
                            <h3 class="text-xl font-bold">${{repo.name}}</h3>
                            <p class="text-sm text-gray-400">${{repo.path}}</p>
                        </div>
                        <span class="ml-auto px-3 py-1 rounded ${{repo.status === 'sota' ? 'bg-green-500/20 text-green-400' : repo.status === 'improvable' ? 'bg-yellow-500/20 text-yellow-400' : 'bg-red-500/20 text-red-400'}}">
                            ${{repo.status_emoji}} ${{repo.status_label}}
                        </span>
                    </div>
                    <div class="grid grid-cols-4 gap-4 mb-6">
                        <div class="p-3 bg-white/5 rounded-lg text-center">
                            <div class="text-xl font-bold">${{repo.fastmcp_version || '?'}}</div>
                            <div class="text-xs text-gray-400">FastMCP</div>
                        </div>
                        <div class="p-3 bg-white/5 rounded-lg text-center">
                            <div class="text-xl font-bold">${{repo.portmanteau_tools}}</div>
                            <div class="text-xs text-gray-400">Portmanteaus</div>
                        </div>
                        <div class="p-3 bg-white/5 rounded-lg text-center">
                            <div class="text-xl font-bold">${{repo.portmanteau_ops}}</div>
                            <div class="text-xs text-gray-400">Operations</div>
                        </div>
                        <div class="p-3 bg-white/5 rounded-lg text-center">
                            <div class="text-xl font-bold">${{repo.individual_tools}}</div>
                            <div class="text-xs text-gray-400">Individual</div>
                        </div>
                    </div>
                </div>
                <div class="border-t border-white/10 pt-6">
                    <h4 class="font-semibold mb-4">📊 Tool Summary</h4>
                    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <div class="p-4 bg-indigo-500/10 rounded-lg">
                            <div class="text-2xl font-bold text-indigo-400">${{repo.tools}}</div>
                            <div class="text-sm text-gray-400">Total Tools Detected</div>
                            <div class="text-xs text-gray-500 mt-2">From static analysis of @app.tool decorators</div>
                        </div>
                        <div class="p-4 bg-purple-500/10 rounded-lg">
                            <div class="text-2xl font-bold text-purple-400">${{repo.portmanteau_ops || 0}}</div>
                            <div class="text-sm text-gray-400">Portmanteau Operations</div>
                            <div class="text-xs text-gray-500 mt-2">Actions within consolidated tools</div>
                        </div>
                    </div>
                    <div class="mt-6 flex gap-4 items-center">
                        <button onclick="connectRepo('${{repo.name}}')" 
                                class="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 rounded font-medium">
                            🔌 Connect Live
                        </button>
                        <div id="repo-connection-status-${{repo.name}}" class="text-sm text-gray-400"></div>
                    </div>
                    <div id="repo-live-tools-${{repo.name}}" class="mt-6 hidden">
                        <h4 class="font-semibold mb-4">🔴 Live Tools</h4>
                        <div id="live-tools-list-${{repo.name}}" class="space-y-2"></div>
                    </div>
                </div>
            `;
        }}

        async function connectRepo(repoName) {{
            const statusDiv = document.getElementById('repo-connection-status-' + repoName);
            const liveToolsDiv = document.getElementById('repo-live-tools-' + repoName);
            const toolsList = document.getElementById('live-tools-list-' + repoName);
            
            statusDiv.textContent = 'Connecting...';
            statusDiv.className = 'text-sm text-yellow-400';
            
            try {{
                const res = await fetch('/api/repos/' + repoName + '/connect', {{method: 'POST'}});
                const data = await res.json();
                
                if (data.status === 'connected') {{
                    statusDiv.textContent = '✅ Connected (' + data.tools.length + ' tools)';
                    statusDiv.className = 'text-sm text-green-400';
                    
                    liveToolsDiv.classList.remove('hidden');
                    toolsList.innerHTML = data.tools.map(tool => `
                        <div class="p-3 bg-white/5 rounded-lg">
                            <div class="font-medium">${{tool.name}}</div>
                            <div class="text-sm text-gray-400 mt-1">${{tool.description}}</div>
                        </div>
                    `).join('');
                }} else {{
                    statusDiv.textContent = '❌ Error: ' + (data.error || data.status);
                    statusDiv.className = 'text-sm text-red-400';
                }}
            }} catch(e) {{
                statusDiv.textContent = '❌ Failed: ' + e.message;
                statusDiv.className = 'text-sm text-red-400';
            }}
        }}

        // Filter change
        document.getElementById('repo-filter').addEventListener('change', renderRepos);

        // Close modal on escape
        document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModal(); }});

        // ═══════════════════════════════════════════════════════════════════
        // CONSOLE TAB - Tool Execution
        // ═══════════════════════════════════════════════════════════════════
        
        let consoleServers = [];
        let consoleSelectedServer = null;
        let consoleSelectedTool = null;

        async function loadConsoleServers() {{
            try {{
                const res = await fetch('/api/connections');
                const data = await res.json();
                consoleServers = data.connections || [];
                renderConsoleServers();
            }} catch(e) {{
                console.error('Error loading connections:', e);
            }}
        }}

        function renderConsoleServers() {{
            const select = document.getElementById('console-server');
            select.innerHTML = '<option value="">Select a connected server...</option>' +
                consoleServers.map(s => `<option value="${{s.id}}">${{s.name}} (${{s.tool_count}} tools)</option>`).join('');
        }}

        function onServerSelect() {{
            const select = document.getElementById('console-server');
            const serverId = select.value;
            const toolSelect = document.getElementById('console-tool');
            
            if (!serverId) {{
                consoleSelectedServer = null;
                toolSelect.innerHTML = '<option value="">Select a tool...</option>';
                document.getElementById('tool-schema').classList.add('hidden');
                return;
            }}
            
            consoleSelectedServer = consoleServers.find(s => s.id === serverId);
            if (!consoleSelectedServer) return;
            
            toolSelect.innerHTML = '<option value="">Select a tool...</option>' +
                consoleSelectedServer.tools.map(t => `<option value="${{t.name}}">${{t.name}}</option>`).join('');
        }}

        function onToolSelect() {{
            const toolSelect = document.getElementById('console-tool');
            const toolName = toolSelect.value;
            const schemaDiv = document.getElementById('tool-schema');
            const paramsInput = document.getElementById('console-params');
            
            if (!toolName || !consoleSelectedServer) {{
                consoleSelectedTool = null;
                schemaDiv.classList.add('hidden');
                return;
            }}
            
            consoleSelectedTool = consoleSelectedServer.tools.find(t => t.name === toolName);
            if (!consoleSelectedTool) return;
            
            // Show tool description and schema
            schemaDiv.innerHTML = `
                <div class="p-4 bg-white/5 rounded-lg mb-4">
                    <div class="font-semibold text-indigo-400 mb-2">${{consoleSelectedTool.name}}</div>
                    <div class="text-sm text-gray-300">${{consoleSelectedTool.description || 'No description'}}</div>
                </div>
            `;
            schemaDiv.classList.remove('hidden');
            
            // Pre-populate params with schema hint
            if (consoleSelectedTool.inputSchema && consoleSelectedTool.inputSchema.properties) {{
                const example = {{}};
                for (const [key, prop] of Object.entries(consoleSelectedTool.inputSchema.properties)) {{
                    if (prop.type === 'string') example[key] = '';
                    else if (prop.type === 'boolean') example[key] = false;
                    else if (prop.type === 'number' || prop.type === 'integer') example[key] = 0;
                    else example[key] = null;
                }}
                paramsInput.value = JSON.stringify(example, null, 2);
            }} else {{
                paramsInput.value = '{{}}';
            }}
        }}

        async function executeToolConsole() {{
            if (!consoleSelectedServer || !consoleSelectedTool) {{
                alert('Please select a server and tool first');
                return;
            }}
            
            const paramsInput = document.getElementById('console-params');
            const resultDiv = document.getElementById('console-result');
            
            let params = {{}};
            try {{
                params = JSON.parse(paramsInput.value || '{{}}');
            }} catch(e) {{
                resultDiv.textContent = 'Error: Invalid JSON in parameters';
                resultDiv.className = 'bg-red-900/30 rounded p-4 mono text-sm min-h-32 overflow-auto text-red-300';
                return;
            }}
            
            resultDiv.textContent = 'Executing...';
            resultDiv.className = 'bg-black/30 rounded p-4 mono text-sm min-h-32 overflow-auto';
            
            try {{
                const repoName = consoleSelectedServer.id.replace('repo:', '');
                const res = await fetch('/api/execute', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        repo_name: repoName,
                        tool_name: consoleSelectedTool.name,
                        parameters: params
                    }})
                }});
                
                const data = await res.json();
                
                if (res.ok) {{
                    resultDiv.textContent = JSON.stringify(data, null, 2);
                    resultDiv.className = 'bg-green-900/30 rounded p-4 mono text-sm min-h-32 overflow-auto text-green-300';
                }} else {{
                    resultDiv.textContent = 'Error: ' + (data.detail || JSON.stringify(data));
                    resultDiv.className = 'bg-red-900/30 rounded p-4 mono text-sm min-h-32 overflow-auto text-red-300';
                }}
            }} catch(e) {{
                resultDiv.textContent = 'Error: ' + e.message;
                resultDiv.className = 'bg-red-900/30 rounded p-4 mono text-sm min-h-32 overflow-auto text-red-300';
            }}
        }}

        // Wire up console selects
        document.getElementById('console-server').addEventListener('change', onServerSelect);
        document.getElementById('console-tool').addEventListener('change', onToolSelect);

        // ═══════════════════════════════════════════════════════════════════
        // AI ASSISTANT TAB
        // ═══════════════════════════════════════════════════════════════════
        
        let aiConnected = false;
        let aiMessages = [];

        async function loadOllamaModels() {{
            const select = document.getElementById('ai-model');
            const info = document.getElementById('ai-model-info');
            
            select.innerHTML = '<option value="">Loading...</option>';
            info.textContent = 'Fetching from Ollama...';
            
            try {{
                const res = await fetch('/api/ollama/models');
                const data = await res.json();
                
                if (data.error) {{
                    select.innerHTML = '<option value="">❌ ' + data.error + '</option>';
                    info.textContent = 'Make sure Ollama is running (ollama serve)';
                    return;
                }}
                
                if (data.models.length === 0) {{
                    select.innerHTML = '<option value="">No models found</option>';
                    info.textContent = 'Run "ollama pull llama3.2" to download a model';
                    return;
                }}
                
                select.innerHTML = data.models.map(m => 
                    `<option value="${{m.name}}">${{m.name}} (${{m.size}})</option>`
                ).join('');
                
                info.innerHTML = `<span class="text-green-400">${{data.count}} models available</span>`;
            }} catch(e) {{
                select.innerHTML = '<option value="">❌ Connection failed</option>';
                info.textContent = 'Cannot connect to Ollama at localhost:11434';
            }}
        }}

        async function connectAI() {{
            const statusEl = document.getElementById('ai-status');
            const btnEl = document.getElementById('ai-connect-btn');
            const chatEl = document.getElementById('ai-chat');
            const modelSelect = document.getElementById('ai-model');
            
            statusEl.textContent = 'Checking Ollama...';
            statusEl.className = 'text-xs px-2 py-0.5 rounded bg-yellow-600 text-yellow-100';
            btnEl.disabled = true;
            
            try {{
                // Check Ollama is running
                const res = await fetch('/api/ollama/models');
                const data = await res.json();
                
                if (data.error) {{
                    throw new Error(data.error);
                }}
                
                if (data.models.length === 0) {{
                    throw new Error('No models loaded in Ollama');
                }}
                
                aiConnected = true;
                const selectedModel = modelSelect.value || data.models[0].name;
                statusEl.textContent = 'Ready (' + data.count + ' models)';
                statusEl.className = 'text-xs px-2 py-0.5 rounded bg-green-600 text-green-100';
                btnEl.textContent = '✓ Connected';
                btnEl.className = 'px-4 py-2 bg-green-600 rounded text-sm font-medium cursor-default';
                
                chatEl.innerHTML = `
                    <div class="flex gap-3">
                        <div class="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-sm">🤖</div>
                        <div class="flex-1 bg-white/5 rounded-lg p-4">
                            <div class="font-medium text-purple-400 mb-1">AI Assistant</div>
                            <div class="text-gray-300">Connected to Ollama with ${{data.count}} models! Using <strong>${{selectedModel}}</strong>. I can help you analyze your MCP zoo, suggest improvements, and answer questions about your servers. What would you like to know?</div>
                        </div>
                    </div>
                `;
                
                updateAIContext();
            }} catch(e) {{
                statusEl.textContent = 'Error: ' + e.message;
                statusEl.className = 'text-xs px-2 py-0.5 rounded bg-red-600 text-red-100';
                btnEl.disabled = false;
            }}
        }}

        function updateAIContext() {{
            document.getElementById('ai-context-repos').textContent = reposData.length;
            document.getElementById('ai-context-tools').textContent = reposData.reduce((acc, r) => acc + r.tools, 0);
            document.getElementById('ai-context-sota').textContent = reposData.filter(r => r.status === 'sota').length;
            document.getElementById('ai-context-runts').textContent = reposData.filter(r => r.status === 'runt').length;
        }}

        function setAIPrompt(text, includeRepos = false) {{
            document.getElementById('ai-input').value = text;
            document.getElementById('ai-include-repos').checked = includeRepos;
        }}
        
        function askWithWebSearch(searchQuery) {{
            document.getElementById('ai-web-search').value = searchQuery;
            document.getElementById('ai-input').value = 'Based on the web search results, summarize the key points and how they apply to my MCP projects.';
        }}

        function clearAIChat() {{
            const chatEl = document.getElementById('ai-chat');
            chatEl.innerHTML = `
                <div class="text-center text-gray-500 py-8">
                    <div class="text-4xl mb-4">🧠</div>
                    <div>Chat cleared</div>
                    <div class="text-sm mt-2">Start a new conversation with the AI</div>
                </div>
            `;
            aiMessages = [];
        }}

        function addChatMessage(role, content) {{
            const chatEl = document.getElementById('ai-chat');
            const isUser = role === 'user';
            
            const msgHtml = `
                <div class="flex gap-3 ${{isUser ? 'justify-end' : ''}}">
                    ${{isUser ? '' : '<div class="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-sm">🤖</div>'}}
                    <div class="flex-1 ${{isUser ? 'max-w-[80%]' : ''}} ${{isUser ? 'bg-indigo-600' : 'bg-white/5'}} rounded-lg p-4">
                        ${{isUser ? '' : '<div class="font-medium text-purple-400 mb-1">AI Assistant</div>'}}
                        <div class="text-gray-${{isUser ? '100' : '300'}} whitespace-pre-wrap">${{content}}</div>
                    </div>
                    ${{isUser ? '<div class="w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-sm">👤</div>' : ''}}
                </div>
            `;
            
            chatEl.insertAdjacentHTML('beforeend', msgHtml);
            chatEl.scrollTop = chatEl.scrollHeight;
        }}

        async function sendAIMessage() {{
            if (!aiConnected) {{
                alert('Please connect to Ollama first');
                return;
            }}
            
            const input = document.getElementById('ai-input');
            const message = input.value.trim();
            if (!message) return;
            
            // Get tool options
            const includeRepos = document.getElementById('ai-include-repos').checked;
            const filePath = document.getElementById('ai-file-path').value.trim();
            const webSearch = document.getElementById('ai-web-search').value.trim();
            
            // Show what tools are being used
            let toolsUsed = [];
            if (includeRepos) toolsUsed.push('📁 repos');
            if (filePath) toolsUsed.push('📄 ' + filePath);
            if (webSearch) toolsUsed.push('🌐 ' + webSearch);
            
            const userMsg = toolsUsed.length > 0 
                ? message + '\\n\\n<span class="text-xs text-gray-500">Tools: ' + toolsUsed.join(', ') + '</span>'
                : message;
            
            input.value = '';
            document.getElementById('ai-file-path').value = '';
            document.getElementById('ai-web-search').value = '';
            document.getElementById('ai-include-repos').checked = false;
            
            addChatMessage('user', userMsg);
            
            // Add thinking indicator
            const chatEl = document.getElementById('ai-chat');
            const thinkingId = 'thinking-' + Date.now();
            const thinkingText = toolsUsed.length > 0 
                ? 'Gathering context... (' + toolsUsed.join(', ') + ')'
                : 'Thinking...';
            chatEl.insertAdjacentHTML('beforeend', `
                <div id="${{thinkingId}}" class="flex gap-3">
                    <div class="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-sm">🤖</div>
                    <div class="flex-1 bg-white/5 rounded-lg p-4">
                        <div class="font-medium text-purple-400 mb-1">AI Assistant</div>
                        <div class="text-gray-400 flex items-center gap-2">
                            <span class="animate-pulse">●</span> ${{thinkingText}}
                        </div>
                    </div>
                </div>
            `);
            chatEl.scrollTop = chatEl.scrollHeight;
            
            try {{
                // Build context about the MCP zoo
                const context = buildZooContext();
                const fullPrompt = context + '\\n\\nUser question: ' + message;
                
                const modelId = document.getElementById('ai-model').value;
                
                const res = await fetch('/api/ai/chat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        model_id: modelId,
                        message: fullPrompt,
                        include_repo_context: includeRepos,
                        file_path: filePath || null,
                        web_search: webSearch || null
                    }})
                }});
                
                const data = await res.json();
                
                // Remove thinking indicator
                document.getElementById(thinkingId)?.remove();
                
                if (data.response) {{
                    addChatMessage('assistant', data.response);
                }} else if (data.error) {{
                    addChatMessage('assistant', '❌ Error: ' + data.error);
                }} else {{
                    addChatMessage('assistant', JSON.stringify(data, null, 2));
                }}
            }} catch(e) {{
                document.getElementById(thinkingId)?.remove();
                addChatMessage('assistant', '❌ Error: ' + e.message);
            }}
        }}

        function buildZooContext() {{
            if (reposData.length === 0) return 'No MCP repositories have been scanned yet.';
            
            const sota = reposData.filter(r => r.status === 'sota');
            const improvable = reposData.filter(r => r.status === 'improvable');
            const runts = reposData.filter(r => r.status === 'runt');
            const totalTools = reposData.reduce((acc, r) => acc + r.tools, 0);
            
            let context = `You are an AI assistant helping analyze an MCP (Model Context Protocol) server zoo.

MCP ZOO SUMMARY:
- Total repositories: ${{reposData.length}}
- Total tools: ${{totalTools}}
- SOTA (excellent): ${{sota.length}} repos
- Improvable: ${{improvable.length}} repos
- Runts (need work): ${{runts.length}} repos

SOTA REPOS: ${{sota.map(r => r.name + ' (' + r.tools + ' tools)').join(', ') || 'none'}}

RUNTS (need improvement): ${{runts.map(r => r.name + ' - issues: ' + r.issues.join(', ')).join('; ') || 'none'}}

TOP REPOS BY TOOLS:
${{reposData.sort((a,b) => b.tools - a.tools).slice(0, 10).map(r => '- ' + r.name + ': ' + r.tools + ' tools, FastMCP ' + (r.fastmcp_version || '?') + ', status: ' + r.status).join('\\n')}}

Please provide helpful, specific advice about MCP server development, tool design, and best practices.`;
            
            return context;
        }}

        // Initial load
        loadClients();
        loadOllamaModels();  // Load available models
        setInterval(loadLogs, 5000);
        setInterval(loadConsoleServers, 3000);
        setInterval(updateAIContext, 5000);  // Keep AI context updated
    </script>
</body>
</html>'''

# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print(f"""
╔══════════════════════════════════════════════════════════════════╗
║  🦁 MCP Studio v{VERSION}                                          ║
║  Mission Control for the MCP Zoo 🐘🦒🐿️                           ║
╠══════════════════════════════════════════════════════════════════╣
║  Dashboard: http://localhost:{PORT}                                ║
║  API Docs:  http://localhost:{PORT}/docs                           ║
╚══════════════════════════════════════════════════════════════════╝
""")
    
    log("🚀 Starting MCP Studio...")
    log(f"📂 Repos directory: {REPOS_DIR}")
    
    if FASTMCP_AVAILABLE:
        log("✅ FastMCP available - live connections enabled")
    else:
        log("⚠️  FastMCP not available - install with: pip install fastmcp")
        log("   Live server connections will be disabled")
    
    # Discover clients on startup
    clients = discover_mcp_clients()
    for client, data in clients.items():
        log(f"🔌 Found {client}: {len(data['servers'])} servers")
    
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")

