"""
Client Settings Manager - Discover and manage IDE client configuration settings
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class SettingType(Enum):
    """Types of settings we can manage."""
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    ARRAY = "array"
    OBJECT = "object"
    UNKNOWN = "unknown"


class SettingCategory(Enum):
    """Categories for organizing settings."""
    EDITOR = "editor"
    WORKBENCH = "workbench"
    TERMINAL = "terminal"
    THEME = "theme"
    EXTENSIONS = "extensions"
    FILES = "files"
    SEARCH = "search"
    GIT = "git"
    DEBUG = "debug"
    OTHER = "other"


@dataclass
class ClientSetting:
    """Represents a client configuration setting."""
    key: str
    value: Any
    setting_type: SettingType
    category: SettingCategory
    description: Optional[str] = None
    display_name: Optional[str] = None
    editable: bool = True
    validation_rules: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ClientConfig:
    """Represents a client's configuration file."""
    client_id: str
    config_path: Path
    settings: Dict[str, ClientSetting] = field(default_factory=dict)
    raw_config: Dict[str, Any] = field(default_factory=dict)


class ClientSettingsManager:
    """Manages client configuration settings discovery and editing."""

    def __init__(self):
        self.clients: Dict[str, ClientConfig] = {}
        self._setting_patterns = self._build_setting_patterns()

    def _build_setting_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Build patterns for categorizing and describing settings."""
        return {
            # Editor settings
            "editor.": {
                "category": SettingCategory.EDITOR,
                "description": "Code editor configuration"
            },
            "diffEditor.": {
                "category": SettingCategory.EDITOR,
                "description": "Diff editor settings"
            },

            # Workbench/UI settings
            "workbench.": {
                "category": SettingCategory.WORKBENCH,
                "description": "Workbench and UI configuration"
            },
            "window.": {
                "category": SettingCategory.WORKBENCH,
                "description": "Window management settings"
            },

            # Terminal settings
            "terminal.": {
                "category": SettingCategory.TERMINAL,
                "description": "Integrated terminal configuration"
            },

            # Theme and appearance
            "colorTheme": {
                "category": SettingCategory.THEME,
                "description": "Color theme selection",
                "display_name": "Color Theme"
            },
            "iconTheme": {
                "category": SettingCategory.THEME,
                "description": "Icon theme selection",
                "display_name": "Icon Theme"
            },

            # File management
            "files.": {
                "category": SettingCategory.FILES,
                "description": "File handling and management"
            },
            "explorer.": {
                "category": SettingCategory.FILES,
                "description": "File explorer configuration"
            },

            # Search settings
            "search.": {
                "category": SettingCategory.SEARCH,
                "description": "Search and find functionality"
            },

            # Git settings
            "git.": {
                "category": SettingCategory.GIT,
                "description": "Git integration settings"
            },

            # Debug settings
            "debug.": {
                "category": SettingCategory.DEBUG,
                "description": "Debugger configuration"
            },
            "launch.": {
                "category": SettingCategory.DEBUG,
                "description": "Launch configuration"
            },
        }

    def _infer_setting_type(self, value: Any) -> SettingType:
        """Infer the type of a setting value."""
        if isinstance(value, str):
            return SettingType.STRING
        elif isinstance(value, (int, float)):
            return SettingType.NUMBER
        elif isinstance(value, bool):
            return SettingType.BOOLEAN
        elif isinstance(value, list):
            return SettingType.ARRAY
        elif isinstance(value, dict):
            return SettingType.OBJECT
        else:
            return SettingType.UNKNOWN

    def _categorize_setting(self, key: str) -> Tuple[SettingCategory, Optional[str], Optional[str]]:
        """Categorize a setting based on its key."""
        for pattern, info in self._setting_patterns.items():
            if key.startswith(pattern) or pattern.rstrip('.') == key:
                return (
                    info["category"],
                    info.get("description"),
                    info.get("display_name", key.replace('.', ' ').title())
                )

        # Extension-specific settings
        if '.' in key and any(ext in key.lower() for ext in ['cline', 'continue', 'gemini', 'roo', 'anthropic']):
            return SettingCategory.EXTENSIONS, "Extension-specific settings", key

        # Default to other
        return SettingCategory.OTHER, None, key.replace('.', ' ').title()

    def _create_setting(self, key: str, value: Any) -> ClientSetting:
        """Create a ClientSetting object from a key-value pair."""
        category, description, display_name = self._categorize_setting(key)

        return ClientSetting(
            key=key,
            value=value,
            setting_type=self._infer_setting_type(value),
            category=category,
            description=description,
            display_name=display_name,
            editable=self._is_setting_editable(key, value)
        )

    def _is_setting_editable(self, key: str, value: Any) -> bool:
        """Determine if a setting should be editable in the UI."""
        # Don't allow editing certain sensitive or complex settings
        non_editable_patterns = [
            "mcpServers",  # We handle this separately
            "machineId",   # System identifiers
            "install",     # Installation settings
            "telemetry",   # Telemetry settings (usually locked)
        ]

        if any(pattern in key for pattern in non_editable_patterns):
            return False

        # Only allow editing simple types
        editable_types = (str, int, float, bool, list)
        return isinstance(value, editable_types)

    def discover_client_settings(self, client_id: str, config_path: Optional[Path] = None) -> Optional[ClientConfig]:
        """
        Discover and parse settings from a client configuration file(s).

        Args:
            client_id: The client identifier
            config_path: Optional specific config path (uses auto-discovery if None)

        Returns:
            ClientConfig object with discovered settings, or None if not found
        """
        try:
            # Get all config files for this client
            if config_path:
                # Single config file specified
                config_files = [("main", config_path)]
            else:
                # Auto-discover all config files
                config_files = self.get_client_config_paths(client_id)

            if not config_files:
                logger.warning(f"No config files found for client: {client_id}")
                return None

            all_settings = {}
            combined_raw_config = {}

            # Process each config file
            for config_type, config_path in config_files:
                if not config_path.exists():
                    continue

                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        raw_config = json.load(f)

                    # For MCP-specific configs, only process MCP-related settings
                    if config_type == "mcp":
                        # MCP configs typically only contain mcpServers
                        if "mcpServers" in raw_config:
                            # Add MCP server settings with a special prefix
                            for server_name in raw_config["mcpServers"]:
                                setting_key = f"mcp.servers.{server_name}"
                                all_settings[setting_key] = ClientSetting(
                                    key=setting_key,
                                    value=raw_config["mcpServers"][server_name],
                                    setting_type=SettingType.OBJECT,
                                    category=SettingCategory.EXTENSIONS,
                                    description=f"MCP server configuration for {server_name}",
                                    display_name=f"MCP: {server_name}",
                                    editable=False  # MCP configs are managed separately
                                )
                            combined_raw_config[f"_mcp_{config_type}"] = raw_config
                        continue

                    # For main configs, process all non-MCP settings
                    if "mcpServers" in raw_config:
                        config_for_settings = {k: v for k, v in raw_config.items() if k != "mcpServers"}
                    else:
                        config_for_settings = raw_config

                    # Create settings from this config
                    for key, value in config_for_settings.items():
                        if key not in all_settings:  # Don't override existing settings
                            all_settings[key] = self._create_setting(key, value)

                    combined_raw_config[f"_{config_type}"] = raw_config

                except Exception as e:
                    logger.warning(f"Failed to read config file {config_path}: {e}")
                    continue

            if not all_settings:
                logger.warning(f"No settings found for client: {client_id}")
                return None

            # Use the first config path as the primary path
            primary_path = config_files[0][1]

            client_config = ClientConfig(
                client_id=client_id,
                config_path=primary_path,
                settings=all_settings,
                raw_config=combined_raw_config
            )

            self.clients[client_id] = client_config
            logger.info(f"Discovered {len(all_settings)} settings for client {client_id} from {len(config_files)} config files")

            return client_config

        except Exception as e:
            logger.error(f"Failed to discover settings for client {client_id}: {e}")
            return None

    def get_client_settings(self, client_id: str) -> Optional[Dict[str, Any]]:
        """Get all settings for a client, organized by category."""
        client_config = self.clients.get(client_id)
        if not client_config:
            return None

        categorized = {}
        for setting in client_config.settings.values():
            category_name = setting.category.value
            if category_name not in categorized:
                categorized[category_name] = []

            categorized[category_name].append({
                "key": setting.key,
                "value": setting.value,
                "type": setting.setting_type.value,
                "description": setting.description,
                "display_name": setting.display_name or setting.key,
                "editable": setting.editable
            })

        # Sort categories and settings within categories
        sorted_categorized = {}
        for category in sorted(categorized.keys()):
            sorted_categorized[category] = sorted(
                categorized[category],
                key=lambda x: x["display_name"].lower()
            )

        return {
            "client_id": client_id,
            "categories": sorted_categorized,
            "total_settings": len(client_config.settings),
            "editable_settings": sum(1 for s in client_config.settings.values() if s.editable)
        }

    def get_setting(self, client_id: str, key: str) -> Optional[Dict[str, Any]]:
        """Get a specific setting."""
        client_config = self.clients.get(client_id)
        if not client_config or key not in client_config.settings:
            return None

        setting = client_config.settings[key]
        return {
            "key": setting.key,
            "value": setting.value,
            "type": setting.setting_type.value,
            "category": setting.category.value,
            "description": setting.description,
            "display_name": setting.display_name,
            "editable": setting.editable
        }

    def update_setting(self, client_id: str, key: str, value: Any, create_backup: bool = True) -> bool:
        """Update a specific setting value."""
        client_config = self.clients.get(client_id)
        if not client_config:
            logger.error(f"Client config not found: {client_id}")
            return False

        if key not in client_config.settings:
            logger.error(f"Setting not found: {key}")
            return False

        setting = client_config.settings[key]
        if not setting.editable:
            logger.error(f"Setting is not editable: {key}")
            return False

        try:
            # Validate the new value type matches the expected type
            if not self._validate_setting_value(value, setting.setting_type):
                logger.error(f"Invalid value type for setting {key}")
                return False

            # Determine which config file to update
            target_config_path, target_config_key = self._find_setting_location(client_id, key)

            if not target_config_path:
                logger.error(f"Could not determine config file location for setting {key}")
                return False

            # Create backup if requested
            if create_backup:
                backup_path = self._create_backup_for_path(target_config_path, f"before_setting_{key}")
                if not backup_path:
                    logger.error("Failed to create backup")
                    return False

            # Load the target config file
            with open(target_config_path, 'r', encoding='utf-8') as f:
                target_config = json.load(f)

            # Update the setting in the target config
            if target_config_key:
                # Setting is at a nested path (e.g., mcp.servers.server_name)
                keys = target_config_key.split('.')
                current = target_config
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            else:
                # Direct setting in the config
                target_config[key] = value

            # Write back to file
            with open(target_config_path, 'w', encoding='utf-8') as f:
                json.dump(target_config, f, indent=2, ensure_ascii=False)

            # Update our in-memory representation
            setting.value = value
            if target_config_key:
                # Update nested config
                keys = target_config_key.split('.')
                current = client_config.raw_config
                for k in keys[:-1]:
                    if k not in current:
                        current[k] = {}
                    current = current[k]
                current[keys[-1]] = value
            else:
                client_config.raw_config[key] = value

            logger.info(f"Updated setting {key} for client {client_id} in {target_config_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to update setting {key}: {e}")
            return False

    def _find_setting_location(self, client_id: str, key: str) -> Tuple[Optional[Path], Optional[str]]:
        """
        Find which config file and key path contains a setting.

        Returns:
            (config_path, config_key) where config_key is the path within the config file
        """
        config_files = self.get_client_config_paths(client_id)

        # Check MCP-specific settings first
        if key.startswith("mcp.servers."):
            server_name = key.replace("mcp.servers.", "")
            for config_type, config_path in config_files:
                if config_type == "mcp" and config_path.exists():
                    try:
                        with open(config_path, 'r', encoding='utf-8') as f:
                            config = json.load(f)
                        if "mcpServers" in config and server_name in config["mcpServers"]:
                            return config_path, f"mcpServers.{server_name}"
                    except Exception:
                        continue

        # Check main config files for regular settings
        for config_type, config_path in config_files:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    if key in config:
                        return config_path, None
                except Exception:
                    continue

        return None, None

    def _create_backup_for_path(self, config_path: Path, backup_name: str) -> Optional[Path]:
        """Create a backup of a specific config file."""
        try:
            backup_dir = config_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)

            backup_path = backup_dir / f"{backup_name}.json"
            import shutil
            shutil.copy2(config_path, backup_path)

            logger.info(f"Created backup: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def _validate_setting_value(self, value: Any, expected_type: SettingType) -> bool:
        """Validate that a value matches the expected setting type."""
        if expected_type == SettingType.STRING:
            return isinstance(value, str)
        elif expected_type == SettingType.NUMBER:
            return isinstance(value, (int, float))
        elif expected_type == SettingType.BOOLEAN:
            return isinstance(value, bool)
        elif expected_type == SettingType.ARRAY:
            return isinstance(value, list)
        elif expected_type == SettingType.OBJECT:
            return isinstance(value, dict)
        else:
            # For unknown types, be permissive
            return True

    def _create_backup(self, client_config: ClientConfig, backup_name: str) -> Optional[Path]:
        """Create a backup of the client config."""
        try:
            backup_dir = client_config.config_path.parent / "backups"
            backup_dir.mkdir(exist_ok=True)

            backup_path = backup_dir / f"{backup_name}.json"
            import shutil
            shutil.copy2(client_config.config_path, backup_path)

            logger.info(f"Created backup: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            return None

    def get_setting_categories(self) -> Dict[str, Dict[str, Any]]:
        """Get information about available setting categories."""
        return {
            category.value: {
                "name": category.value.title(),
                "description": self._get_category_description(category),
                "icon": self._get_category_icon(category)
            }
            for category in SettingCategory
        }

    def _get_category_description(self, category: SettingCategory) -> str:
        """Get human-readable description for a category."""
        descriptions = {
            SettingCategory.EDITOR: "Code editor configuration and behavior",
            SettingCategory.WORKBENCH: "User interface and workbench settings",
            SettingCategory.TERMINAL: "Integrated terminal configuration",
            SettingCategory.THEME: "Appearance and theming options",
            SettingCategory.EXTENSIONS: "Extension-specific settings",
            SettingCategory.FILES: "File handling and workspace settings",
            SettingCategory.SEARCH: "Search and find functionality",
            SettingCategory.GIT: "Git integration and version control",
            SettingCategory.DEBUG: "Debugger and development tools",
            SettingCategory.OTHER: "Miscellaneous settings"
        }
        return descriptions.get(category, "General settings")

    def _get_category_icon(self, category: SettingCategory) -> str:
        """Get icon class for a category."""
        icons = {
            SettingCategory.EDITOR: "fas fa-edit",
            SettingCategory.WORKBENCH: "fas fa-desktop",
            SettingCategory.TERMINAL: "fas fa-terminal",
            SettingCategory.THEME: "fas fa-palette",
            SettingCategory.EXTENSIONS: "fas fa-puzzle-piece",
            SettingCategory.FILES: "fas fa-folder",
            SettingCategory.SEARCH: "fas fa-search",
            SettingCategory.GIT: "fab fa-git",
            SettingCategory.DEBUG: "fas fa-bug",
            SettingCategory.OTHER: "fas fa-cog"
        }
        return icons.get(category, "fas fa-cog")

    def get_client_config_paths(self, client_id: str) -> List[Tuple[str, Path]]:
        """
        Get all configuration file paths for a client.

        Args:
            client_id: The client identifier

        Returns:
            List of (config_type, path) tuples for the client
        """
        from pathlib import Path
        import os

        appdata = Path(os.environ.get("APPDATA", ""))

        # VSCode-based clients can have multiple config files
        if client_id in ["cursor-ide", "windsurf-ide", "cline-vscode", "continue-dev", "vscode-generic"]:
            configs = []

            # Main VSCode settings.json for general settings
            main_settings = appdata / "Code" / "User" / "settings.json"
            if main_settings.exists():
                configs.append(("main", main_settings))

            # Extension-specific configs
            if client_id == "cline-vscode":
                # Roo-Cline MCP config
                roo_cline_mcp = appdata / "Code" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "mcp_settings.json"
                if roo_cline_mcp.exists():
                    configs.append(("mcp", roo_cline_mcp))

                # Claude Dev (original Cline) MCP config - fallback
                claude_dev_mcp = appdata / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json"
                if claude_dev_mcp.exists():
                    configs.append(("mcp", claude_dev_mcp))

            return configs

        # Claude Desktop
        elif client_id == "claude-desktop":
            paths = [
                appdata / "Claude" / "claude_desktop_config.json",
                Path.home() / ".config" / "Claude" / "claude_desktop_config.json",
            ]
            for path in paths:
                if path.exists():
                    return [("main", path)]

        # Antigravity IDE
        elif client_id == "antigravity-ide":
            paths = [
                Path.home() / ".gemini" / "antigravity" / "mcp_config.json",
            ]
            for path in paths:
                if path.exists():
                    return [("main", path)]

        # Zed Editor
        elif client_id == "zed-editor":
            paths = [
                Path.home() / "Library" / "Application Support" / "Zed" / "settings.json",  # macOS
                Path.home() / ".config" / "zed" / "settings.json",  # Linux
                appdata / "Zed" / "settings.json",  # Windows
            ]
            for path in paths:
                if path.exists():
                    return [("main", path)]

        # LM Studio
        elif client_id == "lm-studio":
            # Check both possible LM Studio config locations
            lm_studio_paths = [
                Path.home() / ".lmstudio" / "mcp.json",        # User's preferred location
                appdata / "LM Studio" / "config.json",         # Alternative location
            ]
            for path in lm_studio_paths:
                if path.exists():
                    return [("main", path)]

        return []

    def _get_client_config_path(self, client_id: str) -> Optional[Path]:
        """
        Get the primary configuration file path for a client (backwards compatibility).

        Args:
            client_id: The client identifier

        Returns:
            Path to the client's primary config file, or None if not found
        """
        configs = self.get_client_config_paths(client_id)
        if configs:
            # Return the first (usually main) config
            return configs[0][1]
        return None
