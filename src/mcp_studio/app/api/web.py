"""Web interface routes for MCP Studio."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from ...app.core.config import settings
from ...app.core.logging import get_logger
from ...app.services.server_service import server_service
from ...app.services.config_service import config_service
from ...models.server import ServerStatus

# Set up logger
logger = get_logger(__name__)

# Create router
router = APIRouter(
    tags=["web"],
    include_in_schema=False,  # Exclude from OpenAPI schema
)

# Set up templates directory
templates_dir = Path(__file__).parent.parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Add context processor for template variables
@router.middleware("http")
async def add_template_context(request: Request, call_next):
    """Add common template context variables."""
    # Get the base URL
    base_url = str(request.base_url).rstrip("/")
    
    # Add common context variables
    request.state.template_context = {
        "request": request,
        "app_name": "MCP Studio",
        "app_version": "0.1.0",
        "base_url": base_url,
        "debug": settings.DEBUG,
    }
    
    response = await call_next(request)
    return response

# Root route - redirects to dashboard
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request):
    """Root route that redirects to the dashboard."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            **request.state.template_context,
            "title": "Dashboard",
        },
    )

# Dashboard route
@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request):
    """Dashboard page."""
    return templates.TemplateResponse(
        "dashboard.html",
        {
            **request.state.template_context,
            "title": "Dashboard",
        },
    )

# Servers list route
@router.get("/servers", response_class=HTMLResponse, include_in_schema=False)
async def servers_list(
    request: Request,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
):
    """Servers list page with filtering and search."""
    # Get all servers from the server service
    servers = list(server_service.get_servers().values())
    
    # Apply filters if provided
    if status_filter:
        servers = [s for s in servers if s.status.value == status_filter.lower()]
    
    if search:
        search = search.lower()
        servers = [
            s for s in servers 
            if (search in s.name.lower() or 
                search in (s.description or "").lower() or
                search in s.type.value.lower())
        ]
    
    # Sort servers by status (online first) and then by name
    status_order = {ServerStatus.ONLINE: 0, ServerStatus.STARTING: 1, 
                   ServerStatus.STOPPING: 2, ServerStatus.OFFLINE: 3, 
                   ServerStatus.ERROR: 4}
    servers.sort(key=lambda s: (status_order.get(s.status, 99), s.name.lower()))
    
    # Get status counts for the filter
    status_counts = {
        "all": len(server_service.get_servers()),
        "online": len([s for s in server_service.get_servers().values() 
                       if s.status == ServerStatus.ONLINE]),
        "offline": len([s for s in server_service.get_servers().values() 
                        if s.status == ServerStatus.OFFLINE]),
        "error": len([s for s in server_service.get_servers().values() 
                      if s.status == ServerStatus.ERROR]),
    }
    
    return templates.TemplateResponse(
        "servers/list.html",
        {
            **request.state.template_context,
            "title": "Servers",
            "servers": servers,
            "status_filter": status_filter,
            "search_query": search or "",
            "status_counts": status_counts,
            "active_filter": status_filter or "all",
        },
    )

# Server detail route
@router.get("/servers/{server_id}", response_class=HTMLResponse, include_in_schema=False)
async def server_detail(
    request: Request, 
    server_id: str,
    tab: str = "overview"
):
    """Server detail page with tabbed interface."""
    # Get server from the server service
    server = server_service.get_server(server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID '{server_id}' not found",
        )
    
    # Get tools if on the tools tab
    tools = []
    if tab == "tools":
        tools = server_service.get_server_tools(server_id)
    
    # Get logs if on the logs tab (placeholder for now)
    logs = ""
    if tab == "logs":
        logs = f"Logs for {server_id} will appear here when available."
    
    # Convert server to dict for template
    server_dict = server.dict()
    server_dict["tools_count"] = len(tools)
    
    return templates.TemplateResponse(
        "servers/detail.html",
        {
            **request.state.template_context,
            "title": f"Server: {server.name}",
            "server": server_dict,
            "tools": tools,
            "logs": logs,
            "active_tab": tab,
            "tabs": ["overview", "tools", "logs", "settings"],
        },
    )


