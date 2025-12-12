"""API routes for MCP Studio."""

from fastapi import APIRouter

# Import all routers
from . import servers, tools, discovery, health, clients

# Create main router (prefix will be added in main.py)
router = APIRouter(prefix="/v1", tags=["api"])

# Include all routers with proper prefixes
router.include_router(servers.router, prefix="/servers", tags=["servers"])
router.include_router(tools.router, prefix="/tools", tags=["tools"])
router.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
router.include_router(clients.router, prefix="/clients", tags=["clients"])

# Health endpoints at /api/v1/health/*
router.include_router(health.router, prefix="/health", tags=["health"])

# Repo scanner routes
try:
    print("Attempting to import repo routes...")
    import mcp_studio.api.repo_routes as repo_routes
    print(f"Imported successfully, router has {len(repo_routes.router.routes)} routes")
    router.include_router(repo_routes.router)
    print("Repo scanner routes included in API router")
except Exception as e:
    print(f"Failed to include repo routes: {e}")
    import traceback
    traceback.print_exc()

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