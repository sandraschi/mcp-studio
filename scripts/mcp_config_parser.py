"""
MCP Configuration Parser - Extract and analyze MCP server configurations
from Claude Desktop and Windsurf IDE configurations.

This fills a massive gap - we have 260+ MCP tools across 13+ servers 
and NO visibility into what we actually have available!
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime

@dataclass
class MCPServerInfo:
    """Information about an MCP server configuration."""
    id: str
    name: str
    command: str
    args: List[str]
    cwd: Optional[str] = None
    env: Optional[Dict[str, str]] = None
    source: str = ""  # claude, windsurf, etc.
    estimated_tools: int = 20  # Default estimate
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

@dataclass
class MCPConfigSummary:
    """Summary of all discovered MCP configurations."""
    total_servers: int
    total_estimated_tools: int
    sources: List[str]
    servers: List[MCPServerInfo]
    parsed_at: str
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

class MCPConfigParser:
    """Parser for MCP configurations from various sources."""
    
    def __init__(self):
        self.servers: List[MCPServerInfo] = []
        
    def parse_claude_desktop_config(self) -> List[MCPServerInfo]:
        """Parse Claude Desktop MCP configuration."""
        config_path = Path(os.environ["APPDATA"]) / "Claude" / "claude_desktop_config.json"
        
        if not config_path.exists():
            print(f"❌ Claude config not found at: {config_path}")
            return []
            
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                
            servers = []
            mcp_servers = config.get("mcpServers", {})
            
            for server_id, server_config in mcp_servers.items():
                server = MCPServerInfo(
                    id=server_id,
                    name=server_id.replace("-", " ").replace("_", " ").title(),
                    command=server_config.get("command", ""),
                    args=server_config.get("args", []),
                    cwd=server_config.get("cwd"),
                    env=server_config.get("env"),
                    source="claude-desktop"
                )
                servers.append(server)
                
            print(f"✅ Parsed {len(servers)} MCP servers from Claude Desktop")
            return servers
            
        except Exception as e:
            print(f"❌ Error parsing Claude config: {e}")
            return []
    
    def parse_windsurf_config(self) -> List[MCPServerInfo]:
        """Parse Windsurf IDE MCP configuration."""
        # Check common Windsurf config locations
        possible_paths = [
            Path(os.environ["APPDATA"]) / "Windsurf" / "User" / "globalStorage" / "rooveterinaryinc.roo-cline" / "settings" / "mcp_settings.json",
            Path(os.environ["APPDATA"]) / "Cline" / "mcp_settings.json",
            Path(os.environ["APPDATA"]) / "Windsurf" / "mcp_config.json",
        ]
        
        for config_path in possible_paths:
            if config_path.exists():
                print(f"🔍 Found Windsurf config at: {config_path}")
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # Parse based on actual config structure
                    servers = self._parse_windsurf_structure(config, str(config_path))
                    print(f"✅ Parsed {len(servers)} MCP servers from Windsurf")
                    return servers
                    
                except Exception as e:
                    print(f"❌ Error parsing Windsurf config: {e}")
                    continue
        
        print("ℹ️ No Windsurf MCP config found")
        return []
    
    def _parse_windsurf_structure(self, config: Dict[str, Any], source_path: str) -> List[MCPServerInfo]:
        """Parse Windsurf-specific config structure."""
        servers = []
        
        # Handle different possible Windsurf config structures
        if "mcpServers" in config:
            # Similar to Claude Desktop format
            for server_id, server_config in config["mcpServers"].items():
                server = MCPServerInfo(
                    id=server_id,
                    name=server_id.replace("-", " ").replace("_", " ").title(),
                    command=server_config.get("command", ""),
                    args=server_config.get("args", []),
                    cwd=server_config.get("cwd"),
                    env=server_config.get("env"),
                    source=f"windsurf ({Path(source_path).name})"
                )
                servers.append(server)
        
        # Add other potential structures as we discover them
        return servers
    
    def parse_cursor_config(self) -> List[MCPServerInfo]:
        """Parse Cursor IDE MCP configuration."""
        # Cursor might store MCP config in different locations
        cursor_paths = [
            Path(os.environ.get("APPDATA", "")) / "Cursor" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            Path(os.environ.get("APPDATA", "")) / "Cursor" / "User" / "settings.json",
            Path(os.environ.get("APPDATA", "")) / "Cursor" / "mcp_settings.json",
            Path.home() / ".cursor" / "mcp_settings.json",
        ]
        
        for config_path in cursor_paths:
            if config_path.exists():
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        config = json.load(f)
                    
                    # Look for MCP-related settings
                    if "mcpServers" in config:
                        print(f"🔍 Found Cursor config with MCP settings: {config_path}")
                        servers = self._parse_cursor_structure(config, str(config_path))
                        if servers:
                            print(f"✅ Parsed {len(servers)} MCP servers from Cursor IDE")
                            return servers
                        
                except Exception as e:
                    print(f"⚠️  Error parsing Cursor config at {config_path}: {e}")
                    continue
                    
        print("ℹ️  No Cursor MCP config found")
        return []
    
    def _parse_cursor_structure(self, config: Dict, config_path: str) -> List[MCPServerInfo]:
        """Parse Cursor-specific config structure."""
        servers = []
        
        # Cursor uses same structure as Claude Desktop
        mcp_servers = config.get("mcpServers", {})
        
        for server_id, server_config in mcp_servers.items():
            server = MCPServerInfo(
                id=server_id,
                name=server_id.replace("-", " ").replace("_", " ").title(),
                command=server_config.get("command", ""),
                args=server_config.get("args", []),
                cwd=server_config.get("cwd"),
                env=server_config.get("env"),
                source="cursor-ide"
            )
            servers.append(server)
        
        return servers
    
    def parse_cline_config(self) -> List[MCPServerInfo]:
        """Parse Cline (formerly Claude Dev) VSCode extension config."""
        paths = [
            Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
            Path.home() / ".config" / "Code" / "User" / "globalStorage" / "saoudrizwan.claude-dev" / "settings" / "cline_mcp_settings.json",
        ]
        return self._parse_standard_format(paths, "cline-vscode")
    
    def parse_continue_dev_config(self) -> List[MCPServerInfo]:
        """Parse Continue.dev VSCode extension config."""
        paths = [
            Path.home() / ".continue" / "config.json",
            Path(os.environ.get("APPDATA", "")) / "Code" / "User" / "globalStorage" / "continue.continue" / "config.json",
        ]
        return self._parse_standard_format(paths, "continue-dev")
    
    def parse_lm_studio_config(self) -> List[MCPServerInfo]:
        """Parse LM Studio MCP configuration."""
        paths = [
            Path(os.environ.get("APPDATA", "")) / "LM Studio" / "mcp_config.json",
            Path.home() / ".lmstudio" / "mcp_config.json",
        ]
        return self._parse_standard_format(paths, "lm-studio")
    
    def parse_zed_config(self) -> List[MCPServerInfo]:
        """Parse Zed Editor MCP configuration."""
        paths = [
            Path.home() / ".config" / "zed" / "mcp.json",
            Path(os.environ.get("APPDATA", "")) / "Zed" / "mcp.json",
        ]
        return self._parse_standard_format(paths, "zed-editor")
    
    def _parse_standard_format(self, paths: List[Path], source: str) -> List[MCPServerInfo]:
        """Parse standard MCP config format (mcpServers)."""
        for config_path in paths:
            if not config_path.exists():
                continue
            
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                if "mcpServers" not in config:
                    continue
                
                servers = []
                for server_id, server_config in config["mcpServers"].items():
                    server = MCPServerInfo(
                        id=server_id,
                        name=server_id.replace("-", " ").replace("_", " ").title(),
                        command=server_config.get("command", ""),
                        args=server_config.get("args", []),
                        cwd=server_config.get("cwd"),
                        env=server_config.get("env"),
                        source=source
                    )
                    servers.append(server)
                
                if servers:
                    print(f"✅ Parsed {len(servers)} MCP servers from {source}")
                    return servers
                    
            except Exception as e:
                continue
        
        return []
    
    def parse_all_configs(self) -> MCPConfigSummary:
        """Parse all available MCP configurations from ALL known MCP clients."""
        print("🔍 Scanning MCP Client Zoo...")
        print("   (Claude Desktop, Cursor, Windsurf, Cline, Roo-Cline, Continue.dev, LM Studio, Zed, VSCode)")
        
        all_servers = []
        sources = []
        
        # Parse Claude Desktop
        claude_servers = self.parse_claude_desktop_config()
        all_servers.extend(claude_servers)
        if claude_servers:
            sources.append("claude-desktop")
        
        # Parse Cursor IDE
        cursor_servers = self.parse_cursor_config()
        all_servers.extend(cursor_servers)
        if cursor_servers:
            sources.append("cursor-ide")
        
        # Parse Windsurf IDE
        windsurf_servers = self.parse_windsurf_config()
        all_servers.extend(windsurf_servers)
        if windsurf_servers:
            sources.append("windsurf-ide")
        
        # Parse Cline (VSCode)
        cline_servers = self.parse_cline_config()
        all_servers.extend(cline_servers)
        if cline_servers:
            sources.append("cline-vscode")
        
        # Parse Continue.dev
        continue_servers = self.parse_continue_dev_config()
        all_servers.extend(continue_servers)
        if continue_servers:
            sources.append("continue-dev")
        
        # Parse LM Studio
        lmstudio_servers = self.parse_lm_studio_config()
        all_servers.extend(lmstudio_servers)
        if lmstudio_servers:
            sources.append("lm-studio")
        
        # Parse Zed Editor
        zed_servers = self.parse_zed_config()
        all_servers.extend(zed_servers)
        if zed_servers:
            sources.append("zed-editor")
        
        total_estimated_tools = sum(server.estimated_tools for server in all_servers)
        
        summary = MCPConfigSummary(
            total_servers=len(all_servers),
            total_estimated_tools=total_estimated_tools,
            sources=sources,
            servers=all_servers,
            parsed_at=datetime.now().isoformat()
        )
        
        print(f"\n🎯 DISCOVERY COMPLETE:")
        print(f"   📊 Total Servers: {summary.total_servers}")
        print(f"   🛠️ Estimated Tools: {summary.total_estimated_tools}")
        print(f"   💻 Sources: {', '.join(summary.sources)}")
        
        return summary
    
    def generate_markdown_report(self, summary: MCPConfigSummary) -> str:
        """Generate a comprehensive markdown report of MCP configuration."""
        
        report = f"""# MCP Configuration Report

