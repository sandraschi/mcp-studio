"""API routes for MCP Studio."""

from fastapi import APIRouter

# Import all routers
from . import servers, tools, discovery, health, clients

# Create main router
router = APIRouter(prefix="/api/v1", tags=["api"])

# Include all routers with proper prefixes
router.include_router(servers.router, prefix="/servers", tags=["servers"])
router.include_router(tools.router, prefix="/tools", tags=["tools"])
router.include_router(discovery.router, prefix="/discovery", tags=["discovery"])
router.include_router(clients.router, prefix="/clients", tags=["clients"])

# Health endpoints at /api/v1/health/*
router.include_router(health.router, prefix="/health", tags=["health"])
