"""
MCP Client Metadata Database.

Information about all known MCP clients including descriptions,
homepages, GitHub repos, and capabilities.
"""

from dataclasses import dataclass
from typing import Dict, List, Optional

from ..core.logging_utils import get_logger

logger = get_logger(__name__)


@dataclass
class MCPClientMetadata:
    """Metadata for an MCP client."""
    id: str
    name: str
    short_description: str
    full_description: str
    homepage: Optional[str] = None
    github: Optional[str] = None
    documentation: Optional[str] = None
    platform: str = "Cross-platform"  # Windows, Mac, Linux, Cross-platform
    client_type: str = "Desktop"  # Desktop, IDE, Extension, Library
    status: str = "Active"  # Active, Deprecated, Beta
    features: List[str] = None
    installed: bool = False  # Whether this client is detected as installed
    server_count: int = 0  # Number of MCP servers configured

    def __post_init__(self):
        if self.features is None:
            self.features = []


# ═══════════════════════════════════════════════════════════════
# CLIENT METADATA DATABASE
# ═══════════════════════════════════════════════════════════════

MCP_CLIENT_DATABASE: Dict[str, MCPClientMetadata] = {
    "claude-desktop": MCPClientMetadata(
        id="claude-desktop",
        name="Claude Desktop",
        short_description="Official Anthropic Claude desktop application",
        full_description="Claude Desktop is the official desktop application from Anthropic for interacting with Claude AI. It provides native MCP support for extending Claude with custom tools and integrations.",
        homepage="https://claude.ai/download",
        github=None,  # Proprietary
        documentation="https://docs.anthropic.com/claude/docs/desktop",
        platform="Cross-platform",
        client_type="Desktop",
        status="Active",
        features=[
            "Official Anthropic client",
            "Native MCP support",
            "Secure stdio transport",
            "Production-ready",
            "Auto-updates"
        ]
    ),
    
    "cursor-ide": MCPClientMetadata(
        id="cursor-ide",
        name="Cursor IDE",
        short_description="AI-first code editor with MCP support",
        full_description="Cursor is an AI-first code editor built on VSCode, featuring integrated AI assistance and native MCP support for extending capabilities with custom tools.",
        homepage="https://cursor.sh/",
        github=None,  # Proprietary
        documentation="https://cursor.sh/docs",
        platform="Cross-platform",
        client_type="IDE",
        status="Active",
        features=[
            "AI-first editor",
            "VSCode-based",
            "Integrated AI chat",
            "MCP tool support",
            "Code generation"
        ]
    ),
    
    "windsurf-ide": MCPClientMetadata(
        id="windsurf-ide",
        name="Windsurf IDE",
        short_description="Codeium's AI-powered IDE with MCP integration",
        full_description="Windsurf is Codeium's AI-powered IDE featuring advanced code completion, chat, and native MCP support for extending with custom tools.",
        homepage="https://codeium.com/windsurf",
        github=None,  # Proprietary
        documentation="https://docs.codeium.com/windsurf",
        platform="Cross-platform",
        client_type="IDE",
        status="Active",
        features=[
            "Codeium AI integration",
            "Advanced code completion",
            "MCP support via Roo-Cline",
            "Multi-file editing",
            "Cascade chat"
        ]
    ),
    
    "cline-vscode": MCPClientMetadata(
        id="cline-vscode",
        name="Cline",
        short_description="VSCode extension for Claude AI (formerly Claude Dev)",
        full_description="Cline (formerly Claude Dev) is a VSCode extension that brings Claude AI capabilities directly into your editor, with native MCP support for custom tool integration.",
        homepage="https://marketplace.visualstudio.com/items?itemName=saoudrizwan.claude-dev",
        github="https://github.com/clinebot/cline",
        documentation="https://github.com/clinebot/cline#readme",
        platform="Cross-platform",
        client_type="Extension",
        status="Active",
        features=[
            "VSCode integration",
            "Claude AI in editor",
            "MCP tool support",
            "File operations",
            "Terminal access"
        ]
    ),
    
    "roo-cline": MCPClientMetadata(
        id="roo-cline",
        name="Roo-Cline",
        short_description="Windsurf's fork of Cline with enhanced features",
        full_description="Roo-Cline is Windsurf IDE's enhanced fork of Cline, providing advanced AI coding assistance with native MCP support for tool integration.",
        homepage="https://codeium.com/windsurf",
        github=None,  # Part of Windsurf
        documentation="https://docs.codeium.com/windsurf/mcp",
        platform="Cross-platform",
        client_type="Extension",
        status="Active",
        features=[
            "Windsurf integration",
            "Enhanced Cline features",
            "MCP tool support",
            "Cascade workflows",
            "Multi-agent coordination"
        ]
    ),
    
    "continue-dev": MCPClientMetadata(
        id="continue-dev",
        name="Continue.dev",
        short_description="Open-source AI coding assistant for VSCode",
        full_description="Continue is an open-source AI coding assistant that integrates with VSCode and JetBrains IDEs, supporting multiple AI models and MCP for tool extensibility.",
        homepage="https://continue.dev/",
        github="https://github.com/continuedev/continue",
        documentation="https://docs.continue.dev/",
        platform="Cross-platform",
        client_type="Extension",
        status="Active",
        features=[
            "Open-source",
            "Multi-model support",
            "VSCode + JetBrains",
            "MCP integration",
            "Customizable prompts"
        ]
    ),
    
    "lm-studio": MCPClientMetadata(
        id="lm-studio",
        name="LM Studio",
        short_description="Desktop app for running local LLMs with MCP support",
        full_description="LM Studio is a desktop application for discovering, downloading, and running local Large Language Models, with MCP support for extending capabilities.",
        homepage="https://lmstudio.ai/",
        github=None,  # Proprietary
        documentation="https://lmstudio.ai/docs",
        platform="Cross-platform",
        client_type="Desktop",
        status="Active",
        features=[
            "Run local models",
            "No API keys needed",
            "Privacy-focused",
            "MCP tool support",
            "Model marketplace"
        ]
    ),
    
    "antigravity-ide": MCPClientMetadata(
        id="antigravity-ide",
        name="Antigravity IDE",
        short_description="GitKraken's AI-powered code editor with MCP support",
        full_description="Antigravity is GitKraken's AI-powered code editor featuring advanced code completion, chat, and native MCP support for extending with custom tools.",
        homepage="https://www.gitkraken.com/antigravity",
        github=None,  # Proprietary
        documentation="https://www.gitkraken.com/antigravity/docs",
        platform="Cross-platform",
        client_type="IDE",
        status="Active",
        features=[
            "GitKraken integration",
            "AI-powered coding",
            "MCP support",
            "Advanced code completion",
            "Built-in Git tools"
        ]
    ),
    
    "zed-editor": MCPClientMetadata(
        id="zed-editor",
        name="Zed Editor",
        short_description="High-performance collaborative code editor",
        full_description="Zed is a high-performance, multiplayer code editor built in Rust, featuring AI assistance and MCP support for custom tool integration.",
        homepage="https://zed.dev/",
        github="https://github.com/zed-industries/zed",
        documentation="https://zed.dev/docs",
        platform="Cross-platform",
        client_type="IDE",
        status="Active",
        features=[
            "Built in Rust",
            "Collaborative editing",
            "AI assistance",
            "MCP support",
            "Lightning fast"
        ]
    ),
    
    "vscode-generic": MCPClientMetadata(
        id="vscode-generic",
        name="VSCode",
        short_description="Microsoft's code editor with MCP extensions",
        full_description="Visual Studio Code is Microsoft's popular code editor, extensible with various MCP-compatible extensions for AI assistance and tool integration.",
        homepage="https://code.visualstudio.com/",
        github="https://github.com/microsoft/vscode",
        documentation="https://code.visualstudio.com/docs",
        platform="Cross-platform",
        client_type="IDE",
        status="Active",
        features=[
            "Most popular editor",
            "Massive extension ecosystem",
            "MCP extensions available",
            "Open-source core",
            "Cross-platform"
        ]
    ),
}


