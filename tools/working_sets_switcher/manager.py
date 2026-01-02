"""
MCP Studio Working Set Manager
Manages different working sets of MCP servers for focused workflows.
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

logger = logging.getLogger(__name__)


class WorkingSet:
    """Represents a working set configuration."""

    def __init__(self, data: Dict[str, Any]):
        self.name = data.get("name", "")
        self.id = data.get("id", "")
        self.description = data.get("description", "")
        self.icon = data.get("icon", "🔧")
        self.category = data.get("category", "General")
        self.servers = data.get("servers", [])
        self.created_at = data.get("created_at")
        self.updated_at = data.get("updated_at")

    def get_server_names(self) -> List[str]:
        """Get list of server names in this working set."""
        return [server["name"] for server in self.servers]

    def get_required_servers(self) -> List[str]:
        """Get list of required server names."""
        return [server["name"] for server in self.servers if server.get("required", False)]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "id": self.id,
            "description": self.description,
            "icon": self.icon,
            "category": self.category,
            "servers": self.servers,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
        }


class WorkingSetManager:
    """Manages working sets and Claude Desktop config switching."""

    def __init__(self, config_path: str, backup_dir: str = None, templates_dir: str = None):
        self.config_path = Path(config_path)
        self.backup_dir = Path(backup_dir or self.config_path.parent / "backup")
        self.templates_dir = Path(templates_dir or "templates")

        # Create directories if they don't exist
        try:
            self.backup_dir.mkdir(exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create backup directory (likely read-only fs): {e}")

        try:
            self.templates_dir.mkdir(exist_ok=True)
        except Exception as e:
            logger.warning(f"Could not create templates directory (likely read-only fs): {e}")

        # Load current config and working sets
        self._current_config = self._load_current_config()
        self._working_sets = self._load_working_sets()

    def _load_current_config(self) -> Dict[str, Any]:
        """Load current Claude Desktop config."""
        try:
            if self.config_path.exists():
                with open(self.config_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            return {"mcpServers": {}}
        except Exception as e:
            logger.error(f"Failed to load config: {e}")
            return {"mcpServers": {}}

    def _load_working_sets(self) -> Dict[str, WorkingSet]:
        """Load all working set templates."""
        working_sets = {}
        for template_file in self.templates_dir.glob("*.json"):
            try:
                # Use utf-8-sig to handle UTF-8 BOM markers
                with open(template_file, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                    working_set = WorkingSet(data)
                    working_sets[working_set.id] = working_set
            except Exception as e:
                logger.error(f"Failed to load working set {template_file}: {e}")
        return working_sets

    def list_working_sets(self) -> List[Dict[str, Any]]:
        """Get list of all available working sets."""
        return [ws.to_dict() for ws in self._working_sets.values()]

    def get_working_set(self, working_set_id: str) -> Optional[WorkingSet]:
        """Get specific working set by ID."""
        return self._working_sets.get(working_set_id)

    def get_current_working_set(self) -> Optional[str]:
        """Detect current working set based on active servers."""
        current_servers = set(self._current_config.get("mcpServers", {}).keys())

        # Find best match
        best_match = None
        best_score = 0

        for ws_id, working_set in self._working_sets.items():
            ws_servers = set(working_set.get_server_names())

            # Calculate match score
            intersection = current_servers.intersection(ws_servers)
            union = current_servers.union(ws_servers)

            if len(union) > 0:
                score = len(intersection) / len(union)
                if score > best_score and score > 0.7:  # 70% similarity threshold
                    best_match = ws_id
                    best_score = score

        return best_match

    def create_backup(self, name: str = None) -> str:
        """Create backup of current config."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = name or f"backup_{timestamp}"
        backup_file = self.backup_dir / f"{backup_name}.json"

        try:
            shutil.copy2(self.config_path, backup_file)
            logger.info(f"Created backup: {backup_file}")
            return str(backup_file)
        except Exception as e:
            logger.error(f"Failed to create backup: {e}")
            raise

    def list_backups(self) -> List[Dict[str, Any]]:
        """List all available backups."""
        backups = []
        for backup_file in self.backup_dir.glob("*.json"):
            stat = backup_file.stat()
            backups.append(
                {
                    "name": backup_file.stem,
                    "file": str(backup_file),
                    "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                    "size": stat.st_size,
                }
            )
        return sorted(backups, key=lambda x: x["created"], reverse=True)

    def restore_backup(self, backup_name: str) -> bool:
        """Restore config from backup."""
        backup_file = self.backup_dir / f"{backup_name}.json"
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup not found: {backup_name}")

        try:
            # Create backup of current config first
            self.create_backup("pre_restore")

            # Restore backup
            shutil.copy2(backup_file, self.config_path)
            self._current_config = self._load_current_config()
            logger.info(f"Restored backup: {backup_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to restore backup: {e}")
            raise

    def generate_config_for_working_set(self, working_set_id: str) -> Dict[str, Any]:
        """Generate Claude Desktop config for specific working set."""
        working_set = self.get_working_set(working_set_id)
        if not working_set:
            raise ValueError(f"Working set not found: {working_set_id}")

        # Get server names from working set
        server_names = working_set.get_server_names()

        # Build new config with only specified servers
        new_config = {"mcpServers": {}}
        current_servers = self._current_config.get("mcpServers", {})

        for server_name in server_names:
            if server_name in current_servers:
                new_config["mcpServers"][server_name] = current_servers[server_name]
            else:
                logger.warning(f"Server '{server_name}' not found in current config")

        return new_config

    def switch_to_working_set(self, working_set_id: str, create_backup: bool = True) -> Dict[str, Any]:
        """Switch to specified working set with automatic rollback on failure."""
        working_set = self.get_working_set(working_set_id)
        if not working_set:
            raise ValueError(f"Working set not found: {working_set_id}")

        backup_created = None
        original_config = None

        try:
            # Store original config for potential rollback
            original_config = self._current_config.copy()

            # Create backup if requested
            if create_backup:
                backup_name = f"before_{working_set_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                backup_created = self.create_backup(backup_name)
                logger.info(f"Backup created: {backup_created}")

            # Generate new config
            new_config = self.generate_config_for_working_set(working_set_id)

            # Validate new config structure
            if not isinstance(new_config, dict) or "mcpServers" not in new_config:
                raise ValueError("Generated config is invalid - missing mcpServers key")

            # Write new config
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(new_config, f, indent=2, ensure_ascii=False)

            # Verify the config was written correctly by reading it back
            with open(self.config_path, "r", encoding="utf-8") as f:
                verify_config = json.load(f)

            if not isinstance(verify_config, dict) or "mcpServers" not in verify_config:
                raise ValueError("Written config is corrupted - invalid structure")

            # Update internal state
            self._current_config = new_config

            logger.info(f"Successfully switched to working set: {working_set.name}")
            return {
                "success": True,
                "working_set_id": working_set_id,
                "working_set_name": working_set.name,
                "backup_created": backup_created,
                "servers_count": len(new_config.get("mcpServers", {}))
            }

        except Exception as e:
            logger.error(f"Failed to switch working set {working_set_id}: {e}")

            # Attempt automatic rollback if we have a backup
            if backup_created and original_config:
                try:
                    logger.info("Attempting automatic rollback...")
                    with open(self.config_path, "w", encoding="utf-8") as f:
                        json.dump(original_config, f, indent=2, ensure_ascii=False)
                    self._current_config = original_config
                    logger.info("Rollback successful - config restored from memory")
                except Exception as rollback_error:
                    logger.error(f"Rollback failed: {rollback_error}")
                    logger.warning(f"Config may be in inconsistent state. Manual recovery needed.")
                    logger.warning(f"Backup available at: {backup_created}")

            raise RuntimeError(f"Failed to switch to working set {working_set_id}: {str(e)}. "
                             f"{'Config automatically rolled back.' if backup_created else 'No backup available.'}")

    def preview_working_set_config(self, working_set_id: str) -> Dict[str, Any]:
        """Preview config changes for working set without applying."""
        current_servers = set(self._current_config.get("mcpServers", {}).keys())
        new_config = self.generate_config_for_working_set(working_set_id)
        new_servers = set(new_config.get("mcpServers", {}).keys())

        return {
            "current_servers": sorted(list(current_servers)),
            "new_servers": sorted(list(new_servers)),
            "added_servers": sorted(list(new_servers - current_servers)),
            "removed_servers": sorted(list(current_servers - new_servers)),
            "config_preview": new_config,
        }

    def validate_working_set(self, working_set_id: str) -> Dict[str, Any]:
        """Validate that working set can be applied."""
        working_set = self.get_working_set(working_set_id)
        if not working_set:
            return {"valid": False, "error": f"Working set not found: {working_set_id}"}

        current_servers = self._current_config.get("mcpServers", {})
        missing_servers = []

        for server_name in working_set.get_server_names():
            if server_name not in current_servers:
                missing_servers.append(server_name)

        return {
            "valid": len(missing_servers) == 0,
            "missing_servers": missing_servers,
            "available_servers": list(current_servers.keys()),
            "working_set_servers": working_set.get_server_names(),
        }
