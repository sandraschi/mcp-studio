import json
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

# List of known MCP client configuration locations
MCP_CLIENT_CONFIGS = {
    "claude-desktop": [
        Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
        Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
    ],
    "cursor": [
        Path(os.environ.get("APPDATA", ""))
        / "Cursor"
        / "User"
        / "globalStorage"
        / "cursor-storage"
        / "mcp_config.json",
        Path.home()
        / ".config"
        / "Cursor"
        / "User"
        / "globalStorage"
        / "cursor-storage"
        / "mcp_config.json",
    ],
    "windsurf": [
        Path(os.environ.get("APPDATA", "")) / "Windsurf" / "mcp_config.json",
        Path.home() / ".config" / "Windsurf" / "mcp_config.json",
    ],
    "zed-ide": [
        Path(os.environ.get("APPDATA", "")) / "Zed" / "settings.json",
        Path.home() / ".config" / "zed" / "settings.json",
        Path.home() / "Library" / "Application Support" / "Zed" / "settings.json",  # Mac
    ],
    "antigravity-ide": [
        Path(os.environ.get("APPDATA", "")) / "Antigravity" / "mcp_config.json",
        Path.home() / ".antigravity" / "mcp_config.json",
        Path.home() / ".gemini" / "antigravity" / "mcp_config.json",
    ],
    "cline": [
        Path(os.environ.get("APPDATA", ""))
        / "Code"
        / "User"
        / "globalStorage"
        / "saoudrizwan.claude-dev"
        / "settings"
        / "cline_mcp_settings.json",
    ],
}


def discover_mcp_clients(log_func=None) -> Dict[str, List[Dict]]:
    """
    Discover MCP servers from all known client configurations.
    """

    def _log(msg):
        if log_func:
            log_func(msg)
        logger.info(msg)

    results = {}

    # Check if running in Docker
    in_docker = Path("/.dockerenv").exists() or os.path.exists("/.dockerenv")

    for client_name, config_paths in MCP_CLIENT_CONFIGS.items():
        for config_path in config_paths:
            # If in Docker, try to map paths to mounted locations
            check_path = config_path
            if in_docker:
                path_str = str(config_path)
                if "AppData" in path_str or "APPDATA" in path_str or "Roaming" in path_str:
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

                servers = {}
                if "mcpServers" in config:
                    servers = config.get("mcpServers", {})
                elif "mcp" in config and isinstance(config.get("mcp"), dict):
                    servers = config.get("mcp", {}).get("servers", {})
                elif "servers" in config:
                    servers = config.get("servers", {})

                if servers:
                    results[client_name] = {"path": str(check_path), "servers": []}
                    for server_id, server_config in servers.items():
                        if isinstance(server_config, dict):
                            results[client_name]["servers"].append(
                                {
                                    "id": server_id,
                                    "name": server_id.replace("-", " ").replace("_", " ").title(),
                                    "command": server_config.get("command", ""),
                                    "args": server_config.get("args", []),
                                    "cwd": server_config.get("cwd"),
                                    "env": server_config.get("env", {}),
                                    "type": server_config.get("type", "stdio"),
                                    "url": server_config.get("url", ""),
                                    "status": "discovered",
                                }
                            )
                        elif isinstance(server_config, str):
                            results[client_name]["servers"].append(
                                {
                                    "id": server_id,
                                    "name": server_id.replace("-", " ").replace("_", " ").title(),
                                    "command": server_config,
                                    "args": [],
                                    "status": "discovered",
                                }
                            )
                    break
            except Exception as e:
                _log(f"Error reading {client_name} config: {e}")

    return results
