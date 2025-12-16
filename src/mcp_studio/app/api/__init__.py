"""API routes for MCP Studio."""

from fastapi import APIRouter

# Import all routers
from . import servers, tools, discovery, health, clients
from ..api.endpoints import mcp_servers as mcp_servers_router
from ..api.endpoints import repos as repos_router

# Create main router (prefix will be added in main.py)
router = APIRouter(prefix="/v1", tags=["api"])

# Include all routers with proper prefixes
router.include_router(servers.router, prefix="/servers", tags=["servers"])
router.include_router(tools.router, prefix="/tools", tags=["tools"])
router.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
router.include_router(clients.router, prefix="/clients", tags=["clients"])
router.include_router(mcp_servers_router.router, tags=["mcp-servers"])
router.include_router(repos_router.router, prefix="/repos", tags=["repos"])

# Health endpoints at /api/v1/health/*
router.include_router(health.router, prefix="/health", tags=["health"])

# Try to include additional routers (handle import errors gracefully)
try:
    import mcp_studio.api.settings_routes as settings_routes
    router.include_router(settings_routes.router, prefix="/settings", tags=["settings"])
except Exception as e:
    # Log but don't fail if settings routes can't be loaded
    import logging
    logging.getLogger(__name__).warning(f"Failed to include settings routes: {e}")

try:
    from . import auth, tools, server, files, data, development
    # Include additional routers if they exist
    if hasattr(auth, 'router'):
        router.include_router(auth.router, prefix="/auth", tags=["auth"])
    if hasattr(files, 'router'):
        router.include_router(files.router, prefix="/files", tags=["files"])
    if hasattr(data, 'router'):
        router.include_router(data.router, prefix="/data", tags=["data"])
    if hasattr(development, 'router'):
        router.include_router(development.router, prefix="/development", tags=["development"])
except Exception as e:
    # Log but don't fail if additional routers can't be loaded
    import logging
    logging.getLogger(__name__).warning(f"Failed to include additional routers: {e}")

# Settings routes
try:
    print("Attempting to import settings routes...")
    import mcp_studio.api.settings_routes as settings_routes

    print(f"Settings router has {len(settings_routes.router.routes)} routes")
    router.include_router(settings_routes.router, prefix="/settings", tags=["settings"])
    print("Settings routes included in API router")
except Exception as e:
    print(f"Failed to include settings routes: {e}")
    import traceback

    traceback.print_exc()
