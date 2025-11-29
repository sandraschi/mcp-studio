"""
MCP Client Zoo - Comprehensive MCP client configuration parser.

Supports ALL known MCP clients as of 2025:
- Claude Desktop (Anthropic official)
- Cursor IDE
- Windsurf IDE
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
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from ..core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class MCPServerInfo:
    """Information about an MCP server configuration."""
    id: str
    name: str
    command: str
    args: List[str]
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    source: str = ""  # Which client this came from
    estimated_tools: int = 20


class MCPClientZoo:
    """Parser for MCP configurations from ALL known MCP clients."""
    
    def __init__(self):
        """Initialize the client zoo."""
        self.servers: Dict[str, MCPServerInfo] = {}
        self.sources_found: List[str] = []
    
    # ═══════════════════════════════════════════════════════════════
    # CLAUDE DESKTOP (Anthropic Official)
    # ═══════════════════════════════════════════════════════════════
    
    def parse_claude_desktop(self) -> List[MCPServerInfo]:
        """Parse Claude Desktop MCP configuration."""
        paths = [
            Path(os.environ.get("APPDATA", "")) / "Claude" / "claude_desktop_config.json",
            Path.home() / ".config" / "Claude" / "claude_desktop_config.json",  # Linux/Mac
        ]
        
        return self._parse_standard_format(paths, "claude-desktop")
    
    # ═══════════════════════════════════════════════════════════════
    # CURSOR IDE
    # ═══════════════════════════════════════════════════════════════
    
    def parse_cursor_ide(self) -> List[MCPServerInfo]:
        """Parse Cursor IDE MCP configuration."""
        paths = [
            Path(os.environ.get("APPDATA", "")) / "Cursor" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            Path(os.environ.get("APPDATA", "")) / "Cursor" / "mcp_settings.json",
            Path.home() / ".cursor" / "mcp_settings.json",
            Path.home() / ".config" / "Cursor" / "User" / "mcp_settings.json",  # Linux
        ]
        
        return self._parse_standard_format(paths, "cursor-ide")
    
    # ═══════════════════════════════════════════════════════════════
    # WINDSURF IDE
    # ═══════════════════════════════════════════════════════════════
    
    def parse_windsurf_ide(self) -> List[MCPServerInfo]:
        """Parse Windsurf IDE MCP configuration."""
        paths = [
            Path(os.environ.get("APPDATA", "")) / "Windsurf" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "mcp_settings.json",
            Path(os.environ.get("APPDATA", "")) / "Windsurf" / "mcp_settings.json",
            Path.home() / ".config" / "Windsurf" / "mcp_settings.json",  # Linux
        ]
        
        return self._parse_standard_format(paths, "windsurf-ide")
    
    # ═══════════════════════════════════════════════════════════════
    # CLINE (VSCode Extension - formerly Claude Dev)
    # ═══════════════════════════════════════════════════════════════
    
    def parse_cline(self) -> List[MCPServerInfo]:
        """Parse Cline (formerly Claude Dev) VSCode extension MCP configuration."""
        paths = [
            Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            Path.home() / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",  # Linux
            Path.home() / "Library" / "Application Support" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",  # Mac
        ]
        
        return self._parse_standard_format(paths, "cline-vscode")
    
    # ═══════════════════════════════════════════════════════════════
    # ROO-CLINE (Windsurf's Cline Fork)
    # ═══════════════════════════════════════════════════════════════
    
    def parse_roo_cline(self) -> List[MCPServerInfo]:
        """Parse Roo-Cline (Windsurf's Cline fork) MCP configuration."""
        paths = [
            Path(os.environ.get("APPDATA", "")) / "Windsurf" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "mcp_settings.json",
            Path(os.environ.get("APPDATA", "")) / "Cline" / "mcp_settings.json",
        ]
        
        return self._parse_standard_format(paths, "roo-cline")
    
    # ═══════════════════════════════════════════════════════════════
    # CONTINUE.DEV (VSCode Extension)
    # ═══════════════════════════════════════════════════════════════
    
    def parse_continue_dev(self) -> List[MCPServerInfo]:
        """Parse Continue.dev VSCode extension MCP configuration."""
        paths = [
            Path.home() / ".continue" / "config.json",
            Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "globalStorage" / "continue.continue" / "config.json",
            Path.home() / ".config" / "Code" / "User" / "globalStorage" / "continue.continue" / "config.json",  # Linux
        ]
        
        # Continue.dev might have different structure
        return self._parse_continue_format(paths, "continue-dev")
    
    # ═══════════════════════════════════════════════════════════════
    # LM STUDIO
    # ═══════════════════════════════════════════════════════════════
    
    def parse_lm_studio(self) -> List[MCPServerInfo]:
        """Parse LM Studio MCP configuration."""
        paths = [
            Path(os.environ.get("APPDATA", "")) / "LM Studio" / "mcp_config.json",
            Path.home() / ".lmstudio" / "mcp_config.json",
            Path.home() / "Library" / "Application Support" / "LM Studio" / "mcp_config.json",  # Mac
        ]
        
        return self._parse_standard_format(paths, "lm-studio")
    
    # ═══════════════════════════════════════════════════════════════
    # ZED EDITOR
    # ═══════════════════════════════════════════════════════════════
    
    def parse_zed_editor(self) -> List[MCPServerInfo]:
        """Parse Zed Editor MCP configuration."""
        paths = [
            Path.home() / ".config" / "zed" / "mcp.json",
            Path(os.environ.get("APPDATA", "")) / "Zed" / "mcp.json",
            Path.home() / "Library" / "Application Support" / "Zed" / "mcp.json",  # Mac
        ]
        
        return self._parse_standard_format(paths, "zed-editor")
    
    # ═══════════════════════════════════════════════════════════════
    # VSCODE (Generic)
    # ═══════════════════════════════════════════════════════════════
    
    def parse_vscode_generic(self) -> List[MCPServerInfo]:
        """Parse generic VSCode MCP configuration."""
        paths = [
            Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "mcp_settings.json",
            Path.home() / ".config" / "Code" / "User" / "mcp_settings.json",  # Linux
            Path.home() / "Library" / "Application Support" / "Code" / "User" / "mcp_settings.json",  # Mac
        ]
        
        return self._parse_standard_format(paths, "vscode")
    
    # ═══════════════════════════════════════════════════════════════
    # HELPERS
    # ═══════════════════════════════════════════════════════════════
    
    def _parse_standard_format(self, paths: List[Path], source: str) -> List[MCPServerInfo]:
        """
        Parse standard MCP config format (mcpServers).
        
        Most clients use the same format as Claude Desktop.
        """
        for config_path in paths:
            if not config_path.exists():
                continue
                
            try:
                logger.debug(f"Checking {source} config", path=str(config_path))
                
                with open(config_path, 'r', encoding='utf-8') as f:
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
                        source=source
                    )
                    servers.append(server)
                
                if servers:
                    logger.info(
                        f"Parsed {len(servers)} MCP servers from {source}",
                        path=str(config_path)
                    )
                    return servers
                    
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid JSON in {source} config", path=str(config_path), error=str(e))
            except Exception as e:
                logger.debug(f"Error parsing {source} config", path=str(config_path), error=str(e))
        
        logger.debug(f"No {source} MCP config found")
        return []
    
    def _parse_continue_format(self, paths: List[Path], source: str) -> List[MCPServerInfo]:
        """
        Parse Continue.dev specific format.
        
        Continue.dev might have different structure than standard.
        """
        for config_path in paths:
            if not config_path.exists():
                continue
                
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
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
                            source=source
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
                            source=source
                        )
                        servers.append(server)
                
                if servers:
                    logger.info(f"Parsed {len(servers)} MCP servers from {source}", path=str(config_path))
                    return servers
                    
            except Exception as e:
                logger.debug(f"Error parsing {source} config", path=str(config_path), error=str(e))
        
        logger.debug(f"No {source} MCP config found")
        return []
    
    # ═══════════════════════════════════════════════════════════════
    # SCAN ALL CLIENTS
    # ═══════════════════════════════════════════════════════════════
    
    def scan_all_clients(self) -> Dict[str, List[MCPServerInfo]]:
        """
        Scan ALL known MCP clients and return discovered servers.
        
        Returns:
            Dictionary mapping source name to list of servers
        """
        logger.info("🔍 Scanning MCP Client Zoo...")
        
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
                        f"✅ Found {len(servers)} servers in {client_name}",
                        servers=[s.name for s in servers]
                    )
            except Exception as e:
                logger.warning(f"Error parsing {client_name}", error=str(e))
        
        logger.info(
            f"🎉 Client Zoo scan complete",
            total_servers=total_servers,
            sources=len(self.sources_found),
            found_in=self.sources_found
        )
        
        return results
    
    def get_all_servers(self) -> List[MCPServerInfo]:
        """
        Get deduplicated list of all MCP servers from all clients.
        
        Returns:
            List of unique MCP servers
        """
        results = self.scan_all_clients()
        
        # Deduplicate servers (same command+args = same server)
        unique_servers = {}
        
        for source, servers in results.items():
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
            f"Deduplicated servers",
            total=len(unique_servers),
            original=sum(len(s) for s in results.values())
        )
        
        return list(unique_servers.values())
    
    def get_summary(self) -> Dict[str, Any]:
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
                client: {
                    "count": len(servers),
                    "servers": [s.name for s in servers]
                }
                for client, servers in results.items()
            }
        }
        
        return summary


# ═══════════════════════════════════════════════════════════════
# CONVENIENCE FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def discover_all_mcp_clients() -> Dict[str, Any]:
    """
    Discover MCP servers from ALL known MCP clients.
    
    Returns:
        Summary of discovered servers
    """
    zoo = MCPClientZoo()
    return zoo.get_summary()


def get_all_mcp_servers() -> List[MCPServerInfo]:
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
    print("\n🦁 MCP CLIENT ZOO SCANNER 🦁\n")
    print("=" * 60)
    
    summary = discover_all_mcp_clients()
    
    print(f"\n📊 SUMMARY:")
    print(f"  Total Clients:  {summary['total_clients']}")
    print(f"  Total Servers:  {summary['total_servers']}")
    print(f"  Unique Servers: {summary['unique_servers']}")
    print(f"  Sources Found:  {', '.join(summary['clients_found'])}")
    
    print(f"\n📋 BREAKDOWN:")
    for client, data in summary['breakdown'].items():
        print(f"\n  {client.upper()}: {data['count']} servers")
        for server_name in data['servers']:
            print(f"    • {server_name}")
    
    print("\n" + "=" * 60)
    print("✅ Scan complete!\n")