@router.post("/servers/{server_id}/start", include_in_schema=False)
async def start_server(server_id: str):
    """Start an MCP server."""
    server = server_service.get_server(server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID '{server_id}' not found",
        )
    
    if server.status == ServerStatus.ONLINE:
        return RedirectResponse(
            f"/servers/{server_id}?tab=overview", 
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    success = await server_service.start_server(server_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start server '{server_id}'",
        )
    
    return RedirectResponse(
        f"/servers/{server_id}?tab=overview", 
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/servers/{server_id}/stop", include_in_schema=False)
async def stop_server(server_id: str):
    """Stop an MCP server."""
    server = server_service.get_server(server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID '{server_id}' not found",
        )
    
    if server.status == ServerStatus.OFFLINE:
        return RedirectResponse(
            f"/servers/{server_id}?tab=overview", 
            status_code=status.HTTP_303_SEE_OTHER
        )
    
    success = await server_service.stop_server(server_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop server '{server_id}'",
        )
    
    return RedirectResponse(
        f"/servers/{server_id}?tab=overview", 
        status_code=status.HTTP_303_SEE_OTHER
    )


@router.post("/servers/{server_id}/restart", include_in_schema=False)
async def restart_server(server_id: str):
    """Restart an MCP server."""
    server = server_service.get_server(server_id)
    if not server:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Server with ID '{server_id}' not found",
        )
    
    # Stop the server if it's running
    if server.status == ServerStatus.ONLINE:
        await server_service.stop_server(server_id)
    
    # Start the server
    success = await server_service.start_server(server_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to restart server '{server_id}'",
        )
    
    return RedirectResponse(
        f"/servers/{server_id}?tab=overview", 
        status_code=status.HTTP_303_SEE_OTHER
    )

# Tools list route
@router.get("/tools", response_class=HTMLResponse, include_in_schema=False)
async def tools_list(request: Request):
    """Tools list page."""
    # TODO: Fetch actual tools from the server service
    tools = []
    
    return templates.TemplateResponse(
        "tools/list.html",
        {
            **request.state.template_context,
            "title": "Tools",
            "tools": tools,
        },
    )

# Tool detail route
@router.get("/tools/{tool_name}", response_class=HTMLResponse, include_in_schema=False)
async def tool_detail(request: Request, tool_name: str):
    """Tool detail page."""
    # TODO: Fetch actual tool details from the server service
    tool = None
    
    if not tool:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Tool '{tool_name}' not found",
        )
    
    return templates.TemplateResponse(
        "tools/detail.html",
        {
            **request.state.template_context,
            "title": f"Tool: {tool_name}",
            "tool": tool,
        },
    )

# Execute tool route
@router.get("/tools/execute", response_class=HTMLResponse, include_in_schema=False)
async def execute_tool(request: Request):
    """Execute tool page."""
    # TODO: Fetch available servers and tools for the form
    servers = []
    
    return templates.TemplateResponse(
        "tools/execute.html",
        {
            **request.state.template_context,
            "title": "Execute Tool",
            "servers": servers,
        },
    )

# Templates list route
@router.get("/templates", response_class=HTMLResponse, include_in_schema=False)
async def templates_list(request: Request):
    """Templates list page."""
    # TODO: Fetch actual templates from the database
    templates_list = []
    
    return templates.TemplateResponse(
        "templates/list.html",
        {
            **request.state.template_context,
            "title": "Templates",
            "templates": templates_list,
        },
    )

# Settings route
@router.get("/settings", response_class=HTMLResponse, include_in_schema=False)
async def settings_page(request: Request):
    """Settings page."""
    return templates.TemplateResponse(
        "settings/index.html",
        {
            **request.state.template_context,
            "title": "Settings",
            "settings": {
                "debug": settings.DEBUG,
                "log_level": settings.LOG_LEVEL,
                "host": settings.HOST,
                "port": settings.PORT,
                "workers": settings.WORKERS,
                "mcp_paths": settings.MCP_PATHS,
            },
        },
    )

# 404 handler
@router.get("/{full_path:path}", include_in_schema=False)
async def catch_all(request: Request, full_path: str):
    """Catch-all route for 404 errors."""
    return templates.TemplateResponse(
        "errors/404.html",
        {
            **request.state.template_context,
            "title": "Page Not Found",
            "path": full_path,
        },
        status_code=404,
    )

# Error handler
@router.middleware("http")
async def error_middleware(request: Request, call_next):
    """Global error handler middleware."""
    try:
        return await call_next(request)
    except HTTPException as http_exc:
        # Pass through HTTP exceptions
        if http_exc.status_code == 404:
            return await catch_all(request, request.url.path.lstrip("/"))
        raise
    except Exception as exc:
        # Log the error
        logger.error(
            "Unhandled exception",
            path=request.url.path,
            method=request.method,
            error=str(exc),
            exc_info=True,
        )
        
        # Return a 500 error page
        return templates.TemplateResponse(
            "errors/500.html",
            {
                **request.state.template_context,
                "title": "Internal Server Error",
                "error": str(exc),
            },
            status_code=500,
        )
