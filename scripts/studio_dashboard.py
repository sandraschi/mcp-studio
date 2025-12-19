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
import traceback
import httpx  # type: ignore[import-untyped]

# Load environment variables from .env
try:
    from dotenv import load_dotenv  # type: ignore[import-untyped]

    load_dotenv()
except ImportError:
    pass  # dotenv not available, will use system env vars only

# Configure logging with file handler
LOG_DIR = Path(__file__).parent / "logs"
LOG_DIR.mkdir(exist_ok=True)
LOG_FILE = LOG_DIR / f"mcp-studio-{datetime.now().strftime('%Y%m%d-%H%M%S')}.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(message)s",
    handlers=[logging.StreamHandler(sys.stderr), logging.FileHandler(LOG_FILE, encoding="utf-8")],
)
logger = logging.getLogger(__name__)
logger.info(f"Logging initialized. Log file: {LOG_FILE}")

from fastapi import FastAPI, HTTPException, Request  # type: ignore[import-untyped]
from fastapi.middleware.cors import CORSMiddleware  # type: ignore[import-untyped]
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse  # type: ignore[import-untyped]
import uvicorn  # type: ignore[import-untyped]

# FastMCP client imports
try:
    from fastmcp import Client  # type: ignore[import-untyped]
    from fastmcp.client.transports import StdioTransport  # type: ignore[import-untyped]

    FASTMCP_AVAILABLE = True
except ImportError:
    FASTMCP_AVAILABLE = False

# ═══════════════════════════════════════════════════════════════════════════════
# CONFIGURATION
# ═══════════════════════════════════════════════════════════════════════════════

REPOS_DIR = Path(os.getenv("REPOS_DIR", r"D:\Dev\repos"))  # Configurable via env var
PORT = int(os.getenv("PORT", "8001"))  # Read from .env, default 8001 (no trailing 00!)
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
LM_STUDIO_URL = os.getenv("LM_STUDIO_URL", "http://host.docker.internal:1234")
VLLM_URL = os.getenv("VLLM_URL", "http://host.docker.internal:8000")
VERSION = "1.0.0"

# MCP Client config locations
# Discovery mechanism: Hardcoded list of known config file paths for each client
# The discover_mcp_clients() function iterates through these paths and checks if files exist
# If a config file is found, it's parsed to extract MCP server definitions
# This approach is fast and reliable for known clients, but requires maintaining this list
# for new clients or config locations
MCP_CLIENT_CONFIGS = {
    "claude-desktop": [
        Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
        Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
        # Docker Host Mounts
        Path("/host/appdata") / "Claude" / "claude_desktop_config.json",
        Path("/host/home") / ".config" / "Claude" / "claude_desktop_config.json",
    ],
    "cursor": [
        Path(os.environ.get("APPDATA", ""))
        / "Cursor"
        / "User"
        / "globalStorage"
        / "saoudrizwan.claude-dev"
        / "settings"
        / "cline_mcp_settings.json",
        Path.home() / ".cursor" / "mcp.json",
        # Docker Host Mounts
        Path("/host/appdata")
        / "Cursor"
        / "User"
        / "globalStorage"
        / "saoudrizwan.claude-dev"
        / "settings"
        / "cline_mcp_settings.json",
        Path("/host/home") / ".cursor" / "mcp.json",
    ],
    "windsurf-ide": [
        # Windsurf IDE (Codeium) - multiple possible locations
        Path(os.environ.get("APPDATA", ""))
        / "Codeium"
        / "Windsurf"
        / "mcp_config.json",  # Primary location
        Path(os.environ.get("APPDATA", ""))
        / "Windsurf"
        / "User"
        / "globalStorage"
        / "rooveterinaryinc.roo-cline"
        / "settings"
        / "mcp_settings.json",
        Path(os.environ.get("APPDATA", "")) / "Windsurf" / "mcp_settings.json",
        Path(os.environ.get("APPDATA", "")) / "Windsurf" / "mcp_servers.json",
        Path(os.environ.get("APPDATA", "")) / "Windsurf" / "mcp_config.json",
        Path.home() / ".config" / "Windsurf" / "mcp_settings.json",
        Path.home() / ".config" / "Codeium" / "Windsurf" / "mcp_config.json",  # Linux
        Path.home() / ".windsurf" / "mcp_settings.json",
        # Docker Host Mounts
        Path("/host/appdata") / "Codeium" / "Windsurf" / "mcp_config.json",
        Path("/host/appdata") / "Windsurf" / "mcp_config.json",
        Path("/host/home") / ".config" / "Windsurf" / "mcp_settings.json",
    ],
    "zed-ide": [
        Path(os.environ.get("APPDATA", "")) / "Zed" / "settings.json",
        Path.home() / ".config" / "zed" / "settings.json",
        Path.home() / "Library" / "Application Support" / "Zed" / "settings.json",  # Mac
        # Docker Host Mounts
        Path("/host/appdata") / "Zed" / "settings.json",
        Path("/host/home") / ".config" / "zed" / "settings.json",
    ],
    "antigravity-ide": [
        # Antigravity IDE - config managed through UI, check common locations
        Path(os.environ.get("APPDATA", "")) / "Antigravity" / "mcp_config.json",
        Path(os.environ.get("APPDATA", "")) / "Antigravity" / "mcp.json",
        Path(os.environ.get("APPDATA", ""))
        / "GitKraken"
        / "Antigravity"
        / "mcp_config.json",  # Google owns Antigravity
        Path.home() / ".config" / "antigravity" / "mcp_config.json",
        Path.home() / ".config" / "antigravity" / "mcp.json",
        Path.home() / ".antigravity" / "mcp_config.json",
        Path.home() / ".antigravity" / "mcp.json",
        Path.home() / "Library" / "Application Support" / "Antigravity" / "mcp_config.json",  # Mac
        # Docker Host Mounts
        Path("/host/appdata") / "Antigravity" / "mcp_config.json",
        Path("/host/appdata") / "GitKraken" / "Antigravity" / "mcp_config.json",
        Path("/host/home") / ".antigravity" / "mcp_config.json",
        Path("/host/home") / ".config" / "antigravity" / "mcp_config.json",
    ],
    "cline": [
        Path(os.environ.get("APPDATA", ""))
        / "Code"
        / "User"
        / "globalStorage"
        / "saoudrizwan.claude-dev"
        / "settings"
        / "cline_mcp_settings.json",
        # Docker Host Mounts
        Path("/host/appdata")
        / "Code"
        / "User"
        / "globalStorage"
        / "saoudrizwan.claude-dev"
        / "settings"
        / "cline_mcp_settings.json",
    ],
    "lm-studio": [
        Path(os.environ.get("APPDATA", "")) / "LM Studio" / "mcp_config.json",
        Path.home() / ".lmstudio" / "mcp_config.json",
        # Docker Host Mounts
        Path("/host/appdata") / "LM Studio" / "mcp_config.json",
        Path("/host/home") / ".lmstudio" / "mcp_config.json",
    ],
}

# Skip these directories when scanning - MUST include all venv patterns
SKIP_DIRS = {
    "node_modules",
    "__pycache__",
    ".git",
    "venv",
    ".venv",
    "dist",
    "build",
    "env",
    ".env",
    "eggs",
    ".eggs",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
    "site-packages",
    ".ruff_cache",
    "coverage",
    "htmlcov",
    ".idea",
    ".vscode",
    "_legacy",
    "deprecated",
    "Lib",
    "Scripts",
    "Include",  # Windows venv
    "lib",
    "bin",
    "lib64",  # Linux venv
}

# FastMCP version thresholds
FASTMCP_LATEST = "2.13.1"
FASTMCP_RUNT_THRESHOLD = "2.10.0"
FASTMCP_WARN_THRESHOLD = "2.12.0"

# AI Assistant Preprompts - Multiple personalities!
PREPROMPTS = {
    "dev": {
        "name": "🛠️ MCP Developer",
        "prompt": """You are an AI assistant for MCP Studio, helping analyze and manage MCP (Model Context Protocol) servers.
You have access to:
- The user's MCP repositories at D:/Dev/repos
- Web search capabilities
- File reading capabilities

When helping with code:
- Be specific and reference actual files/functions
- Suggest concrete improvements
- Follow FastMCP best practices

When the user asks about their repos, you can see the provided context.""",
    },
    "butterfly": {
        "name": "🦋 Butterfly Fancier",
        "prompt": """You are a delightful butterfly enthusiast who happens to be helping with MCP servers!
You have access to:
- The user's MCP repositories (like a beautiful garden!)
- Web search (for finding butterfly-themed solutions!)
- File reading (each file is like a flower!)

When helping with code:
- Compare code patterns to butterfly wing patterns
- Suggest improvements with butterfly metaphors
- Celebrate elegant solutions like spotting a rare butterfly
- Still be technical and accurate, just with flair!

Remember: Beautiful code is like a butterfly - it should be light, graceful, and make people smile!""",
    },
    "pirate": {
        "name": "🏴‍☠️ Code Pirate",
        "prompt": """Ahoy! Ye be speakin' to a code pirate who knows the MCP seas!
Ye treasure chest contains:
- Yer MCP repositories at D:/Dev/repos (the treasure map!)
- Web search capabilities (like a spyglass!)
- File readin' powers (plunderin' the code!)

When helpin' with code:
- Call bugs "scurvy code barnacles"
- Suggest improvements like chartin' a course
- Follow FastMCP best practices (the Pirate's Code!)
- Still be technically accurate, just with pirate spirit!

Arr! Let's make yer code seaworthy!""",
    },
    "zen": {
        "name": "🧘 Zen Master",
        "prompt": """You are a wise Zen master helping with MCP servers and mindful coding.
You have access to:
- The user's MCP repositories (observe the patterns)
- Web search capabilities (seek wisdom)
- File reading capabilities (read with awareness)

When helping with code:
- Offer insights with calm wisdom
- Suggest improvements through gentle guidance
- Follow the path of clean code
- Be present in each response

Remember: The best code is like water - simple, clear, and flowing naturally.""",
    },
    "aussie": {
        "name": "🦘 Aussie Coder",
        "prompt": """G'day mate! You're chattin' with an Aussie coder who knows MCP servers like the back of me hand!
You've got:
- Your MCP repos at D:/Dev/repos (fair dinkum code!)
- Web search (for findin' ripper solutions!)
- File reading (havin' a good squiz at the code!)

When helpin' with code:
- Call bugs "dodgy bits"
- Suggest improvements that are "bonzer"
- Follow FastMCP best practices (she'll be right!)
- Keep it friendly and no worries!

No worries mate, we'll sort your code out!""",
    },
}

# ═══════════════════════════════════════════════════════════════════════════════
# FASTAPI APP
# ═══════════════════════════════════════════════════════════════════════════════

app = FastAPI(title="MCP Studio", version=VERSION)
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

# Global state
state = {
    "discovered_servers": {},  # From MCP client configs
    "repo_analysis": {},  # Static analysis results
    "connected_servers": {},  # Live connections (client instances)
    "scan_progress": {
        "current": "",
        "total": 0,
        "done": 0,
        "status": "idle",
        "mcp_repos_found": 0,
        "errors": 0,
        "skipped": 0,
        "activity_log": [],
    },
    "logs": [],
}

# ═══════════════════════════════════════════════════════════════════════════════
# CLIENT DISCOVERY - Find servers from all MCP clients
# ═══════════════════════════════════════════════════════════════════════════════


