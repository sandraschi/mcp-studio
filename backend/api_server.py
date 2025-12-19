"""API-only server for MCP Studio.

This module provides a FastAPI application that serves only the API endpoints
without web templates or static files. This is useful for:
- Microservices architecture
- API-first development
- Headless operation
- Containerized API services
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

def create_api_app() -> FastAPI:
    """Create and configure the API-only FastAPI application."""

    app = FastAPI(
        title="MCP Studio API",
        description="API-only backend for MCP Studio",
        version="1.0.0",
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json"
    )

    # CORS middleware
    app.add_middleware(
        fastapi.middleware.cors.CORSMiddleware,
        allow_origins=["*"],  # Configure for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Add basic API endpoints directly
    print("[DEBUG] Adding API endpoints...")
    @app.get("/api/v1/test")
    async def api_test():
        """API test endpoint."""
        print("[DEBUG] api_test called")
        return {"message": "API test successful", "timestamp": "2025-12-17"}

    @app.get("/api/v1/repos/")
    async def get_repos():
        """Get repository data."""
        return {
            "status": "no_data",
            "message": "No scan data yet. Click 'START REPO SCAN' to analyze repositories.",
            "scan_url": "/api/v1/repos/run_scan/"
        }

    @app.post("/api/v1/repos/run_scan/")
    async def run_scan():
        """Start repository scan."""
        return {
            "status": "scan_started",
            "message": "Repository scan started in background."
        }

    # Health check endpoint
    @app.get("/health")
    async def health_check():
        """Basic health check."""
        return {"status": "healthy", "service": "mcp-studio-api"}

    # Error handlers
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "error": "Validation Error",
                "details": exc.errors(),
                "body": exc.body
            },
        )

    return app


# Create the application instance
app = create_api_app()


def main():
    """Main entry point for running the API server."""
    import uvicorn

    port = 8001

    print(f"[API SERVER] Starting on http://localhost:{port}")

    uvicorn.run(
        "backend.api_server:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    )


if __name__ == "__main__":
    main()
