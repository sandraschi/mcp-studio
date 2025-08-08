""Lifespan management for MCP Studio application."""

import asyncio
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Dict, Any

import structlog
from fastapi import FastAPI

from .config import settings
from .logging import configure_logging

logger = structlog.get_logger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[Dict[str, Any], None]:
    """Manage application lifespan events.
    
    Args:
        app: FastAPI application instance
        
    Yields:
        Application state dictionary
    """
    # Configure logging
    configure_logging(level=settings.LOG_LEVEL, json_logs=settings.JSON_LOGS)
    
    # Application startup
    logger.info(
        "Starting MCP Studio",
        version=settings.APP_VERSION,
        debug=settings.DEBUG,
        environment="development" if settings.DEBUG else "production",
    )
    
    # Initialize application state
    app.state.started_at = asyncio.get_event_loop().time()
    app.state.mcp_servers: Dict[str, Dict[str, Any]] = {}
    
    try:
        # Start background tasks
        from ..services import discovery_service
        
        # Start MCP server discovery
        discovery_task = asyncio.create_task(discovery_service.discover_mcp_servers())
        
        # Add to application state for cleanup
        app.state.background_tasks = {
            "discovery": discovery_task,
        }
        
        # Yield control to the application
        yield {
            "started_at": app.state.started_at,
            "mcp_servers": app.state.mcp_servers,
        }
        
    except asyncio.CancelledError:
        logger.info("Application shutdown requested")
    except Exception as e:
        logger.error("Application error in lifespan", error=str(e), exc_info=True)
        raise
    finally:
        # Application shutdown
        logger.info("Shutting down MCP Studio")
        
        # Cancel background tasks
        if hasattr(app.state, "background_tasks"):
            for name, task in app.state.background_tasks.items():
                if not task.done():
                    logger.debug("Cancelling background task", task=name)
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        logger.error(
                            "Error in background task during shutdown",
                            task=name,
                            error=str(e),
                            exc_info=True,
                        )
        
        # Clean up resources
        if hasattr(app.state, "mcp_servers"):
            for server_id, server in app.state.mcp_servers.items():
                if "client" in server and hasattr(server["client"], "close"):
                    try:
                        await server["client"].close()
                        logger.debug("Closed MCP server connection", server_id=server_id)
                    except Exception as e:
                        logger.error(
                            "Error closing MCP server connection",
                            server_id=server_id,
                            error=str(e),
                            exc_info=True,
                        )
        
        logger.info("MCP Studio shutdown complete")
