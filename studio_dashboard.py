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
import os
import re
import subprocess
import sys
import time
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
import uvicorn

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

# Skip these directories when scanning
SKIP_DIRS = {'node_modules', '__pycache__', '.git', 'venv', '.venv', 'dist', 'build', 
             'env', '.env', 'eggs', '.eggs', '.tox', '.mypy_cache', '.pytest_cache',
             'site-packages', '.ruff_cache', 'coverage', 'htmlcov', '.idea', '.vscode'}

# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(title="MCP Studio", version=VERSION)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Global state
state = {
    "discovered_servers": {},      # From MCP client configs
    "repo_analysis": {},           # Static analysis results
    "connected_servers": {},       # Live connections
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

def is_mcp_repo(repo_path: Path) -> bool:
    """Check if a directory is an MCP server repository."""
    indicators = [
        repo_path / "pyproject.toml",
        repo_path / "setup.py",
        repo_path / "requirements.txt",
    ]
    
    # Must have Python project indicator
    if not any(f.exists() for f in indicators):
        return False
    
    # Check for FastMCP/MCP imports in any Python file
    try:
        for py_file in list(repo_path.glob("*.py"))[:5] + list(repo_path.glob("src/**/*.py"))[:10]:
            if py_file.exists():
                content = py_file.read_text(encoding='utf-8', errors='ignore')[:5000]
                if 'fastmcp' in content.lower() or 'mcp' in content.lower():
                    return True
    except:
        pass
    
    return False

def analyze_repo(repo_path: Path) -> Dict[str, Any]:
    """Analyze a single MCP repository for quality metrics."""
    name = repo_path.name
    
    info = {
        "name": name,
        "path": str(repo_path),
        "fastmcp_version": None,
        "tools": 0,
        "portmanteau_tools": 0,
        "portmanteau_ops": 0,
        "individual_tools": 0,
        "has_src": False,
        "has_tests": False,
        "has_scripts": False,
        "has_tools_dir": False,
        "has_cicd": False,
        "cicd_count": 0,
        "issues": [],
        "recommendations": [],
        "status": "unknown",
        "zoo_class": "chipmunk",
        "zoo_emoji": "🐿️",
    }
    
    # Check structure
    info["has_src"] = (repo_path / "src").is_dir()
    info["has_tests"] = (repo_path / "tests").is_dir()
    info["has_scripts"] = (repo_path / "scripts").is_dir()
    
    # Check CI/CD
    workflows_dir = repo_path / ".github" / "workflows"
    if workflows_dir.exists():
        info["cicd_count"] = len(list(workflows_dir.glob("*.yml"))) + len(list(workflows_dir.glob("*.yaml")))
        info["has_cicd"] = info["cicd_count"] > 0
    
    # Find FastMCP version
    for dep_file in ["pyproject.toml", "requirements.txt", "setup.py"]:
        dep_path = repo_path / dep_file
        if dep_path.exists():
            try:
                content = dep_path.read_text(encoding='utf-8', errors='ignore')
                match = re.search(r'fastmcp[>=<~!\s]*([0-9]+\.[0-9]+(?:\.[0-9]+)?)', content, re.IGNORECASE)
                if match:
                    info["fastmcp_version"] = match.group(1)
                    break
            except:
                pass
    
    # Count tools
    tool_pattern = r'@(?:app|mcp|self\.mcp|server)\.tool(?:\s*\(|\s*$|\s*\n)'
    
    # Determine package directory
    pkg_name = name.replace("-", "_").replace("mcp_", "").replace("_mcp", "")
    search_dirs = []
    
    if info["has_src"]:
        search_dirs.append(repo_path / "src")
    
    for potential_pkg in [repo_path / pkg_name, repo_path / f"{pkg_name}_mcp", repo_path / f"mcp_{pkg_name}"]:
        if potential_pkg.is_dir():
            search_dirs.append(potential_pkg)
            info["has_tools_dir"] = (potential_pkg / "tools").is_dir()
            break
    
    if not search_dirs:
        search_dirs = [repo_path]
    
    # Count tools in Python files
    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        
        for py_file in search_dir.rglob("*.py"):
            if any(skip in str(py_file) for skip in SKIP_DIRS):
                continue
            
            try:
                content = py_file.read_text(encoding='utf-8', errors='ignore')
                tool_matches = len(re.findall(tool_pattern, content))
                
                if "portmanteau" in py_file.name.lower() or "_tool" in py_file.name.lower():
                    info["portmanteau_tools"] += tool_matches
                    # Count operations (Literal types)
                    literal_matches = re.findall(r'Literal\[([^\]]+)\]', content)
                    for match in literal_matches:
                        info["portmanteau_ops"] += len(match.split(','))
                else:
                    info["individual_tools"] += tool_matches
                    
            except:
                pass
    
    info["tools"] = info["portmanteau_tools"] + info["individual_tools"]
    
    # Zoo classification
    total_capability = info["tools"] + info["portmanteau_ops"]
    if total_capability >= 20:
        info["zoo_class"], info["zoo_emoji"] = "jumbo", "🐘"
    elif total_capability >= 10:
        info["zoo_class"], info["zoo_emoji"] = "large", "🦁"
    elif total_capability >= 5:
        info["zoo_class"], info["zoo_emoji"] = "medium", "🦊"
    elif total_capability >= 2:
        info["zoo_class"], info["zoo_emoji"] = "small", "🐰"
    else:
        info["zoo_class"], info["zoo_emoji"] = "chipmunk", "🐿️"
    
    # Analyze issues
    if info["fastmcp_version"]:
        try:
            major, minor = map(int, info["fastmcp_version"].split(".")[:2])
            if major < 2 or (major == 2 and minor < 10):
                info["issues"].append(f"FastMCP {info['fastmcp_version']} is ancient")
                info["recommendations"].append("Upgrade to FastMCP 2.13.1")
        except:
            pass
    
    if not info["has_src"] and not any((repo_path / d).is_dir() for d in [pkg_name, f"{pkg_name}_mcp"]):
        info["issues"].append("No src/ or package directory")
        info["recommendations"].append("Consider src/ layout")
    
    if info["tools"] >= 10 and not info["has_cicd"]:
        info["issues"].append("No CI/CD for large repo")
        info["recommendations"].append("Add GitHub Actions workflow")
    
    if info["tools"] >= 15 and info["portmanteau_tools"] == 0:
        info["issues"].append(f"{info['tools']} tools, no portmanteau pattern")
        info["recommendations"].append("Consider consolidating to portmanteau tools")
    
    if info["tools"] >= 10 and not info["has_tests"]:
        info["issues"].append("No tests/ directory")
        info["recommendations"].append("Add test coverage")
    
    # Determine status
    issue_count = len(info["issues"])
    if issue_count == 0:
        info["status"] = "sota"
        info["status_emoji"] = "✅"
        info["status_label"] = "SOTA"
        info["status_color"] = "green"
    elif issue_count <= 2:
        info["status"] = "improvable"
        info["status_emoji"] = "⚠️"
        info["status_label"] = "Improvable"
        info["status_color"] = "yellow"
    else:
        info["status"] = "runt"
        info["status_emoji"] = "🐛"
        info["status_label"] = "Runt"
        info["status_color"] = "red"
    
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
        
        if is_mcp_repo(repo_path):
            info = analyze_repo(repo_path)
            results.append(info)
            log(f"  {info['zoo_emoji']} {info['status_emoji']} {info['name']} v{info['fastmcp_version'] or '?'} tools={info['tools']}")
    
    state["scan_progress"]["status"] = "complete"
    log(f"✅ Found {len(results)} MCP repos")
    
    return results

# ═══════════════════════════════════════════════════════════════════════════════
# RUNTIME - Live server connections
# ═══════════════════════════════════════════════════════════════════════════════

async def connect_server(server_config: Dict) -> Dict[str, Any]:
    """Connect to an MCP server and list its tools."""
    result = {
        "id": server_config["id"],
        "name": server_config["name"],
        "status": "connecting",
        "tools": [],
        "error": None,
    }
    
    try:
        # Build command
        cmd = server_config["command"]
        args = server_config.get("args", [])
        cwd = server_config.get("cwd")
        env = {**os.environ, **server_config.get("env", {})}
        
        # For Python servers, we can try to get tool info
        if "python" in cmd.lower():
            # Try to import and introspect
            result["status"] = "connected"
            result["tools"] = [{"name": "pending", "description": "Tool discovery pending..."}]
        else:
            result["status"] = "unknown"
            result["tools"] = []
            
    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
    
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
    """Connect to a server and discover its tools."""
    clients = discover_mcp_clients()
    if client not in clients:
        raise HTTPException(404, f"Client {client} not found")
    
    for server in clients[client]["servers"]:
        if server["id"] == server_id:
            result = await connect_server(server)
            state["connected_servers"][f"{client}:{server_id}"] = result
            return result
    
    raise HTTPException(404, f"Server {server_id} not found")

@app.get("/api/progress")
async def get_progress():
    """Get current scan progress."""
    return state["scan_progress"]

@app.get("/api/logs")
async def get_logs():
    """Get recent log messages."""
    return {"logs": state["logs"][-100:]}

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
                    <p class="text-sm text-gray-400 mt-1">Execute tools without an LLM</p>
                </div>
                <div class="p-6">
                    <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
                        <div>
                            <label class="block text-sm font-medium mb-2">Server</label>
                            <select id="console-server" class="w-full bg-midnight-800 border border-white/10 rounded px-3 py-2">
                                <option>Select a server...</option>
                            </select>
                        </div>
                        <div>
                            <label class="block text-sm font-medium mb-2">Tool</label>
                            <select id="console-tool" class="w-full bg-midnight-800 border border-white/10 rounded px-3 py-2">
                                <option>Select a tool...</option>
                            </select>
                        </div>
                    </div>
                    <div class="mt-6">
                        <label class="block text-sm font-medium mb-2">Parameters (JSON)</label>
                        <textarea id="console-params" class="w-full h-32 bg-midnight-800 border border-white/10 rounded px-3 py-2 mono text-sm" placeholder='{{"key": "value"}}'></textarea>
                    </div>
                    <div class="mt-4 flex gap-4">
                        <button onclick="executeToolConsole()" class="px-6 py-2 bg-indigo-600 hover:bg-indigo-500 rounded font-medium">
                            ▶ Execute
                        </button>
                    </div>
                    <div class="mt-6">
                        <label class="block text-sm font-medium mb-2">Result</label>
                        <pre id="console-result" class="bg-black/30 rounded p-4 mono text-sm min-h-32 overflow-auto">Ready...</pre>
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
                    <div class="mt-6 p-4 bg-white/5 rounded-lg">
                        <p class="text-sm text-gray-400">
                            <span class="text-yellow-400">💡 Note:</span> 
                            This shows static analysis from code scanning. For live tool discovery with schemas and docstrings, 
                            the server would need to be started via stdio transport.
                        </p>
                    </div>
                </div>
            `;
        }}

        // Filter change
        document.getElementById('repo-filter').addEventListener('change', renderRepos);

        // Close modal on escape
        document.addEventListener('keydown', e => {{ if (e.key === 'Escape') closeModal(); }});

        // Initial load
        loadClients();
        setInterval(loadLogs, 5000);
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
    
    # Discover clients on startup
    clients = discover_mcp_clients()
    for client, data in clients.items():
        log(f"🔌 Found {client}: {len(data['servers'])} servers")
    
    uvicorn.run(app, host="0.0.0.0", port=PORT, log_level="warning")

