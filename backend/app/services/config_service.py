"""Service for handling MCP server configuration."""
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, TypedDict

import structlog

logger = structlog.get_logger(__name__)


class MCPServerConfig(TypedDict):
    """TypedDict for MCP server configuration."""
    command: str
    args: List[str]
    cwd: Optional[str]
    env: Optional[Dict[str, str]]


class ConfigService:
    """Service for managing MCP server configurations."""
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize the config service.
        
        Args:
            config_path: Path to the Claude Desktop config file. If not provided,
                        will use the default location.
        """
        self.config_path = Path(config_path or 
                              Path.home() / "AppData" / "Roaming" / "Claude" / "claude_desktop_config.json")
        self._config: Dict[str, MCPServerConfig] = {}
        self._load_config()
    
    def _load_config(self) -> None:
        """Load the MCP server configuration from the config file."""
        try:
            if not self.config_path.exists():
                logger.warning("Claude Desktop config file not found", path=str(self.config_path))
                return
                
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                
            self._config = config_data.get('mcpServers', {})
            logger.info("Loaded MCP server configuration", server_count=len(self._config))
            
        except Exception as e:
            logger.error("Failed to load MCP server configuration", error=str(e))
            self._config = {}
    
    def get_server_config(self, server_id: str) -> Optional[MCPServerConfig]:
        """Get the configuration for a specific MCP server.
        
        Args:
            server_id: The ID of the MCP server.
            
        Returns:
            The server configuration if found, None otherwise.
        """
        return self._config.get(server_id)
    
    def get_all_servers(self) -> Dict[str, MCPServerConfig]:
        """Get all configured MCP servers.
        
        Returns:
            A dictionary mapping server IDs to their configurations.
        """
        return self._config.copy()
    
    def refresh(self) -> None:
        """Refresh the configuration from disk."""
        self._load_config()


# Singleton instance
config_service = ConfigService()
