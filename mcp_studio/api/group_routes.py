"""
Tool Group API Routes for MCP Studio.

Manage server groups for smart context loading when LLM is added.
"""
from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from ..tools.tool_groups import GroupStatus, tool_group_manager

router = APIRouter(prefix="/api/groups", tags=["groups"])


class CreateGroupRequest(BaseModel):
    """Request to create a custom group."""
    id: str
    name: str
    servers: List[str]
    description: str = ""
    icon: str = "📦"
    keywords: List[str] = []


class ActivateGroupsRequest(BaseModel):
    """Request to activate specific groups."""
    group_ids: List[str]
    exclusive: bool = False  # If true, deactivate all others


@router.get("/")
async def list_groups():
    """List all tool groups (predefined + custom)."""
    return tool_group_manager.to_dict()


@router.get("/active")
async def get_active_groups():
    """Get currently active groups and servers."""
    return {
        "active_groups": [
            {"id": g.id, "name": g.name, "icon": g.icon, "servers": g.servers}
            for g in tool_group_manager.active_groups
        ],
        "active_servers": list(tool_group_manager.active_servers),
        "context_budget": tool_group_manager.get_context_budget_usage(),
    }


@router.post("/activate/{group_id}")
async def activate_group(group_id: str):
    """Activate a single group."""
    if tool_group_manager.activate(group_id):
        return {"success": True, "status": "active", "group": group_id}
    raise HTTPException(status_code=404, detail=f"Group not found: {group_id}")


@router.post("/deactivate/{group_id}")
async def deactivate_group(group_id: str):
    """Deactivate a single group."""
    if tool_group_manager.deactivate(group_id):
        return {"success": True, "status": "inactive", "group": group_id}
    raise HTTPException(status_code=404, detail=f"Group not found: {group_id}")


@router.post("/toggle/{group_id}")
async def toggle_group(group_id: str):
    """Toggle a group's active status."""
    new_status = tool_group_manager.toggle(group_id)
    if new_status:
        return {"success": True, "status": new_status.value, "group": group_id}
    raise HTTPException(status_code=404, detail=f"Group not found: {group_id}")


@router.post("/activate-many")
async def activate_groups(request: ActivateGroupsRequest):
    """Activate multiple groups at once."""
    if request.exclusive:
        tool_group_manager.activate_only(request.group_ids)
    else:
        for gid in request.group_ids:
            tool_group_manager.activate(gid)
    
    return {
        "success": True,
        "active_groups": [g.id for g in tool_group_manager.active_groups],
        "active_servers": list(tool_group_manager.active_servers),
    }


@router.post("/deactivate-all")
async def deactivate_all():
    """Deactivate all groups."""
    for group in tool_group_manager.all_groups:
        group.status = GroupStatus.INACTIVE
    return {"success": True, "message": "All groups deactivated"}


@router.post("/custom")
async def create_custom_group(request: CreateGroupRequest):
    """Create a custom tool group."""
    group = tool_group_manager.create_custom_group(
        group_id=request.id,
        name=request.name,
        servers=request.servers,
        description=request.description,
        icon=request.icon,
        keywords=request.keywords,
    )
    return {
        "success": True,
        "group": {
            "id": group.id,
            "name": group.name,
            "servers": group.servers,
        }
    }


@router.delete("/custom/{group_id}")
async def delete_custom_group(group_id: str):
    """Delete a custom group."""
    if tool_group_manager.delete_custom_group(group_id):
        return {"success": True, "deleted": group_id}
    raise HTTPException(status_code=404, detail=f"Custom group not found: {group_id}")


@router.get("/suggest")
async def suggest_groups(message: str = Query(..., description="User message/intent")):
    """
    Suggest groups based on user message keywords.
    
    Simple keyword matching for now.
    When LLM is added, can use semantic matching.
    """
    suggested = tool_group_manager.suggest_groups_for_intent(message)
    return {
        "message": message,
        "suggestions": [
            {"id": g.id, "name": g.name, "icon": g.icon, "servers": g.servers}
            for g in suggested[:5]  # Top 5 suggestions
        ],
    }


@router.get("/budget")
async def get_context_budget():
    """Get context budget usage for active groups."""
    return tool_group_manager.get_context_budget_usage()

