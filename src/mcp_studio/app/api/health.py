"""Health check endpoints for MCP Studio."""

import platform
import sys
from datetime import datetime
from typing import Dict, Any

import fastapi
import pydantic
import structlog
from fastapi import APIRouter

from ... import __version__
from ...app.core.config import settings

router = APIRouter()
logger = structlog.get_logger(__name__)

class HealthCheck(pydantic.BaseModel):
    """Health check response model."""
    status: str
    version: str
    timestamp: datetime
    system: Dict[str, Any]
    dependencies: Dict[str, str]

@router.get(
    "/",
    response_model=HealthCheck,
    summary="Health check",
    description="Check if the MCP Studio API is running and healthy.",
)
async def health_check(request: fastapi.Request) -> HealthCheck:
    """
    Health check endpoint.
    
    Returns basic information about the API and its dependencies.
    
    Args:
        request: FastAPI request object
        
    Returns:
        Health check information
    """
    # Get system information
    system_info = {
        "python_version": platform.python_version(),
        "platform": platform.system(),
        "os_release": platform.release(),
        "hostname": platform.node(),
        "cpu_count": str(platform.machine()),
        "architecture": platform.architecture()[0],
    }
    
    # Get dependency versions
    dependencies = {
        "fastapi": fastapi.__version__,
        "pydantic": pydantic.__version__,
    }
    
    return HealthCheck(
        status="ok",
        version=__version__,
        timestamp=datetime.utcnow(),
        system=system_info,
        dependencies=dependencies,
    )

@router.get(
    "/ready",
    summary="Readiness check",
    description="Check if the MCP Studio API is ready to handle requests.",
    responses={
        200: {"description": "API is ready"},
        503: {"description": "API is not ready"},
    },
)
async def readiness_check() -> Dict[str, str]:
    """
    Readiness check endpoint.
    
    Verifies that the API and all its dependencies are ready to handle requests.
    
    Returns:
        Status message
    """
    # TODO: Add more comprehensive readiness checks
    # For example, check database connection, external services, etc.
    
    return {"status": "ready"}

@router.get(
    "/live",
    summary="Liveness check",
    description="Check if the MCP Studio API is alive.",
    responses={
        200: {"description": "API is alive"},
    },
)
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint.
    
    Simple check to verify that the API is running.
    
    Returns:
        Status message
    """
    return {"status": "alive"}

@router.get(
    "/info",
    summary="Service information",
    description="Get detailed information about the MCP Studio service.",
)
async def service_info() -> Dict[str, Any]:
    """
    Get detailed service information.
    
    Returns:
        Detailed service information
    """
    from ...services import discovery_service
    
    # Get server statistics
    server_count = len(discovery_service.discovered_servers)
    tool_count = sum(len(server.tools) for server in discovery_service.discovered_servers.values())
    
    # Get system resource usage
    import psutil
    process = psutil.Process()
    memory_info = process.memory_info()
    
    return {
        "service": "MCP Studio",
        "version": __version__,
        "status": "running",
        "started_at": datetime.fromtimestamp(process.create_time()).isoformat(),
        "uptime_seconds": process.create_time(),
        "resources": {
            "cpu_percent": process.cpu_percent(),
            "memory_rss_mb": memory_info.rss / 1024 / 1024,
            "memory_percent": process.memory_percent(),
            "open_files": len(process.open_files()),
            "threads": process.num_threads(),
        },
        "statistics": {
            "servers": server_count,
            "tools": tool_count,
            "discovery_paths": len(settings.MCP_DISCOVERY_PATHS),
        },
        "settings": {
            "debug": settings.DEBUG,
            "log_level": settings.LOG_LEVEL,
            "json_logs": settings.JSON_LOGS,
            "host": settings.HOST,
            "port": settings.PORT,
        },
    }