**Generated:** {summary.parsed_at}  
**Total Servers:** {summary.total_servers}  
**Estimated Tools:** {summary.total_estimated_tools}  
**Sources:** {', '.join(summary.sources)}

## Server Overview

"""
        
        for server in summary.servers:
            report += f"""### {server.name} (`{server.id}`)

**Source:** {server.source}  
**Command:** `{server.command}`  
**Args:** `{' '.join(server.args)}`  
"""
            if server.cwd:
                report += f"**Working Directory:** `{server.cwd}`\n"
            
            if server.env:
                report += f"**Environment Variables:**\n"
                for key, value in server.env.items():
                    # Mask sensitive values
                    display_value = value if not any(sensitive in key.lower() 
                                                   for sensitive in ['token', 'key', 'password', 'secret']) else "***"
                    report += f"  - `{key}`: `{display_value}`\n"
                    
            report += f"**Estimated Tools:** ~{server.estimated_tools}\n\n"
            
        report += f"""
## Summary Statistics

- **Most Common Command Types:**
  - Python: {len([s for s in summary.servers if 'python' in s.command.lower()])} servers
  - NPX/Node: {len([s for s in summary.servers if 'npx' in s.command.lower()])} servers  
  - Docker: {len([s for s in summary.servers if 'docker' in s.command.lower()])} servers
  - UV/UVX: {len([s for s in summary.servers if 'uv' in s.command.lower()])} servers

- **Servers with Custom Working Directories:** {len([s for s in summary.servers if s.cwd])}
- **Servers with Environment Variables:** {len([s for s in summary.servers if s.env])}

## Next Steps

This report shows the **massive gap** in MCP tooling visibility:
1. ✅ We can parse configs automatically
2. 🔄 **NEXT:** Connect to live servers and extract actual tool schemas
3. 🔄 **NEXT:** Build interactive web UI for tool exploration
4. 🔄 **NEXT:** Add tool testing capabilities
5. 🔄 **NEXT:** Generate comprehensive tool documentation

**The Goal:** Transform this invisible 260+ tool arsenal into a discoverable, searchable, testable interface! 🚀
"""
        
        return report

# Example usage
if __name__ == "__main__":
    parser = MCPConfigParser()
    summary = parser.parse_all_configs()
    
    # Generate report
    report = parser.generate_markdown_report(summary)
    print("\n" + "="*50)
    print("MARKDOWN REPORT:")
    print("="*50)
    print(report)
    
    # Save as JSON for further processing
    with open("mcp_config_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary.to_dict(), f, indent=2, ensure_ascii=False)
    
    print(f"\n💾 Summary saved to: mcp_config_summary.json")