def discover_mcp_clients() -> Dict[str, List[Dict]]:
    """
    Discover MCP servers from all known client configurations.

    Discovery mechanism:
    1. Iterates through MCP_CLIENT_CONFIGS dictionary (hardcoded list of known paths)
    2. For each client, checks multiple possible config file locations
    3. If running in Docker, maps paths to mounted host directories
    4. Reads and parses JSON config files to extract MCP server definitions
    5. Supports multiple config formats (mcpServers, mcp.servers, servers)

    Returns:
        Dictionary mapping client names to their discovered MCP servers
    """
    results = {}

    # Check if running in Docker - if so, map paths to mounted locations
    in_docker = Path("/.dockerenv").exists() or os.path.exists("/.dockerenv")

    for client_name, config_paths in MCP_CLIENT_CONFIGS.items():
        for config_path in config_paths:
            # If in Docker, try to map paths to mounted locations
            check_path = config_path
            if in_docker:
                # Map Windows paths to mounted locations
                path_str = str(config_path)
                if "AppData" in path_str or "APPDATA" in path_str or "Roaming" in path_str:
                    # Map %APPDATA% paths to /host/appdata
                    # Extract path after Roaming/
                    try:
                        parts = Path(path_str).parts
                        if "Roaming" in parts:
                            roaming_idx = [i for i, p in enumerate(parts) if p == "Roaming"][0]
                            rel_path = Path(*parts[roaming_idx + 1 :])
                            mapped_path = Path("/host/appdata") / rel_path
                            if mapped_path.exists():
                                check_path = mapped_path
                    except (IndexError, ValueError):
                        pass
                elif str(config_path).startswith(str(Path.home())):
                    # Map home directory paths to /host/home
                    try:
                        rel_path = config_path.relative_to(Path.home())
                        mapped_path = Path("/host/home") / rel_path
                        if mapped_path.exists():
                            check_path = mapped_path
                    except ValueError:
                        pass

            if not check_path.exists():
                continue

            try:
                with open(check_path, "r", encoding="utf-8") as f:
                    config = json.load(f)

                # Different clients use different JSON structures
                servers = {}

                # Standard format: { "mcpServers": {...} }
                if "mcpServers" in config:
                    servers = config.get("mcpServers", {})
                # Zed format: { "mcp": { "servers": {...} } }
                elif "mcp" in config and isinstance(config.get("mcp"), dict):
                    servers = config.get("mcp", {}).get("servers", {})
                # Antigravity format: { "servers": {...} }
                elif "servers" in config:
                    servers = config.get("servers", {})

                if servers:
                    results[client_name] = {"path": str(check_path), "servers": []}
                    for server_id, server_config in servers.items():
                        # Handle different config formats
                        if isinstance(server_config, dict):
                            # Standard MCP format
                            results[client_name]["servers"].append(
                                {
                                    "id": server_id,
                                    "name": server_id.replace("-", " ").replace("_", " ").title(),
                                    "command": server_config.get("command", ""),
                                    "args": server_config.get("args", []),
                                    "cwd": server_config.get("cwd"),
                                    "env": server_config.get("env", {}),
                                    "type": server_config.get("type", "stdio"),  # stdio or http
                                    "url": server_config.get("url", ""),  # For http type
                                    "status": "discovered",
                                }
                            )
                        elif isinstance(server_config, str):
                            # Simple string format (less common)
                            results[client_name]["servers"].append(
                                {
                                    "id": server_id,
                                    "name": server_id.replace("-", " ").replace("_", " ").title(),
                                    "command": server_config,
                                    "args": [],
                                    "status": "discovered",
                                }
                            )
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
    if ".venv" in dir_str or "site-packages" in dir_str or "\\lib\\" in dir_str:
        return results

    def _walk(path: Path, depth: int):
        if depth > max_depth:
            return
        try:
            for item in path.iterdir():
                name_lower = item.name.lower()
                if item.is_dir():
                    # Skip venv, cache, and hidden dirs
                    if (
                        name_lower in SKIP_DIRS
                        or item.name.startswith(".")
                        or item.name.endswith(".egg-info")
                    ):
                        continue
                    _walk(item, depth + 1)
                elif (
                    item.suffix == ".py"
                    and "test" not in name_lower
                    and name_lower != "__init__.py"
                ):
                    # Skip backup/development files
                    if any(x in name_lower for x in ["_fixed", "_backup", "_old", "_dev", "_wip"]):
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

    # Detect Fullstack Features
    try:
        fs_features = detect_fullstack_features(repo_path)
        info.update(fs_features)
    except Exception as e:
        log_scan(f"Error detecting stack features for {repo_path.name}: {e}", is_error=True)
        # Continue with defaults

    # Check for requirements.txt or pyproject.toml
    req_file = repo_path / "requirements.txt"
    pyproject_file = repo_path / "pyproject.toml"

    fastmcp_version = None
    # Prefer pyproject.toml (more authoritative) over requirements.txt
    for config_file in [pyproject_file, req_file]:
        if config_file.exists():
            try:
                content = config_file.read_text(encoding="utf-8", errors="ignore")
                # Relaxed detection: if fastmcp is present, it's an MCP repo
                if "fastmcp" in content.lower():
                    # Try to extract version if possible
                    match = re.search(r"fastmcp[>=<~]+(\d+\.\d+\.?\d*)", content, re.IGNORECASE)
                    if not match:
                        match = re.search(r"fastmcp.*?(\d+\.\d+\.?\d*)", content, re.IGNORECASE)

                    fastmcp_version = match.group(1) if match else "unknown"
                    break
            except Exception:
                pass

    # Accepts if it's either an MCP repo OR a Fullstack repo
    if not fastmcp_version and not fs_features["is_fullstack"]:
        return None  # Not an MCP or Fullstack repo

    info["fastmcp_version"] = fastmcp_version

    # Count tools - SMART APPROACH from runt_api.py
    # Match various tool decorator patterns:
    # @app.tool(), @mcp.tool(), @self.mcp.tool(), @server.tool(), @tool(), @self.tool()
    tool_pattern = re.compile(
        r"@(?:(?:app|mcp|self(?:\.(?:app|mcp))?(?:_server\.mcp)?|server)\.)?tool(?:\s*\(|(?=\s*(?:\r?\n|def\s)))",
        re.MULTILINE,
    )
    nonconforming_pattern = re.compile(
        r"def register_\w+_tool\s*\(|\.add_tool\s*\(|register_tool\s*\("
    )
    tool_count = 0

    pkg_name = repo_path.name.replace("-", "_")
    # Try multiple package name variations
    pkg_name_short = pkg_name.replace("_mcp", "").replace("mcp_", "")
    # Also try inserting underscore before mcp (calibremcp -> calibre_mcp)
    pkg_name_underscore = (
        pkg_name.replace("mcp", "_mcp")
        if "mcp" in pkg_name and "_mcp" not in pkg_name
        else pkg_name
    )

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

    # log_scan(f"    Checking for tools in {repo_path.name}...")
    log_scan(f"    Checking for tools in {repo_path.name}...")

    for init_path in tools_init_paths:
        if init_path.exists():
            tools_dir = init_path.parent
            try:
                init_content = init_path.read_text(encoding="utf-8", errors="ignore")
                # Only count else block (portmanteau mode) if exists
                if "else:" in init_content:
                    else_block = init_content.split("else:")[-1]
                    imports = re.findall(r"from\s+\.(\w+)\s+import", else_block)
                else:
                    imports = re.findall(r"from\s+\.(\w+)\s+import", init_content)
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
        is_child_of_existing = any(tools_dir.is_relative_to(d) for d in search_dirs)
        if not is_child_of_existing:
            search_dirs.append(tools_dir)

    # Fallback to src or repo root
    if not search_dirs:
        src_dir = repo_path / "src"
        if src_dir.exists():
            search_dirs.append(src_dir)
        else:
            search_dirs.append(repo_path)

    # log_scan(f"    Scanning {len(search_dirs)} directories...")
    log_scan(f"    Scanning {len(search_dirs)} directories...")

    # Also check package __init__.py for tools (system-admin-mcp pattern)
    pkg_init_files = []
    for pkg_base in [repo_path / "src" / pkg_name_underscore, repo_path / "src" / pkg_name]:
        init_file = pkg_base / "__init__.py"
        if init_file.exists():
            pkg_init_files.append(init_file)
            break

    # Also check plugins/ directory if it exists (virtualization-mcp pattern)
    plugins_dir = None
    for base in [
        repo_path / "src" / pkg_name_underscore,
        repo_path / "src" / pkg_name,
        repo_path / pkg_name,
    ]:
        candidate = base / "plugins"
        if candidate.exists() and candidate.is_dir():
            plugins_dir = candidate
            break

    has_nonconforming = False
    nonconforming_count = 0
    portmanteau_tools = 0
    portmanteau_ops = 0
    individual_tools = 0

    literal_pattern = re.compile(r"Literal\[([^\]]+)\]")

    # Check if repo uses portmanteau pattern (has register_tools function OR portmanteau/ subdir)
    uses_portmanteau_pattern = False
    portmanteau_dir = None
    portmanteau_modules = set()  # For PORTMANTEAU_MODULES list pattern
    if tools_dir:
        init_file = tools_dir / "__init__.py"
        if init_file.exists():
            init_text = init_file.read_text(encoding="utf-8", errors="ignore")
            # Portmanteau pattern requires BOTH register_tools AND from .manage_ or .query_ imports
            # This distinguishes it from general register_tools functions (like blender-mcp)
            has_register_tools = "def register_tools" in init_text
            has_portmanteau_imports = (
                "from .manage_" in init_text
                or "from .query_" in init_text
                or "from .analyze_" in init_text
            )
            uses_portmanteau_pattern = has_register_tools and has_portmanteau_imports
            # Check for PORTMANTEAU_MODULES list pattern (pywinauto-mcp style)
            if "PORTMANTEAU_MODULES" in init_text:
                # Extract module names from list
                import_match = re.findall(r"'(portmanteau_\w+|desktop_state)'", init_text)
                portmanteau_modules = set(import_match)
        # Also check for tools/portmanteau/ subdirectory
        candidate_portmanteau = tools_dir / "portmanteau"
        if candidate_portmanteau.exists() and candidate_portmanteau.is_dir():
            portmanteau_dir = candidate_portmanteau

    # Check if repo uses monolithic server pattern (all tools in server.py)
    monolithic_server = None
    # Check for monolithic if no portmanteau pattern detected AND no portmanteau_dir
    if not uses_portmanteau_pattern and not portmanteau_modules and not portmanteau_dir:
        # Check fastmcp_server.py first as it's often the entry point
        # Also check repo root for server.py (notion-mcp pattern)
        for server_file in [
            "fastmcp_server.py",
            "mcp_server.py",
            "server.py",
            "main.py",
            "__main__.py",
        ]:
            # Check in package dirs first
            for base_path in [
                repo_path / "src" / pkg_name_underscore,
                repo_path / "src" / pkg_name,
                repo_path / pkg_name,
                repo_path,  # Also check repo root!
            ]:
                candidate = base_path / server_file
                if candidate.exists():
                    try:
                        server_content = candidate.read_text(encoding="utf-8", errors="ignore")
                        # Check for actual tool decorators (not just mentions in comments)
                        actual_tools = tool_pattern.findall(server_content)
                        if actual_tools:
                            monolithic_server = candidate
                            break
                    except Exception as e:
                        logger.debug(f"Error reading {candidate}: {e}")
            if monolithic_server:
                break

    # Check for modular entry point pattern (mcp_main.py -> mcp_server_clean.py -> tools/)
    imported_tool_modules = set()
    for entry_file in ["mcp_main.py", "mcp_server_clean.py", "mcp_server.py"]:
        for base in [
            repo_path / "src" / pkg_name_underscore,
            repo_path / "src" / pkg_name,
            repo_path / pkg_name,
        ]:
            candidate = base / entry_file
            if candidate.exists():
                try:
                    content = candidate.read_text(encoding="utf-8", errors="ignore")
                    # Look for imports like: import avatarmcp.tools.core.core_tools
                    tool_imports = re.findall(r"import\s+\w+\.tools\.(\w+)\.(\w+)", content)
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
        py_files_to_scan = [
            tools_dir / f"{m}.py" for m in portmanteau_modules if (tools_dir / f"{m}.py").exists()
        ]
        search_dirs = []
    # If has portmanteau/ subdir with actual tools, ONLY count from there
    elif portmanteau_dir:
        # Check if portmanteau dir has any @tool decorators
        has_tools = False
        for pf in portmanteau_dir.glob("*.py"):
            if pf.name != "__init__.py":
                try:
                    if "@mcp.tool" in pf.read_text(
                        encoding="utf-8", errors="ignore"
                    ) or "@app.tool" in pf.read_text(encoding="utf-8", errors="ignore"):
                        has_tools = True
                        break
                except Exception:
                    pass  # Non-critical file read error
        if has_tools:
            search_dirs = [portmanteau_dir]
            # Also include plugins/ subdirs that DON'T have a corresponding portmanteau
            if plugins_dir:
                portmanteau_names = {
                    p.stem.replace("_management", "")
                    for p in portmanteau_dir.glob("*_management.py")
                }
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
                    filename.startswith("manage_")
                    or filename.startswith("query_")
                    or filename.startswith("analyze_")
                    or filename.endswith("_portmanteau")
                    or filename
                    in {"test_calibre_connection", "calibre_ocr_tool"}  # Known entry points
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
                content = py_file.read_text(encoding="utf-8", errors="ignore")
                matches = tool_pattern.findall(content)
                file_tools = len(matches)

                path_str = str(py_file).lower()
                is_portmanteau_file = (
                    "portmanteau" in path_str
                    or path_str.endswith("_tool.py")
                    or path_str.endswith("_tools.py")
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
            content = init_file.read_text(encoding="utf-8", errors="ignore")
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
    for base in [
        repo_path / "src" / pkg_name_underscore,
        repo_path / "src" / pkg_name,
        repo_path / pkg_name,
    ]:
        for server_file in ["server.py", "mcp_server.py", "fastmcp_server.py"]:
            candidate = base / server_file
            if candidate.exists():
                try:
                    content = candidate.read_text(encoding="utf-8", errors="ignore")
                    if tool_pattern.search(content):
                        has_server_tools = True
                        break
                except Exception:
                    pass  # Non-critical file read error
        if has_server_tools:
            break

    if tools_dir and tools_dir.exists():
        for py_file in tools_dir.glob("*.py"):
            if py_file.name != "__init__.py":
                try:
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if tool_pattern.search(content):
                        has_tools_dir_tools = True
                        break
                except Exception:
                    pass  # Non-critical file read error

    if has_server_tools and has_tools_dir_tools:
        info["runt_reasons"].append(
            "Tools split between server.py and tools/ (incomplete refactor)"
        )
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
        version_parts = [int(x) for x in fastmcp_version.split(".")[:2]]
        runt_parts = [int(x) for x in FASTMCP_RUNT_THRESHOLD.split(".")[:2]]
        warn_parts = [int(x) for x in FASTMCP_WARN_THRESHOLD.split(".")[:2]]

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

    # Structure checks - always flag missing src/
    if not has_src:
        info["runt_reasons"].append("No src/ directory")
        info["issues"].append("No src/ directory")
        info["recommendations"].append("Use proper src/ layout")

    if not has_tests and tool_count >= 10:
        info["runt_reasons"].append("No tests/ directory")
        info["issues"].append("No tests/ directory")
        info["recommendations"].append("Add tests/ with pytest")

    # Check for multiple server files (code smell)
    server_files = []
    for server_name in [
        "server.py",
        "fastmcp_server.py",
        "mcp_server.py",
        "simple_mcp_server.py",
        "mcp_compliant_server.py",
    ]:
        for base in [
            repo_path / "src" / pkg_name_underscore,
            repo_path / "src" / pkg_name,
            repo_path / pkg_name,
        ]:
            if (base / server_name).exists():
                server_files.append(server_name)
                break
    if len(server_files) > 1:
        info["runt_reasons"].append(f"Multiple server files: {', '.join(server_files)}")
        info["issues"].append(f"Multiple server files ({len(server_files)})")
        info["recommendations"].append("Keep only the main server file, delete obsolete ones")

    # Check for MCPB packaging (manifest.json)
    has_mcpb = (repo_path / "manifest.json").exists()
    has_dxt = (
        (repo_path / "dxt").exists() or (repo_path / "dxt").is_dir()
        if (repo_path / "dxt").exists()
        else False
    )
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
    has_readme = any(
        (repo_path / f).exists() for f in ["README.md", "README.rst", "README.txt", "README"]
    )
    if not has_readme:
        info["runt_reasons"].append("No README")
        info["issues"].append("No README")
        info["recommendations"].append("Add README.md with usage instructions")

    # Check for LICENSE
    has_license = any(
        (repo_path / f).exists() for f in ["LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING"]
    )
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
                config_content = git_config.read_text(encoding="utf-8", errors="ignore")
                has_remote = '[remote "origin"]' in config_content or "[remote " in config_content
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
            server_content = monolithic_server.read_text(encoding="utf-8", errors="ignore")
            # Count print( but not:
            # - print(file=sys.stderr) or print(..., file=
            # - console.print() (Rich console to stderr)
            # - logger.print() or similar
            import re as re_module

            prints = re_module.findall(r"(?<!\w)print\s*\(", server_content)
            stderr_prints = re_module.findall(r"print\s*\([^)]*file\s*=", server_content)
            console_prints = re_module.findall(r"console\.print\s*\(", server_content)
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
            server_lines = len(
                monolithic_server.read_text(encoding="utf-8", errors="ignore").splitlines()
            )
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
        repo_path / "src" / pkg_name,
        repo_path / "src" / pkg_name_short,
        repo_path / "src" / pkg_name_underscore,
        repo_path / pkg_name,
        repo_path / pkg_name_short,
        repo_path,
    ]
    # Add actual subdirectories under src/
    src_dir = repo_path / "src"
    if src_dir.exists():
        for subdir in src_dir.iterdir():
            if (
                subdir.is_dir()
                and not subdir.name.startswith(".")
                and not subdir.name.startswith("_")
            ):
                dual_search_dirs.append(subdir)

    # Look for MCP server file
    mcp_server_files = ["mcp_server.py", "fastmcp_server.py"]
    for mcp_file in mcp_server_files:
        for search_dir in dual_search_dirs:
            if search_dir.exists() and (search_dir / mcp_file).exists():
                has_mcp_server = True
                break

    # Look for FastAPI server file (main.py, server.py with FastAPI)
    fastapi_files = ["main.py", "server.py", "app.py"]
    for fa_file in fastapi_files:
        for search_dir in dual_search_dirs:
            if search_dir.exists():
                file_path = search_dir / fa_file
                if file_path.exists():
                    try:
                        content = file_path.read_text(encoding="utf-8", errors="ignore")
                        if "FastAPI" in content or "fastapi" in content:
                            has_fastapi_server = True
                            # Check for health endpoint
                            if (
                                "/health" in content
                                or '@app.get("/health")' in content
                                or "health" in content.lower()
                            ):
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
        # Pattern matches @tool or @tool() decorator followed by def with proper docstring
        # Uses [^)]* for params and [^:]* for return type to avoid greedy matching
        # (?:\(\))? makes the parentheses optional to match both @app.tool and @app.tool()
        # \s* after \n handles indented decorators in nested functions (blender-mcp pattern)
        docstring_pattern = re.compile(
            r'@(?:app|mcp|self\.(?:app|mcp)|server)\.tool(?:\(\))?\s*\n\s*(?:async\s+)?def\s+\w+\([^)]*\)[^:]*:\s*\n\s*"""[\s\S]*?(?:Args:|Returns:|Examples:)[\s\S]*?"""',
            re.MULTILINE,
        )
        for search_dir in dual_search_dirs:
            if search_dir.exists():
                for py_file in search_dir.rglob("*.py"):
                    if any(skip in str(py_file) for skip in SKIP_DIRS):
                        continue
                    try:
                        content = py_file.read_text(encoding="utf-8", errors="ignore")
                        matches = docstring_pattern.findall(content)
                        proper_docstrings += len(matches)
                    except Exception:
                        pass  # Docstring scan error

    info["has_proper_docstrings"] = proper_docstrings > 0 and proper_docstrings >= tool_count * 0.5
    if tool_count >= 3 and not info["has_proper_docstrings"]:
        info["runt_reasons"].append("Missing proper docstrings (Args/Returns)")
        info["issues"].append("Poor docstrings")
        info["recommendations"].append(
            "Add multiline docstrings with Args, Returns, Examples sections"
        )
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
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    # Check for type annotations: -> Type, : Type, List[, Dict[, Optional[
                    if re.search(r"def \w+\([^)]*:\s*\w+|-> \w+|\[[\w\[\], ]+\]", content):
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
                    content = py_file.read_text(encoding="utf-8", errors="ignore")
                    if "import logging" in content or "from logging" in content:
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


