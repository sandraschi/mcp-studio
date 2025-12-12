"""
Multi-Client Working Set Manager.

Manages working sets for all MCP clients (Claude Desktop, Cursor, Windsurf, etc.)
"""

import logging
from pathlib import Path
from typing import Dict, Optional, Any, List
from .manager import WorkingSetManager

# Import will be done lazily to avoid circular dependencies
try:
    from mcp_studio.app.services.mcp_client_zoo import MCPClientZoo
except ImportError:
    try:
        from ...mcp_studio.app.services.mcp_client_zoo import MCPClientZoo
    except ImportError:
        # Fallback for different import paths
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from mcp_studio.app.services.mcp_client_zoo import MCPClientZoo

logger = logging.getLogger(__name__)


class ClientWorkingSetManager:
    """Manages working sets for multiple MCP clients."""
    
    def __init__(self, templates_dir: str = None):
        """
        Initialize multi-client working set manager.
        
        Args:
            templates_dir: Directory containing working set templates
        """
        self.templates_dir = Path(templates_dir or "templates")
        self.templates_dir.mkdir(exist_ok=True)
        
        # Cache of managers per client
        self._managers: Dict[str, WorkingSetManager] = {}
        
        # Client zoo for getting config paths
        self._client_zoo = MCPClientZoo()
    
    def get_manager(self, client_id: str) -> Optional[WorkingSetManager]:
        """
        Get WorkingSetManager for a specific client.
        
        Args:
            client_id: Client identifier (e.g., "claude-desktop", "cursor-ide")
            
        Returns:
            WorkingSetManager instance or None if client config not found
        """
        # Return cached manager if available
        if client_id in self._managers:
            return self._managers[client_id]
        
        # Get config path for client
        config_path = self._client_zoo.get_client_config_path(client_id)
        if not config_path:
            logger.debug(f"Config path not found for client: {client_id}")
            return None
        
        # Create backup directory
        backup_dir = config_path.parent / "backup"
        backup_dir.mkdir(exist_ok=True)
        
        # Create manager for this client
        manager = WorkingSetManager(
            config_path=str(config_path),
            backup_dir=str(backup_dir),
            templates_dir=str(self.templates_dir)
        )
        
        # Cache it
        self._managers[client_id] = manager
        
        logger.info(f"Created WorkingSetManager for {client_id}", config_path=str(config_path))
        return manager
    
    def list_clients_with_configs(self) -> List[str]:
        """
        List all clients that have config files.
        
        Returns:
            List of client IDs that have configs
        """
        client_ids = [
            "claude-desktop",
            "cursor-ide",
            "windsurf-ide",
            "antigravity-ide",
            "zed-editor",
            "cline-vscode",
            "roo-cline",
            "continue-dev",
            "lm-studio",
            "vscode-generic",
        ]
        
        clients_with_configs = []
        for client_id in client_ids:
            config_path = self._client_zoo.get_client_config_path(client_id)
            if config_path and config_path.exists():
                clients_with_configs.append(client_id)
        
        return clients_with_configs
    
    def get_client_config_info(self, client_id: str) -> Optional[Dict[str, Any]]:
        """
        Get configuration info for a client.
        
        Args:
            client_id: Client identifier
            
        Returns:
            Dict with config_path, backup_dir, exists, or None if not found
        """
        config_path = self._client_zoo.get_client_config_path(client_id)
        if not config_path:
            return None
        
        backup_dir = config_path.parent / "backup"
        
        return {
            "client_id": client_id,
            "config_path": str(config_path),
            "backup_dir": str(backup_dir),
            "config_exists": config_path.exists(),
            "backup_dir_exists": backup_dir.exists(),
        }
