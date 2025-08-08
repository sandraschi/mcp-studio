""\nMCP Studio - Main application entry point.

This module initializes and configures the FastAPI application for MCP Studio,
including routing, middleware, and event handlers.
"""

import asyncio
import logging
import signal
import sys
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import fastapi
import fastapi.middleware.cors
import structlog
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from .app.core.config import settings
from .app.core.logging import configure_logging
from .app.core.lifespan import lifespan
from .app.api import router as api_router
from .app.services import discovery_service, server_service

# Configure logging
configure_logging(level=settings.LOG_LEVEL, json_logs=settings.JSON_LOGS)
logger = structlog.get_logger(__name__)

# Create the FastAPI application
app = FastAPI(
    title="MCP Studio",
    description="A comprehensive UI for managing MCP servers",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

# Add CORS middleware
app.add_middleware(
    fastapi.middleware.cors.CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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

# Include API routers
app.include_router(api_router.router, prefix="/api")

# Mount static files
static_dir = Path(__file__).parent / "static"
static_dir.mkdir(exist_ok=True, parents=True)
app.mount("/static", StaticFiles(directory=static_dir), name="static")

# Setup templates
templates_dir = Path(__file__).parent / "templates"
templates_dir.mkdir(exist_ok=True, parents=True)
templates = Jinja2Templates(directory=templates_dir)

# Root endpoint
@app.get("/", include_in_schema=False)
async def root():
    """Root endpoint that redirects to the API docs."""
    return fastapi.responses.RedirectResponse(url="/api/docs")

# Add startup and shutdown event handlers
@app.on_event("startup")
async def startup_event():
    """Handle application startup."""
    logger.info("Starting MCP Studio")
    
    # Register signal handlers for graceful shutdown
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(sig)))
    
    # Initialize services
    try:
        # Initialize server service
        await server_service.init_server_service()
        
        # Start discovery service
        asyncio.create_task(discovery_service.discover_mcp_servers())
        
        logger.info("MCP Studio started successfully")
    except Exception as e:
        logger.critical("Failed to start MCP Studio", error=str(e), exc_info=True)
        raise

async def shutdown(signal: signal.Signals):
    """Handle application shutdown."""
    logger.info(f"Received shutdown signal: {signal.name}")
    
    try:
        # Close server service
        await server_service.close()
        
        # Close discovery service
        if hasattr(discovery_service, 'close'):
            await discovery_service.close()
        
        logger.info("MCP Studio shutdown complete")
    except Exception as e:
        logger.error("Error during shutdown", error=str(e), exc_info=True)
    finally:
        # Exit the application
        sys.exit(0)

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
