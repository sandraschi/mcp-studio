"""Web interface routes for MCP Studio."""

import logging
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from ...app.core.config import settings
from ...app.core.logging_utils import get_logger
from ...app.services.server_service import server_service
from ...app.services.config_service import config_service
from ...app.core.enums import ServerStatus

# Set up logger
logger = get_logger(__name__)

# Create router
router = APIRouter(
    tags=["web"],
    include_in_schema=False,  # Exclude from OpenAPI schema
)

# Set up templates directory
templates_dir = Path(__file__).resolve().parent.parent.parent / "templates"
if not templates_dir.exists():
    # Fallback to standard package location
    import mcp_studio

    templates_dir = Path(mcp_studio.__file__).parent / "templates"

templates = Jinja2Templates(directory=str(templates_dir))
logger.info(f"Templates directory: {templates_dir}")


# Template context helper function
def get_template_context(request: Request) -> dict:
    """Get common template context variables."""
    base_url = str(request.base_url).rstrip("/")
    return {
        "request": request,
        "app_name": "MCP Studio",
        "app_version": "0.2.1-beta",
        "base_url": base_url,
        "debug": settings.DEBUG,
    }


def get_dashboard_html(request: Request):
    """Helper to serve the refactored dashboard.html content."""
    # Strict priority: Check explicit locations for dashboard
    possible_paths = [
        # 1. Relative to web.py (in dev/source source)
        Path(__file__).resolve().parent.parent.parent / "templates" / "dashboard.html",
        # 2. Package install location
        templates_dir / "dashboard.html",
        # 3. Docker specific path (absolute fallback)
        Path("/app/src/mcp_studio/templates/dashboard.html"),
    ]

    for path in possible_paths:
        if path.exists():
            logger.info(f"Serving dashboard from: {path}")
            with open(path, "r", encoding="utf-8") as f:
                html_content = f.read()
            # Replace VERSION variable
            return HTMLResponse(content=html_content.replace("{VERSION}", "0.2.1-beta"))

    logger.warning(
        "dashboard_new.html not found in any expected location, falling back to template"
    )
    return templates.TemplateResponse(
        "dashboard_new.html",
        {
            **get_template_context(request),
            "title": "Dashboard",
        },
    )


# Root route
@router.get("/", response_class=HTMLResponse, include_in_schema=False)
async def root(request: Request):
    return get_dashboard_html(request)


# Catch-all for dashboard tabs (since it uses client-side routing, or if user refreshes on a tab)
# Adding these explicit routes ensures we serve the dashboard HTML instead of 404
@router.get("/dashboard", response_class=HTMLResponse, include_in_schema=False)
async def dashboard(request: Request):
    return get_dashboard_html(request)


@router.get("/repos", response_class=HTMLResponse, include_in_schema=False)
async def repos_page(request: Request):
    return get_dashboard_html(request)


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
            s
            for s in servers
            if (
                search in s.name.lower()
                or search in (s.description or "").lower()
                or search in s.type.value.lower()
            )
        ]

    # Sort servers by status (online first) and then by name
    status_order = {
        ServerStatus.ONLINE: 0,
        ServerStatus.STARTING: 1,
        ServerStatus.STOPPING: 2,
        ServerStatus.OFFLINE: 3,
        ServerStatus.ERROR: 4,
    }
    servers.sort(key=lambda s: (status_order.get(s.status, 99), s.name.lower()))

    # Get status counts for the filter
    status_counts = {
        "all": len(server_service.get_servers()),
        "online": len(
            [s for s in server_service.get_servers().values() if s.status == ServerStatus.ONLINE]
        ),
        "offline": len(
            [s for s in server_service.get_servers().values() if s.status == ServerStatus.OFFLINE]
        ),
        "error": len(
            [s for s in server_service.get_servers().values() if s.status == ServerStatus.ERROR]
        ),
    }

    return templates.TemplateResponse(
        "servers/list.html",
        {
            **get_template_context(request),
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
async def server_detail(request: Request, server_id: str, tab: str = "overview"):
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
            **get_template_context(request),
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
            f"/servers/{server_id}?tab=overview", status_code=status.HTTP_303_SEE_OTHER
        )

    success = await server_service.start_server(server_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start server '{server_id}'",
        )

    return RedirectResponse(
        f"/servers/{server_id}?tab=overview", status_code=status.HTTP_303_SEE_OTHER
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
            f"/servers/{server_id}?tab=overview", status_code=status.HTTP_303_SEE_OTHER
        )

    success = await server_service.stop_server(server_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to stop server '{server_id}'",
        )

    return RedirectResponse(
        f"/servers/{server_id}?tab=overview", status_code=status.HTTP_303_SEE_OTHER
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
        f"/servers/{server_id}?tab=overview", status_code=status.HTTP_303_SEE_OTHER
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
            **get_template_context(request),
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
            **get_template_context(request),
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
            **get_template_context(request),
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
            **get_template_context(request),
            "title": "Templates",
            "templates": templates_list,
        },
    )


# Clients list route
@router.get("/clients", response_class=HTMLResponse, include_in_schema=False)
async def clients_list(request: Request):
    """Clients list page."""
    return templates.TemplateResponse(
        "clients/list.html",
        {
            **get_template_context(request),
            "title": "MCP Clients",
        },
    )


# Client detail route
@router.get("/clients/{client_id}", response_class=HTMLResponse, include_in_schema=False)
async def client_detail(request: Request, client_id: str, tab: str = "overview"):
    """Client detail page with tabbed interface."""
    return templates.TemplateResponse(
        "clients/detail.html",
        {
            **get_template_context(request),
            "title": f"Client: {client_id}",
            "client_id": client_id,
            "active_tab": tab,
        },
    )


# Settings route
@router.get("/settings", response_class=HTMLResponse, include_in_schema=False)
async def settings_page(request: Request):
    """Settings page."""
    return templates.TemplateResponse(
        "settings/index.html",
        {
            **get_template_context(request),
            "title": "Settings",
            "settings": {
                "debug": settings.DEBUG,
                "log_level": settings.LOG_LEVEL,
                "host": settings.HOST,
                "port": settings.PORT,
                "workers": settings.WORKERS,
                "repos_path": settings.REPOS_PATH,
                "repo_scan_depth": settings.REPO_SCAN_DEPTH,
                "repo_scan_exclude": settings.REPO_SCAN_EXCLUDE,
                "ui_theme": settings.UI_THEME,
                "ui_refresh_interval": settings.UI_REFRESH_INTERVAL,
            },
        },
    )


# Note: Removed catch-all route to allow static files to be served properly
# FastAPI will handle 404s automatically when no routes match


# Note: Error middleware should be added to the FastAPI app in main.py, not the router
# Router-level error handling is done via exception handlers in the app
