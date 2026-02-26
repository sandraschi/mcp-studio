"""API routes for MCP Studio."""

from fastapi import APIRouter

# Import basic routers
from . import servers, tools, discovery, health, ecosystem
from ..api.endpoints import mcp_servers as mcp_servers_router
from ..api.endpoints import repos as repos_router

# Create main router (prefix will be added in main.py)
router = APIRouter(prefix="/v1", tags=["api"])

# Include all routers with proper prefixes
router.include_router(servers.router, prefix="/servers", tags=["servers"])
router.include_router(tools.router, prefix="/tools", tags=["tools"])
router.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
router.include_router(ecosystem.router, prefix="/ecosystem", tags=["ecosystem"])
router.include_router(mcp_servers_router.router, tags=["mcp-servers"])
router.include_router(repos_router.router, prefix="/repos", tags=["repos"])

# Add logs endpoints directly to avoid circular import issues
from collections import deque
import logging
from typing import Dict, Any

# In-memory log storage (last 100 entries)
log_buffer = deque(maxlen=100)


class LogCaptureHandler(logging.Handler):
    """Custom handler to capture logs in memory."""

    def emit(self, record):
        """Capture log record and store in buffer."""
        try:
            # Format the log record
            log_entry = self.format(record)
            log_buffer.append(log_entry)
        except Exception:
            # Don't let logging errors crash the app
            pass


# Create and configure the log capture handler
log_capture_handler = LogCaptureHandler()
log_capture_handler.setFormatter(
    logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
)

# Add the handler to the root logger to capture all logs
root_logger = logging.getLogger()
root_logger.addHandler(log_capture_handler)

print(f"Adding logs endpoints to router (currently has {len(router.routes)} routes)")


@router.get("/logs", tags=["logs"])
async def get_logs(limit: int = 50) -> Dict[str, Any]:
    """Get recent application logs.

    Args:
        limit: Maximum number of log entries to return (default: 50, max: 100)

    Returns:
        Dict containing logs and metadata
    """
    # Ensure limit is reasonable
    limit = min(max(limit, 1), 100)

    # Get logs from buffer (most recent first)
    recent_logs = list(log_buffer)[-limit:]

    return {
        "status": "success",
        "logs": recent_logs,
        "count": len(recent_logs),
        "total_available": len(log_buffer),
        "limit": limit,
    }


@router.delete("/logs", tags=["logs"])
async def clear_logs() -> Dict[str, Any]:
    """Clear all stored logs.

    Returns:
        Success confirmation
    """
    log_buffer.clear()
    logger = logging.getLogger(__name__)
    logger.info("Logs cleared via API")
    return {"status": "success", "message": "All logs cleared", "cleared_count": 0}


# Logs endpoints added to router

# Clients router now included directly in main.py

# Health endpoints at /api/v1/health/*
router.include_router(health.router, prefix="/health", tags=["health"])


# Test endpoint
@router.get("/test")
async def test_endpoint():
    """Test endpoint to verify API routing works."""
    return {"message": "API test successful", "timestamp": "2025-12-16"}


# Try to include additional routers (handle import errors gracefully)
try:
    from ...api.settings_routes import router as settings_routes

    router.include_router(settings_routes.router, prefix="/settings", tags=["settings"])
except Exception as e:
    # Log but don't fail if settings routes can't be loaded
    import logging

    logging.getLogger(__name__).warning(f"Failed to include settings routes: {e}")

try:
    from . import auth, tools, server, files, data, development

    # Include additional routers if they exist
    if hasattr(auth, "router"):
        router.include_router(auth.router, prefix="/auth", tags=["auth"])
    if hasattr(files, "router"):
        router.include_router(files.router, prefix="/files", tags=["files"])
    if hasattr(data, "router"):
        router.include_router(data.router, prefix="/data", tags=["data"])
    if hasattr(development, "router"):
        router.include_router(development.router, prefix="/development", tags=["development"])
except Exception as e:
    # Log but don't fail if additional routers can't be loaded
    import logging

    logging.getLogger(__name__).warning(f"Failed to include additional routers: {e}")

# Settings routes
try:
    print("Attempting to import settings routes...")
    from ...api.settings_routes import router as settings_routes

    print(f"Settings router has {len(settings_routes.routes)} routes")
    router.include_router(settings_routes, prefix="/settings", tags=["settings"])
    print("Settings routes included in API router")
except Exception as e:
    print(f"Failed to include settings routes: {e}")
    import traceback

    traceback.print_exc()
