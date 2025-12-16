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
from fastapi.responses import JSONResponse, PlainTextResponse
import psutil

# Prometheus client
try:
    from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    # Dummy classes to prevent errors
    class Counter:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
        def inc(self): pass
        def observe(self, value): pass
    class Histogram:
        def __init__(self, *args, **kwargs): pass
        def labels(self, *args, **kwargs): return self
    class Gauge:
        def __init__(self, *args, **kwargs): pass
        def set(self, value): pass
        def inc(self): pass
        def dec(self): pass
    def generate_latest(): return b""

from ...app.core.config import settings
from ...app.core.logging_utils import get_logger

# Import __version__ safely
try:
    from ... import __version__
except ImportError:
    __version__ = "0.1.0"

router = APIRouter()
logger = get_logger(__name__)

# Prometheus metrics (only if prometheus_client is available)
if PROMETHEUS_AVAILABLE:
    # API metrics
    API_REQUESTS_TOTAL = Counter(
        'mcp_api_requests_total',
        'Total number of API requests',
        ['method', 'endpoint', 'status_code']
    )

    API_REQUEST_DURATION = Histogram(
        'mcp_api_request_duration_seconds',
        'API request duration in seconds',
        ['method', 'endpoint'],
        buckets=[0.1, 0.5, 1.0, 2.5, 5.0, 10.0]
    )

    # Active connections
    ACTIVE_CONNECTIONS = Gauge(
        'mcp_active_connections',
        'Number of active connections'
    )

    # Repo scanning metrics
    SCAN_PROGRESS_TOTAL = Gauge(
        'mcp_scan_progress_total',
        'Total repositories being scanned'
    )

    SCAN_PROGRESS_FOUND = Gauge(
        'mcp_scan_progress_found',
        'Number of MCP repositories found'
    )

    SCAN_PROGRESS_SKIPPED = Gauge(
        'mcp_scan_progress_skipped',
        'Number of repositories skipped'
    )

    SCAN_PROGRESS_ERRORS = Gauge(
        'mcp_scan_progress_errors',
        'Number of scanning errors'
    )

    # Repo metrics
    REPO_TOOLS = Gauge(
        'mcp_repo_tools',
        'Number of tools in a repository',
        ['repo_name']
    )


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


@router.get(
    "/metrics",
    summary="Prometheus Metrics",
    description="Expose Prometheus metrics for monitoring",
    response_class=PlainTextResponse,
    responses={
        200: {"description": "Metrics in Prometheus format"},
    },
)
async def metrics():
    """
    Prometheus metrics endpoint.

    Exposes application metrics in Prometheus format for monitoring and alerting.

    Returns:
        Plain text response with Prometheus metrics
    """
    if not PROMETHEUS_AVAILABLE:
        return PlainTextResponse(
            content="# Prometheus client not available\n",
            media_type=CONTENT_TYPE_LATEST
        )

    try:
        return PlainTextResponse(
            content=generate_latest().decode('utf-8'),
            media_type=CONTENT_TYPE_LATEST
        )
    except Exception as e:
        logger.error("Failed to generate metrics", error=str(e))
        return PlainTextResponse(
            content=f"# Error generating metrics: {e}\n",
            media_type=CONTENT_TYPE_LATEST,
            status_code=500
        )