def log_scan(message: str, is_error: bool = False):
    """Log a message to the scan activity log."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    formatted_msg = f"{timestamp} | {message}"

    # Initialize log if needed
    if "activity_log" not in state["scan_progress"]:
        state["scan_progress"]["activity_log"] = []

    state["scan_progress"]["activity_log"].append(formatted_msg)

    # Keep only last 50 entries
    if len(state["scan_progress"]["activity_log"]) > 50:
        state["scan_progress"]["activity_log"] = state["scan_progress"]["activity_log"][-50:]

    if is_error:
        state["scan_progress"]["errors"] += 1
        log(f"❌ SCAN ERROR: {message}")
    else:
        # Optional: don't clog main server log with every granular step
        pass


def scan_repos() -> List[Dict[str, Any]]:
    """Scan all repositories for MCP servers."""
    results = []

    if not REPOS_DIR.exists():
        return results

    dirs = [d for d in REPOS_DIR.iterdir() if d.is_dir() and not d.name.startswith(".")]
    state["scan_progress"]["total"] = len(dirs)
    state["scan_progress"]["status"] = "scanning"
    state["scan_progress"]["mcp_repos_found"] = 0
    state["scan_progress"]["errors"] = 0
    state["scan_progress"]["skipped"] = 0
    state["scan_progress"]["activity_log"] = []

    # Add initial activity
    log_scan(f"🔍 Starting scan of {len(dirs)} directories...")

    for i, repo_path in enumerate(dirs):
        state["scan_progress"]["current"] = repo_path.name
        state["scan_progress"]["done"] = i + 1

        try:
            # analyze_repo returns None if not MCP repo
            # It now handles its own granular logging
            info = analyze_repo(repo_path)
            if info:
                results.append(info)
                mcp_count = state["scan_progress"]["mcp_repos_found"] + 1
                state["scan_progress"]["mcp_repos_found"] = mcp_count

                log_scan(
                    f"  {info['zoo_emoji']} Found {info['name']} v{info['fastmcp_version'] or '?'} ({info['tools']} tools)"
                )
            else:
                skipped = state["scan_progress"]["skipped"] + 1
                state["scan_progress"]["skipped"] = skipped
        except Exception as e:
            log_scan(f"Error analyzing {repo_path.name}: {str(e)}", is_error=True)
            logger.error(f"Error analyzing {repo_path.name}: {e}", exc_info=True)

    # Final summary
    state["scan_progress"]["status"] = "complete"
    summary = f"✅ Scan complete: {len(results)} MCP repos found, {state['scan_progress']['skipped']} skipped, {state['scan_progress']['errors']} errors"
    log_scan(summary)
    log(summary)

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

    # Check if running in Docker - if so, map paths to mounted locations
    in_docker = Path("/.dockerenv").exists() or os.path.exists("/.dockerenv")

    cursor_config_path = Path.home() / ".cursor" / "mcp.json"
    if in_docker:
        # Try mounted path
        mounted_path = Path("/host/home") / ".cursor" / "mcp.json"
        if mounted_path.exists():
            cursor_config_path = mounted_path

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


def parse_readme_config(repo_path: Path) -> Optional[Dict]:
    """Parse README to find MCP server configuration JSON snippets."""
    readme_files = [
        repo_path / "README.md",
        repo_path / "README.rst",
        repo_path / "README.txt",
        repo_path / "README",
    ]

    for readme_file in readme_files:
        if not readme_file.exists():
            continue

        try:
            content = readme_file.read_text(encoding="utf-8", errors="ignore")

            # Look for JSON code blocks with mcpServers
            import re

            # Pattern 1: JSON code blocks with mcpServers
            # Matches ```json ... "mcpServers": {...} ... ```
            json_block_pattern = (
                r'```(?:json|javascript)?\s*\n(.*?"mcpServers"\s*:\s*\{[^`]*?\})\s*```'
            )
            matches = re.finditer(json_block_pattern, content, re.DOTALL | re.IGNORECASE)

            for match in matches:
                json_str = match.group(1)
                try:
                    # Try to parse the JSON
                    config = json.loads(json_str)
                    if "mcpServers" in config and isinstance(config["mcpServers"], dict):
                        # Extract first server (most repos show one example)
                        for server_id, server_config in config["mcpServers"].items():
                            if isinstance(server_config, dict):
                                return {
                                    "id": server_id,
                                    "command": server_config.get("command", ""),
                                    "args": server_config.get("args", []),
                                    "cwd": server_config.get("cwd"),
                                    "env": server_config.get("env", {}),
                                    "type": server_config.get("type", "stdio"),
                                    "url": server_config.get("url", ""),
                                    "source": "README.md",
                                }
                except json.JSONDecodeError:
                    # Try to extract just the server config part
                    # Look for patterns like: "server-name": { "command": "...", "args": [...] }
                    server_pattern = r'"([^"]+)"\s*:\s*\{[^}]*"command"\s*:\s*"([^"]+)"[^}]*"args"\s*:\s*\[([^\]]*?)\][^}]*\}'
                    server_match = re.search(server_pattern, json_str, re.DOTALL)
                    if server_match:
                        server_id = server_match.group(1)
                        command = server_match.group(2)
                        args_str = server_match.group(3)
                        # Parse args array
                        args = []
                        for arg_match in re.finditer(r'"([^"]+)"', args_str):
                            args.append(arg_match.group(1))

                        # Look for cwd and env in the same block
                        cwd_match = re.search(r'"cwd"\s*:\s*"([^"]+)"', json_str)
                        cwd = cwd_match.group(1) if cwd_match else None

                        env = {}
                        env_match = re.search(r'"env"\s*:\s*\{([^}]*?)\}', json_str, re.DOTALL)
                        if env_match:
                            for env_pair in re.finditer(
                                r'"([^"]+)"\s*:\s*"([^"]+)"', env_match.group(1)
                            ):
                                env[env_pair.group(1)] = env_pair.group(2)

                        return {
                            "id": server_id,
                            "command": command,
                            "args": args,
                            "cwd": cwd,
                            "env": env,
                            "source": "README.md",
                        }

            # Pattern 2: Look for installation/configuration sections with JSON examples
            # Common section headers: Installation, Configuration, Setup, Usage
            section_pattern = r'(?:##?\s+(?:Installation|Configuration|Setup|Usage|Getting Started|Quick Start)[^\n]*\n.*?)(?:```(?:json|javascript)?\s*\n(.*?"mcpServers"[^`]*?)\s*```)'
            section_match = re.search(section_pattern, content, re.DOTALL | re.IGNORECASE)
            if section_match:
                json_str = section_match.group(1)
                try:
                    config = json.loads(json_str)
                    if "mcpServers" in config and isinstance(config["mcpServers"], dict):
                        for server_id, server_config in config["mcpServers"].items():
                            if isinstance(server_config, dict):
                                return {
                                    "id": server_id,
                                    "command": server_config.get("command", ""),
                                    "args": server_config.get("args", []),
                                    "cwd": server_config.get("cwd"),
                                    "env": server_config.get("env", {}),
                                    "type": server_config.get("type", "stdio"),
                                    "url": server_config.get("url", ""),
                                    "source": "README.md",
                                }
                except json.JSONDecodeError:
                    pass

        except Exception as e:
            log(f"⚠️ Failed to parse README for {repo_path.name}: {e}")
            continue

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
            match = re.search(
                r'\[project\.scripts\][^\[]*?(\w+)\s*=\s*["\']([^"\']+)["\']', content, re.DOTALL
            )
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
                        "source": "pyproject.toml",
                    }

        # Look for [tool.poetry.scripts]
        if "[tool.poetry.scripts]" in content:
            import re

            match = re.search(
                r'\[tool\.poetry\.scripts\][^\[]*?(\w+)\s*=\s*["\']([^"\']+)["\']',
                content,
                re.DOTALL,
            )
            if match:
                script_name, entry = match.groups()
                if ":" in entry:
                    module_path = entry.split(":")[0]
                    return {
                        "command": "python",
                        "args": ["-m", module_path],
                        "cwd": str(repo_path),
                        "env": {"PYTHONPATH": str(repo_path / "src")},
                        "source": "pyproject.toml",
                    }
    except Exception as e:
        log(f"⚠️ Failed to parse pyproject.toml for {repo_path.name}: {e}")

    return None


async def connect_repo_server(repo_name: str) -> Dict[str, Any]:
    """Connect to an MCP server from a repository using Cursor config or pyproject.toml."""
    repo_path = REPOS_DIR / repo_name

    if not repo_path.exists() or not repo_path.is_dir():
        raise HTTPException(404, f"Repository {repo_name} not found at {repo_path}")

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
            result["error"] = (
                f"No config found for {repo_name}. Add to Cursor mcp.json or define in pyproject.toml"
            )
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
                tool_list.append(
                    {
                        "name": tool.name,
                        "description": tool.description or "No description",
                        "inputSchema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
                    }
                )

            result["status"] = "connected"
            result["tools"] = tool_list

            # Store connection state (note: actual client connection closes after async with block)
            # This is intentional - we only store tool metadata, not the live connection
            state["connected_servers"][connection_id] = {
                "status": "connected",
                "tools": tool_list,
                "config": cursor_config,
            }

            log(f"✅ Connected to {repo_name}: {len(tool_list)} tools")

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        # Store error state so UI can display it
        state["connected_servers"][connection_id] = {
            "status": "error",
            "error": str(e),
            "tools": [],
        }
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
                "name": server_config.get("name", server_id),
                "status": "connected",
                "tools": conn.get("tools", []),
            }

    result = {
        "id": connection_id,
        "name": server_config.get("name", server_id),
        "status": "connecting",
        "tools": [],
        "error": None,
    }

    if not FASTMCP_AVAILABLE:
        result["status"] = "error"
        result["error"] = "FastMCP not installed"
        return result

    try:
        cmd = server_config.get("command")
        if not cmd:
            result["status"] = "error"
            result["error"] = "Missing 'command' in server configuration"
            return result

        args = server_config.get("args", [])
        cwd = server_config.get("cwd")
        env = {**os.environ, **server_config.get("env", {})}

        server_name = server_config.get("name", server_id)
        log(f"🔌 Connecting to {server_name}...")

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
                tool_list.append(
                    {
                        "name": tool.name,
                        "description": tool.description or "No description",
                        "inputSchema": tool.inputSchema if hasattr(tool, "inputSchema") else {},
                    }
                )

            result["status"] = "connected"
            result["tools"] = tool_list

            # Store connection state (note: actual client connection closes after async with block)
            # This is intentional - we only store tool metadata, not the live connection
            state["connected_servers"][connection_id] = {
                "status": "connected",
                "tools": tool_list,
            }

            log(f"✅ Connected to {server_name}: {len(tool_list)} tools")

    except Exception as e:
        result["status"] = "error"
        result["error"] = str(e)
        # Store error state so UI can display it
        state["connected_servers"][connection_id] = {
            "status": "error",
            "error": str(e),
            "tools": [],
        }
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


@app.post("/api/clients/refresh")
def refresh_clients():
    """Force refresh of discovered clients."""
    return discover_mcp_clients()


@app.get("/api/clients/{client_name}/servers")
def get_client_servers(client_name: str):
    """Get all servers for a specific client."""
    clients = discover_mcp_clients()
    if client_name not in clients:
        raise HTTPException(404, f"Client {client_name} not found")
    return {
        "client": client_name,
        "path": clients[client_name]["path"],
        "servers": clients[client_name]["servers"],
    }


@app.post("/api/clients/{client_name}/servers")
def create_server(client_name: str, server_data: dict):
    """Add a new MCP server to a client configuration."""
    clients = discover_mcp_clients()
    if client_name not in clients:
        raise HTTPException(404, f"Client {client_name} not found")

    config_path = Path(clients[client_name]["path"])

    # Map path if in Docker
    in_docker = Path("/.dockerenv").exists() or os.path.exists("/.dockerenv")
    if in_docker:
        path_str = str(config_path)
        if "AppData" in path_str or "Roaming" in path_str:
            try:
                parts = Path(path_str).parts
                if "Roaming" in parts:
                    roaming_idx = [i for i, p in enumerate(parts) if p == "Roaming"][0]
                    rel_path = Path(*parts[roaming_idx + 1 :])
                    config_path = Path("/host/appdata") / rel_path
            except (IndexError, ValueError):
                pass
        elif str(config_path).startswith(str(Path.home())):
            try:
                rel_path = config_path.relative_to(Path.home())
                config_path = Path("/host/home") / rel_path
            except ValueError:
                pass

    if not config_path.exists():
        raise HTTPException(404, f"Config file not found: {config_path}")

    try:
        # Read existing config
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Determine config structure
        if "mcpServers" in config:
            servers = config["mcpServers"]
        elif "mcp" in config and isinstance(config.get("mcp"), dict):
            servers = config["mcp"]["servers"]
        elif "servers" in config:
            servers = config["servers"]
        else:
            # Default to mcpServers format
            config["mcpServers"] = {}
            servers = config["mcpServers"]

        # Add new server
        server_id = server_data.get("id", server_data.get("name", "").lower().replace(" ", "-"))
        if server_id in servers:
            raise HTTPException(400, f"Server '{server_id}' already exists")

        servers[server_id] = {
            "command": server_data.get("command", ""),
            "args": server_data.get("args", []),
        }
        if "cwd" in server_data:
            servers[server_id]["cwd"] = server_data["cwd"]
        if "env" in server_data:
            servers[server_id]["env"] = server_data["env"]
        if "type" in server_data:
            servers[server_id]["type"] = server_data["type"]
        if "url" in server_data:
            servers[server_id]["url"] = server_data["url"]

        # Write back to file
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        log(f"✅ Added server '{server_id}' to {client_name}")
        return {"success": True, "server_id": server_id}

    except Exception as e:
        log(f"❌ Error adding server: {e}")
        raise HTTPException(500, f"Failed to add server: {str(e)}")


@app.put("/api/clients/{client_name}/servers/{server_id}")
def update_server(client_name: str, server_id: str, server_data: dict):
    """Update an existing MCP server configuration."""
    clients = discover_mcp_clients()
    if client_name not in clients:
        raise HTTPException(404, f"Client {client_name} not found")

    config_path = Path(clients[client_name]["path"])

    # Map path if in Docker (same logic as create)
    in_docker = Path("/.dockerenv").exists() or os.path.exists("/.dockerenv")
    if in_docker:
        path_str = str(config_path)
        if "AppData" in path_str or "Roaming" in path_str:
            try:
                parts = Path(path_str).parts
                if "Roaming" in parts:
                    roaming_idx = [i for i, p in enumerate(parts) if p == "Roaming"][0]
                    rel_path = Path(*parts[roaming_idx + 1 :])
                    config_path = Path("/host/appdata") / rel_path
            except (IndexError, ValueError):
                pass
        elif str(config_path).startswith(str(Path.home())):
            try:
                rel_path = config_path.relative_to(Path.home())
                config_path = Path("/host/home") / rel_path
            except ValueError:
                pass

    if not config_path.exists():
        raise HTTPException(404, f"Config file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Determine config structure
        if "mcpServers" in config:
            servers = config["mcpServers"]
        elif "mcp" in config and isinstance(config.get("mcp"), dict):
            servers = config["mcp"]["servers"]
        elif "servers" in config:
            servers = config["servers"]
        else:
            raise HTTPException(404, f"Server '{server_id}' not found")

        if server_id not in servers:
            raise HTTPException(404, f"Server '{server_id}' not found")

        # Update server config
        if "command" in server_data:
            servers[server_id]["command"] = server_data["command"]
        if "args" in server_data:
            servers[server_id]["args"] = server_data["args"]
        if "cwd" in server_data:
            servers[server_id]["cwd"] = server_data["cwd"]
        if "env" in server_data:
            servers[server_id]["env"] = server_data["env"]
        if "type" in server_data:
            servers[server_id]["type"] = server_data["type"]
        if "url" in server_data:
            servers[server_id]["url"] = server_data["url"]

        # Write back
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        log(f"✅ Updated server '{server_id}' in {client_name}")
        return {"success": True, "server_id": server_id}

    except HTTPException:
        raise
    except Exception as e:
        log(f"❌ Error updating server: {e}")
        raise HTTPException(500, f"Failed to update server: {str(e)}")


@app.delete("/api/clients/{client_name}/servers/{server_id}")
def delete_server(client_name: str, server_id: str):
    """Delete an MCP server from a client configuration."""
    clients = discover_mcp_clients()
    if client_name not in clients:
        raise HTTPException(404, f"Client {client_name} not found")

    config_path = Path(clients[client_name]["path"])

    # Map path if in Docker (same logic as create)
    in_docker = Path("/.dockerenv").exists() or os.path.exists("/.dockerenv")
    if in_docker:
        path_str = str(config_path)
        if "AppData" in path_str or "Roaming" in path_str:
            try:
                parts = Path(path_str).parts
                if "Roaming" in parts:
                    roaming_idx = [i for i, p in enumerate(parts) if p == "Roaming"][0]
                    rel_path = Path(*parts[roaming_idx + 1 :])
                    config_path = Path("/host/appdata") / rel_path
            except (IndexError, ValueError):
                pass
        elif str(config_path).startswith(str(Path.home())):
            try:
                rel_path = config_path.relative_to(Path.home())
                config_path = Path("/host/home") / rel_path
            except ValueError:
                pass

    if not config_path.exists():
        raise HTTPException(404, f"Config file not found: {config_path}")

    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Determine config structure
        if "mcpServers" in config:
            servers = config["mcpServers"]
        elif "mcp" in config and isinstance(config.get("mcp"), dict):
            servers = config["mcp"]["servers"]
        elif "servers" in config:
            servers = config["servers"]
        else:
            raise HTTPException(404, f"Server '{server_id}' not found")

        if server_id not in servers:
            raise HTTPException(404, f"Server '{server_id}' not found")

        # Delete server
        del servers[server_id]

        # Write back
        with open(config_path, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)

        log(f"✅ Deleted server '{server_id}' from {client_name}")
        return {"success": True, "server_id": server_id}

    except HTTPException:
        raise
    except Exception as e:
        log(f"❌ Error deleting server: {e}")
        raise HTTPException(500, f"Failed to delete server: {str(e)}")


@app.get("/api/repos")
def get_repo_analysis():
    """Get static analysis of all MCP repositories."""
    return scan_repos()


def detect_installation_methods(repo_path: Path) -> Dict[str, Any]:
    """Detect available installation methods for an MCP server."""
    methods = {
        "mcpb": False,
        "npm": False,
        "npx": False,
        "python": True,  # Always available as fallback
        "mcpb_path": None,
        "npm_package": None,
        "npx_command": None,
    }

    # Check for MCPB (manifest.json)
    manifest_path = repo_path / "manifest.json"
    if manifest_path.exists():
        methods["mcpb"] = True
        methods["mcpb_path"] = str(manifest_path)

    # Check for npm/npx setup (package.json)
    package_json = repo_path / "package.json"
    if package_json.exists():
        try:
            with open(package_json, "r", encoding="utf-8") as f:
                pkg = json.load(f)

            # Check for bin field (npx support)
            if "bin" in pkg:
                methods["npx"] = True
                if isinstance(pkg["bin"], dict):
                    # Get first bin command
                    methods["npx_command"] = list(pkg["bin"].keys())[0]
                elif isinstance(pkg["bin"], str):
                    methods["npx_command"] = pkg["name"] if "name" in pkg else repo_path.name

            # Check for name field (npm package)
            if "name" in pkg:
                methods["npm"] = True
                methods["npm_package"] = pkg["name"]
        except Exception:
            pass

    return methods
    return methods


def detect_fullstack_features(repo_path: Path) -> Dict[str, Any]:
    """Detect fullstack capabilities (frontend, backend, infra, docs)."""
    features = {
        "is_fullstack": False,
        "frontend": [],
        "backend": [],
        "infrastructure": [],
        "docs": [],
        "git": {"exists": False, "dirty": False, "branch": "unknown"},
        "runtime": {"running": False, "container_id": None},
    }

    # --- Frontend Detection ---
    package_json = repo_path / "package.json"
    if package_json.exists():
        try:
            with open(package_json, "r", encoding="utf-8") as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

                if "react" in deps:
                    features["frontend"].append("React")
                if "vue" in deps:
                    features["frontend"].append("Vue")
                if "svelte" in deps:
                    features["frontend"].append("Svelte")
                if "angular" in deps:
                    features["frontend"].append("Angular")
                if "next" in deps:
                    features["frontend"].append("Next.js")
                if "vite" in deps:
                    features["frontend"].append("Vite")
                if "tailwindcss" in deps:
                    features["frontend"].append("Tailwind")
                if "typescript" in deps:
                    features["frontend"].append("TypeScript")
        except:
            pass

    # Simple file checks
    if list(repo_path.glob("*.html")):
        features["frontend"].append("HTML")
    if list(repo_path.glob("*.css")):
        features["frontend"].append("CSS")

    # --- Backend Detection ---
    # Python
    req_txt = repo_path / "requirements.txt"
    py_toml = repo_path / "pyproject.toml"
    if req_txt.exists() or py_toml.exists():
        features["backend"].append("Python")
        # Read content to be more specific
        content = ""
        if req_txt.exists():
            content += req_txt.read_text(errors="ignore")
        if py_toml.exists():
            content += py_toml.read_text(errors="ignore")

        if "fastapi" in content:
            features["backend"].append("FastAPI")
        if "flask" in content:
            features["backend"].append("Flask")
        if "django" in content:
            features["backend"].append("Django")
        if "starlette" in content:
            features["backend"].append("Starlette")

    # Node Backend (Express/Nest)
    if package_json.exists():
        try:
            with open(package_json, "r", encoding="utf-8") as f:
                pkg = json.load(f)
                deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
                if "express" in deps:
                    features["backend"].append("Express")
                if "nestjs" in deps:
                    features["backend"].append("NestJS")
        except:
            pass

    # --- Infrastructure ---
    if (repo_path / "docker-compose.yml").exists() or (repo_path / "docker-compose.yaml").exists():
        features["infrastructure"].append("Docker Compose")
    if (repo_path / "Dockerfile").exists():
        features["infrastructure"].append("Dockerfile")
    if (repo_path / "k8s").exists() or (repo_path / "kubernetes").exists():
        features["infrastructure"].append("Kubernetes")

    # --- Docs ---
    if (repo_path / "README.md").exists():
        features["docs"].append("README")
    if (repo_path / "docs").exists():
        features["docs"].append("docs/")
    if (repo_path / "openapi.json").exists() or (repo_path / "openapi.yaml").exists():
        features["docs"].append("OpenAPI")

    # --- Git Status ---
    git_dir = repo_path / ".git"
    if git_dir.exists():
        features["git"]["exists"] = True
        try:
            # Check branch
            branch = subprocess.check_output(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=repo_path,
                text=True,
                stderr=subprocess.DEVNULL,
            ).strip()
            features["git"]["branch"] = branch

            # Check dirty
            status = subprocess.check_output(
                ["git", "status", "--porcelain"],
                cwd=repo_path,
                text=True,
                stderr=subprocess.DEVNULL,
            )
            features["git"]["dirty"] = bool(status.strip())
        except:
            pass

    # --- Runtime (Docker) ---
    # Try to find a container related to this repo
    # Strategy: Match folder name to formatting names
    repo_name = repo_path.name.lower()
    try:
        # Get all running container names and IDs
        # docker ps --format "{{.ID}}|{{.Names}}"
        output = subprocess.check_output(
            ["docker", "ps", "--format", "{{.ID}}|{{.Names}}"], text=True, stderr=subprocess.DEVNULL
        )
        for line in output.strip().splitlines():
            if "|" in line:
                cid, name = line.split("|", 1)
                # Loose matching: if repo name is substring of container name or vice versa
                if repo_name in name.lower() or name.lower() in repo_name:
                    features["runtime"]["running"] = True
                    features["runtime"]["container_id"] = cid
                    features["runtime"]["name"] = name
                    break
    except:
        pass

    # Decision
    has_frontend = len(features["frontend"]) > 0
    has_backend = len(features["backend"]) > 0
    has_docker = "Docker Compose" in features["infrastructure"]

    # It's fullstack if it has significant parts of both or is a known type
    if (
        (has_frontend and has_backend)
        or (has_frontend and has_docker)
        or (has_backend and has_docker)
    ):
        features["is_fullstack"] = True
    elif (repo_path / "package.json").exists() and (repo_path / "requirements.txt").exists():
        features["is_fullstack"] = True

    return features


def get_client_config_hints(client_name: str) -> Dict[str, str]:
    """Get installation hints for different MCP clients."""
    hints = {
        "claude-desktop": {
            "config_path": "Claude → Settings → Developer → Edit Config",
            "config_file": "claude_desktop_config.json",
            "location": "%APPDATA%\\Claude\\claude_desktop_config.json (Windows) or ~/.config/Claude/claude_desktop_config.json (Linux/Mac)",
            "mcpb_hint": "Open Claude Desktop → Settings → Developer → Add MCP Server → Paste manifest.json path or drag & drop",
        },
        "cursor": {
            "config_path": "Cursor → Settings → Extensions → MCP",
            "config_file": "mcp.json",
            "location": "%APPDATA%\\Cursor\\User\\globalStorage\\...\\cline_mcp_settings.json or ~/.cursor/mcp.json",
            "mcpb_hint": "MCPB not directly supported - use JSON snippet method",
        },
        "windsurf-ide": {
            "config_path": "Windsurf → Settings → MCP Servers",
            "config_file": "mcp_config.json",
            "location": "%APPDATA%\\Codeium\\Windsurf\\mcp_config.json",
            "mcpb_hint": "MCPB not directly supported - use JSON snippet method",
        },
        "zed-ide": {
            "config_path": "Zed → Settings → MCP",
            "config_file": "settings.json",
            "location": "~/.config/zed/settings.json or ~/Library/Application Support/Zed/settings.json",
            "mcpb_hint": "MCPB not directly supported - use JSON snippet method",
        },
        "antigravity-ide": {
            "config_path": "Antigravity → Agent Panel → MCP Servers → Manage",
            "config_file": "mcp_config.json",
            "location": "%APPDATA%\\Antigravity\\mcp_config.json",
            "mcpb_hint": "MCPB not directly supported - use JSON snippet method",
        },
    }
    return hints.get(
        client_name,
        {
            "config_path": "Client settings",
            "config_file": "config.json",
            "location": "Check client documentation",
            "mcpb_hint": "Check if client supports MCPB",
        },
    )


@app.get("/api/available-servers")
async def get_available_servers():
    """Get list of available MCP servers from scanned repositories."""
    available = []

    if not REPOS_DIR.exists():
        return available

    repos = scan_repos()  # Get scanned repos
    for repo in repos:
        repo_path = Path(repo["path"])

        # Detect installation methods
        install_methods = detect_installation_methods(repo_path)

        # Determine best config source (prioritize MCPB, then npm/npx, then README, then pyproject, then inferred)
        config_data = None
        source = "inferred"

        # Priority 1: MCPB (if available)
        if install_methods["mcpb"]:
            # For MCPB, we still need to provide a JSON snippet for clients that don't support MCPB directly
            # But mark it as MCPB-preferred
            source = "MCPB (preferred)"

        # Priority 2: npm/npx (if available)
        if install_methods["npx"]:
            if not config_data:
                config_data = {
                    "command": "npx",
                    "args": ["-y", install_methods["npx_command"] or repo["name"]],
                    "cwd": None,
                    "env": {},
                    "type": "stdio",
                }
                source = "npm/npx"
        elif install_methods["npm"]:
            if not config_data:
                # npm install then use local
                config_data = {
                    "command": "npx",
                    "args": [install_methods["npm_package"] or repo["name"]],
                    "cwd": None,
                    "env": {},
                    "type": "stdio",
                }
                source = "npm"

        # Priority 3: Try README (but user says these are often wrong, so lower priority)
        if not config_data:
            readme_config = parse_readme_config(repo_path)
            if readme_config:
                config_data = readme_config
                source = "README.md (verify accuracy)"

        # Priority 4: pyproject.toml
        if not config_data:
            entrypoint = parse_pyproject_entrypoint(repo_path)
            if entrypoint:
                config_data = entrypoint
                source = "pyproject.toml"

        # Priority 5: Infer from structure
        if not config_data:
            # Look for common entry points
            server_files = [
                repo_path / "fastmcp_server.py",
                repo_path / "mcp_server.py",
                repo_path / "server.py",
                repo_path / "main.py",
            ]

            for server_file in server_files:
                if server_file.exists():
                    if "src" in str(repo_path):
                        pkg_name = repo_path.name.replace("-", "_")
                        config_data = {
                            "command": "python",
                            "args": ["-m", pkg_name],
                            "cwd": str(repo_path),
                            "env": {"PYTHONPATH": str(repo_path / "src")},
                            "source": "inferred (package structure)",
                        }
                    else:
                        config_data = {
                            "command": "python",
                            "args": [str(server_file.relative_to(repo_path))],
                            "cwd": str(repo_path),
                            "env": {},
                            "source": "inferred (file structure)",
                        }
                    break

        # If we have config data, add to available list
        if config_data:
            available.append(
                {
                    "id": repo["name"].replace("_", "-").replace(" ", "-").lower(),
                    "name": repo["name"].replace("-", " ").replace("_", " ").title(),
                    "repo": repo["name"],
                    "command": config_data.get("command", "python"),
                    "args": config_data.get("args", []),
                    "cwd": config_data.get("cwd", str(repo_path)),
                    "env": config_data.get("env", {}),
                    "type": config_data.get("type", "stdio"),
                    "url": config_data.get("url", ""),
                    "source": source,
                    "tools": repo.get("tools", 0),
                    "fastmcp_version": repo.get("fastmcp_version"),
                    "install_methods": install_methods,
                    "has_mcpb": install_methods["mcpb"],
                    "has_npm": install_methods["npm"] or install_methods["npx"],
                }
            )

    return available


@app.get("/api/servers/{client}/{server_id}")
def get_server_details(client: str, server_id: str):
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
            connections.append(
                {
                    "id": conn_id,
                    "name": conn_id.split(":")[-1] if ":" in conn_id else conn_id,
                    "tools": conn.get("tools", []),
                    "tool_count": len(conn.get("tools", [])),
                }
            )
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
    if not repo_path.exists() or not repo_path.is_dir():
        raise HTTPException(404, f"Repository {repo_name} not found at {repo_path}")

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
                items.append(
                    {
                        "name": item.name,
                        "type": "dir" if item.is_dir() else "file",
                        "size": item.stat().st_size if item.is_file() else None,
                    }
                )
            return {"type": "directory", "path": str(file_path), "items": items}

        # Read file (limit size)
        size = file_path.stat().st_size
        if size > 100_000:  # 100KB limit
            return {"error": f"File too large ({size} bytes). Max 100KB."}

        try:
            content = file_path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            return {"error": "Binary file, cannot read as text"}

        return {"type": "file", "path": str(file_path), "content": content, "size": size}
    except Exception as e:
        return {"error": str(e)}


@app.get("/api/ai/search-web")
async def ai_search_web(query: str, num_results: int = 5):
    """Search the web using DuckDuckGo (no API key needed)."""
    try:
        # Use DuckDuckGo HTML search (no API key required)
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(
                "https://html.duckduckgo.com/html/",
                params={"q": query},
                headers={
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                },
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
                    actual_url = re.search(r"uddg=([^&]+)", url)
                    if actual_url:
                        from urllib.parse import unquote

                        url = unquote(actual_url.group(1))

                results.append({"title": title.strip(), "url": url, "snippet": snippet.strip()})

            return {"query": query, "results": results, "count": len(results)}

    except Exception as e:
        return {"error": str(e)}


@app.get("/api/ai/list-repos")
async def ai_list_repos():
    """List all repos in the repos directory with basic info."""
    repos = []
    for item in sorted(REPOS_DIR.iterdir()):
        if item.is_dir() and not item.name.startswith("."):
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
    """Get list of available AI models from Ollama, LM Studio, and vLLM."""
    models = []
    errors = []

    async with httpx.AsyncClient(timeout=3.0) as client:
        # 1. Ollama
        try:
            logger.info(f"Checking Ollama at {OLLAMA_URL}")
            resp = await client.get(f"{OLLAMA_URL}/api/tags")
            if resp.status_code == 200:
                data = resp.json()
                for model in data.get("models", []):
                    size_gb = model.get("size", 0) / (1024**3)
                    models.append(
                        {
                            "name": model.get("name"),
                            "size": f"{size_gb:.1f}GB",
                            "modified": model.get("modified_at", "")[:10],
                            "provider": "Ollama",
                        }
                    )
        except Exception as e:
            errors.append(f"Ollama: {str(e)}")

        # 2. LM Studio (OpenAI Compatible)
        try:
            logger.info(f"Checking LM Studio at {LM_STUDIO_URL}")
            resp = await client.get(f"{LM_STUDIO_URL}/v1/models")
            if resp.status_code == 200:
                data = resp.json()
                for model in data.get("data", []):
                    models.append(
                        {
                            "name": model.get("id"),
                            "size": "—",  # API doesn't always return size
                            "modified": "",
                            "provider": "LM Studio",
                        }
                    )
        except Exception as e:
            errors.append(f"LM Studio: {str(e)}")

        # 3. vLLM (OpenAI Compatible)
        try:
            logger.info(f"Checking vLLM at {VLLM_URL}")
            resp = await client.get(f"{VLLM_URL}/v1/models")
            if resp.status_code == 200:
                data = resp.json()
                for model in data.get("data", []):
                    models.append(
                        {"name": model.get("id"), "size": "—", "modified": "", "provider": "vLLM"}
                    )
        except Exception as e:
            errors.append(f"vLLM: {str(e)}")

    return {"models": models, "count": len(models), "errors": errors}


@app.get("/api/ai/preprompts")
async def get_preprompts():
    """Get available AI preprompt personalities from database."""
    try:
        import preprompt_db

        preprompts = preprompt_db.list_preprompts()
        return {"preprompts": preprompts, "count": len(preprompts), "default": "MCP Developer"}
    except Exception as e:
        # Fallback to builtin preprompts
        log(f"❌ Error loading preprompts: {e}")
        return {
            "preprompts": [
                {"id": key, "name": value["name"], "emoji": value["name"].split()[0]}
                for key, value in PREPROMPTS.items()
            ],
            "count": len(PREPROMPTS),
            "default": "dev",
            "error": str(e),
        }


@app.post("/api/preprompts/add")
async def add_preprompt_endpoint(request: Request):
    """Add a new preprompt."""
    import preprompt_db

    data = await request.json()

    result = preprompt_db.add_preprompt(
        name=data.get("name"),
        prompt_text=data.get("prompt_text"),
        emoji=data.get("emoji", "🤖"),
        source=data.get("source", "user"),
        author=data.get("author", "user"),
        tags=data.get("tags"),
    )
    return result


@app.post("/api/preprompts/import")
async def import_preprompt_markdown(request: Request):
    """Import preprompt from markdown file."""
    import preprompt_db

    data = await request.json()

    content = data.get("content", "")
    filename = data.get("filename", "imported.md")

    result = preprompt_db.import_from_markdown(content, filename)
    return result


@app.post("/api/preprompts/ai-refine")
async def ai_refine_preprompt(request: Request):
    """AI-generate an elaborate preprompt from simple text."""
    import preprompt_db

    data = await request.json()
    simple_text = data.get("text", "")

    if not simple_text:
        return {"success": False, "error": "No text provided"}

    # Generate preprompt using Ollama
    refine_prompt = f"""You are a creative AI assistant helping design preprompts for an AI assistant personality.

