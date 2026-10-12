"""
MCP Client Zoo - Comprehensive MCP client configuration parser.

Supports ALL known MCP clients as of 2025:
- Claude Desktop (Anthropic official)
- Cursor IDE
- Windsurf IDE
- Antigravity IDE (Google)
- Cline (VSCode extension, formerly Claude Dev)
- Roo-Cline (Windsurf version of Cline)
- Continue.dev (VSCode extension)
- LM Studio (local models)
- VSCode (generic with MCP extensions)
- Zed Editor
- Custom configs

Austrian precision: If it uses MCP, we support it! 🇦🇹
"""

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any

HOST_APPDATA = Path("/host/appdata")
HOST_HOME = Path("/host/home")

from ..core.logging_utils import get_logger
from .client_settings_manager import ClientSettingsManager

logger = get_logger(__name__)


@dataclass
class MCPServerInfo:
    """Information about an MCP server configuration."""

    id: str
    name: str
    command: str
    args: list[str]
    cwd: str | None = None
    env: dict[str, str] | None = None
    source: str = ""  # Which client this came from
    estimated_tools: int = 20


class MCPClientZoo:
    """Parser for MCP configurations from ALL known MCP clients."""

    def __init__(self) -> None:
        """Initialize the client zoo."""
        self.servers: dict[str, MCPServerInfo] = {}
        self.sources_found: list[str] = []
        self.settings_manager = ClientSettingsManager()

    # ═══════════════════════════════════════════════════════════════
    # CLAUDE DESKTOP (Anthropic Official)
    # ═══════════════════════════════════════════════════════════════

    def parse_claude_desktop(self) -> list[MCPServerInfo]:
        """Parse Claude Desktop MCP configuration."""
        paths = [
            Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
            Path.home() / ".config" / "Claude" / "claude_desktop_config.json",  # Linux/Mac
            # Docker Host Mounts
            HOST_APPDATA / "Claude" / "claude_desktop_config.json",
            HOST_HOME / ".config" / "Claude" / "claude_desktop_config.json",
            HOST_HOME / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
        ]

        return self._parse_standard_format(paths, "claude-desktop")

    # ═══════════════════════════════════════════════════════════════
    # CURSOR IDE
    # ═══════════════════════════════════════════════════════════════

    def parse_cursor_ide(self) -> list[MCPServerInfo]:
        """Parse Cursor IDE MCP configuration."""
        paths = [
            Path(os.environ.get("APPDATA", ""))
            / "Cursor"
            / "User"
            / "globalStorage"
            / "saoudrizwan.claude-dev"
            / "settings"
            / "cline_mcp_settings.json",
            Path(os.environ.get("APPDATA", "")) / "Cursor" / "mcp_settings.json",
            Path.home() / ".cursor" / "mcp.json",  # Primary Cursor IDE config location
            Path.home() / ".cursor" / "mcp_settings.json",
            Path.home() / ".config" / "Cursor" / "User" / "mcp_settings.json",  # Linux
            # Docker Host Mounts
            HOST_APPDATA
            / "Cursor"
            / "User"
            / "globalStorage"
            / "saoudrizwan.claude-dev"
            / "settings"
            / "cline_mcp_settings.json",
            HOST_APPDATA / "Cursor" / "mcp_settings.json",
            HOST_HOME / ".cursor" / "mcp.json",
            HOST_HOME / ".cursor" / "mcp_settings.json",
            HOST_HOME / ".config" / "Cursor" / "User" / "mcp_settings.json",
        ]

        return self._parse_standard_format(paths, "cursor-ide")

    # ═══════════════════════════════════════════════════════════════
    # WINDSURF IDE
    # ═══════════════════════════════════════════════════════════════

    def parse_windsurf_ide(self) -> list[MCPServerInfo]:
        """Parse Windsurf IDE MCP configuration."""
        paths = [
            Path(os.environ.get("APPDATA", ""))
            / "Windsurf"
            / "User"
            / "globalStorage"
            / "rooveterinaryinc.roo-cline"
            / "settings"
            / "mcp_settings.json",
            Path(os.environ.get("APPDATA", "")) / "Windsurf" / "mcp.json",  # Alternative location
            Path(os.environ.get("APPDATA", "")) / "Windsurf" / "mcp_settings.json",
            Path.home() / ".config" / "Windsurf" / "mcp.json",  # Linux
            Path.home() / ".config" / "Windsurf" / "mcp_settings.json",  # Linux
            Path.home() / "Library" / "Application Support" / "Windsurf" / "mcp.json",  # Mac
            # User's actual config location
            Path.home() / ".codeium" / "windsurf" / "mcp_config.json",
        ]

        return self._parse_standard_format(paths, "windsurf-ide")

    # ═══════════════════════════════════════════════════════════════
    # CLINE (VSCode Extension - formerly Claude Dev)
    # ═══════════════════════════════════════════════════════════════

    def parse_cline(self) -> list[MCPServerInfo]:
        """Parse Cline (formerly Claude Dev) VSCode extension MCP configuration."""
        paths = [
            # Current Cline paths
            Path(os.environ.get("APPDATA", ""))
            / "Code"
            / "User"
            / "globalStorage"
            / "saoudrizwan.claude-dev"
            / "settings"
            / "cline_mcp_settings.json",
            Path.home()
            / ".config"
            / "Code"
            / "User"
            / "globalStorage"
            / "saoudrizwan.claude-dev"
            / "settings"
            / "cline_mcp_settings.json",  # Linux
            Path.home()
            / "Library"
            / "Application Support"
            / "Code"
            / "User"
            / "globalStorage"
            / "saoudrizwan.claude-dev"
            / "settings"
            / "cline_mcp_settings.json",  # Mac
            # Alternative locations
            Path(os.environ.get("APPDATA", ""))
            / "Code"
            / "User"
            / "globalStorage"
            / "saoudrizwan.cline"
            / "settings"
            / "cline_mcp_settings.json",
            Path.home()
            / ".config"
            / "Code"
            / "User"
            / "globalStorage"
            / "saoudrizwan.cline"
            / "settings"
            / "cline_mcp_settings.json",
            # VSCode Insiders
            Path(os.environ.get("APPDATA", ""))
            / "Code - Insiders"
            / "User"
            / "globalStorage"
            / "saoudrizwan.claude-dev"
            / "settings"
            / "cline_mcp_settings.json",
            Path(os.environ.get("APPDATA", ""))
            / "Code - Insiders"
            / "User"
            / "globalStorage"
            / "saoudrizwan.cline"
            / "settings"
            / "cline_mcp_settings.json",
        ]

        return self._parse_standard_format(paths, "cline-vscode")

    # ═══════════════════════════════════════════════════════════════
    # ROO-CLINE (Windsurf's Cline Fork)
    # ═══════════════════════════════════════════════════════════════

    def parse_roo_cline(self) -> list[MCPServerInfo]:
        """Parse Roo-Cline (Windsurf's Cline fork) MCP configuration."""
        paths = [
            Path(os.environ.get("APPDATA", ""))
            / "Windsurf"
            / "User"
            / "globalStorage"
            / "rooveterinaryinc.roo-cline"
            / "settings"
            / "mcp_settings.json",
            Path(os.environ.get("APPDATA", "")) / "Cline" / "mcp_settings.json",
        ]

        return self._parse_standard_format(paths, "roo-cline")

    # ═══════════════════════════════════════════════════════════════
    # CONTINUE.DEV (VSCode Extension)
    # ═══════════════════════════════════════════════════════════════

    def parse_continue_dev(self) -> list[MCPServerInfo]:
        """Parse Continue.dev VSCode extension MCP configuration."""
        paths = [
            # Primary Continue config
            Path.home() / ".continue" / "config.json",
            Path.home() / ".continue" / "config.ts",  # TypeScript config
            # VSCode extension storage
            Path(os.environ.get("APPDATA", ""))
            / "Code"
            / "User"
            / "globalStorage"
            / "continue.continue"
            / "config.json",
            Path.home() / ".config" / "Code" / "User" / "globalStorage" / "continue.continue" / "config.json",  # Linux
            Path.home()
            / "Library"
            / "Application Support"
            / "Code"
            / "User"
            / "globalStorage"
            / "continue.continue"
            / "config.json",  # Mac
            # VSCode Insiders
            Path(os.environ.get("APPDATA", ""))
            / "Code - Insiders"
            / "User"
            / "globalStorage"
            / "continue.continue"
            / "config.json",
            # Cursor support
            Path.home() / ".cursor" / ".continue" / "config.json",
        ]

        # Continue.dev uses various structures - try both standard and continue formats
        result = self._parse_continue_format(paths, "continue-dev")
        if not result:
            result = self._parse_standard_format(paths, "continue-dev")
        return result

    # ═══════════════════════════════════════════════════════════════
    # LM STUDIO
    # ═══════════════════════════════════════════════════════════════

    def parse_lm_studio(self) -> list[MCPServerInfo]:
        """Parse LM Studio MCP configuration."""
        paths = [
            Path.home() / ".lmstudio" / "mcp.json",  # User's preferred location
            Path(os.environ.get("APPDATA", "")) / "LM Studio" / "mcp_config.json",
            Path.home() / ".lmstudio" / "mcp_config.json",  # Alternative user location
            Path.home() / "Library" / "Application Support" / "LM Studio" / "mcp_config.json",  # Mac
        ]

        return self._parse_standard_format(paths, "lm-studio")

    # ═══════════════════════════════════════════════════════════════
    # ANTIGRAVITY IDE
    # ═══════════════════════════════════════════════════════════════

    def parse_antigravity_ide(self) -> list[MCPServerInfo]:
        """Parse Antigravity IDE MCP configuration."""
        paths = [
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
            # User's actual config location
            Path.home() / ".gemini" / "antigravity" / "mcp_config.json",
            # Docker Host Mounts
            HOST_APPDATA / "Antigravity" / "mcp_config.json",
            HOST_APPDATA / "Antigravity" / "mcp.json",
            HOST_APPDATA / "GitKraken" / "Antigravity" / "mcp_config.json",
            HOST_HOME / ".config" / "antigravity" / "mcp_config.json",
            HOST_HOME / ".antigravity" / "mcp_config.json",
            HOST_HOME / "Library" / "Application Support" / "Antigravity" / "mcp_config.json",
        ]

        return self._parse_standard_format(paths, "antigravity-ide")

    # ═══════════════════════════════════════════════════════════════
    # ZED EDITOR
    # ═══════════════════════════════════════════════════════════════

    def parse_zed_editor(self) -> list[MCPServerInfo]:
        """Parse Zed Editor MCP configuration."""
        paths = [
            # Primary Zed config locations
            Path.home() / ".config" / "zed" / "mcp.json",
            Path.home() / ".config" / "zed" / "settings.json",  # Might contain MCP config
            Path(os.environ.get("APPDATA", "")) / "Zed" / "mcp.json",  # Windows
            Path(os.environ.get("APPDATA", "")) / "Zed" / "settings.json",  # Windows - contains context_servers section
            Path.home() / "Library" / "Application Support" / "Zed" / "mcp.json",  # Mac
            Path.home() / "Library" / "Application Support" / "Zed" / "settings.json",  # Mac
            # Alternative locations
            Path.home() / ".zed" / "mcp.json",
            Path.home() / ".zed" / "settings.json",
        ]

        # Try standard format first, then Zed-specific format
        result = self._parse_standard_format(paths, "zed-editor")
        if not result:
            result = self._parse_zed_settings(paths, "zed-editor")
        return result

    # ═══════════════════════════════════════════════════════════════
    # VSCODE (Generic)
    # ═══════════════════════════════════════════════════════════════

    def parse_vscode_generic(self) -> list[MCPServerInfo]:
        """Parse generic VSCode MCP configuration from various MCP extensions."""
        paths = [
            # Standard VSCode User settings
            Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "settings.json",
            Path.home() / ".config" / "Code" / "User" / "settings.json",  # Linux
            Path.home() / "Library" / "Application Support" / "Code" / "User" / "settings.json",  # Mac
            # VSCode Insiders
            Path(os.environ.get("APPDATA", "")) / "Code - Insiders" / "User" / "settings.json",
            Path.home() / ".config" / "Code - Insiders" / "User" / "settings.json",
            # Cursor (VSCode-based)
            Path.home() / ".cursor" / "User" / "settings.json",
            # VSCodium
            Path(os.environ.get("APPDATA", "")) / "VSCodium" / "User" / "settings.json",
            Path.home() / ".config" / "VSCodium" / "User" / "settings.json",
            # Dedicated MCP config files (less common)
            Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "mcp_settings.json",
            Path.home() / ".config" / "Code" / "User" / "mcp_settings.json",
        ]

        # VSCode settings.json might contain MCP config in various formats
        return self._parse_vscode_settings(paths, "vscode")

    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════

    def _parse_standard_format(self, paths: list[Path], source: str) -> list[MCPServerInfo]:
        """
        Parse standard MCP config format (mcpServers).

        Most clients use the same format as Claude Desktop.
        """
        logger.info(f"Scanning {len(paths)} paths for {source}: {[str(p) for p in paths]}")
        for config_path in paths:
            exists = config_path.exists()
            logger.info(f"Checking {source} config: {config_path} (exists: {exists})")
            if not exists:
                continue

            try:
                logger.debug(f"Checking {source} config", path=str(config_path))

                with open(config_path, encoding="utf-8") as f:
                    config = json.load(f)

                # Look for mcpServers key
                if "mcpServers" not in config:
                    continue

                servers = []
                mcp_servers = config.get("mcpServers", {})

                for server_id, server_config in mcp_servers.items():
                    server = MCPServerInfo(
                        id=f"{source}:{server_id}",
                        name=server_id.replace("-", " ").replace("_", " ").title(),
                        command=server_config.get("command", ""),
                        args=server_config.get("args", []),
                        cwd=server_config.get("cwd"),
                        env=server_config.get("env"),
                        source=source,
                    )
                    servers.append(server)

                if servers:
                    logger.info(f"Parsed {len(servers)} MCP servers from {source}", path=str(config_path))
                    return servers

            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in {source} config", path=str(config_path), error=str(e))
            except Exception as e:
                logger.debug(f"Error parsing {source} config", path=str(config_path), error=str(e))

        logger.debug(f"No {source} MCP config found")
        return []

    def _parse_continue_format(self, paths: list[Path], source: str) -> list[MCPServerInfo]:
        """
        Parse Continue.dev specific format.

        Continue.dev might have different structure than standard.
        """
        for config_path in paths:
            if not config_path.exists():
                continue

            try:
                with open(config_path, encoding="utf-8") as f:
                    config = json.load(f)

                servers = []

                # Continue.dev might use "models" or "mcpServers" or "mcp"
                if "mcpServers" in config:
                    # Standard format
                    for server_id, server_config in config["mcpServers"].items():
                        server = MCPServerInfo(
                            id=f"{source}:{server_id}",
                            name=server_id.replace("-", " ").replace("_", " ").title(),
                            command=server_config.get("command", ""),
                            args=server_config.get("args", []),
                            cwd=server_config.get("cwd"),
                            env=server_config.get("env"),
                            source=source,
                        )
                        servers.append(server)

                elif "mcp" in config and isinstance(config["mcp"], dict):
                    # Alternative format
                    for server_id, server_config in config["mcp"].items():
                        server = MCPServerInfo(
                            id=f"{source}:{server_id}",
                            name=server_id.replace("-", " ").replace("_", " ").title(),
                            command=server_config.get("command", ""),
                            args=server_config.get("args", []),
                            cwd=server_config.get("cwd"),
                            env=server_config.get("env"),
                            source=source,
                        )
                        servers.append(server)

                if servers:
                    logger.info(f"Parsed {len(servers)} MCP servers from {source}", path=str(config_path))
                    return servers

            except Exception as e:
                logger.debug(f"Error parsing {source} config", path=str(config_path), error=str(e))

        logger.debug(f"No {source} MCP config found")
        return []

    def _parse_vscode_settings(self, paths: list[Path], source: str) -> list[MCPServerInfo]:
        """
        Parse VSCode settings.json files which may contain MCP configurations.

        VSCode extensions can store MCP config in various ways within settings.json.
        """
        for config_path in paths:
            if not config_path.exists():
                continue

            try:
                logger.debug(f"Checking {source} settings", path=str(config_path))

                with open(config_path, encoding="utf-8") as f:
                    settings = json.load(f)

                servers = []

                # Look for various MCP configuration patterns in VSCode settings
                # Pattern 1: Direct mcpServers in settings
                if "mcpServers" in settings and isinstance(settings["mcpServers"], dict):
                    for server_id, server_config in settings["mcpServers"].items():
                        server = MCPServerInfo(
                            id=f"{source}:{server_id}",
                            name=server_id.replace("-", " ").replace("_", " ").title(),
                            command=server_config.get("command", ""),
                            args=server_config.get("args", []),
                            cwd=server_config.get("cwd"),
                            env=server_config.get("env"),
                            source=source,
                        )
                        servers.append(server)

                # Pattern 2: Extension-specific settings (e.g., "cline.mcpServers")
                for key, value in settings.items():
                    if key.endswith(".mcpServers") and isinstance(value, dict):
                        for server_id, server_config in value.items():
                            server = MCPServerInfo(
                                id=f"{source}:{server_id}",
                                name=server_id.replace("-", " ").replace("_", " ").title(),
                                command=server_config.get("command", ""),
                                args=server_config.get("args", []),
                                cwd=server_config.get("cwd"),
                                env=server_config.get("env"),
                                source=source,
                            )
                            servers.append(server)

                if servers:
                    logger.info(
                        f"Parsed {len(servers)} MCP servers from {source} settings",
                        path=str(config_path),
                    )
                    return servers

            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in {source} settings", path=str(config_path), error=str(e))
            except Exception as e:
                logger.debug(f"Error parsing {source} settings", path=str(config_path), error=str(e))

        logger.debug(f"No {source} MCP settings found")
        return []

    def _parse_zed_settings(self, paths: list[Path], source: str) -> list[MCPServerInfo]:
        """
        Parse Zed Editor settings.json files which contain MCP configs in "context_servers" section.

        Zed stores MCP server configs in settings.json under "context_servers" key.
        """
        for config_path in paths:
            if not config_path.exists():
                continue

            try:
                logger.info(f"Checking Zed settings: {config_path} (exists: True)")

                with open(config_path, encoding="utf-8") as f:
                    content = f.read()

                # Remove comments (lines starting with //) before parsing JSON
                lines = content.split("\n")
                json_lines = [line for line in lines if not line.strip().startswith("//")]
                json_content = "\n".join(json_lines)

                settings = json.loads(json_content)

                servers = []

                # Zed uses "context_servers" section for MCP configs
                if "context_servers" in settings and isinstance(settings["context_servers"], dict):
                    for server_id, server_config in settings["context_servers"].items():
                        if isinstance(server_config, dict):
                            server = MCPServerInfo(
                                id=f"{source}:{server_id}",
                                name=server_id.replace("-", " ").replace("_", " ").title(),
                                command=server_config.get("command", ""),
                                args=server_config.get("args", []),
                                cwd=server_config.get("cwd"),
                                env=server_config.get("env"),
                                source=source,
                            )
                            servers.append(server)

                if servers:
                    logger.info(
                        f"Parsed {len(servers)} MCP servers from Zed settings",
                        path=str(config_path),
                    )
                    return servers

            except json.JSONDecodeError as e:
                logger.warning("Invalid JSON in Zed settings", path=str(config_path), error=str(e))
            except Exception as e:
                logger.debug("Error parsing Zed settings", path=str(config_path), error=str(e))

        logger.debug("No Zed MCP settings found")
        return []

    # ═══════════════════════════════════════════════════════════════
    # SCAN ALL CLIENTS
    # ═══════════════════════════════════════════════════════════════

    def scan_all_clients(self) -> dict[str, list[MCPServerInfo]]:
        """
        Scan ALL known MCP clients and return discovered servers.

        Returns:
            Dictionary mapping source name to list of servers
        """
        logger.info("Scanning MCP Client Zoo...")

        results = {}

        # Define all client parsers
        parsers = [
            ("claude-desktop", self.parse_claude_desktop),
            ("cursor-ide", self.parse_cursor_ide),
            ("windsurf-ide", self.parse_windsurf_ide),
            ("cline-vscode", self.parse_cline),
            ("roo-cline", self.parse_roo_cline),
            ("continue-dev", self.parse_continue_dev),
            ("lm-studio", self.parse_lm_studio),
            ("antigravity-ide", self.parse_antigravity_ide),
            ("zed-editor", self.parse_zed_editor),
            ("vscode-generic", self.parse_vscode_generic),
        ]

        # Parse each client
        total_servers = 0
        for client_name, parser in parsers:
            try:
                servers = parser()
                if servers:
                    results[client_name] = servers
                    total_servers += len(servers)
                    self.sources_found.append(client_name)
                    logger.info(
                        f"Found {len(servers)} servers in {client_name}",
                        servers=[s.name for s in servers],
                    )
            except Exception as e:
                logger.warning(f"Error parsing {client_name}", error=str(e))

        logger.info(
            "[SUCCESS] Client Zoo scan complete",
            total_servers=total_servers,
            sources=len(self.sources_found),
            found_in=self.sources_found,
        )

        return results

    def discover_client_settings(self, client_id: str) -> Any | None:
        """
        Discover and parse settings from a client configuration file(s).

        Args:
            client_id: The client identifier (e.g., 'cursor-ide', 'claude-desktop')

        Returns:
            ClientConfig object with discovered settings, or None if not found
        """
        return self.settings_manager.discover_client_settings(client_id)

    def get_client_settings(self, client_id: str) -> dict[str, Any] | None:
        """
        Get all settings for a client, organized by category.

        Args:
            client_id: The client identifier

        Returns:
            Dictionary with categorized settings, or None if client not found
        """
        # First try to discover settings if not already loaded
        if client_id not in self.settings_manager.clients:
            self.discover_client_settings(client_id)

        return self.settings_manager.get_client_settings(client_id)

    def update_client_setting(self, client_id: str, key: str, value: Any, create_backup: bool = True) -> bool:
        """
        Update a specific setting for a client.

        Args:
            client_id: The client identifier
            key: Setting key to update
            value: New value for the setting
            create_backup: Whether to create a backup before updating

        Returns:
            True if update succeeded, False otherwise
        """
        return self.settings_manager.update_setting(client_id, key, value, create_backup)

    def _get_client_config_path(self, client_id: str) -> Path | None:
        """
        Get the configuration file path for a client.

        Args:
            client_id: The client identifier

        Returns:
            Path to the client's config file, or None if not found
        """
        # Use the settings manager's method for consistency
        configs = self.settings_manager.get_client_config_paths(client_id)
        if configs:
            # For MCP scanning, we want the MCP-specific config if available, otherwise main config
            mcp_configs = [config for config_type, config in configs if config_type == "mcp"]
            if mcp_configs:
                return mcp_configs[0]
            # Fallback to main config
            main_configs = [config for config_type, config in configs if config_type == "main"]
            if main_configs:
                return main_configs[0]

        logger.warning(f"Config path not found for client: {client_id}")
        return None

    def get_setting_categories(self) -> dict[str, dict[str, Any]]:
        """
        Get information about available setting categories.

        Returns:
            Dictionary mapping category IDs to category info
        """
        return self.settings_manager.get_setting_categories()

    def get_all_servers(self) -> list[MCPServerInfo]:
        """
        Get deduplicated list of all MCP servers from all clients.

        Returns:
            List of unique MCP servers
        """
        results = self.scan_all_clients()

        # Deduplicate servers (same command+args = same server)
        unique_servers = {}

        for _source, servers in results.items():
            for server in servers:
                # Create unique key based on command and args
                key = f"{server.command}:{':'.join(server.args)}"

                if key not in unique_servers:
                    unique_servers[key] = server
                else:
                    # Server exists from another client
                    existing = unique_servers[key]
                    existing.source += f", {server.source}"

        logger.info(
            "Deduplicated servers",
            total=len(unique_servers),
            original=sum(len(s) for s in results.values()),
        )

        return list(unique_servers.values())

    def get_summary(self) -> dict[str, Any]:
        """
        Get summary of all discovered MCP clients and servers.

        Returns:
            Summary dictionary with statistics
        """
        results = self.scan_all_clients()

        summary = {
            "total_clients": len(results),
            "total_servers": sum(len(s) for s in results.values()),
            "unique_servers": len(self.get_all_servers()),
            "clients_found": self.sources_found,
            "breakdown": {
                client: {"count": len(servers), "servers": [s.name for s in servers]}
                for client, servers in results.items()
            },
        }

        return summary

    def get_client_config_path(self, client_id: str) -> Path | None:
        """
        Get the config file path for a specific client.

        Args:
            client_id: Client identifier (e.g., "claude-desktop", "cursor-ide")

        Returns:
            Path to config file if found, None otherwise
        """
        # Map client IDs to their parser methods
        parser_map = {
            "claude-desktop": self.parse_claude_desktop,
            "cursor-ide": self.parse_cursor_ide,
            "windsurf-ide": self.parse_windsurf_ide,
            "antigravity-ide": self.parse_antigravity_ide,
            "cline-vscode": self.parse_cline,
            "roo-cline": self.parse_roo_cline,
            "continue-dev": self.parse_continue_dev,
            "lm-studio": self.parse_lm_studio,
            "zed-editor": self.parse_zed_editor,
            "vscode-generic": self.parse_vscode_generic,
        }

        parser = parser_map.get(client_id)
        if not parser:
            return None

        # Get the paths that the parser checks
        # We need to check which paths each parser uses
        if client_id == "claude-desktop":
            paths = [
                Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
                Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
                # Docker Host Mounts
                HOST_APPDATA / "Claude" / "claude_desktop_config.json",
                HOST_HOME / ".config" / "Claude" / "claude_desktop_config.json",
                HOST_HOME / "Library" / "Application Support" / "Claude" / "claude_desktop_config.json",
            ]
        elif client_id == "cursor-ide":
            paths = [
                Path(os.environ.get("APPDATA", ""))
                / "Cursor"
                / "User"
                / "globalStorage"
                / "saoudrizwan.claude-dev"
                / "settings"
                / "cline_mcp_settings.json",
                Path(os.environ.get("APPDATA", "")) / "Cursor" / "mcp_settings.json",
                Path.home() / ".cursor" / "mcp_settings.json",
                Path.home() / ".config" / "Cursor" / "User" / "mcp_settings.json",
                # Docker Host Mounts
                HOST_APPDATA
                / "Cursor"
                / "User"
                / "globalStorage"
                / "saoudrizwan.claude-dev"
                / "settings"
                / "cline_mcp_settings.json",
                HOST_APPDATA / "Cursor" / "mcp_settings.json",
                HOST_HOME / ".cursor" / "mcp.json",
                HOST_HOME / ".cursor" / "mcp_settings.json",
                HOST_HOME / ".config" / "Cursor" / "User" / "mcp_settings.json",
            ]
        elif client_id == "windsurf-ide":
            paths = [
                Path(os.environ.get("APPDATA", ""))
                / "Windsurf"
                / "User"
                / "globalStorage"
                / "rooveterinaryinc.roo-cline"
                / "settings"
                / "mcp_settings.json",
                Path(os.environ.get("APPDATA", "")) / "Windsurf" / "mcp_settings.json",
                Path.home() / ".config" / "Windsurf" / "mcp_settings.json",
            ]
        elif client_id == "antigravity-ide":
            paths = [
                Path(os.environ.get("APPDATA", "")) / "Antigravity" / "mcp_config.json",
                Path(os.environ.get("APPDATA", "")) / "Antigravity" / "mcp.json",
                Path(os.environ.get("APPDATA", "")) / "GitKraken" / "Antigravity" / "mcp_config.json",
                Path.home() / ".config" / "antigravity" / "mcp_config.json",
                Path.home() / ".config" / "antigravity" / "mcp.json",
                Path.home() / ".antigravity" / "mcp_config.json",
                Path.home() / ".antigravity" / "mcp.json",
                Path.home() / "Library" / "Application Support" / "Antigravity" / "mcp_config.json",
                # Docker Host Mounts
                HOST_APPDATA / "Antigravity" / "mcp_config.json",
                HOST_APPDATA / "Antigravity" / "mcp.json",
                HOST_APPDATA / "GitKraken" / "Antigravity" / "mcp_config.json",
                HOST_HOME / ".config" / "antigravity" / "mcp_config.json",
                HOST_HOME / ".antigravity" / "mcp_config.json",
                HOST_HOME / "Library" / "Application Support" / "Antigravity" / "mcp_config.json",
            ]
        elif client_id == "zed-editor":
            paths = [
                Path.home() / ".config" / "zed" / "mcp.json",
                Path(os.environ.get("APPDATA", "")) / "Zed" / "mcp.json",
                Path.home() / "Library" / "Application Support" / "Zed" / "mcp.json",
            ]
        else:
            # For other clients, try to find config by parsing
            servers = parser()
            if servers and hasattr(servers[0], "source"):
                # Try to find the config file by checking paths
                return None  # Would need to track which path was used

        # Check which path exists
        for path in paths:
            if path.exists():
                return path

        return None


# ═══════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════


def discover_all_mcp_clients() -> dict[str, Any]:
    """
    Discover MCP servers from ALL known MCP clients.

    Returns:
        Summary of discovered servers
    """
    zoo = MCPClientZoo()
    return zoo.get_summary()


def get_all_mcp_servers() -> list[MCPServerInfo]:
    """
    Get deduplicated list of all MCP servers from all clients.

    Returns:
        List of unique MCP servers
    """
    zoo = MCPClientZoo()
    return zoo.get_all_servers()


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\nMCP CLIENT ZOO SCANNER\n")
    print("=" * 60)

    summary = discover_all_mcp_clients()

    print("\n[STATS] SUMMARY:")
    print(f"  Total Clients:  {summary['total_clients']}")
    print(f"  Total Servers:  {summary['total_servers']}")
    print(f"  Unique Servers: {summary['unique_servers']}")
    print(f"  Sources Found:  {', '.join(summary['clients_found'])}")

    print("\nBREAKDOWN:")
    for client, data in summary["breakdown"].items():
        print(f"\n  {client.upper()}: {data['count']} servers")
        for server_name in data["servers"]:
            print(f"    • {server_name}")

    print("\n" + "=" * 60)
    print("Scan complete!\n")
