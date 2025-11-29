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

@app.post("/api/ai/chat")
async def ai_chat(request: Request):
    """Chat with local-llm-mcp for AI-powered analysis."""
    data = await request.json()
    model_id = data.get("model_id", "ollama:llama3.2")
    message = data.get("message", "")
    
    if not message:
        raise HTTPException(400, "message required")
    
    if not FASTMCP_AVAILABLE:
        raise HTTPException(503, "FastMCP not available")
    
    # Find local-llm-mcp config
    repo_path = REPOS_DIR / "local-llm-mcp"
    if not repo_path.exists():
        raise HTTPException(404, "local-llm-mcp not found in repos")
    
    cursor_config = find_cursor_config_for_repo("local-llm-mcp", repo_path)
    if not cursor_config:
        raise HTTPException(400, "local-llm-mcp not in Cursor config")
    
    try:
        command = cursor_config.get("command", "python")
        args = cursor_config.get("args", [])
        cwd = cursor_config.get("cwd", str(repo_path))
        config_env = cursor_config.get("env", {})
        
        env = os.environ.copy()
        env.update(config_env)
        env["PYTHONUNBUFFERED"] = "1"
        
        log(f"🤖 AI chat: {message[:50]}...")
        
        transport = StdioTransport(
            command=command,
            args=args,
            env=env,
            cwd=cwd,
        )
        
        client = Client(transport)
        
        async with client:
            await client.initialize()
            
            # Try chat_completion first, fall back to generate_text
            try:
                result = await client.call_tool("chat_completion", {
                    "model": model_id,
                    "messages": [{"role": "user", "content": message}],
                    "max_tokens": 2000,
                })
            except Exception:
                # Fall back to generate_text
                result = await client.call_tool("generate_text", {
                    "model": model_id,
                    "prompt": message,
                    "max_tokens": 2000,
                })
            
            # Extract response text
            if isinstance(result, dict):
                response = result.get("response") or result.get("text") or result.get("content") or str(result)
            elif isinstance(result, list) and len(result) > 0:
                first = result[0]
                if hasattr(first, 'text'):
                    response = first.text
                else:
                    response = str(first)
            else:
                response = str(result)
            
            log(f"✅ AI response received ({len(response)} chars)")
            
            return {"response": response}
    
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
                <div class="lg:col-span-2 glass rounded-xl overflow-hidden flex flex-col" style="height: 70vh;">
                    <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                        <div>
                            <h2 class="font-semibold flex items-center gap-2">
                                🤖 AI Assistant
                                <span id="ai-status" class="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-400">Not Connected</span>
                            </h2>
                            <p class="text-sm text-gray-400 mt-1">Powered by local-llm-mcp</p>
                        </div>
                        <button onclick="connectAI()" id="ai-connect-btn" class="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded text-sm font-medium">
                            🔌 Connect to LLM
                        </button>
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
                    <!-- Quick Prompts -->
                    <div class="glass rounded-xl overflow-hidden">
                        <div class="px-4 py-3 border-b border-white/10">
                            <h3 class="font-semibold text-sm">⚡ Quick Prompts</h3>
                        </div>
                        <div class="p-4 space-y-2">
                            <button onclick="setAIPrompt('Analyze my MCP zoo and identify runts that need the most improvement')" 
                                    class="w-full text-left p-3 bg-white/5 hover:bg-white/10 rounded-lg text-sm">
                                🔍 Analyze runts
                            </button>
                            <button onclick="setAIPrompt('Suggest which tools could be combined into portmanteau patterns')" 
                                    class="w-full text-left p-3 bg-white/5 hover:bg-white/10 rounded-lg text-sm">
                                🔧 Suggest portmanteaus
                            </button>
                            <button onclick="setAIPrompt('Review tool naming conventions and suggest improvements')" 
                                    class="w-full text-left p-3 bg-white/5 hover:bg-white/10 rounded-lg text-sm">
                                📝 Review naming
                            </button>
                            <button onclick="setAIPrompt('Which repos are missing tests and how should they be structured?')" 
                                    class="w-full text-left p-3 bg-white/5 hover:bg-white/10 rounded-lg text-sm">
                                🧪 Test coverage
                            </button>
                            <button onclick="setAIPrompt('Generate a summary of all my MCP servers and their capabilities')" 
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
                        <div class="px-4 py-3 border-b border-white/10">
                            <h3 class="font-semibold text-sm">⚙️ Model</h3>
                        </div>
                        <div class="p-4 space-y-3">
                            <div>
                                <label class="text-xs text-gray-400">Model ID</label>
                                <input id="ai-model" type="text" value="ollama:llama3.2" 
                                       class="w-full mt-1 bg-midnight-800 border border-white/10 rounded px-3 py-2 text-sm">
                            </div>
                            <div class="text-xs text-gray-500">
                                Examples: ollama:llama3.2, lmstudio:default, openai:gpt-4
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

        async function connectAI() {{
            const statusEl = document.getElementById('ai-status');
            const btnEl = document.getElementById('ai-connect-btn');
            const chatEl = document.getElementById('ai-chat');
            
            statusEl.textContent = 'Connecting...';
            statusEl.className = 'text-xs px-2 py-0.5 rounded bg-yellow-600 text-yellow-100';
            btnEl.disabled = true;
            
            try {{
                // Connect to local-llm-mcp
                const res = await fetch('/api/repos/local-llm-mcp/connect', {{ method: 'POST' }});
                const data = await res.json();
                
                if (data.status === 'connected') {{
                    aiConnected = true;
                    statusEl.textContent = 'Connected (' + data.tools.length + ' tools)';
                    statusEl.className = 'text-xs px-2 py-0.5 rounded bg-green-600 text-green-100';
                    btnEl.textContent = '✓ Connected';
                    btnEl.className = 'px-4 py-2 bg-green-600 rounded text-sm font-medium cursor-default';
                    
                    chatEl.innerHTML = `
                        <div class="flex gap-3">
                            <div class="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-sm">🤖</div>
                            <div class="flex-1 bg-white/5 rounded-lg p-4">
                                <div class="font-medium text-purple-400 mb-1">AI Assistant</div>
                                <div class="text-gray-300">Connected to local-llm-mcp with ${{data.tools.length}} tools! I can help you analyze your MCP zoo, suggest improvements, and answer questions about your servers. What would you like to know?</div>
                            </div>
                        </div>
                    `;
                    
                    updateAIContext();
                }} else {{
                    throw new Error(data.error || 'Connection failed');
                }}
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

        function setAIPrompt(text) {{
            document.getElementById('ai-input').value = text;
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
                alert('Please connect to local-llm-mcp first');
                return;
            }}
            
            const input = document.getElementById('ai-input');
            const message = input.value.trim();
            if (!message) return;
            
            input.value = '';
            addChatMessage('user', message);
            
            // Add thinking indicator
            const chatEl = document.getElementById('ai-chat');
            const thinkingId = 'thinking-' + Date.now();
            chatEl.insertAdjacentHTML('beforeend', `
                <div id="${{thinkingId}}" class="flex gap-3">
                    <div class="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-sm">🤖</div>
                    <div class="flex-1 bg-white/5 rounded-lg p-4">
                        <div class="font-medium text-purple-400 mb-1">AI Assistant</div>
                        <div class="text-gray-400 flex items-center gap-2">
                            <span class="animate-pulse">●</span> Thinking...
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
                        message: fullPrompt
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