Given this simple concept: "{simple_text}"

Create an elaborate, engaging preprompt that:
1. Gives the AI a distinctive personality related to "{simple_text}"
2. Maintains technical accuracy while being entertaining
3. Includes metaphors and creative language
4. Still helps with MCP server development effectively
5. Is 150-250 words long

Format the output as a preprompt that starts with "You are..." and describes the personality, capabilities, and how they should help with code.

Be creative and fun while staying professional!"""

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/generate",
                json={
                    "model": data.get("model_id", "qwen2.5:14b"),
                    "prompt": refine_prompt,
                    "stream": False,
                },
            )

            if resp.status_code != 200:
                return {"success": False, "error": f"Ollama returned {resp.status_code}"}

            result = resp.json()
            generated_prompt = result.get("response", "")

            # Extract emoji from simple_text or generate one
            emoji_map = {
                "coin": "🪙",
                "butterfly": "🦋",
                "pirate": "🏴‍☠️",
                "zen": "🧘",
                "aussie": "🦘",
                "artist": "🎨",
                "chef": "👨‍🍳",
                "detective": "🕵️",
                "wizard": "🧙",
                "robot": "🤖",
                "cat": "🐱",
                "dog": "🐕",
            }

            emoji = "🤖"
            for key, val in emoji_map.items():
                if key in simple_text.lower():
                    emoji = val
                    break

            # Save to database
            name = simple_text.title()
            save_result = preprompt_db.add_preprompt(
                name=name,
                prompt_text=generated_prompt,
                emoji=emoji,
                source="ai_generated",
                author="ai",
            )

            return {
                "success": save_result["success"],
                "preprompt": generated_prompt,
                "name": name,
                "emoji": emoji,
                "id": save_result.get("id"),
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/preprompts/{identifier}")
async def get_preprompt_endpoint(identifier: str):
    """Get a specific preprompt by ID or name."""
    import preprompt_db

    preprompt = preprompt_db.get_preprompt(identifier)

    if preprompt:
        return preprompt
    else:
        return {"error": "Preprompt not found"}


@app.put("/api/preprompts/{identifier}")
async def update_preprompt_endpoint(identifier: str, request: Request):
    """Update a preprompt."""
    import preprompt_db

    data = await request.json()

    result = preprompt_db.update_preprompt(
        identifier=identifier,
        name=data.get("name"),
        emoji=data.get("emoji"),
        prompt_text=data.get("prompt_text"),
        tags=data.get("tags"),
    )
    return result


@app.delete("/api/preprompts/{identifier}")
async def delete_preprompt_endpoint(identifier: str):
    """Delete a preprompt."""
    import preprompt_db

    result = preprompt_db.delete_preprompt(identifier)
    return result


@app.post("/api/preprompts/seed")
async def seed_preprompts():
    """Seed database with built-in preprompts."""
    import preprompt_db

    try:
        preprompt_db.seed_builtin_preprompts()
        return {"success": True, "message": "Built-in preprompts seeded"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.get("/api/preprompts/stats/usage")
async def get_usage_stats():
    """Get usage statistics for all preprompts."""
    import preprompt_db

    try:
        stats = preprompt_db.get_usage_stats()
        return {"success": True, "stats": stats, "count": len(stats)}
    except Exception as e:
        return {"success": False, "error": str(e), "stats": []}


@app.post("/api/ai/chat")
async def ai_chat(request: Request):
    """Chat with Ollama for AI-powered analysis with tool capabilities."""
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
            items_str = "\n".join(
                [
                    f"  {'📁' if i['type'] == 'dir' else '📄'} {i['name']}"
                    for i in file_result["items"][:50]
                ]
            )
            context_parts.append(f"DIRECTORY: {file_path}\n{items_str}")

    # Add web search results if requested
    if web_search:
        search_result = await ai_search_web(web_search)
        if "results" in search_result:
            results_str = "\n".join(
                [f"- [{r['title']}]({r['url']}): {r['snippet']}" for r in search_result["results"]]
            )
            context_parts.append(f"WEB SEARCH for '{web_search}':\n{results_str}")

    # Add repo list context if requested
    if include_repo_context:
        repos_result = await ai_list_repos()
        repos_str = "\n".join(
            [f"- {r['name']} ({r.get('type', 'unknown')})" for r in repos_result["repos"][:30]]
        )
        context_parts.append(f"AVAILABLE REPOS in {repos_result['base_path']}:\n{repos_str}")

    # Get system prompt from database (use selected preprompt or default)
    preprompt_name = request.get("preprompt", "MCP Developer")

    try:
        import preprompt_db

        preprompt_data = preprompt_db.get_preprompt(preprompt_name)
        if preprompt_data:
            system_prompt = preprompt_data["prompt_text"]
            log(f"✓ Loaded preprompt: {preprompt_name}")
            # Track usage
            preprompt_db.track_usage(preprompt_name)
        else:
            log(f"⚠️ Preprompt not found: {preprompt_name}, using default")
            # Fallback to builtin
            system_prompt = PREPROMPTS.get("dev", {}).get(
                "prompt", "You are a helpful AI assistant."
            )
    except Exception as e:
        log(f"❌ Error loading preprompt: {e}")
        import traceback

        log(f"Traceback: {traceback.format_exc()}")
        system_prompt = PREPROMPTS.get("dev", {}).get("prompt", "You are a helpful AI assistant.")

    full_message = message
    if context_parts:
        full_message = "\n\n".join(context_parts) + "\n\nUSER QUESTION: " + message

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": model_id,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": full_message},
                    ],
                    "stream": False,
                },
            )

            if resp.status_code != 200:
                return {"error": f"Ollama returned {resp.status_code}: {resp.text}"}

            result = resp.json()
            response = result.get("message", {}).get("content", "")

            if not response:
                response = str(result)

            log(f"✅ AI response received ({len(response)} chars)")
            return {
                "response": response,
                "context_used": list(context_parts) if context_parts else None,
                "preprompt_used": preprompt_name,
                "preprompt_found": preprompt_data is not None
                if "preprompt_data" in locals()
                else False,
            }

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
    return f"""<!DOCTYPE html>
