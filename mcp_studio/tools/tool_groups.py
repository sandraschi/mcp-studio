"""
Tool Groups - Smart Activate/Deactivate for MCP Servers.

Like Cursor's MCP activation, but with predefined groups for common workflows.
When LLM is added, only active group tools are loaded into context.
"""
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set

import structlog

logger = structlog.get_logger(__name__)


class GroupStatus(str, Enum):
    ACTIVE = "active"
    INACTIVE = "inactive"
    AUTO = "auto"  # Let LLM decide based on intent


@dataclass
class ToolGroup:
    """A group of related MCP servers/tools."""
    id: str
    name: str
    description: str
    servers: List[str]  # MCP server names
    icon: str = "📦"
    status: GroupStatus = GroupStatus.INACTIVE
    max_tools: int = 50  # Context budget for this group
    keywords: List[str] = field(default_factory=list)  # For auto-routing


# ============================================================================
# PREDEFINED GROUPS - Common workflows
# ============================================================================

PREDEFINED_GROUPS: Dict[str, ToolGroup] = {
    # Audio Production
    "audio-production": ToolGroup(
        id="audio-production",
        name="Audio Production",
        description="DJ, DAW, music production tools",
        servers=["virtualdj-mcp", "reaper-mcp", "ableton-mcp"],
        icon="🎵",
        keywords=["music", "audio", "mix", "dj", "daw", "track", "bpm", "beat", "song"],
    ),
    
    # Video Production
    "video-production": ToolGroup(
        id="video-production",
        name="Video Production",
        description="Video editing, color grading, rendering",
        servers=["davinci-resolve-mcp", "premiere-mcp", "ffmpeg-mcp"],
        icon="🎬",
        keywords=["video", "edit", "timeline", "color", "render", "export", "clip", "footage"],
    ),
    
    # Smart Home
    "smart-home": ToolGroup(
        id="smart-home",
        name="Smart Home",
        description="Lights, cameras, sensors, automation",
        servers=["tapo-mcp", "hue-mcp", "ring-mcp", "nest-mcp"],
        icon="🏠",
        keywords=["light", "camera", "motion", "temperature", "plug", "switch", "scene", "home"],
    ),
    
    # Media & Entertainment
    "media": ToolGroup(
        id="media",
        name="Media & Entertainment",
        description="Plex, media libraries, streaming",
        servers=["plex-mcp", "jellyfin-mcp", "spotify-mcp"],
        icon="📺",
        keywords=["movie", "show", "playlist", "library", "stream", "watch", "listen"],
    ),
    
    # Knowledge & Notes
    "knowledge": ToolGroup(
        id="knowledge",
        name="Knowledge Management",
        description="Notes, memory, documentation",
        servers=["advanced-memory-mcp", "obsidian-mcp", "notion-mcp"],
        icon="📚",
        keywords=["note", "memory", "remember", "search", "document", "knowledge", "write"],
    ),
    
    # Development
    "development": ToolGroup(
        id="development",
        name="Development Tools",
        description="Git, CI/CD, code analysis",
        servers=["github-mcp", "gitlab-mcp", "docker-mcp"],
        icon="💻",
        keywords=["code", "git", "deploy", "build", "test", "container", "repository"],
    ),
    
    # Transit & Location
    "transit": ToolGroup(
        id="transit",
        name="Transit & Location",
        description="Public transit, maps, weather",
        servers=["vienna-transit", "weather-mcp", "maps-mcp"],
        icon="🚇",
        keywords=["train", "bus", "transit", "route", "weather", "departure", "station"],
    ),
    
    # Communication
    "communication": ToolGroup(
        id="communication",
        name="Communication",
        description="Email, calendar, messaging",
        servers=["gmail-mcp", "calendar-mcp", "slack-mcp", "teams-mcp"],
        icon="💬",
        keywords=["email", "message", "meeting", "calendar", "schedule", "send", "reply"],
    ),
    
    # Web & Browser
    "web": ToolGroup(
        id="web",
        name="Web & Browser",
        description="Browser control, web scraping",
        servers=["cursor-browser-extension", "puppeteer-mcp", "playwright-mcp"],
        icon="🌐",
        keywords=["browse", "website", "click", "screenshot", "scrape", "navigate", "page"],
    ),
}


