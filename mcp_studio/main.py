"""MCP Studio - Main application entry point.

This module initializes and configures the FastAPI application for MCP Studio,
including routing, middleware, and event handlers.
"""

import asyncio
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import fastapi
import fastapi.middleware.cors
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .app.core.config import settings
from .app.core.logging_utils import get_logger, configure_uvicorn_logging
from .app.api import router as api_router
from .app.api.endpoints import mcp_servers as mcp_servers_router
from .app.api.endpoints import repos as repos_router
from .app.services.mcp_discovery_service import discovery_service, start_discovery, stop_discovery

# Configure logging
configure_uvicorn_logging()
logger = get_logger(__name__)

# Import working sets API
try:
    from api.working_sets import router as working_sets_router
except ImportError:
    # Fallback if working_sets is not available
    working_sets_router = None
    logger.warning("Working sets router not available")


# Lifespan event handler
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown."""
    # Startup
    logger.info("Starting MCP Studio...")
    try:
        # Temporarily disable MCP discovery service to test
        # await start_discovery()
        # logger.info("MCP Discovery Service started")
        logger.info("MCP Studio started successfully")
    except Exception as e:
        logger.error(f"Failed to start MCP Studio: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down MCP Studio...")
    try:
        # Stop discovery service
        # await stop_discovery()
        logger.info("MCP Studio shutdown complete")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e), exc_info=True)


# Import web router after logger is configured
try:
    from .app.api.web import router as web_router

    logger.info("Web router loaded successfully")
except Exception as e:
    # Web router might not be available in all configurations
    web_router = None
    logger.warning(f"Web router not available: {e}", exc_info=True)

# Create the FastAPI application
app = FastAPI(
    title="MCP Studio",
    description="A management tool for MCP servers (beta)",
    version="0.2.1-beta",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
    root_path="",  # Ensure root path is handled correctly
)

# Add CORS middleware
app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log all incoming requests and responses."""
    # Skip logging for health checks and static files
    if request.url.path in ["/api/health", "/api/health/", "/static/", "/favicon.ico"]:
        return await call_next(request)

    # Log request
    logger.info(
        "Request started",
        method=request.method,
        url=str(request.url),
        client=request.client.host if request.client else None,
    )

    # Process request
    start_time = asyncio.get_event_loop().time()

    try:
        response = await call_next(request)
        process_time = asyncio.get_event_loop().time() - start_time

        # Log response
        logger.info(
            "Request completed",
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=f"{process_time:.4f}s",
        )

        return response
    except Exception as e:
        process_time = asyncio.get_event_loop().time() - start_time
        logger.error(
            "Request failed",
            method=request.method,
            url=str(request.url),
            error=str(e),
            process_time=f"{process_time:.4f}s",
            exc_info=True,
        )
        raise


# Add exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Handle request validation errors."""
    logger.warning(
        "Request validation failed",
        url=str(request.url),
        errors=exc.errors(),
        body=exc.body,
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": "Validation error",
            "errors": exc.errors(),
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """Handle all other exceptions."""
    logger.error(
        "Unhandled exception",
        url=str(request.url),
        error=str(exc),
        exc_info=True,
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "error": str(exc),
        },
    )


# Include API routers FIRST so they're matched before the web router catch-all
app.include_router(api_router, prefix="/api")

# Include clients router directly in main app
try:
    logger.info("Attempting to include clients router...")
    from .app.api.clients import router as clients_router
    logger.info(f"Clients router has {len(clients_router.routes)} routes before inclusion")
    app.include_router(clients_router, prefix="/api/v1/clients", tags=["clients"])
    logger.info(f"Clients router included with {len(clients_router.routes)} routes at prefix /api/v1/clients")
except Exception as e:
    logger.error(f"Failed to include clients router: {e}", exc_info=True)

# MCP servers and repos are now included in the v1 API router
# app.include_router(mcp_servers_router.router, prefix="/api")
# app.include_router(repos_router.router, prefix="/api")

# Mount static files BEFORE web router so they take precedence
static_dir = Path(__file__).parent.parent / "backend" / "static"
static_dir.mkdir(exist_ok=True, parents=True)
logger.info(f"Mounting static files from: {static_dir}")
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
logger.info("Static files mounted successfully")

# Include web router AFTER static files so catch-all doesn't intercept static files
if web_router:
    app.include_router(web_router)  # Include web UI routes (handles /, /dashboard, etc.)
    logger.info(f"Web router included with {len(web_router.routes)} routes")
else:
    logger.warning("Web router is None - not including web routes!")
if working_sets_router:
    app.include_router(working_sets_router, tags=["working-sets"])  # Add working sets router

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True, parents=True)
templates = Jinja2Templates(directory=templates_dir)

# Root endpoint removed - web router handles this now

# This allows running the application directly with: python -m mcp_studio
if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "mcp_studio.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
        workers=settings.WORKERS,
    )