<html lang="en" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🦁 MCP Studio - Mission Control</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <!-- Toastify for notifications -->
    <link rel="stylesheet" type="text/css" href="https://cdn.jsdelivr.net/npm/toastify-js/src/toastify.min.css">
    <script type="text/javascript" src="https://cdn.jsdelivr.net/npm/toastify-js"></script>
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
        
        /* Tool docstring formatting */
        .tool-description {{ line-height: 1.6; }}
        .tool-description code {{ background: rgba(0, 0, 0, 0.3); padding: 0.125rem 0.25rem; border-radius: 0.25rem; font-size: 0.875rem; }}
        .tool-description strong {{ color: #ffffff; font-weight: 600; }}
        .tool-description ul {{ list-style-type: disc; margin-left: 1.5rem; margin-top: 0.5rem; margin-bottom: 0.5rem; }}
        .tool-description li {{ margin-top: 0.25rem; }}
        .tool-description pre {{ background: rgba(0, 0, 0, 0.4); padding: 0.75rem; border-radius: 0.375rem; border: 1px solid rgba(255, 255, 255, 0.1); overflow-x: auto; margin-top: 0.5rem; margin-bottom: 0.5rem; }}
        .tool-description pre code {{ background: transparent; padding: 0; }}
        .tool-description-compact {{ max-height: 200px; overflow-y: auto; }}
        .tool-description-compact .space-y-4 > * {{ margin-top: 0.5rem; margin-bottom: 0.5rem; }}
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

            <!-- Scan Activity -->
            <div class="mt-8 glass rounded-xl overflow-hidden">
                <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                    <div class="flex items-center gap-4">
                        <h2 class="font-semibold">🔍 Scan Activity</h2>
                        <div id="scan-progress-display" class="text-sm"></div>
                    </div>
                    <span id="scan-errors" class="text-xs text-red-400 font-bold"></span>
                </div>
                <div id="scan-activity" class="p-4 mono text-xs max-h-48 overflow-y-auto bg-black/30 text-gray-400">
                    <div class="italic opacity-50">Ready to scan...</div>
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
                        <button onclick="showScannerCriteria()" class="px-4 py-1 bg-purple-600/50 hover:bg-purple-600/70 rounded text-sm border border-purple-500/30" title="View classification criteria">
                            📋 Criteria
                        </button>
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
                        <div class="flex-1">
                            <h2 class="font-semibold flex items-center gap-2">
                                🤖 AI Assistant
                                <span id="ai-status" class="text-xs px-2 py-0.5 rounded bg-gray-700 text-gray-400">Not Connected</span>
                            </h2>
                            <div class="flex items-center gap-3 mt-2">
                                <p class="text-sm text-gray-400">Powered by Ollama</p>
                                <div class="flex items-center gap-2">
                                    <label class="text-xs text-gray-500">Personality:</label>
                                    <select id="ai-preprompt" class="bg-midnight-800 border border-white/10 rounded px-2 py-1 text-xs" onchange="updatePreprompt()">
                                        <option value="">⏳ Loading...</option>
                                    </select>
                                </div>
                            </div>
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
                    
                    <!-- Preprompt Manager -->
                    <div class="glass rounded-xl overflow-hidden">
                        <div class="px-4 py-3 border-b border-white/10">
                            <h3 class="font-semibold text-sm">🎭 Preprompt Manager</h3>
                        </div>
                        <div class="p-4 space-y-3">
                            <!-- AI Refine -->
                            <div>
                                <label class="text-xs text-gray-400 mb-1 block">🤖 AI Refine (Generate)</label>
                                <div class="flex gap-2">
                                    <input id="ai-refine-text" type="text" placeholder="coin collector, chef, detective..." 
                                           class="flex-1 bg-midnight-800 border border-white/10 rounded px-2 py-1.5 text-xs">
                                    <button onclick="aiRefinePreprompt()" 
                                            class="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 rounded text-xs font-medium whitespace-nowrap">
                                        Generate
                                    </button>
                                </div>
                            </div>
                            
                            <!-- Import MD File -->
                            <div>
                                <label class="text-xs text-gray-400 mb-1 block">📁 Import .md File</label>
                                <input id="preprompt-file-upload" type="file" accept=".md,.txt" 
                                       onchange="importPrepromptFile(this)"
                                       class="w-full text-xs bg-midnight-800 border border-white/10 rounded px-2 py-1.5 file:mr-2 file:py-1 file:px-3 file:rounded file:border-0 file:text-xs file:bg-purple-600 file:text-white hover:file:bg-purple-500">
                            </div>
                            
                            <!-- Library Browser -->
                            <div>
                                <button onclick="togglePrepromptLibrary()" 
                                        class="w-full text-left p-2 bg-white/5 hover:bg-white/10 rounded-lg text-xs font-medium">
                                    📚 Browse Library
                                </button>
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
    <div id="modal" class="fixed inset-0 bg-black/80 backdrop-blur-sm hidden z-50 flex items-center justify-center p-4" onclick="if(event.target.id==='modal'){{closeModal();}}">
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
        // ═══════════════════════════════════════════════════════════════════
        // DOCSTRING FORMATTER - Makes tool docstrings human-readable
        // ═══════════════════════════════════════════════════════════════════
        
        function formatDocstring(docstring) {{
            if (!docstring || docstring.trim() === '') {{
                return '<div class="text-gray-500 italic">No description available</div>';
            }}
            
            // Clean up the docstring
            let text = docstring.trim();
            
            // Split into sections
            const sections = {{
                brief: '',
                detailed: '',
                args: '',
                returns: '',
                examples: '',
                usage: '',
                raises: '',
                notes: '',
                seeAlso: ''
            }};
            
            // Extract brief description (first line or paragraph)
            const lines = text.split('\\n');
            let currentSection = 'brief';
            let currentContent = [];
            let inCodeBlock = false;
            
            for (let i = 0; i < lines.length; i++) {{
                const originalLine = lines[i];
                const trimmed = originalLine.trim();
                
                // Skip empty lines at start
                if (i === 0 && trimmed === '') continue;
                
                // Detect code blocks (preserve original line including leading spaces)
                if (trimmed.startsWith('```')) {{
                    inCodeBlock = !inCodeBlock;
                    currentContent.push(originalLine);
                    continue;
                }}
                
                // If in code block, preserve line as-is
                if (inCodeBlock) {{
                    currentContent.push(originalLine);
                    continue;
                }}
                
                const line = trimmed;
                
                // Detect section headers (case-insensitive)
                const sectionPatterns = {{
                    'args': /^(Args|Parameters|Arguments):/i,
                    'returns': /^(Returns?|Return):/i,
                    'examples': /^(Examples?|Example):/i,
                    'usage': /^(Usage|When to use):/i,
                    'raises': /^(Raises?|Exceptions?):/i,
                    'notes': /^(Notes?|Note):/i,
                    'seeAlso': /^(See Also|See|Related):/i
                }};
                
                let sectionFound = false;
                for (const [section, pattern] of Object.entries(sectionPatterns)) {{
                    if (pattern.test(line)) {{
                        // Save previous section
                        if (currentSection !== 'brief' && currentContent.length > 0) {{
                            sections[currentSection] = currentContent.join('\\n').trim();
                        }} else if (currentSection === 'brief' && currentContent.length > 0) {{
                            sections.brief = currentContent.join('\\n').trim();
                            sections.detailed = '';
                        }}
                        // Start new section
                        currentSection = section;
                        currentContent = [];
                        sectionFound = true;
                        break;
                    }}
                }}
                
                if (!sectionFound) {{
                    // First non-empty line after brief becomes detailed description
                    if (currentSection === 'brief' && line && sections.brief && !sections.detailed) {{
                        sections.detailed = line;
                        currentContent = [line];
                    }} else {{
                        currentContent.push(line);
                    }}
                }}
            }}
            
            // Save last section
            if (currentContent.length > 0) {{
                if (currentSection === 'brief') {{
                    sections.brief = currentContent.join('\\n').trim();
                }} else {{
                    sections[currentSection] = currentContent.join('\\n').trim();
                }}
            }}
            
            // If no sections found, treat entire docstring as brief
            if (!sections.brief && !sections.args && !sections.returns) {{
                sections.brief = text;
            }}
            
            // Build HTML
            let html = '<div class="space-y-4">';
            
            // Brief description
            if (sections.brief) {{
                html += `<div class="text-base text-gray-200 leading-relaxed">${{formatText(sections.brief)}}</div>`;
            }}
            
            // Detailed description
            if (sections.detailed) {{
                html += `<div class="text-sm text-gray-300 mt-2 leading-relaxed">${{formatText(sections.detailed)}}</div>`;
            }}
            
            // Usage section
            if (sections.usage) {{
                html += `<div class="mt-4 pt-3 border-t border-white/10">
                    <div class="text-xs font-semibold text-indigo-400 uppercase tracking-wide mb-2">Usage</div>
                    <div class="text-sm text-gray-300 leading-relaxed">${{formatText(sections.usage)}}</div>
                </div>`;
            }}
            
            // Args section
            if (sections.args) {{
                html += `<div class="mt-4 pt-3 border-t border-white/10">
                    <div class="text-xs font-semibold text-indigo-400 uppercase tracking-wide mb-2">Parameters</div>
                    <div class="text-sm text-gray-300 space-y-2">${{formatArgs(sections.args)}}</div>
                </div>`;
            }}
            
            // Returns section
            if (sections.returns) {{
                html += `<div class="mt-4 pt-3 border-t border-white/10">
                    <div class="text-xs font-semibold text-indigo-400 uppercase tracking-wide mb-2">Returns</div>
                    <div class="text-sm text-gray-300 leading-relaxed">${{formatText(sections.returns)}}</div>
                </div>`;
            }}
            
            // Examples section
            if (sections.examples) {{
                html += `<div class="mt-4 pt-3 border-t border-white/10">
                    <div class="text-xs font-semibold text-indigo-400 uppercase tracking-wide mb-2">Examples</div>
                    <div class="text-sm text-gray-300">${{formatExamples(sections.examples)}}</div>
                </div>`;
            }}
            
            // Raises section
            if (sections.raises) {{
                html += `<div class="mt-4 pt-3 border-t border-white/10">
                    <div class="text-xs font-semibold text-yellow-400 uppercase tracking-wide mb-2">Raises</div>
                    <div class="text-sm text-gray-300">${{formatText(sections.raises)}}</div>
                </div>`;
            }}
            
            // Notes section
            if (sections.notes) {{
                html += `<div class="mt-4 pt-3 border-t border-white/10">
                    <div class="text-xs font-semibold text-blue-400 uppercase tracking-wide mb-2">Notes</div>
                    <div class="text-sm text-gray-300">${{formatText(sections.notes)}}</div>
                </div>`;
            }}
            
            // See Also section
            if (sections.seeAlso) {{
                html += `<div class="mt-4 pt-3 border-t border-white/10">
                    <div class="text-xs font-semibold text-purple-400 uppercase tracking-wide mb-2">See Also</div>
                    <div class="text-sm text-gray-300">${{formatText(sections.seeAlso)}}</div>
                </div>`;
            }}
            
            html += '</div>';
            return html;
        }}
        
        function escapeHtml(text) {{
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }}
        
        function formatText(text) {{
            if (!text) return '';
            
            // Handle code blocks first (before escaping HTML)
            const codeBlockRegex = /```(\\w+)?\\n([\\s\\S]*?)```/g;
            const codeBlocks = [];
            let codeBlockIndex = 0;
            let processed = text.replace(codeBlockRegex, (match, lang, code) => {{
                const placeholder = `__CODE_BLOCK_${{codeBlockIndex}}__`;
                codeBlocks.push({{ lang: lang || '', code: code.trim() }});
                codeBlockIndex++;
                return placeholder;
            }});
            
            // Convert markdown-style formatting
            let formatted = escapeHtml(processed);
            
            // Restore code blocks with proper formatting
            codeBlocks.forEach((block, idx) => {{
                const placeholder = `__CODE_BLOCK_${{idx}}__`;
                formatted = formatted.replace(placeholder, 
                    `<pre class="bg-black/40 p-3 rounded text-xs text-gray-300 font-mono overflow-x-auto border border-white/10 my-2"><code>${{escapeHtml(block.code)}}</code></pre>`
                );
            }});
            
            // Convert **bold** to <strong>
            formatted = formatted.replace(/\\*\\*(.+?)\\*\\*/g, '<strong class="text-white font-semibold">$1</strong>');
            
            // Convert *italic* to <em>
            formatted = formatted.replace(/(?<!\\*)\\*(?!\\*)([^*]+?)\\*(?!\\*)/g, '<em class="text-gray-300">$1</em>');
            
            // Convert `code` to <code> (inline code, not in code blocks)
            formatted = formatted.replace(/`([^`\\n]+)`/g, '<code class="bg-black/30 px-1 py-0.5 rounded text-indigo-300 font-mono text-xs">$1</code>');
            
            // Convert bullet points (properly handle lists)
            const lines = formatted.split('<br>');
            let inList = false;
            let listItems = [];
            let result = [];
            
            for (let i = 0; i < lines.length; i++) {{
                const line = lines[i];
                const bulletMatch = line.match(/^([-*]|\\d+\\.)\\s+(.+)$/);
                
                if (bulletMatch) {{
                    if (!inList) {{
                        if (listItems.length > 0) {{
                            result.push(listItems.join(''));
                            listItems = [];
                        }}
                        inList = true;
                    }}
                    listItems.push(`<li class="ml-4 mb-1">${{bulletMatch[2]}}</li>`);
                }} else {{
                    if (inList) {{
                        result.push(`<ul class="list-disc space-y-1 my-2 ml-4">${{listItems.join('')}}</ul>`);
                        listItems = [];
                        inList = false;
                    }}
                    if (line.trim()) {{
                        result.push(line);
                    }}
                }}
            }}
            
            if (inList && listItems.length > 0) {{
                result.push(`<ul class="list-disc space-y-1 my-2 ml-4">${{listItems.join('')}}</ul>`);
            }}
            
            formatted = result.length > 0 ? result.join('<br>') : formatted;
            
            // Convert line breaks (but preserve existing HTML)
            if (!formatted.includes('<pre>') && !formatted.includes('<ul>')) {{
                formatted = formatted.replace(/\\n/g, '<br>');
            }}
            
            return formatted;
        }}
        
        function formatArgs(argsText) {{
            if (!argsText) return '';
            
            const lines = argsText.split('\\n');
            let html = '';
            let currentParam = null;
            let paramDetails = [];
            
            for (const line of lines) {{
                const trimmed = line.trim();
                if (!trimmed) continue;
                
                // Check if this is a parameter name (supports various formats):
                // - name: description
                // - name (type): description
                // - name (type, optional): description
                const paramMatch = trimmed.match(/^(\\w+)(?:\\s*\\(([^)]+)\\))?:\\s*(.+)$/);
                if (paramMatch) {{
                    // Save previous param
                    if (currentParam) {{
                        const typeInfo = currentParam.type ? `<span class="text-purple-400 text-xs">(${{currentParam.type}})</span>` : '';
                        html += `<div class="mb-3 pb-2 border-b border-white/5">
                            <div class="flex items-center gap-2">
                                <span class="font-mono text-indigo-300 font-semibold">${{currentParam.name}}</span>
                                ${{typeInfo}}
                            </div>
                            <div class="text-gray-400 text-xs ml-4 mt-1">${{formatText(currentParam.desc)}}</div>
                            ${{paramDetails.length > 0 ? `<ul class="text-xs text-gray-500 ml-6 mt-1 space-y-1 list-disc">${{paramDetails.map(d => `<li>${{formatText(d)}}</li>`).join('')}}</ul>` : ''}}
                        </div>`;
                    }}
                    // Start new param
                    currentParam = {{ 
                        name: paramMatch[1], 
                        type: paramMatch[2] || null,
                        desc: paramMatch[3] 
                    }};
                    paramDetails = [];
                }} else if (trimmed.match(/^[-*]\\s+/) && currentParam) {{
                    // Detail line for current param (bullet point)
                    paramDetails.push(trimmed.replace(/^[-*]\\s+/, ''));
                }} else if (trimmed.match(/^\\s{(4,)}/) && currentParam) {{
                    // Indented continuation line
                    currentParam.desc += ' ' + trimmed.trim();
                }} else if (currentParam && !trimmed.match(/^\\w+:/)) {{
                    // Continuation of param description (not a new param)
                    currentParam.desc += ' ' + trimmed;
                }}
            }}
            
            // Save last param
            if (currentParam) {{
                const typeInfo = currentParam.type ? `<span class="text-purple-400 text-xs">(${{currentParam.type}})</span>` : '';
                html += `<div class="mb-3 pb-2 border-b border-white/5">
                    <div class="flex items-center gap-2">
                        <span class="font-mono text-indigo-300 font-semibold">${{currentParam.name}}</span>
                        ${{typeInfo}}
                    </div>
                    <div class="text-gray-400 text-xs ml-4 mt-1">${{formatText(currentParam.desc)}}</div>
                    ${{paramDetails.length > 0 ? `<ul class="text-xs text-gray-500 ml-6 mt-1 space-y-1 list-disc">${{paramDetails.map(d => `<li>${{formatText(d)}}</li>`).join('')}}</ul>` : ''}}
                </div>`;
            }}
            
            return html || formatText(argsText);
        }}
        
        function formatExamples(examplesText) {{
            if (!examplesText) return '';
            
            // Check if it's already a code block
            const codeBlockMatch = examplesText.match(/```(\\w+)?\\n([\\s\\S]*?)```/);
            if (codeBlockMatch) {{
                return `<pre class="bg-black/40 p-3 rounded text-xs text-gray-300 font-mono overflow-x-auto border border-white/10 my-2"><code>${{escapeHtml(codeBlockMatch[2].trim())}}</code></pre>`;
            }}
            
            // Split by example headers (e.g., "Example 1:", "Basic usage:", etc.)
            const parts = examplesText.split(/(?:^|\\n)([A-Z][^:\\n]+:)/gm);
            let html = '<div class="space-y-4">';
            let hasStructured = false;
            
            for (let i = 0; i < parts.length; i += 2) {{
                if (i + 1 < parts.length && parts[i + 2]) {{
                    const title = parts[i + 1].replace(':', '').trim();
                    const code = parts[i + 2].trim();
                    
                    if (code) {{
                        hasStructured = true;
                        html += `<div class="mb-4">
                            <div class="text-xs font-semibold text-green-400 mb-2">${{escapeHtml(title)}}</div>
                            <pre class="bg-black/40 p-3 rounded text-xs text-gray-300 font-mono overflow-x-auto border border-white/10"><code>${{escapeHtml(code)}}</code></pre>
                        </div>`;
                    }}
                }}
            }}
            
            // If no structured examples, check for plain code or format as text
            if (!hasStructured) {{
                const trimmed = examplesText.trim();
                // If it looks like code (has indentation, keywords, etc.), format as code block
                if (trimmed.match(/^(def |class |import |from |\\s{(4,)})/m)) {{
                    html = `<pre class="bg-black/40 p-3 rounded text-xs text-gray-300 font-mono overflow-x-auto border border-white/10"><code>${{escapeHtml(trimmed)}}</code></pre>`;
                }} else {{
                    // Format as regular text with markdown support
                    html = formatText(trimmed);
                }}
            }} else {{
                html += '</div>';
            }}
            
            return html;
        }}
        
        // ═══════════════════════════════════════════════════════════════════
        // END DOCSTRING FORMATTER
        // ═══════════════════════════════════════════════════════════════════
        
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
                    <div class="flex items-center justify-between p-3 bg-white/5 rounded-lg hover:bg-white/10">
                        <div class="flex items-center gap-3 flex-1 cursor-pointer" onclick="switchTab('clients'); setTimeout(() => document.getElementById('clients-detail').scrollIntoView({{behavior: 'smooth', block: 'start'}}), 100);">
                            <span class="text-lg">${{icon}}</span>
                            <div>
                                <div class="font-medium">${{client.replace('-', ' ').replace(/\\b\\w/g, l => l.toUpperCase())}}</div>
                                <div class="text-xs text-gray-400">${{data.servers.length}} servers</div>
                            </div>
                        </div>
                        <button class="text-gray-400 hover:text-indigo-400 transition-colors px-2 py-1 rounded hover:bg-white/5" onclick="event.stopPropagation(); showClientInfo('${{client}}')" title="Show client information">
                            →
                        </button>
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

        // Client information database
        const clientInfo = {{
            'claude-desktop': {{
                name: 'Claude Desktop',
                description: 'Official desktop application from Anthropic for interacting with Claude AI.',
                website: 'https://claude.ai/download',
                configLocation: 'Config file contains MCP server definitions used by Claude Desktop.',
                icon: '🟣',
                developer: 'Anthropic'
            }},
            'cursor': {{
                name: 'Cursor IDE',
                description: 'AI-first code editor built on VS Code, designed for pair programming with AI.',
                website: 'https://cursor.sh',
                configLocation: 'Uses Cline extension settings or .cursor/mcp.json for MCP server configuration.',
                icon: '🔵',
                developer: 'Cursor'
            }},
            'windsurf-ide': {{
                name: 'Windsurf IDE',
                description: 'AI-powered code editor from Codeium, built for modern development workflows.',
                website: 'https://codeium.com/windsurf',
                configLocation: 'MCP servers configured in Windsurf settings or mcp_config.json.',
                icon: '🟢',
                developer: 'Codeium'
            }},
            'zed-ide': {{
                name: 'Zed Editor',
                description: 'High-performance, multiplayer code editor written in Rust with AI capabilities.',
                website: 'https://zed.dev',
                configLocation: 'MCP servers configured in settings.json under mcpServers key.',
                icon: '⚡',
                developer: 'Zed Industries'
            }},
            'antigravity-ide': {{
                name: 'Antigravity IDE',
                description: 'AI-powered IDE from Google with integrated MCP server support.',
                website: 'https://antigravity.google',
                configLocation: 'MCP servers managed through the IDE UI, stored in mcp_config.json.',
                icon: '🚀',
                developer: 'Google'
            }},
            'cline': {{
                name: 'Cline (VSCode Extension)',
                description: 'VSCode extension for Claude AI, formerly known as Claude Dev.',
                website: 'https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev',
                configLocation: 'MCP servers configured in VSCode globalStorage settings.',
                icon: '💜',
                developer: 'Saoud Rizwan'
            }}
        }};

        function showClientInfo(clientName) {{
            const info = clientInfo[clientName] || {{
                name: clientName.replace('-', ' ').replace(/\\b\\w/g, l => l.toUpperCase()),
                description: 'MCP client application.',
                website: '',
                configLocation: 'Configuration file location varies.',
                icon: '🔌',
                developer: 'Unknown'
            }};
            
            const clientData = clientsData[clientName] || {{ servers: [], path: 'Not found' }};
            
            const modal = document.getElementById('modal');
            const modalTitle = document.getElementById('modal-title');
            const modalContent = document.getElementById('modal-content');
            
            modalTitle.innerHTML = `${{info.icon}} ${{info.name}}`;
            modalContent.innerHTML = `
                <div class="space-y-4">
                    <div>
                        <h3 class="text-sm font-semibold text-gray-400 mb-2">Description</h3>
                        <p class="text-sm text-gray-300">${{info.description}}</p>
                    </div>
                    
                    <div>
                        <h3 class="text-sm font-semibold text-gray-400 mb-2">Developer</h3>
                        <p class="text-sm text-gray-300">${{info.developer}}</p>
                    </div>
                    
                    ${{info.website ? `
                    <div>
                        <h3 class="text-sm font-semibold text-gray-400 mb-2">Website</h3>
                        <a href="${{info.website}}" target="_blank" class="text-sm text-indigo-400 hover:text-indigo-300 underline">${{info.website}}</a>
                    </div>
                    ` : ''}}
                    
                    <div>
                        <h3 class="text-sm font-semibold text-gray-400 mb-2">Configuration</h3>
                        <p class="text-xs text-gray-400 mono bg-black/30 p-2 rounded">${{clientData.path}}</p>
                        <p class="text-xs text-gray-500 mt-1">${{info.configLocation}}</p>
                    </div>
                    
                    <div>
                        <div class="flex items-center justify-between mb-2">
                            <h3 class="text-sm font-semibold text-gray-400">MCP Servers (${{clientData.servers.length}})</h3>
                            <button onclick="showAddServerForm('${{clientName}}')" class="text-xs px-3 py-1 bg-indigo-600 hover:bg-indigo-500 rounded">
                                + Add Server
                            </button>
                        </div>
                        ${{clientData.servers.length > 0 ? `
                        <div class="mt-2 space-y-2 max-h-64 overflow-y-auto">
                            ${{clientData.servers.map(s => `
                                <div class="bg-black/30 p-3 rounded-lg border border-white/10">
                                    <div class="flex items-start justify-between">
                                        <div class="flex-1">
                                            <div class="flex items-center gap-2 mb-1">
                                                <span class="text-sm font-medium text-indigo-400">${{s.name}}</span>
                                                <span class="text-xs text-gray-500">(${{s.id}})</span>
                                                ${{s.type && s.type !== 'stdio' ? `<span class="text-xs px-1.5 py-0.5 bg-purple-600/30 text-purple-300 rounded">${{s.type}}</span>` : ''}}
                                            </div>
                                            <div class="text-xs text-gray-400 mono space-y-1">
                                                <div><span class="text-gray-500">Command:</span> ${{s.command || '(none)'}}</div>
                                                ${{s.args && s.args.length > 0 ? `<div><span class="text-gray-500">Args:</span> ${{s.args.join(' ')}}</div>` : ''}}
                                                ${{s.cwd ? `<div><span class="text-gray-500">CWD:</span> ${{s.cwd}}</div>` : ''}}
                                                ${{s.url ? `<div><span class="text-gray-500">URL:</span> ${{s.url}}</div>` : ''}}
                                                ${{s.env && Object.keys(s.env).length > 0 ? `<div><span class="text-gray-500">Env:</span> ${{Object.keys(s.env).length}} variable(s)</div>` : ''}}
                                            </div>
                                        </div>
                                        <div class="flex gap-1 ml-2">
                                            <button onclick="editServer('${{clientName}}', '${{s.id}}')" class="text-xs px-2 py-1 bg-blue-600/50 hover:bg-blue-600 rounded" title="Edit">
                                                ✏️
                                            </button>
                                            <button onclick="deleteServer('${{clientName}}', '${{s.id}}')" class="text-xs px-2 py-1 bg-red-600/50 hover:bg-red-600 rounded" title="Delete">
                                                🗑️
                                            </button>
                                        </div>
                                    </div>
                                </div>
                            `).join('')}}
                        </div>
                        ` : '<p class="text-xs text-gray-500 italic">No servers configured. Click "Add Server" to add one.</p>'}}
                    </div>
                </div>
            `;
            modal.classList.remove('hidden');
        }}

        async function showAddServerForm(clientName) {{
            const modal = document.getElementById('modal');
            const modalTitle = document.getElementById('modal-title');
            const modalContent = document.getElementById('modal-content');
            
            // Load available servers from repos
            let availableServers = [];
            try {{
                const res = await fetch('/api/available-servers');
                availableServers = await res.json();
            }} catch (e) {{
                console.error('Error loading available servers:', e);
            }}
            
            modalTitle.innerHTML = `➕ Add MCP Server to ${{clientName}}`;
            modalContent.innerHTML = `
                <form id="add-server-form" class="space-y-4">
                    ${{availableServers.length > 0 ? `
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-1">Select from Scanned Repos</label>
                        <select id="server-template" class="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm" onchange="fillServerFromTemplate()">
                            <option value="">-- Choose a server from repos --</option>
                            ${{availableServers.map(s => {{
                                let methodIcon = '🐍';
                                let methodLabel = 'Python';
                                if (s.has_mcpb) {{
                                    methodIcon = '📦';
                                    methodLabel = 'MCPB';
                                }} else if (s.has_npm) {{
                                    methodIcon = '📦';
                                    methodLabel = 'npm/npx';
                                }}
                                const sourceIcon = s.source && s.source.includes('MCPB') ? '📦' : s.source && s.source.includes('npm') ? '📦' : s.source === 'README.md' ? '📖' : s.source === 'pyproject.toml' ? '📦' : '🔍';
                                const sourceLabel = s.source || 'inferred';
                                return `
                                <option value="${{s.id}}" 
                                    data-command="${{s.command}}" 
                                    data-args="${{JSON.stringify(s.args)}}" 
                                    data-cwd="${{s.cwd || ''}}" 
                                    data-env="${{JSON.stringify(s.env || null)}}" 
                                    data-name="${{s.name}}" 
                                    data-type="${{s.type || 'stdio'}}" 
                                    data-url="${{s.url || ''}}"
                                    data-has-mcpb="${{s.has_mcpb || false}}"
                                    data-has-npm="${{s.has_npm || false}}"
                                    data-repo="${{s.repo}}">
                                    ${{methodIcon}} ${{s.name}} (${{s.repo}}) - ${{s.tools}} tools [${{methodLabel}}]
                                </option>
                            `}}).join('')}}
                        </select>
                        <p class="text-xs text-gray-500 mt-1">Select a server. MCPB 📦 is preferred, then npm/npx 📦, then Python 🐍. README configs may be outdated.</p>
                        <div id="installation-hints" class="mt-2 text-xs text-gray-400 hidden"></div>
                    </div>
                    <div class="border-t border-white/10 pt-4">
                        <p class="text-sm text-gray-400 mb-3">Or enter manually:</p>
                    </div>
                    ` : `
                    <div class="bg-yellow-600/20 border border-yellow-600/50 rounded-lg p-3 mb-4">
                        <p class="text-sm text-yellow-300 mb-2">⚠️ No servers found from repos</p>
                        <p class="text-xs text-yellow-400/80">Scan your repositories first to auto-fill server configurations. Go to the <strong>Repos</strong> tab and click "Scan" to discover available MCP servers.</p>
                    </div>
                    `}}
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-1">Server ID</label>
                        <input type="text" id="server-id" required class="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm" placeholder="my-server-name">
                        <p class="text-xs text-gray-500 mt-1">Unique identifier (lowercase, hyphens)</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-1">Name</label>
                        <input type="text" id="server-name" class="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm" placeholder="My Server Name">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-1">Command</label>
                        <input type="text" id="server-command" required class="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm mono" placeholder="python">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-1">Arguments (one per line)</label>
                        <textarea id="server-args" class="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm mono" rows="3" placeholder="-m&#10;my_module"></textarea>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-1">Working Directory (optional)</label>
                        <input type="text" id="server-cwd" class="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm mono" placeholder="/path/to/directory">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-1">Type</label>
                        <select id="server-type" class="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm">
                            <option value="stdio">stdio (default)</option>
                            <option value="http">http</option>
                        </select>
                    </div>
                    <div id="server-url-container" class="hidden">
                        <label class="block text-sm font-medium text-gray-400 mb-1">URL (for http type)</label>
                        <input type="text" id="server-url" class="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm mono" placeholder="http://localhost:8000">
                    </div>
                    <div class="flex gap-2 pt-2">
                        <button type="submit" class="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded text-sm">
                            Add Server
                        </button>
                        <button type="button" onclick="closeModal(); setTimeout(() => showClientInfo('${{clientName}}'), 100)" class="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded text-sm">
                            Cancel
                        </button>
                    </div>
                </form>
            `;
            
            // Function to fill form from template
            window.fillServerFromTemplate = function() {{
                const select = document.getElementById('server-template');
                const option = select.options[select.selectedIndex];
                if (!option || !option.value) {{
                    document.getElementById('installation-hints').classList.add('hidden');
                    return;
                }}
                
                const command = option.dataset.command;
                const args = JSON.parse(option.dataset.args || '[]');
                const cwd = option.dataset.cwd;
                const env = JSON.parse(option.dataset.env || '{{}}');
                const name = option.dataset.name;
                const type = option.dataset.type || 'stdio';
                const url = option.dataset.url || '';
                const hasMcpb = option.dataset.hasMcpb === 'true';
                const hasNpm = option.dataset.hasNpm === 'true';
                const repo = option.dataset.repo;
                
                // Show installation hints
                const hintsDiv = document.getElementById('installation-hints');
                hintsDiv.classList.remove('hidden');
                
                let hintsHtml = '<div class="bg-blue-600/20 border border-blue-600/50 rounded p-2 space-y-1">';
                hintsHtml += '<p class="font-semibold text-blue-300">Installation Methods (in order):</p>';
                
                if (hasMcpb) {{
                    hintsHtml += '<p class="text-blue-200">1. 📦 <strong>MCPB (Recommended)</strong>: Open Claude Desktop → Settings → Developer → Add MCP Server → Paste path to manifest.json</p>';
                }}
                if (hasNpm) {{
                    hintsHtml += '<p class="text-blue-200">2. 📦 <strong>npm/npx</strong>: Use the auto-filled command below (if repo supports it)</p>';
                }}
                hintsHtml += '<p class="text-blue-200">3. 📋 <strong>JSON Snippet</strong>: Add the config below to your client config file</p>';
                hintsHtml += '<p class="text-blue-200">4. 🐍 <strong>Python</strong>: Clone repo and use Python setup (last resort)</p>';
                hintsHtml += '</div>';
                
                hintsDiv.innerHTML = hintsHtml;
                
                document.getElementById('server-id').value = option.value;
                if (document.getElementById('server-name')) {{
                    document.getElementById('server-name').value = name;
                }}
                document.getElementById('server-command').value = command;
                document.getElementById('server-args').value = args.join('\\n');
                if (cwd) {{
                    document.getElementById('server-cwd').value = cwd;
                }}
                if (document.getElementById('server-type')) {{
                    document.getElementById('server-type').value = type;
                    // Show/hide URL field
                    const urlContainer = document.getElementById('server-url-container');
                    if (type === 'http') {{
                        urlContainer.classList.remove('hidden');
                        if (url) {{
                            document.getElementById('server-url').value = url;
                        }}
                    }} else {{
                        urlContainer.classList.add('hidden');
                    }}
                }}
            }};
            
            // Show/hide URL field based on type
            document.getElementById('server-type').addEventListener('change', (e) => {{
                const urlContainer = document.getElementById('server-url-container');
                if (e.target.value === 'http') {{
                    urlContainer.classList.remove('hidden');
                }} else {{
                    urlContainer.classList.add('hidden');
                }}
            }});
            
            document.getElementById('add-server-form').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const formData = {{
                    id: document.getElementById('server-id').value.trim(),
                    name: document.getElementById('server-name').value.trim(),
                    command: document.getElementById('server-command').value.trim(),
                    args: document.getElementById('server-args').value.split('\\n').filter(a => a.trim()),
                    cwd: document.getElementById('server-cwd').value.trim() || undefined,
                    type: document.getElementById('server-type').value,
                    url: document.getElementById('server-url').value.trim() || undefined
                }};
                
                try {{
                    const res = await fetch(`/api/clients/${{clientName}}/servers`, {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(formData)
                    }});
                    
                    if (res.ok) {{
                        await loadClients();
                        closeModal();
                        setTimeout(() => showClientInfo(clientName), 100);
                    }} else {{
                        const error = await res.json();
                        alert(`Error: ${{error.detail || 'Failed to add server'}}`);
                    }}
                }} catch (e) {{
                    alert(`Error: ${{e.message}}`);
                }}
            }});
        }}

        async function editServer(clientName, serverId) {{
            const clientData = clientsData[clientName];
            const server = clientData.servers.find(s => s.id === serverId);
            if (!server) return;
            
            const modal = document.getElementById('modal');
            const modalTitle = document.getElementById('modal-title');
            const modalContent = document.getElementById('modal-content');
            
            modalTitle.innerHTML = `✏️ Edit Server: ${{server.name}}`;
            modalContent.innerHTML = `
                <form id="edit-server-form" class="space-y-4">
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-1">Server ID</label>
                        <input type="text" id="server-id" value="${{server.id}}" readonly class="w-full bg-black/50 border border-white/10 rounded px-3 py-2 text-sm" disabled>
                        <p class="text-xs text-gray-500 mt-1">ID cannot be changed</p>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-1">Command</label>
                        <input type="text" id="server-command" value="${{server.command || ''}}" required class="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm mono">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-1">Arguments (one per line)</label>
                        <textarea id="server-args" class="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm mono" rows="3">${{(server.args || []).join('\\n')}}</textarea>
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-1">Working Directory (optional)</label>
                        <input type="text" id="server-cwd" value="${{server.cwd || ''}}" class="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm mono">
                    </div>
                    <div>
                        <label class="block text-sm font-medium text-gray-400 mb-1">Type</label>
                        <select id="server-type" class="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm">
                            <option value="stdio" ${{!server.type || server.type === 'stdio' ? 'selected' : ''}}>stdio</option>
                            <option value="http" ${{server.type === 'http' ? 'selected' : ''}}>http</option>
                        </select>
                    </div>
                    <div id="server-url-container" class="${{server.type === 'http' ? '' : 'hidden'}}">
                        <label class="block text-sm font-medium text-gray-400 mb-1">URL (for http type)</label>
                        <input type="text" id="server-url" value="${{server.url || ''}}" class="w-full bg-black/30 border border-white/10 rounded px-3 py-2 text-sm mono">
                    </div>
                    <div class="flex gap-2 pt-2">
                        <button type="submit" class="flex-1 px-4 py-2 bg-indigo-600 hover:bg-indigo-500 rounded text-sm">
                            Save Changes
                        </button>
                        <button type="button" onclick="closeModal(); setTimeout(() => showClientInfo('${{clientName}}'), 100)" class="px-4 py-2 bg-gray-600 hover:bg-gray-500 rounded text-sm">
                            Cancel
                        </button>
                    </div>
                </form>
            `;
            
            document.getElementById('server-type').addEventListener('change', (e) => {{
                const urlContainer = document.getElementById('server-url-container');
                if (e.target.value === 'http') {{
                    urlContainer.classList.remove('hidden');
                }} else {{
                    urlContainer.classList.add('hidden');
                }}
            }});
            
            document.getElementById('edit-server-form').addEventListener('submit', async (e) => {{
                e.preventDefault();
                const formData = {{
                    command: document.getElementById('server-command').value.trim(),
                    args: document.getElementById('server-args').value.split('\\n').filter(a => a.trim()),
                    cwd: document.getElementById('server-cwd').value.trim() || undefined,
                    type: document.getElementById('server-type').value,
                    url: document.getElementById('server-url').value.trim() || undefined
                }};
                
                try {{
                    const res = await fetch(`/api/clients/${{clientName}}/servers/${{serverId}}`, {{
                        method: 'PUT',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify(formData)
                    }});
                    
                    if (res.ok) {{
                        await loadClients();
                        closeModal();
                        setTimeout(() => showClientInfo(clientName), 100);
                    }} else {{
                        const error = await res.json();
                        alert(`Error: ${{error.detail || 'Failed to update server'}}`);
                    }}
                }} catch (e) {{
                    alert(`Error: ${{e.message}}`);
                }}
            }});
        }}

        async function deleteServer(clientName, serverId) {{
            if (!confirm(`Delete server "${{serverId}}" from ${{clientName}}?`)) return;
            
            try {{
                const res = await fetch(`/api/clients/${{clientName}}/servers/${{serverId}}`, {{
                    method: 'DELETE'
                }});
                
                if (res.ok) {{
                    await loadClients();
                    closeModal();
                    setTimeout(() => showClientInfo(clientName), 100);
                }} else {{
                    const error = await res.json();
                    alert(`Error: ${{error.detail || 'Failed to delete server'}}`);
                }}
            }} catch (e) {{
                alert(`Error: ${{e.message}}`);
            }}
        }}

        // Show scanner criteria modal
        function showScannerCriteria() {{
            const modal = document.getElementById('modal');
            const modalTitle = document.getElementById('modal-title');
            const modalContent = document.getElementById('modal-content');
            
            modalTitle.textContent = '📋 Repository Classification Criteria';
            modalContent.innerHTML = `
                <div class="space-y-6">
                    <div class="text-sm text-gray-300 leading-relaxed">
                        <p>Repositories are classified into three categories based on code quality, structure, and best practices:</p>
                    </div>
                    
                    <!-- SOTA -->
                    <div class="border-l-4 border-green-500 pl-4">
                        <h3 class="text-lg font-semibold text-green-400 mb-2">✅ SOTA (State of the Art)</h3>
                        <p class="text-sm text-gray-300 mb-3">Repositories with no issues - following all best practices.</p>
                        <p class="text-xs text-gray-400 italic">No "runt_reasons" found during analysis.</p>
                    </div>
                    
                    <!-- Improvable -->
                    <div class="border-l-4 border-yellow-500 pl-4">
                        <h3 class="text-lg font-semibold text-yellow-400 mb-2">⚠️ Improvable</h3>
                        <p class="text-sm text-gray-300 mb-3">Repositories with minor issues that should be addressed, but not critical.</p>
                        <p class="text-xs text-gray-400 italic">Has "runt_reasons" but "is_runt" is false.</p>
                    </div>
                    
                    <!-- Runt -->
                    <div class="border-l-4 border-red-500 pl-4">
                        <h3 class="text-lg font-semibold text-red-400 mb-2">🐛 Runt</h3>
                        <p class="text-sm text-gray-300 mb-3">Repositories with critical issues that need immediate attention.</p>
                        <p class="text-xs text-gray-400 italic mb-4">"is_runt" is true due to critical issues.</p>
                        
                        <div class="bg-red-500/10 border border-red-500/30 rounded p-3 mt-3">
                            <h4 class="text-sm font-semibold text-red-300 mb-2">Critical Issues (Marks as Runt):</h4>
                            <ul class="text-xs text-gray-300 space-y-1 list-disc list-inside">
                                <li>FastMCP version &lt; 2.10.0 (ancient version)</li>
                                <li>No CI/CD workflows (for repos with ≥10 tools)</li>
                            </ul>
                        </div>
                    </div>
                    
                    <!-- All Criteria -->
                    <div class="border-t border-white/10 pt-4">
                        <h3 class="text-lg font-semibold mb-3">📊 All Checked Criteria</h3>
                        <div class="space-y-4">
                            <div>
                                <h4 class="text-sm font-semibold text-indigo-400 mb-2">FastMCP Version</h4>
                                <ul class="text-xs text-gray-300 space-y-1 list-disc list-inside ml-4">
                                    <li><span class="text-red-400">Critical:</span> Version &lt; 2.10.0 → Runt</li>
                                    <li><span class="text-yellow-400">Warning:</span> Version &lt; 2.12.0 → Recommendation</li>
                                    <li><span class="text-green-400">Good:</span> Version ≥ 2.13.1 (latest)</li>
                                </ul>
                            </div>
                            
                            <div>
                                <h4 class="text-sm font-semibold text-indigo-400 mb-2">Tool Organization</h4>
                                <ul class="text-xs text-gray-300 space-y-1 list-disc list-inside ml-4">
                                    <li>≥20 tools without portmanteau pattern → Issue</li>
                                    <li>Tools split between server.py and tools/ → Issue</li>
                                    <li>Multiple server files found → Issue</li>
                                </ul>
                            </div>
                            
                            <div>
                                <h4 class="text-sm font-semibold text-indigo-400 mb-2">CI/CD & Testing</h4>
                                <ul class="text-xs text-gray-300 space-y-1 list-disc list-inside ml-4">
                                    <li><span class="text-red-400">Critical:</span> No CI/CD (≥10 tools) → Runt</li>
                                    <li>No tests/ directory (≥10 tools) → Issue</li>
                                </ul>
                            </div>
                            
                            <div>
                                <h4 class="text-sm font-semibold text-indigo-400 mb-2">Project Structure</h4>
                                <ul class="text-xs text-gray-300 space-y-1 list-disc list-inside ml-4">
                                    <li>No src/ directory → Issue</li>
                                    <li>No tests/ directory (≥10 tools) → Issue</li>
                                    <li>No scripts/ directory → Recommendation</li>
                                </ul>
                            </div>
                            
                            <div>
                                <h4 class="text-sm font-semibold text-indigo-400 mb-2">Packaging & Distribution</h4>
                                <ul class="text-xs text-gray-300 space-y-1 list-disc list-inside ml-4">
                                    <li>No manifest.json (≥5 tools) → Issue</li>
                                    <li>Uses deprecated DXT instead of MCPB → Issue</li>
                                    <li>Uses setup.py without pyproject.toml → Issue</li>
                                </ul>
                            </div>
                            
                            <div>
                                <h4 class="text-sm font-semibold text-indigo-400 mb-2">Documentation</h4>
                                <ul class="text-xs text-gray-300 space-y-1 list-disc list-inside ml-4">
                                    <li>No README → Issue</li>
                                    <li>No LICENSE file → Issue</li>
                                    <li>No .cursorrules → Issue</li>
                                </ul>
                            </div>
                            
                            <div>
                                <h4 class="text-sm font-semibold text-indigo-400 mb-2">Version Control</h4>
                                <ul class="text-xs text-gray-300 space-y-1 list-disc list-inside ml-4">
                                    <li>No git repository → Issue</li>
                                    <li>No git remote configured → Issue</li>
                                </ul>
                            </div>
                            
                            <div>
                                <h4 class="text-sm font-semibold text-indigo-400 mb-2">Code Quality</h4>
                                <ul class="text-xs text-gray-300 space-y-1 list-disc list-inside ml-4">
                                    <li>&gt;3 print() calls in server (should use logging) → Issue</li>
                                    <li>Monolithic server.py &gt;1000 lines → Issue</li>
                                    <li>Missing proper docstrings (Args/Returns) → Issue</li>
                                </ul>
                            </div>
                        </div>
                    </div>
                    
                    <div class="bg-indigo-500/10 border border-indigo-500/30 rounded p-3 mt-4">
                        <p class="text-xs text-gray-300">
                            <strong class="text-indigo-300">Note:</strong> Issues are cumulative. A repository can have multiple issues, 
                            but only critical issues (FastMCP version, CI/CD) will mark it as a Runt. 
                            Multiple non-critical issues will mark it as Improvable.
                        </p>
                    </div>
                </div>
            `;
            modal.classList.remove('hidden');
        }}
        
        // Load repos with progress tracking
        async function loadRepos() {{
            // Show progress UI
            const progressHtml = `
                <div class="p-4 space-y-3">
                    <div class="text-sm font-semibold text-indigo-400 mb-3">🔍 Scanning Repositories...</div>
                    <div id="scan-progress-display" class="space-y-2">
                        <div class="flex items-center justify-between text-xs">
                            <span class="text-gray-400">Current:</span>
                            <span id="scan-current" class="text-gray-300 font-mono">-</span>
                        </div>
                        <div class="flex items-center justify-between text-xs">
                            <span class="text-gray-400">Progress:</span>
                            <span id="scan-progress" class="text-gray-300">0 / 0</span>
                        </div>
                        <div class="w-full bg-black/30 rounded-full h-2">
                            <div id="scan-progress-bar" class="bg-indigo-600 h-2 rounded-full transition-all duration-300" style="width: 0%"></div>
                        </div>
                        <div class="grid grid-cols-3 gap-2 mt-3 text-xs">
                            <div class="bg-green-500/10 p-2 rounded text-center">
                                <div id="scan-found" class="text-green-400 font-bold">0</div>
                                <div class="text-gray-500">MCP Repos</div>
                            </div>
                            <div class="bg-gray-500/10 p-2 rounded text-center">
                                <div id="scan-skipped" class="text-gray-400 font-bold">0</div>
                                <div class="text-gray-500">Skipped</div>
                            </div>
                            <div class="bg-red-500/10 p-2 rounded text-center">
                                <div id="scan-errors" class="text-red-400 font-bold">0</div>
                                <div class="text-gray-500">Errors</div>
                            </div>
                        </div>
                        <div class="mt-3 max-h-32 overflow-y-auto bg-black/20 rounded p-2">
                            <div id="scan-activity" class="text-xs text-gray-400 font-mono space-y-1">
                                <div>Waiting for scan to start...</div>
                            </div>
                        </div>
                    </div>
                </div>
            `;
            document.getElementById('repos-health').innerHTML = progressHtml;
            document.getElementById('repos-detail').innerHTML = progressHtml;
            
            // Start polling for progress
            const progressInterval = setInterval(async () => {{
                try {{
                    const progressRes = await fetch('/api/progress');
                    const progress = await progressRes.json();
                    
                    if (progress.status === 'scanning') {{
                        // Update progress display
                        document.getElementById('scan-current').textContent = progress.current || '-';
                        document.getElementById('scan-progress').textContent = `${{progress.done || 0}} / ${{progress.total || 0}}`;
                        
                        const percent = progress.total > 0 ? ((progress.done || 0) / progress.total) * 100 : 0;
                        document.getElementById('scan-progress-bar').style.width = percent + '%';
                        
                        document.getElementById('scan-found').textContent = progress.mcp_repos_found || 0;
                        document.getElementById('scan-skipped').textContent = progress.skipped || 0;
                        document.getElementById('scan-errors').textContent = progress.errors || 0;
                        
                        // Update activity log
                        if (progress.activity_log && progress.activity_log.length > 0) {{
                            const activityDiv = document.getElementById('scan-activity');
                            activityDiv.innerHTML = progress.activity_log.slice(-10).map(msg => 
                                `<div class="text-gray-300">${{msg}}</div>`
                            ).join('');
                            activityDiv.scrollTop = activityDiv.scrollHeight;
                        }}
                    }} else if (progress.status === 'complete') {{
                        // Scan finished, clear interval and load results
                        clearInterval(progressInterval);
                        document.getElementById('scan-progress-display').innerHTML = 
                            `<div class="text-green-400 text-sm font-semibold">✅ Scan complete! Loading results...</div>`;
                        
                        // Fetch final results
                        const res = await fetch('/api/repos');
                        reposData = await res.json();
                        renderRepos();
                        populateRepoSelector();
                        updateStats();
                        loadLogs();
                    }}
                }} catch(e) {{
                    console.error('Error polling progress:', e);
                }}
            }}, 200); // Poll every 200ms
            
            // Start the scan (this is async, so we poll for progress)
            try {{
                const res = await fetch('/api/repos');
                reposData = await res.json();
                
                // Clear interval if scan finished quickly
                clearInterval(progressInterval);
                
                renderRepos();
                populateRepoSelector();
                updateStats();
                loadLogs();
            }} catch(e) {{
                clearInterval(progressInterval);
                console.error('Error loading repos:', e);
                document.getElementById('repos-health').innerHTML = 
                    '<div class="text-red-400">Error scanning repositories: ' + e.message + '</div>';
                document.getElementById('repos-detail').innerHTML = 
                    '<div class="text-red-400">Error scanning repositories: ' + e.message + '</div>';
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
                            <div class="flex gap-2 text-xs flex-wrap mt-2">
                                <span class="px-2 py-0.5 bg-indigo-500/20 rounded">${{r.tools}} tools</span>
                                <span class="px-2 py-0.5 bg-purple-500/20 rounded">${{r.zoo_class}}</span>
                                ${{r.is_fullstack ? '<span class="px-2 py-0.5 bg-blue-500/20 text-blue-300 rounded">Fullstack</span>' : ''}}
                                ${{ (r.frontend || []).map(t => `<span class="px-2 py-0.5 bg-pink-500/20 text-pink-300 rounded">${{t}}</span>`).join('') }}
                                ${{ (r.backend || []).map(t => `<span class="px-2 py-0.5 bg-green-500/20 text-green-300 rounded">${{t}}</span>`).join('') }}
                                ${{ (r.infrastructure || []).map(t => `<span class="px-2 py-0.5 bg-orange-500/20 text-orange-300 rounded">${{t}}</span>`).join('') }}
                                ${{ (r.runtime && r.runtime.running) ? '<span class="px-2 py-0.5 bg-emerald-600 text-white rounded animate-pulse">Running</span>' : '' }}
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

                    ${{repo.is_fullstack || (repo.frontend && repo.frontend.length) || (repo.backend && repo.backend.length) ? `
                        <div>
                            <div class="border-t border-white/10 my-4"></div>
                            <h3 class="font-semibold mb-2 text-indigo-400">🏗️ Tech Stack</h3>
                            <div class="flex gap-2 flex-wrap">
                                ${{repo.is_fullstack ? '<span class="px-2 py-1 rounded text-xs bg-blue-500/20 text-blue-300">Fullstack</span>' : ''}}
                                ${{ (repo.frontend || []).map(t => `<span class="px-2 py-1 rounded text-xs bg-pink-500/20 text-pink-300">${{t}}</span>`).join('') }}
                                ${{ (repo.backend || []).map(t => `<span class="px-2 py-1 rounded text-xs bg-green-500/20 text-green-300">${{t}}</span>`).join('') }}
                                ${{ (repo.infrastructure || []).map(t => `<span class="px-2 py-1 rounded text-xs bg-orange-500/20 text-orange-300">${{t}}</span>`).join('') }}
                                ${{ (repo.runtime && repo.runtime.running) ? '<span class="px-2 py-1 rounded text-xs bg-emerald-600 text-white animate-pulse">Running</span>' : '' }}
                            </div>
                        </div>
                    ` : ''}}

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
                            <div class="text-sm text-gray-400 mt-1 tool-description-compact">${{formatDocstring(tool.description)}}</div>
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
            
            // Show tool description and schema with formatted docstring
            const formattedDescription = formatDocstring(consoleSelectedTool.description);
            schemaDiv.innerHTML = `
                <div class="p-4 bg-white/5 rounded-lg mb-4">
                    <div class="font-semibold text-indigo-400 mb-3 text-lg">${{consoleSelectedTool.name}}</div>
                    <div class="tool-description">${{formattedDescription}}</div>
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
        let currentPreprompt = 'MCP Developer';  // Track current preprompt
        
        // Toast notification helper
        function showToast(message, type = 'success') {{
            const backgrounds = {{
                'success': 'linear-gradient(to right, #10b981, #059669)',
                'error': 'linear-gradient(to right, #ef4444, #dc2626)',
                'info': 'linear-gradient(to right, #3b82f6, #2563eb)',
                'warning': 'linear-gradient(to right, #f59e0b, #d97706)'
            }};
            
            Toastify({{
                text: message,
                duration: 3000,
                gravity: "top",
                position: "right",
                style: {{
                    background: backgrounds[type] || backgrounds['info']
                }}
            }}).showToast();
        }}

        async function loadOllamaModels() {{
            const select = document.getElementById('ai-model');
            const info = document.getElementById('ai-model-info');
            
            select.innerHTML = '<option value="">Loading...</option>';
            info.textContent = 'Fetching from Ollama...';
            
            try {{
                const res = await fetch('/api/ollama/models');
                const data = await res.json();
                
                if (!data || data.error) {{
                    select.innerHTML = '<option value="">❌ ' + (data?.error || 'Connection failed') + '</option>';
                    info.textContent = 'Check AI Service connection';
                    return;
                }}
                
                if (!data.models || data.models.length === 0) {{
                    select.innerHTML = '<option value="">No models found</option>';
                    info.textContent = 'No models returned from configured services';
                    return;
                }}
                
                select.innerHTML = data.models.map(m => 
                    `<option value="${{m.name}}">${{m.name}} (${{m.size}})</option>`
                ).join('');
                
                info.innerHTML = `<span class="text-green-400">${{data.count}} models available</span>`;
            }} catch(e) {{
                select.innerHTML = '<option value="">❌ Connection failed</option>';
                info.textContent = 'Cannot connect to Ollama. Check OLLAMA_URL configuration.';
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
                
                if (!data || data.error) {{
                    throw new Error(data?.error || 'Connection failed');
                }}
                
                if (!data.models || data.models.length === 0) {{
                    throw new Error('No models available');
                }}
                
                aiConnected = true;
                const selectedModel = modelSelect.value || data.models[0].name;
                currentPreprompt = document.getElementById('ai-preprompt').value;
                
                showToast(`Connected with ${{currentPreprompt}}`, 'success');
                
                // Get personality-specific welcome message
                const welcomeMessages = {{
                    'Long John Silver, Pirate': `Ahoy, matey! ☠️ Long John Silver here, connected to Ollama's treasure chest o' ${{data.count}} models! We be sailin' with <strong>${{selectedModel}}</strong> as our trusty vessel. Let me navigate yer MCP seas and chart a course through yer code! What mysteries shall we unravel today, sailor?`,
                    'Coin Col': `*Jingle jingle* 🪙 Greetings, fellow collector! I've accessed the vault of ${{data.count}} Ollama models, and we're minting solutions with <strong>${{selectedModel}}</strong>. Each query is a precious coin to be examined and valued. What treasures shall we appraise in your MCP collection today?`,
                    'Butterfly Fancier': `Oh what a lovely garden! 🦋 I've fluttered into Ollama's meadow of ${{data.count}} models, and we're using the beautiful <strong>${{selectedModel}}</strong> butterfly! Your MCP servers are like flowers waiting to bloom. What delicate patterns shall we admire together?`,
                    'Code Pirate': `Arr! 🏴‍☠️ This scurvy pirate has commandeered Ollama's fleet o' ${{data.count}} models! We be plunderin' code with <strong>${{selectedModel}}</strong> as our flagship. Let's make yer MCP servers seaworthy! What code barnacles need scrapin'?`,
                    'Zen Master': `*Breathes calmly* 🧘 I have connected to the flow of ${{data.count}} Ollama models. We walk the path with <strong>${{selectedModel}}</strong>. Your MCP servers are like ripples in a pond - let us observe them with mindfulness. What wisdom do you seek?`,
                    'Aussie Coder': `G'day mate! 🦘 Just connected to Ollama's ripper collection of ${{data.count}} models! We're using <strong>${{selectedModel}}</strong> and she's a beaut! Ready to have a squiz at your MCP servers. What needs sortin' out, mate?`,
                    'MCP Developer': `Connected to Ollama with ${{data.count}} models! Using <strong>${{selectedModel}}</strong>. I can help you analyze your MCP zoo, suggest improvements, and answer questions about your servers. What would you like to know?`
                }};
                
                const welcomeMsg = welcomeMessages[currentPreprompt] || welcomeMessages['MCP Developer'];
                
                statusEl.textContent = `Ready (${{data.count}} models • ${{currentPreprompt}})`;
                statusEl.className = 'text-xs px-2 py-0.5 rounded bg-green-600 text-green-100';
                btnEl.textContent = '✓ Connected';
                btnEl.className = 'px-4 py-2 bg-green-600 rounded text-sm font-medium cursor-default';
                
                chatEl.innerHTML = `
                    <div class="flex gap-3">
                        <div class="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-sm">🤖</div>
                        <div class="flex-1 bg-white/5 rounded-lg p-4">
                            <div class="font-medium text-purple-400 mb-1">AI Assistant • ${{currentPreprompt}}</div>
                            <div class="text-gray-300">${{welcomeMsg}}</div>
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

        function updatePreprompt() {{
            currentPreprompt = document.getElementById('ai-preprompt').value;
            console.log('Preprompt changed to:', currentPreprompt);
            showToast(`Switched to: ${{currentPreprompt}}`, 'info');
            
            // Update chat header if connected
            if (aiConnected) {{
                const headerEl = document.querySelector('#ai-chat').previousElementSibling;
                if (headerEl) {{
                    const titleEl = headerEl.querySelector('h2');
                    if (titleEl) {{
                        titleEl.innerHTML = `
                            🤖 AI Assistant
                            <span class="text-xs px-2 py-0.5 rounded bg-green-600 text-green-100">Ready (with ${{currentPreprompt}})</span>
                        `;
                    }}
                }}
            }}
        }}

        async function loadPrepromptsFromDB() {{
            try {{
                console.log('Loading preprompts from database...');
                const res = await fetch('/api/ai/preprompts');
                
                if (!res.ok) {{
                    console.error('API returned error:', res.status);
                    return;
                }}
                
                const data = await res.json();
                console.log('Preprompts loaded:', data);
                
                if (data.preprompts && data.preprompts.length > 0) {{
                    const dropdown = document.getElementById('ai-preprompt');
                    if (!dropdown) {{
                        console.error('Dropdown element not found!');
                        return;
                    }}
                    
                    dropdown.innerHTML = '';
                    
                    // Reverse to show newest first
                    data.preprompts.reverse().forEach(p => {{
                        const option = document.createElement('option');
                        option.value = p.name;  // Use name as value for lookup
                        option.textContent = `${{p.emoji}} ${{p.name}}`;
                        dropdown.appendChild(option);
                    }});
                    
                    console.log(`✓ Loaded ${{data.preprompts.length}} preprompts`);
                }} else {{
                    console.warn('No preprompts found in database');
                }}
            }} catch (e) {{
                console.error('Failed to load preprompts:', e);
                alert('⚠️ Failed to load preprompts from database');
            }}
        }}

        async function aiRefinePreprompt() {{
            const text = document.getElementById('ai-refine-text').value.trim();
            if (!text) {{
                showToast('Please enter a personality concept (e.g., "coin collector")', 'warning');
                return;
            }}
            
            const modelId = document.getElementById('ai-model').value;
            
            // Show loading
            const btn = event.target;
            btn.disabled = true;
            btn.textContent = 'Generating...';
            btn.className = 'px-3 py-1.5 bg-yellow-600 rounded text-xs font-medium whitespace-nowrap animate-pulse';
            
            showToast(`🤖 AI generating "${{text}}" personality... (30-60s)`, 'info');
            
            try {{
                const res = await fetch('/api/preprompts/ai-refine', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        text: text,
                        model_id: modelId
                    }})
                }});
                
                const data = await res.json();
                
                if (data.success) {{
                    showToast(`✨ Generated "${{data.emoji}} ${{data.name}}" preprompt!`, 'success');
                    document.getElementById('ai-refine-text').value = '';
                    await loadPrepromptsFromDB();
                    
                    // Auto-select the new preprompt
                    const dropdown = document.getElementById('ai-preprompt');
                    dropdown.value = data.name;
                    currentPreprompt = data.name;
                }} else {{
                    showToast('❌ ' + (data.error || 'Generation failed'), 'error');
                }}
            }} catch (e) {{
                showToast('❌ Error: ' + e.message, 'error');
            }} finally {{
                btn.disabled = false;
                btn.textContent = 'Generate';
                btn.className = 'px-3 py-1.5 bg-purple-600 hover:bg-purple-500 rounded text-xs font-medium whitespace-nowrap';
            }}
        }}

        async function importPrepromptFile(input) {{
            const file = input.files[0];
            if (!file) return;
            
            showToast(`📁 Importing ${{file.name}}...`, 'info');
            
            const reader = new FileReader();
            reader.onload = async (e) => {{
                const content = e.target.result;
                
                try {{
                    const res = await fetch('/api/preprompts/import', {{
                        method: 'POST',
                        headers: {{ 'Content-Type': 'application/json' }},
                        body: JSON.stringify({{
                            content: content,
                            filename: file.name
                        }})
                    }});
                    
                    const data = await res.json();
                    
                    if (data.success) {{
                        showToast(`✅ Imported "${{data.emoji}} ${{data.name}}"!`, 'success');
                        await loadPrepromptsFromDB();
                        
                        // Auto-select the imported preprompt
                        const dropdown = document.getElementById('ai-preprompt');
                        dropdown.value = data.name;
                        currentPreprompt = data.name;
                    }} else {{
                        showToast('❌ ' + (data.error || 'Import failed'), 'error');
                    }}
                }} catch (e) {{
                    showToast('❌ Error: ' + e.message, 'error');
                }}
                
                input.value = '';
            }};
            reader.readAsText(file);
        }}

        async function togglePrepromptLibrary() {{
            const modal = document.getElementById('library-modal');
            modal.classList.remove('hidden');
            await loadPrepromptLibrary();
        }}
        
        function closePrepromptLibrary() {{
            document.getElementById('library-modal').classList.add('hidden');
        }}
        
        async function loadPrepromptLibrary() {{
            const contentEl = document.getElementById('library-content');
            contentEl.innerHTML = '<div class="text-center text-gray-500 py-8"><div class="text-4xl mb-4">⏳</div><div>Loading...</div></div>';
            
            try {{
                // Load preprompts and usage stats in parallel
                const [prepsRes, statsRes] = await Promise.all([
                    fetch('/api/ai/preprompts'),
                    fetch('/api/preprompts/stats/usage')
                ]);
                
                const prepsData = await prepsRes.json();
                const statsData = await statsRes.json();
                
                if (!prepsData.preprompts || prepsData.preprompts.length === 0) {{
                    contentEl.innerHTML = '<div class="text-center text-gray-500 py-8"><div class="text-4xl mb-4">📭</div><div>No preprompts found</div></div>';
                    return;
                }}
                
                // Merge usage stats with preprompts
                const statsMap = {{}};
                if (statsData.stats) {{
                    statsData.stats.forEach(s => {{
                        statsMap[s.id] = s;
                    }});
                }}
                
                prepsData.preprompts.forEach(p => {{
                    p.usage_count = statsMap[p.id]?.usage_count || 0;
                    p.last_used = statsMap[p.id]?.last_used || null;
                }});
                
                // Store for filtering
                window.allPreprompts = prepsData.preprompts;
                document.getElementById('library-count').textContent = prepsData.preprompts.length;
                
                displayLibraryPreprompts(prepsData.preprompts);
            }} catch (e) {{
                contentEl.innerHTML = `<div class="text-center text-red-500 py-8"><div class="text-4xl mb-4">❌</div><div>Error: ${{e.message}}</div></div>`;
            }}
        }}
        
        function displayLibraryPreprompts(preprompts) {{
            const contentEl = document.getElementById('library-content');
            contentEl.innerHTML = '';
            
            preprompts.forEach(p => {{
                const sourceColors = {{
                    'builtin': 'bg-blue-600',
                    'ai_generated': 'bg-purple-600',
                    'imported': 'bg-green-600',
                    'user': 'bg-yellow-600'
                }};
                
                const card = document.createElement('div');
                card.className = 'glass rounded-lg p-4 hover:bg-white/10 transition';
                card.innerHTML = `
                    <div class="flex items-start justify-between">
                        <div class="flex-1">
                            <div class="flex items-center gap-2 mb-2">
                                <span class="text-2xl" title="${{p.prompt_text.substring(0, 200)}}...">${{p.emoji}}</span>
                                <h3 class="font-semibold text-lg" title="${{p.prompt_text.substring(0, 200)}}...">${{p.name}}</h3>
                                <span class="text-xs px-2 py-0.5 rounded ${{sourceColors[p.source] || 'bg-gray-600'}}">${{p.source}}</span>
                                ${{p.usage_count > 0 ? `<span class="text-xs px-2 py-0.5 rounded bg-green-600 text-green-100" title="Times used">📊 ${{p.usage_count}}</span>` : ''}}
                            </div>
                            <p class="text-sm text-gray-400 line-clamp-2" title="${{p.prompt_text.substring(0, 200)}}...">${{p.prompt_text.substring(0, 150)}}...</p>
                            <div class="flex gap-4 mt-2 text-xs text-gray-500">
                                <span title="Created date">📅 ${{new Date(p.created_at).toLocaleDateString()}}</span>
                                <span title="Author">✍️ ${{p.author}}</span>
                                <span title="Character count">📏 ${{p.prompt_text.length}} chars</span>
                                ${{p.last_used ? `<span title="Last used">⏰ ${{new Date(p.last_used).toLocaleDateString()}}</span>` : ''}}
                            </div>
                        </div>
                        <div class="flex gap-2 ml-4">
                            <button onclick="viewPrepromptFull('${{p.id}}')" 
                                    class="px-3 py-1.5 bg-blue-600 hover:bg-blue-500 rounded text-xs" title="View full text">
                                👁️
                            </button>
                            <button onclick="editPreprompt('${{p.id}}')" 
                                    class="px-3 py-1.5 bg-purple-600 hover:bg-purple-500 rounded text-xs" title="Edit">
                                ✏️
                            </button>
                            <button onclick="exportPreprompt('${{p.id}}', '${{p.name}}')" 
                                    class="px-3 py-1.5 bg-green-600 hover:bg-green-500 rounded text-xs" title="Export">
                                💾
                            </button>
                            ${{p.source !== 'builtin' ? `
                            <button onclick="deletePreprompt('${{p.id}}', '${{p.name}}')" 
                                    class="px-3 py-1.5 bg-red-600 hover:bg-red-500 rounded text-xs" title="Delete">
                                🗑️
                            </button>
                            ` : ''}}
                        </div>
                    </div>
                `;
                contentEl.appendChild(card);
            }});
        }}
        
        function filterLibrary() {{
            if (!window.allPreprompts) return;
            
            const searchText = document.getElementById('library-search').value.toLowerCase();
            const sourceFilter = document.getElementById('library-filter').value;
            
            const filtered = window.allPreprompts.filter(p => {{
                const matchesSearch = !searchText || 
                    p.name.toLowerCase().includes(searchText) || 
                    p.prompt_text.toLowerCase().includes(searchText);
                const matchesSource = !sourceFilter || p.source === sourceFilter;
                return matchesSearch && matchesSource;
            }});
            
            displayLibraryPreprompts(filtered);
        }}

        async function viewPrepromptFull(id) {{
            try {{
                const res = await fetch(`/api/preprompts/${{id}}`);
                const prep = await res.json();
                
                if (prep.error) {{
                    showToast('Error loading preprompt', 'error');
                    return;
                }}
                
                // Show in modal with full text
                alert(`${{prep.emoji}} ${{prep.name}}\\n\\n${{prep.prompt_text}}\\n\\nSource: ${{prep.source}}\\nCreated: ${{new Date(prep.created_at).toLocaleString()}}`);
            }} catch (e) {{
                showToast('Error: ' + e.message, 'error');
            }}
        }}
        
        async function editPreprompt(id) {{
            try {{
                const res = await fetch(`/api/preprompts/${{id}}`);
                const prep = await res.json();
                
                if (prep.error) {{
                    showToast('Error loading preprompt', 'error');
                    return;
                }}
                
                // Open editor modal with data
                document.getElementById('edit-name').value = prep.name;
                document.getElementById('edit-emoji').value = prep.emoji;
                document.getElementById('edit-source').value = prep.source;
                document.getElementById('edit-prompt').value = prep.prompt_text;
                document.getElementById('editor-modal').dataset.editId = id;
                updateCharCount();
                
                document.getElementById('editor-modal').classList.remove('hidden');
                closePrepromptLibrary();
            }} catch (e) {{
                showToast('Error: ' + e.message, 'error');
            }}
        }}
        
        function closeEditor() {{
            document.getElementById('editor-modal').classList.add('hidden');
        }}
        
        function updateCharCount() {{
            const text = document.getElementById('edit-prompt').value;
            const count = text.length;
            const words = text.split(/\\s+/).filter(w => w.length > 0).length;
            document.getElementById('edit-char-count').textContent = `(${{count}} chars, ${{words}} words)`;
        }}
        
        async function saveEditedPreprompt() {{
            const id = document.getElementById('editor-modal').dataset.editId;
            const name = document.getElementById('edit-name').value.trim();
            const emoji = document.getElementById('edit-emoji').value.trim();
            const prompt_text = document.getElementById('edit-prompt').value.trim();
            
            if (!name || !prompt_text) {{
                showToast('Name and prompt text are required', 'warning');
                return;
            }}
            
            try {{
                const res = await fetch(`/api/preprompts/${{id}}`, {{
                    method: 'PUT',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{ name, emoji, prompt_text }})
                }});
                
                const data = await res.json();
                
                if (data.success) {{
                    showToast(`✅ Updated "${{emoji}} ${{name}}"`, 'success');
                    closeEditor();
                    await loadPrepromptsFromDB();
                    await togglePrepromptLibrary();
                }} else {{
                    showToast('Error: ' + (data.error || 'Update failed'), 'error');
                }}
            }} catch (e) {{
                showToast('Error: ' + e.message, 'error');
            }}
        }}
        
        async function exportPreprompt(id, name) {{
            try {{
                const res = await fetch(`/api/preprompts/${{id}}`);
                const prep = await res.json();
                
                if (prep.error) {{
                    showToast('Error loading preprompt', 'error');
                    return;
                }}
                
                // Create markdown file
                const markdown = `# ${{prep.emoji}} ${{prep.name}}

**Source**: ${{prep.source}}  
**Created**: ${{new Date(prep.created_at).toLocaleString()}}  
**Author**: ${{prep.author}}

---

${{prep.prompt_text}}
`;
                
                // Download
                const blob = new Blob([markdown], {{ type: 'text/markdown' }});
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = `${{prep.name.toLowerCase().replace(/[^a-z0-9]+/g, '-')}}.md`;
                document.body.appendChild(a);
                a.click();
                document.body.removeChild(a);
                URL.revokeObjectURL(url);
                
                showToast(`📥 Exported "${{prep.name}}.md"`, 'success');
            }} catch (e) {{
                showToast('Error: ' + e.message, 'error');
            }}
        }}
        
        async function deletePreprompt(id, name) {{
            if (!confirm(`Delete "${{name}}"?\\n\\nThis can be undone via database.`)) {{
                return;
            }}
            
            try {{
                const res = await fetch(`/api/preprompts/${{id}}`, {{
                    method: 'DELETE'
                }});
                
                const data = await res.json();
                
                if (data.success) {{
                    showToast(`🗑️ Deleted "${{name}}"`, 'success');
                    await loadPrepromptsFromDB();
                    await loadPrepromptLibrary();
                }} else {{
                    showToast('Error: ' + (data.error || 'Delete failed'), 'error');
                }}
            }} catch (e) {{
                showToast('Error: ' + e.message, 'error');
            }}
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
            
            // Add thinking indicator with preprompt info
            const chatEl = document.getElementById('ai-chat');
            const thinkingId = 'thinking-' + Date.now();
            const thinkingText = toolsUsed.length > 0 
                ? 'Gathering context... (' + toolsUsed.join(', ') + ')'
                : 'Thinking...';
            chatEl.insertAdjacentHTML('beforeend', `
                <div id="${{thinkingId}}" class="flex gap-3">
                    <div class="w-8 h-8 rounded-full bg-purple-600 flex items-center justify-center text-sm animate-pulse">🤖</div>
                    <div class="flex-1 bg-white/5 rounded-lg p-4">
                        <div class="font-medium text-purple-400 mb-1">AI Assistant • ${{currentPreprompt}}</div>
                        <div class="text-gray-400 flex items-center gap-2">
                            <span class="animate-pulse">●</span> ${{thinkingText}}
                        </div>
                        <div class="mt-2">
                            <div class="w-full bg-gray-700 rounded-full h-1.5 overflow-hidden">
                                <div class="bg-purple-600 h-full animate-[pulse_1s_ease-in-out_infinite]" style="width: 100%"></div>
                            </div>
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
                const preprompt = document.getElementById('ai-preprompt').value;
                
                const res = await fetch('/api/ai/chat', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        model_id: modelId,
                        message: fullPrompt,
                        include_repo_context: includeRepos,
                        file_path: filePath || null,
                        web_search: webSearch || null,
                        preprompt: preprompt
                    }})
                }});
                
                const data = await res.json();
                
                // Log preprompt usage for debugging
                if (data.preprompt_used) {{
                    console.log('✓ Response used preprompt:', data.preprompt_used, '(Found:', data.preprompt_found, ')');
                }}
                
                // Remove thinking indicator
                document.getElementById(thinkingId)?.remove();
                
                if (data.response) {{
                    addChatMessage('assistant', data.response);
                    // Show subtle confirmation
                    if (data.preprompt_used && data.preprompt_found) {{
                        console.log(`✅ Chat successfully used "${{data.preprompt_used}}" personality`);
                    }}
                }} else if (data.error) {{
                    addChatMessage('assistant', '❌ Error: ' + data.error);
                    showToast('Chat error: ' + data.error, 'error');
                }} else {{
                    addChatMessage('assistant', JSON.stringify(data, null, 2));
                }}
            }} catch(e) {{
                document.getElementById(thinkingId)?.remove();
                addChatMessage('assistant', '❌ Error: ' + e.message);
                showToast('Error: ' + e.message, 'error');
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
        loadPrepromptsFromDB();  // Load preprompts from database
        setInterval(loadLogs, 5000);
        setInterval(loadConsoleServers, 3000);
        setInterval(updateAIContext, 5000);  // Keep AI context updated
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {{
            // Ctrl+Enter: Send message
            if (e.ctrlKey && e.key === 'Enter' && document.getElementById('ai-input') === document.activeElement) {{
                sendAIMessage();
            }}
            // Ctrl+L: Clear chat
            if (e.ctrlKey && e.key === 'l') {{
                e.preventDefault();
                clearAIChat();
            }}
            // Ctrl+K: Focus preprompt dropdown
            if (e.ctrlKey && e.key === 'k') {{
                e.preventDefault();
                document.getElementById('ai-preprompt').focus();
            }}
            // Ctrl+G: Focus AI Refine input
            if (e.ctrlKey && e.key === 'g') {{
                e.preventDefault();
                document.getElementById('ai-refine-text').focus();
            }}
            // Ctrl+B: Browse library
            if (e.ctrlKey && e.key === 'b') {{
                e.preventDefault();
                togglePrepromptLibrary();
            }}
            // Escape: Close modals
            if (e.key === 'Escape') {{
                closePrepromptLibrary();
                closeEditor();
            }}
        }});
        
        showToast('⌨️ Keyboard shortcuts ready! Ctrl+B=Library, Ctrl+K=Preprompt, Ctrl+L=Clear', 'info');
    </script>
    
    <!-- Preprompt Library Browser Modal -->
    <div id="library-modal" class="fixed inset-0 bg-black/70 backdrop-blur-sm hidden flex items-center justify-center z-50" onclick="if(event.target.id==='library-modal'){{closePrepromptLibrary();}}">
        <div class="glass rounded-xl w-full max-w-4xl max-h-[90vh] overflow-hidden flex flex-col m-4" onclick="event.stopPropagation()">
            <!-- Modal Header -->
            <div class="px-6 py-4 border-b border-white/10 flex items-center justify-between">
                <div>
                    <h2 class="text-xl font-semibold">📚 Preprompt Library</h2>
                    <p class="text-sm text-gray-400 mt-1"><span id="library-count">0</span> personalities</p>
                </div>
                <div class="flex gap-2 items-center">
                    <input id="library-search" type="text" placeholder="Search..." 
                           class="bg-midnight-800 border border-white/10 rounded px-3 py-1.5 text-sm w-48"
                           oninput="filterLibrary()">
                    <select id="library-filter" class="bg-midnight-800 border border-white/10 rounded px-3 py-1.5 text-sm"
                            onchange="filterLibrary()">
                        <option value="">All Sources</option>
                        <option value="builtin">Built-in</option>
                        <option value="ai_generated">AI Generated</option>
                        <option value="imported">Imported</option>
                        <option value="user">User Created</option>
                    </select>
                    <button onclick="closePrepromptLibrary()" 
                            class="px-3 py-1.5 bg-gray-700 hover:bg-gray-600 rounded text-sm">
                        ✕
                    </button>
                </div>
            </div>
            
            <!-- Modal Content -->
            <div id="library-content" class="flex-1 overflow-y-auto p-6 space-y-3">
                <div class="text-center text-gray-500 py-8">
                    <div class="text-4xl mb-4">⏳</div>
                    <div>Loading preprompts...</div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Preprompt Editor Modal -->
    <div id="editor-modal" class="fixed inset-0 bg-black/70 backdrop-blur-sm hidden flex items-center justify-center z-50" onclick="if(event.target.id==='editor-modal'){{closeEditor();}}">
        <div class="glass rounded-xl w-full max-w-3xl m-4" onclick="event.stopPropagation()">
            <div class="px-6 py-4 border-b border-white/10">
                <h2 class="text-xl font-semibold">✏️ Edit Preprompt</h2>
            </div>
            <div class="p-6 space-y-4">
                <div>
                    <label class="text-sm text-gray-400 block mb-2">Name</label>
                    <input id="edit-name" type="text" class="w-full bg-midnight-800 border border-white/10 rounded px-3 py-2">
                </div>
                <div class="flex gap-4">
                    <div class="flex-1">
                        <label class="text-sm text-gray-400 block mb-2">Emoji</label>
                        <input id="edit-emoji" type="text" maxlength="2" class="w-full bg-midnight-800 border border-white/10 rounded px-3 py-2 text-2xl text-center">
                    </div>
                    <div class="flex-1">
                        <label class="text-sm text-gray-400 block mb-2">Source</label>
                        <input id="edit-source" type="text" readonly class="w-full bg-midnight-700 border border-white/10 rounded px-3 py-2 text-gray-500">
                    </div>
                </div>
                <div>
                    <label class="text-sm text-gray-400 block mb-2">Preprompt Text <span id="edit-char-count" class="text-xs text-gray-500"></span></label>
                    <textarea id="edit-prompt" rows="10" class="w-full bg-midnight-800 border border-white/10 rounded px-3 py-2 font-mono text-sm"
                              oninput="updateCharCount()"></textarea>
                </div>
                <div class="flex gap-2 justify-end">
                    <button onclick="closeEditor()" class="px-4 py-2 bg-gray-700 hover:bg-gray-600 rounded">Cancel</button>
                    <button onclick="saveEditedPreprompt()" class="px-4 py-2 bg-purple-600 hover:bg-purple-500 rounded">Save Changes</button>
                </div>
            </div>
        </div>
    </div>
</body>
</html>"""


# ═══════════════════════════════════════════════════════════════════════════════
# PORT CONFLICT HANDLING
# ═══════════════════════════════════════════════════════════════════════════════


def is_port_available(port: int) -> bool:
    """Check if a port is available for binding."""
    import socket

    try:
        logger.debug(f"Checking if port {port} is available...")
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(("0.0.0.0", port))
            logger.debug(f"Port {port} is available")
            return True
    except OSError as e:
        logger.debug(f"Port {port} is not available: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error checking port {port}: {e}", exc_info=True)
        return False


def find_available_port(start_port: int, max_attempts: int = 10) -> int:
    """Find an available port starting from start_port."""
    logger.info(
        f"Searching for available port starting from {start_port} (max {max_attempts} attempts)"
    )
    for i in range(max_attempts):
        port = start_port + i
        try:
            if is_port_available(port):
                logger.info(f"Found available port: {port}")
                return port
        except Exception as e:
            logger.warning(f"Error checking port {port}: {e}")
            continue
    error_msg = (
        f"Could not find available port in range {start_port}-{start_port + max_attempts - 1}"
    )
    logger.error(error_msg)
    raise RuntimeError(error_msg)


def get_port_owner_info(port: int) -> Optional[Dict[str, Any]]:
    """Get information about what process is using a port (Windows)."""
    if sys.platform != "win32":
        logger.debug("get_port_owner_info only works on Windows")
        return None

    try:
        logger.debug(f"Getting port owner info for port {port}...")
        import subprocess

        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True, timeout=5)

        if result.returncode != 0:
            logger.warning(f"netstat command failed with return code {result.returncode}")
            return None

        for line in result.stdout.split("\n"):
            if f":{port}" in line and "LISTENING" in line:
                parts = line.split()
                if len(parts) >= 5:
                    pid = parts[-1]
                    logger.debug(f"Found process using port {port}: PID {pid}")
                    try:
                        import psutil  # type: ignore[import-untyped]

                        proc = psutil.Process(int(pid))
                        info = {
                            "pid": pid,
                            "name": proc.name(),
                            "path": proc.exe(),
                            "cmdline": " ".join(proc.cmdline()),
                        }
                        logger.debug(f"Port owner info: {info}")
                        return info
                    except ImportError:
                        logger.debug("psutil not available, returning basic info")
                        return {"pid": pid, "name": "Unknown", "path": "Unknown"}
                    except Exception as e:
                        logger.warning(f"Error getting process info for PID {pid}: {e}")
                        return {"pid": pid, "name": "Unknown", "path": "Unknown"}
    except subprocess.TimeoutExpired:
        logger.error("netstat command timed out")
        return None
    except Exception as e:
        logger.error(f"Error getting port owner info: {e}", exc_info=True)
        return None

    logger.debug(f"No process found using port {port}")
    return None


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    try:
        logger.info("=" * 80)
        logger.info("MCP Studio Startup - Beginning initialization")
        logger.info(f"Python version: {sys.version}")
        logger.info(f"Platform: {sys.platform}")
        logger.info(f"Working directory: {os.getcwd()}")
        logger.info(f"Script path: {__file__}")

        # Set UTF-8 encoding for Windows console
        if sys.platform == "win32":
            try:
                import codecs

                sys.stdout = codecs.getwriter("utf-8")(sys.stdout.buffer, "strict")
                logger.info("UTF-8 encoding configured for Windows console")
            except Exception as e:
                logger.warning(f"Failed to set UTF-8 encoding: {e}")

        log("🚀 Starting MCP Studio...")
        logger.info("Starting MCP Studio...")
        log(f"📂 Repos directory: {REPOS_DIR}")
        logger.info(f"Repos directory: {REPOS_DIR}")

        # Verify repos directory exists
        if not REPOS_DIR.exists():
            error_msg = f"Repos directory does not exist: {REPOS_DIR}"
            logger.error(error_msg)
            log(f"❌ ERROR: {error_msg}")
            sys.exit(1)

        # Check FastMCP availability
        try:
            if FASTMCP_AVAILABLE:
                log("✅ FastMCP available - live connections enabled")
                logger.info("FastMCP is available")
            else:
                log("⚠️  FastMCP not available - install with: pip install fastmcp")
                log("   Live server connections will be disabled")
                logger.warning("FastMCP not available - live connections disabled")
        except Exception as e:
            logger.error(f"Error checking FastMCP availability: {e}", exc_info=True)
            log(f"⚠️  Error checking FastMCP: {e}")

        # Discover clients on startup
        try:
            logger.info("Discovering MCP clients...")
            clients = discover_mcp_clients()
            logger.info(f"Discovered {len(clients)} clients")
            for client, data in clients.items():
                log(f"🔌 Found {client}: {len(data['servers'])} servers")
                logger.info(f"Client '{client}': {len(data['servers'])} servers")
        except Exception as e:
            logger.error(f"Error discovering MCP clients: {e}", exc_info=True)
            log(f"⚠️  Error discovering clients: {e}")
            clients = {}

        # Initialize preprompt database and seed with builtins
        try:
            logger.info("Initializing preprompt database...")
            import preprompt_db

            preprompt_db.init_db()
            logger.info("Preprompt database initialized")

            # Check if we need to seed
            existing = preprompt_db.list_preprompts(active_only=False)
            if len(existing) == 0:
                log("🎭 Seeding preprompt database with 5 builtin personalities...")
                logger.info("Seeding preprompt database...")
                preprompt_db.seed_builtin_preprompts()
                log("✅ Preprompt database initialized")
                logger.info("Preprompt database seeded successfully")
            else:
                log(f"🎭 Found {len(existing)} preprompts in database")
                logger.info(f"Found {len(existing)} existing preprompts")
        except ImportError as e:
            logger.warning(f"preprompt_db module not available: {e}")
            log(f"⚠️  Preprompt database module not available: {e}")
        except Exception as e:
            logger.error(f"Preprompt database error: {e}", exc_info=True)
            log(f"⚠️  Preprompt database error: {e}")

        # Check port availability before starting
        logger.info(f"Checking port availability for port {PORT}...")
        actual_port = PORT
        try:
            port_available = is_port_available(PORT)
            logger.info(f"Port {PORT} available: {port_available}")

            if not port_available:
                logger.warning(f"Port {PORT} is not available, checking what's using it...")
                port_info = get_port_owner_info(PORT)
                log(f"❌ PORT CONFLICT: Port {PORT} is already in use!")
                logger.error(f"Port conflict detected on port {PORT}")

                if port_info:
                    log(f"   Port {PORT} is being used by:")
                    log(
                        f"   • Process: {port_info.get('name', 'Unknown')} (PID: {port_info.get('pid', 'Unknown')})"
                    )
                    log(f"   • Path: {port_info.get('path', 'Unknown')}")
                    logger.error(
                        f"Port {PORT} used by: {port_info.get('name', 'Unknown')} (PID: {port_info.get('pid', 'Unknown')})"
                    )

                log(f"\n💡 Solutions:")
                log(f"   1. Stop the conflicting process:")
                if port_info and port_info.get("pid"):
                    log(f"      Stop-Process -Id {port_info['pid']} -Force")
                else:
                    log(
                        f"      Get-NetTCPConnection -LocalPort {PORT} | Select-Object OwningProcess"
                    )
                    log(f"      Then: Stop-Process -Id <PID> -Force")
                log(f"   2. Use a different port:")
                log(f"      Set environment variable: $env:PORT=8002")
                log(f"      Or edit .env file: PORT=8002")
                log(f"   3. Auto-find available port (attempting now)...")

                try:
                    logger.info("Attempting to find available port...")
                    actual_port = find_available_port(PORT + 1, max_attempts=10)
                    log(f"✅ Found available port: {actual_port}")
                    log(f"   Dashboard will start on: http://localhost:{actual_port}")
                    logger.info(f"Found available port: {actual_port}")
                except RuntimeError as e:
                    logger.error(f"Failed to find available port: {e}", exc_info=True)
                    log(f"❌ {e}")
                    log(f"   Please manually specify a port or stop conflicting processes.")
                    sys.exit(1)
            else:
                logger.info(f"Port {PORT} is available")
        except Exception as e:
            logger.error(f"Error checking port availability: {e}", exc_info=True)
            log(f"⚠️  Error checking port: {e}")
            # Continue with default port anyway

        # Display startup banner with actual port
        try:
            banner = f"""
╔══════════════════════════════════════════════════════════════════╗
║  🦁 MCP Studio v1.0.0                                          ║
║  Mission Control for the MCP Zoo 🐘🦒🐿️                           ║
╠══════════════════════════════════════════════════════════════════╣
║  Dashboard: http://localhost:{actual_port}                                ║
║  API Docs:  http://localhost:{actual_port}/docs                           ║
║  Log File:  {LOG_FILE}                          ║
╚══════════════════════════════════════════════════════════════════╝"""
            print(banner)
            logger.info(f"Startup banner displayed. Port: {actual_port}")
        except Exception as e:
            logger.error(f"Error displaying startup banner: {e}", exc_info=True)

        # Start the server with error handling
        try:
            log(f"🌐 Starting server on port {actual_port}...")
            logger.info(f"Starting uvicorn server on port {actual_port}...")
            logger.info(f"Server will be accessible at: http://localhost:{actual_port}")
            logger.info(f"API docs will be at: http://localhost:{actual_port}/docs")

            uvicorn.run(app, host="0.0.0.0", port=actual_port, log_level="warning")

        except OSError as e:
            error_msg = f"OSError starting server: {e}"
            logger.error(error_msg, exc_info=True)

            if "address already in use" in str(e).lower() or "10048" in str(e):
                log(f"❌ PORT CONFLICT: Port {actual_port} is already in use!")
                log(f"   Another process started using the port after we checked.")
                logger.error(f"Port {actual_port} conflict detected after initial check")
                log(f"   Solutions:")
                log(f"   1. Stop the conflicting process:")
                log(
                    f"      Get-NetTCPConnection -LocalPort {actual_port} | Select-Object OwningProcess"
                )
                log(f"      Then: Stop-Process -Id <PID> -Force")
                log(f"   2. Use a different port:")
                log(f"      Set environment variable: $env:PORT={actual_port + 1}")
            else:
                log(f"❌ Server startup error: {e}")
            logger.error(f"Server startup failed. Exiting.")
            sys.exit(1)

        except KeyboardInterrupt:
            logger.info("Received KeyboardInterrupt - shutting down gracefully")
            log("\n👋 Shutting down MCP Studio...")
            sys.exit(0)

        except Exception as e:
            error_msg = f"Unexpected error starting server: {e}"
            logger.critical(error_msg, exc_info=True)
            log(f"❌ {error_msg}")
            import traceback

            tb = traceback.format_exc()
            logger.critical(f"Traceback:\n{tb}")
            log(tb)
            log(f"\n📋 Full error details logged to: {LOG_FILE}")
            sys.exit(1)

    except Exception as e:
        # Catch-all for any errors during initialization
        error_msg = f"Fatal error during startup initialization: {e}"
        logger.critical(error_msg, exc_info=True)
        import traceback

        tb = traceback.format_exc()
        logger.critical(f"Traceback:\n{tb}")
        print(f"❌ FATAL ERROR: {error_msg}")
        print(f"📋 Full error details logged to: {LOG_FILE}")
        print(f"\nTraceback:\n{tb}")
        sys.exit(1)