class ToolGroupManager:
    """
    Manages tool group activation for context-aware LLM integration.
    
    When LLM is added:
    - Only active group tools are loaded into context
    - Auto groups route based on user intent keywords
    - Context budget prevents tool overload
    """
    
    def __init__(self):
        self.groups: Dict[str, ToolGroup] = dict(PREDEFINED_GROUPS)
        self.custom_groups: Dict[str, ToolGroup] = {}
        self._active_servers: Set[str] = set()
    
    @property
    def active_servers(self) -> Set[str]:
        """Get all servers from active groups."""
        servers = set()
        for group in self.groups.values():
            if group.status == GroupStatus.ACTIVE:
                servers.update(group.servers)
        for group in self.custom_groups.values():
            if group.status == GroupStatus.ACTIVE:
                servers.update(group.servers)
        return servers
    
    @property
    def active_groups(self) -> List[ToolGroup]:
        """Get all active groups."""
        return [g for g in self.all_groups if g.status == GroupStatus.ACTIVE]
    
    @property
    def all_groups(self) -> List[ToolGroup]:
        """Get all groups (predefined + custom)."""
        return list(self.groups.values()) + list(self.custom_groups.values())
    
    def activate(self, group_id: str) -> bool:
        """Activate a group."""
        group = self.groups.get(group_id) or self.custom_groups.get(group_id)
        if group:
            group.status = GroupStatus.ACTIVE
            logger.info("Group activated", group=group_id, servers=group.servers)
            return True
        return False
    
    def deactivate(self, group_id: str) -> bool:
        """Deactivate a group."""
        group = self.groups.get(group_id) or self.custom_groups.get(group_id)
        if group:
            group.status = GroupStatus.INACTIVE
            logger.info("Group deactivated", group=group_id)
            return True
        return False
    
    def toggle(self, group_id: str) -> Optional[GroupStatus]:
        """Toggle a group's active status."""
        group = self.groups.get(group_id) or self.custom_groups.get(group_id)
        if group:
            if group.status == GroupStatus.ACTIVE:
                group.status = GroupStatus.INACTIVE
            else:
                group.status = GroupStatus.ACTIVE
            return group.status
        return None
    
    def activate_only(self, group_ids: List[str]) -> None:
        """Activate only specified groups, deactivate all others."""
        for group in self.all_groups:
            group.status = GroupStatus.ACTIVE if group.id in group_ids else GroupStatus.INACTIVE
        logger.info("Groups activated exclusively", groups=group_ids)
    
    def create_custom_group(
        self,
        group_id: str,
        name: str,
        servers: List[str],
        description: str = "",
        icon: str = "📦",
        keywords: List[str] = None,
    ) -> ToolGroup:
        """Create a custom tool group."""
        group = ToolGroup(
            id=group_id,
            name=name,
            description=description,
            servers=servers,
            icon=icon,
            keywords=keywords or [],
        )
        self.custom_groups[group_id] = group
        logger.info("Custom group created", group=group_id, servers=servers)
        return group
    
    def delete_custom_group(self, group_id: str) -> bool:
        """Delete a custom group (predefined groups cannot be deleted)."""
        if group_id in self.custom_groups:
            del self.custom_groups[group_id]
            logger.info("Custom group deleted", group=group_id)
            return True
        return False
    
    def suggest_groups_for_intent(self, user_message: str) -> List[ToolGroup]:
        """
        Suggest groups based on keywords in user message.
        
        This is a simple keyword-based approach.
        When LLM is added, this can be enhanced with semantic matching.
        """
        message_lower = user_message.lower()
        scored_groups = []
        
        for group in self.all_groups:
            score = 0
            for keyword in group.keywords:
                if keyword in message_lower:
                    score += 1
            if score > 0:
                scored_groups.append((score, group))
        
        # Sort by score descending
        scored_groups.sort(key=lambda x: x[0], reverse=True)
        return [g for _, g in scored_groups]
    
    def get_context_budget_usage(self) -> Dict[str, Any]:
        """
        Get current context budget usage for active groups.
        
        Returns estimated tool count and budget status.
        """
        total_tools = 0
        total_budget = 0
        group_usage = []
        
        for group in self.active_groups:
            # Estimate tools per server (would be actual count from connected servers)
            estimated_tools = len(group.servers) * 10  # Rough estimate
            total_tools += estimated_tools
            total_budget += group.max_tools
            group_usage.append({
                "group": group.name,
                "servers": len(group.servers),
                "estimated_tools": estimated_tools,
                "max_tools": group.max_tools,
            })
        
        return {
            "active_groups": len(self.active_groups),
            "total_estimated_tools": total_tools,
            "total_budget": total_budget,
            "groups": group_usage,
            "warning": total_tools > 100,  # Warn if too many tools
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Serialize state for API/storage."""
        return {
            "predefined_groups": [
                {
                    "id": g.id,
                    "name": g.name,
                    "description": g.description,
                    "icon": g.icon,
                    "servers": g.servers,
                    "status": g.status.value,
                    "keywords": g.keywords,
                }
                for g in self.groups.values()
            ],
            "custom_groups": [
                {
                    "id": g.id,
                    "name": g.name,
                    "description": g.description,
                    "icon": g.icon,
                    "servers": g.servers,
                    "status": g.status.value,
                    "keywords": g.keywords,
                }
                for g in self.custom_groups.values()
            ],
            "active_servers": list(self.active_servers),
        }


# Global instance
tool_group_manager = ToolGroupManager()