# ═══════════════════════════════════════════════════════════════
# HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_client_metadata(client_id: str) -> Optional[MCPClientMetadata]:
    """
    Get metadata for a specific MCP client.
    
    Args:
        client_id: Client identifier (e.g., "claude-desktop")
        
    Returns:
        Client metadata or None if not found
    """
    return MCP_CLIENT_DATABASE.get(client_id)


def get_all_clients() -> List[MCPClientMetadata]:
    """
    Get metadata for all known MCP clients with installation status.

    Returns:
        List of all client metadata with installed/server_count populated
    """
    from .mcp_client_zoo import MCPClientZoo

    # Get static metadata
    clients = list(MCP_CLIENT_DATABASE.values())

    # Scan for actual installations
    try:
        zoo = MCPClientZoo()
        installed_clients = zoo.scan_all_clients()

        # Update clients with installation status
        for client in clients:
            if client.id in installed_clients:
                client.installed = True
                client.server_count = len(installed_clients[client.id])

    except Exception as e:
        # If scanning fails, just return clients without installation status
        logger.warning(f"Failed to scan clients for installation status: {e}")

    return clients


def get_clients_by_type(client_type: str) -> List[MCPClientMetadata]:
    """
    Get all clients of a specific type.
    
    Args:
        client_type: Type of client (Desktop, IDE, Extension, Library)
        
    Returns:
        List of matching clients
    """
    return [
        client for client in MCP_CLIENT_DATABASE.values()
        if client.client_type == client_type
    ]


