"""
MCP Studio API Package

This package contains the FastAPI application and API endpoints for MCP Studio.
"""
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer
from typing import List, Dict, Any, Optional
import logging

# Initialize logging
logger = logging.getLogger("mcp.api")

# Create FastAPI app
app = FastAPI(
    title="MCP Studio API",
    description="API for MCP Studio - A Modern Control Panel for MCP Servers",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# OAuth2 scheme for token authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")

# API version prefix
API_PREFIX = "/api/v1"

# Include routers
from . import auth, tools, server, files, data, development

# Include API routers
app.include_router(auth.router, prefix=f"{API_PREFIX}/auth", tags=["Authentication"])
app.include_router(tools.router, prefix=f"{API_PREFIX}/tools", tags=["Tools"])
app.include_router(server.router, prefix=f"{API_PREFIX}/server", tags=["Server"])
app.include_router(files.router, prefix=f"{API_PREFIX}/files", tags=["Files"])
app.include_router(data.router, prefix=f"{API_PREFIX}/data", tags=["Data"])
app.include_router(development.router, prefix=f"{API_PREFIX}/dev", tags=["Development"])

# Health check endpoint
@app.get("/api/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "version": "0.1.0"}

# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request, exc):
    """Global exception handler."""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return {"detail": "Internal server error"}, 500

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=7787)
