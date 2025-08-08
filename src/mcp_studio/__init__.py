"""
MCP Studio - A comprehensive UI for managing MCP servers.

This package provides a web-based interface for discovering, managing, and interacting
with MCP (Model Control Protocol) servers.
"""

__version__ = "0.1.0"
__all__ = ["create_app", "run"]

import asyncio
import logging
import sys
from pathlib import Path
from typing import Optional, Dict, Any

import structlog
from fastmcp import FastMCP

from .app.core.config import settings
from .app.core.logging import configure_logging
from .app.core.lifespan import lifespan

# Configure logging early
configure_logging()
logger = structlog.get_logger(__name__)

def create_app() -> FastMCP:
    """Create and configure the FastMCP application."""
    logger.info("Creating MCP Studio application", version=__version__)
    
    # Initialize FastMCP with structured logging
    mcp = FastMCP(
        name="mcp-studio",
        version=__version__,
        description="MCP Studio - UI for managing MCP servers",
        lifespan=lifespan,
    )
    
    # Register tools
    _register_tools(mcp)
    
    # Register API routes
    from .app.api import router as api_router
    mcp.include_router(api_router, prefix="/api")
    
    # Serve static files
    _setup_static_files(mcp)
    
    return mcp

def _register_tools(mcp: FastMCP) -> None:
    """Register all MCP tools."""
    # Import and register tool modules
    from .app.tools import server_tools, discovery_tools, management_tools
    
    # Register tool modules
    server_tools.register(mcp)
    discovery_tools.register(mcp)
    management_tools.register(mcp)
    
    logger.info("Registered MCP tools")

def _setup_static_files(mcp: FastMCP) -> None:
    """Configure static file serving."""
    from fastapi.staticfiles import StaticFiles
    from fastapi.templating import Jinja2Templates
    
    # Mount static files
    static_path = Path(__file__).parent / "static"
    static_path.mkdir(exist_ok=True)
    mcp.mount("/static", StaticFiles(directory=static_path), name="static")
    
    # Set up templates
    templates_path = Path(__file__).parent / "templates"
    templates_path.mkdir(exist_ok=True)
    mcp.state.templates = Jinja2Templates(directory=templates_path)

def run() -> None:
    """Run the MCP Studio server."""
    try:
        app = create_app()
        
        # Start the server
        logger.info("Starting MCP Studio")
        app.run()
        
    except Exception as e:
        logger.critical("Fatal error in MCP Studio", error=str(e), exc_info=True)
        sys.exit(1)
    except KeyboardInterrupt:
        logger.info("MCP Studio stopped by user")
        sys.exit(0)

if __name__ == "__main__":
    run()
