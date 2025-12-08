"""
Standardized health and status endpoints for MCP Studio.
FastAPI best practices compliance.
"""

import platform
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
import psutil

from ...app.core.config import settings
from ...app.core.logging_utils import get_logger

# Import __version__ safely
try:
    from ... import __version__
except ImportError:
    __version__ = "0.1.0"

router = APIRouter()
logger = get_logger(__name__)


class ServiceInfo(BaseModel):
    """Service information model."""
    name: str = Field(..., description="Service name")
    version: str = Field(..., description="Service version")
    status: str = Field(..., description="Service status")


class SystemInfo(BaseModel):
    """System information model."""
    platform: str = Field(..., description="Operating system")
    python_version: str = Field(..., description="Python version")
    hostname: str = Field(..., description="Hostname")
    architecture: str = Field(..., description="System architecture")


class ResourceUsage(BaseModel):
    """Resource usage model."""
    cpu_percent: float = Field(..., description="CPU usage percentage")
    memory_mb: float = Field(..., description="Memory usage in MB")
    memory_percent: float = Field(..., description="Memory usage percentage")
    open_files: int = Field(..., description="Number of open file descriptors")
    threads: int = Field(..., description="Number of threads")


class StatusResponse(BaseModel):
    """Standard status response."""
    service: ServiceInfo = Field(..., description="Service information")
    system: SystemInfo = Field(..., description="System information")
    resources: ResourceUsage = Field(..., description="Resource usage")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    uptime_seconds: Optional[float] = Field(None, description="Server uptime in seconds")


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Health status")
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    version: str = Field(..., description="Service version")


@router.get(
    "/status",
    response_model=StatusResponse,
    summary="Get service status",
    description="Get detailed status information about the MCP Studio service",
    responses={
        200: {"description": "Service is running and healthy"},
        503: {"description": "Service is not ready"},
    },
)
async def get_status() -> StatusResponse:
    """
    Get comprehensive status information.
    
    Returns detailed information about the service, system, and resource usage.
    This endpoint provides production-ready monitoring capabilities.
    
    Returns:
        StatusResponse with service, system, and resource information
    """
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # Get uptime
        create_time = process.create_time()
        uptime = datetime.now().timestamp() - create_time
        
        return StatusResponse(
            service=ServiceInfo(
                name="MCP Studio",
                version=__version__,
                status="running",
            ),
            system=SystemInfo(
                platform=platform.system(),
                python_version=platform.python_version(),
                hostname=platform.node(),
                architecture=platform.machine(),
            ),
            resources=ResourceUsage(
                cpu_percent=process.cpu_percent(interval=0.1),
                memory_mb=memory_info.rss / 1024 / 1024,
                memory_percent=process.memory_percent(),
                open_files=len(process.open_files()),
                threads=process.num_threads(),
            ),
            uptime_seconds=uptime,
        )
    except Exception as e:
        logger.error("Failed to get status", error=str(e), exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"detail": "Service status unavailable"}
        )


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Quick health check endpoint for load balancers and monitoring",
    responses={
        200: {"description": "Service is healthy"},
    },
)
async def health_check() -> HealthResponse:
    """
    Health check endpoint.
    
    Simple endpoint for load balancers and monitoring systems.
    Returns minimal information quickly.
        
    Returns:
        HealthResponse with status and version
    """
    return HealthResponse(
        status="ok",
        version=__version__,
    )


@router.get(
    "/health/ready",
    summary="Readiness check",
    description="Check if the service is ready to handle requests",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is not ready"},
    },
)
async def readiness_check() -> JSONResponse:
    """
    Readiness check endpoint.
    
    Verifies that the service and dependencies are ready.
    Used by Kubernetes liveness probes.
    
    Returns:
        JSON response with status
    """
    try:
        checks = {
            "fastmcp": False,
            "discovery_service": False,
            "settings": False,
        }
        
        # Check FastMCP is importable
        try:
            from fastmcp import FastMCP
            checks["fastmcp"] = True
        except ImportError:
            logger.warning("FastMCP import failed")
        
        # Check discovery service is accessible
        try:
            from ..services.discovery_service import discovered_servers
            checks["discovery_service"] = True
        except Exception as e:
            logger.warning("Discovery service check failed", error=str(e))
        
        # Check settings are accessible
        try:
            from ..core.config import settings
            if settings:
                checks["settings"] = True
        except Exception as e:
            logger.warning("Settings check failed", error=str(e))
        
        # All critical checks must pass
        all_ready = all(checks.values())
        
        if all_ready:
            return JSONResponse(
                status_code=status.HTTP_200_OK,
                content={"status": "ready", "checks": checks}
            )
        else:
            return JSONResponse(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                content={"status": "not ready", "checks": checks}
            )
    except Exception as e:
        logger.warning("Readiness check failed", error=str(e))
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={"status": "not ready", "error": str(e)}
        )


@router.get(
    "/health/live",
    summary="Liveness check",
    description="Check if the service is alive",
    responses={
        200: {"description": "Service is alive"},
    },
)
async def liveness_check() -> JSONResponse:
    """
    Liveness check endpoint.
    
    Simple check to verify the service is running.
    Used by Kubernetes liveness probes.
    
    Returns:
        JSON response with status
    """
    return JSONResponse(
        status_code=status.HTTP_200_OK,
        content={"status": "alive"}
    )