def get_active_clients() -> List[MCPClientMetadata]:
    """
    Get all active (non-deprecated) clients.
    
    Returns:
        List of active clients
    """
    return [
        client for client in MCP_CLIENT_DATABASE.values()
        if client.status == "Active"
    ]


def format_client_info(client_id: str, format: str = "text") -> str:
    """
    Format client information for display.
    
    Args:
        client_id: Client identifier
        format: Output format ("text" or "markdown")
        
    Returns:
        Formatted client information
    """
    client = get_client_metadata(client_id)
    if not client:
        return f"Unknown client: {client_id}"
    
    if format == "markdown":
        lines = [
            f"# {client.name}",
            f"",
            f"{client.full_description}",
            f"",
            f"**Type:** {client.client_type}",
            f"**Platform:** {client.platform}",
            f"**Status:** {client.status}",
            f"",
        ]
        
        if client.homepage:
            lines.append(f"🌐 **Homepage:** {client.homepage}")
        if client.github:
            lines.append(f"💻 **GitHub:** {client.github}")
        if client.documentation:
            lines.append(f"📚 **Docs:** {client.documentation}")
        
        if client.features:
            lines.append(f"")
            lines.append(f"**Features:**")
            for feature in client.features:
                lines.append(f"- {feature}")
        
        return "\n".join(lines)
    
    else:  # text format
        lines = [
            f"{client.name}",
            f"{'=' * len(client.name)}",
            f"",
            f"{client.short_description}",
            f"",
            f"Type: {client.client_type}",
            f"Platform: {client.platform}",
            f"Status: {client.status}",
            f"",
        ]
        
        if client.homepage:
            lines.append(f"Homepage: {client.homepage}")
        if client.github:
            lines.append(f"GitHub: {client.github}")
        if client.documentation:
            lines.append(f"Documentation: {client.documentation}")
        
        return "\n".join(lines)


# ═══════════════════════════════════════════════════════════════
# CLI TEST
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    print("\n🦁 MCP CLIENT METADATA DATABASE 🦁\n")
    print("=" * 70)
    
    print(f"\n📊 TOTAL CLIENTS: {len(MCP_CLIENT_DATABASE)}\n")
    
    # Group by type
    for client_type in ["Desktop", "IDE", "Extension"]:
        clients = get_clients_by_type(client_type)
        if clients:
            print(f"\n{client_type.upper()}S ({len(clients)}):")
            print("-" * 70)
            for client in clients:
                print(f"\n  {client.name}")
                print(f"  {client.short_description}")
                if client.homepage:
                    print(f"  🌐 {client.homepage}")
                if client.github:
                    print(f"  💻 {client.github}")
                print(f"  Features: {', '.join(client.features[:3])}...")
    
    print("\n" + "=" * 70)
    print("✅ Database loaded!\n")

