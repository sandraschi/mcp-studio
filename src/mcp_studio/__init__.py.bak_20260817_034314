"""
MCP Studio - A comprehensive UI for managing MCP servers with FastMCP 2.11 integration.

This package provides a web-based interface for discovering, managing, and interacting
with MCP (Model Context Protocol) servers using the latest FastMCP framework.
"""

__version__ = "0.1.0"
__all__ = ["create_app", "create_mcp_server", "run", "setup_tools"]

import asyncio
import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import structlog
from fastmcp import FastMCP

from .app.core.config import settings
from .app.core.logging import configure_logging
from .tools.registry import (
    initialize_registry,
    setup_fastmcp_with_all_tools,
    setup_fastmcp_minimal,
    get_registry_stats
)

# Configure logging early
configure_logging()
logger = structlog.get_logger(__name__)


def create_app() -> FastMCP:
    """Create and configure the FastAPI application with FastMCP integration.

    This creates a traditional FastAPI application for the web interface
    while also setting up FastMCP capabilities for MCP server management.

    Returns:
        FastAPI application instance
    """
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.staticfiles import StaticFiles

    logger.info("Creating MCP Studio FastAPI application", version=__version__)

    # Create FastAPI app
    app = FastAPI(
        title="MCP Studio",
        description="A comprehensive UI for managing MCP servers",
        version=__version__,
        docs_url="/api/docs",
        redoc_url="/api/redoc",
        openapi_url="/api/openapi.json",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.BACKEND_CORS_ORIGINS or ["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routers
    from .app.api import router as api_router
    app.include_router(api_router, prefix="/api")

    # Mount static files
    static_dir = Path(__file__).parent / "static"
    static_dir.mkdir(exist_ok=True, parents=True)
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

    # Add startup event handler
    @app.on_event("startup")
    async def startup_event():
        """Handle application startup."""
        logger.info("Starting MCP Studio web application")

        # Initialize tool registry
        try:
            await initialize_registry()
            stats = get_registry_stats()
            logger.info("Tool registry initialized", **stats)
        except Exception as e:
            logger.error("Failed to initialize tool registry", error=str(e))

    @app.on_event("shutdown")
    async def shutdown_event():
        """Handle application shutdown."""
        logger.info("Shutting down MCP Studio web application")

    return app


def create_mcp_server(
    name: str = "MCP Studio Server",
    include_experimental: bool = False,
    include_deprecated: bool = False,
    minimal_mode: bool = False
) -> FastMCP:
    """Create and configure a FastMCP server with MCP Studio tools.

    This creates a pure MCP server that can be used as a standalone
    MCP server or integrated into other applications.

    Args:
        name: Name of the MCP server
        include_experimental: Whether to include experimental tools
        include_deprecated: Whether to include deprecated tools
        minimal_mode: Whether to use minimal tool set for safety

    Returns:
        Configured FastMCP server instance
    """
    logger.info(
        "Creating MCP Studio server",
        name=name,
        minimal_mode=minimal_mode,
        include_experimental=include_experimental,
        include_deprecated=include_deprecated
    )

    # Create FastMCP server
    mcp = FastMCP(
        name=name,
        version=__version__,
        description="MCP Studio - Tools for managing MCP servers and infrastructure"
    )

    # Store configuration for later setup
    mcp._mcp_studio_config = {
        'include_experimental': include_experimental,
        'include_deprecated': include_deprecated,
        'minimal_mode': minimal_mode
    }

    return mcp


async def setup_tools(
    mcp: FastMCP,
    include_experimental: bool = None,
    include_deprecated: bool = None,
    minimal_mode: bool = None
) -> int:
    """Set up MCP tools for a FastMCP server instance.

    Args:
        mcp: FastMCP server instance to configure
        include_experimental: Override experimental tools setting
        include_deprecated: Override deprecated tools setting
        minimal_mode: Override minimal mode setting

    Returns:
        Number of tools registered
    """
    # Get configuration from server or use provided values
    config = getattr(mcp, '_mcp_studio_config', {})

    if include_experimental is None:
        include_experimental = config.get('include_experimental', False)
    if include_deprecated is None:
        include_deprecated = config.get('include_deprecated', False)
    if minimal_mode is None:
        minimal_mode = config.get('minimal_mode', False)

    logger.info(
        "Setting up MCP Studio tools",
        server_name=getattr(mcp, 'name', 'Unknown'),
        minimal_mode=minimal_mode,
        include_experimental=include_experimental,
        include_deprecated=include_deprecated
    )

    try:
        if minimal_mode:
            count = await setup_fastmcp_minimal(mcp)
        else:
            count = await setup_fastmcp_with_all_tools(
                mcp,
                include_experimental=include_experimental,
                include_deprecated=include_deprecated
            )

        logger.info(
            "MCP Studio tools setup completed",
            tools_registered=count,
            server_name=getattr(mcp, 'name', 'Unknown')
        )

        return count

    except Exception as e:
        logger.error(
            "Failed to setup MCP Studio tools",
            error=str(e),
            exc_info=True
        )
        return 0


def run(
    mode: str = "web",
    host: str = None,
    port: int = None,
    mcp_name: str = "MCP Studio Server",
    include_experimental: bool = False,
    include_deprecated: bool = False,
    minimal_mode: bool = False
) -> None:
    """Run MCP Studio in different modes.

    Args:
        mode: Run mode - 'web' for web interface, 'mcp' for MCP server only
        host: Host to bind to (web mode only)
        port: Port to bind to (web mode only)
        mcp_name: Name for MCP server (mcp mode only)
        include_experimental: Include experimental tools
        include_deprecated: Include deprecated tools
        minimal_mode: Use minimal tool set
    """
    try:
        if mode == "web":
            # Run web application
            app = create_app()

            import uvicorn
            uvicorn.run(
                app,
                host=host or settings.HOST,
                port=port or settings.PORT,
                reload=settings.DEBUG,
                log_level=settings.LOG_LEVEL.lower(),
            )

        elif mode == "mcp":
            # Run MCP server
            async def run_mcp_server():
                mcp = create_mcp_server(
                    name=mcp_name,
                    include_experimental=include_experimental,
                    include_deprecated=include_deprecated,
                    minimal_mode=minimal_mode
                )

                # Setup tools
                await setup_tools(mcp)

                # Run the server
                logger.info("Starting MCP Studio server")
                mcp.run()

            asyncio.run(run_mcp_server())

        else:
            raise ValueError(f"Unknown run mode: {mode}")

    except KeyboardInterrupt:
        logger.info("MCP Studio stopped by user")
        sys.exit(0)
    except Exception as e:
        logger.critical("Fatal error in MCP Studio", error=str(e), exc_info=True)
        sys.exit(1)


# Convenience functions for common use cases

def create_minimal_server(name: str = "MCP Studio Minimal") -> FastMCP:
    """Create a minimal MCP server with safe tools only."""
    return create_mcp_server(name=name, minimal_mode=True)


def create_full_server(name: str = "MCP Studio Full") -> FastMCP:
    """Create a full MCP server with all tools including experimental."""
    return create_mcp_server(
        name=name,
        include_experimental=True,
        include_deprecated=False
    )


def create_development_server(name: str = "MCP Studio Dev") -> FastMCP:
    """Create a development MCP server with all tools for testing."""
    return create_mcp_server(
        name=name,
        include_experimental=True,
        include_deprecated=True
    )


# Example usage and CLI integration
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="MCP Studio - Manage MCP servers")
    parser.add_argument(
        "--mode",
        choices=["web", "mcp"],
        default="web",
        help="Run mode: web interface or MCP server"
    )
    parser.add_argument(
        "--host",
        default=None,
        help="Host to bind to (web mode only)"
    )
    parser.add_argument(
        "--port",
        type=int,
        default=None,
        help="Port to bind to (web mode only)"
    )
    parser.add_argument(
        "--name",
        default="MCP Studio Server",
        help="MCP server name (mcp mode only)"
    )
    parser.add_argument(
        "--experimental",
        action="store_true",
        help="Include experimental tools"
    )
    parser.add_argument(
        "--deprecated",
        action="store_true",
        help="Include deprecated tools"
    )
    parser.add_argument(
        "--minimal",
        action="store_true",
        help="Use minimal tool set"
    )

    args = parser.parse_args()

    run(
        mode=args.mode,
        host=args.host,
        port=args.port,
        mcp_name=args.name,
        include_experimental=args.experimental,
        include_deprecated=args.deprecated,
        minimal_mode=args.minimal
    )
